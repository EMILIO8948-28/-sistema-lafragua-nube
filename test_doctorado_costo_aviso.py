import subprocess,time,json,os,urllib.request,urllib.error,http.cookiejar,sqlite3
HDR={'Content-Type':'application/json','x-lafragua':'1'}
R={}
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
ANT={('ED%02d'%i):(1 if i<=4 else 2 if i<=7 else 3 if i<=10 else 4 if i<=13 else 5) for i in range(1,17)}
NOMS={('ED%02d'%i):'Seminario %d'%i for i in range(1,17)}
def arranca(port,data,tok,extra=None):
    env=dict(os.environ,PORT=str(port),DATA_DIR=data,LF_SETUP_TOKEN=tok,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000',LF_BAJAS_ARRANQUE_MS='600000',**(extra or {}))
    p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen('http://127.0.0.1:%d/salud'%port,timeout=1);break
        except Exception:pass
    return p
def para(p):
    p.terminate()
    try:out=p.communicate(timeout=5)[0]
    except Exception:out=''
    return out
def sesion(B,tok):
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def llama(m,url,body=None):
        rq=urllib.request.Request(B+url,method=m,data=(json.dumps(body).encode() if body is not None else None),headers=HDR)
        try:
            r=op.open(rq);d=r.read();return r.status,(json.loads(d) if d else {})
        except urllib.error.HTTPError as e:
            return e.code,{}
    llama('POST','/api/configurar',{'token':tok,'name':'Administrador','u':'admin','clave':'clave-segura-1'});return llama
def escenario(n,port,col,ren=None,plan_nombre='Doctorado',marca=True):
    data='/tmp/nbdata_dc%d'%n;os.system('rm -rf %s && mkdir -p %s'%(data,data));B='http://127.0.0.1:%d'%port
    p=arranca(port,data,'tk-dc');adm=sesion(B,'tk-dc')
    adm('PUT','/api/doc/config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':plan_nombre,'n':16,'col':col,'ins':0,'rein':0,'tit':30000}],'extra':{'costo':300,'min':8},'cons':{'costo':50},'ren':ren or {}})
    para(p);time.sleep(1)
    db=sqlite3.connect(data+'/lafragua.db')
    if marca:db.execute("delete from docs where coleccion='meta' and id='migracion-doctorado-costos-1000-2000'")
    db.commit();db.close()
    p=arranca(port,data,'tk-dc');time.sleep(1.5);log=para(p);time.sleep(0.5)
    db=sqlite3.connect(data+'/lafragua.db')
    pl=json.loads(db.execute("select data from docs where coleccion='config' and id='plans'").fetchone()[0])
    m=db.execute("select count(*) from docs where coleccion='meta' and id='migracion-doctorado-costos-1000-2000'").fetchone()[0];aud=[r[0] for r in db.execute("select accion from auditoria").fetchall()];db.close()
    return pl,m,aud,log,data
col=lambda pl,k='Doctorado':[p for p in pl['plans'] if p['k']==k][0]['col']
# A: costo sin definir -> col 2000, inscripción y reinscripción 1000
pl,m,aud,log,data=escenario(1,3440,0)
d0=[p for p in pl['plans'] if p['k']=='Doctorado'][0]
ok('A_doctorado_sin_costo_queda_en_2000_y_1000',col(pl)==2000 and d0['ins']==1000 and d0['rein']==1000 and m==1)
ok('A_no_toca_los_demas_planes',col(pl,'Pedagogía')==1300 and [p for p in pl['plans'] if p['k']=='Pedagogía'][0]['ins']==800)
ok('A_queda_en_la_auditoria',any('costos del Doctorado' in a for a in aud) and 'costos del Doctorado' in log)
db=sqlite3.connect(data+'/lafragua.db');P=pl;[p for p in P['plans'] if p['k']=='Doctorado'][0]['col']=0;db.execute("update docs set data=? where coleccion='config' and id='plans'",(json.dumps(P),));db.commit();db.close()
p=arranca(3440,data,'tk-dc');time.sleep(1);para(p);db=sqlite3.connect(data+'/lafragua.db');p2=json.loads(db.execute("select data from docs where coleccion='config' and id='plans'").fetchone()[0]);db.close()
ok('A_no_se_repite_en_el_siguiente_arranque',col(p2)==0 and [p for p in p2['plans'] if p['k']=='Doctorado'][0]['ins']==1000)
# B: ya tenía un costo propio: la colegiatura no se toca
pl,m,aud,log,_=escenario(2,3441,2500)
ok('B_con_costo_propio_no_se_toca',col(pl)==2500 and m==1)
# B2: la colegiatura provisional de 1800 de la migración anterior pasa a 2000
pl,m,aud,log,_=escenario(5,3444,1800)
ok('B2_provisional_1800_pasa_a_2000',col(pl)==2000)
# C: plan renombrado
pl,m,aud,log,_=escenario(3,3442,0,ren={'Doctorado':'Doctorado en Educación'},plan_nombre='Doctorado en Educación')
ok('C_respeta_el_nombre_cambiado',col(pl,'Doctorado en Educación')==2000)
# D: aviso de privacidad vigente
port=3443;data='/tmp/nbdata_dc4';os.system('rm -rf %s && mkdir -p %s'%(data,data));B='http://127.0.0.1:%d'%port
p=arranca(port,data,'tk-dc');adm=sesion(B,'tk-dc')
t0=urllib.request.urlopen(B+'/privacidad').read().decode()
ok('aviso_sin_configurar_ya_trae_domicilio_y_correo','Guadalupe Victoria No. 3, Tejupilco de Hidalgo, Estado de México' in t0 and 'universidadlafragua@gmail.com' in t0)
s,j=adm('PUT','/api/seguridad/privacidad',{'entidad':'Universidad Lafragua','domicilio':'Calle Falsa 123, Tejupilco, Estado de México','correo':'privacidad@lafragua.mx','telefono':'722 000 0000','responsable':'Control escolar','extra':'<script>alert(1)</script>','aceptacion':False})
ok('guarda_los_datos_del_aviso',s==200)
t=urllib.request.urlopen(B+'/privacidad').read().decode()
for n,x in [('cita_la_ley_vigente','20 de marzo de 2025'),('nombra_la_autoridad','Secretaría Anticorrupción y Buen Gobierno'),('finalidades_necesarias','Finalidades necesarias'),('finalidades_voluntarias','Finalidades voluntarias'),('transferencias','Con quién compartimos tus datos'),('menores_de_edad','menores de edad'),('datos_sensibles','Datos personales sensibles'),('derechos_arco','Tus derechos (ARCO)'),('plazo_20_dias','20 días hábiles'),('plazo_15_dias','15 días hábiles'),('revocacion','revocar tu consentimiento'),('conservacion','Cuánto tiempo conservamos'),('cambios_al_aviso','cambios a este aviso'),('datos_de_contacto','Calle Falsa 123'),('correo_arco','privacidad@lafragua.mx'),('menciona_servicio_social','servicio social'),('menciona_biblioteca','Biblioteca'),('menciona_stripe','Stripe')]:ok(n,x in t)
ok('no_muestra_el_borrador_interno','Borrador generado' not in t)
ok('escapa_el_html_extra','<script>alert(1)</script>' not in t and '&lt;script&gt;' in t)
ok('secciones_numeradas_hasta_11','11. Información adicional' in t)
para(p)
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
