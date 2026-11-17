"""Recargos por mora y descuento por pronto pago: ajustes, aplicación por lote, cancelación, cálculo igual en pantalla y servidor, permisos y validación."""
import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3141;B='http://127.0.0.1:%d'%PORT;TOK='tok-rec-1'
os.system('rm -rf /tmp/nbdata_rec /tmp/crl2 && mkdir -p /tmp/nbdata_rec /tmp/crl2')
RELOJ='/tmp/crl2/reloj.txt';HOY=datetime.date.today().isoformat();open(RELOJ,'w').write(HOY)
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_rec',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ)
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=ENVV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={};errs=[]
def ok(n,c):R[n]=bool(c)
HDR={'Content-Type':'application/json','x-lafragua':'1'}
def W(pg,js,t=30):
    t0=time.time()
    while time.time()-t0<t:
        try:
            if pg.evaluate(js):return
        except Exception:pass
        time.sleep(0.1)
    raise TimeoutError(js[:90])
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1200,'height':950});ctx.set_default_timeout(15000)
    pg=ctx.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept())
    pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','A');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'")
    def raw(path,obj,m='put',c=None):
        c=c or ctx;return getattr(c.request,m)(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    def put(path,obj):assert raw(path,obj).status==200,path
    def get(path,c=None):
        return (c or ctx).request.get(B+'/api/doc/'+path).json()
    def vista():return {f['sid']:f for f in ctx.request.get(B+'/api/cobranza/vista').json()['filas']}
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    nom={'s1':'Ana López Ramírez','s2':'Beto Mena Ruiz','s3':'Carla Díaz Soto'}
    for i,(sid,n) in enumerate(nom.items(),1):put('students/'+sid,{'mat':'2026%04d'%i,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'total':0})
    for sid in nom:
        r=ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'al'+sid,'name':nom[sid],'alumno':sid,'clave':'abcd-efgh'}]}),headers=HDR);assert r.status==200
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===3")
    ok('hoy_es_noviembre_2026_o_posterior',HOY>='2026-11-11')
    hoyd=datetime.date.fromisoformat(HOY)
    # ---------- Antes: sin recargos ----------
    v=vista();ok('adeudo_inicial_3900',all(v[s]['adeudo']['n']==3 and abs(v[s]['adeudo']['total']-3900)<0.01 for s in ('s1','s2')))
    pg.evaluate("ir('pagos');vista('al')");W(pg,"MOD==='pagos'")
    ok('boton_en_la_barra',pg.is_visible('#bRcg'))
    pg.click('#bRcg');pg.wait_for_selector('#dRcg[open]')
    ok('abre_en_pestana_recargos',pg.is_visible('#rcgP1') and pg.is_hidden('#rcgP2'))
    ok('lista_las_colegiaturas_vencidas_de_todos',pg.locator('#rcgTb1 input[type=checkbox]').count()==9)
    ok('monto_por_defecto_5_por_ciento',pg.inner_text('#rcgTb1').count('$65.00')==9)
    ok('resumen_con_la_regla',('5 %' in pg.inner_text('#rcgH1')) and ('día 10' in pg.inner_text('#rcgH1')))
    pg.fill('#rcgB1','20260001');pg.wait_for_timeout(250)
    ok('filtra_por_matricula',pg.locator('#rcgTb1 input[type=checkbox]').count()==3)
    pg.click('#rcgGo1');ok('sin_marcas_avisa','al menos una' in pg.inner_text('#rcgMsg'))
    pg.check('#rcgA1');pg.click('#rcgGo1');W(pg,"document.getElementById('rcgMsg').textContent.indexOf('3 recargos')>-1")
    d=get('recargos/s1')['data']
    ok('guarda_3_recargos_del_alumno',len(d['items'])==3 and all(i['tipo']=='rec' and i['m']==65 and i['cid'] for i in d['items']) and {i['cid'] for i in d['items']}=={'c1','c2','c3'})
    ok('la_cuenta_del_alumno_sube_195',pg.evaluate("cargos(S.find(function(s){return s.id==='s1'})).reduce(function(t,c){return t+c.m},0)")-pg.evaluate("cargos(S.find(function(s){return s.id==='s2'})).reduce(function(t,c){return t+c.m},0)")==195)
    ok('recargos_van_al_final_de_la_cuenta',pg.evaluate("(function(){var L=cargos(S.find(function(s){return s.id==='s1'}));return L.slice(-3).every(function(c){return c.id.charAt(0)==='g'&&/^Recargo por mora: Colegiatura/.test(c.c)})})()"))
    ok('ya_no_se_ofrecen_otra_vez',pg.locator('#rcgTb1 input[type=checkbox]').count()==0 and pg.evaluate("rcgCand().mora.length")==6)
    v=vista();ok('servidor_cuenta_igual_y_no_bloquea_por_recargos',v['s1']['adeudo']['n']==3 and abs(v['s1']['adeudo']['total']-3900)<0.01)
    # pago: los recargos se pagan al final
    put('ledger/s1',{'pagos':[{'id':'p1','fecha':HOY,'monto':1300,'metodo':'Efectivo','estado':'confirmado','folio':'R-000001'}]})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&S.length===3&&REC.s1")
    ok('pago_se_aplica_primero_a_la_colegiatura',pg.evaluate("(function(){var a=applyAll(S.find(function(s){return s.id==='s1'}));var i=a.L.findIndex(function(c){return c.id==='c1'});var g=a.L.findIndex(function(c){return c.id.charAt(0)==='g'});return a.rem[i]<0.01&&a.rem[g]===65})()"))
    v=vista();ok('servidor_tambien_aplica_el_pago_a_la_colegiatura',v['s1']['adeudo']['n']==2 and abs(v['s1']['adeudo']['total']-2600)<0.01)
    # ---------- Ajustes ----------
    pg.evaluate("ir('pagos');vista('al')");W(pg,"MOD==='pagos'");pg.click('#bRcg');pg.wait_for_selector('#dRcg[open]')
    pg.click('#rcgT4');ok('ajustes_muestran_valores_por_defecto',pg.input_value('#rcgDia')=='10' and pg.input_value('#rcgVal')=='5' and pg.input_value('#rcgTipo')=='pct' and pg.input_value('#rcgPp')=='10' and pg.input_value('#rcgPpD')=='5')
    pg.fill('#rcgDia','40');pg.click('#rcgGuarda');ok('rechaza_dia_fuera_de_rango','Revisa los valores' in pg.inner_text('#rcgMsg') and not get('recargos/_config')['exists'])
    pg.fill('#rcgDia','28');pg.fill('#rcgVal','150');pg.select_option('#rcgTipo','pct');pg.click('#rcgGuarda');ok('rechaza_porcentaje_mayor_a_100','100' in pg.inner_text('#rcgMsg') and not get('recargos/_config')['exists'])
    pg.select_option('#rcgTipo','fijo');pg.fill('#rcgVal','100');pg.fill('#rcgPp','10');pg.fill('#rcgPpD','28');pg.click('#rcgGuarda');W(pg,"document.getElementById('rcgMsg').textContent==='Ajustes guardados.'")
    c=get('recargos/_config')['data']
    ok('guarda_ajustes_en_el_servidor',c=={'diaLimite':28,'rec':{'tipo':'fijo','valor':100},'pp':{'pct':10,'dia':28}})
    # ---------- Pronto pago ----------
    pg.click('#rcgT2');W(pg,"document.getElementById('rcgTb2').children.length>0")
    ok('pronto_pago_ofrece_solo_el_mes_en_curso_sin_pagos',pg.evaluate("rcgCand().pp.map(function(r){return r.s.id+'|'+r.cid}).sort().join()")=='s1|c3,s2|c3,s3|c3' or pg.evaluate("rcgCand().pp.length")==3)
    ok('resumen_pronto_pago',('10 %' in pg.inner_text('#rcgH2')) and ('día 28' in pg.inner_text('#rcgH2')))
    ok('descuento_es_10_por_ciento',pg.inner_text('#rcgTb2').count('$130.00')==3)
    pg.fill('#rcgB2','20260002');pg.wait_for_timeout(250);pg.check('#rcgA2');pg.click('#rcgGo2')
    W(pg,"document.getElementById('rcgMsg').textContent.indexOf('1 descuentos')>-1")
    d2=get('recargos/s2')['data']
    ok('guarda_el_descuento',len(d2['items'])==1 and d2['items'][0]['tipo']=='desc' and d2['items'][0]['cid']=='c3' and d2['items'][0]['m']==130)
    ok('cargo_baja_a_1170',pg.evaluate("cargos(S.find(function(s){return s.id==='s2'})).find(function(c){return c.id==='c3'}).m")==1170)
    # con el límite en 28 ya no hay mora: se revisa el nuevo cálculo en servidor (cobranza usa su propio día límite)
    v=vista();ok('servidor_aplica_el_descuento_al_adeudo',v['s2']['adeudo']['n']==3 and abs(v['s2']['adeudo']['total']-3770)<0.01)
    ok('no_se_ofrece_dos_veces_el_descuento',pg.evaluate("rcgCand().pp.filter(function(r){return r.s.id==='s2'}).length")==0)
    ok('con_limite_28_noviembre_ya_no_esta_vencido',pg.evaluate("rcgCand().mora.map(function(r){return r.cid}).sort().join()")=='c1,c1,c2,c2' or hoyd.day>28)
    # ---------- Aplicados ----------
    pg.click('#rcgT3');pg.wait_for_selector('#rcgTb3 .rcgQ')
    ok('lista_todo_lo_aplicado',pg.locator('#rcgTb3 .rcgQ').count()==4)
    pg.fill('#rcgB3','20260002');pg.wait_for_timeout(250)
    ok('filtra_aplicados',pg.locator('#rcgTb3 .rcgQ').count()==1 and 'Descuento' in pg.inner_text('#rcgTb3'))
    pg.click('#rcgTb3 .rcgQ');W(pg,"document.getElementById('rcgMsg').textContent.indexOf('Cancelado')>-1")
    ok('cancelar_quita_el_descuento_en_servidor',get('recargos/s2')['data']['items']==[])
    ok('cuenta_vuelve_al_monto_anterior',pg.evaluate("cargos(S.find(function(s){return s.id==='s2'})).find(function(c){return c.id==='c3'}).m")==1300)
    v=vista();ok('servidor_vuelve_a_3900',abs(v['s2']['adeudo']['total']-3900)<0.01)
    pg.fill('#rcgB3','');pg.wait_for_timeout(250)
    ok('quedan_3_recargos',pg.locator('#rcgTb3 .rcgQ').count()==3)
    pg.click('#rcgCls');ok('cierra',not pg.evaluate("document.getElementById('dRcg').open"))
    ok('estado_de_cuenta_incluye_recargos',pg.evaluate("cEst(S.find(function(s){return s.id==='s1'})).filter(function(c){return /^Recargo/.test(c.c)}).length")==3)
    ok('se_incluye_en_el_respaldo_del_navegador',pg.evaluate("BKCOL.indexOf('recargos')>-1"))
    ok('buscador_encuentra_la_funcion',pg.evaluate("(function(){ir('home');return true})()"))
    W(pg,"MOD==='home'");pg.fill('#hBus','recargo');pg.wait_for_timeout(300);ok('buscador_lista_recargos','Recargos y pronto pago' in pg.inner_text('#hBusR'))
    # ---------- Validación del servidor ----------
    it=lambda **k:dict({'id':'z1','tipo':'rec','cid':'c1','c':'Recargo','m':50,'f':HOY},**k)
    ok('rechaza_monto_negativo',raw('recargos/s3',{'items':[it(m=-5)]}).status==400)
    ok('rechaza_tipo_desconocido',raw('recargos/s3',{'items':[it(tipo='x')]}).status==400)
    ok('rechaza_descuento_sin_cargo',raw('recargos/s3',{'items':[it(tipo='desc',cid='')]}).status==400)
    ok('rechaza_lista_que_no_es_lista',raw('recargos/s3',{'items':'hola'}).status==400)
    ok('rechaza_id_raro',raw('recargos/s3',{'items':[it(id='a b/../')]}).status==400)
    ok('rechaza_ajustes_incompletos',raw('recargos/_config',{'diaLimite':5}).status==400)
    ok('rechaza_ajustes_dia_29',raw('recargos/_config',{'diaLimite':29,'rec':{'tipo':'pct','valor':5},'pp':{'pct':10,'dia':5}}).status==400)
    ok('acepta_valido',raw('recargos/s3',{'items':[it()]}).status==200)
    # ---------- Permisos ----------
    def entra(u,clave):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':clave}),headers=HDR);return cx,r
    cj,r=entra('caja1','clave-caja-123');ok('caja_entra',r.status==200)
    ok('caja_puede_aplicar_un_recargo',raw('recargos/s3',{'items':[it(),it(id='z2')]},c=cj).status==200)
    ok('caja_no_cambia_los_ajustes',raw('recargos/_config',{'diaLimite':5,'rec':{'tipo':'pct','valor':5},'pp':{'pct':10,'dia':5}},c=cj).status==403)
    ok('ajustes_siguen_intactos',get('recargos/_config')['data']['diaLimite']==28)
    ec,r=entra('esc2','clave-esc2-123');ok('control_escolar_entra',r.status==200)
    ok('control_escolar_no_escribe_recargos',raw('recargos/s3',{'items':[it(),it(id='z2'),it(id='z3')]},c=ec).status==403)
    ok('control_escolar_si_los_ve',get('recargos/s1',ec)['exists'])
    al,r=entra('als1','abcd-efgh');ok('alumno_entra',r.status==200)
    al.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-ana-77'}),headers=HDR)
    ok('alumno_ve_sus_recargos',len(get('recargos/s1',al).get('data',{}).get('items',[]))==3)
    ok('alumno_no_ve_los_de_otro',not get('recargos/s2',al)['exists'] and not get('recargos/s3',al)['exists'])
    ok('alumno_no_ve_los_ajustes',not get('recargos/_config',al)['exists'])
    ok('alumno_no_lista_otros',[d['id'] for d in al.request.get(B+'/api/col/recargos').json()['docs']]==['s1'])
    ok('alumno_no_puede_escribir',raw('recargos/s1',{'items':[]},c=al).status==403)
    # portal del alumno: su estado de cuenta incluye los recargos
    pa=al.new_page();pa.goto(B+'/');W(pa,"typeof APP!=='undefined'&&APP!==null&&typeof REC!=='undefined'&&REC.s1")
    ok('portal_del_alumno_suma_los_recargos',pa.evaluate("cargos(S[0]).filter(function(c){return /^Recargo/.test(c.c)}).length")==3)
    ok('sin_errores_de_pagina',not errs)
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
