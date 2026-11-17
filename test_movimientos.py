import subprocess,time,json,os,urllib.request,urllib.error,http.cookiejar,datetime,sqlite3
from playwright.sync_api import sync_playwright
HDR={'Content-Type':'application/json','x-lafragua':'1'}
HOY=datetime.date.today();PER='Sep–Dic 2026'
R={};errs=[]
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
os.system('rm -rf /tmp/nbdata115 && mkdir -p /tmp/nbdata115')
env=dict(os.environ,PORT='3420',DATA_DIR='/tmp/nbdata115',LF_SETUP_TOKEN='tk-mv',LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000',LF_BAJAS_ARRANQUE_MS='600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
B='http://127.0.0.1:3420'
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
def sesion(u=None,c=None):
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def llama(m,url,body=None):
        rq=urllib.request.Request(B+url,method=m,data=(json.dumps(body).encode() if body is not None else None),headers=HDR)
        try:
            r=op.open(rq);d=r.read();return r.status,(json.loads(d) if d else {})
        except urllib.error.HTTPError as e:
            d=e.read()
            try:return e.code,json.loads(d)
            except Exception:return e.code,{}
    if u:
        s,_=llama('POST','/api/login',{'u':u,'clave':c});assert s==200,(u,s)
    return llama
anon=sesion();assert anon('POST','/api/configurar',{'token':'tk-mv','name':'Administrador','u':'admin','clave':'clave-segura-1'})[0]==200
adm=sesion('admin','clave-segura-1');put=lambda path,obj:adm('PUT','/api/doc/'+path,obj)
put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':'Derecho','n':36,'col':1500,'ins':900,'rein':900,'tit':25000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
put('config/cobranza',{'activa':False,'umbral':2,'diaLimite':10,'intervaloDias':7,'graciaDias':7,'reinicioDias':30})
nom={'s1':'Ana Cambia Grupo','s2':'Beto Cambia Plan','s3':'Carla Sin Cambios','s4':'Diego Egresado','s5':'Elena Baja Previa'}
for sid,n in nom.items():put('students/'+sid,{'mat':'2026'+sid[1:].zfill(3),'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
for sid in nom:put('ledger/'+sid,{'pagos':[{'id':'p'+sid,'folio':'R-0000'+sid[1],'fecha':HOY.isoformat(),'monto':3900,'metodo':'Efectivo','cc':['c1','c2','c3']}]})
put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2']});put('grupos/g2',{'num':'4822','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s3']})
put('grupos/g3',{'num':'4830','plan':'Pedagogía','per':'Ene–Abr 2027','cuat':2,'alumnos':[]});put('grupos/g4',{'num':'4901','plan':'Derecho','per':PER,'cuat':1,'alumnos':[]})
put('grupos/g5',{'num':'4700','plan':'Pedagogía','per':'Sep–Dic 2025','cuat':1,'alumnos':['s2']});put('ciclos/sep-dic-2025',{'per':'Sep–Dic 2025','cerrado':True,'fecha':'2025-12-20'})
put('egresados/s4',{'fecha':HOY.isoformat(),'plan':'Pedagogía'})
adm('POST','/api/usuarios',{'u':'esc2','name':'Control Escolar','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'})
adm('POST','/api/usuarios',{'u':'cons','name':'Consulta','rol':'personalizado','modulos':{'escolar':'ver'},'clave':'clave-cons-123'})
adm('POST','/api/usuarios',{'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'})
esc=sesion('esc2','clave-esc2-123');cons=sesion('cons','clave-cons-123');caja=sesion('caja1','clave-caja1-123')
mover=lambda cx,**k:cx('POST','/api/alumnos/mover',k)
grp=lambda gid:adm('GET','/api/doc/grupos/'+gid)[1]['data']['alumnos']
stu=lambda sid:adm('GET','/api/doc/students/'+sid)[1]['data']
# ============ cambiar de grupo ============
ok('quien_no_edita_control_escolar_no_puede_mover',mover(cons,sid='s1',tipo='grupo',grupo='g2',motivo='x y z')[0]==403 and mover(caja,sid='s1',tipo='grupo',grupo='g2',motivo='x y z')[0]==403)
ok('valida_motivo_grupo_y_plan',mover(esc,sid='s1',tipo='grupo',grupo='g2',motivo='')[0]==400 and mover(esc,sid='s1',tipo='grupo',grupo='',motivo='Cambio de turno')[0]==400 and mover(esc,sid='s1',tipo='grupo',grupo='g1',motivo='Cambio de turno')[0]==400 and mover(esc,sid='s1',tipo='grupo',grupo='nada',motivo='Cambio de turno')[0]==400)
s,j=mover(esc,sid='s1',tipo='grupo',grupo='g4',motivo='Cambio de turno');ok('no_acepta_un_grupo_de_otro_plan_y_lo_explica',s==400 and 'otro plan' in j['error'])
put('grupos/g6',{'num':'4600','plan':'Pedagogía','per':'Sep–Dic 2025','cuat':1,'alumnos':[]});ok('ni_de_un_periodo_ya_cerrado',mover(esc,sid='s1',tipo='grupo',grupo='g6',motivo='Cambio de turno')[0]==400)
ok('un_alumno_con_grupo_cambia_de_grupo',mover(esc,sid='s1',tipo='grupo',grupo='g2',motivo='Cambio de turno: trabaja por las mañanas.')[0]==200)
ok('sale_del_grupo_anterior_y_entra_al_nuevo',grp('g1')==['s2'] and sorted(grp('g2'))==['s1','s3'])
m=stu('s1')['movimientos'][-1];ok('queda_en_su_historial',m['tipo']=='grupo' and m['de']=='4821 · Sep–Dic 2026 · cuat. 1' and m['a']=='4822 · Sep–Dic 2026 · cuat. 1' and m['motivo'].startswith('Cambio de turno') and m['por']=='esc2' and m['porNombre']=='Control Escolar' and m['fecha']==HOY.isoformat())
ok('un_grupo_de_otro_periodo_abierto_se_suma_sin_sacarlo_del_actual',mover(esc,sid='s1',tipo='grupo',grupo='g3',motivo='Adelanta su siguiente cuatrimestre.')[0]==200 and 's1' in grp('g2') and 's1' in grp('g3'))
ok('no_se_puede_dar_de_alta_en_el_mismo_grupo_dos_veces',grp('g3').count('s1')==1)
# ============ cambiar de plan ============
ok('el_plan_exige_uno_valido_y_distinto',mover(esc,sid='s2',tipo='plan',plan='Astrología',motivo='Cambio de carrera')[0]==400 and mover(esc,sid='s2',tipo='plan',plan='Pedagogía',motivo='Cambio de carrera')[0]==400 and mover(esc,sid='s2',tipo='plan',plan='Derecho',motivo='')[0]==400)
ok('el_grupo_debe_ser_del_plan_nuevo',mover(esc,sid='s2',tipo='plan',plan='Derecho',grupo='g2',motivo='Cambio de carrera')[0]==400)
ok('cambia_de_plan_y_entra_al_grupo_del_plan_nuevo',mover(esc,sid='s2',tipo='plan',plan='Derecho',grupo='g4',motivo='Quiere estudiar Derecho; presentó solicitud.')[0]==200)
st=stu('s2');ok('el_alumno_queda_con_el_plan_nuevo',st['programa']=='Derecho' and st['carrera']=='Derecho')
ok('sale_de_los_grupos_abiertos_del_plan_anterior_pero_conserva_la_historia_cerrada',grp('g1')==[] and grp('g4')==['s2'] and grp('g5')==['s2'])
m=st['movimientos'][-1];ok('el_historial_dice_de_donde_a_donde',m['tipo']=='plan' and m['de']=='Pedagogía' and m['a']=='Derecho' and m['grupo']=='4901 · Sep–Dic 2026 · cuat. 1' and m['gruposQuitados']==['4821 · Sep–Dic 2026 · cuat. 1'])
ok('sus_pagos_siguen_ahi',adm('GET','/api/doc/ledger/s2')[1]['data']['pagos'][0]['monto']==3900)
ok('un_cambio_de_plan_sin_grupo_tambien_funciona',mover(esc,sid='s3',tipo='plan',plan='Derecho',motivo='Equivalencia de materias.')[0]==200 and stu('s3')['programa']=='Derecho' and 's3' not in grp('g2'))
# ============ protecciones ============
r1=esc('PUT','/api/doc/students/s2',{'mat':'2026002','nombre':'Beto Cambia Plan','carrera':'Derecho','programa':'Derecho','ingreso':2026,'movimientos':[]});r2=esc('PUT','/api/doc/students/s5',{'mat':'2026005','nombre':'Elena','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'movimientos':[{'tipo':'plan'}]});ok('editar_al_alumno_no_borra_ni_falsea_el_historial',r1[0] in (200,403) and len(stu('s2')['movimientos'])==1 and r2[0]==200 and 'movimientos' not in stu('s5'))
ok('un_egresado_no_se_mueve',mover(esc,sid='s4',tipo='grupo',grupo='g2',motivo='Cambio de turno')[0]==400 and mover(esc,sid='s4',tipo='plan',plan='Derecho',motivo='Cambio de carrera')[0]==400)
# ============ baja con todos sus detalles ============
M=esc('GET','/api/bajas/config')[1]['motivos'];ok('hay_motivos_de_baja_mas_completos',all(x in M for x in ['Problemas de salud','Situación económica','Cambio de escuela o institución','Motivos familiares','Fallecimiento','Documentación incompleta','Otro']) and len(M)==14)
baja=lambda **k:esc('POST','/api/bajas/decidir',dict({'sid':'s5','accion':'baja','tipo':'Problemas de salud','motivo':'Presentó incapacidad médica por tres meses.'},**k))
ok('el_detalle_del_motivo_es_obligatorio',baja(motivo='')[0]==400 and baja(motivo='no')[0]==400)
ok('una_baja_temporal_exige_fecha_de_regreso_valida',baja(temporal=True)[0]==400 and baja(temporal=True,regreso=HOY.isoformat())[0]==400 and baja(temporal=True,regreso=(HOY+datetime.timedelta(days=2000)).isoformat())[0]==400)
ok('quien_solicita_debe_ser_valido',baja(solicita='Vecino')[0]==400)
R_=(HOY+datetime.timedelta(days=120)).isoformat()
ok('registra_la_baja_temporal_con_sus_detalles',baja(temporal=True,regreso=R_,solicita='Tutor o familiar',folio='SOL-2026-014',obs='Entregó el comprobante original.')[0]==200)
b=stu('s5')['baja'];ok('guarda_todos_los_datos',b['tipo']=='Problemas de salud' and b['temporal'] is True and b['regreso']==R_ and b['solicita']=='Tutor o familiar' and b['folio']=='SOL-2026-014' and b['obs']=='Entregó el comprobante original.' and 'incapacidad' in b['motivo'])
c5=adm('GET','/api/doc/bajas/s5')[1]['data'];ok('el_historial_del_caso_lo_resume','Baja TEMPORAL' in c5['historial'][-1]['txt'] and 'regreso previsto el '+'/'.join(reversed(R_.split('-'))) in c5['historial'][-1]['txt'] and 'solicitada por: Tutor o familiar' in c5['historial'][-1]['txt'] and 'folio SOL-2026-014' in c5['historial'][-1]['txt'])
av=[v['data'] for v in adm('GET','/api/col/avisos')[1]['docs'] if v['data']['sid']=='s5' and v['data']['titulo']=='Baja de la escuela'];ok('el_aviso_al_alumno_dice_que_es_temporal',len(av)==1 and 'baja temporal' in av[0]['mensaje'] and 'regreso previsto' in av[0]['mensaje'])
ok('baja_definitiva_con_un_motivo_automatico_no_pide_detalle',esc('POST','/api/bajas/decidir',{'sid':'s3','accion':'baja','tipo':'Adeudo de colegiaturas'})[0]==200)
# ============================ PANTALLA ============================
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
with sync_playwright() as pw:
    b=pw.chromium.launch();cx=b.new_context(viewport={'width':1250,'height':1100});cx.set_default_timeout(15000);pg=cx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');W(pg,"typeof sesion==='function'&&document.body.classList.contains('locked')");pg.fill('#lgU','esc2');pg.fill('#lgP','clave-esc2-123');pg.click('#lgGo');W(pg,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pg.wait_for_timeout(1800)
    pg.evaluate("ir('esc');etab('A')");pg.wait_for_selector('#aTb tr');W(pg,"S.length>=5&&Object.keys(GRP).length>=6")
    pg.click('#aTb tr:has-text("Ana Cambia Grupo")');pg.wait_for_selector('#dPf[open]')
    ok('el_expediente_ofrece_los_tres_movimientos',pg.is_visible('#pfGrupo') and pg.is_visible('#pfPlan') and pg.is_visible('#pfBaja'))
    ok('y_muestra_el_historial_de_movimientos_del_alumno','Movimientos del alumno' in pg.inner_text('#pfMov') and 'Cambio de grupo' in pg.inner_text('#pfMov') and '4821 · Sep–Dic 2026 · cuat. 1 → 4822' in pg.inner_text('#pfMov') and 'Cambio de turno' in pg.inner_text('#pfMov'))
    pg.click('#pfGrupo');pg.wait_for_selector('#dMv[open]')
    ok('el_cuadro_de_grupo_muestra_el_actual_y_las_opciones','Ana Cambia Grupo' in pg.inner_text('#mvT') and 'grupo actual' in pg.inner_text('#mvInfo') and pg.is_visible('#mvGr') and pg.is_hidden('#mvPW') and 'Sep–Dic 2025' not in pg.inner_text('#mvGr'))
    ok('solo_ofrece_grupos_de_su_plan_en_periodos_abiertos','4901' not in pg.inner_text('#mvGr') and '4700' not in pg.inner_text('#mvGr') and '4830' in pg.inner_text('#mvGr'))
    pg.click('#mvGo');pg.wait_for_timeout(500);ok('exige_el_motivo','motivo' in pg.inner_text('#mvMsg').lower())
    pg.fill('#mvMot','Prueba de pantalla.');pg.select_option('#mvGr','g1');pg.click('#mvGo');W(pg,"document.getElementById('dMv').open===false");pg.wait_for_timeout(1500)
    pg.wait_for_selector('#dPf[open]');ok('al_confirmar_reabre_el_expediente_con_el_movimiento_nuevo','Prueba de pantalla.' in pg.inner_text('#pfMov'))
    # plan con vista previa del efecto en las cuentas
    pg.click('#pfPlan');pg.wait_for_selector('#dMv[open]');pg.select_option('#mvPl','Derecho');pg.wait_for_timeout(300);prev=pg.inner_text('#mvPrev')
    ok('el_cambio_de_plan_muestra_el_efecto_en_sus_cuentas','Efecto en sus cuentas' in prev and 'cargos del plan' in prev and '→' in prev and 'saldo por pagar' in prev and '$' in prev)
    ok('y_ofrece_los_grupos_del_plan_nuevo','4901' in pg.inner_text('#mvGr2') and 'Sin grupo por ahora' in pg.inner_text('#mvGr2') and pg.is_visible('#mvPW'))
    pg.fill('#mvMot','Cambio de carrera por equivalencias.');pg.select_option('#mvGr2',index=1);pg.click('#mvGo');W(pg,"document.getElementById('dMv').open===false");pg.wait_for_timeout(1500)
    ok('el_alumno_queda_en_el_plan_nuevo_y_en_su_grupo',pg.evaluate("planDe(S.find(function(s){return s.nombre==='Ana Cambia Grupo'}))")=='Derecho' and 'Derecho' in pg.inner_text('#pfBody'))
    ok('el_historial_ya_tiene_los_dos_cambios',pg.inner_text('#pfMov').count('Cambio de')>=3 and 'Cambio de plan' in pg.inner_text('#pfMov') and 'Pedagogía → Derecho' in pg.inner_text('#pfMov'))
    pg.click('#pfCls')
    # baja con detalles desde el expediente
    pg.click('#aTb tr:has-text("Beto Cambia Plan")');pg.wait_for_selector('#dPf[open]');pg.click('#pfBaja');pg.wait_for_selector('#dBj[open]')
    ok('la_baja_ofrece_todos_los_motivos_y_los_nuevos_datos',pg.locator('#bjTipo option').count()==14 and pg.is_visible('#bjSol') and pg.is_visible('#bjFolio') and pg.is_visible('#bjTemp') and pg.is_hidden('#bjReg'))
    pg.check('#bjTemp');ok('al_marcar_temporal_pide_la_fecha_de_regreso',pg.is_visible('#bjReg'))
    pg.select_option('#bjTipo','Situación económica');pg.select_option('#bjSol','Alumno');pg.fill('#bjFolio','SOL-77');pg.fill('#bjReg',(HOY+datetime.timedelta(days=90)).isoformat())
    pg.click('#bjDGo');pg.wait_for_timeout(500);ok('sin_detalle_no_la_guarda','detalle' in pg.inner_text('#bjDMsg').lower())
    pg.fill('#bjBMot','Perdió su empleo; regresa cuando se estabilice.');pg.fill('#bjBObs','Se le dio informes de becas.');pg.click('#bjDGo');W(pg,"document.getElementById('dBj').open===false");pg.wait_for_timeout(800)
    pg.evaluate("ir('esc');etab('B')");pg.select_option('#bjFe','baja');pg.wait_for_timeout(500);t=pg.inner_text('#bjTb')
    ok('la_lista_de_bajas_muestra_los_detalles','Beto Cambia Plan' in t and 'Situación económica' in t and 'Perdió su empleo' in t and 'solicitada por: Alumno' in t and 'folio SOL-77' in t and 'temporal' in t and 'regreso previsto' in t and 'Se le dio informes de becas.' in t)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.click('#aTb tr:has-text("Ana Cambia Grupo")') if False else None
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
