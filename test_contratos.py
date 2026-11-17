import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3150;B='http://127.0.0.1:%d'%PORT;TOK='tok-hn-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata70 && mkdir -p /tmp/nbdata70')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata70',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
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
 P.setFont=function(f,s){this._b=(s==='bold');window.__ev.push(['font',this._b]);return this};
 P.setFontSize=function(n){this._fs=n;window.__ev.push(['fs',n]);return this};
 ['setDrawColor','setLineWidth','setTextColor','setFillColor','setLineDashPattern','addImage','rect'].forEach(function(f){P[f]=function(){return this}});
 P.line=function(a,b,c,d){window.__ev.push(['line',a,b,c,d]);return this};
 P.addPage=function(){this._pages++;window.__ev.push(['page']);return this};
 P.getNumberOfPages=function(){return this._pages};P.setPage=function(i){window.__ev.push(['setpage',i]);return this};
 P.splitTextToSize=function(t,w){cv.font=(this._b?'bold ':'')+(this._fs*96/72)+'px Arial';var out=[],cur='';String(t).split(/\\s+/).forEach(function(word){var tr=cur?cur+' '+word:word;if(cv.measureText(tr).width*25.4/96>w&&cur){out.push(cur);cur=word}else cur=tr});if(cur)out.push(cur);return out};
 P.text=function(t,x,y,o){window.__ev.push(['text',String(t),x,y,o||{}]);return this};
 P.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    PER=pg.evaluate("perAct()")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('docentes/d1',{'nombre':'Mtro. Carlos Pérez Mena','esp':'Maestría en Educación','tel':'722 123 4567','mail':'carlos@correo.mx','asig':[{'plan':'Pedagogía','per':PER,'cuat':2,'nom':'Didáctica general','ses':8}]})
    put('materias/m1',{'per':PER,'plan':'Pedagogía','cuat':2,'nom':'Didáctica general','docId':'d1','ini':'08:00','fin':'11:00','aula':'Aula 3','ev':'2026-12-19'})
    put('config/nomina',{'base':120,'esp':150,'planes':{},'docentes':{'d1':200}})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(DOC).length===1&&Object.keys(MAT).length===1&&NOMC.docentes&&NOMC.docentes.d1===200");time.sleep(0.5)
    pg.evaluate("ir('esc');etab('D')");pg.wait_for_selector('#dcTb tr');pg.evaluate(MOCK)
    ok('el_admin_ve_el_boton_contrato_en_cada_docente',pg.is_visible('#dcTb [data-hn="d1"]') and 'Contrato' in pg.inner_text('#dcTb'))
    pg.click('#dcTb [data-hn="d1"]');pg.wait_for_selector('#dHn[open]')
    ok('el_dialogo_lleva_el_nombre_del_docente','Mtro. Carlos Pérez Mena' in pg.inner_text('#hnT') and 'Todavía no hay contratos' in pg.inner_text('#hnS'))
    ok('lista_la_asignatura_del_docente','Didáctica general · Pedagogía' in pg.inner_text('#hnAs'))
    ok('toma_horas_y_tarifa_del_sistema',pg.input_value('#hnHs')=='3' and pg.input_value('#hnTa')=='200' and 'del docente' in pg.inner_text('#hnTaH') and '08:00 a 11:00' in pg.inner_text('#hnHsH'))
    ok('avisa_la_fecha_de_evaluacion_y_que_son_sabados','sábados' in pg.inner_text('#hnInfo') and '19/12/2026' in pg.inner_text('#hnInfo') and '8 sesiones registradas' in pg.inner_text('#hnInfo'))
    ok('la_duracion_por_defecto_es_de_2_meses',pg.input_value('#hnHa')==pg.evaluate("addDias(addMeses(document.getElementById('hnDe').value,2),-1)"))
    pg.fill('#hnDe','2026-11-02');ok('al_cambiar_el_inicio_se_recorre_el_termino',pg.input_value('#hnHa')=='2027-01-01')
    t=pg.inner_text('#hnPer')
    ok('divide_en_meses_de_servicio_con_sus_sabados','Mes de servicio' in t and pg.locator('#hnPer tbody tr').count()==2 and pg.input_value('#hnPer [data-hp="0"]')=='4' and pg.input_value('#hnPer [data-hp="1"]')=='4' and '02/11/2026' in t and '01/12/2026' in t and '02/12/2026' in t and '01/01/2027' in t)
    r=pg.inner_text('#hnRes');ok('resume_horas_y_honorarios','dos meses' in r and '8 sesiones' in r and '24 horas' in r and '$4,800.00' in r and '$200.00 por hora' in r)
    pg.fill('#hnPer [data-hp="1"]','3');pg.wait_for_timeout(200);r=pg.inner_text('#hnRes');ok('se_pueden_ajustar_las_sesiones_de_cada_mes','7 sesiones' in r and '21 horas' in r and '$4,200.00' in r and '$1,800.00' in pg.inner_text('#hnPer'))
    pg.fill('#hnPer [data-hp="1"]','4')
    # ---- validaciones ----
    pg.fill('#hnRep','');pg.click('#hnOk');ok('exige_el_representante_legal','representante legal' in pg.inner_text('#hnMsg') and pg.evaluate("Object.keys(HNR).length")==0)
    pg.fill('#hnRep','Lic. Ana Torres Ruiz');pg.fill('#hnTa','0');pg.click('#hnOk');ok('exige_la_tarifa','tarifa por hora' in pg.inner_text('#hnMsg'));pg.fill('#hnTa','200')
    pg.fill('#hnHa','2026-10-01');pg.click('#hnOk');ok('no_acepta_un_termino_anterior_al_inicio','fechas' in pg.inner_text('#hnMsg'));pg.fill('#hnHa','2027-01-01')
    pg.fill('#hnDp','31');pg.click('#hnOk');ok('el_dia_de_pago_va_del_1_al_28','1 al 28' in pg.inner_text('#hnMsg'));pg.fill('#hnDp','5')
    # ---- crear ----
    pg.fill('#hnRfc','peme800101ab3');pg.fill('#hnCurp','');pg.fill('#hnDom','Calle Hidalgo 12, Centro, Tejupilco, Edo. de México, C.P. 51400');pg.fill('#hnNo','EL PRESTADOR deberá entregar un informe final de resultados.')
    pg.evaluate("window.__ev=[];window.__sav=[]");pg.click('#hnOk');W(pg,"Object.keys(HNR).length===1&&window.__sav.length===1")
    c=json.loads(pg.evaluate("JSON.stringify(Object.values(HNR)[0])"));
    ok('crea_el_contrato_con_folio_consecutivo',c['num']=='CH-000001' and c['estado']=='generado' and c['did']=='d1' and c['nom']=='Didáctica general')
    ok('guarda_horas_tarifa_y_total',c['hrsSes']==3 and c['tarifa']==200 and c['ses']==8 and c['horas']==24 and c['importe']==4800 and len(c['periodos'])==2 and c['periodos'][0]['importe']==2400)
    ok('guarda_las_partes_y_el_pago_mensual',c['rep']=='Lic. Ana Torres Ruiz' and c['diaPago']==5 and c['rfc']=='PEME800101AB3' and c['desde']=='2026-11-02' and c['hasta']=='2027-01-01' and c['aula']=='Aula 3' and c['horario']=='de 08:00 a 11:00 horas' and c['ev']=='2026-12-19')
    sv=ctx.request.get(B+'/api/doc/contratos/'+c['id']).json()['data'];ok('queda_guardado_en_el_servidor',sv['num']=='CH-000001' and sv['importe']==4800)
    dd=ctx.request.get(B+'/api/doc/docentes/d1').json()['data'];ok('los_datos_fiscales_se_guardan_en_el_docente',dd['rfc']=='PEME800101AB3' and 'Hidalgo 12' in dd['dom'] and dd['asig'][0]['nom']=='Didáctica general')
    ok('descarga_el_pdf_con_su_nombre',pg.evaluate("window.__sav[0]")=='contrato-honorarios-CH-000001-mtro-carlos-perez-mena.pdf')
    ev=pg.evaluate("window.__ev");txt=' '.join(e[1] for e in ev if e[0]=='text')
    ok('el_pdf_dice_que_es_por_honorarios_temporal_y_por_asignatura','CONTRATO DE PRESTACIÓN DE SERVICIOS PROFESIONALES POR HONORARIOS, TEMPORAL Y POR ASIGNATURA' in ' '.join(e[1] for e in ev if e[0]=='text') or 'POR HONORARIOS, TEMPORAL' in txt)
    ok('el_pdf_nombra_las_partes_y_la_asignatura','Lic. Ana Torres Ruiz' in txt and 'Mtro. Carlos Pérez Mena' in txt and 'Didáctica general' in txt and 'Pedagogía' in txt and 'PEME800101AB3' in txt)
    ok('el_pdf_fija_la_vigencia_de_dos_meses','dos meses' in txt and '2 de noviembre de 2026' in txt and '1 de enero de 2027' in txt and 'no se prorroga ni se renueva' in txt)
    ok('el_pdf_pacta_el_pago_por_hora','por cada hora efectivamente impartida' in txt and '$200.00' in txt and 'DOSCIENTOS PESOS 00/100 M.N.' in txt and '24 horas' in txt and '$4,800.00' in txt and 'CUATRO MIL OCHOCIENTOS PESOS 00/100 M.N.' in txt)
    ok('el_pdf_pacta_el_pago_mensual','de manera mensual' in txt and 'a más tardar el día 5 del mes siguiente' in txt and 'Mes de servicio 1: del 02/11/2026 al 01/12/2026' in txt and 'Mes de servicio 2: del 02/12/2026 al 01/01/2027' in txt and 'CFDI' in txt)
    ok('el_pdf_aclara_que_no_hay_relacion_laboral_ni_antiguedad','no existe relación de trabajo' in txt and 'no genera antigüedad' in txt and 'aguinaldo' in txt and 'Código Civil' in txt)
    ok('el_pdf_incluye_horario_aula_evaluacion_y_notas','de 08:00 a 11:00 horas' in txt and 'Aula 3' in txt and '19/12/2026' in txt and 'informe final de resultados' in txt and 'CLÁUSULA ADICIONAL' in txt)
    ok('el_pdf_lleva_firmas_folio_y_paginas','LA UNIVERSIDAD' in txt and 'EL PRESTADOR' in txt and 'CH-000001' in txt and 'Página 1 de' in txt and 'asesor jurídico' not in txt)
    json.dump(ev,open('/tmp/ct_ev.json','w'),ensure_ascii=False)
    # ---- lista, firma y cancelación ----
    pg.wait_for_timeout(300);tl=pg.inner_text('#hnL')
    ok('la_lista_muestra_el_contrato','CH-000001' in tl and 'Didáctica general' in tl and 'Por firmar' in tl and '24 h × $200.00' in tl and '$4,800.00' in tl and pg.is_visible('#hnL [data-hpdf]'))
    pg.evaluate("window.__sav=[]");pg.click('#hnL [data-hpdf]');pg.wait_for_timeout(300);ok('se_puede_descargar_de_nuevo',pg.evaluate("window.__sav.length")==1)
    pg.click('#hnL [data-hfi]');W(pg,"Object.values(HNR)[0].estado==='firmado'");ok('marcar_firmado',ctx.request.get(B+'/api/doc/contratos/'+c['id']).json()['data']['estado']=='firmado' and 'Firmado' in pg.inner_text('#hnL'))
    pg.click('#hnL [data-hde]');W(pg,"Object.values(HNR)[0].estado==='generado'");ok('quitar_firmado_lo_regresa_a_por_firmar','Por firmar' in pg.inner_text('#hnL'))
    # segundo contrato: folio consecutivo
    pg.fill('#hnDe','2027-01-09');pg.fill('#hnHa','2027-03-08');pg.fill('#hnRep','Lic. Ana Torres Ruiz');pg.click('#hnOk');W(pg,"Object.keys(HNR).length===2")
    ok('el_segundo_contrato_toma_el_folio_siguiente',sorted(x['num'] for x in json.loads(pg.evaluate("JSON.stringify(Object.values(HNR))")))==['CH-000001','CH-000002'])
    ok('recuerda_al_representante_para_el_siguiente','Lic. Ana Torres Ruiz' in pg.input_value('#hnRep'))
    pg.locator('#hnL [data-hca]').first.click();W(pg,"Object.values(HNR).some(function(x){return x.estado==='cancelado'})");ok('cancelar_deja_el_registro','Cancelado' in pg.inner_text('#hnL'))
    pg.evaluate("document.getElementById('dHn').close()")
    ok('el_respaldo_incluye_los_contratos_y_su_folio',pg.evaluate("BKCOL.indexOf('contratos')>-1&&BKDOC.indexOf('meta/folioCH')>-1"))
    ok('editar_al_docente_no_borra_su_rfc',True)
    pg.evaluate("document.querySelector('#dcTb [data-ed=\"d1\"]').click()");pg.click('#dcAdd');pg.wait_for_timeout(600)
    ok('editar_al_docente_no_borra_su_rfc',ctx.request.get(B+'/api/doc/docentes/d1').json()['data']['rfc']=='PEME800101AB3')
    # ---- permisos ----
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}});usr('caja1','Caja','caja');usr('con1','Consulta','consulta')
    def entra(u):
        cx=b.new_context(viewport={'width':1200,'height':900});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(900);return pp,cx
    pe,cxe=entra('esc2');pe.evaluate("ir('esc');etab('D')");pe.wait_for_selector('#dcTb tr');pe.evaluate(MOCK)
    ok('control_escolar_ve_el_boton_y_los_contratos',pe.is_visible('#dcTb [data-hn="d1"]') and pe.evaluate("Object.keys(HNR).length")==2)
    pe.click('#dcTb [data-hn="d1"]');pe.wait_for_selector('#dHn[open]');pe.fill('#hnDe','2027-02-06');pe.fill('#hnHa','2027-04-05');pe.fill('#hnRep','Lic. Ana Torres Ruiz');ok('avisa_si_el_usuario_no_ve_las_tarifas_de_nomina','confirma que esta sea la correcta' in pe.inner_text('#hnTaH'));pe.click('#hnOk');W(pe,"Object.keys(HNR).length===3");ok('y_puede_crear_contratos_con_folio_consecutivo',any(x['num']=='CH-000003' for x in json.loads(pe.evaluate("JSON.stringify(Object.values(HNR))"))))
    pk,cxk=entra('caja1');pk.evaluate("ir('home')");ok('caja_no_ve_contratos',pk.evaluate("typeof puedeHn==='function'&&puedeHn()")==False and len(json.loads(pk.evaluate("JSON.stringify(Object.values(HNR))")))==0)
    pc,cxc=entra('con1');ok('consulta_tampoco',pc.evaluate("puedeHn()")==False and len(json.loads(pc.evaluate("JSON.stringify(Object.values(HNR))")))==0)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.evaluate("ir('esc');etab('D')");pg.click('#dcTb [data-hn=\"d1\"]');pg.wait_for_selector('#dHn[open]');pg.wait_for_timeout(300);pg.locator('#dHn').screenshot(path='/tmp/ct_dialogo.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
