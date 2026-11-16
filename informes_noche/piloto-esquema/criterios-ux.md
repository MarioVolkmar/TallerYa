# Criterios UX del esquema (rúbrica v3, modelo por grupos)

Rúbrica para calificar las láminas del esquema y su integración en TallerYa. Desde el 16-nov-2026 el estándar es el **modelo v2 por grupos**, aprobado por el usuario:
- marcas de grupo con nombre;
- piezas que se tocan directo;
- tornillería en píldoras;
- lista plegable con buscador;
- hoja inferior en el celular.

La v3 de la rúbrica adapta la v2 a ese modelo. Las reglas del modelo viejo, con números sobre el despiece, quedan en el anexo.

Son 12 criterios, cada uno de 1 a 5. Los que se pueden medir los mide `motor/medir_lamina.py` (ver «Medición automática») en estos anchos: 360×740, 390×844, 768×1024, 1024×768, 1280×800 y 1440×900.

**Cómo leer las tablas:** los umbrales incluyen el valor del borde (≥ y ≤ son inclusivos). Un valor entre la columna 3 y la de bloqueante vale **2**. La nota de un criterio es el promedio de sus medidas.

**Para aprobar:** promedio de 4 o más, **ningún criterio por debajo de 4** y ningún bloqueante. Un criterio con una medida en «bloqueante» deja la versión sin aprobar, aunque el promedio dé.

## Criterios 1 a 7
Se califican como en `revision-ux.md`, a ojo, salvo las medidas que siguen. El script las imprime como «subnota» para que la revisión las use.

### 1. Claridad del recorrido: medida de toques hasta la ficha
| Medida | 5 | 4 | 3 |
|---|---|---|---|
| Toques desde la vista general hasta ver el contenido de la ficha de una pieza visible (marca → pieza [→ abrir la hoja]) | ≤ 2 | 3 | ≥ 4, o no se llega |
| Pieza de adentro (hay que desarmar el grupo) | ≤ 3 toques y desarme de ≤ 5 s | 1 toque más | desarme largo (> 5 s) |

### 3. Carga cognitiva: medida del largo de la ficha a 360
| Medida | 5 | 4 | 3 |
|---|---|---|---|
| Distancia del inicio de la ficha a «¿Se repara o se cambia?» a 360×740, en pantallas (alto de la ventana) | ≤ 1,5 | ≤ 2,5 | > 2,5 |

Se mide por posición en pantalla, porque el orden puede venir del CSS. El script también da la distancia a «Pedir repuesto», como referencia.

### 6. Uso con el pulgar (modelo por grupos)
| Medida | 5 | 4 | 3 | Bloqueante |
|---|---|---|---|---|
| Marcas de grupo y píldoras de tornillería: toque al centro y a ±9 px, sin solapes y dentro del lienzo, en los 6 anchos | todo bien | — | alguna falla | una marca que tapa a otra, o controles encima del dibujo |
| Alto del área de toque de las marcas | ≥ 44 px en los 6 anchos | — | < 44 px en algún ancho (el script la deja en 4 como máximo) | — |
| Piezas (sin tornillería), en la vista de grupo armada o desarmada: % con área tocable de ≥ 24 px de diámetro a 360 | 100 % | ≥ 75 % | ≥ 50 % | — |
| Piezas sin área tocable en el dibujo | ninguna | alguna, pero está en la lista | — | alguna que tampoco está en la lista |
| Botones de 44 px como mínimo, en la pestaña Piezas y en la hoja inferior | todos | — | alguno más chico | — |

- El **área tocable** es la parte de la silueta que de verdad recibe el toque: se muestrea con `elementFromPoint`, se descuenta lo que tapan otras piezas o marcas y se pasa a diámetro equivalente.
- Las piezas de tornillería se tocan por su píldora, no por su silueta.
- En el modo «Números» rige la regla de densidad del anexo.

## Criterios 8 a 12 (distribución)

### 8. Protagonismo del dibujo
El dibujo es lo que se viene a ver: tiene que llevarse el espacio.

| Medida | 5 | 4 | 3 | Bloqueante |
|---|---|---|---|---|
| Ancho del dibujo / ancho del contenido (≥ 1024 px) | ≥ 55 % | ≥ 50 % | ≥ 40 % | < 35 % |
| Alto del dibujo a 1280×800 | ≥ 460 px | ≥ 420 px | ≥ 360 px | < 300 px |
| Alto del dibujo a 360 px | ≥ 260 px | ≥ 235 px | ≥ 210 px | < 190 px |

### 9. Primer pantallazo
Lo que se ve al llegar, sin bajar.

| Medida | 5 | 4 | 3 | Bloqueante |
|---|---|---|---|---|
| A 1280×800 y 1024×768: dibujo completo y selector de lado a la vista en la vista general, y **«Desarmar» a la vista al entrar a un grupo** | todo, en los dos anchos | todo a 1280 y el dibujo a 1024 | solo el dibujo | el dibujo cortado a 1280 |
| Pestañas y dibujo completo a 390×844 | sí, y «Desarmar» a la vista al entrar a un grupo | sí | el dibujo cortado < 15 % | cortado ≥ 15 % |
| Alto que se llevan los textos de apoyo (aviso, migas, título, catálogo), en % del alto de la ventana, a 1280×800 y 390×844 (cuenta el peor) | ≤ 15 % | ≤ 20 % | ≤ 30 % | > 35 % |

### 10. Espacio muerto
Ninguna columna tiene que quedar estirada y vacía al lado de otra más larga.

| Medida | 5 | 4 | 3 | Bloqueante |
|---|---|---|---|---|
| Hueco bajo el contenido de cada columna, sobre el alto de la fila del despiece (≥ 1024 px). Una columna fija (`sticky`) que cabe en la pantalla cuenta 0 % | ≤ 10 % | ≤ 20 % | ≤ 35 % | > 50 % |
| Ficha sin pieza elegida (estado vacío) | dice algo útil: el estado del sistema, qué hacer, o **la lista con buscador** | solo instrucciones, pero ocupa poco | un párrafo solo en una columna alta | — |
| Navegación secundaria (sistemas) más ancha que la ficha | no | — | sí | — |

### 11. Proximidad entre el control y su efecto
Lo que se toca y lo que cambia van juntos.

| Medida | 5 | 4 | 3 | Bloqueante |
|---|---|---|---|---|
| En computador, la ficha visible justo después de tocar una pieza | sí, sin bajar ni subir | sí, pero con un desplazamiento corto | no | — |
| En celular, **hoja inferior** (o barra fija) al elegir una pieza | aparece con el nombre de la pieza, ocupa ≤ 50 % de la pantalla al abrirse y tapa ≤ 20 % de la pieza elegida | aparece, pero tapa más del 20 % de la pieza o pasa del 50 % | nada | — |
| Controles del dibujo (lado, volver, desarmar, pasos, números) | en una fila pegada al dibujo | en dos filas pegadas | tres o más filas, o separados por texto | encima del dibujo |

**Cómo se mide la hoja inferior** (a 360, 390 y 768, después de tocar una pieza dentro de un grupo):
- Es el elemento fijo (`position: fixed` o `sticky`) más grande que queda pegado abajo: su borde inferior a ≤ 24 px del borde de la ventana, con ≥ 85 % del ancho y ≥ 40 px de alto.
- **Alto al abrirse:** en % del alto de la ventana.
- **Tapa la pieza:** % del área de la silueta elegida que queda bajo la hoja.
- **Nombre:** si muestra el nombre de la pieza elegida.
- **Contenido:** si ya muestra secciones de la ficha (`h4`). Si no, el script busca su botón («Ver ficha», «Abrir», «Más», «Subir»), lo toca y cuenta un toque más hasta ver la ficha (criterio 1).
- **Botones:** de 44 px como mínimo. También anota si tiene botón de cerrar y si su contenido se desplaza adentro.

### 12. Ritmo, alineación y adaptación
Una sola rejilla en todos los anchos.

| Medida | 5 | 4 | 3 | Bloqueante |
|---|---|---|---|---|
| Bordes superiores de las columnas | alineados (± 2 px) | ± 8 px | desalineados | — |
| Columna más angosta en cualquier ancho | ≥ 300 px | ≥ 280 px | ≥ 240 px | < 220 px, o tres columnas a menos de 1200 px |
| Desborde horizontal (`scrollWidth`) | ninguno en los 6 anchos | — | — | alguno |
| Espaciados | de la escala del sitio (8 / 12 / 16 / 24 px) | casi todos | mezclados | — |

## Mínimo de «Cómo funciona» (requisito para aprobar)
Una lámina aprueba solo si su «Cómo funciona» cumple estas 6 condiciones. La referencia es el de la CVT: corte, piezas reconocibles e indicador de rpm. Se agregó el 16-nov-2026, a partir de `revision-como-funciona.md`.

| # | Condición | Cómo se revisa | Si no cumple |
|---|---|---|---|
| 1 | **Piezas reconocibles:** al menos 3 piezas de la lámina dibujadas con su forma y color, no cajas, triángulos ni círculos genéricos | a ojo. El script **alerta** si el esquema tiene menos de 30 formas y menos de 3 degradados | no aprueba (a ojo) |
| 2 | **Lo de adentro:** al menos un corte o transparencia de la pieza donde pasa la acción | a ojo | no aprueba (a ojo) |
| 3 | **Causa → efecto:** cada paso cambia algo visible que corresponde a su texto (se mueve, fluye o cambia de color) | script: elementos del esquema que cambian por paso. **0 o 1 = bloqueante**; 2 = aviso. Que corresponda al texto se revisa a ojo | bloqueante |
| 4 | **Indicador físico** cuando aplica (rpm, presión, flujo, °C, nivel en L, %), con un número que cambie entre pasos | script: busca el indicador en las etiquetas. Si no hay, **alerta**; si no aplica, se declara `funciona.sinIndicador: true` en el JSON | alerta (a ojo decide) |
| 5 | **Etiquetas:** sin montarse y con letra de **12 px o más a 360 y a 1280** | script: cajas de `<text>` del esquema que se cruzan, y letra mínima en pantalla en los dos anchos | bloqueante |
| 6 | **Texto del paso:** 250 caracteres como máximo. Los avisos de seguridad y los pasos de cierre nunca se acortan: lo que sobra va a la ficha | script: largo máximo del texto del paso | bloqueante |

`medir_lamina.py` lo imprime en una línea («Cómo funciona: … → mínimo CUMPLE / NO CUMPLE»). Las condiciones 3, 5 y 6 entran en los bloqueantes; la 1 y la 4 salen como alertas en la lista de lo que falla.

## Cómo dejar la evidencia
Por cada versión: la salida de `medir_lamina.py` (o su `--json`), la nota que resulta y lo propio de la lámina revisado a ojo. Una sola captura final como prueba.

## Medición automática (`motor/medir_lamina.py`)
Un solo comando por lámina:

    venv/Scripts/python.exe informes_noche/piloto-esquema/motor/medir_lamina.py informes_noche/piloto-esquema/motor/<lamina>.html --ojo 5,4.5,5,4,4,4.5 [--captura ruta.jpg] [--json] [--modelo auto|v2|v1]

- **`--ojo`:** son las notas a ojo de los criterios 1, 2, 3, 4, 5 y 7, en ese orden. Con ellas el script da el promedio de los 12 y dice si aprueba.
- **`--modelo auto`** (por omisión) detecta el modelo: si hay marcas de grupo, mide el v2; si hay números, el viejo. `medir_lamina_v2.py` queda como atajo de `--modelo v2`.
- **Cómo corre:** abre la lámina en Chrome sin ventana (DevTools, sin librerías extra) en los 6 anchos a la vez, cada uno en su ventana con el viewport exacto. Mientras mide apaga las transiciones y usa un reloj fijo para las animaciones. Tarda de 1 a 2,5 min.

| Criterio | Lo cubre el script (modelo v2) | Sigue a ojo |
|---|---|---|
| 1 Claridad | toques hasta la ficha y espera del desarme (subnota) | el resto |
| 2 Descubribilidad · 7 Consistencia | — | todo |
| 3 Carga cognitiva | largo de la ficha a 360 (subnota) | el resto |
| 4 Accesibilidad | botones de 44 px en todas las pestañas y en la hoja inferior | orden de foco, foco al entrar a un grupo, textos de `aria-*`, contraste |
| 5 Rendimiento | errores de consola y recursos que no cargan; visor 3D (a 1280) | peso (mirar los archivos) |
| 6 Uso con el pulgar | marcas y tornillería (centro, ±9 px, solapes, dentro del lienzo, alto), área tocable de cada pieza en su grupo (armado y desarmado), que tocarla la seleccione, botones de 44 px | que el pellizco y el arrastre se sientan bien |
| 8 Protagonismo · 9 Primer pantallazo | todas las medidas | — |
| 10 Espacio muerto | hueco bajo las columnas; ficha vacía (5 si muestra la lista, el buscador o qué hacer) | si el texto es útil de verdad |
| 11 Proximidad | ficha a la vista al tocar (1280), hoja inferior (360, 390, 768), filas de controles | — |
| 12 Ritmo | bordes superiores, columna mínima, desborde | espaciados (el script pone 4) |
| Mínimo de «Cómo funciona» | etiquetas montadas, letra ≥ 12 px a 360 y 1280, cambios por paso, largo del texto (bloqueantes); indicador y detalle (alertas) | piezas reconocibles, corte, que la animación explique la causa |

Lo propio de cada lámina se revisa aparte, a ojo: fidelidad del dibujo, si «Cómo funciona» se entiende, textos de las fichas y nombres de los grupos.

## Anexo: modelo viejo (números sobre el despiece, `--modelo v1`)
- **Criterio 6:** toques al centro y a ±9 px de cada número, en armado y despiece, con Normal y Transparente; controles sobre números; radio mínimo; lista deslizable o en rejilla.
- **Criterio 9:** «Desarmar» a la vista al llegar, en lugar de al entrar a un grupo.
- **Criterio 11:** barra fija «Ver ficha» en el celular.
- **Regla de densidad de números a 360** (también para el modo «Números» del v2):
  - **Siempre:** 0 números sin su toque, 0 roces a ±9 px y **≥ 19 px** entre números.
  - **Con 20 números o menos:** ≥ 24 px sin zoom.
  - **Con más de 20:** ≥ 24 px con el primer zoom (×1,6), con el zoom a la vista y la lista de piezas en rejilla.
