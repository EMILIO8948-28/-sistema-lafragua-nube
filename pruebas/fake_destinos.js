'use strict';
const http = require('http'), net = require('net'), fs = require('fs'), path = require('path');
const [pS3, pSmtp, dir] = [parseInt(process.argv[2], 10), parseInt(process.argv[3], 10), process.argv[4]]; fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
const log = (n, o) => { const f = path.join(dir, n + '.json'); const a = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f)) : []; a.push(o); fs.writeFileSync(f, JSON.stringify(a)); };
http.createServer((rq, rs) => { rq.on('error', () => {}); rs.on('error', () => {}); const t = []; rq.on('data', x => t.push(x)); rq.on('end', () => { const b = Buffer.concat(t), clave = decodeURIComponent(rq.url.split('?')[0]); const dest = path.join(dir, 's3', clave); fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.writeFileSync(dest, b); log('s3', { m: rq.method, url: clave, n: b.length, auth: rq.headers.authorization || '' }); rs.writeHead(200); rs.end(); }); }).listen(pS3);
net.createServer(s => {
  s.on('error', () => {}); let modo = 'cmd', datos = '', act = {}, buf = ''; s.write('220 simulado\r\n');
  s.on('data', d => { buf += d.toString('latin1'); let i; while ((i = buf.indexOf('\r\n')) > -1) { const l = buf.slice(0, i); buf = buf.slice(i + 2);
    if (modo === 'data') { if (l === '.') { act.cuerpo = datos; log('correos', act); act = {}; datos = ''; modo = 'cmd'; s.write('250 ok\r\n'); } else datos += l + '\r\n'; continue; }
    if (/^EHLO/.test(l)) s.write('250-simulado\r\n250 AUTH PLAIN\r\n'); else if (/^AUTH PLAIN/.test(l)) { act.auth = Buffer.from(l.slice(11), 'base64').toString('latin1'); s.write(act.auth.endsWith('clave-correo-1') ? '235 ok\r\n' : '535 credenciales incorrectas\r\n'); }
    else if (/^MAIL FROM/.test(l)) s.write('250 ok\r\n'); else if (/^RCPT TO/.test(l)) { (act.para = act.para || []).push(l.slice(8)); s.write('250 ok\r\n'); } else if (l === 'DATA') { modo = 'data'; s.write('354 adelante\r\n'); } else if (l === 'QUIT') { s.write('221 adiós\r\n'); s.end(); } else s.write('500 no\r\n'); } });
}).listen(pSmtp);
console.log('listo');
