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

Regla: ninguna actualización se sube a producción sin que estas pruebas pasen (salvo que el cambio no toque lo que prueban).
