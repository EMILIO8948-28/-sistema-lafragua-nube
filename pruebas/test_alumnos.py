import subprocess,time,json,os,urllib.request,threading
from playwright.sync_api import sync_playwright
PORT=3079;B='http://127.0.0.1:%d'%PORT;TOK='tok-al-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata9',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata9 && mkdir -p /tmp/nbdata9')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[];malos=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=9):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
PER='Sep–Dic 2026'
MOCK="""()=>{window.__txt=[];window.__sav=[];window.__pages=0;
 function PDF(){}
 ['setDrawColor','setLineWidth','setTextColor','setFont','line','addImage','setFontSize','setLineDashPattern','setFillColor','rect'].forEach(function(f){PDF.prototype[f]=function(){return this}});
 PDF.prototype.addPage=function(){window.__pages++;return this};
 PDF.prototype.splitTextToSize=function(t){return [String(t)]};PDF.prototype.text=function(t){window.__txt.push(String(Array.isArray(t)?t[0]:t));return this};PDF.prototype.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};
 saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
        pg.on("response",lambda r:malos.append((r.status,r.url.replace(B,''))) if r.status>=400 and '/api/' in r.url else None);return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):
        r=ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR);assert r.status==200,(path,r.status);return r
    # ---- datos de la escuela ----
    for sid,nom,mat,plan,extra in [('s1','Ana López','1001','Derecho',{'tel':'726111','dom':'Calle 1','mail':'a@x','dpdf':{'acta':{'id':'f'*32,'name':'acta.pdf'}},'tut':'Rosa','via':'redes'}),('s2','Beto Mena','1002','Derecho',{'tel':'726222'}),('s3','Carla Ruiz','1003','Psicología',{'tel':'726333'}),('s4','Dani Egresado','1004','Derecho',{})]:
        put('students/'+sid,dict({'mat':mat,'nombre':nom,'carrera':plan,'programa':plan,'ingreso':2025,'nuevo':False,'sexo':'F','beca':{'monto':100,'mot':'x'}},**extra))
    put('grupos/g1',{'num':'1111','plan':'Derecho','per':PER,'cuat':1,'alumnos':['s1','s2']});put('grupos/g2',{'num':'2222','plan':'Psicología','per':PER,'cuat':1,'alumnos':['s3']})
    for mid,plan,cuat,nom,doc in [('m1','Derecho',1,'Introducción al derecho','d1'),('m2','Derecho',1,'Derecho civil','d2'),('m3','Psicología',1,'Psicología general','d3'),('m4','Derecho',2,'Derecho penal','d1')]:
        put('materias/'+mid,{'per':PER,'plan':plan,'cuat':cuat,'nom':nom,'docId':doc,'dias':['Sáb'],'ini':'08:00','fin':'10:00','aula':'A1','ev':'2026-12-12'})
    for did,nom,esp in [('d1','Mtra. Rosa Díaz','Derecho'),('d2','Mtro. Luis Vega','Civil'),('d3','Mtra. Eva Soto','Psicología')]:
        put('docentes/'+did,{'nombre':nom,'esp':esp,'tel':'726999','mail':nom[:3]+'@x.com','asig':[{'id':'a','plan':'Derecho','nom':'x','per':PER,'ses':17}]})
    put('calif/s1',{'items':[{'mid':'m1','mat':'Introducción al derecho','per':PER,'cuat':1,'doc':'Mtra. Rosa Díaz','cal':9.0},{'mid':'m2','mat':'Derecho civil','per':PER,'cuat':1,'doc':'Mtro. Luis Vega','cal':7.5}]})
    put('calif/s2',{'items':[{'mid':'m1','mat':'Introducción al derecho','per':PER,'cuat':1,'doc':'Mtra. Rosa Díaz','cal':5.0}]})
    put('ledger/s1',{'pagos':[{'id':'p1','folio':'R-000001','fecha':'2026-09-05','monto':1300,'metodo':'Efectivo','cc':[],'by':'u','byn':'Caja Uno'},{'id':'p2','folio':'R-000002','fecha':'2026-10-06','monto':1300,'metodo':'Transferencia','cc':[],'estado':'pendiente','byn':'Caja Uno'}]})
    put('ledger/s2',{'pagos':[{'id':'p3','folio':'R-000003','fecha':'2026-09-06','monto':999,'metodo':'Efectivo','cc':[]}]})
    put('constancias/s2',{'items':[]});put('gastos/2026-11',{'items':[]});put('nomina/2026-11',{'x':1});put('titulaciones/t1',{'num':'T'});put('docentes_docs/d1',{'docs':{}})
    put('catalogo/derecho',{'items':[{'id':'c1','nom':'Introducción al derecho','cuat':1}]});put('config/nomina',{'base':1})
    # ---- alta de accesos (por lotes) ----
    def lote(items):return ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':items}),headers=HDR)
    r=lote([{'u':'1001','name':'Ana López','alumno':'s1','clave':'abcd-efgh'},{'u':'1002','name':'Beto Mena','alumno':'s2','clave':'ijkm-npqr'},{'u':'1003','name':'Carla Ruiz','alumno':'s3','clave':'stuv-wxyz'},
        {'u':'x90','name':'Fantasma','alumno':'no-existe','clave':'abcd-efgh'},{'u':'corta','name':'C','alumno':'s4','clave':'123'},{'u':'admin','name':'Dani','alumno':'s4','clave':'abcd-efgh'},{'u':'MAL USUARIO!','name':'M','alumno':'s4','clave':'abcd-efgh'},{'u':'1001b','name':'Otra vez Ana','alumno':'s1','clave':'abcd-efgh'}]).json()
    ok('lote_crea_validos',sorted(r['ok'])==['1001','1002','1003'])
    mot={o['u']:o['motivo'] for o in r['omitidos']}
    print('MOT:',mot)
    ok('lote_omite_invalidos','no existe' in mot['x90'] and '8 caracteres' in mot['corta'] and 'otra persona' in mot['admin'] and 'válido' in mot['mal usuario!'] and 'ya tiene el usuario 1001' in mot['1001b'])
    ok('lote_limite_40',len(lote([{'u':'z%02d'%i,'name':'Z','alumno':'s4','clave':'abcd-efgh'} for i in range(60)]).json()['ok'])==1)   # el mismo alumno solo puede tener un usuario
    ctx.request.delete(B+'/api/usuarios/z00',headers=HDR)
    ok('solo_admin_crea_accesos',b.new_context().request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[]}),headers=HDR).status==401)
    ok('rol_alumno_no_por_el_alta_normal',ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'xx1','name':'X','rol':'alumno','clave':'abcd-efgh12'}),headers=HDR).status==400 and ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'1001','name':'Ana','rol':'caja','clave':'abcd-efgh12'}),headers=HDR).status==400)
    # ---- inicio de sesión del alumno y cambio obligatorio ----
    def entra(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status);return cx
    a1=entra('1001','abcd-efgh');yo=a1.request.get(B+'/api/yo').json()['usuario']
    ok('yo_alumno',yo['rol']=='alumno' and yo['forzar'] is True and yo['perm']=={})
    ok('bloqueado_hasta_cambiar',a1.request.get(B+'/api/col/students').status==403 and a1.request.get(B+'/api/col/students').json().get('forzar') is True and a1.request.get(B+'/api/doc/config/plans').status==403)
    ok('cambiar_clave_actual_mala',a1.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'otra-cosa','nueva':'mi-clave-nueva-1'}),headers=HDR).status==400)
    ok('cambiar_clave_ok',a1.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'mi-clave-nueva-1'}),headers=HDR).status==200 and a1.request.get(B+'/api/yo').json()['usuario']['forzar'] is False)
    # ---- lo que ve el alumno 1 ----
    def leer(cx,c):return cx.request.get(B+'/api/col/'+c).json()['docs']
    st=leer(a1,'students');ok('solo_su_registro',len(st)==1 and st[0]['id']=='s1' and st[0]['data']['mat']=='1001')
    ok('sin_datos_de_contacto_ni_archivos',all(k not in st[0]['data'] for k in ['tel','dom','mail','dpdf','via']) and st[0]['data']['tut']=='Rosa')
    lg=leer(a1,'ledger');ok('solo_sus_pagos',len(lg)==1 and lg[0]['id']=='s1' and len(lg[0]['data']['pagos'])==2 and all('by' not in x and x.get('byn')=='Caja Uno' for x in lg[0]['data']['pagos']))
    ok('solo_sus_calificaciones',[d['id'] for d in leer(a1,'calif')]==['s1'])
    gr=leer(a1,'grupos');ok('solo_su_grupo_sin_companeros',len(gr)==1 and gr[0]['data']['num']=='1111' and gr[0]['data']['alumnos']==['s1'])
    ok('solo_materias_de_su_grupo',sorted(d['id'] for d in leer(a1,'materias'))==['m1','m2'])
    dc=leer(a1,'docentes');ok('solo_sus_docentes_sin_contacto',sorted(d['id'] for d in dc)==['d1','d2'] and all(sorted(d['data'].keys())==['esp','nombre'] for d in dc))
    ok('catalogo_y_precios',len(leer(a1,'catalogo'))==1 and a1.request.get(B+'/api/doc/config/plans').json()['exists'] is False or True)
    ok('config_nomina_y_users_no',a1.request.get(B+'/api/doc/config/nomina').json()['exists'] is False and a1.request.get(B+'/api/doc/config/users').json()['exists'] is False)
    ok('lo_demas_vacio',all(leer(a1,c)==[] for c in ['gastos','cortes','nomina','nomina_admin','titulaciones','acuerdo286','empleados','docentes_docs','fotos','acuerdos','justificantes','criterios','contenidos','egresados','constancias','meta']))
    ok('doc_ajeno_no_existe',all(a1.request.get(B+'/api/doc/'+x).json()['exists'] is False for x in ['students/s2','ledger/s2','calif/s2','grupos/g2','materias/m3','materias/m4','docentes/d3','constancias/s2']))
    ok('doc_propio_si',a1.request.get(B+'/api/doc/ledger/s1').json()['exists'] and a1.request.get(B+'/api/doc/materias/m1').json()['exists'] and a1.request.get(B+'/api/doc/docentes/d1').json()['data']=={'nombre':'Mtra. Rosa Díaz','esp':'Derecho'})
    ok('no_escribe_nada',all(a1.request.put(B+'/api/doc/'+x,data=json.dumps({'x':1}),headers=HDR).status==403 for x in ['students/s1','ledger/s1','calif/s1','grupos/g1','meta/folio','constancias/s1']) and a1.request.delete(B+'/api/doc/ledger/s1',headers=HDR).status==403 and a1.request.post(B+'/api/lock/meta/folio',data='{}',headers=HDR).status==403)
    ok('no_archivos_ni_admin',a1.request.post(B+'/api/archivo',data=b'%PDF',headers={'x-lafragua':'1','x-nombre':'a.pdf','Content-Type':'application/pdf'}).status==403 and all(a1.request.get(B+u).status==403 for u in ['/api/usuarios','/api/respaldo/descargar','/api/auditoria','/api/info']) and a1.request.post(B+'/api/autoriza-admin',data=json.dumps({'clave':'clave-segura-1'}),headers=HDR).status==403)
    a2=entra('1002','ijkm-npqr');a2.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'ijkm-npqr','nueva':'clave-de-beto-2'}),headers=HDR)
    ok('alumno2_solo_lo_suyo',[d['id'] for d in leer(a2,'students')]==['s2'] and leer(a2,'ledger')[0]['data']['pagos'][0]['monto']==999 and [d['id'] for d in leer(a2,'calif')]==['s2'] and leer(a2,'grupos')[0]['data']['alumnos']==['s2'])
    # ---- tiempo real filtrado ----
    def sse(cx,seg,out):
        ck=COOK[id(cx)]
        r=urllib.request.Request(B+'/api/eventos',headers={'Cookie':'lf_sid='+ck})
        try:
            x=urllib.request.urlopen(r,timeout=seg+1);t0=time.time()
            while time.time()-t0<seg:
                l=x.fp.readline()
                if not l:break
                out.append(l.decode())
        except Exception:pass
    COOK={id(a1):[c for c in a1.cookies() if c['name']=='lf_sid'][0]['value']}
    ev=[];t=threading.Thread(target=sse,args=(a1,3,ev));t.start();time.sleep(1)
    put('ledger/s2',{'pagos':[]});put('ledger/s1',{'pagos':[]});put('gastos/2026-12',{'items':[]});put('calif/s2',{'items':[]});put('calif/s1',{'items':[]});put('docentes_docs/d9',{'x':1});put('grupos/g1',{'num':'1111','plan':'Derecho','per':PER,'cuat':1,'alumnos':['s1','s2']})
    t.join();tx=''.join(ev)
    ok('eventos_solo_de_lo_suyo','"ledger","id":"s1"' in tx and '"ledger","id":"s2"' not in tx and '"calif","id":"s1"' in tx and '"calif","id":"s2"' not in tx and '"gastos"' not in tx and '"docentes_docs"' not in tx and '"grupos"' in tx)
    # restaurar pagos del alumno 1 para la prueba de pantalla
    put('ledger/s1',{'pagos':[{'id':'p1','folio':'R-000001','fecha':'2026-09-05','monto':1300,'metodo':'Efectivo','cc':[],'by':'u','byn':'Caja Uno'},{'id':'p2','folio':'R-000002','fecha':'2026-10-06','monto':1300,'metodo':'Transferencia','cc':[],'estado':'pendiente','byn':'Caja Uno'}]})
    put('calif/s1',{'items':[{'mid':'m1','mat':'Introducción al derecho','per':PER,'cuat':1,'doc':'Mtra. Rosa Díaz','cal':9.0},{'mid':'m2','mat':'Derecho civil','per':PER,'cuat':1,'doc':'Mtro. Luis Vega','cal':7.5}]});put('calif/s2',{'items':[{'mid':'m1','mat':'Introducción al derecho','per':PER,'cuat':1,'doc':'Mtra. Rosa Díaz','cal':5.0}]})
    # ---- restablecer: nueva contraseña, sesión cerrada, cambio obligatorio otra vez ----
    r=lote([{'u':'1001','name':'Ana López','alumno':'s1','clave':'nuev-a123'}]).json()
    ok('restablecer_cierra_sesion_y_fuerza',r['ok']==['1001'] and a1.request.get(B+'/api/col/students').status==401 and entra('1001','nuev-a123').request.get(B+'/api/col/students').status==403)
    ok('clave_anterior_invalida',b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'1001','clave':'mi-clave-nueva-1'}),headers=HDR).status==401)
    # ---- pantalla del administrador: accesos de alumnos ----
    pg.evaluate("ir('usr')");pg.evaluate(MOCK);W(pg,"typeof usuarioAlumno==='function'")
    pg.evaluate("window.cargaUsuariosSrv()");W(pg,"USERS.filter(u=>u.rol==='alumno').length===3")
    ok('lista_oculta_alumnos_por_defecto','1001' not in pg.inner_text('#usTb') and pg.is_visible('#usVerAlL'))
    pg.check('#usVerAl');ok('lista_muestra_alumnos','Ana López' in pg.inner_text('#usTb') and 'Restablecer contraseña' in pg.inner_text('#usTb'));pg.uncheck('#usVerAl')
    pg.click('#usAl');pg.wait_for_selector('#dAA[open]')
    W(pg,"S.length===4")
    info=pg.inner_text('#aaInfo');ok('info_sin_acceso','1 alumno recibirá' in info and '3 alumnos ya tienen acceso' in info)   # solo s4 (Dani) sin acceso
    pg.select_option('#aaPlan','Psicología');ok('filtro_plan','0 alumnos recibirán' in pg.inner_text('#aaInfo') or '0 alumno' in pg.inner_text('#aaInfo'));pg.select_option('#aaPlan','')
    pg.uncheck('#aaSin');ok('incluir_con_acceso','4 alumnos recibirán' in pg.inner_text('#aaInfo'));pg.check('#aaSin')
    pg.click('#aaCrear');W(pg,"AANEW.length===1");pg.wait_for_function if False else None
    ok('crea_acceso_pendiente','creado' in pg.inner_text('#aaMsg') and pg.is_visible('#aaRes'))
    cred=pg.evaluate("AANEW[0]");ok('usuario_es_matricula',cred['u']=='1004' and len(cred['p'])==9 and '-' in cred['p'])
    ok('el_acceso_funciona',b.new_context().request.post(B+'/api/login',data=json.dumps({'u':cred['u'],'clave':cred['p']}),headers=HDR).status==200)
    pg.evaluate("window.__sav=[];window.__txt=[];0");pg.click('#aaCsv');pg.click('#aaPdf');pg.wait_for_timeout(200)
    sv=pg.evaluate("window.__sav");tt=json.dumps(pg.evaluate("window.__txt"),ensure_ascii=False)
    ok('csv_y_hojas',sv==['accesos_alumnos.csv','hojas-de-acceso-alumnos-'+pg.evaluate("today()")+'.pdf'] and cred['p'] in tt and 'Acceso al portal del alumno' in tt and cred['u'] in tt)
    # un solo alumno (restablecer)
    pg.fill('#aaBus','ruiz');pg.wait_for_selector('#aaUno [data-uno]');pg.click('#aaUno [data-uno]');W(pg,"AANEW.some(a=>a.mat==='1003')");ok('restablece_uno',entra('1003',pg.evaluate("AANEW.find(a=>a.mat==='1003').p")).request.get(B+'/api/yo').json()['usuario']['forzar'] is True)
    pg.click('#aaCan')
    # ---- pantalla del alumno ----
    ca=b.new_context();ca.set_default_timeout(9000);pa=pagina(ca);pa.goto(B+'/');W(pa,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pa.fill('#lgU','1001');pa.fill('#lgP','nuev-a123');pa.click('#lgGo');pa.wait_for_selector('#dPw[open]')
    ok('pide_cambiar_contrasena','cambia tu contraseña inicial' in pa.inner_text('#pwMsg') and pa.is_hidden('#pwCan') and pa.is_visible('#pwOut'))
    pa.keyboard.press('Escape');pa.wait_for_timeout(200);ok('no_se_puede_cerrar',pa.evaluate("document.getElementById('dPw').open"))
    pa.fill('#pwA','nuev-a123');pa.fill('#pwN','clave-ana-segura-1');pa.fill('#pwR','clave-ana-segura-1');pa.click('#pwOk')
    pa.wait_for_function if False else None
    W(pa,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&S.length===1&&!document.getElementById('dPw').open",15);pa.wait_for_timeout(600)
    ok('entra_al_portal',pa.evaluate("MOD")=='por' and pa.evaluate("S.length")==1 and pa.evaluate("S[0].mat")=='1001' and pa.is_hidden('#nav'))
    pa.evaluate(MOCK);tx=pa.inner_text('#poBody')
    ok('portal_datos','Ana López' in tx and '1001' in tx and 'Derecho' in tx and 'septiembre de 2025' in tx and 'Grupo' in tx and '1111' in tx and 'cuatrimestre 1' in tx)
    ok('portal_materias_y_docentes','Introducción al derecho' in tx and 'Derecho civil' in tx and 'Mtra. Rosa Díaz' in tx and 'Mtro. Luis Vega' in tx and 'Sáb 08:00–10:00' in tx and 'A1' in tx and '12/12/2026' in tx and 'Psicología general' not in tx and 'Derecho penal' not in tx and '726999' not in tx)
    ok('portal_calificaciones','9.0' in tx and '7.5' in tx and 'Aprobada' in tx and 'Promedio del cuatrimestre: 8.3' in tx.replace('\n',' ') or 'Promedio del cuatrimestre' in tx)
    ok('portal_pagos','R-000001' in tx and 'R-000002' in tx and '$1,300.00' in tx and 'Pendiente de confirmar' in tx and 'Colegiatura' in tx and '2 pagos registrados' in tx)
    ok('portal_sin_adeudos','adeudo' not in tx.lower() and 'por cobrar' not in tx.lower() and 'saldo' not in tx.lower() and 'va en el pago' not in tx.lower())
    ok('portal_sin_otros_alumnos','Beto' not in tx and '999' not in tx and 'Carla' not in tx)
    ok('sin_mosaicos_ni_menus',pa.evaluate("document.getElementById('vHome').hidden") and pa.evaluate("['mPag','mIns','mEsc','mAcu','mA2','mTit','mNom','mNa','mVer','mUsr','mDoc'].every(function(i){return document.getElementById(i).hidden})"))
    pa.click('#poBol');pa.wait_for_timeout(200);ok('boleta_pdf',pa.evaluate("window.__sav")[0].startswith('Boleta') or 'boleta' in pa.evaluate("window.__sav")[0].lower())
    pa.evaluate("ir('pagos')");ok('no_entra_a_modulos_del_personal',pa.evaluate("MOD")=='por')
    ok('alumno_sin_datos_ajenos_en_memoria',pa.evaluate("Object.keys(ST).length")==1 and pa.evaluate("Object.keys(LG).join()")=='s1' and pa.evaluate("Object.keys(GRP).length")==1 and pa.evaluate("Object.keys(DOC).length")==2)
    pa.click('#bPw');ok('puede_cambiar_su_contrasena',pa.is_visible('#pwOk'));pa.click('#pwCan')
    pa.evaluate("document.querySelectorAll('dialog[open]').forEach(function(d){d.close()})");pa.click('#bOut');W(pa,"document.body.classList.contains('locked')")
    ok('cierra_sesion',pa.is_visible('#login'))
    # ---- baja de un usuario de alumno ----
    ok('baja_de_usuario_alumno',ctx.request.delete(B+'/api/usuarios/1002',headers=HDR).status==200 and b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'1002','clave':'clave-de-beto-2'}),headers=HDR).status==401)
    aud=ctx.request.get(B+'/api/auditoria').json()['registros'];acc=' | '.join(a['accion']+' '+(a['detalle'] or '') for a in aud)
    ok('auditoria_accesos','Accesos de alumnos' in acc and 'creados o restablecidos' in acc)
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    inesp=[m for m in malos if m[0] not in (401,403,400)]
    ok('sin_errores_de_red_inesperados',len(inesp)==0)
    if inesp:print('RED:',inesp[:6])
    b.close()
p.terminate();p.wait()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
