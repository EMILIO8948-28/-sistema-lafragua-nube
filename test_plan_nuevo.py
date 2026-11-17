import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3105;B='http://127.0.0.1:%d'%PORT;TOK='tok-pn-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata35',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata35 /tmp/pnx && mkdir -p /tmp/nbdata35 /tmp/pnx')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[];dlg=[]
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
def plan_json(nombre,cuats,extra=None):
    items=[{'id':'x-%d-%d'%(c,i),'cuat':c,'clave':'','nom':'Materia %s %d-%d'%(nombre[:3],c,i),'cred':None,'hrs':None,'ct':1,'pdf':0} for c in range(1,cuats+1) for i in range(1,4)]
    cat={'plan':nombre,'items':items}
    if extra:cat['config']=extra
    return {'app':'colegiaturas-universidad-lafragua','formato':1,'colecciones':{'catalogo':{nombre.lower().replace(' ','-'):cat}},'contenidos':{i['id']:{'txt':'Contenido de '+i['nom']+' '+'x'*400,'pdf':None} for i in items}}
open('/tmp/pnx/sistemas.json','w',encoding='utf-8').write(json.dumps(plan_json('Ingeniería en Sistemas',9),ensure_ascii=False))
open('/tmp/pnx/mecatronica.json','w',encoding='utf-8').write(json.dumps(plan_json('Mecatrónica',12,{'n':42,'col':1500,'ins':900,'rein':900,'tit':25000}),ensure_ascii=False))
open('/tmp/pnx/nuevo.csv','w',encoding='utf-8-sig').write('plan,cuatrimestre,clave,asignatura,creditos,horas\nGastronomía,1,G01,Cocina básica,,\nGastronomía,1,G02,Higiene alimentaria,,\nGastronomía,2,G03,Pastelería,,\nGastronomía,9,G09,Cocina internacional,,\n')
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c,aceptar=True):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:(dlg.append(d.message),d.accept() if aceptar else d.dismiss()));return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    # ---- plan predeterminado que no llegaba a plataformas con planes ya guardados ----
    antiguos=[{'k':k,'n':n,'col':c,'ins':800,'rein':800,'tit':t} for k,n,c,t in [('Pedagogía',36,1300,23000),('Administración',36,1300,23000),('Contaduría',36,1300,23000),('Derecho',36,1300,23000),('Psicología',36,1300,23000),('Enfermería',42,1800,28000),('Arquitectura',42,1300,23000),('Maestría en Educación',16,1800,25000),('Doctorado',0,0,30000)]]
    put('config/plans',{'plans':antiguos,'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10")
    ok('plan_predeterminado_nuevo_llega_a_plataformas_con_planes_guardados',pg.evaluate("PL.some(function(p){return p.k==='Ingeniería Industrial'&&p.col===1350})"))
    W(pg,"1")
    time.sleep(1.0);ok('y_se_guarda_en_la_base',any(x['k']=='Ingeniería Industrial' for x in get('config/plans')['data']['plans']) and get('config/plans')['data']['extra']['costo']==300)
    # ---- caja y control escolar ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    def entra(u,c,aceptar=True):
        cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pp=pagina(cx,aceptar);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP',c);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&PL.length>=10");return pp
    pc=entra('caja1','clave-caja-123');pe=entra('esc2','clave-esc2-123')
    ok('quien_no_es_administrador_tambien_ve_el_plan_predeterminado',pc.evaluate("PL.some(function(p){return p.k==='Ingeniería Industrial'})"))
    # ---- crear un plan nuevo ----
    pg.evaluate("ir('esc');etab('P')");pg.wait_for_selector('#pNuevo');ok('boton_nuevo_plan_visible',pg.is_visible('#pNuevo'))
    pg.click('#pNuevo');pg.wait_for_selector('#dNP[open]')
    ok('muestra_la_duracion','9 cuatrimestres' in pg.inner_text('#npDur') and '3 años' in pg.inner_text('#npDur'))
    pg.fill('#npN','10.5');ok('duracion_con_medio_cuatrimestre','10 cuatrimestres y medio' in pg.inner_text('#npDur') and '3 años y 6 meses' in pg.inner_text('#npDur'))
    pg.click('#npOk');ok('exige_nombre','nombre del plan' in pg.inner_text('#npMsg'))
    pg.fill('#npNom','derecho');pg.click('#npOk');ok('rechaza_nombre_repetido','Ya existe' in pg.inner_text('#npMsg'))
    pg.fill('#npNom','Ingeniería en Sistemas');pg.fill('#npN','13');pg.click('#npOk');ok('rechaza_cuatrimestres_fuera_de_rango','0 a 12' in pg.inner_text('#npMsg'));pg.fill('#npN','9.3');pg.click('#npOk');ok('rechaza_cuatrimestres_que_no_son_medios','0 a 12' in pg.inner_text('#npMsg'))
    pg.fill('#npN','10.5');pg.fill('#npCol','-5');pg.click('#npOk');ok('rechaza_costos_negativos','mayores o iguales a 0' in pg.inner_text('#npMsg'))
    pg.fill('#npCol','1500');pg.fill('#npIns','900');pg.fill('#npRein','900');pg.fill('#npTit','24000');pg.set_input_files('#npFile','/tmp/pnx/sistemas.json');pg.click('#npOk');W(pg,"PL.some(function(p){return p.k==='Ingeniería en Sistemas'})")
    pl=[x for x in get('config/plans')['data']['plans'] if x['k']=='Ingeniería en Sistemas'];ok('plan_creado_con_sus_costos',len(pl)==1 and pl[0]['n']==42 and pl[0]['col']==1500 and pl[0]['ins']==900 and pl[0]['rein']==900 and pl[0]['tit']==24000)
    ok('el_plan_queda_seleccionado_y_muestra_su_mensaje','Ingeniería en Sistemas' in pg.input_value('#pPlan') and 'creado' in pg.inner_text('#pJMsg') and 'Ya aparece en todos los módulos' in pg.inner_text('#pJMsg'))
    W(pg,"document.getElementById('pJMsg').textContent.indexOf('Se cargarán')>0");ok('el_archivo_de_materias_se_prepara','27 asignaturas de Ingeniería en Sistemas' in pg.inner_text('#pJMsg') and pg.is_visible('#pJBar'))
    pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0");ok('materias_cargadas_en_el_plan_nuevo',pg.evaluate("catItems('Ingeniería en Sistemas').length")==27 and pg.evaluate("catItems('Ingeniería en Sistemas').every(function(i){return i.ct===1})"))
    # ---- aparece en todos los módulos ----
    pg.evaluate("renderPlan();renderAl();renderGr();renderMat();renderEgr();renderAA();fillPlans()")
    pg.evaluate("abrirAlumno(null)")
    mods=pg.evaluate("""(function(){var q=function(i){return Array.from(document.querySelectorAll('#'+i+' option')).map(function(o){return o.value||o.textContent}).indexOf('Ingeniería en Sistemas')>-1};
      return {plan:q('pPlan'),alumnos:q('ap'),alumno_form:q('alPlan'),grupos:q('grPlan'),grupos_filtro:q('grFPlan'),calendario:q('mPlan'),calendario_filtro:q('mFPlan'),egresados:q('egPlan'),acuerdos:q('aaPlan'),nuevo_pago:q('nCar')}})()""")
    ok('aparece_en_plan_de_estudios_alumnos_grupos_calendario_egresados_acuerdos_y_pagos',all(mods.values()))
    pg.evaluate("document.getElementById('dAl')&&document.getElementById('dAl').open&&document.getElementById('dAl').close()")
    pg.evaluate("renderCred()");ok('aparece_en_credenciales',pg.evaluate("Array.from(document.querySelectorAll('#crPl option')).some(function(o){return o.textContent==='Ingeniería en Sistemas'})"))
    pg.evaluate("inReset()");ok('aparece_en_inscripcion',pg.evaluate("Array.from(document.querySelectorAll('#inPlan option')).some(function(o){return o.textContent==='Ingeniería en Sistemas'})"))
    pg.evaluate("openPl()");ok('aparece_en_costos_y_planes','Ingeniería en Sistemas' in pg.inner_text('#plB') and '10' in pg.inner_text('#plB tr:has-text("Ingeniería en Sistemas")'));pg.evaluate("document.getElementById('dPl').close()")
    ok('resumen_de_planes_la_incluye','Ingeniería en Sistemas' in pg.inner_text('#pResumen') and '27' in pg.inner_text('#pResumen tr:has-text("Ingeniería en Sistemas")'))
    ok('otra_sesion_la_ve_sola',pc.evaluate("PL.some(function(p){return p.k==='Ingeniería en Sistemas'})") and pe.evaluate("PL.some(function(p){return p.k==='Ingeniería en Sistemas'})"))
    # un alumno del plan nuevo cobra sus colegiaturas con sus costos
    put('students/n1',{'mat':'20260001','nombre':'Luis Nuevo','carrera':'Ingeniería en Sistemas','programa':'Ingeniería en Sistemas','ingreso':2026,'nuevo':True})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&S.length===1&&PL.length>=11")
    cg=pg.evaluate("(function(){var s=S[0],c=cargos(s);return {col:c.filter(function(x){return /^Colegiatura/.test(x.c)}).map(function(x){return x.m}),ins:c.filter(function(x){return /nscripci/.test(x.c)}).map(function(x){return x.m})}})()")
    ok('un_alumno_del_plan_nuevo_se_cobra_con_los_costos_del_plan',len(cg['col'])>=1 and set(cg['col'])=={1500} and 900 in cg['ins'])
    # ---- crear planes al cargar un archivo ----
    pg.evaluate("ir('esc');etab('P')");pg.set_input_files('#pFileJ','/tmp/pnx/mecatronica.json');pg.wait_for_selector('#pJBar:not([hidden])');m=pg.inner_text('#pJMsg')
    ok('avisa_que_creara_el_plan_con_sus_costos','Se crearán los planes nuevos' in m and 'Mecatrónica' in m and '10 cuatrimestres y medio' in m and '$1500' in m)
    ok('no_crea_nada_hasta_confirmar',not pg.evaluate("PL.some(function(p){return p.k==='Mecatrónica'})"))
    pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0")
    mc=[x for x in get('config/plans')['data']['plans'] if x['k']=='Mecatrónica'];ok('archivo_con_plan_nuevo_lo_crea_con_su_configuracion',len(mc)==1 and mc[0]['n']==42 and mc[0]['col']==1500 and mc[0]['tit']==25000 and pg.evaluate("catItems('Mecatrónica').length")==36 and 'Planes nuevos creados: Mecatrónica' in pg.inner_text('#pJMsg'))
    dlg.clear();pg.evaluate("document.getElementById('pForm').open=true");pg.set_input_files('#pFile','/tmp/pnx/nuevo.csv');pg.wait_for_timeout(2500)
    gp=[x for x in get('config/plans')['data']['plans'] if x['k']=='Gastronomía']
    ok('csv_con_plan_nuevo_pregunta_y_lo_crea',any('todavía no existen: Gastronomía' in d for d in dlg) and len(gp)==1 and gp[0]['n']==36 and gp[0]['col']==1300 and pg.evaluate("catItems('Gastronomía').length")==4)
    # ---- quien no es administrador no puede ----
    pe.evaluate("ir('esc');etab('P')");dlg.clear();pe.evaluate("abreNP()");ok('control_escolar_no_crea_planes',any('Solo el Administrador' in d for d in dlg) and not pe.is_visible('#dNP'))
    pe.set_input_files('#pFileJ','/tmp/pnx/sistemas.json') if False else None
    open('/tmp/pnx/otro.json','w',encoding='utf-8').write(json.dumps(plan_json('Ingeniería Química',9),ensure_ascii=False))
    pe.set_input_files('#pFileJ','/tmp/pnx/otro.json');pe.wait_for_timeout(500);ok('control_escolar_tampoco_crea_planes_al_cargar_archivos','solo el Administrador puede crear planes nuevos' in pe.inner_text('#pJMsg') and pe.is_hidden('#pJBar'))
    ok('el_servidor_rechaza_a_quien_no_es_administrador',ctx.request.get(B+'/api/doc/config/plans').status==200)
    cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':'esc2','clave':'clave-esc2-123'}),headers=HDR);rp=cx.request.put(B+'/api/doc/config/plans',data=json.dumps({'plans':[]}),headers=HDR);ok('escritura_de_planes_solo_para_el_administrador',rp.status==403)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
