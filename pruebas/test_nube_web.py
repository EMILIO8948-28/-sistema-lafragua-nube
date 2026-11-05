import subprocess,time,json,os,urllib.request,zipfile,io
from playwright.sync_api import sync_playwright
PORT=3072;B='http://127.0.0.1:%d'%PORT;TOK='tok-web-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata2',LF_SETUP_TOKEN=TOK,LF_MODO='nube')
os.system('rm -rf /tmp/nbdata2 && mkdir -p /tmp/nbdata2')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};malos=[];csp=[];errs=[];paginas=[]
def W(pg,js,t=9):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera agotada: '+js[:90])
LAST=['inicio']
def ok(n,c):
    R[n]=bool(c);LAST[0]=n
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(accept_downloads=True);ctx.set_default_timeout(9000)
    def nuevo():
        pg=ctx.new_page();paginas.append(pg)
        pg.add_init_script("document.addEventListener('securitypolicyviolation',function(e){window.__viol=(window.__viol||[]).concat([e.violatedDirective+' '+e.blockedURI])})")
        pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.on("console",lambda m:csp.append(m.text) if "Content Security Policy" in m.text else None)
        pg.on("response",lambda r:malos.append((r.status,r.url.replace(B,''),LAST[0])) if r.status>=400 and '/api/' in r.url else None)
        pg.on("dialog",lambda d:d.accept())
        return pg
    pg=nuevo()
    # 1) primera vez: va a la configuración
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');ok('redirige_a_configurar',True)
    pg.fill('#tk','codigo-malo');pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go')
    W(pg,"document.getElementById('er').textContent.length>0");ok('configurar_token_malo','código' in pg.inner_text('#er'))
    pg.fill('#tk',TOK);pg.fill('#p2','distinta');pg.click('#go');ok('configurar_no_coinciden','no coinciden' in pg.inner_text('#er'))
    pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/');
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null")
    ok('entra_como_admin',pg.evaluate("ROL")=='admin' and pg.evaluate("APP.u")=='admin' and pg.is_hidden('#login'))
    ok('sin_boton_propietario',pg.is_hidden('#lgOwn'))
    ok('sesion_texto','Administrador' in pg.inner_text('#who'))
    # 2) datos
    pg.evaluate("""async()=>{abrirAlumno(null);$("alMat").value="1001";$("alNom").value="Ana Nube";$("alPlan").value="Derecho";$("alIng").value="2026";$("alNue").checked=false;await $("alOk").onclick()}""")
    W(pg,"S.some(s=>s.nombre==='Ana Nube')")
    pg.evaluate("""async()=>{var s=S.find(x=>x.nombre==='Ana Nube');openSt(s.id);$("pMon").value="1300";$("pMet").value="Efectivo";$("pFec").value=today();$("pCon").value="";await $("sAdd").onclick();$("pMon").value="800";$("pMet").value="Transferencia";$("pRef").value="TR-1";await $("sAdd").onclick()}""")
    W(pg,"S.find(s=>s.nombre==='Ana Nube').pagos.length===2")
    ok('folios_y_pendiente',pg.evaluate("S.find(s=>s.nombre==='Ana Nube').pagos.map(g=>g.folio+(g.estado?':'+g.estado:'')).join(',')")=='R-000001,R-000002:pendiente')
    pg.reload();W(pg,"typeof S!=='undefined'&&S.some(s=>s.nombre==='Ana Nube')");ok('persiste_y_sesion_sigue',pg.evaluate("ROL")=='admin')
    # 3) usuarios desde la pantalla
    pg.evaluate("""async()=>{$("dcNom").value="Mtra. Docente";await $("dcAdd").onclick()}""");W(pg,"Object.keys(DOC).length===1");pg.evaluate("document.getElementById('dDx').close()")
    pg.evaluate("ir('pagos')");pg.click('#bUs');pg.wait_for_selector('#vUsr:not([hidden])')
    def usu(n,u,pw,perfil,doc=None):
        pg.click('#usNew');pg.wait_for_selector('#dUsr[open]');pg.fill('#usNom',n);pg.fill('#usUsu',u);pg.fill('#usPw',pw);pg.select_option('#usRol',perfil)
        if doc:pg.select_option('#usDoc',doc)
        pg.click('#usOk');W(pg,"USERS.some(x=>x.u==='%s')"%u)
    usu('Caja Uno','caja1','clave-caja-1','caja');usu('Docente Uno','doc1','clave-doc-1','docente',pg.evaluate("Object.keys(DOC)[0]"))
    W(pg,"USERS.length===3");ok('usuarios_creados',pg.evaluate("USERS.map(u=>u.u+':'+u.rol).sort().join(',')")=='admin:admin,caja1:caja,doc1:docente')
    pg.click('#usNew');pg.fill('#usNom','Corta');pg.fill('#usUsu','corta1');pg.fill('#usPw','123');pg.click('#usOk');ok('clave_corta_avisa','8 caracteres' in pg.inner_text('#usMsg'));pg.click('#usCan')
    # 4) mi contraseña
    pg.click('#bPw');pg.fill('#pwA','mala');pg.fill('#pwN','nueva-admin-77');pg.fill('#pwR','nueva-admin-77');pg.click('#pwOk');W(pg,"document.getElementById('pwMsg').textContent.length>0");ok('pw_actual_mala','no es correcta' in pg.inner_text('#pwMsg'))
    pg.fill('#pwA','clave-segura-1');pg.fill('#pwR','otra');pg.click('#pwOk');ok('pw_no_coincide','no coincide' in pg.inner_text('#pwMsg'))
    pg.fill('#pwR','nueva-admin-77');pg.click('#pwOk');W(pg,"document.getElementById('pwMsg').textContent.includes('cambiada')");ok('pw_cambiada',True);pg.click('#pwCan')
    # 5) cierre de sesión y login como Caja
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(function(d){d.close()})");pg.click('#bOut');W(pg,"document.body.classList.contains('locked')");ok('logout_muestra_login',pg.is_visible('#login'))
    pg.fill('#lgU','caja1');pg.fill('#lgP','mala');pg.click('#lgGo');W(pg,"document.getElementById('lgE').textContent.length>0");ok('login_mala','incorrectos' in pg.inner_text('#lgE'))
    pg.fill('#lgP','clave-caja-1');pg.click('#lgGo');W(pg,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')")
    ok('rol_caja',pg.evaluate("ROL")=='caja' and 'Caja' in pg.inner_text('#who'))
    W(pg,"typeof S!=='undefined'&&S.some(s=>s.nombre==='Ana Nube')")
    antes=len(malos)
    pg.evaluate("""async()=>{var s=S.find(x=>x.nombre==='Ana Nube');openSt(s.id);$("pMon").value="500";$("pMet").value="Efectivo";$("pFec").value=today();$("pCon").value="";await $("sAdd").onclick()}""")
    W(pg,"S.find(s=>s.nombre==='Ana Nube').pagos.length===3");ok('caja_registra_pago',pg.evaluate("S.find(s=>s.nombre==='Ana Nube').pagos[2].folio")=='R-000003')
    # confirmar transferencia como caja
    pg.evaluate("""async()=>{var s=S.find(x=>x.nombre==='Ana Nube'),g=s.pagos[1];openCf(s.id,g.id);$("cfFec").value=today();await $("cfOk").onclick()}""")
    W(pg,"paid(S.find(s=>s.nombre==='Ana Nube'))===2600");ok('caja_confirma_transferencia',True)
    ok('caja_sin_errores_de_permiso',len(malos)==antes)
    # caja quita un pago: el servidor pide la autorización del encargado (contraseña de un administrador)
    pg.evaluate("""var s=S.find(x=>x.nombre==='Ana Nube');window.__pid=s.pagos[2].id;openSt(s.id)""");pg.wait_for_selector('#dSt[open]');pid=pg.evaluate("window.__pid")
    pg.click('#sPays [data-del="%s"]'%pid);pg.wait_for_timeout(200);pg.click('#sPays [data-del="%s"]'%pid);pg.wait_for_selector('#dAu[open]');ok('caja_ve_pedir_clave',pg.is_visible('#auPw'))
    pg.fill('#auPw','clave-equivocada');pg.click('#auClave');W(pg,"document.getElementById('auMsg').textContent.includes('incorrecta')");ok('caja_clave_admin_mala',pg.evaluate("S.find(s=>s.nombre==='Ana Nube').pagos.length")==3)
    pg.fill('#auPw','nueva-admin-77');pg.click('#auClave');W(pg,"S.find(s=>s.nombre==='Ana Nube').pagos.length===2");ok('caja_clave_admin_buena',True)
    ok('caja_sin_acceso_a_usuarios',pg.evaluate("(async()=>{var r=await fetch('/api/usuarios');return r.status})()")==403 and pg.evaluate("document.getElementById('mUsr').hidden"))
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(function(d){d.close()})");pg.click('#bOut');W(pg,"document.body.classList.contains('locked')")
    # 6) docente
    pg.fill('#lgU','doc1');pg.fill('#lgP','clave-doc-1');pg.click('#lgGo');W(pg,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')")
    W(pg,"typeof MOD!=='undefined'&&MOD==='doc'");ok('docente_entra_a_sus_asignaturas',pg.evaluate("ROL")=='docente');W(pg,"S.length>=1")
    ok('docente_datos_limitados',pg.evaluate("S.length")>=1 and pg.evaluate("S.every(s=>!s.tel&&!s.dom)") and pg.evaluate("Object.keys(LG).length")==0)
    pg.evaluate("document.querySelectorAll('dialog[open]').forEach(function(d){d.close()})");pg.click('#bOut');W(pg,"document.body.classList.contains('locked')")
    # 7) administrador con la contraseña nueva: herramientas y respaldos
    pg.fill('#lgU','admin');pg.fill('#lgP','clave-segura-1');pg.click('#lgGo');W(pg,"document.getElementById('lgE').textContent.length>0");ok('clave_anterior_ya_no','incorrectos' in pg.inner_text('#lgE'))
    pg.fill('#lgP','nueva-admin-77');pg.click('#lgGo');W(pg,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')")
    pg.evaluate("ir('pagos')");pg.click('#bBk');pg.wait_for_selector('#dBk[open]')
    with pg.expect_download() as d:pg.click('#bkSrv')
    ok('descarga_respaldo_servidor',d.value.suggested_filename.startswith('respaldo-completo-'))
    z=zipfile.ZipFile(d.value.path());ok('zip_valido',z.testzip() is None and 'lafragua.db' in z.namelist())
    pg.click('#bkCls')
    ph=nuevo();ph.goto(B+'/herramientas.html');W(ph,"document.getElementById('estado').innerText.includes('Base de datos')")
    ok('herramientas_info','students' in ph.inner_text('#estado'))
    W(ph,"document.getElementById('audit').innerText.includes('Inicio de sesión')");ok('herramientas_auditoria','Cambió su contraseña' in ph.inner_text('#audit'))
    if os.path.exists('/tmp/respaldo_prueba.json'):
        ph.set_input_files('#fJson','/tmp/respaldo_prueba.json');W(ph,"!document.getElementById('bRest').disabled");ph.click('#bRest');ph.click('#bRest')
        W(ph,"document.getElementById('mRest').innerText.includes('Listo')||document.getElementById('mRest').innerText.includes('No se pudo')");ok('restauracion_en_nube','Listo' in ph.inner_text('#mRest'))
    # 8) sin sesión: la página de herramientas no da datos
    anon=ctx.browser.new_context().new_page();anon.goto(B+'/herramientas.html');W(anon,"document.getElementById('estado').innerText.includes('Entra al sistema')");ok('herramientas_sin_sesion_no_da_datos',True)
    # el caso sin sesión no pide datos al servidor al cargar la app (no hay errores 401 repetidos)
    viol=[]
    for q_ in paginas:
        try:viol+=q_.evaluate('window.__viol||[]')
        except Exception:pass
    ok('sin_violaciones_csp',len(csp)==0 and len(viol)==0)
    if viol:print('VIOLACIONES:',viol[:5])
    if csp:print('CSP:',csp[:3])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:5])
    b.close()
p.terminate();p.wait()
esperados={(401,'/api/login'),(403,'/api/autoriza-admin'),(403,'/api/usuarios'),(400,'/api/cambiar-clave'),(401,'/api/configurar')}
print('respuestas de error:',sorted(set((c,u.split('?')[0]) for c,u,_ in malos)))
print('detalle:',[m for m in malos if m[0]==401 and 'config/plans' in m[1]])
inesperados=[(c,u) for c,u,_ in malos if (c,u.split('?')[0]) not in esperados and not (c==403 and u.startswith('/api/configurar')) and not (c==403 and (u.startswith('/api/doc/ledger/') or u.startswith('/api/borrados/'))) and not (c==401 and u.startswith('/api/borrados'))]
ok('sin_errores_inesperados',len(inesperados)==0)
if inesperados:print('INESPERADOS:',inesperados[:8])
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
