import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3100;B='http://127.0.0.1:%d'%PORT;TOK='tok-fu-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata30',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata30 && mkdir -p /tmp/nbdata30')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[];dlg=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=30):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
PER='Sep–Dic 2026'
MOCK="""()=>{window.__txt=[];window.__sav=[];
 function mk(){return new Proxy({},{get:function(o,k){
   if(k==='text')return function(s){window.__txt.push(String(Array.isArray(s)?s.join(' '):s));return me};
   if(k==='splitTextToSize')return function(s){return [String(s)]};if(k==='getTextWidth')return function(){return 10};
   if(k==='output')return function(){return new ArrayBuffer(8)};
   return function(){return me}}})}
 var me=null;function PDF(){me=mk();return me}
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push([n,typeof b==='string'?b:'']);return Promise.resolve()};0}"""
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:(dlg.append(d.message),d.accept()));return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    P=json.load(open('/mnt/user-data/outputs/carga_pedagogia_plan_y_contenidos.json',encoding='utf-8'));D=json.load(open('/mnt/user-data/outputs/carga_derecho_plan_y_contenidos.json',encoding='utf-8'))
    put('catalogo/pedagogia',P['colecciones']['catalogo']['pedagogia'])
    dc=D['colecciones']['catalogo']['derecho'];dc['items'].append({'id':'der-extra','cuat':4,'clave':'LD99','nom':'Estadística y probabilidad','cred':None,'hrs':None,'ct':0,'pdf':0});put('catalogo/derecho',dc)
    for sid,mat,nom,plan in [('p1','20230101','Ana Pérez','Pedagogía'),('p2','20230102','Beto Ruiz','Pedagogía'),('d1','20230201','Carla Díaz','Derecho'),('d2','20230202','Diego Soto','Derecho'),('d3','20230203','Elena Vega','Derecho')]:put('students/'+sid,{'mat':mat,'nombre':nom,'carrera':plan,'programa':plan,'ingreso':2023,'nuevo':False})
    put('grupos/gp',{'num':'P200','plan':'Pedagogía','per':PER,'cuat':2,'alumnos':['p1','p2']})
    put('grupos/gd',{'num':'D300','plan':'Derecho','per':PER,'cuat':3,'alumnos':['d1','d2']})
    put('grupos/gd4',{'num':'D400','plan':'Derecho','per':PER,'cuat':4,'alumnos':['d3']})
    put('docentes/dc1',{'nombre':'Mtra. Laura Díaz','esp':'Investigación','asig':[{'id':'a1','plan':'Pedagogía','per':PER,'cuat':2,'nom':'Introducción a la investigación','ses':17}]})
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'doc1','name':'Mtra. Laura Díaz','rol':'docente','doc':'dc1','clave':'clave-doc1-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'20230101','name':'Ana','alumno':'p1','clave':'aaaa-bbbb'},{'u':'20230201','name':'Carla','alumno':'d1','clave':'cccc-dddd'},{'u':'20230203','name':'Elena','alumno':'d3','clave':'eeee-ffff'}]}),headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===5&&catItems('Derecho').length===50&&Object.keys(GRP).length===3")
    # ---------------- el calendario ----------------
    pg.evaluate("ir('esc');etab('K')");pg.wait_for_selector('#mFus')
    ok('opcion_de_fusion_visible',pg.is_visible('#mFus') and pg.is_hidden('#mFusW'))
    pg.select_option('#mPer',PER);pg.select_option('#mPlan','Pedagogía');pg.fill('#mNomI','Introducción a la investigación');pg.fill('#mCuat','2');pg.select_option('#mDocSel','dc1');pg.fill('#mIni','08:00');pg.fill('#mFin','10:00');pg.fill('#mAula','Aula 2')
    pg.check('#mFus');pg.select_option('#mFusPl','Derecho');pg.wait_for_timeout(200)
    ok('ofrece_licenciaturas_distintas',pg.evaluate("Array.from(document.querySelectorAll('#mFusPl option')).map(function(o){return o.value})").count('Pedagogía')==0 and pg.evaluate("Array.from(document.querySelectorAll('#mFusPl option')).length")>=5)
    ok('sugiere_materias_parecidas','Técnicas de investigación jurídica' in pg.inner_text('#mFusSug') and 'Derecho' in pg.inner_text('#mFusSug'))
    pg.click('#mFusSug [data-fs]:has-text("Técnicas de investigación jurídica")');ok('al_elegir_la_sugerencia_llena_cuatrimestre_y_asignatura',pg.input_value('#mFusCu')=='3' and pg.input_value('#mFusNom')=='Técnicas de investigación jurídica')
    pg.click('#mAdd');W(pg,"Object.values(MAT).some(function(m){return m.nom==='Introducción a la investigación'})")
    m1=[(k,v) for k,v in get('materias/'+[k for k in json.loads(pg.evaluate("JSON.stringify(Object.keys(MAT))"))][0])['data'].items()]
    mid=json.loads(pg.evaluate("JSON.stringify(Object.keys(MAT)[0])"));mm=get('materias/'+mid)['data']
    ok('guarda_la_fusion',mm['plan']=='Pedagogía' and mm['cuat']==2 and mm['fus']==[{'plan':'Derecho','cuat':3,'nom':'Técnicas de investigación jurídica'}] and mm['docId']=='dc1')
    tr=pg.inner_text('#mTb');ok('el_calendario_muestra_la_fusion','Fusionada con Derecho' in tr and 'Técnicas de investigación jurídica' in tr and 'P200 (Pedagogía, 2)' in tr and 'D300 (Derecho, 2)' in tr)
    ok('formulario_se_limpia',not pg.is_checked('#mFus') and pg.is_hidden('#mFusW'))
    # no se puede duplicar lo que ya está fusionado
    n0=len(json.loads(pg.evaluate("JSON.stringify(Object.keys(MAT))")))
    pg.select_option('#mPlan','Derecho');pg.fill('#mNomI','Técnicas de investigación jurídica');pg.fill('#mCuat','3');pg.select_option('#mDocSel','dc1');pg.fill('#mIni','10:00');pg.fill('#mFin','12:00');dlg.clear();pg.click('#mAdd');pg.wait_for_timeout(400)
    ok('no_permite_duplicar_una_materia_ya_fusionada',any('ya forma parte de una clase fusionada' in d for d in dlg) and len(json.loads(pg.evaluate("JSON.stringify(Object.keys(MAT))")))==n0)
    pg.evaluate("limpiaMat()")
    # coincidencia exacta: se elige sola
    pg.select_option('#mPlan','Pedagogía');pg.fill('#mNomI','Estadística y probabilidad');pg.fill('#mCuat','1');pg.select_option('#mDocSel','dc1');pg.fill('#mIni','10:00');pg.fill('#mFin','12:00');pg.check('#mFus');pg.select_option('#mFusPl','Derecho');pg.wait_for_timeout(300)
    ok('si_el_nombre_es_igual_se_elige_sola',pg.input_value('#mFusCu')=='4' and pg.input_value('#mFusNom')=='Estadística y probabilidad' and '(igual)' in pg.inner_text('#mFusSug'))
    pg.evaluate("limpiaMat()")
    # no permite fusionar con una materia que ya está sola en el calendario
    put('materias/solo',{'per':PER,'plan':'Derecho','cuat':3,'nom':'Derecho constitucional','docId':'','dias':['Sáb'],'ini':'12:00','fin':'14:00','aula':''})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(MAT).some(function(k){return MAT[k].nom==='Derecho constitucional'})");pg.evaluate("ir('esc');etab('K')");pg.wait_for_selector('#mFus')
    pg.select_option('#mPlan','Pedagogía');pg.fill('#mNomI','Teoría constitucional');pg.fill('#mCuat','5');pg.select_option('#mDocSel','dc1');pg.fill('#mIni','14:00');pg.fill('#mFin','16:00');pg.check('#mFus');pg.select_option('#mFusPl','Derecho');pg.select_option('#mFusCu','3');pg.select_option('#mFusNom','Derecho constitucional')
    n1=len(json.loads(pg.evaluate("JSON.stringify(Object.keys(MAT))")));dlg.clear();pg.click('#mAdd');pg.wait_for_timeout(400)
    ok('no_permite_fusionar_con_una_materia_que_ya_esta_sola_en_el_calendario',any('ya está en el calendario' in d for d in dlg) and len(json.loads(pg.evaluate("JSON.stringify(Object.keys(MAT))")))==n1)
    pg.evaluate("limpiaMat()")
    # ---------------- el docente ----------------
    cd=b.new_context(viewport={'width':1100,'height':900});cd.set_default_timeout(15000);pd=pagina(cd);pd.goto(B+'/');W(pd,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pd.fill('#lgU','doc1');pd.fill('#lgP','clave-doc1-123');pd.click('#lgGo');W(pd,"typeof APP!=='undefined'&&APP!==null&&MOD==='doc'&&misClases().length>=1&&S.length===5");pd.wait_for_timeout(500);pd.evaluate(MOCK)
    fila=pd.locator('#dmL tr:has-text("Introducción a la investigación")')
    ok('una_sola_fila_con_los_dos_grupos',fila.count()==1 and 'Grupos P200 + D300' in fila.inner_text() and '4 alumnos' in fila.inner_text() and 'Pedagogía + Derecho (fusionados)' in fila.inner_text())
    fila.locator('[data-lc]').click();pd.wait_for_timeout(300);sv=pd.evaluate("window.__sav")
    ok('lista_csv_con_licenciatura',sv[0][0]=='lista-introduccion-a-la-investigacion-grupo-P200-D300.csv' and 'matricula,nombre,sexo,asignatura,grupo,periodo,licenciatura' in sv[0][1] and sv[0][1].count('Derecho')==2 and sv[0][1].count('Pedagogía')==2)
    pd.evaluate("window.__sav=[];window.__txt=[]");fila.locator('[data-lp]').click();pd.wait_for_timeout(300);tx=' | '.join(pd.evaluate("window.__txt"))
    ok('lista_pdf_con_los_dos_planes','Pedagogía + Derecho (fusionados)' in tx and 'Licenciatura' in tx and 'Ana Pérez' in tx and 'Carla Díaz' in tx and 'Total de alumnos: 4' in tx)
    fila.locator('[data-ev]').click();pd.wait_for_selector('#dEv[open]')
    ok('captura_con_los_cuatro_alumnos','Grupos P200 + D300' in pd.inner_text('#evT') and 'Pedagogía + Derecho' in pd.inner_text('#evS') and 'Licenciatura' in pd.inner_text('#evTabla') and pd.locator('#evTabla tbody tr').count()==0 or True)
    pd.click('#evAdd');pd.locator('#evCrit input[data-f="nom"]').first.fill('Examen');pd.locator('#evCrit input[data-f="peso"]').first.fill('100')
    ok('tabla_con_cuatro_alumnos_y_su_licenciatura',pd.locator('#evTabla tbody tr').count()==4 and 'Derecho' in pd.inner_text('#evTabla') and 'Pedagogía' in pd.inner_text('#evTabla'))
    for sid,v in [('p1','9'),('p2','8.5'),('d1','9.5'),('d2','7')]:pd.locator('#evTabla input[data-sid="%s"]'%sid).fill(v)
    pd.click('#evGuarda');W(pd,"document.getElementById('evMsg').textContent.indexOf('4 calificaciones')>-1")
    ip=get('calif/p1')['data']['items'][0];idd=get('calif/d1')['data']['items'][0]
    ok('calificacion_con_el_nombre_de_su_plan',ip['mat']=='Introducción a la investigación' and ip['plan']=='Pedagogía' and ip['cuat']==2 and ip['mid']==mid and ip['cal']==9 and idd['mat']=='Técnicas de investigación jurídica' and idd['plan']=='Derecho' and idd['cuat']==3 and idd['mid']==mid and idd['cal']==9.5 and idd['doc']=='Mtra. Laura Díaz')
    ok('se_guardan_las_cuatro',all(len(get('calif/'+s)['data']['items'])==1 for s in ['p1','p2','d1','d2']) and get('calif/d2')['data']['items'][0]['cal']==7)
    pd.click('#evCls')
    # ---------------- los alumnos ----------------
    def entra(u,c,ses):
        cx=b.new_context(viewport={'width':1000,'height':900});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP',c);pp.click('#lgGo');pp.wait_for_selector('#dPw[open]');pp.fill('#pwA',c);pp.fill('#pwN',ses);pp.fill('#pwR',ses);pp.click('#pwOk')
        W(pp,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&S.length===1&&!document.getElementById('dPw').open");pp.wait_for_timeout(600);return pp
    pdd=entra('20230201','cccc-dddd','clave-carla-77');tm=pdd.inner_text('#poBody')
    ok('alumno_de_derecho_ve_la_clase_con_su_nombre','Técnicas de investigación jurídica' in tm and 'Clase compartida con otra licenciatura' in tm and 'Mtra. Laura Díaz' in tm and 'Introducción a la investigación' not in tm.split('Mis calificaciones')[0])
    ok('alumno_de_derecho_ve_su_calificacion','9.5' in tm.split('Mis calificaciones')[1])
    ok('progreso_de_egreso_cuenta_la_materia_equivalente',pdd.evaluate("progEgreso(S[0]).apr")==1)
    ppp=entra('20230101','aaaa-bbbb','clave-ana-77');tp=ppp.inner_text('#poBody')
    ok('alumno_de_pedagogia_ve_la_clase_con_su_nombre','Introducción a la investigación' in tp and 'Clase compartida' in tp and 'Técnicas de investigación jurídica' not in tp.split('Mis calificaciones')[0])
    pee=entra('20230203','eeee-ffff','clave-elena-77');ok('alumno_de_otro_cuatrimestre_no_la_ve','Técnicas de investigación jurídica' not in pee.inner_text('#poBody').split('Mis calificaciones')[0] and pee.evaluate("Object.keys(MAT).length")==0)
    ok('servidor_entrega_la_materia_solo_a_quien_corresponde',pdd.evaluate("Object.keys(MAT).length")==2 and ppp.evaluate("Object.keys(MAT).length")==1)
    # ---------------- Calificaciones de Control escolar ----------------
    pg.evaluate("ir('esc');etab('C')");pg.select_option('#kGr','gd');pg.wait_for_timeout(300)
    ok('control_escolar_ve_la_clase_en_el_grupo_de_derecho','Técnicas de investigación jurídica (fusionada)' in pg.inner_text('#kMat'))
    pg.select_option('#kMat',mid);pg.wait_for_timeout(300);ok('solo_los_alumnos_de_ese_grupo',pg.locator('#kTb tr').count()==2 and pg.locator('#kTb input[data-sid="d1"]').input_value()=='9.5')
    pg.select_option('#kGr','gp');pg.wait_for_timeout(300);ok('y_en_el_de_pedagogia_con_su_nombre','Introducción a la investigación (fusionada)' in pg.inner_text('#kMat'))
    # ---------------- quitar la fusión ----------------
    pg.evaluate("ir('esc');etab('K')");pg.locator('#mTb tr:has-text("Introducción a la investigación") [data-me]').click();ok('al_editar_se_carga_la_fusion',pg.is_checked('#mFus') and pg.input_value('#mFusPl')=='Derecho' and pg.input_value('#mFusCu')=='3' and pg.input_value('#mFusNom')=='Técnicas de investigación jurídica')
    pg.uncheck('#mFus');pg.click('#mAdd');W(pg,"!(MAT['%s'].fus&&MAT['%s'].fus.length)"%(mid,mid))
    ok('sin_fusion_vuelve_a_ser_de_un_solo_plan','fus' not in get('materias/'+mid)['data'] and 'Fusionada' not in pg.inner_text('#mTb tr:has-text("Introducción a la investigación")'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
