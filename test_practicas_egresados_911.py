"""Servicio social y prácticas profesionales, seguimiento de egresados y estadística 911."""
import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3142;B='http://127.0.0.1:%d'%PORT;TOK='tok-pr-1'
os.system('rm -rf /tmp/nbdata_pr /tmp/crl3 && mkdir -p /tmp/nbdata_pr /tmp/crl3')
RELOJ='/tmp/crl3/reloj.txt';HOY=datetime.date.today().isoformat();open(RELOJ,'w').write(HOY)
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_pr',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ)
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
    def get(path,c=None):return (c or ctx).request.get(B+'/api/doc/'+path).json()
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    A=lambda mat,nom,**k:dict({'mat':mat,'nombre':nom,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':True,'total':0},**k)
    put('students/s1',A('20260001','Ana López Ramírez',sexo='Femenino',edad=20))
    put('students/s2',A('20260002','Beto Mena Ruiz',sexo='Masculino',edad=22,nuevo=False))
    put('students/s3',A('20250003','Carla Díaz Soto',sexo='Femenino',edad=31,ingreso=2025))
    put('students/s4',A('20250004','Diego Vega Luna',sexo='Masculino',ingreso=2025))
    put('students/s5',A('20240005','Elena Ríos Cano',sexo='Femenino',edad=24,ingreso=2024))
    put('students/s6',A('20260006','Fabio Gil Paz',sexo='Masculino',edad=19,baja={'fecha':HOY,'motivo':'Prueba'}))
    put('egresados/s5',{'sid':'s5','mat':'20240005','nombre':'Elena Ríos Cano','plan':'Pedagogía','fecha':HOY,'ciclo':2024})
    for sid,n in {'s1':'Ana López Ramírez','s2':'Beto Mena Ruiz'}.items():
        r=ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'al'+sid,'name':n,'alumno':sid,'clave':'abcd-efgh'}]}),headers=HDR);assert r.status==200
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc2','name':'Esc Dos','rol':'personalizado','modulos':{'escolar':'editar'},'clave':'clave-esc2-123'}),headers=HDR)
    ctx.request.post(B+'/api/usuarios',data=json.dumps({'u':'esc3','name':'Esc Tres','rol':'personalizado','modulos':{'escolar':'ver'},'clave':'clave-esc3-123'}),headers=HDR)
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===6")
    pg.evaluate("ir('esc')");W(pg,"MOD==='esc'")
    ok('pestanas_visibles',all(pg.is_visible('#eTabs [data-et=%s]'%k) for k in 'OYX'))
    # ================= Servicio social y prácticas =================
    pg.click('#eTabs [data-et=O]');W(pg,"ETAB==='O'")
    ok('lista_alumnos_sin_bajas',pg.locator('#prTbl tr').count()==5)
    ok('resumen_inicial','0 liberados' in pg.inner_text('#prRes') and '5 alumnos' in pg.inner_text('#prRes'))
    pg.fill('#prBus','Ana');pg.wait_for_timeout(250);ok('busca_por_nombre',pg.locator('#prTbl tr').count()==1)
    pg.fill('#prBus','');pg.select_option('#prFil','sin');pg.wait_for_timeout(250);ok('filtro_sin_registro',pg.locator('#prTbl tr').count()==5)
    pg.select_option('#prFil','');pg.fill('#prBus','20260001');pg.wait_for_timeout(250)
    pg.click('#prTbl [data-pr]');pg.wait_for_selector('#dPr[open]')
    ok('abre_con_nombre','Ana López' in pg.inner_text('#prNom'))
    ok('horas_requeridas_por_defecto_480',pg.input_value('#prReq')=='480')
    ok('liberar_deshabilitado_sin_horas',pg.is_disabled('#prLib'))
    pg.fill('#prInst','DIF Municipal');pg.fill('#prResp','Lic. Pérez');pg.fill('#prProy','Apoyo educativo');pg.fill('#prIni','2026-09-01');pg.click('#prGuarda');W(pg,"document.getElementById('prMsg').textContent==='Guardado.'")
    d=get('practicas/s1')['data'];it=d['items'][0]
    ok('guarda_programa',it['id']=='ss' and it['inst']=='DIF Municipal' and it['horasReq']==480 and it['estado']=='en curso' and it['registros']==[])
    pg.fill('#prHoras','25');pg.click('#prAdd');ok('rechaza_mas_de_24_horas','máximo 24' in pg.inner_text('#prMsg'))
    pg.fill('#prHoras','0');pg.click('#prAdd');ok('rechaza_cero_horas','máximo 24' in pg.inner_text('#prMsg'))
    pg.fill('#prHoras','');pg.click('#prAdd');ok('rechaza_horas_vacias','máximo 24' in pg.inner_text('#prMsg'))
    pg.fill('#prHoras','24');pg.fill('#prAct','Tutorías');pg.click('#prAdd');W(pg,"document.getElementById('prMsg').textContent==='Horas registradas.'")
    ok('registra_horas',get('practicas/s1')['data']['items'][0]['registros'][0]['h']==24 and '24' in pg.inner_text('#prAvance'))
    pg.evaluate("prMsg('')");pg.fill('#prReq','48');pg.fill('#prHoras','24');pg.fill('#prFecha','2026-10-02');pg.fill('#prAct','Talleres');pg.click('#prAdd');W(pg,"document.getElementById('prMsg').textContent==='Horas registradas.'")
    ok('guarda_nuevo_requisito',get('practicas/s1')['data']['items'][0]['horasReq']==48 and len(get('practicas/s1')['data']['items'][0]['registros'])==2)
    ok('liberar_se_habilita_con_las_horas',not pg.is_disabled('#prLib'))
    pg.click('#prT2');ok('pestana_practicas_vacia',pg.input_value('#prReq')=='240' and pg.input_value('#prInst')=='' and pg.is_disabled('#prLib'))
    pg.fill('#prInst','Despacho Ortega');pg.click('#prGuarda');W(pg,"document.getElementById('prMsg').textContent==='Guardado.'")
    d=get('practicas/s1')['data'];ok('dos_programas_separados',[i['id'] for i in d['items']]==['ss','pp'] and d['items'][1]['inst']=='Despacho Ortega')
    pg.click('#prT1');pg.evaluate("prMsg('')");pg.click('#prLib');W(pg,"document.getElementById('prMsg').textContent==='Liberado.'")
    it=get('practicas/s1')['data']['items'][0]
    ok('libera',it['estado']=='liberado' and it['liberacion']==pg.evaluate('today()'))
    ok('liberado_bloquea_cambios',pg.is_disabled('#prHoras') and pg.is_disabled('#prInst') and pg.is_hidden('#prAdd') and pg.is_hidden('#prLib') and pg.locator('#prTb [data-prq]').count()==0)
    ok('admin_puede_reabrir',pg.is_visible('#prRe'))
    pg.evaluate("prMsg('')");pg.click('#prRe');W(pg,"document.getElementById('prMsg').textContent==='Reabierto.'");ok('reabre',get('practicas/s1')['data']['items'][0]['estado']=='en curso')
    pg.evaluate("prMsg('')");pg.click('#prTb [data-prq]');W(pg,"document.getElementById('prMsg').textContent==='Registro quitado.'");ok('quita_registro',len(get('practicas/s1')['data']['items'][0]['registros'])==1)
    pg.click('#prCls');pg.fill('#prBus','');pg.wait_for_timeout(250)
    ok('resumen_actualizado','0 liberados, 1 en curso' in pg.inner_text('#prRes'))
    pg.select_option('#prFil','curso');pg.wait_for_timeout(250);ok('filtro_en_curso',pg.locator('#prTbl tr').count()==1)
    pg.select_option('#prFil','');
    # --- validacion del servidor
    base=lambda **k:{'items':[dict({'id':'ss','tipo':'ss','inst':'X','resp':'','proyecto':'','inicio':'','fin':'','horasReq':100,'estado':'en curso','liberacion':'','obs':'','registros':[{'id':'r1','f':HOY,'h':10,'act':''}]},**k)]}
    ok('servidor_rechaza_liberar_con_pocas_horas',raw('practicas/s2',base(estado='liberado')).status==400)
    ok('servidor_rechaza_estado_raro',raw('practicas/s2',base(estado='listo')).status==400)
    ok('servidor_rechaza_tipo_raro',raw('practicas/s2',base(tipo='xx')).status==400)
    ok('servidor_rechaza_horas_negativas',raw('practicas/s2',base(registros=[{'id':'r1','f':HOY,'h':-3,'act':''}])).status==400)
    ok('servidor_rechaza_fecha_mala',raw('practicas/s2',base(registros=[{'id':'r1','f':'ayer','h':3,'act':''}])).status==400)
    ok('servidor_rechaza_horas_requeridas_absurdas',raw('practicas/s2',base(horasReq=999999)).status==400)
    ok('servidor_acepta_valido',raw('practicas/s2',base()).status==200)
    ok('servidor_libera_si_cumple',raw('practicas/s2',base(estado='liberado',registros=[{'id':'r1','f':HOY,'h':24,'act':''}]*4+[{'id':'r2','f':HOY,'h':4,'act':''}])).status==200)
    # --- permisos
    def entra(u,clave):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':clave}),headers=HDR);return cx,r
    e2,r=entra('esc2','clave-esc2-123');ok('escolar_editar_entra',r.status==200)
    e3,r=entra('esc3','clave-esc3-123');ok('escolar_ver_entra',r.status==200)
    ok('escolar_editar_escribe',raw('practicas/s3',base(),c=e2).status==200)
    ok('escolar_ver_no_escribe',raw('practicas/s3',base(inst='Y'),c=e3).status==403)
    ok('escolar_ver_si_lee',get('practicas/s1',e3)['exists'])
    al,r=entra('als1','abcd-efgh');ok('alumno_entra',r.status==200)
    al.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':'clave-ana-77'}),headers=HDR)
    ok('alumno_ve_lo_suyo',get('practicas/s1',al)['exists'])
    ok('alumno_no_ve_lo_de_otros',not get('practicas/s2',al)['exists'] and not get('practicas/s3',al)['exists'])
    ok('alumno_no_lista_otros',[d['id'] for d in al.request.get(B+'/api/col/practicas').json()['docs']]==['s1'])
    ok('alumno_no_escribe',raw('practicas/s1',base(),c=al).status==403)
    pa=al.new_page();pa.on("pageerror",lambda e:errs.append(str(e)));pa.goto(B+'/');W(pa,"typeof APP!=='undefined'&&APP!==null&&typeof PRC!=='undefined'&&PRC.s1&&S.length>0")
    W(pa,"typeof renderPor==='function'&&document.getElementById('poBody')&&document.getElementById('poBody').innerText.indexOf('Servicio social')>-1")
    ok('portal_muestra_avance',('Servicio social' in pa.inner_text('#poBody')) and ('DIF Municipal' in pa.inner_text('#poBody')) and ('Despacho Ortega' in pa.inner_text('#poBody')) and pa.locator('#poBody [data-pr],#poBody #prAdd').count()==0)
    # --- escolar solo lectura en pantalla
    p3=e3.new_page();p3.on("pageerror",lambda e:errs.append(str(e)));p3.goto(B+'/');W(p3,"typeof APP!=='undefined'&&APP!==null&&S.length===6")
    p3.evaluate("ir('esc');etab('O')");W(p3,"ETAB==='O'");p3.fill('#prBus','20260001');p3.wait_for_timeout(250);p3.click('#prTbl [data-pr]');p3.wait_for_selector('#dPr[open]')
    ok('solo_lectura_oculta_botones',p3.is_hidden('#prAdd') and p3.is_hidden('#prGuarda') and p3.is_hidden('#prLib') and p3.is_disabled('#prInst'))
    p3.close()
    # ================= Seguimiento de egresados =================
    pg.click('#eTabs [data-et=Y]');W(pg,"ETAB==='Y'")
    ok('lista_solo_egresados',pg.locator('#sgTbl tr').count()==1 and 'Elena Ríos' in pg.inner_text('#sgTbl'))
    ok('resumen_seg','1 egresados · 0 contactados' in pg.inner_text('#sgRes'))
    pg.click('#sgTbl [data-sg]');pg.wait_for_selector('#dSg[open]')
    pg.fill('#sgF','');pg.click('#sgAdd');ok('pide_fecha','fecha' in pg.inner_text('#sgMsg'))
    pg.fill('#sgF',HOY);pg.select_option('#sgMed','WhatsApp');pg.select_option('#sgSit','Trabaja en su área');pg.fill('#sgEmp','Colegio Benito Juárez');pg.fill('#sgPue','Docente');pg.fill('#sgIng','9500');pg.fill('#sgNota','Muy contenta');pg.click('#sgAdd')
    W(pg,"document.getElementById('sgMsg').textContent==='Contacto registrado.'")
    c=get('seguim/s5')['data']['contactos'][0]
    ok('guarda_contacto',c['medio']=='WhatsApp' and c['situacion']=='Trabaja en su área' and c['empresa']=='Colegio Benito Juárez' and c['ingreso']==9500)
    pg.fill('#sgIng','-5');pg.click('#sgAdd');ok('rechaza_ingreso_negativo','ingreso' in pg.inner_text('#sgMsg') and len(get('seguim/s5')['data']['contactos'])==1)
    pg.evaluate("sgMsg('')");pg.fill('#sgIng','');pg.select_option('#sgSit','Busca empleo');pg.fill('#sgEmp','');pg.click('#sgAdd');W(pg,"document.getElementById('sgMsg').textContent==='Contacto registrado.'")
    ok('dos_contactos',len(get('seguim/s5')['data']['contactos'])==2 and pg.locator('#sgTb tr').count()==2)
    pg.evaluate("sgMsg('')");pg.click('#sgTb [data-sgq] >> nth=1');W(pg,"document.getElementById('sgMsg').textContent==='Contacto quitado.'");ok('quita_contacto',len(get('seguim/s5')['data']['contactos'])==1)
    pg.click('#sgCls');pg.wait_for_timeout(250)
    ok('resumen_actualiza','1 contactados (100 %)' in pg.inner_text('#sgRes') and '1 trabajan' in pg.inner_text('#sgRes'))
    pg.select_option('#sgFil','sin');pg.wait_for_timeout(250);ok('filtro_sin_contactar',pg.locator('#sgTbl [data-sg]').count()==0);pg.select_option('#sgFil','')
    sg=lambda **k:{'contactos':[dict({'id':'c1','f':HOY,'medio':'Correo','situacion':'Sin dato'},**k)]}
    ok('servidor_rechaza_medio',raw('seguim/s5',sg(medio='Paloma')).status==400)
    ok('servidor_rechaza_situacion',raw('seguim/s5',sg(situacion='Rico')).status==400)
    ok('servidor_rechaza_fecha',raw('seguim/s5',sg(f='x')).status==400)
    ok('servidor_acepta_contacto',raw('seguim/s5',sg()).status==200)
    ok('escolar_ver_no_escribe_seguim',raw('seguim/s5',sg(nota='z'),c=e3).status==403)
    ok('escolar_editar_escribe_seguim',raw('seguim/s5',sg(nota='z'),c=e2).status==200)
    ok('alumno_no_lee_seguimiento',not get('seguim/s5',al)['exists'] and al.request.get(B+'/api/col/seguim').json()['docs']==[])
    with pg.expect_download() as dl:pg.click('#sgCsv')
    tx=open(dl.value.path(),encoding='utf-8').read()
    ok('csv_seguimiento',tx.count('\n')>=1 and 'Elena Ríos Cano' in tx)
    # ================= Estadística 911 =================
    pg.click('#eTabs [data-et=X]');W(pg,"ETAB==='X'&&document.getElementById('e9Cuerpo').innerHTML.length>100")
    ok('ciclo_actual_por_defecto',pg.input_value('#e9Ciclo')==str(pg.evaluate("cicloAct()")))
    r=pg.evaluate("e9Calcula(2026)")
    ok('matricula_total_4_sin_baja_ni_egresado',r['mat']['t']==4 and r['mat']['H']==2 and r['mat']['M']==2)
    ok('nuevo_ingreso_1_y_reingreso_3',r['nuevo']['t']==1 and r['nuevo']['M']==1 and r['reing']['t']==3)
    ed={e['k']:e['c']['t'] for e in r['edades']}
    ok('edades',ed['20']==1 and ed['22']==1 and ed['30 a 34']==1 and ed['Sin dato de edad']==1 and ed['Menos de 18']==0)
    ok('por_plan_y_cuatrimestre',len(r['planes'])==1 and r['planes'][0]['tot']['t']==4 and r['cuats'][0]['c']['t']==4)
    ok('egresados_del_ciclo',r['egr']['t']==(1 if HOY>='2026-09-01' else 0))
    ok('bajas',r['bajas']['t']==1)
    ok('texto_avisa_dato_faltante','sin edad' in pg.inner_text('#e9Cuerpo') and 'Matrícula total' in pg.inner_text('#e9Cuerpo'))
    pg.select_option('#e9Ciclo','2025');ok('cambiar_ciclo_recalcula',pg.evaluate("E9R.ciclo")==2025 and pg.evaluate("E9R.nuevo.t")==2)
    with pg.expect_download() as dl:pg.click('#e9Csv')
    tx=open(dl.value.path(),encoding='utf-8').read()
    ok('csv_911',tx.startswith('﻿Apartado') and 'Por edad' in tx and 'Egresados' in tx and 'Bajas' in tx)
    ok('seis_tablas',pg.locator('#e9Cuerpo table').count()==6)
    # ================= General =================
    pg.fill('#hBus','servicio social') if pg.evaluate("(function(){ir('home');return true})()") else None
    W(pg,"MOD==='home'");pg.fill('#hBus','servicio social');pg.wait_for_timeout(300)
    ok('buscador_encuentra_servicio_social','Servicio social' in pg.inner_text('#hBusR'))
    ok('respaldo_navegador_incluye_las_colecciones',pg.evaluate("BKCOL.indexOf('practicas')>-1&&BKCOL.indexOf('seguim')>-1"))
    ok('sin_errores_de_pagina',not errs)
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
