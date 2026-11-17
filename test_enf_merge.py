import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3104;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata34',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata34 && mkdir -p /tmp/nbdata34')
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
    raise TimeoutError(js[:80])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    pg.evaluate("ir('esc');etab('P')")
    pg.set_input_files('#pFileJ','/tmp/enf/solo_nombres.json');pg.wait_for_selector('#pJBar:not([hidden])');ok('primero_solo_los_nombres','54 asignaturas de Enfermería con 0 contenidos: 54 nuevas y 0' in pg.inner_text('#pJMsg'))
    pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0")
    ids=pg.evaluate("catItems('Enfermería').map(function(i){return i.id}).sort().join()");ok('quedan_54_sin_contenido',pg.evaluate("catItems('Enfermería').length")==54 and pg.evaluate("catItems('Enfermería').every(function(i){return !i.ct})"))
    pg.set_input_files('#pFileJ','/mnt/user-data/outputs/carga_enfermeria_plan_y_contenidos.json');pg.wait_for_selector('#pJBar:not([hidden])');m=pg.inner_text('#pJMsg')
    ok('despues_el_contenido_se_agrega_sin_duplicar','54 asignaturas de Enfermería con 54 contenidos: 0 nuevas y 54 que ya existen' in m)
    pg.click('#pJOk');W(pg,"document.getElementById('pJMsg').textContent.indexOf('Listo')===0")
    ok('mismas_54_materias_ahora_con_contenido',pg.evaluate("catItems('Enfermería').length")==54 and pg.evaluate("catItems('Enfermería').every(function(i){return i.ct===1})") and pg.evaluate("catItems('Enfermería').map(function(i){return i.id}).sort().join()")==ids)
    pg.select_option('#pPlan','Enfermería');pg.evaluate("renderPlan()");pg.locator('#pLista [data-ct]').filter(has_text='Contenido').first.click()
    pg.wait_for_selector('#dCt[open]');W(pg,"document.getElementById('ctTxt').value.length>800");ok('se_abre_el_contenido_de_una_materia','OBJETIVO GENERAL' in pg.input_value('#ctTxt') and 'Total: 100%' in pg.input_value('#ctTxt'))
    ok('sin_errores_js',len(errs)==0)
    b.close()
p.terminate()
print(len(R),'comprobaciones','FALLAN:',[k for k,v in R.items() if not v])
