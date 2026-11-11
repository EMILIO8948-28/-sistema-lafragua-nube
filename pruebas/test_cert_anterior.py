import subprocess,time,json,os,urllib.request,zipfile
from playwright.sync_api import sync_playwright
PORT=3440;B='http://127.0.0.1:%d'%PORT;TOK='tok-ca-123'
os.system('rm -rf /tmp/nbdata116 /tmp/ca && mkdir -p /tmp/nbdata116 /tmp/ca')
open('/tmp/ca/cert.pdf','wb').write(b'%PDF-1.4 certificado escaneado')
with zipfile.ZipFile('/tmp/ca/esc.zip','w') as z:
    z.writestr('Marcos Ibarra Salgado.pdf',b'%PDF-1.4 a');z.writestr('Laura Pérez Núñez.pdf',b'%PDF-1.4 b');z.writestr('Laura Pérez Núñez_parcial.pdf',b'%PDF-1.4 c');z.writestr('B286-000001.pdf',b'%PDF-1.4 d');z.writestr('desconocido.pdf',b'%PDF-1.4 e');z.writestr('notas.txt',b'hola');z.writestr('B286-000099.pdf',b'%PDF-1.4 f')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata116',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000',LF_BAJAS_ARRANQUE_MS='600000')
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
HDR={'Content-Type':'application/json','x-lafragua':'1'}
MOCK="""()=>{window.__txt=[];window.__sav=[];
 function mk(){return new Proxy({},{get:function(o,k){
   if(k==='text')return function(s){window.__txt.push(String(Array.isArray(s)?s.join(' '):s));return me};
   if(k==='splitTextToSize')return function(s){return [String(s)]};if(k==='getTextWidth')return function(){return 10};
   if(k==='output')return function(){return new ArrayBuffer(8)};
   return function(){return me}}})}
 var me=null;function PDF(){me=mk();return me}
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push([n,typeof b==='string'?b:'']);return Promise.resolve()};0}"""
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1150,'height':950});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    up=ctx.request.post(B+'/api/archivo',data=open('/tmp/ca/cert.pdf','rb').read(),headers={'x-lafragua':'1','x-nombre':'certificado-ana.pdf','Content-Type':'application/pdf'}).json()['id']
    for i,(nom,pat,mat,sx,cert) in enumerate([('Ana','López','Ramírez','Femenino',{'id':up,'name':'certificado-ana.pdf','size':30}),('Beto','Mena','Ruiz','Masculino',None)],1):
        put('acuerdo286/a%d'%i,{'id':'a%d'%i,'num':'B286-%06d'%i,'fecha':'2026-01-10','nombre':nom,'apPat':pat,'apMat':mat,'sexo':sx,'tel':'72600000%d'%i,'docs':{},'tram':{},'pagos':[],'cert':cert,'enviado':True})
    for u,n,r,m in [('a2e','Editor 286','personalizado',{'a286':'editar'}),('a2v','Lector 286','personalizado',{'a286':'ver'})]:
        assert ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':u,'name':n,'rol':r,'modulos':m,'clave':'clave-%s-123'%u}),headers=HDR).status==200
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(A2).length===2");pg.evaluate(MOCK)
    pg.evaluate("ir('a2')");pg.wait_for_selector('#a2Tabs');pg.click('#a2Tabs [data-a2t="C"]');pg.wait_for_selector('#a2PanC:not([hidden])')
    n_ins=len(ctx.request.get(B+'/api/col/acuerdo286').json()['docs']);n_led=len(ctx.request.get(B+'/api/col/ledger').json()['docs'])
    # ============ con inscripción: sigue igual ============
    pg.click('#rgNew');pg.wait_for_selector('#dRg[open]')
    ok('por_defecto_pide_la_inscripcion',pg.is_checked('#rgModoI') and pg.is_visible('#rgAlW') and pg.is_hidden('#rgAnW') and pg.is_visible('#rgModoW'))
    pg.click('#rgOk');ok('sin_inscripcion_elegida_la_pide','Elige la inscripción' in pg.inner_text('#rgMsg'))
    pg.fill('#rgAl','B286-000001 — Ana López Ramírez');pg.fill('#rgDf','CB-2026-0457');pg.click('#rgOk');W(pg,"Object.keys(RGD).length===1")
    d1=list(json.loads(pg.evaluate("JSON.stringify(RGD)")).values())[0]
    ok('con_inscripcion_se_guarda_en_base_a_ella',d1['sid']=='a1' and d1['mat']=='B286-000001' and d1['nombre']=='Ana López Ramírez' and d1['plan']=='Bachillerato por Acuerdo 286' and not d1.get('anterior') and d1['archivo']['id']==up)
    # ============ certificado de tiempo atrás ============
    pg.click('#rgNew');pg.check('#rgModoA')
    ok('al_elegir_certificado_anterior_ya_no_pide_inscripcion',pg.is_hidden('#rgAlW') and pg.is_visible('#rgAnW') and 'no se pide inscripción ni se genera ningún cobro' in pg.inner_text('#rgAnW') and pg.is_hidden('#rgUsaW'))
    pg.click('#rgOk');ok('pide_el_nombre_del_titular','nombre completo del titular' in pg.inner_text('#rgMsg'))
    pg.fill('#rgAnN','Marcos');pg.click('#rgOk');ok('un_solo_nombre_no_basta','nombre completo del titular' in pg.inner_text('#rgMsg'))
    pg.fill('#rgAnN','Marcos Ibarra Salgado');pg.fill('#rgAnC','XX123');pg.click('#rgOk');ok('valida_la_curp','CURP no tiene un formato válido' in pg.inner_text('#rgMsg'))
    pg.fill('#rgAnC','iasm800101hmcblr09');pg.fill('#rgAnT','7221234567');pg.select_option('#rgAnS','Masculino');pg.select_option('#rgTp','Certificado de bachillerato');pg.fill('#rgDf','CB-2008-0099');pg.fill('#rgFx','2008-06-30');pg.fill('#rgUb','Archivero 1, cajón 4');pg.set_input_files('#rgFile','/tmp/ca/cert.pdf')
    pg.click('#rgOk');W(pg,"Object.keys(RGD).length===2")
    a=[x for x in json.loads(pg.evaluate("JSON.stringify(Object.values(RGD))")) if x.get('anterior')][0]
    ok('se_guarda_sin_inscripcion_con_los_datos_del_titular',a['sid']=='' and a['anterior'] is True and a['nombre']=='Marcos Ibarra Salgado' and a['curp']=='IASM800101HMCBLR09' and a['tel']=='7221234567' and a['sexo']=='Masculino' and a['mat']=='Sin inscripción' and a['docFolio']=='CB-2008-0099' and a['fechaExp']=='2008-06-30' and a['ubic']=='Archivero 1, cajón 4' and a['estado']=='resguardo' and a['num']=='RC-000002')
    ok('con_su_escaneo_y_su_historial',a['archivo']['name']=='cert.pdf' and 'certificado anterior, sin inscripción' in a['mov'][0]['a'])
    ok('no_crea_inscripcion_ni_cobros',len(ctx.request.get(B+'/api/col/acuerdo286').json()['docs'])==n_ins and len(ctx.request.get(B+'/api/col/ledger').json()['docs'])==n_led)
    t=pg.inner_text('#rgTb');ok('aparece_en_la_lista_como_sin_inscripcion','Marcos Ibarra Salgado' in t and 'Sin inscripción' in t and 'RC-000002' in t and pg.inner_text('#rgC1')=='2' and pg.inner_text('#rgC3')=='2')
    pg.select_option('#rgEst','anterior');pg.wait_for_timeout(200);ok('se_filtran_los_certificados_anteriores',pg.locator('#rgTb tr').count()==1 and 'Marcos' in pg.inner_text('#rgTb'));pg.select_option('#rgEst','')
    pg.fill('#rgQ','iasm800101');pg.wait_for_timeout(200);ok('se_busca_por_curp',pg.locator('#rgTb tr').count()==1);pg.fill('#rgQ','')
    pg.click('#rgNew');pg.check('#rgModoA');pg.fill('#rgAnN','marcos  ibarra salgado');pg.select_option('#rgTp','Certificado de bachillerato');pg.fill('#rgDf','CB-2008-0099');pg.click('#rgOk');ok('no_repite_el_mismo_certificado_anterior','Ya hay un certificado anterior de esa persona' in pg.inner_text('#rgMsg'));pg.click('#rgCan')
    # editar uno anterior
    pg.locator('#rgTb tr:has-text("RC-000002") [data-rv]').click();pg.wait_for_selector('#dRg[open]')
    ok('al_editar_no_se_cambia_el_tipo_de_registro_y_se_ven_sus_datos',pg.is_hidden('#rgAlW') and pg.is_visible('#rgAnW') and pg.input_value('#rgAnN')=='Marcos Ibarra Salgado' and pg.input_value('#rgAnC')=='IASM800101HMCBLR09' and pg.evaluate("getComputedStyle(document.getElementById('rgModoW')).display")=='none')
    pg.fill('#rgAnN','Marcos Ibarra Salgado Jr');pg.fill('#rgNt','Se corrigió el nombre.');pg.click('#rgOk');W(pg,"Object.values(RGD).some(function(x){return x.nombre==='Marcos Ibarra Salgado Jr'})");ok('y_se_corrigen_sus_datos',True)
    pg.locator('#rgTb tr:has-text("RC-000002") [data-rv]').click();pg.fill('#rgAnN','Marcos Ibarra Salgado');pg.click('#rgOk');W(pg,"Object.values(RGD).some(function(x){return x.nombre==='Marcos Ibarra Salgado'})")
    # constancia y acta
    pg.locator('#rgTb tr:has-text("RC-000002") [data-rr]').click();pg.wait_for_timeout(300);tx=' | '.join(pg.evaluate("window.__txt"))
    ok('la_constancia_no_menciona_folio_de_inscripcion','MARCOS IBARRA SALGADO' in tx and 'certificado de tiempo atrás, sin inscripción en la plataforma' in tx and 'folio de inscripción' not in tx and 'el C.' in tx)
    pg.locator('#rgTb tr:has-text("RC-000002") [data-re]').click();pg.wait_for_selector('#dRgE[open]');pg.fill('#rgENm','INE-123');pg.evaluate("window.__txt=[];window.__sav=[]");pg.click('#rgEOk');W(pg,"Object.values(RGD).some(function(x){return x.anterior&&x.estado==='entregado'})");pg.wait_for_timeout(300);tx=' | '.join(pg.evaluate("window.__txt"))
    ok('y_el_acta_de_entrega_tambien',('Origen' in tx) and 'Certificado de tiempo atrás, sin inscripción' in tx and 'MARCOS IBARRA SALGADO' in tx)
    # exportar
    pg.evaluate("window.__sav=[]");pg.click('#rgCsv');pg.wait_for_timeout(300);csv=pg.evaluate("window.__sav")[0][1]
    ok('el_csv_distingue_los_anteriores','con_inscripcion,curp,telefono' in csv and 'RC-000002,Sin inscripción,Marcos Ibarra Salgado' in csv and ',No,IASM800101HMCBLR09,7221234567' in csv and ',Sí,,' in csv)
    # ============ carga por ZIP ============
    pg.click('#rgZip');pg.wait_for_selector('#dRgZ[open]');pg.set_input_files('#rgZFile','/tmp/ca/esc.zip');pg.wait_for_selector('#rgZRes .mod');pg.wait_for_timeout(500);rs=pg.inner_text('#rgZRes')
    ok('el_zip_reconoce_los_certificados_anteriores_antes_de_cargar','Crear certificado de tiempo atrás de Laura Pérez Núñez (sin inscripción)' in rs and 'Marcos Ibarra Salgado' in rs and 'nombre completo' in rs and 'solo se cargan PDF, JPG o PNG' in rs)
    ok('un_folio_b286_que_no_existe_no_se_toma_como_nombre','B286-000099.pdf' in rs and 'ese folio no existe' in rs)
    ok('y_distingue_el_tipo_por_el_nombre','Crear certificado de tiempo atrás de Laura Pérez Núñez' in rs and rs.count('Crear certificado de tiempo atrás')==3)
    pg.click('#rgZOk');W(pg,"document.getElementById('rgZMsg').textContent.indexOf('Listo')>-1",60);zz=pg.inner_text('#rgZMsg')
    L=[x for x in json.loads(pg.evaluate("JSON.stringify(Object.values(RGD))")) if x.get('anterior')]
    ok('crea_los_registros_nuevos_sin_inscripcion','Listo: 3 escaneos cargados (3 registros nuevos)' in zz and sorted((x['nombre'],x['tipo']) for x in L if x['nombre'].startswith('Laura'))==[('Laura Pérez Núñez','Certificado de bachillerato'),('Laura Pérez Núñez','Certificado parcial')] and all(x['sid']=='' and x['archivo'] for x in L))
    ok('un_archivo_con_folio_de_inscripcion_se_adjunta_a_su_inscripcion',any(x['sid']=='a1' and x['archivo'] for x in json.loads(pg.evaluate("JSON.stringify(Object.values(RGD))"))))
    # el mismo titular y documento ya en resguardo se omite
    pg.evaluate("document.getElementById('dRgZ').open&&document.getElementById('dRgZ').close()");pg.click('#rgZip');pg.wait_for_selector('#dRgZ[open]')
    with zipfile.ZipFile('/tmp/ca/esc3.zip','w') as z:z.writestr('Laura Pérez Núñez.pdf',b'%PDF-1.4 otra vez')
    pg.set_input_files('#rgZFile','/tmp/ca/esc3.zip');pg.wait_for_selector('#rgZRes .mod');ok('si_ya_esta_en_resguardo_no_se_duplica','ese titular ya tiene ese certificado anterior en resguardo' in pg.inner_text('#rgZRes'));pg.evaluate("document.getElementById('dRgZ').close()")
    # sin marcar la opción: no se crean anteriores
    pg.evaluate("document.getElementById('dRgZ').open&&document.getElementById('dRgZ').close()");pg.click('#rgZip');pg.wait_for_selector('#dRgZ[open]');pg.uncheck('#rgZAnt')
    with zipfile.ZipFile('/tmp/ca/esc2.zip','w') as z:z.writestr('Pedro Sosa Vela.pdf',b'%PDF-1.4 p')
    pg.set_input_files('#rgZFile','/tmp/ca/esc2.zip');pg.wait_for_selector('#rgZRes .mod');ok('si_se_desmarca_la_opcion_se_pide_la_inscripcion','no se encontró la inscripción' in pg.inner_text('#rgZRes'));pg.evaluate("document.getElementById('dRgZ').close()")
    # ============ permisos ============
    for u,esperado in [('a2e',True),('a2v',False)]:
        cx=b.new_context(viewport={'width':1150,'height':950});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')");pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1500)
        pp.evaluate("ir('a2')");pp.wait_for_selector('#a2Tabs');pp.click('#a2Tabs [data-a2t="C"]');pp.wait_for_timeout(500)
        ok('permiso_'+u+('_puede_registrar' if esperado else '_solo_consulta'),pp.is_visible('#rgNew')==esperado)
        if esperado:
            pp.click('#rgNew');pp.check('#rgModoA');pp.fill('#rgAnN','Rosa Elena Campos');pp.click('#rgOk');W(pp,"Object.values(RGD).some(function(x){return x.nombre==='Rosa Elena Campos'})");ok('el_editor_de_acuerdo_286_guarda_un_certificado_anterior',True)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.evaluate("document.getElementById('dRgE')&&document.getElementById('dRgE').open&&document.getElementById('dRgE').close()");pg.click('#rgNew');pg.check('#rgModoA');pg.fill('#rgAnN','Marcos Ibarra Salgado');pg.wait_for_timeout(300);pg.locator('#dRg').screenshot(path='/tmp/cert_anterior_dialogo.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
