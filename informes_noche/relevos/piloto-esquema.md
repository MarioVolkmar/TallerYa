# Relevo: esquemas pedagógicos (después de adoptar el v2 y acelerar la skill)

Escrito el 16-nov-2026 por la creadora de los esquemas, antes de que Auxiliares limpie la sesión. `M` = `informes_noche/piloto-esquema/motor`. Todo está sin commit.

## Hecho
- **Adopción del v2** (fase `adopcion_v2`, 33 min). El detalle está en `informes_noche/piloto-esquema/cambios.md`, arriba.
  - Motor único: `M/esquema.js` y `esquema.css`. Un JSON con `v2` usa el modelo v2 y uno sin `v2` sigue con el viejo: las firmas v1 salen idénticas. Respaldos en `capturas-rediseno/respaldo-v2/`.
  - Las fig. 26, 22 y 12 ya son v2: `datos/nmax-fig{26,22,12}.json`. Las viejas quedan como `…-v1.json`, y la fig. 26 tiene además `bomba-freno-v1.html`.
  - La fig. 22 y la fig. 12 se arman con `capturas-rediseno/armar_v2.py <lamina>`, a partir de `…-v1.json` + `v2-textos-<lamina>.json`. Para cambiar un texto se edita ese JSON de textos y se vuelve a correr el script. `armar26v2.py` está retirado: la fig. 26 se edita directo.
  - Ajustes a-e del usuario hechos: píldoras chicas, enlaces en línea, acciones compactas, hoja inferior en el celular y certeza por dato con `certezaDe`.
  - Validador OK en las 3, sin errores de consola. Archivos únicos `M/prueba-nmax-fig{22,12,26}.html` probados con file://. Capturas en `capturas-rediseno/fig26-{general,ficha}-{1280,390}.jpg`.
- **Skill más rápida** (fase `mejora_skill`). Las ganancias medidas están en `M/mejoras.md`, arriba.
  - Herramientas nuevas: `M/esqueleto_v2.py`, `M/plantillas_ficha.py` y `M/autocontrol.py`, más `revisar_estructura_v2` en `mas_controles.py` y el aviso del 125 % en `metricas.py fin`.
  - Actualizados `SKILL.md`, `anexo-formato.md` («Modelo v2») y `anexo-esqueleto.md`, que ahora es el subagente de borradores en paralelo.

## Pendiente
- **ux-piloto** ya tiene el medidor v2: `M/medir_lamina.py <pagina>.html --ojo a,b,c,d,e,f`, que es el que usa `autocontrol.py`. La fig. 26 aprueba lo medible (4,72). La fig. 22 y la CVT quedan en 4,55 por el criterio 6 (ver abajo). No tocar `medir_lamina.py` ni `criterios-ux.md`.
- fig. 26: los `certezaDe` se pusieron con una regla automática a partir de su lista `certeza`.
- Revisión mecánica de la fig. 22 y la fig. 12: aprobadas con 4,8. Arreglos de la CVT hechos (ficha 18 y cierre del paso 15). En la fig. 22, `dif` se deja en «taller» hasta que el usuario decida.
- medir_lamina v2: en la CVT las piezas 14-23 salen con 0 px. Con las animaciones terminadas sí se tocan; parece que el medidor mide antes de que termine el desarme (0,9 s por paso). Avisado a ux-piloto.
- La pieza 44 de la fig. 26 tiene 6 px tocables a 360 (pendiente viejo).

## Meta nueva
15 min de reloj por lámina, sin paralelo y con la verificación incluida (`metricas.json`: `creacion_meta_min`, `meta_fases`). El plan por minuto está en `SKILL.md`. Si la fig. 8 sale bien, siguen la 24, 11, 7, 10 y 1, una por sesión limpia, con un relevo corto entre cada una.

## Siguiente: fig. 8 de la NMAX («Admisión y filtro de aire»), desde una sesión LIMPIA y solo con la skill
- Cargar la skill `hacer-lamina`; no hace falta este historial.
- Meta: **15 min de reloj**, sin paralelo, con la verificación incluida; mecánica ≥ 4,8 y UX ≥ la base del v2. `uso_plan` lo anota Auxiliares.
- Arranque: `M/esqueleto_v2.py nmax-bbe4 8 nmax-fig8 --intervalos yamaha_nmax_155 --tareas filtro-aire`. Propone 9 grupos; se revisan, porque «Amortiguador» y «Abrazadera» quedaron sueltos.
- Con el mismo comando y `--escribir` se crea el JSON. Después: `plantillas_ficha.py … --escribir` y el plan por minuto de `SKILL.md`, sin subagentes.
