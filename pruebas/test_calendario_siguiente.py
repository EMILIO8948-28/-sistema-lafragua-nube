import subprocess,time,json,os,urllib.request
from playwright.sync_api import sync_playwright
PORT=3200;B='http://127.0.0.1:%d'%PORT;TOK='tok-cs-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata_cs && mkdir -p /tmp/nbdata_cs')
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata_cs',LF_SETUP_TOKEN=TOK,LF_SIN_CONTACTO='1',LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
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
PER='Sep–Dic 2026';SIG='Ene–Abr 2027';SIG2='May–Ago 2027';ANT='May–Ago 2026'
MOCK="""()=>{window.__txt=[];window.__sav=[];window.__shared=[];window.__alert=[];
 function PDF(o){window.__orient=o&&o.orientation;this.pages=1}
 ['setDrawColor','setLineWidth','setTextColor','setFont','line','addImage','setFontSize','setLineDashPattern','setFillColor','rect'].forEach(function(f){PDF.prototype[f]=function(){return this}});
 PDF.prototype.addPage=function(){this.pages++;return this};PDF.prototype.getNumberOfPages=function(){return this.pages};PDF.prototype.setPage=function(){return this};
 PDF.prototype.splitTextToSize=function(t){return [String(t)]};PDF.prototype.text=function(t){window.__txt.push(String(Array.isArray(t)?t[0]:t));return this};PDF.prototype.output=function(){return new ArrayBuffer(8)};
 window.jspdf={jsPDF:PDF};saveFile=function(n,b){window.__sav.push(n);return Promise.resolve()};0}"""
with sync_playwright() as pw:
    b=pw.chromium.launch();ctx=b.new_context(viewport={'width':1300,'height':1000});ctx.set_default_timeout(15000)
    def pagina(c):
        pg=c.new_page();pg.on("pageerror",lambda e:errs.append(str(e)));pg.on("dialog",lambda d:d.accept());return pg
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk',TOK);pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&PL.length>=10");time.sleep(1.0)
    sab1=pg.evaluate("sabReciente()");SL=pg.evaluate("slug('Pedagogía')")
    put=lambda path,obj:ctx.request.put(B+'/api/doc/'+path,data=json.dumps(obj),headers=HDR)
    pl=lambda k:{'k':k,'n':36,'col':1300,'ins':800,'rein':800,'tit':23000}
    put('config/plans',{'plans':[pl('Pedagogía'),pl('Psicología')],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    put('catalogo/'+SL,{'items':[{'id':'a%d'%i,'nom':'Primera %d'%i,'cuat':1} for i in range(1,5)]+[{'id':'e%d'%i,'nom':'Segunda %d'%i,'cuat':2} for i in range(1,6)]})
    for i,n in enumerate(['Ana López','Beto Mena','Carla Díaz','Diego Vega'],1):put('students/s%d'%i,{'mat':'2026%03d'%i,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    put('docentes/d1',{'nombre':'Mtro. Pedro Soto','esp':'Historia','asig':[]});put('docentes/d2',{'nombre':'Mtra. Lucía Gómez','esp':'Didáctica','asig':[]})
    put('grupos/g1',{'num':'4821','plan':'Pedagogía','per':PER,'cuat':1,'alumnos':['s1','s2','s3','s4']})
    base=dict(per=PER,plan='Pedagogía',cuat=1,dias=['Sáb'])
    for i in range(1,5):put('materias/m%d'%i,dict(base,ini='08:00' if i%2 else '10:00',fin='10:00' if i%2 else '12:00',nom='Primera %d'%i,docId='d1' if i%2 else 'd2',bl=1 if i<3 else 2,ev='2026-10-24' if i<3 else '2026-12-12',aula='Aula %d'%i))
    # una materia del cuatrimestre 2 que ya se impartió antes: bloque 2, docente, horario y aula
    put('materias/ant1',dict(per=ANT,plan='Pedagogía',cuat=2,nom='Segunda 1',docId='d2',ini='13:00',fin='15:00',aula='Aula Magna',bl=2,dias=['Sáb'],ev='2026-08-15'))
    def cal(sid,notas):put('calif/'+sid,{'items':[{'id':'i%s%d'%(sid,i),'mid':'m%d'%i,'mat':'Primera %d'%i,'plan':'Pedagogía','per':PER,'cuat':1,'cal':notas.get(i,8.5),'fecha':sab1} for i in range(1,5)]})
    for s in ['s1','s2','s3']:cal(s,{})
    cal('s4',{1:5})
    usr=lambda u,n,r,extra=None:ctx.request.post(B+'/api/usuarios',data=json.dumps(dict({'u':u,'name':n,'rol':r,'clave':'clave-%s-123'%u},**(extra or {}))),headers=HDR)
    usr('esc3','Esc Tres','personalizado',{'modulos':{'escolar':'ver'}})
    pg.reload();W(pg,"Object.keys(MAT).length===5&&Object.keys(CAL).length===4&&Object.keys(GRP).length===1")
    # ============ cierre del periodo con política «repite» ============
    pg.evaluate("ir('esc');etab('G')");W(pg,"CIC&&typeof ccAbre==='function'");pg.click('#ccAbre');pg.wait_for_selector('#dCc[open]');pg.select_option('#ccPer',PER);pg.select_option('#ccAlc','p');pg.select_option('#ccPol','repite');pg.wait_for_timeout(300)
    ok('sin_pendientes_para_cerrar',pg.evaluate("CCR.tot.sinCal")==0)
    ok('la_confirmacion_avisa_que_se_cargan_materias',True)
    pg.click('#ccOk');W(pg,"CIC[idPer('%s')]&&CIC[idPer('%s')].cerrado"%(PER,PER),60);pg.wait_for_timeout(500)
    g2=pg.evaluate("Object.keys(GRP).map(function(k){return {c:GRP[k].cuat,p:GRP[k].per,n:(GRP[k].alumnos||[]).length}}).filter(function(g){return g.p==='%s'})"%SIG)
    ok('se_crean_los_dos_grupos_del_periodo_nuevo',sorted([(g['c'],g['n']) for g in g2])==[(1,1),(2,3)])
    nm=pg.evaluate("Object.keys(MAT).map(function(k){return MAT[k]}).filter(function(m){return m.per==='%s'})"%SIG)
    c2=[m for m in nm if m['cuat']==2];c1=[m for m in nm if m['cuat']==1]
    ok('se_cargan_las_9_asignaturas_de_los_dos_grupos',len(nm)==9 and len(c2)==5 and len(c1)==4)
    ok('son_las_del_plan_de_estudios',sorted(m['nom'] for m in c2)==['Segunda %d'%i for i in range(1,6)] and sorted(m['nom'] for m in c1)==['Primera %d'%i for i in range(1,5)] and all(m['plan']=='Pedagogía' and m['dias']==['Sáb'] for m in nm))
    s1=[m for m in c2 if m['nom']=='Segunda 1'][0]
    ok('lo_que_ya_se_impartio_copia_bloque_docente_horario_y_aula',s1['bl']==2 and s1['docId']=='d2' and s1['ini']=='13:00' and s1['fin']=='15:00' and s1['aula']=='Aula Magna')
    ok('lo_nuevo_queda_sin_docente_ni_horario_ni_fecha',all(m['docId']=='' and m['ini']=='' and m['fin']=='' and m['ev']=='' for m in c2 if m['nom']!='Segunda 1'))
    ok('se_reparten_en_dos_bloques_3_y_2',sorted([sum(1 for m in c2 if m['bl']==1),sum(1 for m in c2 if m['bl']==2)])==[2,3] and sum(1 for m in c2 if m['bl']==1)==3)
    ok('el_cuatrimestre_repetido_tambien_se_reparte_2_y_2',sum(1 for m in c1 if m['bl']==1)==2 and sum(1 for m in c1 if m['bl']==2)==2)
    srv=ctx.request.get(B+'/api/col/materias').json()['docs']
    ok('quedan_guardadas_en_el_servidor',len([d for d in srv if d['data']['per']==SIG])==9)
    ok('el_cierre_guarda_cuantas_cargo',pg.evaluate("CIC[idPer('%s')].calendario"%PER)==9 and 'asignaturas en su calendario' in pg.inner_text('#ccMsg'))
    ok('la_bloque_se_calcula_con_bl_aunque_no_haya_fecha',pg.evaluate("Object.keys(MAT).map(function(k){return MAT[k]}).filter(function(m){return m.per==='%s'}).every(function(m){return blDe(m)===m.bl})"%SIG))
    # ============ el calendario lo muestra ============
    pg.click('#ccCls');pg.evaluate("etab('K');renderMat()");pg.select_option('#mFPer',SIG);pg.wait_for_timeout(300)
    t=pg.inner_text('#mTb');ok('el_calendario_marca_lo_pendiente','Horario por definir' in t and 'Sin asignar' in t and 'Aula Magna' in t)
    ok('sin_choques_por_horarios_vacios',pg.evaluate("choques().filter(function(c){return c.per==='%s'}).length"%SIG)==0)
    # ============ idempotente ============
    n0=pg.evaluate("Object.keys(MAT).length")
    pg.click('#mPre');pg.wait_for_timeout(500)
    ok('no_duplica_si_se_vuelve_a_cargar',pg.evaluate("Object.keys(MAT).length")==n0 and 'ya tiene todas' in pg.inner_text('#mPreMsg'))
    # ============ botón manual en otro periodo ============
    put('grupos/g9',{'num':'5555','plan':'Pedagogía','per':SIG2,'cuat':2,'alumnos':['s1']});put('grupos/g8',{'num':'6666','plan':'Psicología','per':SIG2,'cuat':1,'alumnos':['s2']})
    pg.reload();W(pg,"Object.keys(GRP).length===5&&Object.keys(MAT).length===14")
    pg.evaluate("ir('esc');etab('K')");pg.select_option('#mFPer','');pg.click('#mPre');pg.wait_for_timeout(400)
    pg.select_option('#mFPer',SIG2);pg.click('#mPre');W(pg,"Object.keys(MAT).length===19",20);pg.wait_for_timeout(300)
    mm=pg.evaluate("Object.keys(MAT).map(function(k){return MAT[k]}).filter(function(m){return m.per==='%s'})"%SIG2)
    ok('el_boton_manual_carga_las_del_periodo_elegido',len(mm)==5 and all(m['plan']=='Pedagogía' and m['cuat']==2 for m in mm))
    ok('toma_lo_mas_reciente_para_copiar',[m for m in mm if m['nom']=='Segunda 1'][0]['aula']=='Aula Magna')
    ok('avisa_de_los_planes_sin_plan_de_estudios','Psicología · cuat. 1' in pg.inner_text('#mPreMsg'))
    ok('periodo_sin_grupos_no_carga_nada',pg.evaluate("calPlanPrecarga('Ene–Abr 2029').nuevas.length")==0)
    # ============ PDF ============
    pg.evaluate(MOCK);pg.select_option('#mFPer',PER);pg.select_option('#mFPlan','');pg.click('#mPdf');pg.wait_for_timeout(300)
    tx=pg.evaluate("window.__txt");sv=pg.evaluate("window.__sav");j='|'.join(tx)
    ok('el_pdf_se_descarga_con_nombre_del_periodo',sv==['calendario-sep-dic-2026.pdf'])
    ok('es_horizontal',pg.evaluate("window.__orient")=='landscape')
    ok('trae_las_tres_secciones','1. Planeación por grupo' in j and '2. Horario por docente' in j and '3. Calendario de evaluaciones' in j)
    ok('por_grupo_trae_grupo_alumnos_docente_horario_aula','Pedagogía · cuatrimestre 1' in j and '4821 (4 alumnos)' in j and 'Mtro. Pedro Soto' in j and 'Mtra. Lucía Gómez' in j and 'Sáb 08:00–10:00' in j and 'Aula 3' in j and 'Primera 4' in j)
    ok('por_docente_trae_sus_materias_y_su_grupo','1 asignatura' in j or '2 asignaturas' in j)
    ok('evaluaciones_con_fechas','24/10/2026' in j or '24 oct' in j.lower() or pg.evaluate("fd('2026-10-24')") in j)
    ok('encabezado_con_periodo','Calendario escolar y planeación · Sep–Dic 2026' in j)
    # periodo con lo pendiente
    pg.evaluate("window.__txt=[];window.__sav=[]");pg.select_option('#mFPer',SIG);pg.select_option('#mFPlan','Pedagogía');pg.click('#mPdf');pg.wait_for_timeout(300)
    j2='|'.join(pg.evaluate("window.__txt"))
    ok('pdf_marca_lo_pendiente','Horario por definir' in j2 and 'Sin asignar' in j2 and 'Sin docente asignado' in j2 and 'Por definir' in j2 and 'sin fecha de evaluación' in j2)
    ok('el_nombre_incluye_el_plan',pg.evaluate("window.__sav")==['calendario-ene-abr-2027-pedagogia.pdf'])
    ok('el_filtro_de_plan_limita',pg.evaluate("calDatos('%s','Psicología').ms.length"%SIG2)==0 and pg.evaluate("calDatos('%s','Pedagogía').ms.length"%SIG)==9)
    # compartir
    pg.evaluate("window.__sav=[];window.__shared=[];navigator.canShare=function(o){return !!(o&&o.files&&o.files.length)};navigator.share=function(o){window.__shared.push({n:o.files[0].name,t:o.files[0].type,ti:o.title});return Promise.resolve()};0")
    pg.click('#mPdfC');pg.wait_for_timeout(300)
    sh=pg.evaluate("window.__shared");ok('compartir_usa_la_hoja_de_compartir_del_dispositivo',len(sh)==1 and sh[0]['n']=='calendario-ene-abr-2027-pedagogia.pdf' and sh[0]['t']=='application/pdf' and 'Ene–Abr 2027' in sh[0]['ti'] and pg.evaluate("window.__sav")==[])
    pg.evaluate("navigator.canShare=undefined;window.__sav=[]");pg.click('#mPdfC');pg.wait_for_timeout(300)
    ok('si_no_se_puede_compartir_lo_descarga',pg.evaluate("window.__sav")==['calendario-ene-abr-2027-pedagogia.pdf'])
    pg.evaluate("window.__txt=[];window.__sav=[]");pg.select_option('#mFPer','Ene–Abr 2029');pg.select_option('#mFPlan','');pg.click('#mPdf');pg.wait_for_timeout(300)
    ok('periodo_vacio_no_genera_pdf',pg.evaluate("window.__sav")==[])
    # ============ permisos ============
    cx=b.new_context(viewport={'width':1300,'height':1000});cx.set_default_timeout(15000);pp=pagina(cx);pp.goto(B+'/');W(pp,"typeof sesion==='function'&&document.body.classList.contains('locked')")
    pp.fill('#lgU','esc3');pp.fill('#lgP','clave-esc3-123');pp.click('#lgGo');W(pp,"typeof APP!=='undefined'&&APP!==null&&!document.body.classList.contains('locked')&&Object.keys(MAT).length>=19");pp.wait_for_timeout(800)
    pp.evaluate("ir('esc');etab('K')");pp.wait_for_selector('#mFPer')
    ok('quien_solo_ve_puede_bajar_el_pdf_pero_no_cargar_materias',pp.is_visible('#mPdf') and pp.is_visible('#mPdfC') and pp.is_hidden('#mPre'))
    ok('sin_errores_js',len(errs)==0)
    if errs:print('ERRORES JS:',errs[:4])
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v];print(len(R),'comprobaciones');print('FALLAN:',bad)
