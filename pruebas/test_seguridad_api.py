import subprocess,time,json,os,urllib.request,urllib.error,http.cookiejar,hmac,hashlib,base64,struct,sqlite3,datetime,re
PORT=3300;B='http://127.0.0.1:%d'%PORT;TOK='tok-sg-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata104 && mkdir -p /tmp/nbdata104')
def arranca(extra=None):
    env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata104',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000',**(extra or {}))
    p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen(B+'/salud',timeout=1);break
        except Exception:pass
    return p
p=arranca()
R={}
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def sesion(u=None,c=None):
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def llama(m,url,body=None,raw=False):
        rq=urllib.request.Request(B+url,method=m,data=(json.dumps(body).encode() if body is not None else None),headers=HDR)
        try:
            r=op.open(rq);d=r.read()
            if raw:return r.status,d.decode()
            return r.status,(json.loads(d) if d else {})
        except urllib.error.HTTPError as e:
            d=e.read()
            if raw:return e.code,d.decode()
            try:return e.code,json.loads(d)
            except Exception:return e.code,{}
    llama.cj=cj
    if u:
        s,_=llama('POST','/api/login',{'u':u,'clave':c});assert s==200,(u,s)
    return llama
def b32d(s):return base64.b32decode(s+'='*((8-len(s)%8)%8))
def totp(sec,step):
    h=hmac.new(b32d(sec),struct.pack('>Q',step),hashlib.sha1).digest();o=h[-1]&15;n=int.from_bytes(h[o:o+4],'big')&0x7fffffff;return '%06d'%(n%10**6)
def codigo(sec,ultimo=0):
    pp=int(time.time()//30)
    for d in (0,1,-1):
        s=pp+d
        if s>ultimo:return s,totp(sec,s)
    return None,None
cfgp=sesion();s,j=cfgp('POST','/api/configurar',{'token':TOK,'name':'Administrador','u':'admin','clave':'clave-segura-1'});assert s==200
adm=sesion('admin','clave-segura-1')
adm('POST','/api/usuarios',{'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'});adm('POST','/api/usuarios',{'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'})
# ============ vector oficial y página pública ============
ok('el_algoritmo_coincide_con_el_vector_de_la_norma_rfc_6238',totp(base64.b32encode(b'12345678901234567890').decode().rstrip('='),1)=='287082')
anon=sesion();s,t=anon('GET','/privacidad',raw=True)
ok('el_aviso_de_privacidad_es_publico',s==200 and 'Aviso de privacidad' in t and 'Universidad Lafragua' in t and 'Versión 1' in t and 'Derechos (ARCO)'.lower() in t.lower() or 'ARCO' in t)
ok('el_aviso_cubre_los_datos_sensibles_y_las_transferencias','INE' in t and 'justificante médico' in t and 'Stripe' in t and 'WhatsApp' in t and 'borrador' in t.lower())
# ============ activar los dos pasos (caja) ============
caja=sesion('caja1','clave-caja1-123')
ok('por_defecto_no_tiene_dos_pasos',caja('GET','/api/2fa/estado')[1]['activo'] is False)
s,j=caja('POST','/api/2fa/iniciar',{});SEC=j['secreto']
ok('entrega_clave_y_direccion_para_el_qr',s==200 and re.match(r'^[A-Z2-7]{32}$',SEC) and j['uri'].startswith('otpauth://totp/Universidad%20Lafragua%3Acaja1?secret='+SEC) and 'digits=6' in j['uri'] and 'period=30' in j['uri'])
ok('un_codigo_equivocado_no_la_activa',caja('POST','/api/2fa/activar',{'codigo':'000000'})[0]==400 and caja('POST','/api/2fa/activar',{'codigo':'abc'})[0]==400)
ult,cod=codigo(SEC);s,j=caja('POST','/api/2fa/activar',{'codigo':cod});REC=j.get('codigos',[])
ok('con_el_codigo_correcto_se_activa_y_da_10_codigos_de_recuperacion',s==200 and len(REC)==10 and all(re.match(r'^[A-Z2-7]{5}-[A-Z2-7]{5}$',c) for c in REC) and len(set(REC))==10)
dbc=sqlite3.connect('/tmp/nbdata104/lafragua.db');row=dbc.execute("select totp,totp_resp from usuarios where u='caja1'").fetchone();dbc.close()
ok('el_secreto_y_los_codigos_se_guardan_protegidos',SEC not in row[0] and not any(c.replace('-','') in row[1] for c in REC) and len(json.loads(row[1]))==10)
ok('el_estado_y_la_lista_de_usuarios_lo_reflejan',caja('GET','/api/2fa/estado')[1]=={'activo':True,'restantes':10,'exigida':False} and [u for u in adm('GET','/api/seguridad')[1]['usuarios'] if u['u']=='caja1'][0]['dosPasos'] is True)
ok('no_se_puede_iniciar_de_nuevo_si_ya_esta_activa',caja('POST','/api/2fa/iniciar',{})[0]==400)
# ============ iniciar sesión con los dos pasos ============
def paso1(u='caja1',c='clave-caja1-123'):
    cx=sesion();s,j=cx('POST','/api/login',{'u':u,'clave':c});return cx,s,j
cx,s,j=paso1()
ok('con_la_contrasena_sola_no_se_inicia_sesion',s==200 and j.get('requiere2fa') is True and len(j['ticket'])==48 and 'usuario' not in j and cx('GET','/api/col/students')[0]==401)
ok('la_contrasena_mala_sigue_siendo_rechazada_sin_pedir_codigo',paso1(c='mala')[1]==401)
tk=j['ticket']
ok('un_codigo_malo_se_rechaza',cx('POST','/api/login2fa',{'ticket':tk,'codigo':'123456'})[0]==401 and cx('GET','/api/col/students')[0]==401)
ok('un_ticket_inventado_no_sirve',cx('POST','/api/login2fa',{'ticket':'0'*48,'codigo':cod})[0]==401)
s,c2=codigo(SEC,ult);ult2,c2=s,c2
s,j2=cx('POST','/api/login2fa',{'ticket':tk,'codigo':c2});ok('con_el_codigo_correcto_entra',s==200 and j2['usuario']['u']=='caja1' and cx('GET','/api/col/students')[0]==200)
cx3,_,j3=paso1();s,_=cx3('POST','/api/login2fa',{'ticket':j3['ticket'],'codigo':c2});ok('un_codigo_ya_usado_no_se_puede_repetir',s==401)
cx4,_,j4=paso1()
for i in range(4):cx4('POST','/api/login2fa',{'ticket':j4['ticket'],'codigo':'111111'})
s,j=cx4('POST','/api/login2fa',{'ticket':j4['ticket'],'codigo':'111111'});ok('a_los_5_intentos_malos_se_anula_el_ticket',s==429 and cx4('POST','/api/login2fa',{'ticket':j4['ticket'],'codigo':c2})[0]==401)
cx5,_,j5=paso1();s,j=cx5('POST','/api/login2fa',{'ticket':j5['ticket'],'codigo':REC[0].lower()});ok('un_codigo_de_recuperacion_sirve_una_vez',s==200 and j['recuperacion'] is True and j['restantes']==9 and cx5('GET','/api/col/students')[0]==200)
cx6,_,j6=paso1();ok('y_no_se_puede_reusar',cx6('POST','/api/login2fa',{'ticket':j6['ticket'],'codigo':REC[0]})[0]==401)
ok('quien_no_activo_dos_pasos_entra_normal',sesion('esc2','clave-esc2-123')('GET','/api/col/students')[0]==200)
ok('la_sesion_dice_que_tiene_dos_pasos',cx5('GET','/api/yo')[1]['usuario']['dosPasos'] is True)
# ============ desactivar y códigos nuevos ============
ok('no_se_desactiva_con_contrasena_mala',cx5('POST','/api/2fa/desactivar',{'clave':'mala','codigo':REC[1]})[0]==403)
ok('ni_con_codigo_malo',cx5('POST','/api/2fa/desactivar',{'clave':'clave-caja1-123','codigo':'999999'})[0]==401)
s,j=cx5('POST','/api/2fa/codigos',{'clave':'clave-caja1-123','codigo':REC[1]});NEW=j.get('codigos',[]);ok('genera_codigos_nuevos_con_contrasena_y_codigo',s==200 and len(NEW)==10 and not set(NEW)&set(REC))
cx7,_,j7=paso1();ok('los_codigos_anteriores_ya_no_sirven',cx7('POST','/api/login2fa',{'ticket':j7['ticket'],'codigo':REC[2]})[0]==401)
s,j=cx5('POST','/api/2fa/desactivar',{'clave':'clave-caja1-123','codigo':NEW[0]});ok('con_contrasena_y_codigo_se_desactiva',s==200 and cx5('GET','/api/2fa/estado')[1]['activo'] is False and paso1()[2].get('requiere2fa') is None)
# ============ política para administradores ============
ok('solo_el_administrador_cambia_la_politica',caja('PUT','/api/seguridad/config',{'exigir2fa':True})[0]==403 and caja('GET','/api/seguridad')[0]==403)
s,j=adm('PUT','/api/seguridad/config',{'exigir2fa':True});ok('guarda_la_politica',s==200 and j['config']['exigir2fa'] is True)
ok('al_administrador_sin_dos_pasos_se_le_bloquea_lo_demas',adm('GET','/api/col/students')[0]==403 and adm('GET','/api/col/students')[1].get('requiere2fa') is True)
y=adm('GET','/api/yo')[1]['usuario'];ok('pero_puede_activarla_y_se_le_avisa',y['debeActivar2fa'] is True and adm('GET','/api/2fa/estado')[0]==200)
ok('los_demas_roles_no_se_afectan',caja('GET','/api/col/students')[0]==200 and sesion('esc2','clave-esc2-123')('GET','/api/col/students')[0]==200)
s,j=adm('POST','/api/2fa/iniciar',{});SA=j['secreto'];ua,ca=codigo(SA);s,j=adm('POST','/api/2fa/activar',{'codigo':ca});RECA=j['codigos']
ok('al_activarla_el_administrador_recupera_el_acceso',s==200 and adm('GET','/api/col/students')[0]==200 and adm('GET','/api/yo')[1]['usuario']['debeActivar2fa'] is False)
ok('con_la_politica_el_administrador_no_puede_desactivarla',adm('POST','/api/2fa/desactivar',{'clave':'clave-segura-1','codigo':RECA[0]})[0]==400)
# reinicio por el administrador
caja('POST','/api/2fa/iniciar',{});s,j=caja('POST','/api/2fa/iniciar',{});ok('ya_hay_un_proceso_de_activacion_pendiente_se_reinicia',s==200)
SEC2=j['secreto'];_,cc=codigo(SEC2);caja('POST','/api/2fa/activar',{'codigo':cc})
ok('el_administrador_reinicia_los_dos_pasos_de_otra_persona',adm('POST','/api/seguridad/reset',{'u':'caja1'})[0]==200 and paso1()[2].get('requiere2fa') is None and caja('POST','/api/seguridad/reset',{'u':'admin'})[0]==403 and adm('POST','/api/seguridad/reset',{'u':'nadie'})[0]==404)
# ============ aviso de privacidad ============
pv=lambda **k:dict({'entidad':'Universidad Lafragua','domicilio':'Av. Principal 123, Tejupilco, Estado de México','correo':'privacidad@lafragua.mx','telefono':'722 000 0000','responsable':'Control escolar','extra':'','aceptacion':False},**k)
ok('rechaza_un_aviso_incompleto',all(adm('PUT','/api/seguridad/privacidad',pv(**k))[0]==400 for k in [{'entidad':'x'},{'domicilio':''},{'correo':'sin-arroba'},{'responsable':''}]) and caja('PUT','/api/seguridad/privacidad',pv())[0]==403)
s,j=adm('PUT','/api/seguridad/privacidad',pv());v1=j['privacidad']['version']
ok('guardar_los_datos_sube_la_version',s==200 and v1==2 and j['privacidad']['actualizado']!='')
s,j=adm('PUT','/api/seguridad/privacidad',pv(aceptacion=True));ok('solo_cambiar_la_aceptacion_no_sube_la_version',j['privacidad']['version']==2)
_,t=anon('GET','/privacidad',raw=True)
ok('el_aviso_publico_muestra_los_datos_guardados','Av. Principal 123' in t and 'privacidad@lafragua.mx' in t and '722 000 0000' in t and 'Versión 2' in t)
adm('PUT','/api/seguridad/privacidad',pv(extra='<script>alert(1)</script> Texto "x"',aceptacion=True));_,t=anon('GET','/privacidad',raw=True)
ok('el_texto_se_escapa_y_no_ejecuta_codigo','<script>alert(1)</script>' not in t and '&lt;script&gt;' in t)
v=adm('GET','/api/seguridad')[1]['privacidad']['version']
ok('con_la_aceptacion_activa_a_cada_quien_se_le_pide',caja('GET','/api/yo')[1]['usuario']['privacidadPendiente']==v and adm('GET','/api/yo')[1]['usuario']['privacidadPendiente']==v)
ok('no_acepta_una_version_distinta',caja('POST','/api/privacidad/aceptar',{'version':v-1})[0]==400)
ok('acepta_la_vigente',caja('POST','/api/privacidad/aceptar',{'version':v})[0]==200 and caja('GET','/api/yo')[1]['usuario']['privacidadPendiente']==0)
ok('la_aceptacion_de_una_persona_no_cubre_a_otra',sesion('esc2','clave-esc2-123')('GET','/api/yo')[1]['usuario']['privacidadPendiente']==v)
ok('se_cuentan_las_aceptaciones',adm('GET','/api/seguridad')[1]['privacidad']['aceptaciones']=={'total':1,'vigentes':1})
adm('PUT','/api/seguridad/privacidad',pv(extra='Cambio',aceptacion=True));ok('si_cambia_el_aviso_se_vuelve_a_pedir',caja('GET','/api/yo')[1]['usuario']['privacidadPendiente']==v+1 and adm('GET','/api/seguridad')[1]['privacidad']['aceptaciones']['vigentes']==0)
adm('PUT','/api/seguridad/privacidad',pv(extra='Cambio',aceptacion=False));ok('con_la_aceptacion_apagada_no_se_pide',caja('GET','/api/yo')[1]['usuario']['privacidadPendiente']==0)
# ============ conservación de datos ============
ok('rechaza_plazos_fuera_de_rango',all(adm('PUT','/api/seguridad/conservacion',dict({'ineAnios':1,'firmasAnios':5,'mensajesMeses':12,'sesionesPagoMeses':24,'auditoriaMeses':36},**k))[0]==400 for k in [{'ineAnios':20},{'firmasAnios':0},{'mensajesMeses':0},{'sesionesPagoMeses':2},{'auditoriaMeses':3}]) and caja('PUT','/api/seguridad/conservacion',{})[0]==403)
ok('guarda_los_plazos',adm('PUT','/api/seguridad/conservacion',{'ineAnios':1,'firmasAnios':5,'mensajesMeses':12,'sesionesPagoMeses':24,'auditoriaMeses':36})[0]==200)
def sube(nombre,datos):
    rq=urllib.request.Request(B+'/api/archivo',method='POST',data=datos,headers={'x-lafragua':'1','x-nombre':nombre,'x-privado':'1','x-categoria':'contrato','Content-Type':'image/jpeg'})
    op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(adm.cj));return json.loads(op.open(rq).read())['id']
hoy=datetime.date.today();viejo=(hoy-datetime.timedelta(days=365*3)).isoformat();muy=(hoy-datetime.timedelta(days=365*8)).isoformat();rec=hoy.isoformat()
fv=[sube('ine%d.jpg'%i,os.urandom(2000)) for i in range(3)];fr=sube('ine-reciente.jpg',os.urandom(2000))
png='data:image/png;base64,AAAA'
adm('PUT','/api/doc/contratos/c_viejo',{'id':'c_viejo','nombre':'Docente Viejo','estado':'firmado','desde':viejo,'hasta':viejo,'ine':{'d1':{'id':fv[0],'name':'a'},'d2':{'id':fv[1],'name':'b'}},'firmas':{'doc':{'png':png,'fecha':viejo,'nombre':'x','huella':'h'}}})
adm('PUT','/api/doc/contratos/c_muy',{'id':'c_muy','nombre':'Docente Muy Viejo','estado':'firmado','desde':muy,'hasta':muy,'ine':{'d1':{'id':fv[2],'name':'c'}},'firmas':{'doc':{'png':png,'fecha':muy,'nombre':'y','huella':'h2'},'univ':{'png':png,'fecha':muy,'nombre':'z','huella':'h3'}}})
adm('PUT','/api/doc/contratos/c_nuevo',{'id':'c_nuevo','nombre':'Docente Nuevo','estado':'firmado','desde':rec,'hasta':rec,'ine':{'d1':{'id':fr,'name':'r'}},'firmas':{'doc':{'png':png,'fecha':rec,'nombre':'n','huella':'h4'}}})
adm('PUT','/api/doc/fichasins/f_vieja',{'sid':'s1','firmas':{'alumno':{'png':png,'fecha':muy+'T10:00:00.000Z','nombre':'a','huella':'h'}}});adm('PUT','/api/doc/fichasins/f_nueva',{'sid':'s2','firmas':{'alumno':{'png':png,'fecha':rec+'T10:00:00.000Z','nombre':'b','huella':'h'}}})
adm('PUT','/api/doc/pagos_linea/pl_vieja',{'id':'pl_vieja','sid':'s1','estado':'expirada','creada':muy+'T10:00:00.000Z','monto':1});adm('PUT','/api/doc/pagos_linea/pl_creada',{'id':'pl_creada','sid':'s1','estado':'creada','creada':muy+'T10:00:00.000Z','monto':1});adm('PUT','/api/doc/pagos_linea/pl_nueva',{'id':'pl_nueva','sid':'s1','estado':'pagada','creada':rec+'T10:00:00.000Z','monto':1})
dbc=sqlite3.connect('/tmp/nbdata104/lafragua.db');ms=int(time.time()*1000)
for i in range(4):dbc.execute("insert into mensajes (id,ts,canal,para,nombre,evento,asunto,texto,ref,quien,estado) values (?,?,?,?,?,?,?,?,?,?,?)",('mv%d'%i,ms-400*86400000,'correo','a@b.mx','x','manual','a','t','','','enviado'))
dbc.execute("insert into mensajes (id,ts,canal,para,nombre,evento,asunto,texto,ref,quien,estado) values (?,?,?,?,?,?,?,?,?,?,?)",('mn',ms,'correo','a@b.mx','x','manual','a','t','','','enviado'))
for i in range(3):dbc.execute("insert into auditoria (fecha,u,ip,accion,detalle) values (?,?,?,?,?)",(ms-1500*86400000,'x','1.1.1.1','Acción vieja',''))
dbc.commit();dbc.close()
cd=adm('GET','/api/seguridad')[1]['conservacion']['candidatos']
ok('el_reporte_cuenta_lo_que_paso_su_plazo',sorted(cd['ine'])==['c_muy','c_viejo'] and sorted(cd['firmasContrato'])==['c_muy'] and cd['firmasFicha']==['f_vieja'] and cd['mensajes']==4 and cd['sesionesPago']==1 and cd['auditoria']==3)
ok('sin_contrasena_o_con_mala_no_depura',adm('POST','/api/seguridad/depurar',{'categorias':['ine'],'clave':'mala'})[0]==403 and adm('POST','/api/seguridad/depurar',{'categorias':['ine']})[0]==403)
ok('categorias_desconocidas_o_vacias_se_rechazan',adm('POST','/api/seguridad/depurar',{'categorias':['todo'],'clave':'clave-segura-1'})[0]==400 and adm('POST','/api/seguridad/depurar',{'categorias':[],'clave':'clave-segura-1'})[0]==400)
ok('solo_el_administrador_depura',caja('POST','/api/seguridad/depurar',{'categorias':['ine'],'clave':'clave-caja1-123'})[0]==403)
s,j=adm('POST','/api/seguridad/depurar',{'categorias':['ine','firmasContrato','firmasFicha','mensajes','sesionesPago','auditoria'],'clave':'clave-segura-1'});r=j.get('resultado',{})
ok('depura_y_dice_cuanto_borro',s==200 and r=={'ine':3,'firmasContrato':3,'firmasFicha':1,'mensajes':4,'sesionesPago':1,'auditoria':3} or (s==200 and r['ine']==3 and r['mensajes']==4 and r['sesionesPago']==1 and r['auditoria']==3 and r['firmasFicha']==1))
cv=adm('GET','/api/doc/contratos/c_viejo')[1]['data'];cm=adm('GET','/api/doc/contratos/c_muy')[1]['data'];cn=adm('GET','/api/doc/contratos/c_nuevo')[1]['data']
ok('la_ine_vieja_se_borra_con_su_archivo',cv['ine']=={} and cm['ine']=={} and 'inePurgada' in cv and not os.path.exists('/tmp/nbdata104/archivos/'+fv[0]) and not os.path.exists('/tmp/nbdata104/archivos/'+fv[2]))
ok('la_ine_reciente_se_conserva',cn['ine']['d1']['id']==fr and os.path.exists('/tmp/nbdata104/archivos/'+fr))
ok('de_la_firma_vieja_se_borra_la_imagen_pero_queda_la_constancia','png' not in cm['firmas']['doc'] and cm['firmas']['doc']['imagenPurgada'] is True and cm['firmas']['doc']['huella']=='h2' and cm['firmas']['univ']['huella']=='h3' and 'png' in cv['firmas']['doc'] and 'png' in cn['firmas']['doc'])
ok('las_fichas_firmadas_viejas_tambien',adm('GET','/api/doc/fichasins/f_vieja')[1]['data']['firmas']['alumno'].get('png') is None and adm('GET','/api/doc/fichasins/f_nueva')[1]['data']['firmas']['alumno']['png']==png)
ok('se_conservan_los_registros_recientes_y_las_sesiones_creadas_o_nuevas',adm('GET','/api/doc/pagos_linea/pl_nueva')[1]['exists'] and adm('GET','/api/doc/pagos_linea/pl_creada')[1]['exists'] and not adm('GET','/api/doc/pagos_linea/pl_vieja')[1]['exists'])
cd=adm('GET','/api/seguridad')[1]['conservacion']['candidatos'];ok('despues_ya_no_queda_nada_pendiente',cd['ine']==[] and cd['firmasFicha']==[] and cd['mensajes']==0 and cd['auditoria']==0)
dbc=sqlite3.connect('/tmp/nbdata104/lafragua.db');nm=dbc.execute("select count(*) from mensajes").fetchone()[0];acc=[x[0] for x in dbc.execute("select accion from auditoria").fetchall()];dbc.close()
ok('queda_en_la_auditoria_la_depuracion',nm==1 and any('Depuró datos' in a for a in acc) and any('verificación en dos pasos' in a.lower() for a in acc))
# ============ reinicio desde el servidor ============
caja('POST','/api/2fa/iniciar',{});s,j=caja('POST','/api/2fa/iniciar',{});S3=j['secreto'];_,c3=codigo(S3);caja('POST','/api/2fa/activar',{'codigo':c3});ok('caja_vuelve_a_tener_dos_pasos',paso1()[2].get('requiere2fa') is True)
p.terminate();time.sleep(1.2);p=arranca({'LF_2FA_REINICIAR':'caja1'})
ok('con_la_variable_del_servidor_se_reinician_los_dos_pasos_de_ese_usuario',paso1()[2].get('requiere2fa') is None)
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
