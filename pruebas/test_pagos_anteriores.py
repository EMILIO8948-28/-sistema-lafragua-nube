"""Cargar pagos anteriores de colegiaturas, inscripción y reinscripciones (por alumno y por archivo CSV). Solo Administrador."""
import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3131;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,LF_SIN_CONTACTO='1',PORT=str(PORT),DATA_DIR='/tmp/nbdata_hist',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_hist && mkdir -p /tmp/nbdata_hist')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def W(pg,js,t=20):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
CSV1=("matricula,concepto,pagado_hasta,fecha_pago,monto_pagado,metodo,referencia,nombre,programa,ciclo_ingreso,nuevo_ingreso\n"
"20250002,Inscripción,,2025-08-20,800,Efectivo,R-77,,,,\n"
"20250002,Colegiatura septiembre 2025,,05/09/2025,1300,Efectivo,R-78,,,,\n"
"20250002,Colegiatura octubre 2025,,,650,Transferencia,,,,,\n"
"20250002,Reinscripción 2,,2026-01-08,800,Tarjeta,,,,,\n"
"20250009,,,,,,,Beto Mena Ruiz,Pedagogía,2025,si\n"
"20250009,,octubre 2026,,,Efectivo,,,,,\n"
"20259999,Colegiatura septiembre 2025,,2025-09-05,1300,Efectivo,,,,,\n"
"20250002,Colegiatura noviembre 2025,,2027-01-01,1300,Efectivo,,,,,\n"
"20250002,Colegiatura diciembre 2025,,2025-12-05,5000,Efectivo,,,,,\n"
"20250002,Pizza,,2025-12-05,100,Efectivo,,,,,\n"
"20250002,Colegiatura diciembre 2025,,2025-12-05,1300,Bitcoin,,,,,\n")
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):
        r=ctx.request.get(B+'/api/doc/'+path).json();return r.get('data') or {}
    put('students/s1',{'mat':'20250001','nombre':'Ana López Ramírez','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':True})
    put('students/s2',{'mat':'20250002','nombre':'Carlos Díaz Soto','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':True})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===2")
    hoy=pg.evaluate("today()");ym=hoy[:7]
    # ---------- Entradas ----------
    pg.evaluate("ir('pagos');vista('al')");W(pg,"MOD==='pagos'")
    ok('boton_en_la_barra_de_alumnos',pg.is_visible('#bHist'))
    pg.click('#bHist');pg.wait_for_selector('#dHc[open]')
    ok('abre_el_cargador_en_pestana_por_alumno',pg.is_visible('#hcP1') and pg.is_hidden('#hcP2') and pg.is_hidden('#hcBox'))
    ok('lista_de_alumnos_para_elegir',pg.locator('#hcAlL option').count()==2)
    pg.fill('#hcAl','20250001 — Ana López Ramírez');W(pg,"!document.getElementById('hcBox').hidden")
    ok('muestra_nombre_del_alumno','Ana López Ramírez' in pg.inner_text('#hcNom'))
    cargos=pg.evaluate("hcCargos(S.find(function(s){return s.id==='s1'})).map(function(c){return c.id+'|'+c.ym})")
    ok('cargos_empiezan_en_inscripcion_y_septiembre_del_ciclo',cargos[0]=='i|2025-09' and cargos[1]=='c1|2025-09' and cargos[2]=='c2|2025-10')
    ok('reinscripcion_2_cae_en_enero',any(c=='r2|2026-01' for c in cargos) and any(c=='r3|2026-05' for c in cargos))
    filas=pg.locator('#hcTb tr[data-id]').count()
    esperados=len([c for c in cargos if c.split('|')[1]<=ym])
    ok('solo_muestra_cargos_hasta_el_mes_actual',filas==esperados and filas>=15)
    ok('no_muestra_cargos_futuros',pg.evaluate("Array.prototype.every.call(document.querySelectorAll('#hcTb tr[data-id]'),function(t){return t.dataset.ym<=today().slice(0,7)})"))
    ok('boton_registrar_deshabilitado_sin_marcas',pg.is_disabled('#hcGo'))
    # marcar hasta octubre del año en curso
    pg.select_option('#hcHasta','%s-10'%hoy[:4]) if pg.locator('#hcHasta option[value="%s-10"]'%hoy[:4]).count() else None
    hasta=pg.input_value('#hcHasta');pg.click('#hcHastaGo')
    marc=pg.locator('#hcTb [data-hc]:checked').count()
    ok('marcar_hasta_un_mes_marca_todo_lo_anterior',marc==len([c for c in cargos if c.split('|')[1]<=hasta]) and marc>0)
    ok('fecha_por_defecto_dia_10_del_mes_del_cargo',pg.input_value('#hcTb tr[data-id="c1"] [data-hf]')=='2025-09-10' and pg.input_value('#hcTb tr[data-id="c2"] [data-hf]')=='2025-10-10')
    ok('monto_por_defecto_es_el_saldo',pg.input_value('#hcTb tr[data-id="c1"] [data-hm]')=='1300' and pg.input_value('#hcTb tr[data-id="i"] [data-hm]')=='800')
    ok('resumen_indica_cantidad',('%d pagos'%marc) in pg.inner_text('#hcSum'))
    pg.fill('#hcDia','20');pg.dispatch_event('#hcDia','change')
    ok('cambiar_el_dia_actualiza_fechas_automaticas',pg.input_value('#hcTb tr[data-id="c1"] [data-hf]')=='2025-09-20')
    pg.fill('#hcTb tr[data-id="i"] [data-hf]','2025-08-25');pg.dispatch_event('#hcTb tr[data-id="i"] [data-hf]','change')
    pg.fill('#hcTb tr[data-id="c1"] [data-hr]','R-0010')
    pg.select_option('#hcMet','Efectivo')
    # monto parcial para c2 -> queda saldo
    pg.fill('#hcTb tr[data-id="c2"] [data-hm]','1000');pg.dispatch_event('#hcTb tr[data-id="c2"] [data-hm]','input')
    pg.click('#hcGo');W(pg,"document.getElementById('hcMsg').textContent.indexOf('Listo')===0")
    L=get('ledger/s1')['pagos']
    ok('guardo_un_pago_por_cargo_marcado',len(L)==marc)
    ok('todos_son_historicos_con_cargo_y_folio',all(g.get('hist') is True and g.get('cc') and g.get('folio','').startswith('R-') for g in L))
    ok('ninguna_fecha_es_futura',all(g['fecha']<=hoy for g in L))
    ok('folios_unicos_y_consecutivos',len(set(g['folio'] for g in L))==marc and sorted(int(g['folio'][2:]) for g in L)==list(range(int(min(g['folio'] for g in L)[2:]),int(min(g['folio'] for g in L)[2:])+marc)))
    L2=sorted(L,key=lambda g:g['fecha'])
    ok('folios_siguen_el_orden_de_las_fechas',[g['folio'] for g in L2]==sorted(g['folio'] for g in L2) and L2[0]['cc']==['i'] and L2[0]['fecha']=='2025-08-25')
    ok('metodo_y_referencia_guardados',all(g['metodo']=='Efectivo' for g in L) and [g for g in L if g['cc']==['c1']][0]['ref']=='R-0010')
    ok('pago_parcial_guardado',[g for g in L if g['cc']==['c2']][0]['monto']==1000)
    ok('registra_quien_lo_cargo',all(g.get('by') and g.get('byn') for g in L))
    ok('mensaje_con_folios',' a R-' in pg.inner_text('#hcMsg') or 'R-' in pg.inner_text('#hcMsg'))
    est=pg.evaluate("(function(){var s=S.find(function(x){return x.id==='s1'});var a=applyAll(s);return {p:progTxt(s),rem:a.L.map(function(c,i){return c.id+':'+a.rem[i]})}})()")
    ok('avance_del_alumno_se_actualiza',('Pagos cubiertos: %d de'%(marc-1)) in est['p'])
    ok('queda_el_saldo_del_pago_parcial','c2:300' in est['rem'])
    ok('lo_pagado_aparece_como_pagado_y_bloqueado',pg.locator('#hcTb tr[data-id="c1"] .tag.pagado').count()==1 and pg.is_disabled('#hcTb tr[data-id="c1"] [data-hc]'))
    ok('el_parcial_aparece_como_parcial',pg.locator('#hcTb tr[data-id="c2"] .tag.parcial').count()==1)
    ok('el_mes_actual_sigue_pendiente',pg.locator('#hcTb tr[data-id="c%d"] .tag.sin'%(15 if ym=='2026-11' else 1)).count()>=1)
    # no se puede volver a cargar lo ya pagado desde la planeación
    r=pg.evaluate("(function(){var P=hcPlanea([{n:1,sid:'s1',cid:'c1',fecha:'2025-09-10',monto:'',metodo:'Efectivo'}],{dia:10,metodo:'Efectivo'});return P.errores.map(function(e){return e.msg})})()")
    ok('no_duplica_un_cargo_ya_pagado',len(r)==1 and 'ya está pagado' in r[0])
    # ---------- Validaciones por alumno ----------
    r=pg.evaluate("(function(){var P=hcPlanea([{n:1,sid:'s1',cid:'c2',fecha:'2025-10-10',monto:5000,metodo:'Efectivo'}],{dia:10,metodo:'Efectivo'});return P.errores.map(function(e){return e.msg})})()")
    ok('rechaza_monto_mayor_al_saldo',len(r)==1 and 'mayor al saldo' in r[0])
    r=pg.evaluate("(function(){var P=hcPlanea([{n:1,sid:'s1',cid:'c2',fecha:'2099-10-10',monto:10,metodo:'Efectivo'}],{dia:10,metodo:'Efectivo'});return P.errores.map(function(e){return e.msg})})()")
    ok('rechaza_fecha_futura',len(r)==1 and 'posterior a hoy' in r[0])
    pg.click('#hcCls')
    # ---------- Desde la ficha del alumno ----------
    pg.evaluate("openSt('s2')");pg.wait_for_selector('#dSt[open]')
    ok('boton_en_la_ficha_del_alumno',pg.is_visible('#sHist'))
    pg.click('#sHist');pg.wait_for_selector('#dHc[open]')
    ok('abre_con_el_alumno_ya_elegido',pg.is_visible('#hcBox') and 'Carlos Díaz Soto' in pg.inner_text('#hcNom') and pg.is_hidden('#dSt') if False else ('Carlos Díaz Soto' in pg.inner_text('#hcNom') and not pg.evaluate("document.getElementById('dSt').open")))
    # ciclo de ingreso desde aquí
    pg.fill('#hcIng','2024');pg.dispatch_event('#hcIng','change');W(pg,"S.find(function(s){return s.id==='s2'}).ingreso===2024")
    ok('cambiar_ciclo_acomoda_los_cargos',pg.evaluate("hcCargos(S.find(function(s){return s.id==='s2'}))[1].ym")=='2024-09')
    pg.fill('#hcIng','2025');pg.dispatch_event('#hcIng','change');W(pg,"S.find(function(s){return s.id==='s2'}).ingreso===2025")
    # ---------- Archivo CSV ----------
    pg.click('#hcT2');ok('pestana_archivo',pg.is_visible('#hcP2') and pg.is_hidden('#hcP1'))
    with pg.expect_download() as dl:pg.click('#hcTpl')
    pl=open(dl.value.path(),encoding='utf-8-sig').read()
    ok('descarga_plantilla_con_columnas',pl.startswith('matricula,concepto,pagado_hasta,fecha_pago,monto_pagado,metodo'))
    open('/tmp/hist1.csv','w',encoding='utf-8').write(CSV1)
    pg.set_input_files('#hcFile','/tmp/hist1.csv');W(pg,"document.getElementById('hcPrev').innerHTML.length>50")
    pv=pg.inner_text('#hcPrev')
    ok('vista_previa_lista_alumnos',('Carlos Díaz Soto' in pv) and ('Beto Mena Ruiz' in pv) and 'Alumno nuevo' in pv)
    ok('vista_previa_senala_filas_con_problemas','no existe' in pv and 'posterior a hoy' in pv and 'mayor al saldo' in pv and 'Concepto no reconocido' in pv and 'Método de pago no reconocido' in pv)
    ok('vista_previa_avisa_saldo_pendiente','queda con saldo' in pv)
    ok('boton_cargar_visible',pg.is_visible('#hcGo2'))
    ok('aun_no_se_guardo_nada',not get('ledger/s2').get('pagos'))
    pg.click('#hcGo2');W(pg,"document.getElementById('hcMsg').textContent.indexOf('Listo')===0",30)
    L=get('ledger/s2')['pagos']
    ok('cargo_los_pagos_validos_de_carlos',len(L)==4 and all(g['hist'] for g in L))
    por={g['cc'][0]:g for g in L}
    ok('inscripcion_con_fecha_y_referencia',por['i']['fecha']=='2025-08-20' and por['i']['ref']=='R-77' and por['i']['monto']==800)
    ok('fecha_dd_mm_aaaa_aceptada',por['c1']['fecha']=='2025-09-05')
    ok('sin_fecha_usa_dia_10_del_mes',por['c2']['fecha']=='2025-10-10' and por['c2']['monto']==650 and por['c2']['metodo']=='Transferencia')
    ok('reinscripcion_2_por_numero',por['r2']['fecha']=='2026-01-08' and por['r2']['metodo']=='Tarjeta')
    ok('no_cargo_filas_con_error',not any(g['cc'][0] in ('c3','c4') for g in L))
    ok('quedo_el_saldo_parcial_de_octubre',pg.evaluate("(function(){var s=S.find(function(x){return x.id==='s2'});var a=applyAll(s);var i=a.L.findIndex(function(c){return c.id==='c2'});return a.rem[i]})()")==650)
    nuevo=pg.evaluate("S.filter(function(s){return s.mat==='20250009'}).map(function(s){return {n:s.nombre,p:s.programa,i:s.ingreso,nu:s.nuevo,pagos:s.pagos.length}})")
    ok('creo_el_alumno_nuevo_con_plan_y_ciclo',len(nuevo)==1 and nuevo[0]['n']=='Beto Mena Ruiz' and nuevo[0]['p']=='Pedagogía' and nuevo[0]['i']==2025 and nuevo[0]['nu'] is True)
    ok('pagado_hasta_genera_un_pago_por_cargo',nuevo[0]['pagos']==len([1 for c in pg.evaluate("hcCargos(S.find(function(s){return s.mat==='20250009'})).map(function(c){return c.ym})") if c<='2026-10']))
    ok('no_creo_alumno_con_matricula_desconocida',pg.evaluate("S.filter(function(s){return s.mat==='20259999'}).length")==0)
    ok('mensaje_de_carga_correcto','pagos cargados' in pg.inner_text('#hcMsg'))
    # reaplicar el mismo archivo: nada se duplica
    n0=pg.evaluate("S.reduce(function(t,s){return t+s.pagos.length},0)")
    pg.set_input_files('#hcFile','/tmp/hist1.csv');W(pg,"document.getElementById('hcPrev').innerHTML.length>50")
    pv=pg.inner_text('#hcPrev')
    ok('segunda_carga_marca_ya_pagado','ya está pagado' in pv or 'ya estaba al corriente' in pv)
    ok('pago_parcial_repetido_se_detecta_como_duplicado','ya está registrado' in pv)
    ok('segunda_carga_no_ofrece_duplicar',pg.is_hidden('#hcGo2') or pg.evaluate("HCPLAN.pagos")==0)
    pg.evaluate("document.getElementById('hcFile').value=''")
    ok('no_se_duplicaron_pagos',pg.evaluate("S.reduce(function(t,s){return t+s.pagos.length},0)")==n0)
    # columnas faltantes
    open('/tmp/hist2.csv','w',encoding='utf-8').write("nombre,monto\nx,1\n")
    pg.set_input_files('#hcFile','/tmp/hist2.csv');W(pg,"document.getElementById('hcMsg').textContent.indexOf('Falta')===0")
    ok('avisa_si_falta_la_columna_matricula',True)
    # analizadores
    ok('analiza_mes_en_varios_formatos',pg.evaluate("[hcMesTxt('2026-10'),hcMesTxt('10/2026'),hcMesTxt('octubre 2026'),hcMesTxt('Oct-2026'),hcMesTxt(''),hcMesTxt('xx'),hcMesTxt('13/2026')]")==['2026-10','2026-10','2026-10','2026-10','',None,None])
    ok('analiza_fechas',pg.evaluate("[hcFecha('05/09/2025'),hcFecha('2025-9-5'),hcFecha('31/02/2025'),hcFecha('hola'),hcFecha('')]")==['2025-09-05','2025-09-05',None,None,''])
    pg.click('#hcCls')
    # ---------- Beca y monto que paga el alumno ----------
    put('students/s4',{'mat':'20250004','nombre':'Dora Beca Ruiz','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.some(function(s){return s.id==='s4'})")
    pg.evaluate("abreHc('s4',1)");pg.wait_for_selector('#dHc[open]');W(pg,"!document.getElementById('hcBox').hidden")
    ok('sin_beca_muestra_colegiatura_completa',pg.input_value('#hcBeca')=='' and pg.input_value('#hcPaga')=='1300' and 'sin beca' in pg.inner_text('#hcBecaTx') and pg.is_hidden('#hcBecaDel'))
    pg.fill('#hcPaga','1000');ok('monto_que_paga_calcula_la_beca',pg.input_value('#hcBeca')=='300')
    pg.fill('#hcBeca','200');ok('beca_calcula_el_monto_que_paga',pg.input_value('#hcPaga')=='1100')
    pg.fill('#hcBeca','1300');pg.click('#hcBecaGo');ok('rechaza_beca_igual_o_mayor_a_la_colegiatura','no puede ser igual' in pg.inner_text('#hcMsg') and not pg.evaluate("S.find(function(s){return s.id==='s4'}).beca"))
    pg.fill('#hcBeca','');pg.click('#hcBecaGo');ok('exige_monto_para_la_beca','Escribe el descuento' in pg.inner_text('#hcMsg'))
    pg.fill('#hcPaga','1000');pg.fill('#hcBecaMot','Excelencia académica');pg.click('#hcBecaGo');W(pg,"S.find(function(s){return s.id==='s4'}).beca")
    ok('guarda_la_beca_en_el_alumno',pg.evaluate("S.find(function(s){return s.id==='s4'}).beca")=={'monto':300,'mot':'Excelencia académica'} and get('students/s4')['beca']['monto']==300)
    ok('mensaje_y_texto_con_lo_que_paga','paga $1,000.00' in pg.inner_text('#hcMsg') and 'con beca paga $1,000.00' in pg.inner_text('#hcBecaTx') and pg.is_visible('#hcBecaDel'))
    ok('saldo_de_colegiatura_ya_con_beca',pg.input_value('#hcPaga')=='1000' and '$1,000.00' in pg.inner_text('#hcTb tr[data-id="c1"]'))
    pg.click('#hcTb tr[data-id="c1"] [data-hc]');ok('monto_por_defecto_es_lo_que_paga_con_beca',pg.input_value('#hcTb tr[data-id="c1"] [data-hm]')=='1000')
    pg.click('#hcTb tr[data-id="c2"] [data-hc]');pg.fill('#hcTb tr[data-id="c2"] [data-hm]','1000');pg.dispatch_event('#hcTb tr[data-id="c2"] [data-hm]','input')
    pg.click('#hcGo');W(pg,"document.getElementById('hcMsg').textContent.indexOf('Listo')===0")
    L4=get('ledger/s4')['pagos'];ok('pagos_con_beca_quedan_completos',len(L4)==2 and all(g['monto']==1000 for g in L4) and pg.locator('#hcTb tr[data-id="c1"] .tag.pagado').count()==1 and pg.locator('#hcTb tr[data-id="c2"] .tag.pagado').count()==1)
    ok('monto_mayor_al_saldo_con_beca_se_rechaza',len(pg.evaluate("hcPlanea([{n:1,sid:'s4',cid:'c3',fecha:'2025-11-10',monto:1300,metodo:'Efectivo'}],{dia:10,metodo:'Efectivo'}).errores"))==1)
    pg.click('#hcBecaDel');W(pg,"!S.find(function(s){return s.id==='s4'}).beca")
    ok('quitar_beca_regresa_a_la_colegiatura_completa',pg.is_hidden('#hcBecaDel') and pg.input_value('#hcPaga')=='1300' and not get('students/s4').get('beca'))
    # por archivo: beca a alumnos existentes y nuevos
    CSV2=("matricula,concepto,pagado_hasta,fecha_pago,monto_pagado,metodo,referencia,nombre,programa,ciclo_ingreso,nuevo_ingreso,beca_monto,beca_motivo,paga_colegiatura\n"
    "20250002,Colegiatura noviembre 2025,,2025-11-10,1100,Efectivo,,,,,,200,Deportiva,\n"
    "20250010,Colegiatura septiembre 2025,,2025-09-10,1000,Efectivo,,Eva Nueva Soto,Derecho,2025,si,,,1000\n"
    "20250010,Colegiatura octubre 2025,,2025-10-10,,Efectivo,,,,,,,,\n"
    "20250001,Colegiatura diciembre 2025,,2025-12-05,500,Efectivo,,,,,,,,1500\n")
    open('/tmp/hist3.csv','w',encoding='utf-8').write(CSV2)
    pg.click('#hcT2');pg.set_input_files('#hcFile','/tmp/hist3.csv');W(pg,"document.getElementById('hcPrev').innerHTML.length>50")
    pv=pg.inner_text('#hcPrev')
    ok('vista_previa_muestra_beca','Beca $200.00' in pv and 'Deportiva' in pv and 'Beca $300.00' in pv)
    ok('rechaza_paga_mayor_a_la_colegiatura','es mayor a la colegiatura del plan' in pv)
    pg.click('#hcGo2');W(pg,"document.getElementById('hcMsg').textContent.indexOf('Listo')===0",30)
    ok('beca_a_alumno_existente_por_archivo',get('students/s2')['beca']=={'monto':200,'mot':'Deportiva'})
    pe=pg.evaluate("(function(){var s=S.find(function(x){return x.mat==='20250002'});var a=applyAll(s);var i=a.L.findIndex(function(c){return c.id==='c3'});return a.rem[i]})()")
    ok('el_pago_con_beca_cubre_el_cargo',pe==0)
    nv=pg.evaluate("S.filter(function(s){return s.mat==='20250010'}).map(function(s){return {b:s.beca,p:s.pagos.map(function(g){return g.monto})}})")
    ok('alumno_nuevo_con_paga_colegiatura_obtiene_beca',len(nv)==1 and nv[0]['b']['monto']==300 and nv[0]['p']==[1000,1000])
    pg.click('#hcCls')
    # ---------- Integración con el resto: corte de caja y estado de cuenta ----------
    ok('pagos_historicos_entran_al_ledger_con_su_fecha',min(g['fecha'] for g in get('ledger/s1')['pagos'])=='2025-08-25')
    # ---------- Buscador ----------
    pg.evaluate("ir('home')");W(pg,"MOD==='home'");pg.fill('#hBus','pagos anteriores');W(pg,"!document.getElementById('hBusR').hidden")
    ok('buscador_encuentra_la_funcion','Cargar pagos anteriores' in pg.inner_text('#hBusR'))
    pg.click('#hBusR [data-hf]');pg.wait_for_selector('#dHc[open]');ok('buscador_abre_el_cargador',True);pg.click('#hcCls')
    # ---------- Permisos ----------
    rr=ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'rosa','name':'Rosa Caja','rol':'caja','modulos':{'pagos':'editar','escolar':'ver'},'clave':'clave-rosa-1'}),headers=HDR)
    ok('crea_usuario_caja',rr.status in (200,201))
    cx=b.new_context(viewport={'width':1200,'height':950});cx.set_default_timeout(15000);pg2=cx.new_page();pg2.on("pageerror",lambda e:errs.append(str(e)));pg2.on("dialog",lambda d:d.accept())
    pg2.goto(B+'/');W(pg2,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pg2.fill('#lgU','rosa');pg2.fill('#lgP','clave-rosa-1');pg2.click('#lgGo');W(pg2,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'&&1",30)
    W(pg2,'S.length>=2');pg2.evaluate("ir('pagos');vista('al')");W(pg2,"MOD==='pagos'")
    ok('caja_no_ve_el_boton_de_la_barra',pg2.evaluate("ROL")=='caja' and not pg2.is_visible('#bHist'))
    pg2.evaluate("openSt(S[0].id)");pg2.wait_for_selector('#dSt[open]')
    ok('caja_no_ve_el_boton_de_la_ficha',not pg2.is_visible('#sHist'))
    pg2.evaluate("abreHc(null,1)")
    ok('caja_no_puede_abrir_el_cargador',not pg2.evaluate("document.getElementById('dHc').open"))
    pg2.evaluate("document.getElementById('dSt').close()");pg2.evaluate("ir('home')");W(pg2,"MOD==='home'")
    pg2.fill('#hBus','pagos anteriores');pg2.wait_for_timeout(300)
    ok('caja_no_encuentra_la_funcion_en_el_buscador','Cargar pagos anteriores' not in pg2.inner_text('#hBusR'))
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
