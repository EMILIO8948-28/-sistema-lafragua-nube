import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3094;B='http://127.0.0.1:%d'%PORT;TOK='tok-hi-123'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata24',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
os.system('rm -rf /tmp/nbdata24 /tmp/hi && mkdir -p /tmp/nbdata24 /tmp/hi')
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
    raise TimeoutError(js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
SRC='/mnt/user-data/outputs/carga_pedagogia_plan_y_contenidos.json'
D=json.load(open(SRC,encoding='utf-8'));CAT=D['colecciones']['catalogo']['pedagogia']['items']
def clave(c):return [i for i in CAT if i['clave']==c][0]
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    put('catalogo/pedagogia',D['colecciones']['catalogo']['pedagogia'])
    for s,(mat,nom,ing,plan) in {'s1':('20230101','Ana López Ramírez',2023,'Pedagogía'),'s2':('20220205','Daniela Torres Vega',2022,'Pedagogía'),'s3':('20230999','Luis Sin Plan',2023,'Derecho')}.items():
        put('students/'+s,{'mat':mat,'nombre':nom,'carrera':plan,'programa':plan,'ingreso':ing,'nuevo':False})
    # una calificación ya capturada en un grupo para una asignatura del plan
    put('calif/s1',{'items':[{'id':'g1','mid':'m-grupo','mat':'Teoría pedagógica','plan':'Pedagogía','per':'Sep–Dic 2023','cuat':1,'doc':'X','cal':9.0,'fecha':'2024-01-01'}]})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===3&&catItems('Pedagogía').length===47&&itemsDe(S[0].id).length>=0")
    pg.evaluate("ir('esc')");pg.wait_for_selector('#eTabs [data-et="H"]')
    ok('pestana_visible_para_el_administrador',pg.is_visible('#eTabs [data-et="H"]'))
    pg.click('#eTabs [data-et="H"]');pg.wait_for_selector('#eH:not([hidden])')
    ok('aviso_de_que_no_genera_cobros','no generan cobros' in pg.inner_text('#eH') and 'menores a 8.0' in pg.inner_text('#hExtraT') and not pg.is_checked('#hExtra'))
    # ---- un alumno ----
    pg.fill('#hAl','20230101 — Ana López Ramírez');pg.wait_for_selector('#hGrid table')
    ok('muestra_el_plan_por_cuatrimestre',pg.locator('#hGrid h2').count()==9 and pg.locator('#hGrid input[data-hid]').count()==47 and 'Pedagogía' in pg.inner_text('#hInfo') and 'ingreso 2023' in pg.inner_text('#hInfo'))
    ok('periodo_por_defecto_segun_el_ingreso',pg.input_value('#hGrid select[data-hp="1"]')=='Sep–Dic 2023' and pg.input_value('#hGrid select[data-hp="2"]')=='Ene–Abr 2024' and pg.input_value('#hGrid select[data-hp="3"]')=='May–Ago 2024' and pg.input_value('#hGrid select[data-hp="4"]')=='Sep–Dic 2024' and pg.input_value('#hGrid select[data-hp="9"]')=='May–Ago 2026')
    t1=pg.locator('#hGrid input[data-hid]').filter(has=pg.locator('xpath=.')).first
    fila=lambda cl:pg.locator('#hGrid tr:has-text("%s")'%clave(cl)['nom']).first
    ok('lo_capturado_en_un_grupo_no_se_toca',fila('LP02').locator('input').is_disabled() and fila('LP02').locator('input').input_value()=='9' and 'Ya capturada en un grupo' in fila('LP02').inner_text())
    vals={'LP01':'9.5','LP03':'8,5','LP04':'7','LP05':'10','LP06':'6.5'}
    for cl,v in vals.items():fila(cl).locator('input').fill(v)
    pg.click('#hGuarda');W(pg,"document.getElementById('hMsg').textContent.indexOf('Listo')===0")
    it=get('calif/s1')['data']['items'];hist=[i for i in it if i.get('hist')]
    ok('guarda_en_el_historial_del_alumno',len(hist)==5 and all(i['per']=='Sep–Dic 2023' and i['cuat']==1 and i['plan']=='Pedagogía' and i['doc']=='' for i in hist) and sorted((i['mat'],i['cal']) for i in hist)==sorted([(clave('LP01')['nom'],9.5),(clave('LP03')['nom'],8.5),(clave('LP04')['nom'],7.0),(clave('LP05')['nom'],10.0),(clave('LP06')['nom'],6.5)]))
    ok('conserva_la_calificacion_del_grupo',any(i.get('mid')=='m-grupo' and i['cal']==9.0 for i in it) and len(it)==6)
    ok('mensaje_con_avance_de_egreso','5 calificaciones nuevas' in pg.inner_text('#hMsg') and '4 de 47' in pg.inner_text('#hMsg'))
    ok('cuenta_para_promedio_y_egreso',pg.evaluate("progEgreso(S.find(function(s){return s.id==='s1'})).apr")==4 and abs(pg.evaluate("promedio('s1')")-8.42)<0.01)
    ok('no_genera_cobro_de_extraordinario',pg.evaluate("extraCargos(S.find(function(s){return s.id==='s1'})).length")==0)
    # ---- volver a abrir: aparece lo capturado; corregir y quitar ----
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===3&&itemsDe(S.find(function(s){return s.id==='s1'}).id).length===6");pg.evaluate("ir('esc');etab('H')");pg.fill('#hAl','20230101 — Ana López Ramírez');pg.wait_for_selector('#hGrid table')
    ok('muestra_lo_ya_capturado',fila('LP01').locator('input').input_value()=='9.5' and fila('LP06').locator('input').input_value()=='6.5')
    fila('LP01').locator('input').fill('10');fila('LP06').locator('input').fill('');fila('LP07').locator('input').fill('9');pg.locator('#hGrid select[data-hp="2"]').select_option('Ene–Abr 2025')
    pg.click('#hGuarda');W(pg,"document.getElementById('hMsg').textContent.indexOf('Listo')===0")
    it={i['mat']:i for i in get('calif/s1')['data']['items']}
    ok('corrige_quita_y_agrega',it[clave('LP01')['nom']]['cal']==10 and clave('LP06')['nom'] not in it and it[clave('LP07')['nom']]['cal']==9 and it[clave('LP07')['nom']]['per']=='Ene–Abr 2025' and it[clave('LP03')['nom']]['per']=='Sep–Dic 2023')
    # ---- generar cobro de extraordinario solo si se pide ----
    pg.check('#hExtra');fila('LP08').locator('input').fill('7.5');pg.evaluate("document.getElementById('hMsg').textContent=''");pg.click('#hGuarda');W(pg,"document.getElementById('hMsg').textContent.indexOf('Listo')===0")
    ex=pg.evaluate("extraCargos(S.find(function(s){return s.id==='s1'})).map(function(c){return c.c})");ok('con_la_casilla_si_genera_el_cargo',len(ex)==1 and 'Historia de la educación en México' in ex[0])
    pg.uncheck('#hExtra')
    # ---- orden cronológico de los periodos ----
    ok('periodos_en_orden',pg.evaluate("perDe('s1').join('|')")=='Sep–Dic 2023|Ene–Abr 2025|' .replace('|','|') or pg.evaluate("perDe('s1')")==sorted(pg.evaluate("perDe('s1')"),key=lambda p:(int(p[-4:])*3+{'Sep':0,'Ene':1,'May':2}[p[:3]]-(0 if p[:3]=='Sep' else 3))))
    pg.evaluate("openPf('s1')");pg.wait_for_selector('#dPf[open]');ok('boleta_del_historial',pg.locator('#pfPer option').count()>=2 and 'Cuatrimestre 1' in pg.inner_text('#pfPer'));pg.evaluate("document.getElementById('dPf').close()")
    # ---- alumno sin asignaturas en su plan ----
    pg.fill('#hAl','20230999 — Luis Sin Plan');pg.wait_for_selector('#hGrid p')
    ok('plan_sin_asignaturas_avisa','aún no tiene asignaturas' in pg.inner_text('#hGrid') and pg.is_hidden('#hGuarda'))
    pg.fill('#hAl','');ok('sin_alumno_no_hay_formulario',pg.locator('#hGrid table').count()==0)
    # ---- calificaciones fuera de rango ----
    pg.fill('#hAl','20220205 — Daniela Torres Vega');pg.wait_for_selector('#hGrid table');fila('LP01').locator('input').fill('11');pg.click('#hGuarda');ok('rechaza_calificacion_fuera_de_rango','0 a 10' in pg.inner_text('#hMsg') and 'calif/s2' and get('calif/s2')['exists'] is False)
    # ---- CSV ----
    csv='\\n'.join(['matricula,cuatrimestre,clave,asignatura,calificacion,periodo',
      '20220205,1,LP01,,9.5,Sep-Dic 2022',
      '20220205,1,,Teoría pedagógica,8,',
      '20220205,2,LP07,,"9,5",Ene–Abr 2023',
      '20220205,2,LP08,,,',
      '20220205,1,LP01,,9.8,Sep–Dic 2022',
      '20230101,1,,Teoría pedagógica,6,',
      '20230101,3,LP13,,7,may-ago 2024',
      '99999999,1,LP01,,9,',
      '20220205,1,LP99,,9,',
      '20220205,1,LP03,,11,',
      '20220205,1,LP04,,9,Verano 2022',
      '20230999,1,LP01,,9,'])
    open('/tmp/hi/h.csv','w',encoding='utf-8').write(csv.replace('\\n','\n'))
    pg.set_input_files('#hFile','/tmp/hi/h.csv');pg.wait_for_selector('#hOk')
    rs=pg.inner_text('#hRes')
    ok('resumen_del_csv','4 calificaciones listas para 2 alumnos' in rs and '1 omitidas porque ya estaban capturadas en un grupo' in rs and '1 repetidas' in rs and '1 sin calificación' in rs and '5 con error' in rs)
    ok('lista_los_errores_con_su_fila','Fila 9' in rs and 'no existe' in rs and 'LP99' in rs and '11' in rs and 'Verano 2022' in rs and 'aún no tiene asignaturas' in rs)
    ok('no_carga_nada_hasta_confirmar',get('calif/s2')['exists'] is False)
    pg.click('#hOk');W(pg,"document.getElementById('hMsg').textContent.indexOf('Listo')===0")
    c2={i['mat']:i for i in get('calif/s2')['data']['items']}
    ok('carga_a_varios_alumnos','Listo: 4 calificaciones cargadas de 2 alumnos' in pg.inner_text('#hMsg') and len(c2)==3)
    ok('clave_o_nombre_coma_decimal_y_periodo',c2[clave('LP01')['nom']]['cal']==9.8 and c2[clave('LP01')['nom']]['per']=='Sep–Dic 2022' and c2[clave('LP02')['nom']]['cal']==8 and c2[clave('LP02')['nom']]['per']=='Sep–Dic 2022' and c2[clave('LP07')['nom']]['cal']==9.5 and c2[clave('LP07')['nom']]['per']=='Ene–Abr 2023' and all(i['hist'] for i in c2.values()))
    c1={i['mat']:i for i in get('calif/s1')['data']['items']}
    ok('no_pisa_lo_del_grupo_y_agrega_lo_demas',c1[clave('LP02')['nom']].get('mid')=='m-grupo' and c1[clave('LP02')['nom']]['cal']==9.0 and c1[clave('LP13')['nom']]['cal']==7 and c1[clave('LP13')['nom']]['per']=='May–Ago 2024')
    pg.set_input_files('#hFile','/tmp/hi/h.csv');pg.wait_for_selector('#hOk');pg.evaluate("document.getElementById('hMsg').textContent=''");pg.click('#hOk');W(pg,"document.getElementById('hMsg').textContent.indexOf('Listo')===0")
    ok('volver_a_cargar_no_duplica',len(get('calif/s2')['data']['items'])==3)
    open('/tmp/hi/malo.csv','w').write('a,b\n1,2\n');pg.set_input_files('#hFile','/tmp/hi/malo.csv');pg.wait_for_timeout(400);ok('csv_sin_columnas_avisa','Faltan columnas' in pg.inner_text('#hMsg'))
    pg.evaluate("window.__sav=[];saveFile=function(n,b){window.__sav.push([n,b]);return Promise.resolve()};0");pg.click('#hTpl');pg.wait_for_timeout(200);sv=pg.evaluate("window.__sav");ok('plantilla_csv',sv[0][0]=='plantilla_calificaciones_anteriores.csv' and 'matricula,cuatrimestre,clave,asignatura,calificacion,periodo' in sv[0][1])
    # ---- permisos ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    def entra(u,c):
        cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
        pp.fill('#lgU',u);pp.fill('#lgP',c);pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&typeof S!=='undefined'&&S.length===3");return pp
    pc=entra('caja1','clave-caja-123');pc.evaluate("ir('esc')");ok('caja_no_ve_la_pestana',pc.is_hidden('#eTabs [data-et="H"]'))
    pe=entra('esc2','clave-esc2-123');pe.evaluate("ir('esc')");ok('quien_edita_control_escolar_la_ve',pe.is_visible('#eTabs [data-et="H"]'))
    pe.click('#eTabs [data-et="H"]');pe.fill('#hAl','20220205 — Daniela Torres Vega');pe.wait_for_selector('#hGrid table');pe.locator('#hGrid tr:has-text("%s") input'%clave('LP09')['nom']).first.fill('8');pe.click('#hGuarda');W(pe,"document.getElementById('hMsg').textContent.indexOf('Listo')===0")
    ok('quien_edita_control_escolar_guarda_sin_autorizacion',not pe.evaluate("document.getElementById('dAu').open") and len(get('calif/s2')['data']['items'])==4)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
