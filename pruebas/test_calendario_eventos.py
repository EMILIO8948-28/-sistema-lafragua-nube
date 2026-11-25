"""Calendario de eventos: lo consultan todos (alumnos, docentes y personal); lo cargan a mano administración y quien tenga el permiso."""
import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3127;B='http://127.0.0.1:%d'%PORT
ENVV=dict(os.environ,LF_SIN_CONTACTO='1',PORT=str(PORT),DATA_DIR='/tmp/nbdata_cal',LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_cal && mkdir -p /tmp/nbdata_cal')
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
import datetime
HOY=datetime.datetime.utcnow().date()
def dia(n):return (HOY+datetime.timedelta(days=n)).isoformat()
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&typeof DBH!=='undefined'&&DBH!==null")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    put('students/s1',{'mat':'1001','nombre':'Ana López','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[]})
    def usr(u,name,rol,modulos=None,doc=None,clave=None):
        d={'u':u,'name':name,'rol':rol,'clave':clave or 'clave-%s-123'%u}
        if modulos is not None:d['modulos']=modulos
        if doc:d['doc']=doc
        r=ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR);assert r.status==200,(u,r.status,r.text())
    usr('caja1','Rosa Caja','caja');usr('prof1','Dora Docente','docente',doc='d1');usr('edi1','Edgar Editor','personalizado',{'calendario':'editar'});usr('nom1','Nina Nómina','personalizado',{'nomina_adm':'editar'})
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'1001','name':'Ana López','alumno':'s1','clave':'abcd-efgh'}]}),headers=HDR)
    def sesion(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status,r.text());return cx
    S_={u:sesion(u,'clave-%s-123'%u) for u in ['caja1','prof1','edi1','nom1']}
    al=sesion('1001','abcd-efgh');al.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-ana-77'}),headers=HDR);al=sesion('1001','clave-ana-77')
    # ================= ADMINISTRACIÓN: carga manual =================
    ok('hay_mosaico_del_calendario',pg.is_visible('#mCal') and 'Calendario de eventos' in pg.inner_text('#mCal') and 'Sin eventos próximos' in pg.inner_text('#mCalS'))
    pg.click('#mCal');pg.wait_for_selector('#dCal[open]')
    ok('admin_ve_boton_nuevo_evento',pg.is_visible('#calNew') and 'cargar, cambiar y quitar' in pg.inner_text('#calSub'))
    ok('cuadricula_del_mes_actual',pg.locator('#calGrid .cal-d').count()>=28 and pg.locator('#calGrid .cal-h').count()==7 and pg.locator('#calGrid .cal-d.hoy').count()==1)
    pg.click('#calNew');pg.wait_for_selector('#calForm:not([hidden])')
    pg.click('#calFOk');ok('exige_titulo','título' in pg.inner_text('#calMsg'))
    pg.fill('#calFT','Examen de primer parcial');pg.select_option('#calFC','exam');pg.fill('#calFF',dia(3));pg.fill('#calFH','09:00');pg.fill('#calFHE','08:00');pg.click('#calFOk')
    ok('hora_de_termino_posterior','posterior' in pg.inner_text('#calMsg'))
    pg.fill('#calFHE','11:00');pg.fill('#calFL','Aula magna');pg.fill('#calFD','Llevar identificación.\nSin celulares.');pg.fill('#calFE',dia(2));pg.click('#calFOk')
    ok('fecha_final_no_anterior','anterior' in pg.inner_text('#calMsg'))
    pg.fill('#calFE','');pg.click('#calFOk');W(pg,"Object.keys(AGN).length===1")
    ev=list(json.loads(json.dumps([d for d in ctx.request.get(B+'/api/col/agenda').json()['docs']])))[0]['data']
    ok('guarda_el_evento_completo',ev['titulo']=='Examen de primer parcial' and ev['cat']=='exam' and ev['fecha']==dia(3) and ev['hora']=='09:00' and ev['horaFin']=='11:00' and ev['lugar']=='Aula magna' and 'Sin celulares' in ev['desc'] and ev['por']=='A')
    pg.click('#calGrid .cal-d.hoy') if False else None
    mes_ev=dia(3)[:7]
    # navega al mes del evento si cambió
    ok('aparece_en_la_lista','Examen de primer parcial' in pg.inner_text('#calList') and 'Aula magna' in pg.inner_text('#calList') and '09:00–11:00' in pg.inner_text('#calList'))
    ok('aparece_en_la_cuadricula',pg.locator('#calGrid [data-f="%s"] .cal-ch:has-text("Examen")'%dia(3)).count()==1)
    pg.click('#calCls');pg.evaluate("ir('home')");W(pg,"MOD==='home'")
    ok('mosaico_muestra_el_proximo','Examen de primer parcial' in pg.inner_text('#mCalS'))
    # evento de varios días
    pg.click('#mCal');pg.wait_for_selector('#dCal[open]');pg.click('#calNew');pg.fill('#calFT','Vacaciones de invierno');pg.select_option('#calFC','inh');pg.fill('#calFF',dia(5));pg.fill('#calFE',dia(7));pg.click('#calFOk');W(pg,"Object.keys(AGN).length===2")
    ok('evento_de_varios_dias_aparece_en_cada_dia',all(pg.locator('#calGrid [data-f="%s"] .cal-ch:has-text("Vacaciones")'%dia(n)).count()==1 for n in (5,6,7)) and pg.locator('#calGrid [data-f="%s"] .cal-ch:has-text("Vacaciones")'%dia(8)).count()==0)
    ok('rango_se_muestra_completo',('al' in pg.inner_text('#calList')) and 'Todo el día' in pg.inner_text('#calList'))
    # día y filtro
    pg.click('#calGrid [data-f="%s"]'%dia(6));ok('al_elegir_un_dia_solo_lista_ese_dia','Vacaciones' in pg.inner_text('#calList') and 'Examen' not in pg.inner_text('#calList') and pg.is_visible('#calAll'))
    pg.click('#calAll');ok('ver_todo_el_mes','Examen' in pg.inner_text('#calList') and 'Vacaciones' in pg.inner_text('#calList'))
    pg.select_option('#calCat','exam');ok('filtro_por_tipo','Examen' in pg.inner_text('#calList') and 'Vacaciones' not in pg.inner_text('#calList') and pg.locator('#calGrid .cal-ch').count()==1)
    pg.select_option('#calCat','')
    # editar y cambiar
    pg.locator('#calList [data-ce]').first.click();pg.wait_for_selector('#calForm:not([hidden])')
    ok('editar_carga_los_datos',pg.input_value('#calFT') in ('Examen de primer parcial','Vacaciones de invierno') and pg.is_visible('#calFDel'))
    pg.fill('#calFT','Título cambiado');pg.click('#calFOk');W(pg,"Object.values(AGN).some(function(e){return e.titulo==='Título cambiado'})")
    ok('editar_guarda_el_cambio',sum(1 for d in ctx.request.get(B+'/api/col/agenda').json()['docs'] if d['data']['titulo']=='Título cambiado')==1 and len(ctx.request.get(B+'/api/col/agenda').json()['docs'])==2)
    # texto con HTML se muestra como texto
    pg.click('#calNew');pg.fill('#calFT','<img src=x onerror="window.__xss=1">Taller');pg.fill('#calFD','<b>negritas</b>');pg.fill('#calFF',dia(4));pg.click('#calFOk');W(pg,"Object.keys(AGN).length===3")
    ok('html_en_el_titulo_no_se_ejecuta',pg.evaluate("window.__xss")is None and pg.locator('#calList img').count()==0 and '<img src=x' in pg.inner_text('#calList') and pg.locator('#calGrid img').count()==0)
    # eliminar
    pg.locator('#calList [data-ce]').filter(has=pg.locator('xpath=..')).first.click() if False else None
    idx=[i for i,d in enumerate(ctx.request.get(B+'/api/col/agenda').json()['docs']) if d['data']['titulo'].startswith('<img')][0]
    pg.evaluate("calForm(Object.keys(AGN).filter(function(k){return AGN[k].titulo.indexOf('<img')===0})[0])");pg.click('#calFDel');W(pg,"Object.keys(AGN).length===2")
    ok('eliminar_quita_el_evento',len(ctx.request.get(B+'/api/col/agenda').json()['docs'])==2)
    # meses
    m0=pg.inner_text('#calMes');pg.click('#calNext');ok('mes_siguiente',pg.inner_text('#calMes')!=m0);pg.click('#calPrev');ok('mes_anterior',pg.inner_text('#calMes')==m0)
    pg.click('#calHoy');ok('boton_hoy',pg.locator('#calGrid .cal-d.sel').count()==1)
    pg.screenshot(path='/tmp/cal_admin.png')
    pg.click('#calCls')
    # permisos en el módulo de usuarios
    ok('permiso_en_la_lista_de_modulos',pg.evaluate("MODDEF.some(function(m){return m[0]==='calendario'&&m[5][1][0]==='editar'})"))
    # ================= SERVIDOR: todos leen, solo quien debe escribe =================
    def lee(cx):return cx.request.get(B+'/api/col/agenda').json()['docs']
    ok('todos_leen_el_calendario',all(len(lee(c))==2 for c in [S_['caja1'],S_['prof1'],S_['edi1'],S_['nom1'],al]))
    ok('alumno_lee_un_evento_suelto',al.request.get(B+'/api/doc/agenda/%s'%lee(al)[0]['id']).json()['exists'] is True and S_['caja1'].request.get(B+'/api/doc/agenda/%s'%lee(al)[0]['id']).json()['exists'] is True)
    nuevo={'id':'x1','titulo':'Intento','fecha':dia(1),'cat':'otro'}
    ok('solo_consulta_no_escribe',all(c.request.put(B+'/api/doc/agenda/x1',data=json.dumps(nuevo),headers=HDR).status==403 for c in [S_['caja1'],S_['prof1'],S_['nom1'],al]))
    ok('no_borran_los_que_solo_consultan',all(c.request.delete(B+'/api/doc/agenda/'+lee(ctx)[0]['id'],headers=HDR).status==403 for c in [S_['caja1'],S_['prof1'],al]))
    ok('con_permiso_si_escribe',S_['edi1'].request.put(B+'/api/doc/agenda/x1',data=json.dumps(nuevo),headers=HDR).status==200)
    ok('con_permiso_edita',S_['edi1'].request.patch(B+'/api/doc/agenda/x1',data=json.dumps({'titulo':'Intento editado'}),headers=HDR).status==200 and ctx.request.get(B+'/api/doc/agenda/x1').json()['data']['titulo']=='Intento editado')
    ok('con_permiso_borra_sin_autorizacion',S_['edi1'].request.delete(B+'/api/doc/agenda/x1',headers=HDR).status==200 and ctx.request.get(B+'/api/doc/agenda/x1').json()['exists'] is False)
    ok('el_permiso_no_abre_otras_colecciones',S_['edi1'].request.get(B+'/api/col/students').json()['docs']==[] and S_['edi1'].request.put(B+'/api/doc/students/zz',data=json.dumps({'nombre':'x'}),headers=HDR).status==403)
    for nom,cuerpo in [('sin_titulo',{'titulo':'','fecha':dia(1)}),('fecha_mala',{'titulo':'a','fecha':'mañana'}),('fin_anterior',{'titulo':'a','fecha':dia(2),'fin':dia(1)}),('hora_mala',{'titulo':'a','fecha':dia(1),'hora':'9am'}),('titulo_enorme',{'titulo':'x'*500,'fecha':dia(1)}),('desc_enorme',{'titulo':'a','fecha':dia(1),'desc':'y'*5000}),('tipo_raro',{'titulo':{'a':1},'fecha':dia(1)})]:
        ok('rechaza_'+nom,ctx.request.put(B+'/api/doc/agenda/bad',data=json.dumps(cuerpo),headers=HDR).status==400)
    ok('no_quedo_basura',len(lee(ctx))==2)
    # ================= PANTALLAS DE CADA ROL =================
    def entra(u,c):
        cx=b.new_context();cx.set_default_timeout(12000);p2=pagina(cx);p2.goto(B+'/');W(p2,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        p2.fill('#lgU',u);p2.fill('#lgP',c);p2.click('#lgGo');W(p2,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'&&Object.keys(AGN).length===2",20);p2.wait_for_timeout(400);return p2
    for u,etq in [('caja1','caja'),('prof1','docente'),('nom1','administrativo')]:
        px=entra(u,'clave-%s-123'%u);px.evaluate("ir('home')");W(px,"MOD==='home'")
        ok('%s_ve_el_mosaico_y_abre_el_calendario'%etq,px.is_visible('#mCal'))
        px.click('#mCal');px.wait_for_selector('#dCal[open]')
        ok('%s_lee_eventos_y_no_edita'%etq,'Título cambiado' in px.inner_text('#calList') or 'Vacaciones' in px.inner_text('#calList') or 'Examen' in px.inner_text('#calList'))
        ok('%s_no_ve_nuevo_ni_editar'%etq,not px.is_visible('#calNew') and px.locator('#calList [data-ce]').count()==0 and 'Aquí se publican' in px.inner_text('#calSub'))
        px.click('#calCls');px.fill('#hBus','calendario');ok('%s_encuentra_el_calendario_en_el_buscador'%etq,'Calendario de eventos' in px.inner_text('#hBusR') and 'Nuevo evento' not in px.inner_text('#hBusR'))
        px.context.close()
    pe=entra('edi1','clave-edi1-123');pe.evaluate("ir('home')");W(pe,"MOD==='home'");pe.click('#mCal');pe.wait_for_selector('#dCal[open]')
    ok('editor_con_permiso_ve_nuevo_y_editar',pe.is_visible('#calNew') and pe.locator('#calList [data-ce]').count()>=1)
    pe.fill('#hBus','');pe.click('#calCls');pe.fill('#hBus','nuevo evento');ok('editor_encuentra_nuevo_evento_en_el_buscador','Nuevo evento del calendario' in pe.inner_text('#hBusR'))
    pe.click('#hBusR [data-hf]');pe.wait_for_selector('#calForm:not([hidden])');ok('buscador_abre_el_formulario',pe.is_visible('#calFT'))
    pe.fill('#calFT','Junta de personal');pe.fill('#calFF',dia(9));pe.click('#calFOk');W(pe,"Object.keys(AGN).length===3")
    ok('editor_carga_un_evento_desde_su_pantalla',len(lee(ctx))==3 and any(d['data']['titulo']=='Junta de personal' and d['data']['por']=='Edgar Editor' for d in lee(ctx)))
    pe.context.close()
    # alumno
    pa=b.new_context();pa.set_default_timeout(12000);pa=pagina(pa);pa.goto(B+'/');W(pa,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pa.fill('#lgU','1001');pa.fill('#lgP','clave-ana-77');pa.click('#lgGo');W(pa,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&S.length===1&&!document.getElementById('dPw').open&&Object.keys(AGN).length===3",20)
    tx=pa.inner_text('#poBody')
    ok('alumno_ve_proximos_eventos_en_su_portal','Calendario de eventos' in tx and ('Examen de primer parcial' in tx or 'Título cambiado' in tx or 'Junta de personal' in tx))
    ok('alumno_no_ve_el_mosaico_del_panel',pa.evaluate("MOD")=='por')
    pa.click('#poBody [data-ncal]');pa.wait_for_selector('#dCal[open]')
    ok('alumno_abre_el_calendario_completo_sin_editar',pa.locator('#calGrid .cal-d').count()>=28 and not pa.is_visible('#calNew') and pa.locator('#calList [data-ce]').count()==0)
    pa.screenshot(path='/tmp/cal_alumno.png')
    # actualización en vivo para el alumno
    n0=pa.evaluate("Object.keys(AGN).length");put('agenda/vivo1',{'id':'vivo1','titulo':'Evento en vivo','fecha':dia(1),'cat':'inst'});W(pa,"Object.keys(AGN).length===%d"%(n0+1))
    ok('el_alumno_recibe_el_evento_nuevo_sin_recargar',pa.evaluate("!!AGN.vivo1"))
    ok('sin_errores_de_pagina',not errs)
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(json.dumps(R,ensure_ascii=False,indent=0));print('FALLAS:',bad,errs[:3]);print('%d/%d'%(len(R)-len(bad),len(R)))
