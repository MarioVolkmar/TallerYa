# Auditoría independiente: 3D de las motos nuevas, las diferenciadas y la carga más rápida (15-11-2026, sin commit)

Auditor 3D. No se corrigió nada. Servidor local en DEBUG (8001), Chrome sin ventana, GPU Intel UHD (D3D11), CPU 10–50 %.
Medido en las **33 líneas** (25 anteriores + 8 nuevas) con el color de fábrica por defecto de cada una. Capturas:
`informes_noche/relevos/auditor-3d-nuevas-perfil.jpg` (las 8 nuevas de perfil) y `auditor-3d-nuevas-noche.jpg` (noche, encendidas: 3/4 delantero arriba, trasero abajo).

## Resumen
- **Ninguna moto incumple una regla dura**: 0 piezas flotantes en las 33, Rayos X y Estado completos (12/12 piezas con malla), llantas sin choques con carrocería, las 33 encienden Spot + Point + stop/faro/direccionales/tablero de noche, calcas solo con nombres de modelo (ningún emblema de marca), sin cono visible de día.
- Presupuesto: ✓ en todo lo medido salvo un punto de móvil (NMAX) y los programas de shader (ver "Para decidir").
- Optimización: ✓ JS del 3D 239 KB gzip (198 KB brotli) ≤ 300 KB; el minificado da lo mismo que el de desarrollo en métricas e imagen.

## Presupuestos medidos
| Medida | Límite | Resultado (33 líneas) |
|---|---|---|
| Triángulos, alta (escritorio) | ≤60k | mediana 40,9k, máx. **47,8k** (MT-03); nuevas 39,0–44,3k |
| Triángulos con los 8 accesorios | ≤60k | mediana 46,5k, máx. **53,6k** (MT-03) |
| Draw calls, alta (`calls2`) | ≤60 (≤75 con accesorios) | 39–45 (máx. NMAX); con accesorios máx. 46 (CR4); nuevas 39–43 |
| Triángulos, calidad baja (móvil emulado) | ≤35k | mediana 24,0k, máx. **27,6k** (RC 200) |
| Draw calls, baja | ≤60 | máx. 44 (NMAX) |
| Primer cuadro, escritorio | ≤1,5 s | mediana 1,39 s; 32 de 33 entre 0,84 y 1,76 s; NKD 3,77 s (es la primera carga en frío de la corrida) |
| Cuadro (mediana de 15), escritorio | — | 2–6 ms |
| Cuadro móvil (4× CPU) | ≤33 ms | casi todas ≤25 ms; **NMAX 35 y 46 ms en dos corridas** (Best 45 → 30 al repetir: ruido) |
| JS del 3D transferido | ≤300 KB | **239 KB gzip / 198 KB br** (three 167/135, construir 25/22, moto3d 17/15, 4 addons 17/14, resto 14/12) |
| Programas de shader (escritorio) | ≤16 en el 1.er cuadro; ~26 totales aceptado | 30–32 totales en alta tras estabilizar; 20–21 en baja |

## Notas sobre la tabla de motos (al final)
1. **Parecidas todavía**: las negras de tanque con franja dorada (CT 100, Discover, CB, GN, Eco, RS, Hunk 150) comparten silueta de tanque, colín y mofle; CT 100 (5) y Discover (6) casi se confunden de perfil. Las 8 nuevas sí se distinguen entre sí por color, máscara, colín y calcas.
2. **Fidelidad a fotos (8 nuevas)**: comparadas con la `_hoja.jpg` de cada `manual_despiece/<moto>/fotos/`. Colores de fábrica, tipo de carrocería (enduro con aletas y máscara; naked con tanque y colín) y calcas corresponden. Es una versión estilizada: no replica detalles finos (tapas blancas de la XR 190L, rin de 5 radios de la Raider, dos luces de posición de la FZ).
3. **RC 200 apagada de noche**: emisivos `ff2a1f×0,69` (stop) y `fff1c4×1,084` (faro) encendidos con la moto apagada; en las otras 32 el único emisivo apagada es el del tablero `2a3a46×0,6`.
4. **Scooters (Dynamic, Dio, NMAX, Aerox)**: apagados dejan un `PointLight×0,9` (también de día) y de noche el emisivo `a855f7×2,2` (neón inferior). Parece intencional, pero es luz con la moto apagada.
5. **NMAX en móvil**: 35 y 46 ms de mediana por cuadro con CPU 4× más lenta (26,3k tri, 44 calls); Raider, por ejemplo, 12 ms con 23,6k tri. No es de las nuevas.
6. `__visor.info().llamadas` queda en 1 hasta que corre un cuadro; se usó `calls2`.

## Flotantes, translúcidos, Rayos X
- Flotantes: las piezas (a) 3×2×3,5 cm `1c2022` y (b) 12×14×12 cm `23282b` del lote anterior **ya no aparecen**: 0 en las 33.
- Translúcidos: solo `a9bec7@0,45` (mica del faro). El cono `fff1d0` ya no está visible de día (ni en ficha ni en vitrina).
- Llantas: control propio (vértices de cualquier malla salvo llantas, frenos y cadena dentro del cilindro de cada llanta, 0,045 m < r < 0,9 R): solo golpean los halos de Estado de la propia llanta; ninguna malla de carrocería, guardafango o subchasis entra. Guardafangos de las enduro visibles y sobre la llanta en las capturas.
- Rayos X / Estado: 12/12 piezas con mallas, sin `sobran` ni piezas internas visibles de más.

## Noche y día
- De noche y encendida, las 33: SpotLight 26 + PointLight 2,4, emisivos faro `fff1c4×11`, stop `ff2a1f×7`, direccionales `ff9a1f×3,2`, tablero `4fd1c5×3`, conos/halos. En las capturas de las 8 nuevas: cono adelante y stop atrás en todas.
- De día (ficha, apagada): 0 SpotLight y 0 PointLight en las 29 no scooter (los 4 scooters tienen su PointLight, nota 4); los emisivos que se ven ahí son los halos de Estado.
- En la vitrina (`vista-3d`) a 1,5 s de cargar hay Spot 2,5 y faro `×2,6` encendidos: es la animación de arranque de la portada; no lo conté como falla (no medí la moto ya quieta).

## Optimización (three.js propio, importmap, modulepreload, minificado)
- `garaje/static/garaje/vendor/three-0.160.0/` + `_importmap_3d.html` (addons con huella y prefijo de respaldo) en ficha y vitrina, sin jsdelivr. `modulepreload` de three, `moto3d.js` y `construir.js` en la ficha, y de todos los módulos en la vitrina, después del importmap.
- `build_js/` está al día (minificado 16:53; fuentes del 3D con fecha 15:43 o anterior). Con `DEBUG=0`, `settings.py` lo pone primero en `STATICFILES_DIRS`.
- **Producción = desarrollo**: serví los archivos de `build_js/` en la página de desarrollo (interceptando `/static/garaje/js/*`; comprobado: `moto3d.js` 49.058 B contra 101.671 B). En 6 motos (CR4, Gixxer, MT-03, XR 190L, Raider, Hunk 150): triángulos, calls, mallas, geometrías y texturas **idénticos**; píxeles distintos (>12/255) 0,9–2,8 % entre desarrollo y minificado, frente a 0–2,6 % entre dos corridas de desarrollo (deriva de la animación): sin diferencia atribuible al minificado.
- No probado: `collectstatic` real con el manifiesto (importmap con huella + `construir.js` sin huella), 4G con GPU real y el servidor de producción completo (no hay `staticfiles/` local).

## Para decidir / vigilar (no corregí nada)
1. RC 200: luces con brillo estando apagada de noche (nota 3).
2. NMAX móvil > 33 ms (nota 5): remedir sin otras sesiones y, si se repite, recortar calls/triángulos en baja.
3. Programas de shader 30–32 contra "~26 aceptado": las líneas nuevas no empeoran (iguales a las de referencia, 30–31); no medí el tope de 16 del primer cuadro.
4. Negras parecidas (nota 1): CT 100 / Discover / Eco.
5. Los módulos sin huella (`construir.js`, `rasgos.js`, `calcas_fabrica.js`…, ~50 KB br) se sirven con la caché corta de WhiteNoise (60 s): en visitas repetidas revalidan, y tras un despliegue puede haber hasta 60 s de `moto3d.js` nuevo con un módulo viejo.
6. Móvil: primer cuadro 9–11 s con 4× CPU, sin 4G emulado y con la máquina compartida: no sirve para el límite de 3 s; confirmar en Render o en un teléfono.
7. Pendiente conocido (informe de las nuevas): tapas laterales blancas de la XR 190L y máscara más grande de la XTZ 150.

## Tabla por moto (alta = escritorio; baja = móvil emulado)
| # | Moto | Grupo | Alta tri / calls | Con accesorios tri / calls | Baja (móvil) tri | Flotantes | Rayos X / Estado | Noche (encendida) | Veredicto |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AKT NKD 125 | diferenciada | 42168 / 42 | 47762 / 44 | 24634 | 0 | ok | Spot+Point+4 emisivos ✓ | ok. Primer cuadro 3,8 s = primera carga en frío de la corrida (no se repite en las otras) |
| 2 | AKT CR4 125 | diferenciada | 43996 / 44 | 49578 / 46 | 25127 | 0 | ok | Spot+Point+4 emisivos ✓ | ok (cinta lima en rines) |
| 3 | AKT TT 125 DS | referencia | 40254 / 40 | 43418 / 42 | 23763 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 4 | AKT Dynamic Pro 125 | referencia | 35253 / 41 | 38857 / 42 | 21625 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 5 | Auteco Bajaj Boxer CT 100 | diferenciada | 41293 / 43 | 46859 / 45 | 24339 | 0 | ok | Spot+Point+4 emisivos ✓ | parecida a la Discover (6): mismo tanque, franja y colín, ambas negras (ver nota 1) |
| 6 | Auteco Bajaj Discover 125 | diferenciada | 37289 / 43 | 42895 / 45 | 22587 | 0 | ok | Spot+Point+4 emisivos ✓ | parecida a la CT 100 (5) (ver nota 1) |
| 7 | Auteco Bajaj Pulsar NS 200 | diferenciada | 47357 / 43 | 53009 / 44 | 27428 | 0 | ok | Spot+Point+4 emisivos ✓ | ok (rines rojos) |
| 8 | Auteco Bajaj Pulsar RS 200 | referencia | 44693 / 43 | 50273 / 45 | 26193 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 9 | Honda CB 125F | referencia | 39720 / 41 | 45370 / 43 | 22781 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 10 | Honda XR 150L | referencia | 34904 / 40 | 38068 / 42 | 21277 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 11 | Honda Dio 110 | diferenciada | 29787 / 42 | 33391 / 43 | 17242 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 12 | Honda Wave 110S | diferenciada | 33889 / 41 | 39537 / 43 | 19757 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 13 | Suzuki GN 125 | referencia | 39169 / 43 | 44763 / 45 | 24018 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 14 | Suzuki Gixxer 150 | diferenciada | 44000 / 42 | 49636 / 44 | 25755 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 15 | Suzuki Best 125 | diferenciada | 34518 / 41 | 40112 / 43 | 20734 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 16 | Yamaha NMAX 155 | diferenciada | 46453 / 45 | 48853 / 45 | 26252 | 0 | ok | Spot+Point+4 emisivos ✓ | ok en forma; móvil (4× CPU): mediana de cuadro 35–46 ms, sobre el límite de 33 ms (nota 5) |
| 17 | Yamaha XTZ 125 | referencia | 39743 / 40 | 42907 / 42 | 23703 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 18 | Yamaha FZ 25 | diferenciada | 44961 / 42 | 50641 / 44 | 25806 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 19 | Yamaha Crypton FI 115 | diferenciada | 36881 / 41 | 42531 / 43 | 21913 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 20 | Yamaha MT-03 | diferenciada | 47834 / 43 | 53556 / 44 | 27269 | 0 | ok | Spot+Point+4 emisivos ✓ | ok (rines cian) |
| 21 | TVS Apache RTR 160 | diferenciada | 43355 / 42 | 48925 / 44 | 25028 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 22 | KTM Duke 200 | referencia | 44453 / 44 | 50125 / 45 | 26677 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 23 | KTM RC 200 | referencia | 47795 / 43 | 53467 / 44 | 27628 | 0 | ok | Spot+Point+4 emisivos ✓ | de noche y APAGADA queda un emisivo de stop (ff2a1f×0,69) y de faro (fff1c4×1,08) encendidos; las otras 32 no (nota 3) |
| 24 | Hero Eco Deluxe 100 | referencia | 34946 / 42 | 40568 / 44 | 20677 | 0 | ok | Spot+Point+4 emisivos ✓ | parecida a CB/Discover en negro (nota 1) |
| 25 | Yamaha Aerox 155 | diferenciada | 44355 / 45 | 46785 / 45 | 24744 | 0 | ok | Spot+Point+4 emisivos ✓ | ok |
| 26 | Honda XR 190L | nueva | 39621 / 40 | 42797 / 42 | 23236 | 0 | ok | Spot+Point+4 emisivos ✓ | ok vs fotos Galgo: roja, aletas CRF, máscara roja. Pendiente conocido: tapas laterales blancas |
| 27 | Suzuki DR 150 | nueva | 39668 / 39 | 42844 / 41 | 23186 | 0 | ok | Spot+Point+4 emisivos ✓ | ok vs fotos: gris con mitad baja negra, máscara angulosa |
| 28 | Yamaha XTZ 150 | nueva | 39001 / 39 | 42177 / 41 | 23009 | 0 | ok | Spot+Point+4 emisivos ✓ | ok vs fotos: azul con máscara, tapas, colín y guardafango negros |
| 29 | TVS Raider 125 | nueva | 40893 / 42 | 46463 / 44 | 23845 | 0 | ok | Spot+Point+4 emisivos ✓ | ok vs fotos: gris California, colín largo, faro en flecha; guardafango negro |
| 30 | Yamaha FZ 2.0 | nueva | 44324 / 42 | 49936 / 44 | 25546 | 0 | ok | Spot+Point+4 emisivos ✓ | ok vs fotos Commons: azul, tanque ancho, colín largo |
| 31 | Hero Hunk 125R | nueva | 42866 / 42 | 48472 / 44 | 24314 | 0 | ok | Spot+Point+4 emisivos ✓ | ok vs fotos: negra, colín alto y partido, guardafango pintado |
| 32 | Auteco Bajaj Boxer CT 125 | nueva | 35183 / 42 | 40789 / 44 | 20883 | 0 | ok | Spot+Point+4 emisivos ✓ | ok vs fotos: blanca con cuña lima y faro en trapecio; parecida a la CT 100 solo en el chasis |
| 33 | Hero Hunk 150 | nueva | 44320 / 43 | 49916 / 45 | 24966 | 0 | ok | Spot+Point+4 emisivos ✓ | ok vs fotos Commons: negra con franja roja, amortiguadores dobles, bikini |
