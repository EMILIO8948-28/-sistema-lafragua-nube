import subprocess,time,json,os,urllib.request,struct,zlib
from playwright.sync_api import sync_playwright
PORT=3075;B='http://127.0.0.1:%d'%PORT;TOK='tok-dx-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata5',LF_SETUP_TOKEN=TOK)
os.system('rm -rf /tmp/nbdata5 && mkdir -p /tmp/nbdata5 /tmp/dxf')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
# archivos de prueba
def png(path):
    def ch(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    raw=b''.join(b'\x00'+bytes([200,50,50])*20 for _ in range(20))
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',20,20,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw))+ch(b'IEND',b''))
png('/tmp/dxf/foto.png')
for n in ['cv.pdf','cedula.pdf','titulo.pdf','cert.pdf','ine.pdf','curp.pdf','acta.pdf','lic_titulo.pdf','lic_cedula.pdf','lic_cert.pdf']:open('/tmp/dxf/'+n,'wb').write(b'%PDF-1.4\n'+n.encode())
open('/tmp/dxf/cv.docx','wb').write(b'PK\x03\x04docx')
open('/tmp/dxf/malo.exe','wb').write(b'MZ')
open('/tmp/dxf/grande.pdf','wb').write(b'%PDF-1.4\n'+b'0'*(21*1024*1024))
R={};errs=[];malos=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=9):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
def sube(pg,key,archivo):
    pg.set_input_files('#dxDocs [data-up="%s"]'%key,'/tmp/dxf/'+archivo)
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.on("response",lambda r:malos.append((r.status,r.url.replace(B,''))) if r.status>=400 and ('/api/' in r.url or '/_blob/' in r.url) else None)
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html')
    pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof DBH!=='undefined'&&DBH!==null&&typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    pg.evaluate("ir('esc');etab('D')")
    # ---- alta: se abre el expediente ----
    pg.fill('#dcNom','Mtra. Laura Díaz');pg.fill('#dcEsp','Pedagogía');pg.click('#dcAdd');pg.wait_for_selector('#dDx[open]')
    ok('abre_expediente_al_alta','Expediente de Mtra. Laura Díaz' in pg.inner_text('#dxT') and 'Docente registrado' in pg.inner_text('#dxS'))
    did=pg.evaluate("DXID")
    ok('lista_licenciatura','Currículum vitae' in pg.inner_text('#dxDocs') and 'Cédula profesional' in pg.inner_text('#dxDocs') and 'Título' in pg.inner_text('#dxDocs') and 'Certificado total de estudios' in pg.inner_text('#dxDocs') and 'INE' in pg.inner_text('#dxDocs') and 'CURP' in pg.inner_text('#dxDocs') and 'Acta de nacimiento' in pg.inner_text('#dxDocs'))
    ok('sin_slots_de_licenciatura_con_licenciatura','Estudios de licenciatura' not in pg.inner_text('#dxDocs') and pg.locator('#dxDocs [data-up]').count()==7)
    ok('progreso_inicial','0 de 8' in pg.inner_text('#dxProg'))
    # ---- cargas ----
    sube(pg,'cv','cv.docx');W(pg,"(DXD[DXID].docs||{}).cv");ok('cv_word_aceptado',pg.evaluate("DXD[DXID].docs.cv.name")=='cv.docx')
    sube(pg,'cv','cv.pdf');W(pg,"DXD[DXID].docs.cv.name==='cv.pdf'");ok('reemplazar_cv',True)
    sube(pg,'ine','malo.exe');ok('rechaza_tipo','PDF, JPG o PNG' in pg.inner_text('#dxMsg') and not pg.evaluate("!!(DXD[DXID].docs||{}).ine"))
    sube(pg,'ine','grande.pdf');ok('rechaza_tamano','20 MB' in pg.inner_text('#dxMsg'))
    sube(pg,'cv','malo.exe') ;ok('cv_rechaza_exe','Word' in pg.inner_text('#dxMsg'))
    for k,f in [('cedula','cedula.pdf'),('titulo','titulo.pdf'),('cert','cert.pdf'),('ine','ine.pdf'),('curp','curp.pdf'),('acta','acta.pdf')]:
        sube(pg,k,f);W(pg,"DXD[DXID].docs['%s']"%k)
    ok('siete_documentos',pg.evaluate("Object.keys(DXD[DXID].docs).length")==7 and '7 de 8' in pg.inner_text('#dxProg'))
    pg.set_input_files('#dxFoto','/tmp/dxf/foto.png');W(pg,"DXD[DXID].foto");ok('foto_guardada',pg.evaluate("DXD[DXID].foto").startswith('data:image/jpeg') and pg.is_visible('#dxFotoQ') and '8 de 8' in pg.inner_text('#dxProg'))
    pg.set_input_files('#dxFoto','/tmp/dxf/cv.pdf');ok('foto_solo_imagen','imagen' in pg.inner_text('#dxMsg'))
    # ---- grado superior: aparecen los documentos de licenciatura ----
    pg.select_option('#dxGrado','Maestría');W(pg,"DXD[DXID].grado==='Maestría'")
    ok('pide_licenciatura','Estudios de licenciatura' in pg.inner_text('#dxDocs') and pg.locator('#dxDocs [data-up]').count()==10)
    ok('etiquetas_de_maestria','Título de maestría' in pg.inner_text('#dxDocs') and 'Cédula profesional de maestría' in pg.inner_text('#dxDocs') and 'Certificado total de estudios de maestría' in pg.inner_text('#dxDocs') and 'Título de licenciatura' in pg.inner_text('#dxDocs') and 'Cédula profesional de licenciatura' in pg.inner_text('#dxDocs') and 'Certificado total de estudios de licenciatura' in pg.inner_text('#dxDocs'))
    ok('progreso_con_maestria','8 de 11' in pg.inner_text('#dxProg'))
    pg.fill('#dxGradoN','Maestría en Educación');pg.press('#dxGradoN','Tab');W(pg,"DXD[DXID].gradoN==='Maestría en Educación'")
    sube(pg,'lic_titulo','lic_titulo.pdf');W(pg,"DXD[DXID].docs.lic_titulo");sube(pg,'lic_cedula','lic_cedula.pdf');W(pg,"DXD[DXID].docs.lic_cedula");sube(pg,'lic_cert','lic_cert.pdf');W(pg,"DXD[DXID].docs.lic_cert")
    ok('licenciatura_cargada','11 de 11' in pg.inner_text('#dxProg'))
    pg.select_option('#dxGrado','Doctorado');W(pg,"DXD[DXID].grado==='Doctorado'");ok('doctorado_etiquetas','Título de doctorado' in pg.inner_text('#dxDocs') and 'Título de licenciatura' in pg.inner_text('#dxDocs'))
    # regresar a licenciatura no pierde los archivos de licenciatura
    pg.select_option('#dxGrado','Licenciatura');W(pg,"DXD[DXID].grado==='Licenciatura'");ok('no_pierde_licenciatura','Documentos de licenciatura guardados' in pg.inner_text('#dxDocs') and pg.evaluate("Object.keys(DXD[DXID].docs).length")==10)
    pg.select_option('#dxGrado','Maestría');W(pg,"DXD[DXID].grado==='Maestría'")
    # ---- ver, descargar y quitar ----
    fid=pg.evaluate("DXD[DXID].docs.ine.id")
    ok('abre_archivo_admin',ctx.request.get(B+'/_blob/'+fid).body().startswith(b'%PDF'))
    ok('enlace_ver','/_blob/'+fid in pg.inner_html('#dxDocs'))
    pg.evaluate("window.__sav=[];saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0");pg.locator('#dxDocs .pay:has-text("INE") [data-dl]').click();pg.wait_for_timeout(300);ok('descarga',pg.evaluate("window.__sav")==['ine.pdf'])
    pg.locator('#dxDocs .pay:has-text("INE") [data-rm]').click();W(pg,"!DXD[DXID].docs.ine");ok('quitar_documento','Falta' in pg.locator('#dxDocs .pay:has-text("INE")').inner_text())
    ok('archivo_quitado_del_servidor',ctx.request.get(B+'/_blob/'+fid).status==404)
    sube(pg,'ine','ine.pdf');W(pg,"DXD[DXID].docs.ine")
    pg.click('#dxCls');ok('lista_muestra_avance','11 de 11' in pg.inner_text('#dcTb'))
    # recarga: todo persiste
    pg.reload();W(pg,"typeof DXD!=='undefined'&&Object.keys(DXD).length===1");pg.evaluate("ir('esc');etab('D')");pg.click('#dcTb [data-ex]');pg.wait_for_selector('#dDx[open]')
    ok('persiste',pg.evaluate("DXD[DXID].grado")=='Maestría' and pg.evaluate("Object.keys(DXD[DXID].docs).length")==10 and pg.evaluate("!!DXD[DXID].foto") and pg.input_value('#dxGradoN')=='Maestría en Educación')
    pg.click('#dxCls')
    # editar un docente existente no abre el expediente
    pg.click('#dcTb [data-ed]');pg.click('#dcAdd');pg.wait_for_timeout(300);ok('editar_no_abre',pg.evaluate("document.getElementById('dDx').open")==False)
    # ---- confidencialidad en el servidor ----
    hdr={'Content-Type':'application/json','x-lafragua':'1'}
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja Uno','rol':'caja','clave':'clave-caja-1'}),headers=hdr)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'doc1','name':'Docente Uno','rol':'docente','doc':did,'clave':'clave-doc-1'}),headers=hdr)
    def sesion(u,c):
        cx=pw.chromium.launch().new_context();cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=hdr);return cx
    cj=sesion('caja1','clave-caja-1');dc=sesion('doc1','clave-doc-1')
    cedula=pg.evaluate("DXD[DXID].docs.cedula.id")
    ok('caja_no_ve_archivo_confidencial',cj.request.get(B+'/_blob/'+cedula).status==403)
    ok('docente_no_ve_archivo_confidencial',dc.request.get(B+'/_blob/'+cedula).status==403)
    ok('admin_si_ve',ctx.request.get(B+'/_blob/'+cedula).status==200)
    ok('caja_no_lee_expedientes',cj.request.get(B+'/api/col/docentes_docs').json()['docs']==[] and cj.request.get(B+'/api/doc/docentes_docs/'+did).json()['exists'] is False)
    ok('docente_no_lee_expedientes',dc.request.get(B+'/api/col/docentes_docs').json()['docs']==[])
    ok('caja_no_escribe_expedientes',cj.request.put(B+'/api/doc/docentes_docs/'+did,data=json.dumps({'x':1}),headers=hdr).status==403 and dc.request.put(B+'/api/doc/docentes_docs/'+did,data=json.dumps({'x':1}),headers=hdr).status==403)
    ok('caja_no_sube_archivos',cj.request.post(B+'/api/archivo',data=b'%PDF',headers={'x-lafragua':'1','x-nombre':'a.pdf','x-privado':'1','Content-Type':'application/pdf'}).status==403)
    ok('caja_si_lee_docentes_sin_expediente',cj.request.get(B+'/api/col/docentes').json()['docs'][0]['data']['nombre']=='Mtra. Laura Díaz')
    # un archivo no confidencial (de otro módulo) sigue viéndose con sesión
    up=ctx.request.post(B+'/api/archivo',data=b'%PDF-1.4 comun',headers={'x-lafragua':'1','x-nombre':'comun.pdf','Content-Type':'application/pdf'}).json()
    ok('archivo_comun_con_sesion',cj.request.get(B+'/_blob/'+up['id']).status==200)
    # el respaldo marca lo confidencial y la restauración lo conserva
    c,=[0]
    z=ctx.request.get(B+'/api/respaldo/descargar').body()
    import zipfile,io
    zf=zipfile.ZipFile(io.BytesIO(z));idx=json.loads(zf.read('indice-1.json'))
    pri={i['id']:i['privado'] for i in idx};ok('indice_marca_privados',pri[cedula]==1 and pri[up['id']]==0)
    pg.evaluate("ir('pagos')");bk=pg.evaluate("async()=>{var d=await armaRespaldo(function(){});return {col:Object.keys(d.colecciones.docentes_docs).length,arch:d.archivos.filter(a=>/docentes_docs/.test(a.ruta)).length}}")
    ok('respaldo_incluye_expedientes',bk['col']==1 and bk['arch']==10)
    # ---- quitar al docente: borra expediente y archivos ----
    pg.evaluate("ir('esc');etab('D')");ids=pg.evaluate("Object.values(DXD[DXID].docs).map(d=>d.id)")
    pg.locator('#dcTb [data-dl]').click();ok('baja_pide_confirmar','Confirmar' in pg.locator('#dcTb [data-dl]').inner_text() and 'expediente' in pg.inner_text('#dcMsg'))
    pg.locator('#dcTb [data-dl]').click();W(pg,"Object.keys(DOC).length===0");pg.wait_for_timeout(400)
    ok('baja_borra_expediente',pg.evaluate("Object.keys(DXD).length")==0 and ctx.request.get(B+'/api/doc/docentes_docs/'+did).json()['exists'] is False)
    ok('baja_borra_archivos',all(ctx.request.get(B+'/_blob/'+i).status==404 for i in ids))
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    inesp=[m for m in malos if m[0] not in (404,403) ]
    ok('sin_errores_de_red_inesperados',len(inesp)==0)
    if inesp:print('RED:',inesp[:5])
    b.close()
p.terminate();p.wait()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
