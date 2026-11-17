# Prueba 6 de la skill `hacer-lamina`: horquilla delantera Honda CB 125F (fig. F-8)

16-nov-2026 · primera prueba con la ronda 3 y la primera **sin hermana**: ninguna lámina hecha es de suspensión, así que no se copió nada de otra lámina. El arte (17 funciones) y las 17 fichas se hicieron desde cero, con las ayudas de estilo de la CVT y las plantillas.
Página: `motor/cb125f-horquilla.html`. Archivo único: `motor/prueba-cb125f-horquilla.html`. Datos: `datos/cb125f-horquilla*.{json,js}`. Catálogo: F-8 «Front fork», columna C, 19 refs. Las refs 1 y 10 (barras completas) van como `kits`.

## Tiempo (reloj, en serie)
| fase | real | presupuesto | |
|---|---|---|---|
| catálogo + esqueleto | 3 min | 1 | ⚠ +2 (buscar la F-8 en el índice y elegir la columna) |
| dibujo + contenido | 7 min | 4 | ⚠ +3 (todo el arte y las fichas desde cero) |
| validación + mediciones | 5 min | 2,5 | ⚠ +2,5 |
| revisión (revisora + correcciones) | 9 min* | 2 | ✋ CORTE |
| **total con revisión** | **≈ 21 min** (19:33 → 19:54) | 10 | faltaron 11 |

\* 3 de esos minutos se solapan con la medición. La revisora tardó 4 min de reloj. `metricas.py` dice 18 min de reloj porque perdió el `inicio` del catálogo: la fase quedó solo con su `fin`.
Comparado con el clutch Honda (≈ 16 min, con hermana): **5 min más**. Ese tiempo se fue en dibujar y escribir sin una lámina de partida (+3 min contra el presupuesto) y en la revisión.

## Tokens
- **Creación:** ≈ 100 mil (el contexto pasó de 103 mil a 203 mil). El clutch gastó 101 mil.
- **Revisora (una sola, opus):** 92 mil. El clutch gastó 166 mil con dos revisoras: **bajó 45 %**, cerca de los 85 mil previstos.
- **Mediciones completas: 2.** La primera dio «NO APRUEBA» por el criterio 6, porque las píldoras Tapón/Barra se rozaban a 360. La segunda dio «APRUEBA», con UX medible 4,8. Hubo además 2 `--previa` de 24 s, en un solo Chrome.

## Hallazgos (revisora: mecánica 4,3 · UX 4,4)
- **12 hallazgos, 3 graves**, los tres del orden y la seguridad del desarme:
  - «afloja los pernos de la tijera» antes de soltar el tapón, que necesita la barra apretada;
  - no decía cuándo sale la barra de la moto;
  - al armar faltaban la altura de las barras y el torque de la tijera.
- **`aplicar_hallazgos.py` aplicó solo 11** (los 3 graves incluidos), sin fallos. **1 fue a mano** (nombres de los grupos «Barra y retén» y «Barra derecha…»). **0 falsos.** Después se acortó a mano el paso 7, que con el cierre agregado quedó en 324 caracteres.
- Notas por debajo de la base (4,8). Explicación anotada: sin hermana, el desarme se escribió de memoria, y la revisora atrapó justo eso.

## Qué atraparon antes los controles automáticos
- Validador:
  - la moto con un nombre distinto al del catálogo («CB 125F» frente a «CB125F»);
  - el número 12 pegado al borde del encuadre;
  - 6 singulares en fichas de piezas que vienen de a 2;
  - «sello» frente a «retén» en la ficha 14;
  - la dificultad «fácil» del guardapolvo (hay que drenar);
  - la píldora de un grupo sin piezas visibles armadas;
  - el paso de 324 caracteres.
- `--previa`: el tornillo allen tapaba un 34 % de la arandela en el despiece (bloqueante) y la etiqueta «Botella» quedaba tapada en «Cómo funciona».
- Medición final: el roce de las píldoras a 360 y el toque del retén de 21 px.

## Qué siguió fallando y cambios propuestos (sin aplicar)
1. **Sin hermana no hay biblioteca para vista vertical** (paso 3, «Primero la biblioteca»). Las piezas comunes se dibujan de frente, con el eje hacia el lector, y en una horquilla los ejes van verticales: no sirvió ninguna, y anillos, resortes y tornillos se hicieron a mano. Propuesta: un parámetro `p.eje:"vertical"` en `piezas-comunes.js` (anillo como elipse, resorte de lado).
2. **La revisión rompe la regla de corte** (paso 9 y «Cronómetro»). La revisora sola tarda ~4 min de reloj, el doble del presupuesto de la fase. Propuesta: presupuesto de 4 min si corre en paralelo con la medición, o contar solo las correcciones.
3. **El desarme sin hermana sale flojo de orden y seguridad** (paso 3, «Pasos del desarme»). Propuesta: una lista corta por sistema en la skill (suspensión: tapón con la barra en la tijera de abajo, altura de las barras, torque de la tijera, aceite igual en las dos).
4. **`aplicar_hallazgos.py` escribe sobre el JSON** y el script de armado ya no lo regenera igual (paso 3b). Propuesta: que exporte los reemplazos como bloque para pegar en `armar_<lamina>.py`.
5. **`metricas.py` perdió el `inicio` del catálogo** (fase con solo `fin`). Propuesta: avisar al hacer `fin` si no hay `inicio`.
6. **Botones de enlace de 22 px** en las fichas a 1024/1280 (criterio 6, ya visto en el clutch). Siguen apareciendo en la primera medición: falta revisarlo en el motor.

**Auditoría:** `metricas.py` cuenta 4 láminas desde la última auditoría (freno, culata, clutch y horquilla de la CB 125F) y no escribió `auditoria-pendiente.md`. La 5.ª será la próxima.

## Ronda 4 (mejoras a la skill aprobadas por el usuario)
1. **Biblioteca con eje vertical** (`piezas-comunes.js`): con `p.eje:"vertical"`:
   - arandela, retén, o-ring y seguro salen de canto (elipse de arriba + banda);
   - resorte, tornillo y tuerca salen de lado;
   - `"horizontal"` es la misma pieza girada 90°;
   - sin `eje`, todo queda como antes.

   En la horquilla pasé a la biblioteca el o-ring 17, la arandela 14 y el resorte de rebote 4. La captura del despiece antes y después se ve prácticamente igual. Su `arteOring/arteArandela/arteRebote` quedan en el `-arte.js` sin usar. Si se regenera con el script de armado de la prueba 6, hay que pasarle este cambio.
2. **Orden y seguridad del desarme:** `.claude/skills/hacer-lamina/anexo-desarme.md`, con 4-6 reglas para cada uno de los 10 sistemas, enlazado en una línea desde «Pasos del desarme».
   - Control `revisar_orden_sistema` en `mas_controles.py`, lista `ORDEN_SISTEMA`: pernos de la tijera antes del tapón, rueda antes del eje, rueda delantera antes del cáliper, cadena o piñón del árbol antes del PMS o del tensor, tapa del clutch antes de aflojar el cable, positivo antes que negativo.
   - Sobre las 15 láminas: 0 avisos. Sembrando el error de la horquilla («Afloja los pernos de la tijera» antes del tapón), avisa.
3. **Revisión dentro del presupuesto:**
   - la revisora se lanza junto con la medición `--final`;
   - `revision` cuenta solo las correcciones y la espera va a `revision_espera`, fuera del total;
   - presupuestos con los datos de las 6 pruebas: catálogo 1,5 · dibujo + contenido 4 · verificación 2,5 · revisión 1,5 · margen 0,5 = 10.
4. **Botones de 22 px en las fichas:** era el botón «Seguir con: …» (`.esq-v2-seguir .esq-enl`), que solo tenía 44 px bajo 960 px. Ahora los tiene a todo ancho.
   - En la medición final, el clutch aprueba el criterio 6 con 5 y la horquilla no tiene botones chicos.
   - La horquilla sigue con 6 = 4 por **otra causa, que ya estaba antes de esta ronda** (medido con su JSON anterior, igual): a 360, las piezas 15 (23 px) y 16 (18 px) tienen poca área de toque. Se arregla en la lámina (`v2.toqueExtra` o separar), no en el motor.
5. **`aplicar_hallazgos.py`:**
   - cada reemplazo aplicado queda en `datos/<lamina>.hallazgos.json` y la salida muestra la línea para pegar al final del script de armado;
   - `aplicar_hallazgos.py --reaplicar <lamina>` los vuelve a aplicar tras regenerar y salta los que ya están;
   - en el reintento se guarda el texto real encontrado;
   - probado en una copia: aplicar, regenerar, reaplicar dos veces (1 aplicado y luego «ya estaban 1»).
6. **`metricas.py`:**
   - el primer `inicio` de una lámina nueva ahora sí anota su fase: por eso se perdió el `inicio` del catálogo en la prueba 6;
   - `fin` sin `inicio` avisa y sugiere la hora (el fin de la fase anterior);
   - `--hora HH:MM` corrige una marca olvidada.
   - Probado en una copia; el registro de prueba y el `auditoria-pendiente.md` que creó se borraron (las láminas sin auditoría siguen siendo 4).

**Verificación:**
- validador con 0 errores en las 15 láminas;
- `chequeo_rapido --todas` sin incumplimientos nuevos: siguen los avisos de AKT y Boxer y las regresiones de la culata;
- extractor de NMAX, Boxer y AKT idéntico byte a byte; `esqueleto_v2.py` sin cambios en esta ronda;
- firmas: admision idéntica; en cvt, freno y bomba-freno solo cambian `guiasG`/`marcasG` (los contextos del freno salieron iguales al repetir);
- 15 archivos únicos rearmados;
- SKILL.md de 26.501 a 26.430 caracteres; los detalles del dibujo pasaron a `anexo-formato.md`.

Sin commit.

## Regresión (cómo se valida la skill después de cada cambio)
Nuevo `motor/regresion.py`: decide qué revisar con `git status` y, de eso, solo lo que cambió desde la corrida anterior (o con los archivos que se le pasen). Detalle en `anexo-autocontrol.md`; una línea en SKILL.md.

| caso | qué revisa | tiempo medido |
|---|---|---|
| siempre | validador de las 15 (en paralelo) + extractor y esqueleto de NMAX, Boxer, AKT y Honda byte a byte contra `regresion/ref/` | **5-7 s** |
| cambió una lámina | eso + esa lámina en el navegador (390/1280) | **24 s** |
| cambió el motor | eso + navegador (360/390/1280) y firmas en CVT, culata Honda y la última creada (más las láminas que cambiaron) | **≈ 1-2,5 min** (159 s con 7 láminas, por los cambios de esta ronda) |
| solo catálogo, plantillas o skill | solo «siempre» | **7 s** |
| `--todas --sin-cache` (commit grande) | las 15 en el navegador, 3 anchos | **161 s** (antes ≈ 12 min) |
| `--todas` con caché | solo las láminas que cambiaron desde su último OK | **7 s** si no cambió ninguna |

**Antes** (regresión completa a mano): validador en serie 103 s + extractor 23 s + firmas de 4 láminas 49 s + `chequeo_rapido --todas` 537-661 s ≈ **12 min**.

**Qué lo hizo rápido:**
- validador en 6 procesos a la vez (103 → ≈ 5 s);
- extractor y esqueleto en paralelo y contra referencias guardadas;
- en el navegador, 5 láminas a la vez en un solo Chrome, con el solape en la misma pestaña de 1280: antes era un Chrome más por lámina, 19 s cada uno;
- 390/1280 cuando el motor no cambió;
- caché por lámina: hash de su JSON + arte + página + motor.

**Robustez:**
- con carga, Chrome a veces cierra una pestaña o mide antes de que asienten las letras;
- cada ancho tiene un reintento, el solape otro, y lo que bloquea en paralelo se confirma solo, sin carga;
- en las pruebas salió un falso «etiquetas montadas» en el freno Honda, que solo da limpio, y la confirmación lo descarta;
- las firmas ignoran `guiasG`/`marcasG` (ruido conocido).

`regresion.py --aceptar` guarda referencias nuevas tras un cambio querido. Las de hoy coinciden byte a byte con el extractor original. El estado local (`cache.json`, `estado.json`, `ultimo.md`) queda fuera del repo con un `.gitignore` en `motor/regresion/`. Sin commit.
