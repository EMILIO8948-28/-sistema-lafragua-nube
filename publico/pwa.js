/* App instalable: registra el service worker y ofrece «Instalar app» cuando el navegador lo permite. */
(function () {
  if (!('serviceWorker' in navigator)) return;
  var seguro = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
  if (seguro) window.addEventListener('load', function () { navigator.serviceWorker.register('/sw.js').catch(function () {}); });
  var ev = null, btn = null;
  var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone;
  function crea() {
    if (btn || standalone) return;
    btn = document.createElement('button'); btn.id = 'pwaInstalar'; btn.type = 'button'; btn.textContent = 'Instalar app';
    btn.setAttribute('style', 'position:fixed;right:14px;bottom:calc(14px + env(safe-area-inset-bottom,0px));z-index:50;padding:10px 16px;border-radius:999px;border:0;background:var(--accent,#0f6b63);color:var(--accent-ink,#fff);font:600 14px/1.2 inherit;box-shadow:0 4px 14px rgba(0,0,0,.25);cursor:pointer');
    btn.onclick = function () { if (!ev) return; ev.prompt(); ev.userChoice.then(function () { ev = null; btn.remove(); btn = null; }).catch(function () {}); };
    document.body.appendChild(btn);
  }
  window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); ev = e; crea(); });
  window.addEventListener('appinstalled', function () { ev = null; if (btn) { btn.remove(); btn = null; } });
})();
