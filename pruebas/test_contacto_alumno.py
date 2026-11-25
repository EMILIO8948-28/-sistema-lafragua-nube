import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3198;B='http://127.0.0.1:%d'%PORT;TOK='tok-ca-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_ca',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata_ca && mkdir -p /tmp/nbdata_ca')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
import atexit
atexit.register(lambda:p.terminate())
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
    raise TimeoutError(js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(12000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'");time.sleep(0.8)
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    base=lambda mat,n,**k:dict({'mat':mat,'nombre':n,'carrera':'Derecho','programa':'Derecho','ingreso':2026,'nuevo':False},**k)
    put('students/s1',base('1001','Ana Sin Contacto'))
    put('students/s2',base('1002','Beto Con Contacto',tel='7121112233',mail='beto@correo.mx'))
    put('students/s3',base('1003','Carla Ya Cambio',tel='7125556677',mail='carla@correo.mx'))
    put('students/s4',base('1004','Dora Telefono Malo',tel='726111',mail='dora@correo.mx'))
    put('students/s5',base('1005','Eli Interfaz'))
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'1001','name':'Ana','alumno':'s1','clave':'abcd-efgh'},{'u':'1002','name':'Beto','alumno':'s2','clave':'ijkm-npqr'},{'u':'1003','name':'Carla','alumno':'s3','clave':'stuv-wxyz'},{'u':'1004','name':'Dora','alumno':'s4','clave':'wxyz-abcd'},{'u':'1005','name':'Eli','alumno':'s5','clave':'efgh-ijkm'}]}),headers=HDR)
    def entra(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,u;return cx
    yo=lambda cx:cx.request.get(B+'/api/yo').json()['usuario']
    cc=lambda cx,body:cx.request.post(B+'/api/cambiar-clave',data=json.dumps(body),headers=HDR)
    # ---- 1) primer ingreso de un alumno sin teléfono ni correo ----
    a1=entra('1001','abcd-efgh');u1=yo(a1)
    ok('primer_ingreso_pide_cambiar_clave_y_contacto',u1['forzar'] is True and u1['contacto'] is True)
    ok('mientras_tanto_no_ve_datos',a1.request.get(B+'/api/col/students').status==403 and a1.request.get(B+'/api/col/students').json().get('forzar') is True)
    for nombre,cuerpo in (('sin_telefono',{'mail':'ana@correo.mx','wa':True}),('telefono_corto',{'tel':'712123','mail':'ana@correo.mx','wa':True}),('sin_correo',{'tel':'7121234567','wa':True}),('correo_mal',{'tel':'7121234567','mail':'ana@correo','wa':True}),('sin_confirmar_whatsapp',{'tel':'7121234567','mail':'ana@correo.mx'}),('whatsapp_en_falso',{'tel':'7121234567','mail':'ana@correo.mx','wa':False})):
        r=cc(a1,dict({'actual':'abcd-efgh','nueva':'clave-ana-77'},**cuerpo))
        ok('rechaza_'+nombre,r.status==400)
    ok('si_se_rechaza_la_contrasena_no_cambia',entra('1001','abcd-efgh') is not None)
    ok('mensaje_claro_de_whatsapp','WhatsApp' in cc(a1,{'actual':'abcd-efgh','nueva':'clave-ana-77','tel':'7121234567','mail':'ana@correo.mx'}).json()['error'])
    r=cc(a1,{'actual':'abcd-efgh','nueva':'clave-ana-77','tel':'+52 (712) 123-4567','mail':' Ana@Correo.MX ','wa':True})
    ok('acepta_contacto_valido_y_cambia_clave',r.status==200)
    st=ctx.request.get(B+'/api/doc/students/s1').json()['data']
    ok('guarda_telefono_a_10_digitos_y_correo_en_minusculas',st['tel']=='7121234567' and st['mail']=='ana@correo.mx')
    a1b=entra('1001','clave-ana-77');u1b=yo(a1b)
    ok('despues_ya_entra_normal',u1b['forzar'] is False and u1b['contacto'] is False and a1b.request.get(B+'/api/col/students').status==200)
    aud=ctx.request.get(B+'/api/auditoria').json() if ctx.request.get(B+'/api/auditoria').status==200 else None
    # ---- 2) formatos de teléfono ----
    a5=entra('1005','efgh-ijkm');r=cc(a5,{'actual':'efgh-ijkm','nueva':'clave-eli-77','tel':'5217121234567','mail':'eli@correo.mx','wa':True})
    ok('acepta_52_1_y_10_digitos',r.status==200 and ctx.request.get(B+'/api/doc/students/s5').json()['data']['tel']=='7121234567')
    # ---- 3) alumno que ya tiene contacto: solo cambia la contraseña ----
    a2=entra('1002','ijkm-npqr');u2=yo(a2)
    ok('con_contacto_registrado_no_se_le_pide',u2['forzar'] is True and u2['contacto'] is False)
    ok('basta_con_cambiar_la_clave',cc(a2,{'actual':'ijkm-npqr','nueva':'clave-beto-77'}).status==200)
    ok('no_se_toca_su_contacto',ctx.request.get(B+'/api/doc/students/s2').json()['data']['tel']=='7121112233')
    # ---- 4) alumno que ya cambió su clave pero no tiene contacto (o es inválido) ----
    a3=entra('1003','stuv-wxyz');cc(a3,{'actual':'stuv-wxyz','nueva':'clave-carla-77'})
    st3=ctx.request.get(B+'/api/doc/students/s3').json()['data'];st3.pop('tel');put('students/s3',st3)
    a3=entra('1003','clave-carla-77');u3=yo(a3)
    ok('sin_contacto_aunque_ya_cambio_su_clave_se_le_pide',u3['forzar'] is False and u3['contacto'] is True)
    r=a3.request.get(B+'/api/col/students');ok('hasta_registrarlo_no_ve_datos',r.status==403 and r.json().get('contacto') is True)
    ok('endpoint_contacto_rechaza_telefono_malo',a3.request.post(B+'/api/contacto',data=json.dumps({'tel':'123','mail':'carla@correo.mx','wa':True}),headers=HDR).status==400)
    ok('endpoint_contacto_guarda',a3.request.post(B+'/api/contacto',data=json.dumps({'tel':'712 888 9900','mail':'carla@correo.mx','wa':True}),headers=HDR).status==200 and ctx.request.get(B+'/api/doc/students/s3').json()['data']['tel']=='7128889900')
    ok('ya_ve_sus_datos',yo(a3)['contacto'] is False and a3.request.get(B+'/api/col/students').status==200)
    ok('el_telefono_incompleto_tambien_cuenta_como_faltante',yo(entra('1004','wxyz-abcd'))['contacto'] is True)
    ok('el_administrador_no_usa_este_endpoint',ctx.request.post(B+'/api/contacto',data=json.dumps({'tel':'7121234567','mail':'a@b.mx','wa':True}),headers=HDR).status==403)
    # ---- 5) pantalla: primer ingreso con cambio de contraseña + contacto ----
    a4=entra('1004','wxyz-abcd');cc(a4,{'actual':'wxyz-abcd','nueva':'clave-dora-77','tel':'7120001111','mail':'dora@correo.mx','wa':True});put('students/s4',base('1004','Dora Telefono Malo',tel='726111',mail='dora@correo.mx'))
    cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(12000);pa=pagina(cx);pa.goto(B+'/');W(pa,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pa.fill('#lgU','1004');pa.fill('#lgP','clave-dora-77');pa.click('#lgGo');W(pa,"document.getElementById('dCtc')&&document.getElementById('dCtc').open",20)
    ok('aparece_la_ventana_de_contacto',pa.is_visible('#ctcTel') and pa.is_visible('#ctcMail') and 'WhatsApp' in pa.inner_text('#dCtc'))
    pa.fill('#ctcTel','123');pa.fill('#ctcMail','dora@correo.mx');pa.click('#ctcOk');pa.wait_for_timeout(300)
    ok('la_ventana_avisa_si_el_telefono_esta_mal','10 dígitos' in pa.inner_text('#ctcMsg') and pa.evaluate("document.getElementById('dCtc').open"))
    pa.fill('#ctcTel','7127778899');pa.click('#ctcOk');pa.wait_for_timeout(300)
    ok('la_ventana_pide_confirmar_whatsapp','WhatsApp' in pa.inner_text('#ctcMsg'))
    pa.check('#ctcWa');pa.click('#ctcOk');W(pa,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&!document.getElementById('dCtc').open",25)
    ok('despues_de_guardar_entra_al_portal_y_queda_guardado',ctx.request.get(B+'/api/doc/students/s4').json()['data']['tel']=='7127778899')
    # primer ingreso real
    put('students/s6',base('1006','Fer Primera Vez'));ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'1006','name':'Fer','alumno':'s6','clave':'qrst-uvwx'}]}),headers=HDR)
    cx2=b.new_context(viewport={'width':1100,'height':900});cx2.set_default_timeout(12000);pb=pagina(cx2);pb.goto(B+'/');W(pb,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pb.fill('#lgU','1006');pb.fill('#lgP','qrst-uvwx');pb.click('#lgGo');W(pb,"document.getElementById('dPw')&&document.getElementById('dPw').open",20)
    ok('primer_ingreso_muestra_contrasena_y_contacto',pb.is_visible('#pwCt') and pb.is_visible('#pwTel') and pb.is_visible('#pwMail') and 'WhatsApp' in pb.inner_text('#dPw'))
    pb.fill('#pwA','qrst-uvwx');pb.fill('#pwN','clave-fer-77');pb.fill('#pwR','clave-fer-77');pb.fill('#pwMail','fer@correo.mx');pb.click('#pwOk');pb.wait_for_timeout(300)
    ok('primer_ingreso_exige_el_telefono','10 dígitos' in pb.inner_text('#pwMsg'))
    pb.fill('#pwTel','7121230000');pb.click('#pwOk');pb.wait_for_timeout(300)
    ok('primer_ingreso_exige_confirmar_whatsapp','WhatsApp' in pb.inner_text('#pwMsg'))
    pb.check('#pwWa');pb.click('#pwOk');W(pb,"typeof APP!=='undefined'&&APP!==null&&APP.rol==='alumno'&&MOD==='por'&&!document.getElementById('dPw').open",25)
    s6=ctx.request.get(B+'/api/doc/students/s6').json()['data']
    ok('primer_ingreso_guarda_telefono_correo_y_cambia_la_clave',s6['tel']=='7121230000' and s6['mail']=='fer@correo.mx' and entra('1006','clave-fer-77') is not None)
    ok('sin_errores_de_pagina',not errs)
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v]);print(errs[:3])
