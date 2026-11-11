'use strict';
/* ===========================================================================
   Bajas y regularización de alumnos.
   Se abre un caso para Control escolar cuando, al cerrarse un ciclo, el alumno no tiene calificaciones, o cuando debe
   N colegiaturas vencidas (2 por omisión). Control escolar decide: dar de baja, otorgar una prórroga o descartar la alerta.
   =========================================================================== */
const CFG0 = { activa: true, colegiaturas: 2, prorrogaDias: 15 };
const MOTIVOS = ['Adeudo de colegiaturas', 'Sin calificaciones al cerrar el ciclo', 'Baja voluntaria', 'Abandono de estudios', 'Cambio de escuela o institución', 'Problemas de salud', 'Situación económica', 'Cambio de domicilio o de ciudad', 'Motivos laborales', 'Motivos familiares', 'Documentación incompleta', 'Disciplinaria', 'Fallecimiento', 'Otro'];
const AUTOMATICOS = ['Adeudo de colegiaturas', 'Sin calificaciones al cerrar el ciclo'], SOLICITA = ['', 'Alumno', 'Tutor o familiar', 'Escuela'];
const dinero = n => '$' + Number(n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fl = f => String(f || '').split('-').reverse().join('/');
function crea(ctx) {
  const { q, leeDoc, difunde, audita, hoyMx, adeudoDe, cobCfg, planesYExtra, avisaAlumno, avisaDireccion, cierraSesiones, evaluaCob } = ctx;
  const err = (m, c) => { const e = new Error(m); e.cod = c || 400; return e; };
  const leeSis = (id, def) => { const r = q.uno.get('sistema', id); try { return r ? JSON.parse(r.data) : def; } catch (e) { return def; } };
  const ponDoc = (col, id, o) => { q.pon.run(col, id, JSON.stringify(o), Date.now()); difunde(col, id); };
  const cfg = () => Object.assign({}, CFG0, leeSis('bajas', {}));
  function guardaCfg(n) {
    const c = { activa: !!n.activa, colegiaturas: Math.round(Number(n.colegiaturas)), prorrogaDias: Math.round(Number(n.prorrogaDias)) };
    if (!(c.colegiaturas >= 1 && c.colegiaturas <= 6)) throw err('Las colegiaturas vencidas para abrir un caso van de 1 a 6.'); if (!(c.prorrogaDias >= 1 && c.prorrogaDias <= 120)) throw err('Los días de prórroga por omisión van de 1 a 120.');
    q.pon.run('sistema', 'bajas', JSON.stringify(c), Date.now()); return c;
  }
  const sumaDias = (iso, n) => { const d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
  const esBaja = st => !!(st && st.baja && !st.baja.revertida), bajaDe = sid => esBaja(leeDoc('students', sid));
  const egresado = sid => { const e = leeDoc('egresados', sid); return !!(e && !e.revertido); };
  function prorrogaVigente(sid, hoy) { const c = leeDoc('bajas', sid); return c && c.estado === 'prorroga' && c.prorroga && c.prorroga.hasta >= (hoy || hoyMx()) ? c.prorroga.hasta : ''; }
  const pendientes = () => q.lista.all('bajas').filter(r => { try { return JSON.parse(r.data).estado === 'pendiente'; } catch (e) { return false; } }).length;
  const nota = (c, tipo, txt, u, n) => { c.historial = (c.historial || []).concat([{ t: new Date().toISOString(), u: u || 'sistema', n: n || 'Sistema', tipo, txt }]); c.ultimo = new Date().toISOString(); };
  const textoCausas = z => [z.adeudo ? 'debe ' + z.adeudo.n + (z.adeudo.n === 1 ? ' colegiatura vencida' : ' colegiaturas vencidas') + ' (' + dinero(z.adeudo.total) + ')' : '', z.sinCalif ? 'no tiene calificaciones en el ciclo ' + z.sinCalif.per + ', que ya se cerró' : ''].filter(Boolean).join(' y ');
  /* ---- revisión ---- */
  function contexto() {
    const hoy = hoyMx(), docs = col => q.lista.all(col).map(r => { try { return { id: r.id, d: JSON.parse(r.data) }; } catch (e) { return null; } }).filter(Boolean);
    const cerrados = docs('ciclos').filter(x => x.d.cerrado && x.d.per).map(x => ({ per: x.d.per, fecha: x.d.fecha || '', miembros: new Set(), con: new Set(), hay: false })), grupos = docs('grupos');
    if (cerrados.length) {
      cerrados.forEach(c => grupos.filter(g => g.d.per === c.per).forEach(g => (g.d.alumnos || []).forEach(id => c.miembros.add(id))));
      docs('calif').forEach(({ id, d }) => (d.items || []).forEach(i => { if (i && i.cal != null) cerrados.forEach(c => { if (i.per === c.per) { c.con.add(id); c.hay = true; } }); }));
    }
    cerrados.sort((a, b) => String(b.fecha).localeCompare(String(a.fecha)));
    return { hoy, c: cfg(), pe: planesYExtra(), cobc: cobCfg(), cerrados };
  }
  function revisaAlumno(sid, rc, salida) {
    const st = leeDoc('students', sid); if (!st || esBaja(st) || egresado(sid)) return null;
    const z = {}, ad = adeudoDe(sid, rc.hoy, rc.cobc, rc.pe);
    if (ad && ad.n >= rc.c.colegiaturas) z.adeudo = { n: ad.n, total: ad.total, meses: (ad.meses || []).slice(0, 8) };
    const cz = rc.cerrados.find(c => c.miembros.has(sid) && c.hay && !c.con.has(sid)); if (cz) z.sinCalif = { per: cz.per };
    let caso = leeDoc('bajas', sid), hay = Object.keys(z).length > 0, cambio = false;
    if (!hay) { if (caso && (caso.estado === 'pendiente' || caso.estado === 'prorroga')) { caso.estado = 'resuelto'; caso.causas = {}; nota(caso, 'sistema', 'Se regularizó la situación: ya no hay colegiaturas vencidas suficientes ni falta de calificaciones.'); ponDoc('bajas', sid, caso); } return null; }
    if (caso && caso.estado === 'baja') return null;
    if (caso && caso.estado === 'descartado' && caso.silencio && rc.hoy <= caso.silencio) return null;
    const plan = st.programa || st.carrera || '';
    if (!caso || caso.estado === 'resuelto' || caso.estado === 'descartado') {
      caso = { sid, mat: st.mat, nombre: st.nombre, plan, estado: 'pendiente', causas: z, detectado: new Date().toISOString(), episodio: (caso ? caso.episodio || 1 : 0) + 1, historial: caso ? caso.historial || [] : [], prorroga: null }; delete caso.silencio;
      nota(caso, 'sistema', 'Alerta: el alumno ' + textoCausas(z) + '. Control escolar debe decidir si lo da de baja o le otorga una prórroga para regularizarse.'); ponDoc('bajas', sid, caso);
      audita(null, null, 'Alumno pendiente de decisión de baja o prórroga', st.mat + ' · ' + st.nombre + ' · ' + textoCausas(z)); if (salida) salida.nuevas.push(caso); return caso;
    }
    if (caso.estado === 'prorroga') {
      if (rc.hoy > caso.prorroga.hasta) { caso.estado = 'pendiente'; caso.causas = z; caso.prorrogaVencida = caso.prorroga.hasta; nota(caso, 'sistema', 'La prórroga venció el ' + fl(caso.prorroga.hasta) + ' y la situación continúa: el alumno ' + textoCausas(z) + '. Control escolar debe decidir de nuevo.'); ponDoc('bajas', sid, caso); audita(null, null, 'Venció la prórroga de un alumno', st.mat + ' · ' + st.nombre); if (salida) salida.vencidas.push(caso); return caso; }
      if (JSON.stringify(caso.causas) !== JSON.stringify(z)) { caso.causas = z; ponDoc('bajas', sid, caso); } return null;
    }
    if (JSON.stringify(caso.causas) !== JSON.stringify(z)) { const nueva = Object.keys(z).some(k => !caso.causas[k]); caso.causas = z; if (nueva) nota(caso, 'sistema', 'Se sumó otra causa: el alumno ' + textoCausas(z) + '.'); ponDoc('bajas', sid, caso); }
    return null;
  }
  function avisaPersonal(salida) {
    const todas = salida.nuevas.concat(salida.vencidas); if (!todas.length) return;
    const l = todas.slice(0, 15).map(c => '• ' + c.nombre + ' (' + c.mat + ', ' + c.plan + '): ' + textoCausas(c.causas) + (c.prorrogaVencida ? ' · venció su prórroga' : '')).join('\n');
    try { avisaDireccion('baja', todas.length + (todas.length === 1 ? ' alumno pendiente de decisión' : ' alumnos pendientes de decisión') + ' (baja o prórroga)', 'Control escolar debe decidir si da de baja o concede una prórroga a:\n\n' + l + (todas.length > 15 ? '\n… y ' + (todas.length - 15) + ' más' : '') + '\n\nEntra a Control escolar > Bajas para resolverlo.', 'baja:' + Date.now()); } catch (e) { console.error('Bajas (aviso):', e.message); }
  }
  function revisa() {
    const rc = contexto(); if (!rc.c.activa) return { activa: false, nuevas: 0, vencidas: 0 }; const salida = { nuevas: [], vencidas: [] };
    q.lista.all('students').forEach(r => { try { revisaAlumno(r.id, rc, salida); } catch (e) { console.error('Bajas (' + r.id + '):', e.message); } });
    avisaPersonal(salida); return { activa: true, nuevas: salida.nuevas.length, vencidas: salida.vencidas.length, pendientes: pendientes() };
  }
  const colaSids = new Set(); let tm = null;
  function hook(col, id) {
    if (!['ledger', 'calif', 'students', 'egresados', 'ciclos', 'grupos'].includes(col)) return;
    if (col === 'ciclos' || col === 'grupos') colaSids.add('*'); else colaSids.add(id);
    clearTimeout(tm); tm = setTimeout(() => { try { const todos = colaSids.has('*'), sids = [...colaSids]; colaSids.clear(); if (!cfg().activa) return; if (todos) { revisa(); return; } const rc = contexto(), salida = { nuevas: [], vencidas: [] }; sids.forEach(sid => revisaAlumno(sid, rc, salida)); avisaPersonal(salida); } catch (e) { console.error('Bajas:', e.message); } }, 1500); tm.unref && tm.unref();
  }
  /* ---- decisiones de Control escolar ---- */
  function decide(sid, accion, b, quien) {
    const st = leeDoc('students', sid); if (!st) throw err('No existe ese alumno.', 404); const hoy = hoyMx(), u = quien.u, n = quien.name || quien.u;
    let caso = leeDoc('bajas', sid); const motivo = String(b.motivo || '').trim().slice(0, 400), obs = String(b.obs || '').trim().slice(0, 600);
    const base = () => ({ sid, mat: st.mat, nombre: st.nombre, plan: st.programa || st.carrera || '', estado: 'pendiente', causas: {}, detectado: new Date().toISOString(), episodio: 1, historial: [], prorroga: null });
    if (accion === 'baja') {
      if (esBaja(st)) throw err('Ese alumno ya está dado de baja.'); if (egresado(sid)) throw err('Ese alumno es egresado.'); if (!MOTIVOS.includes(String(b.tipo || ''))) throw err('Elige el motivo de la baja.'); if (motivo.length < 5 && !AUTOMATICOS.includes(b.tipo)) throw err('Captura el detalle del motivo (al menos unas palabras).');
      const temporal = !!b.temporal, regreso = String(b.regreso || ''), solicita = String(b.solicita || ''), folio = String(b.folio || '').trim().slice(0, 60);
      if (!SOLICITA.includes(solicita)) throw err('Elige quién solicita la baja.'); if (temporal && (!/^\d{4}-\d{2}-\d{2}$/.test(regreso) || regreso <= hoy || regreso > sumaDias(hoy, 1100))) throw err('Para una baja temporal escribe la fecha prevista de regreso (posterior a hoy y a menos de 3 años).');
      const fecha = /^\d{4}-\d{2}-\d{2}$/.test(String(b.fecha || '')) ? b.fecha : hoy; if (fecha > sumaDias(hoy, 31)) throw err('La fecha de la baja no puede ser tan adelante.');
      caso = caso || base(); const causas = caso.causas || {};
      st.baja = { fecha, tipo: b.tipo, motivo, obs, temporal, regreso: temporal ? regreso : '', solicita, folio, por: u, porNombre: n, causas, registrada: new Date().toISOString() }; ponDoc('students', sid, st);
      caso.estado = 'baja'; caso.baja = { fecha, tipo: b.tipo, temporal, regreso: temporal ? regreso : '' }; nota(caso, 'baja', (temporal ? 'Baja TEMPORAL' : 'Baja') + ' a partir del ' + fl(fecha) + (temporal ? ' (regreso previsto el ' + fl(regreso) + ')' : '') + '. Motivo: ' + b.tipo + (motivo ? ' · ' + motivo : '') + (solicita ? ' · solicitada por: ' + solicita : '') + (folio ? ' · folio ' + folio : '') + (obs ? ' · ' + obs : ''), u, n); ponDoc('bajas', sid, caso);
      try { cierraSesiones(sid); } catch (e) {} audita(u, null, 'Dio de baja a un alumno', st.mat + ' · ' + st.nombre + ' · ' + b.tipo);
      try { avisaAlumno('baja', sid, 'Baja de la escuela', 'Te informamos que causaste baja' + (temporal ? ' temporal' : '') + ' a partir del ' + fl(fecha) + (temporal ? ' (regreso previsto el ' + fl(regreso) + ')' : '') + '. Motivo: ' + b.tipo + '. Si crees que es un error o quieres reincorporarte, acude a Control escolar.', 'baja:' + sid + ':' + fecha); } catch (e) {}
      try { evaluaCob(sid); } catch (e) {} return caso;
    }
    if (accion === 'prorroga') {
      if (esBaja(st)) throw err('Ese alumno está dado de baja.'); if (!caso || (caso.estado !== 'pendiente' && caso.estado !== 'prorroga')) throw err('Ese alumno no tiene un caso pendiente.');
      const hasta = String(b.hasta || ''); if (!/^\d{4}-\d{2}-\d{2}$/.test(hasta) || hasta <= hoy) throw err('Elige una fecha de prórroga posterior a hoy.'); if (hasta > sumaDias(hoy, 180)) throw err('La prórroga no puede pasar de 180 días.'); if (motivo.length < 3) throw err('Escribe las condiciones o el motivo de la prórroga.');
      caso.estado = 'prorroga'; caso.prorroga = { hasta, motivo, por: u, porNombre: n, fecha: new Date().toISOString() }; delete caso.prorrogaVencida; nota(caso, 'prorroga', 'Prórroga hasta el ' + fl(hasta) + '. ' + motivo, u, n); ponDoc('bajas', sid, caso);
      audita(u, null, 'Otorgó una prórroga a un alumno', st.mat + ' · ' + st.nombre + ' · hasta ' + hasta);
      try { avisaAlumno('baja', sid, 'Prórroga para regularizar tu situación', 'Control escolar te concedió una prórroga hasta el ' + fl(hasta) + ' para regularizar tu situación (' + motivo + '). Pasa a Control escolar antes de esa fecha; de lo contrario podría proceder tu baja.', 'prorroga:' + sid + ':' + hasta); } catch (e) {}
      try { evaluaCob(sid); } catch (e) {} return caso;
    }
    if (accion === 'descartar') {
      if (!caso || caso.estado !== 'pendiente') throw err('Ese alumno no tiene un caso pendiente.'); if (motivo.length < 3) throw err('Escribe por qué se descarta la alerta.');
      caso.estado = 'descartado'; caso.silencio = sumaDias(hoy, 30); nota(caso, 'descartado', 'Se descartó la alerta por 30 días. ' + motivo, u, n); ponDoc('bajas', sid, caso); audita(u, null, 'Descartó una alerta de baja', st.mat + ' · ' + st.nombre); return caso;
    }
    if (accion === 'reincorporar') {
      if (!esBaja(st)) throw err('Ese alumno no está dado de baja.'); if (motivo.length < 3) throw err('Escribe el motivo de la reincorporación.');
      st.baja = Object.assign({}, st.baja, { revertida: new Date().toISOString(), revertidaPor: u, revertidaMotivo: motivo }); ponDoc('students', sid, st);
      caso = caso || base(); caso.estado = 'resuelto'; caso.causas = {}; nota(caso, 'reincorporacion', 'Reincorporado. ' + motivo, u, n); ponDoc('bajas', sid, caso); audita(u, null, 'Reincorporó a un alumno dado de baja', st.mat + ' · ' + st.nombre);
      try { avisaAlumno('baja', sid, 'Reincorporación a la escuela', 'Te informamos que tu baja fue revertida: ya puedes entrar de nuevo a la plataforma.', 'reinc:' + sid + ':' + Date.now()); } catch (e) {} return caso;
    }
    throw err('Acción no válida.');
  }
  return { cfg, guardaCfg, revisa, revisaAlumno, hook, decide, bajaDe, prorrogaVigente, pendientes, MOTIVOS, esBaja };
}
module.exports = { crea, MOTIVOS };
