import subprocess,time,json,os,urllib.request,sqlite3
from playwright.sync_api import sync_playwright
PORT=3113;B='http://127.0.0.1:%d'%PORT;TOK='tok-rn-123'
os.system('rm -rf /tmp/nbdata43 /tmp/rnx /tmp/nbdata44 && mkdir -p /tmp/nbdata43 /tmp/rnx /tmp/nbdata44')
def inicia(datos,port,sin=True):
    e=dict(os.environ,PORT=str(port),DATA_DIR=datos,LF_SETUP_TOKEN=TOK)
    if sin:e['LF_SIN_PRECARGA']='1'
    pr=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=e,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen('http://127.0.0.1:%d/salud'%port,timeout=1);break
        except Exception:pass
    return pr
p=inicia('/tmp/nbdata43',PORT)
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
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def plan_json(nombre,cuats):
    items=[{'id':'x-%d-%d'%(c,i),'cuat':c,'clave':'','nom':'Materia %d-%d'%(c,i),'cred':None,'hrs':None,'ct':1,'pdf':0} for c in range(1,cuats+1) for i in range(1,3)]
    return {'app':'colegiaturas-universidad-lafragua','formato':1,'colecciones':{'catalogo':{'x':{'plan':nombre,'items':items}}},'contenidos':{i['id']:{'txt':'Contenido '+i['nom']+' '+'x'*400,'pdf':None} for i in items}}
open('/tmp/rnx/viejo.json','w',encoding='utf-8').write(json.dumps(plan_json('Pedagogía',2),ensure_ascii=False))
open('/tmp/rnx/viejo.csv','w',encoding='utf-8-sig').write('plan,cuatrimestre,clave,asignatura,creditos,horas\nPedagogía,3,P01,Didáctica general,,\nPedagogía,3,P02,Evaluación educativa,,\n')
NUEVO='Licenciatura en Pedagogía'
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    dlg=[]
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:(dlg.append(d.message),d.accept()));return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10")
    time.sleep(1.5)
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    # ---- datos que mencionan el plan ----
    put('students/s1',{'mat':'20250001','nombre':'Ana López','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2025,'nuevo':False})
    put('students/s2',{'mat':'20250002','nombre':'Beto Mena','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    put('students/s3',{'mat':'20250003','nombre':'Carla Díaz','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2025,'nuevo':False})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':'Sep–Dic 2026','cuat':2,'alumnos':['s1','s3']})
    put('grupos/g2',{'num':'4822','plan':'Derecho','per':'Sep–Dic 2026','cuat':2,'alumnos':['s2']})
    put('materias/m1',{'per':'Sep–Dic 2026','plan':'Pedagogía','cuat':2,'nom':'Didáctica general','docId':'d1','ini':'08:00','fin':'10:00'})
    put('materias/m2',{'per':'Sep–Dic 2026','plan':'Derecho','cuat':2,'nom':'Derecho civil','docId':'d1','ini':'10:00','fin':'12:00','fus':[{'plan':'Pedagogía','cuat':2,'nom':'Didáctica general'}]})
    put('materias/m3',{'per':'Sep–Dic 2026','plan':'Derecho','cuat':3,'nom':'Derecho penal','docId':'d1','ini':'12:00','fin':'14:00'})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[{'id':'a1','cid':'x','plan':'Pedagogía','cuat':2,'nom':'Didáctica general','per':'Sep–Dic 2026','ses':4},{'id':'a2','cid':'y','plan':'Derecho','cuat':2,'nom':'Derecho civil','per':'Sep–Dic 2026','ses':4}]})
    put('calif/s1',{'items':[{'id':'i1','mid':'m1','mat':'Didáctica general','plan':'Pedagogía','per':'Sep–Dic 2026','cuat':2,'cal':9},{'id':'i2','mid':'m3','mat':'Derecho penal','plan':'Derecho','per':'Sep–Dic 2026','cuat':3,'cal':8}]})
    put('constancias/s1',{'items':[{'id':'k1','num':'C-1','monto':50,'plan':'Pedagogía','fecha':'2026-10-01'}]})
    put('acuerdos/ac1',{'id':'ac1','sid':'s1','num':'A-1','plan':'Pedagogía','cuotas':[]})
    put('egresados/s3',{'sid':'s3','nombre':'Carla Díaz','plan':'Pedagogía','fecha':'2026-10-01'})
    put('justificantes/j1',{'id':'j1','num':'J-1','sid':'s1','plan':'Pedagogía','estado':'Aprobado'})
    put('resguardos/r1',{'num':'R-000001','sid':'s1','nombre':'Ana López','mat':'20250001','plan':'Pedagogía','tipo':'Título profesional','estado':'resguardo','mov':[]})
    put('solicitudes/so1',{'id':'so1','tipo':'boleta','sid':'s1','plan':'Pedagogía','estado':'pendiente','creada':'2026-11-01T10:00:00.000Z'})
    put('catalogo/pedagogia',{'plan':'Pedagogía','items':[{'id':'ped-lp01','cuat':1,'clave':'LP01','nom':'Introducción a la pedagogía','cred':None,'hrs':None,'ct':1,'pdf':0},{'id':'ped-lp02','cuat':2,'clave':'LP02','nom':'Didáctica general','cred':None,'hrs':None,'ct':0,'pdf':0}]})
    put('contenidos/ped-lp01',{'txt':'Contenido de introducción','pdf':None})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(ST).length===3&&Object.keys(MAT).length===3&&Object.keys(DOC).length===1&&Object.keys(RSG).length===1&&Object.keys(SOL).length===1&&Object.keys(CATA).length>=1")
    pg.evaluate("ir('esc');etab('P')");pg.wait_for_selector('#pRen');ok('boton_visible_para_el_administrador',pg.is_visible('#pRen'))
    pg.select_option('#pPlan','Pedagogía');pg.evaluate("renderPlan()");pg.click('#pRen');pg.wait_for_selector('#dRn[open]')
    ok('abre_con_el_plan_elegido_y_su_nombre',pg.input_value('#rnPlan')=='Pedagogía' and pg.input_value('#rnNom')=='Pedagogía')
    res=pg.inner_text('#rnRes');ok('avisa_cuantos_registros_actualizara','2 alumnos' in res and '1 grupos' in res and '2 materias del calendario' in res and '1 asignaciones de docentes' in res and '1 calificaciones' in res and '1 constancias' in res and '1 acuerdos de pago' in res and '1 egresados' in res and '1 justificantes' in res and '1 títulos en resguardo' in res and '1 solicitudes de alumnos' in res and '2 asignaturas del plan de estudios' in res)
    pg.click('#rnOk');ok('no_acepta_el_mismo_nombre','igual al actual' in pg.inner_text('#rnMsg'))
    pg.fill('#rnNom','derecho');pg.click('#rnOk');ok('no_acepta_el_nombre_de_otro_plan','otro plan' in pg.inner_text('#rnMsg'))
    pg.fill('#rnNom','ab');pg.click('#rnOk');ok('exige_un_nombre_de_3_letras','mínimo 3 letras' in pg.inner_text('#rnMsg'))
    pg.select_option('#rnPlan','Enfermería');pg.fill('#rnNom','Licenciatura en Cuidados');ok('advierte_que_la_tarifa_de_docentes_depende_del_nombre','tarifa' in pg.inner_text('#rnAviso') and '$150.00' in pg.inner_text('#rnAviso') and '$120.00' in pg.inner_text('#rnAviso'))
    pg.fill('#rnNom','Licenciatura en Enfermería');ok('sin_aviso_si_la_tarifa_no_cambia',pg.inner_text('#rnAviso')=='')
    pg.select_option('#rnPlan','Pedagogía');ok('sin_aviso_en_pedagogia',pg.inner_text('#rnAviso')=='')
    pg.fill('#rnNom','  '+NUEVO+'  ');dlg.clear();pg.click('#rnOk');W(pg,"!document.getElementById('dRn').open",60)
    ok('pide_confirmar_con_el_resumen',any('Pedagogía' in d and NUEVO in d and '2 alumnos' in d for d in dlg))
    time.sleep(1.0)
    # ---- todo quedó con el nombre nuevo ----
    ok('alumnos_actualizados',get('students/s1')['data']['programa']==NUEVO and get('students/s1')['data']['carrera']==NUEVO and get('students/s3')['data']['programa']==NUEVO and get('students/s2')['data']['programa']=='Derecho')
    ok('grupos_actualizados',get('grupos/g1')['data']['plan']==NUEVO and get('grupos/g2')['data']['plan']=='Derecho')
    m1,m2,m3=get('materias/m1')['data'],get('materias/m2')['data'],get('materias/m3')['data']
    ok('materias_y_fusiones_actualizadas',m1['plan']==NUEVO and m2['plan']=='Derecho' and m2['fus'][0]['plan']==NUEVO and m2['fus'][0]['nom']=='Didáctica general' and m3['plan']=='Derecho' and 'fus' not in m3 and m1['docId']=='d1' and m1['ini']=='08:00')
    d1=get('docentes/d1')['data'];ok('asignaciones_de_docentes',[a['plan'] for a in d1['asig']]==[NUEVO,'Derecho'] and d1['nombre']=='Prof. Uno')
    ok('calificaciones_y_constancias',[i['plan'] for i in get('calif/s1')['data']['items']]==[NUEVO,'Derecho'] and get('calif/s1')['data']['items'][0]['cal']==9 and get('constancias/s1')['data']['items'][0]['plan']==NUEVO)
    ok('acuerdos_egresados_justificantes_resguardos_y_solicitudes',get('acuerdos/ac1')['data']['plan']==NUEVO and get('egresados/s3')['data']['plan']==NUEVO and get('justificantes/j1')['data']['plan']==NUEVO and get('resguardos/r1')['data']['plan']==NUEVO and get('solicitudes/so1')['data']['plan']==NUEVO)
    ok('el_catalogo_se_mueve_al_nombre_nuevo',get('catalogo/pedagogia')['exists'] is False and get('catalogo/licenciatura-en-pedagogia')['data']['plan']==NUEVO and [i['id'] for i in get('catalogo/licenciatura-en-pedagogia')['data']['items']]==['ped-lp01','ped-lp02'] and get('contenidos/ped-lp01')['data']['txt']=='Contenido de introducción')
    cfg=get('config/plans')['data'];ks=[x['k'] for x in cfg['plans']]
    ok('el_plan_cambia_de_nombre_sin_duplicarse',NUEVO in ks and 'Pedagogía' not in ks and len(ks)==len(set(ks)) and [x for x in cfg['plans'] if x['k']==NUEVO][0]['col']==1300 and cfg['ren']=={'Pedagogía':NUEVO})
    ok('la_pantalla_usa_el_nombre_nuevo',pg.evaluate("PL.some(function(p){return p.k==='%s'})&&!PL.some(function(p){return p.k==='Pedagogía'})"%NUEVO) and pg.input_value('#pPlan')==NUEVO and 'Introducción a la pedagogía' in pg.inner_text('#pLista') and 'ahora se llama' in pg.inner_text('#pJMsg'))
    ok('aparece_en_los_selectores',pg.evaluate("renderPlan();renderAl();renderGr();renderMat();Array.from(document.querySelectorAll('#ap option,#grPlan option,#mPlan option,#nCar option')).some(function(o){return o.textContent==='%s'})"%NUEVO) and not pg.evaluate("Array.from(document.querySelectorAll('#ap option,#grPlan option,#mPlan option,#nCar option')).some(function(o){return o.textContent==='Pedagogía'})"))
    ok('los_alumnos_siguen_cobrando_con_los_costos_del_plan',pg.evaluate("(function(){var s=S.find(function(x){return x.id==='s1'}),c=cargos(s);return c.filter(function(x){return /^Colegiatura/.test(x.c)}).length>=36&&planOf(s)&&planOf(s).k==='%s'})()"%NUEVO))
    # ---- recargar: el nombre anterior no vuelve ----
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    ok('al_recargar_no_reaparece_el_plan_anterior',pg.evaluate("PL.filter(function(p){return p.k==='Pedagogía'}).length===0&&PL.filter(function(p){return p.k==='%s'}).length===1&&PL.length===11"%NUEVO) and 'Pedagogía' not in [x['k'] for x in get('config/plans')['data']['plans']])
    # ---- archivos con el nombre anterior ----
    pg.evaluate("ir('esc');etab('P')");pg.select_option('#pPlan',NUEVO)
    pg.set_input_files('#pFileJ','/tmp/rnx/viejo.json');pg.wait_for_selector('#pJBar:not([hidden])');m=pg.inner_text('#pJMsg')
    ok('un_json_con_el_nombre_anterior_va_al_plan_renombrado',NUEVO in m and 'Se crearán los planes nuevos' not in m and 'Ningún plan' not in m);pg.click('#pJNo')
    n0=len(pg.evaluate("PL"));dlg.clear();pg.evaluate("document.getElementById('pForm').open=true");pg.set_input_files('#pFile','/tmp/rnx/viejo.csv');pg.wait_for_timeout(2500)
    ok('un_csv_con_el_nombre_anterior_tampoco_crea_otro_plan',not any('todavía no existen' in d for d in dlg) and len(pg.evaluate("PL"))==n0 and pg.evaluate("catItems('%s').some(function(i){return i.nom==='Didáctica general'&&i.cuat===3})"%NUEVO))
    # ---- volver al nombre original ----
    pg.evaluate("abreRn()");pg.select_option('#rnPlan',NUEVO);pg.fill('#rnNom','Pedagogía');pg.click('#rnOk');W(pg,"!document.getElementById('dRn').open",60);time.sleep(1.0)
    cfg=get('config/plans')['data'];ok('se_puede_volver_al_nombre_original',[x['k'] for x in cfg['plans']].count('Pedagogía')==1 and NUEVO not in [x['k'] for x in cfg['plans']] and cfg['ren']=={NUEVO:'Pedagogía'} and get('students/s1')['data']['programa']=='Pedagogía' and get('catalogo/pedagogia')['data']['plan']=='Pedagogía' and get('catalogo/licenciatura-en-pedagogia')['exists'] is False)
    # ---- solo el administrador ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pe=pagina(cx);pe.goto(B+'/');W(pe,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pe.fill('#lgU','esc2');pe.fill('#lgP','clave-esc2-123');pe.click('#lgGo');W(pe,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&Object.keys(ST).length===3")
    pe.evaluate("ir('esc');etab('P')");dlg.clear();pe.evaluate("abreRn()");ok('control_escolar_no_puede_cambiar_el_nombre',any('Solo el Administrador' in d for d in dlg) and not pe.is_visible('#dRn'))
    ok('el_servidor_no_deja_a_otro_usuario_cambiar_los_planes',cx.request.put(B+'/api/doc/config/plans',data=json.dumps({'plans':[]}),headers=HDR).status==403)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate();time.sleep(0.5)
# ---- la precarga del servidor respeta el plan renombrado ----
p2=inicia('/tmp/nbdata44',PORT+1)
p2.terminate();time.sleep(0.8)
db=sqlite3.connect('/tmp/nbdata44/lafragua.db')
planes=[{'k':NUEVO,'n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':'Derecho','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}]
db.execute("INSERT OR REPLACE INTO docs (coleccion,id,data,actualizado) VALUES ('config','plans',?,?)",(json.dumps({'plans':planes,'extra':{'costo':300,'min':8},'cons':{'costo':50},'ren':{'Pedagogía':NUEVO}}),int(time.time()*1000)));db.commit();db.close()
p3=inicia('/tmp/nbdata44',PORT+2,sin=False)
db=sqlite3.connect('/tmp/nbdata44/lafragua.db')
def cat(k):
    r=db.execute("SELECT data FROM docs WHERE coleccion='catalogo' AND id=?",(k,)).fetchone();return json.loads(r[0]) if r else None
cn,co,cd=cat('licenciatura-en-pedagogia'),cat('pedagogia'),cat('derecho')
R['la_precarga_usa_el_nombre_nuevo']=bool(cn and cn['plan']==NUEVO and len(cn['items'])==47 and co is None and cd and cd['plan']=='Derecho' and len(cd['items'])==49)
nc=db.execute("SELECT COUNT(*) FROM docs WHERE coleccion='contenidos' AND id LIKE 'ped-%'").fetchone()[0];R['y_carga_sus_contenidos']=nc==47
db.close();p3.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
