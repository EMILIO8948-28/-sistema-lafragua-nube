"""Panel principal: buscador de alumnos y funciones; y días que se presentan los administrativos (días de la semana y marca día por día)."""
import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3123;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_bus',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_bus && mkdir -p /tmp/nbdata_bus')
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
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    emp=lambda n,s,per:{'nombre':n,'puesto':'Administrativo','area':'Dirección','salario':s,'period':per,'metodo':'Transferencia','activo':True}
    put('empleados/e1',emp('Laura Gómez',9000,'mensual'));put('empleados/e3',emp('Sin Reloj Nuevo',3000,'mensual'))
    put('students/s1',{'mat':'20230101','nombre':'Ana López Martínez','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False})
    put('students/s2',{'mat':'20230777','nombre':'Ángeles Hernández Cruz','carrera':'Ingeniería Industrial','programa':'Ingeniería Industrial','ingreso':2023,'nuevo':False})
    put('students/s3',{'mat':'20230303','nombre':'Carlos Baja Pérez','carrera':'Derecho','programa':'Derecho','ingreso':2023,'nuevo':False})
    for i in range(4,16):put('students/s%d'%i,{'mat':'2024%04d'%i,'nombre':'Alumno Prueba%d Apellido'%i,'carrera':'Derecho','programa':'Derecho','ingreso':2024,'nuevo':False})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===15&&Object.keys(EMP).length===2")
    # ================= BUSCADOR =================
    ok('hay_buscador_en_el_panel',pg.is_visible('#hBus') and pg.evaluate("MOD")=='home')
    pg.fill('#hBus','');ok('vacio_sin_resultados',pg.is_hidden('#hBusR'))
    pg.fill('#hBus','ana lopez');W(pg,"!document.getElementById('hBusR').hidden")
    tx=pg.inner_text('#hBusR')
    ok('encuentra_alumno_sin_acentos_ni_mayusculas','Ana López Martínez' in tx and '20230101' in tx and 'Pedagogía' in tx and 'Alumno Prueba' not in tx)
    ok('alumno_ofrece_pagos_y_ficha',pg.locator('#hBusR [data-ha="s1"][data-hm="pagos"]').count()==1 and pg.locator('#hBusR [data-ha="s1"][data-hm="esc"]').count()==1)
    pg.fill('#hBus','20230777');ok('encuentra_por_matricula','Ángeles' in pg.inner_text('#hBusR') and pg.locator('#hBusR [data-ha]').count()>=2)
    pg.fill('#hBus','angeles');ok('encuentra_con_acento_ignorado','Ángeles Hernández' in pg.inner_text('#hBusR'))
    pg.fill('#hBus','ana');tx=pg.inner_text('#hBusR')
    ok('busca_por_inicio_de_palabra_no_por_pedazos','Ana López' in tx and 'Ángeles' not in tx and 'Campañas' not in tx and 'campañas' not in tx)
    pg.fill('#hBus','Prueba');ok('limita_a_ocho_y_avisa_el_resto','alumnos (12)' in pg.inner_text('#hBusR').lower() and 'y 4 alumnos más' in pg.inner_text('#hBusR') and pg.locator('#hBusR .hb-al').count()==8)
    pg.fill('#hBus','zzzxxx');ok('sin_coincidencias_avisa','Sin resultados' in pg.inner_text('#hBusR'))
    # abrir un alumno desde la búsqueda: Pagos y cuenta
    pg.fill('#hBus','ana lopez');pg.click('#hBusR [data-ha="s1"][data-hm="pagos"]');pg.wait_for_selector('#dSt[open]')
    ok('abre_pagos_del_alumno',pg.evaluate("MOD")=='pagos' and 'Ana López Martínez' in pg.inner_text('#sName'))
    pg.click('#sCls');pg.evaluate("ir('home')");W(pg,"MOD==='home'")
    ok('al_volver_al_panel_el_buscador_esta_limpio',pg.input_value('#hBus')=='' and pg.is_hidden('#hBusR'))
    pg.fill('#hBus','Carlos Baja');pg.click('#hBusR [data-ha="s3"][data-hm="esc"]');pg.wait_for_selector('#dPf[open]')
    ok('abre_ficha_escolar',pg.evaluate("MOD")=='esc' and 'Carlos Baja Pérez' in pg.inner_text('#pfBody'))
    pg.click('#pfCls');pg.evaluate("ir('home')");W(pg,"MOD==='home'")
    # funciones
    def busca(q):pg.fill('#hBus',q);return pg.inner_text('#hBusR')
    t=busca('nomina');ok('encuentra_nominas','Nómina administrativa' in t and 'Nómina docente' in t)
    t=busca('credenciales');ok('encuentra_credenciales','Control escolar · Credenciales' in t)
    t=busca('reloj');ok('encuentra_reloj_checador','Asistencia de administrativos (reloj checador)' in t and 'Cargar archivo del reloj checador' in t)
    t=busca('hikvision');ok('encuentra_por_palabra_clave','Cargar archivo del reloj checador' in t)
    t=busca('respaldo');ok('encuentra_respaldos','Respaldos y seguridad' in t)
    t=busca('cierre de ciclo');ok('encuentra_cierre_de_ciclo','Cierre de ciclo' in t)
    t=busca('dias que se presentan');ok('encuentra_dias_de_administrativos','Días que se presentan los administrativos' in t)
    pg.fill('#hBus','credenciales');pg.click('#hBusR [data-hf]');W(pg,"MOD==='esc'&&ETAB==='R'")
    ok('abre_la_pestana_de_credenciales',pg.is_visible('#eR'))
    pg.evaluate("ir('home')");W(pg,"MOD==='home'")
    pg.fill('#hBus','nomina administrativa');pg.focus('#hBus');pg.keyboard.press('Enter');W(pg,"MOD==='na'")
    ok('enter_abre_el_primer_resultado',pg.evaluate("MOD")=='na')
    pg.evaluate("ir('home')");W(pg,"MOD==='home'")
    pg.fill('#hBus','reloj checador');pg.focus('#hBus');pg.keyboard.press('ArrowDown');ok('flecha_abajo_baja_a_resultados',pg.evaluate("document.activeElement.className.indexOf('hb-i')>-1"))
    pg.keyboard.press('Escape');pg.focus('#hBus');pg.keyboard.press('Escape');ok('escape_limpia',pg.input_value('#hBus')=='' and pg.is_hidden('#hBusR'))
    pg.fill('#hBus','Cargar archivo del reloj');pg.click('#hBusR [data-hf]');pg.wait_for_selector('#dAP[open]')
    ok('abre_la_carga_del_archivo_del_reloj',pg.is_visible('#apP2') and pg.evaluate("APTAB")==2)
    pg.click('#apCls');pg.evaluate("ir('home')");W(pg,"MOD==='home'")
    pg.evaluate("document.activeElement.blur()");pg.keyboard.press('/');ok('diagonal_enfoca_el_buscador',pg.evaluate("document.activeElement.id")=='hBus')
    pg.fill('#hBus','')
    # permisos: solo ve lo que le toca
    pg.evaluate("window.__P=PERMS;PERMS={nomina_adm:'editar'}")
    t=busca('ana');ok('sin_permiso_de_alumnos_no_los_lista','Ana López' not in t and 'alumnos (' not in t.lower())
    t=busca('credenciales');ok('sin_control_escolar_no_ofrece_credenciales','Credenciales' not in t)
    t=busca('nomina');ok('con_nomina_adm_solo_ofrece_la_administrativa','Nómina administrativa' in t and 'Nómina docente' not in t)
    pg.evaluate("PERMS={escolar:'ver'}")
    ok('solo_escolar_ofrece_ficha_y_no_pagos',(busca('ana lopez') or True) and pg.locator('#hBusR [data-ha="s1"][data-hm="esc"]').count()==1 and pg.locator('#hBusR [data-ha][data-hm="pagos"]').count()==0)
    ok('escolar_en_ver_no_ofrece_credenciales_ni_bajas',('Credenciales' not in busca('credenciales')) and ('Bajas' not in busca('bajas')))
    pg.evaluate("PERMS=window.__P");pg.fill('#hBus','')
    # ================= DÍAS DE LOS ADMINISTRATIVOS =================
    pg.evaluate("ir('na')");W(pg,"MOD==='na'");pg.click('#naAsis');pg.wait_for_selector('#dAP[open]')
    pg.select_option('#apY','2026');pg.select_option('#apM','10');pg.select_option('#apQ','M')
    ok('sin_id_ni_dias_no_se_evalua',pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e3'},EMP.e3),2026,10,'M');return !a.evaluado&&a.desc===0&&a.motivo.indexOf('Sin ID de reloj')===0})()"))
    pg.click('#apTb [data-apd="e3"]');pg.wait_for_selector('#apAdmBox:not([hidden])')
    ok('detalle_muestra_dias_de_la_semana_y_calendario_del_periodo',pg.locator('#apWD [data-wd]').count()==7 and pg.locator('#apMTb select').count()==31)
    ok('por_omision_no_tiene_dias_marcados',pg.locator('#apWD [data-wd]:checked').count()==0)
    pg.click('#apMAll');W(pg,"document.getElementById('apMsg').textContent.length>0")
    ok('marcar_todos_pide_primero_los_dias',('Primero marca los días' in pg.inner_text('#apMsg')) and get('checadas/2026-10').get('exists') is False)
    for d in [1,2,3,4,5]:pg.check('#apWD [data-wd="%d"]'%d)
    pg.click('#apWDok');W(pg,"APC&&APC.hor&&APC.hor['emp:e3']")
    cfg=get('asistpers/cfg')['data']
    ok('guarda_los_dias_de_la_semana_del_empleado',cfg['hor']['emp:e3']['dias']==[1,2,3,4,5])
    ok('los_otros_no_cambian',cfg['hor'].get('emp:e1') is None and cfg['horDef']['dias']==[])
    ok('sin_marcas_aun_no_descuenta',pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e3'},EMP.e3),2026,10,'M');return !a.evaluado||(a.dias.length===0&&a.desc===0)})()"))
    pg.click('#apMAll');W(pg,"(CHK['2026-10']&&CHK['2026-10'].dman&&CHK['2026-10'].dman['emp:e3']&&Object.keys(CHK['2026-10'].dman['emp:e3']).length>0)")
    dm=get('checadas/2026-10')['data']['dman']['emp:e3']
    ok('marca_se_presento_en_los_22_dias_habiles',len(dm)==22 and set(dm.values())=={'A'} and '2026-10-01' in dm and '2026-10-03' not in dm)
    ok('sin_excepciones_no_hay_descuento',pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e3'},EMP.e3),2026,10,'M');return a.evaluado&&a.dias.length===22&&a.faltas===0&&a.retardos===0&&a.desc===0})()"))
    pg.select_option('#apMTb select[data-mf="2026-10-06"]','F');W(pg,"CHK['2026-10'].dman['emp:e3']['2026-10-06']==='F'")
    pg.select_option('#apMTb select[data-mf="2026-10-12"]','F');W(pg,"CHK['2026-10'].dman['emp:e3']['2026-10-12']==='F'")
    pg.select_option('#apMTb select[data-mf="2026-10-07"]','R');W(pg,"CHK['2026-10'].dman['emp:e3']['2026-10-07']==='R'")
    pg.select_option('#apMTb select[data-mf="2026-10-08"]','D');W(pg,"CHK['2026-10'].dman['emp:e3']['2026-10-08']==='D'")
    a=pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e3'},EMP.e3),2026,10,'M');return {n:a.dias.length,f:a.faltas,r:a.retardos,eq:a.eq,d:a.desc}})()")
    ok('dos_faltas_un_retardo_y_un_descanso',a=={'n':21,'f':2,'r':1,'eq':2,'d':200})
    ok('la_tabla_muestra_el_estado',('No se presentó' in pg.inner_text('#apDetTb')) and ('Retardo' in pg.inner_text('#apDetTb')))
    pg.select_option('#apMTb select[data-mf="2026-10-13"]','R');W(pg,"CHK['2026-10'].dman['emp:e3']['2026-10-13']==='R'")
    pg.select_option('#apMTb select[data-mf="2026-10-14"]','R');W(pg,"CHK['2026-10'].dman['emp:e3']['2026-10-14']==='R'")
    a=pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e3'},EMP.e3),2026,10,'M');return {f:a.faltas,r:a.retardos,eq:a.eq,d:a.desc}})()")
    ok('tres_retardos_cuentan_como_una_falta',a=={'f':2,'r':3,'eq':3,'d':300})
    pg.select_option('#apMTb select[data-mf="2026-10-14"]','');W(pg,"!CHK['2026-10'].dman['emp:e3']['2026-10-14']")
    ok('quitar_la_marca_la_borra',pg.evaluate("apAdm(Object.assign({id:'e3'},EMP.e3),2026,10,'M').retardos")==2)
    pg.select_option('#apMTb select[data-mf="2026-10-14"]','R');W(pg,"CHK['2026-10'].dman['emp:e3']['2026-10-14']==='R'")
    pg.click('#apBack');W(pg,"!document.getElementById('apResW').hidden")
    fila=pg.inner_text('#apTb tr:has([data-apd="e3"])')
    ok('el_resumen_muestra_el_descuento',('$300.00' in fila or '300' in fila) and 'Sin ID' not in fila)
    nf=pg.evaluate("(function(){var f=naFilas(2026,10,'M').filter(function(x){return x.e.id==='e3'})[0];return {da:f.descAsis,n:f.neto}})()")
    ok('la_nomina_descuenta_los_dias',nf=={'da':300,'n':2700})
    # los días futuros no se pueden marcar
    pg.select_option('#apM','12');pg.click('#apTb [data-apd="e3"]');pg.wait_for_selector('#apMTb select')
    ok('dias_futuros_deshabilitados',pg.locator('#apMTb select:not([disabled])').count()==0)
    pg.click('#apBack');pg.select_option('#apM','10')
    # la marca manual manda sobre el reloj
    put('asistpers/cfg',{**cfg,'map':{'emp:e1':'7'},'horDef':{'dias':[1,2,3,4,5],'ent':'09:00','sal':'18:00'}})
    put('checadas/2026-10',{'mes':'2026-10','regs':{'7':{'2026-10-01':['09:00','18:00'],'2026-10-02':['09:50','18:00']}},'man':{},'just':{},'dman':{'emp:e3':dm,'emp:e1':{'2026-10-06':'A','2026-10-07':'D','2026-10-09':'R'}},'imp':[{'desde':'2026-10-01','hasta':'2026-10-31','archivo':'x.csv','n':4,'fecha':'2026-11-01','por':'t'}]})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&APC&&APC.map&&APC.map['emp:e1']==='7'&&CHK['2026-10']&&CHK['2026-10'].dman")
    a=pg.evaluate("(function(){var a=apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M');var x=function(f){var i=a.dias.filter(function(d){return d.f===f})[0];return i?i.estado:null};return {n:a.dias.length,f:a.faltas,r:a.retardos,e1:x('2026-10-01'),e2:x('2026-10-02'),e6:x('2026-10-06'),e7:x('2026-10-07'),e9:x('2026-10-09')}})()")
    ok('reloj_y_marcas_conviven',a['e1']=='ok' and a['e2']=='retardo' and a['e6']=='ok' and a['e7'] is None and a['e9']=='retardo' and a['n']==21 and a['r']==2 and a['f']==17)
    ok('descuento_de_laura',pg.evaluate("apAdm(Object.assign({id:'e1'},EMP.e1),2026,10,'M').desc")==5100)
    # configuración: los días propios del empleado se conservan al guardar la configuración
    pg.evaluate("ir('na')");W(pg,"MOD==='na'");pg.click('#naAsis');pg.wait_for_selector('#dAP[open]');pg.click('#apT3');pg.wait_for_selector('#apCfTb tr[data-ll="emp:e3"]')
    ok('config_muestra_los_dias_propios',pg.is_checked('#apCfTb tr[data-ll="emp:e3"] [data-d="1"]') and not pg.is_checked('#apCfTb tr[data-ll="emp:e3"] [data-d="6"]'))
    pg.click('#apCfOk');W(pg,"document.getElementById('apMsg').textContent.indexOf('guardada')>-1")
    ok('guardar_config_no_borra_los_dias_propios',pg.evaluate("apHorDe('emp:e3').dias.join()")=='1,2,3,4,5' and pg.evaluate("apHorDe('emp:e1').dias.join()")=='1,2,3,4,5')
    # permiso: un usuario sin nómina administrativa no lee ni escribe las marcas
    r=ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'sinnom','name':'Sin Nómina','rol':'personalizado','modulos':{'pagos':'ver'},'clave':'clave-sn-123'}),headers=HDR)
    ses=b.new_context();ses.set_default_timeout(15000)
    rr=ses.request.post(B+'/api/login',data=json.dumps({'u':'sinnom','clave':'clave-sn-123'}),headers=HDR)
    if rr.status==200:
        ok('sin_permiso_no_lee_las_marcas',ses.request.get(B+'/api/doc/checadas/2026-10').json().get('exists') is False)
        ok('sin_permiso_no_escribe_las_marcas',ses.request.put(B+'/api/doc/checadas/2026-10',data=json.dumps({'dman':{}}),headers=HDR).status==403)
    else:
        ok('login_de_prueba',False)
    ok('sin_errores_de_pagina',not errs)
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(json.dumps(R,ensure_ascii=False,indent=0));print('FALLAS:',bad,errs[:3]);print('%d/%d'%(len(R)-len(bad),len(R)))
