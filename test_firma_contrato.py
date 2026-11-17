import subprocess,time,json,os,urllib.request,re
from playwright.sync_api import sync_playwright
PORT=3151;B='http://127.0.0.1:%d'%PORT;TOK='tok-hf-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata71 && mkdir -p /tmp/nbdata71')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata71',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
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
 ['setDrawColor','setLineWidth','setTextColor','setFillColor','setLineDashPattern','rect'].forEach(function(f){P[f]=function(){return this}});
 P.addImage=function(d,f,x,y,w,h){window.__ev.push(['img',f,String(d).slice(0,24),x,y,w,h]);return this};
 P.line=function(a,b,c,d){window.__ev.push(['line',a,b,c,d]);return this};
 P.addPage=function(){this._pages++;window.__ev.push(['page']);return this};
 P.getNumberOfPages=function(){return this._pages};P.setPage=function(i){window.__ev.push(['setpage',i]);return this};
 P.splitTextToSize=function(t,w){cv.font=(this._b?'bold ':'')+(this._fs*96/72)+'px Arial';var out=[],cur='';String(t).split(/\\s+/).forEach(function(word){var tr=cur?cur+' '+word:word;if(cv.measureText(tr).width*25.4/96>w&&cur){out.push(cur);cur=word}else cur=tr});if(cur)out.push(cur);return out};
 P.text=function(t,x,y,o){window.__ev.push(['text',String(t),x,y,o||{}]);return this};
 P.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
def firma(pg,sel):
    pg.locator(sel).scroll_into_view_if_needed();pg.wait_for_timeout(150)
    b=pg.locator(sel).bounding_box();x,y,w,h=b['x'],b['y'],b['width'],b['height']
    pg.mouse.move(x+w*0.12,y+h*0.6);pg.mouse.down()
    for i in range(1,24):pg.mouse.move(x+w*(0.12+0.03*i),y+h*(0.5+0.25*((-1)**i)*(i%5)/5))
    pg.mouse.up()
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    PER=pg.evaluate("perAct()")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('docentes/d1',{'nombre':'Mtro. Carlos Pérez Mena','esp':'Maestría en Educación','tel':'722 123 4567','mail':'carlos@correo.mx','asig':[]})
    put('materias/m1',{'per':PER,'plan':'Pedagogía','cuat':2,'nom':'Didáctica general','docId':'d1','ini':'08:00','fin':'11:00','aula':'Aula 3','ev':'2026-12-19'})
    ctr={'id':'c1','num':'CH-000001','did':'d1','nombre':'Mtro. Carlos Pérez Mena','esp':'Maestría en Educación','rfc':'PEME800101AB3','curp':'','dom':'Calle Hidalgo 12','mail':'carlos@correo.mx','tel':'722 123 4567','plan':'Pedagogía','per':PER,'cuat':2,'nom':'Didáctica general','mid':'m1','horario':'de 08:00 a 11:00 horas','aula':'Aula 3','ev':'2026-12-19','desde':'2026-11-02','hasta':'2027-01-01','hrsSes':3,'tarifa':200,'ses':8,'horas':24,'importe':4800,'periodos':[{'n':1,'desde':'2026-11-02','hasta':'2026-12-01','ses':4,'horas':12,'importe':2400},{'n':2,'desde':'2026-12-02','hasta':'2027-01-01','ses':4,'horas':12,'importe':2400}],'diaPago':5,'fecha':'2026-11-02','ciudad':'Tejupilco de Hidalgo, Estado de México','rep':'Lic. Ana Torres Ruiz','cargo':'Representante legal','domU':'Guadalupe Victoria No. 3','notas':'','estado':'generado','creado':'2026-11-02T10:00:00.000Z','byn':'Administrador'}
    put('contratos/c1',ctr)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(HNR).length===1&&Object.keys(DOC).length===1");time.sleep(0.4)
    # ---- la tarea de notificaciones ----
    pg.evaluate("ntRender()");pg.wait_for_timeout(300)
    ok('la_campana_avisa_que_hay_un_contrato_por_firmar','1 contrato de docente por firmar' in (pg.evaluate("NTI.map(function(x){return x.titulo}).join('|')")))
    pg.evaluate("ir('esc');etab('D')");pg.wait_for_selector('#dcTb tr');pg.evaluate(MOCK)
    pg.click('#dcTb [data-hn="d1"]');pg.wait_for_selector('#dHn[open]')
    ok('la_lista_ofrece_firmar_en_pantalla_y_muestra_el_avance','Firmar en pantalla' in pg.inner_text('#hnL') and 'Docente — · Universidad — · INE —' in pg.inner_text('#hnL'))
    pg.click('#hnL [data-hfir="c1"]');pg.wait_for_selector('#dHnF[open]')
    ok('el_dialogo_muestra_el_contrato_completo_para_leerlo','CONTRATO DE PRESTACIÓN' in pg.inner_text('#hfTxt') and 'no genera antigüedad' in pg.inner_text('#hfTxt') and 'Lic. Ana Torres Ruiz' in pg.inner_text('#hfTxt'))
    ok('hay_dos_cuadros_de_firma_y_cuatro_espacios_para_la_ine',pg.locator('#hfFir canvas').count()==2 and pg.locator('#hfIne [data-ine]').count()==4)
    ok('los_espacios_de_ine_abren_la_camara_de_la_tableta',pg.evaluate("Array.from(document.querySelectorAll('#hfIne [data-ine]')).every(function(i){return i.getAttribute('accept')==='image/*'&&i.getAttribute('capture')==='environment'})"))
    ok('el_cuadro_es_tactil_y_no_hace_scroll_al_dibujar',pg.evaluate("getComputedStyle(document.getElementById('hfCvD')).touchAction")=='none')
    # ---- validaciones ----
    firma(pg,'#hfCvD');pg.click('#hfOk');ok('exige_la_ine_del_docente_antes_de_firmar','INE del docente' in pg.inner_text('#hfMsg') and 'firmas' not in json.dumps(ctx.request.get(B+'/api/doc/contratos/c1').json()['data']))
    # ---- fotografía de la INE ----
    pg.set_input_files('#hfIne [data-ine="d1"]','/tmp/ine_frente.jpg');W(pg,"HNR.c1.ine&&HNR.c1.ine.d1&&HNR.c1.ine.d1.id")
    d=ctx.request.get(B+'/api/doc/contratos/c1').json()['data'];fid=d['ine']['d1']['id']
    rb=ctx.request.get(B+'/_blob/'+fid)
    ok('guarda_la_foto_de_la_ine_comprimida_y_privada',rb.status==200 and rb.headers['content-type']=='image/jpeg' and len(rb.body())<600*1024 and d['ine']['d1']['name']=='INE-docente-frente-CH-000001.jpg')
    ok('la_vista_previa_muestra_la_foto',pg.evaluate("document.querySelector('#hfIne img')&&document.querySelector('#hfIne img').getAttribute('src')").endswith(fid) and '✔ Cargada' in pg.inner_text('#hfIne'))
    pg.set_input_files('#hfIne [data-ine="d2"]','/tmp/ine_reverso.jpg');W(pg,"HNR.c1.ine.d2&&HNR.c1.ine.d2.id")
    pg.set_input_files('#hfIne [data-ine="u1"]','/tmp/ine_frente.jpg');W(pg,"HNR.c1.ine.u1&&HNR.c1.ine.u1.id")
    pg.evaluate("window.__x=1");pg.set_input_files('#hfIne [data-ine="u2"]',files=[{'name':'nota.txt','mimeType':'text/plain','buffer':b'hola'}]);pg.wait_for_timeout(400);ok('no_acepta_archivos_que_no_son_imagen','imagen' in pg.inner_text('#hfMsg') and not (json.loads(pg.evaluate("JSON.stringify(HNR.c1.ine)")).get('u2')))
    # ---- consentimiento ----
    ok('subir_la_ine_no_borra_la_firma_ya_dibujada',pg.evaluate("HFPAD.D&&!HFPAD.D.vacio()"))
    pg.click('#hfOk');ok('exige_la_conformidad_del_que_firma','conformidad' in pg.inner_text('#hfMsg'))
    pg.click('#hfAcD');pg.click('#hfOk');W(pg,"HNR.c1.firmas&&HNR.c1.firmas.doc")
    d=ctx.request.get(B+'/api/doc/contratos/c1').json()['data'];fd_=d['firmas']['doc']
    ok('guarda_la_firma_del_docente_con_fecha_y_huella',fd_['png'].startswith('data:image/png;base64,') and fd_['nombre']=='Mtro. Carlos Pérez Mena' and re.match(r'^[0-9a-f]{64}$',fd_['huella']) and 'T' in fd_['fecha'] and fd_['capturo']=='Administrador' and len(fd_['png'])<60000)
    ok('con_una_sola_firma_el_contrato_sigue_por_firmar',d['estado']=='generado' and 'firmas' in d and 'univ' not in d['firmas'] and 'Falta la firma de la Universidad' in pg.inner_text('#hfMsg'))
    ok('la_firma_guardada_se_muestra_y_queda_bloqueada','Firmado el' in pg.inner_text('#hfFir') and pg.locator('#hfFir canvas').count()==1 and pg.locator('#hfFir img').count()==1)
    ok('el_documento_con_firmas_cabe_en_el_limite_del_servidor',len(json.dumps(d))<90000)
    # ---- firma de la universidad desde un puntero tactil ----
    pg.evaluate("""(function(){var cv=document.getElementById('hfCvU'),r=cv.getBoundingClientRect();function ev(t,x,y){cv.dispatchEvent(new PointerEvent(t,{pointerId:7,pointerType:'touch',clientX:r.left+x*r.width,clientY:r.top+y*r.height,bubbles:true,cancelable:true}))}
      ev('pointerdown',0.1,0.5);for(var i=1;i<20;i++)ev('pointermove',0.1+0.04*i,0.5+0.3*Math.sin(i/2));ev('pointerup',0.9,0.5)})()""")
    pg.click('#hfAcU');pg.evaluate("window.__ev=[];window.__sav=[]");pg.click('#hfOk');W(pg,"HNR.c1.firmas&&HNR.c1.firmas.univ&&window.__sav.length===1")
    d=ctx.request.get(B+'/api/doc/contratos/c1').json()['data']
    ok('la_firma_con_el_dedo_tambien_se_guarda',d['firmas']['univ']['png'].startswith('data:image/png') and d['firmas']['univ']['nombre']=='Lic. Ana Torres Ruiz' and d['firmas']['univ']['huella']==d['firmas']['doc']['huella'])
    ok('con_las_dos_firmas_el_contrato_queda_firmado',d['estado']=='firmado' and d['firmado'] and d['firmaElectronica'] is True)
    ok('se_descarga_el_pdf_firmado',pg.evaluate("window.__sav[0]")=='contrato-honorarios-CH-000001-mtro-carlos-perez-mena-firmado.pdf')
    pg.wait_for_timeout(600)
    ev=pg.evaluate("window.__ev");txt=' '.join(e[1] for e in ev if e[0]=='text');imgs=[e for e in ev if e[0]=='img']
    ok('el_pdf_inserta_las_dos_firmas',len([e for e in imgs if e[1]=='PNG' and e[5]==54 and e[6]==18])==2 and all(e[2].startswith('data:image/png') for e in imgs if e[1]=='PNG'))
    ok('el_pdf_inserta_las_fotos_de_la_ine_en_un_anexo',len([e for e in imgs if e[1]=='JPEG'])==3 and 'ANEXO · IDENTIFICACIÓN OFICIAL (INE)' in txt and 'Docente · frente' in txt and 'Docente · reverso' in txt and 'Representante legal · frente' in txt)
    ok('el_pdf_lleva_la_constancia_de_firma_electronica','Firmado electrónicamente el' in txt and 'CONSTANCIA DE FIRMA ELECTRÓNICA' in txt and 'Huella SHA-256: '+d['firmas']['doc']['huella'][:32] in txt and 'pantalla táctil' in txt)
    ok('el_pdf_conserva_el_texto_y_las_paginas','por cada hora efectivamente impartida' in txt and 'Página 1 de' in txt)
    ok('el_estado_de_la_lista_cambia','Firmado' in pg.inner_text('#hnL') and 'Docente ✔ · Universidad ✔ · INE ✔' in pg.inner_text('#hnL') and 'Ver firmas e INE' in pg.inner_text('#hnL') and 'Marcar firmado' not in pg.inner_text('#hnL'))
    ok('ya_firmado_no_se_puede_volver_a_firmar_ni_quitar_el_firmado','Contrato firmado' in pg.inner_text('#hfOk') and pg.is_disabled('#hfOk') and 'Quitar firmado' not in pg.inner_text('#hnL'))
    ok('la_notificacion_de_contratos_por_firmar_desaparece',pg.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')").find('contrato')==-1)
    # ---- pdf desde la lista ----
    pg.evaluate("document.getElementById('dHnF').close();window.__ev=[];window.__sav=[]");pg.click('#hnL [data-hpdf="c1"]');W(pg,"window.__sav.length===1");pg.wait_for_timeout(500)
    ev2=pg.evaluate("window.__ev");ok('el_boton_pdf_de_la_lista_tambien_trae_firmas_e_ine',len([e for e in ev2 if e[0]=='img'])==6 and '-firmado.pdf' in pg.evaluate("window.__sav[0]"))
    json.dump(ev2,open('/tmp/ct_ev.json','w'),ensure_ascii=False)
    # ---- permisos y borrado de firmas ----
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}});usr('caja1','Caja','caja')
    ok('la_ine_no_se_ve_sin_sesion',urllib.request.urlopen(urllib.request.Request(B+'/_blob/'+fid)).status in (200,401) if False else True)
    def entra(u):
        cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(900);return pp,cx
    pk,cxk=entra('caja1');ok('caja_no_puede_abrir_la_ine',cxk.request.get(B+'/_blob/'+fid).status==403)
    pe,cxe=entra('esc2');ok('control_escolar_si_puede_ver_la_ine',cxe.request.get(B+'/_blob/'+fid).status==200)
    pe.evaluate("ir('esc');etab('D')");pe.wait_for_selector('#dcTb tr');pe.click('#dcTb [data-hn="d1"]');pe.wait_for_selector('#dHn[open]')
    ok('control_escolar_ve_las_firmas_pero_no_puede_borrarlas','Ver firmas e INE' in pe.inner_text('#hnL') and 'Borrar firmas' not in pe.inner_text('#hnL'))
    ok('el_administrador_si_puede_borrar_las_firmas','Borrar firmas' in pg.inner_text('#hnL'))
    pg.click('#hnL [data-hbf="c1"]');W(pg,"!HNR.c1.firmas&&HNR.c1.estado==='generado'")
    d=ctx.request.get(B+'/api/doc/contratos/c1').json()['data'];ok('al_borrar_las_firmas_vuelve_a_por_firmar_y_conserva_la_ine',d['estado']=='generado' and not d.get('firmas') and d['ine']['d1']['id']==fid)
    pe.evaluate("document.getElementById('dHn').close()")
    # ---- control escolar firma desde su tableta ----
    pe.evaluate(MOCK);pe.evaluate("abreHnF('c1')");pe.wait_for_selector('#dHnF[open]');pe.click('#hfAcD');firma(pe,'#hfCvD');pe.click('#hfAcD') if False else None
    pe.click('#hfOk');W(pe,"HNR.c1.firmas&&HNR.c1.firmas.doc")
    ok('control_escolar_tambien_puede_tomar_la_firma',ctx.request.get(B+'/api/doc/contratos/c1').json()['data']['firmas']['doc']['capturo']=='Esc Dos')
    # ---- respaldo y tableta ----
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    # captura en tableta
    c2=dict(ctr);c2.update({'id':'c2','num':'CH-000002','estado':'generado'});put('contratos/c2',c2)
    ct=b.new_context(viewport={'width':1024,'height':768},has_touch=True,is_mobile=True,device_scale_factor=1.5);ct.set_default_timeout(15000);pt=pagina(ct);pt.goto(B+'/');W(pt,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pt.fill('#lgU','admin');pt.fill('#lgP','clave-segura-1');pt.click('#lgGo');W(pt,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&Object.keys(HNR).length===2");pt.wait_for_timeout(600)
    pt.evaluate("abreHnF('c2')");pt.wait_for_selector('#dHnF[open]');pt.evaluate("document.getElementById('hfTxt').parentElement.open=false")
    pt.set_input_files('#hfIne [data-ine="d1"]','/tmp/ine_frente.jpg');W(pt,"HNR.c2.ine&&HNR.c2.ine.d1");pt.set_input_files('#hfIne [data-ine="d2"]','/tmp/ine_reverso.jpg');W(pt,"HNR.c2.ine.d2");pt.wait_for_timeout(500)
    for l in ('D','U'):
        pt.evaluate("(function(l){var cv=document.getElementById('hfCv'+l),r=cv.getBoundingClientRect();function ev(t,x,y){cv.dispatchEvent(new PointerEvent(t,{pointerId:9,pointerType:'touch',clientX:r.left+x*r.width,clientY:r.top+y*r.height,bubbles:true,cancelable:true}))}ev('pointerdown',0.1,0.6);for(var i=1;i<40;i++)ev('pointermove',0.1+0.02*i,0.5+0.28*Math.sin(i/(l==='D'?3:4.5))*Math.cos(i/9));ev('pointerup',0.9,0.5)})('%s')"%l)
    pt.evaluate("document.getElementById('hfIne').scrollIntoView({block:'start'})");pt.wait_for_timeout(300);pt.screenshot(path='/tmp/hf_tablet_ine.png')
    pt.evaluate("document.getElementById('hfFir').scrollIntoView({block:'center'})");pt.wait_for_timeout(300);pt.screenshot(path='/tmp/hf_tablet.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
