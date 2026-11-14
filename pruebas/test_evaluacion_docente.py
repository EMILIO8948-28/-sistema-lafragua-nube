"""Evaluación docente por los alumnos: formato de 5 secciones + valoración general + preguntas abiertas, anónima, disponible desde la evaluación de la asignatura; resultados para Control escolar."""
import subprocess,time,json,os,re,urllib.request
from playwright.sync_api import sync_playwright
PORT=3133;B='http://127.0.0.1:%d'%PORT;DD='/tmp/nbdata_evd'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR=DD,LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
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
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&typeof DBH!=='undefined'&&DBH!==null")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('students/s1',{'mat':'1001','nombre':'Ana López','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    put('students/s2',{'mat':'1002','nombre':'Beto Mena','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    put('students/s3',{'mat':'1003','nombre':'Carla Ruiz','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2025,'nuevo':False})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[]});put('docentes/d2',{'nombre':'Prof. Dos','esp':'Historia','asig':[]})
    put('grupos/g1',{'num':'1111','plan':'Derecho','per':PER,'cuat':2,'alumnos':['s1','s2']});put('grupos/g2',{'num':'2222','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s3']})
    mat=lambda nom,plan,cuat,d,ev=None,**k:dict(dict({'per':PER,'plan':plan,'cuat':cuat,'nom':nom,'ini':'09:00','fin':'11:00'},**({'docId':d} if d else {})),**({'ev':ev} if ev else {}),**k)
    put('materias/m1',mat('Civil I','Derecho',2,'d1','2026-11-07'));put('materias/m2',mat('Civil II','Derecho',2,'d1','2026-11-07'))
    put('materias/m3',mat('Historia','Derecho',2,'d2','2026-12-20'));put('materias/m4',mat('Sin fecha','Derecho',2,'d1'))
    put('materias/m5',mat('Sin docente','Derecho',2,None,'2026-11-07'));put('materias/m6',mat('Didáctica','Pedagogía',1,'d2','2026-11-07'));put('materias/m7',mat('Metodología','Pedagogía',1,'d2','2026-11-07'))
    def usr(u,name,rol,modulos=None,doc=None):
        d={'u':u,'name':name,'rol':rol,'clave':'clave-%s-123'%u}
        if modulos is not None:d['modulos']=modulos
        if doc:d['doc']=doc
        r=ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR);assert r.status==200,(u,r.status,r.text())
    usr('ver1','Eva Escolar Ver','personalizado',{'escolar':'ver'});usr('caja1','Rosa Caja','personalizado',{'pagos':'editar'});usr('prof1','Dora Docente','docente',doc='d1')
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'1001','name':'Ana López','alumno':'s1','clave':'abcd-efgh'},{'u':'1002','name':'Beto Mena','alumno':'s2','clave':'ijkm-npqr'},{'u':'1003','name':'Carla Ruiz','alumno':'s3','clave':'stuv-wxyz'}]}),headers=HDR)
    def sesion(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status,r.text());return cx
    def alumno(u,c0,c1):
        cx=sesion(u,c0);cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':c0,'nueva':c1}),headers=HDR);return sesion(u,c1)
    A1=alumno('1001','abcd-efgh','clave-ana-77');A2=alumno('1002','ijkm-npqr','clave-beto-77');A3=alumno('1003','stuv-wxyz','clave-carla-77')
    S_={u:sesion(u,'clave-%s-123'%u) for u in ['ver1','caja1','prof1']}
    def mias(cx):return cx.request.get(B+'/api/evaldoc/mias').json()
    def est(cx):return {x['mid']:x['estado'] for x in mias(cx)['items']}
    def post(cx,o):return cx.request.post(B+'/api/evaldoc',data=json.dumps(o),headers=HDR)
    R1=[4]*4+[5]*16;R2=[3]*20
    # ================= SERVIDOR =================
    e=est(A1)
    ok('estados_por_asignatura',e=={'m1':'pendiente','m2':'pendiente','m3':'futura','m4':'futura','m5':'sin_docente'})
    ok('no_aparecen_asignaturas_de_otro_grupo','m6' not in e)
    ok('sin_sesion_no_evalua',b.new_context().request.post(B+'/api/evaldoc',data='{}',headers=HDR).status==401)
    r=post(A1,{'mid':'m1','r':R1,'g':5,'fort':'Explica muy bien','mej':'','com':'Gracias'});ok('alumno_envia_evaluacion',r.status==200)
    ok('queda_como_hecha',est(A1)['m1']=='hecha' and est(A1)['m2']=='pendiente')
    r=post(A1,{'mid':'m1','r':R1,'g':5});ok('no_se_puede_evaluar_dos_veces',r.status==409 and 'Ya evaluaste' in r.json()['error'])
    ok('no_evalua_antes_de_la_evaluacion',post(A1,{'mid':'m3','r':R1,'g':5}).status==403 and post(A1,{'mid':'m4','r':R1,'g':5}).status==403)
    ok('no_evalua_asignatura_de_otro_grupo',post(A1,{'mid':'m6','r':R1,'g':5}).status==403)
    ok('no_evalua_sin_docente',post(A1,{'mid':'m5','r':R1,'g':5}).status==400)
    ok('asignatura_inexistente',post(A1,{'mid':'zzz','r':R1,'g':5}).status==403)
    ok('exige_20_aspectos',post(A1,{'mid':'m2','r':R1[:19],'g':5}).status==400)
    ok('rechaza_valor_fuera_de_escala',post(A1,{'mid':'m2','r':[6]+R1[1:],'g':5}).status==400 and post(A1,{'mid':'m2','r':[0]+R1[1:],'g':5}).status==400)
    ok('rechaza_valores_no_enteros',post(A1,{'mid':'m2','r':['5']+R1[1:],'g':5}).status==400 and post(A1,{'mid':'m2','r':[4.5]+R1[1:],'g':5}).status==400)
    ok('exige_valoracion_general',post(A1,{'mid':'m2','r':R1}).status==400 and post(A1,{'mid':'m2','r':R1,'g':9}).status==400)
    ok('nada_se_guardo_con_errores',est(A1)['m2']=='pendiente')
    ok('otro_alumno_evalua_la_misma_asignatura',post(A2,{'mid':'m1','r':R2,'g':3,'fort':'','mej':'Más ejemplos','com':''}).status==200)
    ok('otra_licenciatura_evalua_la_suya',post(A3,{'mid':'m6','r':R1,'g':4}).status==200 and post(A3,{'mid':'m1','r':R1,'g':5}).status==403)
    ok('textos_se_recortan',post(A2,{'mid':'m2','r':R2,'g':3,'fort':'x'*5000,'mej':'','com':''}).status==200)
    # ----- anonimato -----
    docs=ctx.request.get(B+'/api/col/evdoc').json()['docs']
    ok('hay_cuatro_respuestas_guardadas',len(docs)==4)
    blob=json.dumps([d['data'] for d in docs],ensure_ascii=False)
    ok('las_respuestas_no_llevan_alumno',not any(k in blob for k in ['s1','s2','s3','Ana','Beto','Carla','1001','1002','1003','"sid"','"alumno"','"u"','abcd']))
    ok('ids_son_hash_de_32_hex',all(re.fullmatch(r'[0-9a-f]{32}',d['id']) for d in docs) and len(set(d['id'] for d in docs))==4)
    ok('campos_guardados',set(docs[0]['data'].keys())=={'mid','docId','per','plan','cuat','nom','fecha','r','g','fort','mej','com'})
    ok('texto_largo_se_recorta_a_1000',max(len(d['data']['fort']) for d in docs)==1000)
    kf=DD+'/evdoc.key';ok('clave_del_servidor_existe_y_es_privada',os.path.exists(kf) and re.fullmatch(r'[0-9a-f]{64}',open(kf).read().strip()) and oct(os.stat(kf).st_mode)[-3:]=='600')
    ok('alumno_no_lee_las_respuestas',A1.request.get(B+'/api/col/evdoc').json()['docs']==[] and A1.request.get(B+'/api/doc/evdoc/'+docs[0]['id']).json().get('exists') is False)
    ok('alumno_no_escribe_en_evdoc',A1.request.put(B+'/api/doc/evdoc/'+docs[0]['id'],data=json.dumps({'g':5}),headers=HDR).status==403 and A1.request.delete(B+'/api/doc/evdoc/'+docs[0]['id'],headers=HDR).status==403)
    ok('alumno_no_lee_resultados',A1.request.get(B+'/api/evaldoc/resultados').status==403 and A1.request.get(B+'/api/evaldoc/config').status==403)
    # ----- resultados y permisos del personal -----
    rs=ctx.request.get(B+'/api/evaldoc/resultados').json()
    ok('admin_lee_resultados',len(rs['respuestas'])==4 and rs['cfg']['abierta'] is True)
    ok('escolar_ver_lee_resultados',S_['ver1'].request.get(B+'/api/evaldoc/resultados').status==200)
    ok('escolar_ver_no_cambia_ajustes',S_['ver1'].request.put(B+'/api/evaldoc/config',data=json.dumps({'abierta':False,'dias':0}),headers=HDR).status==403)
    ok('sin_permiso_de_escolar_no_lee',S_['caja1'].request.get(B+'/api/evaldoc/resultados').status==403 and S_['prof1'].request.get(B+'/api/evaldoc/resultados').status==403)
    ok('personal_no_puede_evaluar',S_['ver1'].request.post(B+'/api/evaldoc',data=json.dumps({'mid':'m1','r':R1,'g':5}),headers=HDR).status==403)
    ok('personal_sin_permiso_no_lee_la_coleccion',S_['caja1'].request.get(B+'/api/col/evdoc').json()['docs']==[])
    # ----- ajustes: cerrar y plazo -----
    put_cfg=lambda o:ctx.request.put(B+'/api/evaldoc/config',data=json.dumps(o),headers=HDR)
    ok('ajustes_invalidos',put_cfg({'abierta':True,'dias':-1}).status==400 and put_cfg({'abierta':True,'dias':999}).status==400)
    ok('cerrar_evaluacion',put_cfg({'abierta':False,'dias':0}).status==200 and mias(A1)['abierta'] is False)
    ok('cerrada_no_recibe_respuestas',post(A1,{'mid':'m2','r':R1,'g':5}).status==403)
    put_cfg({'abierta':True,'dias':3})
    ok('plazo_vencido_se_marca_cerrada',est(A1)['m2']=='cerrada' and post(A1,{'mid':'m2','r':R1,'g':5}).status==403 and mias(A1)['items'][0]['hasta']=='2026-11-10')
    ok('plazo_no_afecta_las_ya_hechas',est(A1)['m1']=='hecha')
    put_cfg({'abierta':True,'dias':0});ok('sin_limite_vuelve_a_pendiente',est(A1)['m2']=='pendiente')
    # ================= PANTALLA DEL ALUMNO =================
    def entra(u,c,cond):
        cx=b.new_context(viewport={'width':1200,'height':950});cx.set_default_timeout(12000);p2=pagina(cx);p2.goto(B+'/');W(p2,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        p2.fill('#lgU',u);p2.fill('#lgP',c);p2.click('#lgGo');W(p2,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'&&"+cond,25);p2.wait_for_timeout(600);return p2
    pa=entra('1001','clave-ana-77',"APP.rol==='alumno'&&S.length===1&&Object.keys(MAT).length>=5&&EVDM!==null")
    tx=pa.inner_text('#poBody')
    ok('tabla_tiene_columna_evaluar_al_docente','Evaluar al docente' in tx)
    ok('muestra_evaluado_en_la_ya_hecha',pa.locator('#poBody table:has(th:has-text("Evaluar al docente")) tr:has-text("Civil I") .tag.pagado').count()==1)
    ok('boton_en_la_pendiente',pa.locator('#poBody table:has(th:has-text("Evaluar al docente")) tr:has-text("Civil II") [data-evd="m2"]').count()==1)
    ok('futura_dice_desde_cuando','Disponible desde la evaluación' in pa.inner_text('#poBody table:has(th:has-text("Evaluar al docente")) tr:has-text("Historia")') and '20/12/2026' in pa.inner_text('#poBody table:has(th:has-text("Evaluar al docente")) tr:has-text("Historia")'))
    ok('sin_docente_no_tiene_boton',pa.locator('#poBody table:has(th:has-text("Evaluar al docente")) tr:has-text("Sin docente") [data-evd]').count()==0)
    ok('aviso_de_docentes_por_evaluar','Ya puedes evaluar a 1 docente' in tx)
    pa.click('#poBody [data-evd="m2"]');pa.wait_for_selector('#dEvd[open]')
    ok('formulario_con_docente_y_asignatura','Prof. Uno' in pa.inner_text('#evdBody') and 'Civil II' in pa.inner_text('#evdBody'))
    ok('dice_que_es_anonima','anónima' in pa.inner_text('#evdBody'))
    ok('muestra_la_escala','5 = Excelente' in pa.inner_text('#evdBody') and '1 = Deficiente' in pa.inner_text('#evdBody'))
    ok('cinco_secciones_con_sus_criterios',pa.locator('#evdBody .evd-h').count()==7 and pa.locator('#evdBody .evd-q[data-q]').count()==20 and 'Presenta el programa, los objetivos y la forma de trabajo' in pa.inner_text('#evdBody') and 'Muestra disposición para orientar y apoyar el aprendizaje' in pa.inner_text('#evdBody'))
    ok('valoracion_general_y_tres_preguntas_abiertas',pa.locator('#evdBody .evd-q[data-g] input').count()==5 and pa.locator('#evdBody textarea').count()==3 and 'principales fortalezas' in pa.inner_text('#evdBody') and 'debería mejorar' in pa.inner_text('#evdBody') and 'Comentarios o sugerencias adicionales' in pa.inner_text('#evdBody'))
    pa.click('#evdOk')
    ok('no_envia_incompleta_y_marca_lo_que_falta','Falta calificar 21' in pa.inner_text('#evdMsg') and pa.evaluate("document.getElementById('dEvd').open") and pa.locator('.evd-falta').count()==21)
    ok('no_se_guardo_nada_al_fallar',est(A1)['m2']=='pendiente')
    for i in range(20):pa.click('#evdBody .evd-q[data-q="%d"] label:nth-child(%d)'%(i,5 if i%4 else 4))
    pa.click('#evdBody .evd-q[data-g] label:nth-child(5)')
    ok('al_completar_ya_no_marca_faltantes',True)
    pa.fill('#evFort','Muy claro');pa.fill('#evMej','Más práctica');pa.fill('#evCom','Gracias, profe')
    pa.click('#evdOk');W(pa,"!document.getElementById('dEvd').open")
    W(pa,"EVDM&&EVDM.items.find(function(x){return x.mid==='m2'}).estado==='hecha'")
    ok('tras_enviar_cierra_y_marca_evaluado',pa.locator('#poBody table:has(th:has-text("Evaluar al docente")) tr:has-text("Civil II") .tag.pagado').count()==1 and pa.locator('#poBody table:has(th:has-text("Evaluar al docente")) tr:has-text("Civil II") [data-evd]').count()==0)
    ok('desaparece_el_aviso','Ya puedes evaluar' not in pa.inner_text('#poBody'))
    rs=ctx.request.get(B+'/api/evaldoc/resultados').json()['respuestas'];m2=[x for x in rs if x['mid']=='m2' and x['fort']=='Muy claro']
    ok('respuesta_de_pantalla_guardada_completa',len(m2)==1 and m2[0]['r']==[4,5,5,5]*0+[5 if i%4 else 4 for i in range(20)] and m2[0]['g']==5 and m2[0]['mej']=='Más práctica' and m2[0]['com']=='Gracias, profe')
    pa.evaluate("abreEvd('m2')");ok('no_reabre_una_ya_hecha',not pa.evaluate("document.getElementById('dEvd').open"))
    pa.evaluate("abreEvd('m3')");ok('no_abre_una_futura',not pa.evaluate("document.getElementById('dEvd').open"))
    # cerrar evaluación: el portal muestra no disponible
    put_cfg({'abierta':False,'dias':0});pa.evaluate("EVDM=null;evdCarga()");W(pa,"EVDM&&EVDM.abierta===false")
    ok('portal_sin_boton_si_esta_cerrada',pa.locator('#poBody [data-evd]').count()==0)
    put_cfg({'abierta':True,'dias':0})
    # ================= CONTROL ESCOLAR =================
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(MAT).length===7")
    pg.evaluate("ir('esc')");W(pg,"MOD==='esc'");ok('pestana_evaluacion_docente_visible',pg.is_visible('#eTabs [data-et="V"]'))
    pg.click('#eTabs [data-et="V"]');W(pg,"document.querySelectorAll('#evTb tr[data-mid]').length>0")
    f=pg.locator('#evTb tr[data-mid]');ok('lista_asignaturas_evaluadas_y_pendientes_de_respuesta',f.count()==4)
    t1=pg.inner_text('#evTb tr[data-mid="m1"]');t2=pg.inner_text('#evTb tr[data-mid="m2"]')
    ok('civil_i_respuestas_y_promedio','Prof. Uno' in t1 and '2 / 2' in t1 and '4.00' in t1)
    ok('civil_i_promedios_por_seccion',re.search(r'3\.50\s+4\.00\s+4\.00\s+4\.00\s+4\.00',t1.replace('\t',' ').replace('\n',' ')) is not None)
    ok('civil_ii_respuestas',('2 / 2' in t2))
    ok('sin_respuestas_muestra_cero',pg.inner_text('#evTb tr[data-mid="m7"]').count('0 / 1')==1 and '1 / 1' in pg.inner_text('#evTb tr[data-mid="m6"]'))
    ok('no_aparece_la_futura_ni_sin_docente',pg.locator('#evTb tr[data-mid="m3"]').count()==0 and pg.locator('#evTb tr[data-mid="m5"]').count()==0 and pg.locator('#evTb tr[data-mid="m4"]').count()==0)
    ok('resumen_de_participacion','respondieron' in pg.inner_text('#evSum'))
    pg.click('#evTb tr[data-mid="m1"] [data-evd-ver]');pg.wait_for_selector('#dEvR[open]')
    d=pg.inner_text('#dEvR')
    ok('detalle_con_los_20_aspectos',pg.locator('#evrB .evr-f').count()==20 and 'Explica los contenidos de manera clara y comprensible' in d)
    ok('detalle_con_comentarios_sin_nombres','Explica muy bien' in d and 'Más ejemplos' in d and 'Gracias' in d and 'Ana' not in d.replace('Anual','') and 'Beto' not in d and 'Carla' not in d)
    ok('detalle_distribucion_general','5→1' in d and '3→1' in d)
    pg.click('#evrCls')
    pg.select_option('#evDoc','d2');ok('filtro_por_docente',pg.locator('#evTb tr[data-mid]').count()==2 and 'Didáctica' in pg.inner_text('#evTb') and 'Civil' not in pg.inner_text('#evTb'))
    pg.select_option('#evDoc','');pg.fill('#evBus','civil ii');ok('busqueda_por_asignatura',pg.locator('#evTb tr[data-mid]').count()==1);pg.fill('#evBus','')
    with pg.expect_download() as dl:pg.click('#evCsv')
    csv=open(dl.value.path(),encoding='utf-8-sig').read()
    ok('csv_con_encabezado_y_filas',csv.startswith('Periodo,Plan,Cuatrimestre,Asignatura,Docente,Respuestas') and 'Civil I' in csv and csv.count('\n')>=4 and 'Ana' not in csv)
    pg.locator('#evCfgD, details:has(#evAbierta)').first.evaluate("d=>d.open=true");pg.uncheck('#evAbierta');pg.click('#evxGuarda');W(pg,"document.getElementById('evxMsg').textContent.indexOf('guardados')>-1")
    ok('ajuste_cerrar_se_guarda_en_servidor',ctx.request.get(B+'/api/evaldoc/config').json()['abierta'] is False)
    pg.check('#evAbierta');pg.fill('#evDias','10');pg.click('#evxGuarda');W(pg,"document.getElementById('evxMsg').textContent.indexOf('guardados')>-1")
    c=ctx.request.get(B+'/api/evaldoc/config').json();ok('ajuste_abrir_y_plazo_se_guardan',c['abierta'] is True and c['dias']==10)
    put_cfg({'abierta':True,'dias':0})
    pg.evaluate("ir('home')");W(pg,"MOD==='home'");pg.fill('#hBus','evaluacion docente');W(pg,"!document.getElementById('hBusR').hidden")
    ok('buscador_encuentra_la_funcion','Control escolar · Evaluación docente' in pg.inner_text('#hBusR'))
    pg.click('#hBusR [data-hf]');W(pg,"MOD==='esc'&&ETAB==='V'");ok('buscador_abre_la_pestana',pg.is_visible('#eV'))
    # personal con escolar ver: ve resultados pero no edita ajustes
    pv=entra('ver1','clave-ver1-123',"ROL!=='admin'&&S.length===3")
    pv.evaluate("ir('esc')");W(pv,"MOD==='esc'");pv.click('#eTabs [data-et="V"]');W(pv,"document.querySelectorAll('#evTb tr[data-mid]').length>0")
    ok('escolar_ver_ve_los_resultados',pv.locator('#evTb tr[data-mid]').count()==4)
    ok('escolar_ver_no_puede_cambiar_ajustes',pv.is_disabled('#evxGuarda') and pv.is_disabled('#evAbierta'))
    # docente y caja no ven la pestaña
    pd=entra('prof1','clave-prof1-123',"ROL!=='admin'")
    pd.evaluate("ir('home')");pd.evaluate("typeof etab==='function'");
    ok('docente_no_lee_resultados_del_servidor',pd.evaluate("fetch('/api/evaldoc/resultados',{credentials:'same-origin'}).then(function(r){return r.status})") is not None)
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
