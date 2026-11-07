import subprocess,time,json,os,urllib.request,base64,io
from playwright.sync_api import sync_playwright
PORT=3103;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata33',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata33 && mkdir -p /tmp/nbdata33')
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
src=open('/tmp/cred_replay.py').read();REC=src[src.index('REC="""')+7:src.index('"""',src.index('REC="""')+7)]
def foto():
    from PIL import Image,ImageDraw
    im=Image.new('RGB',(300,380),(160,190,210));d=ImageDraw.Draw(im);d.ellipse([90,70,210,210],fill=(224,180,150));b=io.BytesIO();im.save(b,'JPEG');return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200
    put('students/s1',{'mat':'20230101','nombre':'Ana López Martínez','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False,'tut':'Rosa Martínez','tutTel':'7261230000','tel':'7261112233'})
    put('students/s2',{'mat':'20230777','nombre':'María de los Ángeles Hernández de la Cruz Villegas','carrera':'Ingeniería Industrial','programa':'Ingeniería Industrial','ingreso':2023,'nuevo':False})
    for i in range(3,12):put('students/s%d'%i,{'mat':'2023%04d'%i,'nombre':'Alumno %d'%i,'carrera':'Derecho','programa':'Derecho','ingreso':2023,'nuevo':False})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':'Sep–Dic 2026','cuat':3,'alumnos':['s1']})
    pg.reload();W(pg,"S.length===11");pg.evaluate(REC);pg.evaluate("()=>{window.__qrs=[];var q0=qrPDF;qrPDF=function(d,t,x,y,l){window.__qrs.push(t);return q0(d,t,x,y,l)};return 0}")
    def corre(ids,modo):
        pg.evaluate("window.__log=[];window.__qrs=[];window.__sav=[];0")
        pg.evaluate("(a)=>credencialesPDF(S.filter(function(x){return a[0].indexOf(x.id)>-1}),'2026-12-31',a[1])",[ids,modo])
        return pg.evaluate("window.__log"),pg.evaluate("window.__sav"),pg.evaluate("window.__qrs")
    pg.evaluate("(d)=>{FOT['s1']={d:d}}",foto())
    log,sav,qrs=corre(['s1'],'tarjeta')
    txt=[e[1] for e in log if e[0]=='text']
    ok('dos_paginas_por_alumno_en_tamano_tarjeta',len([e for e in log if e[0]=='page'])==1 and 'credenciales-' in sav[0])
    ok('franja_verde_olivo_y_dorado',any(e[0]=='fc' and e[1:4]==[72,82,46] for e in log) and any(e[0]=='dc' and e[1:4]==[185,153,74] for e in log))
    ok('textos_del_frente','CREDENCIAL DE ESTUDIANTE' in txt and 'ANA LÓPEZ' in ' '.join(txt) and '20230101' in txt and 'PLAN DE ESTUDIOS' in txt and 'Pedagogía' in txt and 'GRUPO' in txt and '4821 · sept. 2023' in txt and 'VIGENCIA  31/12/2026' in txt)
    ok('nombre_vertical_letra_por_letra',len([e for e in log if e[0]=='text' and e[4].get('angle')==90])==len('UNIVERSIDAD LAFRAGUA'))
    ok('fotografia_circular_en_png',len([e for e in log if e[0]=='img' and e[2]=='PNG' and e[1].startswith('data:image/png') and abs(e[5]-23)<0.01])>=1 and any(e[0]=='circle' and e[4]=='S' for e in log))
    ok('reverso_con_emergencia_y_telefono','EN CASO DE EMERGENCIA' in txt and 'Rosa Martínez · 7261230000' in txt and 'TELÉFONO DEL ALUMNO' in txt and '7261112233' in txt and 'Firma del alumno' in txt and 'Escanee para verificar' in txt)
    ok('qr_de_verificacion',len(qrs)==1 and qrs[0].startswith(B+'/verificar#a.s1.20261231.'))
    ok('dos_logotipos_uno_en_cada_cara',len([e for e in log if e[0]=='img' and e[2]=='PNG' and abs(e[5]-11.8)<0.01])==2)
    # sin fotografía, sin contactos y nombre largo
    log2,sav2,qrs2=corre(['s2'],'tarjeta');txt2=[e[1] for e in log2 if e[0]=='text']
    ok('sin_fotografia_dibuja_silueta',any(e[0]=='ellipse' for e in log2) and not any(e[0]=='img' and abs(e[5]-23)<0.01 for e in log2))
    ok('sin_contactos_no_imprime_esos_bloques','EN CASO DE EMERGENCIA' not in txt2 and 'TELÉFONO DEL ALUMNO' not in txt2 and 'INGRESO' in txt2 and 'sept. 2023' in txt2)
    ok('nombre_largo_completo',' '.join(t for t in txt2 if t.isupper() and ('MAR' in t or 'HERN' in t or 'VILLEGAS' in t or 'CRUZ' in t)).count('VILLEGAS')==1 and 'Ingeniería Industrial' in txt2)
    # hojas carta: 8 por hoja
    ids=['s%d'%i for i in range(1,10)]
    log3,sav3,qrs3=corre(ids,'carta')
    ok('hojas_carta_frentes_y_reversos',len([e for e in log3 if e[0]=='page'])==3 and len(qrs3)==9 and sav3[0].startswith('credenciales-'))
    # pantalla
    html=pg.evaluate("credHTML(S.find(function(x){return x.id==='s1'}),'2026-12-31')")
    ok('vista_previa_con_el_nuevo_diseno','#48522e' in html and '#b9994a' in html and 'CREDENCIAL DE ESTUDIANTE' in html and 'VIGENCIA' in html and 'Firma del alumno' in html and '<svg' in html and 'border-radius:50%' in html and 'Escanee para verificar' in html and '#0f6b63' not in html)
    # portal del alumno
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'20230101','name':'Ana','alumno':'s1','clave':'abcd-efgh'}]}),headers=HDR)
    cp=b.new_context(viewport={'width':1000,'height':900});cp.set_default_timeout(15000);pp=cp.new_page();pp.on("pageerror",lambda e:errs.append(str(e)));pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pp.fill('#lgU','20230101');pp.fill('#lgP','abcd-efgh');pp.click('#lgGo');pp.wait_for_selector('#dPw[open]');pp.fill('#pwA','abcd-efgh');pp.fill('#pwN','clave-ana-77');pp.fill('#pwR','clave-ana-77');pp.click('#pwOk');W(pp,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&S.length===1&&!document.getElementById('dPw').open")
    pp.wait_for_timeout(600);ok('portal_muestra_la_credencial_nueva','CREDENCIAL DE ESTUDIANTE' in pp.inner_text('#poBody') and 'Firma del alumno' in pp.inner_text('#poBody') and pp.is_visible('#poCred'))
    pp.screenshot(path='/tmp/cred_portal.png',full_page=True)
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
