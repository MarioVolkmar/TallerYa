# Skills `mecanico` y `agregar-moto` (19-nov-2026)

## Qué quedó hecho
- **`.claude/skills/mecanico/`**: `SKILL.md` (reglas fijas: primero entender el conjunto, verificar la pieza en línea, se cambia el empaque y no el tapón, regla de la primera palabra, nombres de Colombia, nada sin fuente; tabla de fuentes con su orden y cómo citarlas en cada archivo; procedimientos; límites y cuándo mandar al taller) + `anexo-diagnostico.md` (forma de una rama, criterio para ordenar causas, urgencias, lista de control, todo alineado con `garaje/diagnostico.py` y el campo `diagnostico` de `fallas.py`), `anexo-revision.md` (lista de 6 puntos y formato de salida G/A para usarla como revisora) y `anexo-terminologia.md` (tabla de términos y unidades).
- **`.claude/skills/agregar-moto/`**: `SKILL.md` (7 pasos con skill, meta de tiempo y si son opcionales; tope al doble; qué hacer si falta manual, catálogo, ficha o fotos), `anexo-despiece.md` (paso 4 completo, que no estaba escrito: dónde está el catálogo de cada marca, cómo reconocer el formato, el mapa, el enlace pieza ↔ tarea con `REGLAS_GLOBALES`, `REPRESENTATIVAS` y `tarea_al_sello`, cómo importar, traducir, verificar y lo que falta para producción) y **`auditar.py`** (modo auditoría; solo lee).
- Respaldo en `C:\Users\volkm\.claude\skills_respaldo\tallerya\` y filas nuevas en `CATALOGO.md`.
- Sin código nuevo en la app (el script vive en la skill), así que no hizo falta correr pruebas. Sin commit.

## Auditoría de las 33 líneas (`auditar.py`, de la que más le falta a la que menos)
Int. = tareas exactas/total (`~` = alguna aproximada) · Fallas = «del modelo»/total · Trad. = % con nombre en español · Tareas = tareas del plan con pieza / que aplican · 3D: GLB realista, rasgos propios o familia genérica · Puntos de 0 a 7.

| Línea | Int. | Fallas | Desp. (n · lám · partes) | Trad. · Tareas | Mapa | Lám. | 3D | Puntos |
|---|---|---|---|---|---|---|---|---|
| Honda Wave 110S | 7/7 | 0/3 | — | — | sí | — | rasgos | 3 |
| Suzuki Best 125 | 4/5 ~ | 0/3 | 1 · 15 · 236 | 100% · 11/14 | sí | — | rasgos | 4 |
| AKT Dynamic Pro 125 | 5/5 | 0/3 | 1 · 12 · 178 | 100% · 12/14 | sí | — | rasgos | 4.5 |
| AKT TT 125 DS | 6/6 | 0/3 | 1 · 16 · 255 | 100% · 14/14 | sí | — | fam | 4.5 |
| Hero Eco Deluxe 100 | 8/9 ~ | 0/3 | 1 · 15 · 264 | 100% · 12/13 | sí | — | rasgos | 4.5 |
| Hero Hunk 125R | 10/10 | 0/3 | 1 · 17 · 305 | 100% · 11/14 | sí | — | rasgos | 4.5 |
| Hero Hunk 150 | 0/10 ~ | 0/3 | 1 · 20 · 384 | 100% · 14/14 | sí | — | rasgos | 4.5 |
| Suzuki GN 125 | 0/6 ~ | 1/3 | 1 · 14 · 288 | 100% · 10/14 | sí | — | rasgos | 4.5 |
| Suzuki Gixxer 150 | 8/16 ~ | 0/3 | 2 · 51 · 912 | 100% · 14/14 | sí | — | rasgos | 4.5 |
| TVS Raider 125 | 8/9 ~ | 0/3 | 1 · 16 · 379 | 100% · 14/14 | sí | — | rasgos | 4.5 |
| Yamaha FZ 25 | 5/6 ~ | 0/3 | 1 · 18 · 455 | 100% · 14/14 | sí | — | rasgos | 4.5 |
| Yamaha XTZ 125 | 5/6 ~ | 1/5 | 1 · 17 · 413 | 100% · 14/14 | sí | — | fam | 4.5 |
| AKT CR4 125 | 4/4 | 0/3 | 1 · 15 · 225 | 100% · 14/14 | sí | — | rasgos | 5 |
| Auteco Bajaj Boxer CT 100 | 0/5 ~ | 0/4 | 1 · 17 · 534 | 100% · 12/13 | sí | 2 | rasgos | 5 |
| Auteco Bajaj Boxer CT 125 | 9/9 | 0/3 | 1 · 18 · 268 | 100% · 13/13 | sí | — | rasgos | 5 |
| Auteco Bajaj Discover 125 | 7/8 ~ | 2/4 | 1 · 18 · 326 | 100% · 14/14 | sí | — | rasgos | 5 |
| Auteco Bajaj Pulsar NS 200 | 0/7 ~ | 4/4 | 1 · 21 · 395 | 100% · 15/15 | sí | — | rasgos | 5 |
| Auteco Bajaj Pulsar RS 200 | 7/8 ~ | 2/6 | 1 · 21 · 414 | 100% · 15/15 | sí | — | rasgos | 5 |
| Honda Dio 110 | 8/8 | 0/4 | 1 · 15 · 382 | 100% · 13/13 | sí | — | rasgos | 5 |
| Honda XR 150L | 8/8 | 3/6 | 1 · 17 · 398 | 100% · 14/14 | sí | — | fam | 5 |
| KTM Duke 200 | 0/9 ~ | 2/6 | 1 · 20 · 571 | 100% · 15/15 | sí | — | rasgos | 5 |
| KTM RC 200 | 0/9 ~ | 2/6 | 1 · 20 · 469 | 100% · 15/15 | sí | — | rasgos | 5 |
| Suzuki DR 150 | 8/8 | 0/4 | 1 · 24 · 504 | 100% · 14/14 | sí | — | rasgos | 5 |
| TVS Apache RTR 160 | 0/4 ~ | 0/3 | 1 · 15 · 450 | 100% · 14/14 | sí | 1 | rasgos | 5 |
| Yamaha Aerox 155 | 8/8 | 3/6 | 1 · 24 · 460 | 100% · 15/15 | sí | — | fam | 5 |
| Yamaha FZ 2.0 | 8/8 | 0/3 | 1 · 19 · 414 | 100% · 14/14 | sí | — | rasgos | 5 |
| Yamaha XTZ 150 | 9/9 | 0/3 | 1 · 18 · 381 | 100% · 14/14 | sí | — | rasgos | 5 |
| AKT NKD 125 | 0/2 ~ | 0/3 | 1 · 15 · 263 | 100% · 13/14 | sí | 3 | rasgos | 5.5 |
| Honda XR 190L | 8/8 | 1/3 | 1 · 17 · 354 | 100% · 14/14 | sí | — | rasgos | 5.5 |
| Yamaha Crypton FI 115 | 9/9 | 0/3 | 1 · 16 · 292 | 100% · 14/14 | sí | 1 | rasgos | 5.5 |
| Yamaha MT-03 | 9/9 | 1/4 | 1 · 19 · 491 | 100% · 15/15 | sí | — | rasgos | 5.5 |
| Honda CB 125F | 6/6 | 0/3 | 1 · 17 · 428 | 100% · 14/14 | sí | 5 | rasgos | 6 |
| Yamaha NMAX 155 | 8/8 | 5/5 | 1 · 20 · 444 | 100% · 15/15 | sí | 10 | GLB | 7 |

33 líneas · puntos: ficha 1 + intervalos 1 + fallas 1 + despiece 2 + láminas 1 + 3D 1 = 7

**Qué completar primero:** Honda Wave 110S (sin despiece: el lector Honda no lee su texto rotado), Hero Hunk 150 (intervalos todos aproximados, sin manual), Suzuki Best 125, Suzuki GN 125 y TVS Apache RTR 160 / AKT NKD 125 (intervalos aproximados). En general: **casi ninguna tiene fallas «del modelo»** (solo NMAX y NS 200 completas), **solo la NMAX tiene GLB** y faltan tareas con pieza en Dynamic Pro, Hunk 125R, Best 125, GN 125 y Eco Deluxe.

## Prueba ligera de `mecanico` (sin corregir)
Revisé las fallas de la Pulsar NS 200, la ficha «PLUG, DRAIN» de `despiece_fichas.py` y dos resultados de frenos de `diagnostico.py`.
- **G1 [enlace]** NS 200, falla `mono-fuga` (amortiguador trasero que gotea): su diagnóstico apunta a `inestable` → `bambolea` («el manubrio se sacude»), que da como resultado **dirección**. Debería ser `{"s": "ruido", "donde": "huecos"}`, que lleva a «Suspensión gastada». Es la única falla con ese enlace.
- A1 [fuente] `mono-fuga` dice «ajusta la precarga»: hay que confirmar en el manual que el mono de la NS 200 la tenga ajustable.
- A2 [seguridad] `recalienta`: dice «revisa el nivel en frío»; mejor decirlo explícito: «nunca abras la tapa del radiador en caliente».
- A3 [seguridad] ficha «PLUG, DRAIN»: «saca el aceite con el motor tibio» → agregar «tibio, no caliente: el aceite quema». Lo demás cumple la regla (se cambia la arandela, no el tapón).
- A4 [nombre] `freno_pegado` y `frenos_aire`: «caliper» y «cable» → «cáliper» y «guaya» (terminología de la skill). La urgencia `parar` está bien en los dos.

## Pendiente
- G1 corregido el 19-nov-2026. Aplicar, si el usuario quiere, A1-A4; son cambios de una línea en `garaje/fallas_frecuentes/auteco_bajaj_pulsar_ns_200.json`, `despiece_fichas.py` y `diagnostico.py`.
- Probar `agregar-moto` de punta a punta con una moto nueva real (la primera de la lista de espera de `ampliar-motos.md`) y ajustar las metas de tiempo con lo medido.
- Cuando se una `moto-3d-alterna`, sumar sus GLB (`garaje/modelos_alt/`) a la columna 3D de `auditar.py`.
- Las fichas de `despiece_fichas.py` se pueden revisar en tandas con `mecanico` (son ~900 líneas): una sesión aparte.
