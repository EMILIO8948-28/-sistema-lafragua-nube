import subprocess,time,json,os,urllib.request,re
from playwright.sync_api import sync_playwright
PORT=3197;B='http://127.0.0.1:%d'%PORT;TOK='tok-bd-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_bd',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_bd && mkdir -p /tmp/nbdata_bd')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
import atexit
atexit.register(lambda:(p.terminate(),))
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
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
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    put('students/s1',{'mat':'2026001','nombre':'Ana Beca Tardía','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('students/s2',{'mat':'2026002','nombre':'Beto Con Beca Total','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'beca':{'monto':300,'mot':'Excelencia'}})
    pg.reload();W(pg,"S.length===2&&PL.some(function(p){return p.k==='Pedagogía'&&p.n===36})")
    col=lambda sid,k:pg.evaluate("(function(){var c=cargos(S.find(function(x){return x.id==='%s'})).filter(function(x){return x.k===%d})[0];return c&&c.m})()"%(sid,k))
    # 1) compatibilidad: beca sin «desde» aplica a todas
    ok('beca_sin_desde_aplica_a_todas',col('s2',1)==1000 and col('s2',2)==1000 and col('s2',36)==1000)
    # 2) beca desde la colegiatura 3 (noviembre 2026)
    put('students/s1',{'mat':'2026001','nombre':'Ana Beca Tardía','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'beca':{'monto':300,'mot':'Convenio','desde':3}})
    put('ledger/s1',{'pagos':[{'id':'a','fecha':'2026-09-10','monto':1300,'metodo':'Efectivo','ref':'','cc':['c1']},{'id':'b','fecha':'2026-10-10','monto':1300,'metodo':'Efectivo','ref':'','cc':['c2']}]})
    pg.wait_for_timeout(1500)
    ok('antes_del_mes_de_la_beca_se_cobra_completo',col('s1',1)==1300 and col('s1',2)==1300)
    ok('desde_el_mes_de_la_beca_se_cobra_con_descuento',col('s1',3)==1000 and col('s1',4)==1000 and col('s1',36)==1000)
    ok('pagos_completos_previos_quedan_saldados_sin_saldo_a_favor',pg.evaluate("(function(){var s=S.find(function(x){return x.id==='s1'}),a=applyAll(s),sf=0;Object.keys(a.out).forEach(function(k){a.out[k].forEach(function(p){if(p.c==='Saldo a favor')sf+=p.m})});return sf})()")==0)
    ok('el_siguiente_monto_sugerido_ya_trae_la_beca',pg.evaluate("nextAmt(S.find(function(x){return x.id==='s1'}))")==1000)
    # el formulario de pago pide el monto con beca
    pg.evaluate("openSt('s1')");pg.wait_for_selector('#pMon');pg.wait_for_timeout(400)
    ok('formulario_de_pago_sugiere_1000',pg.input_value('#pMon')=='1000')
    ok('etiqueta_dice_desde_cuando',('Noviembre 2026' in pg.inner_text('#sBecaT')) and 'a partir de' in pg.inner_text('#sBecaT'))
    pg.evaluate("document.getElementById('sBeca').open=true")
    ok('selector_trae_la_colegiatura_3',pg.input_value('#bDes')=='3' and 'ya pagada' in pg.evaluate("document.querySelector('#bDes option[value=\"1\"]').textContent"))
    # 3) asignar beca desde la pantalla: sugiere la primera colegiatura sin pagar
    put('students/s3',{'mat':'2026003','nombre':'Carla Nueva Beca','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('ledger/s3',{'pagos':[{'id':'a','fecha':'2026-09-10','monto':1300,'metodo':'Efectivo','ref':'','cc':['c1']},{'id':'b','fecha':'2026-10-10','monto':1300,'metodo':'Efectivo','ref':'','cc':['c2']},{'id':'c','fecha':'2026-11-10','monto':1300,'metodo':'Efectivo','ref':'','cc':['c3']}]})
    W(pg,"S.length===3");pg.evaluate("openSt('%s')"%pg.evaluate("S.find(function(x){return x.mat==='2026003'}).id"));pg.wait_for_selector('#bDes',state='attached')
    ok('sugiere_la_primera_colegiatura_sin_pagar',pg.input_value('#bDes')=='4')
    pg.evaluate("document.getElementById('sBeca').open=true");pg.fill('#bMon','400');pg.fill('#bMot','Deportiva');pg.click('#bSave')
    W(pg,"(function(){var s=S.find(function(x){return x.mat==='2026003'});return s&&s.beca&&s.beca.desde===4})()")
    srv=ctx.request.get(B+'/api/doc/students/'+pg.evaluate("S.find(function(x){return x.mat==='2026003'}).id")).json()['data']
    ok('guarda_la_beca_con_su_mes_de_inicio',srv['beca']['monto']==400 and srv['beca']['desde']==4)
    ok('colegiaturas_pagadas_siguen_completas_y_las_nuevas_con_beca',col(pg.evaluate("S.find(function(x){return x.mat==='2026003'}).id"),3)==1300 and col(pg.evaluate("S.find(function(x){return x.mat==='2026003'}).id"),4)==900)
    # desde el inicio = sin campo desde
    pg.evaluate("document.getElementById('sBeca').open=true");pg.select_option('#bDes','1');pg.click('#bSave')
    W(pg,"(function(){var s=S.find(function(x){return x.mat==='2026003'});return s&&s.beca&&!s.beca.desde})()")
    ok('desde_el_inicio_no_guarda_campo','desde' not in ctx.request.get(B+'/api/doc/students/'+pg.evaluate("S.find(function(x){return x.mat==='2026003'}).id")).json()['data']['beca'])
    # 4) panel de pagos anteriores: alumno con dos colegiaturas ya pagadas completas
    put('students/s5',{'mat':'2026005','nombre':'Emma Pagos Previos','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('ledger/s5',{'pagos':[{'id':'a','fecha':'2026-09-10','monto':1300,'metodo':'Efectivo','ref':'','cc':['c1']},{'id':'b','fecha':'2026-10-10','monto':1300,'metodo':'Efectivo','ref':'','cc':['c2']}]})
    pg.reload();W(pg,"S.some(function(s){return s.id==='s5'})&&S.length>=4")
    pg.evaluate("abreHc('s5',1)");pg.wait_for_selector('#dHc[open]');W(pg,"!document.getElementById('hcBox').hidden")
    ok('panel_sugiere_la_beca_desde_la_primera_colegiatura_sin_pagar',pg.input_value('#hcBecaDes')=='3' and 'ya pagada' in pg.evaluate("document.querySelector('#hcBecaDes option[value=\"2\"]').textContent"))
    pg.fill('#hcBeca','300');pg.click('#hcBecaGo');W(pg,"S.find(function(s){return s.id==='s5'}).beca")
    sb=ctx.request.get(B+'/api/doc/students/s5').json()['data']['beca']
    ok('panel_guarda_beca_con_mes_de_inicio',sb['monto']==300 and sb['desde']==3 and 'Noviembre 2026' in pg.inner_text('#hcBecaTx') and 'completa' in pg.inner_text('#hcBecaTx'))
    ok('panel_muestra_saldos_completos_antes_y_con_beca_despues',pg.evaluate("hcCargos(S.find(function(s){return s.id==='s5'})).filter(function(c){return c.id==='c3'})[0].rem")==1000)
    pg.select_option('#hcBecaDes','1');pg.click('#hcBecaGo');W(pg,"!S.find(function(s){return s.id==='s5'}).beca.desde")
    ok('panel_desde_el_inicio_no_guarda_campo_desde','desde' not in ctx.request.get(B+'/api/doc/students/s5').json()['data']['beca'])
    pg.click('#hcCls')
    # 5) CSV de pagos anteriores
    r=pg.evaluate("""(function(){
      var csv=[['matricula','concepto','pagado_hasta','fecha_pago','monto_pagado','metodo','referencia','nombre','programa','ciclo_ingreso','nuevo_ingreso','beca_monto','beca_motivo','paga_colegiatura','beca_desde'],
       ['2026009','Colegiatura septiembre 2026','','2026-09-10','1300','Efectivo','','Dora Nueva','Pedagogía','2026','si','300','Beca','','noviembre 2026'],
       ['2026009','Colegiatura noviembre 2026','','2026-11-10','1000','Efectivo','','','','','','','','','']];
      var F=hcFilasCsv(csv);var P=hcPlanea(F.filas,{dia:10,metodo:'Efectivo'});
      var s=P.alumnos['2026009'].s;return {err:P.errores.map(function(e){return e.msg}),desde:s.beca&&s.beca.desde,pagos:P.pagos}})()""")
    ok('csv_alumno_nuevo_acepta_beca_desde_y_pagos_completos_previos',r['err']==[] and r['desde']==3 and r['pagos']==2)
    ok('con_beca_desde_noviembre_pagar_1300_en_noviembre_se_rechaza',len(pg.evaluate("hcPlanea([{n:1,sid:'s1',cid:'c3',fecha:'2026-11-10',monto:1300,metodo:'Efectivo'}],{dia:10,metodo:'Efectivo'}).errores"))==1)
    ok('con_beca_desde_noviembre_pagar_1000_en_noviembre_se_acepta',len(pg.evaluate("hcPlanea([{n:1,sid:'s1',cid:'c3',fecha:'2026-11-10',monto:1000,metodo:'Efectivo'}],{dia:10,metodo:'Efectivo'}).errores"))==0)
    r=pg.evaluate("""(function(){var F=hcFilasCsv([['matricula','concepto','monto_pagado','metodo','nombre','programa','ciclo_ingreso','beca_monto','beca_desde'],['2026010','Colegiatura septiembre 2026','1000','Efectivo','Eli','Pedagogía','2026','300','xyz']]);var P=hcPlanea(F.filas,{dia:10,metodo:'Efectivo'});return P.errores.map(function(e){return e.msg})})()""")
    ok('csv_rechaza_mes_que_no_entiende',len(r)==1 and 'a partir de qué mes' in r[0])
    r=pg.evaluate("""(function(){var F=hcFilasCsv([['matricula','concepto','monto_pagado','metodo','nombre','programa','ciclo_ingreso','beca_monto','beca_desde'],['2026011','Colegiatura septiembre 2026','1300','Efectivo','Fer','Pedagogía','2026','300','50']]);var P=hcPlanea(F.filas,{dia:10,metodo:'Efectivo'});return P.errores.map(function(e){return e.msg})})()""")
    ok('csv_rechaza_colegiatura_inexistente',len(r)==1 and 'no existe' in r[0])
    # alumno existente: cambia la beca y el mes
    r=pg.evaluate("""(function(){var F=hcFilasCsv([['matricula','concepto','monto_pagado','metodo','beca_monto','beca_desde'],['2026002','Colegiatura septiembre 2026','1300','Efectivo','300','noviembre 2026']]);var P=hcPlanea(F.filas,{dia:10,metodo:'Efectivo'});var a=P.alumnos['2026002'];return {err:P.errores.map(function(e){return e.msg}),cb:a.cambiaBeca,pagos:P.pagos}})()""")
    ok('csv_alumno_existente_cambia_solo_el_mes_de_la_beca',r['err']==[] and r['cb'] and r['cb']['desde']==3 and r['cb']['monto']==300 and r['pagos']==1)
    # 6) alta masiva de alumnos
    r=pg.evaluate("""(function(){var o=analizaMasivo([['nombre','programa','ciclo_ingreso','beca_monto','beca_desde'],['Gina Masiva Uno','Pedagogía','2026','300','enero 2027'],['Hugo Masivo Dos','Pedagogía','2026','','']]);return {ok:o.ok.map(function(r){return r.beca}),bad:o.bad}})()""")
    ok('alta_masiva_lee_beca_desde',r['ok'][0]['desde']==5 and r['ok'][1] is None and r['bad']==[])
    r=pg.evaluate("""(function(){var o=analizaMasivo([['nombre','programa','ciclo_ingreso','beca_monto','beca_desde'],['Ines Masiva','Pedagogía','2026','300','nunca']]);return o.bad.map(function(x){return x.motivo})})()""")
    ok('alta_masiva_avisa_si_no_entiende_el_mes',len(r)==1 and 'a partir de qué mes' in r[0])
    ok('la_plantilla_de_alumnos_trae_beca_desde',pg.evaluate("MASCOL.indexOf('beca_desde')>-1")==True and 'beca_desde' in pg.evaluate("HC_PLANTILLA"))
    # 7) el servidor calcula igual (cobranza / pago en línea)
    src=open('/tmp/nb/servidor.js',encoding='utf-8').read()
    f1=re.search(r'const MESES_C = [^\n]*\n',src);f1b=re.search(r'const mesAnioC = [^\n]*\n',src);f2=re.search(r'function cargosAlumnoSrv[\s\S]*?\n}\n',src)
    js=("const cicloMx=()=>2026;"+f1.group(0)+f1b.group(0)+f2.group(0)+
        "const P=[{k:'Pedagogía',n:36,col:1300,ins:800,rein:800,tit:23000}];const f=b=>cargosAlumnoSrv({programa:'Pedagogía',ingreso:2026,nuevo:false,beca:b},P,{costo:0,min:8},{items:[]},{items:[]},'2026-11-24',null).filter(x=>x.k).map(x=>x.m).slice(0,5);"
        "console.log(JSON.stringify([f(null),f({monto:300}),f({monto:300,desde:3})]))")
    out=subprocess.run(['node','-e',js],capture_output=True,text=True).stdout.strip()
    ok('servidor_calcula_la_beca_desde_el_mes',out=='[[1300,1300,1300,1300,1300],[1000,1000,1000,1000,1000],[1300,1300,1000,1000,1000]]')
    ok('sin_errores_de_pagina',not errs)
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v]);print(errs[:3]);print(out)
