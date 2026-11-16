# Prueba 2 de la skill `hacer-lamina`: clutch de la AKT NKD 125 CBS 2025 (fig. E-4)

Sesión limpia, siguiendo `SKILL.md` y sus anexos. La lámina queda en `motor/akt-embrague.html` (datos en `motor/datos/akt-embrague.json` y `akt-embrague-arte.js`, catálogo en `motor/catalogo/akt-nkd125.json`; script del JSON en el scratchpad de la sesión).
Figura: **E-4 «Sistema clutch slipper»** (p. 5 del catálogo AKT, 15 refs, fotos en lugar de plano). Sí era aprovechable: es el clutch. La E-3 (tapa del clutch, con la leva) queda para otra lámina.

## Tiempos por fase (reloj, `metricas.py`)
| fase | AKT | Boxer (prueba 1) | meta |
|---|---|---|---|
| catalogo (extraer + esqueleto + plantillas) | **5 min** | 5 min | 1 |
| dibujo2d + contenido + 3D (un solo script) | **10 min** | 6 min | 7 + 5 |
| validacion (a 0 errores + previa) | **1 min** | 1 min | 1 |
| mediciones | **9 min** (3 completas de ~2 min) | 8 min | 1 |
| **total creación** | **25 min** | 20 min | 15 |

- El catálogo tardó lo mismo que con la Boxer, por la misma razón: el extractor no leyó el catálogo (ver abajo). Hubo que escribir un extractor propio de 30 líneas.
- Las fichas no fueron «a mano» desde cero, pero casi: las plantillas salieron, y se reescribieron las 15 (nombres con códigos de modelo, «que» genérico, lugar mal nombrado). Lo que ahorró tiempo fue partir de la lámina hermana `boxer-embrague` (mismo sistema): arte, «Cómo funciona», cadenas y la estructura de las fichas se adaptaron en vez de escribirse.
- Mediciones: las dos primeras dieron un bloqueante cada una («etiquetas montadas» en «Cómo funciona»: textos del panel derecho más largos que los de la Boxer contra «Palanca»). La tercera aprueba: validador 0 errores, medir sin bloqueantes, medibles 4,72; notas a ojo 4 (promedio 4,4 < 4,5 de la base, anotado en `explicacion`). Sin revisión mecánica ni UX todavía.
- Contenido figura con 0 min porque se escribió dentro de `dibujo2d`, en el mismo script.

## Qué funcionó sin trabajo manual
- `esqueleto_v2.py` con descripciones en español (`claves_es.py`): clasificó bien resorte, rodamiento, arandela y tornillo, y armó grupos, tornillería y pasos.
- `plantillas_ficha.py`: llenó los 15 borradores; `--tipo 13=seguro` corrigió el tipo.
- Validador y `autocontrol.py --rapido`/`--previa`: rápidos y claros; con la lámina hermana se llegó a 0 errores en 4 corridas.

## Qué siguió fallando o quedó ambiguo
1. **Paso 1 «Catálogo»: `extraer_catalogo.py --figura/--columna` no sirve para AKT.** El catálogo AKT tiene la cabecera `Ref. | PLM | Articulo | Descripciones | Cant | NOTA` y la figura como «E- 4» (letra + número, E = motor, F = chasis). El extractor busca `FIGURA N` y `PARTE/CÓDIGO`: sin `--figura` da «0 figuras», con `--figura 4` «no encontré su tabla». Además, en AKT el código y el EAN-13 a veces salen pegados en una línea (`PORTA_SLIP_CGR 7700149537476`) y algunas filas no traen código.
2. **Paso 2: `esqueleto_v2.py` exige figura entera** (`int(a.figura)`): «E4» falla. Se renombró a «4» en el catálogo; choca si alguna vez se extraen E-4 y F-4 juntas.
3. **Paso 2: los nombres sugeridos arrastran códigos de modelo**: «Manzana slipper clutch cta 125nkd», «Jgo discos clutch 125 x 6», «Balinera 16003/p6 125cgr». `nombre_es` no quita sufijos (125NKD, CGR, 125S, Rp) ni abreviaturas (Jgo, Cta, Separad).
4. **Paso 2: «PIN» = pasador**, pero en AKT «Pin Prensa Clutch» es un seguro (anillo elástico, se ve en la foto). La regla de la primera palabra lo clasifica mal; hay que mirar la foto.
5. **Paso 2: intervalos sin km.** `akt_nkd_125.json` solo tiene `aceite` (km = null) y `cadena-lubricar`; el esqueleto escribió «Aceite: Cada .». No hay tarea de clutch y `--tareas embrague` revienta con `KeyError`.
6. **Paso 3: kits sin dibujo propio.** Las refs 1 (clutch completo), 15 (centro slipper) y 7 (juego de discos) son conjuntos; el validador exige pieza dibujada para cada número, y la skill no dice cómo dibujar un conjunto que no tiene cuerpo propio (la NMAX siempre tuvo uno: cáliper, culata). Se resolvió con miniaturas en marco punteado y un paso «Repuestos por conjunto».
7. **`mas_controles.py`: «la lámina dice CBS y la figura del catálogo no».** CBS es el nombre del modelo (NKD 125 CBS), no un sistema de la figura. Hubo que sacar «CBS» del título.
8. **Validador de certeza**: una frase «deducido de las fotos *del catálogo*» se marca como error («sale del catálogo y está como aprox.»). Hubo que cambiar la palabra.
9. **Manual del propietario escaneado (sin texto)**: la regla «solo texto con pymupdf» no da nada; el juego libre de la palanca queda «sin dato». Se usó la nota del auditor (capa3-nkd.md) para el aceite.
10. **Ambigüedad mecánica propia de la figura** (anotada en `pendientes`): orden interno presionador/portadiscos, «6 resortes» en la ref. 2 contra 3 resortes en la ref. 8, y refs. 5-6 (discos 125S) contra la 7 (juego slipper).

## Cambios propuestos (sin aplicar)
- `extraer_catalogo.py`: tercer formato «AKT» (cabecera `Ref.`+`Descripciones`+`Cant`, figura `^[A-Z]-\s*\d+`, filas `E4-n`, separar EAN-13 pegado, código vacío permitido). Mi script de 30 líneas sirve de base (en el scratchpad de esta sesión: `catalogo_akt.py`).
- `esqueleto_v2.py`: aceptar figura alfanumérica («E4») y no escribir filas de «Cuándo» con km nulo; `--tareas` con clave inexistente → aviso, no `KeyError`.
- `claves_es.py`/`nombre_es`: quitar sufijos de modelo y expandir abreviaturas (Jgo → Juego, Cta → completo, Separad → separadores, Balinera 16003 → Balinera); «Pin … clutch» con anillo → que avise «¿seguro o pasador?».
- `mas_controles.py`: ignorar ABS/CBS cuando forman parte del nombre de la moto (`D["moto"]` o el catálogo).
- `SKILL.md` paso 3: un párrafo «Conjuntos sin cuerpo propio (kit, clutch completo)» con la salida usada aquí (miniatura `esq-oculto-arm` + paso final) o un tipo común `kit` en la biblioteca.
- `SKILL.md` paso 1 y «Leer poco»: decir qué hacer si el manual del propietario es escaneado (buscar primero en las notas del auditor / `garaje/intervalos`), y que la lámina hermana del mismo sistema en otra marca (aquí `boxer-embrague`) es el mejor punto de partida, aunque la numeración cambie.
- La medición completa sigue pasando de 2 min: la skill debería decir que va con `run_in_background`.

## Mejoras aplicadas (16-nov-2026, aprobadas por el usuario)
Qué cambió:
- `catalogo/extraer_catalogo.py`: formato AKT con `--figura E4` (o `E-4`). Lee la cabecera `Ref./Descripciones/Cant` y las filas `E4-n`, separa el EAN-13 pegado y acepta código vacío. La figura queda «E4», así no choca con «F4». Los conjuntos quedan en `partes` porque tienen número en la foto.
- `esqueleto_v2.py`:
  - acepta figura con letra («E4»/«E-4») y la escribe como texto en el JSON;
  - una tarea sin km ni días, o que no existe en `--tareas`, da un aviso en lugar de una fila «Cada .» o un `KeyError`;
  - los ids de grupo salen únicos;
  - avisa «Pin» → ¿seguro?
- `catalogo/claves_es.py`:
  - `nombre_es` quita los sufijos de modelo y los números de balinera (125NKD, CGR, 125S, 125/R, Rp, «x 6», 16003/P6), deja las medidas (6x25, M6x40, 2×16) y expande abreviaturas (Jgo, Cta, Separad, Sliper…);
  - Jgo/Cta marcan conjunto;
  - nueva `aviso_es`.
- `mas_controles.py`: ABS/CBS no da error si es parte del nombre de la moto. «Fotos del catálogo» o «deducido» en una certeza «aprox.» ya no es error.
- `validar_esquema.py`: `figura` puede ser número o texto.
- Nuevo `revisar_funciona.py`, que busca etiquetas montadas en «Cómo funciona» a los 6 anchos (~12 s). Usa la misma regla que `medir_lamina.py` y reutiliza su servidor y Chrome, sin cambiarlo. `autocontrol.py --previa` lo corre al final y sale con 1 si hay etiquetas montadas.
- `SKILL.md`: 4 cambios cortos (AKT `--figura E4`, manual escaneado → «sin dato» + `pendientes`, conjuntos sin cuerpo propio con `arteKit`, `--previa` con el chequeo nuevo y la medición completa en segundo plano).
- Lámina AKT: `catalogo/akt-nkd125.json` ahora sale del extractor (E3 y E4) y `akt-embrague.json` usa `"figura":"E4"`.

Cómo se verificó:
- Antes y después, con el mismo script: extractor NMAX (38 figuras), extractor Boxer fig. 14 TEC y `esqueleto_v2.py` + `plantillas_ficha.py` de NMAX figs. 1, 8, 12 y 26 y Boxer fig. 14. JSON y salida de consola salen **byte a byte idénticos**.
- AKT E-4 extraída sola: `partes` igual a la del catálogo a mano (15 piezas; 9 y 14 sin código).
- El esqueleto de la AKT ahora da nombres limpios («Juego de discos clutch», «Balinera», «Tornillo prensa clutch 6x25»), conjuntos reconocidos, avisos de «Pin» y del aceite sin km, y ya no escribe la fila «Cada .». La agrupación sigue siendo una propuesta para ajustar a mano (sale con 7 grupos).
- `autocontrol.py --rapido`: 0 errores en nmax-fig12, nmax-fig26, boxer-embrague y akt-embrague.
- `revisar_funciona.py`: la AKT pasa en 6 anchos. Una copia temporal con la etiqueta larga de la primera medición la detecta a 360 y 390 (código 1). Esa copia se borró. `autocontrol --previa` completo: 24 s, código 0.

Visto de paso, sin tocar: en `mas_controles.py` (dict `SEGURIDAD`, «marca») hay un carácter de retroceso donde iba `\b`. La palabra «marca» casi no se detecta en el control de regresión.

## Refinamiento 2 (16-nov-2026): tiempos, reprocesos, tokens y revisiones, para todas las láminas
### Qué cambió
- **Meta de 10 min** (`metricas.json` y el plan de `SKILL.md`):
  - presupuesto: catálogo 1 · dibujo 4 · contenido 2 (con el 3D) · verificación 2 (previa + una sola medición completa) · 1 de margen;
  - `metricas.py fin` marca ⚠ si la fase pasa su presupuesto y ✋ **CORTE** si pasa del doble (se para, la causa va a `pendientes` y se sigue);
  - revisiones: 10 min cada una, en paralelo (`meta_revision_min`).
- **Una sola medición completa:**
  - nuevo `motor/chequeo_rapido.py`, que `autocontrol --previa` corre solo. Revisa etiquetas montadas en «Cómo funciona» (a 360, 390 y 1280), pasos sin cambio visible (bloquea), pasos con ≤ 2 cambios o de más de 250 caracteres, marcas de menos de 44 px y pieza tapada en el desarme general (con `medir_lamina.py --solape`);
  - usa las mismas reglas que el medidor y no toca `medir_*.js`, `medir_lamina.py` ni `esquema*.js`;
  - reemplaza a `revisar_funciona.py`, que se borró.
- **`chequeo_rapido.py --todas`:** tabla lámina → qué incumple, de todas las páginas de `motor/` (validador + navegador). Está abajo.
- **Tokens:**
  - `autocontrol.py` da resumen por omisión (hasta 8 errores y avisos agrupados por tipo) y `-v` para el detalle;
  - en `SKILL.md`: 3 imágenes por lámina como máximo, nunca volcar el JSON ni el arte, y tokens al inicio y al final con `metricas.py dato <l> tokens` (el `informe` los muestra).
- **Revisiones más rápidas:**
  - `autocontrol.py <l> --informe` escribe `motor/revision/<l>.md`: desarme, grupos, fichas, «Cómo funciona», cadenas, «Cuándo», certezas aprox., pendientes, validador, última medición y capturas;
  - la medición final se guarda en `revision/<l>-medicion.txt` para ese informe;
  - nueva guía `guia-revision-rapida.md`: qué ya mide la máquina, 6 puntos de mecánica y 5 de UX, 10 min cada una, en paralelo, salida de ≤ 30 líneas.
- **Kits sin dibujo** (pedido del usuario: la píldora «Conjuntos» no se entendía):
  - el validador acepta `"kits":{"<ref>":[refs que trae]}` sin pieza, grupo ni ficha, comprueba que las piezas que trae lo digan («Para pedirla»), y avisa si una píldora apunta a piezas que no se ven armadas;
  - en la AKT, refs. 1, 7 y 15 ya no se dibujan: van en `kits`, en el `cat` de las piezas que traen y en `textoArmado`;
  - la regla quedó en `SKILL.md` en lugar de la de las miniaturas.
- **Errores `\b` arreglados en `mas_controles.py`** (había un carácter de retroceso donde iba `\b`): «marca» y «nuevo» del control de seguridad, «PAD» del control de frenos y un control de nombres. Resultado: no aparecen errores nuevos de «marca». El control v1 → v2 ahora ve «nuevo» y da avisos nuevos en nmax-fig12 (2), fig22 (2), fig24 (1) y fig26 (2): «la v1 decía nuevo y la v2 ya no». Son avisos, no errores; quedan para revisar.
- Verificación: extractor, esqueleto y plantillas de NMAX (1, 8, 12, 26) y Boxer 14 siguen **byte a byte idénticos**; `--rapido` da 0 errores en las 11 láminas; el esqueleto AKT sale igual que en la ronda 1.

### Tabla de todas las láminas (`chequeo_rapido.py --todas`, 338 s con la máquina cargada)
| lámina | validador | navegador (bloquea) | avisos |
|---|---|---|---|
| nmax-fig1 | ok | ok | - |
| nmax-fig7 | 1 paso > 300 car. | ok | - |
| nmax-fig8 | 1 paso > 300 car. | ok | - |
| nmax-fig10 | ok | ok | - |
| nmax-fig11 | 2 píldoras sin pieza visible | ok | - |
| nmax-fig12 | 1 paso > 300 car., 1 píldora sin pieza visible, 2 avisos «nuevo» v1→v2 | ok | - |
| nmax-fig22 | 1 paso > 300 car., 2 avisos «nuevo» | ok | «Cómo funciona» paso 2 con ≤ 2 cambios |
| nmax-fig24 | 1 paso > 300 car., 1 aviso «nuevo» | ok | «Cómo funciona» paso 2 con ≤ 2 cambios |
| nmax-fig26 | 3 pasos > 300 car., 2 avisos «nuevo» | ok | - |
| boxer-embrague | ok | ok | «Cómo funciona» paso 3 con ≤ 2 cambios; pieza tapada 17 % |
| akt-embrague | ok | ok | «Cómo funciona» paso 3 con ≤ 2 cambios; pieza tapada 16 % |

Ninguna lámina tiene bloqueantes en el navegador. La página vieja `nmax-fig26-v1` (pieza tapada 29 %) ya no entra en `--todas`.

### Ahorro esperado por fase (contra la prueba 2: 25 min)
| fase | AKT | esperado | por qué |
|---|---|---|---|
| catálogo | 5 | 1 | el extractor ya lee AKT; nombres limpios; avisos de Pin y de km |
| dibujo + contenido | 10 | 6 | lámina hermana como regla; kits sin dibujo (no hay arte de miniaturas) |
| verificación | 10 | 3 | la previa con chequeo (~1 min) atrapa lo que obligó a 3 mediciones; queda una de ~2 min |
| **total** | **25** | **≈ 10** | |
| revisiones | 32 (UX) | 10 + 10 en paralelo | resumen `--informe` y guía; no se navega ni se mide de nuevo |

Tokens: con 3 imágenes y salidas cortas, el ahorro esperado es de un 30-40 % del contexto por lámina (las imágenes y los volcados eran casi todo). La tercera prueba lo mide con `tokens`.

### Qué impide los 10 min y qué haría falta
- **Verificación:** la medición completa tarda ~2 min de reloj (6 anchos; espera hasta 480 s) y el chequeo rápido 40-100 s según la carga de la máquina (aquí, 43 procesos de Chrome de otras sesiones). Con 2 min de presupuesto queda justo. Haría falta un modo «final» más corto en `medir_lamina.py` (menos anchos, menos espera), que es de relevo-motor: **propuesta**.
- **Dibujo de una lámina sin hermana** (sistema nuevo): 4 min solo alcanza si existe una lámina hermana. Para sistemas nuevos haría falta ampliar la biblioteca de piezas comunes (corona, discos, plato con torres).
- **Propuestas para otras sesiones** (las coordina Auxiliares):
  1. motor: un aviso corto de kits en el panel de la derecha, a partir de `D.kits` (`esquema.js`);
  2. medir: el alto de las marcas da 46 px en el chequeo y 43 en la medición (otro estado de la vista): unificar la regla;
  3. revisora-esquemas y ux-piloto: adoptar `guia-revision-rapida.md` y `--informe`, y correr en paralelo.
