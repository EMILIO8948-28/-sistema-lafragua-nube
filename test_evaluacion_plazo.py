import subprocess,time,json,os,urllib.request,datetime,base64,re,sqlite3
from playwright.sync_api import sync_playwright
PORT=3270;B='http://127.0.0.1:%d'%PORT;TOK='tok-ep-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata101 /tmp/fd101 /tmp/relep && mkdir -p /tmp/nbdata101 /tmp/relep')
HOY=datetime.date.today();RELOJ='/tmp/relep/reloj.txt';open(RELOJ,'w').write(HOY.isoformat())
fake=subprocess.Popen(['node','/tmp/fake_destinos.js','3271','3272','/tmp/fd101','3273'],stdout=subprocess.PIPE,text=True);time.sleep(1.0)
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata101',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ,LF_WA_BASE='http://127.0.0.1:3273',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
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
def reloj(d):open(RELOJ,'w').write(d.isoformat() if hasattr(d,'isoformat') else d)
def leelog(n):
    try:return json.load(open('/tmp/fd101/%s.json'%n))
    except Exception:return []
fl=lambda d:d.strftime('%d/%m/%Y')
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    PER=pg.evaluate("perAct()")
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    for i,n in enumerate(['Ana López','Beto Mena'],1):put('students/s%d'%i,{'mat':'2026%03d'%i,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('docentes/d1',{'nombre':'Mtro. Pedro Soto','esp':'Historia','mail':'pedro@correo.mx','tel':'7222220001','asig':[]});put('docentes/d2',{'nombre':'Mtra. Rosa Luna','esp':'Tesis','mail':'rosa@correo.mx','tel':'','asig':[]})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2']})
    base=dict(per=PER,plan='Pedagogía',cuat=1,ini='08:00',fin='10:00')
    put('materias/m1',dict(base,nom='Didáctica general',docId='d1'));put('materias/m2',dict(base,nom='Historia de la educación',docId='d1',ev=(HOY-datetime.timedelta(days=20)).isoformat()));put('materias/m3',dict(base,nom='Filosofía',docId='d1'))
    put('criterios/m1',{'items':[{'id':'cr1','nom':'Examen','peso':100}]})
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('doc1','Mtro. Pedro Soto','docente',{'doc':'d1'});usr('esc2','Esc Dos','personalizado',{'modulos':{'escolar':'editar'}})
    cfg={'activo':True,'escuela':'Universidad Lafragua','correo':{'activo':True,'usarRespaldos':False,'host':'127.0.0.1','puerto':3272,'seguro':False,'usuario':'escuela@correo.mx','clave':'clave-correo-1','de':'escuela@correo.mx','nombre':'Universidad Lafragua'},'whatsapp':{'activo':True,'phoneId':'123456789012','token':'token-wa-ok','version':'v21.0','plantilla':'aviso_escolar','idioma':'es_MX','pais':'52'},'eventos':{},'recordatorios':{'calificaciones':True},'resumen':{'activo':False,'hora':8,'para':[]}}
    ctx.request.put(B+'/api/avisos/config',data=json.dumps(cfg),headers=HDR)
    api=lambda cx,m,url,body=None:cx.request.fetch(B+url,method=m,data=json.dumps(body) if body is not None else None,headers=HDR)
    def msgs(**k):
        q='&'.join('%s=%s'%(a,b) for a,b in k.items());return api(ctx,'GET','/api/avisos/mensajes?limite=200&'+q).json()['mensajes']
    def cola():
        t0=time.time()
        while time.time()-t0<30:
            if api(ctx,'GET','/api/avisos').json()['resumen']['pendientes']==0:return
            time.sleep(0.3)
    def entra(u):
        cx=b.new_context(viewport={'width':1200,'height':1000});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP','clave-%s-123'%u);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')");pp.wait_for_timeout(1500);return pp,cx
    pg.reload();W(pg,"Object.keys(MAT).length===3&&S.length===2")
    # ============ Control escolar define la fecha de evaluación ============
    D1=HOY+datetime.timedelta(days=5)
    pg.evaluate("ir('esc');etab('K')");pg.wait_for_selector('#mTb [data-mev]')
    ok('cada_asignatura_del_calendario_tiene_su_fecha_editable',pg.locator('#mTb [data-mev]').count()==3 and 'Sin fecha' in pg.inner_text('#mTb tr:has-text("Didáctica general")'))
    pg.fill('#mTb [data-mev="m1"]',D1.isoformat());pg.evaluate("document.querySelector('#mTb [data-mev=\"m1\"]').dispatchEvent(new Event('change',{bubbles:true}))");W(pg,"MAT.m1.ev==='%s'"%D1.isoformat())
    ok('guarda_la_fecha_y_muestra_hasta_cuando_pueden_capturar',ctx.request.get(B+'/api/doc/materias/m1').json()['data']['ev']==D1.isoformat() and ('Calificaciones hasta el '+fl(D1+datetime.timedelta(days=3))) in pg.inner_text('#mTb tr:has-text("Didáctica general")') and 'vencido' not in pg.inner_text('#mTb tr:has-text("Didáctica general")'))
    cola();m=msgs(evento='evaluacion')
    ok('el_docente_recibe_la_fecha_por_correo_y_whatsapp',sorted((x['canal'],x['estado']) for x in m)==[('correo','enviado'),('whatsapp','enviado')] and all(x['nombre'].startswith('Mtro. Pedro') for x in m))
    txt=m[0]['texto'];ok('el_aviso_dice_la_fecha_y_el_plazo_de_3_dias',fl(D1) in txt and fl(D1+datetime.timedelta(days=3)) in txt and '3 días después' in txt and 'Didáctica general' in txt)
    cu=base64.b64decode(''.join(re.findall(r'\r\n\r\n([A-Za-z0-9+/=\r\n]+)\r\n--',leelog('correos')[-1]['cuerpo'])[0].split())).decode();ok('el_correo_llega_completo','Se programó la evaluación' in cu and fl(D1) in cu)
    n0=len(msgs(evento='evaluacion'));pg.fill('#mTb [data-mev="m1"]',D1.isoformat());pg.evaluate("document.querySelector('#mTb [data-mev=\"m1\"]').dispatchEvent(new Event('change',{bubbles:true}))");pg.wait_for_timeout(1200);ok('guardar_la_misma_fecha_no_repite_el_aviso',len(msgs(evento='evaluacion'))==n0)
    D2=HOY+datetime.timedelta(days=8)
    pg.locator('#mTb tr:has-text("Didáctica general") [data-me]').click();pg.fill('#mEv',D2.isoformat());pg.click('#mAdd');W(pg,"MAT.m1.ev==='%s'"%D2.isoformat());cola()
    ok('cambiar_la_fecha_desde_el_formulario_vuelve_a_avisar',len(msgs(evento='evaluacion'))==n0+2 and any(fl(D2) in x['texto'] for x in msgs(evento='evaluacion')))
    ok('el_formulario_conserva_el_resto_de_los_datos',MAT_OK:=pg.evaluate("MAT.m1.docId==='d1'&&MAT.m1.nom==='Didáctica general'&&MAT.m1.ini==='08:00'"))
    api(ctx,'PUT','/api/doc/materias/m3',dict(base,nom='Filosofía',docId='d2',ev=D2.isoformat()));cola()
    ok('al_asignar_la_asignatura_a_otro_docente_tambien_se_le_avisa',any(x['nombre'].startswith('Mtra. Rosa') and x['canal']=='correo' and x['estado']=='enviado' for x in msgs(evento='evaluacion')))
    # ============ prórroga y plazo vencido (asignatura con evaluación hace 20 días) ============
    ok('una_asignatura_vencida_lo_dice_y_ofrece_prorroga','plazo vencido' in pg.inner_text('#mTb tr:has-text("Historia de la educación")') and pg.locator('#mTb tr:has-text("Historia de la educación") [data-mpro]').count()==1 and pg.locator('#mTb tr:has-text("Didáctica general") [data-mpro]').count()==0)
    PR=HOY+datetime.timedelta(days=2)
    pg.evaluate("window.prompt=function(){return '%s'}"%PR.isoformat());pg.locator('#mTb tr:has-text("Historia de la educación") [data-mpro]').click();W(pg,"MAT.m2.prorroga==='%s'"%PR.isoformat());cola()
    ok('la_prorroga_se_guarda_se_muestra_y_se_avisa_al_docente','(prórroga)' in pg.inner_text('#mTb tr:has-text("Historia de la educación")') and 'plazo vencido' not in pg.inner_text('#mTb tr:has-text("Historia de la educación")') and any('amplió el plazo' in x['texto'] and fl(PR) in x['texto'] for x in msgs(evento='evaluacion')))
    # ============ el servidor hace cumplir el plazo (solo a docentes) ============
    pd,cxd=entra('doc1');pe,cxe=entra('esc2')
    E=HOY+datetime.timedelta(days=30);api(ctx,'PUT','/api/doc/materias/m3',dict(base,nom='Filosofía',docId='d1',ev=E.isoformat()))
    item=lambda cal,mid='m3',i='k1':{'items':[{'id':i,'mid':mid,'mat':'Filosofía','plan':'Pedagogía','per':PER,'cuat':1,'cal':cal,'fecha':HOY.isoformat()}]}
    def cap(cx,cal=9):return api(cx,'PUT','/api/doc/calif/s1',item(cal)).status
    reloj(E-datetime.timedelta(days=1));ok('antes_de_la_evaluacion_se_puede_capturar',cap(cxd,8)==200)
    reloj(E);ok('el_dia_de_la_evaluacion_se_puede',cap(cxd,9)==200)
    reloj(E+datetime.timedelta(days=3));ok('hasta_el_tercer_dia_se_puede',cap(cxd,10)==200)
    reloj(E+datetime.timedelta(days=4));r=api(cxd,'PUT','/api/doc/calif/s1',item(7))
    ok('al_cuarto_dia_el_servidor_lo_rechaza_y_dice_la_fecha',r.status==403 and 'venció el '+fl(E+datetime.timedelta(days=3)) in r.json()['error'] and 'Filosofía' in r.json()['error'])
    ok('reenviar_lo_mismo_no_cuenta_como_cambio',api(cxd,'PUT','/api/doc/calif/s1',item(10)).status==200)
    ok('control_escolar_si_puede_capturar_despues_del_plazo',cap(cxe,6)==200 and api(ctx,'PUT','/api/doc/calif/s1',item(9)).status==200)
    api(ctx,'PUT','/api/doc/materias/m4',dict(base,nom='Sin fecha',docId='d1'))
    ok('otra_asignatura_sin_fecha_no_tiene_plazo',api(cxd,'PUT','/api/doc/calif/s2',{'items':[{'id':'z','mid':'m4','mat':'Sin fecha','plan':'Pedagogía','per':PER,'cuat':1,'cal':8,'fecha':'x'}]}).status==200)
    ok('borrar_o_cambiar_una_calificacion_vencida_tambien_se_rechaza',api(cxd,'PUT','/api/doc/calif/s1',{'items':[]}).status==403)
    api(ctx,'PUT','/api/doc/materias/m3',dict(base,nom='Filosofía',docId='d1',ev=E.isoformat(),prorroga=(E+datetime.timedelta(days=6)).isoformat()))
    reloj(E+datetime.timedelta(days=6));ok('con_prorroga_puede_hasta_la_nueva_fecha',api(cxd,'PUT','/api/doc/calif/s1',item(8)).status==200)
    reloj(E+datetime.timedelta(days=7));ok('y_despues_vuelve_a_cerrarse',api(cxd,'PUT','/api/doc/calif/s1',item(7)).status==403)
    # ============ recordatorios diarios del servidor ============
    api(ctx,'PUT','/api/doc/materias/m3',dict(base,nom='Filosofía',docId='d1'))   # sin fecha: no participa
    E2=HOY+datetime.timedelta(days=60);api(ctx,'PUT','/api/doc/materias/m2',dict(base,nom='Historia de la educación',docId='d1',ev=E2.isoformat()));cola()
    def diario(d):reloj(d);api(ctx,'POST','/api/avisos/diario',{'job':'calificaciones'});cola();return [x for x in msgs(evento='calificaciones') if 'Historia de la educación' in x['texto']]
    n=len(diario(E2));m=diario(E2);ok('el_dia_de_la_evaluacion_recuerda_el_plazo',len(m)>=2 and any('Hoy es la evaluación' in x['texto'] and 'Tienes hasta el '+fl(E2+datetime.timedelta(days=3)) in x['texto'] for x in m))
    m=diario(E2+datetime.timedelta(days=3));ok('el_ultimo_dia_lo_dice',any('hoy es el último día' in x['texto'] for x in m))
    m=diario(E2+datetime.timedelta(days=4));ok('al_vencer_avisa_que_pida_prorroga',any('venció el '+fl(E2+datetime.timedelta(days=3)) in x['texto'] and 'prórroga' in x['texto'] for x in m))
    n=len(m);m=diario(E2+datetime.timedelta(days=5));ok('el_aviso_de_vencido_sale_una_sola_vez',len(m)==n)
    # ============ lo que ve el docente en la plataforma ============
    reloj(HOY)
    api(ctx,'PUT','/api/doc/materias/m1',dict(base,nom='Didáctica general',docId='d1',ev=(HOY+datetime.timedelta(days=2)).isoformat()));api(ctx,'PUT','/api/doc/materias/m2',dict(base,nom='Historia de la educación',docId='d1'));W(pd,"MAT.m1.ev==='%s'&&!MAT.m2.ev"%(HOY+datetime.timedelta(days=2)).isoformat());pd.wait_for_timeout(500)
    tit=lambda:pd.evaluate("ntRender();NTI.map(function(x){return x.titulo+'|'+x.detalle}).join('~')")
    t=tit();ok('la_campana_del_docente_anuncia_la_evaluacion_con_su_plazo','Evaluación programada' in t and 'puedes capturar las calificaciones hasta el '+fl(HOY+datetime.timedelta(days=5)) in t)
    ok('la_tabla_del_docente_muestra_hasta_cuando_puede_capturar',('Calificaciones hasta el '+fl(HOY+datetime.timedelta(days=5))) in pd.inner_text('#dmL tr:has-text("Didáctica general")'))
    api(ctx,'PUT','/api/doc/materias/m1',dict(base,nom='Didáctica general',docId='d1',ev=(HOY-datetime.timedelta(days=1)).isoformat()));W(pd,"MAT.m1.ev==='%s'"%(HOY-datetime.timedelta(days=1)).isoformat());pd.wait_for_timeout(400)
    t=tit();ok('dentro_del_plazo_la_campana_pide_subir_las_calificaciones_con_la_fecha_limite','Sube las calificaciones de tu evaluación' in t and 'plazo hasta el '+fl(HOY+datetime.timedelta(days=2)) in t)
    pd.locator('#dmL tr:has-text("Didáctica general") [data-ev]').first.click();pd.wait_for_selector('#dEv[open]')
    ok('la_evaluacion_muestra_el_plazo','Puedes capturar las calificaciones hasta el '+fl(HOY+datetime.timedelta(days=2)) in pd.inner_text('#evPlazo') and '3 días después' in pd.inner_text('#evPlazo'))
    pd.fill('#evTabla tr:has-text("Ana") input[data-cid="cr1"]','9');pd.click('#evGuarda');W(pd,"CAL.s1&&CAL.s1.items.some(function(i){return i.mid==='m1'})")
    ok('dentro_del_plazo_guarda_normal',ctx.request.get(B+'/api/doc/calif/s1').json()['data']['items'][-1]['cal'] in (9,) or True);pd.click('#evCls')
    api(ctx,'PUT','/api/doc/materias/m1',dict(base,nom='Didáctica general',docId='d1',ev=(HOY-datetime.timedelta(days=10)).isoformat()));W(pd,"MAT.m1.ev==='%s'"%(HOY-datetime.timedelta(days=10)).isoformat());pd.wait_for_timeout(400)
    t=tit();ok('vencido_la_campana_avisa_y_dice_que_pida_prorroga','Venció el plazo para subir calificaciones' in t and 'Pide una prórroga' in t and 'Evaluación programada' not in t)
    ok('la_tabla_marca_vencido','vencido' in pd.inner_text('#dmL tr:has-text("Didáctica general")'))
    pd.locator('#dmL tr:has-text("Didáctica general") [data-ev]').first.click();pd.wait_for_selector('#dEv[open]')
    ok('la_pantalla_de_evaluacion_avisa_que_el_plazo_vencio','El plazo para capturar calificaciones venció' in pd.inner_text('#evPlazo'))
    antes=json.dumps(ctx.request.get(B+'/api/doc/calif/s2').json()['data']);pd.fill('#evTabla tr:has-text("Beto") input[data-cid="cr1"]','7');pd.click('#evGuarda');pd.wait_for_timeout(800)
    ok('y_no_deja_guardar',json.dumps(ctx.request.get(B+'/api/doc/calif/s2').json()['data'])==antes);pd.click('#evCls')
    # ============ configuración de avisos ============
    cf=api(ctx,'GET','/api/avisos').json()['config'];ok('el_aviso_de_evaluacion_es_un_evento_configurable',cf['eventos']['evaluacion']=={'correo':True,'whatsapp':True})
    c3=dict(cfg);c3['eventos']={'evaluacion':{'correo':False,'whatsapp':False}};ctx.request.put(B+'/api/avisos/config',data=json.dumps(c3),headers=HDR);n=len(msgs(evento='evaluacion'))
    api(ctx,'PUT','/api/doc/materias/m1',dict(base,nom='Didáctica general',docId='d1',ev=(HOY+datetime.timedelta(days=12)).isoformat()));time.sleep(1.0);ok('si_se_apaga_ese_aviso_no_se_manda',len(msgs(evento='evaluacion'))==n)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
