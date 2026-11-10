import subprocess,time,json,os,urllib.request,base64,io
from playwright.sync_api import sync_playwright
PORT=3170;B='http://127.0.0.1:%d'%PORT;TOK='tok-fd-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata90 && mkdir -p /tmp/nbdata90')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata90',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
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
src=open('/tmp/cred_replay.py').read();REC=src[src.index('REC="""')+7:src.index('"""',src.index('REC="""')+7)]
DIMS="(u)=>new Promise(function(r){var i=new Image();i.onload=function(){r([i.width,i.height])};i.src=u})"
with sync_playwright() as pw:
    b=pw.chromium.launch(args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']);ctx=b.new_context(viewport={'width':1200,'height':950},permissions=['camera']);ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('docentes/d1',{'nombre':'Mtra. Laura Gómez Ríos','esp':'Maestría en Educación','tel':'722 111 2233','mail':'laura@correo.mx','asig':[]})
    put('docentes/d2',{'nombre':'Mtro. Pedro Soto','esp':'Historia','tel':'','mail':'','asig':[]})
    put('docentes_docs/d1',{'grado':'Maestría','gradoN':'Maestría en Educación','docs':{'cv':{'id':'a'*32,'name':'cv.pdf','size':10,'type':'application/pdf'}}})
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('doc1','Mtra. Laura Gómez Ríos','docente',{'doc':'d1'});usr('doc2','Mtro. Pedro Soto','docente',{'doc':'d2'});usr('docsin','Sin Vinculo','personalizado',{'modulos':{'docente':'editar'}});usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}});usr('caja1','Caja','caja')
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(DOC).length===2&&DXD.d1&&DXD.d1.grado");time.sleep(0.4)
    # ============ expediente: foto con cámara ============
    pg.evaluate("ir('esc');etab('D')");pg.wait_for_selector('#dcTb [data-ex="d1"]');pg.click('#dcTb [data-ex="d1"]');pg.wait_for_selector('#dDx[open]')
    ok('el_expediente_ofrece_tomar_la_foto_con_la_camara',pg.is_visible('#dxCam') and 'cámara' in pg.inner_text('#dxCam'))
    pg.click('#dxCam');pg.wait_for_selector('#dCam[open]');W(pg,"document.getElementById('camV').videoWidth>0")
    ok('se_abre_la_camara_y_el_boton_de_tomar_esta_listo',pg.is_enabled('#camOk') and pg.is_visible('#camSw'))
    pg.click('#camOk');W(pg,"DXD.d1.foto")
    f1=ctx.request.get(B+'/api/doc/docentes_docs/d1').json()['data']
    ok('guarda_la_foto_del_rostro_en_jpg_vertical_480x640',f1['foto'].startswith('data:image/jpeg;base64,') and pg.evaluate(DIMS,f1['foto'])==[480,640] and len(f1['foto'])<120000)
    ok('al_guardar_la_foto_no_se_pierde_el_resto_del_expediente',f1['grado']=='Maestría' and f1['docs']['cv']['name']=='cv.pdf')
    ok('la_camara_se_apaga_al_tomar_la_foto',pg.evaluate("CAMS===null")and pg.is_hidden('#dCam') and pg.is_visible('#dxImg'))
    pg.set_input_files('#dxFoto','/tmp/ine_frente.jpg');W(pg,"DXD.d1.foto!==%s"%json.dumps(f1['foto']));f2=ctx.request.get(B+'/api/doc/docentes_docs/d1').json()['data']['foto']
    ok('elegir_una_imagen_horizontal_tambien_queda_vertical_480x640',pg.evaluate(DIMS,f2)==[480,640])
    pg.evaluate("document.getElementById('dDx').close()")
    # cámara bloqueada
    pg.evaluate("ir('esc');etab('D')");pg.click('#dcTb [data-ex="d1"]');pg.wait_for_selector('#dDx[open]')
    pg.evaluate("window.__gum=navigator.mediaDevices.getUserMedia;navigator.mediaDevices.getUserMedia=function(){return Promise.reject(new Error('denegado'))};0")
    pg.click('#dxCam');pg.wait_for_selector('#dCam[open]');pg.wait_for_timeout(400)
    ok('si_la_camara_no_se_puede_abrir_avisa_y_no_deja_tomar',('No se pudo abrir la cámara' in pg.inner_text('#camMsg')) and pg.is_disabled('#camOk'))
    pg.click('#camCls');pg.evaluate("navigator.mediaDevices.getUserMedia=window.__gum;0");pg.evaluate("document.getElementById('dDx').close()")
    # ============ personal sin expedientes ============
    def entra(u):
        cx=b.new_context(viewport={'width':1200,'height':950},permissions=['camera']);cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1200);return pp,cx
    pe,cxe=entra('esc2');pe.evaluate("document.getElementById('dxCam').click()");pe.wait_for_timeout(300);ok('sin_permiso_de_expedientes_no_se_abre_la_camara',pe.is_hidden('#dCam') and pe.evaluate("typeof DXID==='undefined'||!DXID||true"))
    # ============ el docente en su plataforma ============
    pd,cxd=entra('doc1');W(pd,"UFOTO&&UFOTO.indexOf('data:image/jpeg')===0")
    ok('el_docente_ve_su_foto_y_el_boton_mi_perfil_en_su_sesion',pd.is_visible('#uAv') and pd.is_visible('#bPerf') and pd.evaluate("document.getElementById('uAv').getAttribute('src')")==f2)
    ok('quien_no_es_docente_no_ve_el_perfil_de_foto',pe.is_hidden('#uAv') and pe.is_hidden('#bPerf'))
    pd.click('#bPerf');pd.wait_for_selector('#dFp[open]')
    ok('mi_perfil_muestra_nombre_usuario_y_foto','Mtra. Laura Gómez Ríos' in pd.inner_text('#fpNom') and 'doc1' in pd.inner_text('#fpUsr') and pd.evaluate("document.getElementById('fpImg').getAttribute('src')")==f2)
    pd.click('#fpCam');pd.wait_for_selector('#dCam[open]');W(pd,"document.getElementById('camV').videoWidth>0");pd.click('#camOk');W(pd,"UFOTO!==%s"%json.dumps(f2))
    srv=ctx.request.get(B+'/api/doc/docentes_docs/d1').json()['data']
    ok('el_docente_cambia_su_foto_con_la_camara',srv['foto']==pd.evaluate("UFOTO") and srv['foto']!=f2 and pd.evaluate(DIMS,srv['foto'])==[480,640] and srv['fotoPor']=='doc1' and 'T' in srv['fotoFecha'])
    ok('y_el_resto_de_su_expediente_queda_igual',srv['grado']=='Maestría' and srv['docs']['cv']['name']=='cv.pdf')
    ok('el_perfil_y_el_avatar_se_actualizan_y_avisa',pd.evaluate("document.getElementById('uAv').getAttribute('src')")==srv['foto'] and pd.evaluate("document.getElementById('fpImg').getAttribute('src')")==srv['foto'] and 'Foto actualizada' in pd.inner_text('#fpMsg') and 'credencial' in pd.inner_text('#fpMsg'))
    pd.set_input_files('#fpFile','/tmp/ine_reverso.jpg');W(pd,"UFOTO!==%s"%json.dumps(srv['foto']))
    ok('tambien_puede_elegir_o_tomar_una_foto_con_el_selector_de_la_tableta',ctx.request.get(B+'/api/doc/docentes_docs/d1').json()['data']['foto']==pd.evaluate("UFOTO"))
    ok('el_admin_ve_la_nueva_foto_en_el_expediente',pg.evaluate("DXD.d1.foto")==pd.evaluate("UFOTO"))
    pd.screenshot(path='/tmp/fd_perfil.png')
    # ============ seguridad ============
    api=lambda cx,m,url,body=None:cx.request.fetch(B+url,method=m,data=json.dumps(body) if body is not None else None,headers=HDR)
    ok('rechaza_lo_que_no_es_una_imagen_jpg',api(cxd,'PUT','/api/docente/foto',{'foto':'hola'}).status==400 and api(cxd,'PUT','/api/docente/foto',{'foto':'data:text/html;base64,PHNjcmlwdD4='}).status==400)
    ok('rechaza_fotos_gigantes',api(cxd,'PUT','/api/docente/foto',{'foto':'data:image/jpeg;base64,'+'A'*260000}).status==400)
    ok('el_docente_no_puede_escribir_su_expediente_completo',api(cxd,'PUT','/api/doc/docentes_docs/d1',{'foto':'x','docs':{}}).status==403)
    pd2,cxd2=entra('doc2');ok('otro_docente_solo_ve_la_suya',api(cxd2,'GET','/api/docente/foto').json()['foto'] is None and pd2.evaluate("UFOTO")is None and pd2.evaluate("document.getElementById('uAv').getAttribute('src')").startswith('data:image/svg'))
    def sesion(u):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);return cx if r.status==200 else None
    cs=sesion('esc2');ok('personal_que_no_es_docente_no_puede',cs is not None and api(cs,'GET','/api/docente/foto').status==403)
    ok('caja_y_el_administrador_no_usan_este_servicio',api(sesion('caja1'),'PUT','/api/docente/foto',{'foto':'data:image/jpeg;base64,AAAA'}).status==403 and api(ctx,'GET','/api/docente/foto').status==403)
    # ============ credencial de docentes ============
    pg.evaluate("ir('esc');etab('R')");pg.wait_for_selector('#crAlc')
    ok('credenciales_ofrece_docentes',pg.evaluate("Array.from(document.getElementById('crAlc').options).map(function(o){return o.value}).join(',')").endswith('docente,docentes'))
    pg.select_option('#crAlc','docente');pg.wait_for_timeout(200);ok('aparece_el_selector_de_docente',pg.is_visible('#crDcL'))
    pg.select_option('#crDc','d1');pg.wait_for_timeout(300);t=pg.inner_text('#crPrev')
    ok('la_vista_previa_es_credencial_de_docente_con_su_foto_y_especialidad','CREDENCIAL DE DOCENTE' in t and 'ESPECIALIDAD' in t and 'Maestría en Educación' in t and 'MTRA. LAURA GÓMEZ RÍOS' in t and 'laura@correo.mx' in t and 'Firma del docente' in t and 'DOC-' in t and 'ESTUDIANTE' not in t and pg.evaluate("document.querySelector('#crPrev img[style*=\"object-fit:cover\"]')&&document.querySelector('#crPrev img[style*=\"object-fit:cover\"]').getAttribute('src')")==pg.evaluate("DXD.d1.foto"))
    ok('indica_que_esta_completa','1 credencial' in pg.inner_text('#crInfo') and 'todas con fotografía' in pg.inner_text('#crInfo'))
    pg.select_option('#crAlc','docentes');pg.wait_for_timeout(300);ok('todos_los_docentes_y_avisa_quien_no_tiene_foto','2 credenciales' in pg.inner_text('#crInfo') and '1 persona sin fotografía' in pg.inner_text('#crInfo'))
    pg.check('#crSoloFoto');pg.wait_for_timeout(200);ok('solo_con_foto_deja_una','1 credencial' in pg.inner_text('#crInfo'));pg.uncheck('#crSoloFoto')
    pg.evaluate(REC);pg.evaluate("window.__log=[];window.__qrs=[];window.__sav=[];0")
    pg.evaluate("(function(){var q0=qrPDF;qrPDF=function(d,t,x,y,l){window.__qrs.push(t);return q0(d,t,x,y,l)};0})()")
    pg.fill('#crVig','2027-01-31');pg.select_option('#crModo','tarjeta');pg.click('#crPdf');W(pg,"window.__sav.length>=1");pg.wait_for_timeout(300)
    log=pg.evaluate("window.__log");txt=' | '.join(str(e[1]) for e in log if e and e[0]=='text')
    ok('el_pdf_dice_docente_especialidad_y_firma_del_docente','CREDENCIAL DE DOCENTE' in txt and 'ESPECIALIDAD' in txt and 'Firma del docente' in txt and 'Datos de identificación' in txt and 'DOC-' in txt and 'CREDENCIAL DE ESTUDIANTE' not in txt and 'Firma del alumno' not in txt)
    ok('el_pdf_incluye_la_foto_circular_del_docente_con_foto',len([e for e in log if e and e[0]=='img'])>=1)
    ok('el_qr_de_docente_lleva_sus_datos_y_no_un_enlace_de_alumno',len(pg.evaluate("window.__qrs"))==2 and all('DOCENTE' in q and '#a.' not in q for q in pg.evaluate("window.__qrs")))
    # los alumnos siguen igual
    put('students/s1',{'mat':'2023','nombre':'Ana López','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False});W(pg,"S.length===1")
    pg.select_option('#crAlc','todos');pg.evaluate("window.__log=[];window.__qrs=[];window.__sav=[];0");pg.click('#crPdf');W(pg,"window.__sav.length>=1");pg.wait_for_timeout(200)
    txt2=' | '.join(str(e[1]) for e in pg.evaluate("window.__log") if e and e[0]=='text')
    ok('la_credencial_de_alumnos_no_cambia','CREDENCIAL DE ESTUDIANTE' in txt2 and 'PLAN DE ESTUDIOS' in txt2 and 'Firma del alumno' in txt2 and 'DOCENTE' not in txt2 and any('#a.' in q for q in pg.evaluate("window.__qrs")))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    # captura de cámara (tableta)
    ct=b.new_context(viewport={'width':1024,'height':768},has_touch=True,is_mobile=True,permissions=['camera'],device_scale_factor=1.3);ct.set_default_timeout(15000);pt=pagina(ct);pt.goto(B+'/');W(pt,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pt.fill('#lgU','doc1');pt.fill('#lgP','clave-doc1-123');pt.click('#lgGo');W(pt,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&UFOTO");pt.wait_for_timeout(600)
    pt.click('#bPerf');pt.wait_for_selector('#dFp[open]');pt.click('#fpCam');pt.wait_for_selector('#dCam[open]');W(pt,"document.getElementById('camV').videoWidth>0");pt.wait_for_timeout(400);pt.screenshot(path='/tmp/fd_camara.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
