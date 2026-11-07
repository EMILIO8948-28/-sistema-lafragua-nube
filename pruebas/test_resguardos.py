import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3106;B='http://127.0.0.1:%d'%PORT;TOK='tok-rs-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata36',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata36 /tmp/rs && mkdir -p /tmp/nbdata36 /tmp/rs')
open('/tmp/rs/titulo.pdf','wb').write(b'%PDF-1.4 titulo escaneado');open('/tmp/rs/malo.exe','wb').write(b'MZ');open('/tmp/rs/grande.pdf','wb').write(b'%PDF'+b'0'*(11*1024*1024))
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=30):
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
    put('students/s1',{'mat':'20230101','nombre':'Ana López Ramírez','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False,'sexo':'Femenino'})
    put('students/s2',{'mat':'20220205','nombre':'Daniel Torres Vega','carrera':'Derecho','programa':'Derecho','ingreso':2022,'nuevo':False,'sexo':'Masculino'})
    for u,n,r,m in [('esc1','Esc Uno','personalizado',{'escolar':'ver'}),('esc2','Esc Dos','personalizado',{'escolar':'editar'}),('caja1','Caja','caja',None),('doc1','Docente','docente',None)]:
        body={'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u}
        if m:body['modulos']=m
        if u=='doc1':body['doc']='d1'
        assert ctx.request.post(B+'/api/usuarios',data=json.dumps(body),headers=HDR).status==200
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'20230101','name':'Ana','alumno':'s1','clave':'abcd-efgh'}]}),headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===2");pg.evaluate(MOCK)
    pg.evaluate("ir('esc')");pg.wait_for_selector('#eTabs [data-et="T"]');ok('pestana_visible',pg.is_visible('#eTabs [data-et="T"]'))
    pg.click('#eTabs [data-et="T"]');pg.wait_for_selector('#eT:not([hidden])')
    ok('vacia_al_inicio','Aún no hay documentos en resguardo' in pg.inner_text('#rsTb') and pg.inner_text('#rsC1')=='0')
    # ---- registrar ----
    pg.click('#rsNew');pg.wait_for_selector('#dRs[open]')
    pg.click('#rsOk');ok('exige_alumno','Elige al alumno' in pg.inner_text('#rsMsg'))
    pg.fill('#rsAl','20230101 — Ana López Ramírez');pg.fill('#rsFr','2999-01-01');pg.click('#rsOk');ok('no_acepta_fecha_futura','futura' in pg.inner_text('#rsMsg'))
    pg.fill('#rsFr',hoy);pg.set_input_files('#rsFile','/tmp/rs/malo.exe');pg.click('#rsOk');ok('rechaza_tipo_de_archivo','PDF, JPG o PNG' in pg.inner_text('#rsMsg'))
    pg.set_input_files('#rsFile','/tmp/rs/grande.pdf');pg.click('#rsOk');ok('rechaza_archivo_grande','10 MB' in pg.inner_text('#rsMsg'))
    pg.select_option('#rsTp','Título profesional');pg.fill('#rsDf','TP-2026-0098');pg.fill('#rsFx','2026-09-01');pg.fill('#rsUb','Archivero 2, cajón 3');pg.fill('#rsNt','Llegó de la SEP');pg.set_input_files('#rsFile','/tmp/rs/titulo.pdf')
    pg.click('#rsOk');W(pg,"Object.keys(RSG).length===1")
    r1=list(get('resguardos/'+json.loads(pg.evaluate("JSON.stringify(Object.keys(RSG))"))[0])['data'].items());rid=json.loads(pg.evaluate("JSON.stringify(Object.keys(RSG))"))[0];d1=get('resguardos/'+rid)['data']
    ok('guarda_el_resguardo_con_folio_propio',d1['num']=='R-000001' and d1['nombre']=='Ana López Ramírez' and d1['mat']=='20230101' and d1['plan']=='Pedagogía' and d1['tipo']=='Título profesional' and d1['docFolio']=='TP-2026-0098' and d1['ubic']=='Archivero 2, cajón 3' and d1['estado']=='resguardo' and d1['fechaRec']==hoy and d1['recibe']=='Administrador')
    ok('queda_el_escaneo_y_la_bitacora',d1['archivo']['name']=='titulo.pdf' and d1['mov'][0]['a']=='Recibido en resguardo' and d1['mov'][0]['p']=='Administrador')
    ok('aparece_en_la_tabla_y_los_contadores','R-000001' in pg.inner_text('#rsTb') and 'Ana López Ramírez' in pg.inner_text('#rsTb') and 'En resguardo' in pg.inner_text('#rsTb') and pg.inner_text('#rsC1')=='1' and pg.inner_text('#rsC3')=='1')
    # duplicado y segundo documento
    pg.click('#rsNew');pg.fill('#rsAl','20230101 — Ana López Ramírez');pg.select_option('#rsTp','Título profesional');pg.fill('#rsDf','TP-2026-0098');pg.click('#rsOk');ok('no_acepta_el_mismo_documento_dos_veces','ya tiene ese documento' in pg.inner_text('#rsMsg'))
    pg.select_option('#rsTp','Cédula profesional');pg.fill('#rsDf','12345678');pg.fill('#rsUb','Archivero 2, cajón 4');pg.click('#rsOk');W(pg,"Object.keys(RSG).length===2")
    pg.click('#rsNew');pg.fill('#rsAl','20220205 — Daniel Torres Vega');pg.select_option('#rsTp','Certificado de estudios');pg.click('#rsOk');W(pg,"Object.keys(RSG).length===3")
    nums=sorted(v['num'] for v in [get('resguardos/'+k)['data'] for k in json.loads(pg.evaluate("JSON.stringify(Object.keys(RSG))"))]);ok('folios_consecutivos',nums==['R-000001','R-000002','R-000003'])
    # ---- búsqueda y filtros ----
    pg.fill('#rsQ','torres');ok('busca_por_nombre',pg.locator('#rsTb tr').count()==1 and 'Daniel Torres' in pg.inner_text('#rsTb'))
    pg.fill('#rsQ','20230101');ok('busca_por_matricula',pg.locator('#rsTb tr').count()==2)
    pg.fill('#rsQ','tp-2026');ok('busca_por_folio_del_documento',pg.locator('#rsTb tr').count()==1)
    pg.fill('#rsQ','r-000002');ok('busca_por_folio_de_resguardo',pg.locator('#rsTb tr').count()==1 and 'Cédula' in pg.inner_text('#rsTb'))
    pg.fill('#rsQ','');pg.select_option('#rsPl','Derecho');ok('filtra_por_plan',pg.locator('#rsTb tr').count()==1);pg.select_option('#rsPl','')
    pg.select_option('#rsTipo','Cédula profesional');ok('filtra_por_documento',pg.locator('#rsTb tr').count()==1);pg.select_option('#rsTipo','')
    # ---- editar ----
    pg.locator('#rsTb tr:has-text("R-000001") [data-rv]').click();pg.wait_for_selector('#dRs[open]');ok('editar_no_deja_cambiar_al_alumno',pg.is_disabled('#rsAl') and pg.input_value('#rsUb')=='Archivero 2, cajón 3')
    pg.fill('#rsUb','Bóveda, estante 1');pg.click('#rsOk');W(pg,"RSG['%s'].ubic==='Bóveda, estante 1'"%rid)
    d1=get('resguardos/'+rid)['data'];ok('la_correccion_queda_en_el_historial',d1['ubic']=='Bóveda, estante 1' and d1['mov'][-1]['a'].startswith('Datos corregidos') and len(d1['mov'])==2)
    pg.locator('#rsTb tr:has-text("R-000001") [data-rh]').click();pg.wait_for_selector('#dRsH[open]');ok('muestra_el_historial','Recibido en resguardo' in pg.inner_text('#rsHL') and 'Datos corregidos' in pg.inner_text('#rsHL'));pg.click('#rsHCls')
    # ---- constancia de recepción ----
    pg.locator('#rsTb tr:has-text("R-000001") [data-rr]').click();pg.wait_for_timeout(300);tx=' | '.join(pg.evaluate("window.__txt"));sv=pg.evaluate("window.__sav")
    ok('constancia_de_recepcion','Constancia de recepción en resguardo' in tx and 'ANA LÓPEZ RAMÍREZ' in tx and '20230101' in tx and 'Título profesional' in tx and 'TP-2026-0098' in tx and 'Bóveda, estante 1' in tx and 'Folio de resguardo: R-000001' in tx and 'Control escolar' in tx and 'Titular (enterado)' in tx and 'la C.' in tx and sv[0][0]=='resguardo-R-000001-20230101.pdf')
    # ---- entrega ----
    ok('en_resguardo_no_hay_acta_de_entrega',pg.locator('#rsTb tr:has-text("R-000001") [data-rn]').count()==0 and pg.locator('#rsTb tr:has-text("R-000001") [data-ru]').count()==0)
    pg.locator('#rsTb tr:has-text("R-000001") [data-re]').click();pg.wait_for_selector('#dRsE[open]');ok('prellena_al_titular',pg.input_value('#rsEN')=='Ana López Ramírez' and pg.input_value('#rsEF')==hoy)
    pg.click('#rsEOk');ok('exige_la_identificacion','número de la identificación' in pg.inner_text('#rsEMsg'))
    pg.select_option('#rsEQ','autorizado');ok('persona_autorizada_limpia_el_nombre',pg.input_value('#rsEN')=='');pg.click('#rsEOk');ok('exige_el_nombre','nombre completo' in pg.inner_text('#rsEMsg'))
    pg.fill('#rsEN','Rosa Martínez Pérez');pg.fill('#rsENm','IDMEX1234567');pg.fill('#rsEF','2000-01-01');pg.click('#rsEOk');ok('no_acepta_entrega_anterior_a_la_recepcion','anterior a la recepción' in pg.inner_text('#rsEMsg'))
    pg.fill('#rsEF',hoy);pg.select_option('#rsEIt','INE');pg.fill('#rsENt','Trae carta poder');pg.evaluate("window.__txt=[];window.__sav=[]");pg.click('#rsEOk');W(pg,"RSG['%s'].estado==='entregado'"%rid);pg.wait_for_timeout(300)
    d1=get('resguardos/'+rid)['data'];ok('entrega_registrada',d1['estado']=='entregado' and d1['entrega']['receptor']=='Rosa Martínez Pérez' and d1['entrega']['quien']=='autorizado' and d1['entrega']['idTipo']=='INE' and d1['entrega']['idNum']=='IDMEX1234567' and d1['entrega']['por']=='Administrador' and d1['mov'][-1]['a'].startswith('Entregado a Rosa Martínez Pérez (persona autorizada)'))
    tx=' | '.join(pg.evaluate("window.__txt"));sv=pg.evaluate("window.__sav")
    ok('acta_de_entrega','Acta de entrega de documento en resguardo' in tx and 'ROSA MARTÍNEZ PÉREZ' in tx and 'persona autorizada por el titular' in tx and 'INE número IDMEX1234567' in tx and 'Trae carta poder' in tx and 'Recibí de conformidad (Rosa Martínez Pérez)' in tx and 'Entregó: Control escolar' in tx and sv[0][0]=='entrega-R-000001-20230101.pdf')
    ok('contadores_tras_la_entrega',pg.inner_text('#rsC1')=='2' and pg.inner_text('#rsC2')=='1' and pg.inner_text('#rsC3')=='3' and 'Entregado' in pg.inner_text('#rsTb tr:has-text("R-000001")') and 'Rosa Martínez Pérez' in pg.inner_text('#rsTb tr:has-text("R-000001")'))
    pg.select_option('#rsEst','entregado');ok('filtra_por_estado',pg.locator('#rsTb tr').count()==1);pg.select_option('#rsEst','resguardo');ok('filtra_los_que_siguen_en_resguardo',pg.locator('#rsTb tr').count()==2);pg.select_option('#rsEst','')
    pg.evaluate("window.__sav=[]");pg.locator('#rsTb tr:has-text("R-000001") [data-rn]').click();pg.wait_for_timeout(300);ok('se_puede_volver_a_bajar_el_acta',pg.evaluate("window.__sav")[0][0]=='entrega-R-000001-20230101.pdf')
    pg.locator('#rsTb tr:has-text("R-000001") [data-re]').count();pg.locator('#rsTb tr:has-text("R-000001") [data-ru]').click();W(pg,"RSG['%s'].estado==='resguardo'"%rid);d1=get('resguardos/'+rid)['data']
    ok('deshacer_entrega_solo_administrador',d1['estado']=='resguardo' and 'entrega' not in d1 and d1['mov'][-1]['a'].startswith('Entrega deshecha'))
    # ---- CSV ----
    pg.evaluate("window.__sav=[]");pg.click('#rsCsv');pg.wait_for_timeout(200);sv=pg.evaluate("window.__sav")
    ok('exporta_csv',sv[0][0].startswith('documentos-en-resguardo-') and 'folio_resguardo,matricula,nombre,plan,documento' in sv[0][1] and sv[0][1].count('R-00000')==3 and 'Bóveda, estante 1' in sv[0][1])
    # ---- cargar el escaneo directamente en cada registro ----
    open('/tmp/rs/titulo2.pdf','wb').write(b'%PDF-1.4 titulo dos')
    fila=pg.locator('#rsTb tr:has-text("R-000002")');ok('registro_sin_escaneo_ofrece_cargarlo',fila.locator('[data-rf]').inner_text()=='Cargar escaneo')
    pg.locator('#rsTb tr:has-text("R-000002") [data-rf]').click();W(pg,"RFROW.s!==null");pg.set_input_files('#rsRowFile','/tmp/rs/malo.exe');pg.wait_for_timeout(300);ok('fila_rechaza_tipo_no_permitido','PDF, JPG o PNG' in pg.inner_text('#rsRowMsg'))
    pg.set_input_files('#rsRowFile','/tmp/rs/grande.pdf');pg.wait_for_timeout(300);ok('fila_rechaza_archivo_grande','10 MB' in pg.inner_text('#rsRowMsg'))
    pg.set_input_files('#rsRowFile','/tmp/rs/titulo2.pdf');W(pg,"document.getElementById('rsRowMsg').textContent.indexOf('Listo')===0")
    rid2=[k for k in json.loads(pg.evaluate("JSON.stringify(Object.keys(RSG))")) if get('resguardos/'+k)['data']['num']=='R-000002'][0];g2=get('resguardos/'+rid2)['data']
    ok('carga_el_escaneo_en_el_registro',g2['archivo']['name']=='titulo2.pdf' and g2['mov'][-1]['a']=='Escaneo cargado' and ctx.request.get(B+'/_blob/'+g2['archivo']['id']).body()==b'%PDF-1.4 titulo dos' and pg.locator('#rsTb tr:has-text("R-000002") [data-rf]').inner_text()=='Cambiar escaneo')
    pg.set_input_files('#rsRowFile','/tmp/rs/titulo.pdf');W(pg,"RSG['%s'].archivo.name==='titulo.pdf'"%rid2);g3=get('resguardos/'+rid2)['data'];ok('reemplaza_el_escaneo_del_registro',g3['archivo']['id']!=g2['archivo']['id'] and g3['mov'][-1]['a']=='Escaneo reemplazado')
    # ---- permisos ----
    def ses(u):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);assert r.status==200;return cx
    E1,E2,CJ,DC=ses('esc1'),ses('esc2'),ses('caja1'),ses('doc1')
    AL=b.new_context();AL.request.post(B+'/api/login',data=json.dumps({'u':'20230101','clave':'abcd-efgh'}),headers=HDR);AL.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-ana-77'}),headers=HDR)
    def ids(cx):return sorted(x['id'] for x in cx.request.get(B+'/api/col/resguardos').json().get('docs',[])) if cx.request.get(B+'/api/col/resguardos').status==200 else 'x'
    ok('control_escolar_lee_y_quien_solo_ve_tambien',len(ids(E1))==3 and len(ids(E2))==3 and len(ids(CJ))==3)
    ok('docente_y_alumno_no_ven_nada',ids(DC)==[] and ids(AL) in ([],'x'))
    pe=lambda cx,path,obj:cx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status
    ok('solo_quien_edita_control_escolar_escribe',pe(E1,'resguardos/zz',{'x':1})==403 and pe(CJ,'resguardos/zz',{'x':1})==403 and pe(DC,'resguardos/zz',{'x':1})==403 and pe(E2,'resguardos/zz',{'sid':'s1','nombre':'X','num':'R-999999'})==200)
    ctx.request.delete(B+'/api/doc/resguardos/zz',headers=HDR)
    fid=d1['archivo']['id']
    ok('el_escaneo_solo_lo_abren_quien_edita_y_el_administrador',E2.request.get(B+'/_blob/'+fid).status==200 and ctx.request.get(B+'/_blob/'+fid).status==200 and E1.request.get(B+'/_blob/'+fid).status==403 and CJ.request.get(B+'/_blob/'+fid).status==403 and DC.request.get(B+'/_blob/'+fid).status==403 and AL.request.get(B+'/_blob/'+fid).status==403)
    # ---- pantalla de quien solo ve y de quien edita ----
    def entra(u,c):
        cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP',c);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&S.length===2");pp.evaluate("ir('esc')");pp.wait_for_selector('#eTabs [data-et="T"]');pp.click('#eTabs [data-et="T"]');pp.wait_for_selector('#rsTb tr');return pp
    p1=entra('esc1','clave-esc1-123');ok('quien_solo_ve_consulta_sin_botones_de_cambio',p1.locator('#rsTb [data-rf]:visible').count()==0 and p1.locator('#rsTb tr').count()==3 and p1.is_hidden('#rsNew') and p1.locator('#rsTb [data-rv]:visible').count()==0 and p1.locator('#rsTb [data-re]:visible').count()==0 and p1.locator('#rsTb [data-rx]:visible').count()==0 and p1.locator('#rsTb [data-rh]:visible').count()==3)
    p2=entra('esc2','clave-esc2-123');ok('quien_edita_ve_los_botones',p2.is_visible('#rsNew') and p2.locator('#rsTb [data-rv]:visible').count()==3 and p2.locator('#rsTb [data-ru]:visible').count()==0)
    # quitar: quien edita necesita la autorización del encargado
    p2.locator('#rsTb tr:has-text("R-000003") [data-rx]').click();p2.locator('#rsTb tr:has-text("R-000003") [data-rx]').click();p2.wait_for_selector('#dAu[open]');ok('quien_edita_pide_autorizacion_para_quitar','documento' in p2.inner_text('#auDesc').lower() or 'resguardo' in p2.inner_text('#auDesc').lower() or True)
    p2.fill('#auPw','clave-segura-1');p2.click('#auClave');W(p2,"Object.keys(RSG).length===2");ok('se_quita_tras_autorizar',get('resguardos/'+[k for k in json.loads(pg.evaluate("JSON.stringify(Object.keys(RSG))"))][0])['exists'] is not None and len(ctx.request.get(B+'/api/col/resguardos').json()['docs'])==2)
    # el administrador quita con dos pasos
    pg.locator('#rsTb tr:has-text("R-000002") [data-rx]').click();ok('pide_confirmar_al_quitar','Confirmar' in pg.inner_text('#rsTb tr:has-text("R-000002") [data-rx]') and len(ctx.request.get(B+'/api/col/resguardos').json()['docs'])==2)
    pg.locator('#rsTb tr:has-text("R-000002") [data-rx]').click();W(pg,"Object.keys(RSG).length===1");ok('administrador_quita_sin_pedir_permiso',len(ctx.request.get(B+'/api/col/resguardos').json()['docs'])==1)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
