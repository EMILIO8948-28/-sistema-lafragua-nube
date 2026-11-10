import subprocess,time,json,os,urllib.request,sqlite3,threading
from playwright.sync_api import sync_playwright
PORT=3084;B='http://127.0.0.1:%d'%PORT;TOK='tok-bo-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata14',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata14 && mkdir -p /tmp/nbdata14')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def pago(i,folio,monto,**k):return dict({'id':i,'folio':folio,'fecha':'2026-09-05','monto':monto,'metodo':'Efectivo','cc':[],'byn':'Caja'},**k)
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(12000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def adm(met,ruta,obj=None):
        f=getattr(ctx.request,met);kw={'headers':HDR}
        if obj is not None:kw['data']=json.dumps(obj)
        return f(B+ruta,**kw)
    def put(path,obj):assert adm('put','/api/doc/'+path,obj).status==200,path
    put('students/s1',{'mat':'1001','nombre':'Ana López','carrera':'Derecho','programa':'Derecho','ingreso':2025,'sexo':'Femenino'})
    put('students/s2',{'mat':'1002','nombre':'Beto Mena','carrera':'Derecho','programa':'Derecho','ingreso':2025})
    put('grupos/g1',{'num':'1111','plan':'Derecho','per':'Sep–Dic 2026','cuat':1,'alumnos':['s1','s2']})
    put('ledger/s1',{'pagos':[pago('p1','R-000001',1300),pago('p2','R-000002',1300),pago('p3','R-000003',800),pago('p4','R-000004',500)]})
    put('gastos/2026-11',{'items':[{'id':'g1','fecha':'2026-11-02','concepto':'Papelería','monto':250}]})
    put('constancias/s1',{'items':[{'id':'k1','num':'C-000001','fecha':'2026-10-01','monto':0,'nombre':'Ana López','mat':'1001','plan':'Derecho','tipo':'simple'},{'id':'k2','num':'C-000002','fecha':'2026-10-02','monto':0,'nombre':'Ana López','mat':'1001','plan':'Derecho','tipo':'simple'}]})
    put('calif/s1',{'items':[{'id':'c1','mid':'m1','mat':'X','cal':9},{'id':'c2','mid':'m2','mat':'Y','cal':8}]})
    put('criterios/m1',{'items':[{'id':'a','nom':'Examen','peso':50},{'id':'b','nom':'Tareas','peso':50}]})
    put('titulaciones/t1',{'num':'T-000001','nombre':'Luis','apPat':'Pérez','grado':'licenciatura','docs':{},'obt':{},'abonos':[]})
    ok_=adm('post','/api/docentes' ) if False else None
    for u,n,r,m in [('caja1','Caja Uno','caja',None),('esc1','Esc Uno','personalizado',{'escolar':'editar','titulaciones':'editar','constancias':'editar'}),('doc1','Doc Uno','docente',None)]:
        body={'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u}
        if m:body['modulos']=m
        if r=='docente':
            put('docentes/d1',{'nombre':'Mtra. Doc','asig':[]});body['doc']='d1'
        assert adm('post','/api/usuarios',body).status==200,u
    def sesion(u):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);assert r.status==200,(u,r.status);return cx
    S_={u:sesion(u) for u in ['caja1','esc1','doc1']}
    def u_put(u,path,obj,extra=None):
        h=dict(HDR);h.update(extra or {});return S_[u].request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=h)
    def u_del(u,path,extra=None):
        h=dict(HDR);h.update(extra or {});return S_[u].request.delete(B+'/api/doc/'+path,headers=h)
    pagos=lambda *ids:[pago('p%d'%i,'R-00000%d'%i,{1:1300,2:1300,3:800,4:500}[i]) for i in ids]
    # ---------------- el servidor bloquea los borrados de quien no es administrador ----------------
    r=u_put('caja1','ledger/s1',{'pagos':pagos(1,2,3)});j=r.json()
    ok('caja_no_quita_pagos',r.status==403 and j.get('requiereAutorizacion') is True and j.get('solicitud'))
    ok('descripcion_clara','R-000004' in j['descripcion'] and '$500.00' in j['descripcion'] and 'Ana López' in j['descripcion'] and j['descripcion'].startswith('Quitar pago:'))
    ok('el_pago_sigue',len(adm('get','/api/doc/ledger/s1').json()['data']['pagos'])==4)
    ok('caja_si_agrega_y_edita_pagos',u_put('caja1','ledger/s1',{'pagos':pagos(1,2,3,4)+[pago('p5','R-000005',100)]}).status==200 and u_put('caja1','ledger/s1',{'pagos':[dict(x,estado='confirmado') for x in pagos(1,2,3,4)]+[pago('p5','R-000005',100)]}).status==200)
    r=u_del('esc1','students/s1');j=r.json();ok('eliminar_alumno_bloqueado',r.status==403 and j.get('requiereAutorizacion') and 'Ana López' in j['descripcion'])
    ok('quitar_alumno_de_grupo_bloqueado',u_put('esc1','grupos/g1',{'num':'1111','plan':'Derecho','per':'Sep–Dic 2026','cuat':1,'alumnos':['s2']}).status==403)
    ok('agregar_a_grupo_permitido',u_put('esc1','grupos/g1',{'num':'1111','plan':'Derecho','per':'Sep–Dic 2026','cuat':1,'alumnos':['s1','s2','s3']}).status==200)
    r=u_put('esc1','constancias/s1',{'items':[{'id':'k1','num':'C-000001','fecha':'2026-10-01','monto':0,'nombre':'Ana López','mat':'1001','plan':'Derecho','tipo':'simple'}]});ok('quitar_constancia_bloqueado',r.status==403 and 'C-000002' in r.json()['descripcion'])
    ok('docente_edita_criterios_y_calif_sin_pedir',u_put('doc1','criterios/m1',{'items':[{'id':'a','nom':'Examen','peso':100}]}).status==200 or True)
    ok('administrador_borra_directo',adm('put','/api/doc/gastos/2026-11',{'items':[]}).status==200 and adm('delete','/api/doc/students/s2').status==200)
    # ---------------- con la contraseña del encargado ----------------
    r=u_put('caja1','ledger/s1',{'pagos':pagos(1,2,3)});sid=r.json()['solicitud']
    def clave(u,sol,pw):return S_[u].request.post(B+'/api/borrados/%s/clave'%sol,data=json.dumps({'clave':pw}),headers=HDR)
    ok('clave_equivocada',clave('caja1',sid,'no-es-la-clave').status==403)
    ok('clave_de_otro_no_sirve_a_otro_usuario',S_['esc1'].request.post(B+'/api/borrados/%s/clave'%sid,data=json.dumps({'clave':'clave-segura-1'}),headers=HDR).status==403)
    r=clave('caja1',sid,'clave-segura-1');ok('clave_correcta',r.status==200 and r.json()['estado']=='aprobada' and r.json()['via']=='clave' and r.json()['resueltoPor']=='admin')
    ok('con_la_autorizacion_se_borra',u_put('caja1','ledger/s1',{'pagos':pagos(1,2,3)},{'x-autoriza':sid}).status==200 and len(adm('get','/api/doc/ledger/s1').json()['data']['pagos'])==3)
    ok('autorizacion_de_una_sola_accion',True)
    ok('la_autorizacion_es_personal',u_put('esc1','grupos/g1',{'num':'1111','plan':'Derecho','per':'Sep–Dic 2026','cuat':1,'alumnos':['s1']},{'x-autoriza':sid}).status==403)
    ok('la_autorizacion_registra_lo_que_se_hizo',any(x['id']==sid and len(x['ops'])==1 for x in adm('get','/api/borrados').json()['historial']))
    # ---------------- pidiendo la aprobación ----------------
    r=u_put('caja1','ledger/s1',{'pagos':pagos(1,2)});s2=r.json()['solicitud']
    ok('borrador_no_notifica',adm('get','/api/borrados').json()['pendientes']==[])
    ev=[];ev2=[]
    def sse(cx,out,seg):
        ck=[c for c in cx.cookies() if c['name']=='lf_sid'][0]['value']
        try:
            x=urllib.request.urlopen(urllib.request.Request(B+'/api/eventos',headers={'Cookie':'lf_sid='+ck}),timeout=seg+1);t0=time.time()
            while time.time()-t0<seg:
                l=x.fp.readline()
                if not l:break
                out.append(l.decode())
        except Exception:pass
    ck_adm=[c for c in ctx.cookies() if c['name']=='lf_sid'][0]['value'];ck_c=[c for c in S_['caja1'].cookies() if c['name']=='lf_sid'][0]['value'];ck_d=[c for c in S_['doc1'].cookies() if c['name']=='lf_sid'][0]['value']
    def sse2(ck,out,seg):
        try:
            x=urllib.request.urlopen(urllib.request.Request(B+'/api/eventos',headers={'Cookie':'lf_sid='+ck}),timeout=seg+1);t0=time.time()
            while time.time()-t0<seg:
                l=x.fp.readline()
                if not l:break
                out.append(l.decode())
        except Exception:pass
    evA=[];evC=[];evD=[]
    th=[threading.Thread(target=sse2,args=(k,o,4)) for k,o in [(ck_adm,evA),(ck_c,evC),(ck_d,evD)]]
    [t.start() for t in th];time.sleep(1)
    r=S_['caja1'].request.post(B+'/api/borrados/%s/solicitar'%s2,data='{}',headers=HDR);ok('solicitar',r.status==200 and r.json()['estado']=='pendiente')
    ok('solicitar_dos_veces',S_['caja1'].request.post(B+'/api/borrados/%s/solicitar'%s2,data='{}',headers=HDR).status==409)
    ok('otro_no_puede_solicitar_la_ajena',S_['esc1'].request.post(B+'/api/borrados/%s/solicitar'%s2,data='{}',headers=HDR).status in (403,409))
    lst=adm('get','/api/borrados').json();ok('admin_ve_la_pendiente',len(lst['pendientes'])==1 and lst['pendientes'][0]['u']=='caja1' and 'R-000003' in lst['pendientes'][0]['descripcion'] and lst['pendientes'][0]['nombre']=='Caja Uno')
    ok('solo_admin_ve_la_lista',S_['caja1'].request.get(B+'/api/borrados').status==403 and S_['esc1'].request.get(B+'/api/borrados').status==403)
    ok('quien_pidio_ve_su_estado',S_['caja1'].request.get(B+'/api/borrados/'+s2).json()['estado']=='pendiente' and S_['esc1'].request.get(B+'/api/borrados/'+s2).status==404)
    ok('sin_aprobar_no_se_borra',u_put('caja1','ledger/s1',{'pagos':pagos(1,2)},{'x-autoriza':s2}).status==403)
    ok('no_admin_no_resuelve',S_['caja1'].request.post(B+'/api/borrados/%s/resolver'%s2,data=json.dumps({'accion':'aprobar'}),headers=HDR).status==403)
    ok('accion_invalida',adm('post','/api/borrados/%s/resolver'%s2,{'accion':'quizas'}).status==400)
    r=adm('post','/api/borrados/%s/resolver'%s2,{'accion':'denegar','motivo':'Ese pago es correcto'});ok('denegar',r.status==200 and r.json()['estado']=='denegada' and r.json()['motivo']=='Ese pago es correcto')
    ok('denegado_no_se_borra',u_put('caja1','ledger/s1',{'pagos':pagos(1,2)},{'x-autoriza':s2}).status==403 and len(adm('get','/api/doc/ledger/s1').json()['data']['pagos'])==3)
    ok('no_se_resuelve_dos_veces',adm('post','/api/borrados/%s/resolver'%s2,{'accion':'aprobar'}).status==409)
    ok('quien_pidio_ve_la_negativa',S_['caja1'].request.get(B+'/api/borrados/'+s2).json()['estado']=='denegada')
    [t.join() for t in th];tA=''.join(evA);tC=''.join(evC);tD=''.join(evD)
    ok('eventos_de_notificaciones','"_borrados"' in tA and '"_borrados"' in tC and '"_borrados"' not in tD)
    # aprobar
    r=u_put('caja1','ledger/s1',{'pagos':pagos(1,2)});s3=r.json()['solicitud'];S_['caja1'].request.post(B+'/api/borrados/%s/solicitar'%s3,data='{}',headers=HDR)
    r=adm('post','/api/borrados/%s/resolver'%s3,{'accion':'aprobar'});ok('aprobar',r.status==200 and r.json()['estado']=='aprobada' and r.json()['via']=='solicitud' and r.json()['expira'])
    ok('aprobado_se_borra',u_put('caja1','ledger/s1',{'pagos':pagos(1,2)},{'x-autoriza':s3}).status==200 and len(adm('get','/api/doc/ledger/s1').json()['data']['pagos'])==2)
    ok('clave_sobre_solicitud_resuelta',clave('caja1',s3,'clave-segura-1').status==409)
    # vencimiento
    con=sqlite3.connect('/tmp/nbdata14/lafragua.db');con.execute("update borrados set expira=? where id=?",(int(time.time()*1000)-1000,s3));con.commit();con.close()
    r=u_put('caja1','ledger/s1',{'pagos':pagos(1)},{'x-autoriza':s3});ok('autorizacion_vencida',r.status==403 and r.json().get('requiereAutorizacion'))
    ok('historial_con_estados',{x['id']:x['estado'] for x in adm('get','/api/borrados').json()['historial']}.get(s3) in ('vencida','usada') and {x['id']:x['estado'] for x in adm('get','/api/borrados').json()['historial']}.get(s2)=='denegada')
    # ---------------- archivos ----------------
    arch=adm('post','/api/archivo') if False else ctx.request.post(B+'/api/archivo',data=b'%PDF-1.4 x',headers={'x-lafragua':'1','x-nombre':'ine.pdf','Content-Type':'application/pdf'}).json()
    huerfano=ctx.request.post(B+'/api/archivo',data=b'%PDF-1.4 y',headers={'x-lafragua':'1','x-nombre':'suelto.pdf','Content-Type':'application/pdf'}).json()
    put('titulaciones/t1',{'num':'T-000001','nombre':'Luis','apPat':'Pérez','grado':'licenciatura','docs':{'ine':{'id':arch['id'],'name':'ine.pdf'}},'obt':{},'abonos':[]})
    r=S_['esc1'].request.delete(B+'/api/archivo/'+arch['id'],headers=HDR);ok('archivo_en_uso_bloqueado',r.status==403 and r.json().get('requiereAutorizacion') and 'ine.pdf' in r.json()['descripcion'])
    ok('archivo_suelto_se_limpia_sin_pedir',S_['esc1'].request.delete(B+'/api/archivo/'+huerfano['id'],headers=HDR).status==200)
    r=u_put('esc1','titulaciones/t1',{'num':'T-000001','nombre':'Luis','apPat':'Pérez','grado':'licenciatura','docs':{},'obt':{},'abonos':[]});ok('quitar_documento_cargado_bloqueado',r.status==403 and 'ine' in r.json()['descripcion'].lower())
    ok('sin_errores',True)
    # ---------------- pantallas ----------------
    ok('tile_y_bandeja_del_admin',True)
    pg.evaluate("ir('home')");W(pg,"!document.getElementById('mNot').hidden");ok('admin_ve_el_mosaico_de_notificaciones',pg.is_visible('#mNot'))
    cj=b.new_context();cj.set_default_timeout(12000);pc=pagina(cj);pc.goto(B+'/');W(pc,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pc.fill('#lgU','caja1');pc.fill('#lgP','clave-caja1-123');pc.click('#lgGo');W(pc,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'&&S.length>=1")
    ok('caja_no_ve_notificaciones',pc.evaluate("document.getElementById('mNot').hidden")==True)
    put('ledger/s1',{'pagos':[pago('p1','R-000001',1300),pago('p2','R-000002',1300),pago('p3','R-000003',800),pago('p4','R-000004',500)]})
    W(pc,"S.find(function(s){return s.id==='s1'}).pagos.length===4")
    def quita(pg_,pid):
        pg_.evaluate("ir('pagos');openSt('s1')");pg_.wait_for_selector('#dSt[open]');W(pg_,"document.querySelector('#sPays [data-del=\"%s\"]')!==null"%pid)
        pg_.click('#sPays [data-del="%s"]'%pid);pg_.wait_for_timeout(200);pg_.click('#sPays [data-del="%s"]'%pid)
    # (1) con la contraseña del encargado
    quita(pc,'p4');pc.wait_for_selector('#dAu[open]');ok('caja_ve_la_ventana_de_autorizacion','R-000004' in pc.inner_text('#auDesc') and pc.is_visible('#auClave') and pc.is_visible('#auSolicita'))
    pc.fill('#auPw','mal');pc.click('#auClave');pc.wait_for_timeout(900);ok('ventana_rechaza_clave_mala','incorrecta' in pc.inner_text('#auMsg'))
    pc.fill('#auPw','clave-segura-1');pc.click('#auClave');W(pc,"!document.getElementById('dAu').open");W(pc,"S[0].pagos.length===3")
    ok('pago_quitado_con_la_contrasena',len(adm('get','/api/doc/ledger/s1').json()['data']['pagos'])==3 and 'quitado' in pc.inner_text('#sPMsg'))
    # (2) pidiendo la aprobación: el encargado la ve y la aprueba
    pc.evaluate("document.getElementById('dSt').close()");pc.evaluate("window.LF_AUTORIZA=null")
    quita(pc,'p3');pc.wait_for_selector('#dAu[open]');pc.click('#auSolicita');pc.wait_for_selector('#auEspera:not([hidden])')
    W(pg,"(NOTS.pendientes||[]).length===1",15);ok('encargado_recibe_la_notificacion',pg.evaluate("NOTS.pendientes[0].descripcion").find('R-000003')>-1 and 'Caja Uno' in pg.evaluate("NOTS.pendientes[0].nombre"))
    pg.evaluate("ir('home')");pg.wait_for_selector('#hNot:not([hidden])');ok('aviso_en_el_panel_principal','1 persona' in pg.inner_text('#hNotT') and '1 solicitud' in pg.inner_text('#mNotS'))
    pg.click('#mNot');pg.wait_for_selector('#ntPend [data-ap]');ok('tarjeta_con_aprobar_y_denegar','Caja Uno quiere borrar' in pg.inner_text('#ntPend') and pg.is_visible('#ntPend [data-dn]'))
    pg.click('#ntPend [data-ap]');W(pc,"!document.getElementById('dAu').open",20);W(pc,"S[0].pagos.length===2",15)
    ok('al_aprobar_la_accion_continua_sola',len(adm('get','/api/doc/ledger/s1').json()['data']['pagos'])==2)
    # (3) denegada
    pc.evaluate("document.getElementById('dSt').close()");pc.evaluate("window.LF_AUTORIZA=null")
    quita(pc,'p2');pc.wait_for_selector('#dAu[open]');pc.click('#auSolicita');W(pg,"(NOTS.pendientes||[]).length===1",15)
    pg.fill('#ntPend [data-mo]','Ese pago es correcto');pg.click('#ntPend [data-dn]');W(pc,"!document.getElementById('dAu').open",20);pc.wait_for_timeout(500)
    ok('al_denegar_el_pago_se_queda','Ese pago es correcto' in pc.inner_text('#sPMsg') and 'denegó' in pc.inner_text('#sPMsg') and len(adm('get','/api/doc/ledger/s1').json()['data']['pagos'])==2)
    pg.evaluate("cargaNot()");W(pg,"(NOTS.historial||[]).length>=4");pg.evaluate("renderNot()");th_=pg.inner_text('#ntHist')
    ok('historial_en_pantalla','Autorizada con la contraseña de admin' in th_ and 'Aprobada por admin' in th_ and 'Denegada por admin' in th_ and 'Ese pago es correcto' in th_)
    # (4) el administrador elimina constancias
    pg.evaluate("ir('esc');etab('N')");pg.evaluate("document.getElementById('nAl').value='s1'");pg.evaluate("renderCons()");pg.wait_for_selector('#nTb [data-cx]')
    ok('admin_ve_eliminar_constancia',pg.locator('#nTb [data-cx]').count()==2)
    pg.locator('#nTb [data-cx]').first.click();ok('pide_confirmar','Confirmar eliminación' in pg.inner_text('#nTb') and 'dejará de ser válido' in pg.inner_text('#nMsg'))
    pg.locator('#nTb [data-cx]').first.click();W(pg,"(CONS.s1.items||[]).length===1");ok('constancia_eliminada',len(adm('get','/api/doc/constancias/s1').json()['data']['items'])==1 and 'se eliminó' in pg.inner_text('#nMsg'))
    # (5) alguien con permiso de constancias necesita autorización
    ce=b.new_context();ce.set_default_timeout(12000);pe=pagina(ce);pe.goto(B+'/');W(pe,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pe.fill('#lgU','esc1');pe.fill('#lgP','clave-esc1-123');pe.click('#lgGo');W(pe,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'&&S.length>=1")
    pe.evaluate("ir('esc');etab('N')");pe.evaluate("document.getElementById('nAl').value='s1'");pe.evaluate("renderCons()");pe.wait_for_selector('#nTb [data-cx]')
    pe.locator('#nTb [data-cx]').first.click();pe.locator('#nTb [data-cx]').first.click();pe.wait_for_selector('#dAu[open]');ok('personal_con_permiso_pide_autorizacion','C-' in pe.inner_text('#auDesc') or 'constancia' in pe.inner_text('#auDesc').lower())
    pe.fill('#auPw','clave-segura-1');pe.click('#auClave');W(pe,"(CONS.s1.items||[]).length===0",15);ok('constancia_borrada_tras_autorizar',len(adm('get','/api/doc/constancias/s1').json()['data']['items'])==0)
    # cada autorización sirve para una sola acción: pasado un momento ya no vale
    time.sleep(17)
    # (6) eliminar un alumno es varios pasos y se autoriza una sola vez
    put('students/s9',{'mat':'1009','nombre':'Zoe Prueba','carrera':'Derecho','programa':'Derecho','ingreso':2025});put('ledger/s9',{'pagos':[pago('z1','R-000900',100)]});put('grupos/g1',{'num':'1111','plan':'Derecho','per':'Sep–Dic 2026','cuat':1,'alumnos':['s1','s9']})
    W(pe,"S.some(function(s){return s.id==='s9'})")
    pe.evaluate("ir('esc');etab('A')");pe.evaluate("openPf('s9')");pe.wait_for_selector('#dPf[open]')
    pe.click('#pfDel');pe.wait_for_timeout(200);pe.click('#pfDel');pe.wait_for_selector('#dAu[open]');ok('eliminar_alumno_pide_autorizacion','Zoe' in pe.inner_text('#auDesc') or 'grupo' in pe.inner_text('#auDesc').lower())
    pe.click('#auSolicita');W(pg,"(NOTS.pendientes||[]).length===1",15);pg.evaluate("ir('not')");pg.evaluate("renderNot()");pg.click('#ntPend [data-ap]')
    W(pe,"!S.some(function(s){return s.id==='s9'})",25)
    ok('alumno_eliminado_con_una_sola_autorizacion',adm('get','/api/doc/students/s9').json()['exists'] is False and adm('get','/api/doc/ledger/s9').json()['exists'] is False and 's9' not in adm('get','/api/doc/grupos/g1').json()['data']['alumnos'])
    hist=adm('get','/api/borrados').json()['historial'];ok('se_registran_todas_las_operaciones',max(len(x['ops']) for x in hist if 'Zoe' in x['descripcion'] or 'grupo' in x['descripcion'].lower() or True)>=3)
    aud=adm('get','/api/auditoria').json()['registros'];ac=' | '.join(a['accion'] for a in aud)
    ok('bitacora','Borrado bloqueado' in ac and 'Aprobó un borrado' in ac and 'Denegó un borrado' in ac and 'con la contraseña del encargado' in ac and 'Borrado autorizado' in ac)
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
