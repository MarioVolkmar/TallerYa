# Auditor 3D — medición final (2026-11-15)
GPU Intel UHD, CPU ~60 %, con sombras listas, ficha (/garaje/1/ y /2/), 25 líneas, accesorios ON (8). Escritorio en orden normal; móvil (375x812, CPU/4) en orden inverso (empieza la Aerox) para no culpar a la primera en frío.

## Presupuesto (mediana / peor)
| | calls | triángulos | programas | cuadro |
|---|---|---|---|---|
| MOTO alta | 45 / 47 (NMAX) | 47.046 / 53.673 (MT-03) | 27 | 3 ms / 5 (RS) |
| RAYOS X alta | 11 / 11 | 18.918 / 20.732 (FZ 25) | – | 2 ms |
| MOTO baja (móvil) | 44 / 46 (NMAX) | 27.248 / 30.668 (RC) | 21 | 16 ms / **72 (Crypton FI), pico 110** |
| RAYOS X baja (móvil) | 8 / 8 | 11.806 / 13.204 | – | 7 ms / 16 |
Calls ≤60, alta ≤60k, baja ≤35k: **cumplen las 25**. (Rayos ≈ 8–11 calls.)

## Primer cuadro (desde la navegación, ficha)
- Escritorio: mediana 2,0 s, rango 1,5–4,8 s; **la 1ª moto en frío (CR4) 10,3 s**. Límite 1,5 s: NO se cumple en la ficha (solo 5 de 25 ≤1,6 s). En la vitrina (vista-3d, medición del 14-11) la mediana era 0,69 s.
- Móvil CPU/4: mediana 8,4 s, mínimo 6,7 s; en frío (Aerox) 15,1 s.
- Cuadro móvil ≤33 ms: cumple en 24/25 (mediana 16 ms); **falla Crypton FI 115 (72 ms, pico 110)**.
- 4G: no repetido (14-11, NKD en vitrina: 5,8 s sin gzip; confirmar en Render).

## Revisión visual / geométrica
- Noche encendida (Duke, MT-03, RC, RS, NMAX; 3 ángulos): faro con cono al frente, stop rojo atrás, direccionales ámbar, calcas visibles. Sin fallos. Las 25: 2 luces (spot+point), 5 emisivos, 6–10 conos/halos.
- Flotantes: 24 de 25 sin; **GN 125: 2 piezas sueltas** (x 0,23–0,33, y 1,16–1,26, z ±0,01–0,09; simétricas, parecen los espejos o las manijas).  Los flotantes (a) y (b) del lote 3 ya no aparecen.
- Translúcidos: 1 por moto (mica del faro); 2 en NMAX y Aerox.
- Estado/Rayos: todas las piezas con mallas salvo `refrigeracion` (Dynamic, Dio; es artefacto de la prueba). SIN CONFIRMAR: en las 25 el chequeo marca 8 piezas "mal color" con material blanco ffffff (cadena, aceite, filtro_aire, freno_del, bujía, llantas, suspensión_del) en modo Estado y Rayos; antes eran 0. Puede ser regresión de las mallas agrupadas o artefacto de la comprobación (lee material[0] de mallas unidas); mirar con captura en modo Estado.
- Llantas que choquen: no hay prueba automática; en capturas 3/4, frente y atrás de 5 motos no se ve cruce.

## Datos crudos
Scratchpad de Auditor: m2-desktop-acc.json, m2-movil-acc.json, rev-desktop.json.
