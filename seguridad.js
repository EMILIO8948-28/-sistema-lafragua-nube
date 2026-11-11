'use strict';
/* ===========================================================================
   Seguridad y privacidad: verificación en dos pasos (TOTP, RFC 6238), aviso de privacidad con aceptación
   y reglas de conservación de datos (INE, firmas, registros) con depuración. Sin dependencias.
   =========================================================================== */
const crypto = require('crypto'), fs = require('fs'), path = require('path');
const B32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
function base32(buf) { let bits = 0, v = 0, s = ''; for (const b of buf) { v = (v << 8) | b; bits += 8; while (bits >= 5) { s += B32[(v >>> (bits - 5)) & 31]; bits -= 5; } } if (bits > 0) s += B32[(v << (5 - bits)) & 31]; return s; }
function deBase32(s) { let bits = 0, v = 0; const out = []; for (const c of String(s).toUpperCase().replace(/=+$/, '')) { const i = B32.indexOf(c); if (i < 0) continue; v = (v << 5) | i; bits += 5; if (bits >= 8) { out.push((v >>> (bits - 8)) & 255); bits -= 8; } } return Buffer.from(out); }
function codigoTotp(secreto, paso, digitos) { const b = Buffer.alloc(8); b.writeBigUInt64BE(BigInt(paso)); const h = crypto.createHmac('sha1', secreto).update(b).digest(), o = h[h.length - 1] & 15, n = ((h[o] & 0x7f) << 24) | (h[o + 1] << 16) | (h[o + 2] << 8) | h[o + 3]; return String(n % Math.pow(10, digitos || 6)).padStart(digitos || 6, '0'); }
function verificaTotp(secretoB32, codigo, ultimoPaso, ahoraMs) {
  const s = deBase32(secretoB32), p = Math.floor((ahoraMs || Date.now()) / 30000), c = String(codigo || '').replace(/\s/g, '');
  if (!/^\d{6}$/.test(c)) return 0;
  for (const d of [0, -1, 1]) { const paso = p + d; if (paso > (ultimoPaso || 0) && crypto.timingSafeEqual(Buffer.from(codigoTotp(s, paso)), Buffer.from(c))) return paso; }
  return 0;
}
const esc = t => String(t == null ? '' : t).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const PRIV0 = { entidad: 'Universidad Lafragua', domicilio: '', correo: '', telefono: '', responsable: 'Control escolar', version: 1, actualizado: '', aceptacion: false, extra: '' };
const CONS0 = { ineAnios: 1, firmasAnios: 5, mensajesMeses: 12, sesionesPagoMeses: 24, auditoriaMeses: 36, prospectosMeses: 18 };
function crea(ctx) {
  const { db, q, leeDoc, cifra, descifra, audita, claveOk, ARCH, difunde, hoyMx, ENV } = ctx, ahora = ctx.ahora || (() => Date.now());
  ['totp TEXT', 'totp_resp TEXT', 'totp_ult INTEGER'].forEach(c => { try { db.exec('ALTER TABLE usuarios ADD COLUMN ' + c); } catch (e) { /* ya existe */ } });
  const sSet = db.prepare('UPDATE usuarios SET totp = ?, totp_resp = ?, totp_ult = ? WHERE u = ?'), sUlt = db.prepare('UPDATE usuarios SET totp_ult = ? WHERE u = ?'), sResp = db.prepare('UPDATE usuarios SET totp_resp = ? WHERE u = ?'), sDos = db.prepare('SELECT u, totp, totp_resp FROM usuarios WHERE totp IS NOT NULL');
  const leeSis = (id, def) => { const r = q.uno.get('sistema', id); try { return r ? JSON.parse(r.data) : def; } catch (e) { return def; } }, ponSis = (id, o) => q.pon.run('sistema', id, JSON.stringify(o), Date.now());
  const err = (m, c) => { const e = new Error(m); e.cod = c || 400; return e; }, sha = t => crypto.createHash('sha256').update(String(t)).digest('hex');
  const pend = new Map(), tickets = new Map(); setInterval(() => { const a = ahora(); pend.forEach((v, k) => { if (v.exp < a) pend.delete(k); }); tickets.forEach((v, k) => { if (v.exp < a) tickets.delete(k); }); }, 60000).unref();
  const escuela = () => (leeSis('privacidad', {}).entidad || PRIV0.entidad);
  /* ---- dos pasos ---- */
  const fila = u => q.usr.get(u) || {}, tiene = u => !!fila(u).totp;
  const codigosNuevos = () => { const L = []; for (let i = 0; i < 10; i++) { const r = base32(crypto.randomBytes(7)).slice(0, 10); L.push(r.slice(0, 5) + '-' + r.slice(5)); } return L; };
  const normRec = c => String(c || '').toUpperCase().replace(/[^A-Z2-7]/g, '');
  function iniciar(u) { const secreto = base32(crypto.randomBytes(20)); pend.set(u, { secreto, exp: ahora() + 600000 }); const e = escuela(); return { secreto, uri: 'otpauth://totp/' + encodeURIComponent(e + ':' + u) + '?secret=' + secreto + '&issuer=' + encodeURIComponent(e) + '&algorithm=SHA1&digits=6&period=30' }; }
  function activar(u, codigo) {
    const p = pend.get(u); if (!p || p.exp < ahora()) throw err('Pide un código QR nuevo: el anterior caducó.'); const paso = verificaTotp(p.secreto, codigo, 0, ahora()); if (!paso) throw err('El código no es correcto. Revisa la hora de tu teléfono e inténtalo de nuevo.');
    const cods = codigosNuevos(); sSet.run(cifra(p.secreto), JSON.stringify(cods.map(c => sha(normRec(c)))), paso, u); pend.delete(u); return cods;
  }
  function desactivar(u) { sSet.run(null, null, null, u); }
  function regenerar(u) { const cods = codigosNuevos(); sResp.run(JSON.stringify(cods.map(c => sha(normRec(c)))), u); return cods; }
  function restantes(u) { try { return JSON.parse(fila(u).totp_resp || '[]').length; } catch (e) { return 0; } }
  function emiteTicket(u) { const t = crypto.randomBytes(24).toString('hex'); tickets.set(t, { u, exp: ahora() + 300000, n: 0 }); return t; }
  function usaTicket(t, codigo) {
    const k = tickets.get(String(t || '')); if (!k || k.exp < ahora()) throw err('Tu inicio de sesión caducó. Vuelve a escribir tu contraseña.', 401);
    const f = fila(k.u); if (!f.totp) { tickets.delete(t); throw err('Tu inicio de sesión caducó.', 401); } const c = String(codigo || '').trim();
    let ok = false;
    if (/^\d{6}$/.test(c.replace(/\s/g, ''))) { const sec = descifra(f.totp), paso = sec ? verificaTotp(sec, c, f.totp_ult || 0, ahora()) : 0; if (paso) { sUlt.run(paso, k.u); ok = true; } }
    else { const h = sha(normRec(c)); let L = []; try { L = JSON.parse(f.totp_resp || '[]'); } catch (e) {} const i = normRec(c).length === 10 ? L.indexOf(h) : -1; if (i > -1) { L.splice(i, 1); sResp.run(JSON.stringify(L), k.u); ok = 'recuperacion'; } }
    if (!ok) { k.n++; if (k.n >= 5) { tickets.delete(t); throw err('Demasiados intentos. Vuelve a escribir tu contraseña.', 429); } throw err('El código no es correcto.', 401); }
    tickets.delete(t); return { u: k.u, recuperacion: ok === 'recuperacion' };
  }
  function lista() { return sDos.all().map(r => r.u); }
  function reiniciarPorEntorno() { String(ENV.LF_2FA_REINICIAR || '').split(',').map(x => x.trim().toLowerCase()).filter(Boolean).forEach(u => { if (tiene(u)) { desactivar(u); audita(u, null, 'Verificación en dos pasos desactivada desde el servidor (LF_2FA_REINICIAR)'); console.log('Verificación en dos pasos desactivada para', u); } }); }
  const cfgSeg = () => Object.assign({ exigir2fa: false }, leeSis('seguridad', {}));
  /* ---- aviso de privacidad ---- */
  const cfgPriv = () => Object.assign({}, PRIV0, leeSis('privacidad', {}));
  function guardaPriv(n) {
    const a = cfgPriv(), c = { entidad: String(n.entidad || '').trim().slice(0, 150), domicilio: String(n.domicilio || '').trim().slice(0, 300), correo: String(n.correo || '').trim().slice(0, 120), telefono: String(n.telefono || '').trim().slice(0, 40), responsable: String(n.responsable || '').trim().slice(0, 120), extra: String(n.extra || '').trim().slice(0, 2000), aceptacion: !!n.aceptacion };
    if (c.entidad.length < 3) throw err('Escribe el nombre de la institución.'); if (!c.domicilio) throw err('Escribe el domicilio de la institución (lo exige el aviso de privacidad).'); if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(c.correo)) throw err('Escribe el correo para ejercer los derechos ARCO.'); if (!c.responsable) throw err('Escribe quién atiende los datos personales.');
    const cambio = ['entidad', 'domicilio', 'correo', 'telefono', 'responsable', 'extra'].some(k => c[k] !== a[k]);
    ponSis('privacidad', Object.assign(c, { version: cambio ? (a.version || 1) + 1 : (a.version || 1), actualizado: cambio ? hoyMx() : a.actualizado }));
  }
  const cfgCons = () => Object.assign({}, CONS0, leeSis('conservacion', {}));
  function guardaCons(n) {
    const c = { ineAnios: +n.ineAnios, firmasAnios: +n.firmasAnios, mensajesMeses: +n.mensajesMeses, sesionesPagoMeses: +n.sesionesPagoMeses, auditoriaMeses: +n.auditoriaMeses, prospectosMeses: n.prospectosMeses === undefined || n.prospectosMeses === '' ? cfgCons().prospectosMeses : +n.prospectosMeses };
    if (!(c.prospectosMeses >= 3 && c.prospectosMeses <= 120)) throw err('Los meses para conservar prospectos van de 3 a 120.');
    if (!(c.ineAnios >= 0 && c.ineAnios <= 15)) throw err('Los años de conservación de la INE van de 0 a 15.'); if (!(c.firmasAnios >= 1 && c.firmasAnios <= 30)) throw err('Los años de conservación de las firmas van de 1 a 30.');
    if (!(c.mensajesMeses >= 1 && c.mensajesMeses <= 120) || !(c.sesionesPagoMeses >= 6 && c.sesionesPagoMeses <= 120) || !(c.auditoriaMeses >= 12 && c.auditoriaMeses <= 240)) throw err('Revisa los plazos: mensajes 1-120 meses, pagos en línea 6-120, registro de actividad 12-240.');
    ponSis('conservacion', c);
  }
  function paginaPrivacidad() {
    const p = cfgPriv(), c = cfgCons(), L = t => '<li>' + t + '</li>', fecha = p.actualizado ? p.actualizado.split('-').reverse().join('/') : '—';
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aviso de privacidad · ' + esc(p.entidad) + '</title><style>:root{--bg:#f5f7f9;--ink:#16253b;--muted:#5d6b7e;--card:#fff;--line:#dde3ea}@media(prefers-color-scheme:dark){:root{--bg:#10161d;--ink:#e6edf5;--muted:#9fb0c3;--card:#18212b;--line:#2a3643}}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,Segoe UI,Roboto,sans-serif}main{max-width:820px;margin:0 auto;padding:24px 18px 60px}article{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px}h1{font-size:26px;margin:0 0 4px}h2{font-size:18px;margin:22px 0 6px}p,li{color:var(--ink)}.m{color:var(--muted);font-size:14px}ul{padding-left:20px}</style></head><body><main><article><h1>Aviso de privacidad</h1><p class="m">' + esc(p.entidad) + ' · Versión ' + p.version + ' · Última actualización: ' + fecha + '</p>'
      + '<h2>1. Quién es el responsable de tus datos</h2><p><b>' + esc(p.entidad) + '</b>, con domicilio en ' + esc(p.domicilio) + ', es responsable del tratamiento de tus datos personales, conforme a la Ley Federal de Protección de Datos Personales en Posesión de los Particulares. Los atiende: ' + esc(p.responsable) + (p.telefono ? ' · Tel. ' + esc(p.telefono) : '') + ' · ' + esc(p.correo) + '.</p>'
      + '<h2>2. Qué datos personales recabamos</h2><ul>' + L('<b>Identificación y contacto:</b> nombre, matrícula, fecha de nacimiento o edad, domicilio, teléfono, correo electrónico y datos de contacto de emergencia o tutor.') + L('<b>Académicos:</b> plan de estudios, grupo, asistencia, calificaciones, constancias, boletas y títulos.') + L('<b>Patrimoniales y financieros:</b> pagos, adeudos, recibos y, si pides factura, tus datos fiscales (RFC, razón social, código postal, régimen fiscal).') + L('<b>Fotografía y firma:</b> tu fotografía para la credencial y tu firma autógrafa digital capturada en pantalla en fichas de inscripción y contratos.') + L('<b>Si eres prospecto:</b> nombre, teléfono, correo, programa de interés y, en su caso, el mensaje que nos escribes, para darte información y darte seguimiento.') + L('<b>Atención personalizada:</b> si solicitas orientación o seguimiento, registramos el tema y los acuerdos de la atención, incluidos datos personales o sensibles que tú nos compartas (por ejemplo, de salud o familiares); solo los ve el personal que te atiende.') + L('<b>Documentos de identidad:</b> copia o fotografía de tu identificación oficial (INE), solo del personal docente contratado.') + '</ul>'
      + '<h2>3. Datos personales sensibles</h2><p>Si presentas un justificante médico, recabamos información sobre tu estado de salud para justificar tus inasistencias. Solo la usamos para ese fin y su tratamiento requiere tu consentimiento expreso, que otorgas al presentar el justificante.</p>'
      + '<h2>4. Para qué usamos tus datos</h2><p><b>Finalidades necesarias:</b> inscribirte y darte seguimiento académico; emitir credenciales, boletas, constancias y títulos; cobrar y registrar tus pagos y emitir recibos y facturas; contratar y pagar a nuestro personal docente; cumplir obligaciones ante la autoridad educativa y fiscal.</p><p><b>Finalidades adicionales:</b> enviarte avisos operativos por correo electrónico o WhatsApp (por ejemplo, adeudos, respuestas a tus solicitudes y fechas de evaluación). Si no deseas recibirlos, pídelo en ' + esc(p.correo) + ' y dejaremos de enviártelos sin afectar tu servicio.</p>'
      + '<h2>5. Con quién compartimos tus datos</h2><p>No vendemos tus datos. Los compartimos solo cuando es necesario: con la autoridad educativa y fiscal que lo requiera; con el procesador de pagos en línea (Stripe) para cobrar con tarjeta u OXXO; con el proveedor de facturación electrónica que emite tus facturas; y con los proveedores de correo electrónico y mensajería (WhatsApp) para enviarte avisos.</p>'
      + '<h2>6. Tus derechos (ARCO)</h2><p>Tienes derecho a Acceder a tus datos, Rectificarlos, Cancelarlos y Oponerte a su uso, así como a revocar tu consentimiento. Para ejercerlos escribe a ' + esc(p.correo) + ' con tu nombre completo, matrícula y la descripción de lo que solicitas; te responderemos en un máximo de 20 días hábiles.</p>'
      + '<h2>7. Cuánto tiempo conservamos tus datos</h2><ul>' + L('Expediente académico: el tiempo que exige la normativa educativa.') + L('Copia de la INE del personal docente: ' + (c.ineAnios === 0 ? 'se elimina al terminar la relación de trabajo' : c.ineAnios + (c.ineAnios === 1 ? ' año' : ' años') + ' después de terminar el contrato') + '.') + L('Firmas capturadas en pantalla: ' + c.firmasAnios + ' años después de la fecha del documento.') + L('Registro de avisos enviados: ' + c.mensajesMeses + ' meses. Registro de pagos en línea: ' + c.sesionesPagoMeses + ' meses.') + L('Datos de prospectos que no se inscriben: ' + c.prospectosMeses + ' meses después del último contacto.') + L('Registros de atención personalizada: se conservan mientras dure la atención y el tiempo necesario para su seguimiento; su acceso es confidencial.') + '</ul>'
      + '<h2>8. Seguridad</h2><p>Protegemos tus datos con contraseñas, permisos por función, cifrado de llaves y respaldos, verificación en dos pasos para administradores y un registro de actividad.</p><h2>9. Cookies</h2><p>Solo usamos una cookie de sesión necesaria para mantener tu acceso. No usamos cookies de publicidad.</p>'
      + (p.extra ? '<h2>10. Información adicional</h2><p>' + esc(p.extra).replace(/\n/g, '<br>') + '</p>' : '') + '<h2>Cambios a este aviso</h2><p>Cualquier cambio se publicará en esta misma dirección y se te pedirá confirmar de nuevo que lo conoces.</p><p class="m">Borrador generado por la plataforma: debe ser revisado por tu asesor jurídico antes de publicarse.</p></article></main></body></html>';
  }
  const acuerdoDe = u => leeSis('priv_' + u, null) || (leeDoc('privacidad_ok', u));
  function aceptar(u, version) { const p = cfgPriv(); if (version !== p.version) throw err('El aviso cambió. Actualiza la página y léelo de nuevo.'); q.pon.run('privacidad_ok', u, JSON.stringify({ u, version: p.version, fecha: new Date().toISOString() }), Date.now()); }
  const pendienteDe = u => { const p = cfgPriv(); if (!p.aceptacion) return 0; const a = leeDoc('privacidad_ok', u); return a && a.version === p.version ? 0 : p.version; };
  const aceptaciones = () => { const p = cfgPriv(), L = q.lista.all('privacidad_ok').map(r => { try { return JSON.parse(r.data); } catch (e) { return null; } }).filter(Boolean); return { total: L.length, vigentes: L.filter(a => a.version === p.version).length }; };
  /* ---- conservación ---- */
  const fechaCorte = (anios, meses) => { const d = new Date(); if (anios) d.setFullYear(d.getFullYear() - anios); if (meses) d.setMonth(d.getMonth() - meses); return d.toISOString().slice(0, 10); };
  const docs = col => q.lista.all(col).map(r => { try { return { id: r.id, d: JSON.parse(r.data) }; } catch (e) { return null; } }).filter(Boolean);
  const refContrato = c => String(c.hasta || c.firmado || String(c.creado || c.fecha || '').slice(0, 10) || '');
  function candidatos() {
    const c = cfgCons(), r = { ine: [], firmasContrato: [], firmasFicha: [], mensajes: 0, sesionesPago: 0, auditoria: 0, prospectos: [] }, corteIne = fechaCorte(c.ineAnios), corteFir = fechaCorte(c.firmasAnios);
    docs('contratos').forEach(({ id, d }) => { const ref = refContrato(d); if (!ref) return; if (d.ine && Object.values(d.ine).some(x => x && x.id) && ref < corteIne) r.ine.push(id); if (d.firmas && Object.values(d.firmas).some(x => x && x.png) && ref < corteFir) r.firmasContrato.push(id); });
    docs('fichasins').forEach(({ id, d }) => { const fs = Object.values(d.firmas || {}).filter(x => x && x.png), f = fs.length ? String(fs[0].fecha || '').slice(0, 10) : ''; if (f && f < corteFir) r.firmasFicha.push(id); });
    docs('prospectos').forEach(({ id, d }) => { if (d.estado !== 'inscrito' && String(d.ultimo || d.creado || '').slice(0, 10) < fechaCorte(0, c.prospectosMeses)) r.prospectos.push(id); });
    r.mensajes = db.prepare('SELECT COUNT(*) AS n FROM mensajes WHERE ts < ?').get(new Date(fechaCorte(0, c.mensajesMeses) + 'T00:00:00Z').getTime()).n;
    r.sesionesPago = docs('pagos_linea').filter(({ d }) => d.estado !== 'creada' && String(d.creada || '').slice(0, 10) < fechaCorte(0, c.sesionesPagoMeses)).length;
    r.auditoria = db.prepare('SELECT COUNT(*) AS n FROM auditoria WHERE fecha < ?').get(new Date(fechaCorte(0, c.auditoriaMeses) + 'T00:00:00Z').getTime()).n;
    return r;
  }
  function borraArchivo(id) { try { fs.unlinkSync(path.join(ARCH, id)); } catch (e) {} q.bArch.run(id); }
  function depura(cats) {
    const c = cfgCons(), cand = candidatos(), out = {}; cats = cats || [];
    if (cats.includes('ine')) { let n = 0; cand.ine.forEach(id => { const d = leeDoc('contratos', id); if (!d || !d.ine) return; Object.values(d.ine).forEach(x => { if (x && x.id) { borraArchivo(x.id); n++; } }); d.ine = {}; d.inePurgada = new Date().toISOString(); q.pon.run('contratos', id, JSON.stringify(d), Date.now()); difunde('contratos', id); }); out.ine = n; }
    if (cats.includes('firmasContrato')) { let n = 0; cand.firmasContrato.forEach(id => { const d = leeDoc('contratos', id); if (!d || !d.firmas) return; Object.keys(d.firmas).forEach(k => { if (d.firmas[k] && d.firmas[k].png) { delete d.firmas[k].png; d.firmas[k].imagenPurgada = true; n++; } }); q.pon.run('contratos', id, JSON.stringify(d), Date.now()); difunde('contratos', id); }); out.firmasContrato = n; }
    if (cats.includes('firmasFicha')) { let n = 0; cand.firmasFicha.forEach(id => { const d = leeDoc('fichasins', id); if (!d || !d.firmas) return; Object.keys(d.firmas).forEach(k => { if (d.firmas[k] && d.firmas[k].png) { delete d.firmas[k].png; d.firmas[k].imagenPurgada = true; n++; } }); q.pon.run('fichasins', id, JSON.stringify(d), Date.now()); difunde('fichasins', id); }); out.firmasFicha = n; }
    if (cats.includes('prospectos')) { let n = 0; cand.prospectos.forEach(id => { db.prepare("DELETE FROM docs WHERE coleccion = 'prospectos' AND id = ?").run(id); n++; }); out.prospectos = n; }
    if (cats.includes('mensajes')) out.mensajes = db.prepare('DELETE FROM mensajes WHERE ts < ?').run(new Date(fechaCorte(0, c.mensajesMeses) + 'T00:00:00Z').getTime()).changes;
    if (cats.includes('sesionesPago')) { let n = 0; docs('pagos_linea').forEach(({ id, d }) => { if (d.estado !== 'creada' && String(d.creada || '').slice(0, 10) < fechaCorte(0, c.sesionesPagoMeses)) { db.prepare("DELETE FROM docs WHERE coleccion = 'pagos_linea' AND id = ?").run(id); n++; } }); out.sesionesPago = n; }
    if (cats.includes('auditoria')) out.auditoria = db.prepare('DELETE FROM auditoria WHERE fecha < ?').run(new Date(fechaCorte(0, c.auditoriaMeses) + 'T00:00:00Z').getTime()).changes;
    return out;
  }
  return { tiene, iniciar, activar, desactivar, regenerar, restantes, emiteTicket, usaTicket, lista, reiniciarPorEntorno, cfgSeg, guardaSeg: n => ponSis('seguridad', { exigir2fa: !!n.exigir2fa }), cfgPriv, guardaPriv, cfgCons, guardaCons, paginaPrivacidad, aceptar, pendienteDe, aceptaciones, candidatos, depura, verificaTotp, codigoTotp, base32 };
}
module.exports = { crea, verificaTotp, codigoTotp, base32, deBase32 };
