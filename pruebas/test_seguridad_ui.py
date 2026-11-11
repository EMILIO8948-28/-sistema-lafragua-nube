import subprocess,time,json,os,urllib.request,hmac,hashlib,base64,struct,re
from playwright.sync_api import sync_playwright
PORT=3310;B='http://127.0.0.1:%d'%PORT;TOK='tok-su-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata105 && mkdir -p /tmp/nbdata105')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata105',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
def b32d(s):return base64.b32decode(s+'='*((8-len(s)%8)%8))
def totp(sec,step):
    h=hmac.new(b32d(sec),struct.pack('>Q',step),hashlib.sha1).digest();o=h[-1]&15;n=int.from_bytes(h[o:o+4],'big')&0x7fffffff;return '%06d'%(n%10**6)
USADO={}
def codigo(sec):
    pp=int(time.time()//30)
    for d in (0,1,-1):
        s=pp+d
        if s>USADO.get(sec,0):USADO[sec]=s;return totp(sec,s)
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'}),headers=HDR)
    def abre():
        c2=b.new_context(viewport={'width':1200,'height':1000});c2.set_default_timeout(15000);pp=pagina(c2);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')");return pp
    def entra(pp,u,c):
        pp.fill('#lgU',u);pp.fill('#lgP',c);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1200)
    pc=abre()
    ok('la_pantalla_de_entrada_enlaza_el_aviso_de_privacidad',pc.locator('a[href="/privacidad"]').count()>=1 and pc.is_hidden('#lgCW'))
    entra(pc,'caja1','clave-caja1-123')
    ok('la_sesion_ofrece_el_boton_seguridad',pc.is_visible('#bSeg'))
    pc.click('#bSeg');pc.wait_for_selector('#dSx[open]');pc.wait_for_timeout(300)
    ok('muestra_que_esta_desactivada_y_ofrece_activarla','Desactivada' in pc.inner_text('#sxEstado') and pc.is_visible('#sxIniciar'))
    pc.click('#sxIniciar');pc.wait_for_selector('#sxQR:not([hidden])')
    SEC=pc.inner_text('#sxSecreto').replace(' ','')
    ok('muestra_el_qr_y_la_clave',pc.locator('#sxSvg svg').count()==1 and re.match(r'^[A-Z2-7]{32}$',SEC) and pc.locator('#sxSvg svg path').count()==1)
    pc.fill('#sxCod','000000');pc.click('#sxActiva');pc.wait_for_timeout(500);ok('un_codigo_malo_se_explica','no es correcto' in pc.inner_text('#sxMsg'))
    pc.fill('#sxCod',codigo(SEC));pc.click('#sxActiva');pc.wait_for_selector('#sxCodigos:not([hidden])')
    REC=pc.inner_text('#sxLista').split('\n');REC=[x.strip() for x in REC if x.strip()]
    ok('al_activarla_da_los_10_codigos_de_recuperacion_y_lo_dice',len(REC)==10 and 'Activada' in pc.inner_text('#sxEstado') and pc.is_visible('#sxActivo'));pc.click('#sxCerrar')
    # ---- iniciar sesión con los dos pasos ----
    pl=abre();pl.fill('#lgU','caja1');pl.fill('#lgP','clave-caja1-123');pl.click('#lgGo');pl.wait_for_selector('#lgCW:not([hidden])')
    ok('despues_de_la_contrasena_pide_el_codigo',pl.is_visible('#lgC') and pl.inner_text('#lgGo')=='Verificar' and pl.is_disabled('#lgP') and 'código' in pl.inner_text('#lgE').lower())
    pl.fill('#lgC','123456');pl.click('#lgGo');pl.wait_for_timeout(700);ok('un_codigo_malo_se_rechaza_sin_perder_el_paso','no es correcto' in pl.inner_text('#lgE') and pl.is_visible('#lgCW'))
    pl.fill('#lgC',REC[0]);pl.click('#lgGo');W(pl,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pl.wait_for_timeout(1200)
    ok('con_un_codigo_de_recuperacion_entra',pl.evaluate("APP.u")=='caja1' and pl.evaluate("LF_ME.dosPasos")==True)
    pl.click('#bSeg');pl.wait_for_selector('#dSx[open]');pl.wait_for_timeout(300)
    ok('el_dialogo_dice_cuantos_codigos_quedan','9 códigos' in pl.inner_text('#sxEstado'))
    pl.fill('#sxClave','clave-caja1-123');pl.fill('#sxCod2',REC[1]);pl.click('#sxQuita');pl.wait_for_timeout(1200);print('DBG',repr(pl.inner_text('#sxMsg')),repr(pl.inner_text('#sxEstado')),REC[1],flush=True)
    ok('se_puede_desactivar_con_contrasena_y_codigo','Desactivada' in pl.inner_text('#sxEstado') and pl.is_visible('#sxIniciar'))
    # ---- el administrador ----
    pg.evaluate("ir('home')");pg.wait_for_timeout(500)
    ok('el_panel_tiene_la_tarjeta_seguridad_y_privacidad',pg.is_visible('#mSp') and 'Seguridad y privacidad' in pg.inner_text('#mSp'))
    pg.click('#mSp');W(pg,"MOD==='sp'&&SXD");ok('abre_el_modulo_con_la_lista_de_personas','Caja' in pg.inner_text('#sxUsTb') and 'Administrador' in pg.inner_text('#sxUsTb'))
    pg.click('#sxTpri');pg.fill('#pvEnt','Universidad Lafragua');pg.fill('#pvDom','Av. Principal 123, Tejupilco');pg.fill('#pvCor','privacidad@lafragua.mx');pg.fill('#pvRes','Control escolar');pg.check('#pvAcep');pg.click('#pvGuarda');W(pg,"document.getElementById('pvMsg2').textContent.indexOf('guardado')>-1")
    ok('guarda_el_aviso_y_muestra_su_version_y_la_aceptacion','Versión 2' in pg.inner_text('#pvInfo') and '0 personas' in pg.inner_text('#pvInfo'))
    pc2=abre();entra(pc2,'caja1','clave-caja1-123');pc2.wait_for_selector('#dPv[open]')
    ok('con_la_aceptacion_activa_aparece_el_aviso_al_entrar',pc2.is_disabled('#pvOk') and pc2.inner_text('#pvV')=='2' and pc2.locator('#dPv a[href="/privacidad"]').count()==1)
    pc2.keyboard.press('Escape');pc2.wait_for_timeout(300);ok('no_se_puede_cerrar_sin_aceptar',pc2.evaluate("document.getElementById('dPv').open")==True)
    pc2.check('#pvAc');pc2.click('#pvOk');pc2.wait_for_timeout(800);ok('al_aceptar_se_cierra',pc2.evaluate("document.getElementById('dPv').open")==False)
    pc2.reload();W(pc2,"typeof APP!=='undefined'&&APP!==null");pc2.wait_for_timeout(1200);ok('y_no_vuelve_a_pedirlo',pc2.evaluate("document.getElementById('dPv').open")==False)
    pg.click('#sxTpri');pg.evaluate("sxCarga()");pg.wait_for_timeout(700);ok('el_administrador_ve_cuantos_aceptaron','1 personas la han aceptado' in pg.inner_text('#pvInfo'))
    pg.uncheck('#pvAcep');pg.click('#pvGuarda');pg.wait_for_timeout(700)
    # ---- dos pasos obligatorios para administradores ----
    pg.click('#sxTdos');pg.check('#sxExigir');pg.click('#sxGExigir');W(pg,"document.getElementById('sxDosMsg').textContent.indexOf('guardada')>-1")
    pa=abre();entra(pa,'admin','clave-segura-1');pa.wait_for_selector('#dSx[open]')
    ok('al_administrador_se_le_obliga_a_activarla',pa.is_hidden('#sxCerrar') and 'exige' in pa.inner_text('#sxEstado'));pa.keyboard.press('Escape');pa.wait_for_timeout(300);ok('y_el_cuadro_no_se_puede_cerrar',pa.evaluate("document.getElementById('dSx').open")==True)
    pa.click('#sxIniciar');pa.wait_for_selector('#sxQR:not([hidden])');SA=pa.inner_text('#sxSecreto').replace(' ','');pa.fill('#sxCod',codigo(SA));pa.click('#sxActiva');pa.wait_for_selector('#sxCodigos:not([hidden])')
    ok('al_activarla_ya_puede_cerrarlo',pa.is_visible('#sxCerrar'));pa.click('#sxCerrar');ok('y_trabajar_con_normalidad',pa.evaluate("document.getElementById('dSx').open")==False)
    # ---- conservación ----
    pa.evaluate("ir('sp')");W(pa,"MOD==='sp'&&SXD");pa.click('#sxTcon');pa.wait_for_timeout(300)
    ok('muestra_los_plazos_y_lo_pendiente',pa.input_value('#cnIne')=='1' and pa.input_value('#cnFir')=='5' and pa.locator('#cnTb tr').count()==7)
    pa.fill('#cnIne','20');pa.click('#cnGuarda');pa.wait_for_timeout(600);ok('un_plazo_fuera_de_rango_se_explica','0 a 15' in pa.inner_text('#cnMsg'));pa.fill('#cnIne','1')
    pa.click('#cnDep');pa.wait_for_timeout(400);ok('exige_elegir_que_depurar','Elige qué depurar' in pa.inner_text('#cnMsg'))
    ok('sin_registros_viejos_no_hay_nada_que_marcar',pa.locator('#cnTb input[type=checkbox]:not([disabled])').count()>=0)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pc.keyboard.press('Escape');pg.evaluate("ir('sp')");pg.click('#sxTdos');pg.wait_for_timeout(400);pg.screenshot(path='/tmp/sx_modulo.png',full_page=True)
    pl.evaluate("document.getElementById('dSx').close()");pc2.evaluate("1");ps=abre();entra(ps,'caja1','clave-caja1-123');ps.click('#bSeg');ps.wait_for_selector('#dSx[open]');ps.click('#sxIniciar');ps.wait_for_selector('#sxQR:not([hidden])');ps.wait_for_timeout(300);ps.locator('#dSx').screenshot(path='/tmp/sx_qr.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
