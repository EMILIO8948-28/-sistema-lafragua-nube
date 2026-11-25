"""Tablero de dirección: indicadores de matrícula, finanzas, vencidos y académico con fecha fija; permisos y exportación."""
import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3165;B='http://127.0.0.1:%d'%PORT;TOK='tok-dr-1'
os.system('rm -rf /tmp/nbdata_dr /tmp/crl_dr && mkdir -p /tmp/nbdata_dr /tmp/crl_dr')
RELOJ='/tmp/crl_dr/reloj.txt';HOY=datetime.date.today().isoformat();open(RELOJ,'w').write(HOY)
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_dr',LF_SETUP_TOKEN=TOK,LF_SIN_CONTACTO='1',LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ)
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
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950},accept_downloads=True);ctx.set_default_timeout(15000)
    ctx.clock.install(time=datetime.datetime(2026,11,18,12,0,0))
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):
        r=ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR);assert r.status==200,(path,r.status,r.text()[:200])
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':'Derecho','n':36,'col':1500,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    for sid,n,pl in (('s1','Ana López','Pedagogía'),('s2','Beto Mena','Pedagogía'),('s3','Carla Díaz','Pedagogía'),('s4','Dani Ruiz','Derecho')):
        put('students/'+sid,{'mat':'2026%03d'%int(sid[1:]),'nombre':n,'carrera':pl,'programa':pl,'ingreso':2026,'nuevo':False,'total':0})
    P=lambda i,f,m,**k:dict({'id':i,'fecha':f,'monto':m,'metodo':'Efectivo','estado':'confirmado','folio':'R-%06d'%int(i[1:])},**k)
    put('ledger/s2',{'pagos':[P('p1','2026-11-18',3900),P('p9','2026-11-17',500,estado='pendiente')]})
    put('ledger/s3',{'pagos':[P('p2','2026-10-05',1300),P('p3','2026-11-18',1300)]})
    put('gastos/2026-11',{'items':[{'id':'g1','fecha':'2026-11-05','concepto':'Papelería','cat':'Papelería','monto':700,'metodo':'Efectivo'},{'id':'g2','fecha':'2026-11-01','concepto':'Renta','cat':'Renta','monto':300,'metodo':'Transferencia','pend':True,'vence':'2026-11-01'}]})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[]})
    put('grupos/g1',{'num':'1111','plan':'Pedagogía','per':'Sep–Dic 2026','cuat':1,'alumnos':['s1','s2','s3']})
    put('materias/m1',{'per':'Sep–Dic 2026','plan':'Pedagogía','cuat':1,'nom':'Didáctica','ini':'09:00','fin':'11:00','docId':'d1','ev':'2026-11-07'})
    ci=lambda i,m,c,mid:{'id':i,'mid':mid,'mat':m,'plan':'Pedagogía','per':'Sep–Dic 2026','cuat':1,'doc':'Prof. Uno','cal':c,'fecha':'2026-11-01'}
    put('calif/s1',{'items':[ci('1','Lectura',9.0,'x1'),ci('2','Redacción',5.0,'x2')]})
    put('calif/s2',{'items':[ci('3','Lectura',10.0,'x1'),ci('4','Redacción',8.0,'x2')]})
    put('calif/s3',{'items':[ci('5','Lectura',6.0,'x1'),ci('6','Redacción',9.0,'x2')]})
    put('libros/L1',{'titulo':'Rayuela','autor':'Cortázar','ejemplares':1,'activo':True,'disp':0})
    put('prestamos/s1',{'nombre':'Ana López','tipo':'alumno','items':[{'id':'pp1','libro':'L1','fecha':'2026-11-01','vence':'2026-11-08','devuelto':'','renovaciones':0}]})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===4&&CAL.s3&&PRE.s1&&LIB.L1&&MAT.m1")
    ok('fecha_del_navegador_congelada',pg.evaluate("today()")=='2026-11-18')
    ok('mosaico_visible_para_el_admin',pg.evaluate("!document.getElementById('mDir').hidden")  and pg.evaluate("accesoVista('dir')"))
    pg.evaluate("ir('home')");pg.click('#mDir');W(pg,"MOD==='dir'&&!document.getElementById('vDir').hidden");pg.wait_for_timeout(300)
    ok('titulo_de_la_pantalla','Tablero de dirección' in pg.inner_text('#ttl'))
    d=pg.evaluate("drCalc()")
    ok('alumnos_activos_y_nuevos',d['activos']==4 and d['nuevos']==4 and d['bajas']==0 and d['egresados']==0)
    ok('alumnos_por_plan',d['planes']==[{'k':'Pedagogía','n':3},{'k':'Derecho','n':1}])
    ok('cobrado_del_mes_solo_confirmado_y_del_mes',abs(d['cobrado']-5200)<0.01)
    ok('gastos_del_mes_sin_pendientes',abs(d['gastos']-700)<0.01 and abs(d['balance']-4500)<0.01)
    ok('cuentas_por_pagar',d['pendN']==1 and abs(d['pendM']-300)<0.01 and d['pendV']==1)
    ok('vencido_por_cobrar',abs(d['morM']-9700)<0.01 and len(d['mor'])==3 and d['mor2']==2)
    ok('morosos_ordenados_por_adeudo',[m['s']['id'] for m in d['mor']]==['s4','s1','s3'] and [m['n'] for m in d['mor']]==[3,3,1])
    ok('promedio_y_reprobacion',abs(d['prom']-47/6)<0.01 and abs(d['reprob']-100/3)<0.1 and d['alumRep']==2 and d['califN']==6)
    ok('calificaciones_atrasadas',d['califVenc']==1 and d['docVenc']==1)
    ok('pendientes',d['solPend']==0 and d['quejasN']==0 and d['prestVenc']==1)
    tx=pg.inner_text('#vDir')
    ok('muestra_la_matricula','Alumnos activos' in tx and 'Pedagogía' in tx and 'Derecho' in tx and '4 de nuevo ingreso' in tx)
    ok('muestra_las_finanzas','$5,200.00' in tx and '$700.00' in tx and '$4,500.00' in tx and '$9,700.00' in tx and '1 pendientes · 1 vencidas' in tx)
    ok('tabla_de_morosos_con_el_mayor_primero',pg.evaluate("document.querySelector('#drMor tr td').textContent.indexOf('Dani Ruiz')>-1")and '$4,500.00' in pg.inner_text('#drMor') and 'Beto' not in pg.inner_text('#drMor') and '2 deben dos o más' in pg.inner_text('#drMorN'))
    ok('muestra_lo_academico','7.8' in tx and '33.3 %' in tx and '2 alumnos con alguna reprobada' in tx and 'asignaturas de 1 docentes fuera de plazo' in tx)
    ok('muestra_pendientes','Libros vencidos' in tx and 'Solicitudes de alumnos' in tx and 'Buzón de quejas' in tx)
    ok('barras_de_matricula',pg.locator('#drPlanes > div').count()==2)
    # reinscripción
    RQP=lambda sid,n,dec,mot='':{'sid':sid,'nombre':n,'periodo':'Ene–Abr 2027','decision':dec,'motivo':mot,'fecha':'2026-11-18'}
    ok('sin_periodo_avisa_que_falta_configurarlo','Aún no hay un periodo de reinscripción' in pg.inner_text('#drRqP') and pg.evaluate("document.getElementById('drRqW').hidden"))
    put('reinscripciones/_config',{'abierta':True,'periodo':'Ene–Abr 2027','desde':'','hasta':'2026-12-15','mensaje':'','bloquea':True})
    put('reinscripciones/s1',RQP('s1','Ana López','continuo'));put('reinscripciones/s2',RQP('s2','Beto Mena','no_continuo','Cambio de ciudad'));put('reinscripciones/s3',RQP('s3','Carla Díaz','no_continuo','cambio  de ciudad'))
    put('reinscripciones/s4',{'sid':'s4','nombre':'Dani Ruiz','periodo':'Sep–Dic 2025','decision':'continuo','motivo':'','fecha':'2025-08-01'})
    W(pg,"RQ.s3&&RQ._config&&document.getElementById('drRqP').textContent.indexOf('Ene–Abr 2027')>=0");pg.wait_for_timeout(200)
    r=pg.evaluate("drCalc().rq")
    ok('reinscripcion_cuenta',r['per']=='Ene–Abr 2027' and r['n']==4 and r['si']==1 and r['no']==2 and r['pend']==1)
    ok('respuesta_de_otro_periodo_no_cuenta',r['pend']==1 and any(x['k']=='Derecho' and x['pend']==1 and x['si']==0 for x in r['lista']))
    ok('reinscripcion_ingresos',r['ingNow']==5400 and r['ingSi']==1300 and r['ingNo']==2600 and r['ingPend']==1500)
    ok('motivos_agrupados_sin_importar_mayusculas_ni_espacios',r['motivos']==[{'t':'cambio de ciudad','n':2}])
    ok('reinscripcion_por_plan',[(x['k'],x['n'],x['si'],x['no'],x['pend']) for x in r['lista']]==[('Pedagogía',3,1,2,0),('Derecho',1,0,0,1)])
    tx=pg.inner_text('#vDir')
    ok('muestra_reinscripcion','abierta hasta el' in tx and 'Continúan' in tx and '25 % de los activos' in tx and '$1,300.00' in tx and '$2,600.00' in tx and '$1,500.00' in tx and 'cambio de ciudad' in tx and '2 alumnos' in tx)
    ok('tabla_reinscripcion_por_plan','Pedagogía' in pg.inner_text('#drRqT') and '33 %' in pg.inner_text('#drRqT'))
    put('reinscripciones/_config',{'abierta':False,'periodo':'Ene–Abr 2027','desde':'','hasta':'','mensaje':'','bloquea':True})
    W(pg,"document.getElementById('drRqP').textContent.indexOf('cerrada')>=0");ok('reinscripcion_cerrada_se_actualiza_sola',True)
    # cambia un dato y actualiza
    put('ledger/s1',{'pagos':[P('p7','2026-11-18',3900)]});pg.evaluate("ir('home')");pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&S.length===4&&S[0].pagos");pg.evaluate("ir('dir')");W(pg,"MOD==='dir'");pg.wait_for_timeout(300)
    d2=pg.evaluate("drCalc()");ok('al_pagar_baja_lo_vencido_y_sube_lo_cobrado',abs(d2['morM']-5800)<0.01 and len(d2['mor'])==2 and abs(d2['cobrado']-9100)<0.01)
    ok('actualizar_repinta',(pg.click('#drRef') or True) and '$9,100.00' in pg.inner_text('#drFin'))
    # exportar
    with pg.expect_download() as dl:pg.click('#drCsv')
    cv=open(dl.value.path(),encoding='utf-8-sig').read()
    ok('csv_del_resumen','Cobrado del mes,9100.00' in cv and 'Alumnos activos,4' in cv and 'Alumnos en Pedagogía,3' in cv and 'Libros vencidos,1' in cv and 'Reinscripción: continúan,1' in cv and 'Ingreso mensual perdido,2600.00' in cv and 'Reinscripción en Pedagogía (continúan/no/sin responder),1/2/0' in cv and dl.value.suggested_filename=='tablero-direccion-2026-11-18.csv')
    # buscador
    pg.evaluate("ir('home')");W(pg,"MOD==='home'");pg.fill('#hBus','tablero');pg.wait_for_timeout(300);ok('buscador_lo_encuentra','Tablero de dirección' in pg.inner_text('#hBusR'))
    # sin acceso para otros roles
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc1','name':'Esc Uno','rol':'personalizado','modulos':{'escolar':'editar','pagos':'editar'},'clave':'clave-esc1-123'}),headers=HDR)
    cx=b.new_context();cx.clock.install(time=datetime.datetime(2026,11,18,12,0,0));pe=cx.new_page();pe.on("pageerror",lambda e:errs.append(str(e)));pe.goto(B+'/');W(pe,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pe.fill('#lgU','esc1');pe.fill('#lgP','clave-esc1-123');pe.click('#lgGo');W(pe,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&S.length>=1")
    ok('otro_rol_no_ve_el_mosaico',pe.evaluate("document.getElementById('mDir').hidden")  and pe.evaluate("accesoVista('dir')===false"))
    pe.evaluate("ir('dir')");pe.wait_for_timeout(300);ok('otro_rol_no_entra_al_tablero',pe.evaluate("document.getElementById('vDir').hidden||MOD!=='dir'"))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
