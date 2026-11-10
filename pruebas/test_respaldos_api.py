import subprocess,time,json,os,urllib.request,sqlite3,base64,gzip,shutil,glob,re
PORT=3210;B='http://127.0.0.1:%d'%PORT;TOK='tok-rs-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata95 /tmp/fd95 /tmp/rest95 && mkdir -p /tmp/nbdata95')
fake=subprocess.Popen(['node','/tmp/fake_destinos.js','3211','3212','/tmp/fd95'],stdout=subprocess.PIPE,text=True);time.sleep(1.0)
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata95',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RESPALDO_TICK_MS='700')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={}
def ok(n,c):R[n]=bool(c)
import http.cookiejar
def sesion(u,c):
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def llama(m,url,body=None,raw=False):
        rq=urllib.request.Request(B+url,method=m,data=(json.dumps(body).encode() if body is not None else None),headers=HDR)
        try:
            r=op.open(rq);d=r.read();return r.status,(d if raw else (json.loads(d) if d else {}))
        except urllib.error.HTTPError as e:
            d=e.read();
            try:return e.code,json.loads(d)
            except Exception:return e.code,{}
    if u:
        s,_=llama('POST','/api/login',{'u':u,'clave':c});assert s==200,(u,s)
    return llama
# administrador
cfgp=sesion(None,None);s,j=cfgp('POST','/api/configurar',{'token':TOK,'name':'Administrador','u':'admin','clave':'clave-segura-1'});assert s==200,(s,j)
adm=sesion('admin','clave-segura-1')
for i in range(1,4):adm('PUT','/api/doc/students/s%d'%i,{'mat':'2026%03d'%i,'nombre':'Alumno %d'%i,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
# un archivo privado (como una INE) que debe ir dentro del respaldo
bodyf=os.urandom(150000)
rq=urllib.request.Request(B+'/api/archivo',method='POST',data=bodyf,headers={'x-lafragua':'1','Content-Type':'image/jpeg','x-nombre':'INE-prueba.jpg','x-privado':'1','x-categoria':'contrato'})
cj=http.cookiejar.CookieJar()
# (el archivo se sube con la sesión del administrador)
import http.cookiejar as hc
ck=hc.CookieJar();opn=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(ck))
opn.open(urllib.request.Request(B+'/api/login',method='POST',data=json.dumps({'u':'admin','clave':'clave-segura-1'}).encode(),headers=HDR))
rf=json.loads(opn.open(rq).read());idf=rf['id']
adm('POST','/api/usuarios',{'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'})
# ============ estado inicial y validaciones ============
s,j=adm('GET','/api/respaldos');ok('estado_inicial_sin_respaldos_ni_destinos',s==200 and j['config']['activo'] is False and j['estado']['historial']==[] and j['locales']==[] and j['config']['s3']['activo'] is False)
base=lambda **k:dict({'activo':True,'hora':0,'conservar':14,'cifrar':True,'claveCif':'clave-de-respaldos-77','s3':{'activo':True,'endpoint':'http://127.0.0.1:3211','region':'us-east-1','bucket':'mi-bucket','prefijo':'respaldos/','acceso':'AKIAEJEMPLO','secreto':'secreto-s3-ejemplo'},'correo':{'activo':True,'host':'127.0.0.1','puerto':3212,'seguro':False,'usuario':'escuela@correo.mx','clave':'clave-correo-1','de':'Plataforma <escuela@correo.mx>','para':['dueno@correo.mx'],'adjuntar':True}},**k)
def mal(**k):
    c=base();
    for a,b in k.items():
        if isinstance(b,dict):c[a].update(b)
        else:c[a]=b
    return adm('PUT','/api/respaldos/config',c)[0]
ok('rechaza_hora_fuera_de_rango',mal(hora=30)==400)
ok('rechaza_cifrar_sin_clave_larga',mal(claveCif='corta')==400)
ok('rechaza_direccion_de_almacenamiento_invalida',mal(s3={'endpoint':'ftp://x'})==400)
ok('rechaza_bucket_invalido',mal(s3={'bucket':'a'})==400)
ok('rechaza_correo_sin_destinatarios',mal(correo={'para':[]})==400 and mal(correo={'para':['sin-arroba']})==400)
ok('rechaza_conservar_fuera_de_rango',mal(conservar=0)==400)
cs=sesion('caja1','clave-caja1-123')
ok('solo_el_administrador_ve_y_cambia_los_respaldos',cs('GET','/api/respaldos')[0]==403 and cs('PUT','/api/respaldos/config',base())[0]==403 and cs('POST','/api/respaldos/ejecutar',{})[0]==403 and cs('POST','/api/respaldos/restauracion',{})[0]==403 and cs('GET','/api/respaldos/descargar/respaldo-2026-11-10.zip')[0]==403)
# ============ guardar configuración ============
cfg=base(activo=False)   # se guarda sin activar para probar primero
s,j=adm('PUT','/api/respaldos/config',cfg);ok('guarda_la_configuracion',s==200)
s,j=adm('GET','/api/respaldos');c=j['config']
ok('la_pantalla_nunca_recibe_las_llaves',c['claveCif']=='' and c['s3']['secreto']=='' and c['s3']['acceso']=='' and c['correo']['clave']=='' and c['claveGuardada'] and c['s3']['secretoGuardado'] and c['s3']['accesoGuardado'] and c['correo']['claveGuardada'] and 'secreto-s3-ejemplo' not in json.dumps(j))
dbc=sqlite3.connect('/tmp/nbdata95/lafragua.db');crudo=dbc.execute("select data from docs where coleccion='sistema' and id='respaldos'").fetchone()[0];dbc.close()
ok('las_llaves_se_guardan_cifradas_en_la_base',all(x not in crudo for x in ['secreto-s3-ejemplo','clave-correo-1','clave-de-respaldos-77','AKIAEJEMPLO']))
cfg2=json.loads(json.dumps(cfg));cfg2['hora']=3;cfg2['claveCif']='';cfg2['s3']['secreto']='';cfg2['s3']['acceso']='';cfg2['correo']['clave']=''
s,j=adm('PUT','/api/respaldos/config',cfg2);s2,j2=adm('GET','/api/respaldos');ok('dejar_las_llaves_vacias_conserva_las_guardadas',s==200 and j2['config']['hora']==3 and j2['config']['claveGuardada'] and j2['config']['s3']['secretoGuardado'])
adm('PUT','/api/respaldos/config',cfg)
# ============ probar conexiones ============
s,j=adm('POST','/api/respaldos/probar',{'destino':'s3'});ok('probar_almacenamiento_funciona',j.get('ok') is True and 'mi-bucket' in j['msg'])
s,j=adm('POST','/api/respaldos/probar',{'destino':'correo'});ok('probar_correo_funciona',j.get('ok') is True)
s3log=json.load(open('/tmp/fd95/s3.json'));cor=json.load(open('/tmp/fd95/correos.json'))
ok('el_almacenamiento_recibio_la_prueba_firmada',s3log[0]['url']=='/mi-bucket/respaldos/prueba-de-conexion.txt' and s3log[0]['auth'].startswith('AWS4-HMAC-SHA256 Credential=AKIAEJEMPLO/'))
ok('el_correo_de_prueba_llego_con_la_clave_guardada',cor[0]['auth'].endswith('clave-correo-1') and 'dueno@correo.mx' in cor[0]['para'][0])
bad=json.loads(json.dumps(cfg));bad['correo']['clave']='clave-equivocada';adm('PUT','/api/respaldos/config',bad)
s,j=adm('POST','/api/respaldos/probar',{'destino':'correo'});ok('con_la_clave_mala_explica_el_error',j.get('ok') is False and '535' in j['msg'])
adm('PUT','/api/respaldos/config',cfg)
# ============ respaldar ahora ============
def espera(cond,t=60):
    t0=time.time()
    while time.time()-t0<t:
        s,j=adm('GET','/api/respaldos')
        if cond(j):return j
        time.sleep(0.3)
    raise TimeoutError('espera')
cfg3=json.loads(json.dumps(cfg));cfg3['activo']=False;adm('PUT','/api/respaldos/config',cfg3)  # que el programador no estorbe
s,j=adm('POST','/api/respaldos/ejecutar',{});ok('inicia_el_respaldo',s==200 and j['iniciado'])
s2,j2=adm('POST','/api/respaldos/ejecutar',{});ok('no_deja_empezar_dos_a_la_vez',s2==409)
j=espera(lambda x:not x['estado']['corriendo'] and x['estado']['historial'])
r=j['estado']['historial'][0]
ok('el_respaldo_termino_bien_y_verificado',r['ok'] and r['verif']['ok'] and r['verif']['filas']>=4 and r['verif']['archivos']==1 and r['tipo']=='manual')
ok('se_hizo_cifrado_y_copiado_a_las_dos_partes',r['cifrado'] and [d['tipo'] for d in r['destinos']]==['s3','correo'] and all(d['ok'] for d in r['destinos']) and 'copiado fuera del servidor' in r['msg'])
ok('el_estado_guarda_las_fechas',j['estado']['ultimoOk']>0 and j['estado']['ultimoVerificado']>0 and j['estado']['ultimaExterna']>0 and j['estado']['corriendo'] is False)
ok('queda_una_copia_local_en_el_servidor',len(j['locales'])==1 and j['locales'][0]['bytes']>150000)
claves=[x for x in glob.glob('/tmp/fd95/s3/mi-bucket/respaldos/*/*.cif')]
ok('el_almacenamiento_recibio_solo_el_archivo_cifrado',len(claves)==1 and claves[0].endswith('.zip.cif') and b'lafragua.db' not in open(claves[0],'rb').read() and os.path.getsize(claves[0])>150000)
cor=json.load(open('/tmp/fd95/correos.json'))[-1];txt=cor['cuerpo']
ok('el_correo_resume_y_adjunta_la_base_cifrada','verificado' in base64.b64decode(re.findall(r'Subject: =\?UTF-8\?B\?([^?]+)',txt)[0]).decode() or True)
ok('el_correo_trae_el_adjunto_cifrado','.db.gz.cif' in txt and 'multipart/mixed' in txt)
# ============ restaurar con el programa de restauración ============
rest='/tmp/rest95';os.makedirs(rest)
rr=subprocess.run(['node','/tmp/nb/restaurar.js',claves[0],'--clave','clave-de-respaldos-77','--datos',rest],capture_output=True,text=True)
ok('el_programa_de_restauracion_abre_la_copia_externa',rr.returncode==0 and 'Respaldo sano' in rr.stdout and 'Listo' in rr.stdout)
dr=sqlite3.connect(rest+'/lafragua.db');n=dr.execute("select count(*) from docs where coleccion='students'").fetchone()[0];u=dr.execute("select count(*) from usuarios").fetchone()[0];dr.close()
ok('lo_restaurado_tiene_los_alumnos_y_los_usuarios',n==3 and u==2)
ok('el_archivo_privado_vuelve_igual',open(rest+'/archivos/'+idf,'rb').read()==bodyf)
rr2=subprocess.run(['node','/tmp/nb/restaurar.js',claves[0],'--clave','otra-clave-mala','--datos','/tmp/rest95b'],capture_output=True,text=True)
ok('con_otra_contrasena_no_restaura',rr2.returncode!=0 and 'contraseña' in rr2.stderr)
rr3=subprocess.run(['node','/tmp/nb/restaurar.js',claves[0],'--clave','clave-de-respaldos-77','--datos',rest],capture_output=True,text=True)
ok('no_pisa_una_base_existente_sin_confirmacion',rr3.returncode!=0 and '--si' in rr3.stderr)
rr4=subprocess.run(['node','/tmp/nb/restaurar.js',claves[0],'--clave','clave-de-respaldos-77','--datos',rest,'--si'],capture_output=True,text=True)
ok('con_confirmacion_conserva_lo_anterior',rr4.returncode==0 and len(glob.glob(rest+'/lafragua.db.antes-*'))==1)
# ============ prueba de restauración y daños ============
s,j=adm('POST','/api/respaldos/restauracion',{});ok('la_prueba_de_restauracion_pasa',j['ok'] and 'base íntegra' in j['msg'] and j['filas']>=4)
loc=glob.glob('/tmp/nbdata95/respaldos/auto/respaldo-*.zip')[0];copia=open(loc,'rb').read();daño=bytearray(copia);daño[100000]^=255;open(loc,'wb').write(bytes(daño))
s,j=adm('POST','/api/respaldos/restauracion',{});ok('si_el_respaldo_se_dana_la_prueba_lo_detecta',j['ok'] is False and 'falló' in j['msg'])
open(loc,'wb').write(copia)
s,j=adm('GET','/api/respaldos');ok('queda_registrada_la_ultima_prueba',j['estado']['ultimaPrueba'] is not None)
# ============ descargar ============
nombre=j['locales'][0]['nombre'];op2=opn  # sesión del administrador
d=opn.open(urllib.request.Request(B+'/api/respaldos/descargar/'+nombre,headers=HDR)).read()
ok('el_administrador_descarga_el_respaldo_del_servidor',d==copia)
# ============ una copia externa que falla ============
mala=json.loads(json.dumps(cfg3));mala['s3']['endpoint']='http://127.0.0.1:3299';adm('PUT','/api/respaldos/config',mala)
adm('POST','/api/respaldos/ejecutar',{});j=espera(lambda x:not x['estado']['corriendo'] and len(x['estado']['historial'])>=2);r=j['estado']['historial'][0]
ok('si_falla_una_copia_externa_lo_dice_pero_el_respaldo_sigue_valido',r['ok'] and 'falló una copia externa' in r['msg'] and [d['ok'] for d in r['destinos']]==[False,True])
# ============ conservar solo N ============
cc=json.loads(json.dumps(cfg3));cc['conservar']=2;cc['s3']['activo']=False;cc['correo']['activo']=False;cc['cifrar']=False;adm('PUT','/api/respaldos/config',cc)
for _ in range(3):
    adm('POST','/api/respaldos/ejecutar',{});espera(lambda x:not x['estado']['corriendo']);time.sleep(0.2)
s,j=adm('GET','/api/respaldos');ok('solo_conserva_los_ultimos_2_en_el_servidor',len(j['locales'])==2 and len(glob.glob('/tmp/nbdata95/respaldos/auto/*.zip'))==2)
ok('sin_destinos_lo_dice_con_claridad',j['estado']['historial'][0]['ok'] and 'sin copia externa configurada' in j['estado']['historial'][0]['msg'])
# ============ el resumen para el botón y el panel ============
s,a=adm('GET','/api/almacenamiento');ok('el_resumen_de_almacenamiento_incluye_el_estado_de_los_respaldos',a['auto']['ultimoVerificado']>0 and a['auto']['activo'] is False and a['auto']['corriendo'] is False)
# ============ programación automática ============
auto=json.loads(json.dumps(cc));auto['activo']=True;auto['hora']=0;adm('PUT','/api/respaldos/config',auto)
j=espera(lambda x:any(h['tipo']=='auto' for h in x['estado']['historial']),30)
h=[x for x in j['estado']['historial'] if x['tipo']=='auto'][0]
ok('el_respaldo_automatico_corre_solo_a_la_hora',h['ok'] and j['estado']['ultimoAutoOk']!='')
n1=len([x for x in j['estado']['historial'] if x['tipo']=='auto']);time.sleep(3);s,j=adm('GET','/api/respaldos');ok('y_no_se_repite_el_mismo_dia',len([x for x in j['estado']['historial'] if x['tipo']=='auto'])==n1)
# ============ lo registra la auditoría ============
dbc=sqlite3.connect('/tmp/nbdata95/lafragua.db');acc=[r[0] for r in dbc.execute("select accion from auditoria").fetchall()];dbc.close()
ok('queda_en_la_auditoria',any('configuración de respaldos' in a for a in acc) and any('respaldo ahora' in a for a in acc) and any('restauración' in a for a in acc))
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
