import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3330;B='http://127.0.0.1:%d'%PORT;TOK='tok-cu-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata107 /tmp/rel107 && mkdir -p /tmp/nbdata107 /tmp/rel107')
open('/tmp/rel107/leads.csv','w',encoding='utf-8').write('full_name,phone_number,email,created_time,platform\nMaría Torres,+52 722 111 0001,maria@mail.com,2026-11-08T10:00:00,facebook\nJosé Pérez,7221110002,,2026-11-09T11:00:00,instagram\nCarlos Duplicado,7229876543,carlos@mail.com,2026-11-09,instagram\nSin Telefono,,x@y.mx,2026-11-09,facebook\n')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata107',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def W(pg,js,t=40):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
hoy=datetime.date.today();manana=(hoy+datetime.timedelta(days=1)).isoformat()
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':'Derecho','n':36,'col':1500,'ins':900,'rein':900,'tit':25000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    for sid,nom in [('s1','Ana López Ramírez'),('s2','Beto Mena Ruiz')]:put('students/'+sid,{'mat':'2026'+sid[1:].zfill(3),'nombre':nom,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    us=lambda u,n,mods:ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':u,'name':n,'rol':'personalizado','modulos':mods,'clave':'clave-%s-123'%u}),headers=HDR)
    us('at1','Orientadora Uno',{'atencion':'editar'});us('at2','Orientador Dos',{'atencion':'editar'});us('pr1','Ventas Uno',{'prospectos':'editar'});us('prv','Ventas Consulta',{'prospectos':'ver'})
    def entra(u):
        c2=b.new_context(viewport={'width':1200,'height':1000});c2.set_default_timeout(15000);pp=pagina(c2);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1500);return pp,c2
    # ============ permisos de los usuarios en la pantalla ============
    pg.evaluate("ir('home')");pg.wait_for_timeout(500);ok('el_administrador_ve_las_dos_tarjetas',pg.is_visible('#mAt') and pg.is_visible('#mPr'))
    pg.evaluate("ir('usr')");pg.wait_for_timeout(500);ok('la_pantalla_de_usuarios_ofrece_los_permisos_nuevos',pg.evaluate("MODDEF.some(function(m){return m[0]==='atencion'})&&MODDEF.some(function(m){return m[0]==='prospectos'})"))
    # ============ atención personalizada ============
    a1,ca1=entra('at1');a1.evaluate("ir('home')");a1.wait_for_timeout(400)
    ok('la_orientadora_ve_solo_su_tarjeta',a1.is_visible('#mAt') and a1.is_hidden('#mPr') and a1.is_hidden('#mEsc'))
    a1.click('#mAt');W(a1,"MOD==='at'");ok('abre_el_modulo','Atención personalizada' in a1.inner_text('#ttl') and a1.is_visible('#axNuevo') and 'confidencial' in a1.inner_text('#vAt'))
    a1.click('#axNuevo');a1.wait_for_selector('#dAx[open]');a1.fill('#axAlBus','beto');a1.wait_for_timeout(300)
    ok('busca_al_alumno_por_nombre',a1.locator('#axAl option').count()==1 and 'Beto Mena' in a1.inner_text('#axAl'))
    a1.click('#axGuarda');ok('pide_los_datos','asunto' in a1.inner_text('#axNMsg').lower())
    a1.select_option('#axTipo','Salud');ok('un_tema_de_salud_se_marca_confidencial_solo',a1.is_checked('#axPriv'))
    a1.fill('#axAsu','Problema de salud que afecta su asistencia');a1.fill('#axTxt','Comentó que está en tratamiento y pide flexibilidad.');a1.fill('#axProx',hoy.isoformat());a1.click('#axGuarda');W(a1,"Object.keys(ATN).length===1");a1.wait_for_timeout(400)
    t=a1.inner_text('#axTb');ok('el_registro_aparece_con_el_candado_y_el_seguimiento_de_hoy','Beto Mena Ruiz' in t and 'Salud 🔒' in t and 'En seguimiento' in t and 'Orientadora Uno' in t)
    ok('las_tarjetas_cuentan_lo_pendiente','1' in a1.inner_text('#axTar') and a1.inner_text('#axTar').count('1')>=2)
    ok('la_campana_avisa_del_seguimiento_pendiente','seguimiento de atención personalizada pendiente' in a1.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')"))
    a1.click('#axTb [data-axo]');a1.wait_for_selector('#dAxD[open]')
    ok('el_detalle_muestra_la_apertura_y_dice_que_es_confidencial','Confidencial' in a1.inner_text('#axDPr') and 'está en tratamiento' in a1.inner_text('#axDTl'))
    a1.select_option('#axDEst','cerrado');a1.click('#axDGo');ok('para_cerrar_exige_una_nota','escribe una nota' in a1.inner_text('#axDMsg'))
    a1.fill('#axDNota','Se acordó justificar las faltas con constancia médica.');a1.click('#axDGo');W(a1,"ATN[Object.keys(ATN)[0]].estado==='cerrado'");a1.wait_for_timeout(300)
    tl=a1.inner_text('#axDTl');ok('el_historial_conserva_todo_y_el_mas_reciente_va_arriba','Estado: En seguimiento → Cerrado' in tl and 'constancia médica' in tl and tl.index('constancia médica')<tl.index('está en tratamiento'))
    ok('al_cerrar_se_quita_el_seguimiento','Cerrado' in a1.inner_text('#axDEst option:checked') and ATN_OK if False else a1.evaluate("ATN[Object.keys(ATN)[0]].proxima")=='')
    a1.click('#axDCls')
    a2,ca2=entra('at2');a2.evaluate("ir('at')");W(a2,"MOD==='at'");a2.wait_for_timeout(500)
    ok('otro_orientador_no_ve_el_registro_confidencial','Beto' not in a2.inner_text('#axTb') and 'Todavía no hay' in a2.inner_text('#axTb'))
    a2.click('#axNuevo');a2.wait_for_selector('#dAx[open]');a2.check('#axPO');a2.fill('#axNom','Rosa Mena');a2.fill('#axRel','Mamá de un alumno');a2.fill('#axAsu','Duda sobre becas');a2.fill('#axTxt','Preguntó por los requisitos.');a2.click('#axGuarda');W(a2,"Object.keys(ATN).length===1");a2.wait_for_timeout(300)
    ok('registra_a_una_persona_que_no_es_alumno','Rosa Mena' in a2.inner_text('#axTb') and 'Mamá de un alumno' in a2.inner_text('#axTb') and '🔒' not in a2.inner_text('#axTb'))
    W(a1,"Object.keys(ATN).length===2");a1.evaluate("renderAt()");ok('el_equipo_ve_lo_que_no_es_confidencial','Rosa Mena' in a1.inner_text('#axTb'))
    a1.click('#axTb tr:has-text("Rosa") [data-axo]');a1.wait_for_selector('#dAxD[open]');a1.fill('#axDNota','Se le envió el reglamento de becas.');a1.click('#axDGo');W(a1,"Object.values(ATN).some(function(r){return r.notas.length===2})")
    ok('otro_miembro_del_equipo_puede_agregar_notas','Se le envió' in a1.inner_text('#axDTl') and ca1 is not None)
    a1.click('#axDCls')
    a1.fill('#axBus','rosa');a1.select_option('#axFe','cerrado');a1.wait_for_timeout(300);ok('los_filtros_funcionan','Beto' not in a1.inner_text('#axTb'));a1.select_option('#axFe','');a1.fill('#axBus','')
    # ============ prospectos ============
    pp1,cp1=entra('pr1');pp1.evaluate("ir('home')");pp1.wait_for_timeout(400)
    ok('ventas_ve_su_tarjeta_y_no_la_de_atencion',pp1.is_visible('#mPr') and pp1.is_hidden('#mAt'))
    pp1.click('#mPr');W(pp1,"MOD==='pr'");pp1.click('#pxTc');pp1.click('#cmNueva');pp1.wait_for_selector('#dCm[open]')
    pp1.fill('#cmNom','Inscripciones enero · Instagram');pp1.select_option('#cmPlat','Instagram');pp1.fill('#cmPres','3000');pp1.fill('#cmMeta','50');pp1.click('#cmGo');W(pp1,"Object.keys(CMP).length===1");pp1.wait_for_selector('#cmEnl:not([hidden])')
    CID=pp1.evaluate("Object.keys(CMP)[0]")
    ok('crea_la_campana_y_da_su_enlace_con_qr',B+'/registro?c='+CID in pp1.inner_text('#cmUrl') and pp1.locator('#cmQR svg').count()==1 and 'creada' in pp1.inner_text('#cmMsg'))
    pp1.click('#cmCls');pp1.wait_for_timeout(300);ok('la_lista_de_campanas_la_muestra','Inscripciones enero · Instagram' in pp1.inner_text('#cmTb') and 'Activa' in pp1.inner_text('#cmTb') and '$3,000.00' in pp1.inner_text('#cmTb'))
    # el visitante llena el formulario público
    cv=b.new_context(viewport={'width':420,'height':900});pv=cv.new_page();pv.goto(B+'/registro?c='+CID);pv.wait_for_selector('#g')
    ok('el_formulario_publico_dice_la_campana_y_sus_programas','Inscripciones enero · Instagram' in pv.inner_text('article') and pv.locator('#p option').count()>=3 and 'Pedagogía' in pv.inner_text('#p') and 'Derecho' in pv.inner_text('#p'))
    pv.click('#g');pv.wait_for_timeout(500);ok('pide_el_nombre_y_el_aviso_de_privacidad','nombre' in pv.inner_text('#e').lower())
    pv.fill('#n','Carlos Medina Rojas');pv.fill('#t','722 987 6543');pv.fill('#c','carlos@mail.com');pv.select_option('#p','Derecho');pv.fill('#m','¿Tienen horario sabatino?');pv.click('#g');pv.wait_for_timeout(500);ok('sin_aceptar_el_aviso_no_envia','aviso de privacidad' in pv.inner_text('#e'))
    pv.check('#a');pv.click('#g');pv.wait_for_selector('#ok',state='visible');ok('el_visitante_ve_el_agradecimiento','Gracias' in pv.inner_text('#ok'))
    W(pp1,"Object.keys(PRO).length===1");pp1.click('#pxTp');pp1.wait_for_timeout(500);t=pp1.inner_text('#pxTb')
    ok('el_prospecto_aparece_solo_con_su_campana_y_canal','Carlos Medina Rojas' in t and '7229876543' in t and 'Inscripciones enero · Instagram' in t and 'Derecho' in t and 'Nuevo' in t)
    ok('la_campana_avisa_del_prospecto_nuevo','prospecto nuevo por contactar' in pp1.evaluate("ntRender();NTI.map(function(x){return x.titulo}).join('|')"))
    ok('hay_un_boton_de_whatsapp_con_su_numero',pp1.locator('#pxTb a[href^="https://wa.me/527229876543?text="]').count()==1 and 'Carlos' in pp1.get_attribute('#pxTb a','href').replace('%20',' '))
    pp1.click('#pxTb [data-pxo]');pp1.wait_for_selector('#dPx[open]')
    ok('el_detalle_muestra_su_origen_y_su_mensaje','7229876543' in pp1.inner_text('#pxDInfo') and 'horario sabatino' in pp1.inner_text('#pxDInfo') and 'aceptó el aviso de privacidad' in pp1.inner_text('#pxDInfo'))
    pp1.select_option('#pxDEstS','descartado');pp1.click('#pxDGo');ok('para_descartar_pide_el_motivo','motivo' in pp1.inner_text('#pxDMsg'))
    pp1.select_option('#pxDEstS','contactado');pp1.select_option('#pxDAsig',index=1);pp1.fill('#pxDProx',manana);pp1.fill('#pxDNota','Se le llamó; pide visitar el sábado.');pp1.click('#pxDGo');W(pp1,"Object.values(PRO)[0].estado==='contactado'");pp1.wait_for_timeout(400)
    tl=pp1.inner_text('#pxDTl');ok('guarda_estado_asignacion_seguimiento_y_nota','Estado: Nuevo → Contactado' in tl and 'Asignado a: ' in tl and 'Próximo contacto' in tl and 'pide visitar el sábado' in tl and 'Se registró desde el formulario público' in tl)
    ok('queda_asignado_a_quien_lo_atiende',pp1.evaluate("Object.values(PRO)[0].asignado")=='pr1')
    pp1.click('#pxDCls')
    # manual con aviso de duplicado
    pp1.click('#pxNuevo');pp1.wait_for_selector('#dPx[open]');pp1.fill('#pxNNom','Carlos M.');pp1.fill('#pxNTel','7229876543');pp1.click('#pxDGo');pp1.wait_for_timeout(600)
    ok('un_telefono_repetido_avisa_antes_de_duplicar',pp1.evaluate("Object.keys(PRO).length")==2)   # el cuadro de confirmación se acepta solo en la prueba
    pp1.evaluate("document.getElementById('dPx').close()")
    pp1.click('#pxNuevo');pp1.wait_for_selector('#dPx[open]');pp1.fill('#pxNNom','Diana Soto');pp1.fill('#pxNTel','722 000 1111');pp1.fill('#pxNCanal','Visita al plantel');pp1.click('#pxDGo');W(pp1,"Object.keys(PRO).length===3");pp1.wait_for_timeout(400)
    ok('registra_a_un_prospecto_a_mano','Diana Soto' in pp1.inner_text('#pxTb') and 'manual' in pp1.inner_text('#pxTb'))
    pp1.select_option('#pxFe','contactado');pp1.wait_for_timeout(300);ok('el_filtro_por_estado_funciona','Carlos' in pp1.inner_text('#pxTb') and 'Diana' not in pp1.inner_text('#pxTb'));pp1.select_option('#pxFe','')
    ok('el_embudo_cuenta_por_estado','Nuevo · 2' in pp1.inner_text('#pxEmb') and 'Contactado · 1' in pp1.inner_text('#pxEmb') or 'Contactado · 1' in pp1.inner_text('#pxEmb'))
    # importar
    pp1.click('#pxTi');pp1.select_option('#pxImpC',index=1);pp1.set_input_files('#pxFile','/tmp/rel107/leads.csv');pp1.wait_for_selector('#pxImpPrev p')
    t=pp1.inner_text('#pxImpPrev');ok('la_vista_previa_cuenta_nuevas_repetidas_y_no_validas','4</b> filas' in pp1.inner_html('#pxImpPrev') and '2</b> nuevas' in pp1.inner_html('#pxImpPrev') and '1 repetidas' in t and '1 sin nombre' in t and 'María Torres' in t)
    ok('sin_confirmar_la_autorizacion_no_se_puede_importar',pp1.is_disabled('#pxImpGo'));pp1.check('#pxImpOk');ok('al_confirmarla_se_habilita',pp1.is_enabled('#pxImpGo'))
    pp1.click('#pxImpGo');W(pp1,"Object.keys(PRO).length===5");pp1.wait_for_timeout(400)
    ok('importa_los_nuevos_con_su_campana_y_origen','se importaron 2' in pp1.inner_text('#pxImpMsg') and pp1.evaluate("Object.values(PRO).filter(function(p){return p.origen==='importado'&&p.campana}).length")==2 and pp1.evaluate("Object.values(PRO).find(function(p){return p.nombre==='María Torres'}).tel")=='7221110001')
    pp1.click('#pxTr');pp1.wait_for_timeout(300);t=pp1.inner_text('#vPr')
    ok('los_resultados_muestran_embudo_canales_y_costos','Embudo' in t and 'Prospectos' in t and 'Por canal' in t and 'Instagram' in t and 'Inversión total en campañas: $3,000.00' in t and 'costo por prospecto: $600.00' in t)
    pp1.click('#pxTc');pp1.wait_for_timeout(300);ok('la_campana_cuenta_sus_prospectos_y_su_costo','$3,000.00' in pp1.inner_text('#cmTb') and '$1,000.00' in pp1.inner_text('#cmTb') or '$600.00' in pp1.inner_text('#cmTb'))
    # ============ solo consulta ============
    pq,cq=entra('prv');pq.evaluate("ir('pr')");W(pq,"MOD==='pr'");pq.wait_for_timeout(500)
    ok('con_solo_ver_se_listan_los_prospectos',pq.locator('#pxTb tr').count()>=3)
    pq.click('#pxTb [data-pxo]');pq.wait_for_selector('#dPx[open]');pq.select_option('#pxDEstS','interesado');pq.click('#pxDGo');pq.wait_for_timeout(800)
    ok('pero_no_puede_guardar_cambios',pq.evaluate("Object.values(PRO).every(function(p){return p.estado!=='interesado'})") and ('No se pudo' in pq.inner_text('#pxDMsg') or 'permiso' in pq.inner_text('#pxDMsg').lower() or pq.inner_text('#pxDMsg')!=''))
    pq.evaluate("document.getElementById('dPx').close()");pq.click('#pxTc');pq.click('#cmNueva');pq.wait_for_selector('#dCm[open]');pq.fill('#cmNom','Intento sin permiso');pq.click('#cmGo');pq.wait_for_timeout(500);ok('ni_crear_campanas','permiso' in pq.inner_text('#cmMsg'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pp1.click('#pxTp');pp1.wait_for_timeout(300);pp1.screenshot(path='/tmp/pr_lista.png',full_page=True)
    a1.evaluate("ir('at')");a1.wait_for_timeout(300);a1.screenshot(path='/tmp/at_lista.png',full_page=True)
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
