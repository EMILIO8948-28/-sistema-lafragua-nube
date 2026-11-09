import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3089;B='http://127.0.0.1:%d'%PORT;TOK='tok-rv-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata19',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata19 && mkdir -p /tmp/nbdata19')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=15):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
PER='Sep–Dic 2026'
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    put('docentes/d1',{'nombre':'Mtra. Uno','esp':'Pedagogía','asig':[{'id':'a1','plan':'Pedagogía','per':PER,'cuat':1,'nom':'Modelos de enseñanza','ses':17},{'id':'a3','plan':'Pedagogía','per':PER,'cuat':1,'nom':'Didáctica','ses':17}]})
    put('docentes/d2',{'nombre':'Mtro. Dos','esp':'Psicología','asig':[{'id':'a2','plan':'Pedagogía','per':PER,'cuat':1,'nom':'Educación especial','ses':17}]})
    for mid,nom,doc in [('m1','Modelos de enseñanza','d1'),('m2','Educación especial','d2'),('m3','Didáctica','d1')]:put('materias/'+mid,{'per':PER,'plan':'Pedagogía','cuat':1,'nom':nom,'docId':doc,'dias':['Sáb'],'ini':'08:00','fin':'10:00','aula':'A1'})
    # planes de estudio para probar el resumen y el borrado
    put('catalogo/pedagogia',{'plan':'Pedagogía','items':[{'id':'p%d'%i,'cuat':1+(i//3),'clave':'LP%02d'%i,'nom':'Materia %d'%i,'cred':None,'hrs':None,'ct':1,'pdf':0} for i in range(1,8)]})
    for i in range(1,8):put('contenidos/p%d'%i,{'txt':'Contenido de la materia %d '%i+'x'*500,'pdf':None})
    put('catalogo/derecho',{'plan':'Derecho','items':[{'id':'d%d'%i,'cuat':1,'clave':'DER%d'%i,'nom':'Derecho %d'%i,'cred':None,'hrs':None,'ct':1,'pdf':0} for i in range(1,4)]})
    for i in range(1,4):put('contenidos/d%d'%i,{'txt':'Contenido derecho %d '%i+'x'*500,'pdf':None})
    for u,n,r,m,doc in [('doc1','Mtra. Uno','docente',None,'d1'),('doc2','Mtro. Dos','docente',None,'d2'),('esc1','Esc Uno','personalizado',{'escolar':'ver'},None),('esc2','Esc Dos','personalizado',{'escolar':'editar'},None),('caja1','Caja Uno','caja',None,None)]:
        body={'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u}
        if m:body['modulos']=m
        if doc:body['doc']=doc
        assert ctx.request.post(B+'/api/usuarios',data=json.dumps(body),headers=HDR).status==200,u
    def ses(u):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);assert r.status==200;return cx
    S_={u:ses(u) for u in ['doc1','doc2','esc1','esc2','caja1']}
    def hdr(extra=None):
        h=dict(HDR);h.update(extra or {});return h
    def u_put(u,path,obj):return S_[u].request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status
    def u_patch(u,path,obj):return S_[u].request.patch(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status
    def est(mid=None):return get('planeaciones/m1')['data'] if get('planeaciones/m1')['exists'] else {}
    def subir():
        r=S_['doc1'].request.post(B+'/api/archivo',data=b'%PDF-1.4 plan '+os.urandom(4),headers={'x-lafragua':'1','x-nombre':'plan.pdf','x-privado':'1','x-categoria':'planeacion','Content-Type':'application/pdf'});return r.json()['id']
    # ---------------- el servidor: nadie aprueba su propia planeación ----------------
    f1=subir()
    ok('docente_sube_y_queda_en_revision',u_put('doc1','planeaciones/m1',{'files':[{'id':f1,'name':'plan.pdf'}],'estado':'aprobada','revisor':'yo'})==200 and est()['estado']=='pendiente' and 'revisor' not in est())
    ok('docente_no_se_autoriza_a_si_mismo',u_patch('doc1','planeaciones/m1',{'estado':'aprobada'})==200 and est()['estado']=='pendiente')
    ok('quien_no_edita_control_escolar_no_revisa',u_patch('esc1','planeaciones/m1',{'estado':'aprobada'})==403 and u_patch('caja1','planeaciones/m1',{'estado':'aprobada'})==403 and u_patch('doc2','planeaciones/m1',{'estado':'aprobada'})==403)
    r=ctx.request.patch(B+'/api/doc/planeaciones/m1',data=json.dumps({'estado':'aprobada','revisor':'Administrador','revFecha':'2026-11-05','motivo':''}),headers=HDR);ok('administrador_autoriza',r.status==200 and est()['estado']=='aprobada' and est()['revisor']=='Administrador')
    ok('mismos_archivos_no_reabren',u_put('doc1','planeaciones/m1',{'files':[{'id':f1,'name':'plan.pdf'}]})==200 and est()['estado']=='aprobada' and est()['revisor']=='Administrador')
    f2=subir();ok('archivo_nuevo_reabre_la_revision',u_put('doc1','planeaciones/m1',{'files':[{'id':f1,'name':'plan.pdf'},{'id':f2,'name':'plan2.pdf'}]})==200 and est()['estado']=='pendiente' and 'revisor' not in est())
    ctx.request.patch(B+'/api/doc/planeaciones/m1',data=json.dumps({'estado':'aprobada','revisor':'Administrador','revFecha':'2026-11-05'}),headers=HDR)
    ok('mismos_puntos_no_reabren',u_put('doc1','criterios/m1',{'items':[]})==200 and est()['estado']=='aprobada')
    u_put('doc1','criterios/m1',{'items':[{'id':'a','nom':'Examen','peso':50}]});ok('cambiar_puntos_reabre_la_revision',est()['estado']=='pendiente')
    ctx.request.patch(B+'/api/doc/planeaciones/m1',data=json.dumps({'estado':'aprobada','revisor':'Administrador'}),headers=HDR)
    ok('mismos_puntos_otra_vez_no_reabren',u_put('doc1','criterios/m1',{'items':[{'id':'a','nom':'Examen','peso':50}]})==200 and est()['estado']=='aprobada')
    r=S_['esc2'].request.patch(B+'/api/doc/planeaciones/m1',data=json.dumps({'estado':'denegada','revisor':'Esc Dos','revFecha':'2026-11-06','motivo':'Faltan fechas'}),headers=HDR);ok('quien_edita_control_escolar_tambien_revisa',r.status==200 and est()['estado']=='denegada' and est()['motivo']=='Faltan fechas')
    ok('docente_ve_su_negativa_y_no_la_quita',S_['doc1'].request.get(B+'/api/doc/planeaciones/m1').json()['data']['motivo']=='Faltan fechas' and u_patch('doc1','planeaciones/m1',{'estado':'aprobada','motivo':''})==200 and est()['estado']=='denegada' and est()['motivo']=='Faltan fechas')
    u_put('doc1','criterios/m1',{'items':[{'id':'a','nom':'Examen','peso':100}]});ok('corregir_tras_la_negativa_vuelve_a_revision',est()['estado']=='pendiente' and 'motivo' not in est())
    ctx.request.patch(B+'/api/doc/planeaciones/m1',data=json.dumps({'estado':'pendiente'}),headers=HDR)
    # ---------------- plan de estudios ----------------
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(CATA).length>=2&&Object.keys(PLN).length>=1")
    pg.evaluate("ir('esc');etab('P')");pg.wait_for_selector('#pResumen table')
    tr=pg.inner_text('#pResumen');ok('resumen_de_planes_con_sus_materias','Pedagogía' in tr and 'Derecho' in tr and 'Psicología' in tr and pg.locator('#pResumen tr:has-text("Pedagogía") td.n').first.inner_text()=='7' and pg.locator('#pResumen tr:has-text("Derecho") td.n').first.inner_text()=='3')
    # ---- ver las materias: la lista debe quedar a la vista y poderse filtrar por cuatrimestre ----
    pg.set_viewport_size({'width':1280,'height':720});pg.evaluate("window.scrollTo(0,0)")
    pg.click('#pResumen tr:has-text("Pedagogía") [data-pv]');pg.wait_for_timeout(1200)
    top=pg.evaluate("document.getElementById('pLista').getBoundingClientRect().top");ok('al_ver_materias_la_lista_queda_a_la_vista',0<=top<720 and pg.input_value('#pPlan')=='Pedagogía' and 'Materia 1' in pg.inner_text('#pLista'))
    pg.evaluate("window.scrollTo(0,0)");pg.click('#pResumen tr:has-text("Derecho") td:first-child');pg.wait_for_timeout(1200)
    ok('toda_la_fila_del_resumen_es_clicable',pg.input_value('#pPlan')=='Derecho' and 'Derecho 2' in pg.inner_text('#pLista'))
    pg.select_option('#pPlan','Pedagogía');pg.wait_for_timeout(300)
    ok('todos_los_cuatrimestres_por_defecto',pg.input_value('#pCuatF')=='' and 'mostrando todos' in pg.inner_text('#pRes') and pg.locator('#pLista h2').count()>=3)
    opc=pg.evaluate("Array.from(document.querySelectorAll('#pCuatF option')).map(function(o){return o.textContent})");ok('filtro_con_cuantas_materias_hay_en_cada_cuatrimestre',opc[0].startswith('Todos los cuatrimestres (7)') and any('Cuatrimestre 1 (' in o for o in opc))
    pg.select_option('#pCuatF','2');ok('filtrar_un_cuatrimestre','mostrando el cuatrimestre 2' in pg.inner_text('#pRes') and pg.locator('#pLista h2').count()==1 and 'Cuatrimestre 2' in pg.inner_text('#pLista'))
    pg.select_option('#pCuatF','');ok('volver_a_todos',pg.locator('#pLista h2').count()>=3)
    pg.select_option('#pPlan','Derecho');ok('al_cambiar_de_plan_vuelve_a_todos',pg.input_value('#pCuatF')=='')
    ok('formulario_de_alta_plegado_y_separado',pg.evaluate("!document.getElementById('pForm').open")==True)
    pg.select_option('#pPlan','Pedagogía')
    pg.click('#pResumen tr:has-text("Derecho") [data-pv]');ok('ver_materias_de_otro_plan',pg.input_value('#pPlan')=='Derecho' and 'Derecho 1' in pg.inner_text('#pLista') and 'Materia 1' not in pg.inner_text('#pLista'))
    # quitar una materia (dos pasos, sin ventanas del navegador)
    pg.click('#pLista [data-dp="d1"]');ok('pide_confirmar_al_quitar','Se quitará «Derecho 1»' in pg.inner_text('#pDelMsg') and 'Confirmar' in pg.inner_text('#pLista [data-dp="d1"]'))
    pg.click('#pLista [data-dp="d1"]');W(pg,"catItems('Derecho').length===2")
    ok('materia_quitada_con_su_contenido',[i['id'] for i in get('catalogo/derecho')['data']['items']]==['d2','d3'] and get('contenidos/d1')['exists'] is False and get('contenidos/d2')['exists'] is True and 'se quitó del plan' in pg.inner_text('#pDelMsg'))
    # varias a la vez
    pg.select_option('#pPlan','Pedagogía');pg.evaluate("renderPlan()")
    pg.check('#pLista [data-sel="p1"]');pg.check('#pLista [data-sel="p2"]');ok('barra_de_seleccion','Quitar seleccionadas (2)' in pg.inner_text('#pSelBar'))
    pg.check('#pLista [data-sc="3"]') if pg.locator('#pLista [data-sc="3"]').count() else None
    n=len([k for k,v in pg.evaluate("PSEL").items() if v]);pg.uncheck('#pLista [data-sc="3"]') if pg.locator('#pLista [data-sc="3"]').count() else None
    pg.evaluate("PSEL={};renderPlan()");pg.check('#pLista [data-sel="p1"]');pg.check('#pLista [data-sel="p2"]')
    pg.click('#pDelSel');ok('confirmar_varias','Confirmar: quitar 2 asignaturas' in pg.inner_text('#pSelBar') and 'Se quitarán 2' in pg.inner_text('#pDelMsg'))
    pg.click('#pDelSel');W(pg,"catItems('Pedagogía').length===5")
    ok('varias_quitadas_con_su_contenido',[i['id'] for i in get('catalogo/pedagogia')['data']['items']]==['p3','p4','p5','p6','p7'] and get('contenidos/p1')['exists'] is False and get('contenidos/p2')['exists'] is False and get('contenidos/p3')['exists'] is True)
    ok('todo_el_cuatrimestre',pg.locator('#pLista [data-sc]').count()>=1)
    # quien edita Control escolar necesita la autorización del encargado
    ce=b.new_context(viewport={'width':1100,'height':900});ce.set_default_timeout(15000);pe=pagina(ce);pe.goto(B+'/');W(pe,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pe.fill('#lgU','esc2');pe.fill('#lgP','clave-esc2-123');pe.click('#lgGo');W(pe,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof CATA!=='undefined'&&Object.keys(CATA).length>=2")
    pe.evaluate("ir('esc');etab('P')");pe.select_option('#pPlan','Pedagogía');pe.evaluate("renderPlan()");pe.wait_for_selector('#pLista [data-dp="p7"]')
    pe.click('#pLista [data-dp="p7"]');pe.click('#pLista [data-dp="p7"]');pe.wait_for_selector('#dAu[open]');ok('personal_pide_autorizacion_para_quitar_materias','Materia 7' in pe.inner_text('#auDesc') or 'elemento' in pe.inner_text('#auDesc').lower() or 'asignatura' in pe.inner_text('#auDesc').lower())
    pe.fill('#auPw','clave-segura-1');pe.click('#auClave');W(pe,"catItems('Pedagogía').length===4",20)
    ok('materia_quitada_tras_autorizar',len(get('catalogo/pedagogia')['data']['items'])==4 and get('contenidos/p7')['exists'] is False)
    # ---------------- revisión de planeaciones en Docentes ----------------
    put('criterios/m3',{'items':[{'id':'z','nom':'Proyecto','peso':100}]})
    f3=subir();assert u_put('doc1','planeaciones/m3',{'files':[{'id':f3,'name':'didactica.pdf'}]})==200
    pg.evaluate("ir('home')");W(pg,"planPend()>=1");pg.wait_for_selector('#hPl:not([hidden])');ok('aviso_de_planeaciones_por_revisar_en_el_panel','Planeaciones por revisar' in pg.inner_text('#hPl') and 'esperan' in pg.inner_text('#hPlT') or 'espera' in pg.inner_text('#hPlT'))
    pg.click('#hPlGo');pg.wait_for_selector('#dcTb tr')
    fila=pg.inner_text('#dcTb tr:has-text("Mtra. Uno")');ok('columna_planeaciones_en_docentes','por revisar' in fila and 'Planeaciones' in pg.inner_text('#eD thead'))
    ok('docente_sin_planeacion_se_marca','sin planeación' in pg.inner_text('#dcTb tr:has-text("Mtro. Dos")'))
    pg.locator('#dcTb tr:has-text("Mtra. Uno") [data-rv]').click();pg.wait_for_selector('#dRv[open]')
    tx=pg.inner_text('#rvL');ok('revision_muestra_archivos_y_puntos','Modelos de enseñanza' in tx and 'Didáctica' in tx and 'plan.pdf' in tx and 'didactica.pdf' in tx and 'Examen' in tx and '100 %' in tx and 'Proyecto' in tx and pg.locator('#rvL [data-ra]').count()==2 and pg.locator('#rvL [data-rn]').count()==2)
    cd=b.new_context(viewport={'width':1100,'height':900});cd.set_default_timeout(15000);pd=pagina(cd);pd.goto(B+'/');W(pd,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pd.fill('#lgU','doc1');pd.fill('#lgP','clave-doc1-123');pd.click('#lgGo');W(pd,"typeof APP!=='undefined'&&APP!==null&&MOD==='doc'&&misClases().length>=2")
    ok('docente_ve_en_revision',pd.inner_text('#dmL tr:has-text("Modelos de enseñanza")').count('En revisión')>=1)
    # denegar pide motivo
    pg.locator('#rvL .mod:has-text("Modelos de enseñanza") [data-rn]').click();ok('denegar_exige_motivo','motivo' in pg.inner_text('#rvMsg').lower() and est()['estado']=='pendiente')
    pg.locator('#rvL .mod:has-text("Modelos de enseñanza") [data-rm]').fill('Agrega el cronograma de sesiones');pg.locator('#rvL .mod:has-text("Modelos de enseñanza") [data-rn]').click();W(pg,"PLN.m1&&PLN.m1.estado==='denegada'")
    ok('negativa_guardada_con_motivo',est()['estado']=='denegada' and est()['motivo']=='Agrega el cronograma de sesiones' and est()['revisor']=='Administrador' and 'denegada' in pg.inner_text('#rvL .mod:has-text("Modelos de enseñanza")').lower())
    W(pd,"PLN.m1&&PLN.m1.estado==='denegada'");ok('docente_ve_la_negativa_al_instante','Planeación denegada' in pd.inner_text('#dmL tr:has-text("Modelos de enseñanza")'))
    pd.locator('#dmL tr:has-text("Modelos de enseñanza") [data-pl]').click();pd.wait_for_selector('#dPn[open]')
    ok('docente_ve_el_motivo','Agrega el cronograma de sesiones' in pd.inner_text('#plEst') and 'denegada' in pd.inner_text('#plEst').lower())
    # autorizar
    pg.locator('#rvL .mod:has-text("Didáctica") [data-ra]').click();W(pg,"PLN.m3&&PLN.m3.estado==='aprobada'")
    ok('autorizacion_guardada',est() is not None and get('planeaciones/m3')['data']['estado']=='aprobada' and get('planeaciones/m3')['data']['revisor']=='Administrador' and '✔' in pg.inner_text('#rvMsg') or 'autorizada' in pg.inner_text('#rvMsg').lower())
    pd.click('#plCls');W(pd,"PLN.m3&&PLN.m3.estado==='aprobada'");ok('docente_ve_la_autorizacion','Planeación aprobada' in pd.inner_text('#dmL tr:has-text("Didáctica")'))
    # el docente corrige: vuelve a revisión
    pd.locator('#dmL tr:has-text("Modelos de enseñanza") [data-pl]').click();pd.wait_for_selector('#dPn[open]');pd.set_input_files('#plUp','/tmp/plf/plan.pdf');W(pd,"(PLN.m1.files||[]).length>=3");W(pd,"PLN.m1.estado==='pendiente'");W(pd,"document.getElementById('plEst').innerText.indexOf('En revisión')>-1")
    ok('al_corregir_vuelve_a_revision',pd.evaluate("PLN.m1.estado")=='pendiente' and 'En revisión' in pd.inner_text('#plEst'))
    pd.click('#plCls')
    pg.click('#rvCls');pg.evaluate("ir('home')");W(pg,"planPend()>=1");ok('el_aviso_vuelve_a_aparecer',pg.is_visible('#hPl'))
    # solo quien edita Control escolar revisa
    ok('docentes_no_ven_el_boton_de_revision',pd.locator('#dmL [data-rv]').count()==0)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
