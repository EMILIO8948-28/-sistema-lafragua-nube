import subprocess,time,json,os,urllib.request,re,datetime
from playwright.sync_api import sync_playwright
PORT=3180;B='http://127.0.0.1:%d'%PORT;TOK='tok-fz-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata92 && mkdir -p /tmp/nbdata92')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata92',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
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
 P.setFont=function(f,s){this._b=(s==='bold');return this};
 P.setFontSize=function(n){this._fs=n;return this};
 ['setDrawColor','setLineWidth','setTextColor','setFillColor','setLineDashPattern','rect'].forEach(function(f){P[f]=function(){return this}});
 P.addImage=function(d,f,x,y,w,h){window.__ev.push(['img',f,String(d).slice(0,24),x,y,w,h]);return this};
 P.line=function(a,b,c,d){window.__ev.push(['line',a,b,c,d]);return this};
 P.addPage=function(){this._pages++;window.__ev.push(['page']);return this};
 P.getNumberOfPages=function(){return this._pages};P.setPage=function(i){return this};
 P.splitTextToSize=function(t,w){cv.font=(this._b?'bold ':'')+(this._fs*96/72)+'px Arial';var out=[],cur='';String(t).split(/\\s+/).forEach(function(word){var tr=cur?cur+' '+word:word;if(cv.measureText(tr).width*25.4/96>w&&cur){out.push(cur);cur=word}else cur=tr});if(cur)out.push(cur);return out};
 P.text=function(t,x,y,o){window.__ev.push(['text',String(t),x,y,o||{}]);return this};
 P.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
def firma(pg,sel):
    pg.locator(sel).scroll_into_view_if_needed();pg.wait_for_timeout(150);b=pg.locator(sel).bounding_box();x,y,w,h=b['x'],b['y'],b['width'],b['height']
    pg.mouse.move(x+w*0.12,y+h*0.6);pg.mouse.down()
    for i in range(1,24):pg.mouse.move(x+w*(0.12+0.03*i),y+h*(0.5+0.25*((-1)**i)*(i%5)/5))
    pg.mouse.up()
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    PER=pg.evaluate("perAct()");CIC=pg.evaluate("cicloAct()")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':[]})
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('ins2','Recepción','personalizado',{'modulos':{'inscripcion':'editar'}});usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}});usr('caja1','Caja','caja')
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(GRP).length===1");time.sleep(0.5)
    # ============ inscribir ============
    pg.evaluate("ir('ins')");pg.wait_for_selector('#inForm:not([hidden])')
    pg.fill('#inMat','20260901');pg.fill('#inNom','Valeria Ramírez Soto');pg.select_option('#inPlan','Pedagogía');pg.fill('#inTut','Rosa Soto');pg.fill('#inTutTel','7221234567');pg.fill('#inMon','800');W(pg,"document.getElementById('inGrp').options.length>1");pg.select_option('#inGrp','g1')
    pg.click('#inOk');pg.wait_for_selector('#inRes:not([hidden])');pg.evaluate(MOCK)
    sid=pg.evaluate("INLAST.sid")
    ok('al_terminar_la_inscripcion_ofrece_firmar_la_ficha',pg.is_visible('#inFirma') and 'Firmar ficha en pantalla' in pg.inner_text('#inFirma') and 'aún no tiene la firma' in pg.inner_text('#inFirmaE'))
    ok('la_ficha_sin_firma_se_descarga_como_siempre',(pg.click('#inFichaPdf'),pg.wait_for_timeout(400),pg.evaluate("window.__sav[0]"))[2]=='ficha-de-inscripcion-20260901.pdf')
    # ============ firmar ============
    pg.click('#inFirma');pg.wait_for_selector('#dFz[open]')
    t=pg.inner_text('#fzTxt')
    ok('muestra_los_datos_de_la_ficha_para_leerlos','20260901' in t and 'Valeria Ramírez Soto' in t and 'Pedagogía' in t and '4821' in t and 'Rosa Soto' in t and '$800.00' in t and 'Declaro que los datos proporcionados son verdaderos' in t)
    ok('hay_dos_cuadros_de_firma',pg.locator('#fzFir canvas').count()==2 and 'Alumno o tutor' in pg.inner_text('#fzFir').replace('alumno o tutor','Alumno o tutor') and 'Control escolar' in pg.inner_text('#fzFir'))
    pg.click('#fzOk');ok('exige_dibujar_la_firma','Dibuja la firma' in pg.inner_text('#fzMsg'))
    firma(pg,'#fzCvA');pg.click('#fzOk');ok('exige_la_conformidad','conformidad' in pg.inner_text('#fzMsg'))
    pg.click('#fzAcA');pg.evaluate("window.__ev=[];window.__sav=[]");pg.click('#fzOk');W(pg,"FICH['%s']&&FICH['%s'].firmas&&FICH['%s'].firmas.alumno&&window.__sav.length===1"%(sid,sid,sid))
    d=ctx.request.get(B+'/api/doc/fichasins/'+sid).json()['data'];fa=d['firmas']['alumno']
    ok('guarda_la_firma_con_fecha_huella_y_quien_la_capturo',fa['png'].startswith('data:image/png;base64,') and re.match(r'^[0-9a-f]{64}$',fa['huella']) and 'T' in fa['fecha'] and fa['capturo']=='Administrador' and d['sid']==sid and d['mat']=='20260901' and len(json.dumps(d))<90000)
    ok('firma_el_tutor_cuando_hay_tutor',fa['nombre']=='Rosa Soto (tutor)')
    ok('descarga_la_ficha_firmada',pg.evaluate("window.__sav[0]")=='ficha-de-inscripcion-20260901-firmada.pdf')
    pg.wait_for_timeout(300);ev=pg.evaluate("window.__ev");txt=' '.join(e[1] for e in ev if e[0]=='text');imgs=[e for e in ev if e[0]=='img']
    ok('el_pdf_lleva_la_firma_y_la_leyenda_electronica',len([e for e in imgs if e[1]=='PNG' and e[5]==54 and e[6]==18 and e[3]==26])==1 and 'Firmado electrónicamente el' in txt and 'Rosa Soto (tutor)' in txt)
    ok('el_pdf_lleva_la_constancia_con_la_huella','CONSTANCIA DE FIRMA ELECTRÓNICA' in txt and 'Huella SHA-256: '+fa['huella'][:32] in txt and 'pantalla táctil' in txt)
    ok('el_pdf_conserva_los_datos_y_la_declaracion','Valeria Ramírez Soto' in txt and 'Declaro que los datos proporcionados' in txt and 'Firma del alumno o tutor' in txt and 'Control escolar y sello' in txt)
    ok('la_pantalla_final_muestra_que_ya_esta_firmada','Ficha firmada electrónicamente' in pg.inner_text('#inFirmaE') and 'Ver firmas de la ficha' in pg.inner_text('#inFirma'))
    ok('la_firma_guardada_queda_a_la_vista_y_el_boton_sigue_activo_para_la_otra','Firmó' in pg.inner_text('#fzFir') and pg.locator('#fzFir canvas').count()==1 and pg.is_enabled('#fzOk'))
    # ============ firma de control escolar ============
    firma(pg,'#fzCvE');pg.click('#fzAcE');pg.evaluate("window.__ev=[];window.__sav=[]");pg.click('#fzOk');W(pg,"FICH['%s'].firmas.esc&&window.__sav.length===1"%sid);pg.wait_for_timeout(300)
    imgs=[e for e in pg.evaluate("window.__ev") if e[0]=='img' and e[1]=='PNG' and e[5]==54]
    ok('con_las_dos_firmas_el_pdf_trae_ambas_en_su_lugar',len(imgs)==2 and sorted(e[3] for e in imgs)==[26,131])
    ok('la_ficha_queda_cerrada_y_el_administrador_puede_borrar_las_firmas','Ficha firmada' in pg.inner_text('#fzOk') and pg.is_disabled('#fzOk') and pg.is_visible('#fzBor'))
    pg.click('#fzCls');pg.click('#inNueva');pg.wait_for_selector('#inForm:not([hidden])')
    # ============ lista de fichas ============
    put('students/s2',{'mat':'20260902','nombre':'Mateo Cruz Ibarra','carrera':'Pedagogía','programa':'Pedagogía','nuevo':True,'ingreso':CIC,'fins':datetime.date.today().isoformat(),'tut':'','tutTel':'','docs':[]});W(pg,"S.length===2")
    pg.click('#inFichas');pg.wait_for_selector('#dFzL[open]');t=pg.inner_text('#fzlL');ok('la_lista_muestra_firmada_y_sin_firmar','Valeria Ramírez Soto' in t and 'Firmada · Control escolar' in t and 'Mateo Cruz Ibarra' in t and 'Sin firmar' in t and '2 alumnos de nuevo ingreso · 1 ficha sin firmar' in pg.inner_text('#fzlS'))
    pg.fill('#fzlQ','mateo');ok('la_busqueda_filtra','Valeria' not in pg.inner_text('#fzlL') and 'Mateo' in pg.inner_text('#fzlL'));pg.fill('#fzlQ','')
    pg.evaluate("window.__sav=[]");pg.locator('#fzlL [data-fzp="%s"]'%sid).click();pg.wait_for_timeout(300);ok('descarga_la_ficha_firmada_desde_la_lista',pg.evaluate("window.__sav[0]")=='ficha-de-inscripcion-20260901-firmada.pdf')
    pg.locator('#fzlL tr:has-text("Mateo") [data-fzp]').click();pg.wait_for_timeout(300);ok('y_la_de_quien_no_ha_firmado_sale_sin_firmas',pg.evaluate("window.__sav[1]")=='ficha-de-inscripcion-20260902.pdf')
    pg.locator('#fzlL tr:has-text("Mateo") [data-fzf]').click();pg.wait_for_selector('#dFz[open]');ok('desde_la_lista_se_abre_la_firma_de_ese_alumno','Mateo Cruz Ibarra' in pg.inner_text('#fzS') and pg.locator('#fzFir canvas').count()==2)
    ok('aviso_en_la_campana','1 ficha de inscripción por firmar' in pg.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')"))
    firma(pg,'#fzCvA');pg.click('#fzAcA');pg.click('#fzOk');W(pg,"FICH.s2&&FICH.s2.firmas.alumno");ok('firma_a_un_alumno_sin_tutor_con_su_nombre',ctx.request.get(B+'/api/doc/fichasins/s2').json()['data']['firmas']['alumno']['nombre']=='Mateo Cruz Ibarra')
    ok('la_campana_ya_no_avisa',pg.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')").find('ficha de inscripción')==-1)
    pg.click('#fzCls')
    ok('el_respaldo_incluye_las_fichas',pg.evaluate("BKCOL.indexOf('fichasins')>-1"))
    # ============ permisos ============
    def entra(u):
        cx=b.new_context(viewport={'width':1200,'height':950});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1200);return pp,cx
    pi,cxi=entra('ins2');W(pi,"Object.keys(FICH).length===2")
    ok('recepcion_ve_las_fichas_y_puede_firmar',pi.evaluate("typeof abreFz==='function'")and ctx.request.get(B+'/api/doc/fichasins/'+sid).status==200)
    put('students/s3',{'mat':'20260903','nombre':'Ana Prueba','carrera':'Pedagogía','programa':'Pedagogía','nuevo':True,'ingreso':CIC,'fins':datetime.date.today().isoformat()});W(pi,"S.length===3")
    pi.evaluate("ir('ins')");pi.wait_for_selector('#inForm:not([hidden])');pi.click('#inFichas');pi.wait_for_selector('#dFzL[open]');pi.locator('#fzlL tr:has-text("Ana Prueba") [data-fzf]').click();pi.wait_for_selector('#dFz[open]')
    firma(pi,'#fzCvA');pi.click('#fzAcA');pi.click('#fzOk');W(pi,"FICH.s3&&FICH.s3.firmas.alumno");ok('recepcion_guarda_la_firma_en_el_servidor',ctx.request.get(B+'/api/doc/fichasins/s3').json()['data']['firmas']['alumno']['capturo']=='Recepción')
    ok('recepcion_no_ve_el_boton_de_borrar_firmas',pi.is_hidden('#fzBor'))
    pe,cxe=entra('esc2');W(pe,"Object.keys(FICH).length>=2")
    ok('control_escolar_puede_leer_la_ficha_pero_no_escribirla',cxe.request.get(B+'/api/doc/fichasins/'+sid).status==200 and cxe.request.put(B+'/api/doc/fichasins/'+sid,data=json.dumps({'firmas':{}}),headers=HDR).status==403)
    pe.evaluate("abreFz('%s')"%sid);pe.wait_for_timeout(300);ok('y_la_pantalla_no_deja_firmar_sin_permiso_de_inscripcion',pe.is_hidden('#dFz'))
    pk,cxk=entra('caja1');ok('caja_no_ve_las_fichas',pk.evaluate("Object.keys(FICH).length")==0 and cxk.request.get(B+'/api/doc/fichasins/'+sid).json()['exists'] is False)
    # ============ borrar firmas (administrador) ============
    pg.evaluate("abreFz('%s')"%sid);pg.wait_for_selector('#dFz[open]');pg.click('#fzBor');W(pg,"!FICH['%s'].firmas.alumno"%sid)
    ok('el_administrador_borra_las_firmas_y_la_ficha_vuelve_a_firmarse',pg.locator('#fzFir canvas').count()==2 and not ctx.request.get(B+'/api/doc/fichasins/'+sid).json()['data']['firmas'])
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    # captura tableta
    ct=b.new_context(viewport={'width':1024,'height':768},has_touch=True,is_mobile=True,device_scale_factor=1.3);ct.set_default_timeout(15000);pt=pagina(ct);pt.goto(B+'/');W(pt,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pt.fill('#lgU','admin');pt.fill('#lgP','clave-segura-1');pt.click('#lgGo');W(pt,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&Object.keys(FICH).length>=2");pt.wait_for_timeout(500)
    pt.evaluate("abreFz('%s')"%sid);pt.wait_for_selector('#dFz[open]')
    for l in ('A','E'):
        pt.evaluate("(function(l){var cv=document.getElementById('fzCv'+l),r=cv.getBoundingClientRect();function ev(t,x,y){cv.dispatchEvent(new PointerEvent(t,{pointerId:9,pointerType:'touch',clientX:r.left+x*r.width,clientY:r.top+y*r.height,bubbles:true,cancelable:true}))}ev('pointerdown',0.1,0.6);for(var i=1;i<40;i++)ev('pointermove',0.1+0.02*i,0.5+0.28*Math.sin(i/(l==='A'?3:4.5))*Math.cos(i/9));ev('pointerup',0.9,0.5)})('%s')"%l)
    pt.evaluate("document.getElementById('fzTxt').parentElement.open=true");pt.wait_for_timeout(300);pt.screenshot(path='/tmp/fz_tableta.png')
    pt.evaluate("document.getElementById('fzFir').scrollIntoView({block:'center'})");pt.wait_for_timeout(300);pt.screenshot(path='/tmp/fz_tableta_firmas.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
