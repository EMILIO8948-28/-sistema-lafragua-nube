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
    if(!window.__ticket2&&(!u||!p)){$("lgE").textContent="Escribe tu usuario y tu contraseña.";return}
    $("lgGo").disabled=true;
    try{
      if(window.__ticket2){
        var r2=await llama("POST","/api/login2fa",{ticket:window.__ticket2,codigo:$("lgC").value});
        if(r2.ok){location.reload();return}
        $("lgE").textContent=r2.j.error||"El código no es correcto.";$("lgC").value="";
        if(r2.status===401&&/caduc/i.test(r2.j.error||"")||r2.status===429){window.__ticket2=null;$("lgCW").hidden=true;$("lgP").disabled=false;$("lgP").value="";$("lgGo").textContent="Entrar"}
        $("lgGo").disabled=false;return
      }
      var r=await llama("POST","/api/login",{u:u,clave:p});
      if(r.ok&&r.j.requiere2fa){window.__ticket2=r.j.ticket;$("lgCW").hidden=false;$("lgP").disabled=true;$("lgE").textContent="Escribe el código de tu aplicación de verificación (o un código de recuperación).";$("lgGo").textContent="Verificar";$("lgC").value="";$("lgC").focus();$("lgGo").disabled=false;return}
      if(!r.ok){var le=$("lgE");le.textContent=r.j.error||"No se pudo iniciar sesión.";le.style.cssText=r.j.bloqueado?"padding:12px;border:1px solid var(--bad);border-radius:8px;background:rgba(180,40,40,.08);color:#8a1c1c;font-weight:600;line-height:1.45":"";$("lgP").value="";}
      else{location.reload();return}
    }catch(e){$("lgE").textContent="No se pudo conectar con el servidor."}
    $("lgGo").disabled=false;
  };
  $("lgGo").onclick=window.entrar;
  $("bOut").onclick=async function(){window.LF_AUTORIZA=null;window.__lf401=1;window.LF_ME=null;try{await llama("POST","/api/logout")}catch(e){}location.reload()};
  /* Autorización de un administrador (para que Caja pueda quitar un pago) */
  window.claveAdmin=async function(pw){
    var r=await llama("POST","/api/autoriza-admin",{clave:pw,motivo:"Quitar un pago"});
    if(r.ok)return {ok:{name:r.j.nombre}};
    return {err:r.status===409?"sin":"mala",msg:r.j.error};
  };
  /* Administración de usuarios en el servidor (pantalla «Usuarios y permisos») */
  window.PW_MIN=8;
  window.saveUsers=function(){return Promise.resolve()};
  function pasaUsuarios(lista){USERS=(lista||[]).map(function(x){return {u:x.u,name:x.name,rol:x.rol,doc:x.doc||"",modulos:x.modulos||null,perm:x.perm||null,alumno:x.alumno||"",forzar:!!x.forzar,temporal:!!x.temporal,salt:"",hash:"",it:0}});if(typeof renderUsr==="function"&&MOD==="usr")renderUsr();if(MOD==="esc"&&ETAB==="D")renderDoc()}
  window.usrGuardar=async function(o){
    var r=await llama("POST","/api/usuarios",{u:o.u,name:o.name,rol:o.rol,doc:o.doc||"",modulos:o.rol==="admin"?undefined:o.modulos,clave:o.clave||undefined});
    if(!r.ok)throw new Error(r.j.error||"No se pudo guardar el usuario.");
    pasaUsuarios(r.j.usuarios);
  };
  window.usrBorrar=async function(u){
    var r=await llama("DELETE","/api/usuarios/"+encodeURIComponent(u));
    if(!r.ok)throw new Error(r.j.error||"No se pudo eliminar.");
    pasaUsuarios(r.j.usuarios);
  };
  async function cargaUsuarios(){var r=await llama("GET","/api/usuarios");if(r.ok)pasaUsuarios(r.j.usuarios)}
  window.cargaUsuariosSrv=cargaUsuarios;
  /* Solicitudes de borrado (notificaciones del encargado) */
  window.borradosLista=async function(){var r=await llama("GET","/api/borrados");if(!r.ok)throw new Error((r.j&&r.j.error)||"No se pudieron leer las notificaciones.");return r.j};
  window.borradosResolver=async function(id,accion,motivo){var r=await llama("POST","/api/borrados/"+encodeURIComponent(id)+"/resolver",{accion:accion,motivo:motivo||""});if(!r.ok)throw new Error((r.j&&r.j.error)||"No se pudo guardar tu respuesta.");return r.j};
  window.borradoSolicitar=async function(id){var r=await llama("POST","/api/borrados/"+encodeURIComponent(id)+"/solicitar",{});if(!r.ok)throw new Error((r.j&&r.j.error)||"No se pudo enviar la solicitud.");return r.j};
  window.borradoClave=async function(id,clave){var r=await llama("POST","/api/borrados/"+encodeURIComponent(id)+"/clave",{clave:clave});if(!r.ok)throw new Error((r.j&&r.j.error)||"No se pudo autorizar.");return r.j};
  window.borradoEstado=async function(id){var r=await llama("GET","/api/borrados/"+encodeURIComponent(id));if(!r.ok)throw new Error((r.j&&r.j.error)||"No se pudo consultar la solicitud.");return r.j};
  window.apiAlumnos=function(items){return llama("POST","/api/usuarios/alumnos",{items:items})};
  window.apiAcceso=function(sid){return llama("GET","/api/usuarios/alumno/"+encodeURIComponent(sid))};
  /* Accesos de docentes: el servidor guarda las contraseñas cifradas */
  window.accesosDoc=async function(ids){
    if(BASEROL!=="admin"||ROL!=="admin")return;
    if(!ids.length){alert("Todos los docentes ya tienen acceso.");return}
    try{
      for(var i=0;i<ids.length;i++){
        var did=ids[i],d=DOC[did];if(!d)continue;
        var ex=usuarioDoc(did),pass=genPass(),u=ex?ex.u:userDe(d.nombre);
        var r=await llama("POST","/api/usuarios",{u:u,name:d.nombre,rol:ex?ex.rol:"docente",doc:did,clave:pass});
        if(!r.ok)throw new Error(r.j.error||"No se pudo crear el acceso.");
        pasaUsuarios(r.j.usuarios);ACCNEW.push({doc:d.nombre,u:u,p:pass});
      }
      renderDoc();renderAcc();
    }catch(e){alert((e&&e.message)||"No se pudo crear el acceso.")}
  };
  $("dcAccAll").onclick=function(){accesosDoc(Object.keys(DOC).filter(function(k){return !usuarioDoc(k)}))};
  $("bUs").onclick=async function(){await cargaUsuarios();ir("usr")};
  $("mUsr").onclick=async function(){await cargaUsuarios();ir("usr")};
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
    if(window.LF_ME&&window.LF_ME.forzar){setTimeout(function(){location.reload()},600)}
  };
  /* Cambio de contraseña obligatorio (accesos nuevos o restablecidos de alumnos) */
  (window.LF_LISTO||Promise.resolve()).then(function(){
    if(!(window.LF_ME&&window.LF_ME.forzar))return;
    $("pwA").value="";$("pwN").value="";$("pwR").value="";
    $("pwMsg").style.color="var(--ink)";$("pwMsg").textContent="Por seguridad, cambia tu contraseña inicial para continuar. Escribe la que te entregaron y elige una nueva.";
    $("pwCan").hidden=true;
    $("dPw").addEventListener("cancel",function(e){e.preventDefault()});
    var so=document.createElement("button");so.textContent="Cerrar sesión";so.id="pwOut";so.onclick=function(){$("bOut").onclick()};$("pwCan").parentNode.insertBefore(so,$("pwCan"));
    $("dPw").showModal();
  });
  /* Respaldo completo del servidor */
  $("bkSrv").onclick=function(){location.href="/api/respaldo/descargar"};
  (window.LF_LISTO||Promise.resolve()).then(function(){if($("lgIns"))$("lgIns").hidden=!window.LF_INS;$("bPw").hidden=!window.LF_ME;if(window.LF_ME)document.body.setAttribute("data-nube","1");if(typeof sxArranque==="function")sxArranque()});
})();
