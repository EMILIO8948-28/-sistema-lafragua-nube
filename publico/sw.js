/* Service worker de la plataforma: deja instalar la app y mostrar la pantalla de entrada sin red.
   NUNCA guarda respuestas de /api, de archivos adjuntos ni de verificación: los datos siempre vienen del servidor. */
var V = 'lafragua-v1', BASE = ['/', '/shim.js', '/nube.js', '/pwa.js', '/logo.png', '/manifest.webmanifest', '/icon-192.png'];
self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(V).then(function (c) { return Promise.all(BASE.map(function (u) { return c.add(new Request(u, { cache: 'reload' })).catch(function () {}); })); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (k) { return Promise.all(k.filter(function (x) { return x !== V; }).map(function (x) { return caches.delete(x); })); }).then(function () { return self.clients.claim(); }));
});
function cacheable(u) { return u.origin === self.location.origin && !/^\/(api|archivo|archivos|verificar|registro|privacidad|salud)(\/|$)/.test(u.pathname); }
self.addEventListener('fetch', function (e) {
  var r = e.request, u = new URL(r.url);
  if (r.method !== 'GET' || !cacheable(u)) return;
  e.respondWith(fetch(r).then(function (res) {
    if (res && res.ok && res.type === 'basic') { var cp = res.clone(); caches.open(V).then(function (c) { c.put(r, cp); }); }
    return res;
  }).catch(function () {
    return caches.match(r).then(function (m) {
      if (m) return m;
      if (r.mode === 'navigate') return caches.match('/').then(function (h) { return h || new Response('Sin conexión. Vuelve a intentarlo cuando tengas internet.', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }); });
      return new Response('', { status: 504 });
    });
  }));
});
