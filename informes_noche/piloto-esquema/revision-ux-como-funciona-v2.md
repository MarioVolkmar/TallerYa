# Revisión de «Cómo funciona» v2 y de los ajustes del motor pedidos por el usuario

Revisora UX · 16-nov-2026 (11:15–11:47). Volví a calificar los «Cómo funciona» como en `revision-como-funciona.md`. Usé tres fuentes:
- `medir_lamina.py` con el mínimo nuevo, en las 6 láminas rehechas o acortadas;
- una auditoría de las 9 a 390 y 1280, con mosaico;
- revisión a ojo.

Comprobé los ajustes del motor de `informes_noche/relevos/motor-pedidos-usuario.md` en un Chrome propio, con cursor real para el hover.

**Sobre requestAnimationFrame:** piloto-esquema tiene razón en que no corre sin ventana. El medidor y la auditoría lo reemplazan por un reloj fijo de 16 ms mientras miden, y esperan a que el dibujo quede quieto en cada paso. La correa de la CVT llega al final de cada paso (de 7 a 18 cambios medidos).

## Notas de «Cómo funciona» (antes → ahora)
| Lámina | Antes | **Ahora** | Mínimo medible | Qué cambió |
|---|---|---|---|---|
| Fig. 8 admisión | 2 | **4,8** | CUMPLE | caja con filtro plisado en corte, mariposa (también de frente), inyector reconocible, cilindro. Panel «lo que mide el computador» con acelerador, aire y gasolina en % y rpm. 85 formas, 22 degradados, de 4 a 22 cambios por paso |
| Fig. 10 cárter | 2 | **4,7** | CUMPLE | cárter en corte con engranajes; la varilla de cerca con mín./máx.; niveles de 0,90 L y 0,10 L; retén del eje en corte. 54 formas, 24 degradados |
| Fig. 7 aceite | 2,5 | **4,8** | CUMPLE | recorrido del aceite en corte con levas, pistón y cigüeñal; bomba en corte; presión en bar; tamiz y aceite que se oscurece con los km. 76 formas |
| Fig. 11 tapa | 2,5 | **4,7** | CUMPLE | la caja de la correa en corte con el aire entrando y saliendo; °C de la correa; aire en %; filtro de espuma de cerca. 108 formas |
| Fig. 1 culata | 3,5 | **4,8** | CUMPLE | cilindro en corte con válvulas, levas y bujía; barra del ángulo del cigüeñal (adm., comp., fuerza, esc.); la bujía de cerca con su separación. De 10 a 12 cambios por paso |
| Fig. 26 bombas | 4,9 | **4,7** | CUMPLE (paso máximo de 249 caracteres) | igual de bien, pero la etiqueta **«Manguera» sigue tapada por el cáliper** (se lee «Mangu…»). Sin indicador: podría mostrar la presión |
| Fig. 22 freno | 4,8 | **4,3** | **NO CUMPLE** | **a 390, «Pastillas» se monta sobre «Rueda»** (desde que la letra creció); un paso de **397 caracteres**; el paso 4 cambia **1** elemento |
| Fig. 24 freno trasero | 4,8 | **4,3** | **NO CUMPLE** | igual que la fig. 22. Ya dice «Puño izquierdo» (corregido) |
| Fig. 12 CVT | 5 | **4,8** | **NO CUMPLE** | un paso de **341 caracteres**; todo lo demás es la referencia |

**Las cinco rehechas quedaron al nivel de la CVT:** corte, piezas reconocibles, indicador que cambia y animación que explica. Además, letra de 14 px a 360 y de 12,1 px a 1280, sin etiquetas montadas.

## Los ajustes del motor: confirmados los 10
| # | Pedido | Resultado |
|---|---|---|
| 1 | Enlaces `[[ ]]` renderizados en todos los textos | ✓ no queda marcado crudo en ninguna pestaña (fig. 26, 7 y 1) |
| 2 | «Números» sin choques con las píldoras | ✓ 0 números tapados por una píldora (fig. 26: 14 números; fig. 7: 3; fig. 1: 5) |
| 3 | Relacionadas en rejilla | ✓ chips del mismo alto (36 px en computador y 44 en el celular) y del mismo ancho, con el nombre completo en `title`/`aria-label` |
| 4 | Fuentes como chip discreto | ✓ «Fuentes» con ícono, 82 × 44 px de toque |
| 5 | «Desarmar todo» en la vista general | ✓ desarma todo el sistema (fig. 26: 24 piezas; fig. 1: 28; fig. 7: 6), con ◀ ▶, y al armar vuelve a 0 |
| 6 | Encuadre de la vista general ceñido (fig. 7) | ✓ las piezas ocupan el 78 % del encuadre |
| 7 | Navegación fina de la ficha | ✓ versalitas de 12,5 px y 44 px de toque invisible; «anterior» desactivado al 30 % |
| 8 | Elegir una pieza desde «Cómo funciona» cambia a «Piezas» | ✓ tocar «bujía» (fig. 1) o «varilla» (fig. 10) cambia a «Piezas» y deja la pieza elegida con su ficha |
| 9 | Píldora que se alarga con el cursor | ✓ con cursor real: «Tapa» → «Tapa de la culata» (de 46 a 121 px), «Aceite motor» → «Aceite del motor», sin viñeta aparte |
| 10 | Tornillería con guía, más chica y semitransparente | ✓ píldoras de 16-17 px de alto con fondo al 55 %, que no tapan el dibujo; líneas guía en los grupos donde la píldora quedó apartada (culata: 5, 3 y 2) |
| 11 | Guía de la píldora de grupo a su capa (fig. 1) | ✓ 1 guía en la vista general de la fig. 1 (y 3 en la fig. 10) |
| — | Letra de 12 px en «Cómo funciona» | ✓ 12,1 px a 1280 y de 14 a 15,7 px a 360 en las 9 |

## Medición completa de las 6 (rúbrica v3)
| Lámina | Medible | Bloqueantes | Avisos |
|---|---|---|---|
| Fig. 8 admisión | 4,88 | ninguno | enlaces dentro del texto de 25 px de alto («inyector», «mariposa»): están bien como enlaces de renglón (excepción de WCAG para texto en línea) |
| Fig. 10 cárter | 4,88 | ninguno | bordes de 10 y 30 con el grupo armado |
| Fig. 7 aceite | 4,72 | ninguno | marcas de grupo de 43 px (< 44) en algún ancho |
| Fig. 11 tapa | 4,88 | ninguno | enlaces de renglón de 25 px |
| Fig. 1 culata | 4,88 | ninguno | — |
| Fig. 26 bombas | 4,88 | ninguno | «Cómo funciona» sin indicador (alerta) |

## Qué corregir
1. **Freno delantero y trasero (fig. 22 y 24):**
   - separar «Pastillas» de «Rueda» a 390;
   - acortar el paso de 397 caracteres a 250 o menos, sin tocar los avisos ni el cierre;
   - que el paso 4 muestre un cambio visible (hoy cambia 1 elemento).
2. **CVT:** acortar el paso de 341 caracteres.
3. **Fig. 26:** sacar «Manguera» de debajo del cáliper. Opcional: indicador de presión en «Cómo funciona».
4. **Fig. 7:** marcas de grupo a 44 px en todos los anchos.
5. **Medidor:** la espera por omisión pasa de 300 a 480 s, porque la fig. 26 (9 grupos más «Cómo funciona») se cortaba con la máquina cargada.
