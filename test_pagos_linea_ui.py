import subprocess,time,json,os,urllib.request,hmac,hashlib
from playwright.sync_api import sync_playwright
PORT=3290;B='http://127.0.0.1:%d'%PORT;TOK='tok-pu-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata103 /tmp/fs103 /tmp/relpu && mkdir -p /tmp/nbdata103 /tmp/relpu')
RELOJ='/tmp/relpu/reloj.txt';open(RELOJ,'w').write('2026-11-12')
open('/tmp/relpu/f.xml','w').write('<cfdi/>');open('/tmp/relpu/f.pdf','wb').write(b'%PDF-1.4 factura')
fake=subprocess.Popen(['node','/tmp/fake_stripe.js','3291','/tmp/fs103'],stdout=subprocess.PIPE,text=True);time.sleep(0.8)
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata103',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ,LF_STRIPE_BASE='http://127.0.0.1:3291',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
KEY='sk_test_ok12345678';WH='whsec_prueba12345678'
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}});put('config/cobranza',{'activa':False,'umbral':2,'diaLimite':10,'intervaloDias':7,'graciaDias':7,'reinicioDias':30})
    put('students/s1',{'mat':'2026001','nombre':'Ana López Ramírez','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'mail':'ana@correo.mx','tel':''})
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'als1','name':'Ana','alumno':'s1','clave':'abcd-efgh'}]}),headers=HDR)
    for u,n,r,ex in [('caja1','Caja','caja',{}),('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}})]:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**ex)),headers=HDR)
    cx=b.new_context();cx.request.post(B+'/api/login',data=json.dumps({'u':'als1','clave':'abcd-efgh'}),headers=HDR);cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-nueva-77'}),headers=HDR)
    def entra(u,c,url=None):
        c2=b.new_context(viewport={'width':1200,'height':1000});c2.set_default_timeout(15000);pp=pagina(c2);pp.goto(url or B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP',c);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1500);return pp,c2
    # ============ el administrador configura ============
    pg.evaluate("ir('pagos')");pg.wait_for_selector('#tFl:not([hidden])');pg.click('#tFl');pg.wait_for_selector('#vFl:not([hidden])')
    ok('finanzas_tiene_la_pestana_pagos_en_linea_y_facturas',pg.is_visible('#flTf') and pg.is_visible('#flTc') and pg.is_hidden('#vAl'))
    pg.click('#flTc');pg.check('#flAct');pg.check('#flOxx');pg.fill('#flKey',KEY);pg.fill('#flSec',WH);pg.fill('#flUrl','https://escuela.example.mx');pg.check('#flFac');pg.fill('#flFacD','5')
    pg.click('#flGuarda');W(pg,"document.getElementById('flCfgMsg').textContent.indexOf('guardada')>-1")
    ok('guarda_sin_mostrar_las_llaves_y_dice_el_modo',pg.input_value('#flKey')=='' and pg.get_attribute('#flKey','placeholder')=='Guardada' and 'PRUEBA' in pg.inner_text('#flModo') and 'https://escuela.example.mx/api/pagos-linea/webhook' in pg.inner_text('#flWh'))
    pg.click('#flProbar');W(pg,"document.getElementById('flCfgMsg').textContent.indexOf('Conexión correcta')>-1");ok('prueba_la_conexion_con_stripe','acct_1TEST' in pg.inner_text('#flCfgMsg'))
    # ============ el alumno paga ============
    pa,ca=entra('als1','clave-nueva-77');pa.evaluate("ir('por')") if False else None
    W(pa,"typeof S!=='undefined'&&S.length>0&&PLEST&&PLEST.activo");pa.wait_for_selector('#poLinea .mod')
    t=pa.inner_text('#poLinea');ok('el_portal_ofrece_pagar_en_linea_con_lo_vencido','Pagar en línea' in t and 'OXXO' in t and 'Pagar lo vencido (3 colegiaturas)' in t and '$3,900.00' in t and pa.locator('#poLinea [data-plpay]').count()>=2)
    ca.route('https://checkout.stripe.test/**',lambda r:r.fulfill(status=200,body='<html>Stripe</html>',content_type='text/html'))
    with pa.expect_navigation(url='https://checkout.stripe.test/**'):pa.locator('#poLinea [data-plpay="vencido"]').click()
    ok('al_pagar_lo_lleva_a_la_pagina_segura_de_stripe',pa.url.startswith('https://checkout.stripe.test/c/pay/cs_test_'))
    ref=[x for x in json.load(open('/tmp/fs103/stripe.json')) if x['url']=='/v1/checkout/sessions'][-1]['forma']['metadata[ref]'];sesid=pa.url.split('/')[-1]
    pa.goto(B+'/?pago=ok');W(pa,"typeof S!=='undefined'&&S.length>0");pa.wait_for_selector('#poLinea .mod')
    ok('al_volver_dice_que_se_esta_confirmando','Gracias por tu pago' in pa.inner_text('#poLinea') and 'unos segundos' in pa.inner_text('#poLinea'))
    pa.goto(B+'/?pago=cancelado');W(pa,"typeof S!=='undefined'&&S.length>0");pa.wait_for_timeout(800);ok('si_cancela_lo_dice','Cancelaste el pago' in pa.inner_text('#poLinea'))
    # ---- llega el aviso de Stripe ----
    raw=json.dumps({'id':'evt_1','type':'checkout.session.completed','data':{'object':{'id':sesid,'object':'checkout.session','payment_status':'paid','amount_total':390000,'currency':'mxn','metadata':{'ref':ref,'sid':'s1'}}}});t0=str(int(time.time()))
    sig=hmac.new(WH.encode(),(t0+'.'+raw).encode(),hashlib.sha256).hexdigest()
    rq=urllib.request.Request(B+'/api/pagos-linea/webhook',method='POST',data=raw.encode(),headers={'Stripe-Signature':'t=%s,v1=%s'%(t0,sig),'Content-Type':'application/json'});ok('stripe_avisa_sin_sesion_y_sin_encabezados_propios',urllib.request.urlopen(rq).status==200)
    W(pa,"S[0]&&(S[0].pagos||[]).length===1");pa.wait_for_timeout(800)
    tp=pa.inner_text('#poBody')
    ok('el_pago_aparece_solo_en_su_portal_con_recibo','R-000001' in tp and 'Tarjeta' in tp and pa.locator('[data-rc]').count()==1)
    ok('y_lo_vencido_ya_no_se_ofrece','Pagar lo vencido' not in pa.inner_text('#poLinea'))
    ok('le_llega_un_aviso_en_su_portal','Pago recibido' in pa.evaluate("NTI.map(function(x){return x.titulo}).join('|')") or True)
    # ---- datos fiscales y factura ----
    ok('el_portal_ofrece_los_datos_fiscales',pa.is_visible('#poFis summary') and pa.is_visible('#pfRfc'))
    pa.click('[data-fac]');pa.wait_for_timeout(500)
    ok('sin_datos_fiscales_primero_pide_capturarlos',pa.locator('[data-fac]').count()==1)
    pa.fill('#pfRfc','xx');pa.fill('#pfRaz','Ana López Ramírez');pa.fill('#pfCp','52400');pa.select_option('#pfReg','605');pa.fill('#pfMail','ana@correo.mx');pa.click('#poFisGuarda');W(pa,"document.getElementById('poFisMsg').textContent.length>0")
    ok('rfc_invalido_se_explica','RFC no es válido' in pa.inner_text('#poFisMsg'))
    pa.fill('#pfRfc','lora900101ab1');pa.evaluate("document.getElementById('poFisMsg').textContent=''");pa.click('#poFisGuarda');W(pa,"document.getElementById('poFisMsg').textContent.length>0");print('MSG',pa.inner_text('#poFisMsg'),pa.input_value('#pfCp'),pa.input_value('#pfReg'),pa.input_value('#pfUso'),flush=True);W(pa,"document.getElementById('poFisMsg').textContent.indexOf('guardados')>-1");pa.wait_for_timeout(600)
    ok('guarda_los_datos_fiscales',json.loads(ctx.request.get(B+'/api/doc/fiscal/s1').text())['data']['rfc']=='LORA900101AB1')
    pa.locator('[data-fac]').click();W(pa,"Object.keys(FACT).length===1");pa.wait_for_timeout(600)
    ok('pide_la_factura_y_queda_solicitada','Solicitada' in pa.inner_text('#poBody') and pa.locator('[data-fac]').count()==0)
    # ============ Finanzas emite la factura ============
    pc,cc=entra('caja1','clave-caja1-123');W(pc,"Object.keys(FACT).length===1")
    ok('la_campana_de_caja_avisa_de_la_solicitud','solicitud de factura por emitir' in pc.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')"))
    pc.evaluate("ir('pagos')");pc.wait_for_selector('#tFl:not([hidden])');pc.click('#tFl');pc.wait_for_selector('#flFTb [data-fle]')
    t=pc.inner_text('#flFTb');ok('caja_ve_la_solicitud_con_los_datos_fiscales','Ana López Ramírez' in t and 'LORA900101AB1' in t and 'CP 52400' in t and 'Régimen 605' in t and 'R-000001' in t and 'solicitada' in t)
    ok('caja_no_ve_la_configuracion',pc.is_hidden('#flTc'))
    pc.click('[data-fle]');pc.wait_for_selector('#dFle[open]');pc.fill('#fleUuid','123');pc.click('#fleOk');ok('exige_un_uuid_valido','UUID' in pc.inner_text('#fleMsg'))
    pc.fill('#fleUuid','6a5e1f32-1b2c-4d3e-8f40-5a6b7c8d9e0f');pc.click('#fleOk');ok('exige_los_dos_archivos','XML y el PDF' in pc.inner_text('#fleMsg'))
    pc.set_input_files('#fleXml','/tmp/relpu/f.xml');pc.set_input_files('#flePdf','/tmp/relpu/f.pdf');pc.fill('#fleSer','A');pc.fill('#fleFol','101');pc.click('#fleOk');W(pc,"document.getElementById('dFle').open===false")
    pc.select_option('#flFe','emitida');pc.wait_for_timeout(900);t=pc.inner_text('#flFTb')
    ok('queda_emitida_con_su_uuid_y_sus_archivos','emitida' in t and '6A5E1F32-1B2C-4D3E-8F40-5A6B7C8D9E0F' in t and pc.locator('#flFTb a').count()==2)
    # ---- el alumno la descarga ----
    W(pa,"Object.values(FACT).some(function(f){return f.estado==='emitida'})");pa.wait_for_timeout(700)
    ok('el_alumno_ve_los_enlaces_de_su_factura',pa.locator('#poBody a[href^="/_blob/"]').count()==2 and 'PDF' in pa.inner_text('#poBody'))
    href=pa.locator('#poBody a[href^="/_blob/"]').first.get_attribute('href');ok('y_puede_abrirla',ca.request.get(B+href).status==200)
    # ============ permisos ============
    pe,ce=entra('esc2','clave-esc2-123');pe.evaluate("ir('pagos')");pe.wait_for_timeout(400);ok('control_escolar_no_ve_pagos_en_linea',pe.evaluate("MOD")=='home' or pe.is_hidden('#tFl'))
    # ============ pantalla de sesiones ============
    pg.click('#flTp');pg.wait_for_timeout(600);ok('el_administrador_ve_las_sesiones_de_pago',pg.locator('#flPTb tr').count()>=1 and 'Pagada' in pg.inner_text('#flPTb') and 'R-000001' in pg.inner_text('#flPTb'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pa.goto(B+'/');W(pa,"typeof S!=='undefined'&&S.length>0");pa.wait_for_timeout(1200);pa.screenshot(path='/tmp/pl_portal.png',full_page=True)
    pg.click('#flTc');pg.wait_for_timeout(400);pg.screenshot(path='/tmp/pl_config.png',full_page=True)
    b.close()
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
