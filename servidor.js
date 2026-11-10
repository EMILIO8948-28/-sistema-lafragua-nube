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
CREATE TABLE IF NOT EXISTS usuarios (u TEXT PRIMARY KEY, nombre TEXT NOT NULL, rol TEXT NOT NULL, doc TEXT, salt TEXT NOT NULL, hash TEXT NOT NULL, creado INTEGER NOT NULL, modulos TEXT, alumno TEXT, forzar INTEGER NOT NULL DEFAULT 0, temporal TEXT);
CREATE TABLE IF NOT EXISTS sesiones (token TEXT PRIMARY KEY, u TEXT NOT NULL, creado INTEGER NOT NULL, expira INTEGER NOT NULL, ultimo INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha INTEGER NOT NULL, u TEXT, ip TEXT, accion TEXT NOT NULL, detalle TEXT);
`);
try { db.exec('ALTER TABLE archivos ADD COLUMN privado INTEGER NOT NULL DEFAULT 0'); } catch (e) { /* la columna ya existe */ }
try { db.exec('ALTER TABLE archivos ADD COLUMN dueno TEXT'); } catch (e) { /* la columna ya existe */ }
try { db.exec('ALTER TABLE archivos ADD COLUMN cat TEXT'); } catch (e) { /* la columna ya existe */ }
try { db.exec('ALTER TABLE usuarios ADD COLUMN modulos TEXT'); } catch (e) { /* la columna ya existe */ }
try { db.exec('ALTER TABLE usuarios ADD COLUMN temporal TEXT'); } catch (e) { /* la columna ya existe */ }
try { db.exec('ALTER TABLE usuarios ADD COLUMN alumno TEXT'); } catch (e) { /* la columna ya existe */ }
try { db.exec('ALTER TABLE usuarios ADD COLUMN forzar INTEGER NOT NULL DEFAULT 0'); } catch (e) { /* la columna ya existe */ }
for (const c of ['totp TEXT', 'totp_resp TEXT', 'totp_ult INTEGER']) { try { db.exec('ALTER TABLE usuarios ADD COLUMN ' + c); } catch (e) { /* la columna ya existe */ } }
db.exec(`CREATE TABLE IF NOT EXISTS borrados (id TEXT PRIMARY KEY, u TEXT NOT NULL, nombre TEXT, creado INTEGER NOT NULL, estado TEXT NOT NULL, via TEXT, descripcion TEXT NOT NULL, detalle TEXT, resuelto_por TEXT, resuelto INTEGER, motivo TEXT, expira INTEGER, ops TEXT)`);
db.exec('CREATE INDEX IF NOT EXISTS ix_borrados_estado ON borrados (estado, creado)');
const q = {
  lista: db.prepare('SELECT id, data FROM docs WHERE coleccion = ? ORDER BY id'),
  uno: db.prepare('SELECT data FROM docs WHERE coleccion = ? AND id = ?'),
  pon: db.prepare('INSERT INTO docs (coleccion, id, data, actualizado) VALUES (?, ?, ?, ?) ON CONFLICT(coleccion, id) DO UPDATE SET data = excluded.data, actualizado = excluded.actualizado'),
  borra: db.prepare('DELETE FROM docs WHERE coleccion = ? AND id = ?'),
  ponArch: db.prepare('INSERT INTO archivos (id, nombre, tipo, tamano, creado, privado, dueno, cat) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET nombre = excluded.nombre, tipo = excluded.tipo, tamano = excluded.tamano, privado = excluded.privado'),
  uArch: db.prepare('SELECT nombre, tipo, tamano, privado, dueno, cat FROM archivos WHERE id = ?'),
  bArch: db.prepare('DELETE FROM archivos WHERE id = ?'),
  todosArch: db.prepare('SELECT id, nombre, privado FROM archivos ORDER BY id'),
  cuenta: db.prepare('SELECT coleccion, COUNT(*) AS n FROM docs GROUP BY coleccion ORDER BY coleccion'),
  usr: db.prepare('SELECT * FROM usuarios WHERE u = ?'),
  usrs: db.prepare('SELECT u, nombre, rol, doc, modulos, alumno, forzar, (temporal IS NOT NULL) AS tmp, (totp IS NOT NULL) AS dos FROM usuarios ORDER BY nombre'),
  nUsr: db.prepare('SELECT COUNT(*) AS n FROM usuarios'),
  nAdm: db.prepare("SELECT COUNT(*) AS n FROM usuarios WHERE rol = 'admin'"),
  admins: db.prepare("SELECT * FROM usuarios WHERE rol = 'admin'"),
  insUsr: db.prepare('INSERT INTO usuarios (u, nombre, rol, doc, salt, hash, creado, modulos) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(u) DO UPDATE SET nombre = excluded.nombre, rol = excluded.rol, doc = excluded.doc, salt = excluded.salt, hash = excluded.hash, modulos = excluded.modulos'),
  updUsr: db.prepare('UPDATE usuarios SET nombre = ?, rol = ?, doc = ?, modulos = ? WHERE u = ?'),
  borUsr: db.prepare('DELETE FROM usuarios WHERE u = ?'),
  insBor: db.prepare('INSERT INTO borrados (id, u, nombre, creado, estado, descripcion, detalle) VALUES (?, ?, ?, ?, ?, ?, ?)'),
  getBor: db.prepare('SELECT * FROM borrados WHERE id = ?'),
  updBor: db.prepare('UPDATE borrados SET estado = ?, via = ?, resuelto_por = ?, resuelto = ?, motivo = ?, expira = ? WHERE id = ?'),
  opsBor: db.prepare('UPDATE borrados SET ops = ? WHERE id = ?'),
  pasaBor: db.prepare("UPDATE borrados SET estado = 'pendiente', creado = ? WHERE id = ? AND estado = 'borrador'"),
  listaBor: db.prepare("SELECT * FROM borrados WHERE estado != 'borrador' ORDER BY creado DESC LIMIT 200"),
  limpiaBor: db.prepare("DELETE FROM borrados WHERE estado = 'borrador' AND creado < ?"),
  archRef: db.prepare('SELECT 1 FROM docs WHERE data LIKE ? LIMIT 1'),
  cuentaArch: db.prepare('SELECT COUNT(*) AS n FROM archivos WHERE dueno = ? AND creado > ?'),
  setForzar: db.prepare('UPDATE usuarios SET forzar = ? WHERE u = ?'),
  setAlumno: db.prepare('UPDATE usuarios SET alumno = ? WHERE u = ?'),
  setTemporal: db.prepare('UPDATE usuarios SET temporal = ? WHERE u = ?'),
  usrDeAlumno: db.prepare("SELECT u, forzar, temporal FROM usuarios WHERE rol = 'alumno' AND alumno = ?"),
  usrAlumno: db.prepare("SELECT u, nombre, alumno FROM usuarios WHERE rol = 'alumno'"),
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
const ROLES = ['admin', 'caja', 'consulta', 'docente', 'personalizado'];   // 'alumno' solo se crea con /api/usuarios/alumnos
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

/* ---------- Contraseña inicial de los alumnos ----------
   Se guarda cifrada (AES-256-GCM, con una llave que vive solo en el disco del servidor y no entra a los respaldos)
   únicamente mientras el alumno no la cambia; al cambiarla se borra y la contraseña propia del alumno nunca se puede ver. */
const LLAVE_ARCH = path.join(DATOS, 'secreto.key');
let LLAVE = null;
function llave() {
  if (LLAVE) return LLAVE;
  if (ENV.LF_CLAVE_SECRETA && /^[0-9a-f]{64}$/i.test(ENV.LF_CLAVE_SECRETA)) { LLAVE = Buffer.from(ENV.LF_CLAVE_SECRETA, 'hex'); return LLAVE; }
  if (fs.existsSync(LLAVE_ARCH)) LLAVE = Buffer.from(fs.readFileSync(LLAVE_ARCH, 'utf8').trim(), 'hex');
  if (!LLAVE || LLAVE.length !== 32) { LLAVE = crypto.randomBytes(32); fs.writeFileSync(LLAVE_ARCH, LLAVE.toString('hex'), { mode: 0o600 }); }
  return LLAVE;
}
function cifra(txt) { const iv = crypto.randomBytes(12), c = crypto.createCipheriv('aes-256-gcm', llave(), iv), ct = Buffer.concat([c.update(String(txt), 'utf8'), c.final()]); return Buffer.concat([iv, c.getAuthTag(), ct]).toString('base64'); }
function descifra(b64) { try { const b = Buffer.from(String(b64), 'base64'), d = crypto.createDecipheriv('aes-256-gcm', llave(), b.subarray(0, 12)); d.setAuthTag(b.subarray(12, 28)); return Buffer.concat([d.update(b.subarray(28)), d.final()]).toString('utf8'); } catch (e) { return null; } }

/* ---------- Contraseñas y sesiones ---------- */
function hashClave(clave, salt) { return crypto.scryptSync(String(clave), salt, 64, { N: 16384, r: 8, p: 1 }).toString('hex'); }
function hashClaveAsync(clave, salt) { return new Promise((ok, mal) => crypto.scrypt(String(clave), salt, 64, { N: 16384, r: 8, p: 1 }, (e, k) => e ? mal(e) : ok(k.toString('hex')))); }
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
  if (u.rol === 'alumno' && bloqueadoPorPago(u.alumno)) { q.borSes.run(s.token); return null; }
  if (ahora - s.ultimo > 60000) q.tocaSes.run(ahora, s.token);
  const modulos = parseModulos(u.modulos);
  return { u: u.u, name: u.nombre, rol: u.rol, doc: u.doc || '', modulos, perm: permisosDe(u.rol, modulos), alumno: u.alumno || '', forzar: !!u.forzar, _token: s.token };
}
const intentos = new Map();
function limite(clave, max, ventanaMs) { const a = intentos.get(clave), ahora = Date.now(); if (!a || ahora - a.desde > ventanaMs) return false; return a.n >= max; }
function falla(clave, ventanaMs) { const a = intentos.get(clave), ahora = Date.now(); if (!a || ahora - a.desde > ventanaMs) intentos.set(clave, { n: 1, desde: ahora }); else a.n++; }
setInterval(() => { const ahora = Date.now(); intentos.forEach((v, k) => { if (ahora - v.desde > 3600000) intentos.delete(k); }); q.limpiaSes.run(ahora); }, 600000).unref();
const publicoUsuario = u => { const m = u.perm ? u.modulos : parseModulos(u.modulos); return { u: u.u, name: u.nombre || u.name, rol: u.rol, doc: u.doc || '', modulos: m || null, perm: permisosDe(u.rol, m), alumno: u.alumno || '', forzar: !!u.forzar, temporal: !!u.tmp, dosPasos: !!u.dos }; };
const listaUsuarios = () => q.usrs.all().map(x => publicoUsuario(x));

/* ---------- Permisos por módulo (se aplican aquí, no solo en la pantalla) ----------
   Cada usuario tiene un nivel por módulo: "ver" (solo lectura) o "editar" (lectura y escritura).
   L = colecciones que lee; E = colecciones que además escribe cuando el nivel es "editar". */
const MODULOS = {
  pagos:        { L: ['students', 'ledger', 'fotos', 'grupos', 'materias', 'calif', 'catalogo', 'contenidos', 'egresados', 'constancias', 'cobranza', 'avisos', 'acuerdo286', 'fiscal', 'facturas'], E: ['ledger', 'meta', 'constancias'], plans: true },
  corte:        { L: ['gastos', 'cortes', 'ledger', 'students'], E: ['gastos', 'cortes'], plans: true },
  estado:       { L: ['students', 'ledger', 'gastos', 'cortes', 'nomina', 'nomina_admin', 'titulaciones', 'acuerdo286', 'docentes', 'materias', 'calif', 'catalogo', 'constancias', 'egresados'], E: [], plans: true, nomina: true },
  ver:          { L: ['students', 'ledger'], E: ['ledger'], plans: true },
  inscripcion:  { L: ['students', 'fotos', 'grupos', 'ledger', 'catalogo', 'materias', 'calif', 'egresados', 'constancias'], E: ['students', 'fotos', 'ledger', 'meta', 'grupos'], plans: true, archivos: true },
  escolar:      { L: ['students', 'fotos', 'grupos', 'materias', 'calif', 'catalogo', 'contenidos', 'criterios', 'docentes', 'egresados', 'constancias', 'justificantes', 'ledger', 'resguardos', 'ciclos'], E: ['students', 'fotos', 'grupos', 'materias', 'calif', 'catalogo', 'contenidos', 'criterios', 'docentes', 'egresados', 'constancias', 'justificantes', 'ledger', 'meta', 'planeaciones', 'resguardos', 'asistencia', 'ciclos'], plans: true, archivos: true },
  constancias:  { L: ['constancias', 'students', 'ledger', 'calif', 'catalogo', 'materias', 'grupos', 'fotos', 'egresados'], E: ['constancias', 'ledger', 'meta'], plans: true },
  acuerdos:     { L: ['acuerdos', 'ledger', 'students', 'calif', 'catalogo', 'materias', 'grupos', 'fotos', 'egresados', 'constancias'], E: ['acuerdos', 'ledger', 'meta'], plans: true },
  a286:         { L: ['acuerdo286', 'resguardos286'], E: ['acuerdo286', 'meta', 'resguardos286'], archivos: true },
  titulaciones: { L: ['titulaciones'], E: ['titulaciones', 'meta'], archivos: true },
  nomina_doc:   { L: ['nomina', 'docentes', 'materias'], E: ['nomina', 'meta'], nomina: true, nominaE: true },
  nomina_adm:   { L: ['empleados', 'nomina_admin'], E: ['empleados', 'nomina_admin', 'meta'] },
  docente:      { L: ['students', 'grupos', 'materias', 'docentes', 'calif', 'criterios', 'catalogo', 'contenidos', 'ciclos', 'justificantes'], E: ['calif', 'criterios'] },
  expedientes:  { L: ['docentes_docs'], E: ['docentes_docs'], archivos: true, privados: true }
};
const VER_ALUMNOS_COMPLETOS = ['pagos', 'corte', 'estado', 'ver', 'inscripcion', 'escolar', 'constancias', 'acuerdos'];
const PLANTILLAS = {
  caja: { pagos: 'editar', corte: 'editar', ver: 'editar', acuerdos: 'editar', escolar: 'ver', constancias: 'editar' },
  consulta: { pagos: 'ver', escolar: 'ver' },
  docente: { docente: 'editar' },
  personalizado: {}
};
function permisosDe(rol, modulos) {
  if (rol === 'admin') { const t = {}; Object.keys(MODULOS).forEach(k => { t[k] = 'editar'; }); return t; }
  if (modulos && typeof modulos === 'object') return modulos;
  return PLANTILLAS[rol] || {};
}
function parseModulos(txt) { if (!txt) return null; try { const o = JSON.parse(txt); return o && typeof o === 'object' ? o : null; } catch (e) { return null; } }
function nivel(s, m) { return s.rol === 'admin' ? 'editar' : ((s.perm || {})[m] || 'none'); }
function tiene(s, m, min) { const n = nivel(s, m); return min === 'editar' ? n === 'editar' : n !== 'none'; }
/* ---- Alumnos: solo ven lo suyo (filtro por registro) ---- */
function gruposDeAlumno(sid) { return q.lista.all('grupos').map(r => ({ id: r.id, d: JSON.parse(r.data) })).filter(g => Array.isArray(g.d.alumnos) && g.d.alumnos.includes(sid)); }
/* Una materia del calendario es de un grupo si coincide su plan, periodo y cuatrimestre, o si está fusionada con ese plan y cuatrimestre */
function materiaDeGrupo(m, g) {
  if (m.per !== g.per) return false;
  if (m.plan === g.plan && m.cuat === g.cuat) return true;
  return Array.isArray(m.fus) && m.fus.some(f => f.plan === g.plan && f.cuat === g.cuat);
}
function contextoAlumno(s) {
  const grupos = gruposDeAlumno(s.alumno), mats = q.lista.all('materias').map(r => ({ id: r.id, d: JSON.parse(r.data) })).filter(m => grupos.some(g => materiaDeGrupo(m.d, g.d)));
  return { grupos, docIds: new Set(mats.map(m => m.d.docId).filter(Boolean)) };
}
const CAMPOS_ALUMNO = ['mat', 'nombre', 'carrera', 'programa', 'ingreso', 'nuevo', 'sexo', 'edad', 'beca', 'tut', 'tutTel'];
function filtraAlumno(s, col, id, data, ctx) {
  const sid = s.alumno;
  if (!sid) return null;
  switch (col) {
    case 'students': { if (id !== sid) return null; const o = {}; CAMPOS_ALUMNO.forEach(k => { if (data[k] !== undefined) o[k] = data[k]; }); return o; }
    case 'ledger': { if (id !== sid) return null; return { pagos: (data.pagos || []).map(g => { const o = Object.assign({}, g); delete o.by; delete o.confPor; return o; }) }; }
    case 'calif': case 'constancias': case 'egresados': case 'fotos': return id === sid ? data : null;
    case 'solicitudes': case 'avisos': case 'facturas': return data.sid === sid ? data : null;
    case 'fiscal': return id === sid ? data : null;
    case 'justificantes': { if (data.sid !== sid || data.estado !== 'Aprobado') return null; const o = {}; ['id', 'num', 'sid', 'nombre', 'mat', 'plan', 'sexo', 'grupo', 'fecha', 'desde', 'hasta', 'motivo', 'estado', 'solicitud'].forEach(k => { if (data[k] !== undefined) o[k] = data[k]; }); return o; }
    case 'grupos': return (data.alumnos || []).includes(sid) ? Object.assign({}, data, { alumnos: [sid] }) : null;
    case 'materias': return ctx.grupos.some(g => materiaDeGrupo(data, g.d)) ? data : null;
    case 'docentes': return ctx.docIds.has(id) ? { nombre: data.nombre, esp: data.esp || '' } : null;
    case 'catalogo': return data;
    case 'config': return (id === 'plans' || id === 'app') ? data : null;
    default: return null;
  }
}
function eventoAlumno(s, c, id) {
  if (['students', 'ledger', 'calif', 'constancias', 'egresados', 'fotos'].includes(c)) return id === s.alumno;
  if (c === 'fiscal') return id === s.alumno;
  if (c === 'solicitudes' || c === 'justificantes' || c === 'avisos' || c === 'facturas') { const r = q.uno.get(c, id || ''); if (!r) return false; try { return JSON.parse(r.data).sid === s.alumno; } catch (e) { return false; } }
  if (['grupos', 'materias', 'docentes', 'catalogo'].includes(c)) return true;
  if (c === 'config') return id === 'plans' || id === 'app';
  return false;
}
function esPlaneacionPropia(s, id) { if (!s.doc) return false; if (!id) return true; const r = q.uno.get('materias', id); if (!r) return false; try { return JSON.parse(r.data).docId === s.doc; } catch (e) { return false; } }
function puedeLeer(s, col, id) {
  if (col === 'config' && id === 'users') return false;
  if (col === '_borrados') return s.rol === 'admin' || id === s.u;
  if (s.rol === 'alumno') return eventoAlumno(s, col, id);
  if (s.rol === 'admin') return true;
  const P = s.perm || {};
  if (col === 'planeaciones') return P.escolar === 'editar' || (!!(P.docente && P.docente !== 'none') && esPlaneacionPropia(s, id));
  /* Asistencia: Control escolar la ve; cada docente solo la de sus propias asignaturas */
  if (col === 'asistencia') return (!!P.escolar && P.escolar !== 'none') || (!!(P.docente && P.docente !== 'none') && esPlaneacionPropia(s, id));
  if (col === 'solicitudes') return P.escolar === 'editar';
  /* Los contratos llevan datos fiscales y honorarios: solo Control escolar (editar) y la nómina docente los leen */
  if (col === 'contratos') return P.escolar === 'editar' || (!!P.nomina_doc && P.nomina_doc !== 'none');
  /* Las fichas de inscripción firmadas llevan firmas: las lee Inscripción (cualquier nivel) y Control escolar con edición; las escribe Inscripción con edición */
  if (col === 'fichasins') return P.escolar === 'editar' || (!!P.inscripcion && P.inscripcion !== 'none');
  if (col === 'config') {
    if (id === 'nomina') return Object.keys(P).some(m => P[m] !== 'none' && MODULOS[m] && MODULOS[m].nomina);
    if (id === 'plans') return Object.keys(P).some(m => P[m] !== 'none' && MODULOS[m] && MODULOS[m].plans);
    return Object.keys(P).some(m => P[m] !== 'none');
  }
  if (col === 'meta') return Object.keys(P).some(m => P[m] === 'editar' && MODULOS[m] && MODULOS[m].E.includes('meta'));
  return Object.keys(P).some(m => P[m] !== 'none' && MODULOS[m] && MODULOS[m].L.includes(col));
}
function puedeEscribir(s, col, id) {
  if (col === 'config' && id === 'users') return false;
  if (s.rol === 'alumno') return false;
  if (s.rol === 'admin') return true;
  const P = s.perm || {};
  if (col === 'planeaciones' && P.escolar !== 'editar') return P.docente === 'editar' && esPlaneacionPropia(s, id);
  if (col === 'asistencia' && P.escolar !== 'editar') return P.docente === 'editar' && esPlaneacionPropia(s, id);
  if (col === 'solicitudes') return P.escolar === 'editar';
  if (col === 'contratos') return P.escolar === 'editar';
  if (col === 'fichasins') return P.inscripcion === 'editar';
  if (col === 'config') return id === 'nomina' && P.nomina_doc === 'editar';
  return Object.keys(P).some(m => P[m] === 'editar' && MODULOS[m] && MODULOS[m].E.includes(col));
}
function puedeArchivos(s, privado) {
  if (s.rol === 'alumno') return false;
  if (s.rol === 'admin') return true;
  const P = s.perm || {};
  if (privado) return P.expedientes === 'editar' || P.docente === 'editar' || P.escolar === 'editar' || P.a286 === 'editar';
  return Object.keys(P).some(m => P[m] === 'editar' && MODULOS[m] && MODULOS[m].archivos && !MODULOS[m].privados);
}
const CAMPOS_DOCENTE = ['mat', 'nombre', 'carrera', 'programa', 'ingreso', 'sexo', 'nuevo'];
function reduce(s, col, data) {
  /* El docente solo necesita saber qué faltas están justificadas (no el motivo ni los documentos) */
  if (col === 'justificantes' && s.rol === 'docente') { const o = {}; ['id', 'sid', 'num', 'desde', 'hasta', 'estado'].forEach(k => { if (data[k] !== undefined) o[k] = data[k]; }); return o; }
  /* Quien cobra desde Finanzas ve de Acuerdo 286 solo lo necesario para cobrar (sin foto, documentos ni archivos) */
  if (col === 'acuerdo286' && s.rol !== 'admin') {
    const P0 = s.perm || {};
    if ((P0.a286 && P0.a286 !== 'none') || (P0.estado && P0.estado !== 'none')) return data;
    const o = {}; ['id', 'num', 'nombre', 'apPat', 'apMat', 'tel', 'fecha', 'plan', 'nCol', 'pagos', 'enviado'].forEach(k => { if (data[k] !== undefined) o[k] = data[k]; });
    o.certListo = !!data.cert || !!q.lista.all('resguardos286').some(r => { try { return JSON.parse(r.data).sid === data.id; } catch (e) { return false; } });
    return o;
  }
  if (col !== 'students' || s.rol === 'admin') return data;
  const P = s.perm || {};
  if (VER_ALUMNOS_COMPLETOS.some(m => P[m] && P[m] !== 'none')) return data;
  const o = {}; CAMPOS_DOCENTE.forEach(k => { if (data[k] !== undefined) o[k] = data[k]; }); return o;
}
function validaModulos(m) {
  if (m === undefined || m === null) return { ok: true, valor: null };
  if (typeof m !== 'object' || Array.isArray(m)) return { ok: false };
  const o = {};
  for (const k of Object.keys(m)) {
    if (!MODULOS[k]) return { ok: false };
    const v = m[k]; if (!['none', 'ver', 'editar'].includes(v)) return { ok: false };
    if ((k === 'estado' || k === 'expedientes') && false) return { ok: false };
    if (v !== 'none') o[k] = v;
  }
  return { ok: true, valor: o };
}

/* ---------- Borrados protegidos ----------
   Nadie que no sea Administrador borra nada sin autorización: o la contraseña del encargado, o su aprobación.
   Es un borrado: eliminar un documento o un archivo, o quitar elementos de un documento (un pago, un gasto, un documento cargado…). */
const NOMBRES_COL = { students: 'Alumno', ledger: 'Pagos del alumno', calif: 'Calificaciones del alumno', constancias: 'Constancias del alumno', fotos: 'Fotografía del alumno', egresados: 'Registro de egresado', gastos: 'Gastos del mes', cortes: 'Corte de caja', grupos: 'Grupo', materias: 'Materia del calendario', catalogo: 'Plan de estudios', docentes: 'Docente', docentes_docs: 'Expediente del docente', titulaciones: 'Titulación', acuerdo286: 'Acuerdo 286', acuerdos: 'Acuerdo de pago', justificantes: 'Justificante', empleados: 'Empleado', nomina: 'Nómina docente', nomina_admin: 'Nómina administrativa', criterios: 'Puntos de evaluación', contenidos: 'Contenido de asignatura', contratos: 'Contrato de docente', fichasins: 'Ficha de inscripción firmada' };
const idPer = per => String(per || '').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '').toLowerCase();
const cicloDe = per => { if (!per) return null; const r = q.uno.get('ciclos', idPer(per)); try { return r ? JSON.parse(r.data) : null; } catch (e) { return null; } };
const perCerrado = per => { const c = cicloDe(per); return !!(c && c.cerrado); };
/* El cuatrimestre se evalúa en dos bloques de asignaturas (meses 1-2 y 3-4): el bloque sale de la asignatura o de su fecha de evaluación */
const mitadPer = per => { const m = /^(Sep–Dic|Ene–Abr|May–Ago) (\d{4})$/.exec(String(per || '')); return m ? m[2] + (m[1] === 'Sep–Dic' ? '-10-31' : m[1] === 'Ene–Abr' ? '-02-29' : '-06-30') : ''; };
const bloqueDe = m => { if (!m) return 0; if (m.bl === 1 || m.bl === 2) return m.bl; const x = mitadPer(m.per); return m.ev && x ? (m.ev <= x ? 1 : 2) : 0; };
const matCerrada = (mid, cache) => { const r = q.uno.get('materias', mid); let m = null; try { m = r ? JSON.parse(r.data) : null; } catch (e) {} if (!m) return false; if (perCerrado(m.per)) return true; const b = bloqueDe(m), c = cicloDe(m.per); return !!(b && c && c.bloques && c.bloques[b] && c.bloques[b].cerrado); };
const EXENTAS_PUT = new Set(['meta', 'calif', 'criterios', 'contenidos', 'cortes', 'config', 'fotos', 'planeaciones']);
const VENTANA_BORRADO = 10 * 60000, RACHA_BORRADO = 15000;
function alumnoDe(col, id) { if (['students', 'ledger', 'calif', 'constancias', 'fotos', 'egresados'].includes(col)) { const r = q.uno.get('students', id); if (r) { try { return JSON.parse(r.data).nombre || ''; } catch (e) {} } } return ''; }
function resumenReg(o, col) {
  if (o === null || o === undefined) return '';
  if (typeof o !== 'object') { const r = (col === 'grupos') ? q.uno.get('students', String(o)) : null; if (r) { try { return JSON.parse(r.data).nombre; } catch (e) {} } return String(o).slice(0, 60); }
  const p = [];
  if (o.folio) p.push('folio ' + o.folio);
  if (o.num && o.num !== o.folio) p.push(String(o.num));
  const nom = o.nombre || o.emp || o.concepto || o.c || o.name || o.nom; if (nom) p.push(String(nom).slice(0, 60) + (o.apPat ? ' ' + o.apPat : ''));
  if (o.mat && !o.nombre) p.push('matrícula ' + o.mat);
  const mon = typeof o.monto === 'number' ? o.monto : (typeof o.neto === 'number' ? o.neto : null); if (mon !== null) p.push(dinero(mon));
  if (o.fecha) p.push(String(o.fecha));
  return p.join(' · ') || (o.id ? 'registro ' + String(o.id).slice(0, 12) : 'elemento');
}
function esRegistro(a) { return a && typeof a === 'object' && !Array.isArray(a) && (a.id !== undefined || (Object.keys(a).length && Object.values(a).every(v => v && typeof v === 'object' && !Array.isArray(v)))); }
function quitados(v, n, ruta, out, prof) {
  if (prof > 4) return;
  if (Array.isArray(v)) {
    if (!Array.isArray(n)) { if (v.length) out.push({ ruta, item: v[0], n: v.length }); return; }
    const conId = v.length > 0 && v.every(x => x && typeof x === 'object' && x.id !== undefined);
    if (conId) { const ids = new Set(n.filter(x => x && typeof x === 'object').map(x => x.id)); v.forEach(x => { if (!ids.has(x.id)) out.push({ ruta, item: x }); else quitados(x, n.find(z => z && z.id === x.id), ruta + '[' + x.id + ']', out, prof + 1); }); }
    else if (v.length > 0 && v.every(x => x === null || typeof x !== 'object')) { const set = new Set(n); v.forEach(x => { if (!set.has(x)) out.push({ ruta, item: x }); }); }
    else if (n.length < v.length) out.push({ ruta, item: null, n: v.length - n.length });
    return;
  }
  if (v && typeof v === 'object') {
    if (!n || typeof n !== 'object' || Array.isArray(n)) { if (esRegistro(v)) out.push({ ruta, item: v }); return; }
    Object.keys(v).forEach(k => {
      const a = v[k], b = n[k];
      if (a && typeof a === 'object' && (Array.isArray(a) ? a.length : Object.keys(a).length)) {
        if (b === undefined || b === null) { if (Array.isArray(a) || esRegistro(a)) out.push({ ruta: ruta + '.' + k, item: Array.isArray(a) ? a[0] : a, n: Array.isArray(a) ? a.length : undefined }); }
        else quitados(a, b, ruta + '.' + k, out, prof + 1);
      }
    });
  }
}
const TIPO_RUTA = { pagos: 'pago', items: 'registro', abonos: 'abono', docs: 'documento', tram: 'documento', obt: 'documento', asig: 'asignatura', alumnos: 'alumno del grupo', cuotas: 'parcialidad', filas: 'fila de nómina', cert: 'certificado' };
const dinero = n => '$' + Number(n).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
function describeBorrado(m, col, id, viejo, nuevo) {
  const colN = NOMBRES_COL[col] || col, quien = alumnoDe(col, id), de = quien ? ' · ' + quien : '';
  if (m === 'DELETE') return 'Eliminar ' + colN.toLowerCase() + (col === 'students' && viejo && viejo.nombre ? ' ' + viejo.nombre + (viejo.mat ? ' (matrícula ' + viejo.mat + ')' : '') : de.replace(' · ', ' de ')) + (viejo && col !== 'students' ? ' — ' + resumenReg(viejo, col) : '');
  const out = []; quitados(viejo, nuevo, '', out, 0);
  const tr = out.slice(0, 3).map(o => {
    const ult = String(o.ruta || '').split(/[.[]/).filter(Boolean).pop() || '', tipo = TIPO_RUTA[ult] || 'elemento';
    return tipo + ': ' + (o.item !== undefined && o.item !== null ? resumenReg(o.item, col) : (o.n + ' elemento(s)'));
  });
  return 'Quitar ' + tr.join('; ') + (out.length > 3 ? ' y ' + (out.length - 3) + ' más' : '') + ' (' + colN + de + ')';
}
function envioBorrado(u) { difunde('_borrados', u); difunde('_borrados', '*'); }
/* Devuelve true si ya respondió (403) porque el borrado necesita autorización. */
function protegeBorrado(s, req, res, o) {
  if (s.rol === 'admin') return false;
  let esBorrado = false;
  if (o.accion === 'DELETE') esBorrado = o.col !== 'meta';
  else if (o.accion === 'PUT') { if (!EXENTAS_PUT.has(o.col) && o.viejo) { const out = []; quitados(o.viejo, o.nuevo, '', out, 0); esBorrado = out.length > 0; } }
  else if (o.accion === 'ARCHIVO') esBorrado = true;
  if (!esBorrado) return false;
  const id = String(req.headers['x-autoriza'] || '');
  if (id) {
    const b = q.getBor.get(id), ahora = Date.now();
    if (b && b.u === s.u && b.estado === 'aprobada' && b.expira > ahora) {
      /* Autoriza una acción, no una ventana de tiempo: tras la primera operación, las siguientes deben seguir de inmediato */
      const ops = JSON.parse(b.ops || '[]'), ultima = ops.length ? ops[ops.length - 1].t : 0;
      if (ops.length < 80 && (!ultima || ahora - ultima <= RACHA_BORRADO)) { ops.push({ t: ahora, op: o.accion, col: o.col, id: o.id }); q.opsBor.run(JSON.stringify(ops), id); audita(s.u, req, 'Borrado autorizado', o.accion + ' ' + o.col + '/' + o.id + ' · solicitud ' + id); envioBorrado(s.u); return false; }
    }
  }
  q.limpiaBor.run(Date.now() - 3600000);
  const d = o.descripcion || describeBorrado(o.accion, o.col, o.id, o.viejo, o.nuevo), bid = crypto.randomBytes(8).toString('hex');
  q.insBor.run(bid, s.u, s.name, Date.now(), 'borrador', d, JSON.stringify({ op: o.accion, col: o.col, id: o.id }));
  audita(s.u, req, 'Borrado bloqueado: necesita autorización', d);
  responde(res, 403, { error: 'Esta acción necesita la autorización del encargado.', requiereAutorizacion: true, solicitud: bid, descripcion: d });
  return true;
}
function vistaBorrado(b) {
  const ahora = Date.now(); let estado = b.estado;
  if (estado === 'aprobada' && b.expira && b.expira < ahora) estado = 'vencida';
  const _o = JSON.parse(b.ops || '[]'); if (estado === 'aprobada' && _o.length && ahora - _o[_o.length - 1].t > RACHA_BORRADO) estado = 'usada';
  return { id: b.id, u: b.u, nombre: b.nombre, creado: new Date(b.creado).toISOString(), estado, via: b.via || '', descripcion: b.descripcion, resueltoPor: b.resuelto_por || '', resuelto: b.resuelto ? new Date(b.resuelto).toISOString() : '', motivo: b.motivo || '', expira: b.expira ? new Date(b.expira).toISOString() : '', ops: JSON.parse(b.ops || '[]') };
}

/* ---------- Solicitudes de los alumnos (justificante, boleta, constancia) ----------
   El alumno solo puede crear solicitudes propias en estado «pendiente» y marcarlas como leídas; la respuesta la da Control escolar. */
const MOTIVOS_JUST = ['Enfermedad', 'Cita médica', 'Asunto familiar', 'Trámite personal o laboral', 'Otro'];
const fechaOk = f => /^\d{4}-\d{2}-\d{2}$/.test(f) && !isNaN(Date.parse(f + 'T00:00:00Z'));
const txt = (v, n) => String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, n);
async function guardaSolicitudAlumno(s, req, res, id, m) {
  let c; try { c = JSON.parse((await leeCuerpo(req, 30000)).toString('utf8') || '{}'); } catch (e) { if (e.cod) throw e; return responde(res, 400, { error: 'JSON no válido' }); }
  if (!c || typeof c !== 'object' || Array.isArray(c)) return responde(res, 400, { error: 'Se esperaba un objeto' });
  const previo = q.uno.get('solicitudes', id);
  if (previo) {
    const d = JSON.parse(previo.data);
    if (d.sid !== s.alumno) return responde(res, 403, { error: 'No es tu solicitud.' });
    if (m !== 'PATCH' || Object.keys(c).some(k => k !== 'leida') || typeof c.leida !== 'boolean') return responde(res, 403, { error: 'Solo puedes marcar tus notificaciones como leídas.' });
    d.leida = c.leida; q.pon.run('solicitudes', id, JSON.stringify(d), Date.now()); difunde('solicitudes', id); return responde(res, 200, { ok: true });
  }
  if (m !== 'PUT') return responde(res, 403, { error: 'No tienes permiso para hacer esto.' });
  const st = q.uno.get('students', s.alumno); if (!st) return responde(res, 400, { error: 'No se encontró tu registro de alumno.' });
  const al = JSON.parse(st.data), ahora = Date.now(), hoy = new Date(ahora).toISOString().slice(0, 10);
  const mias = q.lista.all('solicitudes').map(r => JSON.parse(r.data)).filter(d => d.sid === s.alumno);
  if (mias.filter(d => d.estado === 'pendiente').length >= 5) return responde(res, 429, { error: 'Ya tienes 5 solicitudes pendientes. Espera a que Control escolar las atienda.' });
  if (mias.filter(d => Date.parse(d.creada) > ahora - 86400000).length >= 10) return responde(res, 429, { error: 'Hiciste demasiadas solicitudes hoy. Inténtalo mañana.' });
  const tipo = txt(c.tipo, 20);
  if (!['justificante', 'boleta', 'constancia'].includes(tipo)) return responde(res, 400, { error: 'Tipo de solicitud no válido.' });
  const d = { id, tipo, sid: s.alumno, nombre: al.nombre || '', mat: al.mat || '', plan: al.programa || al.carrera || '', creada: new Date(ahora).toISOString(), estado: 'pendiente', leida: false, nota: txt(c.nota, 300) };
  if (tipo === 'justificante') {
    const dias = 86400000, f = Date.parse(hoy + 'T00:00:00Z');
    if (!fechaOk(c.desde) || !fechaOk(c.hasta) || c.hasta < c.desde) return responde(res, 400, { error: 'Revisa las fechas de las faltas.' });
    if (Date.parse(c.desde + 'T00:00:00Z') < f - 90 * dias || Date.parse(c.hasta + 'T00:00:00Z') > f + 30 * dias) return responde(res, 400, { error: 'Las fechas deben estar dentro de los últimos 90 días o los próximos 30.' });
    if (!MOTIVOS_JUST.includes(c.motivo)) return responde(res, 400, { error: 'Elige el motivo de tu falta.' });
    const ids = Array.isArray(c.docs) ? c.docs.map(x => String((x && x.id) || x)).slice(0, 3) : [];
    const docs = ids.map(i => { const a = ID_ARCH.test(i) ? q.uArch.get(i) : null; return a && a.dueno === s.u && a.cat === 'solicitud' ? { id: i, name: a.nombre, size: a.tamano, type: a.tipo } : null; });
    if (!docs.length || docs.some(x => !x)) return responde(res, 400, { error: 'Anexa tu comprobante (PDF, JPG o PNG).' });
    Object.assign(d, { desde: c.desde, hasta: c.hasta, motivo: c.motivo, docs });
  } else if (tipo === 'boleta') {
    if (!/^(Sep–Dic|Ene–Abr|May–Ago) \d{4}$/.test(String(c.periodo || ''))) return responde(res, 400, { error: 'Elige el periodo de tu boleta.' });
    d.periodo = c.periodo;
  } else {
    if (!['simple', 'promedio'].includes(c.tipoC)) return responde(res, 400, { error: 'Elige el tipo de constancia.' });
    d.tipoC = c.tipoC; d.dest = txt(c.dest, 120);
  }
  q.pon.run('solicitudes', id, JSON.stringify(d), ahora); difunde('solicitudes', id);
  audita(s.u, req, 'Solicitud de alumno', tipo + ' · ' + d.nombre);
  return responde(res, 200, { ok: true });
}

/* ---------- Eventos en tiempo real ---------- */
function difunde(c, id) { const m = 'data: ' + JSON.stringify({ c, id }) + '\n\n'; clientes.forEach(cl => { if (!puedeLeer(cl.s, c, id)) return; try { cl.res.write(m); } catch (e) { clientes.delete(cl); } }); }
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
  q.todosArch.all().forEach(a => { const ruta = path.join(ARCH, a.id); if (!fs.existsSync(ruta)) return; const nom = 'archivos/' + a.id + '-' + String(a.nombre || 'archivo').replace(/[^\w.\- áéíóúñÁÉÍÓÚÑ]/g, '_'); entradas.push({ nombre: nom, ruta }); indice.push({ id: a.id, archivo: nom, nombre: a.nombre, origen: '', privado: a.privado ? 1 : 0 }); });
  entradas.push({ nombre: 'indice-1.json', datos: Buffer.from(JSON.stringify(indice)) });
  try { await enviaZip(res, 'respaldo-completo-' + hoy() + '.zip', entradas); } finally { try { fs.unlinkSync(tmp); } catch (e) {} }
}

/* ---------- Respaldos automáticos, verificados y con copia fuera del servidor ---------- */
const RESPA = require('./respaldos.js'), AUTO = path.join(RESP, 'auto'); fs.mkdirSync(AUTO, { recursive: true });
const CFG_RESP0 = { activo: false, hora: 2, conservar: 14, cifrar: false, claveCif: '', s3: { activo: false, endpoint: '', region: 'us-east-1', bucket: '', prefijo: 'respaldos/', acceso: '', secreto: '' }, correo: { activo: false, host: '', puerto: 587, seguro: false, usuario: '', clave: '', de: '', para: [], adjuntar: true } };
const SECRETOS_RESP = [['claveCif'], ['s3', 'acceso'], ['s3', 'secreto'], ['correo', 'clave']];
function leeSis(id, def) { const r = q.uno.get('sistema', id); try { return r ? JSON.parse(r.data) : def; } catch (e) { return def; } }
function ponSis(id, o) { q.pon.run('sistema', id, JSON.stringify(o), Date.now()); }
const getP = (o, r) => r.reduce((x, k) => (x == null ? x : x[k]), o);
function setP(o, r, v) { let x = o; r.slice(0, -1).forEach(k => { x = x[k]; }); x[r[r.length - 1]] = v; }
function cfgResp() {  /* configuración con los secretos ya descifrados (solo para uso interno) */
  const g = leeSis('respaldos', {}), c = JSON.parse(JSON.stringify(CFG_RESP0));
  ['activo', 'hora', 'conservar', 'cifrar', 'claveCif'].forEach(k => { if (g[k] !== undefined) c[k] = g[k]; }); Object.assign(c.s3, g.s3 || {}); Object.assign(c.correo, g.correo || {});
  SECRETOS_RESP.forEach(r => { const v = getP(c, r); setP(c, r, v ? (descifra(v) || '') : ''); }); return c;
}
function cfgRespPublica() {
  const c = cfgResp(), p = JSON.parse(JSON.stringify(c));
  p.claveGuardada = !!c.claveCif; p.s3.accesoGuardado = !!c.s3.acceso; p.s3.secretoGuardado = !!c.s3.secreto; p.correo.claveGuardada = !!c.correo.clave;
  SECRETOS_RESP.forEach(r => setP(p, r, '')); p.s3.acceso = ''; return p;
}
function guardaCfgResp(n) {  /* n: lo que manda la pantalla; un secreto vacío conserva el que ya estaba */
  const act = cfgResp(), c = JSON.parse(JSON.stringify(CFG_RESP0)), err = m => { const e = new Error(m); e.cod = 400; throw e; };
  c.activo = !!n.activo; c.cifrar = !!n.cifrar;
  c.hora = Math.round(Number(n.hora)); if (!(c.hora >= 0 && c.hora <= 23)) err('La hora va de 0 a 23.');
  c.conservar = Math.round(Number(n.conservar)); if (!(c.conservar >= 1 && c.conservar <= 60)) err('Los respaldos que se conservan en el servidor van de 1 a 60.');
  const s = n.s3 || {}, m = n.correo || {};
  c.s3 = { activo: !!s.activo, endpoint: String(s.endpoint || '').trim().replace(/\/+$/, ''), region: String(s.region || 'us-east-1').trim(), bucket: String(s.bucket || '').trim(), prefijo: String(s.prefijo || '').trim().replace(/^\/+/, ''), acceso: '', secreto: '' };
  c.correo = { activo: !!m.activo, host: String(m.host || '').trim(), puerto: Math.round(Number(m.puerto) || 587), seguro: !!m.seguro, usuario: String(m.usuario || '').trim(), clave: '', de: String(m.de || '').trim(), para: (Array.isArray(m.para) ? m.para : String(m.para || '').split(/[,;\s]+/)).map(x => String(x).trim()).filter(Boolean), adjuntar: m.adjuntar !== false };
  if (c.s3.activo || c.s3.endpoint) { if (!/^https?:\/\/[^\s/]+/i.test(c.s3.endpoint)) err('La dirección del almacenamiento debe empezar con https://'); if (!/^[A-Za-z0-9._-]{3,63}$/.test(c.s3.bucket)) err('El nombre del «bucket» no es válido.'); if (!/^[a-z0-9-]{2,30}$/i.test(c.s3.region)) err('La región no es válida.'); if (c.s3.prefijo.length > 80) err('La carpeta es demasiado larga.'); }
  if (c.correo.activo) { if (!/^[A-Za-z0-9.-]+$/.test(c.correo.host)) err('Escribe el servidor de correo (por ejemplo smtp.gmail.com).'); if (!(c.correo.puerto >= 1 && c.correo.puerto <= 65535)) err('El puerto del correo no es válido.'); if (!/@/.test(c.correo.de)) err('Escribe el correo del remitente.'); if (!c.correo.para.length || c.correo.para.length > 5 || !c.correo.para.every(x => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(x))) err('Escribe de 1 a 5 correos de destino válidos.'); }
  const nuevo = (v, a) => (typeof v === 'string' && v.length ? v : a);
  c.claveCif = nuevo(n.claveCif, act.claveCif); c.s3.acceso = nuevo(s.acceso, act.s3.acceso); c.s3.secreto = nuevo(s.secreto, act.s3.secreto); c.correo.clave = nuevo(m.clave, act.correo.clave);
  if (c.cifrar && String(c.claveCif).length < 10) err('Escribe una contraseña de cifrado de al menos 10 caracteres.');
  if (c.s3.activo && (!c.s3.acceso || !c.s3.secreto)) err('Escribe la llave de acceso y la llave secreta del almacenamiento.');
  if (c.correo.activo && c.correo.usuario && !c.correo.clave) err('Escribe la contraseña del correo.');
  const g = JSON.parse(JSON.stringify(c)); SECRETOS_RESP.forEach(r => { const v = getP(g, r); setP(g, r, v ? cifra(v) : ''); }); ponSis('respaldos', g);
}
const EST_RESP0 = { corriendo: false, paso: '', ultimoIntento: 0, ultimoAutoOk: '', ultimoOk: 0, ultimoVerificado: 0, ultimaExterna: 0, ultimaPrueba: null, historial: [] };
const estResp = () => Object.assign({}, EST_RESP0, leeSis('respaldos_estado', {}));
function ponEst(e) { ponSis('respaldos_estado', e); }
function resumenAuto() {
  const c = cfgResp(), e = estResp(), ult = (e.historial || [])[0] || null;
  return { activo: c.activo, hora: c.hora, s3: !!(c.s3.activo), correo: !!(c.correo.activo), cifrado: !!c.cifrar, corriendo: !!e.corriendo, ultimoOk: e.ultimoOk, ultimoVerificado: e.ultimoVerificado, ultimaExterna: e.ultimaExterna, ultimoError: ult && !ult.ok ? ult.msg : '', ultimaPrueba: e.ultimaPrueba };
}
function crcRuta(ruta) { return new Promise((ok, mal) => { let c = 0; fs.createReadStream(ruta).on('data', d => { c = zlib.crc32(d, c); }).on('end', () => ok(c >>> 0)).on('error', mal); }); }
function listaLocales() { try { return fs.readdirSync(AUTO).filter(n => /^respaldo-\d{4}-\d{2}-\d{2}-\d{4}-[0-9a-f]{4}\.zip$/.test(n)).map(n => { const s = fs.statSync(path.join(AUTO, n)); return { nombre: n, bytes: s.size, fecha: s.mtimeMs }; }).sort((a, b) => b.fecha - a.fecha); } catch (e) { return []; } }
async function creaPaquete() {
  const mx = RESPA.fechaMx(new Date()), nombre = 'respaldo-' + mx.dia + '-' + new Date().toISOString().slice(11, 16).replace(':', '') + '-' + crypto.randomBytes(2).toString('hex') + '.zip', destino = path.join(AUTO, nombre);
  const tdb = path.join(TMP, 'paq-' + crypto.randomBytes(5).toString('hex') + '.db'); db.exec("VACUUM INTO '" + tdb.replace(/'/g, "''") + "'");
  const d = new DatabaseSync(tdb, { readOnly: true }); const filas = {}; d.prepare('SELECT coleccion, COUNT(*) AS n FROM docs GROUP BY coleccion').all().forEach(r => { filas[r.coleccion] = r.n; });
  const usuarios = d.prepare('SELECT COUNT(*) AS n FROM usuarios').get().n, registrosArchivos = d.prepare('SELECT COUNT(*) AS n FROM archivos').get().n, archs = d.prepare('SELECT id, nombre FROM archivos ORDER BY id').all(); d.close();
  const entradas = [{ nombre: 'lafragua.db', ruta: tdb }], man = { version: 1, sistema: 'lafragua', fecha: new Date().toISOString(), filas, usuarios, registrosArchivos, sha256Db: await RESPA.shaArchivo(tdb), archivos: [] };
  for (const a of archs) { const ruta = path.join(ARCH, a.id); if (!fs.existsSync(ruta)) continue; const ent = 'archivos/' + a.id + '-' + String(a.nombre || 'archivo').replace(/[^\w.\- áéíóúñÁÉÍÓÚÑ]/g, '_'); entradas.push({ nombre: ent, ruta }); man.archivos.push({ id: a.id, entrada: ent, tam: fs.statSync(ruta).size, crc: await crcRuta(ruta) }); }
  entradas.push({ nombre: 'manifest.json', datos: Buffer.from(JSON.stringify(man)) });
  const w = await RESPA.escribeZip(destino, entradas); return { nombre, destino, tdb, bytes: w.bytes };
}
function recorta(e) { e.historial = (e.historial || []).slice(0, 40); return e; }
async function ejecutaRespaldo(tipo, quien) {
  let e = estResp(); if (e.corriendo && Date.now() - (e.ultimoIntento || 0) < 3600000) { const x = new Error('Ya hay un respaldo en curso.'); x.cod = 409; throw x; }
  const c = cfgResp(), reg = { ts: Date.now(), tipo, quien: quien || '', ok: false, msg: '', archivo: '', bytes: 0, verif: null, cifrado: false, destinos: [] }; let pq = null, cif = null, gz = null;
  e.corriendo = true; e.paso = 'Creando el respaldo…'; e.ultimoIntento = Date.now(); if (tipo === 'auto') e.ultimoIntentoAuto = Date.now(); ponEst(e);
  try {
    pq = await creaPaquete(); reg.archivo = pq.nombre; reg.bytes = pq.bytes;
    e = estResp(); e.paso = 'Verificando que se pueda restaurar…'; ponEst(e);
    reg.verif = RESPA.verificaZip(pq.destino, DatabaseSync, TMP); if (!reg.verif.ok) throw new Error('El respaldo no pasó la verificación: ' + reg.verif.errores[0]);
    let ofrece = pq.destino, nombreExt = pq.nombre;
    if (c.cifrar && (c.s3.activo || c.correo.activo)) {
      if (String(c.claveCif || '').length < 10) throw new Error('Falta la contraseña de cifrado de los respaldos (en Respaldos y seguridad).');
      e = estResp(); e.paso = 'Cifrando el respaldo…'; ponEst(e);
      cif = pq.destino + '.cif'; await RESPA.cifraArchivo(pq.destino, cif, c.claveCif);
      const prueba = path.join(TMP, 'dec-' + crypto.randomBytes(4).toString('hex')); try { await RESPA.descifraArchivo(cif, prueba, c.claveCif); if ((await RESPA.shaArchivo(prueba)) !== (await RESPA.shaArchivo(pq.destino))) throw new Error('El cifrado no devolvió el mismo respaldo.'); } finally { try { fs.unlinkSync(prueba); } catch (x) {} }
      reg.cifrado = true; ofrece = cif; nombreExt = pq.nombre + '.cif';
    }
    const dia = RESPA.fechaMx(new Date()).dia;
    if (c.s3.activo) {
      e = estResp(); e.paso = 'Subiendo la copia al almacenamiento externo…'; ponEst(e);
      try { const clave = (c.s3.prefijo ? c.s3.prefijo.replace(/\/*$/, '/') : '') + dia + '/' + nombreExt; await RESPA.s3Pon(c.s3, clave, ofrece, 'application/octet-stream'); reg.destinos.push({ tipo: 's3', ok: true, msg: 'Subido a ' + c.s3.bucket + '/' + clave, bytes: fs.statSync(ofrece).size }); }
      catch (x) { reg.destinos.push({ tipo: 's3', ok: false, msg: x.message }); }
    }
    if (c.correo.activo) {
      e = estResp(); e.paso = 'Enviando el correo…'; ponEst(e);
      try {
        const adj = []; let nota = '';
        if (c.correo.adjuntar) { gz = path.join(TMP, 'mail-' + crypto.randomBytes(4).toString('hex') + '.gz'); const dbx = pq.tdb; fs.writeFileSync(gz, zlib.gzipSync(fs.readFileSync(dbx)));
          let envio = gz, nom = 'lafragua-' + dia + '.db.gz'; if (c.cifrar) { await RESPA.cifraArchivo(gz, gz + '.cif', c.claveCif); envio = gz + '.cif'; nom += '.cif'; }
          if (fs.statSync(envio).size <= 20 * 1024 * 1024) adj.push({ nombre: nom, datos: fs.readFileSync(envio), tipo: 'application/octet-stream' }); else nota = '\nLa base de datos pesa demasiado para ir por correo: la copia completa va solo al almacenamiento externo.'; if (envio !== gz) try { fs.unlinkSync(envio); } catch (x) {} }
        await RESPA.smtpEnvia(c.correo, { asunto: 'Respaldo de la plataforma · ' + dia + ' · verificado', texto: 'El respaldo automático de ' + dia + ' se hizo y se verificó correctamente.\n\nRegistros: ' + reg.verif.filas + ' · Archivos: ' + reg.verif.archivos + ' · Tamaño: ' + Math.round(reg.bytes / 1024) + ' KB' + (reg.cifrado ? '\nLos archivos adjuntos van cifrados con la contraseña de respaldos que guardaste.' : '') + nota + '\n\nPlataforma escolar.', adjuntos: adj });
        reg.destinos.push({ tipo: 'correo', ok: true, msg: 'Enviado a ' + c.correo.para.join(', ') + (adj.length ? ' con la base de datos adjunta' : ''), bytes: adj.length ? adj[0].datos.length : 0 });
      } catch (x) { reg.destinos.push({ tipo: 'correo', ok: false, msg: x.message }); }
    }
    reg.ok = true; reg.msg = reg.destinos.some(x => !x.ok) ? 'Respaldo verificado, pero falló una copia externa.' : (reg.destinos.length ? 'Respaldo verificado y copiado fuera del servidor.' : 'Respaldo verificado en el servidor (sin copia externa configurada).');
    const dias = listaLocales(); dias.slice(Math.max(1, c.conservar)).forEach(f => { try { fs.unlinkSync(path.join(AUTO, f.nombre)); } catch (x) {} });
  } catch (x) {
    reg.ok = false; reg.msg = x.message; if (pq) { try { fs.unlinkSync(pq.destino); } catch (y) {} }
    if (c.correo.activo) { try { await RESPA.smtpEnvia(c.correo, { asunto: '⚠ Falló el respaldo de la plataforma', texto: 'El respaldo de hoy no se pudo completar:\n' + x.message + '\n\nEntra a Respaldos y seguridad para revisarlo.' }); } catch (y) {} }
  } finally {
    [pq && pq.tdb, cif, gz].forEach(f => { if (f) try { fs.unlinkSync(f); } catch (x) {} });
    e = estResp(); e.corriendo = false; e.paso = ''; e.historial = [reg].concat(e.historial || []);
    if (reg.ok) { e.ultimoOk = reg.ts; e.ultimoVerificado = reg.ts; if (tipo === 'auto') e.ultimoAutoOk = RESPA.fechaMx(new Date()).dia; if (reg.destinos.some(x => x.ok)) e.ultimaExterna = reg.ts; }
    ponEst(recorta(e));
  }
  return reg;
}
function pruebaRestauracion() {
  const e = estResp(), l = listaLocales()[0]; let r;
  if (!l) r = { ts: Date.now(), ok: false, msg: 'Todavía no hay respaldos en el servidor para probar.' };
  else { const v = RESPA.verificaZip(path.join(AUTO, l.nombre), DatabaseSync, TMP); r = { ts: Date.now(), ok: v.ok, archivo: l.nombre, filas: v.filas, archivos: v.archivos, ms: v.ms, msg: v.ok ? 'El respaldo «' + l.nombre + '» se abrió como si se restaurara: base íntegra, ' + v.filas + ' registros y ' + v.archivos + ' archivos completos.' : 'La prueba falló: ' + v.errores[0] }; }
  e.ultimaPrueba = r; ponEst(e); return r;
}
let TICK_RESP = null;
function programaRespaldos() {
  const tick = () => { try { const c = cfgResp(), e = estResp(); if (e.corriendo && Date.now() - (e.ultimoIntento || 0) > 3600000) { e.corriendo = false; ponEst(e); } if (RESPA.debeCorrer(c, e, Date.now())) ejecutaRespaldo('auto', 'automático').catch(x => console.error('Respaldo automático:', x.message)); } catch (x) { console.error('Programación de respaldos:', x.message); } };
  TICK_RESP = setInterval(tick, parseInt(ENV.LF_RESPALDO_TICK_MS || '600000', 10)); TICK_RESP.unref(); setTimeout(tick, 20000).unref();
  const e = estResp(); if (e.corriendo) { e.corriendo = false; e.paso = ''; ponEst(e); }   /* quedó a medias por un reinicio */
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
  const base = { 'Content-Security-Policy': CSP, 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'same-origin', 'Permissions-Policy': 'camera=(self), microphone=(), geolocation=()' };
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

/* ---------- Verificación pública de documentos (el QR de recibos, constancias y credenciales) ----------
   Cualquiera que lea el código QR puede comprobar que el documento es auténtico, sin iniciar sesión.
   Solo responde si el código del QR coincide con el registro, y devuelve únicamente lo que ya trae el documento impreso. */
const CAL_APROBATORIA = 8;   // calificación aprobatoria mínima (la misma que MINAP en la pantalla)
const ORDINAL = ['', 'primer', 'segundo', 'tercer', 'cuarto', 'quinto', 'sexto', 'séptimo', 'octavo', 'noveno', 'décimo', 'undécimo', 'duodécimo'];
function chkTxt(t) { t = String(t); let h = 2166136261; for (let i = 0; i < t.length; i++) { h ^= t.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return ('00000000' + h.toString(16)).slice(-8); }
function enmascara(m) { m = String(m || ''); return m.length > 3 ? '•'.repeat(m.length - 3) + m.slice(-3) : m; }
function hoyISO() { const d = new Date(Date.now() - 6 * 3600000); return d.toISOString().slice(0, 10); }   // hora del centro de México
function verificaDoc(t, id, code, vig, fecha) {
  const no = { ok: false, motivo: 'No se encontró un documento que coincida con este código. Si tienes el documento en papel, puede no ser auténtico.' };
  const nombreAl = sid => { const r = q.uno.get('students', sid); return r ? JSON.parse(r.data) : null; };
  if (t === 'c') {
    for (const r of q.lista.all('constancias')) {
      const x = ((JSON.parse(r.data).items) || []).find(i => String(i.num).toUpperCase() === id.toUpperCase());
      if (!x) continue;
      if (code !== chkTxt('C|' + x.num + '|' + x.mat + '|' + x.fecha)) return no;
      const conProm = (x.tipo || (x.prom != null ? 'promedio' : 'simple')) === 'promedio' && x.prom != null;
      return { ok: true, tipo: 'constancia', titulo: 'Constancia de estudios' + (conProm ? ' con promedio' : ''), folio: x.num, fecha: x.fecha, nombre: x.nombre, matricula: enmascara(x.mat), plan: x.plan, periodo: x.cuat ? (ORDINAL[x.cuat] || x.cuat + '.º') + ' cuatrimestre · ' + (x.per || '') : '', grupo: x.grupo || '', promedio: conProm ? Number(x.prom).toFixed(1) : null, dirigida: x.dest || 'A quien corresponda' };
    }
    return no;
  }
  if (t === 'v') {
    const dentro = (origen, nombre, folio, monto, fecha, metodo, estado) => ({ ok: true, tipo: 'recibo', titulo: 'Recibo de pago', origen, folio, fecha, monto: Number(monto), metodo, nombre, estado: estado !== 'pendiente' ? 'Pago registrado' : 'Transferencia pendiente de confirmar' });
    const buscar = (coleccion, sacar) => { for (const r of q.lista.all(coleccion)) { const d = JSON.parse(r.data); for (const g of sacar(d)) { if (String(g.folio || '').toUpperCase() === id.toUpperCase()) return { r, d, g }; } } return null; };
    let h = buscar('ledger', d => d.pagos || []);
    if (h) { if (code !== chkTxt(h.g.folio + '|' + Number(h.g.monto).toFixed(2) + '|' + h.g.fecha)) return no; const a = nombreAl(h.r.id); return dentro('Finanzas', a ? a.nombre : '', h.g.folio, h.g.monto, h.g.fecha, h.g.metodo, h.g.estado); }
    h = buscar('titulaciones', d => d.abonos || []);
    if (h) { if (code !== chkTxt(h.g.folio + '|' + Number(h.g.monto).toFixed(2) + '|' + h.g.fecha)) return no; return dentro('Titulaciones', [h.d.nombre, h.d.apPat, h.d.apMat].filter(Boolean).join(' '), h.g.folio, h.g.monto, h.g.fecha, h.g.metodo, h.g.estado); }
    h = buscar('acuerdo286', d => d.pagos || []);
    if (h) { if (code !== chkTxt(h.g.folio + '|' + Number(h.g.monto).toFixed(2) + '|' + h.g.fecha)) return no; return dentro('Acuerdo 286', [h.d.nombre, h.d.apPat, h.d.apMat].filter(Boolean).join(' '), h.g.folio, h.g.monto, h.g.fecha, h.g.metodo, h.g.estado); }
    return no;
  }
  if (t === 'b') {
    if (code !== chkTxt('B|' + id + '|' + vig + '|' + fecha)) return no;
    const a = nombreAl(id); if (!a) return no;
    const per = (vig[0] === 'S' ? 'Sep–Dic ' : vig[0] === 'E' ? 'Ene–Abr ' : 'May–Ago ') + vig.slice(1);
    const rc = q.uno.get('calif', id), items = (rc ? (JSON.parse(rc.data).items || []) : []).filter(x => x.per === per);
    if (!items.length) return { ok: false, motivo: 'El sistema no tiene calificaciones registradas de ese alumno en ese periodo. La boleta puede no ser auténtica.' };
    const grupo = q.lista.all('grupos').map(r => JSON.parse(r.data)).find(g => g.per === per && Array.isArray(g.alumnos) && g.alumnos.includes(id));
    const con = items.filter(x => x.cal != null), prom = con.length ? Math.round(con.reduce((t2, x) => t2 + x.cal, 0) / con.length * 10) / 10 : null;
    const cuat = (items.find(x => x.cuat) || {}).cuat || (grupo && grupo.cuat) || '';
    return { ok: true, tipo: 'boleta', titulo: 'Boleta de calificaciones', nombre: a.nombre, matricula: enmascara(a.mat), plan: a.programa || a.carrera || '', periodo: per, cuatrimestre: cuat ? String(cuat) : '', grupo: grupo ? String(grupo.num || '') : '', emitida: fecha.slice(0, 4) + '-' + fecha.slice(4, 6) + '-' + fecha.slice(6, 8), promedio: prom === null ? null : prom.toFixed(1), materias: items.slice().sort((x, y) => String(x.mat).localeCompare(String(y.mat))).map(x => ({ asignatura: x.mat, docente: x.doc || '', cal: x.cal == null ? null : x.cal, estatus: x.cal == null ? 'En curso' : (x.cal >= CAL_APROBATORIA ? 'Aprobada' : 'Reprobada') })) };
  }
  if (t === 'j') {
    for (const r of q.lista.all('justificantes')) {
      const x = JSON.parse(r.data);
      if (String(x.num).toUpperCase() !== id.toUpperCase()) continue;
      if (code !== chkTxt('J|' + x.num + '|' + x.sid + '|' + x.desde + '|' + x.hasta)) return no;
      if (x.estado !== 'Aprobado') return { ok: false, motivo: 'Este justificante existe, pero ya no está vigente en el sistema.' };
      return { ok: true, tipo: 'justificante', titulo: 'Justificante de inasistencia', folio: x.num, nombre: x.nombre, matricula: enmascara(x.mat), plan: x.plan || '', grupo: x.grupo || '', desde: x.desde, hasta: x.hasta, emitido: x.fecha || '' };
    }
    return no;
  }
  if (t === 'a') {
    if (code !== chkTxt('CR|' + id + '|' + vig)) return no;
    const a = nombreAl(id); if (!a) return no;
    const eg = q.uno.get('egresados', id), egresado = !!(eg && !JSON.parse(eg.data).revertido), v = vig.slice(0, 4) + '-' + vig.slice(4, 6) + '-' + vig.slice(6, 8);
    return { ok: true, tipo: 'credencial', titulo: 'Credencial de estudiante', nombre: a.nombre, matricula: enmascara(a.mat), plan: a.programa || a.carrera || '', vigencia: v, vigente: !egresado && v >= hoyISO(), egresado };
  }
  return no;
}

async function api(req, res, partes) {
  const m = req.method, [tipo, a, b] = partes, ip = ipDe(req);
  /* El aviso de Stripe llega sin sesión ni encabezados propios: se acepta solo con su firma */
  if (tipo === 'pagos-linea' && a === 'webhook' && m === 'POST') { if (limite('whk|' + ip, 300, 60000)) return responde(res, 429, { error: 'Demasiadas solicitudes' }); falla('whk|' + ip, 60000); return PL.webhook(req, res, leeCuerpo, responde); }
  if (m !== 'GET' && !req.headers['x-lafragua']) return responde(res, 403, { error: 'Solicitud no permitida' });
  if (!origenOk(req)) return responde(res, 403, { error: 'Origen no permitido' });

  /* --- públicas --- */
  if (tipo === 'yo' && m === 'GET') {
    const s = sesionDe(req), hay = q.nUsr.get().n > 0;
    return responde(res, 200, { modo: 'nube', urlPublica: String(ENV.LF_URL_PUBLICA || ''), setup: !hay, usuario: s ? Object.assign(publicoUsuario(s), { dosPasos: SEG.tiene(s.u), debeActivar2fa: s.rol === 'admin' && SEG.cfgSeg().exigir2fa && !SEG.tiene(s.u), privacidadPendiente: SEG.pendienteDe(s.u) }) : null, usuarios: s ? (s.rol === 'admin' ? listaUsuarios() : [publicoUsuario(s)]) : [{ u: '_', name: '', rol: 'consulta', doc: '' }] });
  }
  if (tipo === 'verificar' && m === 'GET') {
    if (limite('ver|' + ip, 60, 60000)) return responde(res, 429, { ok: false, motivo: 'Demasiadas consultas. Espera un minuto e inténtalo de nuevo.' });
    falla('ver|' + ip, 60000);
    const u = new URL(req.url, 'http://x').searchParams, t = u.get('t') || '', id = u.get('id') || '', code = (u.get('c') || '').toLowerCase(), vig = u.get('v') || '', fechaB = u.get('f') || '';
    if (!/^[vcabj]$/.test(t) || !/^[A-Za-z0-9_~-]{1,60}$/.test(id) || !/^[0-9a-f]{8}$/.test(code) || (t === 'a' && !/^\d{8}$/.test(vig)) || (t === 'b' && (!/^[SEM]\d{4}$/.test(vig) || !/^\d{8}$/.test(fechaB)))) return responde(res, 400, { ok: false, motivo: 'El código no es válido.' });
    res.setHeader('Cache-Control', 'no-store');
    return responde(res, 200, Object.assign({ consultado: new Date().toISOString() }, verificaDoc(t, id, code, vig, fechaB)));
  }
  if (tipo === 'login' && m === 'POST') {
    const c = await leeJSON(req), u = String(c.u || '').trim().toLowerCase(), clave = typeof c.clave === 'string' ? c.clave : '';
    if (limite('ip|' + ip, 30, 900000) || limite('u|' + ip + '|' + u, 5, 900000)) { audita(u, req, 'Inicio de sesión bloqueado por intentos'); return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos e inténtalo de nuevo.' }); }
    const usr = USUARIO_OK.test(u) ? q.usr.get(u) : null;
    let ok = false;
    if (usr) ok = claveOk(clave, usr); else hashClave(clave, 'sin-usuario-sal');
    if (!ok) { falla('ip|' + ip, 900000); falla('u|' + ip + '|' + u, 900000); audita(u, req, 'Inicio de sesión fallido'); await dormir(400); return responde(res, 401, { error: 'Usuario o contraseña incorrectos.' }); }
    if (usr.rol === 'alumno' && bloqueadoPorPago(usr.alumno)) { intentos.delete('u|' + ip + '|' + u); audita(usr.u, req, 'Inicio de sesión rechazado: acceso bloqueado por falta de pago'); return responde(res, 403, { error: MSG_BLOQUEO, bloqueado: true }); }
    intentos.delete('u|' + ip + '|' + u);
    if (usr.totp) return responde(res, 200, { requiere2fa: true, ticket: SEG.emiteTicket(usr.u) });
    nuevaSesion(req, res, usr.u); audita(usr.u, req, 'Inicio de sesión');
    return responde(res, 200, { usuario: publicoUsuario(usr) });
  }
  if (tipo === 'login2fa' && m === 'POST') {
    const c = await leeJSON(req, 2000);
    if (limite('f2|' + ip, 40, 900000)) return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos.' }); falla('f2|' + ip, 900000);
    try {
      const r = SEG.usaTicket(c.ticket, c.codigo), usr = q.usr.get(r.u); if (!usr) return responde(res, 401, { error: 'Usuario no encontrado.' });
      if (usr.rol === 'alumno' && bloqueadoPorPago(usr.alumno)) return responde(res, 403, { error: MSG_BLOQUEO, bloqueado: true });
      nuevaSesion(req, res, usr.u); audita(usr.u, req, 'Inicio de sesión con verificación en dos pasos' + (r.recuperacion ? ' (código de recuperación)' : ''));
      return responde(res, 200, { usuario: publicoUsuario(usr), recuperacion: r.recuperacion, restantes: SEG.restantes(usr.u) });
    } catch (e) { audita(null, req, 'Código de verificación incorrecto'); await dormir(300); return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); }
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
    const salt = crypto.randomBytes(16).toString('hex'); q.insUsr.run(u, nombre, 'admin', '', salt, hashClave(c.clave, salt), Date.now(), null);
    audita(u, req, hay ? 'Administrador restablecido por recuperación' : 'Configuración inicial: administrador creado'); nuevaSesion(req, res, u);
    return responde(res, 200, { ok: true });
  }

  /* --- requieren sesión --- */
  const s = sesionDe(req);
  if (!s) return responde(res, 401, { error: 'Sesión requerida' });
  const rol = s.rol;
  if (s.forzar && !['logout', 'cambiar-clave'].includes(tipo)) return responde(res, 403, { error: 'Debes cambiar tu contraseña antes de continuar.', forzar: true });
  if (s.rol === 'admin' && !['logout', 'cambiar-clave', '2fa', 'yo', 'privacidad'].includes(tipo) && SEG.cfgSeg().exigir2fa && !SEG.tiene(s.u)) return responde(res, 403, { error: 'La escuela exige la verificación en dos pasos para los administradores. Actívala para continuar.', requiere2fa: true });

  if (tipo === 'logout' && m === 'POST') { q.borSes.run(s._token); ponCookie(req, res, '', 0); audita(s.u, req, 'Cierre de sesión'); return responde(res, 200, { ok: true }); }

  if (tipo === 'eventos' && m === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive' });
    res.write('retry: 2000\n\n'); const cl = { res, s, u: s.u }; clientes.add(cl); req.on('close', () => clientes.delete(cl)); return;
  }
  if (tipo === 'col' && m === 'GET' && NOMBRE_OK.test(a || '')) {
    if (s.rol === 'alumno') {
      if (!eventoAlumno(s, a, null) && !['students', 'ledger', 'calif', 'constancias', 'egresados', 'fotos', 'grupos', 'materias', 'docentes', 'catalogo', 'solicitudes', 'justificantes', 'avisos', 'facturas', 'fiscal'].includes(a)) return responde(res, 200, { docs: [] });
      const ctx = contextoAlumno(s), docs = [];
      q.lista.all(a).forEach(r => { const d = filtraAlumno(s, a, r.id, JSON.parse(r.data), ctx); if (d) docs.push({ id: r.id, data: d }); });
      return responde(res, 200, { docs });
    }
    if (!puedeLeer(s, a, null)) return responde(res, 200, { docs: [] });
    return responde(res, 200, { docs: q.lista.all(a).filter(r => (a !== 'planeaciones' && a !== 'asistencia') || puedeLeer(s, a, r.id)).map(r => ({ id: r.id, data: reduce(s, a, JSON.parse(r.data)) })) });
  }
  if (tipo === 'doc' && NOMBRE_OK.test(a || '') && NOMBRE_OK.test(b || '')) {
    if (m === 'GET' && s.rol === 'alumno') { const r0 = q.uno.get(a, b), d0 = r0 ? filtraAlumno(s, a, b, JSON.parse(r0.data), contextoAlumno(s)) : null; return responde(res, 200, d0 ? { exists: true, data: d0 } : { exists: false, data: null }); }
    if (m === 'GET') { if (!puedeLeer(s, a, b)) return responde(res, 200, { exists: false, data: null }); const r = q.uno.get(a, b); return responde(res, 200, r ? { exists: true, data: reduce(s, a, JSON.parse(r.data)) } : { exists: false, data: null }); }
    if (s.rol === 'alumno' && a === 'solicitudes' && (m === 'PUT' || m === 'PATCH')) return guardaSolicitudAlumno(s, req, res, b, m);
    if (s.rol === 'alumno' && a === 'avisos' && m === 'PATCH') return guardaAvisoLeido(s, req, res, b);
    if (m === 'PUT' || m === 'PATCH' || m === 'DELETE') {
      if (!puedeEscribir(s, a, b)) { audita(s.u, req, 'Escritura denegada', m + ' ' + a + '/' + b); return responde(res, 403, { error: 'No tienes permiso para hacer esto.' }); }
      if (m === 'DELETE') { const r0 = q.uno.get(a, b); if (protegeBorrado(s, req, res, { accion: 'DELETE', col: a, id: b, viejo: r0 ? JSON.parse(r0.data) : null })) return; q.borra.run(a, b); difunde(a, b); cobHook(a, b); return responde(res, 200, { ok: true }); }
      let cuerpo; try { cuerpo = JSON.parse((await leeCuerpo(req, 6 * 1024 * 1024)).toString('utf8') || '{}'); } catch (e) { if (e.cod) throw e; return responde(res, 400, { error: 'JSON no válido' }); }
      if (cuerpo === null || typeof cuerpo !== 'object' || Array.isArray(cuerpo)) return responde(res, 400, { error: 'Se esperaba un objeto' });
      let nuevo = cuerpo; if (m === 'PATCH') { const r = q.uno.get(a, b); nuevo = Object.assign(r ? JSON.parse(r.data) : {}, cuerpo); }
      if (s.rol !== 'admin') { const r1 = q.uno.get(a, b); if (protegeBorrado(s, req, res, { accion: 'PUT', col: a, id: b, viejo: r1 ? JSON.parse(r1.data) : null, nuevo })) return; }
      /* Planeaciones: quien las sube no puede aprobarlas; si cambia sus archivos, vuelven a revisión */
      if (a === 'planeaciones' && s.rol !== 'admin' && (s.perm || {}).escolar !== 'editar') {
        const r2 = q.uno.get(a, b), viejo2 = r2 ? JSON.parse(r2.data) : {}, ids = x => ((x && x.files) || []).map(f => f.id).sort().join(',');
        ['estado', 'revisor', 'revFecha', 'motivo'].forEach(k => { if (viejo2[k] !== undefined) nuevo[k] = viejo2[k]; else delete nuevo[k]; });
        if (ids(nuevo) !== ids(viejo2) || (!viejo2.estado && ids(nuevo))) { if (ids(nuevo)) { nuevo.estado = 'pendiente'; delete nuevo.revisor; delete nuevo.revFecha; delete nuevo.motivo; } else { delete nuevo.estado; delete nuevo.revisor; delete nuevo.revFecha; delete nuevo.motivo; } }
      }
      /* Si el docente cambia sus puntos de evaluación, la planeación aprobada o denegada vuelve a revisión */
      let reabre = null;
      if (a === 'criterios' && s.rol !== 'admin' && (s.perm || {}).escolar !== 'editar') {
        const rc = q.uno.get(a, b), vc = rc ? JSON.parse(rc.data) : {}, rp = q.uno.get('planeaciones', b);
        if (rp && JSON.stringify(vc.items || []) !== JSON.stringify(nuevo.items || [])) { const dp = JSON.parse(rp.data); if (dp.estado === 'aprobada' || dp.estado === 'denegada') { dp.estado = 'pendiente'; delete dp.revisor; delete dp.revFecha; delete dp.motivo; reabre = dp; } }
      }
      /* Un periodo cerrado ya no admite cambios de calificaciones ni de asistencia (solo el Administrador lo puede reabrir) */
      if (s.rol !== 'admin') {
        if (a === 'asistencia') { const rm = q.uno.get('materias', b); let mm = null; try { mm = rm ? JSON.parse(rm.data) : null; } catch (e) {} if (mm && matCerrada(b)) return responde(res, 403, { error: 'Esa asignatura está cerrada (su bloque o el periodo ' + mm.per + '): la asistencia ya no se puede cambiar.' }); }
        if (a === 'calif') { const rv = q.uno.get('calif', b); let vv = {}; try { vv = rv ? JSON.parse(rv.data) : {}; } catch (e) {} const ci = d => ((d && d.items) || []).filter(i => i && ((i.per && perCerrado(i.per)) || (i.mid && matCerrada(i.mid)))).map(i => JSON.stringify(i)).sort().join('|'); if (ci(vv) !== ci(nuevo)) return responde(res, 403, { error: 'Hay calificaciones de un periodo cerrado: ya no se pueden cambiar. El Administrador puede reabrir el periodo.' }); }
        if (a === 'ciclos') { const rc2 = q.uno.get('ciclos', b); let vc = {}; try { vc = rc2 ? JSON.parse(rc2.data) : {}; } catch (e) {} const abiertos = Object.keys((vc.bloques || {})).filter(k => vc.bloques[k] && vc.bloques[k].cerrado && !((nuevo.bloques || {})[k] && nuevo.bloques[k].cerrado)); if ((vc.cerrado && !nuevo.cerrado) || abiertos.length) return responde(res, 403, { error: 'Solo el Administrador puede reabrir un periodo o un bloque.' }); }
      }
      /* Plazo para capturar calificaciones: 3 días después de la evaluación (o la prórroga que dé Control escolar). Solo rige para docentes */
      if (a === 'calif' && s.rol !== 'admin' && (s.perm || {}).escolar !== 'editar') {
        const rv2 = q.uno.get('calif', b); let v2 = {}; try { v2 = rv2 ? JSON.parse(rv2.data) : {}; } catch (e) {}
        const mapa = d => { const o = {}; ((d && d.items) || []).forEach(i => { if (i && i.id) o[i.id] = JSON.stringify(i); }); return o; }, A = mapa(v2), N = mapa(nuevo), hoyS = hoyMx();
        for (const k of new Set([...Object.keys(A), ...Object.keys(N)])) {
          if (A[k] === N[k]) continue; const it = JSON.parse(N[k] || A[k]), rm = it.mid ? q.uno.get('materias', it.mid) : null; let mm = null; try { mm = rm ? JSON.parse(rm.data) : null; } catch (e) {}
          if (mm && mm.ev) { const def = sumaDias(mm.ev, 3), lim = mm.prorroga && mm.prorroga > def ? mm.prorroga : def; if (hoyS > lim) return responde(res, 403, { error: 'El plazo para capturar las calificaciones de «' + mm.nom + '» venció el ' + lim.split('-').reverse().join('/') + '. Pide una prórroga a Control escolar.' }); }
        }
      }
      const viejoAv = (a === 'solicitudes' || a === 'planeaciones' || a === 'materias') ? q.uno.get(a, b) : null;
      q.pon.run(a, b, JSON.stringify(nuevo), Date.now()); difunde(a, b); cobHook(a, b);
      if (a === 'solicitudes' || (a === 'planeaciones' && (s.rol === 'admin' || (s.perm || {}).escolar === 'editar'))) { try { const vv = viejoAv ? JSON.parse(viejoAv.data) : null; if (a === 'solicitudes') AV.hookSolicitud(b, vv, nuevo); else AV.hookPlaneacion(b, vv, nuevo); } catch (e) { console.error('Avisos:', e.message); } }
      if (a === 'materias') { try { AV.hookEvaluacion(b, viejoAv ? JSON.parse(viejoAv.data) : null, nuevo); } catch (e) { console.error('Avisos:', e.message); } }
      if (reabre) { q.pon.run('planeaciones', b, JSON.stringify(reabre), Date.now()); difunde('planeaciones', b); }
      return responde(res, 200, { ok: true });
    }
  }
  if (tipo === 'lock' && m === 'POST' && NOMBRE_OK.test(a || '') && NOMBRE_OK.test(b || '')) {
    if (!puedeEscribir(s, a, b)) return responde(res, 403, { error: 'No tienes permiso para hacer esto.' });
    const c = await leeJSON(req, 10000), k = a + '/' + b, ahora = Date.now(), v = candados.get(k);
    if (!v || v.exp < ahora || v.holder === c.holder) { candados.set(k, { holder: String(c.holder || ''), exp: ahora + Math.min(Number(c.ttlMs) || 4000, 30000) }); return responde(res, 200, { acquired: true }); }
    return responde(res, 200, { acquired: false });
  }
  if (tipo === 'archivo') {
    const privSolicitado = req.headers['x-privado'] === '1';
    if (m === 'DELETE') { const inf = q.uArch.get(a || ''); if (!puedeArchivos(s, !!(inf && inf.privado))) return responde(res, 403, { error: 'No tienes permiso para quitar archivos.' }); if (inf && inf.privado && s.rol !== 'admin' && inf.dueno !== s.u && !(inf.cat === 'certificado' ? nivel(s, 'a286') === 'editar' : (inf.cat === 'planeacion' || inf.cat === 'solicitud' || inf.cat === 'resguardo') ? nivel(s, 'escolar') === 'editar' : nivel(s, 'expedientes') === 'editar')) return responde(res, 403, { error: 'Ese archivo no es tuyo.' }); }
    else if (s.rol === 'alumno') {
      /* Un alumno solo puede anexar comprobantes (PDF, JPG o PNG, hasta 10 MB) a sus solicitudes */
      if (m !== 'POST' || a || !privSolicitado || req.headers['x-categoria'] !== 'solicitud') return responde(res, 403, { error: 'No tienes permiso para subir archivos.' });
      if (!/^(application\/pdf|image\/jpeg|image\/png)/.test(String(req.headers['content-type'] || ''))) return responde(res, 400, { error: 'El archivo debe ser PDF, JPG o PNG.' });
      if (q.cuentaArch.get(s.u, Date.now() - 86400000).n >= 20) return responde(res, 429, { error: 'Subiste demasiados archivos hoy. Inténtalo mañana.' });
    }
    else if (!puedeArchivos(s, privSolicitado) && !(privSolicitado && req.headers['x-categoria'] === 'factura' && nivel(s, 'pagos') === 'editar')) return responde(res, 403, { error: 'No tienes permiso para subir archivos.' });
    if (m === 'DELETE' && ID_ARCH.test(a || '') && s.rol !== 'admin') { const inf2 = q.uArch.get(a); if (q.archRef.get('%' + a + '%') && protegeBorrado(s, req, res, { accion: 'ARCHIVO', col: 'archivo', id: a, descripcion: 'Eliminar el archivo «' + ((inf2 && inf2.nombre) || a) + '»' })) return; }
    const nombre = () => decodeURIComponent(String(req.headers['x-nombre'] || 'archivo')).slice(0, 200), mime = () => String(req.headers['content-type'] || 'application/octet-stream').slice(0, 100), priv = () => (req.headers['x-privado'] === '1' ? 1 : 0), cat = () => (['planeacion', 'solicitud', 'resguardo', 'certificado', 'contrato', 'factura'].includes(req.headers['x-categoria']) ? req.headers['x-categoria'] : '');
    if (m === 'POST' && !a) { const buf = await leeCuerpo(req, s.rol === 'alumno' ? 10 * 1024 * 1024 : 26 * 1024 * 1024), id = crypto.randomBytes(16).toString('hex'); fs.writeFileSync(path.join(ARCH, id), buf); q.ponArch.run(id, nombre(), mime(), buf.length, Date.now(), priv(), s.u, cat()); return responde(res, 200, { id, sizeBytes: buf.length }); }
    if (ID_ARCH.test(a || '')) {
      if (m === 'PUT') { const buf = await leeCuerpo(req, 26 * 1024 * 1024); fs.writeFileSync(path.join(ARCH, a), buf); q.ponArch.run(a, nombre(), mime(), buf.length, Date.now(), priv(), s.u, cat()); return responde(res, 200, { id: a, sizeBytes: buf.length }); }
      if (m === 'DELETE') { try { fs.unlinkSync(path.join(ARCH, a)); } catch (e) {} q.bArch.run(a); return responde(res, 200, { ok: true }); }
    }
  }

  /* --- usuarios y seguridad --- */
  if (tipo === 'usuarios') {
    if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador puede administrar usuarios.' });
    if (m === 'GET' && !a) return responde(res, 200, { usuarios: listaUsuarios() });
    /* Acceso de un alumno: usuario, estado y, si aún no la cambia, su contraseña inicial */
    if (m === 'GET' && a === 'alumno' && b && NOMBRE_OK.test(b)) {
      const r = q.usrDeAlumno.get(b);
      if (!r) return responde(res, 200, { tiene: false });
      const temporal = r.temporal ? descifra(r.temporal) : null;
      if (temporal) audita(s.u, req, 'Consultó la contraseña inicial de un alumno', 'usuario ' + r.u);
      return responde(res, 200, { tiene: true, u: r.u, forzar: !!r.forzar, temporal });
    }
    /* Accesos de alumnos: usuario y contraseña inicial (deben cambiarla al entrar) */
    if (m === 'POST' && a === 'alumnos') {
      const c = await leeJSON(req, 400000), items = Array.isArray(c.items) ? c.items.slice(0, 40) : [], hechos = [], omitidos = [];
      for (const it of items) {
        const u = String(it.u || '').trim().toLowerCase(), alumno = String(it.alumno || ''), nombre = String(it.name || '').trim().slice(0, 80), clave = String(it.clave || '');
        if (!USUARIO_OK.test(u)) { omitidos.push({ u, motivo: 'El usuario no es válido' }); continue; }
        if (!NOMBRE_OK.test(alumno) || !q.uno.get('students', alumno)) { omitidos.push({ u, motivo: 'El alumno no existe' }); continue; }
        const err = validaClave(clave, u); if (err) { omitidos.push({ u, motivo: err }); continue; }
        const ex = q.usr.get(u);
        if (ex && !(ex.rol === 'alumno' && ex.alumno === alumno)) { omitidos.push({ u, motivo: 'Ese usuario ya existe y pertenece a otra persona' }); continue; }
        const previo = q.usrAlumno.all().find(x => x.alumno === alumno && x.u !== u);
        if (previo) { omitidos.push({ u, motivo: 'El alumno ya tiene el usuario ' + previo.u }); continue; }
        const salt = crypto.randomBytes(16).toString('hex'), hash = await hashClaveAsync(clave, salt);
        q.insUsr.run(u, nombre || u, 'alumno', '', salt, hash, ex ? ex.creado : Date.now(), null); q.setAlumno.run(alumno, u); q.setForzar.run(1, u); q.setTemporal.run(cifra(clave), u);
        if (ex) q.borSesU.run(u);
        hechos.push(u);
      }
      audita(s.u, req, 'Accesos de alumnos', hechos.length + ' creados o restablecidos' + (omitidos.length ? ' · ' + omitidos.length + ' omitidos' : ''));
      return responde(res, 200, { ok: hechos, omitidos });
    }
    if (m === 'POST' && !a) {
      const c = await leeJSON(req), u = String(c.u || '').trim().toLowerCase(), nombre = String(c.name || '').trim().slice(0, 80), r = String(c.rol || ''), doc = String(c.doc || '');
      if (!USUARIO_OK.test(u)) return responde(res, 400, { error: 'El usuario solo puede llevar letras sin acentos, números, punto, guion y guion bajo (3 a 40 caracteres).' });
      if (!nombre) return responde(res, 400, { error: 'Escribe el nombre.' });
      if (!ROLES.includes(r)) return responde(res, 400, { error: 'Rol no válido.' });
      const ex = q.usr.get(u);
      if (ex && ex.rol === 'alumno') return responde(res, 400, { error: 'Los accesos de alumnos se administran desde «Accesos de alumnos».' });
      /* Si la solicitud no trae módulos (por ejemplo al restablecer una clave), se conservan los que ya tenía */
      const vm = (c.modulos === undefined && ex) ? { ok: true, valor: parseModulos(ex.modulos) } : validaModulos(c.modulos); if (!vm.ok) return responde(res, 400, { error: 'Los permisos de módulos no son válidos.' });
      const mods = r === 'admin' ? null : vm.valor;
      const docUsar = doc || ((c.modulos === undefined && ex) ? (ex.doc || '') : '');
      const necesitaDoc = r === 'docente' || !!(mods && mods.docente === 'editar');
      if (necesitaDoc && !docUsar) return responde(res, 400, { error: 'Elige el docente al que pertenece este usuario.' });
      if (ex && ex.rol === 'admin' && r !== 'admin' && q.nAdm.get().n < 2) return responde(res, 400, { error: 'Debe quedar al menos un administrador.' });
      if (!ex || c.clave) { const err = validaClave(c.clave, u); if (err) return responde(res, 400, { error: err }); }
      if (!ex) { const salt = crypto.randomBytes(16).toString('hex'); q.insUsr.run(u, nombre, r, necesitaDoc ? docUsar : '', salt, hashClave(c.clave, salt), Date.now(), mods ? JSON.stringify(mods) : null); audita(s.u, req, 'Usuario creado', u + ' (' + r + ')' + (mods ? ' · módulos: ' + Object.keys(mods).map(k => k + '=' + mods[k]).join(', ') : '')); }
      else {
        q.updUsr.run(nombre, r, necesitaDoc ? docUsar : '', mods ? JSON.stringify(mods) : null, u);
        if (c.clave) { const salt = crypto.randomBytes(16).toString('hex'); q.insUsr.run(u, nombre, r, necesitaDoc ? docUsar : '', salt, hashClave(c.clave, salt), ex.creado, mods ? JSON.stringify(mods) : null); q.borSesU.run(u); }
        audita(s.u, req, 'Usuario modificado', u + ' (' + r + ')' + (mods ? ' · módulos: ' + Object.keys(mods).map(k => k + '=' + mods[k]).join(', ') : '') + (c.clave ? ' · nueva contraseña' : ''));
        clientes.forEach(cl => { if (cl.u === u) { try { cl.res.end(); } catch (e) {} clientes.delete(cl); } });
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
    const salt = crypto.randomBytes(16).toString('hex'); q.insUsr.run(s.u, usr.nombre, usr.rol, usr.doc, salt, hashClave(c.nueva, salt), usr.creado, usr.modulos || null); q.borSesUmenos.run(s.u, s._token); q.setForzar.run(0, s.u); q.setTemporal.run(null, s.u);
    audita(s.u, req, 'Cambió su contraseña'); return responde(res, 200, { ok: true });
  }
  if (tipo === 'cobranza') return rutaCobranza(s, req, res, m, a);
  if (tipo === 'borrados') {
    if (m === 'GET' && !a) {
      if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador.' });
      const L = q.listaBor.all().map(vistaBorrado);
      return responde(res, 200, { pendientes: L.filter(x => x.estado === 'pendiente'), historial: L.filter(x => x.estado !== 'pendiente') });
    }
    const bo = a && NOMBRE_OK.test(a) ? q.getBor.get(a) : null;
    if (!bo) return responde(res, 404, { error: 'No existe esa solicitud.' });
    if (m === 'GET' && !b) { if (bo.u !== s.u && rol !== 'admin') return responde(res, 404, { error: 'No existe esa solicitud.' }); return responde(res, 200, vistaBorrado(bo)); }
    if (m === 'POST' && b === 'solicitar') {
      if (bo.u !== s.u) return responde(res, 403, { error: 'No es tu solicitud.' });
      if (bo.estado !== 'borrador') return responde(res, 409, { error: 'La solicitud ya fue enviada.' });
      q.pasaBor.run(Date.now(), bo.id); audita(s.u, req, 'Solicitó autorización para borrar', bo.descripcion); envioBorrado(s.u);
      return responde(res, 200, vistaBorrado(q.getBor.get(bo.id)));
    }
    if (m === 'POST' && b === 'clave') {
      if (bo.u !== s.u) return responde(res, 403, { error: 'No es tu solicitud.' });
      if (!['borrador', 'pendiente'].includes(bo.estado)) return responde(res, 409, { error: 'La solicitud ya fue resuelta.' });
      const c = await leeJSON(req), adm = q.admins.all();
      if (!adm.length) return responde(res, 409, { error: 'No hay un usuario administrador configurado.' });
      if (limite('aut|' + s.u, 5, 900000)) return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos.' });
      const hit = adm.find(x => claveOk(String(c.clave || ''), x));
      if (!hit) { falla('aut|' + s.u, 900000); audita(s.u, req, 'Autorización de borrado con contraseña fallida', bo.descripcion); await dormir(400); return responde(res, 403, { error: 'Contraseña del encargado incorrecta.' }); }
      q.updBor.run('aprobada', 'clave', hit.u, Date.now(), '', Date.now() + VENTANA_BORRADO, bo.id);
      audita(s.u, req, 'Borrado autorizado con la contraseña del encargado', bo.descripcion + ' · ' + hit.u); envioBorrado(s.u);
      return responde(res, 200, vistaBorrado(q.getBor.get(bo.id)));
    }
    if (m === 'POST' && b === 'resolver') {
      if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador puede aprobar o denegar.' });
      if (bo.estado !== 'pendiente') return responde(res, 409, { error: 'La solicitud ya fue resuelta.' });
      const c = await leeJSON(req), ap = c.accion === 'aprobar';
      if (!ap && c.accion !== 'denegar') return responde(res, 400, { error: 'Acción no válida.' });
      q.updBor.run(ap ? 'aprobada' : 'denegada', 'solicitud', s.u, Date.now(), String(c.motivo || '').slice(0, 200), ap ? Date.now() + VENTANA_BORRADO : null, bo.id);
      audita(s.u, req, ap ? 'Aprobó un borrado' : 'Denegó un borrado', bo.u + ': ' + bo.descripcion); envioBorrado(bo.u);
      return responde(res, 200, vistaBorrado(q.getBor.get(bo.id)));
    }
    return responde(res, 404, { error: 'No encontrado' });
  }
  if (tipo === 'autoriza-admin' && m === 'POST') {
    if (rol !== 'admin' && nivel(s, 'pagos') !== 'editar') return responde(res, 403, { error: 'No tienes permiso para hacer esto.' });
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

  /* Verificación en dos pasos de cada usuario */
  if (tipo === '2fa') {
    try {
      if (m === 'GET' && a === 'estado') return responde(res, 200, { activo: SEG.tiene(s.u), restantes: SEG.restantes(s.u), exigida: s.rol === 'admin' && SEG.cfgSeg().exigir2fa });
      if (m === 'POST' && a === 'iniciar') { if (SEG.tiene(s.u)) return responde(res, 400, { error: 'Ya tienes la verificación en dos pasos activa.' }); return responde(res, 200, SEG.iniciar(s.u)); }
      if (m === 'POST' && a === 'activar') { if (limite('2fa|' + s.u, 10, 900000)) return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos.' }); falla('2fa|' + s.u, 900000); const c = await leeJSON(req, 1000), cods = SEG.activar(s.u, c.codigo); audita(s.u, req, 'Activó la verificación en dos pasos'); return responde(res, 200, { ok: true, codigos: cods }); }
      if (m === 'POST' && (a === 'desactivar' || a === 'codigos')) {
        if (limite('2fa|' + s.u, 10, 900000)) return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos.' }); falla('2fa|' + s.u, 900000);
        const c = await leeJSON(req, 1000), f = q.usr.get(s.u); if (!f.totp) return responde(res, 400, { error: 'No tienes la verificación en dos pasos activa.' });
        if (!claveOk(String(c.clave || ''), f)) { await dormir(300); return responde(res, 403, { error: 'La contraseña no es correcta.' }); }
        SEG.usaTicket(SEG.emiteTicket(s.u), c.codigo);
        if (a === 'desactivar') { if (s.rol === 'admin' && SEG.cfgSeg().exigir2fa) return responde(res, 400, { error: 'La escuela exige la verificación en dos pasos para los administradores.' }); SEG.desactivar(s.u); audita(s.u, req, 'Desactivó la verificación en dos pasos'); return responde(res, 200, { ok: true }); }
        audita(s.u, req, 'Generó códigos de recuperación nuevos'); return responde(res, 200, { ok: true, codigos: SEG.regenerar(s.u) });
      }
    } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); }
  }
  /* Aviso de privacidad: cualquiera con sesión lo acepta */
  if (tipo === 'privacidad' && m === 'POST' && a === 'aceptar') { try { const c = await leeJSON(req, 500); SEG.aceptar(s.u, Number(c.version)); audita(s.u, req, 'Aceptó el aviso de privacidad', 'versión ' + c.version); return responde(res, 200, { ok: true }); } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); } }
  /* Seguridad y privacidad (solo el Administrador) */
  if (tipo === 'seguridad') {
    if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador.' });
    try {
      if (m === 'GET' && !a) return responde(res, 200, { config: SEG.cfgSeg(), usuarios: listaUsuarios().filter(x => x.rol !== 'alumno').map(x => ({ u: x.u, name: x.name, rol: x.rol, dosPasos: !!x.dosPasos })), privacidad: Object.assign(SEG.cfgPriv(), { aceptaciones: SEG.aceptaciones() }), conservacion: { config: SEG.cfgCons(), candidatos: SEG.candidatos() } });
      if (m === 'PUT' && a === 'config') { SEG.guardaSeg(await leeJSON(req, 500)); audita(s.u, req, 'Cambió la política de verificación en dos pasos'); return responde(res, 200, { ok: true, config: SEG.cfgSeg() }); }
      if (m === 'PUT' && a === 'privacidad') { SEG.guardaPriv(await leeJSON(req, 6000)); audita(s.u, req, 'Cambió el aviso de privacidad'); return responde(res, 200, { ok: true, privacidad: Object.assign(SEG.cfgPriv(), { aceptaciones: SEG.aceptaciones() }) }); }
      if (m === 'PUT' && a === 'conservacion') { SEG.guardaCons(await leeJSON(req, 1000)); audita(s.u, req, 'Cambió los plazos de conservación de datos'); return responde(res, 200, { ok: true, conservacion: { config: SEG.cfgCons(), candidatos: SEG.candidatos() } }); }
      if (m === 'POST' && a === 'reset') { const c = await leeJSON(req, 500), u = String(c.u || '').toLowerCase(); if (!USUARIO_OK.test(u) || !q.usr.get(u)) return responde(res, 404, { error: 'No existe ese usuario.' }); SEG.desactivar(u); audita(s.u, req, 'Reinició la verificación en dos pasos de un usuario', u); return responde(res, 200, { ok: true }); }
      if (m === 'POST' && a === 'depurar') {
        if (limite('dep|' + s.u, 5, 900000)) return responde(res, 429, { error: 'Demasiados intentos. Espera 15 minutos.' }); const c = await leeJSON(req, 2000);
        if (!claveOk(String(c.clave || ''), q.usr.get(s.u))) { falla('dep|' + s.u, 900000); await dormir(300); return responde(res, 403, { error: 'Tu contraseña no es correcta.' }); }
        const cats = (Array.isArray(c.categorias) ? c.categorias : []).filter(x => ['ine', 'firmasContrato', 'firmasFicha', 'mensajes', 'sesionesPago', 'auditoria'].includes(x)); if (!cats.length) return responde(res, 400, { error: 'Elige qué depurar.' });
        const r = SEG.depura(cats); audita(s.u, req, 'Depuró datos por plazo de conservación', JSON.stringify(r)); return responde(res, 200, { ok: true, resultado: r, conservacion: { config: SEG.cfgCons(), candidatos: SEG.candidatos() } });
      }
    } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); }
  }
  /* Pagos en línea (Stripe), datos fiscales y facturas */
  if (tipo === 'pagos-linea') {
    if (s.rol === 'alumno') {
      if (!s.alumno) return responde(res, 403, { error: 'No tienes un expediente de alumno.' });
      if (m === 'GET' && a === 'estado') return responde(res, 200, PL.estado(s.alumno));
      if (m === 'POST' && a === 'checkout') {
        if (limite('plk|' + s.u, 8, 60000)) return responde(res, 429, { error: 'Demasiados intentos. Espera un minuto.' }); falla('plk|' + s.u, 60000);
        const c = await leeJSON(req, 2000); try { return responde(res, 200, await PL.checkout(s.alumno, String(c.opcion || ''), req)); } catch (e) { return responde(res, e.cod || 502, { error: e.cod ? e.message : 'No se pudo iniciar el pago: ' + e.message }); }
      }
      return responde(res, 403, { error: 'No permitido.' });
    }
    const adm = rol === 'admin', ver = adm || nivel(s, 'pagos') !== 'none';
    if (!ver) return responde(res, 403, { error: 'No tienes permiso.' });
    if (m === 'GET' && !a) return responde(res, 200, { config: adm ? PL.cfgPublica(baseUrlReq(req)) : { activo: PL.cfg().activo }, sesiones: PL.sesiones(), esAdmin: adm });
    if (!adm) return responde(res, 403, { error: 'Solo el Administrador.' });
    if (m === 'PUT' && a === 'config') { try { PL.guardaCfg(await leeJSON(req, 5000)); audita(s.u, req, 'Cambió la configuración de pagos en línea'); return responde(res, 200, { ok: true, config: PL.cfgPublica(baseUrlReq(req)) }); } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); } }
    if (m === 'POST' && a === 'probar') { try { return responde(res, 200, Object.assign({ ok: true }, await PL.probar())); } catch (e) { return responde(res, 200, { ok: false, msg: e.message }); } }
  }
  if (tipo === 'fiscal') {
    try {
      if (s.rol === 'alumno' && m === 'PUT' && !a) { if (!s.alumno) return responde(res, 403, { error: 'No permitido.' }); PL.guardaFiscal(s.alumno, await leeJSON(req, 3000)); return responde(res, 200, { ok: true }); }
      if (s.rol !== 'alumno' && m === 'PUT' && a && NOMBRE_OK.test(a) && (rol === 'admin' || nivel(s, 'pagos') === 'editar')) { PL.guardaFiscal(a, await leeJSON(req, 3000)); audita(s.u, req, 'Editó los datos fiscales de un alumno', a); return responde(res, 200, { ok: true }); }
    } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); }
    return responde(res, 403, { error: 'No permitido.' });
  }
  if (tipo === 'facturas') {
    try {
      if (s.rol === 'alumno') { if (m === 'POST' && a === 'solicitar' && s.alumno) { const c = await leeJSON(req, 2000), f = PL.solicita(s.alumno, String(c.pagoId || '')); audita(s.u, req, 'Pidió una factura', f.folioPago); return responde(res, 200, { ok: true, id: f.id }); } return responde(res, 403, { error: 'No permitido.' }); }
      const ed = rol === 'admin' || nivel(s, 'pagos') === 'editar', ver = ed || nivel(s, 'pagos') !== 'none'; if (!ver) return responde(res, 403, { error: 'No tienes permiso.' });
      if (m === 'GET' && !a) return responde(res, 200, { facturas: PL.facturas(new URL(req.url, 'http://x').searchParams.get('estado') || ''), regimenes: PL.REGIMENES, usos: PL.USOS });
      if (!ed) return responde(res, 403, { error: 'No tienes permiso para emitir facturas.' });
      if (m === 'POST' && a === 'emitir') { const c = await leeJSON(req, 3000); return responde(res, 200, { ok: true, factura: PL.emitir(String(c.id || ''), c, s.u) }); }
      if (m === 'POST' && a === 'rechazar') { const c = await leeJSON(req, 3000); return responde(res, 200, { ok: true, factura: PL.rechaza(String(c.id || ''), c.motivo, s.u) }); }
    } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); }
  }
  /* Avisos por correo y WhatsApp */
  if (tipo === 'avisos') {
    const adm = rol === 'admin', staff = adm || (s.perm || {}).escolar === 'editar';
    if (!staff) return responde(res, 403, { error: 'No tienes permiso para los avisos.' });
    const limita = c => { if (adm) return c; const o = JSON.parse(JSON.stringify(c)); o.correo = { activo: c.correo.activo, usarRespaldos: c.correo.usarRespaldos }; o.whatsapp = { activo: c.whatsapp.activo }; o.resumen = { activo: c.resumen.activo, hora: c.resumen.hora, para: [] }; return o; };
    if (m === 'GET' && !a) return responde(res, 200, { config: limita(AV.cfgPublica()), resumen: AV.resumen(), esAdmin: adm });
    if (m === 'GET' && a === 'mensajes') { const u = new URL(req.url, 'http://x').searchParams; return responde(res, 200, { mensajes: AV.mensajes({ estado: u.get('estado') || '', canal: u.get('canal') || '', evento: u.get('evento') || '', q: u.get('q') || '', limite: u.get('limite') || 100 }) }); }
    if (m === 'PUT' && a === 'config') { if (!adm) return responde(res, 403, { error: 'Solo el Administrador.' }); try { AV.guardaCfg(await leeJSON(req, 20000)); audita(s.u, req, 'Cambió la configuración de avisos'); return responde(res, 200, { ok: true, config: AV.cfgPublica() }); } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); } }
    if (m === 'PUT' && a === 'sin') { const c = await leeJSON(req, 400000); const n = AV.setSin(Array.isArray(c.ids) ? c.ids : []); audita(s.u, req, 'Actualizó la lista de personas sin avisos', n + ' personas'); return responde(res, 200, { ok: true, total: n }); }
    if (m === 'POST' && a === 'probar') { if (!adm) return responde(res, 403, { error: 'Solo el Administrador.' }); const c = await leeJSON(req, 5000); try { await AV.probar(c.canal === 'whatsapp' ? 'whatsapp' : 'correo', c.para); return responde(res, 200, { ok: true, msg: 'Mensaje de prueba enviado.' }); } catch (e) { return responde(res, 200, { ok: false, msg: e.message }); } }
    if (m === 'POST' && a === 'enviar') { try { const c = await leeJSON(req, 20000), r = AV.enviarManual(s.u, c); if (!c.simular) { audita(s.u, req, 'Envió un aviso', (c.destino && c.destino.tipo) + ' · ' + r.personas + ' personas'); AV.procesa(40).catch(() => {}); } return responde(res, 200, r); } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); } }
    if (m === 'POST' && a === 'reintentar') { const c = await leeJSON(req, 20000); const n = AV.reintenta(c.todos ? 'todos' : c.ids); AV.procesa(40).catch(() => {}); return responde(res, 200, { ok: true, reintentados: n }); }
    if (m === 'POST' && a === 'procesar') { if (!adm) return responde(res, 403, { error: 'Solo el Administrador.' }); return responde(res, 200, await AV.procesa(100)); }
    if (m === 'POST' && a === 'diario') { if (!adm) return responde(res, 403, { error: 'Solo el Administrador.' }); const c = await leeJSON(req, 2000); const r = AV.diarios(c.job === 'resumen' ? 'resumen' : 'calificaciones'); AV.procesa(60).catch(() => {}); return responde(res, 200, r); }
  }
  /* Respaldos automáticos (solo el Administrador) */
  if (tipo === 'respaldos') {
    if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador.' });
    if (m === 'GET' && !a) return responde(res, 200, { config: cfgRespPublica(), estado: Object.assign(estResp(), { historial: (estResp().historial || []).slice(0, 15) }), locales: listaLocales(), bd: (() => { try { return fs.statSync(path.join(DATOS, 'lafragua.db')).size; } catch (e) { return 0; } })() });
    if (m === 'PUT' && a === 'config') { try { guardaCfgResp(await leeJSON(req, 20000)); audita(s.u, req, 'Cambió la configuración de respaldos'); return responde(res, 200, { ok: true, config: cfgRespPublica() }); } catch (e) { return responde(res, e.cod || 500, { error: e.cod ? e.message : 'Error interno' }); } }
    if (m === 'POST' && a === 'ejecutar') { if (estResp().corriendo) return responde(res, 409, { error: 'Ya hay un respaldo en curso.' }); audita(s.u, req, 'Pidió un respaldo ahora'); ejecutaRespaldo('manual', s.nombre || s.u).catch(x => console.error('Respaldo manual:', x.message)); return responde(res, 200, { ok: true, iniciado: true }); }
    if (m === 'POST' && a === 'restauracion') { audita(s.u, req, 'Probó la restauración de un respaldo'); return responde(res, 200, pruebaRestauracion()); }
    if (m === 'POST' && a === 'probar') {
      const c = cfgResp(), cuerpo = await leeJSON(req, 5000);
      try {
        if (cuerpo.destino === 's3') { if (!c.s3.endpoint || !c.s3.bucket || !c.s3.acceso || !c.s3.secreto) return responde(res, 400, { error: 'Guarda primero los datos del almacenamiento.' }); const tmp = path.join(TMP, 'prueba-' + crypto.randomBytes(4).toString('hex') + '.txt'); fs.writeFileSync(tmp, 'Prueba de conexión de la plataforma escolar · ' + new Date().toISOString()); try { await RESPA.s3Pon(c.s3, (c.s3.prefijo ? c.s3.prefijo.replace(/\/*$/, '/') : '') + 'prueba-de-conexion.txt', tmp, 'text/plain'); } finally { try { fs.unlinkSync(tmp); } catch (e) {} } return responde(res, 200, { ok: true, msg: 'Conexión correcta: se subió un archivo de prueba a «' + c.s3.bucket + '».' }); }
        if (cuerpo.destino === 'correo') { if (!c.correo.host || !c.correo.para.length) return responde(res, 400, { error: 'Guarda primero los datos del correo.' }); await RESPA.smtpEnvia(c.correo, { asunto: 'Prueba de correo · respaldos de la plataforma', texto: 'Si recibes este mensaje, los respaldos automáticos podrán avisarte y enviarte la copia de la base de datos.\n\nPlataforma escolar.' }); return responde(res, 200, { ok: true, msg: 'Correo de prueba enviado a ' + c.correo.para.join(', ') + '.' }); }
        return responde(res, 400, { error: 'Elige qué probar.' });
      } catch (e) { return responde(res, 200, { ok: false, msg: e.message }); }
    }
    if (m === 'GET' && a === 'descargar' && /^respaldo-\d{4}-\d{2}-\d{2}-\d{4}-[0-9a-f]{4}\.zip$/.test(b || '') && fs.existsSync(path.join(AUTO, b))) { audita(s.u, req, 'Descargó un respaldo del servidor', b); res.writeHead(200, { 'Content-Type': 'application/zip', 'Content-Disposition': 'attachment; filename="' + b + '"', 'Content-Length': fs.statSync(path.join(AUTO, b)).size, 'Cache-Control': 'no-store' }); fs.createReadStream(path.join(AUTO, b)).pipe(res); return; }
  }
  /* Fotografía del rostro del docente: él mismo la ve y la cambia (solo ese campo de su expediente) */
  if (tipo === 'docente' && a === 'foto') {
    const did = s.rol === 'docente' ? s.doc : '';
    if (!did || !NOMBRE_OK.test(did)) return responde(res, 403, { error: 'Solo un docente con su usuario puede cambiar su fotografía.' });
    const rg = q.uno.get('docentes_docs', did); let exp = {}; try { exp = rg ? JSON.parse(rg.data) : {}; } catch (e) { exp = {}; }
    if (m === 'GET') return responde(res, 200, { foto: exp.foto || null });
    if (m === 'PUT') {
      const c = await leeJSON(req, 400000), f = String(c.foto || '');
      if (!/^data:image\/jpeg;base64,[A-Za-z0-9+/]+=*$/.test(f) || f.length > 250000) return responde(res, 400, { error: 'La fotografía no es válida (debe ser una imagen JPG de tamaño normal).' });
      exp.foto = f; exp.fotoPor = s.u; exp.fotoFecha = new Date().toISOString();
      q.pon.run('docentes_docs', did, JSON.stringify(exp), Date.now()); difunde('docentes_docs', did);
      audita(s.u, req, 'Cambió su fotografía de perfil', 'docente ' + did);
      return responde(res, 200, { ok: true });
    }
  }
  /* Cobro de Acuerdo 286 desde Finanzas: solo agrega un pago a la inscripción (no toca documentos ni datos) */
  if (tipo === 'a286' && a === 'pago' && m === 'POST') {
    const P = s.perm || {};
    if (!(s.rol === 'admin' || P.pagos === 'editar' || P.a286 === 'editar')) return responde(res, 403, { error: 'No tienes permiso para registrar pagos de Acuerdo 286.' });
    const c = await leeJSON(req, 20000), g = (c.pago && typeof c.pago === 'object') ? c.pago : {}, id = String(c.id || '');
    const r0 = NOMBRE_OK.test(id) ? q.uno.get('acuerdo286', id) : null;
    if (!r0) return responde(res, 404, { error: 'No existe esa inscripción.' });
    const monto = Number(g.monto), cc = Array.isArray(g.cc) ? g.cc : [];
    const valido = typeof g.id === 'string' && /^[A-Za-z0-9]{4,40}$/.test(g.id) && /^\d{4}-\d{2}-\d{2}$/.test(String(g.fecha || '')) && monto > 0 && monto <= 100000 && ['Efectivo', 'Transferencia', 'Tarjeta', 'Depósito'].includes(g.metodo) && /^R286-\d{6}$/.test(String(g.folio || '')) && cc.length <= 40 && cc.every(x => typeof x === 'string' && /^[A-Za-z0-9]{1,12}$/.test(x)) && String(g.ref || '').length <= 120 && String(g.byn || '').length <= 80 && (g.estado === undefined || g.estado === 'pendiente') && ((g.metodo === 'Transferencia') === (g.estado === 'pendiente'));
    if (!valido) return responde(res, 400, { error: 'El pago no es válido.' });
    let d; try { d = JSON.parse(r0.data); } catch (e) { return responde(res, 500, { error: 'Error interno' }); }
    d.pagos = Array.isArray(d.pagos) ? d.pagos : [];
    if (d.pagos.some(x => x && (x.id === g.id || x.folio === g.folio))) return responde(res, 409, { error: 'Ese pago o ese folio ya están registrados.' });
    const nuevo = { id: g.id, fecha: g.fecha, monto: Math.round(monto * 100) / 100, metodo: g.metodo, ref: String(g.ref || ''), folio: g.folio, cc, byn: String(g.byn || '') };
    if (g.liq) nuevo.liq = 1; if (g.estado) nuevo.estado = 'pendiente';
    d.pagos.push(nuevo);
    q.pon.run('acuerdo286', id, JSON.stringify(d), Date.now()); difunde('acuerdo286', id);
    audita(s.u, req, 'Registró un pago de Acuerdo 286', g.folio + ' · ' + dinero(monto));
    return responde(res, 200, { ok: true });
  }
  if (tipo === 'almacenamiento' && m === 'GET') {
    if (rol !== 'admin') return responde(res, 403, { error: 'Solo el Administrador.' });
    const a1 = infoAlmacenamiento(), c = qCreada.get(), d = qUltDesc.get();
    return responde(res, 200, Object.assign(a1, { creada: c && c.f ? new Date(c.f).toISOString() : null, ultimaDescarga: d && d.f ? new Date(d.f).toISOString() : null, auto: resumenAuto(), respaldosEnServidor: (() => { try { return fs.readdirSync(RESP).filter(n => /^\d{4}-\d{2}-\d{2}$/.test(n)).length; } catch (e) { return 0; } })() }));
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
      const sBlob = sesionDe(req);
      if (!sBlob) { res.writeHead(401, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('Inicia sesión para ver este archivo.'); }
      const id = ruta.slice(7), f = path.join(ARCH, id);
      if (!ID_ARCH.test(id) || !fs.existsSync(f)) { res.writeHead(404); return res.end('No encontrado'); }
      const info = q.uArch.get(id) || {};
      const facturaPropia = info.cat === 'factura' && sBlob.rol === 'alumno' && q.lista.all('facturas').some(r => { try { const d = JSON.parse(r.data); return d.sid === sBlob.alumno && d.estado === 'emitida' && ((d.xml && d.xml.id === id) || (d.pdf && d.pdf.id === id)); } catch (e) { return false; } });
      const verPriv = sBlob.rol === 'admin' || info.dueno === sBlob.u || facturaPropia || (info.cat === 'factura' ? nivel(sBlob, 'pagos') !== 'none' : info.cat === 'certificado' ? nivel(sBlob, 'a286') === 'editar' : (info.cat === 'planeacion' || info.cat === 'solicitud' || info.cat === 'resguardo' || info.cat === 'contrato') ? nivel(sBlob, 'escolar') === 'editar' : nivel(sBlob, 'expedientes') !== 'none');
      if (info.privado && !verPriv) { res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('Este archivo es confidencial: solo lo puede ver el Administrador.'); }
      res.writeHead(200, { 'Content-Type': info.tipo || 'application/octet-stream', 'Content-Disposition': "inline; filename*=UTF-8''" + encodeURIComponent(info.nombre || id), 'Cache-Control': 'private, no-store' });
      return fs.createReadStream(f).pipe(res);
    }
    if (ruta === '/privacidad') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-cache' }); return res.end(SEG.paginaPrivacidad()); }
    const rel = ruta === '/' ? '/index.html' : (ruta === '/configurar' ? '/configurar.html' : (ruta === '/verificar' ? '/verificar.html' : ruta));
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
/* ---------- Precarga de planes de estudio ----------
   Los archivos .json de la carpeta «precarga» (el mismo formato de «Cargar contenido de las materias») se aplican UNA sola vez,
   al arrancar, y solo a los planes que todavía no tienen asignaturas. Nunca reemplazan ni borran lo que ya existe, y si después
   quitas materias no vuelven a aparecer. Para desactivarla: variable de entorno LF_SIN_PRECARGA=1. */
function precarga() {
  if (ENV.LF_SIN_PRECARGA === '1') return;
  const dir = path.join(__dirname, 'precarga');
  if (!fs.existsSync(dir)) return;
  for (const f of fs.readdirSync(dir).filter(x => /^[A-Za-z0-9_.-]+\.json$/.test(x)).sort()) {
    const marca = 'precarga-' + f.replace(/\.json$/, '');
    if (q.uno.get('meta', marca)) continue;
    let D; try { D = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); } catch (e) { continue; }
    if (!D || D.app !== 'colegiaturas-universidad-lafragua' || !D.colecciones || !D.colecciones.catalogo) continue;
    const hechos = [], omitidos = [];
    for (const k of Object.keys(D.colecciones.catalogo)) {
      if (!NOMBRE_OK.test(k)) continue;
      let cat = D.colecciones.catalogo[k], clave = k;
      /* Si el Administrador cambió el nombre de este plan, la carga se hace con el nombre nuevo */
      try { const pl = q.uno.get('config', 'plans'), ren = (pl && JSON.parse(pl.data).ren) || {}; if (cat && ren[cat.plan]) { const nuevo = String(ren[cat.plan]), kn = nuevo.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); if (kn && NOMBRE_OK.test(kn)) { clave = kn; cat = Object.assign({}, cat, { plan: nuevo }); } } } catch (e) {}
      /* Si el plan existe sin duración (0 colegiaturas) y la carga trae su duración, se fija (nunca pisa una duración ya definida) */
      try {
        const dur = Number(cat && cat.config && cat.config.n);
        if (dur > 0) { const pr = q.uno.get('config', 'plans'); if (pr) { const P = JSON.parse(pr.data), nm = (P.ren && P.ren[cat.plan]) || cat.plan, pl = (P.plans || []).find(x => x.k === nm); if (pl && Number(pl.n) === 0) { pl.n = dur; q.pon.run('config', 'plans', JSON.stringify(P), Date.now()); hechos.push(nm + ': duración fijada en ' + dur + ' colegiaturas'); } } }
      } catch (e) {}
      const previo = q.uno.get('catalogo', clave);
      if (previo && ((JSON.parse(previo.data).items) || []).length) { omitidos.push(clave); continue; }
      let n = 0;
      for (const it of (cat.items || [])) {
        const cd = D.contenidos && D.contenidos[it.id];
        if (cd && cd.txt && NOMBRE_OK.test(String(it.id)) && !q.uno.get('contenidos', String(it.id))) { q.pon.run('contenidos', String(it.id), JSON.stringify({ txt: String(cd.txt), pdf: null, ts: new Date().toISOString(), byn: 'Carga inicial del programa de estudios' }), Date.now()); n++; }
      }
      q.pon.run('catalogo', clave, JSON.stringify(cat), Date.now());
      hechos.push(clave + ' (' + (cat.items || []).length + ' asignaturas, ' + n + ' contenidos)');
    }
    q.pon.run('meta', marca, JSON.stringify({ fecha: new Date().toISOString(), cargados: hechos, omitidos }), Date.now());
    audita('sistema', null, 'Precarga de plan de estudios', f + ': ' + (hechos.join('; ') || 'nada que cargar') + (omitidos.length ? ' · ya tenían materias: ' + omitidos.join(', ') : ''));
    if (hechos.length) console.log('Precarga aplicada:', f, hechos.join('; '));
  }
}

let cobUltimaCorrida = '';
/* ---------- Cobranza: avisos de adeudo y bloqueo del acceso por falta de pago ----------
   Cuando un alumno con acceso a la plataforma debe `umbral` colegiaturas vencidas (2 por defecto), se le envía un aviso a su portal pidiéndole que
   pase a Control escolar; si pasados los plazos no hace ni un abono tras tres avisos, se bloquea su usuario. Solo actúa si el Administrador la activa. */
const TZ_MX = 'America/Mexico_City';
const fmtFechaMx = new Intl.DateTimeFormat('en-CA', { timeZone: TZ_MX, year: 'numeric', month: '2-digit', day: '2-digit' });
/* Solo para pruebas: LF_RELOJ_ARCHIVO apunta a un archivo con la fecha simulada (AAAA-MM-DD) */
const RELOJ_PRUEBA = ENV.LF_RELOJ_ARCHIVO || '';
const hoyMx = ms => { if (RELOJ_PRUEBA && !ms) { try { const t = fs.readFileSync(RELOJ_PRUEBA, 'utf8').trim(); if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return t; } catch (e) {} } return fmtFechaMx.format(new Date(ms || Date.now())); };
const horaMx = () => RELOJ_PRUEBA ? 12 : parseInt(new Intl.DateTimeFormat('en-GB', { timeZone: TZ_MX, hour: '2-digit', hourCycle: 'h23' }).format(new Date()), 10);
const sumaDias = (iso, n) => { const d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const dineroMx = n => '$' + Number(n).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fechaLargaMx = iso => new Date(iso + 'T12:00:00Z').toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
const MESES_C = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
const COB0 = { activa: false, umbral: 2, diaLimite: 10, intervaloDias: 7, graciaDias: 7, reinicioDias: 30 };
const MSG_BLOQUEO = 'Tu acceso a la plataforma se ha bloqueado por falta de pago. Para recuperarlo, pasa a Control escolar a regularizar tu situación. De no hacerlo, podría proceder una baja temporal.';
function leeDoc(col, id) { const r = q.uno.get(col, id); if (!r) return null; try { return JSON.parse(r.data); } catch (e) { return null; } }
function cobCfg() {
  const c = Object.assign({}, COB0, leeDoc('config', 'cobranza') || {});
  const n = (v, d, lo, hi) => { v = Math.floor(Number(v)); return Number.isFinite(v) ? Math.min(Math.max(v, lo), hi) : d; };
  return { activa: c.activa === true, umbral: n(c.umbral, 2, 1, 12), diaLimite: n(c.diaLimite, 10, 1, 28), intervaloDias: n(c.intervaloDias, 7, 1, 60), graciaDias: n(c.graciaDias, 7, 1, 60), reinicioDias: n(c.reinicioDias, 30, 0, 365) };
}
const mesAnioC = (k, ing) => { const t = 8 + k - 1; return MESES_C[t % 12] + ' ' + (ing + Math.floor(t / 12)); };
const cicloMx = hoy => { const y = +hoy.slice(0, 4), m = +hoy.slice(5, 7); return m >= 9 ? y : y - 1; };
function fechaLimiteCol(k, ing, dia) { const t = 8 + k - 1, y = ing + Math.floor(t / 12), m = (t % 12) + 1; return y + '-' + String(m).padStart(2, '0') + '-' + String(dia).padStart(2, '0'); }
/* Misma regla de cargos que la pantalla: inscripción, reinscripciones, colegiaturas mensuales, titulación, extraordinarios y constancias (con beca) */
function cargosAlumnoSrv(st, planes, EXTRA, cal, con, hoy) {
  const P = (planes || []).find(p => p.k === st.programa) || null;
  let L = [];
  if (!P) L.push({ id: 'c0', c: 'Colegiatura', m: st.total || 0 });
  else {
    const ing = st.ingreso || cicloMx(hoy), C = Math.ceil(P.n / 4); let k = 0;
    if (st.nuevo !== false && P.ins > 0) L.push({ id: 'i', c: 'Inscripción', m: P.ins });
    for (let q2 = 1; q2 <= C; q2++) {
      if (q2 > 1 && P.rein > 0) L.push({ id: 'r' + q2, c: 'Reinscripción cuatrimestre ' + q2 + ' (' + mesAnioC(4 * (q2 - 1) + 1, ing) + ')', m: P.rein });
      for (let i = 0; i < 4 && k < P.n; i++) { k++; L.push({ id: 'c' + k, c: 'Colegiatura ' + mesAnioC(k, ing), k, m: P.col }); }
    }
    if (P.tit > 0) L.push({ id: 't', c: 'Pago de derecho a título', m: P.tit });
  }
  if (EXTRA && EXTRA.costo > 0) (cal.items || []).filter(x => x.cal != null && x.cal < EXTRA.min && (!x.hist || x.exCobro)).forEach(x => L.push({ id: 'x' + x.mid, c: 'Examen extraordinario: ' + x.mat + ' (' + x.per + ')', m: EXTRA.costo }));
  (con.items || []).forEach(x => L.push({ id: 'k' + x.id, c: 'Constancia de estudios (' + x.num + ')', m: x.monto }));
  const b = st.beca;
  if (b && b.monto > 0) L = L.map(x => /^Colegiatura/.test(x.c) ? Object.assign({}, x, { m: Math.max(Math.round((x.m - b.monto) * 100) / 100, 0) }) : x);
  return L;
}
function restanteCargos(L, pagos) {
  const rem = L.map(c => c.m), primero = () => rem.findIndex(r => r > 0.004);
  (pagos || []).filter(g => g.estado !== 'pendiente').forEach(g => {
    let amt = Number(g.monto) || 0; const pon = i => { const t = Math.min(amt, rem[i]); if (t <= 0.004) return; rem[i] -= t; amt -= t; };
    (g.cc || []).forEach(lab => { if (amt > 0.004) { const i = L.findIndex(c => c.id === lab); if (i > -1) pon(i); } });
    let j; while (amt > 0.004 && (j = primero()) > -1) pon(j);
  });
  return rem;
}
function planesYExtra() { const d = leeDoc('config', 'plans') || {}; return { planes: d.plans || [], extra: d.extra || { costo: 300, min: 8 } }; }
function acuerdoVigenteSrv(sid, hoy, pagos) {
  const conf = pid => { const g = pagos.find(p => p.id === pid); return !g || g.estado !== 'pendiente'; };
  const ok = x => !!x.pagada && (!x.pid || conf(x.pid));
  return q.lista.all('acuerdos').some(r => {
    try { const a = JSON.parse(r.data); if (a.sid !== sid || a.cancelado) return false; const c = a.cuotas || []; if (c.length && c.every(ok)) return false; if (c.some(x => !ok(x) && x.fecha < hoy)) return false; return true; } catch (e) { return false; }
  });
}
function adeudoDe(sid, hoy, cfg, pe) {
  const st = leeDoc('students', sid); if (!st) return null;
  const led = leeDoc('ledger', sid) || { pagos: [] }, cal = leeDoc('calif', sid) || { items: [] }, con = leeDoc('constancias', sid) || { items: [] };
  const ing = st.ingreso || cicloMx(hoy), L = cargosAlumnoSrv(st, pe.planes, pe.extra, cal, con, hoy), rem = restanteCargos(L, led.pagos || []), meses = [];
  L.forEach((c, i) => { if (c.k && rem[i] > 0.004) { const v = fechaLimiteCol(c.k, ing, cfg.diaLimite); if (v < hoy) meses.push({ c: c.c, rem: Math.round(rem[i] * 100) / 100, vence: v }); } });
  return { st, pagos: led.pagos || [], n: meses.length, total: Math.round(meses.reduce((a, x) => a + x.rem, 0) * 100) / 100, meses };
}
function textoAviso(n, est, ad, cfg, hoy) {
  const nom = String(est.nombre || '').trim().split(/\s+/)[0] || '', k = ad.n, lista = ad.meses.map(m => m.c.replace(/^Colegiatura /, '') + ': ' + dineroMx(m.rem)).join('; ');
  const base = 'a la fecha tienes adeudo de ' + k + (k === 1 ? ' colegiatura' : ' colegiaturas') + ' (' + lista + '), por un total de ' + dineroMx(ad.total) + '.';
  if (n === 1) return { titulo: 'Aviso de adeudo', mensaje: 'Hola, ' + nom + '. De acuerdo con nuestros registros, ' + base + ' Te pedimos amablemente que pases a Control escolar a realizar tu pago o, al menos, un abono para regularizar tu situación. ¡Gracias por tu apoyo!' };
  if (n === 2) return { titulo: 'Recordatorio de adeudo (2 de 3)', mensaje: 'Hola, ' + nom + '. Te recordamos que ' + base + ' Aún no registramos tu pago ni un abono. Te invitamos amablemente a pasar a Control escolar para regularizar tu situación.' };
  return { titulo: 'Último aviso de adeudo (3 de 3)', mensaje: 'Hola, ' + nom + '. Este es tu último aviso: ' + base + ' Si antes del ' + fechaLargaMx(sumaDias(hoy, cfg.graciaDias)) + ' no pasas a Control escolar a realizar al menos un abono, tu usuario y contraseña de la plataforma se bloquearán por falta de pago y, de no regularizar tu situación, podría proceder una baja temporal.' };
}
function guardaAviso(id, doc) { q.pon.run('avisos', id, JSON.stringify(doc), Date.now()); difunde('avisos', id); try { AV.hookAviso(id, doc); } catch (e) { console.error('Avisos:', e.message); } }
function bloqueadoPorPago(sid) { if (!sid) return false; const d = leeDoc('cobranza', sid); return !!(d && d.estado === 'bloqueado'); }
/* Evalúa a un alumno. opciones: { simular } no escribe nada; { alivio } solo permite cerrar avisos o desbloquear (cuando se registra un pago). Devuelve la acción propuesta/ejecutada. */
function evaluaAlumnoCob(sid, ctx, op) {
  op = op || {};
  const { hoy, cfg, pe } = ctx, cuentas = q.usrDeAlumno.all(sid); if (!cuentas.length) return null;
  const ad = adeudoDe(sid, hoy, cfg, pe); if (!ad) return null;
  const previo = leeDoc('cobranza', sid), est = Object.assign({ sid, estado: 'ok', ciclo: 0, avisos: [] }, previo || {});
  est.mat = ad.st.mat; est.nombre = ad.st.nombre; est.plan = ad.st.programa || ad.st.carrera || ''; est.adeudo = { n: ad.n, total: ad.total, meses: ad.meses }; est.revisado = hoy;
  const eg = leeDoc('egresados', sid), egresado = !!(eg && !eg.revertido), acVig = !est.exento && !egresado && acuerdoVigenteSrv(sid, hoy, ad.pagos), exento = !!est.exento || egresado || acVig, motivoEx = est.exento ? 'manual' : egresado ? 'egresado' : acVig ? 'acuerdo de pago vigente' : '';
  const abonoDesde = f => ad.pagos.some(g => g.estado !== 'rechazado' && Number(g.monto) > 0 && String(g.confFecha || g.fecha || '') >= f);
  let accion = '';
  if (est.estado === 'bloqueado') {
    if (exento || ad.n < cfg.umbral) accion = 'desbloqueo:' + (exento ? 'exento' : 'al corriente');
    else if (abonoDesde(est.bloqueadoEn || hoy)) accion = 'desbloqueo:abono';
  } else if (est.estado === 'avisando') {
    const av = est.avisos || [];
    if (exento) accion = 'cierre:exento';
    else if (ad.n < cfg.umbral) accion = 'cierre:al corriente';
    else if (abonoDesde(est.inicio || hoy)) accion = 'cierre:abono';
    else if (!op.alivio && av.length < 3 && hoy >= sumaDias(av[av.length - 1].fecha, cfg.intervaloDias)) accion = 'aviso';
    else if (!op.alivio && av.length >= 3 && hoy >= sumaDias(av[2].fecha, cfg.graciaDias)) accion = 'bloqueo';
  } else {
    const pausa = est.cerrado && est.cerrado.fecha && hoy < sumaDias(est.cerrado.fecha, cfg.reinicioDias);
    if (!op.alivio && !exento && ad.n >= cfg.umbral && !pausa && !abonoDesde(hoy)) accion = 'inicio';
  }
  const resumen = { sid, mat: est.mat, nombre: est.nombre, plan: est.plan, adeudo: est.adeudo, estado: est.estado, ciclo: est.ciclo, avisos: est.avisos, bloqueadoEn: est.bloqueadoEn || null, cerrado: est.cerrado || null, exento: exento, motivoExento: motivoEx, exentoInfo: est.exento || null, accion };
  if (op.simular) return resumen;
  const [tipo, motivo] = accion.split(':');
  if (tipo === 'inicio') { est.estado = 'avisando'; est.ciclo = (previo ? previo.ciclo || 0 : 0) + 1; est.inicio = hoy; est.avisos = []; delete est.cerrado; }
  if (tipo === 'inicio' || tipo === 'aviso') {
    const n = (est.avisos || []).length + 1, t = textoAviso(n, est, ad, cfg, hoy), id = sid + '-' + est.ciclo + '-' + n;
    guardaAviso(id, { sid, tipo: 'adeudo', n, ciclo: est.ciclo, fecha: hoy, creada: new Date().toISOString(), titulo: t.titulo, mensaje: t.mensaje, meses: ad.meses, total: ad.total, leida: false });
    est.avisos = (est.avisos || []).concat([{ n, fecha: hoy, id }]); audita(null, null, 'Cobranza: aviso ' + n + ' de 3', est.mat + ' · ' + est.nombre + ' · adeuda ' + ad.n + ' colegiaturas');
  } else if (tipo === 'bloqueo') {
    est.estado = 'bloqueado'; est.bloqueadoEn = hoy; cuentas.forEach(c => q.borSesU.run(c.u));
    audita(null, null, 'Cobranza: acceso bloqueado por falta de pago', est.mat + ' · ' + est.nombre);
  } else if (tipo === 'cierre' || tipo === 'desbloqueo') {
    const bloq = est.estado === 'bloqueado'; est.estado = 'ok'; est.cerrado = { fecha: hoy, motivo }; delete est.bloqueadoEn;
    if (bloq) { guardaAviso(sid + '-' + est.ciclo + '-d' + Date.now(), { sid, tipo: 'info', n: 0, ciclo: est.ciclo, fecha: hoy, creada: new Date().toISOString(), titulo: 'Acceso restablecido', mensaje: 'Gracias por pasar a regularizar tu situación. Tu acceso a la plataforma está activo de nuevo.', leida: false }); audita(null, null, 'Cobranza: acceso restablecido (' + motivo + ')', est.mat + ' · ' + est.nombre); }
  }
  const previoTxt = previo ? JSON.stringify(previo) : '';
  if (!previo && ad.n === 0 && !accion) return resumen;
  if (JSON.stringify(est) !== previoTxt) { q.pon.run('cobranza', sid, JSON.stringify(est), Date.now()); difunde('cobranza', sid); }
  resumen.estado = est.estado; resumen.avisos = est.avisos; resumen.bloqueadoEn = est.bloqueadoEn || null; resumen.cerrado = est.cerrado || null;
  return resumen;
}
function ctxCobranza() { return { hoy: hoyMx(), cfg: cobCfg(), pe: planesYExtra() }; }
function sidsConAcceso() { const set = new Set(); q.usrAlumno.all().forEach(u => { if (u.alumno) set.add(u.alumno); }); return [...set]; }
function corridaCobranza(op) {
  const ctx = ctxCobranza(), out = []; if (!ctx.cfg.activa && !(op && op.simular)) return { activa: false, acciones: [] };
  sidsConAcceso().forEach(sid => { try { const r = evaluaAlumnoCob(sid, ctx, op); if (r && r.accion) out.push(r); } catch (e) { console.error('Cobranza (' + sid + '):', e.message); } });
  return { activa: ctx.cfg.activa, acciones: out };
}
/* ---------- Avisos fuera de la plataforma (correo y WhatsApp) ---------- */
const AV = require('./avisos.js').crea({ db, q, leeDoc, cifra, descifra, smtpEnvia: RESPA.smtpEnvia, hoyMx: () => hoyMx(), horaMx: () => RESPA.fechaMx(new Date()).hora, audita, cfgCorreoRespaldos: () => cfgResp().correo, ENV });
/* ---------- Pagos en línea y facturas ---------- */
const baseUrlReq = req => { const h = String(req.headers['x-forwarded-host'] || req.headers.host || ''); return (String(req.headers['x-forwarded-proto'] || 'http').split(',')[0]) + '://' + h; };
function pendientesSrv(sid) {
  const st = leeDoc('students', sid); if (!st) return null;
  const hoy = hoyMx(), pe = planesYExtra(), cfg = cobCfg(), led = leeDoc('ledger', sid) || { pagos: [] }, cal = leeDoc('calif', sid) || { items: [] }, con = leeDoc('constancias', sid) || { items: [] };
  const ing = st.ingreso || cicloMx(hoy), L = cargosAlumnoSrv(st, pe.planes, pe.extra, cal, con, hoy), rem = restanteCargos(L, led.pagos || []), pend = [];
  L.forEach((c, i) => { if (rem[i] > 0.004) pend.push({ id: c.id, c: c.c, monto: Math.round(rem[i] * 100) / 100, vencido: !!(c.k && fechaLimiteCol(c.k, ing, cfg.diaLimite) < hoy) }); });
  return { st, hoy, pend };
}
function avisaAlumnoSrv(evento, sid, titulo, mensaje, ref) {
  const id = sid + '-' + String(ref || Date.now()).replace(/[^A-Za-z0-9:_-]/g, '_');
  if (!q.uno.get('avisos', id)) { q.pon.run('avisos', id, JSON.stringify({ sid, tipo: 'info', n: 0, fecha: hoyMx(), creada: new Date().toISOString(), titulo, mensaje, leida: false }), Date.now()); difunde('avisos', id); }
  try { AV.avisaAlumno(evento, sid, titulo, mensaje, ref); } catch (e) { console.error('Avisos:', e.message); }
}
const PL = require('./pagoslinea.js').crea({ q, leeDoc, cifra, descifra, hoyMx: () => hoyMx(), audita, difunde, cobHook: (c, i) => cobHook(c, i), pendientesSrv, avisaAlumno: avisaAlumnoSrv, candados, ENV });
/* ---------- Seguridad y privacidad ---------- */
const SEG = require('./seguridad.js').crea({ db, q, leeDoc, cifra, descifra, audita, claveOk, ARCH, difunde, hoyMx: () => hoyMx(), ENV }); SEG.reiniciarPorEntorno();
const cobPend = new Set(); let cobTodos = false, cobTimer = null;
function cobHook(col, id) {
  if (!['ledger', 'students', 'calif', 'constancias', 'acuerdos', 'config', 'egresados'].includes(col)) return;
  if (col === 'config') { if (id !== 'plans' && id !== 'cobranza') return; cobTodos = true; if (id === 'cobranza') cobUltimaCorrida = ''; }
  else if (col === 'acuerdos') { const a = leeDoc('acuerdos', id); if (a && a.sid) cobPend.add(a.sid); else cobTodos = true; }
  else cobPend.add(id);
  clearTimeout(cobTimer);
  cobTimer = setTimeout(() => {
    try {
      const ctx = ctxCobranza(); if (!ctx.cfg.activa) { cobPend.clear(); cobTodos = false; return; }
      const sids = cobTodos ? sidsConAcceso() : [...cobPend]; cobPend.clear(); cobTodos = false;
      sids.forEach(sid => { try { evaluaAlumnoCob(sid, ctx, { alivio: true }); } catch (e) { console.error('Cobranza (' + sid + '):', e.message); } });
    } catch (e) { console.error('Cobranza:', e.message); }
  }, 2500); cobTimer.unref && cobTimer.unref();
}
function programaCobranza() {
  const rev = () => { try { const hoy = hoyMx(); if (hoy !== cobUltimaCorrida && horaMx() >= 7) { cobUltimaCorrida = hoy; corridaCobranza({}); } } catch (e) { console.error('Cobranza:', e.message); } };
  setTimeout(rev, 45000).unref(); setInterval(rev, 15 * 60000).unref();
}
function guardaAvisoLeido(s, req, res, id) {
  return leeJSON(req).then(c => {
    const d = leeDoc('avisos', id); if (!d || d.sid !== s.alumno) return responde(res, 403, { error: 'No es tu aviso.' });
    if (!c || Object.keys(c).some(k => k !== 'leida') || typeof c.leida !== 'boolean') return responde(res, 403, { error: 'Solo puedes marcar tus avisos como leídos.' });
    d.leida = c.leida; q.pon.run('avisos', id, JSON.stringify(d), Date.now()); difunde('avisos', id); return responde(res, 200, { ok: true });
  });
}
async function rutaCobranza(s, req, res, m, a) {
  const P = s.perm || {}, esAdm = s.rol === 'admin', ver = esAdm || (P.pagos && P.pagos !== 'none'), edita = esAdm || P.pagos === 'editar';
  if (s.rol === 'alumno' || !ver) return responde(res, 403, { error: 'No tienes permiso para ver la cobranza.' });
  if (m === 'GET' && a === 'vista') {
    const ctx = ctxCobranza(), filas = [];
    sidsConAcceso().forEach(sid => { try { const r = evaluaAlumnoCob(sid, ctx, { simular: true }); if (r) filas.push(r); } catch (e) {} });
    return responde(res, 200, { cfg: ctx.cfg, hoy: ctx.hoy, filas });
  }
  if (m === 'POST' && a === 'accion') {
    const c = await leeJSON(req), ac = String(c.accion || ''), sid = String(c.sid || ''), ctx = ctxCobranza(), hoy = ctx.hoy;
    if (ac === 'evaluar') {
      if (!esAdm) return responde(res, 403, { error: 'Solo el Administrador puede ejecutar la revisión.' });
      if (!ctx.cfg.activa) return responde(res, 409, { error: 'La cobranza automática está desactivada.' });
      const r = corridaCobranza({}); audita(s.u, req, 'Cobranza: revisión manual', r.acciones.length + ' acciones'); return responde(res, 200, { ok: true, acciones: r.acciones.length });
    }
    const st = leeDoc('students', sid); if (!st || !q.usrDeAlumno.all(sid).length) return responde(res, 404, { error: 'No se encontró al alumno o no tiene acceso a la plataforma.' });
    const est = Object.assign({ sid, estado: 'ok', ciclo: 0, avisos: [] }, leeDoc('cobranza', sid) || {}); est.mat = st.mat; est.nombre = st.nombre;
    if (ac === 'desbloquear') {
      if (!edita) return responde(res, 403, { error: 'No tienes permiso para desbloquear.' });
      if (est.estado !== 'bloqueado') return responde(res, 409, { error: 'Ese alumno no está bloqueado.' });
      est.estado = 'ok'; est.cerrado = { fecha: hoy, motivo: 'desbloqueo manual (' + s.name + ')' }; delete est.bloqueadoEn;
      guardaAviso(sid + '-' + est.ciclo + '-d' + Date.now(), { sid, tipo: 'info', n: 0, ciclo: est.ciclo, fecha: hoy, creada: new Date().toISOString(), titulo: 'Acceso restablecido', mensaje: 'Control escolar restableció tu acceso a la plataforma. Te recordamos pasar a regularizar tus pagos.', leida: false });
      audita(s.u, req, 'Cobranza: acceso desbloqueado manualmente', st.mat + ' · ' + st.nombre);
    } else if (ac === 'exentar') {
      if (!esAdm) return responde(res, 403, { error: 'Solo el Administrador puede exentar a un alumno.' });
      const motivo = String(c.motivo || '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, 160); if (motivo.length < 3) return responde(res, 400, { error: 'Escribe el motivo de la exención.' });
      est.exento = { por: s.name, fecha: hoy, motivo }; if (est.estado !== 'ok') { est.estado = 'ok'; est.cerrado = { fecha: hoy, motivo: 'exención' }; delete est.bloqueadoEn; }
      audita(s.u, req, 'Cobranza: alumno exento', st.mat + ' · ' + motivo);
    } else if (ac === 'quitar-exencion') {
      if (!esAdm) return responde(res, 403, { error: 'Solo el Administrador puede quitar la exención.' });
      delete est.exento; audita(s.u, req, 'Cobranza: exención retirada', st.mat);
    } else return responde(res, 400, { error: 'Acción no reconocida.' });
    q.pon.run('cobranza', sid, JSON.stringify(est), Date.now()); difunde('cobranza', sid);
    return responde(res, 200, { ok: true });
  }
  return responde(res, 404, { error: 'No existe.' });
}

/* ---------- Dónde viven los datos: aviso si el disco es temporal ---------- */
function leeMontajes() {
  const arch = ENV.LF_MOUNTINFO_ARCHIVO || '/proc/self/mountinfo';
  const dec = s => String(s).replace(/\\([0-7]{3})/g, (m, o) => String.fromCharCode(parseInt(o, 8)));
  return fs.readFileSync(arch, 'utf8').split('\n').filter(Boolean).map(l => { const p = l.split(' '), g = p.indexOf('-'); return { punto: dec(p[4]), fs: p[g + 1], fuente: p[g + 2] }; });
}
function infoAlmacenamiento() {
  const r = { persistente: null, montaje: '', sistema: '', ruta: DATOS, motivo: '' };
  if (ENV.LF_DISCO_OK === '1') { r.persistente = true; r.motivo = 'Confirmado por LF_DISCO_OK.'; return r; }
  if (!(ENV.RENDER || ENV.LF_MODO === 'nube' || ENV.LF_VERIFICAR_DISCO === '1')) { r.motivo = 'No es un servidor en la nube.'; return r; }
  try {
    let mejor = null;
    leeMontajes().forEach(m => { const ok = DATOS === m.punto || DATOS.startsWith(m.punto === '/' ? '/' : m.punto + '/'); if (ok && (!mejor || m.punto.length > mejor.punto.length)) mejor = m; });
    if (!mejor) { r.motivo = 'No se pudo ubicar el disco.'; return r; }
    r.montaje = mejor.punto; r.sistema = mejor.fs;
    r.persistente = mejor.punto !== '/' && !['tmpfs', 'ramfs', 'overlay'].includes(mejor.fs);
    r.motivo = r.persistente ? 'Los datos están en un disco montado aparte (' + mejor.punto + ').' : 'Los datos están en el almacenamiento temporal del contenedor.';
  } catch (e) { r.motivo = 'No se pudo revisar el disco.'; }
  return r;
}
const qCreada = db.prepare('SELECT MIN(creado) AS f FROM usuarios'), qUltDesc = db.prepare("SELECT MAX(fecha) AS f FROM auditoria WHERE accion = 'Descargó el respaldo completo'");

try { precarga(); } catch (e) { console.error('No se pudo aplicar la precarga:', e.message); }

servidor.listen(PUERTO, '0.0.0.0', () => {
  console.log('Sistema escolar Lafragua (nube) escuchando en el puerto ' + PUERTO + '. Datos en ' + DATOS);
  if (q.nUsr.get().n === 0) {
    if (!ENV.LF_SETUP_TOKEN) { SETUP_AUTO = crypto.randomBytes(9).toString('hex'); console.log('==> Aún no hay usuarios. Código de configuración inicial: ' + SETUP_AUTO + ' (usa la página /configurar)'); }
    else console.log('==> Aún no hay usuarios. Abre /configurar y usa el código de configuración de tus variables de entorno (LF_SETUP_TOKEN).');
  }
  respaldoDiario(); setInterval(respaldoDiario, 3600000).unref(); aseguraLibs(); programaCobranza(); programaRespaldos(); AV.programa();
});
function cierra() { try { respaldar(); } catch (e) {} try { db.close(); } catch (e) {} process.exit(0); }
process.on('SIGINT', cierra); process.on('SIGTERM', cierra);
