# Velocidad: mejoras aplicadas — 19-nov-2026 (tarde)

Se aplicaron las mejoras 1-5 de `skill-optimizar-velocidad.md` con la skill `optimizar-velocidad`. Sin commit.
Mediciones con `medir_chrome.py` (Chrome sin ventana, que cuenta como pestaña visible), en el servidor `tallerya-medir` (8024, sin autorrecarga).
Los datos crudos están en el scratchpad de la sesión.

**Aviso sobre el ruido:** mientras se medía, la máquina estaba muy cargada por otras sesiones. El perfil 375/4G (CPU ×4) es el que
más lo sufre: el freno de CPU multiplica la competencia por el procesador. Hubo corridas con un FCP de 8 s y una carga tibia con un FCP de 35 s.
Las cifras de 1366 y de 375 sin freno son las más confiables. Para no confundir ruido con regresiones, cada cambio se
comprobó también con un perfil de CPU o una traza, que muestran qué función hace el trabajo y no dependen del ruido, y con un A/B intercalado.

## Cambios

1. **`personalizar.js`: el cajón se arma solo cuando hace falta.** El perfil de CPU mostró que al recibir `moto3d-listo`,
   `pintarCatalogo` → `TallerYa3D.miniatura` → `canvas.toDataURL` se llevaba **10,3 s (×4)**: las miniaturas de calcas
   esperaban a la tarjeta gráfica, que en ese momento compila el 3D. Ahora `iniciar()` solo conecta el 3D y muestra el botón.
   Las filas de color, el catálogo y las calcas de fábrica se arman al acercarse al botón (pointerenter, focus, touchstart),
   al abrir el cajón, al tocar una calca del 3D, o en reposo (`requestIdleCallback`, 3 s después del 3D). Los colores guardados los
   sigue pintando el visor desde el principio: comprobado a 375 px, el color de la pintura del 3D coincide con el guardado y el cajón abre con
   sus 107 botones, 8 calcas y 3 calcas de fábrica. Después del cambio, `personalizar.js` no aparece en el perfil de la carga.
2. **`moto3d.js`: `compileAsync` sí espera a la GPU.** Había dos causas:
   - `compileAsync` **fallaba en silencio**. `aplicarPersonalizacion` les ponía material a los *grupos* del aro del rin
     (`o.userData.aro` en un `Group`), y three.js revienta (`morphAttributes` de undefined) al compilar un objeto con material
     y sin geometría. Por eso las variantes de las sombras se compilaban de golpe al dibujar (las `GPUTask` largas). Ahora el
     material solo se pone en mallas, y en la pantalla se ve igual (three.js no dibuja el material de un grupo).
   - Los colores y calcas guardados se aplicaban **mientras** la GPU compilaba, y metían variantes nuevas a mitad de la espera.
     Ahora se esperan (`personalizada`, con un tope de 3 s) antes de `compileAsync`, así que nada corre ni dibuja durante la compilación.
   - Además: `renderer.debug.checkShaderErrors = false` (con `?depurar3d` vuelve a revisar), para ahorrar consultas síncronas por programa.
   - Ya había pocas variantes de material: 3 programas físicos antes de las sombras y 15 en total. Las sombras ya iban después del
     primer cuadro, y el arreglo de `compileAsync` hace que su compilación en segundo plano funcione de verdad. **No** se cambió
     el tipo de sombra (PCFSoft), porque se vería distinto. `?modelo3d=glb` sigue funcionando: el GLB carga (`raiz.userData.glb`), `compileAsync` termina y las sombras llegan (1366: listo 11,4 s).
   - Se agregó la marca `personalizado` a `__visor.info().tiempos`.
3. **El 3D arranca después de que se pinta el esquema** (`moto3d-carga.js`). Espera `#despiece.despiece-listo` (o
   `despiece-fallo`), con un tope de 2,5 s, y arranca en el cuadro siguiente. La descarga del módulo sigue adelantada (modulepreload).
   El visor ya cargaba por IntersectionObserver, pero en la ficha está arriba, así que eso no ayudaba. En un A/B intercalado en 375/4G,
   la versión con espera dio esquema 7,2 s y 3D 13,3 s, contra 11,5 y 15,2 sin espera. En la otra pareja de corridas ambas salieron
   en 20-23 s de esquema y unos 39 s de 3D, por la carga de la máquina.
4. **CSS.**
   - **El Layout de 3 s de la portada no viene de reglas caras.** Un relayout completo a 375 px y ×4 tarda **45 ms**, y apagar
     hoja por hoja no cambia casi nada. La tarea larga es el *primer* layout (lo dispara `controles.js` al evaluarse, y igual
     ocurriría antes del primer pintado), más un relayout cada vez que llega una fuente web. Lo más caro de la portada en GPU son
     las animaciones del SVG de la escena (`pm-*`, con `filter: brightness()` sobre `g.pm-moto` y `filter:url(#pm-difuso)`), y
     `backdrop-filter: blur(8px)` en el encabezado y la barra inferior. Esos archivos son de la sesión de la portada: quedan en Pendientes.
     `:has()` solo pesa en el recálculo de estilos (0,1-0,15 s).
   - **Fuentes:** Google Fonts pasó a rangos variables (`Archivo:wght@400..700`, `Oswald:wght@500..700`). Ahora bajan **2 archivos
     en vez de 6-7**, todos los pesos se siguen usando y hay menos relayouts por fuente. Diferencia medida: 0,09 px en un margen del foro.
   - **`tallerya.css` partido en base y secciones.** La base sigue en `tallerya.css`, y en `talleres/css/secciones/` quedaron
     `garaje`, `talleres`, `cuentas`, `foro`, `cupones` y `tramites`. Se cargan con `{% css_seccion %}` (nuevo
     `talleres/templatetags/css_seccion.py`) entre `tallerya.css` y `tw.css`, según la plantilla raíz de la vista
     (`garaje/moto.html` → garaje.css). El reparto lo hizo un script que cruza cada regla con las plantillas y el JS donde se
     usan sus clases (incluye el grafo de include/extends, las secciones de la consola y las clases armadas como
     `fo-grupo-{{ slug }}`). **Las reglas que podían empatar en la cascada** (misma especificidad, misma propiedad y clases que
     pueden ir en el mismo elemento) con una regla de la base posterior **se quedaron en la base** (525 reglas). La primera
     versión sin ese control cambiaba tres cosas (el color de las categorías del foro, el tacómetro y el tamaño de los botones
     de zoom del plano en el celular), y así se detectó el problema.
   - En producción el CSS ya se minificaba al hacer `collectstatic` (`talleres/estaticos.py`). Los KB de abajo son **minificado + brotli**, como en producción.
5. **Sin cambios visuales.** Se tomó una foto de estilos calculados (43 propiedades, caja y `::before`/`::after` de cada
   elemento) en 10 páginas × 2 anchos (portada sin y con sesión, talleres, mecánicos, foro sin y con sesión, garaje, moto 3, Mi ruta y consola),
   dos veces antes, para separar el ruido de las animaciones, y una después. Resultado: **0 diferencias**, salvo los 0,09 px de la
   fuente variable en el foro. `revisar_ux.js` a 1280 y 375 en las 8 páginas: sin scroll horizontal y sin hallazgos nuevos.
   Como los estilos calculados son idénticos, los hallazgos son los mismos que ya había: toques < 44 px, contraste y otros de
   antes. Una captura final a 375 px con el 3D, el esquema y Personalizar abiertos.
6. **Pruebas:** suite completa con las lentas (despiece y diagnóstico): **826 OK** en 105 s. Hay una prueba nueva, `talleres/tests_css_seccion.py`.

## Antes → después contra el presupuesto

Carga fría. Valores en s, o mediana de 2 corridas (5 en 375/4G después; la moto «antes» tiene 1 corrida por perfil). «—» = la medición no
registró el valor (LCP o FCP vacío). Presupuesto (meta / tope): FCP 1,8 / 3 · LCP 2,5 / 4 · esquema 3 / 6 · 3D 4 / 8 sin freno y 12 / 20 con ×4 ·
tarea larga 0,5 / 1 · CSS 40 / 60 KB.

| Página | Perfil | FCP | LCP | Esquema | 3D listo | Tarea larga máx. | CSS br (prod.) |
|---|---|---|---|---|---|---|---|
| Portada | 1366 | 1,46 → 1,39 ✓ | 1,46 → 1,39 ✓ | | | 0,51 → 0,45 ✓ | 64,3 → **52,9** ✓ tope |
| Portada | 375 | 2,50 → **1,06** ✓ | 2,50 → **1,45** ✓ | | | 0,45 → 0,63 | |
| Portada | 375/4G | 3,45 → 4,45 ✗ ⁱ | 3,45 → 4,45 ✗ ⁱ | | | **6,33 → 1,77** ✗ | |
| Talleres | 1366 | 2,29 → — | 2,29 → — | | | 0,33 → 0,15 ✓ | 61,9 → **50,6** ✓ tope |
| Talleres | 375 | 1,68 → — | 1,72 → — | | | 0,31 → 0,16 ✓ | |
| Talleres | 375/4G | 3,37 → 4,00 ✗ ⁱ | 4,14 → 4,00 | | | 0,41 → 0,74 | |
| Mecánicos | 1366 | — | — | | | 0,17 → 0,16 ✓ | 65,1 → **48,6** ✓ tope |
| Mecánicos | 375 | — → 1,36 ✓ | — → 1,36 ✓ | | | 0,27 → 0,21 ✓ | |
| Mecánicos | 375/4G | 3,74 → **2,83** ✓ tope | 4,16 → **2,83** ✓ tope | | | 0,62 → 3,73 ✗ ⁱ | |
| Moto 3 | 1366 | 3,62 → **1,82** | 9,94 → **6,15** | 5,61 → **2,50** ✓ | 10,94 → **6,79** ✓ tope | **2,67 → 1,23** | 64,7 → **59,2** ✓ tope |
| Moto 3 | 375 | 2,44 → 2,09 | 2,91 → 2,62 | 4,96 → 4,46 ✓ tope | 7,79 → 7,97 ✓ tope | 1,77 → 1,74 | |
| Moto 3 | 375/4G | 3,41 → 4,55 ⁱ | 3,86 → 23,7 ⁱ | 8,73 → 22,8 ⁱ | 13,96 → 45,1 ⁱ | 2,38 → 3,16 ⁱ | |

ⁱ Corridas muy contaminadas por la carga de la máquina, con mucha dispersión entre corridas iguales. En la moto, la mejor corrida «después» dio
FCP 4,05 · esquema 7,5 · 3D 12,1 · tarea larga 1,65. El A/B del paso 3 muestra que la versión anterior también llegaba a 23 s de esquema en esas condiciones.
Este perfil **hay que volver a medirlo con la máquina libre** antes de actualizar su línea base.

**Pasos intermedios, moto 3 en 1366, fría, 2 corridas cada uno:**

| Paso | 3D listo | Tarea larga máx. |
|---|---|---|
| Base | 10,9 s | 2,67 s |
| Tras el paso 1 | 9,3 / 7,6 s | 0,99 / 1,27 s |
| Tras el paso 2 | 7,0 / 7,5 s | 0,78 / 0,84 s |
| Tras el paso 3 | 6,2 / 7,3 s | 0,72 / 1,04 s; esquema 3,5 / 3,7 s |

**CSS por página, minificado + brotli:**

| Página | Antes | Después |
|---|---|---|
| Foro | 60,1 KB | 46,5 KB |
| Mi ruta | 63,4 KB | 46,8 KB |
| Consola | 61,1 KB | 44,5 KB |

`tallerya.css` pasó de 54 a 38 KB; se le suma la hoja de la sección (garaje 11, talleres 5,2, cuentas 4,2, foro 3,0, tramites 2,0 y cupones 1,9 KB).
**Todas las páginas medidas quedan por debajo de 60 KB.** El garaje queda al límite (59,2 KB) porque también carga `dm.css`, `cotizador.css`,
`fallas.css` y `chispa-chat.css`.

## Archivos tocados
`garaje/static/garaje/js/personalizar.js`, `garaje/static/garaje/js/moto3d.js` (4 cambios acotados: orden antes de
`compileAsync`, `checkShaderErrors`, material solo en mallas en el aro y la marca `personalizado`), `garaje/static/garaje/js/moto3d-carga.js`,
`talleres/static/talleres/css/tallerya.css` (partido) y el nuevo `talleres/static/talleres/css/secciones/*.css`, `templates/base.html` (fuentes
y `{% css_seccion %}`), los nuevos `talleres/templatetags/css_seccion.py` y `talleres/tests_css_seccion.py`, una línea del mapa de `CLAUDE.md`, y la línea
base en `.claude/skills/optimizar-velocidad/anexo-presupuesto.md` (más su respaldo). Nota para las otras sesiones en la carpeta compartida
de notas (`velocidad-aplicar-css-partido.md`).

**Para unir con el worktree `moto-3d-alterna`:** los cambios en `moto3d.js` son cuatro bloques pequeños y aislados. El más importante es la
condición `o.isMesh &&` del aro en `aplicarPersonalizacion`: sin ella, `compileAsync` falla.

## Pendientes
- **Volver a medir 375/4G con la máquina libre** (todas las páginas) y actualizar esa línea base.
- **Portada (sesión de la portada):** las animaciones del SVG de la escena con `filter` y el desenfoque `pm-difuso` generan `GPUTask` de 0,4 a 0,6 s cada una.
  Convendría pausarlas fuera de pantalla o pasar el filtro a colores ya calculados.
- **Abrir Personalizar en frío** tarda hasta 7 s (×4) en dibujar el cuadro siguiente, por las esferas de acabados (segundo
  renderizador). Ya era así antes; conviene precalentarlas en reposo con un solo programa.
- **La moto sigue con un layout de 1,5-1,9 s (×4)**, por el DOM grande del despiece. `moto3d-carga.js` fuerza un layout al evaluarse
  (`getBoundingClientRect` del visor durante el análisis del HTML): se podría pasar a `DOMContentLoaded`.
- Mejoras 6-9 del informe original, sin tocar: recortar three.js, `icon-192.png` duplicado, consultas del detalle de la moto y `feDropShadow` del SVG.
