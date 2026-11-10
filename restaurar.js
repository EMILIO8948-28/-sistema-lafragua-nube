#!/usr/bin/env node
'use strict';
/* ===========================================================================
   Restaura un respaldo de la plataforma (el .zip, o el .zip.cif si salió cifrado).
   Uso:  node restaurar.js RESPALDO [--clave "contraseña de respaldos"] [--datos /ruta/de/datos] [--si]
   Detén el servicio antes de restaurar. Lo que había antes se conserva con el sufijo «.antes-FECHA».
   =========================================================================== */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const R = require('./respaldos.js');
const { DatabaseSync } = require('node:sqlite');
const args = process.argv.slice(2), pos = [], op = {};
for (let i = 0; i < args.length; i++) { if (args[i].startsWith('--')) { const k = args[i].slice(2); if (k === 'si') op.si = true; else op[k] = args[++i]; } else pos.push(args[i]); }
const origen = pos[0], datos = path.resolve(op.datos || process.env.DATA_DIR || path.join(__dirname, 'datos'));
const sal = (m, c) => { console.error(m); process.exit(c || 1); };
if (!origen || !fs.existsSync(origen)) sal('Indica el archivo de respaldo. Ejemplo: node restaurar.js respaldo-2026-11-10.zip --datos /data');
(async () => {
  const tmp = path.join(datos, 'tmp-restaurar'); fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp, { recursive: true });
  let zip = path.resolve(origen);
  if (/\.cif$/i.test(zip)) { if (!op.clave) sal('Este respaldo está cifrado: agrega --clave "la contraseña de respaldos".'); const d = path.join(tmp, 'descifrado.zip'); console.log('Descifrando…'); await R.descifraArchivo(zip, d, op.clave); zip = d; }
  console.log('Verificando que el respaldo esté completo y sano…');
  const v = R.verificaZip(zip, DatabaseSync, tmp);
  if (!v.ok) sal('El respaldo NO es válido y no se restauró:\n - ' + v.errores.join('\n - '));
  console.log('Respaldo sano: ' + v.filas + ' registros, ' + v.archivos + ' archivos.');
  if (fs.existsSync(path.join(datos, 'lafragua.db')) && !op.si) sal('Ya hay una base de datos en ' + datos + '. Detén el servicio y vuelve a ejecutar con --si para reemplazarla (la actual se conserva con el sufijo .antes-FECHA).');
  const marca = new Date().toISOString().replace(/[:.]/g, '-'), z = R.leeZip(zip);
  try {
    for (const f of ['lafragua.db', 'lafragua.db-wal', 'lafragua.db-shm']) { const p = path.join(datos, f); if (fs.existsSync(p)) fs.renameSync(p, p + '.antes-' + marca); }
    fs.mkdirSync(path.join(datos, 'archivos'), { recursive: true });
    R.extraeEntrada(z, z.entradas.find(e => e.nombre === 'lafragua.db'), path.join(datos, 'lafragua.db'));
    let n = 0; for (const e of z.entradas) { const m = /^archivos\/([0-9a-f]{32})-/.exec(e.nombre); if (m) { R.extraeEntrada(z, e, path.join(datos, 'archivos', m[1])); n++; } }
    console.log('Listo: se restauraron la base de datos y ' + n + ' archivos en ' + datos + '.');
    console.log('Notas: las contraseñas iniciales de alumnos que se guardaban cifradas ya no se podrán ver (se pueden restablecer), y deberás volver a escribir las llaves de respaldos (almacenamiento y correo) en «Respaldos y seguridad».');
  } finally { z.cierra(); fs.rmSync(tmp, { recursive: true, force: true }); }
})().catch(e => sal('No se pudo restaurar: ' + e.message));
