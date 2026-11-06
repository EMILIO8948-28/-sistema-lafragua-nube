import subprocess,time,json,os,urllib.request,urllib.error
from playwright.sync_api import sync_playwright
PORT=3096;B='http://127.0.0.1:%d'%PORT;TOK='tok-so-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata26',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata26 /tmp/so && mkdir -p /tmp/nbdata26 /tmp/so')
open('/tmp/so/medico.pdf','wb').write(b'%PDF-1.4 comprobante medico');open('/tmp/so/receta.jpg','wb').write(b'\xff\xd8\xff\xe0'+b'0'*50);open('/tmp/so/malo.exe','wb').write(b'MZ');open('/tmp/so/grande.pdf','wb').write(b'%PDF'+b'0'*(11*1024*1024))
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=25):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
PER='Sep–Dic 2026'
def chk(s):
    h=2166136261
    for ch in s:h^=ord(ch);h=(h*16777619)&0xffffffff
    return '%08x'%h
def pub(path):
    try:
        r=urllib.request.urlopen(B+path);return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:return e.code,json.loads(e.read())
        except Exception:return e.code,{}
MOCK="""()=>{window.__txt=[];window.__sav=[];window.__qr=null;
 function mk(){return new Proxy({},{get:function(o,k){
   if(k==='text')return function(s){window.__txt.push(String(Array.isArray(s)?s.join(' '):s));return me};
   if(k==='splitTextToSize')return function(s){return [String(s)]};if(k==='getTextWidth')return function(){return 10};
   if(k==='output')return function(){return new ArrayBuffer(8)};
   return function(){return me}}})}
 var me=null;function PDF(){me=mk();return me}
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};
 var q0=qrPDF;qrPDF=function(d,t,x,y,l){window.__qr=t;return q0(d,t,x,y,l)};0}"""
hoy=time.strftime('%Y-%m-%d')
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    for sid,mat,nom in [('s1','20230101','Ana López Martínez'),('s2','20230102','Beto Mena Ruiz')]:put('students/'+sid,{'mat':mat,'nombre':nom,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2023,'nuevo':False,'sexo':'Femenino' if sid=='s1' else 'Masculino'})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':3,'alumnos':['s1','s2']})
    put('calif/s1',{'items':[{'id':'c1','mid':'m1','mat':'Didáctica','plan':'Pedagogía','per':PER,'cuat':3,'doc':'Mtra. Laura Díaz','cal':9.0,'fecha':'2026-11-01'}]})
    put('calif/s2',{'items':[{'id':'c2','mid':'m2','mat':'Educación especial','plan':'Pedagogía','per':PER,'cuat':3,'doc':'Mtro. Iván Cruz','cal':8.5,'fecha':'2026-11-01'}]})
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'20230101','name':'Ana','alumno':'s1','clave':'abcd-efgh'},{'u':'20230102','name':'Beto','alumno':'s2','clave':'ijkm-npqr'}]}),headers=HDR)
    for u,n,r,m in [('esc1','Esc Uno','personalizado',{'escolar':'ver'}),('esc2','Esc Dos','personalizado',{'escolar':'editar'}),('caja1','Caja','caja',None)]:
        body={'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u}
        if m:body['modulos']=m
        assert ctx.request.post(B+'/api/usuarios',data=json.dumps(body),headers=HDR).status==200
    def ses(u,c,cambia=None):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status)
        if cambia:assert cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':c,'nueva':cambia}),headers=HDR).status==200
        return cx
    A1=ses('20230101','abcd-efgh','clave-ana-77');A2=ses('20230102','ijkm-npqr','clave-beto-77')
    S_={'esc1':ses('esc1','clave-esc1-123'),'esc2':ses('esc2','clave-esc2-123'),'caja1':ses('caja1','clave-caja1-123')}
    def sube(cx,datos=b'%PDF-1.4 x',ct='application/pdf',cat='solicitud',priv='1'):
        h={'x-lafragua':'1','x-nombre':'medico.pdf','Content-Type':ct}
        if priv:h['x-privado']=priv
        if cat:h['x-categoria']=cat
        return cx.request.post(B+'/api/archivo',data=datos,headers=h)
    def putS(cx,id,obj):return cx.request.put(B+'/api/doc/solicitudes/'+id,data=json.dumps(obj),headers=HDR)
    def patchS(cx,id,obj):return cx.request.patch(B+'/api/doc/solicitudes/'+id,data=json.dumps(obj),headers=HDR)
    # ---------------- archivos del alumno ----------------
    f1=sube(A1);ok('alumno_anexa_comprobante',f1.status==200);fid=f1.json()['id']
    ok('sin_categoria_o_publico_no',sube(A1,cat='').status==403 and sube(A1,priv='').status==403)
    ok('solo_pdf_jpg_png',sube(A1,ct='text/plain').status==400 and sube(A1,datos=b'\xff\xd8\xff',ct='image/jpeg').status==200)
    ok('maximo_10_mb',sube(A1,datos=open('/tmp/so/grande.pdf','rb').read()).status in (400,413))
    ok('alumno_no_sube_otra_cosa',A1.request.post(B+'/api/archivo',data=b'%PDF',headers={'x-lafragua':'1','x-nombre':'a.pdf','x-privado':'1','x-categoria':'planeacion','Content-Type':'application/pdf'}).status==403 and A1.request.delete(B+'/api/archivo/'+fid,headers=HDR).status==403)
    ok('el_comprobante_solo_lo_ven_su_dueno_y_control_escolar',A1.request.get(B+'/_blob/'+fid).status==200 and S_['esc2'].request.get(B+'/_blob/'+fid).status==200 and ctx.request.get(B+'/_blob/'+fid).status==200 and A2.request.get(B+'/_blob/'+fid).status==403 and S_['caja1'].request.get(B+'/_blob/'+fid).status==403 and S_['esc1'].request.get(B+'/_blob/'+fid).status==403)
    # ---------------- crear solicitudes ----------------
    j={'tipo':'justificante','desde':hoy,'hasta':hoy,'motivo':'Enfermedad','nota':'Gripa','docs':[fid],'estado':'aprobada','nombre':'Otro Nombre','sid':'s2','resp':{'por':'yo'}}
    r=putS(A1,'sol1',j);ok('crea_justificante',r.status==200)
    d=A1.request.get(B+'/api/doc/solicitudes/sol1').json()['data']
    ok('datos_del_alumno_los_pone_el_servidor',d['nombre']=='Ana López Martínez' and d['mat']=='20230101' and d['plan']=='Pedagogía' and d['sid']=='s1')
    ok('siempre_nace_pendiente',d['estado']=='pendiente' and 'resp' not in d and d['leida'] is False and d['docs'][0]['id']==fid and d['docs'][0]['name']=='medico.pdf')
    fid2=sube(A2).json()['id']
    base={'tipo':'justificante','desde':hoy,'hasta':hoy,'motivo':'Cita médica','docs':[fid]}
    ok('justificante_exige_comprobante',putS(A1,'x1',dict(base,docs=[])).status==400 and putS(A1,'x2',{k:v for k,v in base.items() if k!='docs'}).status==400)
    ok('no_usa_archivos_ajenos',putS(A1,'x3',dict(base,docs=[fid2])).status==400 and putS(A1,'x4',dict(base,docs=['f'*32])).status==400)
    ok('valida_fechas_y_motivo',putS(A1,'x5',dict(base,desde='2026-12-05',hasta='2026-12-01')).status==400 and putS(A1,'x6',dict(base,desde='2020-01-01',hasta='2020-01-02')).status==400 and putS(A1,'x7',dict(base,motivo='Vacaciones')).status==400 and putS(A1,'x8',dict(base,desde='mañana')).status==400)
    ok('valida_tipo',putS(A1,'x9',{'tipo':'diploma'}).status==400)
    ok('crea_boleta',putS(A1,'b1',{'tipo':'boleta','periodo':PER,'nota':'Para beca'}).status==200 and putS(A1,'x10',{'tipo':'boleta','periodo':'Verano 2026'}).status==400)
    ok('crea_constancia',putS(A1,'c1',{'tipo':'constancia','tipoC':'promedio','dest':'Instituto Ejemplo'}).status==200 and putS(A1,'x11',{'tipo':'constancia','tipoC':'otra'}).status==400)
    ok('maximo_5_pendientes',putS(A1,'p4',{'tipo':'boleta','periodo':PER}).status==200 and putS(A1,'p5',{'tipo':'boleta','periodo':'Ene–Abr 2026'}).status==200 and putS(A1,'p6',{'tipo':'boleta','periodo':'May–Ago 2026'}).status==429)
    # ---------------- privacidad y límites del alumno ----------------
    ok('alumno_solo_ve_las_suyas',sorted(x['id'] for x in A1.request.get(B+'/api/col/solicitudes').json()['docs'])==['b1','c1','p4','p5','sol1'] and A2.request.get(B+'/api/col/solicitudes').json()['docs']==[] and A2.request.get(B+'/api/doc/solicitudes/sol1').json()['exists'] is False)
    ok('solo_puede_marcar_leida',patchS(A1,'sol1',{'leida':True}).status==200 and get('solicitudes/sol1')['data']['leida'] is True and patchS(A1,'sol1',{'estado':'aprobada'}).status==403 and patchS(A1,'sol1',{'leida':True,'estado':'aprobada'}).status==403 and putS(A1,'sol1',{'tipo':'boleta','periodo':PER}).status==403)
    ok('no_toca_lo_de_otro_alumno',patchS(A2,'sol1',{'leida':True}).status==403 and A1.request.delete(B+'/api/doc/solicitudes/sol1',headers=HDR).status==403)
    ok('solo_control_escolar_las_lee_todas',sorted(x['id'] for x in S_['esc2'].request.get(B+'/api/col/solicitudes').json()['docs'])==['b1','c1','p4','p5','sol1'] and S_['esc1'].request.get(B+'/api/col/solicitudes').json()['docs']==[] and S_['caja1'].request.get(B+'/api/col/solicitudes').json()['docs']==[])
    ok('quien_no_edita_control_escolar_no_responde',patchS(S_['esc1'],'sol1',{'estado':'aprobada'}).status==403 and patchS(S_['caja1'],'sol1',{'estado':'aprobada'}).status==403)
    # justificantes visibles para el alumno
    put('meta/folioJ',{'n':10})
    put('justificantes/j1',{'id':'j1','num':'J-000001','sid':'s1','nombre':'Ana López Martínez','mat':'20230101','plan':'Pedagogía','sexo':'Femenino','grupo':'4821','fecha':hoy,'byn':'Esc Dos','doc':{'id':fid,'name':'medico.pdf'},'desde':hoy,'hasta':hoy,'motivo':'Enfermedad','nota':'Dato interno','estado':'Aprobado'})
    put('justificantes/j2',{'id':'j2','num':'J-000002','sid':'s1','nombre':'Ana','mat':'20230101','plan':'Pedagogía','desde':hoy,'hasta':hoy,'motivo':'Otro','estado':'Pendiente','fecha':hoy})
    put('justificantes/j3',{'id':'j3','num':'J-000003','sid':'s2','nombre':'Beto','mat':'20230102','plan':'Pedagogía','desde':hoy,'hasta':hoy,'motivo':'Otro','estado':'Aprobado','fecha':hoy})
    jj=A1.request.get(B+'/api/col/justificantes').json()['docs'];ok('alumno_ve_solo_sus_justificantes_aprobados_sin_datos_internos',[x['id'] for x in jj]==['j1'] and all(k not in jj[0]['data'] for k in ['nota','doc','byn']) and jj[0]['data']['num']=='J-000001')
    ok('alumno_no_ve_justificantes_ajenos',A2.request.get(B+'/api/doc/justificantes/j1').json()['exists'] is False and A1.request.get(B+'/api/doc/justificantes/j3').json()['exists'] is False and A1.request.get(B+'/api/doc/justificantes/j2').json()['exists'] is False)
    # verificación pública del justificante
    cod=chk('J|J-000001|s1|%s|%s'%(hoy,hoy));st,v=pub('/api/verificar?t=j&id=J-000001&c='+cod)
    ok('verifica_el_justificante_sin_sesion',st==200 and v['ok'] and v['tipo']=='justificante' and v['nombre']=='Ana López Martínez' and v['matricula']=='•••••101' and v['desde']==hoy and v['emitido']==hoy)
    ok('no_muestra_motivo_ni_notas','Enfermedad' not in json.dumps(v) and 'Dato interno' not in json.dumps(v) and 'medico' not in json.dumps(v))
    ok('codigo_malo_o_no_vigente',pub('/api/verificar?t=j&id=J-000001&c=00000000')[1]['ok'] is False and pub('/api/verificar?t=j&id=J-000002&c='+chk('J|J-000002|s1|%s|%s'%(hoy,hoy)))[1]['ok'] is False and pub('/api/verificar?t=j&id=J-999999&c=00000000')[1]['ok'] is False)
    # ---------------- pantallas ----------------
    ca=b.new_context(viewport={'width':1000,'height':900});ca.set_default_timeout(15000);pa=pagina(ca);pa.goto(B+'/');W(pa,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pa.fill('#lgU','20230102');pa.fill('#lgP','clave-beto-77');pa.click('#lgGo');W(pa,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&S.length===1");pa.wait_for_timeout(500);pa.evaluate(MOCK)
    ok('portal_ofrece_solicitar',pa.is_visible('#poBody [data-nsol]') and 'Mis solicitudes' in pa.inner_text('#poBody') and 'Notificaciones' in pa.inner_text('#poBody'))
    pa.click('#poBody [data-nsol]');pa.wait_for_selector('#dSo[open]')
    ok('formulario_de_justificante','Comprobante' in pa.inner_text('#soJ') and pa.is_visible('#soFile') and pa.is_hidden('#soB') and pa.is_hidden('#soC'))
    pa.select_option('#soTipo','boleta');ok('formulario_de_boleta',pa.is_visible('#soB') and pa.is_hidden('#soJ'));pa.select_option('#soTipo','constancia');ok('formulario_de_constancia',pa.is_visible('#soC'))
    pa.select_option('#soTipo','justificante');pa.click('#soEnv');ok('exige_comprobante','Anexa tu comprobante' in pa.inner_text('#soMsg'))
    pa.set_input_files('#soFile','/tmp/so/malo.exe');pa.click('#soEnv');ok('rechaza_tipo_de_archivo','PDF, JPG o PNG' in pa.inner_text('#soMsg'))
    pa.set_input_files('#soFile','/tmp/so/grande.pdf');pa.click('#soEnv');ok('rechaza_archivo_grande','10 MB' in pa.inner_text('#soMsg'))
    pa.fill('#soDes',hoy);pa.fill('#soHas',hoy);pa.select_option('#soMot','Cita médica');pa.fill('#soNota','Estudios de laboratorio');pa.set_input_files('#soFile',['/tmp/so/medico.pdf','/tmp/so/receta.jpg']);pa.click('#soEnv');W(pa,"!document.getElementById('dSo').open&&Object.keys(SOL).length===1")
    sb=[v for v in get('solicitudes/'+list(json.loads(pa.evaluate('JSON.stringify(Object.keys(SOL))')))[0])['data'].values()]
    d2=get('solicitudes/'+json.loads(pa.evaluate('JSON.stringify(Object.keys(SOL))'))[0])['data']
    ok('justificante_enviado_con_comprobantes',d2['tipo']=='justificante' and d2['estado']=='pendiente' and len(d2['docs'])==2 and d2['motivo']=='Cita médica' and d2['nombre']=='Beto Mena Ruiz')
    ok('aparece_en_mis_solicitudes','Justificante de faltas' in pa.inner_text('#poBody') and 'Pendiente' in pa.inner_text('#poBody') and 'Cita médica' in pa.inner_text('#poBody'))
    pa.click('#poBody [data-nsol]');pa.select_option('#soTipo','boleta');pa.click('#soEnv');W(pa,"!document.getElementById('dSo').open&&Object.keys(SOL).length===2")
    pa.click('#poBody [data-nsol]');pa.select_option('#soTipo','constancia');pa.select_option('#soTC','promedio');pa.fill('#soDest','Instituto Demo');pa.click('#soEnv');W(pa,"!document.getElementById('dSo').open&&Object.keys(SOL).length===3")
    ok('boleta_y_constancia_enviadas',sorted(x['data']['tipo'] for x in S_['esc2'].request.get(B+'/api/col/solicitudes').json()['docs'] if x['data']['sid']=='s2')==['boleta','constancia','justificante'])
    # ---- Control escolar ----
    ce=b.new_context(viewport={'width':1100,'height':900});ce.set_default_timeout(15000);pe=pagina(ce);pe.goto(B+'/');W(pe,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pe.fill('#lgU','esc2');pe.fill('#lgP','clave-esc2-123');pe.click('#lgGo');W(pe,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&S.length===2&&Object.keys(SOL).length>=8");pe.wait_for_timeout(500);pe.evaluate(MOCK)
    ok('aviso_en_el_panel_de_control_escolar',pe.is_visible('#hSo') and 'esperan respuesta' in pe.inner_text('#hSoT') or 'espera respuesta' in pe.inner_text('#hSoT'))
    pe.evaluate("ir('esc')");pe.wait_for_selector('#eTabs [data-et="S"]');ok('pestana_con_el_numero_de_pendientes','Solicitudes de alumnos (8)' in pe.inner_text('#eTabs [data-et="S"]'))
    pe.click('#eTabs [data-et="S"]');pe.wait_for_selector('#solPend .mod')
    tj=pe.inner_text('#solPend .mod:has-text("Beto Mena Ruiz"):has-text("Justificante")')
    ok('ve_la_solicitud_con_sus_datos_y_comprobantes','Justificante de faltas' in tj and 'Cita médica' in tj and 'Estudios de laboratorio' in tj and 'medico.pdf' in tj and 'receta.jpg' in tj and pe.locator('#solPend .mod:has-text("Beto Mena Ruiz"):has-text("Justificante") a:has-text("Ver")').count()==2)
    pe.locator('#solPend .mod:has-text("Beto Mena Ruiz"):has-text("Justificante") [data-sn]').click();ok('denegar_exige_motivo','motivo' in pe.inner_text('#solMsg').lower() and get('solicitudes/%s'%d2['id'])['data']['estado']=='pendiente')
    # primero se deniega la de la boleta de Ana para ver el mensaje; la de Beto se aprueba
    pe.locator('#solPend .mod:has-text("Ana López"):has-text("Justificante") [data-sm]').fill('El comprobante no es legible');pe.locator('#solPend .mod:has-text("Ana López"):has-text("Justificante") [data-sn]').click();W(pe,"SOL['sol1']&&SOL['sol1'].estado==='denegada'")
    ok('negativa_guardada_con_motivo',get('solicitudes/sol1')['data']['estado']=='denegada' and get('solicitudes/sol1')['data']['resp']['motivo']=='El comprobante no es legible' and get('solicitudes/sol1')['data']['resp']['por']=='Esc Dos')
    pe.locator('#solPend .mod:has-text("Beto Mena Ruiz"):has-text("Justificante") [data-sa]').click();W(pe,"SOL['%s']&&SOL['%s'].estado==='aprobada'"%(d2['id'],d2['id']))
    sa=get('solicitudes/'+d2['id'])['data'];jid=sa['justId'];ju=get('justificantes/'+jid)['data']
    ok('aprobar_genera_el_justificante_con_folio',sa['estado']=='aprobada' and ju['num']=='J-000011')
    ok('el_justificante_queda_aprobado_con_el_comprobante',ju['estado']=='Aprobado' and ju['sid']=='s2' and ju['desde']==hoy and ju['motivo']=='Cita médica' and ju['doc']['id']==d2['docs'][0]['id'] and ju['solicitud']==d2['id'] and ju['nombre']=='Beto Mena Ruiz' and ju['grupo']=='4821')
    # boleta: generar y atender
    pe.locator('#solPend .mod:has-text("Beto Mena Ruiz"):has-text("Boleta") [data-sb]').click();pe.wait_for_timeout(400)
    ok('genera_la_boleta_desde_la_solicitud',pe.evaluate("window.__sav")==['boleta-20230102-sep-dic-2026.pdf'])
    pe.evaluate("window.__sav=[]");pe.locator('#solPend .mod:has-text("Ana López"):has-text("Ene–Abr 2026") [data-sb]').click();pe.wait_for_timeout(300)
    ok('avisa_si_el_alumno_no_tiene_calificaciones_en_ese_periodo',pe.evaluate("window.__sav")==[] and 'no tiene calificaciones' in pe.inner_text('#solMsg'))
    pe.locator('#solPend .mod:has-text("Beto Mena Ruiz"):has-text("Boleta") [data-st]').click();W(pe,"Object.values(SOL).some(function(x){return x.sid==='s2'&&x.tipo==='boleta'&&x.estado==='atendida'})")
    # constancia: ir a constancias y atender
    pe.locator('#solPend .mod:has-text("Beto Mena Ruiz"):has-text("Constancia") [data-sc]').click();pe.wait_for_selector('#eN:not([hidden])');ok('ir_a_constancias_con_el_alumno_y_el_tipo',pe.input_value('#nAl')=='s2' and pe.input_value('#nTipo')=='promedio' and pe.input_value('#nDest')=='Instituto Demo')
    pe.click('#eTabs [data-et="S"]');pe.locator('#solPend .mod:has-text("Beto Mena Ruiz"):has-text("Constancia") [data-st]').click();W(pe,"Object.values(SOL).some(function(x){return x.sid==='s2'&&x.tipo==='constancia'&&x.estado==='atendida'})")
    ok('historial_de_atendidas','Aprobada' in pe.inner_text('#solHist') and 'Denegada' in pe.inner_text('#solHist') and 'Atendida' in pe.inner_text('#solHist') and 'El comprobante no es legible' in pe.inner_text('#solHist'))
    # el módulo de justificantes lo muestra
    pe.evaluate("etab('J')");ok('aparece_en_justificantes','J-0000' in pe.inner_text('#juTb') and 'Aprobado' in pe.inner_text('#juTb'))
    # ---- de regreso en el portal del alumno ----
    W(pa,"Object.values(SOL).every(function(x){return x.estado!=='pendiente'})&&Object.keys(JUS).length===2")
    tn=pa.inner_text('#poBody');ok('notificaciones_del_alumno','nuevas' in tn and 'Tu justificante' in tn and 'fue aprobado' in tn and 'Descargar justificante' in tn and 'atendió tu solicitud de boleta' in tn and 'atendió tu solicitud de constancia' in tn)
    pa.click('#poBody [data-dj]');pa.wait_for_timeout(400);qr=pa.evaluate("window.__qr");jn=ju['num']
    ok('descarga_el_justificante_con_su_qr',pa.evaluate("window.__sav")==['justificante-%s-20230102.pdf'%jn] and qr==B+'/verificar#j.%s.%s'%(jn,chk('J|%s|s2|%s|%s'%(jn,hoy,hoy))))
    ok('el_pdf_dice_que_se_puede_verificar','Verifique este justificante' in ' | '.join(pa.evaluate("window.__txt")) and 'Justificante de inasistencia' in ' | '.join(pa.evaluate("window.__txt")))
    pa.click('#poBody [data-lee]');W(pa,"Object.values(SOL).every(function(x){return x.leida===true})");ok('marcar_como_leidas','nuevas' not in pa.inner_text('#poBody').split('Mis datos')[0] and all(v['data']['leida'] for v in S_['esc2'].request.get(B+'/api/col/solicitudes').json()['docs'] if v['data']['sid']=='s2'))
    # ---- QR del justificante ----
    cx=b.new_context();pv=cx.new_page();pv.on("pageerror",lambda e:errs.append(str(e)))
    codj=chk('J|%s|s2|%s|%s'%(jn,hoy,hoy));pv.goto(B+'/verificar#j.%s.%s'%(jn,codj));pv.wait_for_selector('.sello.ok');tv=pv.inner_text('#res')
    ok('pagina_publica_del_justificante','Documento auténtico' in tv and 'justificante de inasistencia' in tv.lower() and 'Beto Mena Ruiz' in tv and jn in tv and 'Cita médica' not in tv and pv.evaluate("!document.getElementById('login')"))
    pv.goto(B+'/#j.%s.%s'%(jn,codj));pv.wait_for_selector('.sello.ok');ok('qr_con_la_direccion_del_sistema_redirige',('/verificar#j.'+jn) in pv.url)
    pv.goto(B+'/verificar#j.%s.00000000'%jn);pv.reload();pv.wait_for_selector('.sello.bad');ok('pagina_rechaza_codigo_alterado','No se pudo verificar' in pv.inner_text('#res'))
    # verificación dentro de la aplicación (versión sin servidor propio)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(JUS).length>=3");pg.evaluate("verJust('%s','%s')"%(jn,codj));pg.wait_for_selector('#dRc[open]');ok('verificacion_en_la_aplicacion','Justificante auténtico' in pg.inner_text('#rcRes') and 'Beto Mena Ruiz' in pg.inner_text('#rcRes'));pg.evaluate("document.getElementById('dRc').close()")
    # el justificante que genera control escolar a mano también lleva QR
    pg.evaluate(MOCK);pg.evaluate("justificantePDF(JUS['j1'])");pg.wait_for_timeout(300);ok('justificantes_manuales_tambien_llevan_qr',pg.evaluate("window.__qr")==B+'/verificar#j.J-000001.'+chk('J|J-000001|s1|%s|%s'%(hoy,hoy)))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
