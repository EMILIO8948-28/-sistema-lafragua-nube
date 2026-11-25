import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3196;B='http://127.0.0.1:%d'%PORT;TOK='tok-ce-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_ce',LF_SETUP_TOKEN=TOK,LF_SIN_CONTACTO='1',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_ce && mkdir -p /tmp/nbdata_ce')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=25):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
SRC='/mnt/user-data/outputs/carga_pedagogia_plan_y_contenidos.json'
D=json.load(open(SRC,encoding='utf-8'))
import atexit
atexit.register(lambda:(print('PARCIAL',R),p.terminate()))
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    PER=pg.evaluate("perAct()")
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('catalogo/pedagogia',D['colecciones']['catalogo']['pedagogia'])
    for i,n in enumerate(['Ana López','Beto Mena'],1):put('students/s%d'%i,{'mat':'2026%03d'%i,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('docentes/d1',{'nombre':'Mtro. Pedro Soto','esp':'Historia','mail':'','tel':'','asig':[]})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2']})
    base=dict(per=PER,plan='Pedagogía',cuat=1,ini='08:00',fin='10:00')
    put('materias/m1',dict(base,nom='Didáctica general',docId='d1'))
    put('criterios/m1',{'items':[{'id':'cr1','nom':'Examen','peso':100}]})
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'doc1','name':'Mtro. Pedro Soto','rol':'docente','clave':'clave-doc1-123','doc':'d1'}),headers=HDR)
    pg.reload();W(pg,"Object.keys(MAT).length===1&&S.length===2&&catItems('Pedagogía').length===47")
    def remoto(k):
        put('students/s2',{'mat':'2026002','nombre':'Beto Mena %d'%k,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False});put('calif/s2',{'items':[]});pg.wait_for_timeout(1500)
    # ---- A: calificaciones anteriores (historial) ----
    pg.evaluate("ir('esc')");pg.wait_for_selector('#eTabs [data-et="H"]');pg.click('#eTabs [data-et="H"]');pg.wait_for_selector('#eH:not([hidden])')
    pg.fill('#hAl','2026001 — Ana López');pg.wait_for_selector('#hGrid input[data-hid]')
    ins=pg.locator('#hGrid input[data-hid]');ins.nth(0).fill('9.5');ins.nth(1).fill('8');ins.nth(2).fill('7')
    remoto(1)
    v=pg.evaluate("Array.from(document.querySelectorAll('#hGrid input[data-hid]')).slice(0,3).map(function(i){return i.value})")
    ok('historial_no_pierde_lo_escrito_cuando_llega_un_cambio',v==['9.5','8','7'])
    pg.click('#hGuarda');W(pg,"itemsDe('s1').length===3")
    ok('historial_guarda_lo_que_se_escribio',sorted(x['cal'] for x in json.loads(json.dumps(pg.evaluate("itemsDe('s1')"))))==[7,8,9.5])
    pg.wait_for_timeout(300)
    v2=pg.evaluate("Array.from(document.querySelectorAll('#hGrid input[data-hid]')).slice(0,3).map(function(i){return i.value})")
    ok('historial_muestra_lo_guardado_despues_de_guardar',v2==['9.5','8','7'])
    # al cambiar de alumno se limpia
    pg.fill('#hAl','2026002 — Beto Mena 1');pg.wait_for_timeout(500)
    ok('historial_al_cambiar_de_alumno_muestra_el_nuevo',pg.evaluate("Array.from(document.querySelectorAll('#hGrid input[data-hid]')).slice(0,3).map(function(i){return i.value})")==['','',''])
    ins=pg.locator('#hGrid input[data-hid]');ins.nth(0).fill('6')
    remoto(2);ok('historial_segundo_alumno_tambien_se_conserva',pg.evaluate("document.querySelector('#hGrid input[data-hid]').value")=='6')
    # ---- B: calificaciones por grupo (administrador) ----
    pg.evaluate("ir('esc');etab('C')");pg.wait_for_selector('#kGr')
    pg.select_option('#kGr','g1');pg.select_option('#kMat','m1');pg.wait_for_selector('#kTb input[data-sid]')
    pg.locator('#kTb input[data-sid]').nth(0).fill('9');pg.locator('#kTb input[data-sid]').nth(1).fill('7.5')
    remoto(3)
    ok('grupo_admin_no_pierde_lo_escrito',pg.evaluate("Array.from(document.querySelectorAll('#kTb input[data-sid]')).map(function(i){return i.value})")==['9','7.5'])
    pg.click('#kGuardar');W(pg,"itemOf('s1','m1')&&itemOf('s2','m1')")
    ok('grupo_admin_guarda',pg.evaluate("itemOf('s1','m1').cal")==9 and pg.evaluate("itemOf('s2','m1').cal")==7.5)
    # ---- C: docente ----
    cx=b.new_context(viewport={'width':1200,'height':1000});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pp.fill('#lgU','doc1');pp.fill('#lgP','clave-doc1-123');pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1500)
    pp.evaluate("ir('doc')");pp.wait_for_selector('#dmTb [data-ev], [data-ev]')
    pp.locator('[data-ev]').first.click();pp.wait_for_selector('#evTabla input[data-sid]')
    pp.locator('#evTabla input[data-sid]').nth(0).fill('10');pp.locator('#evTabla input[data-sid]').nth(1).fill('6')
    put('calif/s1',{'items':[]});put('docentes/d1',{'nombre':'Mtro. Pedro Soto','esp':'Historia','mail':'','tel':'','asig':[]});pp.wait_for_timeout(1800)
    ok('docente_no_pierde_lo_escrito',pp.evaluate("Array.from(document.querySelectorAll('#evTabla input[data-sid]')).map(function(i){return i.value})")==['10','6'])
    ok('sin_errores_de_pagina',not errs)
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v]);print(errs[:3])
