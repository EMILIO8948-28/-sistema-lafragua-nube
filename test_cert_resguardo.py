import subprocess,time,json,os,urllib.request,zipfile
from playwright.sync_api import sync_playwright
PORT=3109;B='http://127.0.0.1:%d'%PORT;TOK='tok-cr-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata39',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata39 /tmp/cz && mkdir -p /tmp/nbdata39 /tmp/cz')
open('/tmp/cz/cert.pdf','wb').write(b'%PDF-1.4 certificado escaneado')
with zipfile.ZipFile('/tmp/cz/esc.zip','w') as z:
    z.writestr('B286-000003_parcial.pdf',b'%PDF-1.4 parcial');z.writestr('Beto Mena Ruiz.pdf',b'%PDF-1.4 beto');z.writestr('b286-000001.pdf',b'%PDF-1.4 repetido');z.writestr('desconocido.pdf',b'%PDF-1.4 x');z.writestr('B286-000099.pdf',b'%PDF-1.4 y');z.writestr('__MACOSX/._x.pdf',b'x')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
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
hoy=time.strftime('%Y-%m-%d')
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    up=ctx.request.post(B+'/api/archivo',data=open('/tmp/cz/cert.pdf','rb').read(),headers={'x-lafragua':'1','x-nombre':'certificado-ana.pdf','Content-Type':'application/pdf'}).json()['id']
    for i,(nom,pat,mat,sx,cert) in enumerate([('Ana','López','Ramírez','Femenino',{'id':up,'name':'certificado-ana.pdf','size':30}),('Beto','Mena','Ruiz','Masculino',None),('Carla','Díaz','Soto','Femenino',None)],1):
        put('acuerdo286/a%d'%i,{'id':'a%d'%i,'num':'B286-%06d'%i,'fecha':'2026-01-10','nombre':nom,'apPat':pat,'apMat':mat,'sexo':sx,'tel':'72600000%d'%i,'docs':{},'tram':{},'pagos':[],'cert':cert,'enviado':True})
    for u,n,r,m in [('a2e','Editor 286','personalizado',{'a286':'editar'}),('a2v','Lector 286','personalizado',{'a286':'ver'}),('esc2','Esc Dos','personalizado',{'escolar':'editar'})]:
        assert ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':u,'name':n,'rol':r,'modulos':m,'clave':'clave-%s-123'%u}),headers=HDR).status==200
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(A2).length===3");pg.evaluate(MOCK)
    pg.evaluate("ir('a2')");pg.wait_for_selector('#a2Tabs');ok('opciones_en_el_modulo','Inscripciones' in pg.inner_text('#a2Tabs') and 'Certificados en resguardo' in pg.inner_text('#a2Tabs'))
    ok('por_defecto_se_ven_las_inscripciones',pg.is_visible('#a2PanI') and pg.is_hidden('#a2PanC') and 'B286-000001' in pg.inner_text('#a2Tb'))
    pg.click('#a2Tabs [data-a2t="C"]');pg.wait_for_selector('#a2PanC:not([hidden])');ok('abre_certificados_en_resguardo',pg.is_hidden('#a2PanI') and 'Aún no hay certificados en resguardo' in pg.inner_text('#rgTb') and pg.inner_text('#rgC3')=='0')
    pg.click('#a2Tabs [data-a2t="I"]');ok('se_puede_volver_a_inscripciones',pg.is_visible('#a2PanI'));pg.click('#a2Tabs [data-a2t="C"]')
    # ---- registrar ----
    pg.click('#rgNew');pg.wait_for_selector('#dRg[open]');pg.click('#rgOk');ok('exige_inscripcion','Elige la inscripción' in pg.inner_text('#rgMsg'))
    pg.fill('#rgAl','B286-000001 — Ana López Ramírez');ok('ofrece_usar_el_certificado_ya_cargado',pg.is_visible('#rgUsaW'))
    pg.select_option('#rgTp','Certificado de bachillerato');pg.fill('#rgDf','CB-2026-0457');pg.fill('#rgFx','2026-09-15');pg.fill('#rgUb','Archivero 3, cajón 1');pg.click('#rgOk');W(pg,"Object.keys(RGD).length===1")
    rid=json.loads(pg.evaluate("JSON.stringify(Object.keys(RGD))"))[0];d1=get('resguardos286/'+rid)['data']
    ok('guarda_con_folio_propio',d1['num']=='RC-000001' and d1['nombre']=='Ana López Ramírez' and d1['mat']=='B286-000001' and d1['plan']=='Bachillerato por Acuerdo 286' and d1['tipo']=='Certificado de bachillerato' and d1['docFolio']=='CB-2026-0457' and d1['estado']=='resguardo' and d1['sexo']=='Femenino')
    ok('usa_el_escaneo_ya_cargado_en_la_inscripcion',d1['archivo']['id']==up and d1['mov'][0]['a']=='Recibido en resguardo')
    pg.click('#rgNew');pg.fill('#rgAl','B286-000002 — Beto Mena Ruiz');ok('no_ofrece_si_la_inscripcion_no_tiene_certificado',pg.is_hidden('#rgUsaW'));pg.set_input_files('#rgFile','/tmp/cz/cert.pdf');pg.click('#rgOk');W(pg,"Object.keys(RGD).length===2")
    ids=json.loads(pg.evaluate("JSON.stringify(Object.keys(RGD))"));d2=[get('resguardos286/'+i)['data'] for i in ids if get('resguardos286/'+i)['data']['mat']=='B286-000002'][0]
    ok('sube_un_escaneo_nuevo',d2['num']=='RC-000002' and d2['archivo']['name']=='cert.pdf' and d2['archivo']['id']!=up)
    pg.click('#rgNew');pg.fill('#rgAl','B286-000001 — Ana López Ramírez');pg.select_option('#rgTp','Certificado de bachillerato');pg.fill('#rgDf','CB-2026-0457');pg.click('#rgOk');ok('no_repite_el_mismo_certificado','ya tiene ese certificado' in pg.inner_text('#rgMsg'));pg.click('#rgCan')
    ok('contadores_y_tabla','RC-000001' in pg.inner_text('#rgTb') and pg.inner_text('#rgC1')=='2' and pg.inner_text('#rgC3')=='2')
    pg.fill('#rgQ','mena');ok('busca_por_nombre',pg.locator('#rgTb tr').count()==1);pg.fill('#rgQ','b286-000001');ok('busca_por_folio_de_inscripcion',pg.locator('#rgTb tr').count()==1);pg.fill('#rgQ','')
    # ---- constancia y entrega ----
    pg.locator('#rgTb tr:has-text("RC-000001") [data-rr]').click();pg.wait_for_timeout(300);tx=' | '.join(pg.evaluate("window.__txt"));sv=pg.evaluate("window.__sav")
    ok('constancia_de_recepcion','Constancia de recepción de certificado en resguardo' in tx and 'ANA LÓPEZ RAMÍREZ' in tx and 'B286-000001' in tx and 'Bachillerato por Acuerdo 286' in tx and 'CB-2026-0457' in tx and 'Archivero 3, cajón 1' in tx and 'la C.' in tx and sv[0][0]=='resguardo-certificado-RC-000001-B286000001.pdf')
    pg.locator('#rgTb tr:has-text("RC-000001") [data-re]').click();pg.wait_for_selector('#dRgE[open]');ok('prellena_al_titular',pg.input_value('#rgEN')=='Ana López Ramírez')
    pg.click('#rgEOk');ok('exige_identificacion','número de la identificación' in pg.inner_text('#rgEMsg'));pg.fill('#rgENm','INE-998877');pg.evaluate("window.__txt=[];window.__sav=[]");pg.click('#rgEOk');W(pg,"RGD['%s'].estado==='entregado'"%rid);pg.wait_for_timeout(300)
    d1=get('resguardos286/'+rid)['data'];tx=' | '.join(pg.evaluate("window.__txt"))
    ok('entrega_y_acta','Acta de entrega de certificado en resguardo' in tx and 'INE número INE-998877' in tx and 'ANA LÓPEZ RAMÍREZ' in tx and d1['entrega']['receptor']=='Ana López Ramírez' and d1['mov'][-1]['a'].startswith('Entregado a Ana López Ramírez (titular)') and pg.evaluate("window.__sav")[0][0]=='entrega-certificado-RC-000001-B286000001.pdf')
    ok('contadores_tras_entregar',pg.inner_text('#rgC1')=='1' and pg.inner_text('#rgC2')=='1')
    pg.evaluate("window.__sav=[]");pg.click('#rgCsv');pg.wait_for_timeout(200);sv=pg.evaluate("window.__sav");ok('exporta_csv',sv[0][0].startswith('certificados-en-resguardo-') and 'folio_inscripcion' in sv[0][1] and sv[0][1].count('RC-00000')==2)
    # ---- ZIP ----
    pg.click('#rgZip');pg.wait_for_selector('#dRgZ[open]');pg.set_input_files('#rgZFile','/tmp/cz/esc.zip');pg.wait_for_selector('#rgZRes table');res=pg.inner_text('#rgZRes')
    ok('lee_el_zip','5 archivos en el ZIP' in res and '__MACOSX' not in res)
    fila=lambda t:pg.locator('#rgZRes tr:has-text("%s")'%t).first.inner_text()
    ok('crea_el_certificado_parcial_por_folio','Crear registro de «Certificado parcial»' in fila('B286-000003_parcial.pdf') and 'Carla' in fila('B286-000003_parcial.pdf'))
    ok('omite_el_que_ya_tiene_escaneo_y_los_desconocidos','ya tiene escaneo' in fila('Beto Mena Ruiz.pdf') and 'no se encontró la inscripción' in fila('desconocido.pdf') and 'no se encontró la inscripción' in fila('B286-000099.pdf') and True)
    ok('si_el_certificado_ya_se_entrego_crea_un_registro_nuevo','Crear registro de «Certificado de bachillerato»' in fila('b286-000001.pdf'))
    pg.fill('#rgZUb','Caja certificados');pg.click('#rgZOk');W(pg,"document.getElementById('rgZMsg').textContent.indexOf('Listo')===0")
    docs=[x['data'] for x in ctx.request.get(B+'/api/col/resguardos286').json()['docs']];nu=[x for x in docs if x['mat']=='B286-000003']
    ok('registro_nuevo_desde_zip',len(nu)==1 and nu[0]['num']=='RC-000003' and nu[0]['tipo']=='Certificado parcial' and nu[0]['ubic']=='Caja certificados' and nu[0]['archivo']['name']=='B286-000003_parcial.pdf' and get('meta/folioRC')['data']['n']==4 and len([x for x in docs if x['mat']=='B286-000001'])==2)
    pg.click('#rgZCan')
    # ---- deshacer y quitar ----
    pg.locator('#rgTb tr:has-text("RC-000001") [data-ru]').click();W(pg,"RGD['%s'].estado==='resguardo'"%rid);ok('deshacer_entrega',get('resguardos286/'+rid)['data']['mov'][-1]['a'].startswith('Entrega deshecha'))
    # ---- permisos ----
    def ses(u):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);assert r.status==200;return cx
    E,V,X=ses('a2e'),ses('a2v'),ses('esc2')
    ids=lambda cx:[x['id'] for x in cx.request.get(B+'/api/col/resguardos286').json().get('docs',[])] if cx.request.get(B+'/api/col/resguardos286').status==200 else 'x'
    ok('lee_quien_ve_o_edita_acuerdo_286',len(ids(E))==4 and len(ids(V))==4)
    ok('quien_solo_tiene_control_escolar_no_ve_certificados',ids(X)==[])
    pu=lambda cx,path,obj:cx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status
    ok('solo_quien_edita_acuerdo_286_escribe',pu(V,'resguardos286/zz',{'x':1})==403 and pu(X,'resguardos286/zz',{'x':1})==403 and pu(E,'resguardos286/zz',{'num':'RC-999','sid':'a1'})==200)
    ctx.request.delete(B+'/api/doc/resguardos286/zz',headers=HDR)
    fid=get('resguardos286/'+ids(E)[0])['data']['archivo']
    ok('el_titulo_de_control_escolar_no_se_mezcla',ctx.request.get(B+'/api/col/resguardos').json()['docs']==[] and E.request.get(B+'/api/col/resguardos').json().get('docs',[])==[])
    ok('escaneo_privado_solo_para_quien_edita_acuerdo_286',E.request.get(B+'/_blob/'+d2['archivo']['id']).status==200 and ctx.request.get(B+'/_blob/'+d2['archivo']['id']).status==200 and V.request.get(B+'/_blob/'+d2['archivo']['id']).status==403 and X.request.get(B+'/_blob/'+d2['archivo']['id']).status==403)
    sube=lambda cx:cx.request.post(B+'/api/archivo',data=b'%PDF-1.4 z',headers={'x-lafragua':'1','x-nombre':'a.pdf','x-privado':'1','x-categoria':'certificado','Content-Type':'application/pdf'}).status
    ok('quien_solo_consulta_no_sube_escaneos_de_certificados',sube(E)==200 and sube(V)==403)
    def entra(u,c):
        cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP',c);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&Object.keys(A2).length===3");pp.evaluate("ir('a2')");pp.wait_for_selector('#a2Tabs');pp.click('#a2Tabs [data-a2t=\"C\"]');pp.wait_for_selector('#rgTb tr');return pp
    pv=entra('a2v','clave-a2v-123');ok('quien_solo_ve_consulta_sin_botones_de_cambio',pv.locator('#rgTb tr').count()==4 and pv.is_hidden('#rgNew') and pv.is_hidden('#rgZip') and pv.locator('#rgTb [data-rv]:visible').count()==0 and pv.locator('#rgTb [data-re]:visible').count()==0 and pv.locator('#rgTb [data-rh]:visible').count()==4)
    pe=entra('a2e','clave-a2e-123');ok('quien_edita_ve_los_botones',pe.is_visible('#rgNew') and pe.is_visible('#rgZip') and pe.locator('#rgTb [data-rv]:visible').count()==4)
    pe.locator('#rgTb tr:has-text("RC-000003") [data-rx]').click();pe.locator('#rgTb tr:has-text("RC-000003") [data-rx]').click();pe.wait_for_selector('#dAu[open]');pe.fill('#auPw','clave-segura-1');pe.click('#auClave');W(pe,"Object.keys(RGD).length===3");ok('quitar_pide_autorizacion',len(ctx.request.get(B+'/api/col/resguardos286').json()['docs'])==3)
    # ---- cargar el certificado directamente en cada registro ----
    open('/tmp/cz/cert2.pdf','wb').write(b'%PDF-1.4 segundo certificado');open('/tmp/cz/malo.exe','wb').write(b'MZ');open('/tmp/cz/grande.pdf','wb').write(b'%PDF'+b'0'*(11*1024*1024))
    put('resguardos286/fila1',{'num':'RC-000777','sid':'a3','nombre':'Carla Díaz Soto','mat':'B286-000003','plan':'Bachillerato por Acuerdo 286','sexo':'Femenino','tipo':'Certificado de bachillerato','docFolio':'','fechaExp':'','fechaRec':'2026-11-01','ubic':'','notas':'','archivo':None,'estado':'resguardo','recibe':'Administrador','mov':[{'f':'2026-11-01T10:00:00.000Z','a':'Recibido en resguardo','p':'Administrador'}]})
    pg.click('#a2Tabs [data-a2t="I"]');pg.click('#a2Tabs [data-a2t="C"]');pg.wait_for_selector('#rgTb tr:has-text("RC-000777")')
    fila=pg.locator('#rgTb tr:has-text("RC-000777")')
    ok('cada_registro_sin_escaneo_ofrece_cargar_certificado',fila.locator('[data-rf]').inner_text()=='Cargar certificado' and 'Escaneo' not in fila.inner_text().replace('Cargar','').replace('Cambiar','') .split('Historial')[0])
    pg.locator('#rgTb tr:has-text("RC-000777") [data-rf]').click();W(pg,"RFROW.g!==null");pg.set_input_files('#rgRowFile','/tmp/cz/malo.exe');pg.wait_for_timeout(300);ok('fila_rechaza_tipo_no_permitido','PDF, JPG o PNG' in pg.inner_text('#rgRowMsg') and get('resguardos286/fila1')['data']['archivo'] is None)
    pg.set_input_files('#rgRowFile','/tmp/cz/grande.pdf');pg.wait_for_timeout(300);ok('fila_rechaza_archivo_grande','10 MB' in pg.inner_text('#rgRowMsg'))
    pg.set_input_files('#rgRowFile','/tmp/cz/cert.pdf');W(pg,"document.getElementById('rgRowMsg').textContent.indexOf('Listo')===0")
    f1=get('resguardos286/fila1')['data'];ok('carga_el_certificado_en_el_registro',f1['archivo']['name']=='cert.pdf' and f1['mov'][-1]['a']=='Escaneo cargado' and f1['mov'][-1]['n']=='cert.pdf' and f1['mov'][-1]['p']=='Administrador' and ctx.request.get(B+'/_blob/'+f1['archivo']['id']).body()==open('/tmp/cz/cert.pdf','rb').read())
    ok('el_boton_cambia_a_cambiar_certificado',pg.locator('#rgTb tr:has-text("RC-000777") [data-rf]').inner_text()=='Cambiar certificado' and pg.locator('#rgTb tr:has-text("RC-000777") a:has-text("Escaneo")').count()==1)
    pg.set_input_files('#rgRowFile','/tmp/cz/cert2.pdf');W(pg,"RGD['fila1'].archivo.name==='cert2.pdf'");f2=get('resguardos286/fila1')['data']
    ok('reemplaza_el_certificado_y_lo_deja_en_el_historial',f2['archivo']['name']=='cert2.pdf' and f2['archivo']['id']!=f1['archivo']['id'] and f2['mov'][-1]['a']=='Escaneo reemplazado' and len(f2['mov'])==3)
    pv2=entra('a2v','clave-a2v-123');pv2.wait_for_selector('#rgTb tr:has-text("RC-000777")');ok('quien_solo_consulta_no_ve_el_boton_de_cargar',pv2.locator('#rgTb [data-rf]:visible').count()==0)
    pe2=entra('a2e','clave-a2e-123');pe2.wait_for_selector('#rgTb tr:has-text("RC-000777")');ok('quien_edita_acuerdo_286_si_lo_ve',pe2.locator('#rgTb [data-rf]:visible').count()>=1)
    ctx.request.delete(B+'/api/doc/resguardos286/fila1',headers=HDR)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
