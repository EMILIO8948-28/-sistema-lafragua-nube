import subprocess,time,json,os,urllib.request,zipfile,io
from playwright.sync_api import sync_playwright
PORT=3108;B='http://127.0.0.1:%d'%PORT;TOK='tok-rz-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata38',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata38 /tmp/rz && mkdir -p /tmp/nbdata38 /tmp/rz')
def contenido(n):return b'%PDF-1.4 escaneo '+n.encode()
def zip_de(nombre,archivos,extra=None):
    with zipfile.ZipFile(nombre,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in archivos:z.writestr(n,b)
        z.writestr('escaneos/',b'');z.writestr('__MACOSX/._20230101_titulo.pdf',b'x');z.writestr('.DS_Store',b'x');z.writestr('escaneos/Thumbs.db',b'x')
ARCH=[('20230101_titulo.pdf',contenido('titulo-ana')),('escaneos/20220205-cedula.jpg',b'\xff\xd8\xff\xe0'+b'0'*80),('20210311.pdf',contenido('maria')),('20240001_certificado.pdf',contenido('luis-cert')),('Daniel Torres Vega acta.png',b'\x89PNG\r\n\x1a\n'+b'0'*80),('desconocido.pdf',contenido('x')),('20240002.pdf',contenido('rosa')),('20240002_cedula.pdf',contenido('rosa-ced')),('20230101_titulo (copia).pdf',contenido('copia')),('20240003_titulo.pdf',contenido('pablo')),('20230101.exe',b'MZ'),('20240001_grande.pdf',b'%PDF'+b'0'*(11*1024*1024))]
zip_de('/tmp/rz/escaneos.zip',ARCH)
open('/tmp/rz/escaneos.rar','wb').write(b'Rar!\x1a\x07\x01\x00xx');open('/tmp/rz/roto.zip','wb').write(b'esto no es un zip');zip_de('/tmp/rz/vacio.zip',[])
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=60):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
hoy=time.strftime('%Y-%m-%d')
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    al=[('s1','20230101','Ana López Ramírez','Pedagogía'),('s2','20220205','Daniel Torres Vega','Derecho'),('s3','20210311','María Ortiz Soto','Enfermería'),('s4','20240001','Luis Sin Registro','Contaduría'),('s5','20240002','Rosa Varias Pérez','Derecho'),('s6','20240003','Pablo Ya Entregado','Pedagogía')]
    for sid,mat,nom,plan in al:put('students/'+sid,{'mat':mat,'nombre':nom,'carrera':plan,'programa':plan,'ingreso':2022,'nuevo':False})
    def rg(n,s,tp,est='resguardo',arch=None):
        a=[x for x in al if x[0]==s][0];d={'num':'R-%06d'%n,'sid':s,'nombre':a[2],'mat':a[1],'plan':a[3],'tipo':tp,'docFolio':'','fechaExp':'','fechaRec':'2026-10-01','ubic':'','notas':'','archivo':arch,'estado':est,'recibe':'Administrador','mov':[{'f':'2026-10-01T10:00:00.000Z','a':'Recibido en resguardo','p':'Administrador'}]}
        if est=='entregado':d['entrega']={'fecha':'2026-10-10','receptor':a[2],'quien':'titular','idTipo':'INE','idNum':'X123','nota':'','por':'Administrador'}
        return d
    put('resguardos/r1',rg(1,'s1','Título profesional'));put('resguardos/r2',rg(2,'s2','Cédula profesional',arch={'id':'a'*32,'name':'viejo.jpg','size':10}));put('resguardos/r3',rg(3,'s3','Título profesional'));put('resguardos/r4',rg(4,'s5','Título profesional'));put('resguardos/r5',rg(5,'s5','Cédula profesional'));put('resguardos/r6',rg(6,'s6','Título profesional','entregado'));put('meta/folioR',{'n':6})
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc1','name':'Esc Uno','rol':'personalizado','modulos':{'escolar':'ver'},'clave':'clave-esc1-123'}),headers=HDR);ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===6&&Object.keys(RSG).length===6")
    pg.evaluate("ir('esc');etab('T')");pg.wait_for_selector('#rsZip');ok('boton_visible',pg.is_visible('#rsZip'))
    pg.click('#rsZip');pg.wait_for_selector('#dRsZ[open]');ok('explica_como_nombrar_los_archivos','matrícula' in pg.inner_text('#dRsZ') and '20230101_titulo.pdf' in pg.inner_text('#dRsZ'))
    # ---- archivos que no sirven ----
    pg.set_input_files('#rsZFile','/tmp/rz/escaneos.rar');pg.wait_for_timeout(300);ok('rechaza_rar_y_sugiere_convertir','Solo se aceptan archivos ZIP' in pg.inner_text('#rsZMsg') and 'RAR' in pg.inner_text('#rsZMsg'))
    pg.set_input_files('#rsZFile','/tmp/rz/roto.zip');pg.wait_for_timeout(800);ok('zip_danado','dañado' in pg.inner_text('#rsZMsg') and pg.is_hidden('#rsZOk'))
    pg.set_input_files('#rsZFile','/tmp/rz/vacio.zip');pg.wait_for_timeout(800);ok('zip_vacio','no trae archivos' in pg.inner_text('#rsZMsg'))
    # ---- lectura ----
    pg.set_input_files('#rsZFile','/tmp/rz/escaneos.zip');pg.wait_for_selector('#rsZRes table');res=pg.inner_text('#rsZRes')
    ok('resumen_de_la_lectura','12 archivos en el ZIP: 3 se adjuntan a un registro, 3 registros nuevos y 6 se omiten' in res)
    ok('ignora_carpetas_y_archivos_de_sistema','__MACOSX' not in res and '.DS_Store' not in res and 'Thumbs' not in res)
    fila=lambda t:pg.locator('#rsZRes tr:has-text("%s")'%t).first.inner_text()
    ok('adjunta_por_matricula_y_palabra','Adjuntar a R-000001' in fila('20230101_titulo.pdf') and 'Ana López' in fila('20230101_titulo.pdf'))
    ok('sin_palabra_usa_el_unico_documento_abierto','Adjuntar a R-000003' in fila('20210311.pdf'))
    ok('crea_el_registro_si_no_existe','Crear registro de «Certificado de estudios»' in fila('20240001_certificado.pdf'))
    ok('reconoce_al_alumno_por_su_nombre','Crear registro de «Acta de examen profesional»' in fila('Daniel Torres Vega acta.png') and 'Daniel Torres' in fila('Daniel Torres Vega acta.png'))
    ok('omite_lo_que_ya_tiene_escaneo','ya tiene escaneo' in fila('20220205-cedula.jpg'))
    ok('omite_archivos_sin_alumno','no se encontró al alumno' in fila('desconocido.pdf'))
    ok('omite_si_hay_varios_documentos_sin_palabra','varios documentos' in fila('20240002.pdf') and 'Adjuntar a R-000005' in fila('20240002_cedula.pdf'))
    ok('omite_duplicados_del_zip','otro escaneo del mismo documento' in fila('20230101_titulo (copia).pdf'))
    ok('si_solo_tiene_entregados_crea_uno_nuevo','Crear registro de «Título profesional»' in fila('20240003_titulo.pdf'))
    ok('omite_tipos_no_permitidos_y_archivos_grandes','solo se cargan PDF, JPG o PNG' in fila('20230101.exe') and 'más de 10 MB' in fila('20240001_grande.pdf'))
    ok('no_carga_nada_hasta_confirmar',get('resguardos/r1')['data']['archivo'] is None and len(json.loads(pg.evaluate("JSON.stringify(Object.keys(RSG))")))==6)
    pg.check('#rsZRep');res=pg.inner_text('#rsZRes');ok('reemplazar_cambia_el_plan','1 escaneos se reemplazan' in res or 'se reemplazan' in res and 'Reemplazar el escaneo de R-000002' in fila('20220205-cedula.jpg'))
    pg.fill('#rsZUb','Caja de escaneos 1');pg.fill('#rsZFr','2999-01-01');pg.click('#rsZOk');ok('exige_fecha_valida_para_los_nuevos','fecha de recepción válida' in pg.inner_text('#rsZMsg'));pg.fill('#rsZFr','2026-11-02')
    ok('boton_dice_cuantos',pg.inner_text('#rsZOk')=='Cargar 7 escaneos')
    pg.click('#rsZOk');W(pg,"document.getElementById('rsZMsg').textContent.indexOf('Listo')===0");ok('mensaje_final','Listo: 7 escaneos cargados (3 registros nuevos)' in pg.inner_text('#rsZMsg'))
    r1=get('resguardos/r1')['data'];ok('adjunta_el_escaneo_y_deja_historial',r1['archivo']['name']=='20230101_titulo.pdf' and r1['mov'][-1]['a']=='Escaneo cargado desde ZIP' and r1['mov'][-1]['n']=='20230101_titulo.pdf')
    r2=get('resguardos/r2')['data'];ok('reemplaza_el_escaneo',r2['archivo']['name']=='20220205-cedula.jpg' and r2['archivo']['id']!='a'*32 and r2['mov'][-1]['a'].startswith('Escaneo reemplazado'))
    r3=get('resguardos/r3')['data'];r5=get('resguardos/r5')['data'];r4=get('resguardos/r4')['data']
    ok('los_demas_quedan_como_corresponde',r3['archivo']['name']=='20210311.pdf' and r5['archivo']['name']=='20240002_cedula.pdf' and r4['archivo'] is None)
    docs=ctx.request.get(B+'/api/col/resguardos').json()['docs'];nuevos=sorted([d['data'] for d in docs if d['id'] not in ('r1','r2','r3','r4','r5','r6')],key=lambda x:x['num'])
    ok('crea_tres_registros_con_folios_consecutivos',[n['num'] for n in nuevos]==['R-000007','R-000008','R-000009'] and get('meta/folioR')['data']['n']==9)
    byn={n['mat']+'|'+n['tipo']:n for n in nuevos}
    ok('registros_nuevos_con_sus_datos',byn['20240001|Certificado de estudios']['fechaRec']=='2026-11-02' and byn['20240001|Certificado de estudios']['ubic']=='Caja de escaneos 1' and byn['20240001|Certificado de estudios']['estado']=='resguardo' and byn['20240001|Certificado de estudios']['recibe']=='Administrador' and byn['20240001|Certificado de estudios']['archivo']['name']=='20240001_certificado.pdf' and byn['20220205|Acta de examen profesional']['archivo']['name']=='Daniel Torres Vega acta.png' and byn['20240003|Título profesional']['plan']=='Pedagogía' and byn['20240003|Título profesional']['mov'][0]['a'].startswith('Recibido en resguardo (carga desde ZIP)'))
    ok('los_escaneos_se_abren_con_su_contenido',ctx.request.get(B+'/_blob/'+r1['archivo']['id']).body()==contenido('titulo-ana') and ctx.request.get(B+'/_blob/'+r3['archivo']['id']).body()==contenido('maria'))
    ok('aparecen_en_la_tabla','R-000007' in pg.inner_text('#rsTb') and 'R-000009' in pg.inner_text('#rsTb') and pg.inner_text('#rsC3')=='9' and pg.inner_text('#rsC1')=='8')
    pg.click('#rsZCan')
    # ---- permisos ----
    def ses(u):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);assert r.status==200;return cx
    E1,E2=ses('esc1'),ses('esc2')
    ok('el_escaneo_cargado_solo_lo_abre_quien_edita',E2.request.get(B+'/_blob/'+r1['archivo']['id']).status==200 and E1.request.get(B+'/_blob/'+r1['archivo']['id']).status==403)
    cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pe=pagina(cx);pe.goto(B+'/');W(pe,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pe.fill('#lgU','esc1');pe.fill('#lgP','clave-esc1-123');pe.click('#lgGo');W(pe,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&S.length===6");pe.evaluate("ir('esc')");pe.click('#eTabs [data-et="T"]');pe.wait_for_selector('#rsTb tr')
    ok('quien_solo_ve_no_tiene_el_boton',pe.is_hidden('#rsZip'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
