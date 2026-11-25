"""Credencial vertical CR80 para PVC (diseño A): PDF real (tamaño de página, frente y reverso), solo QR, costo de $80,
validez según la baja del alumno (pantalla y verificación pública) y sin credenciales de Acuerdo 286."""
import subprocess,time,json,os,urllib.request,base64,io
from playwright.sync_api import sync_playwright
PORT=3117;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,LF_SIN_CONTACTO='1',PORT=str(PORT),DATA_DIR='/tmp/nbdata_cpvc',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_cpvc && mkdir -p /tmp/nbdata_cpvc')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={}
def ok(n,c):R[n]=bool(c)
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def W(pg,js,t=25):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:80])
def foto():
    from PIL import Image,ImageDraw
    im=Image.new('RGB',(300,380),(160,190,210));d=ImageDraw.Draw(im);d.ellipse([90,70,210,210],fill=(224,180,150));b=io.BytesIO();im.save(b,'JPEG');return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
# jsPDF no está disponible sin internet: se usa un registro de dibujo con las mismas llamadas. Las medidas de texto se toman de Liberation Sans (compatible con Helvetica).
MOCK="""()=>{window.__log=[];window.__sav=[];var cv=document.createElement('canvas').getContext('2d');
 function PDF(o){var fs=10,bold=false,f=o&&o.format;if(f==='letter')f=[215.9,279.4];window.__log.push(['page',f[0],f[1]]);var me=this;
  function L(n){return function(){window.__log.push([n].concat(Array.prototype.slice.call(arguments)));return me}}
  ['setFillColor','setDrawColor','setTextColor','setLineWidth','rect','roundedRect','circle','ellipse','line','text','addImage'].forEach(function(n){me[n]=L(n)});
  me.setFont=function(a,s){bold=/bold/.test(s);window.__log.push(['font',bold]);return me};
  me.setFontSize=function(n){fs=n;window.__log.push(['fs',n]);return me};
  me.getTextWidth=function(s){cv.font=(bold?'bold ':'')+'100px "Liberation Sans"';return cv.measureText(String(s)).width/100*fs*0.352778};
  me.splitTextToSize=function(s,w){var ws=String(s).split(' '),out=[],c='';ws.forEach(function(x){var t=c?c+' '+x:x;if(c&&me.getTextWidth(t)>w){out.push(c);c=x}else c=t});if(c)out.push(c);return out};
  me.addPage=function(fm){window.__log.push(['page'].concat(fm?[fm[0],fm[1]]:[215.9,279.4]));return me};
  me.output=function(){return new ArrayBuffer(8)}}
 window.jspdf={jsPDF:PDF};saveFile=function(n,d){window.__sav.push(n);return Promise.resolve()};return 0}"""
def corre(pg,ids,modo):
    pg.evaluate("window.__log=[];window.__sav=[];0")
    pg.evaluate("(a)=>credencialesPDF(S.filter(function(x){return a[0].indexOf(x.id)>-1}),'2026-12-31',a[1])",[ids,modo])
    return pg.evaluate("window.__log"),pg.evaluate("window.__sav")
def paginas(log):return [(e[1],e[2]) for e in log if e[0]=='page']
def textos(log):return [e[1] for e in log if e[0]=='text']
def dibuja(log,ruta,esc=12):
    from PIL import Image,ImageDraw,ImageFont
    pgs=[];dr=None;col={'f':(255,255,255),'d':(0,0,0),'t':(0,0,0)};lw=0.2;fs=10;bold=False
    F=lambda b,s:ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf'%('Bold' if b else 'Regular'),max(int(round(s*0.352778*esc)),1))
    for e in log:
        o=e[0]
        if o=='page':
            im=Image.new('RGB',(int(e[1]*esc),int(e[2]*esc)),(255,255,255));pgs.append(im);dr=ImageDraw.Draw(im)
        elif o=='setFillColor':col['f']=tuple(e[1:4])
        elif o=='setDrawColor':col['d']=tuple(e[1:4])
        elif o=='setTextColor':col['t']=tuple(e[1:4]) if len(e)>=4 else (e[1],)*3
        elif o=='setLineWidth':lw=e[1]
        elif o=='font':bold=e[1]
        elif o=='fs':fs=e[1]
        elif o in('rect','roundedRect'):
            x,y,w,h=[v*esc for v in e[1:5]];st=e[-1] if isinstance(e[-1],str) else 'S'
            if 'F' in st:dr.rectangle([x,y,x+w,y+h],fill=col['f'])
            if 'D' in st or st=='S':dr.rectangle([x,y,x+w,y+h],outline=col['d'],width=max(int(lw*esc),1))
        elif o=='circle':
            x,y,r=[v*esc for v in e[1:4]];st=e[4] if len(e)>4 else 'S'
            if 'F' in st:dr.ellipse([x-r,y-r,x+r,y+r],fill=col['f'])
            else:dr.ellipse([x-r,y-r,x+r,y+r],outline=col['d'],width=max(int(lw*esc),1))
        elif o=='ellipse':
            x,y,rx,ry=[v*esc for v in e[1:5]];dr.ellipse([x-rx,y-ry,x+rx,y+ry],fill=col['f'])
        elif o=='line':dr.line([e[1]*esc,e[2]*esc,e[3]*esc,e[4]*esc],fill=col['d'],width=max(int(lw*esc),1))
        elif o=='text':
            opt=e[4] if len(e)>4 and isinstance(e[4],dict) else {};al=opt.get('align','left')
            dr.text((e[2]*esc,e[3]*esc),str(e[1]),font=F(bold,fs),fill=col['t'],anchor={'left':'ls','center':'ms','right':'rs'}[al])
        elif o=='addImage':
            import base64,io
            src=e[1];x,y,w,h=[v*esc for v in e[3:7]]
            if src.startswith('data:'):
                im2=Image.open(io.BytesIO(base64.b64decode(src.split(',',1)[1]))).convert('RGBA').resize((max(int(w),1),max(int(h),1)));pgs[-1].paste(im2,(int(x),int(y)),im2)
    for i,im in enumerate(pgs):im.save(ruta%i)
    return len(pgs)
errs=[]
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('students/s1',{'mat':'20230101','nombre':'Ana López Martínez','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False,'tut':'Rosa Martínez','tutTel':'7261230000'})
    put('students/s2',{'mat':'20230777','nombre':'María de los Ángeles Hernández de la Cruz Villegas','carrera':'Ingeniería Industrial','programa':'Ingeniería Industrial','ingreso':2023,'nuevo':False})
    put('students/s3',{'mat':'20230303','nombre':'Carlos Baja Pérez','carrera':'Derecho','programa':'Derecho','ingreso':2023,'nuevo':False})
    for i in range(4,12):put('students/s%d'%i,{'mat':'2023%04d'%i,'nombre':'Alumno Prueba%d Apellido'%i,'carrera':'Derecho','programa':'Derecho','ingreso':2023,'nuevo':False})
    put('fotos/s1',{'d':foto()})
    # una persona de Acuerdo 286: vive en su propia colección y no debe tener credencial
    put('acuerdo286/a286x',{'nombre':'Persona','apPat':'Del','apMat':'Doscientos','pagos':[]})
    pg.reload();W(pg,"S.length===11")
    # ---- diseño en pantalla ----
    html=pg.evaluate("credHTML(S.find(function(x){return x.id==='s1'}),'2026-12-31')")
    ok('vista_previa_vertical_270x428',html.count('width:270px;height:428px')==2)
    ok('vista_previa_diseno_A','#405030' in html and '#c9a227' in html and 'LICENCIATURA' in html and 'CREDENCIAL OFICIAL' in html and 'ESCANEA PARA VERIFICAR' in html and 'Firma del titular' in html and 'Control escolar' in html)
    ok('nombres_y_apellidos_separados',pg.evaluate("credNomPartes('Ana López Martínez')")==['Ana','López Martínez'] and pg.evaluate("credNomPartes('María de los Ángeles Hernández de la Cruz Villegas')")==['María de los Ángeles Hernández','de la Cruz Villegas'] and pg.evaluate("credNomPartes('Juan Pérez')")==['Juan','Pérez'])
    ok('solo_qr_sin_codigo_de_barras','barcode' not in html.lower() and html.count('<svg')>=2)
    ok('nivel_por_plan',pg.evaluate("credNivel({programa:'Maestría en Educación'})")=='MAESTRÍA' and pg.evaluate("credNivel({programa:'Doctorado en Educación'})")=='DOCTORADO' and pg.evaluate("credNivel({programa:'Derecho'})")=='LICENCIATURA')
    # ---- PDF (registro de dibujo) ----
    pg.evaluate(MOCK)
    log,sav=corre(pg,['s1','s2'],'tarjeta')
    ok('pvc_tamano_exacto_CR80_vertical',paginas(log)==[(54,85.6)]*4 and sav[0].startswith('credenciales-pvc-'))
    tx=' '.join(textos(log))
    ok('pdf_trae_datos_y_vigencia','20230101' in tx and 'LÓPEZ MARTÍNEZ' in tx and 'VIGENCIA 31/12/2026' in tx and 'CICLO SEP–DIC 2026' in tx and 'Firma del titular' in tx and 'Rosa Martínez · 7261230000' in tx and 'Pedagogía' in tx)
    ok('colores_olivo_y_dorado',any(e[0]=='setFillColor' and e[1:4]==[64,80,48] for e in log) and any(e[0]=='setDrawColor' and e[1:4]==[201,162,39] for e in log))
    ok('solo_un_qr_por_cara_sin_barras',len([e for e in log if e[0]=='rect' and e[3]<0.5 and e[4]<0.5])>200 and 'barcode' not in json.dumps(log).lower())
    log2,_=corre(pg,['s1'],'sangrado');ok('pvc_con_sangrado_60x91_6',paginas(log2)==[(60,91.6)]*2)
    log3,sav3=corre(pg,['s%d'%i for i in range(1,11)],'hoja');ok('hoja_carta_9_por_hoja_con_reversos',len(paginas(log3))==4 and paginas(log3)[0]==(215.9,279.4) and sav3[0].startswith('credenciales-'))
    logD,_=corre(pg,['s1'],'tarjeta')
    # imágenes para revisión visual
    pg.evaluate("(d)=>{FOT['s1']={d:d};FOTR={}}",foto());log,_=corre(pg,['s1'],'tarjeta');dibuja(log,'/tmp/cpvc_s1_%d.png')
    ok('foto_recortada_en_jpeg',any(e[0]=='addImage' and e[2]=='JPEG' and abs(e[5]-20)<0.01 and abs(e[6]-26.4)<0.01 for e in log))
    log,_=corre(pg,['s2'],'sangrado');dibuja(log,'/tmp/cpvc_s2_%d.png')
    ok('nombre_largo_cabe_en_una_linea',[x for x in textos(log) if 'CRUZ' in x]==['DE LA CRUZ VILLEGAS'])
    # ---- QR: solo QR, con la dirección de verificación ----
    qr=pg.evaluate("qrCred(S.find(function(x){return x.id==='s1'}),'2026-12-31')")
    ok('qr_apunta_a_la_verificacion',qr.startswith(B+'/#a.s1.20261231.') or qr.startswith(B+'/verificar#a.s1.20261231.') or '#a.s1.20261231.' in qr)
    # ---- Control escolar: pantalla y cobro de $80 ----
    pg.evaluate("ir('esc');etab('R')");pg.wait_for_selector('#crAlc');pg.wait_for_timeout(400)
    ok('opciones_de_formato_pvc',pg.evaluate("Array.from($('crModo').options).map(function(o){return o.value})")==['tarjeta','sangrado','hoja'])
    ok('costo_80_por_defecto',pg.evaluate("credCosto()")==80 and '$80' in pg.inner_text('#crCobL').replace(',','').replace('.00',''))
    pg.select_option('#crAlc','todos');pg.wait_for_timeout(300)
    ok('no_incluye_acuerdo286',pg.evaluate("S.some(function(s){return s.id==='a286x'})")==False and pg.evaluate("credLista().length")==11 and pg.evaluate("credLista().every(function(s){return !!ST[s.id]})"))
    pg.select_option('#crAlc','uno');pg.fill('#crQ','Ana');pg.wait_for_timeout(300);pg.select_option('#crAl','s1');pg.wait_for_timeout(200)
    pg.check('#crCob');pg.evaluate("window.__sav=[]");pg.click('#crPdf');W(pg,"window.__sav.length===1");pg.wait_for_timeout(500)
    st=ctx.request.get(B+'/api/doc/students/s1').json()['data']
    ok('cargo_de_80_en_la_cuenta',len(st.get('credCargos',[]))==1 and st['credCargos'][0]['monto']==80 and st['credCargos'][0]['motivo']=='primera')
    ok('cargo_aparece_en_los_cargos_del_alumno',pg.evaluate("cargos(S.find(function(x){return x.id==='s1'})).some(function(c){return /Credencial de estudiante \\(primera\\)/.test(c.c)&&c.m===80})"))
    ok('mensaje_con_el_cargo','primera credencial' in pg.inner_text('#crMsg'))
    pg.click('#crPdf');W(pg,"window.__sav.length===2");pg.wait_for_timeout(500)
    st=ctx.request.get(B+'/api/doc/students/s1').json()['data']
    ok('segunda_vez_es_reposicion',len(st['credCargos'])==2 and st['credCargos'][1]['motivo']=='reposición')
    pg.uncheck('#crCob');pg.click('#crPdf');W(pg,"window.__sav.length===3");pg.wait_for_timeout(300)
    ok('sin_marcar_no_cobra',len(ctx.request.get(B+'/api/doc/students/s1').json()['data']['credCargos'])==2)
    # el costo se cambia en Costos y planes
    pg.evaluate("EXTRA.cred=120;renderCred()");ok('costo_configurable','$120' in pg.inner_text('#crCobL').replace(',','').replace('.00',''))
    pg.evaluate("EXTRA.cred=80;renderCred()")
    pg.select_option('#crAlc','docentes');pg.wait_for_timeout(300);ok('docentes_sin_cobro',pg.is_hidden('#crCobL'))
    pg.select_option('#crAlc','uno')
    # ---- baja: la credencial deja de ser válida ----
    code=pg.evaluate("chkTxt('CR|s3|20261231')")
    def verifica(sid,cod):
        return json.loads(urllib.request.urlopen(urllib.request.Request(B+'/api/verificar?t=a&id=%s&c=%s&v=20261231'%(sid,cod),headers=HDR)).read())
    j=verifica('s3',code);ok('antes_de_la_baja_vigente',j['ok'] and j['vigente'] is True and j['nombre']=='Carlos Baja Pérez' and not j.get('baja'))
    s,_=(200,None)
    r=ctx.request.post(B+'/api/bajas/decidir',data=json.dumps({'sid':'s3','accion':'baja','tipo':'Baja voluntaria','motivo':'Cambió de ciudad.'}),headers=HDR)
    ok('baja_registrada',r.status==200)
    j=verifica('s3',code);ok('con_baja_no_es_valida',j['ok'] and j['vigente'] is False and j.get('baja') is True and 'nombre' not in j and 'matricula' not in j)
    ok('qr_alterado_sigue_invalido_por_codigo',json.loads(urllib.request.urlopen(urllib.request.Request(B+'/api/verificar?t=a&id=s3&c=00000000&v=20261231',headers=HDR)).read())['ok'] is False)
    W(pg,"esBaja('s3')");ok('baja_no_aparece_en_la_lista_de_credenciales',pg.evaluate("credLista().every(function(s){return s.id!=='s3'})"))
    pg.evaluate("verCred('s3','20261231',chkTxt('CR|s3|20261231'))");pg.wait_for_selector('#dRc[open]')
    ok('verificacion_en_pantalla_marca_baja','NO válida' in pg.inner_text('#rcRes') and 'dado de baja' in pg.inner_text('#rcRes'))
    pg.evaluate("$('dRc').close()")
    # reincorporar: vuelve a ser válida
    pg.evaluate("ir('esc');etab('B')");pg.select_option('#bjFe','baja');pg.wait_for_selector('#bjTb tr:has-text("Carlos")')
    pg.click('#bjTb tr:has-text("Carlos") [data-bjc="reincorporar"]');pg.wait_for_selector('#dBj[open]');pg.fill('#bjRMot','Regresó.');pg.click('#bjDGo');W(pg,"!esBaja('s3')");pg.wait_for_timeout(500)
    j=verifica('s3',code);ok('al_reincorporarse_vuelve_a_ser_valida',j['ok'] and j['vigente'] is True and not j.get('baja'))
    # página pública
    pv=b.new_context().new_page();pv.on("pageerror",lambda e:errs.append(str(e)))
    r=ctx.request.post(B+'/api/bajas/decidir',data=json.dumps({'sid':'s3','accion':'baja','tipo':'Baja voluntaria','motivo':'Otra vez.'}),headers=HDR)
    pv.goto(B+'/verificar#a.s3.20261231.'+code);pv.wait_for_selector('.sello');pv.wait_for_timeout(500)
    tx=pv.inner_text('body');ok('pagina_publica_credencial_no_valida','Credencial NO válida' in tx and 'Carlos' not in tx and '20230303' not in tx)
    pv.screenshot(path='/tmp/cpvc_verificar_baja.png')
    ok('sin_errores_js',len(errs)==0)
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
if errs:print(errs[:3])
