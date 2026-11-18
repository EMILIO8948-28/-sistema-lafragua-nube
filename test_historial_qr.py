import subprocess,time,json,os,urllib.request,urllib.error,datetime
import numpy as np,cv2
from playwright.sync_api import sync_playwright
PORT=3148;B='http://127.0.0.1:%d'%PORT;TOK='tok-hq-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_hq',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_hq && mkdir -p /tmp/nbdata_hq')
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
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':3,'alumnos':['s1']})
    def it(i,m,doc,cal,per=PER,cu=3):return {'id':i,'mid':'m'+i,'mat':m,'plan':'Pedagogía','per':per,'cuat':cu,'doc':doc,'cal':cal,'fecha':'2026-11-01'}
    ITEMS=[it('1','Didáctica','Mtra. Laura Díaz',9.0),it('2','Educación especial','Mtro. Iván Cruz',8.5),it('3','Modelos de enseñanza','Mtra. Laura Díaz',9.2),it('4','Administración y educación','Mtra. Sofía Ramos',5.5),it('5','Sistema educativo nacional','',None),it('6','Antigua','',7.0,'Sep–Dic 2025',2)]
    put('calif/s1',{'items':ITEMS})
    F='20261105'
    def url(i,c,v=None):return '/api/verificar?t=h&id=%s&c=%s'%(i,c)+('&v='+v if v else '')
    cod=chk('H|s1|'+F)
    st,j=pub(url('s1',cod,F))
    ok('verifica_el_historial_sin_sesion',st==200 and j['ok'] and j['tipo']=='historial' and j['titulo']=='Historial académico')
    ok('datos_del_historial',j['nombre']=='Ana López Martínez' and j['matricula']=='•••••101' and j['plan']=='Pedagogía' and j['emitido']=='2026-11-05')
    ok('periodos_en_orden',[p['periodo'] for p in j['periodos']]==['Sep–Dic 2025','Sep–Dic 2026'] and [p['cuatrimestre'] for p in j['periodos']]==['2','3'])
    ok('promedios_y_conteos',j['promedioGeneral']=='7.8' and j['aprobadas']==3 and j['reprobadas']==2 and j['periodos'][1]['promedio']=='8.1' and j['periodos'][0]['promedio']=='7.0')
    ok('estatus_por_materia',{m['asignatura']:m['estatus'] for m in j['periodos'][1]['materias']}=={'Administración y educación':'Reprobada','Didáctica':'Aprobada','Educación especial':'Aprobada','Modelos de enseñanza':'Aprobada','Sistema educativo nacional':'En curso'} and j['periodos'][0]['materias'][0]['estatus']=='Reprobada')
    ok('no_expone_otros_datos','7261112233' not in json.dumps(j) and 'Calle' not in json.dumps(j) and 'Mtra' not in json.dumps(j,ensure_ascii=False))
    ok('codigo_equivocado',pub(url('s1','00000000',F))[1]['ok'] is False)
    ok('fecha_distinta_invalida_el_codigo',pub(url('s1',cod,'20261106'))[1]['ok'] is False)
    ok('el_codigo_de_boleta_no_sirve_como_historial',pub(url('s1',chk('B|s1|S2026|'+F),F))[1]['ok'] is False)
    ok('parametros_invalidos',pub(url('s1',cod))[0]==400 and pub(url('s1',cod,'2026'))[0]==400 and pub(url('s1','xyz',F))[0]==400)
    ok('alumno_sin_calificaciones',pub(url('s2',chk('H|s2|'+F),F))[1]['ok'] is False and 'no tiene calificaciones' in pub(url('s2',chk('H|s2|'+F),F))[1]['motivo'])
    ok('alumno_inexistente',pub(url('zzzz',chk('H|zzzz|'+F),F))[1]['ok'] is False)
    put('calif/s1',{'items':[it('1','Didáctica','X',10.0)]});st,j3=pub(url('s1',cod,F));ok('una_correccion_posterior_se_ve',j3['ok'] and j3['promedioGeneral']=='10.0' and len(j3['periodos'])==1)
    put('calif/s1',{'items':ITEMS})
    # ---- página pública ----
    cx=b.new_context();pv=cx.new_page();pv.on("pageerror",lambda e:errs.append(str(e)))
    pv.goto(B+'/verificar#h.s1.%s.%s'%(F,cod));pv.wait_for_selector('.sello.ok');tv=pv.inner_text('#res')
    ok('pagina_publica_del_historial','Documento auténtico' in tv and 'historial académico' in tv.lower() and 'Ana López Martínez' in tv and '•••••101' in tv and 'Didáctica' in tv and '9.0 · Aprobada' in tv and '5.5 · Reprobada' in tv and '— · En curso' in tv and '7.8' in tv and '05/11/2026' in tv and 'Antigua' in tv)
    ok('pagina_sin_inicio_de_sesion',pv.evaluate("!document.getElementById('login')&&!document.querySelector('input[type=password]')"))
    pv.goto(B+'/verificar#h.s1.%s.00000000'%F);pv.reload();pv.wait_for_selector('.sello.bad');ok('pagina_rechaza_codigo_alterado','No se pudo verificar' in pv.inner_text('#res'))
    pv.goto(B+'/#h.s1.%s.%s'%(F,cod));pv.wait_for_selector('.sello.ok');ok('qr_con_la_direccion_del_sistema_redirige_sin_login','/verificar#h.s1.' in pv.url)
    # ---- el historial que genera la aplicación ----
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===2&&itemsDe('s1').length===6");pg.evaluate(MOCK)
    pg.evaluate("historialPDF('s1')");pg.wait_for_timeout(300)
    hoy=pg.evaluate("today().replace(/-/g,'')");qr=pg.evaluate("window.__qr");esperado=B+'/verificar#h.s1.%s.%s'%(hoy,chk('H|s1|'+hoy))
    ok('el_pdf_lleva_el_qr_de_su_historial',qr==esperado)
    tx=' | '.join(pg.evaluate("window.__txt"));ok('el_pdf_dice_que_se_puede_verificar','Verifique este historial' in tx and 'Escanee el código QR' in tx and 'Historial académico' in tx and 'Promedio general' in tx)
    ok('nombre_del_archivo',pg.evaluate("window.__sav")==['historial-academico-20230101.pdf'])
    m=pg.evaluate("(function(t){var q=QR.make(t);return {n:q.n,mod:q.mod.map(function(r){return r.map(function(v){return v?1:0})})}})(window.__qr)");n=m['n'];esc=10;zona=4
    img=np.full(((n+2*zona)*esc,(n+2*zona)*esc),255,np.uint8)
    for r in range(n):
        for c in range(n):
            if m['mod'][r][c]:img[(r+zona)*esc:(r+zona+1)*esc,(c+zona)*esc:(c+zona+1)*esc]=0
    val,_,_=cv2.QRCodeDetector().detectAndDecode(img);ok('qr_legible_con_camara',val==qr)
    # historial largo: pasa a otra hoja y conserva el QR
    pg.evaluate("(function(){var its=[];for(var p=0;p<9;p++)for(var i=0;i<7;i++)its.push({id:'z'+p+i,mid:'mz'+p+i,mat:'Asignatura '+p+'-'+i,plan:'Pedagogía',per:'Sep–Dic '+(2018+p),cuat:p+1,doc:'X',cal:8});CAL.s1={items:its}})()")
    pg.evaluate("window.__pages=0;window.__qr=null;historialPDF('s1')");pg.wait_for_timeout(300);ok('historial_largo_pasa_a_otras_hojas_y_conserva_el_qr',pg.evaluate("window.__pages")>=1 and pg.evaluate("window.__qr")!=None)
    # ---- verificación dentro de la aplicación ----
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===2&&itemsDe('s1').length===6")
    pg.evaluate("verHist('s1','%s','%s')"%(F,cod));pg.wait_for_selector('#dRc[open]');tr=pg.inner_text('#rcRes');ok('verificacion_en_la_aplicacion','Historial académico auténtico' in tr and '9.0' in tr and 'Aprobada' in tr and 'Antigua' in tr and 'Promedio general' in tr);pg.evaluate("document.getElementById('dRc').close()")
    pg.evaluate("verHist('s1','%s','00000000')"%F);pg.wait_for_selector('#dRc[open]');ok('aplicacion_detecta_alteracion','alterado' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close()")
    pg.evaluate("verHist('s2','%s','%s')"%(F,chk('H|s2|'+F)));pg.wait_for_selector('#dRc[open]');ok('aplicacion_alumno_sin_notas','falso' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close()")
    ok('hash_h_se_interpreta',pg.evaluate("(function(){location.hash='#h.s1.%s.%s';var q=qrHash();location.hash='';return q&&q.tipo==='h'&&q.id==='s1'&&q.fecha==='%s'&&q.code==='%s'})()"%(F,cod,F,cod)))
    ok('hash_h_invalido_se_ignora',pg.evaluate("(function(){location.hash='#h.s1.2026.zzzz';var q=qrHash();location.hash='';return q===null})()"))
    pg.evaluate("location.hash='#h.s1.%s.%s'"%(F,cod));W(pg,"document.getElementById('dRc').open",15);ok('escanear_desde_la_aplicacion_abre_la_verificacion','Historial académico auténtico' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close();location.hash=''")
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
