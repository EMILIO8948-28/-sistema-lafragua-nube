"""Calendario de eventos: fechas automáticas (evaluaciones y plazos de captura de calificaciones que programa Control escolar, y días de pago de colegiatura)."""
import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3129;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,LF_SIN_CONTACTO='1',PORT=str(PORT),DATA_DIR='/tmp/nbdata_cala',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_cala && mkdir -p /tmp/nbdata_cala')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def W(pg,js,t=20):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
PER='Sep–Dic 2026'
NOV="calDerivados('2026-11-01','2026-11-30')"
def cuenta(pg,expr=NOV):
    return pg.evaluate("(function(){var o=%s,c={evalu:0,capt:0,pago:0};o.forEach(function(e){c[e.cat]++});c.txt=o.map(function(e){return e.titulo+'|'+e.desc}).join('\\n');return c})()"%expr)
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&typeof DBH!=='undefined'&&DBH!==null")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('students/s1',{'mat':'1001','nombre':'Ana López','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    put('students/s2',{'mat':'1002','nombre':'Beto Mena','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2025,'nuevo':False})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[]});put('docentes/d2',{'nombre':'Prof. Dos','esp':'Historia','asig':[]})
    put('grupos/g1',{'num':'1111','plan':'Derecho','per':PER,'cuat':2,'alumnos':['s1']});put('grupos/g2',{'num':'2222','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s2']})
    mat=lambda nom,plan,cuat,d,ev=None,**k:dict({'per':PER,'plan':plan,'cuat':cuat,'nom':nom,'docId':d,'ini':'09:00','fin':'11:00'},**({'ev':ev} if ev else {}),**k)
    put('materias/m1',mat('Civil I','Derecho',2,'d1','2026-11-20',aula='A1'));put('materias/m2',mat('Civil II','Derecho',2,'d1','2026-11-20'))
    put('materias/m3',mat('Historia','Derecho',2,'d2','2026-11-27',prorroga='2026-12-05'));put('materias/m4',mat('Didáctica','Pedagogía',1,'d2','2026-11-21'))
    put('materias/m5',mat('Sin fecha','Derecho',2,'d1'))
    def usr(u,name,rol,modulos=None,doc=None):
        d={'u':u,'name':name,'rol':rol,'clave':'clave-%s-123'%u}
        if modulos is not None:d['modulos']=modulos
        if doc:d['doc']=doc
        r=ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR);assert r.status==200,(u,r.status,r.text())
    usr('caja1','Rosa Caja','caja');usr('prof1','Dora Docente','docente',doc='d1');usr('edi1','Edgar Editor','personalizado',{'calendario':'editar'});usr('nom1','Nina Nómina','personalizado',{'nomina_adm':'editar'})
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'1001','name':'Ana López','alumno':'s1','clave':'abcd-efgh'}]}),headers=HDR)
    def sesion(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status,r.text());return cx
    S_={u:sesion(u,'clave-%s-123'%u) for u in ['caja1','prof1','edi1','nom1']}
    al=sesion('1001','abcd-efgh');al.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-ana-77'}),headers=HDR);al=sesion('1001','clave-ana-77')
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(MAT).length===5&&Object.keys(DOC).length===2")
    # ================= ADMINISTRACIÓN: ve todo lo programado =================
    c=cuenta(pg)
    ok('evaluaciones_agrupadas_por_fecha',c['evalu']==3 and 'Evaluaciones (2 asignaturas)' in c['txt'] and 'Evaluación: Historia' in c['txt'] and 'Evaluación: Didáctica' in c['txt'])
    ok('plazos_de_captura_con_su_ventana',c['capt']==3 and 'Plazo para capturar calificaciones (2 asignaturas)' in c['txt'])
    ok('materia_sin_fecha_no_aparece','Sin fecha' not in c['txt'])
    ok('detalle_trae_plan_docente_y_aula','Civil I · Derecho, cuatrimestre 2 · Prof. Uno · A1' in c['txt'])
    ev=pg.evaluate("calDerivados('2026-11-01','2026-11-30').filter(function(e){return e.cat==='capt'}).map(function(e){return [e.fecha,e.fin]}).sort().map(function(x){return x.join('>')}).join(',')")
    ok('ventana_es_evaluacion_mas_3_dias_y_prorroga',ev=='2026-11-20>2026-11-23,2026-11-21>2026-11-24,2026-11-27>2026-12-05')
    ok('prorroga_se_indica','con prórroga' in c['txt'])
    ok('un_mes_sin_programacion_no_trae_evaluaciones',cuenta(pg,"calDerivados('2027-03-01','2027-03-31')")['evalu']==0 and cuenta(pg,"calDerivados('2027-03-01','2027-03-31')")['capt']==0)
    # pantalla
    pg.evaluate("ir('home')");W(pg,"MOD==='home'");pg.click('#mCal');pg.wait_for_selector('#dCal[open]')
    pg.evaluate("CALM={y:2026,m:11};CALSEL='';calRender()")
    ok('leyenda_con_los_tipos_automaticos','Pago de colegiatura' in pg.inner_text('#calLeg') and 'Evaluación programada' in pg.inner_text('#calLeg') and 'Plazo para capturar' in pg.inner_text('#calLeg'))
    ok('chip_de_evaluacion_el_dia_20',pg.locator('#calGrid [data-f="2026-11-20"] .cal-ch:has-text("Evaluaciones")').count()==1)
    ok('el_plazo_cubre_los_dias_de_la_ventana',all(pg.locator('#calGrid [data-f="2026-11-%02d"] .cal-ch:has-text("Plazo")'%d).count()>=1 for d in (20,21,22,23,24)) and pg.locator('#calGrid [data-f="2026-11-25"] .cal-ch:has-text("Plazo")').count()==0)
    pg.click('#calGrid [data-f="2026-11-20"]');tx=pg.inner_text('#calList')
    ok('dia_20_lista_evaluaciones_plazo_y_pago','Evaluaciones (2 asignaturas)' in tx and 'Civil I' in tx and 'Civil II' in tx and 'Plazo para capturar calificaciones (2 asignaturas)' in tx and 'Pago de colegiatura' in tx and 'Historia' not in tx)
    ok('lo_automatico_no_se_edita',pg.locator('#calList [data-ce]').count()==0 and 'Sale solo de la programación de Control escolar' in tx)
    pg.click('#calGrid [data-f="2026-11-30"]');tx=pg.inner_text('#calList')
    ok('prorroga_visible_hasta_diciembre','27/11/2026 al 05/12/2026' in tx and 'con prórroga' in tx and 'Pago de colegiatura' in tx)
    pg.click('#calAll');pg.select_option('#calCat','evalu');ok('filtro_solo_evaluaciones',pg.locator('#calGrid .cal-ch').count()==3 and 'Plazo' not in pg.inner_text('#calList') and 'Pago de' not in pg.inner_text('#calList'))
    pg.select_option('#calCat','pago');ok('filtro_solo_pagos',pg.locator('#calGrid .cal-ch').count()==0 and pg.locator('#calGrid .cal-d.pago').count()==16 and pg.locator('#calGrid [data-f="2026-11-15"].pago').count()==1 and pg.locator('#calGrid [data-f="2026-11-30"].pago').count()==1)
    pg.select_option('#calCat','')
    # días de pago: 15 al 30 de cada mes
    ok('pago_del_15_al_30',pg.evaluate("(function(){var e=calDerivados('2026-11-01','2026-11-30').filter(function(x){return x.cat==='pago'})[0];return e.fecha==='2026-11-15'&&e.fin==='2026-11-30'})()"))
    ok('pago_en_cada_mes_del_rango',pg.evaluate("calDerivados('2026-11-01','2027-02-28').filter(function(x){return x.cat==='pago'}).map(function(x){return x.fecha+'>'+x.fin}).join(',')")=='2026-11-15>2026-11-30,2026-12-15>2026-12-30,2027-01-15>2027-01-30,2027-02-15>2027-02-28')
    ok('pago_no_marca_el_14_ni_el_31',pg.locator('#calGrid [data-f="2026-11-14"].pago').count()==0 and pg.locator('#calGrid [data-f="2026-11-15"].pago').count()==1)
    pg.evaluate("CALM={y:2026,m:12};CALSEL='';calRender()");ok('pago_en_diciembre_y_31_sin_pago',pg.locator('#calGrid [data-f="2026-12-15"].pago').count()==1 and pg.locator('#calGrid [data-f="2026-12-30"].pago').count()==1 and pg.locator('#calGrid [data-f="2026-12-31"].pago').count()==0)
    pg.evaluate("CALM={y:2026,m:11};CALSEL='';calRender()")
    # ajustes
    pg.click('#calAj summary');ok('admin_ve_los_ajustes',pg.is_visible('#calAjI') and pg.input_value('#calAjI')=='15' and pg.input_value('#calAjF')=='30' and pg.is_checked('#calAjOn'))
    pg.fill('#calAjI','25');pg.fill('#calAjF','10');pg.click('#calAjOk');ok('rechaza_dia_inicial_mayor','posterior' in pg.inner_text('#calMsg') and ctx.request.get(B+'/api/doc/agenda/_ajustes').json()['exists'] is False)
    pg.fill('#calAjI','10');pg.fill('#calAjF','25');pg.click('#calAjOk');W(pg,"AGN._ajustes&&AGN._ajustes.pagoIni===10")
    aj=ctx.request.get(B+'/api/doc/agenda/_ajustes').json()['data']
    ok('guarda_ajustes',aj=={'pagoOn':True,'pagoIni':10,'pagoFin':25} and pg.locator('#calGrid [data-f="2026-11-10"].pago').count()==1 and pg.locator('#calGrid [data-f="2026-11-26"].pago').count()==0)
    ok('los_ajustes_no_cuentan_como_evento',pg.evaluate("calLista().length")==0)
    pg.uncheck('#calAjOn');pg.click('#calAjOk');W(pg,"AGN._ajustes.pagoOn===false")
    ok('apagar_los_dias_de_pago',cuenta(pg)['pago']==0 and pg.locator('#calGrid .cal-d.pago').count()==0)
    pg.check('#calAjOn');pg.fill('#calAjI','15');pg.fill('#calAjF','30');pg.click('#calAjOk');W(pg,"AGN._ajustes.pagoOn===true&&AGN._ajustes.pagoIni===15")
    ok('restablecer_15_al_30',cuenta(pg)['pago']==1)
    # un evento manual convive con lo automático
    pg.click('#calNew');pg.fill('#calFT','Junta con padres');pg.fill('#calFF','2026-11-20');pg.click('#calFOk');W(pg,"calLista().length===1")
    pg.click('#calGrid [data-f="2026-11-20"]');ok('manual_y_automatico_juntos',pg.locator('#calList [data-ce]').count()==1 and 'Junta con padres' in pg.inner_text('#calList') and 'Evaluaciones' in pg.inner_text('#calList'))
    pg.screenshot(path='/tmp/cal_auto.png')
    pg.click('#calCls')
    # ================= PERMISOS EN EL SERVIDOR PARA LOS AJUSTES =================
    ok('todos_leen_los_ajustes',all(c_.request.get(B+'/api/doc/agenda/_ajustes').json()['exists'] is True for c_ in [S_['caja1'],S_['prof1'],S_['nom1'],S_['edi1'],al]))
    nuevo={'pagoOn':True,'pagoIni':1,'pagoFin':20}
    ok('solo_consulta_no_cambia_ajustes',all(c_.request.put(B+'/api/doc/agenda/_ajustes',data=json.dumps(nuevo),headers=HDR).status==403 for c_ in [S_['caja1'],S_['prof1'],S_['nom1'],al]))
    ok('editor_si_cambia_ajustes',S_['edi1'].request.put(B+'/api/doc/agenda/_ajustes',data=json.dumps(nuevo),headers=HDR).status==200)
    for nom,cu in [('dia_fuera_de_rango',{'pagoOn':True,'pagoIni':40,'pagoFin':50}),('inicio_mayor',{'pagoOn':True,'pagoIni':20,'pagoFin':5}),('sin_encendido',{'pagoIni':1,'pagoFin':5}),('dia_no_entero',{'pagoOn':True,'pagoIni':'a','pagoFin':5}),('decimal',{'pagoOn':True,'pagoIni':1.5,'pagoFin':5})]:
        ok('ajustes_rechaza_'+nom,ctx.request.put(B+'/api/doc/agenda/_ajustes',data=json.dumps(cu),headers=HDR).status==400)
    ok('ajustes_siguen_validos',ctx.request.get(B+'/api/doc/agenda/_ajustes').json()['data']['pagoFin']==20)
    ctx.request.put(B+'/api/doc/agenda/_ajustes',data=json.dumps({'pagoOn':True,'pagoIni':15,'pagoFin':30}),headers=HDR)
    # ================= LO QUE VE CADA ROL =================
    def entra(u,c,cond):
        cx=b.new_context();cx.set_default_timeout(12000);p2=pagina(cx);p2.goto(B+'/');W(p2,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        p2.fill('#lgU',u);p2.fill('#lgP',c);p2.click('#lgGo');W(p2,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'&&"+cond+"&&AGN._ajustes&&AGN._ajustes.pagoIni===15",20);p2.wait_for_timeout(400);return p2
    pa=entra('1001','clave-ana-77',"APP.rol==='alumno'&&Object.keys(MAT).length>=3&&S.length===1")
    ca=cuenta(pa)
    ok('alumno_ve_evaluaciones_solo_de_su_grupo',ca['evalu']==2 and 'Civil I' in ca['txt'] and 'Historia' in ca['txt'] and 'Didáctica' not in ca['txt'])
    ok('alumno_no_ve_plazos_de_captura',ca['capt']==0 and 'Plazo' not in ca['txt'])
    ok('alumno_ve_dias_de_pago',ca['pago']==1)
    ok('alumno_ve_pago_y_evaluaciones_en_su_portal',pa.evaluate("calProx(8,true).some(function(e){return e.cat==='pago'})") and 'Calendario de eventos' in pa.inner_text('#poBody'))
    pa.click('#poBody [data-ncal]');pa.wait_for_selector('#dCal[open]');pa.evaluate("CALM={y:2026,m:11};CALSEL='2026-11-20';calRender()")
    ok('alumno_en_pantalla_no_ve_plazos_ni_ajustes','Plazo' not in pa.inner_text('#calList') and 'Evaluaciones (2 asignaturas)' in pa.inner_text('#calList') and not pa.is_visible('#calAj'))
    pa.context.close()
    pd=entra('prof1','clave-prof1-123',"Object.keys(MAT).length>=4");pd.evaluate("ir('home')");W(pd,"MOD==='home'")
    cd=cuenta(pd)
    ok('docente_ve_solo_sus_asignaturas',cd['evalu']==1 and cd['capt']==1 and 'Civil I' in cd['txt'] and 'Civil II' in cd['txt'] and 'Historia' not in cd['txt'] and 'Didáctica' not in cd['txt'])
    ok('docente_ve_el_plazo_de_captura',cd['capt']==1 and pd.evaluate("calDerivados('2026-11-01','2026-11-30').filter(function(e){return e.cat==='capt'})[0].fin")=='2026-11-23')
    ok('docente_ve_dias_de_pago',cd['pago']==1)
    pd.click('#mCal');pd.wait_for_selector('#dCal[open]');pd.evaluate("CALM={y:2026,m:11};CALSEL='2026-11-27';calRender()")
    ok('docente_en_pantalla_no_ve_la_materia_ajena','Historia' not in pd.inner_text('#calList') and not pd.is_visible('#calAj') and not pd.is_visible('#calNew'))
    pd.context.close()
    pc=entra('caja1','clave-caja1-123',"Object.keys(MAT).length===5")
    cc=cuenta(pc);ok('caja_ve_toda_la_programacion',cc['evalu']==3 and cc['capt']==3 and cc['pago']==1)
    pc.context.close()
    pn=entra('nom1','clave-nom1-123',"true");cn=cuenta(pn)
    ok('personal_sin_acceso_a_materias_solo_ve_pagos',cn['evalu']==0 and cn['capt']==0 and cn['pago']==1)
    pn.context.close()
    # cambio de programación en vivo
    put('materias/m4',mat('Didáctica','Pedagogía',1,'d2','2026-11-12'))
    W(pg,"calDerivados('2026-11-01','2026-11-30').filter(function(e){return e.cat==='evalu'&&e.fecha==='2026-11-12'}).length===1")
    ok('cambiar_la_fecha_en_control_escolar_mueve_el_evento_en_vivo',cuenta(pg)['evalu']==3 and pg.evaluate("calDerivados('2026-11-01','2026-11-30').filter(function(e){return e.cat==='evalu'&&e.fecha==='2026-11-21'}).length")==0)
    ok('sin_errores_de_pagina',not errs)
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(json.dumps(R,ensure_ascii=False,indent=0));print('FALLAS:',bad,errs[:3]);print('%d/%d'%(len(R)-len(bad),len(R)))
