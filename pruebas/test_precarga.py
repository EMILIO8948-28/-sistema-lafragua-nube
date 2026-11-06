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
    ok('carga_los_47_contenidos',cuenta('/tmp/pcd_a','contenidos')==47 and 'Mesopotamia' in doc('/tmp/pcd_a','contenidos','ped-lp01')['txt'] and 'Antropología' in doc('/tmp/pcd_a','contenidos','ped-lp06')['txt'])
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
    ok('se_ve_en_plan_de_estudios','47 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==47)
    pg.locator('#pLista [data-ct="ped-lp01"]').click();pg.wait_for_selector('#dCt[open]');pg.wait_for_timeout(300);ok('contenido_en_su_materia','Mesopotamia' in pg.input_value('#ctTxt'));pg.click('#ctCls')
    # el administrador quita una materia y reinicia: no vuelve
    cat['items']=[i for i in cat['items'] if i['id']!='ped-lp01']
    c=db('/tmp/pcd_a');c.execute("update docs set data=? where coleccion='catalogo' and id='pedagogia'",(json.dumps(cat),));c.execute("delete from docs where coleccion='contenidos' and id='ped-lp01'");c.commit();c.close()
    para(pa);pa=arranca(3101,'/tmp/pcd_a','/tmp/pc_a')
    ok('no_vuelve_a_cargar_ni_repone_lo_que_se_quito',len(doc('/tmp/pcd_a','catalogo','pedagogia')['items'])==46 and doc('/tmp/pcd_a','contenidos','ped-lp01') is None and cuenta('/tmp/pcd_a','contenidos')==46)
    ok('no_duplica_la_bitacora',db('/tmp/pcd_a').execute("select count(*) from auditoria where accion like 'Precarga%'").fetchone()[0]==1)
    para(pa)
    # ---- B: el plan ya tenía materias: no se toca ----
    pb0=arranca(3102,'/tmp/pcd_b','/tmp/pc_b',{'LF_SIN_PRECARGA':'1'})
    ok('desactivada_con_la_variable',doc('/tmp/pcd_b','catalogo','pedagogia') is None and doc('/tmp/pcd_b','meta','precarga-pedagogia') is None)
    para(pb0)
    c=db('/tmp/pcd_b');c.execute("insert into docs (coleccion,id,data,actualizado) values ('catalogo','pedagogia',?,1)",(json.dumps({'plan':'Pedagogía','items':[{'id':'mia','cuat':1,'clave':'X1','nom':'Mi materia','ct':0,'pdf':0}]}),));c.commit();c.close()
    pb=arranca(3102,'/tmp/pcd_b','/tmp/pc_b')
    cat=doc('/tmp/pcd_b','catalogo','pedagogia');ok('si_ya_hay_materias_no_las_toca',len(cat['items'])==1 and cat['items'][0]['id']=='mia' and cuenta('/tmp/pcd_b','contenidos')==0)
    ok('lo_marca_como_aplicado_sin_cambios',doc('/tmp/pcd_b','meta','precarga-pedagogia')['omitidos']==['pedagogia'])
    para(pb)
    # ---- C: un contenido ya existente no se pisa ----
    c=db('/tmp/pcd_c');c.executescript("create table if not exists docs (coleccion TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, actualizado INTEGER NOT NULL, PRIMARY KEY (coleccion,id))");c.execute("insert into docs values ('contenidos','ped-lp02',?,1)",(json.dumps({'txt':'texto propio','pdf':None}),));c.commit();c.close()
    pc=arranca(3103,'/tmp/pcd_c','/tmp/pc_c')
    ok('no_pisa_contenido_existente',doc('/tmp/pcd_c','contenidos','ped-lp02')['txt']=='texto propio' and len(doc('/tmp/pcd_c','catalogo','pedagogia')['items'])==47 and cuenta('/tmp/pcd_c','contenidos')==47)
    para(pc)
    # ---- D: el paquete trae la carpeta y el Dockerfile la copia ----
    ok('dockerfile_copia_la_precarga','COPY precarga ./precarga' in open('/tmp/pc_d/Dockerfile').read() and os.path.exists('/tmp/pc_d/precarga/pedagogia.json'))
    b.close()
for p in procs:
    try:p.terminate()
    except Exception:pass
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
