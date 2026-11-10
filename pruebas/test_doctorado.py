import subprocess,time,json,os,urllib.request,sqlite3
from playwright.sync_api import sync_playwright
TOK='tok-do-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
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
def arranca(port,datos,precarga):
    env=dict(os.environ,PORT=str(port),DATA_DIR=datos,LF_SETUP_TOKEN=TOK)
    if not precarga:env['LF_SIN_PRECARGA']='1'
    p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen('http://127.0.0.1:%d/salud'%port,timeout=1);break
        except Exception:pass
    return p
def plan_db(datos):
    c=sqlite3.connect(datos+'/lafragua.db');r=c.execute("select data from docs where coleccion='config' and id='plans'").fetchone();c.close()
    return {x['k']:x for x in json.loads(r[0])['plans']} if r else None
def admin(pw,B):
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0);return b,ctx,pg
def planes(ctx,B):return {x['k']:x for x in ctx.request.get(B+'/api/doc/config/plans').json()['data']['plans']}
os.system('rm -rf /tmp/alm60 /tmp/alm61 /tmp/alm62 && mkdir -p /tmp/alm60 /tmp/alm61 /tmp/alm62')
with sync_playwright() as pw:
    # ============ 1. cargar el archivo desde el botón (plan sin duración) ============
    B='http://127.0.0.1:3141';p=arranca(3141,'/tmp/alm60',False);b,ctx,pg=admin(pw,B)
    ok('el_plan_nuevo_por_defecto_dura_5_cuatrimestres',planes(ctx,B)['Doctorado']['n']==20)
    pl=planes(ctx,B);pl['Doctorado']['n']=0   # una plataforma anterior: Doctorado sin duración
    assert ctx.request.put(B+'/api/doc/config/plans',data=json.dumps({'plans':list(pl.values()),'extra':{'costo':300,'min':8},'cons':{'costo':0},'ren':{}}),headers=HDR).status==200
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&PL.find(function(p){return p.k==='Doctorado'}).n===0");time.sleep(0.8)
    pg.evaluate("ir('esc');etab('P')");pg.wait_for_selector('#pFileJ',state='attached')
    pg.set_input_files('#pFileJ','/mnt/user-data/outputs/carga_doctorado_plan_y_contenidos.json');pg.wait_for_selector('#pJBar:not([hidden])');m=pg.inner_text('#pJMsg')
    ok('avisa_que_fijara_la_duracion','16 asignaturas de Doctorado con 16 contenidos: 16 nuevas y 0' in m and '«Doctorado» no tiene duración definida: se fijará en 5 cuatrimestres (20 colegiaturas)' in m)
    pg.click('#pJOk');W(pg,"document.getElementById('pJBar').hidden")
    W(pg,"PL.find(function(p){return p.k==='Doctorado'}).n===20");pg.wait_for_timeout(800);m2=pg.inner_text('#pJMsg')
    ok('al_cargar_fija_la_duracion_y_la_guarda',planes(ctx,B)['Doctorado']['n']==20 and 'Duración fijada en: Doctorado' in m2 and '16 asignaturas cargadas' in m2)
    pg.select_option('#pPlan','Doctorado');pg.evaluate("renderPlan()");ok('el_plan_muestra_5_cuatrimestres','16 asignaturas en 5 cuatrimestres' in pg.inner_text('#pRes') and 'el plan tiene 5' in pg.inner_text('#pRes'))
    ok('cuatrimestre_1_tiene_4_materias_y_los_demas_3',pg.evaluate("[1,2,3,4,5].map(function(c){return catItems('Doctorado').filter(function(i){return i.cuat===c}).length})")==[4,3,3,3,3])
    pg.set_input_files('#pFileJ','/mnt/user-data/outputs/carga_doctorado_plan_y_contenidos.json');pg.wait_for_selector('#pJBar:not([hidden])');ok('si_ya_tiene_duracion_no_la_toca_ni_lo_menciona','duración definida' not in pg.inner_text('#pJMsg') and '16 que ya existen' in pg.inner_text('#pJMsg'));pg.click('#pJNo')
    # ---- cobros: sin costo no se generan colegiaturas ----
    ctx.request.put(B+'/api/doc/students/s1',data=json.dumps({'mat':'D001','nombre':'Dra. Prueba','carrera':'Doctorado','programa':'Doctorado','ingreso':2026,'nuevo':True}),headers=HDR)
    W(pg,"S.length===1")
    cols=lambda:pg.evaluate("cargos(S[0]).filter(function(c){return /^Colegiatura/.test(c.c)}).length")
    ok('sin_costo_de_colegiatura_no_genera_cobros_en_cero',cols()==0)
    pg.evaluate("PL.find(function(p){return p.k==='Doctorado'}).col=2500;refreshTotals()");ok('con_costo_genera_20_colegiaturas',cols()==20 and pg.evaluate("cargos(S[0]).filter(function(c){return /^Reinscripci/.test(c.c)}).length")==0)
    pg.evaluate("PL.find(function(p){return p.k==='Doctorado'}).rein=900;refreshTotals()");ok('y_4_reinscripciones',pg.evaluate("cargos(S[0]).filter(function(c){return /^Reinscripci/.test(c.c)}).length")==4)
    b.close();p.terminate();time.sleep(0.5)
    # ============ 2. precarga del servidor: fija la duración si el plan no la tenía ============
    B2='http://127.0.0.1:3142';p=arranca(3142,'/tmp/alm61',False);b,ctx,pg=admin(pw,B2)
    pl=planes(ctx,B2);pl['Doctorado']['n']=0
    ctx.request.put(B2+'/api/doc/config/plans',data=json.dumps({'plans':list(pl.values()),'extra':{'costo':300,'min':8},'cons':{'costo':0},'ren':{}}),headers=HDR)
    b.close();p.terminate();time.sleep(0.6)
    p=arranca(3142,'/tmp/alm61',True);time.sleep(1.5)
    ok('la_precarga_fija_la_duracion_de_un_plan_sin_duracion',plan_db('/tmp/alm61')['Doctorado']['n']==20)
    c=sqlite3.connect('/tmp/alm61/lafragua.db');n=c.execute("select count(*) from docs where coleccion='catalogo' and id='doctorado'").fetchone()[0];m=c.execute("select count(*) from docs where coleccion='contenidos' and id like 'doc-ed%'").fetchone()[0];c.close()
    ok('y_carga_las_16_materias_con_contenido',n==1 and m==16)
    p.terminate();time.sleep(0.5)
    # ============ 3. nunca pisa una duración que el administrador ya cambió ============
    B3='http://127.0.0.1:3143';p=arranca(3143,'/tmp/alm62',False);b,ctx,pg=admin(pw,B3)
    pl=planes(ctx,B3);pl['Doctorado']['n']=12
    ctx.request.put(B3+'/api/doc/config/plans',data=json.dumps({'plans':list(pl.values()),'extra':{'costo':300,'min':8},'cons':{'costo':0},'ren':{}}),headers=HDR)
    b.close();p.terminate();time.sleep(0.6)
    p=arranca(3143,'/tmp/alm62',True);time.sleep(1.5)
    ok('la_precarga_respeta_una_duracion_ya_definida',plan_db('/tmp/alm62')['Doctorado']['n']==12)
    p.terminate()
ok('sin_errores_js',len(errs)==0)
if errs:print('ERRORES JS:',errs[:3])
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
