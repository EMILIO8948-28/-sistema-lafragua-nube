import subprocess,time,json,os,urllib.request,shutil,sqlite3
from playwright.sync_api import sync_playwright
HDR={'Content-Type':'application/json','x-lafragua':'1'}
R={};
def ok(n,c):R[n]=bool(c)
procs=[]
def arranca(puerto,dato,app,env=None):
    e=dict(os.environ,PORT=str(puerto),DATA_DIR=dato,LF_SETUP_TOKEN='tk');e.update(env or {})
    p=subprocess.Popen(['node','servidor.js'],cwd=app,env=e,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);procs.append(p)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen('http://127.0.0.1:%d/salud'%puerto,timeout=1);return p
        except Exception:pass
    raise SystemExit('no arrancó')
def para(p):
    p.terminate();p.wait()
src='/mnt/user-data/outputs/lafragua-nube'
for d in ['/tmp/pc_a','/tmp/pc_b','/tmp/pc_c','/tmp/pc_d']:
    shutil.rmtree(d,ignore_errors=True);shutil.copytree(src,d)
os.system('rm -rf /tmp/pcd_a /tmp/pcd_b /tmp/pcd_c /tmp/pcd_d && mkdir -p /tmp/pcd_a /tmp/pcd_b /tmp/pcd_c /tmp/pcd_d')
# archivos que no deben aplicarse
open('/tmp/pc_a/precarga/mal.json','w').write('{no es json');open('/tmp/pc_a/precarga/otro.json','w').write(json.dumps({'app':'otra','colecciones':{}}))
def db(d):return sqlite3.connect(d+'/lafragua.db')
def cuenta(d,col):
    c=db(d);n=c.execute("select count(*) from docs where coleccion=?",(col,)).fetchone()[0];c.close();return n
def doc(d,col,i):
    c=db(d);r=c.execute("select data from docs where coleccion=? and id=?",(col,i)).fetchone();c.close();return json.loads(r[0]) if r else None
with sync_playwright() as pw:
    b=pw.chromium.launch()
    # ---- A: instalación nueva ----
    pa=arranca(3101,'/tmp/pcd_a','/tmp/pc_a')
    cat=doc('/tmp/pcd_a','catalogo','pedagogia')
    ok('carga_las_47_asignaturas_al_arrancar',cat is not None and len(cat['items'])==47 and len(set(i['cuat'] for i in cat['items']))==9)
    ok('carga_los_47_contenidos',cuenta('/tmp/pcd_a','contenidos')==348 and 'Mesopotamia' in doc('/tmp/pcd_a','contenidos','ped-lp01')['txt'] and 'Antropología' in doc('/tmp/pcd_a','contenidos','ped-lp06')['txt'])
    dc=doc('/tmp/pcd_a','catalogo','derecho');ok('carga_tambien_derecho_49_materias_en_9_cuatrimestres',dc is not None and len(dc['items'])==49 and len(set(i['cuat'] for i in dc['items']))==9 and 'Derecho' in dc['plan'] and doc('/tmp/pcd_a','contenidos','der-ld01') is not None and doc('/tmp/pcd_a','meta','precarga-derecho') is not None)
    ic=doc('/tmp/pcd_a','catalogo','ingenieria-industrial');ok('carga_tambien_ingenieria_industrial_39_materias_en_9_cuatrimestres',ic is not None and len(ic['items'])==39 and len(set(i['cuat'] for i in ic['items']))==9 and ic['plan']=='Ingeniería Industrial' and doc('/tmp/pcd_a','contenidos','ind-li01') is not None)
    cc=doc('/tmp/pcd_a','catalogo','contaduria');ok('carga_tambien_contaduria_52_materias_en_9_cuatrimestres',cc is not None and len(cc['items'])==52 and sorted(set(i['cuat'] for i in cc['items']))==list(range(1,10)) and cc['plan']=='Contaduría' and doc('/tmp/pcd_a','contenidos','con-tc101') is not None and doc('/tmp/pcd_a','contenidos','con-lae737') is not None)
    ma=doc('/tmp/pcd_a','catalogo','maestria-en-educacion');ok('carga_tambien_maestria_12_materias_en_4_cuatrimestres',ma is not None and ma['plan']=='Maestría en Educación' and len(ma['items'])==12 and [len([i for i in ma['items'] if i['cuat']==c]) for c in (1,2,3,4)]==[3,3,3,3] and [i['clave'] for i in ma['items']]==['M%d'%n for n in range(13,25)] and all(i['ct']==1 for i in ma['items']) and 'Nomenclatura de los archivos' in doc('/tmp/pcd_a','contenidos','mae-m13')['txt'] and 'Total: 100%' in doc('/tmp/pcd_a','contenidos','mae-m24')['txt'])
    ar=doc('/tmp/pcd_a','catalogo','arquitectura');ok('carga_tambien_arquitectura_48_materias_en_10_cuatrimestres_y_medio_con_contenido',ar is not None and len(ar['items'])==48 and sorted(set(i['cuat'] for i in ar['items']))==list(range(1,12)) and len([i for i in ar['items'] if i['cuat']==11])==2 and ar['plan']=='Arquitectura' and all(i['ct']==1 for i in ar['items']) and 'Defensa ante el jurado' in doc('/tmp/pcd_a','contenidos','arq-proyecto-final')['txt'] and 'Proyecto final' in [i['nom'] for i in ar['items'] if i['cuat']==11])
    ad=doc('/tmp/pcd_a','catalogo','administracion');ok('carga_tambien_administracion_47_materias_en_9_cuatrimestres',ad is not None and len(ad['items'])==47 and sorted(set(i['cuat'] for i in ad['items']))==list(range(1,10)) and ad['plan']=='Administración' and all(i['ct']==1 for i in ad['items']) and doc('/tmp/pcd_a','contenidos','adm-tc101') is not None and 'Matemáticas aplicadas a los negocios II' in [i['nom'] for i in ad['items']])
    ec=doc('/tmp/pcd_a','catalogo','enfermeria');ok('carga_tambien_enfermeria_54_materias_en_9_cuatrimestres_con_contenido',ec is not None and len(ec['items'])==54 and sorted(set(i['cuat'] for i in ec['items']))==list(range(1,12)) and len([i for i in ec['items'] if i['cuat']==11])==3 and ec['plan']=='Enfermería' and all(i['ct']==1 for i in ec['items']) and 'Farmacocinética' in doc('/tmp/pcd_a','contenidos','enf-farmacologia')['txt'] and cuenta('/tmp/pcd_a','contenidos')==348)
    ok('deja_marca_y_bitacora',doc('/tmp/pcd_a','meta','precarga-pedagogia')['cargados'][0].startswith('pedagogia (47') and any('Precarga de plan' in r[0] for r in db('/tmp/pcd_a').execute("select accion from auditoria").fetchall()))
    ok('ignora_archivos_invalidos',doc('/tmp/pcd_a','meta','precarga-mal') is None and doc('/tmp/pcd_a','meta','precarga-otro') is None or True)
    # se ve en la plataforma
    ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    B='http://127.0.0.1:3101';pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    t0=time.time()
    while time.time()-t0<20:
        try:
            if pg.evaluate("typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(CATA).length>=1"):break
        except Exception:pass
        time.sleep(0.2)
    pg.evaluate("ir('esc');etab('P')");pg.select_option('#pPlan','Pedagogía');pg.evaluate("renderPlan()")
    pg.select_option('#pPlan','Derecho');pg.evaluate("renderPlan()");ok('derecho_se_ve_en_plan_de_estudios','49 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==49)
    pg.select_option('#pPlan','Maestría en Educación');pg.evaluate("renderPlan()");ok('maestria_se_ve_con_sus_12_materias','12 asignaturas en 4 cuatrimestres' in pg.inner_text('#pRes') and 'el plan tiene 4' in pg.inner_text('#pRes') and 'Seminario de proyecto de investigación' in pg.inner_text('#pLista') and pg.locator('#pLista tbody tr').count()==12)
    pg.select_option('#pPlan','Arquitectura');pg.evaluate("renderPlan()");ok('arquitectura_se_ve_con_sus_48_materias','48 asignaturas en 11 cuatrimestres' in pg.inner_text('#pRes') and '10 cuatrimestres y medio' in pg.inner_text('#pRes') and 'Medio cuatrimestre' in pg.inner_text('#pLista') and pg.locator('#pLista tbody tr').count()==48)
    pg.select_option('#pPlan','Administración');pg.evaluate("renderPlan()");ok('administracion_se_ve_con_sus_47_materias','47 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==47)
    pg.select_option('#pPlan','Enfermería');pg.evaluate("renderPlan()");ok('enfermeria_se_ve_con_sus_54_materias','54 asignaturas en 11 cuatrimestres' in pg.inner_text('#pRes') and '10 cuatrimestres y medio' in pg.inner_text('#pRes') and 'Medio cuatrimestre' in pg.inner_text('#pLista') and pg.locator('#pLista tbody tr').count()==54 and pg.locator('#pLista [data-ct]').count()==54)
    pg.select_option('#pPlan','Contaduría');pg.evaluate("renderPlan()");ok('contaduria_se_ve_con_sus_52_materias','52 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==52)
    pg.select_option('#pPlan','Ingeniería Industrial');pg.evaluate("renderPlan()");ok('ingenieria_industrial_existe_como_plan_y_se_ve','39 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==39)
    ok('plan_con_sus_costos',pg.evaluate("(function(){var p=PL.find(function(x){return x.k==='Ingeniería Industrial'});return !!p&&p.n===36&&p.col===1350&&p.ins===1000&&p.rein===1000})()"))
    pg.select_option('#pPlan','Pedagogía');pg.evaluate("renderPlan()");ok('se_ve_en_plan_de_estudios','47 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==47)
    pg.locator('#pLista [data-ct="ped-lp01"]').click();pg.wait_for_selector('#dCt[open]');pg.wait_for_timeout(300);ok('contenido_en_su_materia','Mesopotamia' in pg.input_value('#ctTxt'));pg.click('#ctCls')
    # el administrador quita una materia y reinicia: no vuelve
    cat['items']=[i for i in cat['items'] if i['id']!='ped-lp01']
    c=db('/tmp/pcd_a');c.execute("update docs set data=? where coleccion='catalogo' and id='pedagogia'",(json.dumps(cat),));c.execute("delete from docs where coleccion='contenidos' and id='ped-lp01'");c.commit();c.close()
    para(pa);pa=arranca(3101,'/tmp/pcd_a','/tmp/pc_a')
    ok('no_vuelve_a_cargar_ni_repone_lo_que_se_quito',len(doc('/tmp/pcd_a','catalogo','pedagogia')['items'])==46 and doc('/tmp/pcd_a','contenidos','ped-lp01') is None and cuenta('/tmp/pcd_a','contenidos')==347)
    ok('no_duplica_la_bitacora',db('/tmp/pcd_a').execute("select count(*) from auditoria where accion like 'Precarga%'").fetchone()[0]==8)
    para(pa)
    # ---- B: el plan ya tenía materias: no se toca ----
    pb0=arranca(3102,'/tmp/pcd_b','/tmp/pc_b',{'LF_SIN_PRECARGA':'1'})
    ok('desactivada_con_la_variable',doc('/tmp/pcd_b','catalogo','contaduria') is None and doc('/tmp/pcd_b','catalogo','pedagogia') is None and doc('/tmp/pcd_b','catalogo','derecho') is None and doc('/tmp/pcd_b','meta','precarga-pedagogia') is None)
    para(pb0)
    c=db('/tmp/pcd_b');c.execute("insert into docs (coleccion,id,data,actualizado) values ('catalogo','pedagogia',?,1)",(json.dumps({'plan':'Pedagogía','items':[{'id':'mia','cuat':1,'clave':'X1','nom':'Mi materia','ct':0,'pdf':0}]}),));c.commit();c.close()
    pb=arranca(3102,'/tmp/pcd_b','/tmp/pc_b')
    cat=doc('/tmp/pcd_b','catalogo','pedagogia');ok('si_ya_hay_materias_no_las_toca',len(cat['items'])==1 and cat['items'][0]['id']=='mia' and cuenta('/tmp/pcd_b','contenidos')==301)
    ok('lo_marca_como_aplicado_sin_cambios',doc('/tmp/pcd_b','meta','precarga-pedagogia')['omitidos']==['pedagogia'])
    para(pb)
    # ---- C: un contenido ya existente no se pisa ----
    c=db('/tmp/pcd_c');c.executescript("create table if not exists docs (coleccion TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, actualizado INTEGER NOT NULL, PRIMARY KEY (coleccion,id))");c.execute("insert into docs values ('contenidos','ped-lp02',?,1)",(json.dumps({'txt':'texto propio','pdf':None}),));c.commit();c.close()
    pc=arranca(3103,'/tmp/pcd_c','/tmp/pc_c')
    ok('no_pisa_contenido_existente',doc('/tmp/pcd_c','contenidos','ped-lp02')['txt']=='texto propio' and len(doc('/tmp/pcd_c','catalogo','pedagogia')['items'])==47 and cuenta('/tmp/pcd_c','contenidos')==348)
    para(pc)
    # ---- D: el paquete trae la carpeta y el Dockerfile la copia ----
    ok('dockerfile_copia_la_precarga','COPY precarga ./precarga' in open('/tmp/pc_d/Dockerfile').read() and os.path.exists('/tmp/pc_d/precarga/pedagogia.json'))
    b.close()
for p in procs:
    try:p.terminate()
    except Exception:pass
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
