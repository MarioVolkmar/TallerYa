# L2 · AKT NKD 125: rueda trasera y transmisión final (fig. F-8)

16-nov-2026 · serie nocturna, lámina 2 de 5 · **sin hermana**.
- Página `motor/nkd-transmision.html` · archivo único `motor/prueba-nkd-transmision.html` (≈ 0,9 MB).
- Figura: **F-8 «Rueda trasera»** (26 números + kit alterno 20A). Trae el kit de arrastre (cadena 428×104, piñón 15 y corona 38), el porta sprocket, los cauchos, los tornillos de la corona, los tensores, el eje y el freno de tambor.
- La tijera, el deslizador, el guardacadena y la cadena suelta van en la **F-14**; la tapa del piñón, en la E-6. Elegí la F-8 porque tiene la corona, los tensores y el kit.
- El piñón se dibuja con la cadena, como parte del kit 20.

## Tiempo
| fase | real | presupuesto |
|---|---|---|
| catálogo + esqueleto | 2 min | 1,5 ⚠ |
| dibujo + contenido | 7 min | 4 ⚠ (+3) |
| verificación (validación + mediciones) | 4 min | 2,5 ⚠ |
| revisión (correcciones) | ≈ 1 min | 1,5 ✓ |
| revisora (en paralelo, no suma) | 2 min | — |
| **total con revisión** | **14 min** (22:18 → 22:32) | 10 |

- **Mediciones completas: 2**, más una `--previa` y un `--solo-solape`.
- La primera medición completa no tuvo bloqueantes, pero dio errores de consola: `v2.grupos.torn` iba como lista de ids. Hubo que repetirla.

## Tokens
- **Creación:** ≈ 98 mil (el contexto pasó de 128 mil a 226 mil).
- **Revisora:** 90,5 mil (una sola, modelo de la sesión).

## Notas
- **Medible:** APRUEBA, promedio 4,88. Criterios: 6 → **5**; 8 → 4,7; 9 → 5,0; 10 → 5,0; 11 → 4,8; 12 → 4,8.
- **A ojo:** 4,5 · 4,5 · 4 · 4,5 · 4 · 4,5.
- **Revisora:** mecánica **4** · UX **4**, por debajo de la base de 4,8.

## Hallazgos
- **13 en total: 4 graves y 9 menores. 12 los aplicó el script; ninguno fue a mano; 1 falso.**
- **El falso:** la «ficha 20A vacía». Venía del esqueleto y yo ya la había quitado al corregir el validador; el resumen que leyó la revisora era anterior.
- **Graves:**
  - falta reajustar el pedal del freno y apretar la tuerca del eje después de tensar la cadena;
  - «leva» se usaba para dos piezas (la 4 y la 5);
  - una cadena de fallas decía «eje torcido» en vez de «cruzado»;
  - la ficha 20A.
- **Después:** acorté a mano 3 textos que la corrección dejó largos (paso del freno 284, paso del eje 288, «Cómo funciona» 5: 228). `--rapido` sin regresiones.
- **Validador final:** 0 errores, 2 avisos aceptados:
  - en «Transparente», las píldoras 18 y 19 casi encima;
  - la marca del grupo «Freno» apunta a piezas ocultas: el freno queda detrás de la rueda.

## Qué falló (con su sección de la skill)
1. **El validador no revisa el formato de `v2.grupos[].torn`** (paso 3b / «Modelo v2» de `anexo-formato.md`). Escribí `torn` como lista de ids y el validador dio 0 errores. Además, con ese `torn` malo se saltaba **todas** las revisiones de grupos: ids inexistentes (`23`, `20` en vez de `23a/b`, `20a/b`), piezas sin grupo, la ficha 20A del kit y «CBS».
   - Solo se vio en la medición, como error de consola. Al arreglar `torn` salieron 6 errores escondidos. Costó una medición completa (+2 min).
2. **Dibujo + contenido +3 min, sin hermana** (paso 3 y «Plan de 10 min»): 15 piezas de arte propio (rueda, llanta, rin, radios, cadena, corona, freno) y 26 fichas desde cero. Sin hermana no alcanzan 4 min.
3. **El esqueleto con figuras de rueda** (paso 2):
   - armó 10 grupos sin sentido mecánico, tomó los cauchos (15) por «arandela» y el kit 20A por grupo propio;
   - creó una ficha para el kit, que el validador rechaza;
   - nada avisa de que «CBS» en el nombre del catálogo choca con el control «la lámina dice CBS».
4. **Paso 9.1:** el resumen de `--informe` quedó viejo después de las correcciones del validador: la revisora vio la ficha 20A ya quitada.
5. **Paso 3, «Cada paso, 250 caracteres»:** las correcciones de la revisora alargan los pasos y el validador solo avisa sobre 300. Tres textos quedaron entre 250 y 330 hasta que los acorté a mano.

## Cambios que propongo (sin aplicar)
- **Validador:**
  - error si `torn` no es lista de objetos `{nombre, corto, ids, cant}`;
  - que un fallo en un grupo no corte las demás revisiones de grupos.
- **`esqueleto_v2.py`:**
  - reconocer los «Kit…» (`Kit Arrast`, `Kit Tornillos`) y no hacerles ficha cuando hay otro kit igual (20/20A);
  - «Jgo Caucho Campana» → caucho, no arandela;
  - agrupar las figuras de rueda por eje / arrastre / freno / rueda.
- **Paso 9:** rehacer `--informe` justo antes de lanzar la revisora, después del último `--rapido` (una línea en la skill).
- **`aplicar_hallazgos.py`:** avisar si un reemplazo deja el campo sobre 250 caracteres (pasos y «Cómo funciona»).
- **Presupuesto sin hermana:** dibujo + contenido 6 min, o meta de 12 min para láminas sin hermana.
- **Nota:** `prueba-nkd-transmision.html` se rearmó después de las últimas correcciones. El script de armado (`armar_nkd-transmision.py`) no tiene los 3 textos acortados a mano: si se regenera, `--reaplicar` repone los 12 hallazgos, pero hay que volver a acortar esos 3.
