'use strict';
/* ===========================================================================
   Avisos fuera de la plataforma: correo (SMTP) y WhatsApp (API de WhatsApp Business de Meta).
   Cola de mensajes con reintentos, sin duplicados, con lista de personas que no quieren avisos,
   avisos automáticos (adeudo, solicitudes, planeaciones, calificaciones, resumen diario) y envío manual.
   Sin dependencias.
   =========================================================================== */
const http = require('http'), https = require('https');
const EVENTOS = ['adeudo', 'solicitud', 'planeacion', 'evaluacion', 'calificaciones', 'pago', 'prospecto', 'baja', 'manual', 'resumen'];
const PLAZO_CAL = 3;   /* días después de la evaluación para capturar calificaciones */
const CFG0 = { activo: false, escuela: 'Universidad Lafragua', correo: { activo: false, usarRespaldos: false, host: '', puerto: 587, seguro: false, usuario: '', clave: '', de: '', nombre: '' }, whatsapp: { activo: false, phoneId: '', token: '', version: 'v21.0', plantilla: 'aviso_escolar', idioma: 'es_MX', pais: '52' }, eventos: { adeudo: { correo: true, whatsapp: true }, solicitud: { correo: true, whatsapp: true }, planeacion: { correo: true, whatsapp: false }, evaluacion: { correo: true, whatsapp: true }, pago: { correo: true, whatsapp: false }, prospecto: { correo: true, whatsapp: false }, baja: { correo: true, whatsapp: false }, calificaciones: { correo: true, whatsapp: true }, manual: { correo: true, whatsapp: true }, resumen: { correo: true, whatsapp: false } }, recordatorios: { calificaciones: true }, resumen: { activo: true, hora: 8, para: [] }, sin: [] };
const MAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
function telWa(t, pais) { const d = String(t || '').replace(/\D/g, ''); if (d.length < 10) return ''; if (d.length === 10) return (pais || '52') + d; if (d.length === 13 && d.startsWith('521')) return '52' + d.slice(3); return d.length <= 15 ? d : ''; }
function limpiaWa(t, max) { return String(t || '').replace(/[\r\n\t]+/g, ' · ').replace(/ {3,}/g, '  ').trim().slice(0, max); }
function peticion(url, opciones, cuerpo) {
  return new Promise((ok, mal) => {
    const lib = url.protocol === 'https:' ? https : http, rq = lib.request(url, opciones, r => { const t = []; r.on('data', d => t.push(d)); r.on('end', () => ok({ status: r.statusCode, cuerpo: Buffer.concat(t).toString('utf8') })); });
    rq.setTimeout(30000, () => rq.destroy(new Error('Tiempo de espera agotado.'))); rq.on('error', mal); rq.end(cuerpo);
  });
}
function crea(ctx) {
  const { db, q, leeDoc, cifra, descifra, smtpEnvia, hoyMx, audita, cfgCorreoRespaldos, ENV, ahora } = ctx, ahoraMs = ahora || (() => Date.now());
  db.exec("CREATE TABLE IF NOT EXISTS mensajes (id TEXT PRIMARY KEY, ts INTEGER NOT NULL, canal TEXT NOT NULL, para TEXT NOT NULL, nombre TEXT, evento TEXT, asunto TEXT, texto TEXT, ref TEXT, quien TEXT, estado TEXT NOT NULL, intentos INTEGER NOT NULL DEFAULT 0, prox INTEGER NOT NULL DEFAULT 0, error TEXT, enviado INTEGER); CREATE INDEX IF NOT EXISTS mensajes_estado ON mensajes(estado, prox); CREATE UNIQUE INDEX IF NOT EXISTS mensajes_ref ON mensajes(ref, canal, para) WHERE ref IS NOT NULL AND ref != ''");
  const sIns = db.prepare('INSERT OR IGNORE INTO mensajes (id, ts, canal, para, nombre, evento, asunto, texto, ref, quien, estado, intentos, prox, error, enviado) VALUES (?,?,?,?,?,?,?,?,?,?,?,0,0,?,?)');
  const leeSis = (id, def) => { const r = q.uno.get('sistema', id); try { return r ? JSON.parse(r.data) : def; } catch (e) { return def; } }, ponSis = (id, o) => q.pon.run('sistema', id, JSON.stringify(o), Date.now());
  const SECRETOS = [['correo', 'clave'], ['whatsapp', 'token']], getP = (o, r) => r.reduce((x, k) => (x == null ? x : x[k]), o), setP = (o, r, v) => { let x = o; r.slice(0, -1).forEach(k => { x = x[k]; }); x[r[r.length - 1]] = v; };
  function cfg() {
    const g = leeSis('avisos', {}), c = JSON.parse(JSON.stringify(CFG0));
    ['activo', 'escuela'].forEach(k => { if (g[k] !== undefined) c[k] = g[k]; }); Object.assign(c.correo, g.correo || {}); Object.assign(c.whatsapp, g.whatsapp || {}); Object.assign(c.recordatorios, g.recordatorios || {}); Object.assign(c.resumen, g.resumen || {}); if (Array.isArray(g.sin)) c.sin = g.sin;
    EVENTOS.forEach(e => { c.eventos[e] = Object.assign({}, c.eventos[e], (g.eventos || {})[e] || {}); });
    SECRETOS.forEach(r => { const v = getP(c, r); setP(c, r, v ? (descifra(v) || '') : ''); }); return c;
  }
  function cfgPublica() { const c = cfg(), p = JSON.parse(JSON.stringify(c)); p.correo.claveGuardada = !!c.correo.clave; p.whatsapp.tokenGuardado = !!c.whatsapp.token; p.correo.clave = ''; p.whatsapp.token = ''; return p; }
  function guardaCfg(n) {
    const act = cfg(), c = JSON.parse(JSON.stringify(CFG0)), err = m => { const e = new Error(m); e.cod = 400; throw e; };
    c.activo = !!n.activo; c.escuela = String(n.escuela || act.escuela).trim().slice(0, 80) || 'Universidad Lafragua';
    const m = n.correo || {}, w = n.whatsapp || {}, r = n.resumen || {};
    c.correo = { activo: !!m.activo, usarRespaldos: !!m.usarRespaldos, host: String(m.host || '').trim(), puerto: Math.round(Number(m.puerto) || 587), seguro: !!m.seguro, usuario: String(m.usuario || '').trim(), clave: '', de: String(m.de || '').trim(), nombre: String(m.nombre || '').trim().slice(0, 80) };
    c.whatsapp = { activo: !!w.activo, phoneId: String(w.phoneId || '').trim(), token: '', version: String(w.version || 'v21.0').trim(), plantilla: String(w.plantilla || 'aviso_escolar').trim(), idioma: String(w.idioma || 'es_MX').trim(), pais: String(w.pais || '52').replace(/\D/g, '') || '52' };
    if (c.correo.activo && !c.correo.usarRespaldos) { if (!/^[A-Za-z0-9.-]+$/.test(c.correo.host)) err('Escribe el servidor de correo (por ejemplo smtp.gmail.com).'); if (!(c.correo.puerto >= 1 && c.correo.puerto <= 65535)) err('El puerto del correo no es válido.'); if (!MAIL.test(c.correo.de.replace(/^.*<|>.*$/g, '')) ) err('Escribe el correo desde el que se envían los avisos.'); }
    if (c.whatsapp.activo) { if (!/^\d{6,20}$/.test(c.whatsapp.phoneId)) err('Escribe el identificador del número de WhatsApp (Phone number ID).'); if (!/^v\d{1,2}\.\d$/.test(c.whatsapp.version)) err('La versión de la API debe verse como v21.0.'); if (!/^[a-z0-9_]{1,80}$/.test(c.whatsapp.plantilla)) err('El nombre de la plantilla solo lleva minúsculas, números y guion bajo.'); if (!/^[a-z]{2}(_[A-Z]{2})?$/.test(c.whatsapp.idioma)) err('El idioma de la plantilla debe verse como es_MX.'); }
    c.correo.clave = (typeof m.clave === 'string' && m.clave.length) ? m.clave : act.correo.clave; c.whatsapp.token = (typeof w.token === 'string' && w.token.length) ? w.token : act.whatsapp.token;
    if (c.correo.activo && !c.correo.usarRespaldos && c.correo.usuario && !c.correo.clave) err('Escribe la contraseña del correo.');
    if (c.whatsapp.activo && !c.whatsapp.token) err('Escribe el token de acceso de WhatsApp.');
    EVENTOS.forEach(e => { const x = (n.eventos || {})[e] || {}; c.eventos[e] = { correo: x.correo !== false && (x.correo !== undefined ? !!x.correo : CFG0.eventos[e].correo), whatsapp: x.whatsapp !== undefined ? !!x.whatsapp : CFG0.eventos[e].whatsapp }; });
    c.recordatorios = { calificaciones: (n.recordatorios || {}).calificaciones !== false };
    const hr = Math.round(Number(r.hora)); if (!(hr >= 0 && hr <= 23)) err('La hora del resumen va de 0 a 23.');
    const para = (Array.isArray(r.para) ? r.para : String(r.para || '').split(/[,;\s]+/)).map(x => String(x).trim()).filter(Boolean); if (para.length > 8 || !para.every(x => MAIL.test(x))) err('Escribe hasta 8 correos válidos para el resumen diario.');
    c.resumen = { activo: !!r.activo, hora: hr, para }; c.sin = act.sin;
    const g = JSON.parse(JSON.stringify(c)); SECRETOS.forEach(rr => { const v = getP(g, rr); setP(g, rr, v ? cifra(v) : ''); }); ponSis('avisos', g);
  }
  function setSin(ids) { const g = leeSis('avisos', {}); g.sin = Array.from(new Set((ids || []).map(String))).slice(0, 5000); ponSis('avisos', g); return g.sin.length; }
  function correoCfg(c) {
    if (c.correo.usarRespaldos) { const r = cfgCorreoRespaldos(); if (!r || !r.host) return null; return { host: r.host, puerto: r.puerto, seguro: r.seguro, usuario: r.usuario, clave: r.clave, de: r.de }; }
    if (!c.correo.host) return null; const de = c.correo.nombre ? c.correo.nombre + ' <' + c.correo.de.replace(/^.*<|>.*$/g, '') + '>' : c.correo.de; return { host: c.correo.host, puerto: c.correo.puerto, seguro: c.correo.seguro, usuario: c.correo.usuario, clave: c.correo.clave, de };
  }
  const idm = () => require('crypto').randomBytes(8).toString('hex');
  /* ---- personas ---- */
  const alumno = sid => { const s = leeDoc('students', sid); return s ? { id: sid, tipo: 'alumno', nombre: s.nombre || '', mail: MAIL.test(String(s.mail || '').trim()) ? String(s.mail).trim() : '', tel: s.tel || '' } : null; };
  const docente = did => { const d = leeDoc('docentes', did); return d ? { id: did, tipo: 'docente', nombre: d.nombre || '', mail: MAIL.test(String(d.mail || '').trim()) ? String(d.mail).trim() : '', tel: d.tel || '' } : null; };
  const esEgresado = sid => { const e = leeDoc('egresados', sid); return !!(e && !e.revertido); };
  /* ---- encolar ---- */
  function encola(evento, p, asunto, texto, ref, quien, simular, canales) {
    const c = cfg(), out = { correo: 0, whatsapp: 0, omitidos: [] }; if (!p) return out;
    const ev = canales ? { correo: canales.includes('correo'), whatsapp: canales.includes('whatsapp') } : (c.eventos[evento] || {}); if (!c.activo) { out.omitidos.push('Los avisos están apagados'); return out; }
    if (c.sin.includes(p.id)) { out.omitidos.push('Sin avisos'); return out; }
    ['correo', 'whatsapp'].forEach(canal => {
      if (!ev[canal]) return;
      if (!c[canal].activo) { out.omitidos.push((canal === 'correo' ? 'Correo' : 'WhatsApp') + ' no está activo'); return; }
      const dest = canal === 'correo' ? p.mail : telWa(p.tel, c.whatsapp.pais);
      if (!dest) { out.omitidos.push('Sin ' + (canal === 'correo' ? 'correo' : 'teléfono') + ' registrado'); if (!simular) sIns.run(idm(), ahoraMs(), canal, '—', p.nombre, evento, asunto, texto, ref ? ref + ':' + p.id : '', quien || '', 'omitido', 'Sin ' + (canal === 'correo' ? 'correo' : 'teléfono') + ' registrado', null); return; }
      if (simular) { out[canal]++; return; }
      const r = sIns.run(idm(), ahoraMs(), canal, dest, p.nombre, evento, asunto, texto, ref || '', quien || '', 'pendiente', null, null); if (r.changes) { out[canal]++; programaProcesa(); }
    });
    return out;
  }
  /* ---- envío real ---- */
  async function envia(canal, m, c) {
    if (canal === 'correo') {
      const cc = correoCfg(c); if (!cc) throw new Error('Falta configurar el correo.');
      const cuerpo = 'Hola ' + (m.nombre || '').split(' ')[0] + ':\n\n' + m.texto + '\n\n— ' + c.escuela + '\nEste es un aviso de la plataforma escolar. Si no deseas recibirlos, avisa a Control escolar.';
      await smtpEnvia(Object.assign({}, cc, { para: [m.para] }), { asunto: m.asunto || c.escuela, texto: cuerpo, adjuntos: [] }); return;
    }
    const w = c.whatsapp, base = String(ENV.LF_WA_BASE || 'https://graph.facebook.com').replace(/\/+$/, ''), url = new URL(base + '/' + w.version + '/' + w.phoneId + '/messages');
    const cuerpo = JSON.stringify({ messaging_product: 'whatsapp', to: m.para, type: 'template', template: { name: w.plantilla, language: { code: w.idioma }, components: [{ type: 'body', parameters: [{ type: 'text', text: limpiaWa((m.nombre || '').split(' ')[0] || 'Hola', 60) }, { type: 'text', text: limpiaWa((m.asunto ? m.asunto + ': ' : '') + m.texto, 900) }] }] } });
    const r = await peticion(url, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + w.token, 'Content-Length': Buffer.byteLength(cuerpo) } }, cuerpo);
    let j = {}; try { j = JSON.parse(r.cuerpo); } catch (e) {}
    if (r.status < 200 || r.status > 299 || !(j.messages && j.messages.length)) { const e = new Error((j.error && (j.error.message || j.error.error_user_msg)) || ('WhatsApp respondió ' + r.status)); e.permanente = !!(j.error && [131026, 131021, 100, 132000, 132001].includes(j.error.code)); throw e; }
  }
  const sSel = db.prepare("SELECT * FROM mensajes WHERE estado IN ('pendiente','reintento') AND prox <= ? ORDER BY ts LIMIT ?"), sOk = db.prepare("UPDATE mensajes SET estado='enviado', enviado=?, intentos=intentos+1, error=NULL WHERE id=?"), sMal = db.prepare('UPDATE mensajes SET estado=?, intentos=intentos+1, prox=?, error=? WHERE id=?');
  let ocupado = false, tProc = null;
  const programaProcesa = () => { clearTimeout(tProc); tProc = setTimeout(() => { procesa(40).catch(e => console.error('Avisos:', e.message)); }, 300); tProc.unref(); };
  async function procesa(max) {
    if (ocupado) return { enviados: 0, fallidos: 0, ocupado: true }; ocupado = true; let ok = 0, mal = 0;
    try {
      const c = cfg(), filas = sSel.all(ahoraMs(), max || 40);
      for (const m of filas) {
        if (!c.activo || !c[m.canal].activo) { sMal.run('omitido', 0, 'El canal está apagado', m.id); continue; }
        try { await envia(m.canal, m, c); sOk.run(ahoraMs(), m.id); ok++; }
        catch (e) { const n = m.intentos + 1, fin = e.permanente || n >= 3; sMal.run(fin ? 'fallido' : 'reintento', ahoraMs() + [120000, 900000, 7200000][Math.min(n - 1, 2)], String(e.message || e).slice(0, 300), m.id); if (fin) mal++; }
      }
    } finally { ocupado = false; }
    try { if (sSel.all(ahoraMs(), 1).length) programaProcesa(); } catch (e) {}
    return { enviados: ok, fallidos: mal };
  }
  /* ---- avisos automáticos ---- */
  const escuelaTxt = () => cfg().escuela;
  function hookAviso(id, d) {
    if (!d || !d.sid) return; const p = alumno(d.sid); if (!p) return;
    encola('adeudo', p, d.titulo || 'Aviso de ' + escuelaTxt(), d.mensaje || '', 'aviso:' + id, 'automático');
  }
  const TIPOS = { justificante: 'justificante de faltas', boleta: 'boleta de estudios', constancia: 'constancia de estudios', historial: 'historial académico' };
  function hookSolicitud(id, viejo, nuevo) {
    if (!nuevo || !nuevo.sid || (viejo && viejo.estado === nuevo.estado) || nuevo.estado === 'pendiente') return; const p = alumno(nuevo.sid); if (!p) return;
    const t = TIPOS[nuevo.tipo] || 'solicitud', mot = nuevo.resp && nuevo.resp.motivo ? ' Motivo: ' + nuevo.resp.motivo + '.' : '';
    const texto = nuevo.estado === 'aprobada' ? 'Tu ' + t + ' fue aprobado(a). Ya puedes consultarlo en tu portal de alumno.' : nuevo.estado === 'atendida' ? 'Tu ' + t + ' ya está lista. Consúltala en tu portal o acude a Control escolar.' : 'Tu ' + t + ' fue denegado(a).' + mot + ' Para más información acude a Control escolar.';
    encola('solicitud', p, 'Respuesta a tu solicitud', texto, 'sol:' + id + ':' + nuevo.estado, 'automático');
  }
  function hookPlaneacion(mid, viejo, nuevo) {
    if (!nuevo || nuevo.estado === (viejo || {}).estado || !['aprobada', 'denegada'].includes(nuevo.estado)) return;
    const m = leeDoc('materias', mid); if (!m || !m.docId) return; const p = docente(m.docId); if (!p) return;
    const texto = 'Tu planeación de «' + m.nom + '» (' + m.plan + ') fue ' + (nuevo.estado === 'aprobada' ? 'aprobada.' : 'denegada.' + (nuevo.motivo ? ' Motivo: ' + nuevo.motivo + '.' : ' Revísala en la plataforma.'));
    encola('planeacion', p, 'Planeación ' + (nuevo.estado === 'aprobada' ? 'aprobada' : 'denegada'), texto, 'pln:' + mid + ':' + nuevo.estado + ':' + (nuevo.revFecha || ''), 'automático');
  }
  const sumaDia = (f, n) => { const d = new Date(f + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
  const limiteCal = m => { const def = sumaDia(m.ev, PLAZO_CAL); return m.prorroga && m.prorroga > def ? m.prorroga : def; }, fl = f => String(f).split('-').reverse().join('/');
  const diaSem = f => { try { return new Date(f + 'T12:00:00Z').toLocaleDateString('es-MX', { weekday: 'long', timeZone: 'UTC' }); } catch (e) { return ''; } };
  function hookEvaluacion(mid, viejo, nuevo) {
    if (!nuevo || !nuevo.docId) return; const p = docente(nuevo.docId); if (!p) return;
    if (nuevo.ev && (!viejo || viejo.ev !== nuevo.ev || viejo.docId !== nuevo.docId)) {
      const lim = limiteCal(nuevo);
      encola('evaluacion', p, 'Evaluación programada', 'Se programó la evaluación de «' + nuevo.nom + '» (' + nuevo.plan + ', cuatrimestre ' + nuevo.cuat + ') para el ' + diaSem(nuevo.ev) + ' ' + fl(nuevo.ev) + '. Podrás capturar las calificaciones en la plataforma hasta el ' + diaSem(lim) + ' ' + fl(lim) + ' (' + PLAZO_CAL + ' días después de la evaluación).', 'eval:' + mid + ':' + nuevo.ev + ':' + nuevo.docId, 'automático');
    }
    if (nuevo.ev && nuevo.prorroga && (!viejo || viejo.prorroga !== nuevo.prorroga)) encola('evaluacion', p, 'Prórroga para capturar calificaciones', 'Control escolar amplió el plazo para capturar las calificaciones de «' + nuevo.nom + '» (' + nuevo.plan + '): ahora puedes hacerlo hasta el ' + diaSem(nuevo.prorroga) + ' ' + fl(nuevo.prorroga) + '.', 'pro:' + mid + ':' + nuevo.prorroga, 'automático');
  }
  function califPendientes(hoy) {
    const out = [], grupos = q.lista.all('grupos').map(r => { try { return JSON.parse(r.data); } catch (e) { return null; } }).filter(Boolean), desde = sumaDia(hoy, -45);
    q.lista.all('materias').forEach(r => {
      let m; try { m = JSON.parse(r.data); } catch (e) { return; } if (!m.ev || m.ev > hoy || m.ev < desde || !m.docId) return;
      const ids = new Set(); grupos.forEach(g => { if (g.per === m.per && ((g.plan === m.plan && g.cuat === m.cuat) || (m.fus || []).some(f => f.plan === g.plan && f.cuat === g.cuat))) (g.alumnos || []).forEach(x => ids.add(x)); });
      const al = [...ids].filter(x => !esEgresado(x)); if (!al.length) return;
      const faltan = al.filter(sid => { const cd = leeDoc('calif', sid); return !((cd && cd.items) || []).some(i => i.mid === r.id && i.cal != null); }).length;
      if (faltan) out.push({ mid: r.id, m, total: al.length, faltan });
    });
    return out;
  }
  function resumenPendientes(hoy) {
    const cuenta = (col, f) => q.lista.all(col).filter(r => { try { return f(JSON.parse(r.data)); } catch (e) { return false; } }).length;
    let transf = 0; q.lista.all('ledger').forEach(r => { try { transf += (JSON.parse(r.data).pagos || []).filter(g => g.estado === 'pendiente').length; } catch (e) {} }); q.lista.all('acuerdo286').forEach(r => { try { transf += (JSON.parse(r.data).pagos || []).filter(g => g.estado === 'pendiente').length; } catch (e) {} });
    return { solicitudes: cuenta('solicitudes', d => d.estado === 'pendiente'), planeaciones: cuenta('planeaciones', d => d.estado === 'pendiente'), transferencias: transf, calificaciones: califPendientes(hoy).length, contratos: cuenta('contratos', d => d.estado === 'generado'), bajas: cuenta('bajas', d => d.estado === 'pendiente') };
  }
  function diarios(force) {
    const c = cfg(), hoy = hoyMx(), hora = ctx.horaMx ? ctx.horaMx() : new Date().getHours(), st = leeSis('avisos_estado', { ultimo: {} }), hecho = { calificaciones: 0, resumen: 0 };
    if (!c.activo) return hecho;
    if (c.recordatorios.calificaciones && (force === 'calificaciones' || (!force && hora >= 8 && st.ultimo.cal !== hoy))) {
      califPendientes(hoy).forEach(x => {
        const p = docente(x.m.docId); if (!p) return;
        const lim = limiteCal(x.m); let texto, ref;
        if (hoy <= lim) { texto = x.m.ev === hoy ? 'Hoy es la evaluación de «' + x.m.nom + '» (' + x.m.plan + '). Tienes hasta el ' + fl(lim) + ' para capturar las calificaciones en la plataforma.' : 'Faltan ' + x.faltan + ' de ' + x.total + ' calificaciones de «' + x.m.nom + '» (' + x.m.plan + '), cuya evaluación fue el ' + fl(x.m.ev) + '. El plazo para capturarlas termina el ' + fl(lim) + (lim === hoy ? ' (hoy es el último día)' : '') + '.'; ref = 'cal:' + x.mid + ':' + hoy; }
        else { texto = 'El plazo para capturar las calificaciones de «' + x.m.nom + '» (' + x.m.plan + ') venció el ' + fl(lim) + ' y faltan ' + x.faltan + ' de ' + x.total + '. Si necesitas más tiempo, pide una prórroga a Control escolar.'; ref = 'calv:' + x.mid + ':' + lim; }
        const r = encola('calificaciones', p, hoy <= lim ? 'Calificaciones por subir' : 'Venció el plazo de calificaciones', texto, ref, 'automático'); hecho.calificaciones += r.correo + r.whatsapp;
      }); if (!force) st.ultimo.cal = hoy;
    }
    if (c.resumen.activo && c.resumen.para.length && (force === 'resumen' || (!force && hora >= c.resumen.hora && st.ultimo.res !== hoy))) {
      const r = resumenPendientes(hoy), tot = r.solicitudes + r.planeaciones + r.transferencias + r.calificaciones + r.contratos + r.bajas;
      if (tot > 0 && c.eventos.resumen.correo && c.correo.activo) {
        const l = [];
        if (r.solicitudes) l.push('• ' + r.solicitudes + ' solicitud(es) de alumnos por atender'); if (r.planeaciones) l.push('• ' + r.planeaciones + ' planeación(es) de docentes por revisar'); if (r.transferencias) l.push('• ' + r.transferencias + ' transferencia(s) por confirmar'); if (r.calificaciones) l.push('• ' + r.calificaciones + ' asignatura(s) con calificaciones sin subir'); if (r.contratos) l.push('• ' + r.contratos + ' contrato(s) de docentes por firmar'); if (r.bajas) l.push('• ' + r.bajas + ' alumno(s) pendientes de decisión: baja o prórroga');
        c.resumen.para.forEach(mail => { const rr = encola('resumen', { id: 'resumen:' + mail, tipo: 'personal', nombre: mail.split('@')[0], mail, tel: '' }, 'Pendientes de hoy · ' + c.escuela, 'Esto es lo que espera tu atención en la plataforma:\n\n' + l.join('\n') + '\n\nEntra a la plataforma para resolverlo.', 'res:' + hoy, 'automático'); hecho.resumen += rr.correo; });
      }
      if (!force) st.ultimo.res = hoy;
    }
    if (!force) ponSis('avisos_estado', st); return hecho;
  }
  /* ---- envío manual ---- */
  function destinatarios(d) {
    const out = [], vistos = new Set(), add = p => { if (p && !vistos.has(p.id)) { vistos.add(p.id); out.push(p); } };
    const alumnos = () => q.lista.all('students').map(r => r.id).filter(id => !esEgresado(id));
    if (d.tipo === 'alumnos') alumnos().forEach(id => add(alumno(id)));
    else if (d.tipo === 'plan') alumnos().forEach(id => { const s = leeDoc('students', id); if (s && (s.programa || s.carrera) === d.plan) add(alumno(id)); });
    else if (d.tipo === 'grupo') { const g = leeDoc('grupos', d.id); ((g && g.alumnos) || []).filter(id => !esEgresado(id)).forEach(id => add(alumno(id))); }
    else if (d.tipo === 'alumno') { if (!esEgresado(d.id)) add(alumno(d.id)); }
    else if (d.tipo === 'docentes') q.lista.all('docentes').forEach(r => add(docente(r.id)));
    else if (d.tipo === 'docente') add(docente(d.id));
    return out;
  }
  function enviarManual(actor, b) {
    const asunto = String(b.asunto || '').trim().slice(0, 120), texto = String(b.texto || '').trim(), err = m => { const e = new Error(m); e.cod = 400; throw e; };
    if (!texto || texto.length > 900) err('Escribe el mensaje (hasta 900 caracteres).');
    const ps = destinatarios(b.destino || {}); if (!ps.length) err('No hay personas con esa selección.');
    const canales = (b.canales || ['correo', 'whatsapp']).filter(x => x === 'correo' || x === 'whatsapp'); if (!canales.length) err('Elige al menos un canal.');
    const r = { personas: ps.length, correo: 0, whatsapp: 0, sinContacto: 0, omitidos: 0 };
    ps.forEach(p => { const x = encola('manual', p, asunto, texto, '', actor, !!b.simular, canales); r.correo += x.correo; r.whatsapp += x.whatsapp; const sc = x.omitidos.filter(o => /^Sin (correo|teléfono)/.test(o)).length; if (sc && !x.correo && !x.whatsapp) r.sinContacto++; else if (x.omitidos.length && !x.correo && !x.whatsapp) r.omitidos++; });
    r.muestra = ps.slice(0, 5).map(p => p.nombre); r.guardado = !b.simular; return r;
  }
  /* ---- consulta ---- */
  function mensajes(f) {
    const w = [], a = []; if (f.estado) { w.push('estado = ?'); a.push(f.estado); } if (f.canal) { w.push('canal = ?'); a.push(f.canal); } if (f.evento) { w.push('evento = ?'); a.push(f.evento); }
    if (f.q) { w.push("(lower(nombre) LIKE ? OR lower(para) LIKE ? OR lower(texto) LIKE ?)"); const x = '%' + String(f.q).toLowerCase() + '%'; a.push(x, x, x); }
    return db.prepare('SELECT * FROM mensajes ' + (w.length ? 'WHERE ' + w.join(' AND ') : '') + ' ORDER BY ts DESC LIMIT ?').all(...a, Math.min(parseInt(f.limite, 10) || 100, 300));
  }
  function resumen() {
    const ya = ahoraMs(), n = (e, desde) => db.prepare('SELECT COUNT(*) AS n FROM mensajes WHERE estado = ?' + (desde ? ' AND enviado >= ?' : '')).get(...(desde ? [e, desde] : [e])).n, st = leeSis('avisos_estado', { ultimo: {} });
    return { enviadosHoy: n('enviado', ya - 86400000), enviados7: n('enviado', ya - 7 * 86400000), pendientes: n('pendiente') + n('reintento'), fallidos: n('fallido'), omitidos: n('omitido'), ultimo: st.ultimo || {} };
  }
  function reintenta(ids) { const ups = db.prepare("UPDATE mensajes SET estado='pendiente', intentos=0, prox=0, error=NULL WHERE id=? AND estado IN ('fallido','reintento')"); let n = 0; if (ids === 'todos') n = db.prepare("UPDATE mensajes SET estado='pendiente', intentos=0, prox=0, error=NULL WHERE estado='fallido'").run().changes; else (ids || []).slice(0, 500).forEach(i => { n += ups.run(String(i)).changes; }); return n; }
  async function probar(canal, para) {
    const c = cfg(), p = { nombre: 'Prueba', para: String(para || '').trim(), asunto: 'Prueba de avisos', texto: 'Si recibes este mensaje, los avisos de la plataforma están funcionando.' };
    if (canal === 'correo') { if (!MAIL.test(p.para)) throw new Error('Escribe un correo válido para la prueba.'); await envia('correo', p, Object.assign({}, c, { activo: true })); }
    else { p.para = telWa(p.para, c.whatsapp.pais); if (!p.para) throw new Error('Escribe un teléfono válido (10 dígitos) para la prueba.'); if (!c.whatsapp.phoneId || !c.whatsapp.token) throw new Error('Guarda primero los datos de WhatsApp.'); await envia('whatsapp', p, c); }
  }
  function programa() {
    const tick = async () => { try { diarios(); await procesa(40); } catch (e) { console.error('Avisos:', e.message); } };
    const t = setInterval(tick, parseInt(ENV.LF_AVISOS_TICK_MS || '30000', 10)); t.unref(); return t;
  }
  function avisaDireccion(evento, asunto, texto, ref) { const c = cfg(); if (!c.activo || !c.correo.activo || !c.eventos[evento] || !c.eventos[evento].correo) return; (c.resumen.para || []).forEach(mail => encola(evento, { id: 'dir:' + mail, tipo: 'personal', nombre: mail.split('@')[0], mail, tel: '' }, asunto, texto, ref, 'automático')); }
  function avisaProspecto(p) { const c = cfg(); encola('prospecto', { id: 'pros:' + p.id, tipo: 'prospecto', nombre: p.nombre, mail: MAIL.test(String(p.correo || '')) ? p.correo : '', tel: p.tel }, 'Gracias por tu interés en ' + c.escuela, 'Recibimos tus datos y un asesor te contactará muy pronto para darte la información' + (p.programa ? ' de ' + p.programa : '') + '. Si ya no deseas que te contactemos, responde a este mensaje.', 'pros:' + p.id, 'automático'); }
  function avisaAlumno(evento, sid, asunto, texto, ref) { const p = alumno(sid); if (p) encola(evento, p, asunto, texto, ref, 'automático'); }
  return { avisaDireccion, avisaProspecto, avisaAlumno, cfgPublica, guardaCfg, setSin, hookAviso, hookSolicitud, hookPlaneacion, hookEvaluacion, diarios, procesa, destinatarios, enviarManual, mensajes, resumen, reintenta, probar, programa, califPendientes, resumenPendientes, cfg };
}
module.exports = { crea, telWa, limpiaWa, MAIL };
