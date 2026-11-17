import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3129;B='http://127.0.0.1:%d'%PORT;TOK='tok-ic-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata51 && mkdir -p /tmp/nbdata51')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata51',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=30):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':1000});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(0.8);pg.evaluate("ir('home')");pg.wait_for_timeout(300)
    visibles=pg.evaluate("Array.from(document.querySelectorAll('#vHome button.mod')).filter(function(b){return b.getBoundingClientRect().width>0}).map(function(b){return b.id})")
    ok('el_administrador_ve_las_opciones_del_panel',set(visibles)>={'mPag','mIns','mEsc','mAcu','mA2','mTit','mNot','mUsr'})
    ok('todas_las_opciones_visibles_tienen_su_icono',pg.evaluate("Array.from(document.querySelectorAll('#vHome button.mod')).filter(function(b){return b.getBoundingClientRect().width>0}).every(function(b){var i=b.querySelector('.ico svg');return i&&i.getBoundingClientRect().width>=20&&b.querySelector('.ico').nextElementSibling.tagName==='B'})"))
    ok('cada_opcion_tiene_un_icono_distinto',pg.evaluate("(function(){var s=Array.from(document.querySelectorAll('#vHome button.mod .ico svg')).map(function(x){return x.innerHTML});return s.length>=12&&new Set(s).size===s.length})()"))
    ok('el_icono_va_arriba_del_titulo_y_no_cambia_el_texto',pg.evaluate("(function(){var b=document.getElementById('mPag'),i=b.querySelector('.ico').getBoundingClientRect(),t=b.querySelector('b').getBoundingClientRect();return i.bottom<=t.top+2&&b.querySelector('b').textContent==='Finanzas'})()") and 'Finanzas' in pg.inner_text('#mPag'))
    ok('los_iconos_son_decorativos_para_lectores_de_pantalla',pg.evaluate("Array.from(document.querySelectorAll('#vHome .ico')).every(function(e){return e.getAttribute('aria-hidden')==='true'})"))
    ok('las_tarjetas_ocultas_de_finanzas_siguen_ocultas',all(pg.is_hidden('#'+i) for i in ['mNom','mNa','mVer']))
    pg.screenshot(path='/tmp/ic_1_panel.png',full_page=True)
    # ---- modo oscuro ----
    pg.emulate_media(color_scheme='dark');pg.wait_for_timeout(300);pg.screenshot(path='/tmp/ic_2_oscuro.png',full_page=True)
    c=pg.evaluate("(function(){var e=document.querySelector('#mPag .ico');var s=getComputedStyle(e);return [s.color,s.backgroundColor]})()");ok('en_modo_oscuro_el_icono_conserva_color_y_fondo',c[0]!=c[1] and c[0] not in ('rgba(0, 0, 0, 0)',))
    pg.emulate_media(color_scheme='light')
    # ---- celular ----
    pg.set_viewport_size({'width':390,'height':800});pg.evaluate("ir('home')");pg.wait_for_timeout(300)
    ok('en_celular_no_se_sale_de_la_pantalla',pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"))
    pg.screenshot(path='/tmp/ic_3_celular.png',full_page=True);pg.set_viewport_size({'width':1100,'height':1000})
    # ---- otros roles ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    cx=b.new_context(viewport={'width':1100,'height':900});pc=cx.new_page();pc.on("pageerror",lambda e:errs.append(str(e)));pc.goto(B+'/');W(pc,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pc.fill('#lgU','caja1');pc.fill('#lgP','clave-caja-123');pc.click('#lgGo');W(pc,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pc.wait_for_timeout(600)
    ok('las_opciones_de_otros_roles_tambien_llevan_icono',pc.evaluate("Array.from(document.querySelectorAll('#vHome button.mod')).filter(function(b){return b.getBoundingClientRect().width>0}).every(function(b){return !!b.querySelector('.ico svg')})") and pc.is_visible('#mPag .ico'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
