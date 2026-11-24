import subprocess,time,json,os,urllib.request,urllib.error,datetime
import numpy as np,cv2
from playwright.sync_api import sync_playwright
PORT=3191;B='http://127.0.0.1:%d'%PORT;TOK='tok-cp-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_cp',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_cp && mkdir -p /tmp/nbdata_cp')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=25):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
PER='Sep–Dic 2026'
def chk(s):
    h=2166136261
    for ch in s:h^=ord(ch);h=(h*16777619)&0xffffffff
    return '%08x'%h
def pub(path):
    try:
        r=urllib.request.urlopen(B+path);return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:return e.code,json.loads(e.read())
        except Exception:return e.code,{}
MOCK="""()=>{window.__txt=[];window.__sav=[];window.__pages=0;window.__qr=null;
 function mk(){return new Proxy({},{get:function(o,k){
   if(k==='text')return function(s){window.__txt.push(String(Array.isArray(s)?s.join(' '):s));return me};
   if(k==='splitTextToSize')return function(s){return [String(s)]};if(k==='getTextWidth')return function(){return 10};
   if(k==='output')return function(){return new ArrayBuffer(8)};if(k==='addPage')return function(){window.__pages++;return me};
   return function(){return me}}})}
 var me=null;function PDF(){me=mk();return me}
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};
 var q0=qrPDF;qrPDF=function(d,t,x,y,l){window.__qr=t;return q0(d,t,x,y,l)};0}"""
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('students/s1',{'mat':'20230101','nombre':'Ana López Martínez','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False,'tel':'7261112233','dom':'Calle 1'})
    put('students/s2',{'mat':'20230102','nombre':'Beto Sin Notas','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False})
    put('students/s3',{'mat':'20230103','nombre':'Carla Reprobada','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False})
    def it(i,m,cal,per=PER,cu=3):return {'id':i,'mid':'m'+i,'mat':m,'plan':'Pedagogía','per':per,'cuat':cu,'doc':'Mtra. Laura Díaz','cal':cal,'fecha':'2026-11-01'}
    ITEMS=[it('1','Didáctica',9.0),it('2','Educación especial',8.0),it('3','Modelos de enseñanza',9.5),it('4','Administración y educación',5.0),it('5','Historia',7.0,'Sep–Dic 2025',2),it('6','Filosofía',8.0,'Sep–Dic 2025',2),it('7','Taller en curso',None)]
    put('calif/s1',{'items':ITEMS})
    put('calif/s3',{'items':[it('9','Didáctica',5.0),it('10','Historia',6.0)]})
    F='20261105'
    def url(i,c,v=None):return '/api/verificar?t=k&id=%s&c=%s'%(i,c)+('&v='+v if v else '')
    cod=chk('K|s1|'+F)
    st,j=pub(url('s1',cod,F))
    ok('verifica_sin_sesion',st==200 and j['ok'] and j['tipo']=='certificado' and j['titulo']=='Certificado parcial de estudios')
    ok('datos',j['nombre']=='Ana López Martínez' and j['matricula']=='•••••101' and j['plan']=='Pedagogía' and j['emitido']=='2026-11-05')
    ok('solo_aprobadas',j['aprobadas']==4 and j['promedio']=='8.6' and [p['periodo'] for p in j['periodos']]==['Sep–Dic 2025','Sep–Dic 2026'])
    nombres=[m['asignatura'] for p in j['periodos'] for m in p['materias']]
    ok('no_incluye_reprobadas_ni_en_curso','Administración y educación' not in nombres and 'Taller en curso' not in nombres and 'Filosofía' in nombres and 'Historia' not in nombres and 'Didáctica' in nombres)
    ok('no_expone_otros_datos','7261112233' not in json.dumps(j) and 'Calle' not in json.dumps(j) and 'Mtra' not in json.dumps(j,ensure_ascii=False))
    ok('codigo_equivocado',pub(url('s1','00000000',F))[1]['ok'] is False)
    ok('fecha_distinta_invalida',pub(url('s1',cod,'20261106'))[1]['ok'] is False)
    ok('codigo_de_historial_no_sirve',pub(url('s1',chk('H|s1|'+F),F))[1]['ok'] is False)
    ok('parametros_invalidos',pub(url('s1',cod))[0]==400 and pub(url('s1',cod,'2026'))[0]==400)
    ok('alumno_sin_aprobadas',pub(url('s3',chk('K|s3|'+F),F))[1]['ok'] is False and 'no tiene asignaturas aprobadas' in pub(url('s3',chk('K|s3|'+F),F))[1]['motivo'])
    ok('alumno_sin_calificaciones',pub(url('s2',chk('K|s2|'+F),F))[1]['ok'] is False)
    ok('alumno_inexistente',pub(url('zzzz',chk('K|zzzz|'+F),F))[1]['ok'] is False)
    cx=b.new_context();pv=cx.new_page();pv.on("pageerror",lambda e:errs.append(str(e)))
    pv.goto(B+'/verificar#k.s1.%s.%s'%(F,cod));pv.wait_for_selector('.sello.ok');tv=pv.inner_text('#res')
    ok('pagina_publica','Documento auténtico' in tv and 'certificado parcial' in tv.lower() and 'Ana López Martínez' in tv and 'Didáctica' in tv and 'Administración y educación' not in tv)
    pv.goto(B+'/verificar#k.s1.%s.00000000'%F);pv.reload();pv.wait_for_selector('.sello.bad');ok('pagina_rechaza_alterado','No se pudo verificar' in pv.inner_text('#res'))
    pv.goto(B+'/#k.s1.%s.%s'%(F,cod));pv.wait_for_selector('.sello.ok');ok('qr_redirige_sin_login','/verificar#k.s1.' in pv.url)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===3&&itemsDe('s1').length===7");pg.evaluate(MOCK)
    pg.evaluate("certParcialPDF('s1')");pg.wait_for_timeout(300)
    hoy=pg.evaluate("today().replace(/-/g,'')");qr=pg.evaluate("window.__qr");esperado=B+'/verificar#k.s1.%s.%s'%(hoy,chk('K|s1|'+hoy))
    ok('pdf_lleva_su_qr',qr==esperado)
    tx=' | '.join(pg.evaluate("window.__txt"));ok('pdf_contenido','Certificado parcial de estudios' in tx and 'Verifique este certificado' in tx and 'Didáctica' in tx and 'Filosofía' in tx and 'Historia' not in tx and 'Administración y educación' not in tx and 'Taller en curso' not in tx and 'Asignaturas aprobadas' in tx)
    ok('nombre_archivo',pg.evaluate("window.__sav")==['certificado-parcial-20230101.pdf'])
    m=pg.evaluate("(function(t){var q=QR.make(t);return {n:q.n,mod:q.mod.map(function(r){return r.map(function(v){return v?1:0})})}})(window.__qr)");n=m['n'];esc=10;zona=4
    img=np.full(((n+2*zona)*esc,(n+2*zona)*esc),255,np.uint8)
    for r in range(n):
        for c in range(n):
            if m['mod'][r][c]:img[(r+zona)*esc:(r+zona+1)*esc,(c+zona)*esc:(c+zona+1)*esc]=0
    val,_,_=cv2.QRCodeDetector().detectAndDecode(img);ok('qr_legible',val==qr)
    pg.evaluate("window.__sav=[];window.__qr=null;ALID='s3';certParcialPDF('s3')");pg.wait_for_timeout(300)
    ok('sin_aprobadas_no_genera',pg.evaluate("window.__sav")==[] and pg.evaluate("window.__qr")is None)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===3&&itemsDe('s1').length===7")
    pg.evaluate("verCertP('s1','%s','%s')"%(F,cod));pg.wait_for_selector('#dRc[open]');tr=pg.inner_text('#rcRes');ok('verificacion_en_app','Certificado parcial auténtico' in tr and 'Didáctica' in tr and 'Administración y educación' not in tr)
    pg.evaluate("verCertP('s1','%s','00000000')"%F);pg.wait_for_selector('#dRc[open]');ok('app_detecta_alteracion','alterado' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close()")
    pg.evaluate("verCertP('s3','%s','%s')"%(F,chk('K|s3|'+F)));pg.wait_for_selector('#dRc[open]');ok('app_sin_aprobadas','falso' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close()")
    ok('hash_k',pg.evaluate("(function(){location.hash='#k.s1.%s.%s';var q=qrHash();location.hash='';return q&&q.tipo==='k'&&q.id==='s1'&&q.fecha==='%s'&&q.code==='%s'})()"%(F,cod,F,cod)))
    pg.evaluate("location.hash='#k.s1.%s.%s'"%(F,cod));W(pg,"document.getElementById('dRc').open",15);ok('escanear_en_app','Certificado parcial auténtico' in pg.inner_text('#rcRes'))
    ok('boton_en_el_perfil',pg.evaluate("!!document.getElementById('pfCerPdf')"))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
