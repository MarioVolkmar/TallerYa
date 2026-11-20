# Revisión automática de la skill moto-3d-tripo (19-nov-2026)

`scripts/revisar.py S salida.glb --nombre X --fotos "g1;g2" [--ficha fichas/X.py] [--hoja X.jpg]` lee el GLB ya exportado
(coordenadas de la página, +z = derecha del piloto) y saca una hoja JPG y un JSON. ~12 s por moto (antes 25-29 s).
Hojas de las 6 motos en `hojas/`.

## Qué detecta cada chequeo

| Sección | Detecta |
|---|---|
| lado | escape a la derecha, corona/cadena/CVT a la izquierda, lado de cada disco (INFO), `scale.z = -1` en moto3d.js |
| cortes | nodos `_quitar` exportados; bordes abiertos (uno por pieza: los dentro del cilindro de una rueda no pasan de AVISO; ERROR si uno a la vista mide ≥ 40 cm); piezas flotantes a > 1,5 cm; reflejo de piezas de un solo lado sobre otra malla (copia simétrica de Tripo) |
| ruedas | banda centrada en el eje, aro/rin/disco/tambor cubren la vuelta, vértices de pintura dentro de la llanta |
| luces | tamaño máximo por tipo (faro 400 cm² / 24 cm, stop 450 / 30, direccional 180 / 14), faro y stop en su extremo, hacia dónde mira, mira al piso, carcasa por el borde, invade guardabarros/portaplaca/llanta, dónde cae la luz a 8 cm |
| **sitio y pares (nuevo)** | zona por tipo relativa a ejes y manubrio (direccionales del./tras., faro, stop, espejo, reposapiés; `SITIOS` en la ficha la cambia); piezas pares (direccional, espejo, reposapiés, posición) sin su reflejo a < 5 cm → sugiere `m.espejar(...)` |
| pintura | qué piezas cambia cada grupo de Personalizar; < 3 fotos = ERROR |

Velocidad: `hay` y `componentes` vectorizados (sin bucles de Python), render de la hoja a densidad 0,6.

## Qué encontró en cada moto (solo anotado, sin corregir)

- **MT-03** (`?v=5`): todo OK salvo pintura (2 fotos en `FOTOS_MODELADO_TRIPO/yamaha_mt_03`). Direccionales delanteras:
  la izquierda achicada en su sitio (4 × 3 cm) y la derecha espejada; pareja OK.
- **NMAX**: pieza flotante de 41 vértices en `oscuro.horquilla` (0,58, 0,30, 0,12) → ERROR; bordes abiertos dentro de la
  rueda delantera (rin, horquilla, mordaza; AVISO); uno a la vista de 8 cm en `plastico.escudo`.
- **NKD**: `pintura.guardabarros_del` con 127 vértices dentro de la llanta (Personalizar la pinta) y `metal.tambor_tras`
  cubre solo el 28 % de la vuelta → ERROR; `ambar.direccional_tras_b` de 30 cm de ancho y `direccional_tras_a` sin
  pareja simétrica (una de las dos traseras quedó mal cortada); stop toca el guardabarros trasero.
- **Boxer CT 100**: `metal.corona` en z +0,06 (lado del escape) → ERROR de lado; borde abierto de 128 cm a la vista en
  `plastico.guardabarros_del`; pieza flotante de 118 vértices en el chasis (−0,05, 0,31, −0,26); `tambor_del` cubre el
  92 %; faro 26 cm de ancho; la luz de las direccionales delanteras cae sobre la farola.
- **XTZ 150 y XTZ 125**: direccionales traseras miran al piso (normal y −0,94: incluyen la cara de abajo); bordes
  abiertos solo dentro de la rueda delantera.
- Todas: pintura ERROR porque las carpetas de fotos tienen menos de 3 fotos (falta bajar más).

## Ajustes de umbrales tras correr las 6

Bordes agrupados por pieza y degradados dentro de las ruedas (eran ~40 líneas por moto); mordaza fuera de los pares
(con un disco va sola); el aro cromado del faro ya no cuenta como «carcasa más chica» ni como invasión; espejo y
reposapiés con zonas más holgadas (NMAX: espejo en el manubrio trasero, piso alto); tamaños de direccional y stop
según NMAX y NKD reales.
