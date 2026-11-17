# Prueba 5 de la skill `hacer-lamina`: clutch Honda CB 125F (fig. E-6-1)

16-nov-2026 · primera prueba con la revisión integrada v2 · hermana `akt-embrague` (otra numeración) · página `motor/cb125f-clutch.html`, archivo único `motor/prueba-cb125f-clutch.html`.
Figura: **E-6-1 «Clutch (GLH125SH)»**, 15 piezas, columna C. La E-6 (GLH1251SH/2SH/3SH) sale vacía en la columna C. El clutch y la tapa vienen en figuras separadas: la tapa derecha, con el brazo del clutch, es la **E-5** y queda fuera.

## Tiempo (reloj, en serie)
| fase | real | presupuesto | |
|---|---|---|---|
| catálogo + esqueleto | 1 min | 1 | ✓ |
| dibujo + contenido | 7 min | 4 | ⚠ +3 |
| validación + mediciones | 6 min | 1,5 | ⚠ +4,5 |
| revisión (revisoras + correcciones) | 2 min* | 3 | ✓ |
| **total con revisión** | **≈ 16 min** (metricas.py: 15) | 10 | faltaron 5-6 |

\* Las revisoras se lanzaron mientras corría la medición completa (que duró ~2 min), así que su tiempo queda en parte dentro de «mediciones». Contando de punta a punta (18:31 → 18:47) da 16 min.
Comparación: Boxer 20 min · AKT 25 · culata Honda ≈ 20 · **clutch CB 125F ≈ 16**. Es la más rápida de las cuatro con revisión, pero no llegó a los 10 min.

## Tokens
- **Creación:** ≈ 101 mil (el contexto pasó de 102 mil a 203 mil). La culata gastó ~110 mil.
- **Revisora mecánica** (opus): 85,5 mil. **Revisora UX** (sonnet): 80,2 mil. **Total de las dos: 166 mil**; la culata gastó ~170 mil. Prácticamente no bajó: el resumen compacto (4 mil tokens) ayuda poco, porque la mayor parte se va en el contexto fijo de cada subagente.
- **Mediciones completas: 1** (más 1 `--previa` y 2 `chequeo_rapido.py` sueltos para el solape).

## Hallazgos
- **Mecánica (nota 4):** 9 hallazgos, 2 graves. (1) Los resortes se apoyan en la manzana, no en las torres; (2) la guía no gira suelta con la palanca suelta. **7 los aplicó solo el script**; 2 fueron a mano: la posición de la arandela de 17 mm y el aviso del pedal de freno y del empaque de la tapa.
- **UX (nota 4):** 11 hallazgos, 1 grave (paso 1 de «Cómo funciona» muy largo). **6 los aplicó solo el script**, 2 fallaron porque la mecánica ya había cambiado ese texto y 3 eran a mano: el de las fichas 8 y 13 era falso, porque el resumen no mostraba sus campos; lo práctico primero en «Cuándo» del aceite sí se corrigió; el tono de «Cómo funciona» 3-4 se dejó.
- **En total: 13 aplicados por `aplicar_hallazgos.py`, 4 tocados a mano** (y además se acortó el paso 1, que la corrección dejó en 311 caracteres).
- Notas de la medición: UX medible 4,63, sin bloqueantes, pero «Medible NO APRUEBA» por el criterio 6 (3,5): botones de enlace de 22 px a 1024. Notas de las revisoras: 4 y 4, **por debajo de la base de 4,8**.

## Qué atraparon antes los controles automáticos
- El validador frenó las medidas sin fuente (17 mm y 2,8 mm de las arandelas) y el «Cuándo» del aceite sin plazo en años, que se coló desde un texto propio.
- El chequeo rápido atrapó el **solape del despiece** (28 % y luego 22 %) al agregar una quinta capa de discos. Se arregló antes de medir.
- El control de rastros de la hermana no dio nada: el script ya había limpiado AKT/NKD/slipper/73.
- Ninguna revisora repitió problemas de cantidad, jerga ni relleno.

## Qué siguió fallando (con su sección de la skill)
1. **«Dibujo + contenido» +3 min** (paso 3b): las 15 fichas se escriben a mano porque la hermana tiene otros nombres y otra cantidad. Se perdió tiempo en 4 corridas del script: comillas en `\n`, y el script lee su propia salida como esqueleto. Al regenerar, el «Cuándo» de una corrida se coló en la siguiente.
2. **Verificación +4,5 min** (pasos 6-7): `--previa` (~1 min) + dos `chequeo_rapido` (~35 s c/u) + la medición (~2 min). Con 1,5 min de presupuesto no alcanza ni con una sola medición.
3. **Paso 9.2 / 9.3, formato:** la skill pide a las revisoras «un JSON con hallazgos más una nota», pero `aplicar_hallazgos.py` solo acepta una **lista**: falló con `TypeError` y hubo que convertir el archivo. Además, sin `campo` dos reemplazos de UX chocaron con los de la mecánica.
4. **Resumen compacto** (paso 9.1): no muestra todos los campos de las fichas, y la UX reportó como faltantes los de las fichas 8 y 13.
5. **Motor (CSS):** `.esq-enlaces/.esq-efecto button` solo tienen 44 px bajo 700 px de ancho. A 1024, la medición marca los botones de 22 px y el criterio 6 baja a 3,5. Queda en `pendientes` para Auxiliares.
6. **Dibujo pendiente:** la arandela de 17 mm (ref. 13) quedó en el texto entre la campana y la manzana, pero en el despiece todavía sale detrás de la campana.

## Cambios que propongo (sin aplicar)
- `aplicar_hallazgos.py`: aceptar `{"nota", "hallazgos":[…]}` además de la lista, y anotar la nota sola en `metricas.py`.
- Paso 9.2: exigir `campo` en cada hallazgo y aplicar la UX **antes** que la mecánica, o reintentar por `campo` cuando el texto ya cambió.
- `--informe`: incluir en el resumen todos los campos de cada ficha (aunque sea abreviados), para que no salgan falsos «faltan».
- Receta 3b: que el script de armado lea el esqueleto desde una copia (`<lamina>.esqueleto.json`) y no desde su propia salida. Y presupuesto real: dibujo + contenido 6 min y verificación 3 min, o aceptar 15 min como meta con revisión.
- Esqueleto: tratar «DISK, CLUTCH FRICTION» repetido con dos códigos como «tipo A/B» automáticamente.
- Motor: `min-height:44px` en `.esq-enlaces/.esq-efecto button` a todo ancho (pedírselo a Auxiliares, con la firma de las 5 láminas).

## Ronda 3 (mejoras a la skill aprobadas por el usuario)
1. **Una sola revisora** (paso 9): un subagente con el modelo de la sesión revisa mecánica y UX en una pasada (las dos listas de `guia-revision-rapida.md`, sin repetir). Devuelve `{"nota":{"mecanica":x,"ux":y},"hallazgos":[…]}` con máximo 15 hallazgos, graves primero. La calidad la vigila la auditoría externa cada 5 láminas. **Ahorro esperado: ≈ 80 mil tokens por lámina** (de 166 mil con dos revisoras a ≈ 85 mil, lo que gastó la mecánica sola: el gasto es el contexto fijo de cada subagente).
2. **`aplicar_hallazgos.py`:**
   - acepta la lista o `{"nota", "hallazgos"}`, y la nota va a `metricas.py` (`notas_revision`);
   - un hallazgo de texto sin `campo` no se aplica: falla con el motivo;
   - si el texto cambió, reintenta en el `campo` sin mirar espacios, mayúsculas ni etiquetas; si no lo encuentra, o ya dice lo nuevo, avisa y va a mano (no falla);
   - probado con los dos formatos en una copia del freno: aplicado exacto, sin campo, reintento por espaciado, ya aplicado, inexistente y nota anotada; después se limpió.
3. **`--informe`:** cada ficha muestra todos sus campos (que, sirve, porque, cuando, fallas, síntomas, arrastra, decisión, conecta): «(heredado)» si es igual a la hermana y «— falta» si está vacío. Ya no salen hallazgos falsos de «faltan campos».
4. **Verificación en una corrida:**
   - `autocontrol --previa` hace en un solo Chrome «Cómo funciona» a 360/390/1280, marcas, el **solape** y la **captura**. Antes eran 3 Chrome: medir `--solo-captura`, el chequeo y medir `--solape`.
   - El solape de un grupo se vuelve a medir con `--previa --solo-solape --grupo 13,1,2` (filtro nuevo en `medir_solape.js`).
   - Medido en el clutch: la previa baja de **62 s** (19 + 24 + 19) a **29 s**, y volver a medir el solape de un grupo tarda **23 s**, frente a ~43 s de un `chequeo_rapido` suelto. En la prueba 5 eso habría sido de ≈ 2,5 min a ≈ 1 min; la verificación queda en ≈ 3-3,5 min con la medición final (~2 min, que sigue igual).
5. **Fichas desde la hermana:**
   - `plantillas_ficha.py --hermana <lámina> --escribir` le pone a cada ficha vacía la de la hermana del mismo tipo (claves_es + palabras del catálogo en inglés), con el nombre nuevo y los enlaces como texto; lo que falte sale de la plantilla.
   - Probado con el esqueleto del clutch Honda y la Boxer de hermana. Discos con discos, resorte con resorte, tornillos con tornillos, tuerca con tuerca, arandelas con arandela; para editar, no para dejarlas así.
   - Esqueleto: `esqueleto_v2.py --escribir` deja siempre `<lamina>.esqueleto.json` (copia limpia) y no pisa una lámina que ya existe; la receta 3b dice partir de esa copia, nunca de la propia salida.
6. **Presupuestos** (`meta_fases`, suman 10): catálogo 1 · dibujo + contenido 4 · verificación 2,5 · revisión 2 · margen 0,5.
   - Con los datos de las 5 pruebas, dibujo + contenido fue de 5 a 7 min; las fichas desde la hermana deberían quitar ≈ 2.
   - La verificación fue de 3 a 6 min; con la previa en una corrida queda en ≈ 3.
   - La revisión con una sola revisora corre mientras se hace la medición.
7. **Motor (CSS):** `.esq-cadena/.esq-enlaces/.esq-efecto button` con `min-height:44px` a todo ancho (antes solo bajo 700 px).
8. **Clutch Honda:** en el despiece, la arandela 13 sale ahora delante de la campana, en el mismo eje y antes de la manzana (paso 5: `[-50,-36]` en vez de `[-151,-110]`, que la dejaba detrás). `separar_numeros` separó su número del 7. Archivo único rearmado.

**SKILL.md:** de 26.935 a 26.501 caracteres. El paso 9 quedó para una sola revisora; el detalle del validador y de los toques pasó a `anexo-autocontrol.md`.

**Verificación:**
- validador con 0 errores en las 14 láminas;
- extractor de NMAX, Boxer y AKT idéntico byte a byte al original, y `esqueleto_v2.py` con salida idéntica a la de antes (más la copia limpia);
- `chequeo_rapido --todas` sin incumplimientos nuevos: siguen los avisos de AKT y Boxer (pieza tapada 16-17 %) y las regresiones de la culata contra su `.antes.json`;
- firmas: cvt, bomba-freno y admision idénticas; freno solo en `marcasG`, el ruido conocido;
- captura del despiece del clutch: la arandela queda delante de la campana;
- los 14 archivos únicos rearmados (por el CSS). Sin commit.
