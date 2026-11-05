import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3088;B='http://127.0.0.1:%d'%PORT;TOK='tok-pl-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata18',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata18 /tmp/plf && mkdir -p /tmp/nbdata18 /tmp/plf')
open('/tmp/plf/plan.pdf','wb').write(b'%PDF-1.4 planeacion');open('/tmp/plf/plan2.docx','wb').write(b'PK\x03\x04doc');open('/tmp/plf/malo.exe','wb').write(b'MZ');open('/tmp/plf/grande.pdf','wb').write(b'%PDF'+b'0'*(21*1024*1024))
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
    for d,n in [('d1','Mtra. Uno'),('d2','Mtro. Dos')]:put('docentes/'+d,{'nombre':n,'esp':'Pedagogía','asig':[]})
    put('docentes/d1',{'nombre':'Mtra. Uno','esp':'Pedagogía','asig':[{'id':'a1','plan':'Pedagogía','per':PER,'cuat':1,'nom':'Modelos de enseñanza','ses':17},{'id':'a3','plan':'Pedagogía','per':PER,'cuat':1,'nom':'Didáctica','ses':17}]})
    put('docentes/d2',{'nombre':'Mtro. Dos','esp':'Psicología','asig':[{'id':'a2','plan':'Pedagogía','per':PER,'cuat':1,'nom':'Educación especial','ses':17}]})
    for mid,nom,doc in [('m1','Modelos de enseñanza','d1'),('m2','Educación especial','d2'),('m3','Didáctica','d1')]:put('materias/'+mid,{'per':PER,'plan':'Pedagogía','cuat':1,'nom':nom,'docId':doc,'dias':['Sáb'],'ini':'08:00','fin':'10:00','aula':'A1'})
    put('students/s1',{'mat':'1001','nombre':'Ana López','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2025});put('grupos/g1',{'num':'1111','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1']})
    for u,n,r,m,doc in [('doc1','Mtra. Uno','docente',None,'d1'),('doc2','Mtro. Dos','docente',None,'d2'),('esc1','Esc Uno','personalizado',{'escolar':'ver'},None),('esc2','Esc Dos','personalizado',{'escolar':'editar'},None),('caja1','Caja Uno','caja',None,None)]:
        body={'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u}
        if m:body['modulos']=m
        if doc:body['doc']=doc
        assert ctx.request.post(B+'/api/usuarios',data=json.dumps(body),headers=HDR).status==200,u
    def ses(u):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);assert r.status==200;return cx
    S_={u:ses(u) for u in ['doc1','doc2','esc1','esc2','caja1']}
    def pu(u,path,obj):return S_[u].request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status
    def col(u,c):return sorted(d['id'] for d in S_[u].request.get(B+'/api/col/'+c).json()['docs'])
    # ---------------- servidor: cada docente solo ve y escribe lo suyo ----------------
    ok('docente_escribe_su_planeacion',pu('doc1','planeaciones/m1',{'files':[]})==200 and pu('doc1','planeaciones/m3',{'files':[]})==200)
    ok('docente_no_escribe_la_de_otro',pu('doc1','planeaciones/m2',{'files':[]})==403 and pu('doc2','planeaciones/m1',{'files':[]})==403)
    put('planeaciones/m2',{'files':[]})
    ok('cada_docente_ve_solo_las_suyas',col('doc1','planeaciones')==['m1','m3'] and col('doc2','planeaciones')==['m2'])
    ok('quien_edita_control_escolar_las_ve_todas',col('esc2','planeaciones')==['m1','m2','m3'] and col('esc1','planeaciones')==[])
    ok('caja_no_ve_planeaciones',col('caja1','planeaciones')==[] and pu('caja1','planeaciones/m1',{'files':[]})==403)
    ok('doc_ajeno_no_existe',S_['doc1'].request.get(B+'/api/doc/planeaciones/m2').json()['exists'] is False)
    up=S_['doc1'].request.post(B+'/api/archivo',data=b'%PDF-1.4 plan',headers={'x-lafragua':'1','x-nombre':'plan.pdf','x-privado':'1','x-categoria':'planeacion','Content-Type':'application/pdf'});fid=up.json()['id']
    ok('docente_sube_archivo_privado',up.status==200)
    ok('docente_no_sube_archivos_publicos',S_['doc1'].request.post(B+'/api/archivo',data=b'%PDF',headers={'x-lafragua':'1','x-nombre':'a.pdf','Content-Type':'application/pdf'}).status==403)
    ok('quien_puede_abrir_el_archivo',S_['doc1'].request.get(B+'/_blob/'+fid).status==200 and ctx.request.get(B+'/_blob/'+fid).status==200 and S_['esc2'].request.get(B+'/_blob/'+fid).status==200)
    ok('otros_no_abren_el_archivo',S_['doc2'].request.get(B+'/_blob/'+fid).status==403 and S_['caja1'].request.get(B+'/_blob/'+fid).status==403 and S_['esc1'].request.get(B+'/_blob/'+fid).status==403)
    ok('otro_docente_no_borra_el_archivo',S_['doc2'].request.delete(B+'/api/archivo/'+fid,headers=HDR).status==403)
    put('planeaciones/m1',{'files':[{'id':fid,'name':'plan.pdf','size':14,'fecha':'2026-11-01'}]})
    ok('docente_quita_su_archivo_sin_pedir_permiso',pu('doc1','planeaciones/m1',{'files':[]})==200 and S_['doc1'].request.delete(B+'/api/archivo/'+fid,headers=HDR).status==200)
    ok('docente_define_puntos_de_evaluacion',pu('doc1','criterios/m1',{'items':[{'id':'a','nom':'Examen','peso':40}]})==200)
    # ---------------- pantalla del docente ----------------
    cd=b.new_context(viewport={'width':1100,'height':900});cd.set_default_timeout(15000);pd=pagina(cd);pd.goto(B+'/');W(pd,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pd.fill('#lgU','doc1');pd.fill('#lgP','clave-doc1-123');pd.click('#lgGo');W(pd,"typeof APP!=='undefined'&&APP!==null&&MOD==='doc'&&misClases().length>=2")
    ok('mensaje_de_asistencia_en_mis_asignaturas','La asistencia vale un 20 % sobre el valor de la calificación' in pd.inner_text('#vDoc'))
    t=pd.inner_text('#dmL');ok('boton_y_estado_de_planeacion',pd.locator('#dmL [data-pl]').count()==2 and t.count('Falta la planeación')==2 and 'Planeación y evaluación' in t)
    pd.locator('#dmL tr:has-text("Modelos de enseñanza") [data-pl]').click();pd.wait_for_selector('#dPn[open]')
    ok('dialogo_con_mensaje_y_titulo','La asistencia vale un 20 % sobre el valor de la calificación' in pd.inner_text('#dPn') and 'Modelos de enseñanza' in pd.inner_text('#plT') and 'Mtra. Uno' in pd.inner_text('#plS'))
    ok('puntos_previos_se_muestran',pd.locator('#plCrit input[data-f="nom"]').count()==1 and pd.input_value('#plCrit input[data-f="nom"]')=='Examen')
    pd.set_input_files('#plUp','/tmp/plf/malo.exe');pd.wait_for_timeout(300);ok('rechaza_tipo','PDF, Word' in pd.inner_text('#plMsg'))
    pd.set_input_files('#plUp','/tmp/plf/grande.pdf');pd.wait_for_timeout(500);ok('rechaza_tamano','20 MB' in pd.inner_text('#plMsg'))
    pd.set_input_files('#plUp',['/tmp/plf/plan.pdf','/tmp/plf/plan2.docx']);W(pd,"(PLN.m1&&PLN.m1.files||[]).length===2")
    ok('sube_varios_archivos','2 archivos cargados' in pd.inner_text('#plMsg') and 'plan.pdf' in pd.inner_text('#plFiles') and 'plan2.docx' in pd.inner_text('#plFiles'))
    ids=pd.evaluate("PLN.m1.files.map(function(f){return f.id})");ok('archivos_guardados_en_el_servidor',all(ctx.request.get(B+'/_blob/'+i).status==200 for i in ids) and len(ctx.request.get(B+'/api/doc/planeaciones/m1').json()['data']['files'])==2)
    # puntos de evaluación
    pd.click('#plAdd');pd.click('#plAdd')
    nombres=pd.locator('#plCrit input[data-f="nom"]');pesos=pd.locator('#plCrit input[data-f="peso"]')
    nombres.nth(1).fill('Tareas');pesos.nth(1).fill('30');nombres.nth(2).fill('Proyecto final');pesos.nth(2).fill('10')
    pesos.nth(0).fill('40');ok('muestra_la_suma','suman 80 %' in pd.inner_text('#plSuma'))
    pesos.nth(2).fill('150');pd.click('#plSave');ok('rechaza_porcentaje_fuera_de_rango','0 a 100' in pd.inner_text('#plMsg'))
    pesos.nth(2).fill('10');pd.click('#plSave');W(pd,"document.getElementById('plMsg').textContent.includes('guardados')")
    cr=ctx.request.get(B+'/api/doc/criterios/m1').json()['data']['items'];ok('puntos_y_porcentajes_guardados',[(c['nom'],c['peso']) for c in cr]==[('Examen',40),('Tareas',30),('Proyecto final',10)])
    pd.click('#plCls');ok('etiqueta_cambia_a_cargada','En revisión' in pd.inner_text('#dmL tr:has-text("Modelos de enseñanza")') and 'Falta la planeación' in pd.inner_text('#dmL tr:has-text("Didáctica")'))
    # al capturar calificaciones aparecen los mismos puntos y el mensaje
    pd.locator('#dmL tr:has-text("Modelos de enseñanza") [data-ev]').click();pd.wait_for_selector('#dEv[open]')
    ok('calificaciones_usan_los_puntos_y_muestran_el_mensaje','La asistencia vale un 20 % sobre el valor de la calificación' in pd.inner_text('#dEv') and pd.locator('#evCrit input[data-f="nom"]').count()==3 and pd.input_value('#evCrit input[data-f="nom"] >> nth=2')=='Proyecto final')
    pd.click('#evCls')
    # quitar un archivo propio no pide autorización
    pd.locator('#dmL tr:has-text("Modelos de enseñanza") [data-pl]').click();pd.wait_for_selector('#dPn[open]');pd.locator('#plFiles [data-pq]').first.click();W(pd,"(PLN.m1.files||[]).length===1")
    ok('quitar_archivo_propio_sin_autorizacion',not pd.evaluate("document.getElementById('dAu').open") and len(ctx.request.get(B+'/api/doc/planeaciones/m1').json()['data']['files'])==1)
    pd.click('#plCls')
    ok('docente_no_ve_las_materias_de_otro_docente',pd.locator('#dmL [data-pl]').count()==2)
    # ---------------- el encargado las ve en el calendario ----------------
    # el calendario (alta de una materia con docente desde la pantalla) y que no haya identificadores repetidos
    ids=pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()");ok('sin_identificadores_repetidos',ids==[])
    pg.evaluate("ir('esc');etab('K')");pg.select_option('#mDocSel','d2');pg.fill('#mNomI','Taller de lectura');pg.fill('#mIni','08:00');pg.fill('#mFin','10:00');pg.click('#mAdd');W(pg,"Object.values(MAT).some(function(m){return m.nom==='Taller de lectura'&&m.docId==='d2'})")
    ok('alta_de_materia_en_el_calendario_con_docente',True)
    pg.evaluate("ir('esc');etab('K')");W(pg,"Object.keys(PLN).length>=1");pg.evaluate("renderMat()")
    ok('admin_ve_el_boton_en_el_calendario',pg.locator('#mTb tr:has-text("Modelos de enseñanza") [data-mpl]').count()==1 and 'Planeación (1)' in pg.inner_text('#mTb tr:has-text("Modelos de enseñanza")'))
    pg.locator('#mTb tr:has-text("Modelos de enseñanza") [data-mpl]').click();pg.wait_for_selector('#dPn[open]')
    ok('admin_ve_sin_poder_editar','plan' in pg.inner_text('#plFiles') and pg.is_hidden('#plUpW') and pg.is_hidden('#plSave') and pg.locator('#plFiles [data-pq]').count()==0 and pg.locator('#plCrit input[data-f="nom"]').count()==3)
    pg.click('#plCls')
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
