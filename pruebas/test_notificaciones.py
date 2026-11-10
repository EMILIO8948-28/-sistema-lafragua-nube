import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3131;B='http://127.0.0.1:%d'%PORT;TOK='tok-nt-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata53 && mkdir -p /tmp/nbdata53')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata53',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
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
def fijaNots(pg):
    for _ in range(4):
        pg.evaluate("window.borradosLista=async function(){return {pendientes:[{id:'b1'}],historial:[]}};0");pg.evaluate("NOTS={pendientes:[{id:'b1'}]};ntRender();0");time.sleep(0.5)
hoy=datetime.date.today();iso=lambda d:d.isoformat()
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    PER=pg.evaluate("perAct()")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    for i in (1,2):put('students/s%d'%i,{'mat':'2026000%d'%i,'nombre':['','Ana López','Beto Mena'][i],'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':2,'alumnos':['s1','s2']})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[]});put('docentes/d2',{'nombre':'Prof. Dos','esp':'Historia','asig':[]})
    mat=lambda nom,d,ev:{'per':PER,'plan':'Pedagogía','cuat':2,'nom':nom,'docId':d,'ini':'08:00','fin':'10:00','ev':ev}
    put('materias/m1',mat('Didáctica general','d1',iso(hoy-datetime.timedelta(days=2))))
    put('materias/m2',mat('Historia de la educación','d2',iso(hoy+datetime.timedelta(days=5))))
    put('materias/m3',mat('Filosofía antigua','d1',iso(hoy-datetime.timedelta(days=60))))
    put('materias/m4',mat('Evaluación del aprendizaje','d1',''));put('materias/m5',mat('Psicología educativa','d1',''))
    put('calif/s1',{'items':[{'id':'i1','mid':'m1','mat':'Didáctica general','plan':'Pedagogía','per':PER,'cuat':2,'cal':9}]})
    put('planeaciones/m1',{'files':[{'id':'f1','name':'plan.pdf','size':10}],'estado':'pendiente'})
    put('planeaciones/m4',{'files':[{'id':'f2','name':'p2.pdf','size':10}],'estado':'denegada','motivo':'Falta el cronograma','revisor':'Control escolar','revFecha':iso(hoy)})
    put('planeaciones/m5',{'files':[{'id':'f3','name':'p3.pdf','size':10}],'estado':'aprobada','motivo':'','revisor':'Control escolar','revFecha':iso(hoy)})
    ahora=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    put('solicitudes/so1',{'id':'so1','tipo':'justificante','sid':'s1','nombre':'Ana López','desde':iso(hoy),'hasta':iso(hoy),'motivo':'Cita médica','estado':'pendiente','creada':ahora})
    put('solicitudes/so2',{'id':'so2','tipo':'justificante','sid':'s1','nombre':'Ana López','desde':iso(hoy),'hasta':iso(hoy),'motivo':'Enfermedad','estado':'aprobada','justId':'j1','resp':{'por':'Control escolar','fecha':iso(hoy)},'leida':False,'creada':ahora})
    put('justificantes/j1',{'id':'j1','num':'J-000001','sid':'s1','nombre':'Ana López','mat':'20260001','desde':iso(hoy),'hasta':iso(hoy),'estado':'Aprobado'})
    put('solicitudes/so3',{'id':'so3','tipo':'constancia','tipoC':'simple','sid':'s1','nombre':'Ana López','estado':'denegada','resp':{'por':'Control escolar','fecha':iso(hoy),'motivo':'Tienes adeudo de colegiaturas'},'leida':False,'creada':ahora})
    put('solicitudes/so4',{'id':'so4','tipo':'boleta','periodo':PER,'sid':'s1','nombre':'Ana López','estado':'atendida','resp':{'por':'Control escolar','fecha':iso(hoy)},'leida':False,'creada':ahora})
    put('avisos/s1-1-1',{'sid':'s1','tipo':'adeudo','n':1,'ciclo':1,'fecha':iso(hoy),'creada':ahora,'titulo':'Aviso de adeudo','mensaje':'Hola, Ana. De acuerdo con nuestros registros tienes adeudo de 2 colegiaturas.','meses':[],'total':2600,'leida':False})
    put('ledger/s1',{'pagos':[{'id':'p1','fecha':iso(hoy),'monto':1300,'metodo':'Transferencia','estado':'pendiente','folio':'R-000001','ref':'ABC'}]})
    put('acuerdos/ac1',{'id':'ac1','sid':'s1','num':'AC-1','cuotas':[{'fecha':iso(hoy-datetime.timedelta(days=5)),'monto':1300,'pagada':False}]})
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}});usr('caja1','Caja','caja');usr('doc1','Profesor Uno','docente',{'doc':'d1'});usr('con1','Consulta','consulta')
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'als1','name':'Ana','alumno':'s1','clave':'abcd-efgh'}]}),headers=HDR)
    # ================== administrador ==================
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(MAT).length===5&&Object.keys(SOL).length===4&&Object.keys(PLN).length===3");fijaNots(pg);pg.wait_for_timeout(500)
    caja=lambda:pg.evaluate("(function(){var a=document.getElementById('bNotif').getBoundingClientRect(),k=document.getElementById('bBk').getBoundingClientRect(),m=document.querySelector('main').getBoundingClientRect();return {x:a.left,r:a.right,t:a.top,vis:a.width>0,kx:k.left,kr:k.right,mr:m.right}})()")
    r=caja();ok('la_campana_esta_arriba_a_la_derecha_junto_al_respaldo',r['vis'] and r['t']<110 and r['x']>600 and r['r']<=r['kx'] and abs(r['kr']-r['mr'])<30)
    ok('el_icono_es_una_campana_con_insignia',pg.evaluate("!!document.querySelector('#bNotif svg path[d*=\"M6 9.5\"]')") and pg.is_visible('#ntN'))
    ok('el_numero_suma_lo_que_hay_por_atender',pg.inner_text('#ntN')=='8')
    pg.click('#bNotif');pg.wait_for_selector('#pNot:not([hidden])');t=pg.inner_text('#pNot')
    ok('el_panel_lista_cada_pendiente','1 solicitud de alumno por atender' in t and '1 planeación de docente por revisar' in t and '1 asignatura con calificaciones sin subir' in t and '1 solicitud de eliminación por aprobar' in t and '1 transferencia por confirmar' in t and '1 pago por verificar' in t and '1 acuerdo de pago vencido' in t)
    ok('indica_que_calificaciones_faltan_y_de_quien','Didáctica general (Prof. Uno' in t and 'Historia de la educación' not in t and 'Filosofía antigua' not in t)
    ok('el_aviso_de_calificaciones_ignora_evaluaciones_futuras_y_muy_antiguas','Historia de la educación' not in t and 'Filosofía antigua' not in t)
    for txt,js in [('solicitud de alumno',"MOD==='esc'&&ETAB==='S'"),('planeación de docente',"MOD==='esc'&&ETAB==='D'"),('calificaciones sin subir',"MOD==='esc'&&ETAB==='K'"),('solicitud de eliminación',"MOD==='not'"),('transferencia por confirmar',"MOD==='pagos'"),('pago por verificar',"MOD==='ver'"),('acuerdo de pago vencido',"MOD==='acu'")]:
        pg.keyboard.press('Escape');pg.evaluate("ir('home')");fijaNots(pg);pg.click('#bNotif');pg.wait_for_selector('#pNot:not([hidden])');pg.locator('#pNot .nt-i:has-text("%s")'%txt).first.click();W(pg,js);ok('lleva_a_'+txt.replace(' ','_'),True and pg.is_hidden('#pNot'))
    pg.evaluate("ir('home')");pg.click('#bNotif');pg.wait_for_selector('#pNot:not([hidden])');pg.keyboard.press('Escape');ok('con_escape_se_cierra',pg.is_hidden('#pNot'))
    pg.click('#bNotif');pg.wait_for_selector('#pNot:not([hidden])');pg.mouse.click(300,500);ok('al_pulsar_fuera_se_cierra',pg.is_hidden('#pNot'))
    # resolver algo baja el contador
    fijaNots(pg)
    put('solicitudes/so1',{'id':'so1','tipo':'justificante','sid':'s1','nombre':'Ana López','desde':iso(hoy),'hasta':iso(hoy),'motivo':'Cita médica','estado':'aprobada','resp':{'por':'Control escolar','fecha':iso(hoy)},'leida':False,'creada':ahora})
    W(pg,"solPend().length===0");fijaNots(pg);ok('al_resolver_una_solicitud_baja_el_numero',pg.inner_text('#ntN')=='7')
    put('solicitudes/so1',{'id':'so1','tipo':'justificante','sid':'s1','nombre':'Ana López','desde':iso(hoy),'hasta':iso(hoy),'motivo':'Cita médica','estado':'pendiente','creada':ahora});W(pg,"solPend().length===1")
    put('calif/s2',{'items':[{'id':'i2','mid':'m1','mat':'Didáctica general','plan':'Pedagogía','per':PER,'cuat':2,'cal':8}]});W(pg,"califPend().length===0");fijaNots(pg);ok('al_subir_las_calificaciones_se_quita_el_aviso',pg.inner_text('#ntN')=='7')
    put('calif/s2',{'items':[]});W(pg,"califPend().length===1")
    pg.screenshot(path='/tmp/nt_1_admin.png');pg.click('#bNotif');pg.wait_for_selector('#pNot:not([hidden])');pg.screenshot(path='/tmp/nt_2_panel_admin.png',clip={'x':500,'y':0,'width':600,'height':720})
    # ================== otros roles ==================
    def entra(u,c,cond):
        cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP',c);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&"+cond);pp.wait_for_timeout(900);return pp
    pe=entra('esc2','clave-esc2-123',"Object.keys(SOL).length===4&&Object.keys(MAT).length===5")
    ok('control_escolar_ve_lo_suyo',pe.inner_text('#ntN')=='4');pe.click('#bNotif');pe.wait_for_selector('#pNot:not([hidden])');te=pe.inner_text('#pNot');ok('y_no_ve_pagos_ni_eliminaciones','solicitud de alumno' in te and 'planeación de docente' in te and 'calificaciones sin subir' in te and 'transferencia' not in te and 'eliminación' not in te and 'acuerdo' not in te)
    pc=entra('caja1','clave-caja1-123',"S.length===2");pc.wait_for_timeout(500)
    ok('caja_ve_pagos_verificacion_y_acuerdos',pc.inner_text('#ntN')=='3');pc.click('#bNotif');pc.wait_for_selector('#pNot:not([hidden])');tc=pc.inner_text('#pNot');ok('y_no_ve_lo_de_control_escolar','transferencia por confirmar' in tc and 'pago por verificar' in tc and 'acuerdo de pago vencido' in tc and 'solicitud de alumno' not in tc and 'planeación' not in tc)
    pk=entra('con1','clave-con1-123',"S.length===2");ok('quien_solo_consulta_no_tiene_pendientes',pk.is_hidden('#ntN') and pk.is_visible('#bNotif'));pk.click('#bNotif');pk.wait_for_selector('#pNot:not([hidden])');ok('y_el_panel_dice_todo_al_dia','Todo al día' in pk.inner_text('#pNot'))
    # ---- docente ----
    pd=entra('doc1','clave-doc1-123',"Object.keys(MAT).length>=1&&Object.keys(PLN).length>=1");pd.wait_for_timeout(500)
    ok('el_docente_ve_su_campana_con_3_cosas',pd.is_visible('#bNotif') and pd.inner_text('#ntN')=='3' and pd.is_hidden('#bBk'))
    pd.click('#bNotif');pd.wait_for_selector('#pNot:not([hidden])');td=pd.inner_text('#pNot');pd.screenshot(path='/tmp/nt_3_docente.png',clip={'x':600,'y':0,'width':500,'height':640})
    ok('le_pide_las_calificaciones_el_dia_de_la_evaluacion','Sube las calificaciones de tu evaluación' in td and 'Didáctica general' in td and 'faltan 1 de 2' in td and 'Historia de la educación' not in td)
    ok('le_avisa_si_se_aprobo_o_nego_su_planeacion','Planeación denegada' in td and 'Evaluación del aprendizaje' in td and 'Motivo: Falta el cronograma' in td and 'Planeación aprobada' in td and 'Psicología educativa' in td)
    pd.locator('#pNot .nt-i:has-text("Planeación aprobada")').click();W(pd,"MOD==='doc'");pd.wait_for_timeout(500)
    ok('al_pulsar_una_notificacion_la_marca_leida_y_lo_lleva_a_sus_asignaturas',pd.inner_text('#ntN')=='2')
    pd.click('#bNotif');pd.wait_for_selector('#pNot:not([hidden])');pd.click('#ntLeidas');pd.wait_for_timeout(500);ok('marcar_como_leidas_deja_solo_lo_pendiente',pd.inner_text('#ntN')=='1' and pd.is_hidden('#ntLeidas'))
    pd.reload();W(pd,"typeof APP!=='undefined'&&APP!==null&&Object.keys(PLN).length>=1&&Object.keys(MAT).length>=1");pd.wait_for_timeout(900);ok('lo_leido_se_recuerda_al_volver_a_entrar',pd.inner_text('#ntN')=='1')
    # ---- alumno ----
    pa_=b.new_context(viewport={'width':1100,'height':900});pa_.request.post(B+'/api/login',data=json.dumps({'u':'als1','clave':'abcd-efgh'}),headers=HDR);pa_.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-ana-77'}),headers=HDR)
    pa=entra('als1','clave-ana-77',"Object.keys(SOL).length===4&&Object.keys(AVI).length===1&&S.length===1");pa.wait_for_timeout(500)
    ok('el_alumno_tiene_campana_y_no_respaldo',pa.is_visible('#bNotif') and pa.is_hidden('#bBk') and pa.inner_text('#ntN')=='4')
    pa.click('#bNotif');pa.wait_for_selector('#pNot:not([hidden])');ta=pa.inner_text('#pNot');pa.screenshot(path='/tmp/nt_4_alumno.png',clip={'x':600,'y':0,'width':500,'height':700})
    ok('le_avisa_de_justificante_aprobado','Justificante de faltas aprobado' in ta and 'J-000001' in ta and 'Ya puedes descargarlo' in ta)
    ok('y_de_una_solicitud_denegada_con_su_motivo','Constancia de estudios denegada' in ta and 'Motivo: Tienes adeudo de colegiaturas' in ta)
    ok('y_de_documentos_listos_y_avisos_de_adeudo','Boleta de estudios atendida' in ta and 'Acude a Control escolar' in ta and 'Aviso de adeudo' in ta)
    ok('las_solicitudes_en_revision_no_cuentan','Justificante de faltas: en revisión' in ta and pa.inner_text('#ntN')=='4')
    pa.locator('#pNot .nt-i:has-text("Constancia de estudios denegada")').click();W(pa,"MOD==='por'");pa.wait_for_timeout(700)
    ok('al_abrir_una_se_marca_leida_en_el_servidor_y_baja_el_numero',ctx.request.get(B+'/api/doc/solicitudes/so3').json()['data']['leida'] is True and pa.inner_text('#ntN')=='3')
    pa.click('#bNotif');pa.wait_for_selector('#pNot:not([hidden])');pa.click('#ntLeidas');pa.wait_for_timeout(900)
    ok('marcar_como_leidas_las_deja_todas',pa.is_hidden('#ntN') and ctx.request.get(B+'/api/doc/avisos/s1-1-1').json()['data']['leida'] is True and ctx.request.get(B+'/api/doc/solicitudes/so2').json()['data']['leida'] is True)
    # ---- celular ----
    pa.keyboard.press('Escape');pa.set_viewport_size({'width':390,'height':800});pa.evaluate("ir('por')");pa.click('#bNotif');pa.wait_for_selector('#pNot:not([hidden])');bb=pa.evaluate("(function(){var r=document.getElementById('pNot').getBoundingClientRect();return {l:r.left,r:r.right,w:window.innerWidth}})()")
    ok('en_celular_el_panel_cabe_en_la_pantalla',bb['l']>=0 and bb['r']<=bb['w']+1)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
