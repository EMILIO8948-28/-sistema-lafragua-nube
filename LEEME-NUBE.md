# Sistema escolar · Universidad Lafragua — versión en la nube

Servidor propio de la escuela publicado en internet con HTTPS. Cada persona entra con su usuario y contraseña, y los permisos de cada rol los aplica el servidor (no solo la pantalla).

## Qué hay en este paquete
- `servidor.js`: el servidor (usuarios, sesiones, permisos, base de datos SQLite, respaldos).
- `publico/`: la aplicación y sus páginas (`index.html`, `configurar.html`, `herramientas.html`).
- `Dockerfile`, `package.json`, `render.yaml`: lo que necesita Render para publicarlo.
- `desarrollo/construir_nube.py`: genera `publico/index.html` a partir de la aplicación (solo para quien haga cambios).

## Publicar en Render (una sola vez)
1. Crea una cuenta en https://render.com (puedes entrar con tu cuenta de GitHub) y activa la verificación en dos pasos.
2. En GitHub crea un repositorio **privado** nuevo, por ejemplo `sistema-lafragua-nube`, y sube **el contenido** de esta carpeta (los archivos y la carpeta `publico`, no la carpeta contenedora): botón Add file > Upload files.
3. En Render: **New > Blueprint**, elige ese repositorio y pulsa **Apply**. Render lee `render.yaml`, crea el servicio (plan Starter) y su disco de 2 GB, y lo publica.
4. Cuando termine, entra a tu servicio > **Environment** y copia el valor de **LF_SETUP_TOKEN** (se genera solo).
5. Abre `https://TU-SERVICIO.onrender.com/configurar`, escribe ese código y crea tu usuario **administrador** con una contraseña fuerte.
6. Desde ese momento ya no se puede volver a usar esa página (salvo la recuperación de abajo).

## Costos (revisa los precios vigentes en render.com/pricing)
- Servicio web de pago Starter: desde US$7 al mes.
- Disco persistente: US$0.25 por GB al mes (2 GB ≈ US$0.50).
- El plan Hobby del espacio de trabajo es gratis. Los servicios gratuitos de Render se apagan solos y no permiten disco: no sirven para este sistema.
- Dominio propio (opcional): se paga aparte a quien lo registre.

## Pasar los datos de la plataforma anterior
1. En la plataforma anterior (claude.ai), como Administrador, pulsa **Respaldo** y descarga los **datos (JSON)** y los **archivos adjuntos (ZIP)**.
2. En la nueva, entra como Administrador y abre `https://TU-SERVICIO.onrender.com/herramientas.html`.
3. Paso 1: sube el JSON y restaura. Paso 2: sube el ZIP (o todas sus partes).
4. Las contraseñas no se pasan: crea los usuarios en el botón **Usuarios** (Control de pagos).

## Usuarios y contraseñas
- Mínimo 8 caracteres. Cada persona puede cambiar la suya con **Mi contraseña**.
- Después de 5 intentos fallidos se bloquea el acceso 15 minutos. Las sesiones se cierran solas tras 12 horas sin uso.
- Para quitar un pago, Caja necesita la contraseña de un administrador; queda registrado en el **registro de seguridad** (`herramientas.html`).
- Si se pierde la contraseña del administrador: en Render > Environment agrega temporalmente `LF_PERMITIR_RECUPERACION` = `1`, abre `/configurar`, usa el código y crea el administrador de nuevo (reemplaza al de ese usuario). Después **borra esa variable**.

## Respaldos (muy importante)
- El servidor hace un respaldo de la base de datos cada día y conserva 14.
- Render guarda además una copia automática del disco cada 24 horas, disponible por al menos 7 días (Render > tu servicio > Disks).
- **Cada semana descarga un respaldo completo a tu computadora**: botón **Respaldo > Respaldo completo del servidor (ZIP)** o en `herramientas.html`. Guárdalo fuera del servidor (USB, nube de tu elección).
- El ZIP incluye la base de datos y todos los archivos adjuntos.

## Actualizar el sistema
Cuando te entregue una versión nueva, sube los archivos cambiados al repositorio de GitHub. Render publica solo; durante el cambio el sistema se interrumpe unos instantes (los servicios con disco no se actualizan sin pausa).

## Cosas a saber
- Es **un solo servidor** (no se debe aumentar a varias copias): para ~300 alumnos sobra.
- Los QR de recibos, constancias y credenciales llevan la dirección de este sistema. Si después pones dominio propio, los QR nuevos usarán esa dirección; los ya impresos conservan la anterior (la dirección de Render seguirá funcionando).
- Los PDF y el Excel necesitan que el navegador cargue sus librerías de internet la primera vez.


## Dirección de los códigos QR (opcional)
Los recibos, constancias y credenciales llevan un código QR que abre la página pública `/verificar` de este sistema. Por defecto usa la dirección desde la que se usa el sistema. Si quieres fijar una dirección (por ejemplo, tu dominio propio), agrega en Render > Environment la variable `LF_URL_PUBLICA` con la dirección completa, por ejemplo `https://sistema.tuescuela.edu.mx` (sin diagonal final).
