import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3199;B='http://127.0.0.1:%d'%PORT;TOK='tok-dr-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_dr',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_dr && mkdir -p /tmp/nbdata_dr')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
import atexit
atexit.register(lambda:p.terminate())
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[];DL=[]
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
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(12000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:(DL.append(d.message),d.accept()))
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(0.8)
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    base=lambda mat,n,**k:dict({'mat':mat,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False},**k)
    put('students/s1',base('2026001','Ana Que Recomienda'))
    put('students/s2',base('2026002','Nuevo Uno',nuevo=True))
    put('students/s3',base('2026003','Nuevo Dos',nuevo=True))
    put('students/s4',base('2026004','Viejo Cuatro'))
    put('students/s5',base('2026005','Otra Que Recomienda'))
    pg.reload();W(pg,"S.length===5&&PL.some(function(p){return p.k==='Pedagogía'&&p.n===36})")
    pg.evaluate("openSt('s1')");pg.wait_for_selector('#pDscBox',state='attached');pg.wait_for_timeout(300)
    opts=pg.evaluate("Array.from(document.querySelectorAll('#pDscL option')).map(function(o){return o.value})")
    ok('lista_solo_alumnos_nuevos_y_no_ella_misma',sorted(opts)==['2026002 — Nuevo Uno','2026003 — Nuevo Dos'])
    ok('el_cargo_se_ve_completo_antes',pg.evaluate("cargos(S.find(function(x){return x.id==='s1'})).filter(function(x){return x.k===1})[0].m")==1300)
    pg.evaluate("document.getElementById('pDscBox').open=true")
    # 1) descuento + pago
    pg.fill('#pDscAl','2026002 — Nuevo Uno');pg.fill('#pDscMon','300');pg.wait_for_timeout(200)
    ok('el_monto_del_pago_se_ajusta_con_el_descuento',pg.input_value('#pMon')=='1000')
    ok('el_texto_explica_a_que_cargo_se_aplica','Colegiatura Septiembre 2026' in pg.inner_text('#pDscTx') and '1,000' in pg.inner_text('#pDscTx'))
    pg.select_option('#pMet','Efectivo');pg.click('#sAdd');W(pg,"S.find(function(x){return x.id==='s1'}).pagos.length===1")
    s1=lambda js:pg.evaluate("(function(){var s=S.find(function(x){return x.id==='s1'});return "+js+"})()")
    ok('el_pago_queda_por_el_monto_cobrado',s1("s.pagos[0].monto")==1000 and s1("s.pagos[0].dsc.m")==300 and s1("s.pagos[0].dsc.rec.nom")=='Nuevo Uno')
    ok('la_colegiatura_queda_pagada_completa',s1("cEst(s).filter(function(c){return c.c==='Colegiatura Septiembre 2026'})[0].m")==1000 and s1("cEst(s).filter(function(c){return c.c==='Colegiatura Septiembre 2026'})[0].p")==1000)
    ok('el_siguiente_pago_sigue_en_1300',s1("nextAmt(s)")==1300)
    rec=ctx.request.get(B+'/api/doc/recargos/s1').json()['data']['items']
    ok('queda_registrado_el_descuento_con_el_alumno_recomendado',len(rec)==1 and rec[0]['tipo']=='desc' and rec[0]['m']==300 and rec[0]['rec']['id']=='s2' and 'Nuevo Uno' in rec[0]['c'] and rec[0]['byn']=='Administrador')
    ok('el_ingreso_en_caja_es_solo_lo_cobrado',ctx.request.get(B+'/api/doc/ledger/s1').json()['data']['pagos'][0]['monto']==1000)
    ok('el_recibo_muestra_el_descuento',pg.evaluate("recRows(S.find(function(x){return x.id==='s1'}),S.find(function(x){return x.id==='s1'}).pagos[0]).some(function(r){return /Descuento por recomendaci/.test(r[1])&&/300/.test(r[1])})"))
    ok('la_lista_de_pagos_lo_menciona','con descuento por recomendación' in pg.inner_text('#sPays'))
    ok('queda_en_recargos_y_descuentos_aplicados',pg.evaluate("RCTAB=3;rcgRender();document.getElementById('rcgTb3').innerText.indexOf('Descuento por recomendación')>-1"))
    # 2) validaciones
    def intenta(al,mon,esperado,nombre):
        n0=len(DL);pg.evaluate("openSt('s1')");pg.wait_for_selector('#pDscBox',state='attached');pg.wait_for_timeout(200)
        pg.evaluate("document.getElementById('pDscBox').open=true");pg.fill('#pDscAl',al);pg.fill('#pDscMon',mon);pg.select_option('#pMet','Efectivo');pg.click('#sAdd');pg.wait_for_timeout(500)
        ok(nombre,len(DL)>n0 and esperado in DL[-1] and s1("s.pagos.length")==1)
    intenta('2026002 — Nuevo Uno','100','Ya se aplicó un descuento por la recomendación de Nuevo Uno','no_permite_usar_dos_veces_al_mismo_alumno_nuevo')
    intenta('','100','Elige de la lista','exige_elegir_al_alumno_recomendado')
    intenta('2026003 — Nuevo Dos','','Escribe el monto','exige_el_monto')
    intenta('2026003 — Nuevo Dos','5000','no puede ser mayor','el_descuento_no_puede_pasar_de_lo_que_falta')
    intenta('2026004 — Viejo Cuatro','100','no es de nuevo ingreso','un_alumno_que_no_es_nuevo_no_se_acepta')
    # otra persona no puede reutilizar al mismo recomendado
    pg.evaluate("openSt('s5')");pg.wait_for_selector('#pDscBox',state='attached');pg.wait_for_timeout(200)
    pg.evaluate("document.getElementById('pDscBox').open=true");pg.fill('#pDscAl','2026002 — Nuevo Uno');pg.fill('#pDscMon','100');n0=len(DL);pg.select_option('#pMet','Efectivo');pg.click('#sAdd');pg.wait_for_timeout(500)
    ok('otro_alumno_tampoco_puede_cobrar_por_el_mismo_recomendado',len(DL)>n0 and 'Ya se aplicó' in DL[-1] and 'Ana Que Recomienda' in DL[-1])
    # 3) segundo recomendado distinto, sobre la siguiente colegiatura, con el concepto elegido
    pg.evaluate("openSt('s1')");pg.wait_for_selector('#pDscBox',state='attached');pg.wait_for_timeout(200)
    pg.evaluate("document.getElementById('pDscBox').open=true");pg.fill('#pDscAl','2026003 — Nuevo Dos');pg.fill('#pDscMon','250');pg.select_option('#pMet','Efectivo');pg.click('#sAdd');W(pg,"S.find(function(x){return x.id==='s1'}).pagos.length===2")
    ok('segundo_descuento_por_otro_alumno_nuevo',s1("s.pagos[1].monto")==1050 and s1("s.pagos[1].dsc.m")==250 and s1("cEst(s).filter(function(c){return c.c==='Colegiatura Octubre 2026'})[0].m")==1050)
    # 4) un pago normal no cambia nada y los campos se limpian
    pg.evaluate("openSt('s1')");pg.wait_for_selector('#pMon');pg.wait_for_timeout(300)
    ok('los_campos_de_descuento_inician_vacios',pg.input_value('#pDscAl')=='' and pg.input_value('#pDscMon')=='' and pg.input_value('#pMon')=='1300')
    pg.select_option('#pMet','Efectivo');pg.click('#sAdd');W(pg,"S.find(function(x){return x.id==='s1'}).pagos.length===3")
    ok('un_pago_sin_descuento_no_lleva_dsc',s1("s.pagos[2].dsc")is None and s1("s.pagos[2].monto")==1300)
    # 5) quien cobra en caja también puede, y se puede cancelar desde Recargos y descuentos
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja Uno','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    cj=b.new_context();cj.request.post(B+'/api/login',data=json.dumps({'u':'caja1','clave':'clave-caja-123'}),headers=HDR);cj.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'clave-caja-123','nueva':'clave-caja-456'}),headers=HDR)
    ok('caja_puede_registrar_el_descuento',cj.request.put(B+'/api/doc/recargos/s4',data=json.dumps({'items':[]}),headers=HDR).status==200)
    pg.evaluate("document.getElementById('dSt').close();abreRc();RCTAB=3;rcgRender()");pg.wait_for_selector('#rcgTb3 .rcgQ');tot0=pg.evaluate("cargos(S.find(function(x){return x.id==='s1'})).slice(0,3).reduce(function(a,c){return a+c.m},0)")
    pg.click('#rcgTb3 .rcgQ >> nth=0');W(pg,"((REC.s1&&REC.s1.items)||[]).length===1")
    ok('al_cancelar_el_descuento_la_cuenta_vuelve_a_su_monto',pg.evaluate("cargos(S.find(function(x){return x.id==='s1'})).slice(0,3).reduce(function(a,c){return a+c.m},0)")-tot0 in (300,250))
    ok('sin_errores_de_pagina',not errs)
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v]);print(errs[:3]);print(DL[-3:])
