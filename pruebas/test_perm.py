import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3076;B='http://127.0.0.1:%d'%PORT;TOK='tok-perm-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata6',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata6 && mkdir -p /tmp/nbdata6')
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
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
        pg.on("response",lambda r:malos.append((r.status,r.url.replace(B,''),pg.url)) if r.status>=400 and '/api/' in r.url else None);return pg
    pg=pagina(ctx)
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    # ---- panel del administrador ----
    ok('admin_ve_todos_los_mosaicos',all(pg.is_visible('#'+i) for i in ['mPag','mIns','mEsc','mAcu','mA2','mTit','mNom','mNa','mVer','mUsr']) and pg.is_hidden('#mDoc'))
    pg.click('#mUsr');pg.wait_for_selector('#vUsr:not([hidden])');ok('abre_usuarios','Usuarios y permisos' in pg.inner_text('#ttl') and 'admin' in pg.inner_text('#usTb'))
    ok('admin_perfil_todos','Todos los módulos' in pg.inner_text('#usTb'))
    # docente para vincular
    pg.evaluate("""async()=>{$("dcNom").value="Mtra. Laura Díaz";await $("dcAdd").onclick();document.getElementById('dDx').close()}""");W(pg,"Object.keys(DOC).length===1");did=pg.evaluate("Object.keys(DOC)[0]")
    pg.evaluate("ir('usr')")
    def nuevo(nom,usu,pw,perfil,mods=None,doc=None):
        pg.click('#usNew');pg.wait_for_selector('#dUsr[open]');pg.fill('#usNom',nom);pg.fill('#usUsu',usu);pg.fill('#usPw',pw);pg.select_option('#usRol',perfil)
        if perfil=='personalizado':pg.evaluate("document.querySelectorAll('#usMods select').forEach(function(s){s.value='none'})")
        if mods is not None:
            for k,v in mods.items():pg.select_option('#usMods select[data-m="%s"]'%k,v)
        if doc:pg.select_option('#usDoc',doc)
        pg.click('#usOk')
    # validaciones
    pg.click('#usNew');pg.wait_for_selector('#dUsr[open]');pg.click('#usOk');ok('v_nombre','nombre' in pg.inner_text('#usMsg'))
    pg.fill('#usNom','X');pg.fill('#usUsu','Ro sa!');pg.fill('#usPw','12345678');pg.click('#usOk');ok('v_usuario','solo puede llevar' in pg.inner_text('#usMsg'))
    pg.fill('#usUsu','rosa');pg.fill('#usPw','123');pg.click('#usOk');ok('v_clave_corta','8 caracteres' in pg.inner_text('#usMsg'))
    pg.fill('#usPw','12345678');pg.select_option('#usRol','personalizado');pg.evaluate("document.querySelectorAll('#usMods select').forEach(function(s){s.value='none'})");pg.click('#usOk');ok('v_sin_modulos','al menos un módulo' in pg.inner_text('#usMsg'))
    pg.select_option('#usRol','docente');ok('docente_pide_docente',pg.is_visible('#usDoc'));pg.click('#usOk');ok('v_docente','docente' in pg.inner_text('#usMsg').lower())
    pg.select_option('#usRol','caja');ok('plantilla_caja',pg.input_value('#usMods select[data-m="pagos"]')=='editar' and pg.input_value('#usMods select[data-m="escolar"]')=='ver' and pg.input_value('#usMods select[data-m="nomina_adm"]')=='none' and pg.input_value('#usMods select[data-m="constancias"]')=='editar')
    pg.select_option('#usMods select[data-m="titulaciones"]','ver');ok('cambiar_modulo_pasa_a_personalizado',pg.input_value('#usRol')=='personalizado')
    pg.select_option('#usRol','admin');ok('admin_bloquea_modulos',pg.is_disabled('#usMods select[data-m="pagos"]'));pg.click('#usCan')
    # ---- crear usuarios ----
    nuevo('Rosa Caja','rosa','clave-rosa-1','caja')
    pg.wait_for_function("document.getElementById('usMsg2').textContent.includes('guardado')") if False else W(pg,"USERS.some(u=>u.u==='rosa')")
    nuevo('Nina Nómina','nina','clave-nina-1','personalizado',{'nomina_adm':'editar'})
    W(pg,"USERS.some(u=>u.u==='nina')")
    nuevo('Vera Consulta','vera','clave-vera-1','consulta')
    W(pg,"USERS.some(u=>u.u==='vera')")
    nuevo('Tito Mixto','tito','clave-tito-1','personalizado',{'titulaciones':'editar','pagos':'ver','expedientes':'editar'})
    W(pg,"USERS.some(u=>u.u==='tito')")
    nuevo('Dora Docente','dora','clave-dora-1','docente',None,did)
    W(pg,"USERS.some(u=>u.u==='dora')")
    nuevo('Cuco Cuentas','cuco','clave-cuco-1','personalizado',{'estado':'ver','pagos':'ver'})
    W(pg,"USERS.some(u=>u.u==='cuco')")
    ok('usuarios_creados',pg.evaluate("USERS.length")==7)
    t=pg.inner_text('#usTb');ok('lista_con_modulos','Control de pagos (editar)' in t and 'Nómina administrativa (editar)' in t and 'Estado de cuenta final (ver)' in t and 'Docente: Mtra. Laura Díaz' in t and 'Personalizado' in t)
    # ---- editar: conservar contraseña y cambiar módulos ----
    pg.click('#usTb tr:has-text("rosa") [data-ed]');pg.wait_for_selector('#dUsr[open]');ok('editar_carga_datos',pg.input_value('#usNom')=='Rosa Caja' and pg.input_value('#usMods select[data-m="corte"]')=='editar' and pg.is_visible('#usUsu') and pg.evaluate("document.getElementById('usUsu').readOnly"))
    pg.select_option('#usMods select[data-m="acuerdos"]','none');pg.click('#usOk');W(pg,"!USERS.find(u=>u.u==='rosa').modulos.acuerdos")
    ok('editar_guarda_modulos',pg.evaluate("USERS.find(u=>u.u==='rosa').rol")=='personalizado')
    # ---- servidor: sesiones y matriz ----
    def sesion(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status,r.text());return cx
    ses={u:sesion(u,c) for u,c in [('rosa','clave-rosa-1'),('nina','clave-nina-1'),('vera','clave-vera-1'),('tito','clave-tito-1'),('dora','clave-dora-1'),('cuco','clave-cuco-1')]}
    ses['admin']=ctx
    def leer(u,col):return ses[u].request.get(B+'/api/col/'+col).json()['docs']
    def doc(u,path):return ses[u].request.get(B+'/api/doc/'+path).json()
    def poner(u,path,obj=None):return ses[u].request.put(B+'/api/doc/'+path,data=json.dumps(obj or {'x':1}),headers=HDR).status
    # datos de prueba (administrador)
    for path,obj in [('students/s1',{'mat':'1','nombre':'Ana','programa':'Derecho','ingreso':2025,'tel':'726','dom':'Calle 1','beca':{'monto':1}}),('ledger/s1',{'pagos':[]}),('gastos/2026-11',{'items':[]}),('nomina/2026-11',{'x':1}),('nomina_admin/2026-11',{'x':1}),('empleados/e1',{'nombre':'Emp'}),('titulaciones/t1',{'num':'T-1'}),('acuerdo286/q1',{'num':'B'}),('docentes_docs/'+did,{'docs':{}}),('config/nomina',{'base':120,'esp':150}),('config/plans',{'plans':[]}),('calif/s1',{'items':[]}),('constancias/s1',{'items':[]}),('acuerdos/a1',{'x':1}),('docentes/'+did,{'nombre':'Mtra. Laura Díaz','asig':[]}),('materias/m1',{'nom':'x'})]:
        assert poner('admin',path,obj)==200,path
    ok('rosa_matriz',leer('rosa','students')[0]['data'].get('tel')=='726' and poner('rosa','ledger/s1')==200 and poner('rosa','gastos/2026-11')==200 and poner('rosa','constancias/s1')==200 and poner('rosa','students/s1')==403 and poner('rosa','acuerdos/a1')==403 and leer('rosa','nomina_admin')==[] and leer('rosa','titulaciones')==[])
    ok('rosa_lee_acuerdos_no',leer('rosa','acuerdos')==[])   # se le quitó el módulo de acuerdos
    ok('nina_solo_nomina_administrativa',poner('nina','empleados/e2',{'nombre':'Otro'})==200 and poner('nina','nomina_admin/2026-12')==200 and poner('nina','meta/folioNA',{'n':1})==200 and len(leer('nina','empleados'))==2 and leer('nina','students')==[] and leer('nina','ledger')==[] and poner('nina','students/s1')==403 and poner('nina','ledger/s1')==403 and poner('nina','nomina/2026-11')==403 and leer('nina','nomina')==[])
    ok('nina_sin_gastos_ni_config_nomina',leer('nina','gastos')==[] and doc('nina','config/nomina')['exists'] is False and doc('nina','config/plans')['exists'] is False and doc('nina','config/app')['exists'] in (True,False))
    ok('vera_solo_lectura',leer('vera','students')[0]['data'].get('tel')=='726' and len(leer('vera','ledger'))==1 and poner('vera','ledger/s1')==403 and poner('vera','students/s1')==403 and leer('vera','gastos')==[] and doc('vera','config/plans')['exists'] is True)
    ok('tito_titulaciones_y_expedientes',poner('tito','titulaciones/t2',{'num':'T-2'})==200 and poner('tito','meta/folioT',{'n':1})==200 and poner('tito','docentes_docs/'+did,{'docs':{}})==200 and poner('tito','ledger/s1')==403 and len(leer('tito','ledger'))==1)   # pagos: solo ver
    up=ses['admin'].request.post(B+'/api/archivo',data=b'%PDF-1.4 x',headers={'x-lafragua':'1','x-nombre':'ine.pdf','x-privado':'1','Content-Type':'application/pdf'}).json()
    pu=ses['admin'].request.post(B+'/api/archivo',data=b'%PDF-1.4 y',headers={'x-lafragua':'1','x-nombre':'comun.pdf','Content-Type':'application/pdf'}).json()
    ok('privados_segun_permiso',ses['tito'].request.get(B+'/_blob/'+up['id']).status==200 and ses['rosa'].request.get(B+'/_blob/'+up['id']).status==403 and ses['vera'].request.get(B+'/_blob/'+up['id']).status==403 and ses['rosa'].request.get(B+'/_blob/'+pu['id']).status==200)
    ok('subida_de_archivos_segun_modulo',ses['tito'].request.post(B+'/api/archivo',data=b'%PDF',headers={'x-lafragua':'1','x-nombre':'a.pdf','x-privado':'1','Content-Type':'application/pdf'}).status==200 and ses['tito'].request.post(B+'/api/archivo',data=b'%PDF',headers={'x-lafragua':'1','x-nombre':'a.pdf','Content-Type':'application/pdf'}).status==200 and ses['rosa'].request.post(B+'/api/archivo',data=b'%PDF',headers={'x-lafragua':'1','x-nombre':'a.pdf','Content-Type':'application/pdf'}).status==403 and ses['nina'].request.post(B+'/api/archivo',data=b'%PDF',headers={'x-lafragua':'1','x-nombre':'a.pdf','x-privado':'1','Content-Type':'application/pdf'}).status==403)
    d=leer('dora','students')[0]['data'];ok('dora_alumnos_reducidos','tel' not in d and 'dom' not in d and leer('dora','ledger')==[] and poner('dora','calif/s1')==200 and poner('dora','ledger/s1')==403 and leer('dora','nomina')==[] and doc('dora','config/plans')['exists'] is False)
    ok('cuco_estado',len(leer('cuco','gastos'))==1 and len(leer('cuco','nomina'))==1 and len(leer('cuco','nomina_admin'))==2 and len(leer('cuco','titulaciones'))==2 and doc('cuco','config/nomina')['exists'] is True and poner('cuco','gastos/2026-11')==403 and poner('cuco','ledger/s1')==403 and leer('cuco','empleados')==[] and leer('cuco','docentes_docs')==[])
    ok('nadie_gestiona_usuarios',all(ses[u].request.get(B+'/api/usuarios').status==403 for u in ['rosa','nina','vera','tito','dora','cuco']) and all(ses[u].request.get(B+'/api/respaldo/descargar').status==403 for u in ['rosa','tito','cuco']) and all(ses[u].request.get(B+'/api/auditoria').status==403 for u in ['rosa','cuco']))
    ok('autoriza_admin_solo_con_pagos_editar',ses['rosa'].request.post(B+'/api/autoriza-admin',data=json.dumps({'clave':'clave-segura-1'}),headers=HDR).status==200 and ses['vera'].request.post(B+'/api/autoriza-admin',data=json.dumps({'clave':'clave-segura-1'}),headers=HDR).status==403 and ses['nina'].request.post(B+'/api/autoriza-admin',data=json.dumps({'clave':'clave-segura-1'}),headers=HDR).status==403)
    yo=ses['rosa'].request.get(B+'/api/yo').json()['usuario'];ok('yo_incluye_permisos',yo['rol']=='personalizado' and yo['perm']['pagos']=='editar' and 'acuerdos' not in yo['perm'])
    ok('api_rechaza_modulos_invalidos',ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'xx1','name':'X','rol':'personalizado','modulos':{'inventado':'editar'},'clave':'clave-xx-123'}),headers=HDR).status==400 and ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'xx1','name':'X','rol':'personalizado','modulos':{'pagos':'todo'},'clave':'clave-xx-123'}),headers=HDR).status==400)
    # conservar módulos al restablecer una clave sin enviar módulos
    r=ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'nina','name':'Nina Nómina','rol':'personalizado','clave':'clave-nina-2'}),headers=HDR);ok('clave_conserva_modulos',r.status==200 and [u for u in r.json()['usuarios'] if u['u']=='nina'][0]['perm']=={'nomina_adm':'editar'})
    ok('clave_nueva_cierra_sesion',ses['nina'].request.get(B+'/api/col/empleados').status==401)
    ses['nina']=sesion('nina','clave-nina-2')
    # ---- pantallas de cada usuario ----
    def entra(u,c):
        cx=b.new_context();cx.set_default_timeout(9000);pg2=pagina(cx);pg2.goto(B+'/');W(pg2,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pg2.fill('#lgU',u);pg2.fill('#lgP',c);pg2.click('#lgGo');W(pg2,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'");pg2.wait_for_timeout(500);return pg2
    def tiles(pg2):return sorted(pg2.evaluate("['mPag','mIns','mEsc','mAcu','mA2','mTit','mNom','mNa','mVer','mUsr','mDoc'].filter(function(i){return !document.getElementById(i).hidden})"))
    pr=entra('rosa','clave-rosa-1');ok('rosa_mosaicos',tiles(pr)==['mEsc','mPag','mVer'])
    pr.click('#mPag');W(pr,"MOD==='pagos'");ok('rosa_pagos_rol_caja',pr.evaluate("ROL")=='caja' and pr.is_visible('#tGa') and pr.is_hidden('#tEf'))
    pr.click('#tGa');W(pr,"TAB==='ga'");ok('rosa_corte',pr.evaluate("ROL")=='caja')
    pr.evaluate("ir('esc')");W(pr,"MOD==='esc'");ok('rosa_escolar_solo_ver_y_constancias',pr.evaluate("ETAB")!=None and pr.is_visible('#eTabs [data-et=N]') and pr.is_hidden('#eTabs [data-et=R]'))
    pr.click('#eTabs [data-et=N]');W(pr,"ETAB==='N'");ok('rosa_constancias_rol_caja',pr.evaluate("ROL")=='caja')
    pr.click('#eTabs [data-et=D]');W(pr,"ETAB==='D'");ok('rosa_docentes_sin_expediente_ni_accesos',pr.evaluate("ROL")=='consulta' and pr.is_hidden('#dcAccAll') and 'Expediente' not in pr.inner_html('#dcTb') and 'Crear acceso' not in pr.inner_html('#dcTb'))
    pr.evaluate("ir('usr')");ok('rosa_no_entra_a_usuarios',pr.evaluate("MOD")=='home')
    pr.evaluate("ir('nom')");ok('rosa_no_entra_a_nomina',pr.evaluate("MOD")=='home')
    pn=entra('nina','clave-nina-2');ok('nina_mosaicos',tiles(pn)==['mNa'])
    pn.click('#mNa');W(pn,"MOD==='na'");ok('nina_nomina_rol_admin',pn.evaluate("ROL")=='admin' and pn.evaluate("BASEROL")=='consulta')
    pn.click('#naT2');pn.evaluate("abreEmp(null)");pn.fill('#emNom','Pepe Admin');pn.fill('#emSal','9000');pn.click('#emSave');W(pn,"Object.values(EMP).some(e=>e.nombre==='Pepe Admin')");pn.click('#emCan')
    ok('nina_crea_empleado',pn.evaluate("Object.keys(EMP).length")==3)
    pn.click('#naT1');pn.evaluate("document.getElementById('naM').value='11';document.getElementById('naPer').value='M';renderNa()")
    pn.locator('#naTb tr:has-text("Pepe") [data-pg]').click();pn.wait_for_selector('#dNa[open]');pn.click('#naPOk');W(pn,"Object.values(NAD).some(d=>Object.values(d.pagos||{}).some(p=>p.emp==='Pepe Admin'))")
    ok('nina_paga_nomina',pn.evaluate("Object.values(Object.values(NAD).find(d=>d.pagos&&Object.keys(d.pagos).length).pagos)[0].folio").startswith('NA-'))
    ok('nina_no_ve_alumnos',pn.evaluate("S.length")==0)
    pn.evaluate("ir('pagos')");ok('nina_no_entra_a_pagos',pn.evaluate("MOD")=='home')
    pv=entra('vera','clave-vera-1');ok('vera_mosaicos',tiles(pv)==['mEsc','mPag'])
    pv.click('#mPag');W(pv,"MOD==='pagos'");ok('vera_solo_consulta',pv.evaluate("ROL")=='consulta' and pv.is_hidden('#tGa'))
    ok('vera_ve_alumno',pv.evaluate("S.length")==1)
    pt=entra('tito','clave-tito-1');ok('tito_mosaicos',tiles(pt)==['mPag','mTit'])
    pt.click('#mTit');W(pt,"MOD==='tit'");ok('tito_titulaciones_rol_admin',pt.evaluate("ROL")=='admin')
    pt.evaluate("ir('esc')");ok('tito_sin_escolar',pt.evaluate("MOD")=='home')
    pd=entra('dora','clave-dora-1');W(pd,"MOD==='doc'");ok('dora_directo_a_sus_asignaturas',tiles(pd)==['mDoc'] and pd.evaluate("ROL")=='docente')
    pc=entra('cuco','clave-cuco-1');ok('cuco_mosaicos',tiles(pc)==['mPag'])
    pc.click('#mPag');W(pc,"MOD==='pagos'");ok('cuco_pestanas',pc.is_visible('#tEf') and pc.is_visible('#tAl') and pc.is_hidden('#tGa'))
    pc.click('#tEf');W(pc,"TAB==='ef'");pc.wait_for_selector('#efRes b');ok('cuco_estado_de_cuenta',pc.evaluate("ROL")=='admin' and 'Resultado' in pc.inner_text('#efRes'))
    # ---- el administrador cambia los módulos de Rosa y ella los ve al recargar ----
    pg.evaluate("ir('usr')");pg.click('#usTb tr:has-text("rosa") [data-ed]');pg.wait_for_selector('#dUsr[open]');pg.select_option('#usMods select[data-m="pagos"]','none');pg.select_option('#usMods select[data-m="corte"]','none');pg.select_option('#usMods select[data-m="ver"]','none');pg.select_option('#usMods select[data-m="nomina_doc"]','ver');pg.click('#usOk');W(pg,"USERS.find(u=>u.u==='rosa').perm&&USERS.find(u=>u.u==='rosa').perm.nomina_doc==='ver'")
    pr.reload();W(pr,"typeof APP!=='undefined'&&APP!==null&&typeof S!=='undefined'&&!document.body.classList.contains('locked')");pr.wait_for_timeout(500);ok('rosa_nuevos_mosaicos',tiles(pr)==['mEsc','mNom'])
    # ---- baja de usuarios ----
    pg.evaluate("ir('usr')");pg.click('#usTb tr:has-text("vera") [data-dl]');ok('baja_pide_confirmar','Confirmar' in pg.locator('#usTb tr:has-text("vera") [data-dl]').inner_text())
    pg.locator('#usTb tr:has-text("vera") [data-dl]').click();W(pg,"!USERS.some(u=>u.u==='vera')");ok('baja_elimina',ses['vera'].request.get(B+'/api/col/students').status==401)
    pg.locator('#usTb tr:has-text("Administrador") [data-dl]').click();ok('no_se_elimina_a_si_mismo','propio usuario' in pg.inner_text('#usMsg2'))
    # ---- accesos de docentes en la nube (clave generada por el sistema) ----
    pg.evaluate("ir('esc');etab('D')");pg.evaluate("""async()=>{$("dcNom").value="Mtro. Beto Ruiz";await $("dcAdd").onclick();document.getElementById('dDx').close()}""");W(pg,"Object.keys(DOC).length===2")
    pg.evaluate("document.getElementById('dcAccAll').onclick()");W(pg,"ACCNEW.length>=1")
    cred=pg.evaluate("ACCNEW[0]");ok('accesos_docentes_nube',cred['doc']=='Mtro. Beto Ruiz' and len(cred['p'])>=8 and 'Beto' in pg.inner_text('#dcAccTb'))
    lg=b.new_context().request.post(B+'/api/login',data=json.dumps({'u':cred['u'],'clave':cred['p']}),headers=HDR);ok('acceso_generado_funciona',lg.status==200 and lg.json()['usuario']['rol']=='docente')
    pg.click('#dcTb tr:has-text("Beto") [data-ac]');W(pg,"ACCNEW.length>=2");ok('restablecer_clave_docente',pg.evaluate("ACCNEW[1].u")==cred['u'])
    # ---- bitácora ----
    aud=ctx.request.get(B+'/api/auditoria').json()['registros'];acc=' | '.join(a['accion']+' '+(a['detalle'] or '') for a in aud)
    ok('auditoria_usuarios','Usuario creado' in acc and 'nomina_adm=editar' in acc and 'Usuario modificado' in acc and 'Usuario eliminado' in acc)
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    inesp=[m for m in malos if not (m[0]==403 and ('/api/usuarios' in m[1] or '/api/autoriza' in m[1] or '/_blob' in m[1])) and m[0]!=401]
    ok('sin_errores_de_red_inesperados',len(inesp)==0)
    if inesp:print('RED:',[(a,b_) for a,b_,c in inesp][:8])
    b.close()
p.terminate();p.wait()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
