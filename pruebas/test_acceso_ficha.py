import subprocess,time,json,os,urllib.request,sqlite3,zipfile,io,stat
from playwright.sync_api import sync_playwright
PORT=3080;B='http://127.0.0.1:%d'%PORT;TOK='tok-ac-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata10',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata10 && mkdir -p /tmp/nbdata10')
def arranca():
    p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(60):
        time.sleep(0.25)
        try:urllib.request.urlopen(B+'/salud',timeout=1);return p
        except Exception:pass
    raise SystemExit('no arrancó')
srv=arranca()
R={};errs=[]
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
MOCK="""()=>{window.__txt=[];window.__sav=[];window.__clip=[];
 function PDF(){}
 ['setDrawColor','setLineWidth','setTextColor','setFont','line','addImage','setFontSize','setLineDashPattern','setFillColor','rect','addPage'].forEach(function(f){PDF.prototype[f]=function(){return this}});
 PDF.prototype.splitTextToSize=function(t){return [String(t)]};PDF.prototype.text=function(t){window.__txt.push(String(Array.isArray(t)?t[0]:t));return this};PDF.prototype.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};
 Object.defineProperty(navigator,'clipboard',{value:{writeText:function(t){window.__clip.push(t);return Promise.resolve()}},configurable:true});0}"""
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200
    for sid,nom,mat in [('s1','Ana López','1001'),('s2','Beto Mena','1002')]:put('students/'+sid,{'mat':mat,'nombre':nom,'carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    W(pg,"S.length===2");pg.evaluate(MOCK)
    pg.evaluate("ir('pagos')")
    # ---- sin acceso: crear ----
    pg.evaluate("openPf('s1')");pg.wait_for_selector('#dPf[open]');W(pg,"document.getElementById('pfAcc').innerText.includes('Acceso a la plataforma')")
    ok('sin_acceso_ofrece_crear','todavía no tiene usuario' in pg.inner_text('#pfAcc') and pg.is_visible('#pfAcc [data-ac=reset]'))
    pg.click('#pfAcc [data-ac=reset]');W(pg,"ACCPF.p&&document.getElementById('pfAcc').innerText.includes('1001')")
    pw1=pg.evaluate("ACCPF.p");ok('crea_y_muestra_usuario_y_contrasena',pg.evaluate("usuarioAlumno('s1').u")=='1001' and len(pw1)==9 and pw1 in pg.inner_text('#pfAcc') and '1001' in pg.inner_text('#pfAcc') and 'Aún no entra' in pg.inner_text('#pfAcc'))
    # ---- cifrado en el servidor ----
    con=sqlite3.connect('/tmp/nbdata10/lafragua.db');tmp=con.execute("select temporal from usuarios where u='1001'").fetchone()[0];con.close()
    ok('guardada_cifrada',tmp and pw1 not in tmp and len(tmp)>30)
    ok('llave_solo_en_disco',os.path.exists('/tmp/nbdata10/secreto.key') and (os.stat('/tmp/nbdata10/secreto.key').st_mode&0o077)==0)
    # ---- reabrir: oculta hasta pedirla ----
    pg.evaluate("document.getElementById('dPf').close()");pg.evaluate("openPf('s1')");W(pg,"document.getElementById('pfAcc').innerText.includes('1001')")
    t=pg.inner_text('#pfAcc');ok('reabre_oculta','••••••••' in t and pw1 not in t and pg.is_visible('#pfAcc [data-ac=ver]'))
    pg.click('#pfAcc [data-ac=ver]');W(pg,"ACCPF.p");ok('mostrar_la_revela',pg.evaluate("ACCPF.p")==pw1 and pw1 in pg.inner_text('#pfAcc'))
    aud=ctx.request.get(B+'/api/auditoria').json()['registros'];ok('consulta_queda_en_bitacora',any(a['accion'].startswith('Consultó la contraseña inicial') for a in aud))
    pg.click('#pfAcc [data-ac=copiar]');pg.wait_for_timeout(150);ok('copiar',pg.evaluate("window.__clip")==['Usuario: 1001\nContraseña: '+pw1])
    pg.click('#pfAcc [data-ac=pdf]');pg.wait_for_timeout(150);tx=json.dumps(pg.evaluate("window.__txt"),ensure_ascii=False)
    ok('hoja_de_acceso_pdf',pg.evaluate("window.__sav")==['hoja-de-acceso-1001.pdf'] and pw1 in tx and '1001' in tx and 'Ana López' in tx and 'Acceso al portal del alumno' in tx)
    # ---- permisos del servidor ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja Uno','rol':'caja','clave':'clave-caja-1'}),headers=HDR)
    cj=b.new_context();cj.request.post(B+'/api/login',data=json.dumps({'u':'caja1','clave':'clave-caja-1'}),headers=HDR)
    al=b.new_context();ok('el_alumno_entra_con_la_inicial',al.request.post(B+'/api/login',data=json.dumps({'u':'1001','clave':pw1}),headers=HDR).status==200)
    ok('solo_admin_consulta',cj.request.get(B+'/api/usuarios/alumno/s1').status==403 and al.request.get(B+'/api/usuarios/alumno/s1').status==403 and b.new_context().request.get(B+'/api/usuarios/alumno/s1').status==401)
    ok('admin_ve_estado',ctx.request.get(B+'/api/usuarios/alumno/s1').json()=={'tiene':True,'u':'1001','forzar':True,'temporal':pw1} and ctx.request.get(B+'/api/usuarios/alumno/s2').json()=={'tiene':False})
    ok('lista_marca_temporal_sin_mostrarla',[u for u in ctx.request.get(B+'/api/usuarios').json()['usuarios'] if u['u']=='1001'][0]['temporal'] is True and pw1 not in ctx.request.get(B+'/api/usuarios').text())
    # ---- el alumno cambia su contraseña: la inicial desaparece ----
    ok('alumno_cambia',al.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':pw1,'nueva':'mi-clave-propia-77'}),headers=HDR).status==200)
    ok('inicial_borrada',ctx.request.get(B+'/api/usuarios/alumno/s1').json()=={'tiene':True,'u':'1001','forzar':False,'temporal':None})
    con=sqlite3.connect('/tmp/nbdata10/lafragua.db');ok('columna_vacia',con.execute("select temporal from usuarios where u='1001'").fetchone()[0] is None);con.close()
    pg.evaluate("window.cargaUsuariosSrv()");pg.evaluate("document.getElementById('dPf').close()");pg.evaluate("ACCPF={sid:null,p:null}");pg.evaluate("openPf('s1')");W(pg,"document.getElementById('pfAcc').innerText.includes('1001')")
    t=pg.inner_text('#pfAcc');ok('ficha_ya_cambio','Ya cambió' in t and 'no se puede ver' in t and pg.locator('#pfAcc [data-ac=ver]').count()==0 and '••••' not in t)
    # ---- restablecer ----
    pg.click('#pfAcc [data-ac=reset]');W(pg,"ACCPF.p");pw2=pg.evaluate("ACCPF.p")
    ok('restablecer_da_nueva',pw2!=pw1 and pw2 in pg.inner_text('#pfAcc') and 'Aún no entra' in pg.inner_text('#pfAcc'))
    ok('la_propia_ya_no_sirve',b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'1001','clave':'mi-clave-propia-77'}),headers=HDR).status==401 and al.request.get(B+'/api/col/students').status==401)
    ok('la_nueva_sirve_y_es_inicial',b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'1001','clave':pw2}),headers=HDR).json()['usuario']['forzar'] is True)
    # ---- respaldo: sin la llave ----
    z=zipfile.ZipFile(io.BytesIO(ctx.request.get(B+'/api/respaldo/descargar').body()));ok('respaldo_sin_llave','secreto.key' not in ' '.join(z.namelist()))
    # ---- reinicio: la llave persiste ----
    srv.terminate();srv.wait();srv=arranca()
    ctx2=b.new_context();ctx2.request.post(B+'/api/login',data=json.dumps({'u':'admin','clave':'clave-segura-1'}),headers=HDR)
    ok('tras_reiniciar_se_puede_ver',ctx2.request.get(B+'/api/usuarios/alumno/s1').json()['temporal']==pw2)
    # ---- Caja no ve la sección ----
    cx=b.new_context();cx.set_default_timeout(9000);pc=pagina(cx);pc.goto(B+'/');W(pc,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pc.fill('#lgU','caja1');pc.fill('#lgP','clave-caja-1');pc.click('#lgGo');W(pc,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'&&S.length===2")
    pc.evaluate("ir('pagos')");pc.evaluate("openPf('s1')");pc.wait_for_timeout(500);ok('caja_no_ve_el_acceso',pc.evaluate("document.getElementById('pfAcc').innerHTML")=='' )
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    b.close()
srv.terminate()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
