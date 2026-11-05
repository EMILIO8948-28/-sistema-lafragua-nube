import subprocess,time,json,os,urllib.request,shutil
from playwright.sync_api import sync_playwright
PORT=3092;B='http://127.0.0.1:%d'%PORT;TOK='tok-cj-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata22',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata22 /tmp/cj && mkdir -p /tmp/nbdata22 /tmp/cj')
SRC='/mnt/user-data/uploads/carga_pedagogia_plan_y_contenidos.json'
if not os.path.exists(SRC):SRC='/mnt/user-data/outputs/carga_pedagogia_plan_y_contenidos.json'
D=json.load(open(SRC,encoding='utf-8'))
open('/tmp/cj/otro.json','w').write(json.dumps({'hola':1}));open('/tmp/cj/roto.json','w').write('{no es json');
X=json.loads(json.dumps(D));X['colecciones']['catalogo']={'astrologia':{'plan':'Astrología','items':[{'id':'z1','cuat':1,'clave':'AS1','nom':'Astros','cred':None,'hrs':None}]}};open('/tmp/cj/plan_raro.json','w').write(json.dumps(X))
sol={'app':'colegiaturas-universidad-lafragua','formato':1,'colecciones':{'catalogo':{}}};open('/tmp/cj/sin_catalogo.json','w').write(json.dumps({'app':'colegiaturas-universidad-lafragua','colecciones':{'ledger':{}}}))
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=30):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    pg.evaluate("ir('esc');etab('P')");pg.wait_for_selector('#pImpJ')
    ok('boton_visible_para_el_administrador',pg.is_visible('#pImpJ'))
    # ---- archivos que no sirven ----
    pg.set_input_files('#pFileJ','/tmp/cj/roto.json');pg.wait_for_timeout(300);ok('rechaza_json_roto','no es un JSON válido' in pg.inner_text('#pJMsg'))
    pg.set_input_files('#pFileJ','/tmp/cj/otro.json');pg.wait_for_timeout(300);ok('rechaza_otro_archivo','no es una carga del plan' in pg.inner_text('#pJMsg') and pg.is_hidden('#pJBar'))
    pg.set_input_files('#pFileJ','/tmp/cj/sin_catalogo.json');pg.wait_for_timeout(300);ok('rechaza_respaldo_sin_plan','no es una carga del plan' in pg.inner_text('#pJMsg'))
    pg.set_input_files('#pFileJ','/tmp/cj/plan_raro.json');pg.wait_for_timeout(300);ok('plan_desconocido','Ningún plan' in pg.inner_text('#pJMsg') and 'Astrología' in pg.inner_text('#pJMsg') and pg.is_hidden('#pJBar'))
    # ---- primera carga ----
    shutil.copy(SRC,'/tmp/cj/carga.json')
    pg.set_input_files('#pFileJ','/tmp/cj/carga.json');pg.wait_for_selector('#pJBar:not([hidden])')
    m=pg.inner_text('#pJMsg');ok('resumen_antes_de_cargar','47 asignaturas de Pedagogía con 47 contenidos' in m and '47 nuevas y 0' in m and 'Confirmar carga' in m)
    ok('no_carga_nada_hasta_confirmar',get('catalogo/pedagogia')['exists'] is False)
    pg.click('#pJNo');ok('cancelar',pg.is_hidden('#pJBar') and get('catalogo/pedagogia')['exists'] is False)
    pg.set_input_files('#pFileJ','/tmp/cj/carga.json');pg.wait_for_selector('#pJBar:not([hidden])');pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0")
    ok('mensaje_final','47 asignaturas cargadas (47 nuevas y 0 actualizadas) y 47 contenidos' in pg.inner_text('#pJMsg'))
    c=get('catalogo/pedagogia')['data']['items'];ok('47_asignaturas_en_9_cuatrimestres',len(c)==47 and len(set(i['cuat'] for i in c))==9 and all(i['ct']==1 for i in c))
    ok('cada_contenido_en_su_materia',all(len(get('contenidos/'+i['id'])['data']['txt'])>400 for i in c) and 'Mesopotamia' in get('contenidos/ped-lp01')['data']['txt'] and 'Antropología' in get('contenidos/ped-lp06')['data']['txt'])
    pg.select_option('#pPlan','Pedagogía');pg.evaluate("renderPlan()");ok('se_ve_en_la_pantalla','47 asignaturas en 9 cuatrimestres' in pg.inner_text('#pRes') and pg.locator('#pLista [data-ct]').count()==47)
    pg.locator('#pLista [data-ct="ped-lp01"]').click();pg.wait_for_selector('#dCt[open]');W(pg,"document.getElementById('ctTxt').value.length>400");ok('contenido_abre_en_la_materia','Mesopotamia' in pg.input_value('#ctTxt'));pg.click('#ctCls')
    # ---- segunda carga: no duplica ----
    pg.set_input_files('#pFileJ','/tmp/cj/carga.json');pg.wait_for_selector('#pJBar:not([hidden])');m=pg.inner_text('#pJMsg');ok('segunda_vez_avisa_que_reemplaza','0 nuevas y 47 que ya existen' in m and '47 ya tenían contenido' in m)
    pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0");ok('no_duplica',len(get('catalogo/pedagogia')['data']['items'])==47)
    # ---- ya hay materias cargadas con otros identificadores: se les agrega el contenido ----
    put('catalogo/pedagogia',{'plan':'Pedagogía','items':[
        {'id':'x1','cuat':7,'clave':'LP01','nom':'Historia de la educacion (viejo nombre)','cred':6,'hrs':4,'ct':0,'pdf':0},
        {'id':'x2','cuat':1,'clave':'','nom':'Teoría pedagógica','cred':None,'hrs':None,'ct':1,'pdf':1},
        {'id':'x3','cuat':5,'clave':'','nom':'Materia propia de la escuela','cred':3,'hrs':2,'ct':0,'pdf':0}]})
    put('contenidos/x2',{'txt':'texto anterior','pdf':{'id':'a'*32,'name':'temario.pdf','size':1000}})
    for i in c:
        if i['id']!='ped-lp01' and i['id']!='ped-lp02':ctx.request.delete(B+'/api/doc/contenidos/'+i['id'],headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&catItems('Pedagogía').length===3");pg.evaluate("ir('esc');etab('P')")
    pg.set_input_files('#pFileJ','/tmp/cj/carga.json');pg.wait_for_selector('#pJBar:not([hidden])');m=pg.inner_text('#pJMsg');ok('resumen_con_materias_existentes','44 nuevas y 2 que ya existen' in m or '45 nuevas y 2' in m or 'que ya existen' in m)
    pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0")
    its={i['id']:i for i in get('catalogo/pedagogia')['data']['items']};ok('conserva_los_identificadores_existentes','x1' in its and 'x2' in its and 'ped-lp01' not in its and 'ped-lp02' not in its)
    ok('conserva_creditos_y_agrega_clave_y_cuatrimestre',its['x1']['cred']==6 and its['x1']['hrs']==4 and its['x1']['cuat']==1 and its['x1']['clave']=='LP01' and its['x1']['nom']=='Historia de la educación' and its['x2']['clave']=='LP02' and its['x2']['cuat']==1)
    ok('conserva_materias_propias',its['x3']['nom']=='Materia propia de la escuela' and its['x3']['cuat']==5 and its['x3']['cred']==3 and len(its)==47+1)
    ok('contenido_en_la_materia_existente',get('contenidos/x1')['data']['txt'].startswith('FINES') and its['x1']['ct']==1 and get('contenidos/x2')['data']['txt']!='texto anterior')
    ok('conserva_el_pdf_de_la_materia',get('contenidos/x2')['data']['pdf']['name']=='temario.pdf' and its['x2']['pdf']==1)
    ok('sin_duplicados',len(set((i['clave'] or i['nom']) for i in its.values()))==len(its))
    # ---- quien no es administrador ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    cj=b.new_context(viewport={'width':1100,'height':900});cj.set_default_timeout(15000);pc=pagina(cj);pc.goto(B+'/');W(pc,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pc.fill('#lgU','caja1');pc.fill('#lgP','clave-caja-123');pc.click('#lgGo');W(pc,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof CATA!=='undefined'");pc.evaluate("ir('esc');etab('P')");ok('caja_no_ve_el_boton',pc.is_hidden('#pImpJ'))
    # quien edita Control escolar sí puede cargar (solo agrega, no borra: no necesita autorización)
    put('catalogo/pedagogia',{'plan':'Pedagogía','items':[]})
    ce=b.new_context(viewport={'width':1100,'height':900});ce.set_default_timeout(15000);pe=pagina(ce);pe.goto(B+'/');W(pe,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pe.fill('#lgU','esc2');pe.fill('#lgP','clave-esc2-123');pe.click('#lgGo');W(pe,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof CATA!=='undefined'");pe.evaluate("ir('esc');etab('P')")
    pe.set_input_files('#pFileJ','/tmp/cj/carga.json');pe.wait_for_selector('#pJBar:not([hidden])');pe.click('#pJOk');W(pe,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0")
    ok('quien_edita_control_escolar_puede_cargar_sin_autorizacion',len(get('catalogo/pedagogia')['data']['items'])==47 and not pe.evaluate("document.getElementById('dAu').open"))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
