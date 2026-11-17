# Prueba 3 de la skill `hacer-lamina`: Honda CB 125F, freno delantero (16-nov-2026)

Lámina `cb125f-freno` · página `motor/cb125f-freno.html` · resumen para las revisoras: `motor/revision/cb125f-freno.md`.
La GLH125SH viene con **tambor o con disco** (F-9 «front brake panel» / F-10 «front brake caliper»). Hice la **de disco (F-10)**, con la fig. 22 de la NMAX como lámina hermana. El tambor (F-9) queda para otra lámina.

## Tiempos (meta: 10 min)
| fase | real | presupuesto | |
|---|---|---|---|
| catalogo | 1 | 1 | ✓ (sin contar los ~2 min de la extracción a mano, ver abajo) |
| dibujo2d | 5 | 4 | ⚠ incluye el contenido: se hizo todo en el mismo script |
| contenido | 0 | 2 | va dentro de dibujo2d |
| validacion | 1 | 1-2 | ✓ (`--rapido` + `--previa` + chequeo rápido) |
| mediciones | 2 | 2 | ✓ |
| **creación** | **9 min** | 10 | Boxer 20 min · AKT 25 min |

- **Tokens:** el contexto pasó de 100.020 a 168.175 (**≈ 68 k**). El plan de 5 h pasó del 45 % al 48 %.
- **Mediciones completas: 1** (la meta). Código 0, sin bloqueantes, notas medibles 4,5-5,0 (promedio 4,8). Hubo una sola `--previa`.
- **Imágenes: 1** (la previa a 640 px). Ni la grilla del plano (no hay grilla de Honda) ni la captura final hicieron falta.

## ¿El extractor leyó solo el catálogo Honda?
Sí. Solo abrió ese PDF, pero **no lo entendió**: «figura F10: no encontré su tabla» (solo reconoce las cabeceras de Yamaha, Auteco/Bajaj y AKT). Saqué las 13 referencias con un script propio (`cat_honda.py` en el scratchpad): columna C = GLH125SH, sin las piezas Nissin «2U» (refs. 14-16). Los dos PDF de la carpeta son **manuales del propietario**: `manual-cb125f.pdf` no es de servicio y no trae torques del freno.

## Qué siguió fallando
1. **Paso 1 / `extraer_catalogo.py`** no reconoce el formato Honda (columnas por versión 7/8/A/C, códigos de mercado y filas de reemplazo sin número).
2. **Paso 3b (lámina hermana con otra numeración):** la skill solo explica el caso con «la misma numeración». Con números distintos hubo que mapear ids, números y enlaces `[[n|…]]`. Además salieron:
   - enlaces a fichas de contexto (`[[liquido|…]]`) que la hermana sí tenía;
   - chips de `ordenChips` (`barra`, `manguera`, `liquido`) sin ficha;
   - rótulos de contexto dentro del arte («lámina 18/26»);
   - y `v2.deriva`, que compara la seguridad con la ficha de *otra* pieza (avisos falsos «la v1 decía nuevo…»).
3. **Datos «Seguro» (paso 4):** sin manual de servicio, los torques van como «manual de servicio» y la certeza total queda en 34 %.
4. **Medición:** «Cómo funciona» no tiene indicador físico (la fig. 22 tampoco). En el corte se ve uno de los dos pistones. A 360 px, el toque de 5a mide 22 px (la meta es 24). El aviso 6·6/9·9 se ve en transparente.
5. **Cronómetro:** `contenido` en 0 min es engañoso cuando todo se arma en un solo script.

## Cambios propuestos (sin aplicar)
- `extraer_catalogo.py`: formato Honda (`--columna C`, saltar mercados elegidos, filas de reemplazo heredan la ref).
- Paso 3b: una receta «hermana con otra numeración» con mapa `N`/`ID`, remapeo de enlaces, limpiar `ordenChips` y textos de contexto en el arte y quitar `v2.deriva`; y un `grep` de rastros que incluya «lámina \d+» del arte.
- Paso 1: si el catálogo trae variantes (tambor/disco), elegir por la versión que nombre el pedido y decirlo en `cabeza.aviso`.
- Cronómetro: permitir una fase `dibujo+contenido` cuando se arman juntas, con presupuesto 6.
- Fig. 22 y derivadas: agregar el indicador de presión (bar aprox.) en «Cómo funciona».

## Pendientes de la lámina
Torques (falta el manual de servicio Honda); fila «Pastillas y nivel» sin tarea en `garaje/intervalos/honda_cb_125f.json`; sin 3D propio; uno de los dos pasadores y tapones dibujado.

## Revisión integrada (prueba sobre `cb125f-freno`)
Dos subagentes sonnet en paralelo (mecánica y UX). Cada uno recibió solo la página, `motor/revision/cb125f-freno.md` y `guia-revision-rapida.md`; la mecánica, además, el manual. Devolvieron un hallazgo por línea con la etiqueta grave/menor.

| fase | real | presupuesto propuesto |
|---|---|---|
| creación (catálogo + dibujo/contenido + verificación) | 9 min | 6,5 (1 + 4 + 1,5) |
| revisión (las dos en paralelo, de reloj) | 2 min (mecánica 2, UX 1) | 3 (revisión + correcciones) |
| correcciones + chequeo rápido | 2 min | (dentro de revisión) |
| `--final` de nuevo (se tocó el arte) | ~2 min | (dentro de verificación) |
| **total** | **≈ 15 min** (9 + 2 + 2 + 2) | 10 |

El «tiempo de reloj 22 min» de `metricas.py` cuenta también la espera entre turnos por los mensajes de Auxiliares; no fue trabajo.

- **Hallazgos:** UX 2 graves + 10 menores (4,2/5); mecánica 2 graves + 10 menores (4,0/5). Los graves coincidían: la ficha 11 decía «un solo pistón» y quedaba un rastro de la NMAX en las fuentes. **Corregí los 4 graves y 15 menores.** Los menores de más de 1 min van a `pendientes`: 6·6/9·9 en transparente y `cat` en inglés.
- **Verificación:** `--rapido` avisó de una regresión (se había perdido «nuevas» en la ficha 5) y la recuperé. Después, una sola `--final`: código 0, sin bloqueantes, 4,8 medible.
- **5a a 22 px a 360:** agrandar el pistón en el arte no lo arregló; lo arregló el motor (ver «Aplicado»). Ahora todas las piezas tienen ≥ 24 px y el criterio 6 sube de 4,5 a 5 (promedio medible 4,88).
- **Para llegar a 10:** la creación tiene que bajar a ~6 min. Para eso hacen falta la receta 3b (hermana con otra numeración) y `extraer_catalogo.py` con el formato Honda: con ellos el 3b se habría hecho sin las 3 vueltas de errores heredados (~2 min). Además, la revisión mecánica debería recibir del armador una lista de «datos sin fuente» para no gastar tiempo buscándolos.

### Aplicado (el usuario autorizó tocar la skill y sus scripts)
- **`metricas.py`:**
  - fases `dibujo_contenido` (alias `dibujo+contenido`) y `revision`, con presupuestos agrupados (`meta_fases`): catálogo 1, dibujo + contenido 4, verificación 1,5, revisión 3, margen 0,5. Las fases viejas cuentan contra su grupo;
  - el total ahora es creación + revisión;
  - contador de auditoría: a la 5.ª lámina sin auditoría escribe `auditoria-pendiente.md` (tabla con las notas y un brief para pegar) y avisa «hay una auditoría externa pendiente: pídesela a Auxiliares»;
  - `metricas.py auditoria <lamina> <sigue|ajustar|parar>` la registra, borra el pendiente y reinicia el contador;
  - las láminas viejas, que ya tuvieron revisoras externas, quedaron con `revision_externa`, así que el contador está en 1 (la Honda);
  - probado en una copia: a la 5.ª escribió el archivo y la auditoría lo reinició.
- **`extraer_catalogo.py`:**
  - formato Honda: `--figura F10 --columna C --saltar 2U`; sin `--columna` lista las versiones; las filas de reemplazo heredan la ref y se descartan las páginas de índice;
  - da las mismas 13 piezas que la extracción a mano;
  - NMAX, Boxer y AKT: salida **byte a byte idéntica** a la del extractor anterior;
  - el catálogo Honda quedó como `F10` y la lámina como `"figura":"F10"`; el esqueleto lo lee igual.
- **`esquema.js` (toque automático a 360):** con el mínimo de 13 px, dos círculos de toque vecinos se encimaban y el que se pinta después le quitaba área al anterior; era el caso de 5a con 1a. Ahora el círculo nuevo se corre lo que se encima. Comprobaciones:
  - firmas de las láminas de referencia: idénticas, salvo las capas `guiasG`/`marcasG`, que varían igual con el motor viejo (es ruido);
  - Boxer y AKT a 360: sin cambio en piezas (todas ≥ 24 px);
  - freno NMAX: su pieza 4 pasa de 21 a 23 px (ya estaba bajo 24 antes de este cambio; queda pendiente de esa lámina);
  - Honda: 5a resuelto. `medir_lamina.py` no se tocó.
- **SKILL.md:**
  - meta de 10 min para todo;
  - fases y presupuestos;
  - paso 9 «Revisión integrada» (2 subagentes sonnet sin contexto; graves siempre; menores < 1 min o a `pendientes`; `--rapido`; `--final` solo si cambió el arte o el layout; `notas_revision`);
  - formato Honda y variantes en el paso 1;
  - receta «hermana con otra numeración» en el 3b;
  - una línea sobre la auditoría externa.
- **Validador:** OK en las 12 láminas.

### Auditoría externa cada 5 láminas
La guía para la sesión independiente ya está escrita: `guia-auditoria-externa.md`. Sortea 2 de 5 láminas y las revisa a fondo contra el manual y la CVT. Si sus notas difieren en más de 0,3 de las de la revisión integrada, esta está siendo blanda. También mira la tendencia y entrega una página con veredicto (sigue / ajustar / parar); al usuario solo le llega el veredicto. La parte automática ya está en `metricas.py` (`auditoria-pendiente.md`, el aviso y `metricas.py auditoria`).

## Revisión v2 (paso 9 más barato; pedido aprobado por el usuario)
Motivo: en la culata Honda las dos revisoras gastaron ≈ 170 mil tokens (más que la creación), repitieron hallazgos (4 de 11 graves los encontraron las dos) y varios graves los podía ver la máquina.

**Qué cambió**
1. **`mas_controles.py`, 4 controles nuevos** (corren en `--rapido`):
   - `revisar_cantidad_texto`: «un solo pistón» con 2 en el catálogo es **error**; «un/una …» con 2 o más, y «los/dos …» con 1, son aviso. No juzga tornillería ni juegos (SET/KIT/pastillas), ni cabezas que comparten varias fichas.
   - `revisar_rastros`: nombre de otra moto en un texto visible o en el arte es **error** (en Fuentes, aviso: puede ser a propósito); «fig./lámina N» con el formato de otro catálogo (22 en una Honda F10) es aviso.
   - `revisar_jerga`: «copia entregada», «consultado el», «(Escribe…», «plantilla», TODO son **error**; «(manual)»/«(catálogo)» sin decir cuál, aviso.
   - `revisar_dos_nombres`: un enlace `[[n|…]]` o `nombres` con un sinónimo distinto del nombre de la ficha (empaque/junta, retén/sello, rodamiento/balinera…) es **error**; la prosa con un sinónimo que ninguna ficha usa, aviso.
   - Probados con errores sembrados en una copia del freno: los 4 dan error. Sobre la versión sin corregir de la culata atrapan los 3 «(Escribe…)».
2. **Registro de aprendizaje:** `motor/revision/hallazgos.jsonl` (sembrado con los 20 hallazgos reales de las dos revisiones Honda). `aplicar_hallazgos.py --candidatas` lista las categorías repetidas en 2 o más láminas sin control: hoy sale **etiqueta** (números juntos, letra de píldoras).
3. **Resumen compacto** (`autocontrol.py <lamina> --informe --hermana <lámina>`): textos visibles, cantidades del catálogo, fuentes y certezas; lo heredado sin cambio va como «(heredado)»; y las **páginas del manual que aplican** (búsqueda con pymupdf), para que la mecánica no lea el PDF entero. Freno: de ≈ 5.500 a 3.700 tokens; culata: de ≈ 6.300 a 6.000 (sus textos ya eran propios).
4. **Hallazgos con el arreglo exacto:** máximo 12 por revisora, graves primero, en JSON `{gravedad, categoria, campo, reemplazar, por, texto}`. `aplicar_hallazgos.py <lamina> <revisora> <archivo>` aplica los reemplazos (guarda `.antes.json` para las regresiones), lista lo que va a mano y registra todo.
   - Probado en una copia (2 aplicados, 1 a mano, 1 ambiguo rechazado) y luego de verdad en `cb125f-freno`, con 5 reemplazos: «(manual)» → «(manual del propietario)» y «los guardapolvos» → «el guardapolvo». `--rapido` quedó sin regresiones.
   - `--final` se repite solo si hubo graves de dibujo o se tocó el arte o el layout.
5. **Alcances y modelos:** la mecánica (modelo de la sesión) mira técnica, seguridad y datos; la UX (`model: sonnet`) mira claridad, textos y orden, sin repetir lo de la otra. SKILL.md, paso 9, en 6 líneas.

**Ahorro esperado (estimación; se mide en la próxima lámina)**
| fuente de gasto | antes (culata) | v2 |
|---|---|---|
| manual para la mecánica | PDF entero en texto | 6-12 páginas del resumen |
| hallazgos duplicados | 4 de 11 graves, de las dos | alcances separados: ≈ 0 |
| graves que ve la máquina | buscados por las revisoras | `--rapido` antes de revisar: 2 de 4 en el freno y 1 de 6 tipos en la culata |
| resumen | ≈ 6 mil tokens × 2 | 3,7-6 mil × 2 |
| correcciones de la sesión | reescritas a mano | reemplazos con un comando |
| precio por token de la UX | modelo de la sesión | sonnet |

Estimado: **de ≈ 170 mil a ≈ 70-90 mil tokens** en las dos revisoras, y la corrección baja de ~2 min a menos de 1 min cuando los hallazgos son de texto.

**Hallazgos de los controles nuevos sobre las 13 láminas:** 0 errores; 45 avisos. NMAX, Boxer y AKT no se tocaron.
| control | láminas | avisos | lectura |
|---|---|---|---|
| jerga «(manual)» | fig. 7, 10, 11, 22, 24 y freno Honda | 26 (uno es «(catálogo)») | real: nota interna sin decir qué manual. Honda corregida; NMAX, pendiente |
| dos nombres | fig. 8, 11, 22, 24 (junta/empaque), fig. 10 y 11 (sello/retén), AKT y fig. 12 (pin/seguro) | 8 | mayoría real (vocabulario mezclado); «pines» de la fig. 12 parece otra pieza |
| cantidad | fig. 1 («una guía», «dos varillas»), fig. 10 («un buje»), fig. 12 («las rampas»), fig. 24 («una lámina»), AKT («un resorte»), freno Honda | 10 | mayoría genérica y aceptable; real: «los guardapolvos» (Honda, corregido). Falso: «un pistón» de la bomba (otra pieza) |
| rastros | AKT («como el clutch de la Boxer», en Fuentes) | 1 | a propósito; por eso en Fuentes es aviso |

- **Ajustes de reglas por falsos positivos**:
  - «todo» confundido con TODO: ahora distingue mayúsculas;
  - plural de juegos (pastillas, zapatas, rodillos, discos: el catálogo cuenta el juego);
  - plural de cabezas compartidas («las guías»);
  - referencias a otras figuras del mismo catálogo («ver fig. 7»).
- **Verificación:** validador con exit 0 en las 13; extractor de NMAX, Boxer y AKT idéntico byte a byte al original; `esqueleto_v2.py` y `plantillas_ficha.py` sin cambios. Archivo único del freno Honda rearmado. Sin commit.
