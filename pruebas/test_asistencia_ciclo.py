import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3250;B='http://127.0.0.1:%d'%PORT;TOK='tok-as-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata99 && mkdir -p /tmp/nbdata99')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata99',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
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
PER='Sep–Dic 2026';SIG='Ene–Abr 2027'
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    sab1=pg.evaluate("sabReciente()");d1=datetime.date.fromisoformat(sab1);sab0=(d1-datetime.timedelta(days=7)).isoformat()
    SLUG=pg.evaluate("slug('Pedagogía')")
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    put('catalogo/'+SLUG,{'items':[{'id':'k1','nom':'Didáctica general','cuat':1},{'id':'k2','nom':'Historia de la educación','cuat':1},{'id':'k3','nom':'Tesis','cuat':3}]})
    nom={'s1':'Ana López','s2':'Beto Mena','s3':'Carla Díaz','s4':'Diego Vega','s5':'Elena Ríos'}
    for i,(sid,n) in enumerate(nom.items(),1):put('students/'+sid,{'mat':'2026%03d'%i,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('docentes/d1',{'nombre':'Mtro. Pedro Soto','esp':'Historia','asig':[]});put('docentes/d2',{'nombre':'Mtra. Rosa Luna','esp':'Tesis','asig':[]})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2','s3','s4']});put('grupos/g3',{'num':'4833','plan':'Pedagogía','per':PER,'cuat':3,'alumnos':['s5']})
    put('grupos/gv',{'num':'4700','plan':'Pedagogía','per':'May–Ago 2026','cuat':1,'alumnos':[]})
    put('materias/m1',{'per':PER,'plan':'Pedagogía','cuat':1,'nom':'Didáctica general','docId':'d1','ini':'08:00','fin':'10:00','ev':sab1});put('materias/m2',{'per':PER,'plan':'Pedagogía','cuat':1,'nom':'Historia de la educación','docId':'d1','ini':'10:00','fin':'12:00','ev':sab1});put('materias/m3',{'per':PER,'plan':'Pedagogía','cuat':3,'nom':'Tesis','docId':'d2','ini':'08:00','fin':'10:00','ev':sab1})
    put('criterios/m1',{'items':[{'id':'cr1','nom':'Examen','peso':100}]})
    it=lambda i,mid,nm,cu,cal,pts=None:dict({'id':i,'mid':mid,'mat':nm,'plan':'Pedagogía','per':PER,'cuat':cu,'cal':cal,'fecha':sab1},**({'pts':pts} if pts else {}))
    put('calif/s1',{'items':[it('a1','m1','Didáctica general',1,9,{'cr1':9}),it('a2','m2','Historia de la educación',1,9)]})
    put('calif/s2',{'items':[it('b1','m1','Didáctica general',1,8,{'cr1':8}),it('b2','m2','Historia de la educación',1,6)]})
    put('calif/s3',{'items':[it('c1','m1','Didáctica general',1,10,{'cr1':10})]})
    put('calif/s4',{'items':[it('d1','m1','Didáctica general',1,7,{'cr1':7}),it('d2','m2','Historia de la educación',1,9)]})
    put('calif/s5',{'items':[it('e1','m3','Tesis',3,9)]})
    put('justificantes/j1',{'id':'j1','num':'J-000001','sid':'s2','nombre':'Beto Mena','mat':'2026002','desde':sab0,'hasta':sab0,'estado':'Aprobado','motivo':'Salud'})
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('doc1','Mtro. Pedro Soto','docente',{'doc':'d1'});usr('doc2','Mtra. Rosa Luna','docente',{'doc':'d2'});usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}});usr('caja1','Caja','caja')
    def entra(u):
        cx=b.new_context(viewport={'width':1200,'height':1000});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1500);return pp,cx
    api=lambda cx,m,url,body=None:cx.request.fetch(B+url,method=m,data=json.dumps(body) if body is not None else None,headers=HDR)
    # ============ el docente captura asistencia ============
    pd,cxd=entra('doc1');W(pd,"Object.keys(MAT).length>=3&&Object.keys(CAL).length>=5&&Object.keys(JUS).length>=1")
    pd.evaluate("ir('doc')") if False else None
    W(pd,"ROL==='docente'");pd.wait_for_selector('#dmL [data-as]')
    ok('el_docente_ve_el_boton_asistencia_en_sus_asignaturas',pd.locator('#dmL [data-as]').count()>=2)
    pd.locator('#dmL tr:has-text("Didáctica general") [data-as]').first.click();pd.wait_for_selector('#dAs[open]')
    ok('abre_con_los_alumnos_de_la_asignatura_y_la_fecha_del_ultimo_sabado','Didáctica general' in pd.inner_text('#asT') and pd.locator('#asTb tr').count()==4 and pd.input_value('#asFec')==sab1 and 'Aún no hay sesiones' in pd.inner_text('#asChips'))
    pd.click('#asOk');ok('exige_marcar_a_todos','Falta marcar a 4 alumnos' in pd.inner_text('#asMsg'))
    pd.evaluate("document.getElementById('asFec').value='2099-01-01';document.getElementById('asFec').dispatchEvent(new Event('change'))");ok('no_deja_capturar_fechas_futuras','futura' in pd.inner_text('#asMsg') and pd.input_value('#asFec')==sab1)
    pd.fill('#asFec',sab0);pd.evaluate("document.getElementById('asFec').dispatchEvent(new Event('change'))");pd.click('#asTodos')
    pd.check('#asTb tr:has-text("Beto") input[value="F"]');pd.check('#asTb tr:has-text("Carla") input[value="R"]')
    ok('un_justificante_aprobado_se_marca_como_justificada','Justificada' in pd.inner_text('#asTb tr:has-text("Beto")') and 'justificante' in pd.inner_text('#asTb tr:has-text("Ana")').lower() is False or 'Justificada' in pd.inner_text('#asTb tr:has-text("Beto")'))
    pd.click('#asOk');W(pd,"ASI.m1&&ASI.m1.sesiones['%s']"%sab0)
    d=ctx.request.get(B+'/api/doc/asistencia/m1').json()['data']
    ok('guarda_la_sesion_en_el_servidor',d['sesiones'][sab0]=={'s1':'P','s2':'F','s3':'R','s4':'P'} and d['por']=='Mtro. Pedro Soto' and d['mid']=='m1')
    pd.fill('#asFec',sab1);pd.evaluate("document.getElementById('asFec').dispatchEvent(new Event('change'))");pd.click('#asTodos');pd.check('#asTb tr:has-text("Ana") input[value="F"]');pd.click('#asOk');W(pd,"Object.keys(ASI.m1.sesiones).length===2")
    ok('las_sesiones_aparecen_como_botones_de_fecha',pd.locator('#asChips button').count()==2 and '2 sesiones' in pd.inner_text('#asS'))
    pd.click('#asRes');W(pd,"document.getElementById('asResTb').rows.length===4")
    def fila(n):return [x.strip() for x in pd.inner_text('#asResTb tr:has-text("%s")'%n).split('\t')]
    ok('el_resumen_calcula_el_porcentaje',fila('Ana')[-2:]==['50 %','5.0'] and fila('Beto')[-2:]==['100 %','10.0'] and fila('Carla')[-2:]==['75 %','7.5'] and fila('Diego')[-2:]==['100 %','10.0'])
    ok('la_justificada_cuenta_como_asistencia',fila('Beto')[4]=='1' and fila('Beto')[3]=='0')
    pd.click('#asCls')
    # ============ la asistencia pesa 20 % de la calificación ============
    pd.locator('#dmL tr:has-text("Didáctica general") [data-ev]').first.click();pd.wait_for_selector('#dEv[open]')
    ok('la_evaluacion_avisa_que_la_asistencia_vale_20','La calificación final es 80 % tus puntos y 20 % la asistencia' in pd.inner_text('#evAsis') and 'Asistencia' in pd.inner_text('#evTabla thead'))
    fin=lambda n:pd.inner_text('#evTabla tr:has-text("%s") [data-fin]'%n).strip()
    ok('calcula_80_puntos_mas_20_asistencia',fin('Ana')=='8.2' and fin('Beto')=='8.4' and fin('Carla')=='9.5' and fin('Diego')=='7.6')
    pd.click('#evGuarda');W(pd,"CAL.s1.items.find(function(i){return i.mid==='m1'}).cal===8.2");c1=ctx.request.get(B+'/api/doc/calif/s1').json()['data']['items']
    i1=[x for x in c1 if x['mid']=='m1'][0];i2=[x for x in c1 if x['mid']=='m2'][0]
    ok('guarda_la_calificacion_final_la_academica_y_la_asistencia',i1['cal']==8.2 and i1['calAc']==9 and i1['asis']==50.0 and i2['cal']==9)
    pd.click('#evCls')
    pd.locator('#dmL tr:has-text("Historia de la educación") [data-as]').first.click();pd.wait_for_selector('#dAs[open]');ok('otra_asignatura_sin_asistencia_queda_igual','Historia de la educación' in pd.inner_text('#asT') and 'Aún no hay sesiones' in pd.inner_text('#asChips'));pd.click('#asCls')
    # ============ permisos ============
    pd2,cxd2=entra('doc2')
    ok('otro_docente_no_ve_ni_escribe_la_asistencia_ajena',api(cxd2,'GET','/api/doc/asistencia/m1').json()['exists'] is False and api(cxd2,'PUT','/api/doc/asistencia/m1',{'mid':'m1','sesiones':{}})[ 'status' if False else 'status']==403 if False else (api(cxd2,'GET','/api/doc/asistencia/m1').json()['exists'] is False and api(cxd2,'PUT','/api/doc/asistencia/m1',{'mid':'m1','sesiones':{}}).status==403))
    ok('y_sus_propias_si_puede',api(cxd2,'PUT','/api/doc/asistencia/m3',{'mid':'m3','sesiones':{sab1:{'s5':'P'}}}).status==200)
    pe,cxe=entra('esc2');ck,cxk=entra('caja1')
    ok('control_escolar_lee_y_escribe_la_asistencia',api(cxe,'GET','/api/doc/asistencia/m1').json()['exists'] is True and api(cxe,'PUT','/api/doc/asistencia/m3',{'mid':'m3','sesiones':{sab1:{'s5':'R'}}}).status==200)
    ok('caja_no_puede_escribirla',api(cxk,'PUT','/api/doc/asistencia/m3',{'mid':'m3','sesiones':{}}).status==403)
    pg.evaluate("ir('esc');etab('K')");W(pg,"ASI.m1");pg.wait_for_selector('#mTb [data-mas]')
    ok('control_escolar_tambien_abre_la_asistencia_desde_el_calendario',pg.locator('#mTb tr:has-text("Didáctica general") [data-mas]').inner_text().startswith('Asistencia (2)'))
    # ============ cierre de ciclo ============
    pe.evaluate("ir('esc');etab('G')");W(pe,"Object.keys(GRP).length===3&&Object.keys(CAL).length>=5")
    ok('la_campana_avisa_del_periodo_terminado_por_cerrar','periodo terminado por cerrar' in pe.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')"))
    pe.click('#ccAbre');pe.wait_for_selector('#dCc[open]')
    pe.select_option('#ccPer',PER);pe.wait_for_timeout(300)
    ok('muestra_el_siguiente_periodo','Siguiente periodo: '+SIG in pe.inner_text('#ccSig'))
    t=pe.inner_text('#ccRev');ok('la_revision_cuenta_calificaciones_y_sesiones_de_asistencia','Didáctica general' in t and '4 de 4' in t and '3 de 4' in t and 'Tesis' in t)
    t=pe.inner_text('#ccPrev');ok('la_vista_previa_separa_pasan_adeudo_y_terminan','4821' in t and '4833' in t and 'Total: 5 alumnos · 1 pasan · 3 con adeudo · 0 repiten · 1 terminan el plan' in t)
    pe.select_option('#ccPol','repite');pe.wait_for_timeout(300);ok('con_la_politica_repite_cambia_la_vista','1 pasan · 0 con adeudo · 3 repiten' in pe.inner_text('#ccPrev'));pe.select_option('#ccPol','adeudo');pe.wait_for_timeout(300)
    ok('si_faltan_calificaciones_ofrece_cerrar_de_todos_modos',pe.is_visible('#ccForzW'))
    pe.click('#ccOk');pe.wait_for_timeout(400);ok('no_cierra_si_faltan_calificaciones_sin_confirmar','Faltan calificaciones' in pe.inner_text('#ccMsg') and ctx.request.get(B+'/api/doc/ciclos/'+pg.evaluate("idPer('%s')"%PER)).json()['exists'] is False)
    pe.check('#ccForzar');pe.click('#ccOk');W(pe,"CIC[idPer('%s')]&&CIC[idPer('%s')].cerrado"%(PER,PER));pe.wait_for_timeout(400)
    c=ctx.request.get(B+'/api/doc/ciclos/'+pg.evaluate("idPer('%s')"%PER)).json()['data']
    ok('registra_el_cierre_con_resumen_y_adeudos',c['cerrado'] and c['sig']==SIG and c['resumen']=={'alumnos':5,'pasan':1,'adeudo':3,'repiten':0,'terminan':1,'sinCal':1} and sorted(c['adeudos'].keys())==['s2','s3','s4'] and c['politica']=='adeudo' and c['forzado'] is True and c['por']=='Esc Dos')
    gs=[v for v in ctx.request.get(B+'/api/col/grupos').json()['docs'] if v['data']['per']==SIG]
    ok('crea_los_grupos_del_siguiente_periodo_con_los_alumnos_que_pasan',len(gs)==1 and gs[0]['data']['cuat']==2 and sorted(gs[0]['data']['alumnos'])==['s1','s2','s3','s4'] and gs[0]['data']['plan']=='Pedagogía' and gs[0]['data']['num'] not in ('4821','4833','4700'))
    ok('el_alumno_del_ultimo_cuatrimestre_no_pasa_a_ningun_grupo',not any('s5' in v['data']['alumnos'] for v in gs))
    ok('la_pantalla_muestra_el_periodo_cerrado','Periodo cerrado' in pe.inner_text('#ccCerrado') and pe.is_hidden('#ccOk') and pe.is_hidden('#ccReabre'))
    pe.click('#ccCls')
    # ============ bloqueo del periodo cerrado ============
    W(pd,"CIC[idPer('%s')]&&CIC[idPer('%s')].cerrado"%(PER,PER))
    ci=ctx.request.get(B+'/api/doc/calif/s1').json()['data'];ci2=json.loads(json.dumps(ci));ci2['items'][0]['cal']=10
    ok('el_servidor_no_deja_cambiar_calificaciones_de_un_periodo_cerrado',api(cxd,'PUT','/api/doc/calif/s1',ci2).status==403 and api(cxe,'PUT','/api/doc/calif/s1',ci2).status==403)
    ok('tampoco_la_asistencia',api(cxd,'PUT','/api/doc/asistencia/m1',{'mid':'m1','sesiones':{}}).status==403 and api(cxe,'PUT','/api/doc/asistencia/m3',{'mid':'m3','sesiones':{}}).status==403)
    ok('el_administrador_si_puede_corregir',api(ctx,'PUT','/api/doc/calif/s1',ci2).status==200);api(ctx,'PUT','/api/doc/calif/s1',ci)
    ok('un_cambio_de_otro_periodo_no_se_bloquea',api(cxd,'PUT','/api/doc/calif/s1',{'items':ci['items']+[{'id':'z1','mid':'mx','mat':'Otra','plan':'Pedagogía','per':'May–Ago 2027','cuat':2,'cal':9}]}).status==200);api(ctx,'PUT','/api/doc/calif/s1',ci)
    pd.evaluate("ir('doc')") if False else None
    pd.locator('#dmL tr:has-text("Didáctica general") [data-as]').first.click();pd.wait_for_selector('#dAs[open]')
    ok('la_pantalla_de_asistencia_avisa_que_esta_cerrado',pd.is_visible('#asCerr') and pd.is_hidden('#asOk') and pd.is_hidden('#asTodos') and pd.is_disabled('#asFec'));pd.click('#asCls')
    pd.locator('#dmL tr:has-text("Didáctica general") [data-ev]').first.click();pd.wait_for_selector('#dEv[open]');pd.fill('#evTabla tr:has-text("Ana") input[data-cid="cr1"]','5');pd.click('#evGuarda');pd.wait_for_timeout(600)
    ok('y_la_de_calificaciones_no_guarda',ctx.request.get(B+'/api/doc/calif/s1').json()['data']['items'][0]['cal'] in (9,8.2,10) and [x for x in ctx.request.get(B+'/api/doc/calif/s1').json()['data']['items'] if x['mid']=='m1'][0]['cal']==8.2);pd.click('#evCls')
    # ============ reabrir ============
    ok('control_escolar_no_puede_reabrir_por_el_servidor',api(cxe,'PUT','/api/doc/ciclos/'+pg.evaluate("idPer('%s')"%PER),dict(c,cerrado=False)).status==403)
    pg.evaluate("ir('esc');etab('G')");W(pg,"CIC[idPer('%s')]"%PER);pg.click('#ccAbre');pg.wait_for_selector('#dCc[open]');pg.select_option('#ccPer',PER);pg.wait_for_timeout(300)
    ok('el_administrador_ve_el_boton_de_reabrir',pg.is_visible('#ccReabre'))
    pg.click('#ccReabre');W(pg,"!CIC[idPer('%s')].cerrado"%PER);pg.wait_for_timeout(300)
    ok('al_reabrir_se_puede_volver_a_cambiar',api(cxd,'PUT','/api/doc/calif/s1',ci2).status==200 and api(cxd,'PUT','/api/doc/asistencia/m1',{'mid':'m1','sesiones':{sab0:{'s1':'P','s2':'P','s3':'P','s4':'P'}}}).status==200 and pg.evaluate("CIC[idPer('%s')].reabierto.por"%PER)=='Administrador');api(ctx,'PUT','/api/doc/calif/s1',ci)
    pg.click('#ccCls')
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pd.locator('#dmL tr:has-text("Didáctica general") [data-as]').first.click();pd.wait_for_selector('#dAs[open]');pd.wait_for_timeout(400);pd.screenshot(path='/tmp/as_captura.png')
    pg.evaluate("ir('esc');etab('G')");pg.click('#ccAbre');pg.wait_for_selector('#dCc[open]');pg.select_option('#ccPer','Sep–Dic 2026');pg.wait_for_timeout(500);pg.screenshot(path='/tmp/cc_cierre.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
