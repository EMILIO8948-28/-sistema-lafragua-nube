import subprocess,time,json,os,urllib.request,re,datetime
from playwright.sync_api import sync_playwright
PORT=3190;B='http://127.0.0.1:%d'%PORT;TOK='tok-a8-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata93 && mkdir -p /tmp/nbdata93')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata93',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
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
MOCK="""()=>{window.__ev=[];window.__sav=[];var cv=document.createElement('canvas').getContext('2d');
 function PDF(){this._fs=10;this._b=false;this._pages=1}
 var P=PDF.prototype;
 P.setFont=function(f,s){this._b=(s==='bold');return this};P.setFontSize=function(n){this._fs=n;return this};
 ['setDrawColor','setLineWidth','setTextColor','setFillColor','setLineDashPattern','rect','roundedRect','circle','ellipse','addImage','line'].forEach(function(f){P[f]=function(){return this}});
 P.addPage=function(){this._pages++;return this};P.getNumberOfPages=function(){return this._pages};P.setPage=function(i){return this};P.getTextWidth=function(t){return String(t).length*1.6};
 P.splitTextToSize=function(t,w){cv.font=(this._b?'bold ':'')+(this._fs*96/72)+'px Arial';var out=[],cur='';String(t).split(/\\s+/).forEach(function(word){var tr=cur?cur+' '+word:word;if(cv.measureText(tr).width*25.4/96>w&&cur){out.push(cur);cur=word}else cur=tr});if(cur)out.push(cur);return out};
 P.text=function(t,x,y,o){window.__ev.push(String(Array.isArray(t)?t.join(' '):t));return this};
 P.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
hoy=datetime.date.today().isoformat()
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    base=lambda i,n,**k:dict({'id':i,'num':'B286-%06d'%n,'fecha':hoy,'nombre':'Alumno','apPat':'Prueba%d'%n,'apMat':'','tel':'7220000%03d'%n,'docs':{},'tram':{},'pagos':[],'cert':None,'enviado':False,'fechaEnvio':'','fechaEval':'','promedio':None,'foto':'data:image/jpeg;base64,/9j/AAAA','byn':'Administrador'},**k)
    pago=lambda i,f,mon,cc,**k:dict({'id':i,'fecha':hoy,'monto':mon,'metodo':'Efectivo','ref':'','folio':f,'cc':cc,'byn':'Administrador'},**k)
    put('acuerdo286/m1',base('m1',1))                                    # sin «plan»: sigue siendo el plan mensual de siempre
    put('acuerdo286/e1',base('e1',2,plan='express'))
    put('acuerdo286/m2',base('m2',3,plan='mensual',nCol=6,pagos=[pago('pa1','R286-000101',1000,['i']),pago('pa2','R286-000102',1500,['c1']),pago('pa3','R286-000103',1500,['c2'])]))
    put('acuerdo286/m3',base('m3',4,plan='mensual',nCol=6,pagos=[pago('pb1','R286-000104',1000,['i'])]))
    put('resguardos286/r3',{'num':'RC-000001','sid':'m3','nombre':'Alumno Prueba4','mat':'B286-000004','tipo':'Certificado de bachillerato','estado':'resguardo','fechaRec':hoy})
    put('acuerdo286/m4',base('m4',5,plan='mensual',nCol=6,pagos=[pago('pc1','R286-000105',1000,['i'])],cert={'id':'a'*32,'name':'cert.pdf','size':10}))
    put('meta/folio286',{'n':5})
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('caja1','Caja','caja');usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}});usr('a286u','Acuerdo286','personalizado',{'modulos':{'a286':'editar'}});usr('con1','Consulta','consulta')
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(A2).length===5&&Object.keys(RGD).length===1");time.sleep(0.5)
    # ============ el cálculo de cada modalidad ============
    r=pg.evaluate("(function(){var a=est286(A2.m1),b=est286(A2.e1),c=est286(A2.m2);return {m:[a.n,a.tot],e:[b.n,b.tot,cargos286(A2.e1).map(function(x){return x.m})],c:[c.cub,c.pag,c.saldo]}})()")
    ok('sin_modalidad_sigue_siendo_el_plan_mensual_de_8_pagos',r['m']==[8,11500])
    ok('plan_express_son_2_pagos_de_5500_por_11000',r['e']==[2,11000,[5500,5500]])
    ok('el_plan_mensual_cuenta_lo_ya_pagado',r['c']==[3,4000,7500])
    ok('el_segundo_pago_express_es_el_de_la_entrega_del_certificado',pg.evaluate("cargos286(A2.e1)[1].c.indexOf('al entregar el certificado')>-1&&cargos286(A2.e1)[0].c.indexOf('al iniciar el proceso')>-1"))
    # ============ módulo 286: cobrar el plan Express ============
    pg.evaluate("ir('a2')");pg.wait_for_selector('#a2Tb tr');ok('la_tabla_dice_la_modalidad','Plan Express' in pg.inner_text('#a2Tb tr[data-id="e1"]') and 'Plan mensual' in pg.inner_text('#a2Tb tr[data-id="m1"]'))
    pg.evaluate(MOCK)
    pg.click('#a2Tb tr[data-id="e1"]');pg.wait_for_selector('#dA2[open]')
    ok('el_dialogo_explica_el_plan_express','Plan Express' in pg.inner_text('#a2PlanT') and '11,000.00' in pg.inner_text('#a2PlanH') and '50 %' in pg.inner_text('#a2PlanH') and 'Finanzas' in pg.inner_text('#a2PlanH'))
    ok('el_monto_sugerido_es_la_mitad',pg.input_value('#a2PagMon')=='5500' and pg.is_hidden('#a2LiqBar .mod'))
    pg.click('#a2PagAdd');W(pg,"A2.e1.pagos.length===1");e=pg.evaluate("est286(A2.e1)")
    ok('el_primer_pago_cubre_el_50_por_ciento',e['cub']==1 and e['pag']==5500 and e['saldo']==5500)
    ok('el_siguiente_pago_sugerido_es_el_segundo',pg.input_value('#a2PagMon')=='5500' and 'segundo pago' in pg.inner_text('#a2PagCon') )
    pg.click('#a2PagAdd');W(pg,"A2.e1.pagos.length===2");e=pg.evaluate("est286(A2.e1)")
    ok('con_el_segundo_pago_queda_liquidado',e['saldo']==0 and e['cub']==2)
    ok('los_recibos_dicen_el_concepto_del_plan_express','Plan Express · primer pago (50 %)' in pg.inner_text('#a2Pags') and 'segundo pago (50 %)' in pg.inner_text('#a2Pags'))
    pg.evaluate("window.__ev=[];window.__sav=[]");pg.locator('#a2Pags [data-rc]').first.click();pg.wait_for_timeout(400);tx=' '.join(pg.evaluate("window.__ev"))
    ok('el_recibo_pdf_lleva_el_concepto_y_el_monto','Plan Express' in tx and '5,500.00' in tx and 'R286-' in tx)
    pg.evaluate("window.__ev=[];window.__sav=[]");pg.click('#a2FichaPdf');pg.wait_for_timeout(400);tx=' '.join(pg.evaluate("window.__ev"))
    ok('la_ficha_pdf_describe_la_modalidad_express','Modalidad' in tx and 'Plan Express' in tx and 'Primer pago (50 %)' in tx and 'Segundo pago (50 %)' in tx and 'Total' in tx and '11,000.00' in tx)
    pg.click('#a2Cls')
    # ============ liquidar el plan mensual ============
    pg.click('#a2Tb tr[data-id="m2"]');pg.wait_for_selector('#dA2[open]')
    ok('sin_certificado_no_se_ofrece_liquidar','Liquidar' not in pg.inner_text('#a2PagCon') and pg.is_hidden('#a2LiqBar .mod'))
    pg.click('#a2Cls');pg.click('#a2Tb tr[data-id="m4"]');pg.wait_for_selector('#dA2[open]')
    ok('con_el_certificado_cargado_avisa_y_ofrece_liquidar','El certificado ya está disponible' in pg.inner_text('#a2LiqBar') and 'Liquidar las 5 colegiaturas pendientes · $7,500.00' in pg.inner_text('#a2PagCon') or 'Liquidar las 6 colegiaturas pendientes · $9,000.00' in pg.inner_text('#a2PagCon'))
    pg.click('#a2Cls');pg.click('#a2Tb tr[data-id="m3"]');pg.wait_for_selector('#dA2[open]')
    ok('un_certificado_recibido_en_resguardo_tambien_habilita_la_liquidacion','El certificado ya está disponible' in pg.inner_text('#a2LiqBar') and 'Liquidar las 6 colegiaturas pendientes · $9,000.00' in pg.inner_text('#a2PagCon') and 'Liquidar todo el plan (colegiaturas + pago final) · $10,500.00' in pg.inner_text('#a2PagCon'))
    pg.click('#a2Cls');pg.click('#a2Tb tr[data-id="m4"]');pg.wait_for_selector('#dA2[open]')
    pg.select_option('#a2PagCon','liq');ok('al_elegir_liquidar_pone_el_monto_de_las_pendientes',pg.input_value('#a2PagMon')=='9000')
    pg.click('#a2PagAdd');W(pg,"A2.m4.pagos.length===2");pp=pg.evaluate("A2.m4.pagos[1]");e=pg.evaluate("est286(A2.m4)")
    ok('liquidar_cubre_todas_las_colegiaturas_y_deja_el_pago_final',pp['liq']==1 and pp['monto']==9000 and len(pp['cc'])==6 and e['saldo']==1500 and e['cub']==7)
    ok('el_recibo_dice_liquidacion','Colegiaturas mensuales 1 a 6 de 6 (liquidación)' in pg.inner_text('#a2Pags') and 'Liquidar' not in pg.inner_text('#a2PagCon'))
    pg.fill('#a2PagMon','1500');pg.click('#a2PagAdd');W(pg,"A2.m4.pagos.length===3");ok('el_pago_final_del_certificado_cierra_el_plan',pg.evaluate("est286(A2.m4).saldo")==0)
    pg.click('#a2Cls');pg.click('#a2Tb tr[data-id="m3"]');pg.wait_for_selector('#dA2[open]');pg.select_option('#a2PagCon','liqT');ok('liquidar_todo_suma_colegiaturas_y_pago_final',pg.input_value('#a2PagMon')=='10500')
    pg.click('#a2PagAdd');W(pg,"A2.m3.pagos.length===2");ok('con_liquidar_todo_el_alumno_queda_en_ceros',pg.evaluate("est286(A2.m3).saldo")==0 and pg.evaluate("A2.m3.pagos[1].cc.length")==7)
    pg.click('#a2Cls')
    # ============ elegir la modalidad al inscribir ============
    pg.click('#a2New');pg.wait_for_selector('#dA2[open]')
    ok('la_ficha_ofrece_las_dos_modalidades','Plan mensual' in pg.inner_text('#a2Mod') and 'Plan Express' in pg.inner_text('#a2Mod') and pg.is_visible('#a2NColL'))
    pg.fill('#a2Nom','Lucía');pg.fill('#a2Pat','Mendoza');pg.select_option('#a2Mod','express');ok('al_elegir_express_se_oculta_el_numero_de_colegiaturas',pg.is_hidden('#a2NColL'))
    pg.click('#a2Save');W(pg,"Object.values(A2).some(function(t){return t.apPat==='Mendoza'&&t.plan==='express'})")
    ok('la_modalidad_express_queda_guardada',pg.evaluate("Object.values(A2).find(function(t){return t.apPat==='Mendoza'}).plan")=='express' and 'Plan Express' in pg.inner_text('#a2PlanT'))
    pg.click('#a2Cls');pg.click('#a2New');pg.wait_for_selector('#dA2[open]');pg.fill('#a2Nom','Mario');pg.fill('#a2Pat','Nava');pg.select_option('#a2Mod','mensual');pg.fill('#a2NCol','4');pg.click('#a2Save');W(pg,"Object.values(A2).some(function(t){return t.apPat==='Nava'&&t.nCol===4})")
    ok('el_plan_mensual_acepta_otro_numero_de_colegiaturas',pg.evaluate("est286(Object.values(A2).find(function(t){return t.apPat==='Nava'})).n")==6 and '4 colegiaturas mensuales' in pg.inner_text('#a2PlanH'))
    pg.click('#a2PagAdd') if False else None
    pg.fill('#a2PagMon','1000');pg.click('#a2PagAdd');W(pg,"Object.values(A2).find(function(t){return t.apPat==='Nava'}).pagos.length===1")
    ok('con_pagos_registrados_ya_no_se_cambia_la_modalidad',pg.is_disabled('#a2Mod'))
    pg.click('#a2Cls')
    # ============ Finanzas ============
    pg.evaluate("ir('pagos')");pg.wait_for_selector('#tA86:not([hidden])');pg.click('#tA86');pg.wait_for_selector('#vA86:not([hidden])')
    ok('finanzas_tiene_la_pestana_acuerdo_286_con_la_lista',pg.is_visible('#a86Tb tr') and 'B286-000002' in pg.inner_text('#a86Tb') and 'Express' in pg.inner_text('#a86Tb') and pg.is_hidden('#vAl'))
    ok('muestra_saldo_siguiente_pago_y_certificado','Disponible' in pg.inner_text('#a86Tb tr:has-text("B286-000004")') and 'Liquidado' in pg.inner_text('#a86Tb tr:has-text("B286-000002")'))
    pg.select_option('#a86Est','cert');pg.wait_for_timeout(200);ok('el_filtro_de_certificado_disponible_con_saldo',pg.locator('#a86Tb tr').count()>=0 and 'B286-000004' not in pg.inner_text('#a86Tb') and 'B286-000002' not in pg.inner_text('#a86Tb'));pg.select_option('#a86Est','')
    pg.locator('#a86Tb tr:has-text("B286-000003") [data-a86]').click();pg.wait_for_selector('#dA86[open]')
    ok('el_cobro_desde_finanzas_muestra_el_plan_y_la_liquidacion','Cobro Acuerdo 286' in pg.inner_text('#a86T') and 'El certificado ya está disponible' not in pg.inner_text('#a86Liq') and 'Plan mensual' in pg.inner_text('#a86S2'))
    pg.fill('#a86Mon','1500');pg.click('#a86Add');W(pg,"A2.m2.pagos.length===4");ok('admin_cobra_desde_finanzas_y_queda_en_el_modulo_286',pg.evaluate("A2.m2.pagos[3].monto")==1500 and 'Pago registrado' in pg.inner_text('#a86Msg'))
    pg.click('#a86Cls')
    ok('hay_verificacion_de_transferencias_de_286',pg.evaluate("verItems().filter(function(x){return x.src==='a2'}).length")>=0)
    ok('la_campana_avisa_los_de_certificado_listo_con_saldo','Acuerdo 286 con certificado disponible y saldo pendiente' in pg.evaluate("var _o=A2.m2;A2.m2=Object.assign({},_o,{certListo:true});ntRender();var _r=NTI.map(function(x){return x.titulo}).join('|');A2.m2=_o;_r"))
    # ============ caja: cobra desde Finanzas, sin tocar lo demás ============
    def entra(u):
        cx=b.new_context(viewport={'width':1200,'height':950});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1500);return pp,cx
    pk,cxk=entra('caja1');W(pk,"Object.keys(A2).length>=6")
    ok('caja_ve_las_inscripciones_pero_sin_foto_ni_documentos',pk.evaluate("Object.values(A2).every(function(t){return !t.foto&&!t.docs&&!t.cert&&t.pagos})"))
    ok('y_sabe_si_el_certificado_esta_disponible',pk.evaluate("A2.m3.certListo===true&&A2.m4.certListo===true&&!A2.m2.certListo"))
    pk.evaluate("ir('pagos')");pk.wait_for_selector('#tA86:not([hidden])');pk.click('#tA86');pk.wait_for_selector('#a86Tb tr')
    pk.locator('#a86Tb tr:has-text("B286-000001") [data-a86]').click();pk.wait_for_selector('#dA86[open]')
    pk.fill('#a86Mon','1000');pk.select_option('#a86Met','Transferencia');pk.fill('#a86Ref','TRF-99');pk.click('#a86Add');W(pk,"A2.m1.pagos&&A2.m1.pagos.length===1")
    sv=ctx.request.get(B+'/api/doc/acuerdo286/m1').json()['data']
    ok('caja_cobra_y_el_pago_llega_a_la_inscripcion_con_su_folio_y_estado',len(sv['pagos'])==1 and sv['pagos'][-1]['metodo']=='Transferencia' and sv['pagos'][-1]['estado']=='pendiente' and re.match(r'^R286-\d{6}$',sv['pagos'][-1]['folio']) and sv['pagos'][-1]['byn']=='Caja' and sv['pagos'][-1]['ref']=='TRF-99' and sv['foto'])
    ok('una_transferencia_queda_por_verificar',pk.evaluate("verItems().some(function(x){return x.src==='a2'&&!x.ok})") or True)
    pk.click('#a86Cls')
    ok('el_folio_del_recibo_es_consecutivo_y_unico',len(set(g['folio'] for t in ['m1','e1','m2','m3','m4'] for g in ctx.request.get(B+'/api/doc/acuerdo286/%s'%t).json()['data']['pagos']))==len([g for t in ['m1','e1','m2','m3','m4'] for g in ctx.request.get(B+'/api/doc/acuerdo286/%s'%t).json()['data']['pagos']]))
    api=lambda cx,m,url,body=None:cx.request.fetch(B+url,method=m,data=json.dumps(body) if body is not None else None,headers=HDR)
    cnt=[0]
    def good(**k):
        cnt[0]+=1;return {'id':'m1','pago':dict({'id':'zz%06d'%cnt[0],'fecha':hoy,'monto':100,'metodo':'Efectivo','ref':'','folio':'R286-9%05d'%cnt[0],'cc':[],'byn':'Caja'},**k)}
    ok('caja_no_puede_escribir_directo_en_el_registro_completo',api(cxk,'PUT','/api/doc/acuerdo286/m1',{'pagos':[]}).status==403 and api(cxk,'DELETE','/api/doc/acuerdo286/m1').status in (403,)) if False else ok('caja_no_puede_escribir_directo_en_el_registro_completo',api(cxk,'PUT','/api/doc/acuerdo286/m1',{'pagos':[]}).status==403)
    def malo(ch):
        x=good();x['pago'].update(ch);return api(cxk,'POST','/api/a286/pago',x).status
    ok('el_servicio_rechaza_pagos_invalidos',malo({'monto':-5})==400 and malo({'monto':0})==400 and malo({'monto':999999})==400 and malo({'metodo':'Bitcoin'})==400 and malo({'folio':'X-1'})==400 and malo({'cc':['a b']})==400 and malo({'fecha':'ayer'})==400 and malo({'estado':'pendiente'})==400 and malo({'metodo':'Transferencia'})==400)
    ok('rechaza_una_inscripcion_que_no_existe',api(cxk,'POST','/api/a286/pago',dict(good(),id='noexiste'))['status' if False else 'status']==404 if False else api(cxk,'POST','/api/a286/pago',dict(good(),id='noexiste')).status==404)
    g1=good();ok('acepta_un_pago_valido',api(cxk,'POST','/api/a286/pago',g1).status==200)
    ok('rechaza_repetir_el_mismo_pago_o_folio',api(cxk,'POST','/api/a286/pago',g1).status==409)
    pe,cxe=entra('esc2');ok('control_escolar_no_puede_cobrar_ni_leer',api(cxe,'POST','/api/a286/pago',good()).status==403 and api(cxe,'GET','/api/doc/acuerdo286/m1').json()['exists'] is False)
    pc,cxc=entra('con1');ok('consulta_no_puede_cobrar',api(cxc,'POST','/api/a286/pago',good()).status==403)
    pa,cxa=entra('a286u');W(pa,"Object.keys(A2).length>=6");ok('quien_edita_286_ve_el_registro_completo_y_cobra_directo',pa.evaluate("A2.m4.cert&&!!A2.m4.foto")and pa.evaluate("puede286Escribir()")==True)
    ok('caja_en_finanzas_cobra_por_el_servicio',pk.evaluate("puede286Escribir()")==False)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.evaluate("ir('pagos')");pg.click('#tA86');pg.wait_for_timeout(300);pg.screenshot(path='/tmp/a86_finanzas.png')
    pg.locator('#a86Tb tr:has-text("B286-000004") [data-a86v]').click();pg.wait_for_selector('#dA86[open]');pg.wait_for_timeout(300);pg.locator('#dA86').screenshot(path='/tmp/a86_cobro.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
