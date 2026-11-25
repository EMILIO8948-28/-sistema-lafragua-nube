"""Reinscripción en línea: configuración, ventana de fechas, revisión de adeudo, respuesta del alumno, permisos, validación, cascada y pantallas."""
import subprocess,time,json,os,re,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3167;B='http://127.0.0.1:%d'%PORT;DD='/tmp/nbdata_rq'
ENVV=dict(os.environ,LF_SIN_CONTACTO='1',PORT=str(PORT),DATA_DIR=DD,LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf %s && mkdir -p %s'%(DD,DD))
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
HDR={'Content-Type':'application/json','x-lafragua':'1'}
PER='Sep–Dic 2026'
def W(pg,js,t=20):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&typeof DBH!=='undefined'&&DBH!==null")
    def raw(cx,path,o,m='put'):return getattr(cx.request,m)(B+'/api/doc/'+path,data=json.dumps(o),headers=HDR)
    def put(path,o):
        r=raw(ctx,path,o);assert r.status==200,(path,r.status,r.text()[:200])
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':'Derecho','n':36,'col':1500,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    for i,(n,pl) in enumerate([('Ana López','Pedagogía'),('Beto Mena','Pedagogía'),('Carla Díaz','Derecho'),('Dani Ruiz','Pedagogía')],1):put('students/s%d'%i,{'mat':'100%d'%i,'nombre':n,'carrera':pl,'programa':pl,'ingreso':(2026 if i==3 else 2027),'nuevo':False})
    put('grupos/g1',{'num':'1111','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2']});put('grupos/g2',{'num':'2222','plan':'Derecho','per':PER,'cuat':1,'alumnos':['s3']})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[]});put('docentes/d2',{'nombre':'Prof. Dos','esp':'Historia','asig':[]})
    def usr(u,name,rol,modulos=None,doc=None):
        d={'u':u,'name':name,'rol':rol,'clave':'clave-%s-123'%u}
        if modulos is not None:d['modulos']=modulos
        if doc:d['doc']=doc
        r=ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR);assert r.status==200,(u,r.status,r.text())
    usr('prof1','Prof. Uno','docente',doc='d1');usr('prof2','Prof. Dos','docente',doc='d2');usr('esc1','Esc Uno','personalizado',{'escolar':'editar'});usr('ver1','Eva Ver','personalizado',{'escolar':'ver'})
    nombres=['Ana López','Beto Mena','Carla Díaz','Dani Ruiz']
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'100%d'%i,'name':nombres[i-1],'alumno':'s%d'%i,'clave':'abcd-efg%d'%i} for i in range(1,5)]}),headers=HDR)
    def sesion(u,c):
        cx=b.new_context(viewport={'width':1200,'height':950});r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status,r.text());return cx
    def alumno(i):
        cx=sesion('100%d'%i,'abcd-efg%d'%i);cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efg%d'%i,'nueva':'clave-nueva-7%d'%i}),headers=HDR);return sesion('100%d'%i,'clave-nueva-7%d'%i)
    AL=[alumno(i) for i in range(1,5)];P1=sesion('prof1','clave-prof1-123');P2=sesion('prof2','clave-prof2-123');E1=sesion('esc1','clave-esc1-123');V1=sesion('ver1','clave-ver1-123')
    hoy=datetime.date.today();viejo=(hoy-datetime.timedelta(days=10)).isoformat();futuro=(hoy+datetime.timedelta(days=30)).isoformat()
    C=lambda t,para,**k:dict({'titulo':t,'cuerpo':'Texto del comunicado '+t,'para':para,'importante':False,'hasta':'','activo':True,'fecha':hoy.isoformat(),'autor':'Esc Uno'},**k)
    DOC=lambda i:(ctx.request.get(B+'/api/doc/reinscripciones/'+i).json().get('data') or {})
    DOCG=lambda i:(ctx.request.get(B+'/api/doc/grupos/'+i).json().get('data') or {})
    CFG=lambda **k:dict({'abierta':True,'periodo':'Ene–Abr 2027','desde':'','hasta':'','mensaje':'Confirma tu lugar','bloquea':True},**k)
    GET=lambda cx,p:cx.request.get(B+'/api/reinscripcion/'+p)
    POST=lambda cx,p,o:cx.request.post(B+'/api/reinscripcion/'+p,data=json.dumps(o),headers=HDR)
    # ---- validación y permisos de la configuración ----
    ok('cfg_sin_booleano_400',raw(E1,'reinscripciones/_config',CFG(abierta='si')).status==400)
    ok('cfg_fecha_mala_400',raw(E1,'reinscripciones/_config',CFG(desde='ayer')).status==400)
    ok('cfg_cierre_antes_400',raw(E1,'reinscripciones/_config',CFG(desde='2026-12-10',hasta='2026-12-01')).status==400)
    ok('escolar_ver_no_configura',raw(V1,'reinscripciones/_config',CFG()).status in (401,403))
    ok('alumno_no_configura',raw(AL[0],'reinscripciones/_config',CFG()).status in (401,403))
    ok('docente_no_configura',raw(P1,'reinscripciones/_config',CFG()).status in (401,403))
    ok('alumno_no_escribe_su_respuesta_directo',raw(AL[0],'reinscripciones/s1',{'decision':'continuo','periodo':'Ene–Abr 2027'}).status in (401,403))
    ok('respuesta_decision_mala_400',raw(E1,'reinscripciones/s1',{'decision':'tal vez','periodo':'x'}).status==400)
    ok('nada_guardado_con_errores',ctx.request.get(B+'/api/col/reinscripciones').json()['docs']==[])
    # ---- cerrada / sin configurar ----
    e=GET(AL[0],'estado').json()
    ok('sin_config_cerrada',e['abierta']==False and e['respuesta'] is None)
    ok('responder_cerrada_409',POST(AL[0],'responder',{'decision':'continuo'}).status==409)
    ok('solo_alumnos_estado_403',GET(P1,'estado').status==403 and GET(ctx,'estado').status==403)
    ok('solo_alumnos_responder_403',POST(P1,'responder',{'decision':'continuo'}).status==403)
    # ---- abierta ----
    ok('escolar_abre',raw(E1,'reinscripciones/_config',CFG()).status==200)
    AVS=lambda:[v['data'] for v in ctx.request.get(B+'/api/col/avisos').json()['docs']]
    TA='Reinscripción abierta: Ene–Abr 2027'
    ok('abrir_avisa_a_los_4_alumnos',sorted(a['sid'] for a in AVS() if a['titulo']==TA)==['s1','s2','s3','s4'])
    ok('aviso_apunta_al_portal',all('portal' in a['mensaje'] and 'Ene–Abr 2027' in a['mensaje'] for a in AVS() if a['titulo']==TA))
    raw(E1,'reinscripciones/_config',CFG(mensaje='Otro texto'))
    ok('guardar_de_nuevo_no_repite_aviso',len([a for a in AVS() if a['titulo']==TA])==4)
    raw(E1,'reinscripciones/_config',CFG())
    e=GET(AL[0],'estado').json()
    ok('estado_abierta',e['abierta']==True and e['periodo']=='Ene–Abr 2027' and e['mensaje']=='Confirma tu lugar' and e['vencidas']==0)
    ok('decision_invalida_400',POST(AL[0],'responder',{'decision':'quiza'}).status==400)
    ok('no_continuo_sin_motivo_400',POST(AL[3],'responder',{'decision':'no_continuo','motivo':' '}).status==400)
    ok('sin_respuesta_aun',GET(AL[0],'estado').json()['respuesta'] is None)
    r=POST(AL[0],'responder',{'decision':'continuo'});ok('alumno_confirma',r.status==200)
    d=DOC('s1')
    ok('doc_guardado',d.get('decision')=='continuo' and d.get('sid')=='s1' and d.get('periodo')=='Ene–Abr 2027' and d.get('nombre')=='Ana López' and d.get('nombre')=='Ana López' and d.get('mat')=='1001' and d.get('periodo')=='Ene–Abr 2027' and len(d.get('fecha',''))==10)
    ok('estado_con_respuesta',GET(AL[0],'estado').json()['respuesta']['decision']=='continuo')
    ok('alumno_no_suplanta',(POST(AL[1],'responder',{'decision':'continuo','sid':'s1'}).status==200) and DOC('s1')['nombre']=='Ana López' and DOC('s2')['sid']=='s2')
    r=POST(AL[3],'responder',{'decision':'no_continuo','motivo':'Cambio de ciudad'});ok('no_continua_con_motivo',r.status==200)
    d=DOC('s4');ok('motivo_guardado',d['decision']=='no_continuo' and d['motivo']=='Cambio de ciudad')
    ok('puede_cambiar_respuesta',POST(AL[3],'responder',{'decision':'continuo'}).status==200 and DOC('s4')['decision']=='continuo' and DOC('s4')['motivo']=='' and DOC('s4')['cambios']==1)
    # ---- adeudo ----
    e=GET(AL[2],'estado').json();ok('estado_con_adeudo',e['vencidas']>0 and e['vencido']>0)
    r=POST(AL[2],'responder',{'decision':'continuo'});ok('adeudo_bloquea_409',r.status==409 and 'vencida' in r.json()['error'] and not DOC('s3').get('decision'))
    ok('adeudo_si_puede_decir_no_continuo',POST(AL[2],'responder',{'decision':'no_continuo','motivo':'Motivos económicos'}).status==200)
    raw(E1,'reinscripciones/_config',CFG(bloquea=False))
    ok('sin_revision_de_adeudo_permite',POST(AL[2],'responder',{'decision':'continuo'}).status==200)
    d=DOC('s3');ok('guarda_adeudo_al_confirmar',d['decision']=='continuo' and d['vencidas']>0)
    # ---- ventana de fechas ----
    raw(E1,'reinscripciones/_config',CFG(desde=futuro))
    ok('antes_de_apertura_cerrada',GET(AL[0],'estado').json()['abierta']==False and POST(AL[0],'responder',{'decision':'continuo'}).status==409)
    raw(E1,'reinscripciones/_config',CFG(desde=viejo,hasta=(hoy-datetime.timedelta(days=1)).isoformat()))
    ok('despues_del_cierre_cerrada',GET(AL[0],'estado').json()['abierta']==False and POST(AL[0],'responder',{'decision':'continuo'}).status==409)
    raw(E1,'reinscripciones/_config',CFG(desde=viejo,hasta=hoy.isoformat()))
    ok('ultimo_dia_abierta',GET(AL[0],'estado').json()['abierta']==True)
    raw(E1,'reinscripciones/_config',CFG(abierta=False))
    ok('cerrada_manual',GET(AL[0],'estado').json()['abierta']==False and POST(AL[0],'responder',{'decision':'continuo'}).status==409)
    # ---- nuevo periodo: las respuestas anteriores no cuentan ----
    raw(E1,'reinscripciones/_config',CFG(periodo='May–Ago 2027'))
    e=GET(AL[0],'estado').json();ok('nuevo_periodo_sin_respuesta',e['respuesta'] is None and e['periodo']=='May–Ago 2027')
    # ---- avisos: recordatorio automático y manual ----
    titR=lambda p:'Recordatorio: reinscripción '+p
    raw(E1,'reinscripciones/_config',CFG(periodo='Sep–Dic 2027',hasta=(hoy+datetime.timedelta(days=1)).isoformat()))
    ok('abrir_otro_periodo_avisa',len([a for a in AVS() if a['titulo']=='Reinscripción abierta: Sep–Dic 2027'])==4)
    ok('aviso_con_fecha_limite',all('Tienes hasta el' in a['mensaje'] for a in AVS() if a['titulo']=='Reinscripción abierta: Sep–Dic 2027'))
    ok('recordatorio_automatico_cerca_del_cierre',len([a for a in AVS() if a['titulo']==titR('Sep–Dic 2027')])==4)
    ok('manual_mismo_dia_409',POST(E1,'recordar',{}).status==409)
    raw(E1,'reinscripciones/_config',CFG(periodo='Ene–Abr 2028'))
    ok('alumno_no_recuerda',POST(AL[0],'recordar',{}).status==403)
    ok('escolar_ver_no_recuerda',POST(V1,'recordar',{}).status in (401,403))
    ok('docente_no_recuerda',POST(P1,'recordar',{}).status==403)
    r=POST(E1,'recordar',{});ok('recordatorio_manual_ok',r.status==200 and r.json()['n']==4 and len([a for a in AVS() if a['titulo']==titR('Ene–Abr 2028')])==4)
    ok('recordatorio_manual_segundo_409',POST(E1,'recordar',{}).status==409)
    raw(E1,'reinscripciones/_config',CFG(periodo='Ene–Abr 2029',abierta=False))
    r=POST(E1,'recordar',{});ok('recordar_cerrada_409',r.status==409 and 'no está abierta' in r.json()['error'])
    # ---- limite de intentos ----
    n429=0
    for _ in range(25):
        if POST(AL[1],'responder',{'decision':'quiza'}).status==429:n429+=1
    ok('limite_de_intentos',n429>0)
    # ---- auditoría ----
    # ---- pantalla de Control escolar ----
    raw(E1,'reinscripciones/_config',CFG(periodo='Ene–Abr 2027'))
    ce=b.new_context(viewport={'width':1200,'height':950});ce.request.post(B+'/api/login',data=json.dumps({'u':'esc1','clave':'clave-esc1-123'}),headers=HDR)
    pg2=pagina(ce);pg2.goto(B+'/');W(pg2,"typeof APP!=='undefined'&&APP!==null&&typeof DBH!=='undefined'&&DBH!==null&&S.length==4")
    W(pg2,"typeof ir==='function'");pg2.evaluate("ir('esc');etab('Q')")
    W(pg2,"!document.getElementById('eQ').hidden")
    W(pg2,"document.getElementById('rqTbl').rows.length==4")
    ok('ui_resumen',pg2.evaluate("document.getElementById('rqRes').textContent").count('Ene–Abr 2027')==1 and 'sin responder' in pg2.inner_text('#rqRes'))
    ok('ui_cuenta',pg2.evaluate("document.getElementById('rqRes').textContent.indexOf('4 continúan')>=0 && document.getElementById('rqRes').textContent.indexOf('0 no continúan')>=0"))
    pg2.select_option('#rqFil','pend');W(pg2,"document.getElementById('rqTbl').rows.length==1")
    ok('ui_filtro_pend_vacio',pg2.evaluate("document.getElementById('rqTbl').rows[0].textContent")=='No hay alumnos con ese filtro.')
    pg2.select_option('#rqFil','');pg2.fill('#rqBus','Carla');W(pg2,"document.getElementById('rqTbl').rows.length==1")
    ok('ui_busqueda',pg2.evaluate("document.getElementById('rqTbl').rows[0].textContent.indexOf('Carla')>=0"))
    pg2.fill('#rqBus','')
    pg2.fill('#rqPer','Sep–Dic 2027');pg2.fill('#rqDes','2027-08-01');pg2.fill('#rqHas','2027-08-31');pg2.check('#rqAbi');pg2.click('#rqGuarda')
    W(pg2,"document.getElementById('rqMsgS').textContent.indexOf('Guardado')==0")
    c=DOC('_config');ok('ui_guarda_config',c['periodo']=='Sep–Dic 2027' and c['abierta']==True and c['desde']=='2027-08-01' and c['hasta']=='2027-08-31')
    pg2.fill('#rqHas','2027-07-01');pg2.click('#rqGuarda');W(pg2,"document.getElementById('rqMsgS').textContent.indexOf('cierre')>=0")
    ok('ui_valida_fechas',DOC('_config')['hasta']=='2027-08-31')
    raw(E1,'reinscripciones/_config',CFG(periodo='Ene–Abr 2027'))
    put('grupos/g3',{'num':'3333','plan':'Pedagogía','per':'Ene–Abr 2027','cuat':2,'alumnos':[]});put('grupos/g4',{'num':'4444','plan':'Derecho','per':'Ene–Abr 2027','cuat':2,'alumnos':[]})
    pg2.reload();W(pg2,"typeof APP!=='undefined'&&APP!==null&&S.length==4");pg2.evaluate("ir('esc');etab('Q')");W(pg2,"document.getElementById('rqTbl').rows.length==4")
    with pg2.expect_download() as dl:pg2.click('#rqCsv')
    csv=open(dl.value.path(),encoding='utf-8-sig').read();ok('ui_csv',csv.startswith('Periodo,Alumno') and 'Ana López' in csv and 'Continúa' in csv and csv.count('\n')>=4)
    # asignación a grupos del nuevo periodo
    pg2.click('#rqAsig');W(pg2,"document.getElementById('rqAsigR').textContent.indexOf('3 asignados')>=0")
    ok('asig_pedagogia_a_g3',sorted(DOCG('g3')['alumnos'])==['s1','s2'])
    ok('asig_derecho_a_g4',DOCG('g4')['alumnos']==['s3'])
    ok('asig_avisa_sin_grupo_actual','sin grupo actual' in pg2.inner_text('#rqAsigR'))
    ok('asig_columna_grupo_nuevo',pg2.evaluate("[].some.call(document.getElementById('rqTbl').rows,function(r){return r.textContent.indexOf('Ana López')>=0&&r.textContent.indexOf('3333')>=0&&r.textContent.indexOf('1111')>=0})"))
    pg2.click('#rqAsig');W(pg2,"document.getElementById('rqAsigR').textContent.indexOf('Nada que asignar')>=0")
    ok('asig_segunda_vez_no_duplica',sorted(DOCG('g3')['alumnos'])==['s1','s2'] and DOCG('g4')['alumnos']==['s3'])
    # recordatorio manual desde la pantalla
    put('students/s5',{'mat':'1005','nombre':'Eli Paz','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2027,'nuevo':False})
    W(pg2,"S.length==5")
    pg2.click('#rqRec');W(pg2,"document.getElementById('rqMsgS').textContent.indexOf('Recordatorio enviado a 1 alumno')>=0")
    ok('ui_recordatorio_solo_a_pendientes',len([a for a in AVS() if a['titulo']==titR('Ene–Abr 2027')])==1)
    pg2.click('#rqRec');W(pg2,"document.getElementById('rqMsgS').textContent.indexOf('ya se envió')>=0")
    ok('ui_recordatorio_una_vez_al_dia',len([a for a in AVS() if a['titulo']==titR('Ene–Abr 2027')])==1)
    # no continúa -> baja
    raw(E1,'reinscripciones/s5',{'sid':'s5','nombre':'Eli Paz','mat':'1005','periodo':'Ene–Abr 2027','decision':'no_continuo','motivo':'Cambio de ciudad','fecha':hoy.isoformat()})
    W(pg2,"[].some.call(document.getElementById('rqTbl').rows,function(r){return r.querySelector('[data-rqb=s5]')})")
    pg2.click('[data-rqb=s5]');W(pg2,"document.getElementById('dBj').open")
    ok('baja_precargada',pg2.input_value('#bjTipo')=='Baja voluntaria' and 'Cambio de ciudad' in pg2.input_value('#bjBMot') and pg2.input_value('#bjSol')=='Alumno')
    pg2.click('#bjDGo');W(pg2,"!document.getElementById('dBj').open")
    st=ctx.request.get(B+'/api/doc/students/s5').json()['data'];ok('baja_registrada',bool(st.get('baja')) and st['baja']['tipo']=='Baja voluntaria')
    ok('respuesta_se_conserva',DOC('s5').get('decision')=='no_continuo')
    W(pg2,"![].some.call(document.getElementById('rqTbl').rows,function(r){return r.textContent.indexOf('Eli Paz')>=0})")
    cv=b.new_context(viewport={'width':1200,'height':950});cv.request.post(B+'/api/login',data=json.dumps({'u':'ver1','clave':'clave-ver1-123'}),headers=HDR)
    pg3=pagina(cv);pg3.goto(B+'/');W(pg3,"typeof APP!=='undefined'&&APP!==null&&typeof DBH!=='undefined'&&DBH!==null");pg3.evaluate("ir('esc')");W(pg3,"MOD==='esc'")
    ok('ui_ver_no_ve_pestana',pg3.evaluate("document.querySelector('[data-et=Q]').hidden"))
    # ---- portal del alumno ----
    raw(E1,'reinscripciones/_config',CFG(periodo='Ene–Abr 2027',abierta=True,bloquea=True))
    ca=b.new_context(viewport={'width':1200,'height':950});ca.request.post(B+'/api/login',data=json.dumps({'u':'1004','clave':'clave-nueva-74'}),headers=HDR)
    pa=pagina(ca);pa.goto(B+'/');W(pa,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'");W(pa,"document.getElementById('rqBoxP')&&document.getElementById('rqBoxP').textContent.indexOf('Reinscripción')>=0")
    ok('portal_muestra_tarjeta','Confirma tu lugar' in pa.inner_text('#rqBoxP') and 'Ene–Abr 2027' in pa.inner_text('#rqBoxP'))
    ok('portal_muestra_respuesta',pa.evaluate("document.getElementById('rqBoxP').textContent.indexOf('Ya confirmé')>=0"))
    pa.click('[data-rq=no_continuo]');ok('portal_pide_motivo',pa.evaluate("!document.getElementById('rqNoBox').hidden"))
    pa.click('[data-rq=no_ok]');W(pa,"document.getElementById('rqMsgP').textContent.indexOf('motivo')>=0")
    ok('portal_motivo_obligatorio',DOC('s4')['decision']=='continuo')
    pa.fill('#rqMot','Me mudo');pa.click('[data-rq=no_ok]');W(pa,"document.getElementById('rqBoxP').textContent.indexOf('No continuaré. Me mudo')>=0")
    d=DOC('s4');ok('portal_registra_no_continua',d['decision']=='no_continuo' and d['motivo']=='Me mudo')
    pa.click('[data-rq=continuo]');W(pa,"document.getElementById('rqBoxP').textContent.indexOf('Continuaré el siguiente periodo')>=0")
    ok('portal_cambia_a_continua',DOC('s4')['decision']=='continuo')
    cd=b.new_context(viewport={'width':1200,'height':950});cd.request.post(B+'/api/login',data=json.dumps({'u':'1003','clave':'clave-nueva-73'}),headers=HDR)
    pd=pagina(cd);pd.goto(B+'/');W(pd,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'");W(pd,"document.getElementById('rqBoxP')&&document.getElementById('rqBoxP').textContent.indexOf('Reinscripción')>=0")
    ok('portal_adeudo_aviso','vencida' in pd.inner_text('#rqBoxP'))
    ok('portal_adeudo_deshabilita',pd.evaluate("document.querySelector('[data-rq=continuo]').disabled"))
    pd.close()
    raw(E1,'reinscripciones/_config',CFG(abierta=False))
    ca2=b.new_context(viewport={'width':1200,'height':950});ca2.request.post(B+'/api/login',data=json.dumps({'u':'1002','clave':'clave-nueva-72'}),headers=HDR)
    pb=pagina(ca2);pb.goto(B+'/');W(pb,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'");time.sleep(1.2)
    ok('portal_cerrada_sin_botones',pb.evaluate("document.querySelectorAll('[data-rq]').length==0"))
    # ---- cascada al borrar alumno ----
    r=ctx.request.delete(B+'/api/doc/students/s2',headers=HDR)
    ok('borrar_alumno_ok',r.status==200)
    ok('cascada_reinscripcion',not DOC('s2').get('decision'))
    ok('config_sigue',DOC('_config').get('periodo')=='Ene–Abr 2027')
    ok('sin_errores_js',not errs)
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
if errs:print('ERRORES JS:',errs[:5])
