'use strict';
/* ===========================================================================
   Respaldos automáticos, verificados y con copia fuera del servidor.
   Sin dependencias: ZIP propio, cifrado AES-256-GCM, firma AWS SigV4 (almacenamiento
   compatible con S3: Backblaze B2, Cloudflare R2, Wasabi, MinIO, AWS…) y envío por correo (SMTP).
   =========================================================================== */
const net = require('net'), tls = require('tls'), http = require('http'), https = require('https'), zlib = require('zlib'), crypto = require('crypto'), fs = require('fs'), path = require('path');

/* ---------- ZIP (sin compresión) ---------- */
function dosFecha(d) { return [((d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1)) & 0xffff, (((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate()) & 0xffff]; }
function escribeZip(destino, entradas) {
  return new Promise((ok, mal) => {
    const ws = fs.createWriteStream(destino); let desp = 0; ws.on('error', mal);
    const escribe = b => new Promise(r => { if (ws.write(b)) r(); else ws.once('drain', r); });
    (async () => {
      const central = [], [hora, fecha] = dosFecha(new Date());
      for (const e of entradas) {
        const nom = Buffer.from(e.nombre, 'utf8'), pos = desp, h = Buffer.alloc(30);
        h.writeUInt32LE(0x04034b50, 0); h.writeUInt16LE(20, 4); h.writeUInt16LE(0x0808, 6); h.writeUInt16LE(0, 8); h.writeUInt16LE(hora, 10); h.writeUInt16LE(fecha, 12); h.writeUInt16LE(nom.length, 26);
        await escribe(h); await escribe(nom); desp += 30 + nom.length;
        let crc = 0, tam = 0;
        if (e.datos) { crc = zlib.crc32(e.datos, 0); tam = e.datos.length; await escribe(e.datos); }
        else for await (const trozo of fs.createReadStream(e.ruta)) { crc = zlib.crc32(trozo, crc); tam += trozo.length; await escribe(trozo); }
        desp += tam;
        const d = Buffer.alloc(16); d.writeUInt32LE(0x08074b50, 0); d.writeUInt32LE(crc >>> 0, 4); d.writeUInt32LE(tam, 8); d.writeUInt32LE(tam, 12); await escribe(d); desp += 16;
        central.push({ nom, crc: crc >>> 0, tam, pos });
      }
      const inicio = desp;
      for (const c of central) {
        const h = Buffer.alloc(46);
        h.writeUInt32LE(0x02014b50, 0); h.writeUInt16LE(20, 4); h.writeUInt16LE(20, 6); h.writeUInt16LE(0x0808, 8); h.writeUInt16LE(0, 10); h.writeUInt16LE(hora, 12); h.writeUInt16LE(fecha, 14);
        h.writeUInt32LE(c.crc, 16); h.writeUInt32LE(c.tam, 20); h.writeUInt32LE(c.tam, 24); h.writeUInt16LE(c.nom.length, 28); h.writeUInt32LE(c.pos, 42);
        await escribe(h); await escribe(c.nom); desp += 46 + c.nom.length;
      }
      const fin = Buffer.alloc(22); fin.writeUInt32LE(0x06054b50, 0); fin.writeUInt16LE(central.length, 8); fin.writeUInt16LE(central.length, 10); fin.writeUInt32LE(desp - inicio, 12); fin.writeUInt32LE(inicio, 16);
      ws.end(fin, () => ok({ bytes: desp + 22, entradas: central.length }));
    })().catch(mal);
  });
}
function leeZip(ruta) {
  const fd = fs.openSync(ruta, 'r'), tam = fs.fstatSync(fd).size;
  try {
    if (tam < 22) throw new Error('El archivo es demasiado pequeño para ser un respaldo.');
    const n = Math.min(tam, 70000), buf = Buffer.alloc(n); fs.readSync(fd, buf, 0, n, tam - n);
    let i = n - 22; while (i >= 0 && buf.readUInt32LE(i) !== 0x06054b50) i--;
    if (i < 0) throw new Error('No parece un ZIP completo (falta su final).');
    const total = buf.readUInt16LE(i + 10), cdTam = buf.readUInt32LE(i + 12), cdPos = buf.readUInt32LE(i + 16);
    const cd = Buffer.alloc(cdTam); fs.readSync(fd, cd, 0, cdTam, cdPos);
    const entradas = []; let p = 0;
    for (let k = 0; k < total; k++) {
      if (cd.readUInt32LE(p) !== 0x02014b50) throw new Error('El directorio del ZIP está dañado.');
      const nl = cd.readUInt16LE(p + 28), el = cd.readUInt16LE(p + 30), cl = cd.readUInt16LE(p + 32);
      entradas.push({ nombre: cd.toString('utf8', p + 46, p + 46 + nl), crc: cd.readUInt32LE(p + 16), tam: cd.readUInt32LE(p + 24), metodo: cd.readUInt16LE(p + 10), pos: cd.readUInt32LE(p + 42) });
      p += 46 + nl + el + cl;
    }
    return { fd, entradas, bytes: tam, cierra() { try { fs.closeSync(fd); } catch (e) {} } };
  } catch (e) { fs.closeSync(fd); throw e; }
}
function inicioDatos(z, e) { const h = Buffer.alloc(30); fs.readSync(z.fd, h, 0, 30, e.pos); if (h.readUInt32LE(0) !== 0x04034b50) throw new Error('Entrada dañada: ' + e.nombre); return e.pos + 30 + h.readUInt16LE(26) + h.readUInt16LE(28); }
function crcEntrada(z, e) {
  if (e.metodo !== 0) throw new Error('Entrada comprimida no admitida: ' + e.nombre);
  let pos = inicioDatos(z, e), resta = e.tam, crc = 0; const buf = Buffer.alloc(1 << 20);
  while (resta > 0) { const n = Math.min(resta, buf.length), l = fs.readSync(z.fd, buf, 0, n, pos); if (l <= 0) throw new Error('El ZIP termina antes de tiempo: ' + e.nombre); crc = zlib.crc32(buf.subarray(0, l), crc); pos += l; resta -= l; }
  return crc >>> 0;
}
function leeEntrada(z, e) { const b = Buffer.alloc(e.tam); fs.readSync(z.fd, b, 0, e.tam, inicioDatos(z, e)); return b; }
function extraeEntrada(z, e, destino) {
  const out = fs.openSync(destino, 'w'); try {
    let pos = inicioDatos(z, e), resta = e.tam; const buf = Buffer.alloc(1 << 20);
    while (resta > 0) { const n = Math.min(resta, buf.length), l = fs.readSync(z.fd, buf, 0, n, pos); if (l <= 0) throw new Error('El ZIP termina antes de tiempo'); fs.writeSync(out, buf, 0, l); pos += l; resta -= l; }
  } finally { fs.closeSync(out); }
}
function shaArchivo(ruta) { return new Promise((ok, mal) => { const h = crypto.createHash('sha256'); fs.createReadStream(ruta).on('data', d => h.update(d)).on('end', () => ok(h.digest('hex'))).on('error', mal); }); }

/* ---------- Verificación: se abre el respaldo como si fuera a restaurarse ---------- */
function verificaZip(ruta, DatabaseSync, tmp) {
  const t0 = Date.now(), errores = []; let z = null, tdb = null;
  try {
    z = leeZip(ruta);
    const eman = z.entradas.find(e => e.nombre === 'manifest.json'), edb = z.entradas.find(e => e.nombre === 'lafragua.db');
    if (!eman) errores.push('Falta el manifiesto del respaldo.'); if (!edb) errores.push('Falta la base de datos.');
    for (const e of z.entradas) { if (crcEntrada(z, e) !== e.crc) errores.push('El contenido no coincide (archivo dañado): ' + e.nombre); }
    let man = null; if (eman) { try { man = JSON.parse(leeEntrada(z, eman).toString('utf8')); } catch (e) { errores.push('El manifiesto está dañado.'); } }
    let filas = 0, colecciones = 0;
    if (edb && man && !errores.length) {
      tdb = path.join(tmp, 'verif-' + crypto.randomBytes(5).toString('hex') + '.db'); extraeEntrada(z, edb, tdb);
      const d = new DatabaseSync(tdb, { readOnly: true });
      try {
        const ic = d.prepare('PRAGMA integrity_check').all(); if (!(ic.length === 1 && String(Object.values(ic[0])[0]) === 'ok')) errores.push('La base de datos no pasó la revisión de integridad.');
        const cuenta = {}; d.prepare('SELECT coleccion, COUNT(*) AS n FROM docs GROUP BY coleccion').all().forEach(r => { cuenta[r.coleccion] = r.n; filas += r.n; colecciones++; });
        const esp = man.filas || {}; Object.keys(Object.assign({}, esp, cuenta)).forEach(k => { if ((esp[k] || 0) !== (cuenta[k] || 0)) errores.push('Faltan o sobran registros en «' + k + '» (' + (cuenta[k] || 0) + ' de ' + (esp[k] || 0) + ').'); });
        const nu = d.prepare('SELECT COUNT(*) AS n FROM usuarios').get().n; if (nu !== man.usuarios) errores.push('Los usuarios del respaldo no coinciden (' + nu + ' de ' + man.usuarios + ').');
        const na = d.prepare('SELECT COUNT(*) AS n FROM archivos').get().n; if (na !== man.registrosArchivos) errores.push('El índice de archivos no coincide.');
      } finally { d.close(); }
      if (crypto.createHash('sha256').update(fs.readFileSync(tdb)).digest('hex') !== man.sha256Db) errores.push('La huella (SHA-256) de la base de datos no coincide.');
      for (const a of man.archivos || []) { const e = z.entradas.find(x => x.nombre === a.entrada); if (!e) errores.push('Falta el archivo ' + a.entrada); else if (e.tam !== a.tam || e.crc !== a.crc) errores.push('El archivo ' + a.entrada + ' no coincide.'); }
    }
    return { ok: errores.length === 0, errores: errores.slice(0, 8), filas, colecciones, archivos: man ? (man.archivos || []).length : 0, bytes: z.bytes, ms: Date.now() - t0 };
  } catch (e) { return { ok: false, errores: [e.message], filas: 0, colecciones: 0, archivos: 0, bytes: z ? z.bytes : 0, ms: Date.now() - t0 }; }
  finally { if (z) z.cierra(); if (tdb) { try { fs.unlinkSync(tdb); } catch (e) {} } }
}

/* ---------- Cifrado de los respaldos que salen del servidor ---------- */
const MAGIA = Buffer.from('LFRC1\0');
function claveDe(clave, salt) { return crypto.scryptSync(String(clave), salt, 32, { N: 16384, r: 8, p: 1 }); }
function cifraArchivo(origen, destino, clave) {
  return new Promise((ok, mal) => {
    const salt = crypto.randomBytes(16), iv = crypto.randomBytes(12), c = crypto.createCipheriv('aes-256-gcm', claveDe(clave, salt), iv), ws = fs.createWriteStream(destino);
    ws.on('error', mal); ws.write(Buffer.concat([MAGIA, salt, iv]));
    const rs = fs.createReadStream(origen); rs.on('error', mal);
    rs.on('data', d => { if (!ws.write(c.update(d))) { rs.pause(); ws.once('drain', () => rs.resume()); } });
    rs.on('end', () => { ws.write(c.final()); ws.end(c.getAuthTag(), () => ok()); });
  });
}
function descifraArchivo(origen, destino, clave) {
  return new Promise((ok, mal) => {
    const fd = fs.openSync(origen, 'r'), tam = fs.fstatSync(fd).size; try {
      if (tam < 6 + 16 + 12 + 16) throw new Error('El archivo cifrado está incompleto.');
      const cab = Buffer.alloc(34), tag = Buffer.alloc(16); fs.readSync(fd, cab, 0, 34, 0); fs.readSync(fd, tag, 0, 16, tam - 16);
      if (!cab.subarray(0, 6).equals(MAGIA)) throw new Error('Este archivo no es un respaldo cifrado de la plataforma.');
      const d = crypto.createDecipheriv('aes-256-gcm', claveDe(clave, cab.subarray(6, 22)), cab.subarray(22, 34)); d.setAuthTag(tag);
      const ws = fs.createWriteStream(destino); ws.on('error', mal);
      const rs = fs.createReadStream(origen, { start: 34, end: tam - 17 }); rs.on('error', mal);
      rs.on('data', b => { try { if (!ws.write(d.update(b))) { rs.pause(); ws.once('drain', () => rs.resume()); } } catch (e) { mal(e); } });
      rs.on('end', () => { try { ws.write(d.final()); ws.end(() => ok()); } catch (e) { ws.destroy(); mal(new Error('La contraseña no es correcta o el archivo está dañado.')); } });
    } catch (e) { mal(e); } finally { fs.closeSync(fd); }
  });
}

/* ---------- Firma AWS Signature Version 4 ---------- */
const hmac = (k, t) => crypto.createHmac('sha256', k).update(t, 'utf8').digest();
const hex = t => crypto.createHash('sha256').update(t, 'utf8').digest('hex');
function codifica(t, barra) { return encodeURIComponent(t).replace(/[!'()*]/g, c => '%' + c.charCodeAt(0).toString(16).toUpperCase()).replace(/%2F/g, barra ? '/' : '%2F'); }
function firmaAws(o) {
  const amz = o.fecha, dia = amz.slice(0, 8), hs = Object.keys(o.headers).map(k => k.toLowerCase()).sort();
  const ch = hs.map(k => k + ':' + String(Object.entries(o.headers).find(([x]) => x.toLowerCase() === k)[1]).trim().replace(/\s+/g, ' ') + '\n').join(''), fh = hs.join(';');
  const consulta = Object.keys(o.consulta || {}).sort().map(k => codifica(k) + '=' + codifica(o.consulta[k])).join('&');
  const canon = [o.metodo, o.ruta, consulta, ch, fh, o.payload].join('\n');
  const alcance = dia + '/' + o.region + '/' + o.servicio + '/aws4_request', porFirmar = ['AWS4-HMAC-SHA256', amz, alcance, hex(canon)].join('\n');
  const k = hmac(hmac(hmac(hmac('AWS4' + o.secreto, dia), o.region), o.servicio), 'aws4_request'), firma = crypto.createHmac('sha256', k).update(porFirmar, 'utf8').digest('hex');
  return { firma, authorization: 'AWS4-HMAC-SHA256 Credential=' + o.acceso + '/' + alcance + ', SignedHeaders=' + fh + ', Signature=' + firma, canonica: canon };
}
function ahoraAmz() { return new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, ''); }
function solicitud(url, opciones, cuerpoRuta, timeoutMs) {
  return new Promise((ok, mal) => {
    const lib = url.protocol === 'https:' ? https : http;
    const rq = lib.request(url, opciones, r => { const t = []; r.on('data', d => t.push(d)); r.on('end', () => ok({ status: r.statusCode, cuerpo: Buffer.concat(t).toString('utf8').slice(0, 600) })); });
    rq.setTimeout(timeoutMs || 600000, () => rq.destroy(new Error('Tiempo de espera agotado.'))); rq.on('error', mal);
    if (cuerpoRuta) { const rs = fs.createReadStream(cuerpoRuta); rs.on('error', mal); rs.pipe(rq); } else rq.end();
  });
}
async function s3Pon(cfg, clave, rutaArchivo, mime) {
  const base = new URL(String(cfg.endpoint || '').replace(/\/+$/, '')), claveObj = String(clave).replace(/^\/+/, '');
  const rutaUrl = '/' + codifica(cfg.bucket) + '/' + claveObj.split('/').map(s => codifica(s)).join('/');
  const url = new URL(base.origin + rutaUrl), payload = rutaArchivo ? await shaArchivo(rutaArchivo) : hex(''), tam = rutaArchivo ? fs.statSync(rutaArchivo).size : 0, amz = ahoraAmz();
  const headers = { 'host': url.host, 'x-amz-content-sha256': payload, 'x-amz-date': amz, 'content-length': String(tam), 'content-type': mime || 'application/octet-stream' };
  const f = firmaAws({ metodo: 'PUT', ruta: url.pathname, consulta: {}, headers, payload, region: cfg.region || 'us-east-1', servicio: 's3', acceso: cfg.acceso, secreto: cfg.secreto, fecha: amz });
  const r = await solicitud(url, { method: 'PUT', headers: Object.assign({}, headers, { authorization: f.authorization }) }, rutaArchivo || null);
  if (r.status < 200 || r.status > 299) throw new Error('El almacenamiento respondió ' + r.status + (r.cuerpo ? ': ' + r.cuerpo.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 160) : ''));
  return r.status;
}

/* ---------- Correo (SMTP) ---------- */
function leeRespuesta(sock) {
  return new Promise((ok, mal) => {
    let buf = ''; const alDato = d => { buf += d.toString('utf8'); const ls = buf.split(/\r?\n/).filter(Boolean); if (ls.length && /^\d{3} /.test(ls[ls.length - 1]) && /\r?\n$/.test(buf)) { quita(); ok({ codigo: parseInt(ls[ls.length - 1].slice(0, 3), 10), texto: ls.join('\n') }); } };
    const alError = e => { quita(); mal(e); }, alFin = () => { quita(); mal(new Error('El servidor de correo cerró la conexión.')); }, t = setTimeout(() => { quita(); mal(new Error('El servidor de correo no respondió.')); }, 30000);
    function quita() { clearTimeout(t); sock.removeListener('data', alDato); sock.removeListener('error', alError); sock.removeListener('close', alFin); }
    sock.on('data', alDato); sock.on('error', alError); sock.on('close', alFin);
  });
}
const b64 = t => Buffer.from(t, 'utf8').toString('base64');
const trozos76 = b => b.toString('base64').replace(/(.{76})/g, '$1\r\n');
function armaMime(cfg, msg) {
  const bnd = 'lf_' + crypto.randomBytes(8).toString('hex'), para = cfg.para.join(', ');
  const cab = ['From: ' + cfg.de, 'To: ' + para, 'Subject: =?UTF-8?B?' + b64(msg.asunto) + '?=', 'Date: ' + new Date().toUTCString(), 'Message-ID: <' + crypto.randomBytes(8).toString('hex') + '@lafragua>', 'MIME-Version: 1.0', 'Content-Type: multipart/mixed; boundary="' + bnd + '"'];
  let c = cab.join('\r\n') + '\r\n\r\n--' + bnd + '\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n\r\n' + trozos76(Buffer.from(msg.texto, 'utf8')) + '\r\n';
  (msg.adjuntos || []).forEach(a => { c += '--' + bnd + '\r\nContent-Type: ' + (a.tipo || 'application/octet-stream') + '; name="' + a.nombre + '"\r\nContent-Transfer-Encoding: base64\r\nContent-Disposition: attachment; filename="' + a.nombre + '"\r\n\r\n' + trozos76(a.datos) + '\r\n'; });
  return (c + '--' + bnd + '--\r\n').replace(/^\./gm, '..');
}
async function smtpEnvia(cfg, msg) {
  let sock = await new Promise((ok, mal) => { const s = cfg.seguro ? tls.connect({ host: cfg.host, port: cfg.puerto, servername: cfg.host, rejectUnauthorized: cfg.confiar !== true }, () => ok(s)) : net.connect({ host: cfg.host, port: cfg.puerto }, () => ok(s)); s.on('error', mal); s.setTimeout(60000, () => s.destroy(new Error('Tiempo de espera agotado con el servidor de correo.'))); });
  const cmd = async (linea, esperado) => { if (linea !== null) sock.write(linea + '\r\n'); const r = await leeRespuesta(sock); if (esperado && !esperado.includes(r.codigo)) throw new Error('El correo respondió ' + r.codigo + ' a ' + (linea ? linea.split(' ')[0] : 'la conexión') + ': ' + r.texto.split('\n').pop().slice(4, 120)); return r; };
  try {
    await cmd(null, [220]); let r = await cmd('EHLO lafragua.local', [250]);
    if (!cfg.seguro && /STARTTLS/i.test(r.texto)) {
      await cmd('STARTTLS', [220]);
      sock = await new Promise((ok, mal) => { const s = tls.connect({ socket: sock, servername: cfg.host, rejectUnauthorized: cfg.confiar !== true }, () => ok(s)); s.on('error', mal); });
      r = await cmd('EHLO lafragua.local', [250]);
    }
    if (cfg.usuario) { if (/AUTH[^\n]*PLAIN/i.test(r.texto)) await cmd('AUTH PLAIN ' + Buffer.from('\0' + cfg.usuario + '\0' + cfg.clave).toString('base64'), [235]); else { await cmd('AUTH LOGIN', [334]); await cmd(b64(cfg.usuario), [334]); await cmd(b64(cfg.clave), [235]); } }
    await cmd('MAIL FROM:<' + cfg.de.replace(/^.*<|>.*$/g, '') + '>', [250]);
    for (const p of cfg.para) await cmd('RCPT TO:<' + p + '>', [250, 251]);
    await cmd('DATA', [354]); sock.write(armaMime(cfg, msg) + '\r\n.\r\n'); await cmd(null, [250]);
    try { sock.write('QUIT\r\n'); } catch (e) {}
  } finally { try { sock.destroy(); } catch (e) {} }
}

/* ---------- Programación (hora de la Ciudad de México) ---------- */
function fechaMx(d) { const p = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Mexico_City', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23' }).formatToParts(d || new Date()).reduce((o, x) => (o[x.type] = x.value, o), {}); return { dia: p.year + '-' + p.month + '-' + p.day, hora: parseInt(p.hour, 10) }; }
function debeCorrer(cfg, est, ahora) {
  if (!cfg || !cfg.activo) return false; const mx = fechaMx(new Date(ahora)); if (mx.hora < (cfg.hora == null ? 2 : cfg.hora)) return false;
  if (est.ultimoAutoOk === mx.dia) return false;
  if (est.ultimoIntentoAuto && ahora - est.ultimoIntentoAuto < 3600000) return false;
  return true;
}

module.exports = { escribeZip, leeZip, crcEntrada, leeEntrada, extraeEntrada, shaArchivo, verificaZip, cifraArchivo, descifraArchivo, firmaAws, s3Pon, smtpEnvia, armaMime, debeCorrer, fechaMx, ahoraAmz };
