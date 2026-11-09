import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3114;B='http://127.0.0.1:%d'%PORT;TOK='tok-tf-123'
os.system('rm -rf /tmp/nbdata45 && mkdir -p /tmp/nbdata45')
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata45',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
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
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    dlg=[]
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:(dlg.append(d.message),d.accept()));return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.2)
    Y=pg.evaluate("new Date().getFullYear()");S=pg.evaluate("sabadosMes(%d,11)"%Y);PER='Sep–Dic %d'%Y;MES='%d-11'%Y
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    asig=lambda i,plan,nom:{'id':i,'cid':i,'plan':plan,'cuat':2,'nom':nom,'per':PER,'ses':S}
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[asig('a1','Pedagogía','Didáctica general'),asig('a2','Enfermería','Anatomía humana I')]})
    put('docentes/d2',{'nombre':'Prof. Dos','esp':'Historia','asig':[asig('a3','Pedagogía','Historia de la educación')]})
    put('docentes/d3',{'nombre':'Prof. Tres','esp':'Filosofía','asig':[asig('a4','Pedagogía','Filosofía de la educación')]})
    mat=lambda plan,nom,d,ini,fin:{'per':PER,'plan':plan,'cuat':2,'nom':nom,'docId':d,'ini':ini,'fin':fin}
    put('materias/m1',mat('Pedagogía','Didáctica general','d1','08:00','10:00'));put('materias/m2',mat('Enfermería','Anatomía humana I','d1','10:00','12:00'))
    put('materias/m3',mat('Pedagogía','Historia de la educación','d2','08:00','09:00'));put('materias/m4',mat('Pedagogía','Filosofía de la educación','d3','09:00','10:00'))
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(DOC).length===3&&Object.keys(MAT).length===4");pg.evaluate(MOCK)
    pg.evaluate("ir('nom')");pg.wait_for_selector('#nmBase');pg.select_option('#nmY',str(Y));pg.select_option('#nmM','11')
    filas=lambda d:pg.evaluate("resumenNom('%s',%d,11)"%(d,Y))
    tar=lambda d:{f['plan']:f['tarifa'] for f in filas(d)['filas']}
    ok('tarifas_de_origen_120_y_150',tar('d1')=={'Pedagogía':120,'Enfermería':150} and tar('d2')=={'Pedagogía':120} and abs(filas('d1')['total']-S*2*120-S*2*150)<0.01)
    ok('hay_dos_tarifas_generales_y_el_boton_nuevo',pg.input_value('#nmBase')=='120' and pg.input_value('#nmEsp')=='150' and pg.is_visible('#nmTarMas'))
    # ---- tarifa general ----
    pg.fill('#nmBase','130');pg.click('#nmTar');W(pg,"NOMC.base===130");c=get('config/nomina')['data']
    ok('guarda_la_tarifa_general_sin_perder_lo_demas',c['base']==130 and c['esp']==150 and c['planes']=={} and c['docentes']=={} and tar('d1')=={'Pedagogía':130,'Enfermería':150})
    # ---- por plan y por docente ----
    pg.click('#nmTarMas');pg.wait_for_selector('#dNmT[open]')
    ok('lista_planes_y_docentes',pg.locator('#nmtPl tr').count()==pg.evaluate("PL.length") and pg.locator('#nmtDc tr').count()==3 and 'Prof. Uno' in pg.inner_text('#nmtDc'))
    ok('muestra_la_tarifa_general_que_le_toca_a_cada_plan','$130.00' in pg.inner_text('#nmtPl tr:has-text("Pedagogía")') and '$150.00' in pg.inner_text('#nmtPl tr:has-text("Enfermería")'))
    pg.fill('#nmtPl tr:has-text("Pedagogía") input','140');pg.fill('#nmtPl tr:has-text("Enfermería") input','160')
    pg.fill('#nmtQ','dos');ok('filtra_docentes',pg.locator('#nmtDc tr').count()==1);pg.fill('#nmtDc tr:has-text("Prof. Dos") input','200');pg.fill('#nmtQ','')
    ok('lo_escrito_se_conserva_al_filtrar',pg.input_value('#nmtPl tr:has-text("Pedagogía") input')=='140' and pg.input_value('#nmtDc tr:has-text("Prof. Dos") input')=='200')
    pg.click('#nmtGuarda');W(pg,"NOMC.planes&&NOMC.planes['Pedagogía']===140&&NOMC.docentes&&NOMC.docentes.d2===200");c=get('config/nomina')['data']
    ok('guarda_planes_y_docentes',c['planes']=={'Pedagogía':140,'Enfermería':160} and c['docentes']=={'d2':200} and c['base']==130 and c['esp']==150 and 'Tarifas guardadas: 2 planes y 1 docente' in pg.inner_text('#nmMsg'))
    ok('el_plan_gana_a_la_general_y_el_docente_al_plan',tar('d1')=={'Pedagogía':140,'Enfermería':160} and tar('d2')=={'Pedagogía':200} and tar('d3')=={'Pedagogía':140})
    ok('indica_de_donde_viene_la_tarifa',[f['origen'] for f in filas('d1')['filas']]==['del plan','del plan'] and filas('d2')['filas'][0]['origen']=='del docente')
    # ---- cancelar no cambia nada ----
    pg.click('#nmTarMas');pg.fill('#nmtPl tr:has-text("Pedagogía") input','999');pg.click('#nmtCan');ok('cancelar_no_cambia_nada',tar('d1')=={'Pedagogía':140,'Enfermería':160} and get('config/nomina')['data']['planes']['Pedagogía']==140)
    pg.click('#nmTarMas');ok('al_reabrir_muestra_lo_guardado',pg.input_value('#nmtPl tr:has-text("Pedagogía") input')=='140');pg.fill('#nmtDc tr:has-text("Prof. Dos") input','');pg.click('#nmtGuarda');W(pg,"!NOMC.docentes.d2")
    ok('dejar_vacio_quita_la_tarifa_propia',tar('d2')=={'Pedagogía':140} and get('config/nomina')['data']['docentes']=={})
    # ---- ajuste en una asignatura de un mes ----
    pg.evaluate("openNm('d1')");pg.wait_for_selector('#dNm[open]')
    ok('el_detalle_permite_editar_la_tarifa','Tarifa por hora' in pg.inner_text('#nmFilas') and pg.locator('#nmFilas input[data-f="tar"]').count()==2)
    k=pg.locator('#nmFilas input[data-f="tar"]').first.get_attribute('data-k')
    pg.fill('#nmFilas input[data-f="tar"] >> nth=0','250');tot=pg.inner_text('#nmTot')
    ok('recalcula_el_total_al_cambiar_la_tarifa','$%s'%'{:,.2f}'.format(S*2*250+S*2*140) in tot and 'ajustada en esta asignatura' in pg.inner_text('#nmFilas'))
    pg.click('#nmGuarda');W(pg,"document.getElementById('nmDMsg').textContent.indexOf('guardados')>-1");fl=get('nomina/'+MES)['data']['filas']
    ok('guarda_el_ajuste_de_esa_asignatura_y_ese_mes',fl[k]['tar']==250 and all('tar' not in v for kk,v in fl.items() if kk!=k) and tar('d1')=={'Pedagogía':140,'Enfermería':250})
    pg.fill('#nmFilas input[data-f="tar"] >> nth=0','0');pg.click('#nmGuarda');W(pg,"document.getElementById('nmDMsg').textContent.indexOf('guardados')>-1");time.sleep(0.4)
    ok('escribir_cero_vuelve_a_la_tarifa_normal',tar('d1')=={'Pedagogía':140,'Enfermería':160} and 'tar' not in get('nomina/'+MES)['data']['filas'][k])
    # ---- pagar: lo pagado ya no cambia ----
    pg.click('#nmPagar');W(pg,"NOM['%s']&&NOM['%s'].pagos&&NOM['%s'].pagos.d1"%(MES,MES,MES));pg.wait_for_timeout(300)
    pago=get('nomina/'+MES)['data']['pagos']['d1'];ok('el_pago_guarda_las_tarifas_aplicadas',{f['plan']:f['tarifa'] for f in pago['filas']}=={'Pedagogía':140,'Enfermería':160} and abs(pago['monto']-(S*2*140+S*2*160))<0.01)
    tx=' | '.join(pg.evaluate("window.__txt"));ok('el_recibo_trae_la_tarifa_de_cada_asignatura_y_la_nota_nueva','$140.00' in tx and '$160.00' in tx and 'Tarifa por hora aplicada a cada asignatura' in tx and 'para Enfermería, maestría y doctorado' not in tx)
    pg.click('#nmCerrar') if pg.locator('#nmCerrar').count() else pg.evaluate("document.getElementById('dNm').close()")
    pg.click('#nmTarMas');pg.fill('#nmtPl tr:has-text("Pedagogía") input','175');pg.click('#nmtGuarda');W(pg,"NOMC.planes['Pedagogía']===175")
    ok('cambiar_la_tarifa_no_toca_lo_ya_pagado_pero_si_lo_pendiente',tar('d1')=={'Pedagogía':140,'Enfermería':160} and tar('d3')=={'Pedagogía':175} and filas('d1')['pago'] is not None)
    # ---- renombrar un plan conserva su tarifa propia ----
    pg.evaluate("ir('esc');etab('P')");pg.evaluate("abreRn()");pg.select_option('#rnPlan','Pedagogía');pg.fill('#rnNom','Licenciatura en Pedagogía')
    ok('sin_aviso_si_el_plan_tiene_tarifa_propia',pg.inner_text('#rnAviso')=='')
    pg.select_option('#rnPlan','Maestría en Educación');pg.fill('#rnNom','Educación posgrado');ok('avisa_si_no_tiene_tarifa_propia','tarifa por hora propia' in pg.inner_text('#rnAviso') and '$150.00' in pg.inner_text('#rnAviso') and '$130.00' in pg.inner_text('#rnAviso'))
    pg.select_option('#rnPlan','Pedagogía');pg.fill('#rnNom','Licenciatura en Pedagogía');pg.click('#rnOk');W(pg,"!document.getElementById('dRn').open",60);time.sleep(1.0)
    c=get('config/nomina')['data'];ok('la_tarifa_propia_sigue_al_plan_renombrado',c['planes']=={'Licenciatura en Pedagogía':175,'Enfermería':160} and c['base']==130)
    pg.evaluate("ir('nom')");ok('el_pago_de_docentes_sigue_igual_tras_renombrar',tar('d3')=={'Licenciatura en Pedagogía':175})
    # ---- permisos ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'nm1','name':'Nómina','rol':'personalizado','modulos':{'nomina_doc':'editar'},'clave':'clave-nm1-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    def ses(u):
        cx=b.new_context();cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);return cx
    NM,ES=ses('nm1'),ses('esc2');pu=lambda cx,o:cx.request.put(B+'/api/doc/config/nomina',data=json.dumps(o),headers=HDR).status
    ok('solo_nomina_y_el_administrador_cambian_tarifas',pu(ES,{'base':1,'esp':1})==403 and pu(NM,dict(c,planes=dict(c['planes'],Derecho=125)))==200 and get('config/nomina')['data']['planes']['Derecho']==125)
    cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pn=pagina(cx);pn.goto(B+'/');W(pn,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pn.fill('#lgU','nm1');pn.fill('#lgP','clave-nm1-123');pn.click('#lgGo');W(pn,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&Object.keys(DOC).length===3");pn.evaluate("ir('nom')")
    ok('quien_lleva_la_nomina_ve_y_usa_el_boton',pn.is_visible('#nmTarMas'));pn.click('#nmTarMas');pn.wait_for_selector('#dNmT[open]');pn.fill('#nmtDc tr:has-text("Prof. Tres") input','210');pn.click('#nmtGuarda');W(pn,"NOMC.docentes&&NOMC.docentes.d3===210")
    ok('y_queda_guardado',get('config/nomina')['data']['docentes']=={'d3':210} and get('config/nomina')['data']['planes']['Derecho']==125)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
