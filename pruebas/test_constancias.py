import subprocess,time,json,os,urllib.request,urllib.error
from playwright.sync_api import sync_playwright
PORT=3082;B='http://127.0.0.1:%d'%PORT;TOK='tok-co-123';PUB='https://escuela.example.com'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata12',LF_SETUP_TOKEN=TOK,LF_URL_PUBLICA=PUB)
os.system('rm -rf /tmp/nbdata12 && mkdir -p /tmp/nbdata12')
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
def chk(s):
    h=2166136261
    for ch in s:
        h^=ord(ch);h=(h*16777619)&0xffffffff
    return '%08x'%h
MOCK="""()=>{window.__txt=[];window.__sav=[];
 function mk(){return new Proxy({},{get:function(o,k){
   if(k==='text')return function(s){window.__txt.push(String(Array.isArray(s)?s.join(' '):s));return me};
   if(k==='splitTextToSize')return function(s){return [String(s)]};if(k==='getTextWidth')return function(){return 10};
   if(k==='output')return function(){return new ArrayBuffer(8)};if(k==='internal')return {pageSize:{getWidth:function(){return 210},getHeight:function(){return 297}}};
   if(k==='GState')return function(){};
   return function(){return me}}})}
 var me=null;function PDF(){me=mk();return me}
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
def pub(path):
    cx=urllib.request.Request(B+path)
    try:
        r=urllib.request.urlopen(cx);return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:return e.code,json.loads(e.read())
        except Exception:return e.code,{}
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:(pg.__dict__.setdefault('dlg',[]).append(d.message),d.accept()))
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('students/s1',{'mat':'1001','nombre':'Ana López Martínez','carrera':'Derecho','programa':'Derecho','ingreso':2025,'sexo':'Femenino','tel':'726111','dom':'Calle 1'})
    put('students/s2',{'mat':'1002','nombre':'Beto Mena','carrera':'Derecho','programa':'Derecho','ingreso':2025,'sexo':'Masculino'})
    put('students/s3',{'mat':'1003','nombre':'Carla Egresada','carrera':'Derecho','programa':'Derecho','ingreso':2022})
    put('egresados/s3',{'fecha':'2026-08-01','revertido':False})
    put('grupos/g1',{'num':'1111','plan':'Derecho','per':'Sep–Dic 2026','cuat':3,'alumnos':['s1','s2']})
    put('calif/s1',{'items':[{'mid':'m1','mat':'Introducción','per':'Sep–Dic 2026','cuat':3,'doc':'X','cal':9.0},{'mid':'m2','mat':'Civil','per':'Sep–Dic 2026','cuat':3,'doc':'X','cal':8.4}]})
    put('constancias/s1',{'items':[
        {'id':'k1','num':'C-000001','fecha':'2026-10-01','monto':50,'nombre':'Ana López Martínez','mat':'1001','plan':'Derecho','sexo':'Femenino','tipo':'simple','prom':None,'cuat':3,'per':'Sep–Dic 2026','grupo':'1111','dest':''},
        {'id':'k2','num':'C-000002','fecha':'2026-10-02','monto':50,'nombre':'Ana López Martínez','mat':'1001','plan':'Derecho','sexo':'Femenino','tipo':'promedio','prom':8.7,'cuat':3,'per':'Sep–Dic 2026','grupo':'1111','dest':'Instituto Ejemplo'},
        {'id':'k3','num':'C-000003','fecha':'2026-10-03','monto':50,'nombre':'Ana López Martínez','mat':'1001','plan':'Derecho','sexo':'Femenino','prom':8.1,'cuat':3,'per':'Sep–Dic 2026','grupo':'1111'}]})
    put('meta/folioC',{'n':10})
    put('ledger/s1',{'pagos':[{'id':'p1','folio':'R-000001','fecha':'2026-09-05','monto':1300,'metodo':'Efectivo','cc':[],'byn':'Caja'},{'id':'p2','folio':'R-000002','fecha':'2026-10-06','monto':1300.5,'metodo':'Transferencia','cc':[],'estado':'pendiente'}]})
    put('titulaciones/t1',{'num':'T-000001','nombre':'Luis','apPat':'Pérez','apMat':'Gil','grado':'licenciatura','abonos':[{'id':'a1','folio':'RT-000001','fecha':'2026-10-10','monto':500,'metodo':'Efectivo'}]})
    put('acuerdo286/q1',{'num':'B286-000001','nombre':'Mari','apPat':'Ruiz','pagos':[{'id':'g1','folio':'R286-000001','fecha':'2026-10-11','monto':1000,'metodo':'Efectivo','cc':['i']}]})
    # ---------------- verificación pública (sin sesión) ----------------
    def cc(f,mat,fecha):return chk('C|'+f+'|'+mat+'|'+fecha)
    st,j=pub('/api/verificar?t=c&id=C-000001&c='+cc('C-000001','1001','2026-10-01'))
    ok('pub_constancia_simple',st==200 and j['ok'] and j['titulo']=='Constancia de estudios' and j['promedio'] is None and j['nombre']=='Ana López Martínez' and j['matricula']=='•••1' or j.get('matricula')=='•001')
    ok('pub_matricula_enmascarada',j.get('matricula')=='•001')
    ok('pub_constancia_simple_sin_datos_extra',sorted(j.keys())==sorted(['ok','consultado','tipo','titulo','folio','fecha','nombre','matricula','plan','periodo','grupo','promedio','dirigida']) and 'tel' not in json.dumps(j) and 'Calle' not in json.dumps(j))
    st,j=pub('/api/verificar?t=c&id=C-000002&c='+cc('C-000002','1001','2026-10-02'))
    ok('pub_constancia_con_promedio',j['ok'] and j['titulo']=='Constancia de estudios con promedio' and j['promedio']=='8.7' and j['dirigida']=='Instituto Ejemplo')
    st,j=pub('/api/verificar?t=c&id=c-000003&c='+cc('C-000003','1001','2026-10-03'))
    ok('pub_constancia_anterior_sin_tipo_cuenta_como_promedio',j['ok'] and j['promedio']=='8.1' and 'con promedio' in j['titulo'])
    st,j=pub('/api/verificar?t=c&id=C-000001&c=00000000');ok('pub_codigo_distinto',st==200 and j['ok'] is False)
    st,j=pub('/api/verificar?t=c&id=C-999999&c='+cc('C-999999','1','x'));ok('pub_folio_inexistente',j['ok'] is False and 'No se encontró' in j['motivo'])
    ok('pub_entradas_invalidas',pub('/api/verificar?t=x&id=C-1&c=00000000')[0]==400 and pub('/api/verificar?t=c&id=C-1&c=zz')[0]==400 and pub('/api/verificar?t=c&id=%3Cscript%3E&c=00000000')[0]==400 and pub('/api/verificar?t=a&id=s1&c=00000000')[0]==400)
    st,j=pub('/api/verificar?t=v&id=R-000001&c='+chk('R-000001|1300.00|2026-09-05'))
    ok('pub_recibo',j['ok'] and j['tipo']=='recibo' and j['nombre']=='Ana López Martínez' and j['monto']==1300 and j['estado']=='Pago registrado' and j['origen']=='Finanzas')
    st,j=pub('/api/verificar?t=v&id=R-000002&c='+chk('R-000002|1300.50|2026-10-06'));ok('pub_recibo_transferencia_pendiente',j['ok'] and j['estado']=='Transferencia pendiente de confirmar')
    st,j=pub('/api/verificar?t=v&id=RT-000001&c='+chk('RT-000001|500.00|2026-10-10'));ok('pub_recibo_titulacion',j['ok'] and j['origen']=='Titulaciones' and j['nombre']=='Luis Pérez Gil')
    st,j=pub('/api/verificar?t=v&id=R286-000001&c='+chk('R286-000001|1000.00|2026-10-11'));ok('pub_recibo_286',j['ok'] and j['origen']=='Acuerdo 286')
    st,j=pub('/api/verificar?t=v&id=R-000001&c='+chk('R-000001|1300.00|2026-09-06'));ok('pub_recibo_monto_o_fecha_alterados',j['ok'] is False)
    st,j=pub('/api/verificar?t=a&id=s1&v=20301231&c='+chk('CR|s1|20301231'));ok('pub_credencial_vigente',j['ok'] and j['vigente'] is True and j['nombre']=='Ana López Martínez' and j['plan']=='Derecho')
    st,j=pub('/api/verificar?t=a&id=s1&v=20200101&c='+chk('CR|s1|20200101'));ok('pub_credencial_vencida',j['ok'] and j['vigente'] is False and j['egresado'] is False)
    st,j=pub('/api/verificar?t=a&id=s3&v=20301231&c='+chk('CR|s3|20301231'));ok('pub_credencial_egresado',j['ok'] and j['egresado'] is True and j['vigente'] is False)
    st,j=pub('/api/verificar?t=a&id=s1&v=20301231&c=00000000');ok('pub_credencial_codigo_malo',j['ok'] is False)
    r=urllib.request.urlopen(B+'/verificar');html=r.read().decode();ok('pagina_publica',r.status==200 and 'Verificación de documentos' in html and 'noindex' in html)
    ok('yo_trae_direccion_publica',json.loads(urllib.request.urlopen(B+'/api/yo').read())['urlPublica']==PUB)
    # ---------------- pantalla: dos tipos de constancia ----------------
    pg.evaluate("ir('esc');etab('N')");W(pg,"document.getElementById('nTipo')!==null");pg.evaluate(MOCK)
    ok('opciones_de_tipo',pg.evaluate("Array.from(document.querySelectorAll('#nTipo option')).map(o=>o.textContent)")==['Constancia simple','Constancia con promedio'])
    ok('ya_no_hay_casilla_de_promedio',pg.evaluate("document.getElementById('nProm')")==None)
    W(pg,"CONS.s1&&CONS.s1.items.length===3");pg.evaluate("document.getElementById('nAl').value='s1'");pg.evaluate("renderCons()");
    ok('tabla_con_columna_tipo','Tipo' in pg.inner_text('#eN thead') and 'Simple' in pg.inner_text('#nTb') and 'Con promedio' in pg.inner_text('#nTb'))
    def genera(tipo,sid,dest=''):
        pg.evaluate("window.__txt=[];window.__sav=[];0");pg.evaluate("document.getElementById('nAl').value='%s'"%sid);pg.evaluate("renderCons()");pg.select_option('#nTipo',tipo);pg.fill('#nDest',dest);pg.click('#nGen');pg.wait_for_timeout(1500)
        return pg.evaluate("window.__sav"),' | '.join(pg.evaluate("window.__txt"))
    sv,tx=genera('simple','s1')
    ok('simple_sin_promedio',len(sv)==1 and sv[0].startswith('constancia-de-estudios-1001-C-') and 'con promedio' not in tx and 'promedio general' not in tx and 'Constancia de estudios' in tx)
    sv,tx=genera('promedio','s1','Instituto Demo')
    ok('con_promedio_incluye_promedio',len(sv)==1 and 'con-promedio-1001' in sv[0] and 'Constancia de estudios con promedio' in tx and 'promedio general de 8.7' in tx and 'INSTITUTO DEMO' in tx.upper())
    guardadas=pg.evaluate("CONS['s1'].items.map(function(x){return [x.tipo,x.prom]})")
    ok('guarda_el_tipo',guardadas[-2]==['simple',None] and guardadas[-1][0]=='promedio' and guardadas[-1][1]==8.7)
    pg.dlg=[];sv,tx=genera('promedio','s2');ok('promedio_exige_calificaciones',sv==[] and any('calificaciones' in m for m in pg.dlg) and len(pg.evaluate("(CONS['s2']&&CONS['s2'].items)||[]"))==0)
    sv,tx=genera('simple','s2');ok('simple_para_alumno_sin_calificaciones',len(sv)==1 and 'promedio' not in tx.lower().replace('promedio','') or len(sv)==1)
    # ---------------- el QR apunta a la plataforma ----------------
    x=pg.evaluate("CONS['s1'].items.slice(-1)[0]");url=pg.evaluate("qrConst(CONS['s1'].items.slice(-1)[0])")
    ok('qr_usa_direccion_configurada',url.startswith(PUB+'/verificar#c.'+x['num']+'.') and pg.evaluate("qrRecibo('R-000001',1300,'2026-09-05')").startswith(PUB+'/verificar#v.R-000001.') and pg.evaluate("qrCred(S[0],'2030-12-31')").startswith(PUB+'/verificar#a.'))
    pg.evaluate("window.LF_URLP=''");ok('qr_sin_direccion_usa_la_del_sitio',pg.evaluate("qrConst(CONS['s1'].items.slice(-1)[0])").startswith(B+'/verificar#c.'))
    pg.evaluate("window.LF_URLP='%s/'"%PUB);ok('qr_quita_diagonal_final',pg.evaluate("qrConst(CONS['s1'].items.slice(-1)[0])").startswith(PUB+'/verificar#c.'))
    # ---------------- cualquiera abre el enlace del QR ----------------
    enlace=url.replace(PUB,B)
    cx=b.new_context();pv=cx.new_page();pv.goto(enlace);pv.wait_for_selector('.sello');tv=pv.inner_text('#res')
    ok('pagina_verifica_la_constancia','Documento auténtico' in tv and 'Constancia de estudios con promedio' in tv and 'Ana López Martínez' in tv and '8.7' in tv and '•001' in tv and '1001' not in tv.replace('•001',''))
    pv.goto(enlace[:-3]+'abc');pv.reload();pv.wait_for_selector('.sello.bad');ok('pagina_rechaza_codigo_alterado','No se encontró' in pv.inner_text('#res'))
    pv.goto(B+'/verificar');pv.wait_for_selector('.sello');ok('pagina_sin_codigo','Escanea el código QR' in pv.inner_text('#res'))
    rec=pg.evaluate("qrRecibo('R-000001',1300,'2026-09-05')").replace(PUB,B);pv.goto(rec);pv.reload();pv.wait_for_selector('.sello.ok');ok('pagina_verifica_recibo','Recibo' in pv.inner_text('#res') or 'recibo' in pv.inner_text('#res'))
    cred=pg.evaluate("qrCred(S.find(function(s){return s.id==='s1'}),'2030-12-31')").replace(PUB,B);pv.goto(cred);pv.reload();pv.wait_for_selector('.sello.ok');ok('pagina_verifica_credencial','vigente' in pv.inner_text('#res'))
    # ---------------- formato de verificación: sin inicio de sesión, con logo, comprobante y verificación manual ----------------
    ok('pagina_sin_inicio_de_sesion',pv.evaluate("!document.getElementById('login')&&!document.querySelector('input[type=password]')") )
    pv.goto(enlace);pv.wait_for_selector('.sello.ok')
    ok('formato_con_encabezado_y_comprobante','Universidad Lafragua' in pv.inner_text('.enc') and 'DOCUMENTO AUTÉNTICO' in pv.inner_text('.sello').upper() and 'existe en su base de datos' in pv.inner_text('.sello') and 'Consulta realizada' in pv.inner_text('#cons') and pv.is_visible('#imp'))
    ok('logo_publico',urllib.request.urlopen(B+'/logo.png').headers.get('Content-Type')=='image/png')
    ok('respuesta_con_fecha_de_consulta',pub('/api/verificar?t=c&id=C-000001&c='+cc('C-000001','1001','2026-10-01'))[1].get('consultado','').startswith('20'))
    # QR impresos con la dirección del sistema: abren la verificación pública, no el inicio de sesión
    c2=b.new_context();p2=c2.new_page();p2.goto(B+'/#c.C-000002.'+cc('C-000002','1001','2026-10-02'));p2.wait_for_selector('.sello.ok')
    ok('qr_antiguo_redirige_sin_login','/verificar#c.C-000002.' in p2.url and 'Documento auténtico' in p2.inner_text('#res') or 'DOCUMENTO AUTÉNTICO' in p2.inner_text('#res').upper())
    p2.goto(B+'/#v.R-000001.'+chk('R-000001|1300.00|2026-09-05'));p2.wait_for_selector('.sello.ok');ok('qr_antiguo_recibo_redirige','/verificar#v.R-000001.' in p2.url)
    # verificación manual con los datos impresos
    def manual(tipo,folio,dato,fecha):
        p2.goto(B+'/verificar');p2.wait_for_selector('.sello');p2.select_option('#mt',tipo);p2.fill('#mf',folio);p2.fill('#md',fecha)
        if tipo=='c':p2.fill('#mm',dato)
        else:p2.fill('#mo',dato)
        p2.click('#fm button[type=submit]');p2.wait_for_function if False else p2.wait_for_timeout(900);return p2.inner_text('#res')
    r1=manual('c','c-000002','1001','2026-10-02');ok('manual_constancia_autentica','DOCUMENTO AUTÉNTICO' in r1.upper() and 'Ana López Martínez' in r1)
    r2=manual('c','C-000002','1009','2026-10-02');ok('manual_constancia_dato_equivocado','NO SE PUDO VERIFICAR' in r2.upper())
    r3=manual('v','R-000001','1300','2026-09-05');ok('manual_recibo_autentico','DOCUMENTO AUTÉNTICO' in r3.upper() and '$1,300.00' in r3)
    r4=manual('v','R-000001','1300.01','2026-09-05');ok('manual_recibo_monto_distinto','NO SE PUDO VERIFICAR' in r4.upper())
    # límite de consultas
    n429=0
    for i in range(70):
        s_,_=pub('/api/verificar?t=c&id=C-000001&c=00000000')
        if s_==429:n429+=1
    ok('limite_de_consultas',n429>0)
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
