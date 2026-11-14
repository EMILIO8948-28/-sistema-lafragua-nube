'use strict';
/* ===========================================================================
   Evaluación docente por los alumnos (formato «EVALUACIÓN DOCENTE LAFRAGUA»).
   - El alumno evalúa al docente de cada asignatura de su grupo a partir de la fecha de evaluación de esa asignatura.
   - La evaluación es ANÓNIMA: cada respuesta se guarda en la colección «evdoc» sin matrícula, usuario ni hora. Para impedir
     que se conteste dos veces, el identificador de la respuesta es un HMAC(clave del servidor, alumno + asignatura): solo el
     servidor puede saber de quién es y nada en la base permite reconstruirlo sin esa clave (archivo evdoc.key en DATA_DIR).
   - 5 secciones de 4 aspectos (escala 1 a 5), valoración general (1 a 5) y 3 preguntas abiertas.
   =========================================================================== */
const crypto = require('crypto'), fs = require('fs'), path = require('path');
const NSEC = 5, NASP = 4, CFG0 = { abierta: true, dias: 0 };
function crea(ctx) {
  const { q, leeDoc, hoyMx, gruposDeAlumno, materiaDeGrupo, datos } = ctx;
  const err = (m, c) => { const e = new Error(m); e.cod = c || 400; return e; };
  let clave = null;
  function laClave() {
    if (clave) return clave;
    const f = path.join(datos, 'evdoc.key');
    try { clave = fs.readFileSync(f, 'utf8').trim(); } catch (e) { clave = ''; }
    if (!/^[0-9a-f]{64}$/.test(clave)) { clave = crypto.randomBytes(32).toString('hex'); fs.writeFileSync(f, clave + '\n', { mode: 0o600 }); }
    return clave;
  }
  const idResp = (sid, mid) => crypto.createHmac('sha256', laClave()).update(sid + '|' + mid).digest('hex').slice(0, 32);
  const leeSis = (id, def) => { const r = q.uno.get('sistema', id); try { return r ? JSON.parse(r.data) : def; } catch (e) { return def; } };
  const cfg = () => Object.assign({}, CFG0, leeSis('evdoc', {}));
  function guardaCfg(n) {
    const c = { abierta: !!n.abierta, dias: Math.round(Number(n.dias) || 0) };
    if (!(c.dias >= 0 && c.dias <= 365)) throw err('Los días para evaluar van de 0 (sin límite) a 365.');
    q.pon.run('sistema', 'evdoc', JSON.stringify(c), Date.now()); return c;
  }
  const suma = (iso, n) => { const d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
  /* Asignaturas de los grupos del alumno con su estado: futura (aún no es la evaluación), pendiente, hecha, cerrada (venció el plazo), sin_docente */
  function materiasDe(sid) {
    const c = cfg(), hoy = hoyMx(), grupos = gruposDeAlumno(sid), out = [];
    q.lista.all('materias').forEach(r => {
      let m; try { m = JSON.parse(r.data); } catch (e) { return; }
      if (!grupos.some(g => materiaDeGrupo(m, g.d))) return;
      let estado;
      if (!m.docId || !leeDoc('docentes', m.docId)) estado = 'sin_docente';
      else if (!m.ev) estado = 'futura';
      else if (q.uno.get('evdoc', idResp(sid, r.id))) estado = 'hecha';
      else if (hoy < m.ev) estado = 'futura';
      else if (c.dias > 0 && hoy > suma(m.ev, c.dias)) estado = 'cerrada';
      else estado = 'pendiente';
      out.push({ mid: r.id, estado, desde: m.ev || '', hasta: c.dias > 0 && m.ev ? suma(m.ev, c.dias) : '', m });
    });
    return out;
  }
  function mias(sid) {
    return { abierta: cfg().abierta, items: materiasDe(sid).map(x => ({ mid: x.mid, estado: x.estado, desde: x.desde, hasta: x.hasta })) };
  }
  const txt = (v, n) => String(v == null ? '' : v).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, ' ').trim().slice(0, n);
  function envia(s, c) {
    if (s.rol !== 'alumno' || !s.alumno) throw err('Solo los alumnos evalúan a sus docentes.', 403);
    if (!cfg().abierta) throw err('La evaluación docente está cerrada por ahora.', 403);
    const mid = String(c.mid || '');
    const x = materiasDe(s.alumno).find(y => y.mid === mid);
    if (!x) throw err('Esa asignatura no es de tu grupo.', 403);
    if (x.estado === 'hecha') throw err('Ya evaluaste a este docente en esta asignatura.', 409);
    if (x.estado === 'futura') throw err('Podrás evaluar a este docente a partir de la evaluación de la asignatura' + (x.desde ? ' (' + x.desde.split('-').reverse().join('/') + ')' : '') + '.', 403);
    if (x.estado === 'cerrada') throw err('Ya terminó el plazo para evaluar esta asignatura.', 403);
    if (x.estado === 'sin_docente') throw err('Esta asignatura todavía no tiene docente asignado.', 400);
    const r = c.r;
    if (!Array.isArray(r) || r.length !== NSEC * NASP || r.some(v => !Number.isInteger(v) || v < 1 || v > 5)) throw err('Califica todos los aspectos del 1 al 5.');
    if (!Number.isInteger(c.g) || c.g < 1 || c.g > 5) throw err('Califica el desempeño general del docente.');
    const m = x.m, hoy = hoyMx();
    const d = { mid, docId: m.docId, per: m.per || '', plan: m.plan || '', cuat: m.cuat || '', nom: txt(m.nom, 120), fecha: hoy, r, g: c.g, fort: txt(c.fort, 1000), mej: txt(c.mej, 1000), com: txt(c.com, 1000) };
    /* sin hora exacta: la fecha de modificación queda al inicio del día para que no sirva de rastro */
    q.pon.run('evdoc', idResp(s.alumno, mid), JSON.stringify(d), Date.parse(hoy + 'T00:00:00Z'));
    return { ok: true };
  }
  /* Respuestas sin ningún dato del alumno: las lee Control escolar */
  function resultados() { return q.lista.all('evdoc').map(r => { try { return JSON.parse(r.data); } catch (e) { return null; } }).filter(Boolean); }
  return { cfg, guardaCfg, mias, envia, resultados, NSEC, NASP };
}
module.exports = { crea };
