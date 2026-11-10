'use strict';
/* ===========================================================================
   Pagos en línea (Stripe Checkout: tarjeta y OXXO) y facturas (datos fiscales, solicitudes y registro de CFDI).
   Sin dependencias. Los montos SIEMPRE se calculan en el servidor; el pago solo se registra cuando llega el aviso
   (webhook) firmado por Stripe.
   =========================================================================== */
const https = require('https'), http = require('http'), crypto = require('crypto');
const RFC = /^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$/;
const REGIMENES = { '601': 'General de Ley Personas Morales', '603': 'Personas Morales con Fines no Lucrativos', '605': 'Sueldos y Salarios', '606': 'Arrendamiento', '607': 'Enajenación o Adquisición de Bienes', '608': 'Demás ingresos', '610': 'Residentes en el Extranjero', '611': 'Ingresos por Dividendos', '612': 'Personas Físicas con Actividades Empresariales y Profesionales', '614': 'Ingresos por intereses', '615': 'Régimen de los ingresos por obtención de premios', '616': 'Sin obligaciones fiscales', '620': 'Sociedades Cooperativas de Producción', '621': 'Incorporación Fiscal', '622': 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras', '623': 'Opcional para Grupos de Sociedades', '624': 'Coordinados', '625': 'RESICO: actividades empresariales con ingresos por plataformas tecnológicas', '626': 'Régimen Simplificado de Confianza (RESICO)' };
const USOS = { G01: 'Adquisición de mercancías', G03: 'Gastos en general', D01: 'Honorarios médicos, dentales y gastos hospitalarios', D10: 'Pagos por servicios educativos (colegiaturas)', S01: 'Sin efectos fiscales', CP01: 'Pagos' };
const CFG0 = { activo: false, stripeKey: '', webhookSecret: '', metodos: { tarjeta: true, oxxo: true }, oxxoDias: 3, urlPublica: '', facturas: { activo: false, diaLimite: 5 } };
function firmaStripeOk(raw, cabecera, secreto, ahoraS, tolerancia) {
  const partes = String(cabecera || '').split(',').map(x => x.trim().split('=')), t = (partes.find(p => p[0] === 't') || [])[1], vs = partes.filter(p => p[0] === 'v1').map(p => p[1]);
  if (!t || !vs.length || !secreto) return false; if (Math.abs((ahoraS || Math.floor(Date.now() / 1000)) - parseInt(t, 10)) > (tolerancia || 300)) return false;
  const esperado = crypto.createHmac('sha256', secreto).update(t + '.' + raw, 'utf8').digest('hex');
  return vs.some(v => { try { return v.length === esperado.length && crypto.timingSafeEqual(Buffer.from(v), Buffer.from(esperado)); } catch (e) { return false; } });
}
function aForm(o, pre, out) {
  out = out || []; Object.keys(o).forEach(k => { const v = o[k], n = pre ? pre + '[' + k + ']' : k; if (v === undefined || v === null) return; if (Array.isArray(v)) v.forEach((x, i) => { if (x !== null && typeof x === 'object') aForm(x, n + '[' + i + ']', out); else out.push(encodeURIComponent(n + '[' + i + ']') + '=' + encodeURIComponent(String(x))); }); else if (typeof v === 'object') aForm(v, n, out); else out.push(encodeURIComponent(n) + '=' + encodeURIComponent(String(v))); }); return out;
}
function crea(ctx) {
  const { q, leeDoc, cifra, descifra, hoyMx, audita, difunde, cobHook, pendientesSrv, avisaAlumno, candados, ENV } = ctx;
  const idm = () => crypto.randomBytes(10).toString('hex'), err = (m, c) => { const e = new Error(m); e.cod = c || 400; return e; };
  const leeSis = (id, def) => { const r = q.uno.get('sistema', id); try { return r ? JSON.parse(r.data) : def; } catch (e) { return def; } }, ponSis = (id, o) => q.pon.run('sistema', id, JSON.stringify(o), Date.now());
  const ponDoc = (col, id, o) => { q.pon.run(col, id, JSON.stringify(o), Date.now()); difunde(col, id); };
  function cfg() { const g = leeSis('pagos', {}), c = JSON.parse(JSON.stringify(CFG0)); ['activo', 'oxxoDias', 'urlPublica'].forEach(k => { if (g[k] !== undefined) c[k] = g[k]; }); Object.assign(c.metodos, g.metodos || {}); Object.assign(c.facturas, g.facturas || {}); c.stripeKey = g.stripeKey ? (descifra(g.stripeKey) || '') : ''; c.webhookSecret = g.webhookSecret ? (descifra(g.webhookSecret) || '') : ''; return c; }
  function cfgPublica(base) { const c = cfg(); return { activo: c.activo, metodos: c.metodos, oxxoDias: c.oxxoDias, urlPublica: c.urlPublica, facturas: c.facturas, claveGuardada: !!c.stripeKey, firmaGuardada: !!c.webhookSecret, modoPrueba: /^sk_test_/.test(c.stripeKey), webhookUrl: (c.urlPublica || base || '').replace(/\/+$/, '') + '/api/pagos-linea/webhook' }; }
  function guardaCfg(n) {
    const act = cfg(), c = JSON.parse(JSON.stringify(CFG0));
    c.activo = !!n.activo; c.metodos = { tarjeta: (n.metodos || {}).tarjeta !== false, oxxo: !!(n.metodos || {}).oxxo }; c.oxxoDias = Math.round(Number(n.oxxoDias) || 3); if (!(c.oxxoDias >= 1 && c.oxxoDias <= 7)) throw err('Los días de vigencia de la ficha de OXXO van de 1 a 7.');
    c.urlPublica = String(n.urlPublica || '').trim().replace(/\/+$/, ''); if (c.urlPublica && !/^https?:\/\/[^\s/]+/i.test(c.urlPublica)) throw err('La dirección pública debe empezar con https://');
    const f = n.facturas || {}; c.facturas = { activo: !!f.activo, diaLimite: Math.round(Number(f.diaLimite)) }; if (!(c.facturas.diaLimite >= 0 && c.facturas.diaLimite <= 28)) throw err('El día límite para pedir factura va de 0 a 28 (0 = solo el mismo mes).');
    const k = typeof n.stripeKey === 'string' && n.stripeKey.length ? n.stripeKey.trim() : act.stripeKey, w = typeof n.webhookSecret === 'string' && n.webhookSecret.length ? n.webhookSecret.trim() : act.webhookSecret;
    if (k && !/^sk_(test|live)_[A-Za-z0-9]{10,}$/.test(k)) throw err('La llave secreta de Stripe debe empezar con sk_test_ o sk_live_.'); if (w && !/^whsec_[A-Za-z0-9]{8,}$/.test(w)) throw err('El secreto del webhook debe empezar con whsec_.');
    if (c.activo && (!k || !w)) throw err('Para activar los pagos en línea escribe la llave secreta de Stripe y el secreto del webhook.'); if (c.activo && !c.metodos.tarjeta && !c.metodos.oxxo) throw err('Elige al menos un método de pago.');
    ponSis('pagos', { activo: c.activo, metodos: c.metodos, oxxoDias: c.oxxoDias, urlPublica: c.urlPublica, facturas: c.facturas, stripeKey: k ? cifra(k) : '', webhookSecret: w ? cifra(w) : '' });
  }
  /* ---- Stripe ---- */
  function stripe(c, metodo, ruta, form) {
    return new Promise((ok, mal) => {
      const base = new URL(String(ENV.LF_STRIPE_BASE || 'https://api.stripe.com')), cuerpo = form ? aForm(form).join('&') : '', lib = base.protocol === 'https:' ? https : http;
      const rq = lib.request({ protocol: base.protocol, hostname: base.hostname, port: base.port || undefined, path: ruta, method: metodo, headers: Object.assign({ Authorization: 'Bearer ' + c.stripeKey }, cuerpo ? { 'Content-Type': 'application/x-www-form-urlencoded', 'Content-Length': Buffer.byteLength(cuerpo) } : {}) }, r => { const t = []; r.on('data', d => t.push(d)); r.on('end', () => { let j = {}; try { j = JSON.parse(Buffer.concat(t).toString('utf8')); } catch (e) {} if (r.statusCode >= 200 && r.statusCode < 300) ok(j); else mal(new Error((j.error && j.error.message) || ('Stripe respondió ' + r.statusCode))); }); });
      rq.setTimeout(25000, () => rq.destroy(new Error('Stripe no respondió a tiempo.'))); rq.on('error', mal); rq.end(cuerpo || undefined);
    });
  }
  async function probar() { const c = cfg(); if (!c.stripeKey) throw err('Guarda primero la llave secreta de Stripe.'); const j = await stripe(c, 'GET', '/v1/account'); return { cuenta: j.id || '', pais: j.country || '', nombre: (j.business_profile && j.business_profile.name) || (j.settings && j.settings.dashboard && j.settings.dashboard.display_name) || '' }; }
  /* ---- lo que puede pagar el alumno ---- */
  function opciones(sid) {
    const d = pendientesSrv(sid); if (!d) return []; const out = [], venc = d.pend.filter(x => x.vencido);
    if (venc.length) out.push({ id: 'vencido', label: 'Pagar lo vencido (' + venc.length + (venc.length === 1 ? ' colegiatura' : ' colegiaturas') + ')', monto: Math.round(venc.reduce((a, x) => a + x.monto, 0) * 100) / 100, cc: venc.map(x => x.id) });
    d.pend.slice(0, 8).forEach((x, i) => out.push({ id: 'c:' + x.id, label: (i === 0 && !venc.length ? 'Siguiente pago: ' : '') + x.c, monto: x.monto, cc: [x.id] }));
    return out;
  }
  const baseDe = (c, req) => { const b = c.urlPublica || String(ENV.LF_URL_PUBLICA || '').replace(/\/+$/, ''); if (b) return b; const h = String(req.headers['x-forwarded-host'] || req.headers.host || ''); return (String(req.headers['x-forwarded-proto'] || 'http').split(',')[0]) + '://' + h; };
  function estado(sid) { const c = cfg(); return { activo: c.activo && !!c.stripeKey, facturas: !!c.facturas.activo, metodos: c.metodos, opciones: c.activo ? opciones(sid) : [], recientes: q.lista.all('pagos_linea').map(r => { try { return JSON.parse(r.data); } catch (e) { return null; } }).filter(x => x && x.sid === sid).sort((a, b) => String(b.creada).localeCompare(String(a.creada))).slice(0, 5).map(x => ({ id: x.id, monto: x.monto, estado: x.estado, creada: x.creada, folio: x.folio || '', descripcion: x.descripcion })) }; }
  async function checkout(sid, opcion, req) {
    const c = cfg(); if (!c.activo || !c.stripeKey) throw err('Los pagos en línea no están activos.');
    const o = opciones(sid).find(x => x.id === opcion); if (!o) throw err('Esa opción de pago ya no está disponible. Actualiza la página.');
    const cents = Math.round(o.monto * 100); if (cents < 1000) throw err('El monto mínimo de pago en línea es de $10.00.');
    const metodos = []; if (c.metodos.tarjeta) metodos.push('card'); if (c.metodos.oxxo && cents <= 1000000) metodos.push('oxxo'); if (!metodos.length) throw err('Ese monto no se puede pagar con los métodos activos. Acude a Control escolar.');
    const st = leeDoc('students', sid) || {}, id = idm(), base = baseDe(c, req), mail = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(st.mail || '').trim()) ? String(st.mail).trim() : '';
    const reg = { id, sid, nombre: st.nombre || '', mat: st.mat || '', opcion, descripcion: o.label, monto: o.monto, cents, conceptos: o.cc, metodos, estado: 'creada', creada: new Date().toISOString() };
    const form = { mode: 'payment', success_url: base + '/?pago=ok', cancel_url: base + '/?pago=cancelado', client_reference_id: sid, line_items: [{ price_data: { currency: 'mxn', unit_amount: cents, product_data: { name: String(o.label).slice(0, 120) + ' · ' + String(st.mat || '') } }, quantity: 1 }], payment_method_types: metodos, metadata: { ref: id, sid, opcion }, payment_intent_data: { metadata: { ref: id, sid } } };
    if (metodos.includes('oxxo')) form.payment_method_options = { oxxo: { expires_after_days: c.oxxoDias } }; if (mail) form.customer_email = mail;
    const r = await stripe(c, 'POST', '/v1/checkout/sessions', form); if (!r.id || !r.url) throw err('Stripe no devolvió la dirección de pago.', 502);
    reg.stripe = r.id; reg.url = r.url; ponDoc('pagos_linea', id, reg); audita(sid, req, 'Inició un pago en línea', o.label + ' · $' + o.monto);
    return { url: r.url, id };
  }
  /* ---- folios (el mismo contador que usa Control escolar: meta/folio) ---- */
  async function siguienteFolio() {
    for (let i = 0; i < 20; i++) { const v = candados.get('meta/folio'); if (!v || v.exp < Date.now()) break; await new Promise(r => setTimeout(r, 250)); }
    candados.set('meta/folio', { holder: 'servidor', exp: Date.now() + 3000 });
    try { const r = q.uno.get('meta', 'folio'); let d = {}; try { d = r ? JSON.parse(r.data) : {}; } catch (e) {} const n = (d.n || 0) + 1; q.pon.run('meta', 'folio', JSON.stringify({ n }), Date.now()); difunde('meta', 'folio'); return 'R-' + String(n).padStart(6, '0'); }
    finally { candados.delete('meta/folio'); }
  }
  async function registra(reg, sesion, metodo) {
    if (reg.estado === 'pagada') return { repetido: true };
    if (sesion.amount_total !== reg.cents || String(sesion.currency || '').toLowerCase() !== 'mxn') { reg.estado = 'discrepancia'; reg.nota = 'El monto cobrado (' + sesion.amount_total + ' ' + sesion.currency + ') no coincide con el esperado (' + reg.cents + ' mxn).'; ponDoc('pagos_linea', reg.id, reg); audita(null, null, 'Pago en línea con monto distinto', reg.id); return { discrepancia: true }; }
    const folio = await siguienteFolio(), hoy = hoyMx(), led = leeDoc('ledger', reg.sid) || { pagos: [] }, pago = { id: crypto.randomBytes(8).toString('hex'), folio, fecha: hoy, monto: reg.monto, metodo, ref: (metodo === 'Tarjeta' ? 'Stripe · tarjeta · ' : 'Stripe · OXXO · ') + sesion.id, cc: reg.conceptos, byn: 'Pago en línea', linea: true, via: 'stripe', sesion: sesion.id };
    led.pagos = (led.pagos || []).concat([pago]); ponDoc('ledger', reg.sid, led); try { cobHook('ledger', reg.sid); } catch (e) {}
    reg.estado = 'pagada'; reg.pagada = new Date().toISOString(); reg.folio = folio; reg.pagoId = pago.id; reg.metodo = metodo; ponDoc('pagos_linea', reg.id, reg);
    audita(null, null, 'Pago en línea recibido', reg.mat + ' · ' + reg.nombre + ' · $' + reg.monto + ' · ' + folio);
    try { avisaAlumno('pago', reg.sid, 'Pago recibido', 'Recibimos tu pago en línea de $' + reg.monto.toFixed(2) + ' (folio ' + folio + '). Ya puedes descargar tu recibo en tu portal.', 'plpago:' + reg.id); } catch (e) {}
    return { ok: true, folio };
  }
  async function webhook(req, res, leeCuerpo, responde) {
    const c = cfg(), raw = (await leeCuerpo(req, 512 * 1024)).toString('utf8');
    if (!c.webhookSecret || !firmaStripeOk(raw, req.headers['stripe-signature'], c.webhookSecret)) return responde(res, 400, { error: 'Firma no válida.' });
    let ev; try { ev = JSON.parse(raw); } catch (e) { return responde(res, 400, { error: 'Evento no válido.' }); }
    const s = ev.data && ev.data.object ? ev.data.object : {}, ref = (s.metadata && s.metadata.ref) || '', r0 = ref ? q.uno.get('pagos_linea', ref) : null; let reg = null; try { reg = r0 ? JSON.parse(r0.data) : null; } catch (e) {}
    if (!reg || reg.stripe !== s.id) return responde(res, 200, { received: true, ignorado: true });
    try {
      if (ev.type === 'checkout.session.completed') { if (s.payment_status === 'paid') await registra(reg, s, 'Tarjeta'); else if (reg.estado === 'creada') { reg.estado = 'esperando'; ponDoc('pagos_linea', reg.id, reg); } }
      else if (ev.type === 'checkout.session.async_payment_succeeded') await registra(reg, s, 'Depósito');
      else if (ev.type === 'checkout.session.async_payment_failed') { if (reg.estado !== 'pagada') { reg.estado = 'fallida'; ponDoc('pagos_linea', reg.id, reg); } }
      else if (ev.type === 'checkout.session.expired') { if (reg.estado === 'creada' || reg.estado === 'esperando') { reg.estado = 'expirada'; ponDoc('pagos_linea', reg.id, reg); } }
    } catch (e) { console.error('Pagos en línea:', e.message); return responde(res, 500, { error: 'No se pudo registrar.' }); }
    return responde(res, 200, { received: true });
  }
  function sesiones() { return q.lista.all('pagos_linea').map(r => { try { const d = JSON.parse(r.data); delete d.url; return d; } catch (e) { return null; } }).filter(Boolean).sort((a, b) => String(b.creada).localeCompare(String(a.creada))).slice(0, 150); }
  /* ---- datos fiscales y facturas ---- */
  function guardaFiscal(sid, b) {
    const rfc = String(b.rfc || '').trim().toUpperCase(), razon = String(b.razon || '').trim().toUpperCase().slice(0, 150), cp = String(b.cp || '').trim(), reg = String(b.regimen || ''), uso = String(b.uso || ''), correo = String(b.correo || '').trim();
    if (!RFC.test(rfc)) throw err('El RFC no es válido (12 caracteres para persona moral o 13 para persona física).'); if (razon.length < 3) throw err('Escribe tu nombre o razón social tal como aparece en tu constancia de situación fiscal.');
    if (!/^\d{5}$/.test(cp)) throw err('El código postal fiscal debe tener 5 dígitos.'); if (!REGIMENES[reg]) throw err('Elige tu régimen fiscal.'); if (!USOS[uso]) throw err('Elige el uso del CFDI.'); if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(correo)) throw err('Escribe el correo donde quieres recibir tu factura.');
    ponDoc('fiscal', sid, { sid, rfc, razon, cp, regimen: reg, uso, correo, act: new Date().toISOString() });
  }
  function solicita(sid, pagoId) {
    const c = cfg(); if (!c.facturas.activo) throw err('La facturación en línea no está activa. Pide tu factura en Control escolar.');
    const fi = leeDoc('fiscal', sid); if (!fi) throw err('Primero captura tus datos fiscales.');
    const led = leeDoc('ledger', sid) || { pagos: [] }, g = (led.pagos || []).find(x => x.id === pagoId); if (!g) throw err('No encontramos ese pago.', 404); if (g.estado === 'pendiente' || g.estado === 'rechazado') throw err('Ese pago todavía no está confirmado.');
    const hoy = hoyMx(), mesPago = String(g.fecha || '').slice(0, 7), lim = (() => { const d = new Date(mesPago + '-01T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() + 1); d.setUTCDate(c.facturas.diaLimite || 1); const dia = c.facturas.diaLimite; if (!dia) { d.setUTCDate(1); d.setUTCDate(0); } return d.toISOString().slice(0, 10); })();
    if (hoy > lim) throw err('Ya pasó el plazo para pedir la factura de este pago (' + lim.split('-').reverse().join('/') + '). Acude a Control escolar.');
    const ya = q.lista.all('facturas').some(r => { try { const d = JSON.parse(r.data); return d.sid === sid && d.pagoId === pagoId && d.estado !== 'rechazada' && d.estado !== 'cancelada'; } catch (e) { return false; } }); if (ya) throw err('Ya pediste la factura de este pago.');
    const st = leeDoc('students', sid) || {}, id = idm(), f = { id, sid, nombre: st.nombre || '', mat: st.mat || '', pagoId, folioPago: g.folio || '', fechaPago: g.fecha, monto: g.monto, concepto: 'Colegiatura y servicios educativos · ' + (g.folio || ''), rfc: fi.rfc, razon: fi.razon, cp: fi.cp, regimen: fi.regimen, uso: fi.uso, correo: fi.correo, estado: 'solicitada', solicitada: new Date().toISOString() };
    ponDoc('facturas', id, f); return f;
  }
  function emitir(id, b, quien) {
    const r = q.uno.get('facturas', id); if (!r) throw err('No existe esa solicitud.', 404); const f = JSON.parse(r.data); if (f.estado !== 'solicitada') throw err('Esa solicitud ya no está pendiente.');
    const uuid = String(b.uuid || '').trim().toUpperCase(), serie = String(b.serie || '').trim().slice(0, 20), folio = String(b.folio || '').trim().slice(0, 20), idArch = x => (x && /^[0-9a-f]{32}$/.test(String(x.id || '')) && q.uArch.get(String(x.id))) ? { id: String(x.id), name: String(x.name || 'factura').slice(0, 120) } : null;
    if (!/^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$/.test(uuid)) throw err('El folio fiscal (UUID) no es válido.'); const xml = idArch(b.xml), pdf = idArch(b.pdf); if (!xml) throw err('Sube el XML de la factura.'); if (!pdf) throw err('Sube el PDF de la factura.');
    if (q.lista.all('facturas').some(x => { try { return JSON.parse(x.data).uuid === uuid; } catch (e) { return false; } })) throw err('Ese folio fiscal ya está registrado en otra factura.');
    Object.assign(f, { estado: 'emitida', uuid, serie, folio, xml, pdf, emitida: new Date().toISOString(), emitidaPor: quien }); ponDoc('facturas', id, f);
    audita(quien, null, 'Registró una factura', f.mat + ' · ' + uuid); try { avisaAlumno('pago', f.sid, 'Tu factura está lista', 'Ya puedes descargar tu factura (PDF y XML) del pago ' + f.folioPago + ' en tu portal.', 'fac:' + id + ':emitida'); } catch (e) {} return f;
  }
  function rechaza(id, motivo, quien) {
    const r = q.uno.get('facturas', id); if (!r) throw err('No existe esa solicitud.', 404); const f = JSON.parse(r.data); if (f.estado !== 'solicitada') throw err('Esa solicitud ya no está pendiente.'); const m = String(motivo || '').trim().slice(0, 300); if (m.length < 5) throw err('Escribe el motivo para que el alumno lo sepa.');
    Object.assign(f, { estado: 'rechazada', motivo: m, rechazada: new Date().toISOString(), rechazadaPor: quien }); ponDoc('facturas', id, f); audita(quien, null, 'Rechazó una solicitud de factura', f.mat + ' · ' + m);
    try { avisaAlumno('pago', f.sid, 'No se pudo emitir tu factura', 'No pudimos emitir la factura del pago ' + f.folioPago + '. Motivo: ' + m + ' Corrige tus datos fiscales y vuelve a pedirla.', 'fac:' + id + ':rechazada'); } catch (e) {} return f;
  }
  function facturas(estadoF) { return q.lista.all('facturas').map(r => { try { return JSON.parse(r.data); } catch (e) { return null; } }).filter(f => f && (!estadoF || f.estado === estadoF)).sort((a, b) => String(b.solicitada).localeCompare(String(a.solicitada))).slice(0, 300); }
  return { cfg, cfgPublica, guardaCfg, probar, estado, checkout, webhook, sesiones, opciones, guardaFiscal, solicita, emitir, rechaza, facturas, REGIMENES, USOS };
}
module.exports = { crea, firmaStripeOk, aForm, RFC, REGIMENES, USOS };
