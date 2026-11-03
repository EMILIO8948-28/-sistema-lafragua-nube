'use strict';
/* ===========================================================================
   Sistema escolar Universidad Lafragua · versión para la NUBE
   Servidor Node.js sin dependencias: base SQLite, usuarios y sesiones propios,
   permisos por rol en el servidor, respaldos y cabeceras de seguridad.
   Requiere Node.js 22.13 o más nuevo y un disco persistente (DATA_DIR).
   =========================================================================== */
const http = require('http'), fs = require('fs'), path = require('path'), crypto = require('crypto'), https = require('https'), zlib = require('zlib');
let DatabaseSync;
try { ({ DatabaseSync } = require('node:sqlite')); }
catch (e) { console.error('Este programa necesita Node.js 22.13 o más nuevo.'); process.exit(1); }

const ENV = process.env, RAIZ = __dirname;
const PUERTO = parseInt(ENV.PORT || '3000', 10);
const DATOS = ENV.DATA_DIR ? path.resolve(ENV.DATA_DIR) : path.join(RAIZ, 'datos');
const ARCH = path.join(DATOS, 'archivos'), RESP = path.join(DATOS, 'respaldos'), TMP = path.join(DATOS, 'tmp'), PUB = path.join(RAIZ, 'publico');
const URL_PUBLICA = ENV.LF_URL_PUBLICA || '';
const CONFIAR_PROXY = ENV.LF_TRUST_PROXY !== '0';
const COOKIE_SEGURA = ENV.LF_COOKIE_SECURE === '1';
const PERMITIR_RECUPERACION = ENV.LF_PERMITIR_RECUPERACION === '1';
const CONSERVAR = parseInt(ENV.LF_RESPALDOS_CONSERVAR || '14', 10);
const IDLE_MS = 12 * 3600 * 1000, ABS_MS = 7 * 24 * 3600 * 1000;
[DATOS, ARCH, RESP, TMP].forEach(d => fs.mkdirSync(d, { recursive: true }));

const db = new DatabaseSync(path.join(DATOS, 'lafragua.db'));
db.exec('PRAGMA journal_mode = WAL; PRAGMA synchronous = FULL;');
db.exec(`
CREATE TABLE IF NOT EXISTS docs (coleccion TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, actualizado INTEGER NOT NULL, PRIMARY KEY (coleccion, id));
CREATE TABLE IF NOT EXISTS archivos (id TEXT PRIMARY KEY, nombre TEXT, tipo TEXT, tamano INTEGER, creado INTEGER);
CREATE TABLE IF NOT EXISTS usuarios (u TEXT PRIMARY KEY, nombre TEXT NOT NULL, rol TEXT NOT NULL, doc TEXT, salt TEXT NOT NULL, hash TEXT NOT NULL, creado INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sesiones (token TEXT PRIMARY KEY, u TEXT NOT NULL, creado INTEGER NOT NULL, expira INTEGER NOT NULL, ultimo INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha INTEGER NOT NULL, u TEXT, ip TEXT, accion TEXT NOT NULL, detalle TEXT);
`);
const q = {
  lista: db.prepare('SELECT id, data FROM docs WHERE coleccion = ? ORDER BY id'),
  uno: db.prepare('SELECT data FROM docs WHERE coleccion = ? AND id = ?'),
  pon: db.prepare('INSERT INTO docs (coleccion, id, data, actualizado) VALUES (?, ?, ?, ?) ON CONFLICT(coleccion, id) DO UPDATE SET data = excluded.data, actualizado = excluded.actualizado'),
  borra: db.prepare('DELETE FROM docs WHERE coleccion = ? AND id = ?'),
  ponArch: db.prepare('INSERT INTO archivos (id, nombre, tipo, tamano, creado) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET nombre = excluded.nombre, tipo = excluded.tipo, tamano = excluded.tamano'),
  uArch: db.prepare('SELECT nombre, tipo, tamano FROM archivos WHERE id = ?'),
  bArch: db.prepare('DELETE FROM archivos WHERE id = ?'),
  todosArch: db.prepare('SELECT id, nombre FROM archivos ORDER BY id'),
  cuenta: db.prepare('SELECT coleccion, COUNT(*) AS n FROM docs GROUP BY coleccion ORDER BY coleccion'),
  usr: db.prepare('SELECT * FROM usuarios WHERE u = ?'),
  usrs: db.prepare('SELECT u, nombre, rol, doc FROM usuarios ORDER BY nombre'),
  nUsr: db.prepare('SELECT COUNT(*) AS n FROM usuarios'),
  nAdm: db.prepare("SELECT COUNT(*) AS n FROM usuarios WHERE rol = 'admin'"),
  admins: db.prepare("SELECT * FROM usuarios WHERE rol = 'admin'"),
  insUsr: db.prepare('INSERT INTO usuarios (u, nombre, rol, doc, salt, hash, creado) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(u) DO UPDATE SET nombre = excluded.nombre, rol = excluded.rol, doc = excluded.doc, salt = excluded.salt, hash = excluded.hash'),
  updUsr: db.prepare('UPDATE usuarios SET nombre = ?, rol = ?, doc = ? WHERE u = ?'),
  borUsr: db.prepare('DELETE FROM usuarios WHERE u = ?'),
  insSes: db.prepare('INSERT INTO sesiones (token, u, creado, expira, ultimo) VALUES (?, ?, ?, ?, ?)'),
  getSes: db.prepare('SELECT * FROM sesiones WHERE token = ?'),
  tocaSes: db.prepare('UPDATE sesiones SET ultimo = ? WHERE token = ?'),
  borSes: db.prepare('DELETE FROM sesiones WHERE token = ?'),
  borSesU: db.prepare('DELETE FROM sesiones WHERE u = ?'),
  borSesUmenos: db.prepare('DELETE FROM sesiones WHERE u = ? AND token <> ?'),
  limpiaSes: db.prepare('DELETE FROM sesiones WHERE expira < ?'),
  audit: db.prepare('INSERT INTO auditoria (fecha, u, ip, accion, detalle) VALUES (?, ?, ?, ?, ?)'),
  auditoria: db.prepare('SELECT fecha, u, ip, accion, detalle FROM auditoria ORDER BY id DESC LIMIT 200')
};

/* ---------- Utilidades ---------- */
const hoy = () => { const d = new Date(), p = n => String(n).padStart(2, '0'); return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()); };
const dormir = ms => new Promise(r => setTimeout(r, ms));
const NOMBRE_OK = /^[A-Za-z0-9_.@+:~-]{1,200}$/, ID_ARCH = /^[0-9a-f]{32}$/, USUARIO_OK = /^[a-z0-9._-]{3,40}$/;
const ROLES = ['admin', 'caja', 'consulta', 'docente'];
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon' };
const clientes = new Set();
function ipDe(req) { if (CONFIAR_PROXY && req.headers['x-forwarded-for']) return String(req.headers['x-forwarded-for']).split(',')[0].trim(); return req.socket.remoteAddress || ''; }
function audita(u, req, accion, detalle) { try { q.audit.run(Date.now(), u || null, req ? ipDe(req) : null, accion, detalle ? String(detalle).slice(0, 400) : null); } catch (e) {} }
function responde(res, cod, obj) { const b = Buffer.from(JSON.stringify(obj)); res.writeHead(cod, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': b.length, 'Cache-Control': 'no-store' }); res.end(b); }
function leeCuerpo(req, max) {
  return new Promise((ok, mal) => {
    const trozos = []; let n = 0;
    let cortado = false;
    req.on('data', c => { if (cortado) return; n += c.length; if (n > max) { cortado = true; trozos.length = 0; mal(Object.assign(new Error('Archivo demasiado grande'), { cod: 413 })); } else trozos.push(c); });
    req.on('end', () => ok(Buffer.concat(trozos))); req.on('error', mal);
  });
}
async function leeJSON(req, max) { try { const o = JSON.parse((await leeCuerpo(req, max || 100000)).toString('utf8') || '{}'); return o && typeof o === 'object' ? o : {}; } catch (e) { if (e.cod) throw e; return {}; } }
function cookies(req) { const o = {}; String(req.headers.cookie || '').split(';').forEach(p => { const i = p.indexOf('='); if (i > 0) o[p.slice(0, i).trim()] = p.slice(i + 1).trim(); }); return o; }
const sha = t => crypto.createHash('sha256').update(t).digest('hex');

/* ---------- Contraseñas y sesiones ---------- */
function hashClave(clave, salt) { return crypto.scryptSync(String(clave), salt, 64, { N: 16384, r: 8, p: 1 }).toString('hex'); }
function claveOk(clave, u) { const a = Buffer.from(hashClave(clave, u.salt), 'hex'), b = Buffer.from(u.hash, 'hex'); return a.length === b.length && crypto.timingSafeEqual(a, b); }
function validaClave(c, u) { if (typeof c !== 'string' || c.length < 8) return 'La contraseña debe tener al menos 8 caracteres.'; if (c.length > 200) return 'La contraseña es demasiado larga.'; if (u && c.toLowerCase() === u) return 'La contraseña no puede ser igual al usuario.'; return ''; }
function esSegura(req) { return COOKIE_SEGURA || (CONFIAR_PROXY && String(req.headers['x-forwarded-proto'] || '').split(',')[0].trim() === 'https'); }
function ponCookie(req, res, token, maxAge) { res.setHeader('Set-Cookie', 'lf_sid=' + token + '; HttpOnly; SameSite=Lax; Path=/; Max-Age=' + maxAge + (esSegura(req) ? '; Secure' : '')); }
function nuevaSesion(req, res, u) {
  const t = crypto.randomBytes(32).toString('hex'), ahora = Date.now();
  q.insSes.run(sha(t), u, ahora, ahora + ABS_MS, ahora); ponCookie(req, res, t, Math.floor(ABS_MS / 1000)); return t;
}
function sesionDe(req) {
  const t = cookies(req).lf_sid; if (!t || !/^[0-9a-f]{64}$/.test(t)) return null;
  const s = q.getSes.get(sha(t)), ahora = Date.now(); if (!s) return null;
  if (s.expira < ahora || ahora - s.ultimo > IDLE_MS) { q.borSes.run(s.token); return null; }
  const u = q.usr.get(s.u); if (!u) { q.borSes.run(s.token); return null; }
  if (ahora - s.ultimo > 60000) q.tocaSes.run(ahora, s.token);
  return { u: u.u, name: u.nombre, rol: u.rol, doc: u.doc || '', _token: s.token };
}
const intentos = new Map();
function limite(clave, max, ventanaMs) { const a = intentos.get(clave), ahora = Date.now(); if (!a || ahora - a.desde > ventanaMs) return false; return a.n >= max; }
function falla(clave, ventanaMs) { const a = intentos.get(clave), ahora = Date.now(); if (!a || ahora - a.desde > ventanaMs) intentos.set(clave, { n: 1, desde: ahora }); else a.n++; }
setInterval(() => { const ahora = Date.now(); intentos.forEach((v, k) => { if (ahora - v.desde > 3600000) intentos.delete(k); }); q.limpiaSes.run(ahora); }, 600000).unref();
const publicoUsuario = u => ({ u: u.u, name: u.nombre || u.name, rol: u.rol, doc: u.doc || '' });
const listaUsuarios = () => q.usrs.all().map(x => ({ u: x.u, name: x.nombre, rol: x.rol, doc: x.doc || '' }));

/* ---------- Permisos por rol (se aplican aquí, no solo en la pantalla) ---------- */
const COL_LEE = {
  caja: ['students', 'ledger', 'fotos', 'grupos', 'materias', 'calif', 'catalogo', 'contenidos', 'egresados', 'acuerdos', 'constancias', 'gastos', 'cortes', 'criterios', 'justificantes', 'docentes', 'meta', 'config'],
  consulta: ['students', 'ledger', 'fotos', 'grupos', 'materias', 'calif', 'catalogo', 'contenidos', 'egresados', 'constancias', 'criterios', 'justificantes', 'docentes', 'config'],
  docente: ['students', 'grupos', 'materias', 'docentes', 'calif', 'criterios', 'catalogo', 'contenidos', 'config']
};
const COL_ESC = { caja: ['ledger', 'gastos', 'cortes', 'acuerdos', 'constancias', 'meta'], consulta: [], docente: ['calif', 'criterios'] };
function puedeLeer(rol, col, id) {
  if (col === 'config' && id === 'users') return false;
  if (rol === 'admin') return true;
  if (col === 'config') { if (id === 'nomina') return false; if (id === 'plans') return rol !== 'docente'; return true; }
  return (COL_LEE[rol] || []).includes(col);
}
function puedeEscribir(rol, col, id) {
  if (col === 'config' && id === 'users') return false;
  if (rol === 'admin') return true;
  return (COL_ESC[rol] || []).includes(col);
}
const CAMPOS_DOCENTE = ['mat', 'nombre', 'carrera', 'programa', 'ingreso', 'sexo', 'nuevo'];
function reduce(rol, col, data) { if (rol !== 'docente' || col !== 'students') return data; const o = {}; CAMPOS_DOCENTE.forEach(k => { if (data[k] !== undefined) o[k] = data[k]; }); return o; }

/* ---------- Eventos en tiempo real ---------- */
function difunde(c, id) { const m = 'data: ' + JSON.stringify({ c, id }) + '\n\n'; clientes.forEach(cl => { if (!puedeLeer(cl.rol, c, id)) return; try { cl.res.write(m); } catch (e) { clientes.delete(cl); } }); }
const candados = new Map();

/* ---------- Respaldos ---------- */
function respaldar() {
  const dir = path.join(RESP, hoy()); fs.mkdirSync(dir, { recursive: true });
  const dest = path.join(dir, 'lafragua.db'); if (fs.existsSync(dest)) fs.unlinkSync(dest);
  db.exec("VACUUM INTO '" + dest.replace(/'/g, "''") + "'");
  const dias = fs.readdirSync(RESP).filter(n => /^\d{4}-\d{2}-\d{2}$/.test(n)).sort().reverse();
  dias.slice(Math.max(1, CONSERVAR)).forEach(n => fs.rmSync(path.join(RESP, n), { recursive: true, force: true }));
  return dir;
}
function respaldoDiario() { try { if (!fs.existsSync(path.join(RESP, hoy(), 'lafragua.db'))) console.log('Respaldo automático en', respaldar()); } catch (e) { console.error('No se pudo hacer el respaldo automático:', e.message); } }

/* ---------- ZIP (sin compresión) para descargar el respaldo completo ---------- */
function dosFecha(d) { return [((d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1)) & 0xffff, (((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate()) & 0xffff]; }
async function enviaZip(res, nombreZip, entradas) {
  res.writeHead(200, { 'Content-Type': 'application/zip', 'Content-Disposition': 'attachment; filename="' + nombreZip + '"', 'Cache-Control': 'no-store' });
  const escribe = b => new Promise(ok => { if (res.write(b)) ok(); else res.once('drain', ok); });
  let desp = 0; const central = [], [hora, fecha] = dosFecha(new Date());
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
  res.end(fin);
}
async function respaldoCompleto(res) {
  const tmp = path.join(TMP, 'dl-' + crypto.randomBytes(6).toString('hex') + '.db');
  db.exec("VACUUM INTO '" + tmp.replace(/'/g, "''") + "'");
  const entradas = [{ nombre: 'lafragua.db', ruta: tmp }], indice = [];
  q.todosArch.all().forEach(a => { const ruta = path.join(ARCH, a.id); if (!fs.existsSync(ruta)) return; const nom = 'archivos/' + a.id + '-' + String(a.nombre || 'archivo').replace(/[^\w.\- áéíóúñÁÉÍÓÚÑ]/g, '_'); entradas.push({ nombre: nom, ruta }); indice.push({ id: a.id, archivo: nom, nombre: a.nombre, origen: '' }); });
  entradas.push({ nombre: 'indice-1.json', datos: Buffer.from(JSON.stringify(indice)) });
  try { await enviaZip(res, 'respaldo-completo-' + hoy() + '.zip', entradas); } finally { try { fs.unlinkSync(tmp); } catch (e) {} }
}

/* ---------- Librerías de PDF y Excel (se descargan una vez si faltan) ---------- */
const LIBS = [['jspdf.umd.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'], ['xlsx.full.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js']];
function descarga(url, dest, saltos) {
  return new Promise((ok, mal) => {
    https.get(url, r => {
      if ([301, 302, 307, 308].includes(r.statusCode) && r.headers.location && (saltos || 0) < 4) { r.resume(); return descarga(r.headers.location, dest, (saltos || 0) + 1).then(ok, mal); }
      if (r.statusCode !== 200) { r.resume(); return mal(new Error('estado ' + r.statusCode)); }
      const t = dest + '.tmp', w = fs.createWriteStream(t); r.pipe(w); w.on('finish', () => { fs.renameSync(t, dest); ok(); }); w.on('error', mal);
    }).on('error', mal).setTimeout(20000, function () { this.destroy(new Error('sin respuesta')); });
  });
}
async function aseguraLibs() { for (const [n, u] of LIBS) { const d = path.join(PUB, 'lib', n); if (fs.existsSync(d)) continue; try { await descarga(u, d); console.log('Librería descargada:', n); } catch (e) { console.log('No se pudo descargar ' + n + ' (' + e.message + '); se usará internet desde el navegador.'); } } }

/* ---------- Cabeceras de seguridad ---------- */
const CSP = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob:; connect-src 'self'; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'";
function cabeceras(req, res) {
  const base = { 'Content-Security-Policy': CSP, 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'same-origin', 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()' };
  if (esSegura(req)) base['Strict-Transport-Security'] = 'max-age=31536000';
  const wh = res.writeHead.bind(res); res.writeHead = (cod, h) => wh(cod, Object.assign({}, base, h || {}));
}

/* ---------- API ---------- */
function origenOk(req) {
  if (!req.headers.origin) return true; let o; try { o = new URL(req.headers.origin).host; } catch (e) { return false; }
  if (o === req.headers.host) return true;
  if (URL_PUBLICA) { try { return o === new URL(URL_PUBLICA).host; } catch (e) {} }
  return false;
}
function tokenSetupOk(t) { const esp = ENV.LF_SETUP_TOKEN || SETUP_AUTO; if (typeof t !== 'string' || !esp) return false; const a = Buffer.from(t), b = Buffer.from(esp); return a.length === b.length && crypto.timingSafeEqual(a, b); }
let SETUP_AUTO = '';

async function api(req, res, partes) {
  const m = req.method, [tipo, a, b] = partes, ip = ipDe(req);
  if (m !== 'GET' && !req.headers['x-lafragua']) return responde(res, 403, { error: 'Solicitud no permitida' });
  if (!origenOk(req)) return responde(res, 403, { error: 'Origen no permitido' });

  /* --- públicas --- */
  if (tipo === 'yo' && m === 'GET') {
    const s = sesionDe(req), hay = q.nUsr.get().n > 0;
    return responde(res, 200, { modo: 'nube', setup: !hay, usuario: s ? publicoUsuario(s) : null, usuarios: s ? (s.rol === 'admin' ? listaUsuarios() : [publicoUsuario(s)]) : [{ u: '_', name: '', rol: 'consulta', doc: '' }] });
  }
  if (tipo === 'login' && m === 'POST') {
    const c = await leeJSON(req), u = String(c.u || '').trim().toLowerCase(), clave = typeof c.clave === 'string' ? c.clave : '';
    if (limite('ip|' + ip, 30, 900000) || limite('u|' + ip + '|' + u, 5, 900000)) { audita(u, req, 'Inicio de sesión bloqueado por intentos'); return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos e inténtalo de nuevo.' }); }
    const usr = USUARIO_OK.test(u) ? q.usr.get(u) : null;
    let ok = false;
    if (usr) ok = claveOk(clave, usr); else hashClave(clave, 'sin-usuario-sal');
    if (!ok) { falla('ip|' + ip, 900000); falla('u|' + ip + '|' + u, 900000); audita(u, req, 'Inicio de sesión fallido'); await dormir(400); return responde(res, 401, { error: 'Usuario o contraseña incorrectos.' }); }
    intentos.delete('u|' + ip + '|' + u); nuevaSesion(req, res, usr.u); audita(usr.u, req, 'Inicio de sesión');
    return responde(res, 200, { usuario: publicoUsuario(usr) });
  }
  if (tipo === 'configurar' && m === 'POST') {
    const c = await leeJSON(req), hay = q.nUsr.get().n > 0;
    if (hay && !PERMITIR_RECUPERACION) return responde(res, 403, { error: 'El sistema ya está configurado.' });
    if (limite('cfg|' + ip, 8, 900000)) return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos.' });
    if (!tokenSetupOk(c.token)) { falla('cfg|' + ip, 900000); audita(null, req, 'Configuración inicial rechazada (código incorrecto)'); await dormir(400); return responde(res, 403, { error: 'El código de configuración no es correcto.' }); }
    const u = String(c.u || '').trim().toLowerCase(), nombre = String(c.name || '').trim().slice(0, 80), err = validaClave(c.clave, u);
    if (!USUARIO_OK.test(u)) return responde(res, 400, { error: 'El usuario solo puede llevar letras sin acentos, números, punto, guion y guion bajo (3 a 40 caracteres).' });
    if (!nombre) return responde(res, 400, { error: 'Escribe el nombre.' });
    if (err) return responde(res, 400, { error: err });
    const salt = crypto.randomBytes(16).toString('hex'); q.insUsr.run(u, nombre, 'admin', '', salt, hashClave(c.clave, salt), Date.now());
    audita(u, req, hay ? 'Administrador restablecido por recuperación' : 'Configuración inicial: administrador creado'); nuevaSesion(req, res, u);
    return responde(res, 200, { ok: true });
  }

  /* --- requieren sesión --- */
  const s = sesionDe(req);
  if (!s) return responde(res, 401, { error: 'Sesión requerida' });
  const rol = s.rol;

  if (tipo === 'logout' && m === 'POST') { q.borSes.run(s._token); ponCookie(req, res, '', 0); audita(s.u, req, 'Cierre de sesión'); return responde(res, 200, { ok: true }); }

  if (tipo === 'eventos' && m === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive' });
    res.write('retry: 2000\n\n'); const cl = { res, rol }; clientes.add(cl); req.on('close', () => clientes.delete(cl)); return;
  }
  if (tipo === 'col' && m === 'GET' && NOMBRE_OK.test(a || '')) {
    if (!puedeLeer(rol, a, null)) return responde(res, 200, { docs: [] });
    return responde(res, 200, { docs: q.lista.all(a).map(r => ({ id: r.id, data: reduce(rol, a, JSON.parse(r.data)) })) });
  }
  if (tipo === 'doc' && NOMBRE_OK.test(a || '') && NOMBRE_OK.test(b || '')) {
    if (m === 'GET') { if (!puedeLeer(rol, a, b)) return responde(res, 200, { exists: false, data: null }); const r = q.uno.get(a, b); return responde(res, 200, r ? { exists: true, data: reduce(rol, a, JSON.parse(r.data)) } : { exists: false, data: null }); }
    if (m === 'PUT' || m === 'PATCH' || m === 'DELETE') {
      if (!puedeEscribir(rol, a, b)) { audita(s.u, req, 'Escritura denegada', m + ' ' + a + '/' + b); return responde(res, 403, { error: 'No tienes permiso para hacer esto.' }); }
      if (m === 'DELETE') { q.borra.run(a, b); difunde(a, b); return responde(res, 200, { ok: true }); }
      let cuerpo; try { cuerpo = JSON.parse((await leeCuerpo(req, 6 * 1024 * 1024)).toString('utf8') || '{}'); } catch (e) { if (e.cod) throw e; return responde(res, 400, { error: 'JSON no válido' }); }
      if (cuerpo === null || typeof cuerpo !== 'object' || Array.isArray(cuerpo)) return responde(res, 400, { error: 'Se esperaba un objeto' });
      let nuevo = cuerpo; if (m === 'PATCH') { const r = q.uno.get(a, b); nuevo = Object.assign(r ? JSON.parse(r.data) : {}, cuerpo); }
      q.pon.run(a, b, JSON.stringify(nuevo), Date.now()); difunde(a, b); return responde(res, 200, { ok: true });
    }
  }
  if (tipo === 'lock' && m === 'POST' && NOMBRE_OK.test(a || '') && NOMBRE_OK.test(b || '')) {
    if (!puedeEscribir(rol, a, b)) return responde(res, 403, { error: 'No tienes permiso para hacer esto.' });
    const c = await leeJSON(req, 10000), k = a + '/' + b, ahora = Date.now(), v = candados.get(k);
    if (!v || v.exp < ahora || v.holder === c.holder) { candados.set(k, { holder: String(c.holder || ''), exp: ahora + Math.min(Number(c.ttlMs) || 4000, 30000) }); return responde(res, 200, { acquired: true }); }
    return responde(res, 200, { acquired: false });
  }
  if (tipo === 'archivo') {
    if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador puede subir o quitar archivos.' });
    const nombre = () => decodeURIComponent(String(req.headers['x-nombre'] || 'archivo')).slice(0, 200), mime = () => String(req.headers['content-type'] || 'application/octet-stream').slice(0, 100);
    if (m === 'POST' && !a) { const buf = await leeCuerpo(req, 26 * 1024 * 1024), id = crypto.randomBytes(16).toString('hex'); fs.writeFileSync(path.join(ARCH, id), buf); q.ponArch.run(id, nombre(), mime(), buf.length, Date.now()); return responde(res, 200, { id, sizeBytes: buf.length }); }
    if (ID_ARCH.test(a || '')) {
      if (m === 'PUT') { const buf = await leeCuerpo(req, 26 * 1024 * 1024); fs.writeFileSync(path.join(ARCH, a), buf); q.ponArch.run(a, nombre(), mime(), buf.length, Date.now()); return responde(res, 200, { id: a, sizeBytes: buf.length }); }
      if (m === 'DELETE') { try { fs.unlinkSync(path.join(ARCH, a)); } catch (e) {} q.bArch.run(a); return responde(res, 200, { ok: true }); }
    }
  }

  /* --- usuarios y seguridad --- */
  if (tipo === 'usuarios') {
    if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador puede administrar usuarios.' });
    if (m === 'GET' && !a) return responde(res, 200, { usuarios: listaUsuarios() });
    if (m === 'POST' && !a) {
      const c = await leeJSON(req), u = String(c.u || '').trim().toLowerCase(), nombre = String(c.name || '').trim().slice(0, 80), r = String(c.rol || ''), doc = String(c.doc || '');
      if (!USUARIO_OK.test(u)) return responde(res, 400, { error: 'El usuario solo puede llevar letras sin acentos, números, punto, guion y guion bajo (3 a 40 caracteres).' });
      if (!nombre) return responde(res, 400, { error: 'Escribe el nombre.' });
      if (!ROLES.includes(r)) return responde(res, 400, { error: 'Rol no válido.' });
      if (r === 'docente' && !doc) return responde(res, 400, { error: 'Elige el docente al que pertenece este usuario.' });
      const ex = q.usr.get(u);
      if (ex && ex.rol === 'admin' && r !== 'admin' && q.nAdm.get().n < 2) return responde(res, 400, { error: 'Debe quedar al menos un administrador.' });
      if (!ex || c.clave) { const err = validaClave(c.clave, u); if (err) return responde(res, 400, { error: err }); }
      if (!ex) { const salt = crypto.randomBytes(16).toString('hex'); q.insUsr.run(u, nombre, r, r === 'docente' ? doc : '', salt, hashClave(c.clave, salt), Date.now()); audita(s.u, req, 'Usuario creado', u + ' (' + r + ')'); }
      else {
        q.updUsr.run(nombre, r, r === 'docente' ? doc : '', u);
        if (c.clave) { const salt = crypto.randomBytes(16).toString('hex'); q.insUsr.run(u, nombre, r, r === 'docente' ? doc : '', salt, hashClave(c.clave, salt), ex.creado); q.borSesU.run(u); }
        audita(s.u, req, 'Usuario modificado', u + ' (' + r + ')' + (c.clave ? ' · nueva contraseña' : ''));
      }
      return responde(res, 200, { usuarios: listaUsuarios() });
    }
    if (m === 'DELETE' && a) {
      const ex = q.usr.get(String(a).toLowerCase()); if (!ex) return responde(res, 404, { error: 'No existe ese usuario.' });
      if (ex.u === s.u) return responde(res, 400, { error: 'No puedes eliminar tu propio usuario.' });
      if (ex.rol === 'admin' && q.nAdm.get().n < 2) return responde(res, 400, { error: 'Debe quedar al menos un administrador.' });
      q.borUsr.run(ex.u); q.borSesU.run(ex.u); audita(s.u, req, 'Usuario eliminado', ex.u); return responde(res, 200, { usuarios: listaUsuarios() });
    }
  }
  if (tipo === 'cambiar-clave' && m === 'POST') {
    const c = await leeJSON(req), usr = q.usr.get(s.u);
    if (limite('pw|' + s.u, 5, 900000)) return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos.' });
    if (!claveOk(String(c.actual || ''), usr)) { falla('pw|' + s.u, 900000); await dormir(400); return responde(res, 400, { error: 'La contraseña actual no es correcta.' }); }
    const err = validaClave(c.nueva, s.u); if (err) return responde(res, 400, { error: err });
    const salt = crypto.randomBytes(16).toString('hex'); q.insUsr.run(s.u, usr.nombre, usr.rol, usr.doc, salt, hashClave(c.nueva, salt), usr.creado); q.borSesUmenos.run(s.u, s._token);
    audita(s.u, req, 'Cambió su contraseña'); return responde(res, 200, { ok: true });
  }
  if (tipo === 'autoriza-admin' && m === 'POST') {
    if (rol !== 'admin' && rol !== 'caja') return responde(res, 403, { error: 'No tienes permiso para hacer esto.' });
    const c = await leeJSON(req), adm = q.admins.all();
    if (!adm.length) return responde(res, 409, { error: 'No hay un usuario administrador configurado.' });
    if (limite('aut|' + s.u, 5, 900000)) return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos.' });
    const hit = adm.find(x => claveOk(String(c.clave || ''), x));
    if (!hit) { falla('aut|' + s.u, 900000); audita(s.u, req, 'Autorización de administrador fallida'); await dormir(400); return responde(res, 403, { error: 'Contraseña de administrador incorrecta.' }); }
    audita(s.u, req, 'Autorización de administrador', 'autorizó: ' + hit.u + (c.motivo ? ' · ' + String(c.motivo).slice(0, 120) : '')); return responde(res, 200, { ok: true, nombre: hit.nombre });
  }
  if (tipo === 'auditoria' && m === 'GET') { if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador.' }); return responde(res, 200, { registros: q.auditoria.all().map(r => ({ fecha: new Date(r.fecha).toISOString(), u: r.u, ip: r.ip, accion: r.accion, detalle: r.detalle })) }); }
  if (tipo === 'respaldo') {
    if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador.' });
    if (m === 'POST' && !a) { try { const d = respaldar(); audita(s.u, req, 'Respaldo manual en el servidor'); return responde(res, 200, { ok: true, carpeta: d }); } catch (e) { return responde(res, 500, { error: e.message }); } }
    if (m === 'GET' && a === 'descargar') { audita(s.u, req, 'Descargó el respaldo completo'); try { await respaldoCompleto(res); } catch (e) { console.error(e.message); try { res.end(); } catch (x) {} } return; }
  }
  if (tipo === 'info' && m === 'GET') {
    if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador.' });
    let disco = 0; try { fs.readdirSync(ARCH).forEach(f => { disco += fs.statSync(path.join(ARCH, f)).size; }); } catch (e) {}
    let bd = 0; try { bd = fs.statSync(path.join(DATOS, 'lafragua.db')).size; } catch (e) {}
    return responde(res, 200, { colecciones: q.cuenta.all(), bytesArchivos: disco, bytesBaseDatos: bd, respaldos: fs.readdirSync(RESP).filter(n => /^\d{4}-\d{2}-\d{2}$/.test(n)).sort().reverse() });
  }
  return responde(res, 404, { error: 'No encontrado' });
}

const servidor = http.createServer(async (req, res) => {
  try {
    cabeceras(req, res);
    const url = new URL(req.url, 'http://localhost'), ruta = decodeURIComponent(url.pathname);
    if (ruta === '/salud') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end('ok'); }
    if (ruta.startsWith('/api/')) return await api(req, res, ruta.slice(5).split('/'));
    if (ruta === '/config-local.js') { res.writeHead(200, { 'Content-Type': 'text/javascript; charset=utf-8', 'Cache-Control': 'no-store' }); return res.end('window.LOCAL_APPURL=' + JSON.stringify(URL_PUBLICA || '') + ';'); }
    if (ruta.startsWith('/_blob/')) {
      if (!sesionDe(req)) { res.writeHead(401, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('Inicia sesión para ver este archivo.'); }
      const id = ruta.slice(7), f = path.join(ARCH, id);
      if (!ID_ARCH.test(id) || !fs.existsSync(f)) { res.writeHead(404); return res.end('No encontrado'); }
      const info = q.uArch.get(id) || {};
      res.writeHead(200, { 'Content-Type': info.tipo || 'application/octet-stream', 'Content-Disposition': "inline; filename*=UTF-8''" + encodeURIComponent(info.nombre || id), 'Cache-Control': 'private, no-store' });
      return fs.createReadStream(f).pipe(res);
    }
    const rel = ruta === '/' ? '/index.html' : (ruta === '/configurar' ? '/configurar.html' : ruta);
    const f = path.normalize(path.join(PUB, rel));
    if (!f.startsWith(PUB + path.sep) || !fs.existsSync(f) || !fs.statSync(f).isFile()) { res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('No encontrado'); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(f).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
    fs.createReadStream(f).pipe(res);
  } catch (e) {
    console.error('Error:', e.message);
    if (!res.headersSent) { if (e.cod === 413) res.setHeader('Connection', 'close'); responde(res, e.cod || 500, { error: e.cod === 413 ? 'El archivo es demasiado grande' : 'Error interno' }); } else try { res.end(); } catch (x) {}
  }
});
servidor.on('error', e => { console.error(e.code === 'EADDRINUSE' ? 'El puerto ' + PUERTO + ' ya está en uso.' : e); process.exit(1); });
servidor.listen(PUERTO, '0.0.0.0', () => {
  console.log('Sistema escolar Lafragua (nube) escuchando en el puerto ' + PUERTO + '. Datos en ' + DATOS);
  if (q.nUsr.get().n === 0) {
    if (!ENV.LF_SETUP_TOKEN) { SETUP_AUTO = crypto.randomBytes(9).toString('hex'); console.log('==> Aún no hay usuarios. Código de configuración inicial: ' + SETUP_AUTO + ' (usa la página /configurar)'); }
    else console.log('==> Aún no hay usuarios. Abre /configurar y usa el código de configuración de tus variables de entorno (LF_SETUP_TOKEN).');
  }
  respaldoDiario(); setInterval(respaldoDiario, 3600000).unref(); aseguraLibs();
});
function cierra() { try { respaldar(); } catch (e) {} try { db.close(); } catch (e) {} process.exit(0); }
process.on('SIGINT', cierra); process.on('SIGTERM', cierra);
