import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3240;B='http://127.0.0.1:%d'%PORT;TOK='tok-au-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata98 /tmp/fd98 && mkdir -p /tmp/nbdata98')
fake=subprocess.Popen(['node','/tmp/fake_destinos.js','3241','3242','/tmp/fd98','3243'],stdout=subprocess.PIPE,text=True);time.sleep(1.0)
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata98',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_WA_BASE='http://127.0.0.1:3243',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
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
def leelog(n):
    try:return json.load(open('/tmp/fd98/%s.json'%n))
    except Exception:return []
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('students/s1',{'mat':'2026001','nombre':'Ana López Ramírez','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'mail':'ana@correo.mx','tel':'7221110001'})
    put('students/s2',{'mat':'2026002','nombre':'Beto Mena Ruiz','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'mail':'','tel':''})
    put('docentes/d1',{'nombre':'Mtro. Pedro Soto','esp':'Historia','mail':'pedro@correo.mx','tel':'7222220001','asig':[]})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':'Sep–Dic 2026','cuat':1,'alumnos':['s1','s2']})
    for u,n,r,ex in [('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}}),('caja1','Caja','caja',{})]:
        ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**ex)),headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===2&&Object.keys(DOC).length===1&&Object.keys(GRP).length===1");pg.evaluate("ir('home')");pg.wait_for_timeout(600)
    ok('el_panel_tiene_la_tarjeta_de_avisos',pg.is_visible('#mAv') and 'Avisos por correo y WhatsApp' in pg.inner_text('#mAv') and pg.evaluate("!!document.querySelector('#mAv .ico svg')"))
    pg.click('#mAv');W(pg,"MOD==='av'&&AVD&&AVD.config");ok('abre_el_modulo_con_el_resumen',pg.is_visible('#vAv') and 'Avisos por correo' in pg.inner_text('#ttl') and pg.is_visible('#avEst'))
    ok('avisa_que_estan_apagados','apagados' in pg.inner_text('#avApag') and pg.is_visible('#avApag'))
    t=pg.inner_text('#avEst');ok('las_tarjetas_dicen_que_correo_y_whatsapp_estan_apagados','Apagado' in t and '0 enviados hoy' in t)
    # ---- configuración ----
    pg.click('#avTcfg');pg.wait_for_selector('#avPcfg:not([hidden])')
    pg.check('#avAct');pg.fill('#avEsc','Universidad Lafragua')
    pg.check('#avCoA');pg.fill('#avCoH','127.0.0.1');pg.fill('#avCoP','3242');pg.fill('#avCoU','escuela@correo.mx');pg.fill('#avCoC','clave-correo-1');pg.fill('#avCoD','avisos@correo.mx');pg.fill('#avCoN','Universidad Lafragua')
    pg.check('#avWaA');pg.fill('#avWaI','123456789012');pg.fill('#avWaT','token-wa-ok')
    pg.fill('#avResP','direccion@correo.mx')
    pg.click('#avGuarda');W(pg,"document.getElementById('avCfgMsg').textContent.indexOf('guardada')>-1")
    ok('guarda_y_no_muestra_las_llaves',pg.input_value('#avCoC')=='' and pg.input_value('#avWaT')=='' and pg.get_attribute('#avCoC','placeholder')=='Guardada' and pg.get_attribute('#avWaT','placeholder')=='Guardado' and pg.input_value('#avWaI')=='123456789012')
    pg.fill('#avCoPara','prueba@correo.mx');pg.click('#avCoT');W(pg,"document.getElementById('avCfgMsg').textContent.indexOf('prueba enviado')>-1");ok('correo_de_prueba',any('prueba@correo.mx' in x['para'][0] for x in leelog('correos')))
    pg.fill('#avWaPara','7221234567');pg.click('#avWaTb');W(pg,"document.getElementById('avCfgMsg').textContent.indexOf('prueba enviado')>-1");ok('whatsapp_de_prueba',leelog('wa')[-1]['body']['to']=='527221234567')
    pg.fill('#avWaI','abc');pg.click('#avGuarda');pg.wait_for_timeout(500);ok('si_algo_esta_mal_lo_dice','Phone number ID' in pg.inner_text('#avCfgMsg'));pg.fill('#avWaI','123456789012')
    pg.uncheck('#avE_planeacion_c');pg.click('#avGuarda');W(pg,"document.getElementById('avCfgMsg').textContent.indexOf('guardada')>-1")
    ok('los_eventos_se_guardan',pg.evaluate("AVD.config.eventos.planeacion.correo")==False and pg.evaluate("AVD.config.eventos.adeudo.whatsapp")==True);pg.check('#avE_planeacion_c');pg.click('#avGuarda');pg.wait_for_timeout(600)
    ok('al_activar_desaparece_el_aviso_de_apagado',pg.is_hidden('#avApag'))
    # ---- enviar un aviso ----
    pg.click('#avTenv');pg.wait_for_selector('#avPenv:not([hidden])')
    pg.select_option('#avDest','grupo');ok('al_elegir_grupo_aparece_su_selector',pg.is_visible('#avGrpL') and '4821' in pg.inner_text('#avGrp') and pg.is_hidden('#avPlanL'))
    pg.click('#avRev');ok('pide_escribir_el_mensaje','Escribe el mensaje' in pg.inner_text('#avEnvMsg'))
    pg.fill('#avAsu','Suspensión de clases');pg.fill('#avTxt','El sábado no habrá clases por mantenimiento del edificio.');ok('cuenta_los_caracteres','/ 900' in pg.inner_text('#avCont') and pg.inner_text('#avCont').startswith('5'))
    pg.click('#avRev');W(pg,"document.getElementById('avEnvMsg').textContent.indexOf('Se enviaría')>-1");t=pg.inner_text('#avEnvMsg')
    ok('la_vista_previa_cuenta_las_personas_y_los_canales','2 personas' in t and 'correo: 1' in t and 'WhatsApp: 1' in t and 'sin contacto: 1' in t and 'Ana López Ramírez' in t and pg.is_visible('#avEnvGo'))
    pg.click('#avEnvGo');W(pg,"document.getElementById('avEnvMsg').textContent.indexOf('Listo')>-1");pg.wait_for_timeout(1500)
    ok('envia_el_aviso',any(x['para'][0].endswith('ana@correo.mx>') for x in leelog('correos')) and any(x['body']['to']=='527221110001' for x in leelog('wa')) and pg.is_hidden('#avEnvGo'))
    pg.select_option('#avDest','alumno');pg.select_option('#avAl','s1');ok('un_alumno_ofrece_abrir_whatsapp_a_mano',pg.is_visible('#avWaMano'))
    pg.evaluate("window.__ab=[];window.open=function(u){window.__ab.push(u);return null};0");pg.click('#avWaMano');ab=pg.evaluate("window.__ab")
    ok('el_enlace_de_whatsapp_lleva_el_numero_y_el_texto',len(ab)==1 and ab[0].startswith('https://wa.me/527221110001?text=') and 'mantenimiento' in ab[0])
    pg.select_option('#avDest','docentes');ok('para_grupos_no_ofrece_el_enlace_a_mano',pg.is_hidden('#avWaMano'))
    # ---- mensajes ----
    pg.click('#avTmsg');W(pg,"AVMS&&AVMS.length>0");t=pg.inner_text('#avMTb')
    ok('la_bitacora_muestra_lo_enviado_y_lo_omitido','Ana López Ramírez' in t and 'enviado' in t and 'Aviso manual' in t and 'omitido' in t and 'Sin correo registrado' in t)
    pg.select_option('#avFe','omitido');pg.wait_for_timeout(700);ok('filtra_por_estado',pg.locator('#avMTb tr').count()>=1 and 'enviado' not in pg.inner_text('#avMTb').replace('omitido','')[:0]+'' and all('omitido' in x for x in pg.evaluate("Array.from(document.querySelectorAll('#avMTb tr')).map(function(r){return r.innerText})")))
    pg.select_option('#avFe','');pg.select_option('#avFc','correo');pg.wait_for_timeout(700);ok('filtra_por_canal',all('Correo' in x for x in pg.evaluate("Array.from(document.querySelectorAll('#avMTb tr')).map(function(r){return r.innerText})")))
    pg.select_option('#avFc','');pg.fill('#avFq','beto');pg.wait_for_timeout(900);ok('busca_por_nombre','Beto' in pg.inner_text('#avMTb') and 'Ana' not in pg.inner_text('#avMTb'));pg.fill('#avFq','')
    # ---- sin avisos ----
    pg.click('#avTsin');pg.fill('#avSq','ana');pg.wait_for_selector('#avSinTb [data-avs]');pg.check('#avSinTb [data-avs="s1"]');pg.wait_for_timeout(700)
    ok('marca_a_alguien_sin_avisos',pg.evaluate("AVD.config.sin.indexOf('s1')>-1")and '1 persona no recibe avisos' in pg.inner_text('#avSinS'))
    pg.fill('#avSq','');pg.wait_for_timeout(300);ok('sin_busqueda_lista_a_quienes_estan_marcados','Ana López Ramírez' in pg.inner_text('#avSinTb') and 'Beto' not in pg.inner_text('#avSinTb'))
    n=len(leelog('correos'));pg.click('#avTenv');pg.select_option('#avDest','alumno');pg.select_option('#avAl','s1');pg.fill('#avTxt','Mensaje de prueba para quien no quiere avisos');pg.click('#avRev');W(pg,"document.getElementById('avEnvMsg').textContent.indexOf('Se enviaría')>-1")
    ok('quien_no_quiere_avisos_se_cuenta_como_omitido','correo: 0' in pg.inner_text('#avEnvMsg') and 'sin avisos o canal apagado: 1' in pg.inner_text('#avEnvMsg'))
    pg.click('#avTsin');pg.fill('#avSq','ana');pg.uncheck('#avSinTb [data-avs="s1"]');pg.wait_for_timeout(600)
    # ---- permisos ----
    def entra(u):
        cx=b.new_context(viewport={'width':1200,'height':950});pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1200);return pp
    pe=entra('esc2');pe.evaluate("ir('home')");pe.wait_for_timeout(500)
    ok('control_escolar_ve_la_tarjeta_y_entra',pe.is_visible('#mAv'));pe.click('#mAv');W(pe,"MOD==='av'&&AVD&&AVD.config")
    ok('pero_no_ve_la_configuracion',pe.is_hidden('#avTcfg') and pe.is_visible('#avTenv') and pe.is_visible('#avTmsg') and pe.is_visible('#avTsin'))
    pk=entra('caja1');ok('caja_no_ve_la_tarjeta',pk.is_hidden('#mAv'));pk.evaluate("ir('av')");ok('ni_entra_al_modulo',pk.evaluate("MOD")=='home' and pk.is_hidden('#vAv'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.evaluate("ir('av')");pg.click('#avTcfg');pg.wait_for_timeout(500);pg.screenshot(path='/tmp/av_config.png',full_page=True)
    pg.click('#avTenv');pg.select_option('#avDest','grupo');pg.fill('#avAsu','Suspensión de clases');pg.fill('#avTxt','El sábado no habrá clases por mantenimiento del edificio.');pg.click('#avRev');pg.wait_for_timeout(800);pg.screenshot(path='/tmp/av_enviar.png')
    b.close()
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
