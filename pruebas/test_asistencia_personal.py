"""Asistencia del personal con reloj checador: carga del archivo (CSV de Hikvision/Dahua y otro con fecha y hora separadas),
reglas para administrativos (falta = 1 día, retardos) y docentes (minutos), justificaciones, nómina, recibos y permisos."""
import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3119;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,LF_SIN_CONTACTO='1',PORT=str(PORT),DATA_DIR='/tmp/nbdata_asis',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_asis && mkdir -p /tmp/nbdata_asis')
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
MOCK="""()=>{window.__txt=[];window.__sav=[];
 function mk(){var t={};return new Proxy(t,{get:function(o,k){
   if(k==='text')return function(s){window.__txt.push(String(Array.isArray(s)?s[0]:s));return this_};
   if(k==='splitTextToSize')return function(s){return [String(s)]};
   if(k==='getTextWidth')return function(){return 10};
   if(k==='output')return function(){return new ArrayBuffer(8)};
   if(k==='internal')return {pageSize:{getWidth:function(){return 215.9},getHeight:function(){return 279}}};
   return function(){return this_}}})}
 var this_=null;function PDF(){this_=mk();return this_}
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
Y=2026;MES='2026-10'
def dias_habiles(a,b):
    import datetime
    return [datetime.date(Y,10,d) for d in range(a,b+1) if datetime.date(Y,10,d).weekday()<5]
# ---- archivo 1 (estilo Hikvision/Dahua, 1 al 15 de octubre): columnas en inglés, fecha y hora juntas ----
esp={1:('08:55','18:05'),2:('09:25','18:00'),5:None,6:('09:30','18:00'),7:('09:11','18:00'),8:('09:10','18:00'),9:None,12:None}
f1=['Person ID,Name,Department,Time,Attendance Status,Check Point']
for d in dias_habiles(1,15):
    m=esp.get(d.day,('08:58','18:01'))
    if m:f1+=['0007,Laura Gómez,Administración,2026-10-%02d %s:07,Check-in,Puerta 1'%(d.day,m[0]),'0007,Laura Gómez,Administración,2026-10-%02d %s:30,Check-out,Puerta 1'%(d.day,m[1])]
    f1+=['8,Pedro Ruiz,Administración,2026-10-%02d 08:50:00,Check-in,Puerta 1'%d.day,'8,Pedro Ruiz,Administración,2026-10-%02d 18:10:00,Check-out,Puerta 1'%d.day]
# sábados 3 y 10 de octubre (docentes)
f1+=['55,Prof. Uno,Docentes,2026-10-03 08:58:00,Check-in,P','55,Prof. Uno,Docentes,2026-10-03 13:02:00,Check-out,P','56,Prof. Dos,Docentes,2026-10-03 09:00:00,Check-in,P']
open('/tmp/asis_1.csv','w',encoding='utf-8').write('\n'.join(f1))
# ---- archivo 2 (16 al 31): columnas en español, fecha dd/mm/aaaa y hora en columnas separadas, con punto y coma ----
f2=['No. de empleado;Nombre;Fecha;Hora']
for d in dias_habiles(16,31):
    f2+=['7;Laura Gómez;%02d/10/2026;08:58'%d.day,'7;Laura Gómez;%02d/10/2026;18:01'%d.day,'8;Pedro Ruiz;%02d/10/2026;08:50'%d.day,'8;Pedro Ruiz;%02d/10/2026;18:10'%d.day]
f2+=['8;Pedro Ruiz;31/10/2026;10:00','55;Prof. Uno;17/10/2026;09:30','55;Prof. Uno;17/10/2026;13:00','55;Prof. Uno;24/10/2026;09:05','55;Prof. Uno;24/10/2026;12:30']
open('/tmp/asis_2.csv','w',encoding='utf-8').write('\n'.join(f2))
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    emp=lambda n,s,per,act=True:{'nombre':n,'puesto':'Administrativo','area':'Dirección','salario':s,'period':per,'metodo':'Transferencia','activo':act}
    put('empleados/e1',emp('Laura Gómez',9000,'mensual'));put('empleados/e2',emp('Pedro Ruiz',6000,'quincenal'));put('empleados/e3',emp('Sin Reloj Nuevo',3000,'mensual'))
    PER='Sep–Dic 2026';asig=lambda i,plan,nom:{'id':i,'cid':i,'plan':plan,'cuat':2,'nom':nom,'per':PER,'ses':5}
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[asig('a1','Derecho','Civil I'),asig('a2','Derecho','Civil II')]})
    put('docentes/d2',{'nombre':'Prof. Dos','esp':'Historia','asig':[asig('a3','Derecho','Historia')]})
    mat=lambda nom,d,ini,fin:{'per':PER,'plan':'Derecho','cuat':2,'nom':nom,'docId':d,'ini':ini,'fin':fin}
    put('materias/m1',mat('Civil I','d1','09:00','11:00'));put('materias/m2',mat('Civil II','d1','11:00','13:00'));put('materias/m3',mat('Historia','d2','09:00','11:00'))
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(EMP).length===3&&Object.keys(DOC).length===2&&Object.keys(MAT).length===3");pg.evaluate(MOCK)
    # ---- sin configuración ni archivos: nada se descuenta ----
    ok('sin_id_ni_archivos_no_descuenta',pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M');return !a.evaluado&&a.desc===0&&a.motivo.indexOf('Sin ID de reloj')===0})()") and pg.evaluate("apDocDet('d1',2026,10).evaluado")==False)
    # ---- configuración desde la pantalla ----
    pg.evaluate("ir('na')");W(pg,"MOD==='na'");pg.click('#naAsis');pg.wait_for_selector('#dAP[open]')
    ok('abre_el_dialogo_con_las_tres_pestanas',pg.is_visible('#apT1') and pg.is_visible('#apT2') and pg.is_visible('#apT3') and pg.locator('#apG option').count()==2)
    pg.click('#apT3');pg.wait_for_selector('#apCfTb tr[data-ll]')
    ok('lista_a_administrativos_y_docentes',pg.locator('#apCfTb tr[data-ll^="emp:"]').count()==3 and pg.locator('#apCfTb tr[data-ll^="doc:"]').count()==2)
    pg.fill('#apHEnt','09:00');pg.fill('#apHSal','18:00')
    for d in [1,2,3,4,5]:pg.check('#apHDias [data-d="%d"]'%d)
    pg.fill('#apCfTb tr[data-ll="emp:e1"] [data-k="id"]','7');pg.fill('#apCfTb tr[data-ll="emp:e2"] [data-k="id"]','8')
    pg.fill('#apCfTb tr[data-ll="doc:d1"] [data-k="id"]','55');pg.fill('#apCfTb tr[data-ll="doc:d2"] [data-k="id"]','56')
    pg.fill('#apInhF','2026-10-12');pg.fill('#apInhN','Día de la Raza');pg.click('#apInhAdd')
    ok('agrega_dia_inhabil_sin_perder_lo_escrito',pg.input_value('#apCfTb tr[data-ll="emp:e1"] [data-k="id"]')=='7' and 'Día de la Raza' in pg.inner_text('#apInhL'))
    pg.fill('#apCfTb tr[data-ll="doc:d2"] [data-k="id"]','7');pg.click('#apCfOk');W(pg,"document.getElementById('apMsg').textContent.indexOf('mismo')>-1||document.getElementById('apMsg').textContent.indexOf('dos personas')>-1")
    ok('no_permite_repetir_un_id_de_reloj',get('asistpers/cfg').get('exists') is False)
    pg.fill('#apCfTb tr[data-ll="doc:d2"] [data-k="id"]','56');pg.click('#apCfOk');W(pg,"APC&&APC.map&&APC.map['doc:d2']==='56'")
    cfg=get('asistpers/cfg')['data']
    ok('guarda_configuracion',cfg['map']=={'emp:e1':'7','emp:e2':'8','doc:d1':'55','doc:d2':'56'} and cfg['tol']==10 and cfg['retFalta']==3 and cfg['horDef']['dias']==[1,2,3,4,5] and cfg['horDef']['ent']=='09:00' and cfg['inh']=={'2026-10-12':'Día de la Raza'} and cfg['hor']=={})
    ok('sin_archivos_cargados_sigue_sin_descontar',pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M');return a.evaluado&&a.dias.length===0&&a.desc===0})()"))
    # ---- carga del archivo 1 ----
    pg.click('#apT2');pg.set_input_files('#apFile','/tmp/asis_1.csv');W(pg,"APIMP&&APIMP.recs&&APIMP.recs.length>0")
    ok('detecta_las_columnas_solas',pg.input_value('#apCI')=='0' and pg.input_value('#apCN')=='1' and pg.input_value('#apCFH')=='3')
    inf=pg.inner_text('#apImpInfo');ok('resumen_de_la_carga','asis_1.csv' in inf and 'checadas de 4 personas' in inf and '01/10/2026 al 15/10/2026' in inf)
    ok('el_id_con_ceros_se_normaliza',pg.evaluate("apNid('0007')")=='7' and pg.evaluate("apNid('7.0')")=='7' and pg.evaluate("APIMP.recs.filter(function(r){return r.id==='7'}).length")>0)
    pg.click('#apImpGo');W(pg,"CHK['2026-10']&&CHK['2026-10'].imp&&CHK['2026-10'].imp.length===1")
    ch=get('checadas/'+MES)['data'];ok('guarda_las_checadas_por_id_del_reloj',ch['regs']['7']['2026-10-02']==['09:25','18:00'] and ch['regs']['8']['2026-10-01']==['08:50','18:10'] and ch['imp'][0]['desde']=='2026-10-01' and ch['imp'][0]['hasta']=='2026-10-15' and ch['imp'][0]['archivo']=='asis_1.csv')
    a=pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M');return {n:a.dias.length,f:a.faltas,r:a.retardos,eq:a.eq,d:a.desc}})()")
    ok('solo_se_evaluan_los_dias_cargados',a['n']==11 and a['f']==2 and a['r']==3 and a['eq']==3 and a['d']==900)
    ok('tolerancia_de_10_minutos',pg.evaluate("apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M').dias.filter(function(x){return x.f==='2026-10-08'})[0].estado")=='ok' and pg.evaluate("apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M').dias.filter(function(x){return x.f==='2026-10-07'})[0].estado")=='retardo')
    ok('dia_inhabil_no_cuenta_como_falta',pg.evaluate("apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M').dias.filter(function(x){return x.f==='2026-10-12'})[0].estado")=='inh')
    # ---- archivo 2 (otro formato) ----
    pg.click('#apT2');pg.set_input_files('#apFile','/tmp/asis_2.csv');W(pg,"APIMP&&APIMP.nombre==='asis_2.csv'&&APIMP.recs&&APIMP.recs.length>0")
    ok('detecta_fecha_y_hora_separadas_con_punto_y_coma',pg.input_value('#apCI')=='0' and pg.input_value('#apCFH')=='-1' and pg.input_value('#apCF')=='2' and pg.input_value('#apCH')=='3' and '16/10/2026 al 31/10/2026' in pg.inner_text('#apImpInfo'))
    pg.click('#apImpGo');W(pg,"CHK['2026-10']&&CHK['2026-10'].imp.length===2");pg.wait_for_timeout(300)
    a=pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M');return {n:a.dias.length,d:a.desc}})()")
    ok('con_el_segundo_archivo_se_evalua_todo_el_mes',a['n']==22 and a['d']==900)
    antes=pg.evaluate("JSON.stringify(CHK['2026-10'].regs)")
    pg.click('#apT2');pg.set_input_files('#apFile','/tmp/asis_1.csv');W(pg,"APIMP&&APIMP.nombre==='asis_1.csv'&&APIMP.recs&&APIMP.recs.length>0");pg.click('#apImpGo');W(pg,"CHK['2026-10'].imp.length===3");pg.wait_for_timeout(300)
    ok('importar_de_nuevo_no_duplica',pg.evaluate("JSON.stringify(CHK['2026-10'].regs)")==antes)
    # ---- formatos de fecha ----
    ok('lee_formatos_comunes',pg.evaluate("apParse('02/11/2026 09:15 a. m.','dmy')")=={'f':'2026-11-02','h':'09:15'} and pg.evaluate("apParse('11/02/2026 3:05 PM','mdy')")=={'f':'2026-11-02','h':'15:05'} and pg.evaluate("apParse(46328.375,'dmy')")=={'f':'2026-11-02','h':'09:00'} and pg.evaluate("apParse('2026-11-02T08:01:55','dmy')")=={'f':'2026-11-02','h':'08:01'} and pg.evaluate("apParse('12:00 AM','dmy')")=={'h':'00:00'})
    # ---- justificar y checada manual desde el detalle ----
    pg.click('#apT1');pg.select_option('#apG','adm');pg.select_option('#apM','10');pg.select_option('#apY','2026');pg.select_option('#apQ','M');pg.wait_for_timeout(300)
    tx=pg.inner_text('#apTb');ok('resumen_administrativos','Laura Gómez' in tx and '$900.00' in tx and 'Sin ID de reloj' in tx and 'Pedro Ruiz' not in tx)
    pg.click('#apTb tr:has-text("Laura") [data-apd]');pg.wait_for_selector('#apDetTb tr')
    ok('detalle_dia_por_dia','2026-10-05'.split('-')[2] in pg.inner_text('#apDetTb') and 'Falta' in pg.inner_text('#apDetTb') and 'Retardo (25 min)' in pg.inner_text('#apDetTb') and 'Día inhábil' in pg.inner_text('#apDetTb'))
    pg.click('#apDetTb tr:has-text("09/10/2026") [data-apf]');pg.wait_for_selector('#apForm:not([hidden])');pg.select_option('#apFT','Incapacidad');pg.fill('#apFN','IMSS');pg.click('#apFJ');W(pg,"apJust('emp:e1','2026-10-09')")
    ok('justificar_un_dia_quita_la_falta',get('checadas/'+MES)['data']['just']['emp:e1|2026-10-09']['tipo']=='Incapacidad' and pg.evaluate("apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M').desc")==600)
    pg.click('#apDetTb tr:has-text("05/10/2026") [data-apf]');pg.wait_for_selector('#apForm:not([hidden])');pg.fill('#apFH','09:00');pg.click('#apFM');W(pg,"apMarcas('emp:e1','2026-10-05').length===1")
    ok('checada_manual_corrige_la_falta',pg.evaluate("apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M').desc")==300)
    pg.click('#apDetTb tr:has-text("05/10/2026") [data-apf]');pg.wait_for_selector('#apFX:not([hidden])');pg.click('#apFX');W(pg,"apMarcas('emp:e1','2026-10-05').length===0")
    ok('quitar_checada_manual_regresa_la_falta',pg.evaluate("apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M').desc")==600)
    pg.screenshot(path='/tmp/asis_detalle.png',full_page=True);pg.click('#apBack')
    # ---- nómina administrativa ----
    pg.click('#apCls');pg.select_option('#naY','2026');pg.select_option('#naM','10');pg.select_option('#naPer','M');pg.wait_for_timeout(300)
    F=pg.evaluate("naFilas(2026,10,'M').map(function(f){return {k:f.key,s:f.sueldo,da:f.descAsis,n:f.neto,m:(f.as||{}).motivo||''}})");L={f['k']:f for f in F}
    ok('nomina_descuenta_por_asistencia',L['e1|M']['da']==600 and L['e1|M']['n']==8400 and L['e3|M']['da']==0 and L['e3|M']['m'].startswith('Sin ID de reloj'))
    tbl=pg.inner_text('#naTb');ok('la_tabla_muestra_el_descuento','Desc. por asistencia' in pg.inner_text('#naP1') and '$600.00' in tbl and '1 falta(s) · 3 retardo(s)' in tbl and '$8,400.00' in tbl)
    q=pg.evaluate("naFilas(2026,10,'Q1').map(function(f){return {k:f.key,s:f.sueldo,da:f.descAsis,n:f.neto}})");ok('quincenal_sin_incidencias',[x for x in q if x['k']=='e2|Q1']==[{'k':'e2|Q1','s':3000,'da':0,'n':3000}])
    pg.evaluate("abrePagoNa(['e1|M'])");pg.wait_for_selector('#dNa[open]');pg.click('#naPOk');W(pg,"NAD['2026-10']&&NAD['2026-10'].pagos&&NAD['2026-10'].pagos['e1|M']");pg.wait_for_timeout(400)
    pago=get('nomina_admin/'+MES)['data']['pagos']['e1|M']
    ok('el_pago_guarda_el_descuento_y_la_nota',pago['desc']==600 and pago['descAsis']==600 and pago['neto']==8400 and 'Asistencia: 1 falta y 3 retardos (descuento de 2 días)' in pago['nota'])
    pg.evaluate("window.__txt=[]");pg.evaluate("reciboNaPDF('e1|M','2026-10')");pg.wait_for_timeout(200);tx=' | '.join(pg.evaluate("window.__txt"))
    ok('el_recibo_separa_el_descuento_por_asistencia','Descuento por asistencia (faltas y retardos)' in tx and '- $600.00' in tx and '$8,400.00' in tx)
    # lo pagado ya no cambia aunque cambie la configuración
    cf=get('asistpers/cfg')['data'];cf['map'].pop('emp:e1');put('asistpers/cfg',cf);W(pg,"!APC.map['emp:e1']");pg.wait_for_timeout(300)
    r=pg.evaluate("naFilas(2026,10,'M').filter(function(f){return f.key==='e1|M'})[0]");ok('lo_pagado_no_cambia_al_cambiar_la_configuracion',r['neto']==8400 and r['descAsis']==600 and r['pago'] is not None)
    cf['map']['emp:e1']='7';put('asistpers/cfg',cf);W(pg,"APC.map['emp:e1']==='7'")
    # ---- docentes ----
    pg.evaluate("ir('nom')");W(pg,"MOD==='nom'");pg.select_option('#nmY','2026');pg.select_option('#nmM','10');pg.wait_for_timeout(300)
    # sábado 3: puntual; 10: sin checadas (falta); 17: llega 09:30; 24: sale 12:30; 31: justificado
    pg.evaluate("apGuardaMes('2026-10',function(d){d.just['doc:d1|2026-10-31']={tipo:'Permiso',nota:'Trámite'}})");W(pg,"apJust('doc:d1','2026-10-31')")
    # el sábado 10 también debe estar cargado desde el reloj (archivo 1 llegó hasta el 15)
    d=pg.evaluate("(function(){var a=apDocDet('d1',2026,10);return {n:a.dias.length,f:a.faltas,i:a.incid||a.incidencias,min:a.min,e:a.dias.map(function(x){return x.f.slice(8)+':'+x.estado+':'+x.min})}})()")
    ok('docente_reglas_por_sabado',d['n']==5 and d['f']==1 and d['i']==2 and d['min']==300 and d['e']==['03:ok:0','10:falta:240','17:desc:30','24:desc:30','31:just:0'])
    tar=pg.evaluate("tarifaDe('d1','Derecho')")
    rows=pg.evaluate("filasNom('d1',2026,10).map(function(f){return {n:f.nom,h:f.horas,d:f.hDesc,i:f.importe,t:f.tarifa}})");rows.sort(key=lambda x:x['n'])
    ok('descuento_por_clase_en_horas',[(r['n'],r['h'],r['d']) for r in rows]==[('Civil I',10,2.5),('Civil II',10,2.5)] and all(abs(r['i']-(10-2.5)*tar)<0.01 for r in rows))
    rs=pg.evaluate("(function(){var r=resumenNom('d1',2026,10);return {t:r.total,h:r.horas,d:r.hDesc}})()");ok('resumen_con_horas_descontadas',abs(rs['t']-15*tar)<0.01 and rs['h']==20 and rs['d']==5)
    d2=pg.evaluate("apDocDet('d2',2026,10).dias.map(function(x){return x.f.slice(8)+':'+x.estado})");ok('una_sola_checada_queda_incompleta_sin_descuento',d2[0]=='03:incompleta' and pg.evaluate("filasNom('d2',2026,10)[0].hDesc")==2*4)
    pg.evaluate("openNm('d1')");pg.wait_for_selector('#dNm[open]')
    ok('detalle_docente_muestra_horas_descontadas','Desc. por asistencia (h)' in pg.inner_text('#nmFilas') and '− 2.5' in pg.inner_text('#nmFilas') and 'Descontadas por asistencia: 5 h' in pg.inner_text('#nmTot'))
    pg.click('#nmPagar');W(pg,"NOM['2026-10']&&NOM['2026-10'].pagos&&NOM['2026-10'].pagos.d1");pg.wait_for_timeout(300)
    pago=get('nomina/'+MES)['data']['pagos']['d1']
    ok('pago_docente_congela_horas_descontadas',abs(pago['monto']-15*tar)<0.01 and sorted(f['hDesc'] for f in pago['filas'])==[2.5,2.5])
    tx=' | '.join(pg.evaluate("window.__txt"));ok('recibo_docente_trae_el_descuento','Desc. asist.' in tx and '-2.5 h' in tx and 'Horas descontadas por asistencia' in tx)
    cf=get('asistpers/cfg')['data'];MP=cf['map'].pop('doc:d1');put('asistpers/cfg',cf);W(pg,"!APC.map['doc:d1']");pg.wait_for_timeout(300)
    ok('docente_pagado_no_cambia',abs(pg.evaluate("resumenNom('d1',2026,10).total")-15*tar)<0.01)
    pg.evaluate("$('dNm').close()")
    pg.evaluate("abreAP('doc')");pg.wait_for_selector('#dAP[open]');pg.select_option('#apM','10');pg.select_option('#apY','2026');pg.wait_for_timeout(300)
    tx=pg.inner_text('#apTb');ok('resumen_docentes','Prof. Dos' in tx and 'Prof. Uno' in tx and 'Sin ID de reloj' in tx)
    pg.screenshot(path='/tmp/asis_docentes.png',full_page=True)
    pg.evaluate("$('dAP').close()")
    # ---- sábados sin clase: eventos del calendario tipo «inh» ----
    ok('sin_eventos_cuentan_todos_los_sabados',pg.evaluate("sabadosMes(2026,10)")==5 and pg.evaluate("sabadosPeriodo('Sep–Dic 2026')")==17)
    put('agenda/e1',{'id':'e1','titulo':'Puente','fecha':'2026-10-10','cat':'inh'});put('agenda/e3',{'id':'e3','titulo':'Junta','fecha':'2026-10-17','cat':'reu'});W(pg,"AGN&&AGN.e1&&AGN.e3")
    ok('sabado_sin_clase_resta_del_mes',pg.evaluate("sabadosMes(2026,10)")==4)
    ok('un_evento_que_no_es_inhabil_no_resta',pg.evaluate("scSet()['2026-10-17']")is None)
    put('agenda/e2',{'id':'e2','titulo':'Vacaciones de diciembre','fecha':'2026-12-19','fin':'2027-01-04','cat':'inh'});W(pg,"AGN.e2")
    ok('rango_de_vacaciones_resta_los_sabados_del_rango',pg.evaluate("sabadosPeriodo('Sep–Dic 2026')")==17-1-2 and pg.evaluate("sabadosMes(2026,12)")==2)
    ok('las_sesiones_de_la_nomina_no_cuentan_sabados_sin_clase',pg.evaluate("filasNom('d1',2026,12).length>0&&filasNom('d1',2026,12).every(function(f){return f.ses===2})") and pg.evaluate("filasNom('d1',2026,11).every(function(f){return f.ses===4})"))
    ok('mes_ya_pagado_conserva_sus_sesiones',pg.evaluate("filasNom('d1',2026,10).every(function(f){return f.ses===5})"))
    cf=get('asistpers/cfg')['data'];cf['map']['doc:d1']=MP;put('asistpers/cfg',cf);W(pg,"APC.map['doc:d1']");pg.wait_for_timeout(300)
    d=pg.evaluate("(function(){var a=apDocDet('d1',2026,10);return {f:a.faltas,e:a.dias.map(function(x){return x.f.slice(8)+':'+x.estado})}})()")
    ok('docente_no_tiene_falta_en_sabado_sin_clase',d['f']==0 and '10:inh' in d['e'] and '03:ok' in d['e'])
    ok('sabado_sin_clase_conserva_el_motivo',pg.evaluate("apDocDet('d1',2026,10).dias.filter(function(x){return x.f==='2026-10-10'})[0].nota")=='Puente')
    ok('el_calendario_muestra_el_texto_nuevo','sábado sin clase' in pg.evaluate("CALCATS.map(function(c){return c[1]}).join('|')"))
    # ---- permisos en el servidor ----
    def usr(u,mod):
        ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':u,'name':u,'rol':'personalizado','modulos':mod,'clave':'clave-%s-123'%u}),headers=HDR)
        cx=b.new_context();cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':'clave-%s-123'%u}),headers=HDR);return cx
    NM=usr('nm1',{'nomina_doc':'editar'});NA=usr('na1',{'nomina_adm':'editar'});NV=usr('nv1',{'nomina_adm':'ver'});ES=usr('esc2',{'escolar':'editar'})
    rd=lambda cx,c:cx.request.get(B+'/api/col/'+c).status;wr=lambda cx,path:cx.request.put(B+'/api/doc/'+path,data=json.dumps({'x':1}),headers=HDR).status
    nd=lambda cx,c:len(cx.request.get(B+'/api/col/'+c).json().get('docs',[]))
    dg=lambda cx,c:cx.request.get(B+'/api/doc/'+c).json().get('exists')
    ok('lectura_solo_para_nomina',nd(NM,'checadas')>0 and nd(NA,'checadas')>0 and nd(NV,'checadas')>0 and nd(NA,'asistpers')>0 and nd(ES,'checadas')==0 and nd(ES,'asistpers')==0 and dg(ES,'checadas/2026-10') is False and dg(ES,'asistpers/cfg') is False and dg(NA,'checadas/2026-10') is True and dg(NA,'asistpers/cfg') is True)
    ok('escritura_solo_con_nomina_en_editar',wr(NM,'checadas/2026-09')==200 and wr(NA,'asistpers/cfg2')==200 and wr(NV,'checadas/2026-08')==403 and wr(ES,'checadas/2026-07')==403)
    ok('sin_errores_js',len(errs)==0)
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
if errs:print(errs[:3])
