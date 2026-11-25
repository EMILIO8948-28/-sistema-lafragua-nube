"""Choques de horario (docente, aula, grupo), resultados de la evaluación para el docente y llave de evaluación incluida en los respaldos."""
import subprocess,time,json,os,re,urllib.request
from playwright.sync_api import sync_playwright
PORT=3143;B='http://127.0.0.1:%d'%PORT;DD='/tmp/nbdata_dch'
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
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&typeof DBH!=='undefined'&&DBH!==null")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    for i,n in enumerate(['Ana','Beto','Carla','Diego'],1):put('students/s%d'%i,{'mat':'100%d'%i,'nombre':n+' Prueba','carrera':'Derecho','programa':'Derecho','ingreso':2025,'nuevo':False})
    put('docentes/d1',{'nombre':'Prof. Uno','esp':'Educación','asig':[]});put('docentes/d2',{'nombre':'Prof. Dos','esp':'Historia','asig':[]})
    put('grupos/g1',{'num':'1111','plan':'Derecho','per':PER,'cuat':2,'alumnos':['s1','s2','s3','s4']})
    mat=lambda nom,plan,cuat,d,ini,fin,per=PER,**k:dict({'per':per,'plan':plan,'cuat':cuat,'nom':nom,'ini':ini,'fin':fin},**dict(({'docId':d} if d else {}),**k))
    put('materias/m1',mat('Civil I','Derecho',2,'d1','09:00','11:00',ev='2026-11-07',aula='A1'))
    put('materias/m2',mat('Civil II','Derecho',2,'d1','11:00','12:00',ev='2026-11-07'))   # pegada a m1: no hay choque
    def usr(u,name,rol,modulos=None,doc=None):
        d={'u':u,'name':name,'rol':rol,'clave':'clave-%s-123'%u}
        if modulos is not None:d['modulos']=modulos
        if doc:d['doc']=doc
        r=ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR);assert r.status==200,(u,r.status,r.text())
    usr('prof1','Dora Docente','docente',doc='d1');usr('prof2','Dario Docente','docente',doc='d2');usr('ver1','Eva Ver','personalizado',{'escolar':'ver'})
    ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'100%d'%i,'name':'A%d'%i,'alumno':'s%d'%i,'clave':'abcd-efg%d'%i} for i in range(1,5)]}),headers=HDR)
    def sesion(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status,r.text());return cx
    def alumno(i):
        cx=sesion('100%d'%i,'abcd-efg%d'%i);cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efg%d'%i,'nueva':'clave-nueva-7%d'%i}),headers=HDR);return sesion('100%d'%i,'clave-nueva-7%d'%i)
    AL=[alumno(i) for i in range(1,5)];P1=sesion('prof1','clave-prof1-123');P2=sesion('prof2','clave-prof2-123');V1=sesion('ver1','clave-ver1-123')
    post=lambda cx,o:cx.request.post(B+'/api/evaldoc',data=json.dumps(o),headers=HDR)
    docente=lambda cx:cx.request.get(B+'/api/evaldoc/docente')
    # ============ Resultados para el docente ============
    ok('docente_sin_respuestas_no_ve_nada',docente(P1).status==200 and all(m['n']==0 for m in docente(P1).json()['materias']))
    R5=[5]*20;R3=[3]*20
    post(AL[0],{'mid':'m1','r':R5,'g':5,'fort':'Claro','mej':'','com':'Excelente trato'});post(AL[1],{'mid':'m1','r':R3,'g':3,'fort':'','mej':'Más ejemplos','com':''})
    m1=[m for m in docente(P1).json()['materias'] if m['mid']==('m1')] if 'mid' in (docente(P1).json()['materias'] or [{}])[0] else [m for m in docente(P1).json()['materias'] if m['nom']=='Civil I']
    ok('con_2_respuestas_se_oculta',len(m1)==1 and m1[0]['n']==2 and m1[0]['oculto'] is True and not m1[0].get('asp') and not m1[0].get('com'))
    ok('docente_ve_solo_sus_asignaturas',all(m['nom'] in ('Civil I','Civil II') for m in docente(P1).json()['materias']) and docente(P2).json()['materias']==[])
    post(AL[2],{'mid':'m1','r':[4]*20,'g':4,'fort':'','mej':'','com':'Buen curso'})
    d=docente(P1).json();m1=[m for m in d['materias'] if m['nom']=='Civil I'][0]
    ok('con_3_respuestas_se_muestra',m1['n']==3 and not m1.get('oculto') and len(m1['asp'])==20 and abs(m1['asp'][0]-4)<0.01)
    ok('comentarios_visibles_sin_identidad',sorted(m1['com'])==['Buen curso','Excelente trato'] and 'Más ejemplos' in m1['mej'])
    txt=docente(P1).text()
    ok('respuesta_no_contiene_datos_de_alumnos',not any(x in txt for x in ['"s1"','"s2"','"s3"','Ana','Beto','"alumno"','"user"']))
    ok('minimo_3',d['minimo']==3)
    ok('alumno_no_usa_vista_docente',docente(AL[0]).status==403)
    ok('escolar_ver_no_usa_vista_docente',docente(V1).status in (403,404))
    ok('docente_no_pasa_a_resultados_de_escolar',P1.request.get(B+'/api/evaldoc/resultados').status==403)
    pp=pagina(P1);pp.goto(B+'/');W(pp,"typeof APP!=='undefined'&&APP!==null&&ROL==='docente'&&typeof EVDD!=='undefined'&&EVDD!==null")
    W(pp,"document.getElementById('dmEv')&&document.getElementById('dmEv').innerText.indexOf('Cómo te evaluaron')>-1")
    pp.evaluate("document.querySelectorAll('#dmEv details').forEach(function(d){d.open=true})");t=pp.inner_text('#dmEv')
    ok('pantalla_docente_muestra_resultado',('Civil I' in t) and ('3 respuestas' in t) and ('Excelente trato' in t) and ('Más ejemplos' in t))
    ok('pantalla_muestra_barras_por_aspecto',pp.locator('#dmEv .evr-f').count()>=20)
    pq=pagina(P2);pq.goto(B+'/');W(pq,"typeof APP!=='undefined'&&APP!==null&&ROL==='docente'");pq.wait_for_timeout(800)
    ok('otro_docente_no_ve_el_bloque',pq.inner_text('#dmEv').strip()=='')
    # ============ Choques de horario ============
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(MAT).length>=2")
    ok('sin_choques_inicialmente_tiempos_pegados',pg.evaluate("choques().length")==0)
    put('materias/m3',mat('Civil III','Derecho',3,'d1','10:00','12:00',aula='B2'))              # mismo docente que m1, traslape
    put('materias/m4',mat('Historia','Pedagogía',1,'d2','10:30','11:30',aula=' a1 '))            # misma aula que m1 (sin importar mayúsculas)
    put('materias/m5',mat('Derecho Romano','Derecho',2,'d2','09:00','10:00'))                   # mismo grupo que m1
    put('materias/m6',mat('Otro periodo','Derecho',2,'d1','09:00','11:00',per='Ene–Abr 2027',aula='A1'))   # otro periodo: no choca
    put('materias/m7',mat('Sin horario','Derecho',2,'d1','',''))                                 # sin horario: se ignora
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(MAT).length===7")
    tipos=pg.evaluate("choques().map(function(c){return c.t+':'+[c.a,c.b].sort().join('-')}).sort()")
    ok('detecta_docente_aula_y_grupo',tipos==['Aula:m1-m4','Docente:m1-m3','Docente:m2-m3','Grupo:m1-m5'])
    ok('horarios_pegados_no_chocan',not any(t.endswith('m1-m2') for t in tipos))
    ok('otro_periodo_no_choca',not any('m6' in t for t in tipos))
    ok('sin_horario_no_choca',not any('m7' in t for t in tipos))
    pg.evaluate("ir('esc');etab('K')");W(pg,"ETAB==='K'")
    ok('aviso_en_el_calendario',('choques de horario' in pg.inner_text('#mChoq')) and ('Docente «Prof. Uno»' in pg.inner_text('#mChoq')) and ('Aula' in pg.inner_text('#mChoq')))
    put('materias/m3',mat('Civil III','Derecho',3,'d1','12:00','13:00',aula='B2'))
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(MAT).length===7")
    t2=pg.evaluate("choques().map(function(c){return c.t+':'+[c.a,c.b].sort().join('-')}).sort()")
    ok('al_corregir_desaparece_el_choque',not any(x.startswith('Docente:m1-m3') for x in t2))
    # ============ La llave de evaluación va en el respaldo ============
    r=ctx.request.post(B+'/api/respaldos/ejecutar',data='{}',headers=HDR);ok('pide_respaldo',r.status in (200,202))
    for _ in range(100):
        e=ctx.request.get(B+'/api/respaldos').json()
        if not e['estado'].get('corriendo') and e.get('locales'):break
        time.sleep(0.3)
    loc=ctx.request.get(B+'/api/respaldos').json()['locales']
    ok('hay_respaldo_en_el_servidor',len(loc)>=1)
    import zipfile,io
    zb=ctx.request.get(B+'/api/respaldos/descargar/'+loc[0]['nombre']).body()
    z=zipfile.ZipFile(io.BytesIO(zb));nm=z.namelist()
    ok('respaldo_incluye_la_llave','evdoc.key' in nm and 'lafragua.db' in nm and 'manifest.json' in nm)
    llave=open(DD+'/evdoc.key').read().strip()
    ok('la_llave_del_respaldo_es_la_misma',z.read('evdoc.key').decode().strip()==llave and len(llave)>=32)
    # restaurar en otra carpeta con el programa de restauración
    os.system('rm -rf /tmp/nbdata_dch_rest && mkdir -p /tmp/nbdata_dch_rest')
    open('/tmp/respaldo_dch.zip','wb').write(zb)
    rr=subprocess.run(['node','restaurar.js','/tmp/respaldo_dch.zip','--datos','/tmp/nbdata_dch_rest','--si'],cwd='/tmp/nb',capture_output=True,text=True)
    ok('restaura_sin_error',rr.returncode==0)
    ok('restaura_la_llave',os.path.exists('/tmp/nbdata_dch_rest/evdoc.key') and open('/tmp/nbdata_dch_rest/evdoc.key').read().strip()==llave)
    ok('sin_errores_de_pagina',not errs)
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
