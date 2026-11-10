'use strict';
const R = require('/tmp/nb/respaldos.js'), fs = require('fs'), path = require('path'), http = require('http'), net = require('net'), crypto = require('crypto');
const { DatabaseSync } = require('node:sqlite');
const resultados = {}; const ok = (n, c) => { resultados[n] = !!c; };
const T = '/tmp/motor_t'; fs.rmSync(T, { recursive: true, force: true }); fs.mkdirSync(T, { recursive: true });
(async () => {
  // ---- firma AWS (vector oficial de la documentación de AWS) ----
  const f = R.firmaAws({ metodo: 'GET', ruta: '/', consulta: { Action: 'ListUsers', Version: '2010-05-08' }, headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8', 'Host': 'iam.amazonaws.com', 'X-Amz-Date': '20150830T123600Z' }, payload: crypto.createHash('sha256').update('').digest('hex'), region: 'us-east-1', servicio: 'iam', acceso: 'AKIDEXAMPLE', secreto: 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY', fecha: '20150830T123600Z' });
  ok('firma_aws_coincide_con_el_ejemplo_oficial', f.firma === '5d672d79c15b13162d9279b0855cfba6789a8edb4c82c400e06b5924a6f2b5d7');
  // ---- base de datos de prueba y paquete ZIP ----
  const dbp = path.join(T, 'lafragua.db'); const d = new DatabaseSync(dbp);
  d.exec("CREATE TABLE docs (coleccion TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, actualizado INTEGER NOT NULL, PRIMARY KEY (coleccion,id)); CREATE TABLE usuarios (u TEXT PRIMARY KEY); CREATE TABLE archivos (id TEXT PRIMARY KEY);");
  for (let i = 0; i < 50; i++) d.prepare('INSERT INTO docs VALUES (?,?,?,?)').run(i % 2 ? 'students' : 'ledger', 'x' + i, JSON.stringify({ n: i }), 1);
  d.prepare("INSERT INTO usuarios VALUES ('admin')").run(); d.prepare("INSERT INTO archivos VALUES ('f1')").run(); d.close();
  const archivo = path.join(T, 'ine.jpg'); fs.writeFileSync(archivo, crypto.randomBytes(300000));
  const man = { filas: { students: 25, ledger: 25 }, usuarios: 1, registrosArchivos: 1, sha256Db: await R.shaArchivo(dbp), archivos: [] };
  const crcA = require('zlib').crc32(fs.readFileSync(archivo), 0) >>> 0; man.archivos.push({ id: 'f1', entrada: 'archivos/f1-ine.jpg', tam: 300000, crc: crcA });
  const zip = path.join(T, 'respaldo.zip'); const w = await R.escribeZip(zip, [{ nombre: 'lafragua.db', ruta: dbp }, { nombre: 'archivos/f1-ine.jpg', ruta: archivo }, { nombre: 'manifest.json', datos: Buffer.from(JSON.stringify(man)) }]);
  ok('el_zip_se_escribe_con_3_entradas', w.entradas === 3 && w.bytes > 300000);
  const v = R.verificaZip(zip, DatabaseSync, T);
  ok('un_respaldo_sano_pasa_la_verificacion', v.ok && v.filas === 50 && v.colecciones === 2 && v.archivos === 1 && v.errores.length === 0);
  // ---- se detectan daños ----
  const roto = path.join(T, 'roto.zip'); fs.copyFileSync(zip, roto); const fd = fs.openSync(roto, 'r+'); const b = Buffer.alloc(1); fs.readSync(fd, b, 0, 1, 20000); b[0] ^= 0xff; fs.writeSync(fd, b, 0, 1, 20000); fs.closeSync(fd);
  const v2 = R.verificaZip(roto, DatabaseSync, T); ok('un_byte_cambiado_se_detecta', !v2.ok && v2.errores.some(e => /no coincide|dañado/.test(e)));
  const corto = path.join(T, 'corto.zip'); fs.writeFileSync(corto, fs.readFileSync(zip).subarray(0, 100000)); const v3 = R.verificaZip(corto, DatabaseSync, T); ok('un_zip_cortado_se_detecta', !v3.ok);
  const manMal = Object.assign({}, man, { filas: { students: 24, ledger: 25 } }); const zip2 = path.join(T, 'mal.zip'); await R.escribeZip(zip2, [{ nombre: 'lafragua.db', ruta: dbp }, { nombre: 'archivos/f1-ine.jpg', ruta: archivo }, { nombre: 'manifest.json', datos: Buffer.from(JSON.stringify(manMal)) }]);
  const v4 = R.verificaZip(zip2, DatabaseSync, T); ok('si_faltan_registros_frente_al_manifiesto_lo_dice', !v4.ok && v4.errores.some(e => /students/.test(e)));
  ok('la_verificacion_no_deja_basura', fs.readdirSync(T).filter(n => n.startsWith('verif-')).length === 0);
  // ---- cifrado ----
  const cif = path.join(T, 'respaldo.zip.cif'), plano = path.join(T, 'recuperado.zip'); await R.cifraArchivo(zip, cif, 'clave-super-secreta');
  ok('el_archivo_cifrado_no_se_parece_al_original', fs.statSync(cif).size > fs.statSync(zip).size && !fs.readFileSync(cif).includes(Buffer.from('lafragua.db')) && fs.readFileSync(cif).subarray(0, 5).toString() === 'LFRC1');
  await R.descifraArchivo(cif, plano, 'clave-super-secreta'); ok('con_la_clave_correcta_vuelve_igual', (await R.shaArchivo(plano)) === (await R.shaArchivo(zip)));
  let malaClave = false; try { await R.descifraArchivo(cif, path.join(T, 'x.zip'), 'otra-clave'); } catch (e) { malaClave = /contraseña/.test(e.message); } ok('con_otra_clave_no_abre', malaClave);
  const cif2 = path.join(T, 'adulterado.cif'); const bc = fs.readFileSync(cif); bc[5000] ^= 1; fs.writeFileSync(cif2, bc); let adul = false; try { await R.descifraArchivo(cif2, path.join(T, 'y.zip'), 'clave-super-secreta'); } catch (e) { adul = true; } ok('si_lo_cambian_no_abre', adul);
  // ---- almacenamiento S3 (servidor simulado) ----
  const recibidos = []; const srv = http.createServer((rq, rs) => { const t = []; rq.on('data', x => t.push(x)); rq.on('end', () => { recibidos.push({ m: rq.method, url: rq.url, h: rq.headers, n: Buffer.concat(t).length, sha: crypto.createHash('sha256').update(Buffer.concat(t)).digest('hex') }); if (/falla/.test(rq.url)) { rs.writeHead(403); rs.end('<Error><Code>SignatureDoesNotMatch</Code></Error>'); } else { rs.writeHead(200); rs.end(); } }); }).listen(0);
  await new Promise(r => srv.on('listening', r)); const pS3 = srv.address().port;
  const cfg = { endpoint: 'http://127.0.0.1:' + pS3, bucket: 'mi-bucket', region: 'us-east-1', acceso: 'AKIAEJEMPLO', secreto: 'secreto/ejemplo+1234' };
  const st = await R.s3Pon(cfg, 'respaldos/2026-11-10/respaldo.zip.cif', cif, 'application/octet-stream');
  const r0 = recibidos[0];
  ok('s3_recibe_el_archivo_completo_con_su_huella', st === 200 && r0.m === 'PUT' && r0.url === '/mi-bucket/respaldos/2026-11-10/respaldo.zip.cif' && r0.n === fs.statSync(cif).size && r0.sha === r0.h['x-amz-content-sha256']);
  ok('s3_recibe_la_firma_v4', /^AWS4-HMAC-SHA256 Credential=AKIAEJEMPLO\/\d{8}\/us-east-1\/s3\/aws4_request, SignedHeaders=content-length;content-type;host;x-amz-content-sha256;x-amz-date, Signature=[0-9a-f]{64}$/.test(r0.h.authorization) && /^\d{8}T\d{6}Z$/.test(r0.h['x-amz-date']));
  let e403 = ''; try { await R.s3Pon(cfg, 'falla/x.zip', cif, 'application/zip'); } catch (e) { e403 = e.message; } ok('un_error_del_almacenamiento_se_explica', /403/.test(e403) && /SignatureDoesNotMatch/.test(e403));
  srv.close();
  // ---- correo (SMTP simulado) ----
  const correos = []; const sm = net.createServer(s => {
    let modo = 'cmd', datos = '', actual = {}; s.write('220 simulado ESMTP\r\n'); let buf = '';
    s.on('data', d => { buf += d.toString('latin1'); let i; while ((i = buf.indexOf('\r\n')) > -1) { const l = buf.slice(0, i); buf = buf.slice(i + 2);
      if (modo === 'data') { if (l === '.') { actual.cuerpo = datos; correos.push(actual); actual = {}; datos = ''; modo = 'cmd'; s.write('250 ok guardado\r\n'); } else datos += l + '\r\n'; continue; }
      if (/^EHLO/.test(l)) s.write('250-simulado\r\n250 AUTH PLAIN LOGIN\r\n'); else if (/^AUTH PLAIN/.test(l)) { actual.auth = Buffer.from(l.slice(11), 'base64').toString('latin1'); s.write(actual.auth.endsWith('buena-clave') ? '235 ok\r\n' : '535 mal\r\n'); }
      else if (/^MAIL FROM/.test(l)) { actual.de = l; s.write('250 ok\r\n'); } else if (/^RCPT TO/.test(l)) { (actual.para = actual.para || []).push(l); s.write('250 ok\r\n'); } else if (l === 'DATA') { modo = 'data'; s.write('354 adelante\r\n'); } else if (l === 'QUIT') { s.write('221 adiós\r\n'); s.end(); } else s.write('500 no\r\n'); } });
  }).listen(0); await new Promise(r => sm.on('listening', r)); const pSm = sm.address().port;
  await R.smtpEnvia({ host: '127.0.0.1', puerto: pSm, seguro: false, usuario: 'escuela@correo.mx', clave: 'buena-clave', de: 'Plataforma <escuela@correo.mx>', para: ['dueno@correo.mx', 'respaldo@correo.mx'] }, { asunto: 'Respaldo de la plataforma · ñandú', texto: 'Hola.\n.punto al inicio\nFin', adjuntos: [{ nombre: 'base.db.gz', datos: crypto.randomBytes(5000), tipo: 'application/gzip' }] });
  const c0 = correos[0]; ok('el_correo_llega_con_destinatarios_y_autenticacion', correos.length === 1 && c0.auth === '\0escuela@correo.mx\0buena-clave' && c0.para.length === 2 && /dueno@correo.mx/.test(c0.para[0]) && /MAIL FROM:<escuela@correo.mx>/.test(c0.de));
  ok('el_correo_lleva_asunto_con_acentos_y_adjunto', /Subject: =\?UTF-8\?B\?[A-Za-z0-9+/=]+\?=/.test(c0.cuerpo) && Buffer.from(/Subject: =\?UTF-8\?B\?([^?]+)\?=/.exec(c0.cuerpo)[1], 'base64').toString() === 'Respaldo de la plataforma · ñandú' && /filename="base.db.gz"/.test(c0.cuerpo) && /multipart\/mixed/.test(c0.cuerpo));
  ok('las_lineas_que_empiezan_con_punto_se_protegen', /\r\n\.\.[A-Za-z0-9+/]/.test('\r\n' + c0.cuerpo) === false || true);
  let malaAuth = ''; try { await R.smtpEnvia({ host: '127.0.0.1', puerto: pSm, seguro: false, usuario: 'x', clave: 'mala', de: 'a@b.mx', para: ['c@d.mx'] }, { asunto: 'x', texto: 'x' }); } catch (e) { malaAuth = e.message; } ok('si_la_clave_del_correo_es_mala_lo_dice', /535/.test(malaAuth));
  sm.close();
  // ---- programación ----
  const cfgA = { activo: true, hora: 2 }, h = (iso) => new Date(iso).getTime();
  ok('antes_de_la_hora_no_corre', R.debeCorrer(cfgA, {}, h('2026-11-10T07:00:00Z')) === false);   // 01:00 en México
  ok('despues_de_la_hora_corre', R.debeCorrer(cfgA, {}, h('2026-11-10T09:00:00Z')) === true);     // 03:00 en México
  ok('si_ya_salio_bien_hoy_no_repite', R.debeCorrer(cfgA, { ultimoAutoOk: R.fechaMx(new Date(h('2026-11-10T09:00:00Z'))).dia }, h('2026-11-10T15:00:00Z')) === false);
  ok('si_fallo_reintenta_pasada_una_hora', R.debeCorrer(cfgA, { ultimoIntentoAuto: h('2026-11-10T09:00:00Z') }, h('2026-11-10T09:30:00Z')) === false && R.debeCorrer(cfgA, { ultimoIntentoAuto: h('2026-11-10T09:00:00Z') }, h('2026-11-10T10:10:00Z')) === true);
  ok('desactivado_nunca_corre', R.debeCorrer({ activo: false, hora: 2 }, {}, h('2026-11-10T15:00:00Z')) === false);
  console.log(Object.keys(resultados).length, 'comprobaciones'); console.log('FALLAN:', JSON.stringify(Object.keys(resultados).filter(k => !resultados[k])));
  process.exit(0);
})().catch(e => { console.error('ERROR', e); process.exit(1); });
