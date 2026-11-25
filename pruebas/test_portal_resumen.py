import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3192;B='http://127.0.0.1:%d'%PORT;TOK='tok-po-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_po',LF_SETUP_TOKEN=TOK,LF_SIN_CONTACTO='1')
os.system('rm -rf /tmp/nbdata_po && mkdir -p /tmp/nbdata_po')
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
    put('calif/s1',{'items':[{'id':'1','mid':'m1','mat':'Introducción al derecho','plan':'Derecho','per':PER,'cuat':1,'doc':'X','cal':9.0},{'id':'2','mid':'m2','mat':'Lógica','plan':'Derecho','per':PER,'cuat':1,'doc':'X','cal':7.0}]})
    def lote(items):return ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':items}),headers=HDR).json()
    lote([{'u':'1001','name':'Ana López','alumno':'s1','clave':'abcd-efgh'},{'u':'1002','name':'Beto Mena','alumno':'s2','clave':'ijkm-npqr'},{'u':'1003','name':'Carla Egresada','alumno':'s3','clave':'stuv-wxyz'}])
    def entra(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200;return cx
    a1=entra('1001','abcd-efgh');a1.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-ana-77'}),headers=HDR)
    ok('foto_propia_si',a1.request.get(B+'/api/doc/fotos/s1').json()['exists'] is True and [d['id'] for d in a1.request.get(B+'/api/col/fotos').json()['docs']]==['s1'])
    ok('foto_ajena_no',a1.request.get(B+'/api/doc/fotos/s2').json()['exists'] is False)
    ok('foto_no_se_escribe',a1.request.put(B+'/api/doc/fotos/s1',data=json.dumps({'d':'x'}),headers=HDR).status==403)
    st=a1.request.get(B+'/api/col/students').json()['docs'][0]['data'];ok('tutor_si_domicilio_no','tut' in st and st['tutTel']=='7261234567' and 'dom' not in st and 'tel' not in st)
    a2=entra('1002','ijkm-npqr');a2.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'ijkm-npqr','nueva':'clave-beto-77'}),headers=HDR)
    def portal(u,c):
        cx=b.new_context();cx.set_default_timeout(9000);pa=pagina(cx);pa.goto(B+'/');W(pa,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pa.fill('#lgU',u);pa.fill('#lgP',c);pa.click('#lgGo');W(pa,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&S.length===1&&!document.getElementById('dPw').open",15);pa.wait_for_timeout(900);return pa
    pa=portal('1001','clave-ana-77')
    ok('hay_resumen',pa.is_visible('#poRes'))
    rs=pa.inner_text('#poRes')
    ok('resumen_cuatrimestre_y_grupo','Cuatrimestre actual' in rs and 'Grupo 1111' in rs)
    ok('resumen_promedio','Promedio general' in rs and '8.0' in rs)
    ok('no_muestra_avance_de_pagos_al_alumno','Avance de pagos' not in rs and 'Pendiente' not in rs and '%' not in rs and pa.locator('#poRes [style*="var(--ok)"]').count()==0)
    ok('resumen_avisos','Avisos nuevos' in rs)
    ok('resumen_arriba_de_las_secciones',pa.evaluate("(function(){var r=document.getElementById('poRes'),h=document.querySelector('#poBody h2');return !!(r.compareDocumentPosition(h)&Node.DOCUMENT_POSITION_FOLLOWING)})()"))
    ok('hay_menu_de_secciones',pa.is_visible('#poNav'))
    ch=pa.eval_on_selector_all('#poNav [data-posec]','e=>e.map(x=>x.dataset.posec)')
    ok('menu_incluye_secciones_clave',all(any(k in c for c in ch) for k in ['Mis calificaciones','Mi credencial digital','Mis solicitudes','Mis pagos y recibos','Notificaciones','Mis datos']))
    ok('sin_chips_repetidos',len(ch)==len(set(ch)))
    ok('menu_fijo','sticky' in pa.evaluate("getComputedStyle(document.getElementById('poNav')).position"))
    pa.evaluate("window.scrollTo(0,0)")
    pa.click('#poNav [data-posec="Mis pagos y recibos"]');pa.wait_for_timeout(900)
    top=pa.evaluate("(function(){var h=Array.prototype.slice.call(document.querySelectorAll('#poBody h2')).find(function(x){return /Mis pagos y recibos/.test(x.textContent)});return {t:h.getBoundingClientRect().top,n:document.getElementById('poNav').getBoundingClientRect().bottom,y:window.pageYOffset}})()")
    ok('el_menu_lleva_a_la_seccion',top['y']>0 and top['t']>=top['n']-6 and top['t']<500)
    pa.click('#poNav [data-posec="Mis calificaciones"]');pa.wait_for_timeout(900)
    ok('menu_a_calificaciones',pa.evaluate("(function(){var h=Array.prototype.slice.call(document.querySelectorAll('#poBody h2')).find(function(x){return /Mis calificaciones/.test(x.textContent)});var r=h.getBoundingClientRect();return r.top<500&&r.top>=-5})()"))
    ok('hash_intacto',pa.evaluate("location.hash===''"))
    # tras repintar sigue habiendo un solo resumen y un solo menú
    pa.evaluate("renderPor();renderPor();0");pa.wait_for_timeout(300)
    ok('un_solo_resumen_y_menu',pa.locator('#poRes').count()==1 and pa.locator('#poNav').count()==1)
    ok('secciones_existentes_siguen',pa.is_visible('#poCred') and pa.is_visible('#poBol') and pa.locator('#rqBoxP').count()==1 and pa.locator('#cmBoxP').count()==1)
    # alumna egresada y alumno sin calificaciones
    pb=portal('1002','clave-beto-77');rb=pb.inner_text('#poRes')
    ok('alumno_sin_calificaciones','Aún sin calificaciones' in rb and pb.is_visible('#poNav'))
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
