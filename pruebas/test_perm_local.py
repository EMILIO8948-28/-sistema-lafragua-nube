import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:3055'
os.system('rm -rf /tmp/lf1/datos /tmp/lf1/respaldos')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/lf1',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/api/info',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=9):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:80])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context();ctx.set_default_timeout(9000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');W(pg,"typeof DBH!=='undefined'&&DBH!==null&&ROL==='admin'")
    ok('abierto_sin_usuarios',pg.evaluate("!document.getElementById('mUsr').hidden"))
    pg.click('#mUsr');pg.wait_for_selector('#vUsr:not([hidden])')
    def usu(n,u,pw,perfil,mods=None):
        pg.click('#usNew');pg.wait_for_selector('#dUsr[open]');pg.fill('#usNom',n);pg.fill('#usUsu',u);pg.fill('#usPw',pw);pg.select_option('#usRol',perfil)
        if perfil=='personalizado':pg.evaluate("document.querySelectorAll('#usMods select').forEach(function(s){s.value='none'})")
        for k,v in (mods or {}).items():pg.select_option('#usMods select[data-m="%s"]'%k,v)
        pg.click('#usOk');W(pg,"USERS.some(x=>x.u==='%s')"%u)
    usu('Admin','admin','secreta-1','admin')
    W(pg,"document.body.classList.contains('locked')");ok('pide_login_tras_crear_el_primero',pg.is_visible('#login'))
    pg.fill('#lgU','admin');pg.fill('#lgP','secreta-1');pg.click('#lgGo');W(pg,"APP!==null&&!document.body.classList.contains('locked')");pg.evaluate("ir('usr')");pg.wait_for_selector('#vUsr:not([hidden])')
    usu('Nina','nina','clave-nina','personalizado',{'nomina_adm':'editar','a286':'ver'})
    ok('guardados_con_modulos',pg.evaluate("USERS.find(u=>u.u==='nina').modulos.nomina_adm")=='editar' and pg.evaluate("!!USERS.find(u=>u.u==='nina').hash"))
    pg.evaluate("sessionStorage.clear()");pg.reload();W(pg,"document.body.classList.contains('locked')")
    pg.fill('#lgU','nina');pg.fill('#lgP','clave-nina');pg.click('#lgGo');W(pg,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pg.wait_for_timeout(400)
    vis=pg.evaluate("['mPag','mIns','mEsc','mAcu','mA2','mTit','mNom','mNa','mVer','mUsr','mDoc'].filter(function(i){return !document.getElementById(i).hidden}).sort()")
    ok('nina_ve_solo_sus_modulos',vis==['mA2','mPag'])
    pg.click('#mA2');W(pg,"MOD==='a2'");ok('a286_solo_ver',pg.evaluate("ROL")=='consulta')
    pg.evaluate("ir('home')");pg.click('#mPag');W(pg,"MOD==='na'");ok('nomina_adm_editar',pg.evaluate("ROL")=='admin' and pg.evaluate("BASEROL")=='consulta')
    pg.evaluate("ir('pagos')");ok('sin_acceso_a_pagos',pg.evaluate("MOD")=='home')
    ok('sin_errores_js',len(errs)==0)
    if errs:print(errs[:3])
    b.close()
p.terminate();p.wait()
print(len(R),'comprobaciones','FALLAN:',[k for k,v in R.items() if not v])
