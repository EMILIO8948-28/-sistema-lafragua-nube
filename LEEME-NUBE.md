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
4. Las contraseñas no se pasan: crea los usuarios en el botón **Usuarios** (Finanzas).

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

## Respaldos automáticos con copia fuera del servidor
Entra como Administrador a **Respaldos y seguridad** (tarjeta del panel o botón «Respaldo» de arriba a la derecha):
1. **Activa el respaldo automático** y elige la hora (por ejemplo, 2).
2. **Almacenamiento externo (recomendado):** crea una cuenta gratuita en Backblaze B2 o Cloudflare R2, un «bucket» **privado** y una llave de aplicación con permiso de escritura solo en ese bucket. Escribe la dirección (endpoint), la región, el bucket y las dos llaves, y pulsa **Guardar y probar la conexión**.
3. **Correo (opcional):** con Gmail, activa la verificación en dos pasos y crea una «contraseña de aplicación»; servidor `smtp.gmail.com`, puerto `587`. Pulsa **Guardar y enviar un correo de prueba**.
4. **Cifrado:** activa «Cifrar las copias que salen del servidor» y escribe una contraseña de respaldos (mínimo 10 caracteres). **Guárdala fuera de la plataforma**: sin ella no se abren las copias cifradas.
5. Pulsa **Respaldar ahora** y comprueba que las tres tarjetas queden en verde, y **Probar restauración**.
Para **restaurar**: en Render, Shell del servicio, con el servicio suspendido: `node restaurar.js /data/respaldo-AAAA-MM-DD-….zip --datos /data --si` (agrega `--clave "tu contraseña"` si es un `.zip.cif`). Vuelve a escribir las llaves del almacenamiento y del correo después de restaurar.

## Si después de actualizar faltan datos
Actualizar el sistema (subir archivos nuevos a GitHub) **no borra datos**: el servidor solo cambia de programa y vuelve a abrir la misma base de datos. Si desaparecen registros después de una actualización, casi siempre es porque la base está en un **disco temporal** y no en el disco persistente. Cómo revisarlo:
1. Entra como Administrador: si los datos están en un disco temporal, el panel principal muestra un aviso rojo («Tus datos se guardan en un disco temporal»). En el botón **Respaldo** también aparece el estado del almacenamiento y la fecha en que se creó la base de datos (si es reciente y no esperabas empezar de cero, los datos se reiniciaron).
2. En Render, tu servicio > **Disks** debe mostrar un disco llamado `datos` con la ruta `/data`, y en **Environment** debe existir `DATA_DIR` = `/data`. Si el servicio es gratuito o se creó sin disco, hay que usar el plan Starter con disco (ver «Costos»).
3. Mientras no esté resuelto, **descarga un respaldo completo antes de cada actualización** (botón Respaldo > «Respaldo completo del servidor (ZIP)»); el panel te lo recuerda si pasan más de 7 días.
4. Para recuperar: Render guarda copias del disco (Disks > Snapshots) si el disco existe; el servidor deja respaldos diarios en `/data/respaldos`; y los respaldos descargados se restauran en `herramientas.html` (al restaurar, los registros con el mismo nombre se **reemplazan** por los del respaldo y los demás se conservan; antes de restaurar el servidor hace un respaldo propio).
Para silenciar el aviso si tu disco sí es persistente pero el sistema no lo detecta, agrega la variable `LF_DISCO_OK` = `1`.

## Cosas a saber
- Es **un solo servidor** (no se debe aumentar a varias copias): para ~300 alumnos sobra.
- Los QR de recibos, constancias y credenciales llevan la dirección de este sistema. Si después pones dominio propio, los QR nuevos usarán esa dirección; los ya impresos conservan la anterior (la dirección de Render seguirá funcionando).
- Los PDF y el Excel necesitan que el navegador cargue sus librerías de internet la primera vez.


## Dirección de los códigos QR (opcional)
Los recibos, constancias y credenciales llevan un código QR que abre la página pública `/verificar` de este sistema. Por defecto usa la dirección desde la que se usa el sistema. Si quieres fijar una dirección (por ejemplo, tu dominio propio), agrega en Render > Environment la variable `LF_URL_PUBLICA` con la dirección completa, por ejemplo `https://sistema.tuescuela.edu.mx` (sin diagonal final).


## Precarga de planes de estudio (opcional)
La carpeta `precarga/` trae los planes de Pedagogía (47 asignaturas), Administración (47), Contaduría (52), Derecho (49), Arquitectura (48, con contenido propuesto pendiente de revisión académica), Maestría en Educación (12), Doctorado (16), Enfermería (54, con contenido propuesto pendiente de revisión académica) e Ingeniería Industrial (39, provisional), con sus contenidos. Al publicar esta versión, el sistema los carga solo, una única vez, si Pedagogía aún no tiene materias. Si ya tenía materias, no toca nada. Para desactivarlo, agrega en Render > Environment la variable `LF_SIN_PRECARGA` con el valor `1`.
