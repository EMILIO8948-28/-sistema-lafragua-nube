'use strict';
/* ===========================================================================
   Cambios de grupo y de plan de estudios de un alumno, con su historial (students.movimientos).
   =========================================================================== */
function crea(ctx) {
  const { q, leeDoc, difunde, audita, hoyMx, planesYExtra, perCerrado, hook } = ctx;
  const err = (m, c) => { const e = new Error(m); e.cod = c || 400; return e; };
  const ponDoc = (col, id, o) => { q.pon.run(col, id, JSON.stringify(o), Date.now()); difunde(col, id); };
  const planDe = st => st.programa || st.carrera || '';
  const etq = g => g ? g.num + ' · ' + g.per + (g.cuat ? ' · cuat. ' + g.cuat : '') : 'sin grupo';
  const grupos = () => q.lista.all('grupos').map(r => { try { return { id: r.id, d: JSON.parse(r.data) }; } catch (e) { return null; } }).filter(Boolean);
  const verifica = (sid) => {
    const st = leeDoc('students', sid); if (!st) throw err('No existe ese alumno.', 404);
    if (st.baja && !st.baja.revertida) throw err('Ese alumno está dado de baja. Reincorpóralo primero.');
    const e = leeDoc('egresados', sid); if (e && !e.revertido) throw err('Ese alumno es egresado.');
    return st;
  };
  const sacaDeGrupos = (sid, filtro) => { const quitados = []; grupos().forEach(({ id, d }) => { if (Array.isArray(d.alumnos) && d.alumnos.includes(sid) && filtro(d)) { d.alumnos = d.alumnos.filter(x => x !== sid); ponDoc('grupos', id, d); quitados.push(d); } }); return quitados; };
  const mete = (sid, gid) => { const g = leeDoc('grupos', gid); g.alumnos = (g.alumnos || []).concat([sid]); ponDoc('grupos', gid, g); return g; };
  const registra = (st, mov, quien) => { st.movimientos = (st.movimientos || []).concat([Object.assign({ t: new Date().toISOString(), fecha: hoyMx(), por: quien.u, porNombre: quien.name || quien.u }, mov)]); };
  function cambiaGrupo(sid, gid, motivo, quien) {
    const st = verifica(sid); motivo = String(motivo || '').trim().slice(0, 400); if (motivo.length < 3) throw err('Escribe el motivo del cambio.');
    const g = gid ? leeDoc('grupos', String(gid)) : null; if (!g) throw err('Elige el grupo al que se cambia.'); if (g.plan !== planDe(st)) throw err('Ese grupo es de otro plan de estudios (' + g.plan + '). Para cambiarlo de plan usa «Cambiar de plan».');
    if (perCerrado(g.per)) throw err('Ese grupo es de un periodo ya cerrado.'); if ((g.alumnos || []).includes(sid)) throw err('El alumno ya está en ese grupo.');
    const antes = sacaDeGrupos(sid, d => d.per === g.per), de = antes.length ? etq(antes[0]) : 'sin grupo';
    mete(sid, String(gid)); registra(st, { tipo: 'grupo', de, a: etq(g), motivo }, quien); ponDoc('students', sid, st);
    audita(quien.u, null, 'Cambió de grupo a un alumno', st.mat + ' · ' + st.nombre + ' · ' + de + ' → ' + etq(g)); try { hook('students', sid); } catch (e) {} return st;
  }
  function cambiaPlan(sid, plan, gid, motivo, quien) {
    const st = verifica(sid); motivo = String(motivo || '').trim().slice(0, 400); if (motivo.length < 3) throw err('Escribe el motivo del cambio.');
    plan = String(plan || ''); const planes = planesYExtra().planes; if (!planes.some(p => p.k === plan)) throw err('Elige un plan de estudios válido.'); const actual = planDe(st); if (plan === actual) throw err('El alumno ya está en ese plan.');
    let g = null; if (gid) { g = leeDoc('grupos', String(gid)); if (!g || g.plan !== plan) throw err('Ese grupo no es del plan nuevo.'); if (perCerrado(g.per)) throw err('Ese grupo es de un periodo ya cerrado.'); }
    /* deja los grupos abiertos de su plan anterior; los de periodos ya cerrados quedan como historia */
    const quitados = sacaDeGrupos(sid, d => d.plan !== plan && !perCerrado(d.per)); if (g) { sacaDeGrupos(sid, d => d.per === g.per && d.plan === plan); mete(sid, String(gid)); }
    st.programa = plan; st.carrera = plan; registra(st, { tipo: 'plan', de: actual, a: plan, motivo, grupo: g ? etq(g) : '', gruposQuitados: quitados.map(etq) }, quien); ponDoc('students', sid, st);
    audita(quien.u, null, 'Cambió de plan de estudios a un alumno', st.mat + ' · ' + st.nombre + ' · ' + actual + ' → ' + plan); try { hook('students', sid); } catch (e) {} return st;
  }
  return { cambiaGrupo, cambiaPlan };
}
module.exports = { crea };
