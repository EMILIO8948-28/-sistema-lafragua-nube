import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3116;B='http://127.0.0.1:%d'%PORT;TOK='tok-cu-123'
os.system('rm -rf /tmp/nbdata47 && mkdir -p /tmp/nbdata47')
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata47',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
def W(pg,js,t=30):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError('espera: '+js[:90])
HDR={'Content-Type':'application/json','x-lafragua':'1'}
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1100,'height':900});ctx.set_default_timeout(15000)
    dlg=[]
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:(dlg.append(d.message),d.accept()));return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    def put(path,obj):assert ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR).status==200,path
    def get(path):return ctx.request.get(B+'/api/doc/'+path).json()
    plan=lambda k:[x for x in get('config/plans')['data']['plans'] if x['k']==k][0]
    for i in (1,2,3):put('students/s%d'%i,{'mat':'2025000%d'%i,'nombre':'Alumno %d'%i,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2025,'nuevo':False})
    put('ledger/s1',{'pagos':[{'id':'p1','fecha':'2026-10-01','monto':76200,'metodo':'Efectivo','estado':'confirmado','folio':'R-000001'}]})
    put('ledger/s2',{'pagos':[{'id':'p2','fecha':'2026-10-01','monto':1300,'metodo':'Efectivo','estado':'confirmado','folio':'R-000002'}]})
    put('catalogo/pedagogia',{'plan':'Pedagogía','items':[{'id':'ped-1','cuat':1,'clave':'P1','nom':'Uno','cred':None,'hrs':None,'ct':0,'pdf':0},{'id':'ped-2','cuat':3,'clave':'P3','nom':'Tres','cred':None,'hrs':None,'ct':0,'pdf':0}]})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':'Sep–Dic 2026','cuat':4,'alumnos':['s1','s2','s3']})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===3&&Object.keys(GRP).length===1&&Object.keys(CATA).length>=1")
    col=lambda:pg.evaluate("(function(){var s=S.find(function(x){return x.id==='s2'});return cargos(s).filter(function(c){return /^Colegiatura/.test(c.c)}).length})()")
    ok('punto_de_partida_36_colegiaturas',plan('Pedagogía')['n']==36 and col()==36)
    pg.evaluate("ir('esc');etab('P')");pg.wait_for_selector('#pCu');pg.select_option('#pPlan','Pedagogía');pg.evaluate("renderPlan()")
    ok('boton_para_el_administrador',pg.is_visible('#pCu'))
    pg.click('#pCu');pg.wait_for_selector('#dCu[open]')
    ok('abre_con_el_plan_y_su_duracion_actual',pg.input_value('#cuPlan')=='Pedagogía' and pg.input_value('#cuN')=='9' and '9 cuatrimestres' in pg.inner_text('#cuDur') and '36 colegiaturas y 8 reinscripciones' in pg.inner_text('#cuDur'))
    ok('dice_el_cuatrimestre_mas_alto_en_uso','más alto con asignaturas, grupos o clases: 4' in pg.inner_text('#cuMin'))
    pg.fill('#cuN','13');ok('rechaza_mas_de_12','0 a 12' in pg.inner_text('#cuDur'));pg.click('#cuOk');ok('no_guarda_mas_de_12','0 a 12' in pg.inner_text('#cuMsg') and plan('Pedagogía')['n']==36)
    pg.fill('#cuN','9.3');pg.click('#cuOk');ok('solo_acepta_medios_cuatrimestres','0 a 12' in pg.inner_text('#cuMsg'))
    pg.fill('#cuN','3');pg.click('#cuOk');ok('no_deja_bajar_de_un_cuatrimestre_con_grupos_o_asignaturas','cuatrimestre 4' in pg.inner_text('#cuMsg') and 'Muévelas o quítalas' in pg.inner_text('#cuMsg') and plan('Pedagogía')['n']==36)
    pg.fill('#cuN','9');pg.click('#cuOk');ok('mismo_valor_no_hace_nada','ya tiene esa duración' in pg.inner_text('#cuMsg'))
    # ---- reducir a 8 ----
    pg.fill('#cuN','8');imp=pg.inner_text('#cuImp')
    ok('avisa_el_efecto_antes_de_guardar','de 9 a 8 cuatrimestres (36 → 32 colegiaturas)' in imp and '3 alumnos' in imp and '1 alumno ya ha pagado más' in imp and 'saldo a favor' in imp)
    ok('el_aviso_no_cambia_los_datos_todavia',col()==36 and plan('Pedagogía')['n']==36)
    dlg.clear();pg.click('#cuOk');W(pg,"!document.getElementById('dCu').open");time.sleep(0.8)
    ok('pide_confirmar_con_el_resumen',any('¿Cambiar la duración del plan?' in d and 'Se recalculan los cobros de 3 alumnos' in d for d in dlg))
    ok('guarda_la_nueva_duracion',plan('Pedagogía')['n']==32 and pg.evaluate("PL.find(function(p){return p.k==='Pedagogía'}).n")==32)
    ok('los_cobros_se_recalculan',col()==32 and pg.evaluate("(function(){var s=S.find(function(x){return x.id==='s2'});return cargos(s).filter(function(c){return /^Reinscripci/.test(c.c)}).length})()")==7)
    ok('la_pantalla_dice_los_cuatrimestres_nuevos','8 cuatrimestres' in pg.inner_text('#pJMsg') and 'el plan tiene 8' in pg.inner_text('#pRes'))
    # ---- medio cuatrimestre ----
    pg.click('#pCu');pg.fill('#cuN','10.5');ok('muestra_10_cuatrimestres_y_medio','10 cuatrimestres y medio' in pg.inner_text('#cuDur') and '3 años y 6 meses' in pg.inner_text('#cuDur') and '42 colegiaturas' in pg.inner_text('#cuDur'));pg.click('#cuOk');W(pg,"!document.getElementById('dCu').open");time.sleep(0.6)
    ok('guarda_10_5_como_42_colegiaturas',plan('Pedagogía')['n']==42 and col()==42 and 'el plan tiene 10 cuatrimestres y medio' in pg.inner_text('#pRes'))
    # ---- otro plan sin colegiaturas ----
    pg.click('#pCu');pg.select_option('#cuPlan','Doctorado');ok('doctorado_dura_4_cuatrimestres_por_defecto',pg.input_value('#cuN')=='4' and '1 año y 4 meses' in pg.inner_text('#cuDur') and '16 colegiaturas' in pg.inner_text('#cuDur'));pg.fill('#cuN','6');pg.click('#cuOk');W(pg,"!document.getElementById('dCu').open");time.sleep(0.5)
    ok('cambia_la_duracion_de_otro_plan',plan('Doctorado')['n']==24)
    # ---- costos y planes (Finanzas) ----
    pg.evaluate("ir('pagos')");pg.click('#bPl');pg.wait_for_selector('#dPl[open]')
    ok('la_columna_ahora_son_cuatrimestres','Cuatrimestres' in pg.inner_text('#dPl thead') and pg.input_value('#plB tr:has-text("Pedagogía") input[data-f="cuat"]')=='10.5' and '42 colegiaturas · 10 reinscripc.' in pg.inner_text('#plB tr:has-text("Pedagogía")'))
    pg.fill('#plB tr:has-text("Pedagogía") input[data-f="cuat"]','9');ok('recalcula_en_vivo','36 colegiaturas · 8 reinscripc.' in pg.inner_text('#plB tr:has-text("Pedagogía")'))
    pg.fill('#plB tr:has-text("Pedagogía") input[data-f="cuat"]','9.3');ok('avisa_si_el_numero_no_sirve','revisa el número' in pg.inner_text('#plB tr:has-text("Pedagogía")'))
    dlg.clear();pg.click('#plOk');pg.wait_for_timeout(500);ok('no_guarda_numeros_invalidos',any('van de 0 a 12' in d for d in dlg) and plan('Pedagogía')['n']==42 and pg.evaluate("document.getElementById('dPl').open"))
    dlg.clear();pg.fill('#plB tr:has-text("Pedagogía") input[data-f="cuat"]','3');pg.click('#plOk');pg.wait_for_timeout(500);ok('tampoco_baja_de_donde_ya_hay_grupos',any('cuatrimestre 4' in d for d in dlg) and plan('Pedagogía')['n']==42)
    dlg.clear();pg.fill('#plB tr:has-text("Pedagogía") input[data-f="cuat"]','9');pg.click('#plOk');W(pg,"!document.getElementById('dPl').open");time.sleep(0.8)
    ok('guarda_desde_costos_y_pide_confirmar',plan('Pedagogía')['n']==36 and any('de 10.5 a 9 cuatrimestres (42 → 36 colegiaturas)' in d for d in dlg))
    pg.click('#bPl');dlg.clear();pg.fill('#plB tr:has-text("Derecho") input[data-f="col"]','1400');pg.click('#plOk');W(pg,"!document.getElementById('dPl').open");time.sleep(0.6)
    ok('cambiar_solo_un_costo_no_pide_confirmacion_ni_toca_los_cuatrimestres',plan('Derecho')['col']==1400 and plan('Derecho')['n']==36 and not dlg and plan('Pedagogía')['n']==36)
    # ---- la cobranza del servidor usa la nueva duración ----
    put('config/cobranza',{'activa':False})
    v=ctx.request.get(B+'/api/cobranza/vista');ok('el_servidor_lee_los_planes_con_la_duracion_nueva',v.status==200)
    # ---- permisos ----
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    cx=b.new_context(viewport={'width':1100,'height':900});cx.set_default_timeout(15000);pe=pagina(cx);pe.goto(B+'/');W(pe,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pe.fill('#lgU','esc2');pe.fill('#lgP','clave-esc2-123');pe.click('#lgGo');W(pe,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&S.length===3")
    pe.evaluate("ir('esc');etab('P')");dlg.clear();pe.evaluate("abreCu()");ok('control_escolar_no_cambia_cuatrimestres',any('Solo el Administrador' in d for d in dlg) and not pe.is_visible('#dCu'))
    ok('el_servidor_tampoco_lo_permite',cx.request.put(B+'/api/doc/config/plans',data=json.dumps({'plans':[]}),headers=HDR).status==403)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:3])
    b.close()
p.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
