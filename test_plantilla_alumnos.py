import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3350;B='http://127.0.0.1:%d'%PORT;TOK='tk-pa';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata109 && mkdir -p /tmp/nbdata109')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata109',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:80])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});pg=ctx.new_page();pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1)
    PER=pg.evaluate("perAct()")
    ctx.request.put(B+'/api/doc/grupos/g1',data=json.dumps({'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':[]}),headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&Object.keys(GRP).length===1");time.sleep(0.5)
    pg.evaluate("ir('esc');etab('A')");pg.wait_for_selector('#aMas')
    pg.set_input_files('#aMasFile','/mnt/user-data/outputs/plantilla_alumnos_ejemplo.csv');pg.wait_for_selector('#dMas[open]');pg.wait_for_timeout(500)
    print('RESUMEN:',pg.inner_text('#masRes'))
    print('DETALLE:',pg.inner_text('#masDet').replace('\n',' | ')[:700])
    pg.locator('#dMas').screenshot(path='/tmp/plantilla_alumnos_carga.png')
    pg.click('#masOk');W(pg,"document.getElementById('masRes').textContent.indexOf('Carga terminada')>-1",60)
    print('FINAL:',pg.inner_text('#masRes'))
    print('ALUMNOS:',pg.evaluate("S.length"),'· con grupo:',pg.evaluate("Object.values(GRP)[0].alumnos.length"),'· con beca:',pg.evaluate("S.filter(function(s){return s.beca}).length"),'· planes:',sorted(set(pg.evaluate("S.map(function(s){return s.programa})"))))
    print('DATOS Mateo:',json.dumps(pg.evaluate("(function(){var s=S.find(function(x){return x.mat==='2026102'});return {nombre:s.nombre,sexo:s.sexo,edad:s.edad,ingreso:s.ingreso,nuevo:s.nuevo,tel:s.tel,tut:s.tut,tutTel:s.tutTel,beca:s.beca,dom:s.dom}})()"),ensure_ascii=False))
    # segunda carga: todo repetido
    pg.evaluate("document.getElementById('dMas').close()");pg.set_input_files('#aMasFile','/mnt/user-data/outputs/plantilla_alumnos_ejemplo.csv');pg.wait_for_selector('#dMas[open]');pg.wait_for_timeout(400)
    print('REPETIDA:',pg.inner_text('#masRes'))
    b.close()
p.terminate()
