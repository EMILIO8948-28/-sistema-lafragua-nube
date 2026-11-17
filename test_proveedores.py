"""Proveedores, cuentas por pagar y gastos fijos del mes."""
import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3145;B='http://127.0.0.1:%d'%PORT;TOK='tok-pv-1'
os.system('rm -rf /tmp/nbdata_pv /tmp/crl5 && mkdir -p /tmp/nbdata_pv /tmp/crl5')
RELOJ='/tmp/crl5/reloj.txt';HOY=datetime.date.today().isoformat();open(RELOJ,'w').write(HOY)
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_pv',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ)
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def W(pg,js,t=30):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def raw(path,obj,m='put',c=None):
        c=c or ctx;return getattr(c.request,m)(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    def get(path,c=None):return (c or ctx).request.get(B+'/api/doc/'+path).json()
    HOYC=pg.evaluate("today()");MES=HOYC[:7];AYER=(datetime.date.fromisoformat(HOYC)-datetime.timedelta(days=1)).isoformat()
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'cons1','name':'Cons','rol':'consulta','clave':'clave-cons-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    pg.evaluate("ir('pagos');vista('ga')");W(pg,"!document.getElementById('vGa').hidden")
    ok('boton_sin_pendientes',pg.inner_text('#bPv')=='Proveedores y cuentas por pagar')
    pg.click('#bPv');pg.wait_for_selector('#dPrv[open]')
    ok('abre_en_por_pagar_vacio',pg.is_visible('#prvP1') and 'No hay cuentas por pagar' in pg.inner_text('#prvR1'))
    # --- proveedores
    pg.click('#prvT2');pg.wait_for_timeout(500);pg.click('#prvGuarda');ok('pide_nombre','nombre' in pg.inner_text('#prvMsg'))
    pg.fill('#prvNom','Papelería Central');pg.fill('#prvRfc','ABC');pg.click('#prvGuarda');ok('rechaza_rfc_corto','RFC' in pg.inner_text('#prvMsg'))
    pg.fill('#prvRfc','pce010101ab1');pg.fill('#prvTel','2221234567');pg.fill('#prvCon','Sra. Lupe');pg.select_option('#prvCat','Papelería y oficina');pg.click('#prvGuarda');W(pg,"document.getElementById('prvMsg').textContent==='Proveedor guardado.'")
    P=get('proveedores/'+pg.evaluate("pvLista()[0].id")+'')['data']
    ok('guarda_proveedor',P['nombre']=='Papelería Central' and P['rfc']=='PCE010101AB1' and P['activo'] is True and P['cat']=='Papelería y oficina')
    pid=pg.evaluate("pvLista()[0].id")
    pg.fill('#prvNom','papeleria central');pg.click('#prvNuevo');pg.fill('#prvNom','papeleria central');pg.click('#prvGuarda');ok('rechaza_nombre_repetido','Ya existe' in pg.inner_text('#prvMsg') and len(pg.evaluate("pvLista()"))==1)
    pg.fill('#prvNom','Luz y Fuerza SA');pg.fill('#prvRfc','');pg.select_option('#prvCat','Servicios (luz, agua, internet)');pg.evaluate("pvMsg('')");pg.click('#prvGuarda');W(pg,"document.getElementById('prvMsg').textContent==='Proveedor guardado.'")
    ok('dos_proveedores',pg.evaluate("pvLista().length")==2 and pg.locator('#prvTb2 tr').count()==2)
    pg.fill('#prvBus','luz');pg.wait_for_timeout(250);ok('busca_proveedor',pg.locator('#prvTb2 tr').count()==1);pg.fill('#prvBus','')
    pg.wait_for_timeout(250)
    pg.click('#prvTb2 [data-pe="%s"]'%pid);ok('edita_carga_datos',pg.input_value('#prvNom')=='Papelería Central' and pg.input_value('#prvTel')=='2221234567' and 'Editar' in pg.inner_text('#prvFt'))
    pg.fill('#prvTel','2229999999');pg.evaluate("pvMsg('')");pg.click('#prvGuarda');W(pg,"document.getElementById('prvMsg').textContent==='Proveedor guardado.'")
    ok('edita_sin_duplicar',get('proveedores/'+pid)['data']['tel']=='2229999999' and pg.evaluate("pvLista().length")==2)
    luz=[x['id'] for x in pg.evaluate("pvLista()") if x['nombre'].startswith('Luz')][0]
    ok('selector_de_gastos_lista_proveedores',pg.locator('#gProv option').count()==3)
    # --- inactivo
    pg.click('#prvTb2 [data-pe="%s"]'%luz);pg.uncheck('#prvAct');pg.evaluate("pvMsg('')");pg.click('#prvGuarda');W(pg,"document.getElementById('prvMsg').textContent==='Proveedor guardado.'")
    ok('inactivo_sale_del_selector',pg.locator('#gProv option').count()==2 and pg.locator('#prvTb2 tr').count()==1)
    pg.check('#prvIna');pg.wait_for_timeout(250);ok('mostrar_inactivos',pg.locator('#prvTb2 tr').count()==2 and 'Inactivo' in pg.inner_text('#prvTb2'))
    pg.click('#prvTb2 [data-pe="%s"]'%luz);pg.check('#prvAct');pg.evaluate("pvMsg('')");pg.click('#prvGuarda');W(pg,"document.getElementById('prvMsg').textContent==='Proveedor guardado.'");pg.uncheck('#prvIna')
    pg.click('#prvCls')
    # --- gasto normal con proveedor
    pg.fill('#gFec',HOYC);pg.fill('#gMon','500');pg.fill('#gCon','Papel y toner');pg.select_option('#gProv',pid);pg.click('#gAdd')
    W(pg,"gastosTodos().length===1")
    g=get('gastos/'+MES)['data']['items'][0]
    ok('gasto_guarda_proveedor',g['prov']==pid and 'pend' not in g and g['monto']==500)
    ok('gasto_cuenta_en_el_corte',pg.evaluate("datosCorte(today()).E.length")==1 and 'Papelería Central' in pg.inner_text('#cGas'))
    # --- cuenta por pagar
    pg.fill('#gFec',AYER);pg.fill('#gMon','1200');pg.fill('#gCon','Renta de noviembre');pg.select_option('#gProv',luz);pg.check('#gPend');pg.fill('#gVen',AYER);pg.click('#gAdd')
    W(pg,"pvPend().length===1")
    ok('pendiente_con_aviso','cuenta por pagar' in pg.inner_text('#gMsg'))
    ok('pendiente_no_cuenta_como_gasto',pg.evaluate("gastosTodos().length")==1 and pg.evaluate("sm(gastosTodos(),'monto')")==500)
    ok('corte_ignora_pendiente',pg.evaluate("datosCorte(today()).E.length")==1 and pg.evaluate("datosCorte('"+AYER+"').E.length")==0)
    ok('badge_con_numero',pg.inner_text('#bPv')=='Proveedores y cuentas por pagar (1)')
    gp=[x for x in get('gastos/'+AYER[:7])['data']['items'] if x.get('pend')][0]
    ok('servidor_guarda_pend_y_vence',gp['pend'] is True and gp['vence']==AYER and gp['prov']==luz)
    pg.click('#bPv');pg.wait_for_selector('#dPrv[open]')
    ok('lista_pendiente_vencida','1 cuentas por pagar por $1,200.00' in pg.inner_text('#prvR1') and '1 vencidas' in pg.inner_text('#prvR1') and 'Vencida' in pg.inner_text('#prvTb1') and 'Luz y Fuerza' in pg.inner_text('#prvTb1'))
    pg.click('#prvT2');ok('proveedor_muestra_por_pagar',pg.evaluate("(function(){var r=[].slice.call(document.querySelectorAll('#prvTb2 tr')).find(function(t){return /Luz/.test(t.innerText)});return /\\$1,200\\.00/.test(r.innerText)})()"))
    pg.click('#prvT1');pg.select_option('[data-pm]','Transferencia');pg.click('[data-pp]');W(pg,"gastosTodos().length===2")
    ok('al_pagar_ya_es_gasto',pg.evaluate("sm(gastosTodos(),'monto')")==1700 and 'Pagada con transferencia' in pg.inner_text('#prvMsg'))
    all_=[x for k in sorted({'gastos/'+MES,'gastos/'+AYER[:7]}) for x in get(k).get('data',{}).get('items',[])]
    pagado=[x for x in all_ if x['concepto']=='Renta de noviembre'][0]
    ok('servidor_pagado',pagado.get('pend') is None and pagado['fecha']==HOYC and pagado['metodo']=='Transferencia' and pagado['fechaFactura']==AYER and pagado['prov']==luz)
    ok('ya_no_hay_pendientes',pg.evaluate("pvPend().length")==0 and pg.inner_text('#bPv')=='Proveedores y cuentas por pagar' and len([x for x in all_ if x['concepto']=='Renta de noviembre'])==1)
    ok('corte_de_hoy_suma_ambos',pg.evaluate("datosCorte(today()).E.length")==2)
    pg.click('#prvT2');pg.wait_for_timeout(200)
    ok('pagado_este_ano_por_proveedor',pg.evaluate("(function(){var r=[].slice.call(document.querySelectorAll('#prvTb2 tr')),f=function(n){return r.find(function(t){return t.innerText.indexOf(n)>-1}).innerText};return /\\$500\\.00/.test(f('Papelería'))&&/\\$1,200\\.00/.test(f('Luz'))})()"))
    # --- gastos fijos
    pg.click('#prvT3');pg.click('#pfMes');ok('sin_fijos_avisa','Primero agrega' in pg.inner_text('#prvMsg'))
    pg.fill('#pfCon','Internet');pg.fill('#pfMon','0');pg.click('#pfAdd');ok('rechaza_monto_cero','mayor a cero' in pg.inner_text('#prvMsg'))
    pg.fill('#pfMon','800');pg.fill('#pfDia','31');pg.click('#pfAdd');ok('rechaza_dia_31','1 a 28' in pg.inner_text('#prvMsg'))
    pg.fill('#pfDia','5');pg.select_option('#pfProv',luz);pg.evaluate("pvMsg('')");pg.click('#pfAdd');W(pg,"document.getElementById('prvMsg').textContent==='Gasto fijo agregado.'")
    ok('guarda_gasto_fijo',get('proveedores/_plantillas')['data']['items'][0]['dia']==5 and pg.locator('#prvTb3 tr').count()==1)
    pg.evaluate("pvMsg('')");pg.click('#pfMes');W(pg,"document.getElementById('prvMsg').textContent.indexOf('registrados como cuentas')>-1")
    pen=pg.evaluate("pvPend()")
    ok('crea_pendiente_del_mes',len(pen)==1 and pen[0]['fecha']==MES+'-05' and pen[0]['vence']==MES+'-05' and pen[0]['monto']==800 and pen[0]['pend'] is True and pen[0]['pl'])
    pg.evaluate("pvMsg('')");pg.click('#pfMes');pg.wait_for_timeout(500);ok('no_duplica','ya estaban registrados' in pg.inner_text('#prvMsg') and pg.evaluate("pvPend().length")==1)
    pg.click('#prvT1');pg.click('[data-pp]');W(pg,"pvPend().length===0")
    pg.click('#prvT3');pg.evaluate("pvMsg('')");pg.click('#pfMes');pg.wait_for_timeout(500)
    ok('pagado_tampoco_se_duplica','ya estaban registrados' in pg.inner_text('#prvMsg') and pg.evaluate("pvPend().length")==0)
    pg.evaluate("pvMsg('')");pg.click('#prvTb3 [data-pfq]');W(pg,"document.getElementById('prvMsg').textContent==='Gasto fijo quitado.'")
    ok('quita_gasto_fijo',get('proveedores/_plantillas')['data']['items']==[])
    # quitar pendiente
    pg.click('#prvCls');pg.fill('#gFec',HOYC);pg.fill('#gMon','90');pg.fill('#gCon','Agua');pg.check('#gPend');pg.click('#gAdd');W(pg,"pvPend().length===1")
    pg.click('#bPv');pg.click('#prvT1');pg.click('[data-pq]');W(pg,"pvPend().length===0")
    ok('quita_pendiente',True)
    with pg.expect_download() as dl:
        pg.click('#prvT2');pg.click('#prvCsv')
    tx=open(dl.value.path(),encoding='utf-8').read()
    ok('csv_por_proveedor','Papelería Central' in tx and 'Luz y Fuerza SA' in tx and 'Pagado' in tx and 'Renta de noviembre' in tx)
    pg.click('#prvCls')
    ok('busqueda_global_encuentra',pg.evaluate("(function(){ir('home');return true})()"))
    W(pg,"MOD==='home'");pg.fill('#hBus','proveedor');pg.wait_for_timeout(300);ok('buscador_lista_proveedores','Proveedores y cuentas por pagar' in pg.inner_text('#hBusR'))
    ok('respaldo_incluye_proveedores',pg.evaluate("BKCOL.indexOf('proveedores')>-1"))
    # --- validación del servidor
    pv=lambda **k:dict({'nombre':'X','rfc':'','activo':True},**k)
    ok('rechaza_sin_nombre',raw('proveedores/n1',pv(nombre='')).status==400)
    ok('rechaza_rfc_malo',raw('proveedores/n1',pv(rfc='123')).status==400)
    ok('rechaza_activo_no_booleano',raw('proveedores/n1',pv(activo='si')).status==400)
    ok('rechaza_nombre_largo',raw('proveedores/n1',pv(nombre='x'*200)).status==400)
    ok('acepta_proveedor_valido',raw('proveedores/n1',pv()).status==200)
    ok('rechaza_plantilla_dia_31',raw('proveedores/_plantillas',{'items':[{'id':'a','concepto':'x','monto':5,'dia':31}]}).status==400)
    ok('rechaza_plantilla_monto_negativo',raw('proveedores/_plantillas',{'items':[{'id':'a','concepto':'x','monto':-5,'dia':3}]}).status==400)
    gi=lambda **k:{'items':[dict({'id':'q','fecha':HOYC,'concepto':'x','monto':5},**k)]}
    ok('rechaza_pend_no_booleano',raw('gastos/2030-01',gi(pend='si')).status==400)
    ok('rechaza_vence_mal',raw('gastos/2030-01',gi(vence='mañana')).status==400)
    ok('rechaza_prov_no_texto',raw('gastos/2030-01',gi(prov=5)).status==400)
    ok('acepta_gasto_pendiente_valido',raw('gastos/2030-01',gi(pend=True,vence='2030-01-15',prov='n1')).status==200)
    # --- permisos
    def entra(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,u;return cx
    cj=entra('caja1','clave-caja-123');cn=entra('cons1','clave-cons-123');ec=entra('esc2','clave-esc2-123')
    ok('caja_lee_proveedores',get('proveedores/n1',cj)['exists'])
    ok('caja_escribe_proveedores',raw('proveedores/n2',pv(nombre='Y'),c=cj).status==200)
    ok('caja_marca_pendientes',raw('gastos/2030-02',gi(pend=True),c=cj).status==200)
    ok('consulta_no_escribe_proveedores',raw('proveedores/n3',pv(),c=cn).status==403)
    r_=ec.request.get(B+'/api/doc/proveedores/n1');ok('escolar_no_lee_proveedores',r_.status==403 or (r_.status==200 and not r_.json().get('exists') and not r_.json().get('data')))
    ok('escolar_no_escribe_proveedores',raw('proveedores/n3',pv(),c=ec).status==403)
    pc=cj.new_page();pc.on("pageerror",lambda e:errs.append(str(e)));pc.goto(B+'/');W(pc,"typeof APP!=='undefined'&&APP!==null&&PVD&&Object.keys(PVD).length>0")
    pc.evaluate("ir('pagos');vista('ga')");pc.click('#bPv');pc.wait_for_selector('#dPrv[open]');pc.click('#prvT2')
    ok('caja_puede_usar_el_formulario',not pc.is_disabled('#prvNom') and not pc.is_disabled('#prvGuarda'))
    pn=cn.new_page();pn.on("pageerror",lambda e:errs.append(str(e)));pn.goto(B+'/');W(pn,"typeof APP!=='undefined'&&APP!==null&&ROL==='consulta'")
    ok('consulta_no_ve_el_modulo_de_gastos',pn.evaluate("permiso('corte')")!='editar')
    ok('sin_errores_de_pagina',not errs)
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
