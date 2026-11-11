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
def escenario(n,port,dist,plan_n,ren=None,plan_nombre='Doctorado'):
    data='/tmp/nbdata_mg%d'%n;os.system('rm -rf %s && mkdir -p %s'%(data,data));B='http://127.0.0.1:%d'%port
    p=arranca(port,data,'tk-mg');adm=sesion(B,'tk-mg')
    adm('PUT','/api/doc/config/plans',{'plans':[{'k':plan_nombre,'n':plan_n,'col':0,'ins':0,'rein':0,'tit':30000}],'extra':{'costo':300,'min':8},'cons':{'costo':50},'ren':ren or {}})
    adm('PUT','/api/doc/catalogo/doctorado',{'plan':'Doctorado','items':[{'id':'doc-'+c.lower(),'cuat':dist[c],'clave':c,'nom':NOMS[c],'cred':None,'hrs':None,'ct':1,'pdf':0} for c in sorted(dist)]})
    para(p);time.sleep(1)
    db=sqlite3.connect(data+'/lafragua.db');db.execute("delete from docs where coleccion='meta' and id='migracion-doctorado-4cuat'");db.commit();db.close()
    p=arranca(port,data,'tk-mg');time.sleep(1.5);log=para(p);time.sleep(0.5)
    db=sqlite3.connect(data+'/lafragua.db')
    cat=json.loads(db.execute("select data from docs where coleccion='catalogo' and id='doctorado'").fetchone()[0]);pl=json.loads(db.execute("select data from docs where coleccion='config' and id='plans'").fetchone()[0])
    marca=db.execute("select count(*) from docs where coleccion='meta' and id='migracion-doctorado-4cuat'").fetchone()[0];aud=[r[0] for r in db.execute("select accion from auditoria").fetchall()];db.close()
    return cat,pl,marca,aud,log,data,port
dist=lambda cat:[sum(1 for i in cat['items'] if i['cuat']==c) for c in range(1,6)]
# A: plataforma que ya tenía el doctorado en 5 cuatrimestres
cat,pl,marca,aud,log,data,port=escenario(1,3430,ANT,20)
ok('A_pasa_a_4_cuatrimestres_de_4_seminarios',dist(cat)==[4,4,4,4,0] and [i['cuat'] for i in sorted(cat['items'],key=lambda x:x['clave'])]==[(k-1)//4+1 for k in range(1,17)])
ok('A_la_duracion_pasa_de_20_a_16_colegiaturas',pl['plans'][0]['n']==16)
ok('A_se_conserva_el_resto_del_plan',all(i['nom']==NOMS[i['clave']] and i['ct']==1 for i in cat['items']) and pl['plans'][0]['tit']==30000)
ok('A_queda_en_la_auditoria_y_en_la_bitacora',any('Migración: Doctorado en Educación redistribuido en 4 cuatrimestres' in a for a in aud) and 'redistribuido en 4 cuatrimestres y la duración pasó de 20 a 16 colegiaturas' in log and marca==1)
# una segunda vez no vuelve a tocar nada (aunque el administrador lo cambie)
db=sqlite3.connect(data+'/lafragua.db');cat['items'][0]['cuat']=2;db.execute("update docs set data=? where coleccion='catalogo' and id='doctorado'",(json.dumps(cat),));db.commit();db.close()
p=arranca(port,data,'tk-mg');time.sleep(1);para(p);db=sqlite3.connect(data+'/lafragua.db');c2=json.loads(db.execute("select data from docs where coleccion='catalogo' and id='doctorado'").fetchone()[0]);db.close()
ok('A_no_se_repite_en_el_siguiente_arranque',c2['items'][0]['cuat']==2)
# B: el administrador ya había movido una materia: no se toca
d2=dict(ANT);d2['ED16']=3
cat,pl,marca,aud,log,_,_=escenario(2,3431,d2,20)
ok('B_si_ya_estaba_personalizado_no_se_toca_nada',dist(cat)==[4,3,4,3,2] and pl['plans'][0]['n']==20 and marca==1 and not any('Migración' in a for a in aud))
# C: duración distinta de 20: se redistribuye pero se respeta la duración
cat,pl,marca,aud,log,_,_=escenario(3,3432,ANT,12)
ok('C_con_duracion_propia_se_redistribuye_pero_no_se_cambia_la_duracion',dist(cat)==[4,4,4,4,0] and pl['plans'][0]['n']==12 and 'la duración' not in log.split('Migración:')[1].split('.')[0] if 'Migración:' in log else False)
# D: el plan se llama distinto
cat,pl,marca,aud,log,_,_=escenario(4,3433,ANT,20,ren={'Doctorado':'Doctorado en Educación'},plan_nombre='Doctorado en Educación')
ok('D_si_el_plan_fue_renombrado_tambien_ajusta_su_duracion',dist(cat)==[4,4,4,4,0] and pl['plans'][0]['n']==16)
# E: instalación nueva sin catálogo: solo marca
data='/tmp/nbdata_mg5';os.system('rm -rf %s && mkdir -p %s'%(data,data));p=arranca(3434,data,'tk-mg');time.sleep(1);log=para(p);db=sqlite3.connect(data+'/lafragua.db');m=db.execute("select count(*) from docs where coleccion='meta' and id='migracion-doctorado-4cuat'").fetchone()[0];db.close()
ok('E_sin_catalogo_no_hace_nada_y_queda_marcada',m==1 and 'Migración' not in log)
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
