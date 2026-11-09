import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3073;B='http://127.0.0.1:%d'%PORT;TOK='tok-na-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata3',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata3 && mkdir -p /tmp/nbdata3')
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
MOCK="""()=>{window.__txt=[];window.__qr=[];window.__sav=[];
 function PDF(){}
 ['setDrawColor','setLineWidth','setTextColor','setFont','line','addImage','addPage','setFontSize','setLineDashPattern','setFillColor','rect'].forEach(function(f){PDF.prototype[f]=function(){return this}});
 PDF.prototype.splitTextToSize=function(t){return [String(t)]};PDF.prototype.text=function(t){window.__txt.push(String(Array.isArray(t)?t[0]:t));return this};PDF.prototype.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};
 window.XLSX={utils:{book_new:function(){return {sheets:[]}},aoa_to_sheet:function(a){return {__aoa:a}},book_append_sheet:function(wb,ws,n){wb.sheets.push({n:n,ws:ws})},encode_range:function(){return 'A1:B2'},encode_cell:function(c){return 'R'+c.r+'C'+c.c}},write:function(wb){window.__wb=wb;return new Uint8Array([80,75])}};
 var q0=qrPDF;qrPDF=function(d,t,x,y,l){window.__qr.push(t);return q0(d,t,x,y,l)};
 saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};
}"""
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.on("response",lambda r:malos.append((r.status,r.url.replace(B,''))) if r.status>=400 and '/api/' in r.url else None)
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    pg.evaluate(MOCK)
    ok('tarjeta_en_panel',pg.is_visible('#mPag') and pg.is_hidden('#mNa') and 'nómina administrativa' in pg.inner_text('#mPag').lower())
    # --- empleados ---
    pg.evaluate("ir('na')");pg.click('#naT2');ok('pestana_empleados',pg.is_visible('#emNew') and pg.is_hidden('#naTb'))
    pg.click('#emNew');pg.click('#emSave');ok('emp_sin_nombre','nombre' in pg.inner_text('#emMsg'))
    pg.fill('#emNom','Ana Admin');pg.click('#emSave');ok('emp_sin_sueldo','sueldo' in pg.inner_text('#emMsg'))
    def emp(nombre,puesto,sal,per,met='Transferencia'):
        pg.evaluate("abreEmp(null)");pg.fill('#emNom',nombre);pg.fill('#emPue',puesto);pg.fill('#emSal',str(sal));pg.select_option('#emPer',per);pg.select_option('#emMet',met);pg.click('#emSave');W(pg,"Object.values(EMP).some(e=>e.nombre==='%s')"%nombre);pg.click('#emCan')
    pg.click('#emCan')
    emp('Ana Admin','Recepción',12000,'mensual','Efectivo');emp('Beto Admin','Intendencia',8000,'quincenal');emp('Carla Admin','Contabilidad',10000,'mensual');
    ok('empleados',pg.evaluate("Object.keys(EMP).length")==3 and 'Ana Admin' in pg.inner_text('#emTb'))
    pg.fill('#emBus','conta');ok('buscar_empleado','Carla' in pg.inner_text('#emTb') and 'Ana' not in pg.inner_text('#emTb'));pg.fill('#emBus','')
    # --- nómina mensual ---
    pg.click('#naT1');pg.evaluate("document.getElementById('naM').value=String(new Date().getMonth()+1);document.getElementById('naPer').value='M';renderNa()")
    ok('mensual_muestra_solo_mensuales','Ana Admin' in pg.inner_text('#naTb') and 'Carla' in pg.inner_text('#naTb') and 'Beto' not in pg.inner_text('#naTb'))
    ok('resumen_pendientes','2 empleados' in pg.inner_text('#naRes') and '$22,000.00' in pg.inner_text('#naRes'))
    fila=pg.locator('#naTb tr:has-text("Ana Admin")')
    fila.locator('[data-f=bonos]').fill('500');fila.locator('[data-f=desc]').fill('200');fila.locator('[data-f=nota]').fill('Bono por puntualidad');ok('neto_en_vivo','$12,300.00' in fila.inner_text())
    fila.locator('[data-f=nota]').press('Tab');W(pg,"Object.values(NAD).some(d=>Object.keys(d.aj||{}).length>0)")
    ok('ajustes_guardados',pg.evaluate("Object.values(NAD)[0].aj[Object.keys(Object.values(NAD)[0].aj)[0]].bonos")==500)
    # pagar a Ana (efectivo)
    pg.locator('#naTb tr:has-text("Ana Admin") [data-pg]').click();pg.wait_for_selector('#dNa[open]');ok('dialogo_pago','Ana Admin' in pg.inner_text('#naPInfo') and '$12,300.00' in pg.inner_text('#naPInfo'))
    ok('metodo_habitual',pg.evaluate("document.getElementById('naPMet').value")=='Efectivo')
    pg.click('#naPOk');W(pg,"Object.values(NAD).some(d=>Object.keys(d.pagos||{}).length===1)")
    ok('folio_na1',pg.evaluate("Object.values(Object.values(NAD)[0].pagos)[0].folio")=='NA-000001')
    ok('fila_pagada','Pagado' in pg.locator('#naTb tr:has-text("Ana Admin")').inner_text() and pg.locator('#naTb tr:has-text("Ana Admin") [data-f=bonos]').count()==0)
    # pagar todos los pendientes (Carla, transferencia)
    pg.click('#naPagarT');pg.wait_for_selector('#dNa[open]');pg.select_option('#naPMet','Transferencia');pg.fill('#naPRef','TR-77');pg.click('#naPOk');W(pg,"Object.values(NAD)[0]&&Object.keys(Object.values(NAD)[0].pagos).length===2")
    ok('pagar_todos','NA-000002' in json.dumps(pg.evaluate("Object.values(Object.values(NAD)[0].pagos).map(p=>p.folio)")) and pg.is_disabled('#naPagarT'))
    ok('mensaje_integracion','corte de caja' in pg.inner_text('#naMsg'))
    # --- quincenal ---
    pg.select_option('#naPer','Q1');ok('quincenal_mitad','$4,000.00' in pg.locator('#naTb tr:has-text("Beto")').inner_text() and 'Ana' not in pg.inner_text('#naTb'))
    pg.locator('#naTb tr:has-text("Beto") [data-pg]').click();pg.wait_for_selector('#dNa[open]');pg.click('#naPOk');W(pg,"Object.values(NAD)[0]&&Object.keys(Object.values(NAD)[0].pagos).length===3")
    pg.select_option('#naPer','Q2');ok('q2_pendiente','Pendiente' in pg.locator('#naTb tr:has-text("Beto")').inner_text())
    pg.select_option('#naPer','M')
    # neto en cero o negativo no se paga
    pg.evaluate("abreEmp(null)");pg.fill('#emNom','Dani Admin');pg.fill('#emSal','1000');pg.click('#emSave');W(pg,"Object.values(EMP).some(e=>e.nombre==='Dani Admin')");pg.click('#emCan');pg.evaluate("renderNa()")
    f2=pg.locator('#naTb tr:has-text("Dani")');f2.locator('[data-f=desc]').fill('1500');f2.locator('[data-f=nota]').press('Tab');pg.wait_for_timeout(300)
    pg.locator('#naTb tr:has-text("Dani") [data-pg]').click();ok('neto_negativo_no_paga','cero o negativo' in pg.inner_text('#naMsg') and pg.evaluate("document.getElementById('dNa').open")==False)
    # --- recibo y QR ---
    pg.evaluate("window.__txt=[];window.__qr=[]");mes=pg.evaluate("Object.keys(NAD)[0]");key=pg.evaluate("Object.keys(Object.values(NAD)[0].pagos)[0]")
    pg.evaluate("(a)=>reciboNaPDF(a[0],a[1])",[key,mes]);pg.wait_for_timeout(100)
    t=pg.evaluate("window.__txt").__str__()
    p1=pg.evaluate("Object.values(Object.values(NAD)[0].pagos).find(p=>p.folio==='NA-000001')")
    esp=pg.evaluate("(p)=>qrRecibo(p.folio,p.neto,p.fecha)",p1)
    ok('recibo_contenido','Recibo de pago de nómina administrativa' in t and 'NA-000001' in t and 'Ana Admin' in t and 'Recibí (firma del empleado)' in t and 'doce mil trescientos' in t.lower())
    ok('recibo_qr',pg.evaluate("window.__qr")==[esp] and 'Verifique este recibo' in t)
    # --- verificación por folio ---
    ok('busca_folio_na',pg.evaluate("(function(){var r=buscaRecibo('na-000001');return r&&r.origen==='Nómina administrativa'&&r.monto===12300&&r.nombre==='Ana Admin'})()"))
    pg.evaluate("verRecibo('NA-000001',chkRec('NA-000001',12300,Object.values(Object.values(NAD)[0].pagos).find(p=>p.folio==='NA-000001').fecha))");ok('verifica_autentico','Recibo auténtico' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close()")
    # --- corte de caja ---
    pg.evaluate("ir('pagos');vista('ga')");pg.evaluate("document.getElementById('cFec').value=today();renderCaja()")
    D=pg.evaluate("(function(){var d=datosCorte(today());return {tg:d.tg,efg:d.efg,n:d.E.length,esp:d.esp,cats:d.E.map(x=>x.cat).join(','),tr:d.M['Transferencia']&&d.M['Transferencia'].g}})()")
    ok('corte_gastos_nomina_admin',D['n']==3 and D['tg']==26300 and D['efg']==12300 and set(D['cats'].split(','))=={'Nómina administrativa'} and D['tr']==14000)   # 12300 + 10000 + 4000
    cg=pg.inner_html('#cGas');ok('corte_fila_sin_quitar','Nómina administrativa' in cg and 'data-gd=' not in cg)
    # --- ingresos para el estado de cuenta ---
    pg.evaluate("""async()=>{abrirAlumno(null);$("alMat").value="1001";$("alNom").value="Ana Alumna";$("alPlan").value="Derecho";$("alIng").value="2026";$("alNue").checked=true;await $("alOk").onclick();
      var s=S.find(x=>x.nombre==='Ana Alumna');openSt(s.id);$("pMon").value="800";$("pMet").value="Efectivo";$("pFec").value=today();$("pCon").value="";await $("sAdd").onclick();
      $("pMon").value="1300";$("pMet").value="Transferencia";$("pRef").value="TRX";await $("sAdd").onclick()}""")
    W(pg,"S.find(s=>s.nombre==='Ana Alumna').pagos.length===2")
    pg.evaluate("""async()=>{var s=S.find(x=>x.nombre==='Ana Alumna');openCf(s.id,s.pagos[1].id);$("cfFec").value=today();await $("cfOk").onclick();$("dSt").close()}""")
    W(pg,"paid(S.find(s=>s.nombre==='Ana Alumna'))===2100")
    # un gasto normal
    pg.evaluate("""async()=>{$("gFec").value=today();$("gCon").value="Papelería";$("gMon").value="300";$("gMet").value="Efectivo";await $("gAdd").onclick()}""");W(pg,"gastosTodos().some(x=>x.concepto==='Papelería')")
    # titulación y 286 (ingresos extra)
    pg.evaluate("""async()=>{var t={id:'t1',num:'T-000001',nombre:'Marco',apPat:'López',apMat:'',grado:'licenciatura',costo:20000,abonos:[{id:'a1',folio:'RT-000001',fecha:today(),monto:5000,metodo:'Efectivo'}],docs:{}};await DBH.doc('titulaciones/t1').set(t);TIT_.t1=t;
      var q={id:'q1',num:'B286-000001',nombre:'Bea',apPat:'Mena',apMat:'',pagos:[{id:'g1',folio:'R286-000001',fecha:today(),monto:1000,metodo:'Efectivo'}],docs:{},tram:{}};await DBH.doc('acuerdo286/q1').set(q);A2.q1=q}""")
    W(pg,"TIT_.t1&&A2.q1")
    pg.evaluate("vista('ef')");pg.wait_for_selector('#efRes b')
    E=pg.evaluate("(function(){var d=efDatos();return {ing:d.ing.total,egr:d.egr.total,neto:d.neto,cats:Object.keys(d.ing.cats).sort().map(k=>k+':'+d.ing.cats[k].m).join('|'),sumcats:Object.values(d.ing.cats).reduce((a,c)=>a+c.m,0),egrcats:Object.keys(d.egr.cats).sort().map(k=>k+':'+d.egr.cats[k].m).join('|'),met:JSON.stringify(d.mets)}})()")
    # ingresos: 800 inscripción (nuevo ingreso) + 1300 (colegiatura) + 5000 titulación + 1000 acuerdo 286 = 8100
    ok('ef_ingresos',E['ing']==8100 and E['sumcats']==8100)
    ok('ef_categorias','Inscripciones:800' in E['cats'] and 'Colegiaturas:1300' in E['cats'] and 'Titulaciones por experiencia laboral:5000' in E['cats'] and 'Acuerdo 286:1000' in E['cats'])
    print('EGRCATS:',E['egrcats']);ok('ef_egresos',E['egr']==26600 and 'Nómina administrativa:26300' in E['egrcats'] and E['egrcats'].count(':')==2)   # 26300 nómina + 300 gasto
    ok('ef_resultado',E['neto']==8100-26600)
    m=json.loads(E['met']);ok('ef_por_metodo',m['Efectivo']['i']==6800 and m['Efectivo']['g']==12600 and m['Transferencia']['i']==1300 and m['Transferencia']['g']==14000)
    ok('ef_pantalla','$8,100.00' in pg.inner_text('#efRes') and '$26,600.00' in pg.inner_text('#efRes') and 'Nómina administrativa' in pg.inner_text('#efEgr') and 'Nómina administrativa' in pg.inner_text('#efDet'))
    pg.uncheck('#efExt');E2=pg.evaluate("efDatos().ing.total");ok('ef_sin_extras',E2==2100);pg.check('#efExt')
    pg.select_option('#efM','0');ok('ef_anual',pg.evaluate("efDatos().ing.total")==8100);pg.evaluate("document.getElementById('efM').value=String(new Date().getMonth()+1);renderEf()")
    pg.select_option('#efM','1' if pg.evaluate("new Date().getMonth()")!=0 else '2');ok('ef_otro_mes_vacio',pg.evaluate("efDatos().ing.total")==0 and pg.evaluate("efDatos().egr.total")==0);pg.evaluate("document.getElementById('efM').value=String(new Date().getMonth()+1);renderEf()")
    # PDF y Excel
    pg.evaluate("window.__txt=[];window.__sav=[]");pg.click('#efPdf');pg.wait_for_timeout(150)
    tx=json.dumps(pg.evaluate("window.__txt"),ensure_ascii=False);ok('ef_pdf','Estado de cuenta final' in tx and 'Total de ingresos' in tx and '$8,100.00' in tx and 'Nómina administrativa' in tx and 'Resultado del periodo' in tx and pg.evaluate("window.__sav")[0].startswith('estado-de-cuenta-final-'))
    pg.click('#efXls');pg.wait_for_timeout(150);ok('ef_excel',pg.evaluate("window.__wb.sheets.map(s=>s.n).join(',')")=='Resumen,Ingresos,Egresos' and pg.evaluate("window.__wb.sheets[1].ws.__aoa.length")==5)   # 4 movimientos + encabezado
    pg.evaluate("window.__sav=[]");pg.evaluate("ir('na')");pg.click('#naXls');pg.wait_for_timeout(100);ok('na_excel',pg.evaluate("window.__sav")[0].startswith('nomina-administrativa-') and pg.evaluate("window.__wb.sheets[0].n")=='Nómina administrativa' and pg.evaluate("window.__wb.sheets[0].ws.__aoa.length")==5)   # 3 filas (Ana, Carla, Dani) + total + encabezado
    # --- anular un pago ---
    pg.evaluate("ir('na')");pg.evaluate("document.getElementById('naPer').value='M';renderNa()")
    pg.locator('#naTb tr:has-text("Ana Admin") [data-an]').click();ok('anular_pide_confirmar','Confirmar anulación' in pg.locator('#naTb tr:has-text("Ana Admin")').inner_text())
    pg.locator('#naTb tr:has-text("Ana Admin") [data-an]').click();W(pg,"Object.keys(Object.values(NAD)[0].pagos).length===2");ok('anulado','anulado' in pg.inner_text('#naMsg') and 'Pendiente' in pg.locator('#naTb tr:has-text("Ana Admin")').inner_text())
    print('TRAS ANULAR:',pg.evaluate("datosCorte(today()).tg"),pg.evaluate("efDatos().egr.total"));ok('corte_tras_anular',pg.evaluate("datosCorte(today()).tg")==14300 and pg.evaluate("efDatos().egr.total")==14300)
    # el folio no se reutiliza
    pg.locator('#naTb tr:has-text("Ana Admin") [data-pg]').click();pg.click('#naPOk');W(pg,"Object.keys(Object.values(NAD)[0].pagos).length===3");ok('folio_no_reutilizado',pg.evaluate("Object.values(Object.values(NAD)[0].pagos).map(p=>p.folio).sort().join(',')")=='NA-000002,NA-000003,NA-000004')
    # --- baja y eliminación de empleados ---
    pg.click('#naT2');pg.click('#emTb tr:has-text("Ana Admin")');pg.click('#emDel');ok('no_elimina_con_pagos','ya tiene pagos' in pg.inner_text('#emMsg'))
    pg.uncheck('#emAct');pg.click('#emSave');W(pg,"Object.values(EMP).find(e=>e.nombre==='Ana Admin').activo===false");pg.click('#emCan')
    ok('baja_marcada','Baja' in pg.locator('#emTb tr:has-text("Ana Admin")').inner_text())
    pg.click('#naT1');ok('baja_con_pago_sigue_visible','Ana Admin' in pg.inner_text('#naTb'))
    pg.click('#naT2');pg.click('#emTb tr:has-text("Dani Admin")');pg.click('#emDel');ok('elimina_paso1','Confirmar eliminación' in pg.inner_text('#emDel'));pg.click('#emDel');W(pg,"!Object.values(EMP).some(e=>e.nombre==='Dani Admin')");ok('elimina_sin_pagos',True)
    # --- respaldo y permisos de la nube ---
    bk=pg.evaluate("async()=>{var d=await armaRespaldo(function(){});return {col:Object.keys(d.colecciones.empleados).length,na:Object.keys(d.colecciones.nomina_admin).length,folio:!!d.documentos['meta/folioNA']}}")
    ok('respaldo_incluye',bk['col']==3 and bk['na']==1 and bk['folio'])
    ck=ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja Uno','rol':'caja','clave':'clave-caja-1'}),headers={'Content-Type':'application/json','x-lafragua':'1'});ok('crea_caja',ck.status==200)
    c2=pw.chromium.launch().new_context();lg=c2.request.post(B+'/api/login',data=json.dumps({'u':'caja1','clave':'clave-caja-1'}),headers={'Content-Type':'application/json','x-lafragua':'1'})
    rr=c2.request.get(B+'/api/col/empleados');ok('caja_no_lee_empleados',rr.json()['docs']==[])
    rr=c2.request.get(B+'/api/col/nomina_admin');ok('caja_no_lee_nomina_admin',rr.json()['docs']==[])
    rr=c2.request.put(B+'/api/doc/nomina_admin/2026-10',data=json.dumps({'x':1}),headers={'Content-Type':'application/json','x-lafragua':'1'});ok('caja_no_escribe_nomina_admin',rr.status==403)
    rr=c2.request.put(B+'/api/doc/empleados/zz',data=json.dumps({'x':1}),headers={'Content-Type':'application/json','x-lafragua':'1'});ok('caja_no_escribe_empleados',rr.status==403)
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    ok('sin_errores_de_red',all(c in (403,) for c,u in malos if 'empleados' in u or 'nomina_admin' in u) and not [m for m in malos if 'empleados' not in m[1] and 'nomina_admin' not in m[1] and '/api/usuarios' not in m[1]])
    if [m for m in malos if 'empleados' not in m[1] and 'nomina_admin' not in m[1]]:print('RED:',[m for m in malos][:6])
    b.close()
p.terminate();p.wait()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
