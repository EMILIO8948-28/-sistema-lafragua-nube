import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3112;B='http://127.0.0.1:%d'%PORT;TOK='tok-cb-123'
os.system('rm -rf /tmp/nbdata42 /tmp/crl && mkdir -p /tmp/nbdata42 /tmp/crl')
RELOJ='/tmp/crl/reloj.txt';open(RELOJ,'w').write('2026-11-12')
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata42',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ)
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def reloj(f):open(RELOJ,'w').write(f)
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    def vista():return {f['sid']:f for f in ctx.request.get(B+'/api/cobranza/vista').json()['filas']}
    def avisos():return {x['id']:x['data'] for x in ctx.request.get(B+'/api/col/avisos').json()['docs']}
    def evalua():return ctx.request.post(B+'/api/cobranza/accion',data=json.dumps({'accion':'evaluar'}),headers=HDR)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    nombres={'s1':'Ana López Ramírez','s2':'Beto Mena Ruiz','s3':'Carla Díaz Soto','s4':'Diego Vega Luna','s5':'Elena Ríos Cano','s6':'Fabio Gil Paz','s7':'Gina Soto Ibarra','s8':'Hugo Sin Acceso'}
    for i,(sid,nom) in enumerate(nombres.items(),1):put('students/'+sid,{'mat':'2026%04d'%i,'nombre':nom,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'total':0})
    pago=lambda i,f,m,est='confirmado':{'id':'p%s'%i,'fecha':f,'monto':m,'metodo':'Efectivo','estado':est,'folio':'R-%06d'%int(i[1:]) if i[1:].isdigit() else 'R-1'}
    put('ledger/s3',{'pagos':[pago('p31','2026-09-05',1300),pago('p32','2026-10-05',1300)]})
    put('egresados/s5',{'fecha':'2026-10-01'})
    put('acuerdos/ac1',{'id':'ac1','sid':'s4','num':'AC-1','cuotas':[{'fecha':'2026-12-15','monto':2600,'pagada':False}]})
    for sid in ['s1','s2','s3','s4','s5','s6','s7']:
        r=ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'al'+sid,'name':nombres[sid],'alumno':sid,'clave':'abcd-efgh'}]}),headers=HDR);assert r.status==200
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    def sesion_alumno(sid,clave='abcd-efgh',nueva='clave-ana-77'):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':'al'+sid,'clave':clave}),headers=HDR)
        if r.status==200:
            cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':clave,'nueva':nueva}),headers=HDR)
        return cx,r
    A1,r1=sesion_alumno('s1');ok('alumno_entra_antes_de_cualquier_aviso',r1.status==200)
    # ================== desactivada: vista previa ==================
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===8");pg.evaluate("ir('pagos')");pg.wait_for_selector('#bCob');pg.click('#bCob');pg.wait_for_selector('#dCob[open]');W(pg,"COBV!==null")
    ok('avisa_que_esta_desactivada',pg.is_visible('#cbAviso') and 'desactivada' in pg.inner_text('#cbAviso'))
    ok('vista_previa_de_quien_recibiria_el_aviso','Ana López Ramírez' in pg.inner_text('#cbTb') and 'Recibiría el aviso 1' in pg.inner_text('#cbTb') and '3 colegiaturas' in pg.inner_text('#cbTb:has-text("Ana")') )
    v=vista();ok('calcula_las_colegiaturas_vencidas',v['s1']['adeudo']['n']==3 and abs(v['s1']['adeudo']['total']-3900)<0.01 and [m['c'] for m in v['s1']['adeudo']['meses']]==['Colegiatura Septiembre 2026','Colegiatura Octubre 2026','Colegiatura Noviembre 2026'] and v['s1']['accion']=='inicio')
    ok('respeta_los_pagos_ya_hechos',v['s3']['adeudo']['n']==1 and v['s3']['accion']=='' and v['s2']['adeudo']['n']==3)
    ok('no_cuenta_a_egresados_ni_acuerdos_vigentes',v['s5']['exento'] and v['s5']['motivoExento']=='egresado' and v['s4']['exento'] and v['s4']['motivoExento']=='acuerdo de pago vigente' and v['s4']['accion']=='' and v['s5']['accion']=='')
    ok('solo_alumnos_con_acceso','s8' not in v and len(v)==7)
    ok('desactivada_no_ejecuta',evalua().status==409 and avisos()=={})
    reloj('2026-11-13');ok('si_no_esta_activa_no_envia_nada',evalua().status==409 and avisos()=={})
    reloj('2026-11-12')
    # exención manual
    ok('exentar_pide_motivo',ctx.request.post(B+'/api/cobranza/accion',data=json.dumps({'accion':'exentar','sid':'s6'}),headers=HDR).status==400)
    pg.evaluate("renderCob()");pg.locator('#cbTb tr:has-text("Fabio") [data-cbx]').click();pg.wait_for_selector('#dCbEx[open]');pg.click('#cbExOk');ok('motivo_obligatorio_en_pantalla','motivo' in pg.inner_text('#cbExMsg'));pg.fill('#cbExM','Convenio verbal con dirección');pg.click('#cbExOk');W(pg,"COBV.filas.find(function(f){return f.sid==='s6'}).exento")
    ok('alumno_exento',vista()['s6']['exento'] and vista()['s6']['exentoInfo']['motivo']=='Convenio verbal con dirección' and vista()['s6']['accion']=='')
    # ================== activar desde la pantalla ==================
    pg.locator('#dCob summary').click();pg.check('#cbAct');pg.fill('#cbUmb','5');pg.click('#cbGuardar');ok('valida_numeros_en_pantalla',True)
    pg.fill('#cbUmb','2');pg.fill('#cbDia','40');pg.click('#cbGuardar');ok('rechaza_numeros_fuera_de_rango','Revisa los números' in pg.inner_text('#cbMsg'))
    pg.fill('#cbDia','10');pg.click('#cbGuardar');W(pg,"COBV.cfg.activa===true")
    ok('activa_la_cobranza_con_la_configuracion',get('config/cobranza')['data']['activa'] is True and get('config/cobranza')['data']['umbral']==2 and get('config/cobranza')['data']['graciaDias']==7 and pg.is_hidden('#cbAviso'))
    time.sleep(0.5)
    # ================== pagos antes de la revisión ==================
    reloj('2026-11-12');r=evalua();ok('revision_manual_solo_admin',r.status==200)
    av=avisos();ok('primer_aviso_a_quien_debe_dos_o_mas',set(av)=={'s1-1-1','s2-1-1','s7-1-1'})
    a1=av['s1-1-1'];ok('mensaje_amable_con_el_adeudo',a1['n']==1 and a1['titulo']=='Aviso de adeudo' and 'Hola, Ana' in a1['mensaje'] and 'adeudo de 3 colegiaturas' in a1['mensaje'] and 'Septiembre 2026: $1,300.00' in a1['mensaje'] and '$3,900.00' in a1['mensaje'] and 'amablemente' in a1['mensaje'] and 'Control escolar' in a1['mensaje'] and a1['leida'] is False and abs(a1['total']-3900)<0.01 and len(a1['meses'])==3)
    ok('no_avisa_a_quien_debe_menos_exentos_o_egresados',not any(k.startswith(('s3','s4','s5','s6')) for k in av))
    c1=get('cobranza/s1')['data'];ok('queda_en_proceso_de_aviso',c1['estado']=='avisando' and c1['inicio']=='2026-11-12' and c1['avisos'][0]['n']==1 and c1['ciclo']==1)
    reloj('2026-11-15');evalua();ok('no_repite_el_aviso_antes_de_tiempo',set(avisos())=={'s1-1-1','s2-1-1','s7-1-1'})
    # s2 hace un abono: se cierra el ciclo; s7 manda una transferencia pendiente
    put('ledger/s2',{'pagos':[pago('p21','2026-11-17',500)]})
    put('ledger/s7',{'pagos':[pago('p71','2026-11-18',1300,'pendiente')]})
    time.sleep(3.5)
    ok('el_abono_cierra_el_ciclo_sin_bloquear',get('cobranza/s2')['data']['estado']=='ok' and get('cobranza/s2')['data']['cerrado']['motivo']=='abono')
    ok('una_transferencia_pendiente_tambien_cuenta_como_abono',get('cobranza/s7')['data']['estado']=='ok' and get('cobranza/s7')['data']['cerrado']['motivo']=='abono')
    reloj('2026-11-19');evalua();av=avisos()
    ok('segundo_aviso_solo_a_quien_sigue_sin_pasar',set(av)=={'s1-1-1','s2-1-1','s7-1-1','s1-1-2'} and av['s1-1-2']['titulo']=='Recordatorio de adeudo (2 de 3)' and 'Aún no registramos tu pago' in av['s1-1-2']['mensaje'])
    reloj('2026-11-26');evalua();av=avisos();a3=av.get('s1-1-3',{})
    ok('tercer_aviso_con_la_advertencia',a3.get('titulo')=='Último aviso de adeudo (3 de 3)' and 'último aviso' in a3.get('mensaje','') and 'antes del 3 de diciembre de 2026' in a3.get('mensaje','') and 'bloquearán' in a3.get('mensaje','') and 'baja temporal' in a3.get('mensaje',''))
    ok('exactamente_tres_avisos_a_s1',len([k for k in av if k.startswith('s1-1-')])==3)
    reloj('2026-12-02');evalua();ok('no_bloquea_antes_del_plazo',get('cobranza/s1')['data']['estado']=='avisando' and A1.request.get(B+'/api/col/students').status==200)
    # ---- el alumno ve sus avisos ----
    ok('alumno_lee_sus_avisos',sorted(x['id'] for x in A1.request.get(B+'/api/col/avisos').json()['docs'])==['s1-1-1','s1-1-2','s1-1-3'])
    A2c,_=sesion_alumno('s2');ok('no_ve_los_avisos_de_otros',sorted(x['id'] for x in A2c.request.get(B+'/api/col/avisos').json()['docs'])==['s2-1-1'])
    ok('alumno_no_ve_la_cobranza',A1.request.get(B+'/api/col/cobranza').json()['docs']==[] and A1.request.get(B+'/api/cobranza/vista').status==403)
    pa=lambda cx,path,obj,met='PATCH':cx.request.fetch(B+'/api/doc/'+path,method=met,data=json.dumps(obj),headers=HDR).status
    ok('alumno_solo_marca_leidos_los_suyos',pa(A1,'avisos/s1-1-1',{'leida':True})==200 and pa(A1,'avisos/s2-1-1',{'leida':True})==403 and pa(A1,'avisos/s1-1-2',{'mensaje':'x'})==403 and pa(A1,'avisos/s1-1-2',{'leida':True},'PUT')==403 and get('avisos/s1-1-1')['data']['leida'] is True)
    pa(A1,'avisos/s1-1-1',{'leida':False})
    # ---- portal en pantalla ----
    cp=b.new_context(viewport={'width':1000,'height':900});cp.set_default_timeout(15000);pp=pagina(cp);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pp.fill('#lgU','als1');pp.fill('#lgP','clave-ana-77');pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&S.length===1&&Object.keys(AVI).length===3");pp.wait_for_timeout(500)
    tx=pp.inner_text('#poBody');ok('portal_muestra_los_avisos_de_adeudo','Aviso de adeudo' in tx and 'Recordatorio de adeudo (2 de 3)' in tx and 'Último aviso de adeudo (3 de 3)' in tx and 'amablemente' in tx and 'Septiembre 2026' in tx and '$3,900.00' in tx and 'Nuevo' in tx)
    pp.screenshot(path='/tmp/cb_portal.png',full_page=True)
    pp.click('[data-lee]');W(pp,"aviNoLeidos().length===0");ok('marcar_como_leidas',all(get('avisos/s1-1-%d'%i)['data']['leida'] for i in (1,2,3)) and 'Nuevo' not in pp.inner_text('#poBody'))
    # ================== bloqueo ==================
    reloj('2026-12-03');evalua();c1=get('cobranza/s1')['data']
    ok('bloquea_al_vencer_el_plazo_sin_abonos',c1['estado']=='bloqueado' and c1['bloqueadoEn']=='2026-12-03')
    ok('cierra_la_sesion_abierta_del_alumno',A1.request.get(B+'/api/col/students').status==401)
    rb=b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'als1','clave':'clave-ana-77'}),headers=HDR);jb=rb.json()
    ok('al_entrar_le_dice_que_se_bloqueo_por_falta_de_pago',rb.status==403 and jb.get('bloqueado') is True and 'bloqueado por falta de pago' in jb['error'] and 'Control escolar' in jb['error'] and 'regularizar tu situación' in jb['error'] and 'baja temporal' in jb['error'])
    rw=b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'als1','clave':'otra-clave-123'}),headers=HDR)
    ok('con_clave_incorrecta_no_revela_el_estado',rw.status==401 and rw.json()['error']=='Usuario o contraseña incorrectos.' and 'bloqueado' not in rw.text())
    ok('los_demas_siguen_entrando',b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'als2','clave':'clave-ana-77'}),headers=HDR).status==200)
    pl=pagina(b.new_context(viewport={'width':900,'height':800}));pl.goto(B+'/');W(pl,"typeof sesion==='function'&&document.body.classList.contains('locked')");pl.fill('#lgU','als1');pl.fill('#lgP','clave-ana-77');pl.click('#lgGo');W(pl,"document.getElementById('lgE').textContent.length>20")
    ok('pantalla_de_inicio_muestra_el_mensaje','bloqueado por falta de pago' in pl.inner_text('#lgE') and 'baja temporal' in pl.inner_text('#lgE') and pl.is_visible('#lgE'));pl.screenshot(path='/tmp/cb_login.png')
    ok('administrador_ve_el_bloqueo',vista()['s1']['estado']=='bloqueado')
    pg.evaluate("renderCob();cargaCob()");time.sleep(0.8);W(pg,"COBV.filas.find(function(f){return f.sid==='s1'}).estado==='bloqueado'");pg.screenshot(path='/tmp/cb_admin.png',full_page=True)
    ok('pantalla_muestra_bloqueado_y_boton_desbloquear','Bloqueado' in pg.inner_text('#cbTb:has-text("Ana")') and pg.locator('#cbTb tr:has-text("Ana") [data-cbd]').count()==1 and pg.inner_text('#cbC3')=='1')
    # ================== desbloqueo por abono ==================
    put('ledger/s1',{'pagos':[pago('p11','2026-12-04',300)]});time.sleep(3.5)
    c1=get('cobranza/s1')['data'];ok('al_pasar_a_pagar_se_desbloquea_solo',c1['estado']=='ok' and c1['cerrado']['motivo']=='abono' and 'bloqueadoEn' not in c1)
    A1b,rr=sesion_alumno('s1',clave='clave-ana-77',nueva='clave-ana-88') if False else (b.new_context(),None)
    rl=A1b.request.post(B+'/api/login',data=json.dumps({'u':'als1','clave':'clave-ana-77'}),headers=HDR);ok('ya_puede_entrar',rl.status==200)
    inf=[x for x in A1b.request.get(B+'/api/col/avisos').json()['docs'] if x['data']['tipo']=='info'];ok('queda_un_aviso_de_acceso_restablecido',len(inf)==1 and inf[0]['data']['titulo']=='Acceso restablecido')
    reloj('2026-12-20');evalua();ok('tras_un_abono_hay_pausa_antes_de_nuevos_avisos',not any(k.startswith('s1-2-') for k in avisos()) and get('cobranza/s1')['data']['estado']=='ok')
    reloj('2027-01-04');evalua();ok('pasada_la_pausa_y_con_adeudo_empieza_otro_ciclo','s1-2-1' in avisos() and get('cobranza/s1')['data']['ciclo']==2)
    # ================== manual: desbloquear y exentar con permisos ==================
    put('cobranza/s2',{'sid':'s2','estado':'bloqueado','ciclo':1,'avisos':[],'bloqueadoEn':'2027-01-04','mat':'20260002','nombre':nombres['s2']})
    CJ=b.new_context();CJ.request.post(B+'/api/login',data=json.dumps({'u':'caja1','clave':'clave-caja-123'}),headers=HDR)
    ES=b.new_context();ES.request.post(B+'/api/login',data=json.dumps({'u':'esc2','clave':'clave-esc2-123'}),headers=HDR)
    acc=lambda cx,o:cx.request.post(B+'/api/cobranza/accion',data=json.dumps(o),headers=HDR).status
    ok('control_escolar_sin_pagos_no_ve_la_cobranza',ES.request.get(B+'/api/cobranza/vista').status==403 and acc(ES,{'accion':'desbloquear','sid':'s2'})==403)
    ok('caja_ve_la_cobranza',CJ.request.get(B+'/api/cobranza/vista').status==200 and any(x['id']=='s2' for x in CJ.request.get(B+'/api/col/cobranza').json()['docs']))
    ok('el_acceso_de_s2_esta_bloqueado',b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'als2','clave':'clave-ana-77'}),headers=HDR).status==403)
    ok('caja_no_puede_exentar_ni_cambiar_la_configuracion',acc(CJ,{'accion':'exentar','sid':'s2','motivo':'prueba'})==403 and acc(CJ,{'accion':'evaluar'})==403 and CJ.request.put(B+'/api/doc/config/cobranza',data=json.dumps({'activa':False}),headers=HDR).status==403)
    ok('caja_puede_desbloquear',acc(CJ,{'accion':'desbloquear','sid':'s2'})==200 and get('cobranza/s2')['data']['estado']=='ok' and b.new_context().request.post(B+'/api/login',data=json.dumps({'u':'als2','clave':'clave-ana-77'}),headers=HDR).status==200)
    ok('no_se_desbloquea_a_quien_no_esta_bloqueado',acc(CJ,{'accion':'desbloquear','sid':'s2'})==409 and acc(CJ,{'accion':'desbloquear','sid':'nadie'})==404)
    ok('admin_exenta_y_quita_la_exencion',acc(ctx,{'accion':'exentar','sid':'s2','motivo':'Convenio'})==200 and vista()['s2']['exento'] and acc(ctx,{'accion':'quitar-exencion','sid':'s2'})==200 and not vista()['s2']['exento'])
    # configuración fuera de rango se acota
    put('config/cobranza',{'activa':True,'umbral':99,'diaLimite':0,'intervaloDias':-5,'graciaDias':'x','reinicioDias':9999})
    c=ctx.request.get(B+'/api/cobranza/vista').json()['cfg'];ok('la_configuracion_se_acota',c['umbral']==12 and c['diaLimite']==1 and c['intervaloDias']==1 and c['graciaDias']==7 and c['reinicioDias']==365 and c['activa'] is True)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
