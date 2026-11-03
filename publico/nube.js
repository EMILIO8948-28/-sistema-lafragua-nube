/* Ajustes de la versión en la nube: inicio de sesión, usuarios y autorizaciones en el servidor */
(function(){
  "use strict";
  var H={"Content-Type":"application/json","x-lafragua":"1"};
  function llama(met,url,cuerpo){
    return fetch(url,{method:met,headers:H,credentials:"same-origin",body:cuerpo===undefined?undefined:JSON.stringify(cuerpo)}).then(function(r){return r.json().catch(function(){return {}}).then(function(j){return {ok:r.ok,status:r.status,j:j}})});
  }
  /* Inicio y cierre de sesión */
  window.entrar=async function(){
    var u=nrm($("lgU").value),p=$("lgP").value;$("lgE").textContent="";
    if(!u||!p){$("lgE").textContent="Escribe tu usuario y tu contraseña.";return}
    $("lgGo").disabled=true;
    try{var r=await llama("POST","/api/login",{u:u,clave:p});
      if(!r.ok){$("lgE").textContent=r.j.error||"No se pudo iniciar sesión.";$("lgP").value="";}
      else{location.reload();return}
    }catch(e){$("lgE").textContent="No se pudo conectar con el servidor."}
    $("lgGo").disabled=false;
  };
  $("lgGo").onclick=window.entrar;
  $("bOut").onclick=async function(){window.__lf401=1;window.LF_ME=null;try{await llama("POST","/api/logout")}catch(e){}location.reload()};
  /* Autorización de un administrador (para que Caja pueda quitar un pago) */
  window.claveAdmin=async function(pw){
    var r=await llama("POST","/api/autoriza-admin",{clave:pw,motivo:"Quitar un pago"});
    if(r.ok)return {ok:{name:r.j.nombre}};
    return {err:r.status===409?"sin":"mala",msg:r.j.error};
  };
  /* Administración de usuarios en el servidor */
  window.saveUsers=function(){return Promise.resolve()};
  function pasaUsuarios(lista){USERS=(lista||[]).map(function(x){return {u:x.u,name:x.name,rol:x.rol,doc:x.doc||"",salt:"",hash:"",it:0}});renderUs()}
  $("bUs").onclick=async function(){
    var r=await llama("GET","/api/usuarios");if(r.ok)pasaUsuarios(r.j.usuarios);
    limpiaUs();$("dUs").showModal();
  };
  $("uAdd").onclick=async function(){
    if(ROL!=="admin")return;
    var n=$("uN").value.trim(),u=nrm($("uU").value),p=$("uP").value,rol=$("uR").value;
    if(!n||!u){alert("Completa el nombre y el usuario.");return}
    if(!/^[a-z0-9._-]{3,40}$/.test(u)){alert("El usuario solo puede llevar letras sin acentos, números, punto, guion y guion bajo (3 a 40 caracteres).");return}
    if(rol==="docente"&&!$("uDoc").value){alert("Elige el docente al que pertenece este usuario.");return}
    var nuevo=!USERS.some(function(x){return x.u===u});
    if(nuevo&&p.length<8){alert("La contraseña debe tener al menos 8 caracteres.");return}
    if(p&&p.length<8){alert("La contraseña debe tener al menos 8 caracteres.");return}
    var r=await llama("POST","/api/usuarios",{u:u,name:n,rol:rol,doc:rol==="docente"?$("uDoc").value:"",clave:p||undefined});
    if(!r.ok){alert(r.j.error||"No se pudo guardar el usuario.");return}
    pasaUsuarios(r.j.usuarios);limpiaUs();
  };
  $("usL").onclick=async function(e){
    var d=e.target.dataset;
    if(d.ed!==undefined){var x=USERS[+d.ed];$("uN").value=x.name;$("uU").value=x.u;$("uU").readOnly=true;$("uR").value=x.rol;uRolUI();$("uDoc").value=x.doc||"";$("uP").value="";$("uP").focus()}
    if(d.dl!==undefined){
      var y=USERS[+d.dl];
      if(APP&&y.u===APP.u){alert("No puedes eliminar tu propio usuario.");return}
      if(!confirm("¿Eliminar a "+y.name+"?"))return;
      var r=await llama("DELETE","/api/usuarios/"+encodeURIComponent(y.u));
      if(!r.ok){alert(r.j.error||"No se pudo eliminar.");return}
      pasaUsuarios(r.j.usuarios);
    }
  };
  /* Cambiar mi contraseña */
  $("bPw").onclick=function(){$("pwA").value="";$("pwN").value="";$("pwR").value="";$("pwMsg").textContent="";$("dPw").showModal()};
  $("pwCan").onclick=function(){$("dPw").close()};
  $("pwOk").onclick=async function(){
    var a=$("pwA").value,n=$("pwN").value,r=$("pwR").value;$("pwMsg").style.color="var(--bad)";
    if(!a||!n){$("pwMsg").textContent="Completa la contraseña actual y la nueva.";return}
    if(n!==r){$("pwMsg").textContent="La confirmación no coincide con la nueva contraseña.";return}
    var x=await llama("POST","/api/cambiar-clave",{actual:a,nueva:n});
    if(!x.ok){$("pwMsg").textContent=x.j.error||"No se pudo cambiar la contraseña.";return}
    $("pwMsg").style.color="var(--ok)";$("pwMsg").textContent="Contraseña cambiada. Las demás sesiones abiertas se cerraron.";
  };
  /* Respaldo completo del servidor */
  $("bkSrv").onclick=function(){location.href="/api/respaldo/descargar"};
  (window.LF_LISTO||Promise.resolve()).then(function(){$("bPw").hidden=!window.LF_ME;if(window.LF_ME)document.body.setAttribute("data-nube","1")});
})();
