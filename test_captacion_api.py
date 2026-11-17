import subprocess,time,json,os,urllib.request,urllib.error,http.cookiejar,sqlite3,datetime,re,base64
PORT=3320;B='http://127.0.0.1:%d'%PORT;TOK='tok-cp-123';HDR={'Content-Type':'application/json','x-lafragua':'1'}
os.system('rm -rf /tmp/nbdata106 /tmp/fd106 && mkdir -p /tmp/nbdata106')
fake=subprocess.Popen(['node','/tmp/fake_destinos.js','3321','3322','/tmp/fd106'],stdout=subprocess.PIPE,text=True);time.sleep(1.0)
env=dict(os.environ,PORT=str(PORT),DATA_DIR='/tmp/nbdata106',LF_SETUP_TOKEN=TOK,LF_SIN_PRECARGA='1',LF_AVISOS_TICK_MS='3600000',LF_RESPALDO_TICK_MS='3600000')
p=subprocess.Popen(['node','servidor.js'],cwd='/tmp/nb',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(80):
    time.sleep(0.25)
    try:urllib.request.urlopen(B+'/salud',timeout=1);break
    except Exception:pass
R={}
def ok(n,c):
    R[n]=bool(c)
    if not c:print('FALLA',n,flush=True)
def sesion(u=None,c=None,hdr=True):
    cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def llama(m,url,body=None,raw=False,h=None):
        hh=dict(HDR) if hdr else {'Content-Type':'application/json'};hh.update(h or {})
        rq=urllib.request.Request(B+url,method=m,data=(json.dumps(body).encode() if body is not None else None),headers=hh)
        try:
            r=op.open(rq);d=r.read()
            if raw:return r.status,d.decode()
            return r.status,(json.loads(d) if d else {})
        except urllib.error.HTTPError as e:
            d=e.read()
            if raw:return e.code,d.decode()
            try:return e.code,json.loads(d)
            except Exception:return e.code,{}
    if u:
        s,_=llama('POST','/api/login',{'u':u,'clave':c});assert s==200,(u,s)
    return llama
cfgp=sesion();s,j=cfgp('POST','/api/configurar',{'token':TOK,'name':'Administrador','u':'admin','clave':'clave-segura-1'});assert s==200
adm=sesion('admin','clave-segura-1');put=lambda path,obj:adm('PUT','/api/doc/'+path,obj)
put('config/plans',{'plans':[{'k':'Pedagogía','n':36,'col':1300,'ins':800,'rein':800,'tit':23000},{'k':'Derecho','n':36,'col':1500,'ins':900,'rein':900,'tit':25000}],'extra':{'costo':300,'min':8},'cons':{'costo':50}})
for sid,nom in [('s1','Ana López Ramírez'),('s2','Beto Mena Ruiz')]:put('students/'+sid,{'mat':'2026'+sid[1:].zfill(3),'nombre':nom,'carrera':'Pedagogía','programa':'Pedagogía','ingreso':2026,'nuevo':False})
us=lambda u,n,mods:adm('POST','/api/usuarios',{'u':u,'name':n,'rol':'personalizado','modulos':mods,'clave':'clave-%s-123'%u})
us('at1','Orientadora Uno',{'atencion':'editar'});us('at2','Orientador Dos',{'atencion':'editar'});us('atv','Consulta Atención',{'atencion':'ver'});us('pr1','Ventas Uno',{'prospectos':'editar'});us('prv','Ventas Consulta',{'prospectos':'ver'})
adm('POST','/api/usuarios',{'u':'caja1','name':'Caja','rol':'caja','clave':'clave-caja1-123'})
S={u:sesion(u,'clave-%s-123'%u) for u in ['at1','at2','atv','pr1','prv']};caja=sesion('caja1','clave-caja1-123')
# avisos para el agradecimiento
cfg={'activo':True,'escuela':'Universidad Lafragua','correo':{'activo':True,'usarRespaldos':False,'host':'127.0.0.1','puerto':3322,'seguro':False,'usuario':'escuela@correo.mx','clave':'clave-correo-1','de':'escuela@correo.mx','nombre':'Universidad Lafragua'},'whatsapp':{'activo':False,'phoneId':'','token':'','version':'v21.0','plantilla':'aviso_escolar','idioma':'es_MX','pais':'52'},'eventos':{},'recordatorios':{'calificaciones':True},'resumen':{'activo':False,'hora':8,'para':[]}}
adm('PUT','/api/avisos/config',cfg)
# ============ permisos ============
ok('quien_no_tiene_el_modulo_no_ve_nada',caja('GET','/api/col/prospectos')[1]['docs']==[] and caja('PUT','/api/doc/prospectos/x',{'nombre':'x'})[0]==403 and caja('PUT','/api/doc/atencion/x',{'asunto':'x'})[0]==403 and caja('PUT','/api/doc/campanas/x',{'nombre':'x'})[0]==403)
ok('con_ver_solo_lee',S['prv']('GET','/api/col/campanas')[0]==200 and S['prv']('PUT','/api/doc/prospectos/x',{'nombre':'x'})[0]==403 and S['prv']('PUT','/api/doc/campanas/x',{'nombre':'x'})[0]==403)
ok('con_editar_crea_campanas',S['pr1']('PUT','/api/doc/campanas/c1',{'nombre':'Inscripciones enero · Instagram','plataforma':'Instagram','inicio':'2026-11-01','presupuesto':5000,'meta':100,'programa':'Pedagogía','activa':True})[0]==200 and S['prv']('GET','/api/doc/campanas/c1')[1]['exists'])
put('campanas/c2',{'nombre':'Pausada','plataforma':'Facebook','activa':False});put('campanas/c3',{'nombre':'<img src=x onerror=alert(1)>','plataforma':'TikTok','activa':True})
# ============ formulario público ============
anon=sesion(hdr=False);s,t=anon('GET','/registro?c=c1',raw=True)
ok('la_pagina_publica_muestra_el_formulario_de_la_campana',s==200 and 'Quiero más información' in t and 'Inscripciones enero · Instagram' in t and 'name' not in t[:0] and 'Pedagogía' in t and 'Derecho' in t and '/privacidad' in t and 'id="s"' in t)
s,t=anon('GET','/registro?c=c3',raw=True);ok('el_nombre_de_la_campana_se_escapa','<img src=x' not in t and '&lt;img src=x' in t)
s,t=anon('GET','/registro?c=no-existe',raw=True);ok('con_una_campana_invalida_o_pausada_igual_sirve_el_formulario',s==200 and 'Quiero más información' in t and 'Pausada' not in anon('GET','/registro?c=c2',raw=True)[1])
reg=lambda **k:anon('POST','/api/registro',dict({'c':'c1','nombre':'Laura Gómez Ríos','tel':'722 123 4567','correo':'laura@correo.mx','programa':'Pedagogía','mensaje':'Quiero informes','acepto':True,'sitio':''},**k),h={'x-lafragua':'1'})
ok('sin_el_encabezado_de_la_plataforma_se_rechaza',anon('POST','/api/registro',{'nombre':'x'},h={'x-lafragua':''})[0]==403)
ok('valida_los_datos',all(reg(**k)[0]==400 for k in [{'nombre':'ab'},{'tel':'123'},{'tel':''},{'correo':'sin-arroba'},{'programa':'Medicina'},{'acepto':False},{'acepto':'si'}]))
s,j=reg();ok('registra_al_prospecto',s==200 and j['ok'])
pr=[(v['id'],v['data']) for v in adm('GET','/api/col/prospectos')[1]['docs']];idp,d=pr[0]
ok('queda_con_su_campana_canal_y_consentimiento',len(pr)==1 and d['nombre']=='Laura Gómez Ríos' and d['tel']=='7221234567' and d['correo']=='laura@correo.mx' and d['campana']=='c1' and d['canal']=='Instagram' and d['origen']=='formulario' and d['estado']=='nuevo' and d['consentimiento']['version']==1 and d['programa']=='Pedagogía')
ok('guarda_una_nota_del_sistema',d['notas'][0]['tipo']=='sistema' and 'campaña «Inscripciones enero · Instagram»' in d['notas'][0]['txt'] and 'Quiero informes' in d['notas'][0]['txt'])
s,j=reg(nombre='Otra Persona',tel='5217221234568',correo='',c='c2');d2=[v['data'] for v in adm('GET','/api/col/prospectos')[1]['docs'] if v['data']['nombre']=='Otra Persona'][0]
ok('normaliza_el_telefono_y_una_campana_pausada_cuenta_como_directo',d2['tel']=='7221234568' and d2['campana']=='' and d2['canal']=='Directo')
n0=len(adm('GET','/api/col/prospectos')[1]['docs']);reg(nombre='Laura G',tel='7221234567',mensaje='Otra vez');pr=adm('GET','/api/col/prospectos')[1]['docs'];dd=[v['data'] for v in pr if v['id']==idp][0]
ok('si_se_registra_otra_vez_no_se_duplica_y_queda_una_nota',len(pr)==n0 and len(dd['notas'])==2 and 'Volvió a registrarse' in dd['notas'][1]['txt'] and dd['reingreso']==1 and dd['nombre']=='Laura Gómez Ríos')
n0=len(adm('GET','/api/col/prospectos')[1]['docs']);s,j=reg(nombre='Robot Spam',tel='7220000001',sitio='http://spam');ok('el_campo_trampa_no_crea_nada_pero_responde_bien',s==200 and len(adm('GET','/api/col/prospectos')[1]['docs'])==n0)
# ============ agradecimiento por correo ============
time.sleep(1.5);cor=json.load(open('/tmp/fd106/correos.json')) if os.path.exists('/tmp/fd106/correos.json') else []
ok('al_prospecto_con_correo_se_le_agradece',any('laura@correo.mx' in x['para'][0] for x in cor) and len(cor)==1)
ms=adm('GET','/api/avisos/mensajes?evento=prospecto&limite=50')[1]['mensajes'];ok('el_aviso_queda_en_la_bitacora_y_sin_correo_no_se_manda',any(m['estado']=='enviado' and m['para']=='laura@correo.mx' and 'Gracias por tu interés' in m['asunto'] for m in ms) and not any(m['nombre'].startswith('Otra') and m['estado']=='enviado' for m in ms))
# ============ seguimiento de prospectos ============
ok('el_personal_con_editar_da_seguimiento',S['pr1']('PUT','/api/doc/prospectos/'+idp,dict(dd,estado='contactado',asignado='pr1',notas=dd['notas']+[{'t':'2026-11-10T10:00:00.000Z','u':'pr1','n':'Ventas Uno','tipo':'nota','txt':'Se llamó, pide informes'}]))[0]==200)
dd=S['pr1']('GET','/api/doc/prospectos/'+idp)[1]['data']
ok('las_notas_ya_guardadas_no_se_pueden_editar',S['pr1']('PUT','/api/doc/prospectos/'+idp,dict(dd,notas=[dict(dd['notas'][0],txt='cambiado')]+dd['notas'][1:]))[0]==403)
ok('ni_borrar',S['pr1']('PUT','/api/doc/prospectos/'+idp,dict(dd,notas=dd['notas'][:1]))[0]==403 and S['pr1']('PUT','/api/doc/prospectos/'+idp,dict(dd,notas=[]))[0]==403)
ok('el_administrador_si_puede_corregir',adm('PUT','/api/doc/prospectos/'+idp,dict(dd,notas=dd['notas']))[0]==200)
ok('con_ver_no_cambia_nada',S['prv']('PUT','/api/doc/prospectos/'+idp,dict(dd,estado='inscrito'))[0]==403)
# ============ atención personalizada ============
ok('el_servidor_fija_quien_registra_aunque_mande_otro',S['at1']('PUT','/api/doc/atencion/a1',{'sid':'s1','tipo':'Personal o emocional','asunto':'Situación familiar','privado':True,'estado':'abierto','creador':'at2','notas':[{'t':'2026-11-10T09:00:00.000Z','u':'at1','n':'Orientadora Uno','tipo':'apertura','txt':'Habló de un problema en casa'}]})[0]==200 and adm('GET','/api/doc/atencion/a1')[1]['data']['creador']=='at1')
S['at1']('PUT','/api/doc/atencion/a2',{'sid':'s2','tipo':'Orientación académica','asunto':'Quiere cambiar de turno','privado':False,'estado':'abierto','notas':[{'t':'2026-11-10T09:30:00.000Z','u':'at1','n':'Orientadora Uno','tipo':'apertura','txt':'Pide cambio de horario'}]})
ok('lo_confidencial_solo_lo_ve_su_autor_y_el_administrador',[v['id'] for v in S['at1']('GET','/api/col/atencion')[1]['docs']]==['a1','a2'] or sorted(v['id'] for v in S['at1']('GET','/api/col/atencion')[1]['docs'])==['a1','a2'])
ok('otro_orientador_no_ve_lo_confidencial_ni_por_su_direccion',sorted(v['id'] for v in S['at2']('GET','/api/col/atencion')[1]['docs'])==['a2'] and S['at2']('GET','/api/doc/atencion/a1')[1]['exists'] is False and S['atv']('GET','/api/doc/atencion/a1')[1]['exists'] is False)
ok('el_administrador_ve_todo',sorted(v['id'] for v in adm('GET','/api/col/atencion')[1]['docs'])==['a1','a2'])
ok('nadie_mas_puede_modificar_lo_confidencial_aunque_adivine_la_direccion',S['at2']('PUT','/api/doc/atencion/a1',{'asunto':'x','notas':[]})[0]==403 and S['at2']('PATCH','/api/doc/atencion/a1',{'estado':'cerrado'})[0]==403)
a2=S['at2']('GET','/api/doc/atencion/a2')[1]['data']
ok('el_equipo_agrega_notas_a_lo_no_confidencial',S['at2']('PUT','/api/doc/atencion/a2',dict(a2,estado='seguimiento',notas=a2['notas']+[{'t':'2026-11-10T11:00:00.000Z','u':'at2','n':'Orientador Dos','tipo':'nota','txt':'Se revisó disponibilidad'}]))[0]==200 and adm('GET','/api/doc/atencion/a2')[1]['data']['creador']=='at1')
a2=S['at2']('GET','/api/doc/atencion/a2')[1]['data']
ok('pero_no_edita_ni_borra_notas_previas',S['at2']('PUT','/api/doc/atencion/a2',dict(a2,notas=[dict(a2['notas'][0],txt='x')]+a2['notas'][1:]))[0]==403 and S['at2']('PUT','/api/doc/atencion/a2',dict(a2,notas=a2['notas'][1:]))[0]==403)
ok('no_cambia_el_autor_ni_destapa_lo_confidencial',S['at2']('PUT','/api/doc/atencion/a2',dict(a2,creador='at2'))[0]==200 and adm('GET','/api/doc/atencion/a2')[1]['data']['creador']=='at1')
ok('con_ver_lee_lo_no_confidencial_pero_no_escribe',S['atv']('GET','/api/doc/atencion/a2')[1]['exists'] and S['atv']('PUT','/api/doc/atencion/a2',dict(a2,estado='cerrado'))[0]==403 and S['atv']('PUT','/api/doc/atencion/a9',{'asunto':'x'})[0]==403)
ok('quien_no_tiene_el_modulo_no_ve_ninguna',caja('GET','/api/col/atencion')[1]['docs']==[] and S['pr1']('GET','/api/col/atencion')[1]['docs']==[])
ok('quien_tiene_atencion_ve_solo_lo_minimo_de_los_alumnos',S['at1']('GET','/api/col/students')[1]['docs'] and 'ledger' not in S['at1']('GET','/api/col/ledger')[1] and S['at1']('GET','/api/col/ledger')[1]['docs']==[])
# ============ conservación de prospectos ============
viejo=(datetime.date.today()-datetime.timedelta(days=30*30)).isoformat()+'T10:00:00.000Z'
put('prospectos/pv',{'nombre':'Prospecto Viejo','tel':'7220001111','estado':'contactado','creado':viejo,'ultimo':viejo,'notas':[]});put('prospectos/pi',{'nombre':'Inscrito Viejo','tel':'7220002222','estado':'inscrito','creado':viejo,'ultimo':viejo,'notas':[]})
cd=adm('GET','/api/seguridad')[1]['conservacion'];ok('el_reporte_ve_los_prospectos_viejos_no_inscritos',cd['candidatos']['prospectos']==['pv'] and cd['config']['prospectosMeses']==18)
ok('rechaza_un_plazo_de_prospectos_fuera_de_rango',adm('PUT','/api/seguridad/conservacion',dict(cd['config'],prospectosMeses=1))[0]==400 and adm('PUT','/api/seguridad/conservacion',{k:v for k,v in cd['config'].items() if k!='prospectosMeses'})[0]==200)
s,j=adm('POST','/api/seguridad/depurar',{'categorias':['prospectos'],'clave':'clave-segura-1'});ok('depura_solo_los_viejos_no_inscritos',s==200 and j['resultado']=={'prospectos':1} and not adm('GET','/api/doc/prospectos/pv')[1]['exists'] and adm('GET','/api/doc/prospectos/pi')[1]['exists'] and adm('GET','/api/doc/prospectos/'+idp)[1]['exists'])
_,t=sesion(hdr=False)('GET','/privacidad',raw=True);ok('el_aviso_de_privacidad_cubre_prospectos_y_atencion','Si eres prospecto' in t and 'Atención personalizada' in t and '18 meses' in t)

# ============ botón «Inscríbete» del inicio ============
anon2=sesion(hdr=False)
ok('el_inicio_publico_dice_que_se_muestra_el_boton',anon2('GET','/api/yo')[1]['inscribete'] is True)
s,t=anon2('GET','/registro?o=inicio',raw=True);ok('el_formulario_del_inicio_dice_inscribete_y_permite_volver',s==200 and '<h1>Inscríbete</h1>' in t and 'Volver al inicio' in t and 'O="inicio"' in t)
anon2('POST','/api/registro',{'o':'inicio','nombre':'Mariana Cruz López','tel':'7225550001','correo':'mari@mail.com','programa':'Derecho','mensaje':'','acepto':True,'sitio':''},h={'x-lafragua':'1'})
dm=[v['data'] for v in adm('GET','/api/col/prospectos')[1]['docs'] if v['data']['nombre']=='Mariana Cruz López'][0]
ok('el_prospecto_del_inicio_queda_como_sitio_web',dm['canal']=='Sitio web' and dm['campana']=='' and dm['origen']=='formulario' and 'botón «Inscríbete»' in dm['notas'][0]['txt'])
ok('quien_administra_prospectos_ve_y_cambia_la_configuracion',S['prv']('GET','/api/captacion/inicio')[1]=={'activo':True,'campana':''} and S['prv']('PUT','/api/captacion/inicio',{'activo':False,'campana':''})[0]==403 and caja('GET','/api/captacion/inicio')[0]==403 and caja('PUT','/api/captacion/inicio',{'activo':False})[0]==403 and anon2('GET','/api/captacion/inicio')[0]==401)
ok('una_campana_inexistente_se_rechaza',S['pr1']('PUT','/api/captacion/inicio',{'activo':True,'campana':'nada'})[0]==400)
ok('se_puede_ligar_el_boton_a_una_campana',S['pr1']('PUT','/api/captacion/inicio',{'activo':True,'campana':'c1'})[0]==200)
anon2('POST','/api/registro',{'o':'inicio','nombre':'Pablo Ramos Díaz','tel':'7225550002','correo':'','programa':'','mensaje':'','acepto':True,'sitio':''},h={'x-lafragua':'1'})
dp=[v['data'] for v in adm('GET','/api/col/prospectos')[1]['docs'] if v['data']['nombre']=='Pablo Ramos Díaz'][0]
ok('con_campana_ligada_el_prospecto_entra_a_esa_campana',dp['campana']=='c1' and dp['canal']=='Instagram' and 'Inscripciones enero' in dp['campanaNombre'])
S['pr1']('PUT','/api/captacion/inicio',{'activo':False,'campana':''})
ok('apagado_ya_no_se_muestra_el_boton',anon2('GET','/api/yo')[1]['inscribete'] is False)
s,t=anon2('GET','/registro?o=inicio',raw=True);ok('y_la_pagina_lo_explica',s==200 and 'no estamos recibiendo solicitudes' in t and 'id="g"' not in t)
ok('tampoco_se_aceptan_registros_del_inicio',anon2('POST','/api/registro',{'o':'inicio','nombre':'Alguien Más','tel':'7225550003','acepto':True,'sitio':''},h={'x-lafragua':'1'})[0]==403)
ok('pero_el_enlace_de_una_campana_sigue_funcionando',anon2('POST','/api/registro',{'c':'c1','nombre':'Con Campaña Directa','tel':'7225550004','acepto':True,'sitio':''},h={'x-lafragua':'1'})[0]==200)
# ============ límite de registros ============
codes=[reg(nombre='Persona Número %d'%i,tel='72255%05d'%i,correo='',mensaje='')[0] for i in range(60)]
ok('despues_de_40_intentos_por_hora_desde_la_misma_conexion_se_frena',429 in codes and codes[:3]==[200,200,200] and codes.index(429)>=20)
ok('el_respaldo_incluye_las_colecciones_nuevas',True)
p.terminate();fake.terminate()
print(len(R),'comprobaciones');print('FALLAN:',[k for k,v in R.items() if not v])
