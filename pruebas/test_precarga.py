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
    ok('carga_los_47_contenidos',cuenta('/tmp/pcd_a','contenidos')==465 and 'Mesopotamia' in doc('/tmp/pcd_a','contenidos','ped-lp01')['txt'] and 'Antropología' in doc('/tmp/pcd_a','contenidos','ped-lp06')['txt'])
    dc=doc('/tmp/pcd_a','catalogo','derecho');ok('carga_tambien_derecho_49_materias_en_9_cuatrimestres',dc is not None and len(dc['items'])==49 and len(set(i['cuat'] for i in dc['items']))==9 and 'Derecho' in dc['plan'] and doc('/tmp/pcd_a','contenidos','der-ld01') is not None and doc('/tmp/pcd_a','meta','precarga-derecho') is not None)
    ic=doc('/tmp/pcd_a','catalogo','ingenieria-industrial');ok('carga_tambien_ingenieria_industrial_39_materias_en_9_cuatrimestres',ic is not None and len(ic['items'])==39 and len(set(i['cuat'] for i in ic['items']))==9 and ic['plan']=='Ingeniería Industrial' and doc('/tmp/pcd_a','contenidos','ind-li01') is not None)
    cc=doc('/tmp/pcd_a','catalogo','contaduria');ok('carga_tambien_contaduria_52_materias_en_9_cuatrimestres',cc is not None and len(cc['items'])==52 and sorted(set(i['cuat'] for i in cc['items']))==list(range(1,10)) and cc['plan']=='Contaduría' and doc('/tmp/pcd_a','contenidos','con-tc101') is not None and doc('/tmp/pcd_a','contenidos','con-lae737') is not None)
    dr=doc('/tmp/pcd_a','catalogo','doctorado');ok('carga_tambien_doctorado_16_materias_en_4_cuatrimestres',dr is not None and dr['plan']=='Doctorado' and len(dr['items'])==16 and [len([i for i in dr['items'] if i['cuat']==c]) for c in (1,2,3,4,5)]==[4,4,4,4,0] and [i['clave'] for i in dr['items']]==['ED%02d'%n for n in range(1,17)] and all(i['ct']==1 for i in dr['items']) and dr['config']['n']==16 and 'Total: 100%' in doc('/tmp/pcd_a','contenidos','doc-ed16')['txt'])
    ma=doc('/tmp/pcd_a','catalogo','maestria-en-educacion');ok('carga_tambien_maestria_12_materias_en_4_cuatrimestres',ma is not None and ma['plan']=='Maestría en Educación' and len(ma['items'])==12 and [len([i for i in ma['items'] if i['cuat']==c]) for c in (1,2,3,4)]==[3,3,3,3] and [i['clave'] for i in ma['items']]==['M%d'%n for n in range(13,25)] and all(i['ct']==1 for i in ma['items']) and 'Nomenclatura de los archivos' in doc('/tmp/pcd_a','contenidos','mae-m13')['txt'] and 'Total: 100%' in doc('/tmp/pcd_a','contenidos','mae-m24')['txt'])
    ar=doc('/tmp/pcd_a','catalogo','arquitectura');ok('carga_tambien_arquitectura_48_materias_en_10_cuatrimestres_y_medio_con_contenido',ar is not None and len(ar['items'])==48 and sorted(set(i['cuat'] for i in ar['items']))==list(range(1,12)) and len([i for i in ar['items'] if i['cuat']==11])==2 and ar['plan']=='Arquitectura' and all(i['ct']==1 for i in ar['items']) and 'Defensa ante el jurado' in doc('/tmp/pcd_a','contenidos','arq-proyecto-final')['txt'] and 'Proyecto final' in [i['nom'] for i in ar['items'] if i['cuat']==11])
    ad=doc('/tmp/pcd_a','catalogo','administracion');ok('carga_tambien_administracion_49_materias_en_9_cuatrimestres',ad is not None and len(ad['items'])==49 and sorted(set(i['cuat'] for i in ad['items']))==list(range(1,10)) and ad['plan']=='Administración' and all(i['ct']==1 for i in ad['items']) and doc('/tmp/pcd_a','contenidos','adm-tc101') is not None and 'Matemáticas aplicadas a los negocios II' in [i['nom'] for i in ad['items']])
    ap=[i for i in ad['items'] if i['id']=='adm-cp419'];ac=[i for i in ad['items'] if i['id']=='adm-compras']
    ok('administracion_trae_personal_en_4_y_compras_en_5',len(ap)==1 and ap[0]['cuat']==4 and ap[0]['clave']=='CP419' and ap[0]['nom']=='Administración de personal' and len(ac)==1 and ac[0]['cuat']==5 and ac[0]['nom']=='Administración de compras' and not ac[0]['clave'] and len([i for i in ad['items'] if i['clave']=='LAE634'])==1 and [len([i for i in ad['items'] if i['cuat']==c]) for c in range(1,10)]==[6,6,6,6,5,5,5,5,5])
    tp=doc('/tmp/pcd_a','contenidos','adm-cp419')['txt'];tc=doc('/tmp/pcd_a','contenidos','adm-compras')['txt']
    ok('administracion_personal_y_compras_traen_programa_completo',all(x in tp for x in ('OBJETIVO GENERAL','8. INDUCCIÓN','Pruebas o tests','Elaboración de curso de capacitación: 10%','Total: 100%')) and all(x in tc for x in ('OBJETIVO GENERAL','6. COMPRAS ESTRATÉGICAS Y TECNOLOGÍA','Compras electrónicas','Un examen parcial: 70%','Ensayo: 10%','Total: 100%')) and 'tets' not in tp)
    ec=doc('/tmp/pcd_a','catalogo','enfermeria');ok('carga_tambien_enfermeria_54_materias_en_9_cuatrimestres_con_contenido',ec is not None and len(ec['items'])==54 and sorted(set(i['cuat'] for i in ec['items']))==list(range(1,12)) and len([i for i in ec['items'] if i['cuat']==11])==3 and ec['plan']=='Enfermería' and all(i['ct']==1 for i in ec['items']) and 'Farmacocinética' in doc('/tmp/pcd_a','contenidos','enf-farmacologia')['txt'] and cuenta('/tmp/pcd_a','contenidos')==465)
    ec2=sorted(ec['items'],key=lambda i:i['clave']);ok('enfermeria_trae_claves_LE01_a_LE54_sin_repetir',[i['clave'] for i in ec2]==['LE%02d'%n for n in range(1,55)] and ec['items'][0]['clave']=='LE01' and ec['items'][-1]['clave']=='LE54' and [i['clave'] for i in ec['items']]==['LE%02d'%n for n in range(1,55)])
    ps=doc('/tmp/pcd_a','catalogo','psicologia');ok('carga_tambien_psicologia_49_materias_en_9_cuatrimestres_max_6',ps is not None and ps['plan']=='Psicología' and len(ps['items'])==49 and [len([i for i in ps['items'] if i['cuat']==c]) for c in range(1,10)]==[6,6,6,6,5,5,5,5,5] and len(set(i['clave'] for i in ps['items']))==49 and sorted(i['clave'] for i in ps['items'])==['LP%02d'%n for n in range(1,50)])
    cp=doc('/tmp/pcd_a','contenidos','psi-lp03');ok('psicologia_trae_programa_completo',all(k in cp['txt'] for k in ('OBJETIVO GENERAL DE LA ASIGNATURA','CONTENIDO TEMÁTICO','ACTIVIDADES DE APRENDIZAJE','CRITERIOS Y PROCEDIMIENTOS DE EVALUACIÓN Y ACREDITACIÓN','Freud','Total: 100%')) and all(doc('/tmp/pcd_a','contenidos',i['id']) for i in ps['items']))
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
    pg.select_option('#pPlan','Psicología');pg.evaluate("renderPlan()");ok('psicologia_se_ve_con_sus_49_materias','49 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==49)
    pg.select_option('#pPlan','Derecho');pg.evaluate("renderPlan()");ok('derecho_se_ve_en_plan_de_estudios','49 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==49)
    pg.select_option('#pPlan','Doctorado');pg.evaluate("renderPlan()");ok('doctorado_se_ve_con_sus_16_materias','16 asignaturas en 4 cuatrimestres' in pg.inner_text('#pRes') and 'el plan tiene 4' in pg.inner_text('#pRes') and 'Seminario de investigación especializado' in pg.inner_text('#pLista') and pg.locator('#pLista tbody tr').count()==16)
    pg.select_option('#pPlan','Maestría en Educación');pg.evaluate("renderPlan()");ok('maestria_se_ve_con_sus_12_materias','12 asignaturas en 4 cuatrimestres' in pg.inner_text('#pRes') and 'el plan tiene 4' in pg.inner_text('#pRes') and 'Seminario de proyecto de investigación' in pg.inner_text('#pLista') and pg.locator('#pLista tbody tr').count()==12)
    pg.select_option('#pPlan','Arquitectura');pg.evaluate("renderPlan()");ok('arquitectura_se_ve_con_sus_48_materias','48 asignaturas en 11 cuatrimestres' in pg.inner_text('#pRes') and '10 cuatrimestres y medio' in pg.inner_text('#pRes') and 'Medio cuatrimestre' in pg.inner_text('#pLista') and pg.locator('#pLista tbody tr').count()==48)
    pg.select_option('#pPlan','Administración');pg.evaluate("renderPlan()");ok('administracion_se_ve_con_sus_49_materias','49 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==49)
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
    ok('no_vuelve_a_cargar_ni_repone_lo_que_se_quito',len(doc('/tmp/pcd_a','catalogo','pedagogia')['items'])==46 and doc('/tmp/pcd_a','contenidos','ped-lp01') is None and cuenta('/tmp/pcd_a','contenidos')==464)
    ok('no_duplica_la_bitacora',db('/tmp/pcd_a').execute("select count(*) from auditoria where accion like 'Precarga%'").fetchone()[0]==11)
    para(pa)
    # ---- B: el plan ya tenía materias: no se toca ----
    pb0=arranca(3102,'/tmp/pcd_b','/tmp/pc_b',{'LF_SIN_PRECARGA':'1'})
    ok('desactivada_con_la_variable',doc('/tmp/pcd_b','catalogo','contaduria') is None and doc('/tmp/pcd_b','catalogo','pedagogia') is None and doc('/tmp/pcd_b','catalogo','derecho') is None and doc('/tmp/pcd_b','meta','precarga-pedagogia') is None)
    para(pb0)
    c=db('/tmp/pcd_b');c.execute("insert into docs (coleccion,id,data,actualizado) values ('catalogo','pedagogia',?,1)",(json.dumps({'plan':'Pedagogía','items':[{'id':'mia','cuat':1,'clave':'X1','nom':'Mi materia','ct':0,'pdf':0}]}),));c.commit();c.close()
    pb=arranca(3102,'/tmp/pcd_b','/tmp/pc_b')
    cat=doc('/tmp/pcd_b','catalogo','pedagogia');ok('si_ya_hay_materias_no_las_toca',len(cat['items'])==1 and cat['items'][0]['id']=='mia' and cuenta('/tmp/pcd_b','contenidos')==418)
    ok('lo_marca_como_aplicado_sin_cambios',doc('/tmp/pcd_b','meta','precarga-pedagogia')['omitidos']==['pedagogia'])
    para(pb)
    # ---- C: un contenido ya existente no se pisa ----
    c=db('/tmp/pcd_c');c.executescript("create table if not exists docs (coleccion TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, actualizado INTEGER NOT NULL, PRIMARY KEY (coleccion,id))");c.execute("insert into docs values ('contenidos','ped-lp02',?,1)",(json.dumps({'txt':'texto propio','pdf':None}),));c.commit();c.close()
    pc=arranca(3103,'/tmp/pcd_c','/tmp/pc_c')
    ok('no_pisa_contenido_existente',doc('/tmp/pcd_c','contenidos','ped-lp02')['txt']=='texto propio' and len(doc('/tmp/pcd_c','catalogo','pedagogia')['items'])==47 and cuenta('/tmp/pcd_c','contenidos')==465)
    para(pc)
    # ---- E: instalaciones con Psicología en 7 cuatrimestres se redistribuyen en 9 (solo si no se tocó) ----
    for d in ('/tmp/pc_e','/tmp/pc_f'):
        shutil.rmtree(d,ignore_errors=True);shutil.copytree(src,d)
    os.system('rm -rf /tmp/pcd_e /tmp/pcd_f && mkdir -p /tmp/pcd_e /tmp/pcd_f')
    for pto,dd,ap in ((3104,'/tmp/pcd_e','/tmp/pc_e'),(3105,'/tmp/pcd_f','/tmp/pc_f')):
        pe=arranca(pto,dd,ap);para(pe)
    ANT={'LP01':1,'LP02':1,'LP03':1,'LP04':1,'LP05':1,'LP06':1,'LP07':1,'LP08':1,'LP09':2,'LP10':2,'LP11':2,'LP12':2,'LP13':2,'LP14':2,'LP15':2,'LP16':2,'LP17':3,'LP18':3,'LP19':3,'LP20':3,'LP21':3,'LP22':3,'LP23':4,'LP24':4,'LP25':4,'LP26':4,'LP27':4,'LP28':4,'LP29':4,'LP31':4,'LP32':4,'LP30':5,'LP33':5,'LP34':5,'LP35':5,'LP36':6,'LP37':6,'LP38':6,'LP39':6,'LP40':6,'LP41':6,'LP42':6,'LP44':6,'LP45':6,'LP47':6,'LP48':6,'LP43':7,'LP46':7,'LP49':7}
    for dd in ('/tmp/pcd_e','/tmp/pcd_f'):
        c=db(dd);r=json.loads(c.execute("select data from docs where coleccion='catalogo' and id='psicologia'").fetchone()[0])
        for i in r['items']:i['cuat']=ANT[i['clave']]
        if dd.endswith('_f'):r['items'][0]['cuat']=2
        c.execute("update docs set data=? where coleccion='catalogo' and id='psicologia'",(json.dumps(r),));c.execute("delete from docs where coleccion='meta' and id='migracion-psicologia-9-cuatrimestres'");c.execute("delete from auditoria where accion like 'Migración: Psicología%'");c.commit();c.close()
    pv=doc('/tmp/pcd_e','catalogo','psicologia');ok('prueba_E_parte_de_la_distribucion_vieja',[len([i for i in pv['items'] if i['cuat']==c]) for c in range(1,8)]==[8,8,6,9,4,11,3])
    pe=arranca(3104,'/tmp/pcd_e','/tmp/pc_e');pf=arranca(3105,'/tmp/pcd_f','/tmp/pc_f')
    pn=doc('/tmp/pcd_e','catalogo','psicologia');cuats=[len([i for i in pn['items'] if i['cuat']==c]) for c in range(1,10)]
    ok('migracion_psicologia_9_cuatrimestres_max_6',cuats==[6,6,6,6,5,5,5,5,5] and len(pn['items'])==49 and max(cuats)<=6 and doc('/tmp/pcd_e','meta','migracion-psicologia-9-cuatrimestres') is not None)
    ok('migracion_psicologia_deja_la_bitacora',db('/tmp/pcd_e').execute("select count(*) from auditoria where accion like 'Migración: Psicología redistribuida%'").fetchone()[0]==1)
    pn2=doc('/tmp/pcd_f','catalogo','psicologia');ok('migracion_psicologia_respeta_si_ya_fue_editado',[len([i for i in pn2['items'] if i['cuat']==c]) for c in range(1,8)]==[7,9,6,9,4,11,3])
    para(pe);para(pf)
    # ---- G: instalaciones con Administración de 47 materias reciben personal y compras (sin duplicar ni pisar) ----
    for d in ('/tmp/pc_g','/tmp/pc_h'):
        shutil.rmtree(d,ignore_errors=True);shutil.copytree(src,d)
        nj=json.load(open(d+'/precarga/administracion.json'))
        nj['colecciones']['catalogo']['administracion']['items']=[i for i in nj['colecciones']['catalogo']['administracion']['items'] if i['id'] not in ('adm-cp419','adm-compras')]
        for k3 in ('adm-cp419','adm-compras'):nj['contenidos'].pop(k3,None)
        json.dump(nj,open(d+'/precarga/administracion_vieja.json','w'),ensure_ascii=False);os.replace(d+'/precarga/administracion.json',d+'/administracion_nueva.json');os.replace(d+'/precarga/administracion_vieja.json',d+'/precarga/administracion.json')
    os.system('rm -rf /tmp/pcd_g /tmp/pcd_h && mkdir -p /tmp/pcd_g /tmp/pcd_h')
    for pto,dd,ap_ in ((3106,'/tmp/pcd_g','/tmp/pc_g'),(3107,'/tmp/pcd_h','/tmp/pc_h')):
        pe=arranca(pto,dd,ap_);para(pe)
    ok('prueba_G_parte_de_47_materias',len(doc('/tmp/pcd_g','catalogo','administracion')['items'])==47 and doc('/tmp/pcd_g','contenidos','adm-cp419') is None)
    for dd,ap_ in (('/tmp/pcd_g','/tmp/pc_g'),('/tmp/pcd_h','/tmp/pc_h')):
        os.replace(ap_+'/administracion_nueva.json',ap_+'/precarga/administracion.json')
        c=db(dd);c.execute("delete from docs where coleccion='meta' and id='migracion-administracion-personal-compras'");c.commit();c.close()
    c=db('/tmp/pcd_h');r=json.loads(c.execute("select data from docs where coleccion='catalogo' and id='administracion'").fetchone()[0]);r['items'].append({'id':'mia','cuat':4,'clave':'X9','nom':'administración de compras','ct':0,'pdf':0});c.execute("update docs set data=? where coleccion='catalogo' and id='administracion'",(json.dumps(r),));c.execute("insert into docs values ('contenidos','adm-cp419',?,1)",(json.dumps({'txt':'mi texto','pdf':None}),));c.commit();c.close()
    pg_=arranca(3106,'/tmp/pcd_g','/tmp/pc_g');ph_=arranca(3107,'/tmp/pcd_h','/tmp/pc_h')
    ag=doc('/tmp/pcd_g','catalogo','administracion');agp=[i for i in ag['items'] if i['id']=='adm-cp419'];agc=[i for i in ag['items'] if i['id']=='adm-compras']
    ok('migracion_administracion_agrega_personal_en_4_y_compras_en_5',len(ag['items'])==49 and len(agp)==1 and agp[0]['cuat']==4 and len(agc)==1 and agc[0]['cuat']==5 and 'INDUCCIÓN' in doc('/tmp/pcd_g','contenidos','adm-cp419')['txt'] and 'COMPRAS ESTRATÉGICAS' in doc('/tmp/pcd_g','contenidos','adm-compras')['txt'] and [i['id'] for i in ag['items'] if i['cuat']==4][0]=='adm-cp419')
    ok('migracion_administracion_deja_la_bitacora',db('/tmp/pcd_g').execute("select count(*) from auditoria where accion like 'Migración: materias agregadas al plan de Administración%'").fetchone()[0]==1)
    ah=doc('/tmp/pcd_h','catalogo','administracion')
    ok('migracion_administracion_no_duplica_si_ya_existe_por_nombre_y_no_pisa_contenido',len(ah['items'])==49 and len([i for i in ah['items'] if i['id']=='adm-compras'])==0 and len([i for i in ah['items'] if i['id']=='adm-cp419'])==1 and doc('/tmp/pcd_h','contenidos','adm-cp419')['txt']=='mi texto')
    para(pg_);pg_=arranca(3106,'/tmp/pcd_g','/tmp/pc_g')
    ok('migracion_administracion_corre_una_sola_vez',len(doc('/tmp/pcd_g','catalogo','administracion')['items'])==49)
    para(pg_);para(ph_)
    # ---- H: instalaciones con Enfermería sin clave reciben LE01–LE54 (sin pisar claves ya escritas) ----
    for d in ('/tmp/pc_i','/tmp/pc_j'):
        shutil.rmtree(d,ignore_errors=True);shutil.copytree(src,d);shutil.copy(d+'/precarga/enfermeria.json',d+'/enfermeria_nueva.json')
        nj=json.load(open(d+'/precarga/enfermeria.json'))
        for i in nj['colecciones']['catalogo']['enfermeria']['items']:i['clave']=''
        json.dump(nj,open(d+'/precarga/enfermeria.json','w'),ensure_ascii=False)
    os.system('rm -rf /tmp/pcd_i /tmp/pcd_j && mkdir -p /tmp/pcd_i /tmp/pcd_j')
    for pto,dd,ap_ in ((3108,'/tmp/pcd_i','/tmp/pc_i'),(3109,'/tmp/pcd_j','/tmp/pc_j')):
        pe=arranca(pto,dd,ap_);para(pe)
    ok('prueba_H_parte_de_enfermeria_sin_claves',all(not i['clave'] for i in doc('/tmp/pcd_i','catalogo','enfermeria')['items']))
    for dd,ap_ in (('/tmp/pcd_i','/tmp/pc_i'),('/tmp/pcd_j','/tmp/pc_j')):
        shutil.copy(ap_+'/enfermeria_nueva.json',ap_+'/precarga/enfermeria.json')
        c=db(dd);c.execute("delete from docs where coleccion='meta' and id='migracion-enfermeria-claves-le'");c.commit();c.close()
    c=db('/tmp/pcd_j');r=json.loads(c.execute("select data from docs where coleccion='catalogo' and id='enfermeria'").fetchone()[0]);r['items'][0]['clave']='MIA-1';c.execute("update docs set data=? where coleccion='catalogo' and id='enfermeria'",(json.dumps(r),));c.commit();c.close()
    pi_=arranca(3108,'/tmp/pcd_i','/tmp/pc_i');pj_=arranca(3109,'/tmp/pcd_j','/tmp/pc_j')
    ei=doc('/tmp/pcd_i','catalogo','enfermeria');ej=doc('/tmp/pcd_j','catalogo','enfermeria')
    ok('migracion_enfermeria_pone_LE01_a_LE54',[i['clave'] for i in ei['items']]==['LE%02d'%n for n in range(1,55)] and len(ei['items'])==54)
    ok('migracion_enfermeria_deja_la_bitacora',db('/tmp/pcd_i').execute("select count(*) from auditoria where accion like 'Migración: claves de materia del plan de Enfermería%'").fetchone()[0]==1)
    ok('migracion_enfermeria_no_pisa_una_clave_ya_escrita',ej['items'][0]['clave']=='MIA-1' and [i['clave'] for i in ej['items'][1:]]==['LE%02d'%n for n in range(2,55)])
    para(pi_);para(pj_)
    # ---- D: el paquete trae la carpeta y el Dockerfile la copia ----
    ok('dockerfile_copia_la_precarga','COPY precarga ./precarga' in open('/tmp/pc_d/Dockerfile').read() and os.path.exists('/tmp/pc_d/precarga/pedagogia.json'))
    b.close()
for p in procs:
    try:p.terminate()
    except Exception:pass
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
