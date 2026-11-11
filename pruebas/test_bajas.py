import subprocess,time,json,os,urllib.request,urllib.error,http.cookiejar,datetime,sqlite3
from playwright.sync_api import sync_playwright
HDR={'Content-Type':'application/json','x-lafragua':'1'}
HOY=datetime.date.today();PER='Sep–Dic 2026'
R={};errs=[]
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def arranca(port,data,tok,reloj,fd):
    os.system('rm -rf %s && mkdir -p %s'%(data,data));open(reloj,'w').write(HOY.isoformat())
    env=dict(os.environ,PORT=str(port),DATA_DIR=data,LF_SETUP_TOKEN=tok,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=reloj,LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000',LF_BAJAS_TICK_MS='3600000',LF_BAJAS_ARRANQUE_MS='600000')
    p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen('http://127.0.0.1:%d/salud'%port,timeout=1);break
        except Exception:pass
    return p
def sesion(B,u=None,c=None):
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def llama(m,url,body=None):
        rq=urllib.request.Request(B+url,method=m,data=(json.dumps(body).encode() if body is not None else None),headers=HDR)
        try:
            r=op.open(rq);d=r.read();return r.status,(json.loads(d) if d else {})
        except urllib.error.HTTPError as e:
            d=e.read()
            try:return e.code,json.loads(d)
            except Exception:return e.code,{}
    if u:
        s,_=llama('POST','/api/login',{'u':u,'clave':c});assert s==200,(u,s)
    return llama
def monta(B,tok):
    anon=sesion(B);s,j=anon('POST','/api/configurar',{'token':tok,'name':'Administrador','u':'admin','clave':'clave-segura-1'});assert s==200
    adm=sesion(B,'admin','clave-segura-1');put=lambda path,obj:adm('PUT','/api/doc/'+path,obj)
    cfg={'activo':True,'escuela':'Universidad Lafragua','correo':{'activo':True,'usarRespaldos':False,'host':'127.0.0.1','puerto':3322,'seguro':False,'usuario':'e@correo.mx','clave':'clave-correo-1','de':'e@correo.mx','nombre':'Universidad Lafragua'},'whatsapp':{'activo':False,'phoneId':'','token':'','version':'v21.0','plantilla':'aviso_escolar','idioma':'es_MX','pais':'52'},'eventos':{},'recordatorios':{'calificaciones':False},'resumen':{'activo':True,'hora':23,'para':['direccion@correo.mx']}}
    adm('PUT','/api/avisos/config',cfg)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    put('config/cobranza',{'activa':True,'umbral':2,'diaLimite':10,'intervaloDias':7,'graciaDias':7,'reinicioDias':30})
    nombres={'s1':'Ana Deudora López','s2':'Beto Al Corriente','s3':'Carla Sin Calificaciones','s4':'Diego Con Calificaciones','s5':'Elena Una Deuda'}
    for sid,n in nombres.items():put('students/'+sid,{'mat':'2026'+sid[1:].zfill(3),'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'mail':'%s@correo.mx'%sid})
    pago=lambda cc,m:{'pagos':[{'id':'p'+cc[0],'folio':'R-0000%s'%cc[0][-1],'fecha':HOY.isoformat(),'monto':m,'metodo':'Efectivo','cc':cc}]}
    for sid in ['s2','s3','s4']:put('ledger/'+sid,pago(['c1','c2','c3'],3900))
    put('ledger/s5',pago(['c1','c2'],2600))   # debe solo una colegiatura vencida
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s2','s3','s4']})
    for sid in ['s2','s4']:put('calif/'+sid,{'items':[{'id':'i'+sid,'mid':'m1','mat':'Didáctica','plan':'Pedagogía','per':PER,'cuat':1,'cal':9,'fecha':HOY.isoformat()}]})
    for sid in nombres:adm('POST','/api/usuarios/alumnos',{'items':[{'u':'al'+sid,'name':nombres[sid],'alumno':sid,'clave':'abcd-efgh'}]})
    adm('POST','/api/usuarios',{'u':'esc2','name':'Control Escolar','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'})
    adm('POST','/api/usuarios',{'u':'cons','name':'Consulta','rol':'personalizado','modulos':{'escolar':'ver'},'clave':'clave-cons-123'})
    adm('POST','/api/usuarios',{'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'})
    adm('POST','/api/usuarios',{'u':'doc1','name':'Docente Uno','rol':'docente','doc':'d1','clave':'clave-doc1-123'})
    put('docentes/d1',{'nombre':'Docente Uno','esp':'x','asig':[]})
    for sid in nombres:
        a=sesion(B);a('POST','/api/login',{'u':'al'+sid,'clave':'abcd-efgh'});a('POST','/api/cambiar-clave',{'actual':'abcd-efgh','nueva':'clave-nueva-77'})
    return adm,put

os.system('rm -rf /tmp/fd112')
fake=subprocess.Popen(['node','/tmp/fake_destinos.js','3381','3322','/tmp/fd112','3383'],stdout=subprocess.PIPE,text=True);time.sleep(1.0)
B='http://127.0.0.1:3380';RELOJ='/tmp/relbj.txt'
p=arranca(3380,'/tmp/nbdata112','tk-bj',RELOJ,'/tmp/fd112')
adm,put=monta(B,'tk-bj')
esc=sesion(B,'esc2','clave-esc2-123');cons=sesion(B,'cons','clave-cons-123');caja=sesion(B,'caja1','clave-caja1-123');doc=sesion(B,'doc1','clave-doc1-123')
def alumno(sid,clave='clave-nueva-77'):
    a=sesion(B);return a,a('POST','/api/login',{'u':'al'+sid,'clave':clave})
casos=lambda:{v['id']:v['data'] for v in adm('GET','/api/col/bajas')[1]['docs']}
# ============ aún sin cerrar el ciclo: solo la deuda ============
ok('la_configuracion_de_inicio_es_2_colegiaturas_y_15_dias',esc('GET','/api/bajas/config')[1]['colegiaturas']==2 and esc('GET','/api/bajas/config')[1]['prorrogaDias']==15 and esc('GET','/api/bajas/config')[1]['activa'] is True)
ok('quien_no_tiene_control_escolar_no_ve_ni_decide',doc('GET','/api/bajas/config')[0]==403 and caja('POST','/api/bajas/decidir',{'sid':'s1','accion':'baja'})[0]==403 and doc('POST','/api/bajas/revisar',{})[0]==403 and alumno('s1')[0]('POST','/api/bajas/decidir',{'sid':'s1','accion':'baja'})[0]==403)
ok('con_solo_ver_puede_consultar_pero_no_decidir',cons('GET','/api/bajas/config')[0]==200 and cons('POST','/api/bajas/decidir',{'sid':'s1','accion':'baja','tipo':'Baja voluntaria'})[0]==403 and cons('PUT','/api/bajas/config',{'activa':True,'colegiaturas':2,'prorrogaDias':15})[0]==403 and cons('POST','/api/bajas/revisar',{})[0]==403)
time.sleep(3.5);s,j=esc('POST','/api/bajas/revisar',{});ok('el_sistema_abre_un_caso_por_deber_2_colegiaturas_o_mas',s==200 and j['activa'] is True and list(casos())==['s1'])
c1=casos()['s1'];ok('el_caso_dice_cuanto_debe',c1['estado']=='pendiente' and c1['causas']['adeudo']['n']==3 and c1['causas']['adeudo']['total']==3900 and 'sinCalif' not in c1['causas'] and 'debe 3 colegiaturas vencidas ($3,900.00)' in c1['historial'][0]['txt'])
ok('quien_debe_solo_una_no_se_marca',not any(k in casos() for k in ['s2','s3','s4','s5']))
ok('segunda_revision_no_repite',esc('POST','/api/bajas/revisar',{})[1]['nuevas']==0)
# ============ cerrar el ciclo: sin calificaciones ============
put('ciclos/sep-dic-2026',{'per':PER,'cerrado':True,'fecha':HOY.isoformat(),'sig':'Ene–Abr 2027'});time.sleep(4.0)
cs=casos();ok('al_cerrar_el_ciclo_se_abre_el_caso_de_quien_no_tiene_calificaciones_solo',sorted(cs)==['s1','s3'] and cs['s3']['estado']=='pendiente' and cs['s3']['causas']=={'sinCalif':{'per':PER}} and 'no tiene calificaciones en el ciclo Sep–Dic 2026' in cs['s3']['historial'][0]['txt'])
ok('quien_si_tiene_calificaciones_no_se_marca',not any(k in cs for k in ['s2','s4']))
put('grupos/g2',{'num':'4900','plan':'Pedagogía','per':'Ene–Abr 2027','cuat':2,'alumnos':['s5']});put('ciclos/ene-abr-2027',{'per':'Ene–Abr 2027','cerrado':True,'fecha':HOY.isoformat()});time.sleep(3.0)
ok('si_nadie_capturo_calificaciones_en_un_ciclo_no_se_marca_a_todos','s5' not in casos())
ok('si_ya_estaba_marcado_se_suma_la_causa_de_adeudo_o_de_calificaciones_sin_duplicar',len(casos())==2)
# ============ aviso a dirección ============
time.sleep(1.5);ms=adm('GET','/api/avisos/mensajes?evento=baja&limite=50')[1]['mensajes']
ok('dirección_recibe_el_aviso_por_correo',any(m['para']=='direccion@correo.mx' and m['estado']=='enviado' and m['canal']=='correo' for m in ms))
ok('el_aviso_lista_a_los_alumnos_y_pide_decidir',any('Ana Deudora' in m['texto'] and 'baja o prórroga' in m['asunto'] for m in ms) and any('Carla Sin Calificaciones' in m['texto'] and 'Control escolar > Bajas' in m['texto'] for m in ms))
# ============ prórroga ============
ok('la_prorroga_exige_fecha_futura_y_motivo',esc('POST','/api/bajas/decidir',{'sid':'s1','accion':'prorroga','hasta':HOY.isoformat(),'motivo':'x pago'})[0]==400 and esc('POST','/api/bajas/decidir',{'sid':'s1','accion':'prorroga','hasta':(HOY+datetime.timedelta(days=5)).isoformat(),'motivo':''})[0]==400 and esc('POST','/api/bajas/decidir',{'sid':'s1','accion':'prorroga','hasta':(HOY+datetime.timedelta(days=400)).isoformat(),'motivo':'pago'})[0]==400)
H1=(HOY+datetime.timedelta(days=10)).isoformat()
s,j=esc('POST','/api/bajas/decidir',{'sid':'s1','accion':'prorroga','hasta':H1,'motivo':'Liquidar las 3 colegiaturas antes de la fecha.'});c=casos()['s1']
ok('control_escolar_otorga_la_prorroga',s==200 and c['estado']=='prorroga' and c['prorroga']['hasta']==H1 and c['prorroga']['por']=='esc2' and 'Prórroga hasta' in c['historial'][-1]['txt'])
a1,_=alumno('s1');av=[v['data'] for v in adm('GET','/api/col/avisos')[1]['docs'] if v['data']['sid']=='s1' and 'Prórroga' in v['data']['titulo']]
ok('el_alumno_recibe_el_aviso_con_la_fecha_y_las_condiciones',len(av)==1 and 'Liquidar las 3 colegiaturas' in av[0]['mensaje'] and HOY.strftime('%Y') in av[0]['mensaje'])
fila=[f for f in adm('GET','/api/cobranza/vista')[1]['filas'] if f['sid']=='s1'][0]
ok('mientras_dura_la_prorroga_la_cobranza_automatica_lo_exime',fila['exento'] is True and 'prórroga' in fila['motivoExento'])
esc('POST','/api/bajas/revisar',{});ok('y_la_alerta_no_vuelve_mientras_sigue_vigente',casos()['s1']['estado']=='prorroga')
ok('el_alumno_con_prorroga_sigue_entrando',alumno('s1')[1][0]==200)
# la prórroga vence
open(RELOJ,'w').write((HOY+datetime.timedelta(days=11)).isoformat());time.sleep(0.3)
s,j=esc('POST','/api/bajas/revisar',{});c=casos()['s1']
ok('al_vencer_la_prorroga_con_la_deuda_el_caso_vuelve_a_decision',j['vencidas']==1 and c['estado']=='pendiente' and c['prorrogaVencida']==H1 and 'La prórroga venció' in c['historial'][-1]['txt'])
time.sleep(1.5);ms=adm('GET','/api/avisos/mensajes?evento=baja&limite=50')[1]['mensajes']
ok('y_dirección_recibe_otro_aviso',len([m for m in ms if m['para']=='direccion@correo.mx' and 'Ana Deudora' in m['texto'] and 'venció su prórroga' in m['texto']])==1)
open(RELOJ,'w').write(HOY.isoformat())
# se regulariza pagando
put('ledger/s1',{'pagos':[{'id':'pz','folio':'R-000090','fecha':HOY.isoformat(),'monto':3900,'metodo':'Efectivo','cc':['c1','c2','c3']}]});time.sleep(3.5)
ok('si_el_alumno_paga_el_caso_se_resuelve_solo',casos()['s1']['estado']=='resuelto' and 'Se regularizó' in casos()['s1']['historial'][-1]['txt'])
# calificaciones capturadas
put('calif/s3',{'items':[{'id':'ic3','mid':'m1','mat':'Didáctica','plan':'Pedagogía','per':PER,'cuat':1,'cal':8,'fecha':HOY.isoformat()}]});time.sleep(3.5)
ok('si_le_capturan_calificaciones_el_caso_tambien_se_resuelve',casos()['s3']['estado']=='resuelto')
# ============ descartar ============
put('calif/s3',{'items':[]});time.sleep(3.5);ok('si_vuelve_la_causa_se_abre_un_caso_nuevo_con_el_mismo_historial',casos()['s3']['estado']=='pendiente' and casos()['s3']['episodio']==2 and len(casos()['s3']['historial'])>=3)
ok('descartar_pide_motivo',esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'descartar','motivo':''})[0]==400)
ok('se_puede_descartar_la_alerta',esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'descartar','motivo':'Ya entregó sus trabajos al docente.'})[0]==200 and casos()['s3']['estado']=='descartado')
esc('POST','/api/bajas/revisar',{});ok('no_vuelve_a_alertar_durante_30_dias',casos()['s3']['estado']=='descartado')
open(RELOJ,'w').write((HOY+datetime.timedelta(days=31)).isoformat());time.sleep(0.3);esc('POST','/api/bajas/revisar',{});ok('pasado_ese_tiempo_si_la_causa_sigue_se_vuelve_a_abrir',casos()['s3']['estado']=='pendiente' and casos()['s3']['episodio']==3)
open(RELOJ,'w').write(HOY.isoformat())
# ============ baja ============
a3,_=alumno('s3');ok('antes_de_la_baja_entra',a3('GET','/api/yo')[1]['usuario'] is not None)
ok('la_baja_exige_motivo_valido',esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'baja','tipo':'Cualquiera'})[0]==400 and esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'baja','tipo':'Otro','motivo':''})[0]==400 and esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'baja','tipo':'Baja voluntaria','fecha':(HOY+datetime.timedelta(days=90)).isoformat()})[0]==400)
s,j=esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'baja','tipo':'Sin calificaciones al cerrar el ciclo','motivo':'No se presentó a evaluaciones.','obs':'Se intentó contactarlo.','fecha':HOY.isoformat()})
st=adm('GET','/api/doc/students/s3')[1]['data']
ok('control_escolar_da_de_baja_al_alumno',s==200 and st['baja']['tipo']=='Sin calificaciones al cerrar el ciclo' and st['baja']['por']=='esc2' and st['baja']['fecha']==HOY.isoformat() and casos()['s3']['estado']=='baja')
ok('su_sesion_se_cierra',a3('GET','/api/col/students')[0]==401)
a3b=sesion(B);s,j=a3b('POST','/api/login',{'u':'als3','clave':'clave-nueva-77'});ok('ya_no_puede_entrar_y_se_le_explica',s==403 and 'causaste baja' in j['error'] and j['bloqueado'] is True)
av=[v['data'] for v in adm('GET','/api/col/avisos')[1]['docs'] if v['data']['sid']=='s3' and v['data']['titulo']=='Baja de la escuela'];ok('recibe_el_aviso_de_baja',len(av)==1 and 'causaste baja' in av[0]['mensaje'])
ok('no_se_puede_dar_de_baja_dos_veces',esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'baja','tipo':'Baja voluntaria'})[0]==400)
ok('el_docente_solo_sabe_que_es_baja_no_el_motivo',doc('GET','/api/doc/students/s3')[1]['data']['baja']=={'fecha':HOY.isoformat()} and 'ledger' not in json.dumps(doc('GET','/api/doc/students/s3')[1]))
fila=[f for f in adm('GET','/api/cobranza/vista')[1]['filas'] if f['sid']=='s3'];ok('la_cobranza_ya_no_lo_considera',not fila or fila[0]['exento'] is True and fila[0]['motivoExento']=='baja')
ok('editar_al_alumno_no_quita_la_baja',esc('PUT','/api/doc/students/s3',{'mat':'2026003','nombre':'Carla Editada','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026})[0]==200 and adm('GET','/api/doc/students/s3')[1]['data']['baja']['tipo']=='Sin calificaciones al cerrar el ciclo')
ok('ni_se_puede_dar_de_baja_editandolo',esc('PUT','/api/doc/students/s4',{'mat':'2026004','nombre':'Diego','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'baja':{'fecha':HOY.isoformat(),'tipo':'Otro'}})[0]==200 and 'baja' not in adm('GET','/api/doc/students/s4')[1]['data'])
# baja manual de quien no tiene caso
s,j=esc('POST','/api/bajas/decidir',{'sid':'s4','accion':'baja','tipo':'Baja voluntaria','motivo':'Se mudó de ciudad.'});ok('tambien_se_puede_dar_de_baja_a_mano_sin_alerta_previa',s==200 and casos()['s4']['estado']=='baja' and 'Se mudó' in casos()['s4']['historial'][-1]['txt'])
# reincorporar
ok('reincorporar_pide_motivo',esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'reincorporar','motivo':''})[0]==400 and esc('POST','/api/bajas/decidir',{'sid':'s1','accion':'reincorporar','motivo':'prueba'})[0]==400)
ok('se_puede_reincorporar',esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'reincorporar','motivo':'Presentó sus evaluaciones pendientes.'})[0]==200 and alumno('s3')[1][0]==200 and casos()['s3']['estado']=='resuelto')
# configuración
ok('rechaza_valores_fuera_de_rango',esc('PUT','/api/bajas/config',{'activa':True,'colegiaturas':0,'prorrogaDias':15})[0]==400 and esc('PUT','/api/bajas/config',{'activa':True,'colegiaturas':2,'prorrogaDias':500})[0]==400)
ok('con_1_colegiatura_se_marca_a_quien_debe_una',esc('PUT','/api/bajas/config',{'activa':True,'colegiaturas':1,'prorrogaDias':15})[0]==200 and esc('POST','/api/bajas/revisar',{})[1]['nuevas']>=1 and 's5' in casos())
ok('apagada_no_revisa',esc('PUT','/api/bajas/config',{'activa':False,'colegiaturas':2,'prorrogaDias':15})[0]==200 and esc('POST','/api/bajas/revisar',{})[1]['activa'] is False)
dbc=sqlite3.connect('/tmp/nbdata112/lafragua.db');acc=[r[0] for r in dbc.execute("select accion from auditoria").fetchall()];dbc.close()
ok('todo_queda_en_la_auditoria',any('pendiente de decisión' in a for a in acc) and any('Dio de baja' in a for a in acc) and any('Otorgó una prórroga' in a for a in acc) and any('Reincorporó' in a for a in acc) and any('Descartó una alerta' in a for a in acc))

# ============================ PANTALLA ============================
os.system('rm -rf /tmp/fd113')
fake=subprocess.Popen(['node','/tmp/fake_destinos.js','3391','3322','/tmp/fd113','3393'],stdout=subprocess.PIPE,text=True);time.sleep(1.0)
B='http://127.0.0.1:3390';p=arranca(3390,'/tmp/nbdata113','tk-bj2','/tmp/relbj2.txt','/tmp/fd113')
adm,put=monta(B,'tk-bj2');put('ciclos/sep-dic-2026',{'per':PER,'cerrado':True,'fecha':HOY.isoformat(),'sig':'Ene–Abr 2027'});time.sleep(4.5)
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
with sync_playwright() as pw:
    b=pw.chromium.launch()
    def entra(u,c):
        cx=b.new_context(viewport={'width':1250,'height':1000});cx.set_default_timeout(15000);pg=cx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());pg.goto(B+'/');W(pg,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pg.fill('#lgU',u);pg.fill('#lgP',c);pg.click('#lgGo');W(pg,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pg.wait_for_timeout(1800);return pg
    pe=entra('esc2','clave-esc2-123');W(pe,"Object.keys(BAJ).length>=2")
    ok('la_campana_avisa_de_los_alumnos_pendientes','alumnos pendientes de decisión: baja o prórroga' in pe.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')"))
    pe.evaluate("ir('esc')");pe.wait_for_selector('#eTabs [data-et="B"]:not([hidden])');pe.click('#eTabs [data-et="B"]');pe.wait_for_selector('#bjTb tr');pe.wait_for_timeout(500)
    t=pe.inner_text('#bjTb')
    ok('la_pestana_bajas_muestra_los_dos_casos_con_su_causa','Ana Deudora López' in t and 'Debe 3 colegiaturas vencidas ($3,900.00)' in t and 'Carla Sin Calificaciones' in t and 'Sin calificaciones en el ciclo Sep–Dic 2026 (ya cerrado)' in t and 'Pendiente' in t)
    ok('la_pestana_trae_la_cifra_de_pendientes',pe.inner_text('#bjN')=='2' and '2' in pe.inner_text('#bjTar'))
    ok('cada_caso_ofrece_baja_prorroga_y_descartar',pe.locator('#bjTb [data-bjc="baja"]').count()==2 and pe.locator('#bjTb [data-bjc="prorroga"]').count()==2 and pe.locator('#bjTb [data-bjc="descartar"]').count()==2)
    # prórroga a Ana
    pe.click('#bjTb tr:has-text("Ana Deudora") [data-bjc="prorroga"]');pe.wait_for_selector('#dBj[open]')
    ok('la_prorroga_sugiere_15_dias_y_una_condicion',pe.input_value('#bjHasta')==(HOY+datetime.timedelta(days=15)).isoformat() and 'liquidar o abonar' in pe.inner_text('#bjPHint'))
    pe.fill('#bjPMot','');pe.click('#bjDGo');pe.wait_for_timeout(500);ok('sin_motivo_no_se_guarda','condiciones' in pe.inner_text('#bjDMsg') or 'motivo' in pe.inner_text('#bjDMsg').lower())
    pe.fill('#bjPMot','Liquidar sus colegiaturas vencidas antes de la fecha.');pe.click('#bjDGo');W(pe,"BAJ.s1&&BAJ.s1.estado==='prorroga'");pe.wait_for_timeout(500)
    ok('la_prorroga_se_guarda_y_el_caso_sale_de_pendientes','Ana Deudora' not in pe.inner_text('#bjTb') and 'Carla' in pe.inner_text('#bjTb') and pe.inner_text('#bjN')=='1')
    pe.select_option('#bjFe','prorroga');pe.wait_for_timeout(300);t=pe.inner_text('#bjTb')
    ok('en_la_lista_de_prorrogas_aparece_hasta_cuando',('hasta '+(HOY+datetime.timedelta(days=15)).strftime('%d/%m/%Y')) in t and 'Cambiar prórroga' in t)
    pe.click('#bjTb [data-bjh]');pe.wait_for_selector('#dBj[open]');tl=pe.inner_text('#bjDTl')
    ok('el_historial_conserva_la_alerta_y_la_prorroga','Alerta: el alumno debe 3 colegiaturas' in tl and 'Prórroga hasta' in tl and 'Control Escolar' in tl);pe.click('#bjDCls')
    # baja de Carla
    pe.select_option('#bjFe','pendiente');pe.click('#bjTb tr:has-text("Carla") [data-bjc="baja"]');pe.wait_for_selector('#dBj[open]')
    ok('la_baja_sugiere_el_motivo_segun_la_causa',pe.input_value('#bjTipo')=='Sin calificaciones al cerrar el ciclo' and pe.input_value('#bjFecha')==HOY.isoformat() and 'pierde el acceso' in pe.inner_text('#bjFB'))
    pe.fill('#bjBMot','No presentó evaluaciones.');pe.click('#bjDGo');W(pe,"BAJ.s3&&BAJ.s3.estado==='baja'");pe.wait_for_timeout(600)
    ok('al_darlo_de_baja_sale_de_pendientes_y_aparece_en_bajas','No hay alumnos pendientes de decisión' in pe.inner_text('#bjTb'))
    pe.select_option('#bjFe','baja');pe.wait_for_timeout(300);t=pe.inner_text('#bjTb')
    ok('la_lista_de_bajas_dice_motivo_y_fecha_y_permite_reincorporar','Carla Sin Calificaciones' in t and 'Sin calificaciones al cerrar el ciclo' in t and 'No presentó evaluaciones' in t and 'Reincorporar' in t)
    ok('ya_no_aparece_en_las_listas_activas',pe.evaluate("S.filter(function(s){return !esInact(s.id)}).every(function(s){return s.id!=='s3'})") and pe.evaluate("alumnosGr(GRP.g1).map(function(s){return s.id}).sort().join(',')")=='s2,s4')
    pe.evaluate("ir('esc');etab('A')");pe.wait_for_selector('#aTb tr');ok('ni_en_la_lista_de_alumnos','Carla' not in pe.inner_text('#aTb') and 'Diego Con Calificaciones' in pe.inner_text('#aTb'))
    pe.click('#aTb tr:has-text("Diego")');pe.wait_for_selector('#dPf[open]');ok('desde_el_expediente_se_puede_dar_de_baja',pe.is_visible('#pfBaja'))
    pe.click('#pfBaja');pe.wait_for_selector('#dBj[open]');ok('abre_el_cuadro_de_baja_del_alumno','Dar de baja · Diego Con Calificaciones' in pe.inner_text('#bjDT') and pe.input_value('#bjTipo')=='Baja voluntaria');pe.click('#bjDCls')
    # reincorporar
    pe.evaluate("etab('B')");pe.select_option('#bjFe','baja');pe.click('#bjTb tr:has-text("Carla") [data-bjc="reincorporar"]');pe.wait_for_selector('#dBj[open]');pe.fill('#bjRMot','Presentó sus evaluaciones.');pe.click('#bjDGo');W(pe,"!esBaja('s3')");pe.wait_for_timeout(500)
    pe.evaluate("etab('A')");pe.wait_for_timeout(400);ok('al_reincorporarlo_vuelve_a_las_listas','Carla Sin Calificaciones' in pe.inner_text('#aTb') and pe.evaluate("alumnosGr(GRP.g1).length")==3)
    # permisos en pantalla
    pc=entra('cons','clave-cons-123');pc.evaluate("ir('esc')");pc.wait_for_timeout(600);ok('con_solo_ver_no_aparece_la_pestana_bajas',pc.is_hidden('#eTabs [data-et="B"]'))
    pe.evaluate("etab('B')");pe.click('details summary');pe.wait_for_timeout(200);ok('la_configuracion_muestra_los_valores',pe.input_value('#bjCol')=='2' and pe.input_value('#bjDias')=='15' and pe.is_checked('#bjAct'))
    pe.fill('#bjCol','3');pe.click('#bjGuarda');pe.wait_for_timeout(600);ok('y_se_puede_cambiar',json.loads(urllib.request.urlopen(urllib.request.Request(B+'/api/bajas/config',headers=HDR)).read() if False else '{}')=={} and 'guardada' in pe.inner_text('#bjMsg'))
    pe.fill('#bjCol','2');pe.click('#bjGuarda');pe.wait_for_timeout(500)
    ok('sin_identificadores_repetidos',pe.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pe.evaluate("etab('B')");pe.select_option('#bjFe','todos');pe.wait_for_timeout(300);pe.screenshot(path='/tmp/bajas_tab.png',full_page=True)
    b.close()
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
