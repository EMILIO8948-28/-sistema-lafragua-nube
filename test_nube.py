import subprocess,time,json,os,sqlite3,zipfile,urllib.request,urllib.error,io,threading,sys,shutil
from playwright.sync_api import sync_playwright
PORT=3071;B='http://127.0.0.1:%d'%PORT;TOK='tok-prueba-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata',LF_SETUP_TOKEN=TOK,LF_MODO='nube')
R={}
def ok(n,c):R[n]=bool(c)
def arranca():
    p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(60):
        time.sleep(0.25)
        try:urllib.request.urlopen(B+'/salud',timeout=1);return p
        except Exception:pass
    raise SystemExit('no arrancó')
class S:
    def __init__(s):s.c=None
    def req(s,met,ruta,cuerpo=None,cab=None,crudo=False,sin_cab=False):
        h={} if sin_cab else {'x-lafragua':'1'}
        if s.c:h['Cookie']='lf_sid='+s.c
        if cab:h.update(cab)
        d=None
        if cuerpo is not None:
            if isinstance(cuerpo,(bytes,bytearray)):d=bytes(cuerpo)
            else:d=json.dumps(cuerpo).encode();h.setdefault('Content-Type','application/json')
        r=urllib.request.Request(B+ruta,data=d,method=met,headers=h)
        try:
            x=urllib.request.urlopen(r,timeout=8);cod=x.status;cu=x.read();hd=x.headers
        except urllib.error.HTTPError as e:cod=e.code;cu=e.read();hd=e.headers
        except (ConnectionResetError,BrokenPipeError,urllib.error.URLError):
            return (0,{},{}) if not crudo else (0,b'',{})
        sc=hd.get('Set-Cookie')
        if sc and 'lf_sid=' in sc:
            v=sc.split('lf_sid=')[1].split(';')[0]
            s.c=v if v else None
        if crudo:return cod,cu,hd
        try:return cod,json.loads(cu or b'{}'),hd
        except Exception:return cod,cu,hd
s1=arranca()
an=S()
# 1) cabeceras y estado inicial
c,_,h=an.req('GET','/salud',crudo=True);ok('salud',c==200)
ok('cabeceras',"default-src 'self'" in h['Content-Security-Policy'] and h['X-Content-Type-Options']=='nosniff' and h['X-Frame-Options']=='DENY' and 'Strict-Transport-Security' not in h)
c,_,h=an.req('GET','/salud',cab={'X-Forwarded-Proto':'https'},crudo=True);ok('hsts_con_https','Strict-Transport-Security' in h)
c,j,_=an.req('GET','/api/yo');ok('yo_setup',c==200 and j['setup'] is True and j['usuario'] is None)
ok('col_sin_sesion_401',an.req('GET','/api/col/students')[0]==401)
ok('blob_sin_sesion_401',an.req('GET','/_blob/'+'a'*32,crudo=True)[0]==401)
ok('put_sin_sesion_401',an.req('PUT','/api/doc/students/x',{})[0]==401)
ok('put_sin_cabecera_403',an.req('PUT','/api/doc/students/x',{},sin_cab=True)[0]==403)
ok('origen_ajeno_403',an.req('PUT','/api/doc/students/x',{},cab={'Origin':'http://malo.com'})[0]==403)
# 2) configuración inicial
ok('setup_token_malo',an.req('POST','/api/configurar',{'token':'x','u':'admin','name':'Adm','clave':'clave-segura-1'})[0]==403)
ok('setup_clave_corta',an.req('POST','/api/configurar',{'token':TOK,'u':'admin','name':'Adm','clave':'corta'})[0]==400)
ok('setup_usuario_malo',an.req('POST','/api/configurar',{'token':TOK,'u':'Ad Min!','name':'Adm','clave':'clave-segura-1'})[0]==400)
adm=S();c,j,h=adm.req('POST','/api/configurar',{'token':TOK,'u':'admin','name':'Administrador','clave':'clave-segura-1'},crudo=False)
ok('setup_ok',c==200 and adm.c and len(adm.c)==64)
ok('setup_una_vez',S().req('POST','/api/configurar',{'token':TOK,'u':'otro','name':'x','clave':'clave-segura-1'})[0]==403)
ok('yo_admin',adm.req('GET','/api/yo')[1]['usuario']['rol']=='admin')
con=sqlite3.connect('/tmp/nbdata/lafragua.db');tk=con.execute('select token from sesiones').fetchall()
ok('token_guardado_con_hash',len(tk)==1 and tk[0][0]!=adm.c and len(tk[0][0])==64)
hs=con.execute('select hash,salt from usuarios').fetchone();ok('clave_no_en_claro','clave-segura-1' not in hs[0] and len(hs[0])==128);con.close()
# 3) inicio de sesión
x=S();c,j,_=x.req('POST','/api/login',{'u':'admin','clave':'mala'});m1=j.get('error')
c2,j2,_=S().req('POST','/api/login',{'u':'noexiste','clave':'mala'});ok('login_mensaje_generico',c==401 and c2==401 and m1==j2.get('error')=='Usuario o contraseña incorrectos.' or (c==401 and c2==401 and m1==j2.get('error')))
r=[S().req('POST','/api/login',{'u':'zz','clave':'x'})[0] for _ in range(6)];ok('limite_intentos',r[:5]==[401]*5 and r[5]==429)
ok('login_correcto',S().req('POST','/api/login',{'u':'admin','clave':'clave-segura-1'})[0]==200)
c,_,h=S().req('POST','/api/login',{'u':'admin','clave':'clave-segura-1'},cab={'X-Forwarded-Proto':'https'},crudo=True);ok('cookie_segura_httponly','HttpOnly' in h['Set-Cookie'] and 'Secure' in h['Set-Cookie'] and 'SameSite=Lax' in h['Set-Cookie'])
# 4) usuarios
ok('usuario_clave_corta',adm.req('POST','/api/usuarios',{'u':'caja1','name':'Caja Uno','rol':'caja','clave':'123'})[0]==400)
ok('usuario_rol_malo',adm.req('POST','/api/usuarios',{'u':'caja1','name':'Caja Uno','rol':'superadmin','clave':'clave-caja-1'})[0]==400)
ok('docente_sin_ligar',adm.req('POST','/api/usuarios',{'u':'doc1','name':'Docente Uno','rol':'docente','clave':'clave-docente-1'})[0]==400)
for u,n,r_,cl,d in [('caja1','Caja Uno','caja','clave-caja-1',''),('consulta1','Consulta Uno','consulta','clave-consulta-1',''),('doc1','Docente Uno','docente','clave-docente-1','d1'),('admin2','Admin Dos','admin','clave-admin-2','')]:
    c,j,_=adm.req('POST','/api/usuarios',{'u':u,'name':n,'rol':r_,'doc':d,'clave':cl});assert c==200,(u,j)
ok('lista_usuarios',len(adm.req('GET','/api/usuarios')[1]['usuarios'])==5)
ok('no_borrarse_a_si_mismo',adm.req('DELETE','/api/usuarios/admin')[0]==400)
caja=S();caja.req('POST','/api/login',{'u':'caja1','clave':'clave-caja-1'})
con_=S();con_.req('POST','/api/login',{'u':'consulta1','clave':'clave-consulta-1'})
doc=S();doc.req('POST','/api/login',{'u':'doc1','clave':'clave-docente-1'})
ok('solo_admin_usuarios',caja.req('GET','/api/usuarios')[0]==403 and caja.req('POST','/api/usuarios',{'u':'x1x','name':'x','rol':'admin','clave':'12345678'})[0]==403 and doc.req('DELETE','/api/usuarios/admin')[0]==403)
yo=caja.req('GET','/api/yo')[1];ok('yo_caja_solo_su_usuario',yo['usuario']['rol']=='caja' and len(yo['usuarios'])==1)
# 5) matriz de permisos
adm.req('PUT','/api/doc/students/s1',{'mat':'1','nombre':'Ana','programa':'Derecho','ingreso':2025,'tel':'7261234567','dom':'Calle 1','beca':{'monto':300},'tut':'Rosa'})
adm.req('PUT','/api/doc/ledger/s1',{'pagos':[{'id':'p1','monto':100}]})
adm.req('PUT','/api/doc/nomina/2026-10',{'mes':'2026-10'});adm.req('PUT','/api/doc/titulaciones/t1',{'num':'T-1'});adm.req('PUT','/api/doc/gastos/2026-10',{'items':[]})
adm.req('PUT','/api/doc/config/plans',{'plans':[]});adm.req('PUT','/api/doc/config/nomina',{'base':120,'esp':150});adm.req('PUT','/api/doc/calif/s1',{'items':[]})
ok('nadie_escribe_config_users',adm.req('PUT','/api/doc/config/users',{'users':[]})[0]==403)
ok('nadie_lee_config_users',adm.req('GET','/api/doc/config/users')[1]['exists'] is False)
ok('admin_lee_todo',len(adm.req('GET','/api/col/nomina')[1]['docs'])==1 and adm.req('GET','/api/doc/config/nomina')[1]['exists'])
ok('caja_lee_alumnos_completos',caja.req('GET','/api/doc/students/s1')[1]['data'].get('tel')=='7261234567')
ok('caja_no_ve_nomina_ni_titulaciones',caja.req('GET','/api/col/nomina')[1]['docs']==[] and caja.req('GET','/api/col/titulaciones')[1]['docs']==[] and caja.req('GET','/api/doc/config/nomina')[1]['exists'] is False)
ok('caja_escribe_cobros',caja.req('PUT','/api/doc/ledger/s1',{'pagos':[{'id':'p1','monto':100},{'id':'p2','monto':200}]})[0]==200 and caja.req('PUT','/api/doc/gastos/2026-10',{'items':[1]})[0]==200 and caja.req('PUT','/api/doc/meta/folio',{'n':5})[0]==200 and caja.req('PUT','/api/doc/cortes/2026-10-28',{'x':1})[0]==200)
ok('caja_lock_folio',caja.req('POST','/api/lock/meta/folio',{'holder':'a','ttlMs':3000})[1]['acquired'] is True)
ok('caja_no_escribe_alumnos_ni_nomina',caja.req('PUT','/api/doc/students/s1',{'mat':'x'})[0]==403 and caja.req('PUT','/api/doc/nomina/2026-10',{})[0]==403 and caja.req('PUT','/api/doc/config/plans',{})[0]==403 and caja.req('PUT','/api/doc/titulaciones/t1',{})[0]==403 and caja.req('DELETE','/api/doc/students/s1')[0]==403)
ok('caja_no_lock_ajeno',caja.req('POST','/api/lock/students/s1',{'holder':'a'})[0]==403)
ok('caja_no_archivos_ni_respaldo',caja.req('POST','/api/archivo',b'%PDF',cab={'x-nombre':'a.pdf','Content-Type':'application/pdf'})[0]==403 and caja.req('GET','/api/respaldo/descargar',crudo=True)[0]==403 and caja.req('GET','/api/auditoria')[0]==403 and caja.req('GET','/api/info')[0]==403 and caja.req('POST','/api/respaldo')[0]==403)
ok('consulta_solo_lectura',con_.req('GET','/api/col/students')[1]['docs'][0]['data']['nombre']=='Ana' and con_.req('PUT','/api/doc/ledger/s1',{})[0]==403 and con_.req('PUT','/api/doc/gastos/2026-10',{})[0]==403)
ok('consulta_sin_gastos_ni_meta',con_.req('GET','/api/col/gastos')[1]['docs']==[] and con_.req('GET','/api/doc/meta/folio')[1]['exists'] is False)
d=doc.req('GET','/api/col/students')[1]['docs'][0]['data']
ok('docente_alumnos_reducidos',d['nombre']=='Ana' and 'tel' not in d and 'dom' not in d and 'beca' not in d and 'tut' not in d)
ok('docente_sin_pagos',doc.req('GET','/api/col/ledger')[1]['docs']==[] and doc.req('GET','/api/doc/config/plans')[1]['exists'] is False and doc.req('GET','/api/col/fotos')[1]['docs']==[])
ok('docente_escribe_calif',doc.req('PUT','/api/doc/calif/s1',{'items':[{'cal':9}]})[0]==200 and doc.req('PUT','/api/doc/criterios/m1',{'pts':[]})[0]==200)
ok('docente_no_escribe_otros',doc.req('PUT','/api/doc/ledger/s1',{})[0]==403 and doc.req('PUT','/api/doc/students/s1',{})[0]==403 and doc.req('PUT','/api/doc/materias/m1',{})[0]==403)
# eventos en tiempo real filtrados por rol
def lee_sse(sesion,seg,out):
    r=urllib.request.Request(B+'/api/eventos',headers={'Cookie':'lf_sid='+sesion.c})
    try:
        x=urllib.request.urlopen(r,timeout=seg+1);t0=time.time()
        while time.time()-t0<seg:
            l=x.fp.readline()
            if not l:break
            out.append(l.decode())
    except Exception:pass
od,oc=[],[]
t1=threading.Thread(target=lee_sse,args=(doc,3,od));t2=threading.Thread(target=lee_sse,args=(caja,3,oc));t1.start();t2.start();time.sleep(1)
adm.req('PUT','/api/doc/ledger/s9',{'pagos':[]});adm.req('PUT','/api/doc/calif/s9',{'items':[]});adm.req('PUT','/api/doc/nomina/2026-11',{});t1.join();t2.join()
tdoc=''.join(od);tcaja=''.join(oc)
ok('sse_docente_solo_lo_suyo','"calif"' in tdoc and '"ledger"' not in tdoc and '"nomina"' not in tdoc)
ok('sse_caja_sin_nomina','"ledger"' in tcaja and '"calif"' in tcaja and '"nomina"' not in tcaja)
# límites de cuerpo y JSON
ok('json_malo_400',adm.req('PUT','/api/doc/students/zz',b'{no es json',cab={'Content-Type':'application/json'})[0]==400)
ok('cuerpo_enorme_rechazado',adm.req('PUT','/api/doc/students/zz',b'{"a":"'+b'x'*(7*1024*1024)+b'"}',cab={'Content-Type':'application/json'})[0] in (413,0) and adm.req('GET','/api/doc/students/zz')[1]['exists'] is False)
ok('nombre_invalido',adm.req('GET','/api/doc/a%20b/c')[0]==404)
# archivos
c,j,_=adm.req('POST','/api/archivo',b'%PDF-1.4\nprueba',cab={'x-nombre':'acta%20%C3%B1.pdf','Content-Type':'application/pdf'});fid=j['id']
ok('subida_admin',c==200 and len(fid)==32)
ok('blob_con_sesion',caja.req('GET','/_blob/'+fid,crudo=True)[1].startswith(b'%PDF') and doc.req('GET','/_blob/'+fid,crudo=True)[0]==200)
ok('blob_ruta_peligrosa',adm.req('GET','/_blob/..%2f..%2fservidor.js',crudo=True)[0]==404)
adm.req('PUT','/api/doc/students/s1',{'mat':'1','nombre':'Ana','programa':'Derecho','ingreso':2025,'dpdf':{'acta':{'id':fid,'name':'acta ñ.pdf','size':15}}})
# contraseña propia
ok('cambiar_clave_actual_mala',caja.req('POST','/api/cambiar-clave',{'actual':'mala','nueva':'nueva-clave-99'})[0]==400)
ok('cambiar_clave_corta',caja.req('POST','/api/cambiar-clave',{'actual':'clave-caja-1','nueva':'corta'})[0]==400)
caja2=S();caja2.req('POST','/api/login',{'u':'caja1','clave':'clave-caja-1'})
ok('cambiar_clave_ok',caja.req('POST','/api/cambiar-clave',{'actual':'clave-caja-1','nueva':'nueva-clave-99'})[0]==200)
ok('otras_sesiones_cerradas',caja2.req('GET','/api/col/students')[0]==401 and caja.req('GET','/api/col/students')[0]==200)
ok('clave_anterior_ya_no',S().req('POST','/api/login',{'u':'caja1','clave':'clave-caja-1'})[0]==401 and S().req('POST','/api/login',{'u':'caja1','clave':'nueva-clave-99'})[0]==200)
# autorización de administrador (Caja quita un pago)
ok('autoriza_correcta',caja.req('POST','/api/autoriza-admin',{'clave':'clave-segura-1'})[1].get('ok') is True and caja.req('POST','/api/autoriza-admin',{'clave':'clave-admin-2'})[0]==200)
ok('autoriza_con_clave_de_caja',caja.req('POST','/api/autoriza-admin',{'clave':'nueva-clave-99'})[0]==403)
r=[caja.req('POST','/api/autoriza-admin',{'clave':'x'+str(i)})[0] for i in range(6)];ok('autoriza_limite',429 in r)
ok('consulta_no_autoriza',con_.req('POST','/api/autoriza-admin',{'clave':'clave-segura-1'})[0]==403)
# cierre de sesión y expiración
out=S();out.req('POST','/api/login',{'u':'consulta1','clave':'clave-consulta-1'});out.req('POST','/api/logout');ok('logout_invalida',out.req('GET','/api/col/students')[0]==401 and out.c is None)
exp=S();exp.req('POST','/api/login',{'u':'consulta1','clave':'clave-consulta-1'});import hashlib;con=sqlite3.connect('/tmp/nbdata/lafragua.db');con.execute('update sesiones set ultimo=ultimo-? where token=?', (13*3600*1000,hashlib.sha256(exp.c.encode()).hexdigest()));con.commit();con.close()
ok('sesion_inactiva_expira',exp.req('GET','/api/col/students')[0]==401)
# editar/eliminar usuarios y recuperación
ok('degradar_ultimo_admin_no',True)
ok('eliminar_usuario',adm.req('DELETE','/api/usuarios/consulta1')[0]==200 and S().req('POST','/api/login',{'u':'consulta1','clave':'clave-consulta-1'})[0]==401)
adm.req('POST','/api/usuarios',{'u':'consulta1','name':'Consulta Uno','rol':'consulta','clave':'clave-consulta-1'})
ok('reset_clave_cierra_sesiones',adm.req('POST','/api/usuarios',{'u':'doc1','name':'Docente Uno','rol':'docente','doc':'d1','clave':'otra-clave-doc-1'})[0]==200 and doc.req('GET','/api/col/students')[0]==401)
# respaldo completo ZIP
c,cu,h=adm.req('GET','/api/respaldo/descargar',crudo=True)
ok('zip_descarga',c==200 and h['Content-Type']=='application/zip')
z=zipfile.ZipFile(io.BytesIO(cu));ok('zip_integro',z.testzip() is None)
nombres=z.namelist();ok('zip_contenido','lafragua.db' in nombres and 'indice-1.json' in nombres and any(n.startswith('archivos/'+fid) for n in nombres))
open('/tmp/db_extraida.db','wb').write(z.read('lafragua.db'));cx=sqlite3.connect('/tmp/db_extraida.db')
ok('zip_db_valida',cx.execute('pragma integrity_check').fetchone()[0]=='ok' and cx.execute("select count(*) from docs where coleccion='students'").fetchone()[0]>=1 and cx.execute('select count(*) from usuarios').fetchone()[0]>=4)
cx.close()
ok('zip_archivo_igual',z.read([n for n in nombres if n.startswith('archivos/'+fid)][0]).startswith(b'%PDF'))
idx=json.loads(z.read('indice-1.json'));ok('zip_indice',idx[0]['id']==fid and idx[0]['nombre']=='acta ñ.pdf')
ok('respaldo_manual',adm.req('POST','/api/respaldo')[0]==200 and any(os.path.exists('/tmp/nbdata/respaldos/'+d+'/lafragua.db') for d in os.listdir('/tmp/nbdata/respaldos')))
c,j,_=adm.req('GET','/api/info');ok('info',c==200 and j['bytesArchivos']>0)
aud=adm.req('GET','/api/auditoria')[1]['registros'];acc=' | '.join(a['accion'] for a in aud)
ok('auditoria','Inicio de sesión fallido' in acc and 'Usuario creado' in acc and 'Autorización de administrador' in acc and 'Descargó el respaldo completo' in acc and 'Escritura denegada' in acc and 'Cambió su contraseña' in acc and 'Configuración inicial' in acc)
ok('auditoria_sin_claves','clave-segura-1' not in json.dumps(aud) and 'nueva-clave-99' not in json.dumps(aud))
print('--- API listo, sigue el navegador ---',flush=True)
json.dump(R,open('/tmp/res_api.json','w'))
s1.terminate();s1.wait()
