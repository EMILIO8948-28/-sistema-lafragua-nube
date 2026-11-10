import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
TOK='tok-al-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/alm && mkdir -p /tmp/alm')
RAIZ='/tmp/nb'
def arranca(n,extra):
    port=3120+n;datos='/tmp/alm/d%d'%n;os.makedirs(datos,exist_ok=True)
    env=dict(os.environ,PORT=str(port),DATA_DIR=datos,LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_VERIFICAR_DISCO='1');env.update(extra(datos) if callable(extra) else extra)
    pr=subprocess.Popen(['node','servidor.js'],cwd=RAIZ,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen('http://127.0.0.1:%d/salud'%port,timeout=1);break
        except Exception:pass
    return pr,'http://127.0.0.1:%d'%port
def fake(contenido):
    def f(datos):
        a=datos+'.mountinfo';open(a,'w').write(contenido.replace('@DATOS',os.path.abspath(datos)));return {'LF_MOUNTINFO_ARCHIVO':a}
    return f
RAIZLINEA='22 1 0:20 / / rw shared:1 - overlay overlay rw\n23 22 0:21 / /proc rw - proc proc rw\n'
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
def admin(pw,B):
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900},accept_downloads=True);ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'");return b,ctx,pg
hoy=time.strftime('%d/%m/%Y')
with sync_playwright() as pw:
    # ---------- 1. disco temporal ----------
    p1,B1=arranca(1,fake(RAIZLINEA));b1,c1,pg=admin(pw,B1)
    info=c1.request.get(B1+'/api/almacenamiento').json()
    ok('detecta_el_disco_temporal',info['persistente'] is False and info['montaje']=='/' and info['sistema']=='overlay' and 'temporal' in info['motivo'])
    ok('dice_cuando_se_creo_la_base',info['creada'] is not None and info['creada'][:10]==time.strftime('%Y-%m-%d',time.gmtime()) or info['creada'][:10] in (time.strftime('%Y-%m-%d'),))
    ok('aun_no_hay_respaldo_descargado',info['ultimaDescarga'] is None)
    pg.evaluate("ir('home')");pg.wait_for_selector('#hAlm:not([hidden])');t=pg.inner_text('#hAlm')
    ok('aviso_rojo_en_el_panel','disco temporal' in t and 'nómina administrativa' in t and 'Disks' in t and '/data' in t and 'DATA_DIR' in t and 'se creó el' in t and 'ya se reiniciaron' in t)
    ok('el_aviso_es_rojo',pg.evaluate("document.getElementById('hAlm').style.borderColor")=='var(--bad)')
    with pg.expect_download() as d:pg.click('#hAlmGo')
    ok('el_boton_descarga_el_respaldo_completo',d.value.suggested_filename.startswith('respaldo-completo-') and d.value.suggested_filename.endswith('.zip'))
    time.sleep(0.8);info=c1.request.get(B1+'/api/almacenamiento').json();ok('queda_registrada_la_descarga',info['ultimaDescarga'] is not None and info['ultimaDescarga'][:10]==time.strftime('%Y-%m-%d',time.gmtime()))
    pg.evaluate("abreDlgBk()");pg.wait_for_selector('#dBk[open]');W(pg,"document.getElementById('bkAlm').textContent.length>10")
    ok('el_cuadro_de_respaldo_muestra_el_estado_y_el_boton_del_servidor','DISCO TEMPORAL' in pg.inner_text('#bkAlm') and 'Último respaldo completo descargado' in pg.inner_text('#bkAlm') and pg.is_visible('#bkSrv'))
    pg.evaluate("document.getElementById('dBk').close()")
    # ---------- permisos ----------
    c1.request.post(B1+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    cx=b1.new_context(viewport={'width':1100,'height':900});pc=cx.new_page();pc.on("pageerror",lambda e:errs.append(str(e)));pc.goto(B1+'/');W(pc,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pc.fill('#lgU','caja1');pc.fill('#lgP','clave-caja-123');pc.click('#lgGo');W(pc,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pc.wait_for_timeout(800)
    ok('quien_no_es_administrador_no_ve_el_aviso_ni_la_informacion',pc.is_hidden('#hAlm') and cx.request.get(B1+'/api/almacenamiento').status==403)
    b1.close();p1.terminate();time.sleep(0.4)
    # ---------- 2. disco persistente ----------
    p2,B2=arranca(2,fake(RAIZLINEA+'45 22 8:1 / @DATOS rw - ext4 /dev/sda1 rw\n'));b2,c2,pg2=admin(pw,B2)
    i2=c2.request.get(B2+'/api/almacenamiento').json()
    ok('detecta_el_disco_persistente',i2['persistente'] is True and i2['sistema']=='ext4' and i2['montaje'].endswith('/d2'))
    pg2.evaluate("ir('home')");pg2.wait_for_selector('#hAlm:not([hidden])');t2=pg2.inner_text('#hAlm')
    ok('con_disco_persistente_solo_recuerda_el_respaldo','Aún no has descargado un respaldo completo' in t2 and 'disco temporal' not in t2 and pg2.evaluate("document.getElementById('hAlm').style.borderColor")=='var(--warn)')
    c2.request.get(B2+'/api/respaldo/descargar');pg2.evaluate("ALM=null;ALMT=0;ir('home')");pg2.wait_for_timeout(1200)
    ok('tras_descargar_un_respaldo_desaparece_el_aviso',pg2.is_hidden('#hAlm'))
    pg2.evaluate("abreDlgBk()");pg2.wait_for_selector('#dBk[open]');W(pg2,"document.getElementById('bkAlm').textContent.length>10")
    ok('el_cuadro_dice_disco_persistente','disco persistente ✓' in pg2.inner_text('#bkAlm') and 'hace 0 días' in pg2.inner_text('#bkAlm'))
    b2.close();p2.terminate();time.sleep(0.4)
    # ---------- 3. no se puede comprobar ----------
    p3,B3=arranca(3,{'LF_MOUNTINFO_ARCHIVO':'/tmp/alm/no-existe'});b3,c3,pg3=admin(pw,B3)
    i3=c3.request.get(B3+'/api/almacenamiento').json();ok('si_no_puede_comprobar_no_alarma',i3['persistente'] is None)
    pg3.evaluate("ir('home')");c3.request.get(B3+'/api/respaldo/descargar');pg3.evaluate("ALM=null;ALMT=0;ir('home')");pg3.wait_for_timeout(1200);ok('y_no_muestra_aviso_rojo',pg3.is_hidden('#hAlm'))
    b3.close();p3.terminate();time.sleep(0.4)
    # ---------- 4. confirmado por el administrador del servidor ----------
    p4,B4=arranca(4,dict(fake(RAIZLINEA)('/tmp/alm/d4'),LF_DISCO_OK='1'));b4,c4,pg4=admin(pw,B4)
    i4=c4.request.get(B4+'/api/almacenamiento').json();ok('LF_DISCO_OK_silencia_el_aviso',i4['persistente'] is True)
    b4.close();p4.terminate()
    # ---------- 5. instalación local (no es la nube) ----------
    env=dict(os.environ,PORT='3126',DATA_DIR='/tmp/alm/d5',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1');env.pop('LF_VERIFICAR_DISCO',None);env.pop('LF_MODO',None);env.pop('RENDER',None);os.makedirs('/tmp/alm/d5',exist_ok=True)
    p5=subprocess.Popen(['node','servidor.js'],cwd=RAIZ,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen('http://127.0.0.1:3126/salud',timeout=1);break
        except Exception:pass
    b5,c5,pg5=admin(pw,'http://127.0.0.1:3126');i5=c5.request.get('http://127.0.0.1:3126/api/almacenamiento').json();ok('fuera_de_la_nube_no_se_revisa',i5['persistente'] is None);b5.close();p5.terminate()
ok('sin_errores_js',len(errs)==0)
if errs:print('ERRORES JS:',errs[:3])
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
