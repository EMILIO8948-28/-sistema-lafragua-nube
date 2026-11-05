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

Regla: ninguna actualización se sube a producción sin que estas pruebas pasen (salvo que el cambio no toque lo que prueban).
