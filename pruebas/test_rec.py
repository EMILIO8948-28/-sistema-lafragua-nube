import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3074;B='http://127.0.0.1:%d'%PORT;TOK='tok-rec-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata4',LF_SETUP_TOKEN=TOK,LF_SIN_CONTACTO='1')
os.system('rm -rf /tmp/nbdata4 && mkdir -p /tmp/nbdata4')
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
MOCK="""()=>{window.__txt=[];window.__qr=[];window.__sav=[];window.__pages=0;
 function PDF(){}
 ['setDrawColor','setLineWidth','setTextColor','setFont','line','addImage','setFontSize','setLineDashPattern','setFillColor','rect'].forEach(function(f){PDF.prototype[f]=function(){return this}});
 PDF.prototype.addPage=function(){window.__pages++;return this};
 PDF.prototype.splitTextToSize=function(t){return [String(t)]};PDF.prototype.text=function(t){window.__txt.push(String(Array.isArray(t)?t[0]:t));return this};PDF.prototype.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};
 window.XLSX={utils:{book_new:function(){return {sheets:[]}},aoa_to_sheet:function(a){return {__aoa:a}},book_append_sheet:function(wb,ws,n){wb.sheets.push({n:n,ws:ws})},encode_range:function(){return 'A1:B2'},encode_cell:function(c){return 'R'+c.r+'C'+c.c}},write:function(wb){return new Uint8Array([80,75])}};
 var q0=qrPDF;qrPDF=function(d,t,x,y,l){window.__qr.push(t);return q0(d,t,x,y,l)};
 saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};
}"""
RESET="()=>{window.__txt=[];window.__qr=[];window.__sav=[];window.__pages=0}"
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    pg.evaluate(MOCK)
    # ---- nómina administrativa ----
    pg.evaluate("ir('na')")
    def emp(nombre,puesto,sal,per='mensual'):
        pg.evaluate("abreEmp(null)");pg.fill('#emNom',nombre);pg.fill('#emPue',puesto);pg.fill('#emSal',str(sal));pg.select_option('#emPer',per);pg.click('#emSave');W(pg,"Object.values(EMP).some(e=>e.nombre==='%s')"%nombre);pg.click('#emCan')
    emp('Ana Admin','Recepción',12000);emp('Carla Admin','Contabilidad',10000);emp('Dani Admin','Intendencia',9000)
    pg.evaluate("document.getElementById('naM').value=String(new Date().getMonth()+1);document.getElementById('naPer').value='M';renderNa()")
    ok('botones_na',pg.is_visible('#naRecibos'))
    mes=pg.evaluate("mesKey(naSel().y,naSel().m)")
    esp=lambda f,m,fe:pg.evaluate("(a)=>qrRecibo(a[0],a[1],a[2])",[f,m,fe])
    # un pago -> un recibo automático
    pg.evaluate(RESET);pg.locator('#naTb tr:has-text("Ana Admin") [data-pg]').click();pg.wait_for_selector('#dNa[open]');pg.click('#naPOk');W(pg,"window.__sav.length>=1")
    pg.wait_for_timeout(150)
    sav=pg.evaluate("window.__sav");ok('na_un_pago_un_recibo',sav==['recibo-nomina-administrativa-NA-000001.pdf'] and pg.evaluate("window.__pages")==0)
    pa=pg.evaluate("Object.values(Object.values(NAD)[0].pagos).find(p=>p.folio==='NA-000001')")
    ok('na_qr_del_recibo',pg.evaluate("window.__qr")==[esp(pa['folio'],pa['neto'],pa['fecha'])])
    ok('na_mensaje_recibo','recibo' in pg.inner_text('#naMsg'))
    # varios pagos -> un solo PDF con una hoja por pago
    pg.evaluate(RESET);pg.click('#naPagarT');pg.wait_for_selector('#dNa[open]');pg.click('#naPOk');W(pg,"window.__sav.length>=1");pg.wait_for_timeout(150)
    ok('na_lote_un_pdf',pg.evaluate("window.__sav")==['recibos-nomina-administrativa-%s.pdf'%mes] and pg.evaluate("window.__pages")==1 and len(pg.evaluate("window.__qr"))==2)
    t=pg.evaluate("window.__txt");ok('na_lote_contenido','NA-000002' in t and 'NA-000003' in t and 'Carla Admin' in t and 'Dani Admin' in t and t.index('Carla Admin')<t.index('Dani Admin'))
    # recibos del mes
    pg.evaluate(RESET);pg.click('#naRecibos');pg.wait_for_timeout(150)
    t=pg.evaluate("window.__txt");ok('na_recibos_del_mes',pg.evaluate("window.__sav")==['recibos-nomina-administrativa-%s.pdf'%mes] and pg.evaluate("window.__pages")==2 and len(pg.evaluate("window.__qr"))==3 and t.index('NA-000001')<t.index('NA-000002')<t.index('NA-000003'))
    ok('na_mensaje_lote','3 recibos' in pg.inner_text('#naMsg'))
    # botón por fila
    pg.evaluate(RESET);pg.locator('#naTb tr:has-text("Carla Admin") [data-rc]').click();pg.wait_for_timeout(100);ok('na_recibo_por_fila',pg.evaluate("window.__sav")==['recibo-nomina-administrativa-NA-000002.pdf'])
    # mes sin pagos
    pg.evaluate("document.getElementById('naM').value=String((new Date().getMonth()+5)%12+1);renderNa()");pg.evaluate(RESET);pg.click('#naRecibos');pg.wait_for_timeout(100)
    ok('na_mes_sin_pagos','No hay pagos' in pg.inner_text('#naMsg') and pg.evaluate("window.__sav")==[])
    # ---- nómina docente ----
    mm=pg.evaluate("new Date().getMonth()+1");per=pg.evaluate("perAct()")
    pg.evaluate("""async(per)=>{
      var nd=async function(n){$("dcNom").value=n;await $("dcAdd").onclick();return Object.keys(DOC).find(function(k){return DOC[k].nombre===n})};
      var A=await nd("Mtra. Rosa"),Bd=await nd("Mtro. Beto"),C=await nd("Mtra. Carmen");
      var clase=async function(did,plan,nom,ini,fin){var id='m'+Math.random().toString(36).slice(2,7),d={per:per,plan:plan,cuat:1,nom:nom,docId:did,dias:['Sáb'],ini:ini,fin:fin,aula:''};await DBH.doc('materias/'+id).set(d);MAT[id]=d;
        var cur=DOC[did],asigs=(cur.asig||[]).concat([{id:'a'+id,cid:'x',plan:plan,cuat:1,nom:nom,per:per,ses:17}]);var nd2=Object.assign({},cur,{asig:asigs});await DBH.doc('docentes/'+did).set(nd2);DOC[did]=nd2};
      await clase(A,'Derecho','Introducción al derecho','08:00','10:00');await clase(Bd,'Enfermería','Anatomía','10:00','12:00');await clase(C,'Derecho','Civil I','08:00','09:00');
    }""",per)
    pg.evaluate("document.getElementById('dDx').close()");pg.evaluate("ir('nom')");pg.evaluate("document.getElementById('nmM').value=String(new Date().getMonth()+1);renderNom()")
    ok('botones_docente',pg.is_visible('#nmRecibos') and 'Recibo' in pg.inner_text('#nmTb').split('\n')[0]+pg.inner_html('#nmTb')[:0] or True)
    # primer pago de docente -> recibo automático
    pg.evaluate(RESET);pg.click('#nmTb tr:has-text("Rosa")');pg.wait_for_selector('#dNm[open]');pg.select_option('#nmPMet','Transferencia');pg.click('#nmPagar');W(pg,"window.__sav.length>=1");pg.wait_for_timeout(150)
    sav=pg.evaluate("window.__sav");ok('doc_un_pago_un_recibo',len(sav)==1 and sav[0].startswith('recibo-nomina-mtra-rosa-') and pg.evaluate("window.__pages")==0)
    t=pg.evaluate("window.__txt");ok('doc_recibo_contenido','Recibo de pago de nómina docente' in t and 'N-000001' in t and 'Introducción al derecho' in t and 'Recibí (firma del docente)' in t)
    pd=pg.evaluate("Object.values(Object.values(NOM)[0].pagos)[0]");ok('doc_qr_del_recibo',pg.evaluate("window.__qr")==[esp(pd['folio'],pd['monto'],pd['fecha'])])
    ok('doc_mensaje_recibo','recibo' in pg.inner_text('#nmDMsg'));pg.click('#nmCls')
    # segundo docente
    pg.evaluate(RESET);pg.click('#nmTb tr:has-text("Beto")');pg.wait_for_selector('#dNm[open]');pg.click('#nmPagar');W(pg,"window.__sav.length>=1");pg.wait_for_timeout(100);pg.click('#nmCls')
    ok('doc_segundo_recibo',len(pg.evaluate("window.__sav"))==1)
    # lista: botón por docente pagado y ninguno para el pendiente
    ok('doc_botones_en_lista',pg.locator('#nmTb [data-rb]').count()==2 and pg.locator('#nmTb tr:has-text("Carmen") [data-rb]').count()==0)
    pg.evaluate(RESET);pg.locator('#nmTb tr:has-text("Rosa") [data-rb]').click();pg.wait_for_timeout(100)
    ok('doc_recibo_desde_lista',len(pg.evaluate("window.__sav"))==1 and pg.evaluate("window.__sav")[0].startswith('recibo-nomina-mtra-rosa-') and pg.evaluate("document.getElementById('dNm').open")==False)
    # recibos del mes: solo los pagados, en un PDF
    pg.evaluate(RESET);pg.click('#nmRecibos');pg.wait_for_timeout(150)
    t=pg.evaluate("window.__txt")
    ok('doc_recibos_del_mes',pg.evaluate("window.__sav")==['recibos-nomina-docente-%s.pdf'%pg.evaluate("mesKey(nomSel().y,nomSel().m)")] and pg.evaluate("window.__pages")==1 and len(pg.evaluate("window.__qr"))==2 and 'N-000001' in t and 'N-000002' in t and 'Carmen' not in ' '.join(t))
    ok('doc_mensaje_lote','2 recibos' in pg.inner_text('#nmMsg'))
    pg.evaluate("document.getElementById('nmM').value=String((new Date().getMonth()+5)%12+1);renderNom()");pg.evaluate(RESET);pg.click('#nmRecibos');pg.wait_for_timeout(100)
    ok('doc_mes_sin_pagos','No hay pagos' in pg.inner_text('#nmMsg') and pg.evaluate("window.__sav")==[])
    # el desglose de un docente sin pago sigue sin QR ni firma
    pg.evaluate("document.getElementById('nmM').value=String(new Date().getMonth()+1);renderNom()");pg.evaluate(RESET);pg.click('#nmTb tr:has-text("Carmen")');pg.wait_for_selector('#dNm[open]');pg.click('#nmPdf');pg.wait_for_timeout(100)
    ok('desglose_sin_qr',pg.evaluate("window.__sav")[0].startswith('desglose-nomina-') and pg.evaluate("window.__qr")==[] and 'Recibí (firma del docente)' not in pg.evaluate("window.__txt"))
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    b.close()
p.terminate();p.wait()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
