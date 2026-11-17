import subprocess,time,json,os,urllib.request,urllib.error,datetime
import numpy as np,cv2
from playwright.sync_api import sync_playwright
PORT=3095;B='http://127.0.0.1:%d'%PORT;TOK='tok-bq-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata25',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata25 && mkdir -p /tmp/nbdata25')
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
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':3,'alumnos':['s1']})
    def it(i,m,doc,cal,per=PER):return {'id':i,'mid':'m'+i,'mat':m,'plan':'Pedagogía','per':per,'cuat':3,'doc':doc,'cal':cal,'fecha':'2026-11-01'}
    put('calif/s1',{'items':[it('1','Didáctica','Mtra. Laura Díaz',9.0),it('2','Educación especial','Mtro. Iván Cruz',8.5),it('3','Modelos de enseñanza','Mtra. Laura Díaz',9.2),it('4','Administración y educación','Mtra. Sofía Ramos',5.5),it('5','Sistema educativo nacional','',None),it('6','Antigua','',7.0,'Sep–Dic 2025')]})
    F='20261105'
    def url(t,i,c,v=None,f=None):
        return '/api/verificar?t=%s&id=%s&c=%s'%(t,i,c)+('&v='+v if v else '')+('&f='+f if f else '')
    cod=chk('B|s1|S2026|'+F)
    st,j=pub(url('b','s1',cod,'S2026',F))
    ok('verifica_la_boleta_sin_sesion',st==200 and j['ok'] and j['tipo']=='boleta' and j['titulo']=='Boleta de calificaciones')
    ok('datos_de_la_boleta',j['nombre']=='Ana López Martínez' and j['matricula']=='•••••101' and j['plan']=='Pedagogía' and j['periodo']==PER and j['cuatrimestre']=='3' and j['grupo']=='4821' and j['emitida']=='2026-11-05')
    ok('promedio_y_estatus',j['promedio']=='8.1' and [m['asignatura'] for m in j['materias']]==sorted(m['asignatura'] for m in j['materias']) and {m['asignatura']:m['estatus'] for m in j['materias']}=={'Administración y educación':'Reprobada','Didáctica':'Aprobada','Educación especial':'Aprobada','Modelos de enseñanza':'Aprobada','Sistema educativo nacional':'En curso'} and len(j['materias'])==5)
    ok('calificacion_aprobatoria_8',pg.evaluate("MINAP")==8 and pg.evaluate("[estat(8),estat(7.9),estat(null),estat(10)]")==['Aprobada','Reprobada','En curso','Aprobada'])
    put('calif/s1',{'items':[it('1','Didáctica','X',8.0),it('2','Educación especial','X',7.9),it('3','Modelos','X',7.5)]});ok('servidor_usa_8_como_minima',{m['asignatura']:m['estatus'] for m in pub(url('b','s1',cod,'S2026',F))[1]['materias']}=={'Didáctica':'Aprobada','Educación especial':'Reprobada','Modelos':'Reprobada'})
    put('calif/s1',{'items':[it('1','Didáctica','Mtra. Laura Díaz',9.0),it('2','Educación especial','Mtro. Iván Cruz',8.5),it('3','Modelos de enseñanza','Mtra. Laura Díaz',9.2),it('4','Administración y educación','Mtra. Sofía Ramos',5.5),it('5','Sistema educativo nacional','',None),it('6','Antigua','',7.0,'Sep–Dic 2025')]})
    ok('solo_el_periodo_de_la_boleta','Antigua' not in json.dumps(j,ensure_ascii=False))
    ok('no_expone_otros_datos','7261112233' not in json.dumps(j) and 'Calle' not in json.dumps(j))
    ok('codigo_equivocado',pub(url('b','s1','00000000','S2026',F))[1]['ok'] is False)
    ok('fecha_distinta_invalida_el_codigo',pub(url('b','s1',cod,'S2026','20261106'))[1]['ok'] is False)
    ok('periodo_distinto_invalida_el_codigo',pub(url('b','s1',cod,'E2027',F))[1]['ok'] is False)
    ok('parametros_invalidos',pub(url('b','s1',cod,'X2026',F))[0]==400 and pub(url('b','s1',cod,'S2026',None))[0]==400 and pub(url('b','s1',cod,'S2026','2026'))[0]==400 and pub(url('b','s1',cod))[0]==400)
    cod2=chk('B|s1|E2027|'+F);st,j2=pub(url('b','s1',cod2,'E2027',F));ok('periodo_sin_calificaciones',st==200 and j2['ok'] is False and 'no tiene calificaciones' in j2['motivo'])
    cod3=chk('B|zzzz|S2026|'+F);ok('alumno_inexistente',pub(url('b','zzzz',cod3,'S2026',F))[1]['ok'] is False)
    put('calif/s1',{'items':[it('1','Didáctica','Mtra. Laura Díaz',10.0)]});st,j3=pub(url('b','s1',cod,'S2026',F));ok('una_correccion_posterior_se_ve_en_la_pagina',j3['ok'] and j3['materias'][0]['cal']==10 and j3['promedio']=='10.0')
    put('calif/s1',{'items':[it('1','Didáctica','Mtra. Laura Díaz',9.0),it('2','Educación especial','Mtro. Iván Cruz',8.5),it('3','Modelos de enseñanza','Mtra. Laura Díaz',9.2),it('4','Administración y educación','Mtra. Sofía Ramos',5.5),it('5','Sistema educativo nacional','',None)]})
    # ---- página pública ----
    cx=b.new_context();pv=cx.new_page();pv.on("pageerror",lambda e:errs.append(str(e)))
    pv.goto(B+'/verificar#b.s1.S2026.%s.%s'%(F,cod));pv.wait_for_selector('.sello.ok');tv=pv.inner_text('#res')
    ok('pagina_publica_de_la_boleta','Documento auténtico' in tv and 'boleta de calificaciones' in tv.lower() and 'Ana López Martínez' in tv and '•••••101' in tv and 'Didáctica' in tv and '9.0 · Aprobada' in tv and '5.5 · Reprobada' in tv and '— · En curso' in tv and '8.1' in tv and '05/11/2026' in tv and 'Mtra. Laura Díaz' in tv)
    ok('pagina_sin_inicio_de_sesion',pv.evaluate("!document.getElementById('login')&&!document.querySelector('input[type=password]')"))
    pv.goto(B+'/verificar#b.s1.S2026.%s.00000000'%F);pv.reload();pv.wait_for_selector('.sello.bad');ok('pagina_rechaza_codigo_alterado','No se pudo verificar' in pv.inner_text('#res'))
    pv.goto(B+'/#b.s1.S2026.%s.%s'%(F,cod));pv.wait_for_selector('.sello.ok');ok('qr_con_la_direccion_del_sistema_redirige_sin_login','/verificar#b.s1.S2026.' in pv.url)
    # ---- la boleta que genera la aplicación ----
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===1&&itemsDe('s1').length===5");pg.evaluate(MOCK)
    pg.evaluate("boletaPDF('s1','%s')"%PER);pg.wait_for_timeout(300)
    hoy=pg.evaluate("today().replace(/-/g,'')");qr=pg.evaluate("window.__qr");esperado=B+'/verificar#b.s1.S2026.%s.%s'%(hoy,chk('B|s1|S2026|'+hoy))
    ok('el_pdf_lleva_el_qr_de_su_boleta',qr==esperado)
    tx=' | '.join(pg.evaluate("window.__txt"));ok('la_boleta_dice_calificacion_aprobatoria_8','Calificación aprobatoria: 8.0' in tx)
    ok('el_pdf_dice_que_se_puede_verificar','Verifique esta boleta' in tx and 'Escanee el código QR' in tx and 'Boleta de calificaciones' in tx and 'Control escolar' in tx and 'Sello' in tx)
    ok('nombre_del_archivo',pg.evaluate("window.__sav")==['boleta-20230101-sep-dic-2026.pdf'])
    ok('una_sola_pagina',pg.evaluate("window.__pages")==0)
    # el QR se puede leer con una cámara
    m=pg.evaluate("(function(t){var q=QR.make(t);return {n:q.n,mod:q.mod.map(function(r){return r.map(function(v){return v?1:0})})}})(window.__qr)");n=m['n'];esc=10;zona=4
    img=np.full(((n+2*zona)*esc,(n+2*zona)*esc),255,np.uint8)
    for r in range(n):
        for c in range(n):
            if m['mod'][r][c]:img[(r+zona)*esc:(r+zona+1)*esc,(c+zona)*esc:(c+zona+1)*esc]=0
    val,_,_=cv2.QRCodeDetector().detectAndDecode(img);ok('qr_legible_con_camara',val==qr)
    # boleta larga: no se sale de la hoja
    pg.evaluate("(function(){var its=itemsDe('s1').slice();for(var i=0;i<16;i++)its.push({id:'z'+i,mid:'mz'+i,mat:'Asignatura extra '+i,plan:'Pedagogía',per:'Sep–Dic 2026',cuat:3,doc:'Mtro. X',cal:8});CAL.s1={items:its}})()")
    pg.evaluate("window.__pages=0;window.__qr=null;boletaPDF('s1','%s')"%PER);pg.wait_for_timeout(300);ok('boleta_larga_pasa_a_otra_hoja_y_conserva_el_qr',pg.evaluate("window.__pages")>=1 and pg.evaluate("window.__qr")!=None)
    # ---- verificación dentro de la aplicación (versión sin servidor propio) ----
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===1&&itemsDe('s1').length===5")
    pg.evaluate("verBoleta('s1','S2026','%s','%s')"%(F,cod));pg.wait_for_selector('#dRc[open]');ok('verificacion_en_la_aplicacion','Boleta auténtica' in pg.inner_text('#rcRes') and '9.0' in pg.inner_text('#rcRes') and 'Aprobada' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close()")
    pg.evaluate("verBoleta('s1','S2026','%s','00000000')"%F);pg.wait_for_selector('#dRc[open]');ok('aplicacion_detecta_alteracion','alterada' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close()")
    ok('hash_b_se_interpreta',pg.evaluate("(function(){location.hash='#b.s1.S2026.%s.%s';var q=qrHash();location.hash='';return q&&q.tipo==='b'&&q.per==='S2026'&&q.fecha==='%s'})()"%(F,cod,F)))
    ok('periodos_de_ida_y_vuelta',pg.evaluate("['Sep–Dic 2026','Ene–Abr 2027','May–Ago 2025'].map(function(p){return perDeCod(perCod(p))===p}).every(Boolean)"))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
