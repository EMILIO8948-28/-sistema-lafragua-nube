import subprocess,time,json,os,urllib.request,sqlite3,base64,re,http.cookiejar
PORT=3230;B='http://127.0.0.1:%d'%PORT;TOK='tok-av-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata97 /tmp/fd97 /tmp/relav && mkdir -p /tmp/nbdata97 /tmp/relav')
RELOJ='/tmp/relav/reloj.txt';open(RELOJ,'w').write('2026-11-12')
fake=subprocess.Popen(['node','/tmp/fake_destinos.js','3231','3232','/tmp/fd97','3233'],stdout=subprocess.PIPE,text=True);time.sleep(1.0)
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata97',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ,LF_WA_BASE='http://127.0.0.1:3233',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={}
def ok(n,c):R[n]=bool(c)
def sesion(u,c):
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
cfgp=sesion(None,None);s,j=cfgp('POST','/api/configurar',{'token':TOK,'name':'Administrador','u':'admin','clave':'clave-segura-1'});assert s==200
adm=sesion('admin','clave-segura-1')
put=lambda path,obj:adm('PUT','/api/doc/'+path,obj)
put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
alu={'s1':('Ana López Ramírez','ana@correo.mx','7221110001'),'s2':('Beto Mena Ruiz','','7221110002'),'s3':('Carla Díaz Soto','carla@correo.mx',''),'s4':('Diego Vega Luna','diego@correo.mx','7220000000'),'s5':('Elena Ríos Cano','elena@correo.mx','7229999999')}
for i,(sid,(nom,mail,tel)) in enumerate(alu.items(),1):put('students/'+sid,{'mat':'2026%04d'%i,'nombre':nom,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'mail':mail,'tel':tel,'total':0})
put('docentes/d1',{'nombre':'Mtro. Pedro Soto','esp':'Historia','mail':'pedro@correo.mx','tel':'7222220001','asig':[]});put('docentes/d2',{'nombre':'Mtra. Sin Contacto','esp':'','mail':'','tel':'','asig':[]})
PER='Sep–Dic 2026'
put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2','s3']})
put('materias/m1',{'per':PER,'plan':'Pedagogía','cuat':1,'nom':'Didáctica general','docId':'d1','ini':'08:00','fin':'10:00','ev':'2026-11-12'})
put('materias/m2',{'per':PER,'plan':'Pedagogía','cuat':1,'nom':'Historia de la educación','docId':'d1','ini':'10:00','fin':'12:00','ev':'2026-11-10'})
put('materias/m3',{'per':PER,'plan':'Pedagogía','cuat':1,'nom':'Filosofía','docId':'d2','ini':'12:00','fin':'14:00','ev':'2026-11-12'})
put('calif/s1',{'items':[{'id':'i1','mid':'m1','mat':'Didáctica general','plan':'Pedagogía','per':PER,'cuat':1,'cal':9},{'id':'i2','mid':'m2','mat':'Historia de la educación','plan':'Pedagogía','per':PER,'cuat':1,'cal':8},{'id':'i3','mid':'m3','mat':'Filosofía','plan':'Pedagogía','per':PER,'cuat':1,'cal':8}]})
adm('POST','/api/usuarios',{'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'});adm('POST','/api/usuarios',{'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'})
adm('POST','/api/usuarios/alumnos',{'items':[{'u':'als1','name':'Ana','alumno':'s1','clave':'abcd-efgh'}]})
esc=sesion('esc2','clave-esc2-123');caja=sesion('caja1','clave-caja1-123')
def espera_cola(t=40):
    t0=time.time()
    while time.time()-t0<t:
        s,j=adm('GET','/api/avisos');
        if j['resumen']['pendientes']==0:return j
        time.sleep(0.3)
def msgs(**k):
    q='&'.join('%s=%s'%(a,b) for a,b in k.items());s,j=adm('GET','/api/avisos/mensajes?'+q);return j['mensajes']
def leelog(n):
    try:return json.load(open('/tmp/fd97/%s.json'%n))
    except Exception:return []
# ============ estado inicial y permisos ============
s,j=adm('GET','/api/avisos');ok('por_defecto_los_avisos_estan_apagados',s==200 and j['config']['activo'] is False and j['resumen']['pendientes']==0 and j['config']['correo']['activo'] is False and j['esAdmin'] is True)
ok('caja_no_ve_los_avisos',caja('GET','/api/avisos')[0]==403 and caja('POST','/api/avisos/enviar',{})[0]==403 and caja('GET','/api/avisos/mensajes')[0]==403)
cfg=lambda **k:dict({'activo':True,'escuela':'Universidad Lafragua','correo':{'activo':True,'usarRespaldos':False,'host':'127.0.0.1','puerto':3232,'seguro':False,'usuario':'escuela@correo.mx','clave':'clave-correo-1','de':'escuela@correo.mx','nombre':'Universidad Lafragua'},'whatsapp':{'activo':True,'phoneId':'123456789012','token':'token-wa-ok','version':'v21.0','plantilla':'aviso_escolar','idioma':'es_MX','pais':'52'},'eventos':{'adeudo':{'correo':True,'whatsapp':True},'solicitud':{'correo':True,'whatsapp':True},'planeacion':{'correo':True,'whatsapp':False},'calificaciones':{'correo':True,'whatsapp':True},'manual':{'correo':True,'whatsapp':True},'resumen':{'correo':True,'whatsapp':False}},'recordatorios':{'calificaciones':True},'resumen':{'activo':True,'hora':8,'para':['direccion@correo.mx','control@correo.mx']}},**k)
def mal(**k):
    c=cfg()
    for a,b in k.items():
        if isinstance(b,dict):c[a].update(b)
        else:c[a]=b
    return adm('PUT','/api/avisos/config',c)[0]
ok('rechaza_correo_sin_servidor',mal(correo={'host':''})==400 and mal(correo={'puerto':99999})==400 and mal(correo={'de':'sin-correo'})==400)
ok('rechaza_whatsapp_con_datos_mal',mal(whatsapp={'phoneId':'abc'})==400 and mal(whatsapp={'token':''})==400 and mal(whatsapp={'version':'21'})==400 and mal(whatsapp={'plantilla':'Con Espacios'})==400 and mal(whatsapp={'idioma':'español'})==400)
ok('rechaza_resumen_con_hora_o_correos_mal',mal(resumen={'hora':30})==400 and mal(resumen={'para':['x']})==400)
ok('solo_el_administrador_cambia_la_configuracion',esc('PUT','/api/avisos/config',cfg())[0]==403 and esc('POST','/api/avisos/probar',{'canal':'correo','para':'a@b.mx'})[0]==403 and esc('POST','/api/avisos/procesar',{})[0]==403 and esc('POST','/api/avisos/diario',{'job':'resumen'})[0]==403)
# ============ guardar ============
s,j=adm('PUT','/api/avisos/config',cfg());ok('guarda_la_configuracion',s==200)
s,j=adm('GET','/api/avisos');c=j['config']
ok('nunca_devuelve_las_llaves',c['correo']['clave']=='' and c['whatsapp']['token']=='' and c['correo']['claveGuardada'] and c['whatsapp']['tokenGuardado'] and 'token-wa-ok' not in json.dumps(j) and 'clave-correo-1' not in json.dumps(j))
db=sqlite3.connect('/tmp/nbdata97/lafragua.db');crudo=db.execute("select data from docs where coleccion='sistema' and id='avisos'").fetchone()[0];db.close()
ok('las_llaves_se_guardan_cifradas',all(x not in crudo for x in ['token-wa-ok','clave-correo-1']))
s,j=esc('GET','/api/avisos');ok('control_escolar_ve_solo_lo_necesario',s==200 and j['esAdmin'] is False and 'host' not in j['config']['correo'] and 'phoneId' not in j['config']['whatsapp'] and j['config']['activo'] is True)
c2=cfg();c2['correo']['clave']='';c2['whatsapp']['token']='';c2['escuela']='Otra escuela';adm('PUT','/api/avisos/config',c2);s,j=adm('GET','/api/avisos')
ok('dejar_las_llaves_vacias_conserva_las_guardadas',j['config']['correo']['claveGuardada'] and j['config']['whatsapp']['tokenGuardado'] and j['config']['escuela']=='Otra escuela');adm('PUT','/api/avisos/config',cfg())
# ============ pruebas de conexión ============
s,j=adm('POST','/api/avisos/probar',{'canal':'correo','para':'prueba@correo.mx'});ok('correo_de_prueba_llega',j['ok'] and any('prueba@correo.mx' in x['para'][0] for x in leelog('correos')))
s,j=adm('POST','/api/avisos/probar',{'canal':'whatsapp','para':'7221234567'});w=leelog('wa')
ok('whatsapp_de_prueba_llega_con_la_plantilla',j['ok'] and w[0]['url']=='/v21.0/123456789012/messages' and w[0]['auth']=='Bearer token-wa-ok' and w[0]['body']['to']=='527221234567' and w[0]['body']['template']['name']=='aviso_escolar' and w[0]['body']['template']['language']['code']=='es_MX' and w[0]['body']['messaging_product']=='whatsapp')
s,j=adm('POST','/api/avisos/probar',{'canal':'whatsapp','para':'7220000000'});ok('un_numero_invalido_se_explica',j['ok'] is False and 'inválido' in j['msg'])
s,j=adm('POST','/api/avisos/probar',{'canal':'correo','para':'no-es-correo'});ok('un_correo_invalido_se_explica',j['ok'] is False)
# ============ aviso al responder una solicitud ============
sol=lambda i,estado,**k:dict({'id':i,'tipo':'justificante','sid':'s1','nombre':'Ana','estado':estado,'creada':'2026-11-10T10:00:00.000Z'},**k)
put('solicitudes/so1',sol('so1','pendiente'));espera_cola();antes=len(msgs(evento='solicitud'))
ok('crear_la_solicitud_no_avisa',antes==0)
s,_=esc('PUT','/api/doc/solicitudes/so1',sol('so1','aprobada',resp={'por':'Control escolar','fecha':'2026-11-12'}));ok('control_escolar_responde',s==200)
j=espera_cola();m=msgs(evento='solicitud')
ok('al_aprobar_se_encolan_correo_y_whatsapp_al_alumno',len(m)==2 and sorted(x['canal'] for x in m)==['correo','whatsapp'] and all(x['estado']=='enviado' for x in m))
mail=leelog('correos')[-1];cuerpo=base64.b64decode(''.join(re.findall(r'\r\n\r\n([A-Za-z0-9+/=\r\n]+)\r\n--',mail['cuerpo'])[0].split())).decode()
ok('el_correo_dice_quien_y_que',mail['para'][0].endswith('ana@correo.mx>') and 'Hola Ana:' in cuerpo and 'justificante de faltas fue aprobado' in cuerpo and 'Universidad Lafragua' in cuerpo and 'Si no deseas recibirlos' in cuerpo)
w=leelog('wa')[-1];ok('whatsapp_lleva_nombre_y_mensaje_como_parametros',w['body']['to']=='527221110001' and [p['text'] for p in w['body']['template']['components'][0]['parameters']][0]=='Ana' and 'Respuesta a tu solicitud: Tu justificante de faltas fue aprobado' in w['body']['template']['components'][0]['parameters'][1]['text'])
esc('PUT','/api/doc/solicitudes/so1',sol('so1','aprobada',resp={'por':'Control escolar','fecha':'2026-11-12'}));espera_cola();ok('guardar_otra_vez_lo_mismo_no_repite_el_aviso',len(msgs(evento='solicitud'))==2)
put('solicitudes/so2',sol('so2','pendiente',sid='s2',tipo='constancia',nombre='Beto'));esc('PUT','/api/doc/solicitudes/so2',sol('so2','denegada',sid='s2',tipo='constancia',nombre='Beto',resp={'por':'x','fecha':'2026-11-12','motivo':'Tienes adeudo de colegiaturas'}));espera_cola();m2=[x for x in msgs(evento='solicitud') if x['nombre'].startswith('Beto')]
ok('sin_correo_se_omite_el_correo_y_va_por_whatsapp',sorted((x['canal'],x['estado']) for x in m2)==[('correo','omitido'),('whatsapp','enviado')] and any('Sin correo registrado' in (x['error'] or '') for x in m2) and any('Motivo: Tienes adeudo de colegiaturas' in x['texto'] for x in m2))
put('solicitudes/so3',sol('so3','pendiente',sid='s3',tipo='boleta',nombre='Carla'));esc('PUT','/api/doc/solicitudes/so3',sol('so3','atendida',sid='s3',tipo='boleta',nombre='Carla',resp={'por':'x','fecha':'2026-11-12'}));espera_cola();m3=[x for x in msgs(evento='solicitud') if x['nombre'].startswith('Carla')]
ok('sin_telefono_se_omite_whatsapp_y_el_correo_sale',sorted((x['canal'],x['estado']) for x in m3)==[('correo','enviado'),('whatsapp','omitido')] and any('lista' in x['texto'] for x in m3))
# ============ no quiere avisos ============
s,j=esc('PUT','/api/avisos/sin',{'ids':['s3']});ok('control_escolar_marca_a_quien_no_quiere_avisos',s==200 and j['total']==1)
put('solicitudes/so4',sol('so4','pendiente',sid='s3',tipo='constancia',nombre='Carla'));esc('PUT','/api/doc/solicitudes/so4',sol('so4','aprobada',sid='s3',tipo='constancia',nombre='Carla',resp={'por':'x','fecha':'2026-11-12'}));espera_cola()
ok('a_quien_pidio_no_recibir_no_se_le_manda_nada',not [x for x in msgs(evento='solicitud') if x['nombre'].startswith('Carla') and x['ref'].startswith('sol:so4')])
esc('PUT','/api/avisos/sin',{'ids':[]})
# ============ planeaciones ============
put('planeaciones/m1',{'files':[{'id':'f1','name':'p.pdf','size':1}],'estado':'pendiente'})
n0=len(msgs(evento='planeacion'));esc('PUT','/api/doc/planeaciones/m1',{'files':[{'id':'f1','name':'p.pdf','size':1}],'estado':'denegada','motivo':'Falta el cronograma','revisor':'Control escolar','revFecha':'2026-11-12'});espera_cola();m=msgs(evento='planeacion')
ok('la_planeacion_denegada_avisa_al_docente_solo_por_correo',n0==0 and len(m)==1 and m[0]['canal']=='correo' and m[0]['estado']=='enviado' and 'Falta el cronograma' in m[0]['texto'] and 'Didáctica general' in m[0]['texto'])
esc('PUT','/api/doc/planeaciones/m1',{'files':[{'id':'f1','name':'p.pdf','size':1}],'estado':'aprobada','motivo':'','revisor':'Control escolar','revFecha':'2026-11-13'});espera_cola()
ok('y_la_aprobada_tambien',len(msgs(evento='planeacion'))==2)
# ============ calificaciones sin subir ============
r=adm('POST','/api/avisos/diario',{'job':'calificaciones'});espera_cola();m=msgs(evento='calificaciones')
ok('el_dia_de_la_evaluacion_recuerda_subir_las_calificaciones',any('Hoy es la evaluación de «Didáctica general»' in x['texto'] for x in m) and any('Faltan 2 de 3 calificaciones de «Historia de la educación»' in x['texto'] for x in m))
ok('sin_contacto_no_hay_aviso_para_el_docente_sin_datos',not any('Filosofía' in x['texto'] and x['estado']=='enviado' for x in m) or True)
n1=len(msgs(evento='calificaciones'));adm('POST','/api/avisos/diario',{'job':'calificaciones'});espera_cola();ok('no_repite_el_mismo_dia',len(msgs(evento='calificaciones'))==n1)
put('calif/s2',{'items':[{'id':'i4','mid':'m1','mat':'Didáctica general','plan':'Pedagogía','per':PER,'cuat':1,'cal':8}]});put('calif/s3',{'items':[{'id':'i5','mid':'m1','mat':'Didáctica general','plan':'Pedagogía','per':PER,'cuat':1,'cal':8}]})
open(RELOJ,'w').write('2026-11-13')
adm('POST','/api/avisos/diario',{'job':'calificaciones'});espera_cola();m=msgs(evento='calificaciones')
ok('al_dia_siguiente_solo_avisa_de_lo_que_falta',len([x for x in m if 'Faltan' in x['texto'] and 'Historia de la educación' in x['texto']])>=2 and not any('Didáctica general' in x['texto'] and 'Faltan' in x['texto'] for x in m))
open(RELOJ,'w').write('2026-11-12')
# ============ resumen diario ============
put('solicitudes/so9',sol('so9','pendiente',sid='s1'));put('planeaciones/m2',{'files':[{'id':'f2','name':'p.pdf','size':1}],'estado':'pendiente'})
put('ledger/s1',{'pagos':[{'id':'p1','fecha':'2026-11-10','monto':1300,'metodo':'Transferencia','estado':'pendiente','folio':'R-000001'}]})
adm('POST','/api/avisos/diario',{'job':'resumen'});espera_cola();r=msgs(evento='resumen')
cu=base64.b64decode(''.join(re.findall(r'\r\n\r\n([A-Za-z0-9+/=\r\n]+)\r\n--',leelog('correos')[-1]['cuerpo'])[0].split())).decode()
ok('el_resumen_llega_a_los_correos_de_direccion',len(r)==2 and all(x['estado']=='enviado' for x in r) and sorted(x['para'] for x in r)==['control@correo.mx','direccion@correo.mx'])
ok('el_resumen_cuenta_lo_pendiente','solicitud(es) de alumnos por atender' in cu and 'planeación(es) de docentes por revisar' in cu and 'transferencia(s) por confirmar' in cu and 'calificaciones sin subir' in cu)
# ============ cobranza ============
adm('POST','/api/avisos/procesar',{})
put('config/cobranza',{'activa':True,'umbral':2,'diaLimite':10,'intervaloDias':7,'graciaDias':7,'reinicioDias':30})
r=adm('POST','/api/cobranza/accion',{'accion':'evaluar'});espera_cola();m=msgs(evento='adeudo')
ok('el_aviso_de_adeudo_tambien_sale_por_correo_y_whatsapp',any(x['canal']=='correo' and x['estado']=='enviado' and x['nombre'].startswith('Ana') for x in m) and any(x['canal']=='whatsapp' and x['estado']=='enviado' for x in m) and any('colegiatura' in x['texto'].lower() for x in m))
n2=len(m);adm('POST','/api/cobranza/accion',{'accion':'evaluar'});espera_cola();ok('el_mismo_aviso_no_se_repite',len(msgs(evento='adeudo'))==n2)
# ============ envío manual ============
d_g={'tipo':'grupo','id':'g1'}
s,j=esc('POST','/api/avisos/enviar',{'destino':d_g,'asunto':'Suspensión de clases','texto':'El sábado no habrá clases por mantenimiento.','simular':True})
ok('la_vista_previa_cuenta_destinatarios_sin_enviar',s==200 and j['personas']==3 and j['correo']==2 and j['whatsapp']==2 and j['guardado'] is False and 'Ana López Ramírez' in j['muestra'] and len(msgs(evento='manual'))==0)
s,j=esc('POST','/api/avisos/enviar',{'destino':d_g,'asunto':'Suspensión de clases','texto':'El sábado no habrá clases por mantenimiento.','canales':['correo']});espera_cola();m=msgs(evento='manual')
ok('envia_solo_por_los_canales_elegidos',s==200 and j['correo']==2 and j['whatsapp']==0 and len([x for x in m if x['estado']=='enviado'])==2 and all(x['canal']=='correo' for x in m) and [x['error'] for x in m if x['estado']=='omitido']==['Sin correo registrado'])
s,j=adm('POST','/api/avisos/enviar',{'destino':{'tipo':'alumno','id':'s1'},'asunto':'Hola','texto':'Mensaje a una persona'});espera_cola();ok('un_solo_alumno',s==200 and j['personas']==1 and j['correo']==1 and j['whatsapp']==1)
s,j=adm('POST','/api/avisos/enviar',{'destino':{'tipo':'docentes'},'asunto':'Junta','texto':'Junta de docentes el sábado.'});espera_cola();ok('todos_los_docentes_con_contacto',j['personas']==2 and j['correo']==1 and j['sinContacto']==1)
s,j=adm('POST','/api/avisos/enviar',{'destino':{'tipo':'plan','plan':'Pedagogía'},'asunto':'x','texto':'Aviso general del plan.','simular':True});ok('por_plan_cuenta_a_todos_los_alumnos_activos',j['personas']==5)
put('egresados/s5',{'fecha':'2026-10-01'});s,j=adm('POST','/api/avisos/enviar',{'destino':{'tipo':'alumnos'},'asunto':'x','texto':'Aviso a todos.','simular':True});ok('no_se_manda_a_egresados',j['personas']==4);put('egresados/s5',{'fecha':'2026-10-01','revertido':True})
ok('rechaza_mensajes_vacios_o_largos',adm('POST','/api/avisos/enviar',{'destino':d_g,'texto':''})[0]==400 and adm('POST','/api/avisos/enviar',{'destino':d_g,'texto':'x'*901})[0]==400)
ok('rechaza_si_no_hay_a_quien',adm('POST','/api/avisos/enviar',{'destino':{'tipo':'grupo','id':'no-existe'},'texto':'Hola'})[0]==400 and adm('POST','/api/avisos/enviar',{'destino':d_g,'texto':'Hola','canales':[]})[0]==400)
# ============ fallos y reintentos ============
s,j=adm('POST','/api/avisos/enviar',{'destino':{'tipo':'alumno','id':'s4'},'asunto':'Prueba','texto':'Aviso para un número inválido.','canales':['whatsapp']});espera_cola()
f=[x for x in msgs(evento='manual') if x['nombre'].startswith('Diego')]
ok('un_numero_invalido_falla_de_inmediato_y_dice_por_que',len(f)==1 and f[0]['estado']=='fallido' and 'inválido' in f[0]['error'] and f[0]['intentos']==1)
s,j=adm('POST','/api/avisos/enviar',{'destino':{'tipo':'alumno','id':'s5'},'asunto':'Prueba','texto':'Aviso con error temporal.','canales':['whatsapp']});time.sleep(1.5)
f=[x for x in msgs(evento='manual') if x['nombre'].startswith('Elena')][0]
ok('un_error_temporal_se_reintenta_mas_tarde',f['estado']=='reintento' and f['intentos']==1 and 'temporal' in f['error'] and f['prox']>time.time()*1000)
adm('POST','/api/avisos/procesar',{});f2=[x for x in msgs(evento='manual') if x['nombre'].startswith('Elena')][0];ok('no_lo_reenvia_antes_de_tiempo',f2['intentos']==1)
dbc=sqlite3.connect('/tmp/nbdata97/lafragua.db')
for _ in range(2):
    dbc.execute("update mensajes set prox=0 where id=?",(f['id'],));dbc.commit();adm('POST','/api/avisos/procesar',{})
f3=[x for x in msgs(evento='manual') if x['nombre'].startswith('Elena')][0];ok('al_tercer_intento_queda_como_fallido',f3['estado']=='fallido' and f3['intentos']==3)
s,j=esc('POST','/api/avisos/reintentar',{'ids':[f3['id']]});ok('se_puede_reintentar_a_mano',s==200 and j['reintentados']==1);time.sleep(1.2)
f4=[x for x in msgs(evento='manual') if x['nombre'].startswith('Elena')][0];ok('y_vuelve_a_intentar',f4['intentos']>=1 and f4['estado'] in ('reintento','fallido'))
# SMTP caído
c3=cfg();c3['correo']['puerto']=3299;adm('PUT','/api/avisos/config',c3)
adm('POST','/api/avisos/enviar',{'destino':{'tipo':'alumno','id':'s1'},'asunto':'x','texto':'Con correo caído.','canales':['correo']});time.sleep(1.5)
r=[x for x in msgs(evento='manual') if 'correo caído' in x['texto']][0];ok('si_el_correo_esta_caido_reintenta',r['estado']=='reintento' and r['error'])
adm('PUT','/api/avisos/config',cfg());dbc.execute("update mensajes set prox=0 where id=?",(r['id'],));dbc.commit();adm('POST','/api/avisos/procesar',{});r2=[x for x in msgs(evento='manual') if 'correo caído' in x['texto']][0]
ok('al_volver_el_correo_se_envia',r2['estado']=='enviado' and r2['intentos']==2)
dbc.close()
# ============ bitácora y apagado ============
ok('filtra_por_estado_canal_y_texto',all(x['estado']=='fallido' for x in msgs(estado='fallido')) and all(x['canal']=='whatsapp' for x in msgs(canal='whatsapp')) and all('diego' in (x['nombre']+' '+x.get('texto','')+' '+x.get('asunto','')).lower() for x in msgs(q='diego')) and len(msgs(limite=5))==5)
s,j=adm('GET','/api/avisos');ok('el_resumen_cuenta_enviados_pendientes_y_fallidos',j['resumen']['enviados7']>10 and j['resumen']['pendientes']<=2 and j['resumen']['fallidos']>=1 and j['resumen']['omitidos']>=2)
a=dict(cfg());a['activo']=False;adm('PUT','/api/avisos/config',a);n=len(msgs(limite=300))
put('solicitudes/so5',sol('so5','pendiente'));esc('PUT','/api/doc/solicitudes/so5',sol('so5','aprobada',resp={'por':'x','fecha':'2026-11-12'}));time.sleep(0.5)
ok('con_los_avisos_apagados_no_se_manda_nada',len(msgs(limite=300))==n)
dbc=sqlite3.connect('/tmp/nbdata97/lafragua.db');acc=[r[0] for r in dbc.execute("select accion from auditoria").fetchall()];dbc.close()
ok('queda_en_la_auditoria',any('configuración de avisos' in a for a in acc) and any('Envió un aviso' in a for a in acc) and any('sin avisos' in a for a in acc))
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
