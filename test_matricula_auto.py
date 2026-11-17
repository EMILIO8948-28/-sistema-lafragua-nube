import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3400;B='http://127.0.0.1:%d'%PORT;TOK='tk-ma';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata114 && mkdir -p /tmp/nbdata114')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata114',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000',LF_BAJAS_ARRANQUE_MS='600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={}
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def W(pg,js,t=60):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
CIC=datetime.date.today().year
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':1000},accept_downloads=True);ctx.set_default_timeout(20000);pg=ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=11");time.sleep(1.0)
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    plans=json.loads(ctx.request.get(B+'/api/doc/config/plans').text())['data'];plans['plans'].append({'k':'Licenciatura en Gastronomía Internacional','n':36,'col':1300,'ins':800,'rein':800,'tit':23000});put('config/plans',plans)
    put('students/ex1',{'mat':'2026PED005','nombre':'Existente Alumno Pérez','carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&S.length===1&&PL.length>=12");time.sleep(0.8)
    pg.evaluate("ir('esc');etab('A')");pg.wait_for_selector('#aMas')
    ok('las_pruebas_internas_de_la_clave_de_lista',pg.evaluate("claveLista('Ana de la Cruz Mena')")=='de la cruz mena ana' and pg.evaluate("claveLista('Luis Ángel Beltrán Ruiz')")=='beltran ruiz luis angel' and pg.evaluate("claveLista('Zoe Núñez')")=='nunez zoe' and pg.evaluate("claveLista('Cher')")=='cher')
    ok('y_de_la_clave_del_plan',pg.evaluate("codigoPlan('Pedagogía')")=='PED' and pg.evaluate("codigoPlan('Licenciatura en Gastronomía Internacional')")=='LGI' and pg.evaluate("codigoPlan('Turismo')")=='TUR' and pg.evaluate("codigoPlan('Ciencias de la Educación')")=='CED')
    pg.set_input_files('#aMasFile','/tmp/mat/sin_matricula.csv');pg.wait_for_selector('#dMas[open]');pg.wait_for_timeout(500)
    res=pg.inner_text('#masRes');det=pg.inner_text('#masDet')
    ok('acepta_un_archivo_sin_la_columna_de_matricula','13 filas leídas · 10 alumnos nuevos para cargar · 2 con matrícula o nombre repetido (se omiten) · 1 con errores (se omiten)' in res)
    ok('avisa_que_genero_las_matriculas_y_como',('10 matrículas se generaron solas' in det) and 'año de ingreso + clave del plan + número de lista' in det and '2026PED006' in det)
    ok('avisa_de_los_repetidos_por_nombre_y_del_error','ya existe un alumno con ese nombre, plan y ciclo de ingreso' in det and 'Existente Alumno Pérez' in det and 'Falta el nombre' in det)
    pg.click('#masOk');W(pg,"document.getElementById('masRes').textContent.indexOf('Carga terminada')>-1",90)
    M={s['nombre']:s['mat'] for s in pg.evaluate("S.map(function(s){return {nombre:s.nombre,mat:s.mat}})")}
    ok('pedagogia_2026_sigue_la_lista_alfabetica_despues_de_la_ultima_matricula_existente',M['Zoe Aguilar Núñez']=='2026PED006' and M['Luis Ángel Beltrán Ruiz']=='2026PED007' and M['Mateo Cruz Ibarra']=='2026PED008' and M['Ana de la Cruz Mena']=='2026PED009' and M['Valeria Ramírez Soto']=='2026PED010')
    ok('derecho_2026_empieza_en_001_por_apellidos_y_el_ciclo_vacio_usa_el_actual',M['Sin Ciclo Alumno Reyes']=='2026DER001' and M['Beto Alvarado Pérez']=='2026DER002' and M['Camila Torres Vega']=='2026DER003')
    ok('cada_ciclo_lleva_su_propio_numero',M['Regina Millán Ochoa']=='2025PED001')
    ok('un_plan_nuevo_saca_su_clave_de_las_iniciales',M['Iván Gastro Lara']=='2026LGI001')
    ok('no_duplica_a_los_repetidos',pg.evaluate("S.length")==11 and pg.evaluate("S.filter(function(s){return s.nombre==='Zoe Aguilar Núñez'}).length")==1)
    ok('guarda_el_plan_el_ciclo_y_los_datos',pg.evaluate("(function(){var s=S.find(function(x){return x.mat==='2026PED006'});return s.programa==='Pedagogía'&&s.ingreso===2026&&s.tel==='7221110104'&&s.sexo==='Femenino'})()"))
    ok('las_matriculas_son_unicas',pg.evaluate("(function(){var m={},d=0;S.forEach(function(s){if(m[s.mat])d++;m[s.mat]=1});return d})()")==0)
    ok('al_terminar_ofrece_descargar_la_lista',pg.is_visible('#masDesc'))
    with pg.expect_download() as dl:pg.click('#masDesc')
    d=dl.value;path='/tmp/mat/descarga.csv';d.save_as(path);txt=open(path,encoding='utf-8-sig',newline='').read().split('\r\n')
    ok('la_lista_descargada_trae_las_matriculas',d.suggested_filename=='alumnos_cargados_con_matricula.csv' and txt[0]=='matricula,nombre,programa,ciclo_ingreso,grupo' and '2026PED006,Zoe Aguilar Núñez,Pedagogía,2026,' in txt and '2026LGI001,Iván Gastro Lara,Licenciatura en Gastronomía Internacional,2026,' in txt and len([l for l in txt[1:] if l])==10)
    pg.evaluate("document.getElementById('dMas').close()")
    # una segunda carga del mismo archivo no duplica a nadie
    pg.set_input_files('#aMasFile','/tmp/mat/sin_matricula.csv');pg.wait_for_selector('#dMas[open]');pg.wait_for_timeout(400)
    ok('cargar_otra_vez_el_mismo_archivo_no_duplica','0 alumnos nuevos para cargar' in pg.inner_text('#masRes') and '12 con matrícula o nombre repetido' in pg.inner_text('#masRes'))
    pg.evaluate("document.getElementById('dMas').close()")
    # mezcla: una con matrícula propia y otra automática
    pg.set_input_files('#aMasFile','/tmp/mat/mixto.csv');pg.wait_for_selector('#dMas[open]');pg.wait_for_timeout(400)
    ok('mezcla_una_matricula_propia_nueva_y_una_automatica','2 alumnos nuevos para cargar' in pg.inner_text('#masRes') and '2026PED002' in pg.inner_text('#masDet') and '2026PED011' in pg.inner_text('#masDet') and '1 matrícula se generó sola' in pg.inner_text('#masDet'))
    pg.click('#masOk');W(pg,"document.getElementById('masRes').textContent.indexOf('Carga terminada')>-1",60)
    ok('la_siguiente_automatica_continua_despues_de_la_mayor',pg.evaluate("S.find(function(s){return s.nombre==='Nora Quintero Díaz'}).mat")=='2026PED011')
    ok('la_matricula_propia_se_respeta',pg.evaluate("S.find(function(s){return s.nombre==='Manual Persona López'}).mat")=='2026PED002')
    # archivo sin las columnas obligatorias
    open('/tmp/mat/malo.csv','w',encoding='utf-8').write('matricula,telefono\n1,7221110000\n')
    pg.evaluate("document.getElementById('dMas').close()")
    msg=[]
    pg.on("dialog",lambda d:msg.append(d.message))
    pg.set_input_files('#aMasFile','/tmp/mat/malo.csv');pg.wait_for_timeout(800)
    ok('sin_nombre_y_programa_lo_explica',any('columnas nombre y programa' in m and 'se genera sola' in m for m in msg))
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    pg.set_input_files('#aMasFile','/tmp/mat/sin_matricula.csv');pg.wait_for_timeout(300)
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
