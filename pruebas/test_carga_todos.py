import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3098;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata28',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata28 && mkdir -p /tmp/nbdata28')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=90):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:80])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    pg.evaluate("ir('esc');etab('P')");pg.set_input_files('#pFileJ','/mnt/user-data/outputs/carga_todos_los_planes_y_contenidos.json');pg.wait_for_selector('#pJBar:not([hidden])')
    ok('resumen_de_los_dos_planes','348 asignaturas de Pedagogía, Administración, Contaduría, Derecho, Arquitectura, Enfermería, Ingeniería Industrial, Maestría en Educación con 348 contenidos: 348 nuevas y 0' in pg.inner_text('#pJMsg'))
    pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0")
    ok('mensaje_final','348 asignaturas cargadas (348 nuevas y 0 actualizadas) y 348 contenidos' in pg.inner_text('#pJMsg'))
    ok('resumen_de_planes',pg.evaluate("catItems('Pedagogía').length")==47 and pg.evaluate("catItems('Derecho').length")==49 and 'Pedagogía' in pg.inner_text('#pResumen') and pg.locator('#pResumen tr:has-text("Derecho") td.n').first.inner_text()=='49')
    ok('enfermeria_54_con_contenido',pg.evaluate("catItems('Enfermería').length")==54 and pg.evaluate("catItems('Enfermería').every(function(i){return i.ct===1})"))
    ok('maestria_12_con_contenido',pg.evaluate("catItems('Maestría en Educación').length")==12 and pg.evaluate("catItems('Maestría en Educación').every(function(i){return i.ct===1&&i.clave.indexOf('M')===0})"))
    ok('arquitectura_48_con_contenido',pg.evaluate("catItems('Arquitectura').length")==48 and pg.evaluate("catItems('Arquitectura').every(function(i){return i.ct===1})"))
    ok('administracion_47',pg.evaluate("catItems('Administración').length")==47 and pg.evaluate("catItems('Administración').every(function(i){return i.ct===1})"))
    ok('contaduria_52',pg.evaluate("catItems('Contaduría').length")==52)
    ok('industrial_39',pg.evaluate("catItems('Ingeniería Industrial').length")==39)
    ok('todas_con_contenido',pg.evaluate("catItems('Pedagogía').concat(catItems('Derecho')).concat(catItems('Ingeniería Industrial')).every(function(i){return i.ct===1})"))
    ok('sin_errores_js',len(errs)==0)
    b.close()
p.terminate()
print(len(R),'comprobaciones','FALLAN:',[k for k,v in R.items() if not v])
