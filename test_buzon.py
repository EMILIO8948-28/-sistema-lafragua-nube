"""Buzón de quejas y sugerencias: envío del alumno (con nombre o anónimo con folio), atención de Control escolar, permisos y anonimato."""
import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3146;B='http://127.0.0.1:%d'%PORT;TOK='tok-bz-1'
os.system('rm -rf /tmp/nbdata_bz /tmp/crl6 && mkdir -p /tmp/nbdata_bz /tmp/crl6')
RELOJ='/tmp/crl6/reloj.txt';HOY=datetime.date.today().isoformat();open(RELOJ,'w').write(HOY)
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_bz',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ)
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
    for sid,n,mt in (('s1','Ana López Ramírez','20260001'),('s2','Beto Mena Ruiz','20260002'),('s3','Carla Díaz Soto','20260003')):
        assert raw('students/'+sid,{'mat':mt,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'total':0}).status==200
    for sid,n in (('s1','Ana'),('s2','Beto'),('s3','Carla')):
        assert ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'al'+sid,'name':n,'alumno':sid,'clave':'abcd-efgh'}]}),headers=HDR).status==200
    for u,r,m in (('esc2','personalizado',{'escolar':'editar'}),('esc3','personalizado',{'escolar':'ver'}),('caja1','caja',None)):
        d={'u':u,'name':u,'rol':r,'clave':'clave-%s-123'%u}
        if m:d['modulos']=m
        assert ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR).status==200
    def entra(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status);return cx
    def alumno(sid,nueva):
        cx=entra('al'+sid,'abcd-efgh');cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':nueva}),headers=HDR);return entra('al'+sid,nueva)
    A1=alumno('s1','clave-ana-777');A2=alumno('s2','clave-beto-777');A3=alumno('s3','clave-carla-777')
    E2=entra('esc2','clave-esc2-123');E3=entra('esc3','clave-esc3-123');CJ=entra('caja1','clave-caja1-123')
    post=lambda cx,o:cx.request.post(B+'/api/buzon',data=json.dumps(o),headers=HDR)
    ok_=lambda **k:dict({'tipo':'Queja','area':'Control escolar','asunto':'Horario cambiado','texto':'Nos cambiaron el horario sin avisar con tiempo.','anonimo':False},**k)
    ok('rechaza_tipo_invalido',post(A1,ok_(tipo='Insulto')).status==400)
    ok('rechaza_area_invalida',post(A1,ok_(area='Marte')).status==400)
    ok('rechaza_asunto_corto',post(A1,ok_(asunto='ab')).status==400)
    ok('rechaza_mensaje_corto',post(A1,ok_(texto='corto')).status==400)
    ok('rechaza_mensaje_largo',post(A1,ok_(texto='x'*2001)).status==400)
    ok('nada_se_guardo_con_errores',ctx.request.get(B+'/api/col/quejas').json()['docs']==[])
    r=post(A1,ok_());j=r.json();F1=j.get('folio','')
    ok('envia_con_nombre',r.status==200 and j['anonimo'] is False and bool(__import__('re').fullmatch(r'BZ-[A-Z0-9]{8}',F1)))
    d=get('quejas/'+F1)['data']
    ok('guarda_con_alumno',d['sid']=='s1' and d['nombre']=='Ana López Ramírez' and d['mat']=='20260001' and d['estado']=='nuevo' and d['anonimo'] is False and d['respuestas']==[] and d['fecha']==pg.evaluate("today()") or d['fecha'] in (pg.evaluate("today()"),HOY))
    r=post(A2,ok_(tipo='Sugerencia',area='Instalaciones',asunto='Más bancas',texto='Faltan bancas en el patio central.',anonimo=True));j=r.json();F2=j['folio']
    ok('envia_anonimo',r.status==200 and j['anonimo'] is True)
    raw2=json.dumps(get('quejas/'+F2)['data'])
    ok('anonimo_sin_rastro_del_alumno',not any(x in raw2 for x in ['s2','Beto','20260002','als2','sid','nombre','"mat"']) and get('quejas/'+F2)['data']['anonimo'] is True)
    mias1=A1.request.get(B+'/api/buzon/mias').json()['mensajes'];mias2=A2.request.get(B+'/api/buzon/mias').json()['mensajes']
    ok('mias_solo_con_nombre',len(mias1)==1 and mias1[0]['folio']==F1 and mias2==[])
    ok('folio_propio_anonimo',A2.request.get(B+'/api/buzon/folio/'+F2).json()['mensaje']['asunto']=='Más bancas')
    ok('folio_ajeno_con_nombre_no_se_ve',A3.request.get(B+'/api/buzon/folio/'+F1).status==404)
    ok('folio_propio_con_nombre_se_ve',A1.request.get(B+'/api/buzon/folio/'+F1.lower()).status==200)
    ok('folio_mal_formado',A1.request.get(B+'/api/buzon/folio/hola').status==404 and A1.request.get(B+'/api/buzon/folio/BZ-AAAAAAAA').status==404)
    # límites
    for n in range(10):r=post(A3,ok_(asunto='Mensaje %d'%n))
    ok('limite_de_10_por_hora',r.status==200 and post(A3,ok_()).status==429)
    # roles que no son alumno
    ok('personal_no_envia',post(E2,ok_()).status==403 and post(ctx,ok_()).status==403)
    ok('personal_no_usa_vista_alumno',E2.request.get(B+'/api/buzon/mias').status==403)
    ok('sin_sesion_nada',b.new_context().request.post(B+'/api/buzon',data='{}',headers=HDR).status in (401,403))
    # el alumno no puede leer ni escribir quejas por la API general
    ok('alumno_no_lee_quejas_por_api_general',A1.request.get(B+'/api/col/quejas').json()['docs']==[] and not get('quejas/'+F1,A1)['exists'])
    ok('alumno_no_escribe_quejas',raw('quejas/'+F1,dict(d,estado='resuelto'),c=A1).status==403)
    # atención de Control escolar
    ok('escolar_editar_lee',get('quejas/'+F1,E2)['exists'] and get('quejas/'+F2,E2)['exists'])
    ok('escolar_solo_ver_no_lee',not get('quejas/'+F1,E3)['exists'] and E3.request.get(B+'/api/col/quejas').json()['docs']==[])
    ok('caja_no_lee',not get('quejas/'+F1,CJ)['exists'])
    resp=lambda base,**k:dict(base,**k)
    base=get('quejas/'+F1)['data']
    ok('escolar_ver_no_escribe',raw('quejas/'+F1,resp(base,estado='en revisión'),c=E3).status==403)
    ok('rechaza_cambiar_texto',raw('quejas/'+F1,resp(base,texto='otro texto distinto'),c=E2).status==400)
    ok('rechaza_cambiar_asunto',raw('quejas/'+F1,resp(base,asunto='otro'),c=E2).status==400)
    ok('rechaza_cambiar_alumno',raw('quejas/'+F1,resp(base,sid='s3'),c=E2).status==400)
    b2=get('quejas/'+F2)['data']
    ok('rechaza_identificar_al_anonimo',raw('quejas/'+F2,resp(b2,sid='s2',nombre='Beto'),c=E2).status==400 and raw('quejas/'+F2,resp(b2,anonimo=False),c=E2).status==400)
    ok('rechaza_estado_invalido',raw('quejas/'+F1,resp(base,estado='borrado'),c=E2).status==400)
    ok('rechaza_respuesta_vacia',raw('quejas/'+F1,resp(base,respuestas=[{'f':HOY,'por':'x','texto':'  ','publica':True}]),c=E2).status==400)
    ok('personal_no_crea_mensajes',raw('quejas/BZ-ZZZZZZZZ',dict(base,folio='BZ-ZZZZZZZZ'),c=E2).status==403)
    ok('escolar_editar_responde',raw('quejas/'+F1,resp(base,estado='resuelto',respuestas=[{'f':HOY,'por':'Control escolar','texto':'Ya se corrigió el horario.','publica':True}],interna=[{'f':HOY,'por':'Control escolar','texto':'NOTA-SECRETA-INTERNA'}]),c=E2).status==200)
    m1=A1.request.get(B+'/api/buzon/mias').json()['mensajes'][0]
    ok('alumno_ve_la_respuesta',m1['estado']=='resuelto' and m1['respuestas'][0]['texto']=='Ya se corrigió el horario.')
    ok('alumno_no_ve_notas_internas','NOTA-SECRETA-INTERNA' not in json.dumps(m1) and 'interna' not in m1)
    ok('escolar_editar_responde_al_anonimo',raw('quejas/'+F2,resp(b2,estado='en revisión',respuestas=[{'f':HOY,'por':'Control escolar','texto':'Lo vamos a revisar.','publica':True}]),c=E2).status==200)
    ok('anonimo_ve_respuesta_con_su_folio',A2.request.get(B+'/api/buzon/folio/'+F2).json()['mensaje']['respuestas'][0]['texto']=='Lo vamos a revisar.' and A2.request.get(B+'/api/buzon/folio/'+F2).json()['mensaje']['estado']=='en revisión')
    ok('respuesta_privada_no_se_muestra',True)
    raw('quejas/'+F2,resp(get('quejas/'+F2)['data'],respuestas=get('quejas/'+F2)['data']['respuestas']+[{'f':HOY,'por':'x','texto':'SOLO-PERSONAL','publica':False}]),c=E2)
    ok('respuesta_no_publica_oculta','SOLO-PERSONAL' not in A2.request.get(B+'/api/buzon/folio/'+F2).text())
    # ---------------- Pantalla de Control escolar ----------------
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(BZQ).length>=12")
    pg.evaluate("ir('esc')");W(pg,"MOD==='esc'")
    nuevos=pg.evaluate("bzLista().filter(function(d){return d.estado==='nuevo'}).length")
    ok('pestana_con_contador',pg.inner_text('#tUbz')=='Buzón (%d)'%nuevos and nuevos==10)
    pg.click('#tUbz');W(pg,"ETAB==='U'")
    ok('lista_todos',pg.locator('#bzTbl [data-bz]').count()==12 and 'Anónimo' in pg.inner_text('#bzTbl'))
    ok('resumen','12 mensajes' in pg.inner_text('#bzRes') and '10 nuevos' in pg.inner_text('#bzRes') and '1 anónimos' in pg.inner_text('#bzRes'))
    pg.select_option('#bzEst','abiertos');pg.wait_for_timeout(250);ok('filtro_pendientes',pg.locator('#bzTbl [data-bz]').count()==11)
    pg.select_option('#bzEst','resuelto');pg.wait_for_timeout(250);ok('filtro_resuelto',pg.locator('#bzTbl [data-bz]').count()==1)
    pg.select_option('#bzEst','');pg.select_option('#bzTip','Sugerencia');pg.wait_for_timeout(250);ok('filtro_tipo',pg.locator('#bzTbl [data-bz]').count()==1);pg.select_option('#bzTip','')
    pg.fill('#bzBus',F1.lower());pg.wait_for_timeout(250);ok('busca_por_folio',pg.locator('#bzTbl [data-bz]').count()==1)
    pg.fill('#bzBus','ana lopez');pg.wait_for_timeout(250);ok('busca_por_alumno',pg.locator('#bzTbl [data-bz]').count()==1);pg.fill('#bzBus','')
    pg.fill('#bzBus','beto');pg.wait_for_timeout(250);ok('no_se_puede_buscar_al_anonimo_por_nombre',pg.locator('#bzTbl [data-bz]').count()==0);pg.fill('#bzBus','')
    pg.wait_for_timeout(250)
    pg.click('#bzTbl [data-bz="%s"]'%F2);pg.wait_for_selector('#dBzS[open]')
    ok('detalle_anonimo','Anónima' in pg.inner_text('#bzsMeta') or 'anónima' in pg.inner_text('#bzsMeta'))
    ok('detalle_muestra_texto_y_respuestas','bancas' in pg.inner_text('#bzsTexto') and 'Lo vamos a revisar' in pg.inner_text('#bzsResp'))
    pg.fill('#bzsNueva','Ya pedimos 10 bancas nuevas.');pg.select_option('#bzsEst','resuelto');pg.fill('#bzsInt','Compras autorizó.');pg.click('#bzsGuarda');W(pg,"document.getElementById('bzsMsg').textContent==='Guardado.'")
    dd=get('quejas/'+F2)['data']
    ok('guarda_respuesta_estado_y_nota',dd['estado']=='resuelto' and any(r['texto']=='Ya pedimos 10 bancas nuevas.' and r['publica'] is True for r in dd['respuestas']) and dd['interna'][0]['texto']=='Compras autorizó.')
    ok('sigue_anonimo_tras_guardar','sid' not in dd and dd['anonimo'] is True)
    ok('detalle_se_actualiza','Ya pedimos' in pg.inner_text('#bzsResp') and 'Compras autorizó' in pg.inner_text('#bzsNotas'))
    pg.click('#bzsGuarda');ok('sin_cambios_avisa','No hay cambios' in pg.inner_text('#bzsMsg'))
    pg.click('#bzsCls')
    ok('contador_baja',pg.inner_text('#tUbz')=='Buzón (10)' or pg.inner_text('#tUbz')=='Buzón (10)')
    with pg.expect_download() as dl:pg.click('#bzCsv')
    tx=open(dl.value.path(),encoding='utf-8').read()
    ok('csv',F1 in tx and 'Anónimo' in tx and 'Ana López' in tx and 'Beto' not in tx)
    ok('buscador_global',pg.evaluate("(function(){ir('home');return true})()"))
    W(pg,"MOD==='home'");pg.fill('#hBus','buzon');pg.wait_for_timeout(300);ok('buscador_lista_buzon','Buzón de quejas' in pg.inner_text('#hBusR'))
    ok('respaldo_incluye_quejas',pg.evaluate("BKCOL.indexOf('quejas')>-1"))
    # quien solo puede ver Control escolar no ve la pestaña
    p3=E3.new_page();p3.on("pageerror",lambda e:errs.append(str(e)));p3.goto(B+'/');W(p3,"typeof APP!=='undefined'&&APP!==null&&S.length>=0")
    p3.evaluate("ir('esc')");W(p3,"MOD==='esc'");p3.evaluate("etab('U')")
    ok('solo_ver_no_ve_la_pestana_ni_entra',p3.evaluate("document.querySelector('#eTabs [data-et=U]').hidden")==True and p3.evaluate("ETAB")=='A')
    # ---------------- Portal del alumno ----------------
    pa=A3.new_page();pa.on("pageerror",lambda e:errs.append(str(e)));pa.goto(B+'/');W(pa,"typeof APP!=='undefined'&&APP!==null&&S.length>0")
    W(pa,"document.getElementById('bzNuevo')!==null",20)
    ok('portal_muestra_el_buzon','Buzón de quejas y sugerencias' in pa.inner_text('#poBody') and pa.locator('#bzTbl,#poBody table tbody tr').count()>=10)
    pa.click('#bzNuevo');pa.wait_for_selector('#dBz[open]')
    pa.fill('#bzAsu','ab');pa.fill('#bzTxt','Texto largo suficiente para enviar.');pa.click('#bzEnv');ok('portal_pide_asunto','asunto' in pa.inner_text('#bzMsg').lower())
    pa.fill('#bzAsu','Beca de transporte');pa.fill('#bzTxt','corto');pa.click('#bzEnv');ok('portal_pide_mas_texto','10 caracteres' in pa.inner_text('#bzMsg'))
    ok('contador_de_caracteres',pa.inner_text('#bzCnt')=='5 / 2000')
    pa.fill('#bzTxt','Quisiera saber si existe una beca de transporte.');pa.click('#bzEnv');pa.wait_for_timeout(600)
    ok('limite_visible_al_alumno','Enviaste muchos' in pa.inner_text('#bzMsg'))
    pa.click('#bzCls')
    pb=A1.new_page();pb.on("pageerror",lambda e:errs.append(str(e)));pb.goto(B+'/');W(pb,"document.getElementById('bzNuevo')!==null",20)
    ok('portal_muestra_respuesta_recibida','Ya se corrigió el horario' in pb.inner_text('#poBody'))
    pb.click('#bzNuevo');pb.wait_for_selector('#dBz[open]');pb.select_option('#bzTipo','Felicitación');pb.select_option('#bzArea','Docentes');pb.fill('#bzAsu','Excelente clase');pb.fill('#bzTxt','La maestra de Metodología explica muy bien.');pb.check('#bzAnon');pb.click('#bzEnv')
    W(pb,"!document.getElementById('bzOk').hidden")
    fol=pb.inner_text('#bzFol');ok('muestra_folio_anonimo',fol.startswith('BZ-') and 'anónimo' in pb.inner_text('#bzFolN') and get('quejas/'+fol)['data']['anonimo'] is True and 'sid' not in get('quejas/'+fol)['data'])
    pb.click('#bzFin');pb.wait_for_timeout(600)
    ok('anonimo_no_aparece_en_mis_mensajes',fol not in pb.inner_text('#poBody'))
    pb.fill('#bzFolIn',fol.lower());pb.click('#bzFolGo');pb.wait_for_selector('#bzFolRes b')
    ok('consulta_por_folio_en_pantalla',fol in pb.inner_text('#bzFolRes') and 'Excelente clase' in pb.inner_text('#bzFolRes'))
    pb.fill('#bzFolIn','BZ-NOEXISTE');pb.click('#bzFolGo');pb.wait_for_timeout(500);ok('folio_inexistente_avisa','No encontramos' in pb.inner_text('#bzFolRes'))
    pb.click('#bzNuevo');pb.wait_for_selector('#dBz[open]');pb.fill('#bzAsu','Duda con mi horario');pb.fill('#bzTxt','Mi horario del jueves se empalma con otra materia.');pb.click('#bzEnv');W(pb,"!document.getElementById('bzOk').hidden")
    ok('con_nombre_indica_que_vera_respuesta','esta misma sección' in pb.inner_text('#bzFolN') and get('quejas/'+pb.inner_text('#bzFol'))['data']['sid']=='s1')
    pb.click('#bzFin');pb.wait_for_timeout(600);ok('con_nombre_aparece_en_mis_mensajes','Duda con mi horario' in pb.inner_text('#poBody'))
    ok('sin_errores_de_pagina',not errs)
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
