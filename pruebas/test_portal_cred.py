import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3081;B='http://127.0.0.1:%d'%PORT;TOK='tok-pc-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata11',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata11 && mkdir -p /tmp/nbdata11')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
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
PER='Sep–Dic 2026'
# jsPDF simulado con Proxy: registra los textos y acepta cualquier método
MOCK="""()=>{window.__txt=[];window.__sav=[];window.__pages=0;
 function mk(){var t={};return new Proxy(t,{get:function(o,k){
   if(k==='text')return function(s){window.__txt.push(String(Array.isArray(s)?s[0]:s));return this_};
   if(k==='splitTextToSize')return function(s){return [String(s)]};
   if(k==='getTextWidth')return function(){return 10};
   if(k==='output')return function(){return new ArrayBuffer(8)};
   if(k==='addPage')return function(){window.__pages++;return this_};
   if(k==='internal')return {pageSize:{getWidth:function(){return 215.9},getHeight:function(){return 279}}};
   return function(){return this_}}})}
 var this_=null;
 function PDF(){this_=mk();return this_}
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
PNG='data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA='
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('students/s1',{'mat':'1001','nombre':'Ana López','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False,'sexo':'F','tut':'Rosa López','tutTel':'7261234567','tel':'726111','dom':'Calle 1'})
    put('students/s2',{'mat':'1002','nombre':'Beto Mena','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    put('students/s3',{'mat':'1003','nombre':'Carla Egresada','carrera':'Derecho','programa':'Derecho','ingreso':2022,'nuevo':False})
    put('fotos/s1',{'d':PNG});put('fotos/s2',{'d':PNG});put('egresados/s3',{'fecha':'2026-08-01'})
    put('grupos/g1',{'num':'1111','plan':'Derecho','per':PER,'cuat':1,'alumnos':['s1','s2','s3']})
    put('ledger/s1',{'pagos':[{'id':'p1','folio':'R-000001','fecha':'2026-09-05','monto':1300,'metodo':'Efectivo','cc':[],'by':'u','byn':'Caja Uno'},{'id':'p2','folio':'R-000002','fecha':'2026-10-06','monto':1300,'metodo':'Transferencia','cc':[],'estado':'pendiente','byn':'Caja Uno'}]})
    def lote(items):return ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':items}),headers=HDR).json()
    lote([{'u':'1001','name':'Ana López','alumno':'s1','clave':'abcd-efgh'},{'u':'1002','name':'Beto Mena','alumno':'s2','clave':'ijkm-npqr'},{'u':'1003','name':'Carla Egresada','alumno':'s3','clave':'stuv-wxyz'}])
    def entra(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200;return cx
    a1=entra('1001','abcd-efgh');a1.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-ana-77'}),headers=HDR)
    ok('foto_propia_si',a1.request.get(B+'/api/doc/fotos/s1').json()['exists'] is True and [d['id'] for d in a1.request.get(B+'/api/col/fotos').json()['docs']]==['s1'])
    ok('foto_ajena_no',a1.request.get(B+'/api/doc/fotos/s2').json()['exists'] is False)
    ok('foto_no_se_escribe',a1.request.put(B+'/api/doc/fotos/s1',data=json.dumps({'d':'x'}),headers=HDR).status==403)
    st=a1.request.get(B+'/api/col/students').json()['docs'][0]['data'];ok('tutor_si_domicilio_no','tut' in st and st['tutTel']=='7261234567' and 'dom' not in st and 'tel' not in st)
    # ---- pantalla de Ana ----
    def portal(u,c):
        cx=b.new_context();cx.set_default_timeout(9000);pa=pagina(cx);pa.goto(B+'/');W(pa,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pa.fill('#lgU',u);pa.fill('#lgP',c);pa.click('#lgGo');W(pa,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&S.length===1&&!document.getElementById('dPw').open",15);pa.wait_for_timeout(600);pa.evaluate(MOCK);return pa
    pa=portal('1001','clave-ana-77');tx=pa.inner_text('#poBody')
    ok('seccion_credencial','Mi credencial digital' in tx and pa.is_visible('#poCred'))
    cred=pa.inner_text('#poBody div[style*="342px"]') if pa.locator('#poBody div[style*="342px"]').count() else ''
    ok('credencial_tiene_sus_datos','Ana López' in tx and '1001' in tx and 'Derecho' in tx and 'Rosa López' in tx and '7261234567' in tx and 'Vigencia: 31/12/2026' in tx)
    ok('credencial_con_foto_y_qr',pa.locator('#poBody img[src^="data:image/jpeg"]').count()>=1 and (pa.locator('#poBody svg').count()>=1 or pa.locator('#poBody canvas').count()>=1))
    ok('credencial_frente_y_reverso',pa.locator('#poBody div[style*="342px"]').count()==2)
    pa.click('#poCred');pa.wait_for_timeout(250);t=json.dumps(pa.evaluate("window.__txt"),ensure_ascii=False)
    ok('credencial_pdf',pa.evaluate("window.__sav")==['credencial-1001.pdf'] and 'ANA LÓPEZ' in t and '1001' in t)
    # ---- recibos ----
    ok('recibo_solo_si_confirmado',pa.locator('#poBody [data-rc]').count()==1 and 'Se emite al confirmar' in tx)
    pa.evaluate("window.__sav=[];window.__txt=[];0");pa.click('#poBody [data-rc]');pa.wait_for_timeout(300)
    t=json.dumps(pa.evaluate("window.__txt"),ensure_ascii=False);sv=pa.evaluate("window.__sav")
    ok('recibo_pdf',len(sv)==1 and 'R-000001' in sv[0] and 'R-000001' in t and 'Ana López' in t and '1,300' in t)
    ok('recibo_incluye_concepto_y_forma_de_pago','Efectivo' in t and 'Colegiatura' in t)
    ok('recibo_no_muestra_pendiente','R-000002' not in t)
    # un pago pendiente no genera recibo aunque se fuerce
    pa.evaluate("window.__sav=[];S[0].pagos.slice().forEach(function(g){if(g.folio==='R-000002')recFormalPDF(S[0],g)})");pa.wait_for_timeout(200);ok('pendiente_no_emite',pa.evaluate("window.__sav")==[])
    # el pago se confirma → aparece el recibo
    put('ledger/s1',{'pagos':[{'id':'p1','folio':'R-000001','fecha':'2026-09-05','monto':1300,'metodo':'Efectivo','cc':[],'by':'u','byn':'Caja Uno'},{'id':'p2','folio':'R-000002','fecha':'2026-10-06','monto':1300,'metodo':'Transferencia','cc':[],'estado':'confirmado','confFecha':'2026-10-07','byn':'Caja Uno'}]})
    W(pa,"document.querySelectorAll('#poBody [data-rc]').length===2");ok('al_confirmar_aparece_su_recibo',pa.locator('#poBody [data-rc]').count()==2)
    # ---- sin fotografía y egresado ----
    pb=portal('1002','ijkm-npqr') if False else None
    a2=entra('1002','ijkm-npqr');a2.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'ijkm-npqr','nueva':'clave-beto-77'}),headers=HDR)
    put('fotos/s2',{'d':None}) if False else ctx.request.delete(B+'/api/doc/fotos/s2',headers=HDR)
    pb=portal('1002','clave-beto-77');tb=pb.inner_text('#poBody')
    ok('sin_foto_avisa','todavía no hay fotografía registrada' in tb and pb.is_visible('#poCred'))
    a3=entra('1003','stuv-wxyz');a3.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'stuv-wxyz','nueva':'clave-carla-77'}),headers=HDR)
    pc=portal('1003','clave-carla-77');tc=pc.inner_text('#poBody')
    ok('egresado_sin_credencial','disponible para alumnos activos' in tc and pc.locator('#poCred').count()==0 and 'Mi credencial digital' in tc)
    ok('alumno_no_ve_credencial_ajena','Beto' not in tx and '1002' not in tx and pb.evaluate("S.length")==1)
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
