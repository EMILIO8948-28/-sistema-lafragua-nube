"""Resultados de prospectos: alumnos inscritos por medio por el que se enteraron y por asesor, con filtros y exportación."""
import subprocess,time,json,os,re,urllib.request,datetime
from playwright.sync_api import sync_playwright
PORT=3169;B='http://127.0.0.1:%d'%PORT;DD='/tmp/nbdata_va'
ENVV=dict(os.environ,PORT=str(PORT),DATA_DIR=DD,LF_SETUP_TOKEN='tk',LF_SIN_PRECARGA='1')
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
    put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':'Derecho','n':36,'col':1500,'ins':800,'rein':800,'tit':23000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
    A=lambda i,n,pl,ing,**k:put('students/'+i,dict({'mat':'200'+i[1:],'nombre':n,'carrera':pl,'programa':pl,'ingreso':ing,'nuevo':False},**k))
    A('s1','Ana López','Pedagogía',2026,via='redes')
    A('s2','Beto Mena','Pedagogía',2026,via='asesor',asNom='Laura Pérez',asTel='722 111 1111')
    A('s3','Carla Díaz','Derecho',2026,via='asesor',asNom='laura  pérez')
    A('s4','Dani Ruiz','Derecho',2025,via='asesor',asNom='Marco Díaz',asTel='722 222 2222')
    A('s5','Eli Paz','Pedagogía',2025,via='tel')
    A('s6','Fer Gil','Derecho',2025)
    put('egresados/s5',{'sid':'s5','fecha':'2026-08-01'})
    pg.reload();W(pg,"typeof APP!=='undefined'&&APP!==null&&ROL==='admin'&&S.length===6&&EGR&&EGR.s5")
    pg.evaluate("ST.s3.baja={fecha:'2026-10-01',tipo:'Baja voluntaria'}")
    pg.evaluate("ir('pr')");W(pg,"MOD==='pr'");pg.click('#pxTr');W(pg,"!document.getElementById('pxPr').hidden&&document.getElementById('rsVia').rows.length>0")
    d=pg.evaluate("(function(){var o=vaDatos();return {tot:o.tot,v:o.vias.map(function(x){return [x.k,x.n,x.act,x.baja]}),a:o.ases.map(function(x){return [x.nom,x.tel,x.n,x.act,x.baja]})}})()")
    ok('total_de_alumnos',d['tot']==6)
    ok('por_medio',d['v']==[['Algún asesor',3,2,1],['No especificado',1,1,0],['Número de teléfono de la escuela',1,0,0],['Redes sociales de la escuela',1,1,0]] or sorted(d['v'])==sorted([['Algún asesor',3,2,1],['No especificado',1,1,0],['Número de teléfono de la escuela',1,0,0],['Redes sociales de la escuela',1,1,0]]))
    ok('asesores_agrupados_sin_importar_mayusculas_ni_espacios',[a[:1]+a[2:] for a in d['a']]==[['Laura Pérez',2,1,1],['Marco Díaz',1,1,0]] and d['a'][0][1]=='722 111 1111')
    tx=pg.inner_text('#vPr') if pg.locator('#vPr').count() else pg.inner_text('#pxPr')
    ok('pantalla_muestra_medios_y_asesores','Algún asesor' in tx and 'Laura Pérez' in tx and 'Marco Díaz' in tx and '50 %' in tx and '3 llegaron por un asesor' in tx)
    ok('porcentaje_de_bajas_por_asesor','50 %' in pg.inner_text('#rsAses'))
    pg.select_option('#rsAnio','2025');pg.wait_for_timeout(200)
    d=pg.evaluate("(function(){var o=vaDatos();return {tot:o.tot,a:o.ases.map(function(x){return x.nom})}})()");ok('filtra_por_anio',d['tot']==3 and d['a']==['Marco Díaz'])
    pg.select_option('#rsAnio','');pg.select_option('#rsPlan','Derecho');pg.wait_for_timeout(200)
    d=pg.evaluate("vaDatos().tot");ok('filtra_por_plan',d==3 and 'Marco Díaz' in pg.inner_text('#rsAses') and 'laura' in pg.inner_text('#rsAses').lower() and 'Ana' not in pg.inner_text('#rsAses'))
    pg.select_option('#rsAnio','2026');pg.wait_for_timeout(200);ok('filtra_por_anio_y_plan',pg.evaluate("vaDatos().tot")==1 and 'laura pérez' in pg.inner_text('#rsAses').lower() and 'Marco' not in pg.inner_text('#rsAses'))
    pg.select_option('#rsPlan','Pedagogía');pg.select_option('#rsAnio','2025');pg.wait_for_timeout(200)
    ok('sin_asesores_avisa','Ningún alumno de este filtro llegó por un asesor' in pg.inner_text('#rsAses'))
    pg.select_option('#rsAnio','');pg.select_option('#rsPlan','')
    with pg.expect_download() as dl:pg.click('#rsCsvV')
    cv=open(dl.value.path(),encoding='utf-8-sig').read();ok('csv','Algún asesor,3,2,1' in cv and 'Laura Pérez,722 111 1111,2,1,1' in cv and 'Marco Díaz' in cv and dl.value.suggested_filename.startswith('alumnos-por-medio-y-asesor-'))
    ok('lo_anterior_sigue_funcionando',pg.evaluate("document.getElementById('rsEmb').children.length")>0)
    ok('sin_identificadores_repetidos',pg.evaluate("(function(){var c={},d=[];document.querySelectorAll('[id]').forEach(function(e){c[e.id]=(c[e.id]||0)+1});for(var k in c)if(c[k]>1)d.push(k);return d})()")==[])
    ok('sin_errores_js',not errs)
    b.close()
p.terminate()
bad=[k for k,v in R.items() if not v]
print(len(R),'comprobaciones');print('FALLAN:',bad)
if errs:print('ERRORES JS:',errs[:5])
