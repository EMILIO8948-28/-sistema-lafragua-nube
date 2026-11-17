import subprocess,time,json,os,urllib.request,urllib.error,http.cookiejar,hmac,hashlib,sqlite3,datetime
PORT=3280;B='http://127.0.0.1:%d'%PORT;TOK='tok-pl-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata102 /tmp/fs102 /tmp/relpl && mkdir -p /tmp/nbdata102 /tmp/relpl')
RELOJ='/tmp/relpl/reloj.txt';open(RELOJ,'w').write('2026-11-12')
fake=subprocess.Popen(['node','/tmp/fake_stripe.js','3281','/tmp/fs102'],stdout=subprocess.PIPE,text=True);time.sleep(0.8)
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata102',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ,LF_STRIPE_BASE='http://127.0.0.1:3281',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={}
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def sesion(u,c):
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def llama(m,url,body=None,raw=None,hdr=None):
        h=dict(HDR);h.update(hdr or {})
        rq=urllib.request.Request(B+url,method=m,data=(raw if raw is not None else (json.dumps(body).encode() if body is not None else None)),headers=h)
        try:
            r=op.open(rq);d=r.read()
            try:return r.status,json.loads(d) if d else {}
            except Exception:return r.status,d
        except urllib.error.HTTPError as e:
            d=e.read()
            try:return e.code,json.loads(d)
            except Exception:return e.code,{}
    if u:
        s,_=llama('POST','/api/login',{'u':u,'clave':c});assert s==200,(u,s)
    return llama
anon=sesion(None,None);s,j=anon('POST','/api/configurar',{'token':TOK,'name':'Administrador','u':'admin','clave':'clave-segura-1'});assert s==200
adm=sesion('admin','clave-segura-1');put=lambda path,obj:adm('PUT','/api/doc/'+path,obj)
put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
put('config/cobranza',{'activa':False,'umbral':2,'diaLimite':10,'intervaloDias':7,'graciaDias':7,'reinicioDias':30})
for sid,nom,mail in [('s1','Ana López Ramírez','ana@correo.mx'),('s2','Beto Mena Ruiz','')]:put('students/'+sid,{'mat':'2026'+sid[1:].zfill(3),'nombre':nom,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'mail':mail,'tel':''})
put('students/s3',{'mat':'2026003','nombre':'Carla Díaz','carrera':'Otro','programa':'Otro','ingreso':2026,'nuevo':False,'total':15000})
adm('POST','/api/usuarios/alumnos',{'items':[{'u':'als1','name':'Ana','alumno':'s1','clave':'abcd-efgh'},{'u':'als2','name':'Beto','alumno':'s2','clave':'abcd-efgh'},{'u':'als3','name':'Carla','alumno':'s3','clave':'abcd-efgh'}]})
adm('POST','/api/usuarios',{'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'});adm('POST','/api/usuarios',{'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'})
def alumno(u):
    c=sesion(None,None);s,j=c('POST','/api/login',{'u':u,'clave':'abcd-efgh'});assert s==200,(u,s,j)
    c('POST','/api/cambiar-clave',{'actual':'abcd-efgh','nueva':'clave-nueva-77'});return c
a1=alumno('als1');a2=alumno('als2');a3=alumno('als3');caja=sesion('caja1','clave-caja1-123');esc=sesion('esc2','clave-esc2-123')
KEY='sk_test_ok12345678';WH='whsec_prueba12345678'
cfg=lambda **k:dict({'activo':True,'metodos':{'tarjeta':True,'oxxo':True},'oxxoDias':3,'urlPublica':'https://escuela.example.mx','stripeKey':KEY,'webhookSecret':WH,'facturas':{'activo':True,'diaLimite':5}},**k)
def stl():
    try:return json.load(open('/tmp/fs102/stripe.json'))
    except Exception:return []
# ============ configuración ============
ok('por_defecto_los_pagos_en_linea_estan_apagados',a1('GET','/api/pagos-linea/estado')[1]['activo'] is False and adm('GET','/api/pagos-linea')[1]['config']['activo'] is False)
bad=lambda **k:adm('PUT','/api/pagos-linea/config',dict(cfg(),**k))[0]
ok('rechaza_llaves_con_formato_equivocado',bad(stripeKey='clave-cualquiera')==400 and bad(webhookSecret='xyz')==400)
ok('rechaza_activar_sin_llaves',adm('PUT','/api/pagos-linea/config',dict(cfg(),stripeKey='',webhookSecret=''))[0]==400)
ok('rechaza_datos_fuera_de_rango',bad(oxxoDias=9)==400 and bad(urlPublica='ftp://x')==400 and bad(metodos={'tarjeta':False,'oxxo':False})==400 and bad(facturas={'activo':True,'diaLimite':40})==400)
ok('solo_el_administrador_configura',caja('PUT','/api/pagos-linea/config',cfg())[0]==403 and esc('GET','/api/pagos-linea')[0]==403 and a1('GET','/api/pagos-linea')[0]==403 and caja('POST','/api/pagos-linea/probar',{})[0]==403)
s,j=adm('PUT','/api/pagos-linea/config',cfg());ok('guarda_la_configuracion',s==200 and j['config']['modoPrueba'] is True and j['config']['webhookUrl']=='https://escuela.example.mx/api/pagos-linea/webhook')
s,j=adm('GET','/api/pagos-linea');ok('nunca_devuelve_las_llaves',KEY not in json.dumps(j) and WH not in json.dumps(j) and j['config']['claveGuardada'] and j['config']['firmaGuardada'])
dbc=sqlite3.connect('/tmp/nbdata102/lafragua.db');crudo=dbc.execute("select data from docs where coleccion='sistema' and id='pagos'").fetchone()[0];dbc.close()
ok('las_llaves_se_guardan_cifradas',KEY not in crudo and WH not in crudo)
s,j=caja('GET','/api/pagos-linea');ok('caja_ve_las_sesiones_pero_no_la_configuracion',s==200 and j['esAdmin'] is False and 'claveGuardada' not in j['config'])
s,j=adm('POST','/api/pagos-linea/probar',{});ok('probar_la_conexion_con_stripe',j['ok'] is True and j['cuenta']=='acct_1TEST' and stl()[-1]['url']=='/v1/account' and stl()[-1]['auth']=='Bearer '+KEY)
adm('PUT','/api/pagos-linea/config',dict(cfg(),stripeKey='sk_test_malaMALA12345'));s,j=adm('POST','/api/pagos-linea/probar',{});ok('con_una_llave_mala_explica_el_error',j['ok'] is False and 'Invalid API Key' in j['msg']);adm('PUT','/api/pagos-linea/config',cfg())
# ============ lo que puede pagar el alumno ============
s,j=a1('GET','/api/pagos-linea/estado');o={x['id']:x for x in j['opciones']}
ok('el_alumno_ve_lo_vencido_y_sus_cargos',j['activo'] and o['vencido']['monto']==3900 and 'vencido' in o and any(k.startswith('c:') for k in o))
ok('lo_vencido_incluye_las_3_colegiaturas',len(o['vencido']['cc'])==3 and o['vencido']['cc']==['c1','c2','c3'])
# ============ crear el pago ============
a1('POST','/api/pagos-linea/checkout',{'opcion':'no-existe'});ok('rechaza_una_opcion_que_no_existe',a1('POST','/api/pagos-linea/checkout',{'opcion':'no-existe'})[0]==400 and a1('POST','/api/pagos-linea/checkout',{'opcion':'c:inventada'})[0]==400)
s,j=a1('POST','/api/pagos-linea/checkout',{'opcion':'vencido'});ses=[x for x in stl() if x['url']=='/v1/checkout/sessions'][-1]['forma']
ok('crea_la_sesion_y_regresa_la_direccion_de_pago',s==200 and j['url']=='https://checkout.stripe.test/c/pay/cs_test_1')
ok('el_monto_lo_pone_el_servidor_en_pesos_mexicanos',ses['mode']=='payment' and ses['line_items[0][price_data][currency]']=='mxn' and ses['line_items[0][price_data][unit_amount]']=='390000' and ses['line_items[0][quantity]']=='1')
ok('acepta_tarjeta_y_oxxo_con_su_vigencia',ses['payment_method_types[0]']=='card' and ses['payment_method_types[1]']=='oxxo' and ses['payment_method_options[oxxo][expires_after_days]']=='3')
ok('liga_el_pago_al_alumno_y_vuelve_al_portal',ses['client_reference_id']=='s1' and ses['metadata[sid]']=='s1' and ses['customer_email']=='ana@correo.mx' and ses['success_url']=='https://escuela.example.mx/?pago=ok' and ses['cancel_url']=='https://escuela.example.mx/?pago=cancelado' and ses['payment_intent_data[metadata][sid]']=='s1')
ref=ses['metadata[ref]']
s,j=a1('GET','/api/pagos-linea/estado');ok('queda_registrada_la_sesion',j['recientes'][0]['estado']=='creada' and j['recientes'][0]['monto']==3900)
s,j=a2('POST','/api/pagos-linea/checkout',{'opcion':'vencido'});ses2=[x for x in stl() if x['url']=='/v1/checkout/sessions'][-1]['forma'];ok('cada_alumno_paga_solo_lo_suyo',ses2['client_reference_id']=='s2' and ses2['metadata[sid]']=='s2' and 'customer_email' not in ses2)
s,j=a3('POST','/api/pagos-linea/checkout',{'opcion':'c:c0'});ses3=[x for x in stl() if x['url']=='/v1/checkout/sessions'][-1]['forma'];ok('arriba_de_10_mil_pesos_no_se_ofrece_oxxo',s==200 and ses3['payment_method_types[0]']=='card' and 'payment_method_types[1]' not in ses3 and ses3['line_items[0][price_data][unit_amount]']=='1500000')
ok('caja_y_administrativos_no_inician_pagos_de_alumnos',caja('POST','/api/pagos-linea/checkout',{'opcion':'vencido'})[0]==403 and esc('POST','/api/pagos-linea/checkout',{'opcion':'vencido'})[0]==403)
# ============ el aviso de Stripe (webhook) ============
def evento(tipo,sesion,sid='s1',ref=None,estado='paid',monto=390000,cur='mxn',ts=None,secreto=WH,firma_mala=False):
    obj={'id':sesion,'object':'checkout.session','payment_status':estado,'amount_total':monto,'currency':cur,'metadata':{'ref':ref,'sid':sid}}
    raw=json.dumps({'id':'evt_'+str(time.time()),'type':tipo,'data':{'object':obj}});t=str(ts or int(time.time()))
    v1=hmac.new(secreto.encode(),(t+'.'+raw).encode(),hashlib.sha256).hexdigest()
    return anon('POST','/api/pagos-linea/webhook',raw=raw.encode(),hdr={'Stripe-Signature':'t=%s,v1=%s'%(t,v1 if not firma_mala else '0'*64),'Content-Type':'application/json','x-lafragua':''})
def ledger(sid):
    r=adm('GET','/api/doc/ledger/'+sid);return (r[1].get('data') or {}).get('pagos',[])
ok('sin_firma_o_con_firma_mala_no_registra_nada',anon('POST','/api/pagos-linea/webhook',raw=b'{}',hdr={'x-lafragua':''})[0]==400 and evento('checkout.session.completed','cs_test_1',ref=ref,firma_mala=True)[0]==400 and evento('checkout.session.completed','cs_test_1',ref=ref,secreto='whsec_otroSecreto123')[0]==400 and ledger('s1')==[])
ok('un_aviso_viejo_se_rechaza',evento('checkout.session.completed','cs_test_1',ref=ref,ts=int(time.time())-3600)[0]==400 and ledger('s1')==[])
ok('un_aviso_de_una_sesion_desconocida_se_ignora',evento('checkout.session.completed','cs_test_999',ref='nada')[0]==200 and ledger('s1')==[])
ok('con_otro_monto_no_se_registra_y_queda_marcado',evento('checkout.session.completed','cs_test_1',ref=ref,monto=100000)[0]==200 and ledger('s1')==[] and [x for x in adm('GET','/api/pagos-linea')[1]['sesiones'] if x['id']==ref][0]['estado']=='discrepancia')
s,j=a1('POST','/api/pagos-linea/checkout',{'opcion':'vencido'});ses=[x for x in stl() if x['url']=='/v1/checkout/sessions'][-1]['forma'];ref=ses['metadata[ref]'];sesid='cs_test_4'
ok('se_crea_otra_sesion_despues_de_la_discrepancia',s==200 and j['url'].endswith(sesid))
r=evento('checkout.session.completed',sesid,ref=ref);pg=ledger('s1')
ok('con_el_pago_confirmado_se_registra_en_su_cuenta',r[0]==200 and len(pg)==1 and pg[0]['monto']==3900 and pg[0]['metodo']=='Tarjeta' and pg[0]['folio']=='R-000001' and pg[0]['cc']==['c1','c2','c3'] and pg[0]['linea'] is True and pg[0]['sesion']==sesid and pg[0]['byn']=='Pago en línea' and pg[0]['fecha']=='2026-11-12')
evento('checkout.session.completed',sesid,ref=ref);ok('el_mismo_aviso_dos_veces_no_duplica_el_pago',len(ledger('s1'))==1)
dbm=sqlite3.connect('/tmp/nbdata102/lafragua.db');mrows=dbm.execute("select id,data from docs where coleccion='meta'").fetchall();dbm.close();print('META',mrows,adm('GET','/api/doc/meta/folio'),flush=True)
ok('el_contador_de_folios_avanzo',len(mrows)>0 and json.loads(mrows[0][1])['n']>=1)
s,j=a1('GET','/api/pagos-linea/estado');ok('lo_vencido_ya_no_aparece_y_la_sesion_dice_pagada','vencido' not in [x['id'] for x in j['opciones']] and j['recientes'][0]['estado']=='pagada' and j['recientes'][0]['folio']=='R-000001')
av=[v['data'] for v in adm('GET','/api/col/avisos')[1]['docs'] if v['data']['sid']=='s1' and v['data']['titulo']=='Pago recibido'];ok('el_alumno_recibe_un_aviso_en_su_portal',len(av)==1 and 'R-000001' in av[0]['mensaje'] and '$3900.00' in av[0]['mensaje'])
ok('el_alumno_ve_su_pago_en_su_cuenta',len(a1('GET','/api/doc/ledger/s1')[1]['data']['pagos'])==1)
# OXXO
s,j=a2('POST','/api/pagos-linea/checkout',{'opcion':'vencido'});ses=[x for x in stl() if x['url']=='/v1/checkout/sessions'][-1]['forma'];ref2=ses['metadata[ref]'];sid2=j['url'].split('/')[-1]
evento('checkout.session.completed',sid2,sid='s2',ref=ref2,estado='unpaid');ok('una_ficha_de_oxxo_queda_esperando_y_no_cuenta_como_pago',ledger('s2')==[] and [x for x in adm('GET','/api/pagos-linea')[1]['sesiones'] if x['id']==ref2][0]['estado']=='esperando')
evento('checkout.session.async_payment_succeeded',sid2,sid='s2',ref=ref2);pg=ledger('s2')
ok('al_pagar_en_la_tienda_se_registra_como_deposito',len(pg)==1 and pg[0]['metodo']=='Depósito' and 'OXXO' in pg[0]['ref'] and pg[0]['folio']=='R-000002' and pg[0]['monto']==3900)
s,j=a3('POST','/api/pagos-linea/checkout',{'opcion':'c:c0'});ref3=[x for x in stl() if x['url']=='/v1/checkout/sessions'][-1]['forma']['metadata[ref]'];sid3=j['url'].split('/')[-1]
evento('checkout.session.async_payment_failed',sid3,sid='s3',ref=ref3,estado='unpaid',monto=1500000);ok('si_el_pago_falla_queda_marcado_y_no_se_registra',ledger('s3')==[] and [x for x in adm('GET','/api/pagos-linea')[1]['sesiones'] if x['id']==ref3][0]['estado']=='fallida')
s,j=a3('POST','/api/pagos-linea/checkout',{'opcion':'c:c0'});ref4=[x for x in stl() if x['url']=='/v1/checkout/sessions'][-1]['forma']['metadata[ref]'];sid4=j['url'].split('/')[-1]
evento('checkout.session.expired',sid4,sid='s3',ref=ref4,estado='unpaid',monto=1500000);ok('una_sesion_vencida_queda_expirada',[x for x in adm('GET','/api/pagos-linea')[1]['sesiones'] if x['id']==ref4][0]['estado']=='expirada' and ledger('s3')==[])
ok('la_lista_de_sesiones_no_expone_la_direccion_de_pago',all('url' not in x for x in adm('GET','/api/pagos-linea')[1]['sesiones']))
# ============ datos fiscales ============
f=lambda **k:dict({'rfc':'LORA900101AB1','razon':'ana lópez ramírez','cp':'52400','regimen':'605','uso':'D10','correo':'ana@correo.mx'},**k)
ok('rechaza_datos_fiscales_incorrectos',all(a1('PUT','/api/fiscal',f(**k))[0]==400 for k in [{'rfc':'xx'},{'rfc':'LORA9001AB1'},{'razon':'a'},{'cp':'123'},{'regimen':'999'},{'uso':'ZZ9'},{'correo':'sin-arroba'}]))
ok('guarda_los_datos_fiscales_del_alumno_en_mayusculas',a1('PUT','/api/fiscal',f())[0]==200 and a1('GET','/api/doc/fiscal/s1')[1]['data']['razon']=='ANA LÓPEZ RAMÍREZ' and a1('GET','/api/doc/fiscal/s1')[1]['data']['rfc']=='LORA900101AB1')
ok('otro_alumno_no_ve_ni_cambia_los_datos_fiscales',a2('GET','/api/doc/fiscal/s1')[1]['exists'] is False and a2('PUT','/api/fiscal/s1',f())[0]==403 and a2('PUT','/api/doc/fiscal/s1',{'rfc':'X'})[0]==403)
ok('caja_si_los_ve_y_puede_corregirlos',caja('GET','/api/doc/fiscal/s1')[1]['exists'] is True and caja('PUT','/api/fiscal/s1',f(razon='Ana López Ramírez SA'))[0]==200 and esc('PUT','/api/fiscal/s1',f())[0]==403);caja('PUT','/api/fiscal/s1',f())
# ============ solicitar factura ============
pid=ledger('s1')[0]['id']
ok('sin_datos_fiscales_no_se_puede_pedir',a2('POST','/api/facturas/solicitar',{'pagoId':ledger('s2')[0]['id']})[0]==400)
ok('no_se_pide_la_factura_de_un_pago_ajeno_ni_inexistente',a1('POST','/api/facturas/solicitar',{'pagoId':ledger('s2')[0]['id']})[0]==404 and a1('POST','/api/facturas/solicitar',{'pagoId':'x'})[0]==404)
s,j=a1('POST','/api/facturas/solicitar',{'pagoId':pid});ok('el_alumno_pide_la_factura_de_su_pago',s==200)
fa=[v['data'] for v in a1('GET','/api/col/facturas')[1]['docs']]
ok('la_solicitud_guarda_los_datos_del_momento',len(fa)==1 and fa[0]['estado']=='solicitada' and fa[0]['rfc']=='LORA900101AB1' and fa[0]['monto']==3900 and fa[0]['folioPago']=='R-000001' and fa[0]['sid']=='s1')
ok('no_se_puede_pedir_dos_veces',a1('POST','/api/facturas/solicitar',{'pagoId':pid})[0]==400)
ok('otro_alumno_no_ve_la_factura',len(a2('GET','/api/col/facturas')[1]['docs'])==0)
fid=fa[0]['id']
put('ledger/s2',{'pagos':ledger('s2')+[{'id':'pt1','folio':'R-000050','fecha':'2026-11-10','monto':500,'metodo':'Transferencia','estado':'pendiente','cc':[]}]});a2('PUT','/api/fiscal',f(rfc='MERB900101AB1',razon='Beto Mena Ruiz'))
ok('un_pago_sin_confirmar_no_se_factura',a2('POST','/api/facturas/solicitar',{'pagoId':'pt1'})[0]==400)
# ============ la factura la registra Finanzas ============
ok('quien_no_tiene_pagos_no_ve_las_solicitudes',len(caja('GET','/api/facturas')[1]['facturas'])==1 and esc('GET','/api/facturas')[0]==403 and a1('GET','/api/facturas')[0]==403)
def sube(cx,nombre,datos):return cx('POST','/api/archivo',raw=datos,hdr={'x-nombre':nombre,'x-privado':'1','x-categoria':'factura','Content-Type':'application/octet-stream'})
s,x=sube(caja,'f.xml',b'<cfdi/>');s2,pf=sube(caja,'f.pdf',b'%PDF-1.4 factura')
ok('caja_sube_el_xml_y_el_pdf_como_archivos_privados',s==200 and s2==200 and len(x['id'])==32)
UU='6A5E1F32-1B2C-4D3E-8F40-5A6B7C8D9E0F'
em=lambda **k:caja('POST','/api/facturas/emitir',dict({'id':fid,'serie':'A','folio':'101','uuid':UU,'xml':{'id':x['id'],'name':'f.xml'},'pdf':{'id':pf['id'],'name':'f.pdf'}},**k))
ok('rechaza_uuid_invalido_o_archivos_faltantes',em(uuid='123')[0]==400 and em(xml=None)[0]==400 and em(pdf={'id':'a'*32,'name':'x'})[0]==400)
ok('control_escolar_no_registra_facturas',esc('POST','/api/facturas/emitir',{'id':fid})[0]==403 and a1('POST','/api/facturas/emitir',{'id':fid})[0]==403)
ok('caja_registra_la_factura',em()[0]==200)
fa=[v['data'] for v in a1('GET','/api/col/facturas')[1]['docs']][0]
ok('queda_emitida_con_su_folio_fiscal',fa['estado']=='emitida' and fa['uuid']==UU and fa['serie']=='A' and fa['emitidaPor']=='caja1' and fa['xml']['id']==x['id'])
ok('no_se_puede_emitir_dos_veces',em()[0]==400)
av=[v['data'] for v in adm('GET','/api/col/avisos')[1]['docs'] if v['data']['sid']=='s1' and 'factura' in v['data']['titulo'].lower()];ok('el_alumno_recibe_el_aviso_de_factura_lista',len(av)==1 and 'R-000001' in av[0]['mensaje'])
def blob(cx,i):
    rq=urllib.request.Request(B+'/_blob/'+i)
    try:return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cx.__closure__ and None)).open(rq).status
    except Exception as e:return getattr(e,'code',0)
def blob2(c,i):  # con la sesión de cada quien
    s,d=c('GET','/_blob/'+i);return s
ok('el_alumno_descarga_su_factura',blob2(a1,x['id'])==200 and blob2(a1,pf['id'])==200)
sinsesion=sesion(None,None)
ok('otro_alumno_y_quien_no_inicio_sesion_no_pueden',blob2(a2,x['id'])==403 and blob2(sinsesion,x['id'])==401)
ok('caja_y_el_administrador_si_pueden',blob2(caja,x['id'])==200 and blob2(adm,pf['id'])==200 and blob2(esc,x['id'])==403)
# ============ rechazar ============
s,j=a2('POST','/api/facturas/solicitar',{'pagoId':ledger('s2')[0]['id']});fid2=[v['data'] for v in a2('GET','/api/col/facturas')[1]['docs']][0]['id']
ok('se_rechaza_con_motivo',caja('POST','/api/facturas/rechazar',{'id':fid2,'motivo':'x'})[0]==400 and caja('POST','/api/facturas/rechazar',{'id':fid2,'motivo':'El RFC no coincide con tu constancia fiscal.'})[0]==200)
f2=[v['data'] for v in a2('GET','/api/col/facturas')[1]['docs']][0];ok('el_alumno_ve_el_motivo',f2['estado']=='rechazada' and 'RFC no coincide' in f2['motivo'])
s,j=a2('POST','/api/facturas/solicitar',{'pagoId':ledger('s2')[0]['id']});ok('despues_de_un_rechazo_puede_volver_a_pedirla',s==200)
# ============ plazo ============
open(RELOJ,'w').write('2026-12-04');ok('hasta_el_dia_limite_del_mes_siguiente_aun_se_puede',a1('POST','/api/facturas/solicitar',{'pagoId':pid})[0]==400 and 'Ya pediste' in a1('POST','/api/facturas/solicitar',{'pagoId':pid})[1]['error'])
put('ledger/s3',{'pagos':[{'id':'pz','folio':'R-000060','fecha':'2026-10-20','monto':100,'metodo':'Efectivo','cc':[]}]});a3('PUT','/api/fiscal',f(rfc='DIAC900101AB1',razon='Carla Díaz'));open(RELOJ,'w').write('2026-11-05')
ok('un_pago_de_octubre_aun_se_factura_el_5_de_noviembre_pero_no_despues',a3('POST','/api/facturas/solicitar',{'pagoId':'pz'})[0]==200)
put('ledger/s3',{'pagos':[{'id':'pw','folio':'R-000061','fecha':'2026-10-20','monto':100,'metodo':'Efectivo','cc':[]}]});open(RELOJ,'w').write('2026-11-06');r=a3('POST','/api/facturas/solicitar',{'pagoId':'pw'})
ok('pasado_el_plazo_lo_rechaza_y_dice_la_fecha',r[0]==400 and '05/11/2026' in r[1]['error'])
# ============ configuración de facturas apagada ============
adm('PUT','/api/pagos-linea/config',cfg(facturas={'activo':False,'diaLimite':5}));ok('con_la_facturacion_apagada_no_se_piden',a2('POST','/api/facturas/solicitar',{'pagoId':ledger('s2')[0]['id']})[0]==400)
adm('PUT','/api/pagos-linea/config',cfg(activo=False));ok('con_los_pagos_apagados_no_se_crean_sesiones',a1('POST','/api/pagos-linea/checkout',{'opcion':'c:c4'})[0]==400 and a1('GET','/api/pagos-linea/estado')[1]['activo'] is False)
dbc=sqlite3.connect('/tmp/nbdata102/lafragua.db');acc=[r[0] for r in dbc.execute("select accion from auditoria").fetchall()];dbc.close()
ok('queda_en_la_auditoria',any('pagos en línea' in a.lower() for a in acc) and any('Pago en línea recibido' in a for a in acc) and any('Registró una factura' in a for a in acc))
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
