"""App instalable (PWA): manifiesto, íconos, service worker, modo sin conexión y botón de instalar."""
import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3144;B='http://127.0.0.1:%d'%PORT;TOK='tok-pwa-1'
os.system('rm -rf /tmp/nbdata_pwa /tmp/crl4 && mkdir -p /tmp/nbdata_pwa /tmp/crl4')
RELOJ='/tmp/crl4/reloj.txt';HOY=datetime.date.today().isoformat();open(RELOJ,'w').write(HOY)
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_pwa',LF_SETUP_TOKEN=TOK,LF_SIN_CONTACTO='1',LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ)
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def W(pg,js,t=30):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':420,'height':850});ctx.set_default_timeout(15000)
    api=ctx.request
    r=api.get(B+'/manifest.webmanifest');m=r.json()
    ok('manifiesto_con_tipo_correcto','manifest+json' in r.headers['content-type'])
    ok('manifiesto_completo',m['display']=='standalone' and m['start_url'].startswith('/') and m['scope']=='/' and m['lang']=='es-MX' and m['short_name']=='Lafragua' and m['theme_color']=='#0f6b63')
    ok('manifiesto_con_3_iconos',[i['sizes'] for i in m['icons']]==['192x192','512x512','512x512'] and any(i['purpose']=='maskable' for i in m['icons']))
    from PIL import Image
    import io
    for ic in m['icons']:
        rr=api.get(B+ic['src']);im=Image.open(io.BytesIO(rr.body()))
        ok('icono_'+ic['src'].strip('/'),rr.status==200 and rr.headers['content-type']=='image/png' and '%dx%d'%im.size==ic['sizes'])
    ok('icono_apple',Image.open(io.BytesIO(api.get(B+'/apple-touch-icon.png').body())).size==(180,180))
    r=api.get(B+'/sw.js');ok('sw_sin_cache_y_javascript',r.status==200 and 'javascript' in r.headers['content-type'] and r.headers['cache-control']=='no-cache' and r.headers.get('service-worker-allowed')=='/')
    ok('sw_no_cachea_la_api',"'/api" in r.text() or '(api|' in r.text())
    ok('pwa_js_servido',api.get(B+'/pwa.js').status==200)
    h=api.get(B+'/').text()
    ok('index_enlaza_manifiesto','rel="manifest" href="/manifest.webmanifest"' in h and 'name="theme-color"' in h and 'apple-touch-icon' in h and '<script src="/pwa.js">' in h)
    ok('csp_permite_el_worker',"default-src 'self'" in api.get(B+'/').headers['content-security-policy'] and 'worker-src' not in api.get(B+'/').headers['content-security-policy'])
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.goto(B+'/');pg.wait_for_url('**/configurar.html');
    pg.goto(B+'/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null")
    W(pg,"navigator.serviceWorker.controller!==null||true")
    reg=lambda:pg.evaluate("navigator.serviceWorker.getRegistration().then(function(r){return !!(r&&(r.active||r.installing||r.waiting))})")
    W(pg,"navigator.serviceWorker.getRegistration().then(function(r){window.__r=!!(r&&r.active)});window.__r===true",20)
    ok('service_worker_registrado_y_activo',reg())
    pg.reload();W(pg,"navigator.serviceWorker.controller!==null",20)
    ok('la_pagina_queda_controlada',pg.evaluate("navigator.serviceWorker.controller!==null"))
    # lo que hay en la caché
    ks=pg.evaluate("caches.keys().then(function(k){return caches.open(k[0]).then(function(c){return c.keys().then(function(r){return r.map(function(x){return new URL(x.url).pathname})})})})")
    ok('cachea_la_pantalla_de_entrada',('/' in ks) and ('/shim.js' in ks))
    ok('no_cachea_datos_de_la_api',not any(x.startswith('/api') for x in ks))
    # sin conexión
    ctx.set_offline(True);pg.reload();pg.wait_for_timeout(1500)
    ok('sin_conexion_abre_la_pagina',pg.evaluate("document.body&&document.body.innerText.length>20")  and pg.evaluate("typeof APP!=='undefined'||document.getElementById('lgU')!==null"))
    ctx.set_offline(False)
    # botón de instalar
    pg.reload();W(pg,"typeof APP!=='undefined'")
    ok('sin_evento_no_hay_boton',pg.locator('#pwaInstalar').count()==0)
    pg.evaluate("window.__p=0;var e=new Event('beforeinstallprompt');e.prompt=function(){window.__p++};e.userChoice=Promise.resolve({outcome:'accepted'});window.dispatchEvent(e)")
    pg.wait_for_selector('#pwaInstalar');ok('muestra_boton_instalar',pg.inner_text('#pwaInstalar')=='Instalar app')
    pg.click('#pwaInstalar');W(pg,"window.__p===1&&!document.getElementById('pwaInstalar')")
    ok('boton_llama_a_instalar_y_se_quita',pg.evaluate("window.__p")==1 and pg.locator('#pwaInstalar').count()==0)
    # el SW no rompe el inicio de sesión ni los datos
    ok('api_sigue_respondiendo_en_vivo',api.get(B+'/salud').status==200 and api.get(B+'/api/col/students').status in (200,401,403))
    ok('sin_errores_de_pagina',not errs)
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
