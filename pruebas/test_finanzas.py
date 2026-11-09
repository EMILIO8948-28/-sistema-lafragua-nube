import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3115;B='http://127.0.0.1:%d'%PORT;TOK='tok-fn-123'
os.system('rm -rf /tmp/nbdata46 && mkdir -p /tmp/nbdata46')
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata46',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=30):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(0.8)
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('students/s1',{'mat':'20260001','nombre':'Ana López','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('ledger/s1',{'pagos':[{'id':'p1','fecha':'2026-11-01','monto':1300,'metodo':'Transferencia','estado':'pendiente','folio':'R-000001'}]})
    put('empleados/e1',{'nombre':'Luis Admin','puesto':'Auxiliar','activo':True,'sueldo':8000,'period':'Mensual'})
    usr=lambda u,n,r,m=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**({'modulos':m} if m else {}))),headers=HDR)
    usr('caja1','Caja','caja');usr('nomi1','Nomi','personalizado',{'nomina_doc':'editar'});usr('adm1','Adm','personalizado',{'nomina_adm':'editar'});usr('ver1','Ver','personalizado',{'ver':'editar'});usr('esc1','Esc','personalizado',{'escolar':'ver'});usr('est1','Est','personalizado',{'estado':'ver'})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===1")
    # ---- administrador ----
    pg.evaluate("ir('home')");t=pg.inner_text('#vHome')
    ok('el_panel_muestra_finanzas_y_no_control_de_pagos','Finanzas' in pg.inner_text('#mPag') and 'Control de pagos' not in pg.inner_text('body'))
    ok('las_tarjetas_de_nomina_y_verificacion_ya_no_estan_en_el_panel',all(pg.is_hidden('#'+i) for i in ['mNom','mNa','mVer']))
    ok('el_resumen_junta_pagos_verificacion_y_nomina','1 alumno' in pg.inner_text('#mPagS') and '1 por verificar' in pg.inner_text('#mPagS') and 'Nómina:' in pg.inner_text('#mPagS') and 'empleado activo' in pg.inner_text('#mPagS'))
    pg.click('#mPag');W(pg,"MOD==='pagos'")
    ok('el_modulo_se_llama_finanzas','Finanzas' in pg.inner_text('#ttl') and 'Control de pagos' not in pg.inner_text('#ttl'))
    ok('muestra_las_cuatro_secciones',pg.is_visible('#finTabs') and [pg.is_visible('#finTabs [data-fm="%s"]'%m) for m in ['pagos','ver','nom','na']]==[True]*4 and pg.inner_text('#finTabs').replace('\n',' | ')=='Pagos de alumnos | Verificación de pagos | Nómina docente | Nómina administrativa')
    ok('abre_en_pagos_de_alumnos_marcado',pg.evaluate("document.querySelector('#finTabs [data-fm=pagos]').className")=='p' and pg.is_visible('#vAl') and pg.is_visible('#tAl') and pg.is_visible('#tGa') and pg.is_visible('#tEf'))
    for m,vista,txt in [('ver','vVer','Transferencias'),('nom','vNom','Tarifa por hora'),('na','vNa','Nuevo empleado')]:
        pg.click('#finTabs [data-fm="%s"]'%m);W(pg,"MOD==='%s'"%m)
        ok('seccion_%s'%m,pg.is_visible('#'+vista) and 'Finanzas' in pg.inner_text('#ttl') and pg.is_visible('#finTabs') and pg.evaluate("document.querySelector('#finTabs [data-fm=%s]').className"%m)=='p' and pg.evaluate("document.querySelector('#finTabs [data-fm=pagos]').className")=='' and pg.is_hidden('#tabs'))
    pg.click('#finTabs [data-fm="pagos"]');W(pg,"MOD==='pagos'");ok('vuelve_a_pagos_de_alumnos_con_sus_pestanas',pg.is_visible('#vAl') and pg.is_visible('#tabs'))
    pg.click('#tGa');ok('las_pestanas_internas_siguen_funcionando',pg.is_visible('#vGa') and pg.is_visible('#finTabs'))
    pg.click('#nHome');W(pg,"MOD==='home'");ok('al_salir_se_ocultan_las_secciones',pg.is_hidden('#finTabs'))
    # ---- accesos antiguos siguen funcionando ----
    pg.evaluate("ir('nom')");ok('los_enlaces_internos_a_nomina_siguen_sirviendo',pg.is_visible('#vNom') and pg.is_visible('#finTabs'))
    # ---- permisos ----
    def entra(u):
        cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'");pp.wait_for_timeout(400);return pp
    secs=lambda pp:[m for m in ['pagos','ver','nom','na'] if pp.is_visible('#finTabs [data-fm="%s"]'%m)]
    pc=entra('caja1');pc.click('#mPag');W(pc,"MOD==='pagos'");ok('caja_ve_pagos_y_verificacion_pero_no_nominas',secs(pc)==['pagos','ver'])
    pn=entra('nomi1');ok('solo_nomina_docente_ve_finanzas',pn.is_visible('#mPag'));pn.click('#mPag');W(pn,"MOD==='nom'");ok('y_entra_directo_a_su_seccion',secs(pn)==['nom'] and pn.is_visible('#vNom') and 'Finanzas' in pn.inner_text('#ttl'))
    pa=entra('adm1');pa.click('#mPag');W(pa,"MOD==='na'");ok('solo_nomina_administrativa_entra_a_su_seccion',secs(pa)==['na'])
    pv=entra('ver1');pv.click('#mPag');W(pv,"MOD==='ver'");ok('solo_verificacion_entra_a_su_seccion',secs(pv)==['ver'])
    pe=entra('est1');pe.click('#mPag');W(pe,"MOD==='pagos'");ok('estado_de_cuenta_final_se_alcanza_por_pagos_de_alumnos',secs(pe)==['pagos'] and pe.is_visible('#tEf') and pe.is_hidden('#tAl'))
    ps=entra('esc1');ok('quien_no_tiene_finanzas_no_ve_la_tarjeta',ps.is_hidden('#mPag'));ps.evaluate("ir('nom')");ok('ni_puede_entrar_a_una_seccion',ps.evaluate("MOD")=='home' and ps.is_hidden('#finTabs'))
    # ---- usuarios y permisos ----
    pg.evaluate("ir('usr')");W(pg,"MOD==='usr'");pg.wait_for_selector('#usTb tr')
    ok('permisos_muestran_las_secciones_dentro_de_finanzas',all(x in pg.inner_text('#usTb')+pg.inner_text('#vUsr') for x in ['Finanzas · Pagos de alumnos','Finanzas · Verificación de pagos','Finanzas · Nómina docente','Finanzas · Nómina administrativa','Finanzas · Gastos y corte de caja']))
    ok('en_ninguna_parte_dice_control_de_pagos',pg.evaluate("document.documentElement.outerHTML.indexOf('Control de pagos')")==-1)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.evaluate("ir('home')");pg.screenshot(path='/tmp/fn_panel.png');pg.click('#mPag');W(pg,"MOD==='pagos'");pg.click('#finTabs [data-fm="nom"]');W(pg,"MOD==='nom'");pg.wait_for_timeout(300);pg.screenshot(path='/tmp/fn_finanzas.png')
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
