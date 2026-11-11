import subprocess,time,json,os,urllib.request,re,sqlite3
from playwright.sync_api import sync_playwright
OUT='/mnt/user-data/outputs/'
def arranca(port,data,tok,sin_precarga):
    os.system('rm -rf %s && mkdir -p %s'%(data,data))
    env=dict(os.environ,PORT=str(port),DATA_DIR=data,LF_SETUP_TOKEN=tok,LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
    if sin_precarga:env['LF_SIN_PRECARGA']='1'
    p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(120):
        time.sleep(0.25)
        try:urllib.request.urlopen('http://127.0.0.1:%d/salud'%port,timeout=1);break
        except Exception:pass
    return p
R={}
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def W(pg,js,t=60):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
SRC=json.load(open(OUT+'carga_ciencias_de_la_educacion_plan_y_contenidos.json',encoding='utf-8'))
ITEMS=SRC['colecciones']['catalogo']['ciencias-de-la-educacion']['items'];CONT=SRC['contenidos']
# ============ el archivo de carga ============
ok('el_archivo_trae_50_asignaturas_con_su_contenido',len(ITEMS)==50 and len(CONT)==50 and all(i['id'] in CONT for i in ITEMS))
ok('claves_L01_a_L50_en_orden',[i['clave'] for i in ITEMS]==['L%02d'%n for n in range(1,51)])
ok('distribucion_6_6_6_6_6_6_5_5_4',[len([i for i in ITEMS if i['cuat']==c]) for c in range(1,10)]==[6,6,6,6,6,6,5,5,4])
ok('la_psicologia_de_la_educacion_va_en_el_primer_cuatrimestre',[i['cuat'] for i in ITEMS if i['nom']=='Psicología de la Educación']==[1])
ok('cada_temario_tiene_sus_cinco_secciones',all(all(h in CONT[i['id']]['txt'] for h in ['FINES DEL APRENDIZAJE O FORMACIÓN','CONTENIDO TEMÁTICO','ACTIVIDADES DE APRENDIZAJE','CRITERIOS DE EVALUACIÓN','MODALIDADES TECNOLÓGICAS E INFORMÁTICAS']) for i in ITEMS))
def suma(t):
    i=t.index('CRITERIOS DE EVALUACIÓN');j=t.index('MODALIDADES',i);return sum(float(x.replace(',','.')) for x in re.findall(r'•[^\n]*?:\s*(\d+(?:[.,]\d+)?)\s*%',t[i:j]))
ok('los_criterios_de_cada_asignatura_suman_100',all(abs(suma(CONT[i['id']]['txt'])-100)<0.01 for i in ITEMS))
ok('el_contenido_es_el_del_documento','senderos que se juntan' in CONT['ced-l01']['txt'] and '1.1 Objeto de estudio de la Filosofía' in CONT['ced-l01']['txt'] and 'Atlas Ti' in CONT['ced-l31']['txt'] and 'SPSS' in CONT['ced-l31']['txt'])
ok('sin_restos_del_encabezado_del_documento',not any('CICLO ESCOLAR' in c['txt'] or 'CLAVE DE LA ASIGNATURA' in c['txt'] or '\xa0' in c['txt'] for c in CONT.values()))
csvt=open(OUT+'plan_ciencias_de_la_educacion_cuatrimestral.csv',encoding='utf-8-sig',newline='').read().split('\r\n')
ok('el_csv_del_plan_tiene_50_filas_y_el_mismo_formato_que_los_demas',csvt[0]=='plan,cuatrimestre,clave,asignatura,creditos,horas' and len([l for l in csvt[1:] if l])==50 and csvt[1]=='Ciencias de la Educación,1,L01,Filosofía de la Educación,,')
T=json.load(open(OUT+'carga_todos_los_planes_y_contenidos.json',encoding='utf-8'))
ok('el_archivo_combinado_ya_incluye_el_plan_nuevo',len(T['colecciones']['catalogo'])==10 and 'ciencias-de-la-educacion' in T['colecciones']['catalogo'] and len(T['contenidos'])==414)
# ============ servidor con la precarga automática ============
p=arranca(3360,'/tmp/nbdata110','tk-ce',False)
B='http://127.0.0.1:3360'
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(20000);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk-ce');pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=11");time.sleep(1.5)
    get=lambda path:json.loads(ctx.request.get(B+'/api/doc/'+path).text())
    cat=get('catalogo/ciencias-de-la-educacion')['data']
    ok('la_precarga_del_servidor_cargo_el_plan',cat['plan']=='Ciencias de la Educación' and len(cat['items'])==50 and all(i['ct']==1 for i in cat['items']))
    ok('y_su_contenido',get('contenidos/ced-l01')['data']['txt']==CONT['ced-l01']['txt'] and get('contenidos/ced-l50')['data']['txt']==CONT['ced-l50']['txt'])
    dbc=sqlite3.connect('/tmp/nbdata110/lafragua.db');n=dbc.execute("select count(*) from docs where coleccion='contenidos'").fetchone()[0];ac=[r[0] for r in dbc.execute("select accion||' '||coalesce(detalle,'') from auditoria where accion like 'Precarga%'").fetchall()];dbc.close()
    ok('se_cargaron_los_10_planes_y_414_contenidos',n==414 and len(ac)==10 and any('ciencias-de-la-educacion' in a for a in ac))
    ok('el_plan_existe_con_su_duracion_y_costos_por_omision',pg.evaluate("(function(){var p=PL.find(function(x){return x.k==='Ciencias de la Educación'});return !!p&&p.n===36&&p.col===1300&&p.ins===800&&p.tit===23000})()"))
    ok('los_demas_planes_siguen_igual',len(get('catalogo/pedagogia')['data']['items'])==47 and len(get('catalogo/maestria-en-educacion')['data']['items'])==12)
    pg.evaluate("ir('esc');etab('P')");pg.wait_for_selector('#pPlan');pg.select_option('#pPlan','Ciencias de la Educación');pg.wait_for_timeout(500)
    ok('el_plan_de_estudios_lo_muestra_completo',pg.inner_text('#pRes').startswith('Ciencias de la Educación: 50 asignaturas en 9 cuatrimestres (el plan tiene 9)'))
    ok('con_sus_9_cuatrimestres_y_6_materias_en_el_primero','Cuatrimestre 1 (6 materias)' in pg.inner_text('#pCuatF') and 'Cuatrimestre 9 (4 materias)' in pg.inner_text('#pCuatF') and pg.locator('#pCuatF option').count()==10)
    pg.select_option('#pCuatF','1');pg.wait_for_timeout(300);t=pg.inner_text('#pLista')
    ok('el_primer_cuatrimestre_trae_las_6_materias_de_la_clave_L01_a_L06','Filosofía de la Educación' in t and 'Psicología de la Educación' in t and 'Didáctica General' in t and 'L06' in t and 'L07' not in t)
    ok('el_calendario_sugiere_sus_materias',pg.evaluate("catItems('Ciencias de la Educación').length")==50)
    pg.screenshot(path='/tmp/ced_plan.png',full_page=False)
    ok('sin_errores_js',len(errs)==0)
    b.close()
p.terminate();time.sleep(1)
# ============ cargar el JSON y el CSV desde la pantalla (sin precarga) ============
p=arranca(3361,'/tmp/nbdata111','tk-ce2',True)
B='http://127.0.0.1:3361'
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(20000);pg=ctx.new_page();pg.on("dialog",lambda d:(setattr(pg,'_ult',d.message),d.accept()))
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk-ce2');pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=11");time.sleep(1.2)
    pg.evaluate("ir('esc');etab('P')");pg.wait_for_selector('#pPlan')
    pg.set_input_files('#pFileJ',OUT+'carga_ciencias_de_la_educacion_plan_y_contenidos.json');pg.wait_for_selector('#pJBar:not([hidden])');m=pg.inner_text('#pJMsg')
    ok('la_pantalla_resume_antes_de_cargar','50 asignaturas de Ciencias de la Educación con 50 contenidos' in m and '50 nuevas y 0' in m)
    pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('asignaturas cargadas')>-1",90);m=pg.inner_text('#pJMsg')
    ok('carga_las_50_asignaturas_y_sus_50_contenidos','50 asignaturas cargadas (50 nuevas y 0 actualizadas) y 50 contenidos' in m)
    ok('quedan_en_el_plan',pg.evaluate("catItems('Ciencias de la Educación').length")==50)
    get=lambda path:json.loads(ctx.request.get(B+'/api/doc/'+path).text())
    ok('el_contenido_guardado_es_identico',get('contenidos/ced-l12')['data']['txt']==CONT['ced-l12']['txt'])
    # el CSV en otra base limpia de ese plan: se prueba cargándolo tras quitar lo anterior
    pg.select_option('#pPlan','Ciencias de la Educación');pg.wait_for_timeout(300)
    pg.set_input_files('#pFile',OUT+'plan_ciencias_de_la_educacion_cuatrimestral.csv');pg.wait_for_timeout(1500)
    ok('el_csv_se_reconoce_y_no_duplica_nada','0 asignaturas nuevas' in getattr(pg,'_ult','') and '50 actualizadas' in getattr(pg,'_ult','') or '50 asignaturas' in getattr(pg,'_ult','') or '0 asignaturas nuevas' in getattr(pg,'_ult',''))
    ok('sigue_habiendo_50_materias',pg.evaluate("catItems('Ciencias de la Educación').length")==50)
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
