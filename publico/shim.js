/* Conexión de la aplicación con el servidor en la nube (reemplaza lo que antes daba claude.ai) */
(function(){
  "use strict";
  /* Los QR impresos con la dirección del sistema (#c., #v., #a.) abren la verificación pública, sin iniciar sesión */
  if(/^#[vcabj]\.[A-Za-z0-9_~-]+\.[A-Za-z0-9_~.-]+$/.test(location.hash||"")&&location.pathname!=="/verificar"){location.replace("/verificar"+location.hash)}
  var CAB={"x-lafragua":"1"},YO=null,CONSULTA=false;
  function aviso401(){if(window.__lf401)return;window.__lf401=1;alert("Tu sesión terminó. Vuelve a iniciar sesión.");location.reload()}
  function api(met,ruta,cuerpo,extra,reint){
    var h=Object.assign({},CAB,extra||{}),o={method:met,headers:h,cache:"no-store",credentials:"same-origin"};
    if(window.LF_AUTORIZA&&!/^borrados/.test(ruta))h["x-autoriza"]=window.LF_AUTORIZA;
    if(cuerpo!==undefined){if(cuerpo instanceof Blob||cuerpo instanceof ArrayBuffer||ArrayBuffer.isView(cuerpo))o.body=cuerpo;else{o.body=JSON.stringify(cuerpo);h["Content-Type"]="application/json"}}
    return fetch("/api/"+ruta,o).then(function(r){return r.json().catch(function(){return {}}).then(function(j){if(!r.ok){
      /* Borrar o quitar información necesita la autorización del encargado: se pide y se reintenta */
      if(r.status===403&&j.requiereAutorizacion&&!reint&&typeof window.pideAutorizacion==="function"){return window.pideAutorizacion(j).then(function(id){window.LF_AUTORIZA=id;return api(met,ruta,cuerpo,extra,true)})}
      if(r.status===401&&YO&&YO.usuario)aviso401();var e=new Error(j.error||("Error "+r.status));e.code=String(r.status);throw e}return j})});
  }
  function cargaYo(){if(!YO)YO=fetch("/api/yo",{credentials:"same-origin",cache:"no-store"}).then(function(r){return r.json()}).then(function(j){
    window.LF_NUBE=true;window.LF_URLP=String(j.urlPublica||"");window.LF_ME=j.usuario||null;window.LF_USERS=j.usuarios||[];window.LF_SETUP=!!j.setup;window.LF_INS=!!j.inscribete;
    if(j.setup&&!/configurar/.test(location.pathname)){location.replace("/configurar.html")}
    return j}).catch(function(){window.LF_ME=null;window.LF_USERS=[];return {}});return YO}
  var yoLista=cargaYo();window.LF_LISTO=yoLista;
  /* Dirección que llevan los códigos QR: la de la plataforma donde está alojada (o la que se fije con LF_URL_PUBLICA) */
  Object.defineProperty(window,"LF_APPURL",{configurable:true,get:function(){return String(window.LF_URLP||location.origin).replace(/\/+$/,"")+"/verificar"}});
  var escuchas=[],tiempos={};
  function vacioCol(){return {docs:[]}}
  function snapDoc(id,r){return {id:id,exists:!!r.exists,data:function(){return r.data?JSON.parse(JSON.stringify(r.data)):undefined}}}
  function carga(L){
    if(L.off)return;
    yoLista.then(function(){
      if(L.off)return;
      if(!window.LF_ME||window.LF_ME.forzar)return;   /* sin sesión (o con cambio de contraseña pendiente) no se entrega nada: así la aplicación nunca cree que un registro "no existe" y escriba valores por defecto */
      if(L.tipo==="col"){
        api("GET","col/"+encodeURIComponent(L.col)).then(function(r){if(L.off)return;L.cb({docs:r.docs.map(function(d){return {id:d.id,exists:true,data:function(){return JSON.parse(JSON.stringify(d.data))}}})})}).catch(function(e){if(L.err)L.err(e)});
      }else{
        api("GET","doc/"+encodeURIComponent(L.col)+"/"+encodeURIComponent(L.id)).then(function(r){if(L.off)return;L.cb(snapDoc(L.id,r))}).catch(function(e){if(L.err)L.err(e)});
      }
    });
  }
  function refresca(col,id){
    var k=col+"/"+id;clearTimeout(tiempos[k]);
    tiempos[k]=setTimeout(function(){escuchas=escuchas.filter(function(L){return !L.off});escuchas.forEach(function(L){if(L.col===col&&(L.tipo==="col"||L.id===id))carga(L)})},60);
  }
  yoLista.then(function(){
    if(!window.LF_ME)return;
    try{var es=new EventSource("/api/eventos"),abierto=false;
      es.onmessage=function(e){try{var m=JSON.parse(e.data);if(m.c==="_borrados"){if(window.LF_BORRADOS)window.LF_BORRADOS(m.id);return}refresca(m.c,m.id)}catch(x){}};
      es.onopen=function(){/* al abrir el canal se vuelve a leer todo lo que pudo cambiar mientras se abría (salvo lo pesado y casi fijo) */if(abierto)escuchas.forEach(carga);else escuchas.forEach(function(L){if(["catalogo","contenidos","fotos"].indexOf(L.col)<0)carga(L)});abierto=true};
    }catch(e){}
  });
  function docUsuarios(){
    function mapa(u){return {u:u.u,name:u.name,rol:u.rol,doc:u.doc||"",modulos:u.modulos||null,perm:u.perm||null,salt:"",hash:"",it:0}}
    var d={users:(window.LF_USERS||[]).map(mapa)};
    return {get:function(){return yoLista.then(function(){return snapDoc("users",{exists:true,data:{users:window.LF_USERS?(window.LF_USERS.map(mapa)):[]}})})},
      set:function(){return Promise.reject(new Error("Los usuarios se administran desde el servidor."))},
      delete:function(){return Promise.reject(new Error("Los usuarios se administran desde el servidor."))},
      update:function(){return Promise.reject(new Error("Los usuarios se administran desde el servidor."))},
      onSnapshot:function(cb){var L={off:false};yoLista.then(function(){if(!L.off)cb(snapDoc("users",{exists:true,data:{users:(window.LF_USERS||[]).map(mapa)}}))});return function(){L.off=true}},
      acquire:function(){return Promise.resolve({acquired:false})}};
  }
  var DB={
    collection:function(col){return {onSnapshot:function(cb,err){var L={tipo:"col",col:col,cb:cb,err:err};escuchas.push(L);carga(L);return function(){L.off=true}}}},
    doc:function(ruta){
      if(ruta==="config/users")return docUsuarios();
      var p=String(ruta).split("/"),col=p[0],id=p[1];
      var base="doc/"+encodeURIComponent(col)+"/"+encodeURIComponent(id);
      return {
        get:function(){return yoLista.then(function(){return window.LF_ME&&!window.LF_ME.forzar?api("GET",base):{exists:false,data:null}}).then(function(r){return snapDoc(id,r)})},
        set:function(obj){return api("PUT",base,obj).then(function(){refresca(col,id)})},
        update:function(obj){return api("PATCH",base,obj).then(function(){refresca(col,id)})},
        delete:function(){return api("DELETE",base).then(function(){refresca(col,id)})},
        onSnapshot:function(cb,err){var L={tipo:"doc",col:col,id:id,cb:cb,err:err};escuchas.push(L);carga(L);return function(){L.off=true}},
        acquire:function(o){return api("POST","lock/"+encodeURIComponent(col)+"/"+encodeURIComponent(id),o)}
      };
    }
  };
  var USER={
    isOwner:function(){return yoLista.then(function(){return false})},
    canEdit:function(){return yoLista.then(function(){return true})},
    can:function(){return yoLista.then(function(){return true})},
    id:function(){return yoLista.then(function(){return window.LF_ME?window.LF_ME.u:""})},
    me:function(){return yoLista.then(function(){return {name:window.LF_ME?window.LF_ME.name:""}})},
    profiles:function(ids){var o={};(ids||[]).forEach(function(i){o[i]={name:""}});return Promise.resolve(o)}
  };
  var ASSETS={
    upload:function(f,o){var h={"x-nombre":encodeURIComponent(f.name||"archivo"),"Content-Type":f.type||"application/octet-stream"};if(o&&o.privado)h["x-privado"]="1";if(o&&o.categoria)h["x-categoria"]=String(o.categoria);return api("POST","archivo",f,h)},
    delete:function(id){return api("DELETE","archivo/"+id)}
  };
  var DL={
    save:function(o){
      var d=o.data,b=d instanceof Blob?d:new Blob([d],{type:/\.json$/i.test(o.filename)?"application/json":"application/octet-stream"});
      var u=URL.createObjectURL(b),a=document.createElement("a");a.href=u;a.download=o.filename;document.body.appendChild(a);a.click();
      setTimeout(function(){URL.revokeObjectURL(u);a.remove()},1500);return Promise.resolve();
    }
  };
  window.claude={use:function(n){return Promise.resolve(n==="db"?DB:n==="user"?USER:n==="assets"?ASSETS:n==="downloads"?DL:null)}};
})();
