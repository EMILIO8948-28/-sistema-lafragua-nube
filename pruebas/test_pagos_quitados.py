"""Bitácora de pagos quitados o modificados: registro automático (también del Administrador), permisos de solo lectura para el admin y pantalla."""
import subprocess,time,json,os,re,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3168;B='http://127.0.0.1:%d'%PORT;DD='/tmp/nbdata_pq'
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
    pg=pagina(ctx);pg.goto(B+'/');pg.wait_for_url('**/configurar.html');pg.fill('#tk','tk');pg.fill('#nm','Administrador');pg.fill('#us','admin');pg.fill('#pw','clave-segura-1');pg.fill('#p2','clave-segura-1');pg.click('#go');pg.wait_for_url(B+'/')
    W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&typeof DBH!=='undefined'&&DBH!==null")
    def raw(cx,path,o,m='put'):return getattr(cx.request,m)(B+'/api/doc/'+path,data=json.dumps(o),headers=HDR)
    def put(path,o):
        r=raw(ctx,path,o);assert r.status==200,(path,r.status,r.text()[:200])
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    for i,n in enumerate(['Ana López','Beto Mena'],1):put('students/s%d'%i,{'mat':'100%d'%i,'nombre':n,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
    def usr(u,name,rol,modulos=None):
        d={'u':u,'name':name,'rol':rol,'clave':'clave-%s-123'%u}
        if modulos is not None:d['modulos']=modulos
        r=ctx.request.post(B+'/api/usuarios',data=json.dumps(d),headers=HDR);assert r.status==200,(u,r.status,r.text())
    usr('caja1','Rosa Caja','caja');usr('esc1','Esc Uno','personalizado',{'escolar':'editar'})
    def sesion(u,c):
        cx=b.new_context(viewport={'width':1200,'height':950});r=cx.request.post(B+'/api/login',data=json.dumps({'u':u,'clave':c}),headers=HDR);assert r.status==200,(u,r.status,r.text());return cx
    CJ=sesion('caja1','clave-caja1-123');E1=sesion('esc1','clave-esc1-123')
    P=lambda i,m,**k:dict({'id':i,'fecha':'2026-11-10','monto':m,'metodo':'Efectivo','estado':'confirmado','folio':'R-%06d'%int(i[1:])},**k)
    LG=lambda cx,sid,pagos:raw(cx,'ledger/'+sid,{'pagos':pagos})
    REG=lambda:[v['data'] for v in ctx.request.get(B+'/api/col/pagosquit').json()['docs']]
    ok('al_crear_el_historial_no_se_registra_nada',LG(ctx,'s1',[P('p1',1300),P('p2',800),P('p3',500,estado='pendiente')]).status==200 and REG()==[])
    ok('agregar_un_pago_no_se_registra',LG(ctx,'s1',[P('p1',1300),P('p2',800),P('p3',500,estado='pendiente'),P('p4',200)]).status==200 and REG()==[])
    # admin quita un pago
    ok('admin_quita_un_pago',LG(ctx,'s1',[P('p1',1300),P('p3',500,estado='pendiente'),P('p4',200)]).status==200)
    r=REG();ok('queda_el_registro_del_admin',len(r)==1 and r[0]['tipo']=='quitado' and r[0]['u']=='admin' and r[0]['alumno']=='Ana López' and r[0]['mat']=='1001' and r[0]['pago']['monto']==800 and r[0]['pago']['folio']=='R-000002' and r[0]['pago']['metodo']=='Efectivo')
    ok('el_registro_trae_fecha_y_hora',r[0]['ts']>0 and r[0]['fecha'][:10]==datetime.date.today().isoformat() or r[0]['fecha'][:10]==datetime.datetime.utcnow().date().isoformat())
    # caja cambia un monto
    ok('caja_cambia_un_monto',LG(CJ,'s1',[P('p1',1000),P('p3',500,estado='pendiente'),P('p4',200)]).status==200)
    r=[x for x in REG() if x['tipo']=='monto'];ok('queda_el_cambio_de_monto',len(r)==1 and r[0]['antes']==1300 and r[0]['despues']==1000 and r[0]['u']=='caja1' and r[0]['nombre']=='Rosa Caja' and r[0]['rol']=='caja')
    # confirmar un pendiente no se registra; desconfirmar sí
    n0=len(REG());ok('confirmar_un_pendiente_no_se_registra',LG(CJ,'s1',[P('p1',1000),P('p3',500),P('p4',200)]).status==200 and len(REG())==n0)
    ok('caja_deja_de_confirmar_un_pago',LG(CJ,'s1',[P('p1',1000,estado='pendiente'),P('p3',500),P('p4',200)]).status==200)
    r=[x for x in REG() if x['tipo']=='estado'];ok('queda_la_confirmacion_quitada',len(r)==1 and r[0]['antes']=='confirmado' and r[0]['despues']=='pendiente' and r[0]['pago']['id']=='p1')
    # un cambio que no toca monto ni confirmación no se registra
    n0=len(REG());ok('cambiar_la_nota_no_se_registra',LG(CJ,'s1',[P('p1',1000,estado='pendiente',nota='x'),P('p3',500),P('p4',200)]).status==200 and len(REG())==n0)
    # quitar sin permiso: bloqueado y sin registro
    n0=len(REG());rr=LG(CJ,'s1',[P('p1',1000,estado='pendiente',nota='x'),P('p3',500)]);ok('caja_no_puede_quitar_sin_autorizacion',rr.status==403 and rr.json().get('requiereAutorizacion') and len(REG())==n0)
    ok('el_pago_sigue_ahi',len(ctx.request.get(B+'/api/doc/ledger/s1').json()['data']['pagos'])==3)
    # eliminar el historial completo
    LG(ctx,'s2',[P('p7',900),P('p8',1100)])
    n0=len(REG());rd=ctx.request.delete(B+'/api/doc/ledger/s2',headers=HDR);ok('admin_elimina_el_historial',rd.status==200)
    r=REG();nuevos=r[:]
    q=[x for x in r if x['sid']=='s2'];ok('se_registran_todos_sus_pagos',sorted(x['pago']['monto'] for x in q)==[900,1100] and all(x['tipo']=='quitado' and 'historial' in x['via'] for x in q))
    # eliminar al alumno
    LG(ctx,'s2',[P('p9',700)]);rd=ctx.request.delete(B+'/api/doc/students/s2',headers=HDR);ok('admin_elimina_al_alumno',rd.status==200)
    q=[x for x in REG() if x['sid']=='s2' and x['pago']['monto']==700];ok('al_eliminar_al_alumno_queda_registrado_su_pago',len(q)==1 and 'alumno' in q[0]['via'] and q[0]['alumno']=='Beto Mena')
    # permisos
    ok('el_admin_no_puede_editar_la_bitacora',raw(ctx,'pagosquit/x',{'a':1}).status==403 and ctx.request.delete(B+'/api/doc/pagosquit/'+REG()[0]['id'],headers=HDR).status==403)
    ok('caja_no_ve_la_bitacora',len(CJ.request.get(B+'/api/col/pagosquit').json().get('docs',[]))==0 and CJ.request.get(B+'/api/doc/pagosquit/'+REG()[0]['id']).json().get('exists')==False)
    ok('escolar_no_ve_la_bitacora',len(E1.request.get(B+'/api/col/pagosquit').json().get('docs',[]))==0)
    ok('caja_no_escribe_la_bitacora',raw(CJ,'pagosquit/z',{'a':1}).status==403)
    ok('sigue_el_registro_tras_intentar_borrarlo',len(REG())>=6)
    # pantalla
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&Object.keys(PQ).length>=6")
    pg.evaluate("ir('sp')");W(pg,"MOD==='sp'");pg.click('#sxTpag');W(pg,"!document.getElementById('sxPpag').hidden")
    W(pg,"document.getElementById('pqTb').rows.length>=6")
    n=pg.evaluate("document.getElementById('pqTb').rows.length");tx=pg.inner_text('#pqTb')
    ok('pantalla_lista_los_registros',n==len(REG()) and 'Rosa Caja' in tx and 'Ana López' in tx and 'R-000002' in tx and 'Cambió el monto de $1,300.00 a $1,000.00' in tx and 'Dejó de estar confirmado' in tx)
    ok('pantalla_suma_lo_quitado','pagos quitados' in pg.inner_text('#pqRes') and '$' in pg.inner_text('#pqRes'))
    pg.select_option('#pqTipo','monto');pg.wait_for_timeout(200);ok('filtra_por_tipo',pg.evaluate("document.getElementById('pqTb').rows.length")==1)
    pg.select_option('#pqTipo','');pg.fill('#pqBus','rosa');pg.wait_for_timeout(200);ok('busca_por_quien',pg.evaluate("document.getElementById('pqTb').rows.length")==len([x for x in REG() if x['u']=='caja1']))
    pg.fill('#pqBus','zzzz');pg.wait_for_timeout(200);ok('sin_resultados_avisa','No hay registros' in pg.inner_text('#pqTb'))
    pg.fill('#pqBus','');pg.fill('#pqDes','2999-01-01');pg.wait_for_timeout(200);ok('filtra_por_fecha',pg.evaluate("document.getElementById('pqTb').rows.length")==1 and 'No hay registros' in pg.inner_text('#pqTb'))
    pg.fill('#pqDes','')
    with pg.expect_download() as dl:pg.click('#pqCsv')
    cv=open(dl.value.path(),encoding='utf-8-sig').read();ok('csv',cv.startswith('Fecha,Hora,Quién') and 'Rosa Caja' in cv and 'Quitó el pago' in cv and cv.count('\n')>=len(REG()) and dl.value.suggested_filename.startswith('pagos-quitados-'))
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',not errs)
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
if errs:print('ERRORES JS:',errs[:5])
