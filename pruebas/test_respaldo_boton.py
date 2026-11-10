import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3128;B='http://127.0.0.1:%d'%PORT;TOK='tok-rb-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata50 && mkdir -p /tmp/nbdata50')
mi='/tmp/nbdata50.mountinfo';open(mi,'w').write('22 1 0:20 / / rw shared:1 - overlay overlay rw\n45 22 8:1 / /tmp/nbdata50 rw - ext4 /dev/sda1 rw\n')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata50',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_VERIFICAR_DISCO='1',LF_MOUNTINFO_ARCHIVO=mi)
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
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900},accept_downloads=True);ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.2)
    caja=lambda:pg.evaluate("(function(){var r=document.getElementById('bBk').getBoundingClientRect(),m=document.querySelector('main').getBoundingClientRect();return {x:r.left,r:r.right,t:r.top,b:r.bottom,mr:m.right,mt:m.top,vis:r.width>0&&r.height>0}})()")
    r=caja()
    ok('el_boton_esta_arriba_a_la_derecha',r['vis'] and r['t']<110 and abs(r['r']-r['mr'])<30 and r['x']>600)
    ok('ya_no_esta_en_la_barra_de_finanzas',pg.evaluate("document.querySelectorAll('#vAl #bBk').length")==0 and pg.evaluate("document.getElementById('bBk').parentElement.id")=='accTop')
    ok('trae_el_logotipo_de_respaldo_y_el_texto',pg.evaluate("!!document.querySelector('#bBk svg')") and 'Respaldo' in pg.inner_text('#bBk'))
    ok('con_la_insignia_de_advertencia_roja_si_nunca_se_ha_respaldado',pg.evaluate("document.getElementById('bBk').className")=='bk-top rojo' and pg.is_visible('#bkIns') and pg.inner_text('#bkIns')=='!' and 'Aún no has hecho un respaldo' in pg.get_attribute('#bBk','title'))
    for m in ['esc','pagos','nom','na','home']:
        pg.evaluate("ir('%s')"%m);pg.wait_for_timeout(150);ok('visible_en_%s'%m,caja()['vis'] and abs(caja()['r']-r['r'])<2 and pg.is_visible('#bkIns'))
    pg.evaluate("ir('pagos')");pg.click('#bBk');W(pg,"MOD==='bk'");ok('al_pulsarlo_abre_el_modulo_de_respaldos',pg.is_visible('#vBk') and pg.is_visible('#rbAhora'));pg.click('#rbOld');pg.wait_for_selector('#dBk[open]');ok('y_desde_ahi_el_cuadro_de_respaldo_del_navegador',pg.is_visible('#bkJson') and pg.is_visible('#bkSrv'));pg.evaluate("document.getElementById('dBk').close()")
    # ---- respaldo completo del servidor ----
    ctx.request.get(B+'/api/respaldo/descargar');pg.evaluate("ALM=null;ALMT=0;cargaAlm()");pg.wait_for_timeout(1200)
    ok('tras_un_respaldo_completo_la_insignia_desaparece',pg.evaluate("document.getElementById('bBk').className")=='bk-top ok' and pg.is_hidden('#bkIns') and 'Respaldo al día' in pg.get_attribute('#bBk','title'))
    # ---- pasa el tiempo ----
    pg.evaluate("ALM.ultimaDescarga=new Date(Date.now()-30*3600*1000).toISOString();actualizaInsigniaBk()")
    ok('a_las_24_horas_se_pone_amarilla','amarillo' in pg.evaluate("document.getElementById('bBk').className") and pg.is_visible('#bkIns') and 'hace 30 horas' in pg.get_attribute('#bBk','title') and pg.evaluate("getComputedStyle(document.getElementById('bkIns')).backgroundColor")!=pg.evaluate("(function(){var e=document.getElementById('bBk');e.classList.add('rojo');var c=getComputedStyle(document.getElementById('bkIns')).backgroundColor;e.classList.remove('rojo');return c})()"))
    pg.evaluate("ALM.ultimaDescarga=new Date(Date.now()-60*3600*1000).toISOString();actualizaInsigniaBk()");ok('con_dos_dias_dice_hace_2_dias','hace 2 días' in pg.get_attribute('#bBk','title'))
    pg.evaluate("ALM.ultimaDescarga=new Date().toISOString();ALM.persistente=false;actualizaInsigniaBk()")
    ok('con_disco_temporal_es_roja_aunque_haya_respaldo','rojo' in pg.evaluate("document.getElementById('bBk').className") and 'disco temporal' in pg.get_attribute('#bBk','title'));pg.evaluate("ALM.persistente=true;actualizaInsigniaBk()")
    # ---- respaldo de datos (JSON) hecho desde el cuadro ----
    pg.evaluate("ALM.ultimaDescarga=null;localStorage.removeItem(KEY+'-ultbk');actualizaInsigniaBk()");ok('sin_respaldo_vuelve_a_rojo','rojo' in pg.evaluate("document.getElementById('bBk').className"))
    pg.evaluate("abreDlgBk()");pg.wait_for_selector('#dBk[open]')
    with pg.expect_download() as d:pg.click('#bkJson')
    ok('descarga_los_datos',d.value.suggested_filename.startswith('respaldo-colegiaturas-'));pg.wait_for_timeout(800)
    ok('el_respaldo_de_datos_tambien_quita_la_advertencia',pg.evaluate("document.getElementById('bBk').className")=='bk-top ok');pg.evaluate("document.getElementById('dBk').close()")
    # ---- celular ----
    pg.set_viewport_size({'width':400,'height':800});pg.evaluate("ir('esc')");pg.wait_for_timeout(300)
    inter=pg.evaluate("(function(){var a=document.getElementById('bBk').getBoundingClientRect(),c=document.getElementById('ttl').getBoundingClientRect();return !(a.right<=c.left||a.left>=c.right||a.bottom<=c.top||a.top>=c.bottom)})()")
    ok('en_el_celular_solo_muestra_el_icono_y_no_tapa_el_titulo',caja()['vis'] and pg.is_hidden('#bBk .t') and not inter and caja()['r']<=400);pg.set_viewport_size({'width':1100,'height':900})
    # ---- permisos ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    cx=b.new_context(viewport={'width':1100,'height':900});pc=cx.new_page();pc.on("pageerror",lambda e:errs.append(str(e)));pc.goto(B+'/');W(pc,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pc.fill('#lgU','caja1');pc.fill('#lgP','clave-caja-123');pc.click('#lgGo');W(pc,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pc.wait_for_timeout(600)
    ok('quien_no_es_administrador_no_lo_ve_en_el_panel',pc.is_hidden('#bBk'));pc.evaluate("ir('pagos')");pc.wait_for_timeout(300);ok('ni_en_finanzas_aunque_edite_pagos',pc.is_hidden('#bBk'))
    # ---- al iniciar sesión no se ve ----
    pl=b.new_context(viewport={'width':900,'height':800}).new_page();pl.goto(B+'/');W(pl,"typeof sesion==='function'&&document.body.classList.contains('locked')");ok('en_la_pantalla_de_inicio_no_aparece',pl.is_hidden('#bBk'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.screenshot(path='/tmp/bk_1_panel.png');pg.evaluate("ALM.ultimaDescarga=new Date(Date.now()-30*3600*1000).toISOString();localStorage.removeItem(KEY+'-ultbk');actualizaInsigniaBk();ir('home')");pg.wait_for_timeout(300);pg.screenshot(path='/tmp/bk_2_amarilla.png',clip={'x':0,'y':0,'width':1100,'height':260})
    pg.evaluate("ALM.ultimaDescarga=null;actualizaInsigniaBk()");pg.wait_for_timeout(200);pg.screenshot(path='/tmp/bk_3_roja.png',clip={'x':0,'y':0,'width':1100,'height':260})
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
