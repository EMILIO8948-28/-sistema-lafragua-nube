#!/usr/bin/env python3
"""Genera publico/index.html (versión nube) a partir de la aplicación (colegiaturas.html).
Uso: python3 construir_nube.py ruta/a/colegiaturas.html ruta/a/lafragua-nube/publico/index.html"""
import re,sys
origen,destino=sys.argv[1],sys.argv[2]
h=open(origen,encoding='utf-8').read()
def rep(old,new,n=1):
    global h
    assert h.count(old)==n,(old[:80],h.count(old)); h=h.replace(old,new)
# 1) librerías: locales y, si faltan, internet
cdn=re.findall(r'<script src="(https://cdnjs[^"]+)"></script>',h)
assert len(cdn)>=3,cdn
for u in cdn: h=h.replace('<script src="'+u+'"></script>','',1)
cargador='''<script src="/config-local.js"></script>
<script src="/shim.js"></script>
<script>
(function(){
  var L=[["lib/jspdf.umd.min.js","https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"],["lib/pdf-lib.min.js","https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js"],["lib/xlsx.full.min.js","https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"]];
  L.forEach(function(x){var s=document.createElement("script");s.src=x[0];s.onerror=function(){var t=document.createElement("script");t.src=x[1];document.head.appendChild(t)};document.head.appendChild(s)});
})();
</script>
'''
rep('<script>\n',cargador+'<script>\n')
rep('s.src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js";\n    s.onload=function(){res(window.JSZip||null)};s.onerror=function(){res(null)};','s.src="lib/jszip.min.js";\n    s.onload=function(){res(window.JSZip||null)};s.onerror=function(){var t=document.createElement("script");t.src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js";t.onload=function(){res(window.JSZip||null)};t.onerror=function(){res(null)};document.head.appendChild(t)};')
h=re.sub(r'var APPURL="https://claude\.ai/artifact/[^"]+"','var APPURL=(window.LOCAL_APPURL||(location.origin+"/"))',h,count=1)
assert 'LOCAL_APPURL' in h
# 2) la sesión viene del servidor
rep('if(!APP){var su="";try{su=sessionStorage.getItem(KEY+"-ses")||""}catch(e){}var x=su&&USERS.find(function(y){return y.u===su});if(x)APP={u:x.u,name:x.name,rol:x.rol,doc:x.doc||"",modulos:x.modulos||null,perm:x.perm||null}}','if(!APP){if(window.LF_ME)APP={u:LF_ME.u,name:LF_ME.name,rol:LF_ME.rol,doc:LF_ME.doc||"",modulos:LF_ME.modulos||null,perm:LF_ME.perm||null}}')
# 3) botón y ventana de "Mi contraseña" y botón del respaldo del servidor
rep('<button id="bOut"','<button id="bPw">Mi contraseña</button> <button id="bOut"')
rep('<dialog id="dRc"','''<dialog id="dPw" style="width:min(440px,96vw)">
  <h2>Cambiar mi contraseña</h2>
  <div class="row">
    <label class="full">Contraseña actual<input id="pwA" type="password" autocomplete="current-password"></label>
    <label class="full">Contraseña nueva (mínimo 8 caracteres)<input id="pwN" type="password" autocomplete="new-password"></label>
    <label class="full">Repite la contraseña nueva<input id="pwR" type="password" autocomplete="new-password"></label>
  </div>
  <p class="hint" id="pwMsg" style="min-height:1.4em"></p>
  <div class="bar" style="justify-content:flex-end;margin:0"><button id="pwCan">Cerrar</button><button class="p" id="pwOk">Cambiar contraseña</button></div>
</dialog>

<dialog id="dRc"''')
rep('<button id="bkZip">Descargar archivos adjuntos (ZIP)</button>','<button id="bkZip">Descargar archivos adjuntos (ZIP)</button><button class="p" id="bkSrv">Respaldo completo del servidor (ZIP)</button>')
# 4) ajustes del navegador y de usuarios en el servidor
rep('</body>','<script src="/nube.js"></script>\n</body>')
open(destino,'w',encoding='utf-8').write(h)
print('listo:',destino,len(h),'caracteres')
