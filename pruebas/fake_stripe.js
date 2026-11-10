'use strict';
const http = require('http'), fs = require('fs'), path = require('path');
const [puerto, dir] = [parseInt(process.argv[2], 10), process.argv[3]]; fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
let n = 0; const log = o => { const f = path.join(dir, 'stripe.json'), a = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f)) : []; a.push(o); fs.writeFileSync(f, JSON.stringify(a)); };
http.createServer((rq, rs) => {
  rq.on('error', () => {}); rs.on('error', () => {}); const x = []; rq.on('data', d => x.push(d));
  rq.on('end', () => {
    const cuerpo = Buffer.concat(x).toString(), j = (c, o) => { rs.writeHead(c, { 'Content-Type': 'application/json' }); rs.end(JSON.stringify(o)); };
    const forma = {}; cuerpo.split('&').filter(Boolean).forEach(p => { const [k, v] = p.split('='); forma[decodeURIComponent(k)] = decodeURIComponent((v || '').replace(/\+/g, ' ')); });
    log({ m: rq.method, url: rq.url, auth: rq.headers.authorization || '', tipo: rq.headers['content-type'] || '', forma });
    if ((rq.headers.authorization || '') !== 'Bearer sk_test_ok12345678') return j(401, { error: { message: 'Invalid API Key provided: sk_test_****' } });
    if (rq.method === 'GET' && rq.url === '/v1/account') return j(200, { id: 'acct_1TEST', country: 'MX', business_profile: { name: 'Universidad Lafragua' } });
    if (rq.method === 'POST' && rq.url === '/v1/checkout/sessions') { n++; return j(200, { id: 'cs_test_' + n, object: 'checkout.session', url: 'https://checkout.stripe.test/c/pay/cs_test_' + n, amount_total: parseInt(forma['line_items[0][price_data][unit_amount]'], 10), currency: 'mxn' }); }
    j(404, { error: { message: 'No existe' } });
  });
}).listen(puerto); console.log('listo');
