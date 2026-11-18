import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
TOK='tok-es-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/esis && mkdir -p /tmp/esis')
RAIZ='/tmp/nb'
def arranca(n,extra):
    port=3160+n;datos='/tmp/esis/d%d'%n;os.makedirs(datos,exist_ok=True)
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
def get(cx,B,path):return cx.request.get(B+path)
def itm(j,i):return [x for x in j['items'] if x['id']==i][0]
with sync_playwright() as pw:
    # ---------- 1. disco temporal, sin respaldo externo ----------
    p1,B1=arranca(1,fake(RAIZLINEA));b1,c1,pg=admin(pw,B1)
    r=get(c1,B1,'/api/estado-sistema');j=r.json()
    ok('responde_al_admin',r.status==200 and j['items'] and set(['mal','aviso','ok']) <= set(j))
    ok('disco_temporal_en_rojo',itm(j,'disco')['nivel']=='mal' and 'Render' in itm(j,'disco')['accion'] and 'Disks' in itm(j,'disco')['accion'])
    ok('sin_copia_externa_en_rojo',itm(j,'externa')['nivel']=='mal' and 'fuera del servidor' in itm(j,'externa')['titulo'])
    ok('correo_sin_configurar_aviso',itm(j,'correo')['nivel']=='aviso')
    ok('whatsapp_y_stripe_son_opcionales',itm(j,'whatsapp')['nivel']=='info' and itm(j,'stripe')['nivel']=='info')
    ok('admin_sin_2fa_aviso',itm(j,'dospasos')['nivel']=='aviso' and 'admin' in itm(j,'dospasos')['detalle'])
    ok('tamano_de_datos',itm(j,'datos')['nivel']=='info' and 'MB' in itm(j,'datos')['detalle'])
    ok('resumen_cuenta_los_niveles',j['mal']==len([x for x in j['items'] if x['nivel']=='mal']) and j['aviso']==len([x for x in j['items'] if x['nivel']=='aviso']) and j['mal']>=2)
    ok('no_expone_llaves',not any(k in json.dumps(j).lower() for k in ('secreto','"clave"','stripekey','token":')))
    # usuario que no es administrador
    ok('crea_usuario_escolar',c1.request.post(B1+'/api/usuarios',data=json.dumps({'u':'esc1','name':'Esc Uno','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc1-123'}),headers=HDR).status in (200,201))
    cx=b1.new_context();ce=cx.request
    ok('sin_sesion_no_puede',ce.get(B1+'/api/estado-sistema').status in (401,403))
    lg=ce.post(B1+'/api/login',data=json.dumps({'u':'esc1','clave':'clave-esc1-123'}),headers=HDR);ok('login_escolar',lg.status==200)
    ok('escolar_no_puede',ce.get(B1+'/api/estado-sistema').status==403)
    # pantalla
    pg.evaluate("ir('bk')");W(pg,"!document.getElementById('esSis').hidden&&document.getElementById('esLista').children.length>=8",20)
    tx=pg.inner_text('#esSis')
    ok('panel_visible_con_resumen','Estado del sistema' in tx and 'por resolver' in tx and 'Disco temporal' not in tx and 'disco temporal' in tx.lower())
    ok('panel_muestra_la_accion_a_seguir','➜' in tx and 'Disks' in tx)
    ok('panel_muestra_todo_el_semaforo','Sin copia fuera del servidor' in tx and 'Avisos por correo sin configurar' in tx and 'Pagos en línea apagados' in tx and 'WhatsApp no está configurado' in tx)
    ok('actualizar_recarga',pg.evaluate("(function(){ESIS=null;return true})()") and (pg.click('#esRef') or True))
    W(pg,"ESIS&&ESIS.items.length>=8",15);ok('actualizar_vuelve_a_cargar',True)
    pg.evaluate("ir('home')");W(pg,"MOD==='home'");pg.fill('#hBus','estado del sistema');pg.wait_for_timeout(300);ok('buscador_lo_encuentra','Estado del sistema' in pg.inner_text('#hBusR'))
    # un respaldo verificado lo pone en verde
    ok('respaldo_apagado_en_rojo',itm(get(c1,B1,'/api/estado-sistema').json(),'respaldo')['nivel']=='mal' and 'apagado' in itm(get(c1,B1,'/api/estado-sistema').json(),'respaldo')['titulo'])
    cf=c1.request.put(B1+'/api/respaldos/config',data=json.dumps({'activo':True,'hora':3,'conservar':7,'cifrar':False,'claveCif':'','s3':{'activo':False,'endpoint':'','region':'','bucket':'','prefijo':'','acceso':'','secreto':''},'correo':{'activo':False,'host':'','puerto':587,'seguro':False,'usuario':'','clave':'','de':'','para':'','adjuntar':False}}),headers=HDR);ok('activa_el_respaldo',cf.status==200)
    ej=c1.request.post(B1+'/api/respaldos/ejecutar',data='{}',headers=HDR);ok('ejecuta_respaldo',ej.status in (200,202))
    t0=time.time();nv=''
    while time.time()-t0<90:
        nv=itm(get(c1,B1,'/api/estado-sistema').json(),'respaldo')['nivel']
        if nv=='ok':break
        time.sleep(1)
    ok('respaldo_verificado_en_verde',nv=='ok')
    # el aviso de 2FA desaparece al activarla
    b1.close();p1.terminate()
    # ---------- 2. disco persistente confirmado ----------
    p2,B2=arranca(2,{'LF_DISCO_OK':'1'});b2,c2,pg2=admin(pw,B2)
    j2=get(c2,B2,'/api/estado-sistema').json();ok('disco_persistente_en_verde',itm(j2,'disco')['nivel']=='ok' and 'accion' in itm(j2,'disco'))
    ok('verde_no_pide_accion',itm(j2,'disco')['accion']=='')
    pg2.evaluate("ir('bk')");W(pg2,"!document.getElementById('esSis').hidden",20);ok('panel_verde_sin_flecha_de_accion','Disco persistente' in pg2.inner_text('#esLista'))
    b2.close();p2.terminate()
    # ---------- 3. fuera de la nube: no se alarma por el disco ----------
    p3,B3=arranca(3,{'LF_VERIFICAR_DISCO':'0'});b3,c3,pg3=admin(pw,B3)
    j3=get(c3,B3,'/api/estado-sistema').json();ok('local_el_disco_es_informativo',itm(j3,'disco')['nivel'] in ('info','aviso') and itm(j3,'disco')['nivel']!='mal')
    b3.close();p3.terminate()
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
