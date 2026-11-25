"""Biblioteca e inventario: validación, permisos, préstamos (límites, renovación, devolución, vencidos), catálogo, inventario y portal del alumno."""
import subprocess,time,json,os,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3147;B='http://127.0.0.1:%d'%PORT;TOK='tok-bb-1'
os.system('rm -rf /tmp/nbdata_bb /tmp/crl7 && mkdir -p /tmp/nbdata_bb /tmp/crl7')
RELOJ='/tmp/crl7/reloj.txt';HOY=datetime.date.today().isoformat();open(RELOJ,'w').write(HOY)
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_bb',LF_SETUP_TOKEN=TOK,LF_SIN_CONTACTO='1',LF_SIN_PRECARGA='1',LF_RELOJ_ARCHIVO=RELOJ)
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
    def get(path,c=None):return (c or ctx).request.get(B+'/api/doc/'+path).json()
    for sid,n,mt in (('s1','Ana López Ramírez','20260001'),('s2','Beto Mena Ruiz','20260002'),('s3','Carla Díaz Soto','20260003')):
        assert raw('students/'+sid,{'mat':mt,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False,'total':0}).status==200
    for sid,n in (('s1','Ana'),('s2','Beto'),('s3','Carla')):
        assert ctx.request.post(B+'/api/usuarios/alumnos',data=json.dumps({'items':[{'u':'al'+sid,'name':n,'alumno':sid,'clave':'abcd-efgh'}]}),headers=HDR).status==200
    for u,r,m in (('esc2','personalizado',{'escolar':'editar'}),('bib1','personalizado',{'biblioteca':'editar'}),('bib2','personalizado',{'biblioteca':'ver'}),('caja1','caja',None)):
        d={'u':u,'name':u,'rol':r,'clave':'clave-%s-123'%u}
        if m:d['modulos']=m
        assert ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR).status==200
    def entra(u,c):
        cx=b.new_context();r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status);return cx
    def alumno(sid,nueva):
        cx=entra('al'+sid,'abcd-efgh');cx.request.post(B+'/api/cambiar-clave',data=json.dumps({'actual':'abcd-efgh','nueva':nueva}),headers=HDR);return entra('al'+sid,nueva)
    A1=alumno('s1','clave-ana-777');A2=alumno('s2','clave-beto-777');A3=alumno('s3','clave-carla-777')
    E2=entra('esc2','clave-esc2-123');BE=entra('bib1','clave-bib1-123');BV=entra('bib2','clave-bib2-123');CJ=entra('caja1','clave-caja1-123')
    put=lambda cx,path,o:cx.request.put(B+'/api/doc/'+path,data=json.dumps(o),headers=HDR)
    L1={'titulo':'Rayuela','autor':'Julio Cortázar','ejemplares':2,'categoria':'Novela','ubicacion':'A-1','isbn':'978-1','nota':'nota interna'}
    # --- validación servidor
    ok('libro_sin_titulo_400',put(ctx,'libros/x1',dict(L1,titulo='')).status==400)
    ok('libro_ejemplares_0_400',put(ctx,'libros/x1',dict(L1,ejemplares=0)).status==400)
    ok('libro_ejemplares_1001_400',put(ctx,'libros/x1',dict(L1,ejemplares=1001)).status==400)
    ok('libro_anio_3000_400',put(ctx,'libros/x1',dict(L1,anio=3000)).status==400)
    ok('config_invalida_400',put(ctx,'libros/_config',{'dias':0,'max':3,'multa':5}).status==400 and put(ctx,'libros/_config',{'dias':7,'max':3,'multa':-1}).status==400)
    ok('prestamo_tipo_invalido_400',put(ctx,'prestamos/s1',{'nombre':'Ana','tipo':'x','items':[]}).status==400)
    ok('prestamo_vence_antes_400',put(ctx,'prestamos/s1',{'nombre':'Ana','tipo':'alumno','items':[{'id':'a1','libro':'x1','fecha':'2026-05-10','vence':'2026-05-01','devuelto':'','renovaciones':0}]}).status==400)
    ok('inventario_cantidad_0_400',put(ctx,'inventario/i0',{'nombre':'Silla','cantidad':0,'estado':'Bueno'}).status==400)
    ok('inventario_estado_invalido_400',put(ctx,'inventario/i0',{'nombre':'Silla','cantidad':1,'estado':'Roto'}).status==400)
    ok('inventario_costo_negativo_400',put(ctx,'inventario/i0',{'nombre':'Silla','cantidad':1,'estado':'Bueno','costo':-3}).status==400)
    ok('nada_se_guardo_con_errores',ctx.request.get(B+'/api/col/libros').json()['docs']==[] and ctx.request.get(B+'/api/col/inventario').json()['docs']==[])
    ok('admin_guarda_libro_valido',put(ctx,'libros/L1',L1).status==200)
    # --- permisos
    ok('biblioteca_editar_escribe_libros',put(BE,'libros/L2',{'titulo':'Ficciones','autor':'Borges','ejemplares':1}).status==200)
    ok('biblioteca_ver_no_escribe_libros',put(BV,'libros/L3',{'titulo':'X','ejemplares':1}).status in (401,403))
    ok('biblioteca_ver_lee_libros',BV.request.get(B+'/api/col/libros').status==200 and len(BV.request.get(B+'/api/col/libros').json()['docs'])==2)
    ok('escolar_sin_biblioteca_no_escribe',put(E2,'libros/L3',{'titulo':'X','ejemplares':1}).status in (401,403))
    ok('escolar_sin_biblioteca_no_lee_inventario',E2.request.get(B+'/api/col/inventario').status in (401,403) or E2.request.get(B+'/api/col/inventario').json()['docs']==[])
    ok('caja_no_lee_inventario',CJ.request.get(B+'/api/col/inventario').status in (401,403) or CJ.request.get(B+'/api/col/inventario').json()['docs']==[])
    ok('biblioteca_editar_escribe_inventario',put(BE,'inventario/i1',{'codigo':'INV-0001','nombre':'Proyector','cantidad':1,'estado':'Bueno','costo':8500.5,'categoria':'Equipo'}).status==200)
    ok('alumno_no_lee_inventario',A1.request.get(B+'/api/col/inventario').status in (401,403) or A1.request.get(B+'/api/col/inventario').json().get('docs')==[])
    ok('alumno_no_escribe_libros',put(A1,'libros/L9',{'titulo':'X','ejemplares':1}).status in (401,403))
    ok('alumno_no_escribe_inventario',put(A1,'inventario/i9',{'nombre':'X','cantidad':1,'estado':'Bueno'}).status in (401,403))
    lj=A1.request.get(B+'/api/col/libros').json()['docs']
    ok('alumno_lee_catalogo_sin_isbn_ni_notas',len(lj)==2 and all('isbn' not in json.dumps(x) and 'nota' not in json.dumps(x) for x in lj))
    HOYI=pg.evaluate("today()")
    hace=lambda n:(datetime.date.fromisoformat(HOYI)-datetime.timedelta(days=n)).isoformat()
    ok('bib_editar_registra_prestamo_ajeno',put(BE,'prestamos/s2',{'nombre':'Beto Mena Ruiz','tipo':'alumno','items':[{'id':'p-beto','libro':'L2','fecha':hace(1),'vence':hace(-6),'devuelto':'','renovaciones':0}]}).status==200)
    ok('alumno_no_escribe_prestamo_propio',put(A2,'prestamos/s2',{'nombre':'Beto','tipo':'alumno','items':[]}).status in (401,403))
    ok('alumno_no_lee_prestamo_ajeno',A1.request.get(B+'/api/doc/prestamos/s2').status in (401,403,404) or A1.request.get(B+'/api/doc/prestamos/s2').json().get('data') is None)
    ok('alumno_lee_su_prestamo',A2.request.get(B+'/api/doc/prestamos/s2').status==200)
    ok('alumno_solo_ve_los_suyos_en_lista',all('p-beto' not in json.dumps(x) for x in A1.request.get(B+'/api/col/prestamos').json()['docs']))
    # --- visibilidad de pestañas
    def abre(cx):
        p_=cx.new_page();p_.on("pageerror",lambda e:errs.append(str(e)));p_.goto(B+'/');W(p_,"typeof APP!=='undefined'&&APP!==null&&S.length>=0");return p_
    pb=abre(BE);pb.evaluate("ir('esc')");W(pb,"MOD==='esc'")
    ok('bib_editar_ve_pestanas_W_Z',pb.evaluate("[...document.querySelectorAll('#eTabs button')].filter(b=>!b.hidden).map(b=>b.dataset.et).sort().join('')")=='WZ')
    pb.evaluate("etab('W')");W(pb,"!document.getElementById('eW').hidden")
    ok('bib_editar_pestana_W_activa',pb.evaluate("!document.getElementById('bbNuevoP').disabled"))
    pv=abre(BV);pv.evaluate("ir('esc')");W(pv,"MOD==='esc'");pv.evaluate("etab('W')");W(pv,"!document.getElementById('eW').hidden")
    ok('bib_ver_no_puede_prestar',pv.evaluate("document.getElementById('bbNuevoP').disabled&&document.getElementById('bbNuevoL').disabled===false||document.getElementById('bbNuevoP').disabled"))
    pe=abre(E2);pe.evaluate("ir('esc')");W(pe,"MOD==='esc'")
    ok('escolar_no_ve_pestanas_W_Z',pe.evaluate("[...document.querySelectorAll('#eTabs button')].filter(b=>!b.hidden&&(b.dataset.et==='W'||b.dataset.et==='Z')).length")==0)
    pe.evaluate("etab('W')");ok('escolar_no_entra_a_W',pe.evaluate("document.getElementById('eW').hidden"))
    # --- UI admin: catálogo
    pg.evaluate("ir('esc');etab('W')");W(pg,"!document.getElementById('eW').hidden")
    pg.click('#bbT2');W(pg,"!document.getElementById('bbP2').hidden")
    ok('catalogo_lista_los_libros_sembrados','Rayuela' in pg.inner_text('#bbTb2') and 'Ficciones' in pg.inner_text('#bbTb2'))
    pg.click('#bbNuevoL');pg.wait_for_selector('#dBl[open]');pg.click('#blGuarda');ok('ui_libro_exige_titulo','título' in pg.inner_text('#blMsg'))
    pg.fill('#blTit','El Aleph');pg.fill('#blAut','Jorge Luis Borges');pg.fill('#blEj','0');pg.click('#blGuarda');ok('ui_libro_ejemplares_invalidos','1 a 1000' in pg.inner_text('#blMsg'))
    pg.fill('#blEj','1');pg.fill('#blAnio','abc') if False else None
    pg.fill('#blUbi','B-2');pg.click('#blGuarda');W(pg,"document.getElementById('blMsg').textContent.indexOf('guardado')>-1")
    pg.click('#blCls');pg.wait_for_timeout(300)
    alef=[d for d in ctx.request.get(B+'/api/col/libros').json()['docs'] if d['data'].get('titulo')=='El Aleph']
    ok('ui_libro_guardado_en_servidor',len(alef)==1 and alef[0]['data']['ejemplares']==1 and alef[0]['data']['disp']==1 and alef[0]['data']['ubicacion']=='B-2')
    LA=alef[0]['id']
    pg.fill('#bbBus2','cortazar');pg.wait_for_timeout(300);ok('busqueda_catalogo_por_autor','Rayuela' in pg.inner_text('#bbTb2') and 'Aleph' not in pg.inner_text('#bbTb2'))
    pg.fill('#bbBus2','');pg.wait_for_timeout(200)
    # --- ajustes
    pg.click('#bbT3');pg.fill('#bbDias','0');pg.click('#bbGuardaCfg');ok('ui_ajustes_invalidos','Revisa' in pg.inner_text('#bbMsg'))
    pg.fill('#bbDias','5');pg.fill('#bbMax','2');pg.fill('#bbMulta','10');pg.click('#bbGuardaCfg');W(pg,"document.getElementById('bbMsg').textContent.indexOf('guardados')>-1")
    cfg=ctx.request.get(B+'/api/doc/libros/_config').json()['data']
    ok('ajustes_guardados',cfg=={'dias':5,'max':2,'multa':10})
    # --- préstamos
    pg.click('#bbT1');W(pg,"!document.getElementById('bbP1').hidden")
    ok('resumen_inicial','1 préstamos activos' in pg.inner_text('#bbR1') and '0 vencidos' in pg.inner_text('#bbR1') and 'Beto' in pg.inner_text('#bbTb1'))
    def nuevo_prestamo(tipo,buscar,lib,fec=None,ven=None,nom=None):
        pg.evaluate("document.getElementById('dBp').open&&document.getElementById('dBp').close()");pg.click('#bbNuevoP');pg.wait_for_selector('#dBp[open]');pg.select_option('#bpTipo',tipo)
        if tipo=='otro':pg.fill('#bpNom',nom or '')
        else:
            pg.fill('#bpBus',buscar);pg.wait_for_timeout(200)
        pg.select_option('#bpLib',lib)
        if fec:pg.fill('#bpFec',fec)
        if ven:pg.fill('#bpVen',ven)
        pg.evaluate("document.getElementById('bpMsg').textContent=''");pg.click('#bpGuarda')
        W(pg,"document.getElementById('bpMsg').textContent.length>0");return pg.inner_text('#bpMsg')
    m=nuevo_prestamo('alumno','Ana','L1')
    ok('prestamo_ana_registrado','Préstamo registrado' in m)
    pa=get('prestamos/s1')['data']
    ok('prestamo_en_servidor',len(pa['items'])==1 and pa['items'][0]['libro']=='L1' and pa['items'][0]['vence']==(datetime.date.fromisoformat(HOYI)+datetime.timedelta(days=5)).isoformat() and pa['nombre']=='Ana López Ramírez')
    ok('disponibles_bajan_a_1',get('libros/L1')['data']['disp']==1)
    m=nuevo_prestamo('alumno','Ana','L1');ok('mismo_libro_dos_veces_bloqueado','ya tiene ese libro' in m or 'ya tiene' in m)
    m=nuevo_prestamo('docente','','L1') if False else ''
    pg.click('#bpCls')
    # L1 tiene 2 ejemplares: Beto no lo tiene; segundo ejemplar para otra persona
    m=nuevo_prestamo('otro','','L1',nom='Visitante Prueba');ok('prestamo_a_persona_externa','Préstamo registrado' in m)
    ok('externo_con_clave_o_slug',any(k.startswith('o-visitante') for k in [d['id'] for d in ctx.request.get(B+'/api/col/prestamos').json()['docs']]))
    ok('sin_ejemplares_ya_no_aparece_en_lista','Rayuela' not in pg.evaluate("document.getElementById('bpLib').innerHTML"))
    ok('disponibles_cero',get('libros/L1')['data']['disp']==0)
    pg.click('#bpCls');pg.wait_for_timeout(200)
    # límite por persona (max=2): Ana tiene 1; segundo libro permitido, tercero no
    pg.evaluate("document.getElementById('dBp').open&&document.getElementById('dBp').close()");pg.click('#bbNuevoP');pg.wait_for_selector('#dBp[open]');pg.fill('#bpBus','Ana');pg.wait_for_timeout(200);pg.select_option('#bpLib',LA);pg.evaluate("document.getElementById('bpMsg').textContent=''");pg.click('#bpGuarda');W(pg,"document.getElementById('bpMsg').textContent.length>0")
    ok('ana_segundo_libro_ok','Préstamo registrado' in pg.inner_text('#bpMsg'))
    pg.click('#bpCls')
    ok('limite_por_persona_alcanzado',len(get('prestamos/s1')['data']['items'])==2)
    put(ctx,'libros/L4',{'titulo':'Pedro Páramo','autor':'Rulfo','ejemplares':2,'activo':True,'disp':2})
    pg.evaluate("DBH.collection('libros')") if False else None
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&LIB.L4");pg.evaluate("ir('esc');etab('W')");W(pg,"!document.getElementById('eW').hidden")
    m=nuevo_prestamo('alumno','Ana','L4');ok('limite_max_bloquea','máximo' in m);pg.click('#bpCls')
    # --- vencidos
    m=nuevo_prestamo('alumno','Carla','L4',fec=hace(10),ven=hace(3));ok('prestamo_vencido_registrado','Préstamo registrado' in m)
    put(ctx,'libros/L5',{'titulo':'Aura','autor':'Fuentes','ejemplares':1,'activo':True,'disp':1})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&LIB.L5");pg.evaluate("ir('esc');etab('W')");W(pg,"!document.getElementById('eW').hidden")
    m=nuevo_prestamo('alumno','Carla','L5');ok('vencido_bloquea_nuevo_prestamo','vencidos' in m);pg.click('#bpCls')
    pg.wait_for_timeout(200)
    ok('resumen_con_vencido','1 vencidos' in pg.inner_text('#bbR1') and 'multa estimada' in pg.inner_text('#bbR1'))
    ok('multa_calculada_3dias_x_10','$30.00' in pg.inner_text('#bbR1') or '30' in pg.inner_text('#bbR1'))
    pg.select_option('#bbFil1','venc');pg.wait_for_timeout(200)
    ok('filtro_vencidos','Carla' in pg.inner_text('#bbTb1') and 'Ana' not in pg.inner_text('#bbTb1') and 'Vencido 3' in pg.inner_text('#bbTb1'))
    # devolver con retraso
    pg.click('#bbTb1 button[data-bbd]');W(pg,"document.getElementById('bbMsg').textContent.indexOf('retraso')>-1")
    ok('devolucion_tarde_muestra_multa','3 día' in pg.inner_text('#bbMsg') and '30' in pg.inner_text('#bbMsg'))
    cj=get('prestamos/s3')['data']['items'][0]
    ok('devolucion_guardada',cj['devuelto']==HOYI)
    ok('disponibles_suben_al_devolver',get('libros/L4')['data']['disp']==2)
    # renovar (Ana)
    pg.select_option('#bbFil1','');pg.fill('#bbBus1','Ana');pg.wait_for_timeout(300)
    pg.click('#bbTb1 tr:has-text("Rayuela") button[data-bbr]');W(pg,"document.getElementById('bbMsg').textContent.indexOf('Renovado')>-1")
    ra=[x for x in get('prestamos/s1')['data']['items'] if x['libro']=='L1'][0]
    ok('renovacion_extiende_y_cuenta',ra['renovaciones']==1 and ra['vence']==(datetime.date.fromisoformat(HOYI)+datetime.timedelta(days=10)).isoformat())
    pg.click('#bbTb1 tr:has-text("Rayuela") button[data-bbr]');W(pg,"document.getElementById('bbMsg').textContent.indexOf('Renovado')>-1");pg.wait_for_timeout(300)
    ok('renovacion_maxima_2_oculta_boton',pg.locator('#bbTb1 tr:has-text("Rayuela") button[data-bbr]').count()==0)
    pg.select_option('#bbFil1','hist');pg.fill('#bbBus1','');pg.wait_for_timeout(300)
    ok('historial_muestra_devueltos','Carla' in pg.inner_text('#bbTb1') and 'Devuelto el' in pg.inner_text('#bbTb1'))
    # --- editar libro: no bajar ejemplares por debajo de prestados
    pg.click('#bbT2');pg.fill('#bbBus2','Rayuela');pg.wait_for_timeout(300);pg.click('#bbTb2 button[data-bbe]');pg.wait_for_selector('#dBl[open]')
    pg.fill('#blEj','1');pg.click('#blGuarda');ok('no_baja_ejemplares_bajo_prestados','prestados' in pg.inner_text('#blMsg'))
    pg.click('#blCls')
    # --- CSV catálogo
    with pg.expect_download() as dl:pg.click('#bbCsv')
    cv=open(dl.value.path(),encoding='utf-8-sig').read()
    ok('csv_catalogo','Rayuela' in cv and 'Título' in cv and 'El Aleph' in cv)
    # --- inventario UI
    pg.evaluate("etab('Z')");W(pg,"!document.getElementById('eZ').hidden")
    ok('inventario_lista_sembrado','Proyector' in pg.inner_text('#ivTb') and 'INV-0001' in pg.inner_text('#ivTb'))
    ok('inventario_resumen_valor','1 bienes' in pg.inner_text('#ivRes') and '8,500.50' in pg.inner_text('#ivRes'))
    pg.click('#ivNuevo');pg.wait_for_selector('#dIf[open]');pg.click('#ifGuarda');ok('inv_exige_nombre','nombre' in pg.inner_text('#ifMsg'))
    pg.fill('#ifNom','Silla de escritorio');pg.fill('#ifCan','0');pg.click('#ifGuarda');ok('inv_cantidad_invalida','cantidad' in pg.inner_text('#ifMsg'))
    pg.fill('#ifCan','10');pg.fill('#ifCat','Mobiliario');pg.fill('#ifCos','1200');pg.fill('#ifUbi','Aula 3');pg.fill('#ifRsp','Lupita');pg.click('#ifGuarda');W(pg,"document.getElementById('ifMsg').textContent.indexOf('Guardado')>-1")
    ok('inv_codigo_autogenerado','INV-0002' in pg.inner_text('#ifMsg'))
    pg.fill('#ifNom','Silla ejecutiva');pg.fill('#ifCod','INV-0001');pg.click('#ifGuarda');ok('inv_codigo_duplicado','Ya existe' in pg.inner_text('#ifMsg'))
    pg.click('#ifCls');pg.wait_for_timeout(300)
    ok('inv_resumen_actualiza','11 bienes' in pg.inner_text('#ivRes') and '20,500.50' in pg.inner_text('#ivRes'))
    pg.select_option('#ivCat','Mobiliario');pg.wait_for_timeout(200);ok('inv_filtro_categoria','Silla' in pg.inner_text('#ivTb') and 'Proyector' not in pg.inner_text('#ivTb'))
    pg.select_option('#ivCat','');pg.fill('#ivBus','lupita');pg.wait_for_timeout(200);ok('inv_busqueda_responsable','Silla' in pg.inner_text('#ivTb') and 'Proyector' not in pg.inner_text('#ivTb'))
    pg.fill('#ivBus','')
    pg.click('#ivTb tr:has-text("Proyector") button[data-ife]');pg.wait_for_selector('#dIf[open]');pg.select_option('#ifEst','Baja');pg.fill('#ifBajaMot','') ;pg.click('#ifGuarda');ok('inv_baja_exige_motivo','motivo' in pg.inner_text('#ifMsg'))
    pg.fill('#ifBajaMot','Se descompuso');pg.click('#ifGuarda');W(pg,"document.getElementById('ifMsg').textContent.indexOf('Guardado')>-1");pg.click('#ifCls');pg.wait_for_timeout(300)
    pj=get('inventario/i1')['data']
    ok('inv_baja_guardada',pj['estado']=='Baja' and pj['bajaMotivo']=='Se descompuso' and pj['bajaFecha']==HOYI)
    ok('inv_baja_sale_del_valor','10 bienes' in pg.inner_text('#ivRes') and '12,000.00' in pg.inner_text('#ivRes') and '1 dados de baja' in pg.inner_text('#ivRes'))
    pg.select_option('#ivEst','Baja');pg.wait_for_timeout(200);ok('inv_filtro_estado_baja','Proyector' in pg.inner_text('#ivTb') and 'Silla' not in pg.inner_text('#ivTb'))
    pg.select_option('#ivEst','')
    with pg.expect_download() as dl2:pg.click('#ivCsv')
    cv2=open(dl2.value.path(),encoding='utf-8-sig').read()
    ok('csv_inventario','Proyector' in cv2 and 'Se descompuso' in cv2 and 'INV-0002' in cv2)
    # --- buscador global
    pg.evaluate("ir('home')");W(pg,"MOD==='home'");pg.fill('#hBus','inventario');pg.wait_for_timeout(300);ok('buscador_lista_inventario','Inventario de bienes' in pg.inner_text('#hBusR'))
    # --- portal del alumno
    pa1=abre(A1);W(pa1,"document.getElementById('bbPorBus')!==null",20)
    ok('portal_muestra_sus_prestamos','Rayuela' in pa1.inner_text('#poBody') and 'El Aleph' in pa1.inner_text('#poBody'))
    ok('portal_no_muestra_prestamos_ajenos','Pedro Páramo' not in pa1.inner_text('#poBody').split('Buscar un libro')[0])
    pa1.fill('#bbPorBus','borges');pa1.wait_for_timeout(300)
    ok('portal_busca_catalogo','Ficciones' in pa1.inner_text('#bbPorRes') and 'Rayuela' not in pa1.inner_text('#bbPorRes'))
    pa1.fill('#bbPorBus','rayuela');pa1.wait_for_timeout(300)
    ok('portal_muestra_disponibles',pa1.evaluate("(document.querySelector('#bbPorRes tbody tr td.n')||{textContent:'?'}).textContent.trim()")=='0')
    pa1.fill('#bbPorBus','zzzzzz');pa1.wait_for_timeout(300);ok('portal_sin_resultados','No encontramos' in pa1.inner_text('#bbPorRes'))
    pa3=abre(A3);W(pa3,"document.getElementById('bbPorBus')!==null",20)
    ok('portal_sin_prestamos_activos','No tienes libros prestados' in pa3.inner_text('#poBody'))
    # --- respaldo del navegador incluye colecciones
    ok('respaldo_incluye_colecciones',pg.evaluate("BKCOL.indexOf('libros')>-1&&BKCOL.indexOf('prestamos')>-1&&BKCOL.indexOf('inventario')>-1"))
    ok('sin_errores_de_pagina',not errs)
    b.close()
bad=[k for k,v in R.items() if not v]
print(len(R)-len(bad),'/',len(R));print('FALLAN:',bad);print('errores:',errs[:3])
p.terminate()
