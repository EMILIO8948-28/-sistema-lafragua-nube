import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3260;B='http://127.0.0.1:%d'%PORT;TOK='tok-bl-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata100 && mkdir -p /tmp/nbdata100')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata100',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
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
PER='Sep–Dic 2026'
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    sab1=pg.evaluate("sabReciente()");SLUG=pg.evaluate("slug('Pedagogía')")
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    put('catalogo/'+SLUG,{'items':[{'id':'k1','nom':'Materia uno','cuat':1},{'id':'k2','nom':'Materia dos','cuat':1},{'id':'k3','nom':'Materia tres','cuat':1},{'id':'k4','nom':'Materia cuatro','cuat':1},{'id':'k5','nom':'Materia cinco','cuat':1},{'id':'k6','nom':'Tesis','cuat':3}]})
    for i,n in enumerate(['Ana López','Beto Mena','Carla Díaz','Diego Vega'],1):put('students/s%d'%i,{'mat':'2026%03d'%i,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('docentes/d1',{'nombre':'Mtro. Pedro Soto','esp':'Historia','asig':[]})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2','s3','s4']})
    base=dict(per=PER,plan='Pedagogía',cuat=1,docId='d1',ini='08:00',fin='10:00')
    put('materias/m1',dict(base,nom='Materia uno',bl=1,ev='2026-10-24'))        # bloque 1 explícito
    put('materias/m2',dict(base,nom='Materia dos',bl=2,ev='2026-12-12'))        # bloque 2 explícito
    put('materias/m3',dict(base,nom='Materia tres',ev='2026-10-17'))            # sin bloque: por su fecha, es el 1.º
    put('materias/m4',dict(base,nom='Materia cuatro',ev='2026-12-05'))          # sin bloque: por su fecha, es el 2.º
    put('materias/m5',dict(base,nom='Materia cinco'))                           # sin bloque ni fecha
    def cal(sid,items):put('calif/'+sid,{'items':[{'id':'i%s%s'%(sid,m),'mid':m,'mat':n,'plan':'Pedagogía','per':PER,'cuat':1,'cal':8.5,'fecha':sab1} for m,n in items]})
    for s in ['s1','s2','s3','s4']:cal(s,[('m1','Materia uno'),('m3','Materia tres')])
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('doc1','Mtro. Pedro Soto','docente',{'doc':'d1'});usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}})
    def entra(u):
        cx=b.new_context(viewport={'width':1200,'height':1000});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1500);return pp,cx
    api=lambda cx,m,url,body=None:cx.request.fetch(B+url,method=m,data=json.dumps(body) if body is not None else None,headers=HDR)
    pg.reload();W(pg,"Object.keys(MAT).length===5&&Object.keys(CAL).length===4")
    # ============ cada asignatura sabe en qué bloque está ============
    r=pg.evaluate("Object.keys(MAT).sort().map(function(k){return blDe(MAT[k])})")
    ok('el_bloque_sale_de_la_asignatura_o_de_su_fecha_de_evaluacion',r==[1,2,1,2,0])
    pg.evaluate("ir('esc');etab('K')");pg.wait_for_selector('#mTb tr')
    t=pg.inner_text('#mTb');ok('el_calendario_muestra_el_bloque','1.er bloque' in pg.inner_text('#mTb tr:has-text("Materia uno")') and '2.º bloque' in pg.inner_text('#mTb tr:has-text("Materia cuatro")') and 'bloque' not in pg.inner_text('#mTb tr:has-text("Materia cinco")'))
    pg.locator('#mTb tr:has-text("Materia cinco") [data-me]').click();pg.select_option('#mBl','2');pg.click('#mAdd');W(pg,"MAT.m5.bl===2")
    ok('se_puede_elegir_el_bloque_al_editar_una_asignatura',pg.evaluate("blDe(MAT.m5)")==2 and ctx.request.get(B+'/api/doc/materias/m5').json()['data']['bl']==2 and pg.input_value('#mBl')=='')
    put('materias/m5',dict(base,nom='Materia cinco',bl=2))
    # ============ cerrar el 1.er bloque ============
    pe,cxe=entra('esc2');W(pe,"Object.keys(MAT).length===5&&Object.keys(CAL).length===4")
    ok('la_campana_avisa_que_el_1er_bloque_ya_termino','bloque de asignaturas terminado por cerrar' in pe.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')"))
    pe.evaluate("ir('esc');etab('G')");pe.click('#ccAbre');pe.wait_for_selector('#dCc[open]');pe.select_option('#ccPer',PER)
    ok('al_haber_un_bloque_terminado_abre_en_ese_bloque',pe.input_value('#ccAlc')=='1' and '2 asignaturas' in pe.inner_text('#ccAlc option[value="1"]') and '3 asignaturas' in pe.inner_text('#ccAlc option[value="2"]'))
    t=pe.inner_text('#ccRev');ok('la_revision_solo_lista_las_del_bloque','Materia uno' in t and 'Materia tres' in t and 'Materia dos' not in t and 'Materia cuatro' not in t and '4 de 4' in t)
    ok('para_un_bloque_no_hay_vista_previa_de_alumnos',pe.is_hidden('#ccPrev') and pe.is_hidden('#ccPolW') and 'no cambian de grupo' in pe.inner_text('#ccSig') and 'Cerrar el 1.er bloque' in pe.inner_text('#ccOk'))
    pe.click('#ccOk');W(pe,"CIC[idPer('%s')]&&CIC[idPer('%s')].bloques&&CIC[idPer('%s')].bloques['1']"%(PER,PER,PER));pe.wait_for_timeout(300)
    c=ctx.request.get(B+'/api/doc/ciclos/'+pg.evaluate("idPer('%s')"%PER)).json()['data']
    ok('guarda_el_cierre_del_bloque_sin_cerrar_el_periodo',c['bloques']['1']['cerrado'] and c['bloques']['1']['por']=='Esc Dos' and c['cerrado'] is False and c['bloques']['1']['faltaban']==0)
    gs=ctx.request.get(B+'/api/col/grupos').json()['docs'];ok('no_crea_grupos_ni_mueve_alumnos',len(gs)==1)
    ok('queda_a_la_vista_y_ya_no_avisa','1.er bloque cerrado' in pe.inner_text('#ccCerrado') and pe.is_hidden('#ccOk') and pe.is_hidden('#ccReabre') and 'bloque de asignaturas terminado' not in pe.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')"))
    pe.click('#ccCls')
    # ============ el bloqueo solo alcanza a las asignaturas del bloque ============
    pd,cxd=entra('doc1');W(pd,"Object.keys(MAT).length===5&&Object.keys(CIC).length===1")
    asi=lambda m:api(cxd,'PUT','/api/doc/asistencia/'+m,{'mid':m,'sesiones':{sab1:{'s1':'P','s2':'P','s3':'P','s4':'P'}}}).status
    ok('la_asistencia_de_las_asignaturas_del_bloque_cerrado_se_bloquea',asi('m1')==403 and asi('m3')==403)
    ok('y_la_de_las_del_otro_bloque_sigue_abierta',asi('m2')==200 and asi('m4')==200 and asi('m5')==200)
    c1=ctx.request.get(B+'/api/doc/calif/s1').json()['data'];c1b=json.loads(json.dumps(c1));[i for i in c1b['items'] if i['mid']=='m1'][0]['cal']=10
    ok('las_calificaciones_del_bloque_cerrado_no_se_cambian',api(cxd,'PUT','/api/doc/calif/s1',c1b).status==403)
    c1c=json.loads(json.dumps(c1));c1c['items'].append({'id':'nuevo','mid':'m2','mat':'Materia dos','plan':'Pedagogía','per':PER,'cuat':1,'cal':9,'fecha':sab1})
    ok('pero_si_se_pueden_capturar_las_del_otro_bloque',api(cxd,'PUT','/api/doc/calif/s1',c1c).status==200);api(ctx,'PUT','/api/doc/calif/s1',c1)
    ok('el_administrador_si_puede_corregir',api(ctx,'PUT','/api/doc/calif/s1',c1b).status==200);api(ctx,'PUT','/api/doc/calif/s1',c1)
    pd.locator('#dmL tr:has-text("Materia uno") [data-as]').first.click();pd.wait_for_selector('#dAs[open]')
    ok('la_pantalla_del_docente_avisa_que_esta_cerrada',pd.is_visible('#asCerr') and pd.is_hidden('#asOk'));pd.click('#asCls')
    pd.locator('#dmL tr:has-text("Materia dos") [data-as]').first.click();pd.wait_for_selector('#dAs[open]')
    ok('y_la_del_otro_bloque_se_puede_capturar',pd.is_hidden('#asCerr') and pd.is_visible('#asTodos'));pd.click('#asCls')
    # ============ reabrir ============
    ok('control_escolar_no_puede_reabrir_un_bloque',api(cxe,'PUT','/api/doc/ciclos/'+pg.evaluate("idPer('%s')"%PER),dict(c,bloques={'1':dict(c['bloques']['1'],cerrado=False)})).status==403)
    pg.evaluate("ir('esc');etab('G')");W(pg,"CIC[idPer('%s')]"%PER);pg.click('#ccAbre');pg.wait_for_selector('#dCc[open]');pg.select_option('#ccPer',PER);pg.select_option('#ccAlc','1');pg.wait_for_timeout(300)
    ok('el_administrador_ve_el_boton_para_reabrir_el_bloque',pg.is_visible('#ccReabre') and 'bloque' in pg.inner_text('#ccReabre'))
    pg.click('#ccReabre');W(pg,"!bloqueCerrado('%s',1)"%PER);pg.wait_for_timeout(300)
    ok('al_reabrir_el_docente_vuelve_a_poder_capturar',asi('m1')==200 and pg.evaluate("CIC[idPer('%s')].bloques['1'].reabierto.por"%PER)=='Administrador')
    # ============ cerrar el 2.º bloque y luego el periodo completo ============
    pg.select_option('#ccAlc','2');pg.wait_for_timeout(300);t=pg.inner_text('#ccRev')
    ok('el_2o_bloque_lista_sus_asignaturas_y_pide_calificaciones','Materia dos' in t and 'Materia cuatro' in t and 'Materia cinco' in t and 'Materia uno' not in t and pg.is_visible('#ccForzW'))
    pg.click('#ccOk');pg.wait_for_timeout(400);ok('no_cierra_si_faltan_calificaciones','Faltan calificaciones' in pg.inner_text('#ccMsg'))
    pg.check('#ccForzar');pg.click('#ccOk');W(pg,"bloqueCerrado('%s',2)"%PER)
    ok('el_2o_bloque_queda_cerrado_con_lo_que_faltaba',pg.evaluate("CIC[idPer('%s')].bloques['2'].forzado"%PER) is True and pg.evaluate("CIC[idPer('%s')].bloques['2'].faltaban"%PER)>0)
    pg.select_option('#ccAlc','p');pg.wait_for_timeout(300);ok('el_periodo_completo_sigue_disponible','Qué pasará con los alumnos' in pg.inner_text('#vGr, #dCc') and pg.is_visible('#ccPrev') and pg.is_visible('#ccPolW'))
    pg.check('#ccForzar');pg.click('#ccOk');W(pg,"CIC[idPer('%s')].cerrado"%PER);pg.wait_for_timeout(300)
    c2=ctx.request.get(B+'/api/doc/ciclos/'+pg.evaluate("idPer('%s')"%PER)).json()['data']
    ok('el_cierre_del_periodo_conserva_el_registro_de_los_bloques',c2['cerrado'] and c2['bloques']['1']['reabierto'] and c2['bloques']['2']['cerrado'] and c2['resumen']['alumnos']==4)
    ok('con_el_periodo_cerrado_todas_las_asignaturas_quedan_bloqueadas',all(asi(m)==403 for m in ('m1','m2','m3','m4','m5')))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
