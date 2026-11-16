# Revisión UX: fig. 11 «Tapa de la transmisión y filtro de la correa» (`motor/tapa-transmision.html`)

Revisora UX · 16-nov-2026 (07:45–07:49). La medí con `medir_lamina.py` en los 6 anchos (rúbrica v3) y la revisé a ojo con dos capturas: la vista general a 1280 y el grupo «Tapa exterior» con la hoja a 390.

## Veredicto: aprueba
| Medible (6 · 8 · 9 · 10 · 11 · 12) | A ojo (1 · 2 · 3 · 4 · 5 · 7) | **Total** | Bloqueantes |
|---|---|---|---|
| 4,5 · 4,7 · 5 · 5 · 4,8 · 4,8 = **4,80** | 5 · 4,5 · 5 · 4 · 4 · **4** | **4,61** | ninguno |

Lo medible coincide con lo que mide piloto-esquema (4,8). La diferencia está en mi ojo: pongo **4 en consistencia (criterio 7)** en vez de 4,5. Las tapas son siluetas aproximadas, oscuras sobre el fondo oscuro, con poco detalle. En la vista general se ven como una mancha negra grande: se entiende qué es cada grupo por las píldoras, no por el dibujo. Las otras láminas tienen más volumen y brillo, y en ellas el dibujo explica solo.

## Medidas
- 4 grupos (Tapa exterior, Espumas, Filtro, Tapa), sin selector de lado. Las marcas miden 45 px, sin fallas ni solapes.
- El dibujo se ve completo en los 6 anchos (236 px a 360 y 469 px a 1280). Al entrar a un grupo, «Desarmar» queda a la vista; el desarme dura 3,9 s como máximo. Los textos de apoyo ocupan del 9 al 15 % de la pantalla.
- La hoja inferior ocupa el 12 % de la pantalla, con nombre y botón de cerrar, sin tapar la pieza.
- 18 de las 19 piezas tienen 24 px o más a 360. La 6 queda en 22 px, y con el grupo armado su borde no responde (sí responde desarmada).
- «¿Se repara?» está a 0,42 pantallas del inicio de la ficha y «Pedir», a 0,77.
- No hay desborde ni errores de consola. El 3D abre en el filtro de la correa (único con 3D, de acuerdo con la regla).

**Corrección del medidor:** en la primera pasada no encontraba el 3D. Al elegir una pieza, la lista se vuelve a dibujar y los botones que el medidor tenía guardados quedaban sueltos. Ahora busca cada botón por su clave. En las láminas anteriores no se notaba, porque la primera pieza de la lista ya tenía 3D.

## Qué corregir (nada bloquea)
1. **Legibilidad del dibujo** (sube el criterio 7 a 4,5):
   - dar un poco de luz a las tapas: borde claro, un reflejo o el color de la otra tapa de aluminio;
   - dibujar algún detalle reconocible: tornillos marcados, la rejilla, el logo en relieve;
   - el objetivo es que la tapa exterior (plástico negro) y la de aluminio se distingan sin leer las píldoras.
2. **Pieza 6:** subirla de 22 a 24 px y, con la tapa armada, que no asome o que su borde responda.
3. **Espumas antirruido (10 piezas genéricas, 16 a 23):** como son placas casi iguales, conviene que la ficha diga dónde va cada una («la de la tapa, arriba del variador») para que el motero sepa cuál pide. Se puede revisar con mecánica si conviene agruparlas en «Juego de espumas» cuando se venden juntas.
4. **Título a 1280:** «Tapa de la transmisión y filtro de la correa» empuja las pestañas a una segunda fila. No es grave, porque el dibujo queda entero, pero un título más corto en la barra del visor (por ejemplo, «Tapa y filtro de la correa») ahorra 50 px.
