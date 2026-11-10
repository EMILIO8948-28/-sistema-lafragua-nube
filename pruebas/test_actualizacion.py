import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3127;B='http://127.0.0.1:%d'%PORT;TOK='tok-ac-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata49 && mkdir -p /tmp/nbdata49')
def arranca(precarga):
    env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata49',LF_SETUP_TOKEN=TOK)
    if not precarga:env['LF_SIN_PRECARGA']='1'
    pr=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    for _ in range(80):
        time.sleep(0.25)
        try:urllib.request.urlopen(B+'/salud',timeout=1);break
        except Exception:pass
    return pr
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
p=arranca(False)
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('students/s1',{'mat':'20260001','nombre':'Ana López','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('ledger/s1',{'pagos':[{'id':'p1','fecha':'2026-11-01','monto':1300,'metodo':'Efectivo','estado':'confirmado','folio':'R-000001'}]})
    put('empleados/e1',{'nombre':'Luis Administrativo','puesto':'Auxiliar contable','activo':True,'sueldo':8000,'period':'Mensual','creado':'2026-10-01'})
    put('empleados/e2',{'nombre':'Marta Recepción','puesto':'Recepcionista','activo':True,'sueldo':7000,'period':'Quincenal','creado':'2026-10-01'})
    put('nomina_admin/2026-10',{'mes':'2026-10','aj':{},'pagos':{'e1':{'folio':'NA-000001','monto':8000,'fecha':'2026-10-31','metodo':'Transferencia'}}})
    put('gastos/2026-11',{'items':[{'id':'g1','fecha':'2026-11-02','concepto':'Papelería','cat':'Oficina','monto':450,'metodo':'Efectivo'}]})
    put('cortes/2026-11-01',{'fondo':500,'contado':1800,'obs':''})
    put('nomina/2026-10',{'filas':{},'pagos':{}})
    antes=ctx.request.get(B+'/api/info').json()['colecciones'];antes={c['coleccion']:c['n'] for c in antes}
    ok('hay_datos_de_finanzas_antes_de_actualizar',antes.get('empleados')==2 and antes.get('nomina_admin')==1 and antes.get('gastos')==1 and antes.get('cortes')==1 and antes.get('ledger')==1)
    b.close()
p.terminate();time.sleep(0.8)
# ---- "se sube una versión nueva": el servidor se detiene y arranca otra vez con los mismos datos (y la precarga activada) ----
p=arranca(True)
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');W(pg,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pg.fill('#lgU','admin');pg.fill('#lgP','clave-segura-1');pg.click('#lgGo');W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    des=ctx.request.get(B+'/api/info').json()['colecciones'];des={c['coleccion']:c['n'] for c in des}
    ok('despues_de_actualizar_siguen_todos_los_registros_de_finanzas',all(des.get(k)==antes[k] for k in ['empleados','nomina_admin','gastos','cortes','ledger','students','nomina']))
    ok('la_precarga_solo_agrego_materias',des.get('catalogo',0)>=8 and 'empleados' in des)
    ok('el_usuario_administrador_sigue_igual',ctx.request.get(B+'/api/doc/config/plans').status==200)
    pg.evaluate("ir('na')");pg.wait_for_selector('#vNa:not([hidden])');pg.evaluate("document.getElementById('naT2').click()");pg.wait_for_selector('#naP2:not([hidden])');time.sleep(0.5)
    tx=pg.inner_text('#vNa')
    ok('la_nomina_administrativa_muestra_sus_empleados','Luis Administrativo' in tx and 'Marta Recepción' in tx)
    nd=ctx.request.get(B+'/api/doc/nomina_admin/2026-10').json()['data'];ok('y_el_pago_ya_registrado_queda_igual',nd['pagos']['e1']['folio']=='NA-000001' and nd['pagos']['e1']['monto']==8000)
    ok('al_igual_que_los_gastos_y_el_corte_de_caja',ctx.request.get(B+'/api/doc/gastos/2026-11').json()['data']['items'][0]['concepto']=='Papelería' and ctx.request.get(B+'/api/doc/cortes/2026-11-01').json()['data']['contado']==1800)
    ok('sin_errores_js',len(errs)==0)
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
