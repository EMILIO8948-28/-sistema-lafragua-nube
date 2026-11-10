# Pruebas automáticas

Escritas con Python + Playwright (Chromium) contra el servidor real en una carpeta temporal. Se escribieron en Linux: las rutas `/tmp/...` y el nombre del proceso deben adaptarse en Windows (Claude Code puede hacerlo).

Antes de las pruebas: copiar el repositorio a una carpeta temporal (`/tmp/nb`), instalar `playwright` para Python (`pip install playwright` y `playwright install chromium`) y tener Node.js 22.13 o más nuevo.

- `test_nube.py` · permisos por rol, sesiones, bloqueos, respaldo ZIP y bitácora (76 comprobaciones).
- `test_nube_web.py` · configuración inicial, usuarios, roles, cambio de contraseña y respaldo desde la pantalla (35).
- `test_na.py` · nómina administrativa y estado de cuenta final (54).
- `test_rec.py` · recibos de nómina docente y administrativa (23).
- `test_dx.py` · expediente del docente y archivos confidenciales (42).
- `test_perm.py` · usuarios, módulos y privilegios: pantalla de usuarios, permisos del servidor por usuario y lo que ve cada uno (66).

- `test_alumnos.py` · portal del alumno: accesos por lotes, aislamiento de datos por registro, cambio obligatorio de contraseña y la pantalla del alumno (56).
- `test_acceso_ficha.py` · usuario y contraseña inicial del alumno en su ficha: cifrado, bitácora, permisos, restablecer y hoja de acceso (24).
- `test_portal_cred.py` · credencial digital y recibos descargables en el portal del alumno (19).
- `test_constancias.py` · constancia simple y con promedio, QR hacia la plataforma y verificación pública sin inicio de sesión, con verificación manual (47).
- `test_borrados.py` · borrados con autorización del encargado (contraseña o aprobación), notificaciones, vencimiento y eliminación de constancias (63). Tarda unos 40 segundos por una espera que comprueba que cada autorización sirve para una sola acción.
- `test_planeacion.py` · planeación y puntos de evaluación del docente, privacidad entre docentes, calendario escolar y que no haya identificadores repetidos (33).
- `test_revision.py` · resumen del plan de estudios, quitar materias (una, varias y con autorización) y revisión de planeaciones por el encargado (38).
- `test_carga_json.py` · carga del plan y los contenidos desde el archivo .json (con y sin materias ya cargadas) (26). Usa el archivo de Pedagogía de `/mnt/user-data/uploads` o de `outputs`; adáptalo a tu ruta.
- `test_precarga.py` · precarga automática del plan de Pedagogía al arrancar: una sola vez, sin pisar lo existente (13).
- `test_historial.py` · calificaciones anteriores por alumno y por CSV, sin cobros de extraordinario, periodos y permisos (32).
- `test_boleta_qr.py` · QR de la boleta: verificación pública, PDF, lectura con cámara (necesita `opencv-python` y `numpy`) y verificación dentro de la aplicación (28).
- `test_solicitudes.py` · solicitudes del alumno (justificante, boleta, constancia), atención de Control escolar, notificaciones del alumno, QR del justificante y privacidad (59).
- `test_fusion.py` · fusión de grupos de dos licenciaturas: calendario, docente, calificaciones por plan, portal y Control escolar (30).
- `test_credencial.py` · credencial nueva: PDF (tarjeta y hoja carta), foto circular, nombre largo, vista previa y portal (15). Usa `/tmp/cred_replay.py` para el registro de dibujo; adáptalo a tu ruta.
- `test_plan_nuevo.py` · crear planes nuevos (diálogo y archivos), que aparezcan en todos los módulos y sesiones, plan predeterminado que no llegaba y permisos (31).
- `test_resguardos.py` · títulos en resguardo: registro, edición, entrega, acuses en PDF, filtros, CSV, permisos y autorización para quitar (47).
- `test_resguardos_zip.py` · carga de escaneos de resguardo desde un ZIP: asignación por matrícula, nombre y palabra, reemplazo, registros nuevos y permisos (33).
- `test_cert_resguardo.py` · certificados en resguardo de Acuerdo 286: registro, certificado ya cargado, entrega, acuses, ZIP, permisos del módulo y autorización para quitar (37).
- `test_cobranza.py` · avisos de adeudo y bloqueo por falta de pago: cálculo de colegiaturas vencidas, tres avisos, abonos, bloqueo, mensaje al iniciar sesión, desbloqueo, pausas, exenciones y permisos (56). Usa un reloj simulado (`LF_RELOJ_ARCHIVO`).
- `test_renombrar_plan.py` · cambio de nombre de un plan: actualiza todos los registros, mueve el catálogo, no reaparece el nombre anterior, alias en importaciones y precarga, volver al nombre original y permisos (31).
- `test_tarifas.py` · tarifa por hora de los docentes: general, por plan, por docente y por asignatura en un mes, nóminas pagadas, recibo, renombrar un plan y permisos (29).
- `test_finanzas.py` · módulo Finanzas: tarjeta del panel, secciones (pagos, verificación, nómina docente y administrativa), acceso según permisos, título y nombres en Usuarios y permisos (25).
- `test_cuatrimestres.py` · cuatrimestres de cada plan: cambio desde Plan de estudios y desde Costos y planes, medios cuatrimestres, mínimo por grupos y asignaturas, aviso del efecto, recálculo de cobros y permisos (31).
- `test_almacenamiento.py` · aviso de disco temporal y recordatorio de respaldo (18).
- `test_actualizacion.py` · reiniciar el servidor con los mismos datos no borra nada (8).
- `test_respaldo_boton.py` · botón de respaldo arriba a la derecha: posición, insignia roja/amarilla, tiempos, celular y permisos (23).
- `test_iconos.py` · iconos de las tarjetas del panel: uno por opción, distintos, decorativos, modo oscuro, celular y otros roles (11).
- `test_notificaciones.py` · campana de notificaciones: administrador, personal por permiso, docente (calificaciones y planeaciones), alumno (solicitudes y avisos), leídas, navegación y celular (39).
- `test_doctorado.py` · carga del Doctorado: duración de 5 cuatrimestres, aviso al cargar, precarga del servidor que no pisa duraciones, cobros sin costo (13).
- `test_contratos.py` · contratos de docentes por honorarios: dialogo, meses de servicio, folios, texto del PDF, firma, cancelación, datos fiscales y permisos (44).
- `test_firma_contrato.py` · firma electrónica en pantalla táctil, fotos de la INE, PDF firmado con anexo, bloqueo y permisos (36).
- `test_foto_docente.py` · foto del rostro del docente: cámara, expediente, Mi perfil, seguridad del servicio y credencial de docentes (34).
- `test_ficha_firma.py` · ficha de inscripción con firma electrónica: firmas del alumno o tutor y de Control escolar, PDF firmado, lista, campana y permisos (34).

Regla: ninguna actualización se sube a producción sin que estas pruebas pasen (salvo que el cambio no toque lo que prueban).
