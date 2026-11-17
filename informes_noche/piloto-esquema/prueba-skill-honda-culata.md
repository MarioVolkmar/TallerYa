# Prueba 4 de la skill `hacer-lamina`: Honda CB 125F, culata (16-nov-2026)

Lámina `cb125f-culata` · página `motor/cb125f-culata.html` · archivo único `motor/prueba-cb125f-culata.html` · resumen para las revisoras: `motor/revision/cb125f-culata.md`.
**Figura:** la GLH125SH separa la culata en tres figuras: **E-1-2** «Cylinder head» (culata, portalevas, guías, bujía, tubo de admisión: 21 piezas), E-1-1 (tapa) y la de árbol de levas y válvulas. Hice la **E-1-2**, la principal. **Hermana:** NMAX fig. 1, con otra numeración (receta 3b). De ella tomé los DEFS y el «Cómo funciona» de 4 tiempos, cambiando el refrigerante por aletas de aire; el arte de las piezas es nuevo (7 piezas propias).

**Pausa:** hubo una interrupción entre la validación y la revisión (después de `--informe`/`--antes`, antes de lanzar las revisoras). Cae dentro de la fase `revision` de `metricas.py` y **no debe contarse**. No quedó medida; se estima en 2-3 min.

## Tiempos (meta: 10 min con revisión)
| fase | real | presupuesto | |
|---|---|---|---|
| catalogo | 2 | 1 | ⚠ el extractor no leyó E-1-2 (ver abajo) |
| dibujo + contenido | 7 | 4 | ⚠ parser propio + 7 piezas de arte propio + JSON en un script |
| validación + medición | 3 | 1,5 | ⚠ `--rapido`, `--previa` y una medición completa |
| revisión | 10 (≈ 7-8 sin la pausa) | 3 | ✋ CORTE: 12 fichas reescritas, 2.ª medición, un bloqueante |
| **total con revisión** | **≈ 20 min** sin la pausa (23 según `metricas.py`) | 10 | |

Freno Honda (prueba 3): ≈ 15 min con revisión, antes de esta iteración de la skill. **Esta salió peor (≈ +5 min)**. La revisión integrada funcionó bien: las revisoras tardaron 40 s y 80 s y encontraron problemas reales. Lo que costó fue el contenido de plantilla que llegó a revisión sin escribir, y el catálogo.

**Tokens:** contexto de la sesión de 101 k al empezar a 211 k al terminar (≈ 110 k). Las dos revisoras gastaron ≈ 170 k más (83 k + 87 k, sonnet). Imágenes: 3 (plano, previa y una lectura de la captura que se repitió en la revisora UX).
**Mediciones completas: 2.** La 1.ª salió sin bloqueantes. La 2.ª, obligatoria porque cambié la píldora y `toqueExtra`, dio un bloqueante: un paso de «Cómo funciona» de 266 caracteres. Se corrigió y se verificó con `--previa` (chequeo rápido sin problemas), sin una 3.ª medición por la regla de corte.
**Estado final:** validador con 0 errores y 6 avisos (4 son de «regresión» por el texto genérico de la plantilla que se quitó a propósito; los otros 2, la píldora de «Guías» y los números 7·18 juntos en transparente). Medible: promedio 4,63, criterio 6 en 3,5.

**Retoque posterior (pedido de Auxiliares, `chequeo_rapido.py --todas`):** las guías (3, 4, 7), que van prensadas dentro de la culata, pasaron al grupo «Culata»; ya no hay una píldora «Guías» que apunte a piezas ocultas. A las fichas 12-16, 20 y 21 les volvió «si está barrido, va nuevo» y el torque donde faltaba (espárrago del escape, tornillos largos). Quedan 3 avisos de regresión que no son reales: la plantilla repetía «torque» y «manual de servicio» en dos campos, y «en cruz» no aplica a piezas de uno o dos tornillos. `--previa`: chequeo rápido sin problemas.

## Hallazgos de las revisoras (nota antes de corregir: mecánica 3/5 · UX 2/5)
**Graves (11, todos corregidos):**
- Las fichas 10, 17 y 18 tenían relleno de plantilla «(Escribe…)»; la 7 hablaba de mangueras. Las dos revisoras lo encontraron.
- Tornillería (12-16, 20 y 21) con género y número mal («las portalevas») y la 13 descrita como tornillo de culata. Reescribí a mano 12 fichas.
- Cadena «Bujía vieja» terminaba en el espárrago del escape; «Tubo rajado» terminaba en una culata «dañada». Las dos cadenas quedaron causales.
- Faltaban en el desarme el tensor y el piñón del árbol de levas antes del portalevas, y el texto del paso no decía que salían los tornillos y la placa de tope.
- Fichas 3 y 4 nombraban el catálogo en la prosa («trae la de sobremedida») y decían «escarian».

**Menores (17):**
- Corregí 8: escape antes de la culata; compresor de resortes antes de las guías; el balancín en «Cómo funciona»; tuercas y arandelas separadas (4 + 4); prueba de aire con limpiador y no con agua; síntoma de humo de la guía de escape; intervalo en la ficha 5; PMS explicado.
- Quedaron sin corregir (corte): letra de las píldoras del dibujo (≈ 7 px a 1280, es del motor); «Guías» lejos de las guías (al moverla rozaba con «Portalevas»); fichas 3 y 4 casi iguales; «Seguir con:» del panel; pasos con piezas resaltadas que el texto no nombra (en parte); rangos «(0–180°, ideal)».

## Qué siguió fallando (sin aplicar)
1. **Paso 1 de la skill: el extractor Honda no lee figuras de tres niveles.** `extraer_catalogo.py` acepta solo `([A-Z])-?(\d+)` (y `clave_fig` lo exige para entrar a Honda), y su patrón de filas pide las columnas «-------- --------» que la tabla E-1-2 no trae. *Propuesta:* aceptar `E-1-2` → clave `E1-2` y hacer opcionales los guiones. Las alternativas entre paréntesis «(1)» y los mercados (2TU) se resuelven como `--saltar`. El parser que usé está en el scratchpad (`cat_e12.py`, ~20 líneas).
2. **Paso 2 (`plantillas_ficha.py`): la plantilla deja relleno visible y textos que no encajan.** Los tipos `pieza` y `conjunto` dejan «(Escribe…)» y el validador no lo marca; la plantilla de tornillos dice «Los tornillos…» para una pieza; «grapa» toma la plantilla de manguera; el género sale del nombre del grupo («las portalevas»). *Propuesta:* que el validador marque como **error** cualquier «(Escribe» o «(Cuándo revisarlo.)»; usar un artículo por grupo (`"articulo":"el"`); que espárrago y pasador guía tengan su propia plantilla; singular cuando la ficha es de una pieza.
3. **Paso 9: la revisión no cabe en 3 min si la creación deja deuda.** *Propuesta:* antes de lanzar las revisoras, un `autocontrol.py --rapido` que falle por relleno (punto 2) y por cadenas cuyo eslabón sea tornillería. Así esa deuda se corrige en `contenido` y no en `revision`.
4. **Validador, falso aviso de «sobremedida»:** no reconoce «(OS)» de Honda como pieza de sobremedida. *Propuesta:* contar `(OS)`/`O.S.` en la descripción del catálogo.
5. **Toques:** el o-ring 19 sigue en 21 px a 360 aunque está en `v2.toqueExtra`, y el botón «Bujía» mide 32×22 en todas las pestañas. Hay que ver si es del motor.

## Resumen en 5 líneas
1. Culata CB 125F (fig. E-1-2, 21 piezas) hecha desde la hermana NMAX fig. 1 con otra numeración; validador con 0 errores y medible sin bloqueantes (4,63).
2. Total ≈ 20 min con revisión, sin la pausa (meta 10; freno Honda ≈ 15): peor, por el catálogo (extractor sin E-1-2) y por fichas de plantilla sin escribir.
3. La revisión integrada sirvió: 2 revisoras en paralelo, 11 graves reales, todos corregidos; 8 de 17 menores corregidos; la revisión se cortó a los 10 min.
4. 2 mediciones completas; ≈ 110 k tokens de contexto + 170 k de las revisoras.
5. Propuestas: extractor con figuras de 3 niveles y tablas sin guiones; error de validador por relleno de plantilla; artículo y número en las plantillas; contar «(OS)» como sobremedida.
