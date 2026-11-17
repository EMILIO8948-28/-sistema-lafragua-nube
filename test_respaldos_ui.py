import subprocess,time,json,os,urllib.request,glob
from playwright.sync_api import sync_playwright
PORT=3220;B='http://127.0.0.1:%d'%PORT;TOK='tok-ru-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata96 /tmp/fd96 && mkdir -p /tmp/nbdata96')
fake=subprocess.Popen(['node','/tmp/fake_destinos.js','3221','3222','/tmp/fd96'],stdout=subprocess.PIPE,text=True);time.sleep(1.0)
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata96',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RESPALDO_TICK_MS='900000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000},accept_downloads=True);ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    for i in (1,2):ctx.request.put(B+'/api/doc/students/s%d'%i,data=json.dumps({'mat':'2026%03d'%i,'nombre':'Alumno %d'%i,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'}),headers=HDR)
    pg.evaluate("ir('home')");pg.wait_for_timeout(800)
    ok('el_panel_tiene_la_tarjeta_respaldos_y_seguridad_para_el_administrador',pg.is_visible('#mBk') and 'Respaldos y seguridad' in pg.inner_text('#mBk') and pg.evaluate("!!document.querySelector('#mBk .ico svg')"))
    pg.click('#mBk');W(pg,"MOD==='bk'");ok('abre_el_modulo',pg.is_visible('#vBk') and 'Respaldos y seguridad' in pg.inner_text('#ttl'))
    W(pg,"RB&&RB.config");t=pg.inner_text('#rbEst')
    ok('al_inicio_avisa_que_no_hay_respaldo_ni_copia_externa','Todavía no hay respaldo' in t and 'No configurada' in t and 'Aún no se ha hecho' in t and 'desactivado' in t)
    ok('el_boton_de_arriba_lleva_al_modulo',(pg.evaluate("ir('home')"),pg.click('#bBk'),pg.wait_for_timeout(400),pg.evaluate("MOD"))[3]=='bk')
    pg.click('#rbOld');pg.wait_for_selector('#dBk[open]');ok('y_el_respaldo_desde_el_navegador_sigue_disponible',pg.is_visible('#bkJson'));pg.evaluate("document.getElementById('dBk').close()")
    # ---- configurar ----
    pg.fill('#rbHora','0');pg.fill('#rbCons','5');pg.check('#rbAct');pg.check('#rbCif');pg.fill('#rbClave','corta');pg.click('#rbGuarda');pg.wait_for_timeout(500)
    ok('rechaza_una_contrasena_de_cifrado_corta','10 caracteres' in pg.inner_text('#rbMsg'))
    pg.fill('#rbClave','clave-de-respaldos-77')
    pg.check('#rbS3A');pg.fill('#rbS3E','http://127.0.0.1:3221');pg.fill('#rbS3R','us-east-1');pg.fill('#rbS3B','mi-bucket');pg.fill('#rbS3P','respaldos/');pg.fill('#rbS3K','AKIAEJEMPLO');pg.fill('#rbS3S','secreto-s3-ejemplo')
    pg.check('#rbCoA');pg.fill('#rbCoH','127.0.0.1');pg.fill('#rbCoP','3222');pg.fill('#rbCoU','escuela@correo.mx');pg.fill('#rbCoC','clave-correo-1');pg.fill('#rbCoD','Plataforma <escuela@correo.mx>');pg.fill('#rbCoPara','dueno@correo.mx, respaldo@correo.mx')
    pg.click('#rbGuarda');W(pg,"document.getElementById('rbMsg').textContent.indexOf('guardada')>-1")
    ok('guarda_y_nunca_muestra_las_llaves',pg.input_value('#rbClave')=='' and pg.input_value('#rbS3S')=='' and pg.input_value('#rbCoC')=='' and 'Guardada' in pg.get_attribute('#rbClave','placeholder') and 'Guardada' in pg.get_attribute('#rbS3S','placeholder') and pg.input_value('#rbS3B')=='mi-bucket' and pg.input_value('#rbCoPara')=='dueno@correo.mx, respaldo@correo.mx')
    pg.click('#rbS3T');W(pg,"document.getElementById('rbMsg').textContent.indexOf('Conexión correcta')>-1");ok('prueba_la_conexion_al_almacenamiento','mi-bucket' in pg.inner_text('#rbMsg'))
    pg.click('#rbCoT');W(pg,"document.getElementById('rbMsg').textContent.indexOf('Correo de prueba enviado')>-1");ok('envia_el_correo_de_prueba','dueno@correo.mx' in pg.inner_text('#rbMsg'))
    pg.fill('#rbCoC','clave-mala');pg.click('#rbCoT');W(pg,"document.getElementById('rbMsg').textContent.indexOf('535')>-1");ok('con_clave_mala_explica_el_error','535' in pg.inner_text('#rbMsg'));pg.fill('#rbCoC','clave-correo-1');pg.click('#rbGuarda');pg.wait_for_timeout(500)
    # ---- respaldar ahora ----
    pg.click('#rbAhora');W(pg,"RB&&RB.estado.historial.length>=1&&!RB.estado.corriendo",60);pg.wait_for_timeout(500)
    t=pg.inner_text('#rbEst');h=pg.inner_text('#rbHist')
    ok('las_tres_tarjetas_quedan_en_verde','Verificado hace menos de una hora' in t and 'Enviada hace menos de una hora' in t and 'almacenamiento externo y correo' in t and 'cifrada' in t)
    ok('el_historial_muestra_el_respaldo_y_sus_destinos','Verificado' in h and 'A petición' in h and '✔ Almacenamiento' in h and '✔ Correo' in h and 'Cifrada' in h)
    ok('lista_los_respaldos_del_servidor',pg.inner_text('#rbLoc').startswith('Respaldos guardados en el servidor (1)'))
    ok('el_boton_de_arriba_queda_sin_advertencia',(pg.evaluate("ALM=null;ALMT=0;cargaAlm()"),pg.wait_for_timeout(900),pg.evaluate("document.getElementById('bBk').className"))[2]=='bk-top ok' and 'copia fuera del servidor' in pg.get_attribute('#bBk','title'))
    pg.evaluate("ir('home')");pg.wait_for_timeout(700);ok('la_tarjeta_del_panel_dice_que_esta_al_dia','✔ Al día' in pg.inner_text('#mBkS'))
    pg.click('#mBk');pg.wait_for_selector('#rbEst')
    pg.click('#rbProbarRes');W(pg,"document.getElementById('rbMsg').textContent.indexOf('base íntegra')>-1");pg.wait_for_timeout(500)
    ok('la_prueba_de_restauracion_se_muestra','Pasó' in pg.inner_text('#rbEst') and 'registros' in pg.inner_text('#rbEst'))
    with pg.expect_download() as d:pg.click('#rbDesc')
    ok('descarga_el_respaldo_completo_del_servidor',d.value.suggested_filename.startswith('respaldo-completo-') and d.value.suggested_filename.endswith('.zip'))
    # ---- sin copia externa: advertencia amarilla ----
    pg.uncheck('#rbS3A');pg.uncheck('#rbCoA');pg.click('#rbGuarda');pg.wait_for_timeout(700);pg.evaluate("ALM=null;ALMT=0;cargaAlm()");pg.wait_for_timeout(900)
    ok('sin_destinos_pone_la_insignia_amarilla_y_lo_explica',pg.evaluate("document.getElementById('bBk').className")=='bk-top amarillo' and 'falta la copia fuera del servidor' in pg.get_attribute('#bBk','title'))
    # ---- permisos ----
    cx=b.new_context(viewport={'width':1200,'height':950});pk=pagina(cx);pk.goto(B+'/')
    t0=time.time()
    while time.time()-t0<30:
        try:
            if pk.evaluate("typeof sesion==='function'&&document.body.classList.contains('locked')"):break
        except Exception:pass
        time.sleep(0.2)
    pk.fill('#lgU','caja1');pk.fill('#lgP','clave-caja1-123');pk.click('#lgGo');W(pk,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pk.wait_for_timeout(900)
    pk.evaluate("ir('bk')");ok('caja_no_ve_ni_entra_al_modulo',pk.is_hidden('#mBk') and pk.evaluate("MOD")=='home' and pk.is_hidden('#vBk'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.evaluate("ir('bk')");pg.wait_for_timeout(500);pg.screenshot(path='/tmp/rb_modulo.png',full_page=True)
    b.close()
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
