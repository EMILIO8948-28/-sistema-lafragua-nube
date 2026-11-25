"""Comunicados generales: publicación, destinatarios (todos, alumnos, docentes, plan, grupo), vigencia, confirmación de lectura, permisos y portales."""
import subprocess,time,json,os,re,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3166;B='http://127.0.0.1:%d'%PORT;DD='/tmp/nbdata_cm'
ENVV=dict(os.environ,LF_SIN_CONTACTO='1',PORT=str(PORT),DATA_DIR=DD,LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf %s && mkdir -p %s'%(DD,DD))
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
HDR={'Content-Type':'application/json','x-lafragua':'1'}
PER='Sep–Dic 2026'
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
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&typeof DBH!=='undefined'&&DBH!==null")
    def raw(cx,path,o,m='put'):return getattr(cx.request,m)(B+'/api/doc/'+path,data=json.dumps(o),headers=HDR)
    def put(path,o):
        r=raw(ctx,path,o);assert r.status==200,(path,r.status,r.text()[:200])
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':'Derecho','n':36,'col':1500,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    for i,(n,pl) in enumerate([('Ana López','Pedagogía'),('Beto Mena','Pedagogía'),('Carla Díaz','Derecho'),('Dani Ruiz','Pedagogía')],1):put('students/s%d'%i,{'mat':'100%d'%i,'nombre':n,'carrera':pl,'programa':pl,'ingreso':2026,'nuevo':False})
    put('grupos/g1',{'num':'1111','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2']});put('grupos/g2',{'num':'2222','plan':'Derecho','per':PER,'cuat':1,'alumnos':['s3']})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[]});put('docentes/d2',{'nombre':'Prof. Dos','esp':'Historia','asig':[]})
    def usr(u,name,rol,modulos=None,doc=None):
        d={'u':u,'name':name,'rol':rol,'clave':'clave-%s-123'%u}
        if modulos is not None:d['modulos']=modulos
        if doc:d['doc']=doc
        r=ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR);assert r.status==200,(u,r.status,r.text())
    usr('prof1','Prof. Uno','docente',doc='d1');usr('prof2','Prof. Dos','docente',doc='d2');usr('esc1','Esc Uno','personalizado',{'escolar':'editar'});usr('ver1','Eva Ver','personalizado',{'escolar':'ver'})
    nombres=['Ana López','Beto Mena','Carla Díaz','Dani Ruiz']
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'100%d'%i,'name':nombres[i-1],'alumno':'s%d'%i,'clave':'abcd-efg%d'%i} for i in range(1,5)]}),headers=HDR)
    def sesion(u,c):
        cx=b.new_context(viewport={'width':1200,'height':950});r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status,r.text());return cx
    def alumno(i):
        cx=sesion('100%d'%i,'abcd-efg%d'%i);cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efg%d'%i,'nueva':'clave-nueva-7%d'%i}),headers=HDR);return sesion('100%d'%i,'clave-nueva-7%d'%i)
    AL=[alumno(i) for i in range(1,5)];P1=sesion('prof1','clave-prof1-123');P2=sesion('prof2','clave-prof2-123');E1=sesion('esc1','clave-esc1-123');V1=sesion('ver1','clave-ver1-123')
    hoy=datetime.date.today();viejo=(hoy-datetime.timedelta(days=10)).isoformat();futuro=(hoy+datetime.timedelta(days=30)).isoformat()
    C=lambda t,para,**k:dict({'titulo':t,'cuerpo':'Texto del comunicado '+t,'para':para,'importante':False,'hasta':'','activo':True,'fecha':hoy.isoformat(),'autor':'Esc Uno'},**k)
    # ---- validación y permisos de escritura ----
    ok('titulo_corto_400',raw(E1,'comunicados/x1',C('ab',{'tipo':'todos'})).status==400)
    ok('cuerpo_vacio_400',raw(E1,'comunicados/x1',C('Titulo',{'tipo':'todos'},cuerpo=' ')).status==400)
    ok('destinatario_invalido_400',raw(E1,'comunicados/x1',C('Titulo',{'tipo':'todas'})).status==400 and raw(E1,'comunicados/x1',C('Titulo',{}) ).status==400)
    ok('plan_sin_nombre_400',raw(E1,'comunicados/x1',C('Titulo',{'tipo':'plan'})).status==400 and raw(E1,'comunicados/x1',C('Titulo',{'tipo':'grupo','grupo':''})).status==400)
    ok('fecha_no_valida_400',raw(E1,'comunicados/x1',C('Titulo',{'tipo':'todos'},hasta='mañana')).status==400)
    ok('booleanos_no_validos_400',raw(E1,'comunicados/x1',C('Titulo',{'tipo':'todos'},importante='si')).status==400)
    ok('nada_se_guardo_con_errores',ctx.request.get(B+'/api/col/comunicados').json()['docs']==[])
    ok('escolar_ver_no_publica',raw(V1,'comunicados/x1',C('Titulo valido',{'tipo':'todos'})).status in (401,403))
    ok('alumno_no_publica',raw(AL[0],'comunicados/x1',C('Titulo valido',{'tipo':'todos'})).status in (401,403))
    ok('docente_no_publica',raw(P1,'comunicados/x1',C('Titulo valido',{'tipo':'todos'})).status in (401,403))
    ok('escolar_editar_publica',raw(E1,'comunicados/c1',C('Cierre de semestre',{'tipo':'todos'},importante=True)).status==200)
    for i,(tt,pa,k) in enumerate([('Solo alumnos',{'tipo':'alumnos'},{}),('Solo docentes',{'tipo':'docentes'},{}),('Plan Pedagogía',{'tipo':'plan','plan':'Pedagogía'},{}),('Grupo 1111',{'tipo':'grupo','grupo':'g1'},{}),('Archivado',{'tipo':'todos'},{'activo':False}),('Vencido',{'tipo':'todos'},{'hasta':viejo}),('Vigente con fecha',{'tipo':'alumnos'},{'hasta':futuro})],2):put('comunicados/c%d'%i,C(tt,pa,**k))
    mios=lambda cx:cx.request.get(B+'/api/comunicados/mios')
    tit=lambda cx:sorted(x['titulo'] for x in mios(cx).json()['comunicados'])
    # ---- a quién le toca ----
    ok('ana_grupo_y_plan',tit(AL[0])==sorted(['Cierre de semestre','Solo alumnos','Plan Pedagogía','Grupo 1111','Vigente con fecha']))
    ok('beto_igual_que_ana',tit(AL[1])==tit(AL[0]))
    ok('carla_de_otro_plan_solo_los_generales',tit(AL[2])==sorted(['Cierre de semestre','Solo alumnos','Vigente con fecha']))
    ok('dani_sin_grupo_pero_del_plan',tit(AL[3])==sorted(['Cierre de semestre','Solo alumnos','Plan Pedagogía','Vigente con fecha']))
    ok('docente_solo_todos_y_docentes',tit(P1)==sorted(['Cierre de semestre','Solo docentes']) and tit(P2)==tit(P1))
    ok('archivado_y_vencido_no_se_muestran',all('Archivado' not in tit(c) and 'Vencido' not in tit(c) for c in AL+[P1]))
    ok('personal_no_recibe_por_este_medio',mios(E1).status==200 and mios(E1).json()['comunicados']==[])
    ok('sin_sesion_no_puede',b.new_context().request.get(B+'/api/comunicados/mios').status in (401,403))
    ok('todos_traen_los_campos',all(set(['id','titulo','cuerpo','fecha','importante','leido']) <= set(x) for x in mios(AL[0]).json()['comunicados']) and [x for x in mios(AL[0]).json()['comunicados'] if x['titulo']=='Cierre de semestre'][0]['importante'] is True)
    ok('alumno_no_lee_la_coleccion',AL[0].request.get(B+'/api/col/comunicados').json()['docs']==[] and P1.request.get(B+'/api/col/comunicados').json()['docs']==[])
    ok('alumno_no_lee_las_lecturas',AL[0].request.get(B+'/api/col/comlec').json()['docs']==[])
    # ---- confirmar lectura ----
    leer=lambda cx,i:cx.request.post(B+'/api/comunicados/leido',data=json.dumps({'id':i}),headers=HDR)
    ok('ana_confirma',leer(AL[0],'c1').status==200)
    leidos=lambda cx:{x['titulo']:x['leido'] for x in mios(cx).json()['comunicados']}
    ok('queda_leido_solo_para_ana',leidos(AL[0])['Cierre de semestre'] is True and leidos(AL[1])['Cierre de semestre'] is False and leidos(AL[0])['Solo alumnos'] is False)
    ok('confirmar_dos_veces_no_duplica',leer(AL[0],'c1').status==200 and len(json.loads(ctx.request.get(B+'/api/doc/comlec/c1').text())['data']['lect'])==1)
    ok('no_puede_confirmar_el_que_no_es_para_el',leer(AL[2],'c5').status==404 and leer(AL[2],'c4').status==404 and leer(P1,'c2').status==404)
    ok('id_inventado_404',leer(AL[0],'zzzz').status==404 and leer(AL[0],'../x').status==404)
    ok('docente_confirma_el_suyo',leer(P1,'c3').status==200 and leidos(P1)['Solo docentes'] is True and leidos(P2)['Solo docentes'] is False)
    ok('archivado_no_se_puede_confirmar',leer(AL[0],'c6').status==404)
    # ---- resumen para Control escolar ----
    rs=E1.request.get(B+'/api/comunicados/resumen');rj=rs.json()['resumen'] if rs.status==200 else {}
    ok('resumen_para_escolar',rs.status==200 and rj['c1']['total']==6 and rj['c1']['leidos']==1 and rj['c1']['leyeron'][0]['n']=='Ana López' and 'Prof. Uno' in rj['c1']['pendientes'] and 'Ana López' not in rj['c1']['pendientes'])
    ok('resumen_por_destinatario',rj['c2']['total']==4 and rj['c3']['total']==2 and rj['c3']['leidos']==1 and rj['c4']['total']==3 and rj['c5']['total']==2 and rj['c5']['pendientes']==['Ana López','Beto Mena'])
    rj2=ctx.request.get(B+'/api/comunicados/resumen').json()['resumen'];ok('resumen_ve_al_docente_que_leyo',rj2['c3']['leidos']==1 and rj2['c3']['leyeron'][0]['n']=='Prof. Uno')
    ok('escolar_ver_puede_ver_resumen',V1.request.get(B+'/api/comunicados/resumen').status==200)
    ok('alumno_y_docente_no_ven_resumen',AL[0].request.get(B+'/api/comunicados/resumen').status==403 and P1.request.get(B+'/api/comunicados/resumen').status==403)
    # ---- pantalla de Control escolar ----
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===4&&Object.keys(COM).length===8");pg.evaluate("ir('esc');etab('M')");W(pg,"!document.getElementById('eM').hidden&&document.getElementById('cmLista').children.length>=8")
    tx=pg.inner_text('#cmLista')
    ok('lista_muestra_los_publicados','Cierre de semestre' in tx and 'Solo docentes' in tx and 'Archivado' in tx and 'Vencido' in tx and 'Importante' in tx)
    ok('lista_muestra_destinatarios','Solo alumnos' in tx and 'Alumnos de Pedagogía' in tx and 'Grupo 1111 · Pedagogía' in tx)
    W(pg,"COMR!==null&&COMR.c1");pg.wait_for_timeout(300);ok('lista_muestra_lecturas','Leído por 1 de 6' in pg.inner_text('#cmLista'))
    pg.locator('#cmLista details summary').first.click()
    ok('detalle_de_quien_leyo_y_quien_no','Ya lo leyeron' in pg.inner_text('#cmLista') or 'Aún no lo leen' in pg.inner_text('#cmLista'))
    # validación de pantalla
    pg.click('#cmPub');ok('ui_exige_titulo','título' in pg.inner_text('#cmcMsg').lower())
    pg.fill('#cmTit','Junta de padres');pg.click('#cmPub');ok('ui_exige_mensaje','mensaje' in pg.inner_text('#cmcMsg').lower())
    pg.fill('#cmCue','El viernes a las 10:00 en el auditorio.');pg.select_option('#cmPara','plan');ok('ui_muestra_plan_y_oculta_grupo',pg.is_visible('#cmPlan') and not pg.is_visible('#cmGrp'))
    pg.select_option('#cmPara','grupo');ok('ui_muestra_grupo',pg.is_visible('#cmGrp') and 'Derecho' in pg.inner_text('#cmGrp'))
    pg.select_option('#cmPara','plan');pg.select_option('#cmPlan','Derecho');pg.fill('#cmHas',viejo);pg.click('#cmPub');ok('ui_rechaza_vigencia_pasada','ya pasó' in pg.inner_text('#cmcMsg'))
    pg.fill('#cmHas','');pg.check('#cmImp');pg.click('#cmPub');W(pg,"document.getElementById('cmcMsg').textContent.indexOf('publicado')>-1")
    nuevo=[d for d in ctx.request.get(B+'/api/col/comunicados').json()['docs'] if d['data']['titulo']=='Junta de padres']
    ok('ui_publica_en_el_servidor',len(nuevo)==1 and nuevo[0]['data']['para']=={'tipo':'plan','plan':'Derecho'} and nuevo[0]['data']['importante'] is True and nuevo[0]['data']['autor']=='Administrador' and nuevo[0]['data']['fecha']==pg.evaluate("today()"))
    ok('ui_limpia_el_formulario',pg.input_value('#cmTit')=='' and pg.input_value('#cmPara')=='todos')
    ok('ui_el_nuevo_le_llega_a_carla',any(x=='Junta de padres' for x in tit(AL[2])) and 'Junta de padres' not in tit(AL[0]))
    # editar
    pg.wait_for_timeout(500);pg.locator('#cmLista .pay:has-text("Junta de padres") button[data-cme]').click();ok('ui_editar_carga_el_formulario',pg.input_value('#cmTit')=='Junta de padres' and pg.input_value('#cmPara')=='plan' and pg.input_value('#cmPlan')=='Derecho' and 'Guardar cambios' in pg.inner_text('#cmPub'))
    pg.select_option('#cmPara','todos');pg.fill('#cmTit','Junta de padres y docentes');pg.click('#cmPub');W(pg,"document.getElementById('cmcMsg').textContent.indexOf('Cambios guardados')>-1")
    ed=ctx.request.get(B+'/api/doc/comunicados/'+nuevo[0]['id']).json()['data'];ok('ui_edicion_conserva_id_y_fecha',ed['titulo']=='Junta de padres y docentes' and ed['para']=={'tipo':'todos'} and ed['fecha']==nuevo[0]['data']['fecha'] and len(ctx.request.get(B+'/api/col/comunicados').json()['docs'])==9)
    # archivar
    pg.wait_for_timeout(400);pg.locator('#cmLista .pay:has-text("Junta de padres y docentes") button[data-cma]').click();W(pg,"document.getElementById('cmcMsg').textContent.indexOf('archivado')>-1")
    ok('ui_archivar_lo_oculta_a_los_portales',ctx.request.get(B+'/api/doc/comunicados/'+nuevo[0]['id']).json()['data']['activo'] is False and 'Junta de padres y docentes' not in tit(AL[2]))
    pg.locator('#cmLista .pay:has-text("Junta de padres y docentes") button[data-cma]').click();W(pg,"document.getElementById('cmcMsg').textContent.indexOf('reactivado')>-1");ok('ui_reactivar',ctx.request.get(B+'/api/doc/comunicados/'+nuevo[0]['id']).json()['data']['activo'] is True)
    # ---- portal del alumno ----
    pa=pagina(AL[1]);pa.goto(B+'/');W(pa,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&document.getElementById('cmBoxP')!==null");W(pa,"document.getElementById('cmBoxP').textContent.indexOf('Comunicados')>-1",20)
    tp=pa.inner_text('#cmBoxP')
    ok('portal_muestra_comunicados_con_contador','Comunicados' in tp and 'nuevos' in tp and 'Cierre de semestre' in tp and 'Importante' in tp and 'Plan Pedagogía' in tp and 'Solo docentes' not in tp)
    nn=pa.locator('#cmBoxP [data-cml]').count()
    pa.locator('#cmBoxP .pay:has-text("Cierre de semestre") [data-cml]').click();W(pa,"document.querySelectorAll('#cmBoxP [data-cml]').length==%d"%(nn-1))
    ok('portal_entendido_marca_leido','✔ Leído' in pa.inner_text('#cmBoxP .pay:has-text("Cierre de semestre")') and pa.locator('#cmBoxP [data-cml]').count()==nn-1)
    ok('portal_el_servidor_lo_registra',leidos(AL[1])['Cierre de semestre'] is True)
    pa.reload();W(pa,"typeof APP!=='undefined'&&APP!==null&&document.getElementById('cmBoxP')!==null&&document.getElementById('cmBoxP').textContent.indexOf('Cierre de semestre')>-1",20);ok('portal_persiste_tras_recargar','✔ Leído' in pa.inner_text('#cmBoxP .pay:has-text("Cierre de semestre")'))
    ok('portal_cuenta_actualizada','%d nuevos'%(nn-1) in pa.inner_text('#cmBoxP') or (nn-1==1 and '1 nuevo' in pa.inner_text('#cmBoxP')))
    # ---- docente ----
    pd=pagina(P2);pd.goto(B+'/');W(pd,"typeof APP!=='undefined'&&APP!==null&&ROL==='docente'");pd.evaluate("ir('doc')");W(pd,"MOD==='doc'&&document.getElementById('cmBoxD').textContent.indexOf('Comunicados')>-1",20)
    td=pd.inner_text('#cmBoxD');ok('docente_ve_solo_los_suyos','Solo docentes' in td and 'Cierre de semestre' in td and 'Solo alumnos' not in td and 'Plan Pedagogía' not in td)
    pd.locator('#cmBoxD .pay:has-text("Solo docentes") [data-cml]').click();W(pd,"document.querySelector('#cmBoxD .pay') && document.querySelector('#cmBoxD').textContent.indexOf('✔ Leído')>-1");ok('docente_confirma_desde_su_vista',leidos(P2)['Solo docentes'] is True)
    # ---- la lista de Control escolar se actualiza con las lecturas ----
    pg.evaluate("COMR=null");pg.evaluate("cmRes()");W(pg,"COMR&&COMR.c3&&COMR.c3.leidos===2");ok('lecturas_se_actualizan',pg.evaluate("COMR.c3.leidos")==2)
    # ---- Control escolar con solo ver / otros no ven la pestaña ----
    pv=pagina(V1);pv.goto(B+'/');W(pv,"typeof APP!=='undefined'&&APP!==null&&S.length>=1");pv.evaluate("ir('esc')");W(pv,"MOD==='esc'");ok('escolar_ver_no_ve_la_pestana',pv.evaluate("[...document.querySelectorAll('#eTabs button')].filter(b=>!b.hidden&&b.dataset.et==='M').length")==0)
    pv.evaluate("etab('M')");ok('escolar_ver_no_entra_a_M',pv.evaluate("document.getElementById('eM').hidden"))
    pe=pagina(E1);pe.goto(B+'/');W(pe,"typeof APP!=='undefined'&&APP!==null&&S.length>=1");pe.evaluate("ir('esc')");W(pe,"MOD==='esc'");ok('escolar_editar_ve_la_pestana',pe.evaluate("[...document.querySelectorAll('#eTabs button')].filter(b=>!b.hidden&&b.dataset.et==='M').length")==1)
    pg.evaluate("ir('home')");W(pg,"MOD==='home'");pg.fill('#hBus','comunicado');pg.wait_for_timeout(300);ok('buscador_lo_encuentra','Comunicados generales' in pg.inner_text('#hBusR'))
    ok('respaldo_incluye_la_coleccion',pg.evaluate("BKCOL.indexOf('comunicados')>-1"))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
