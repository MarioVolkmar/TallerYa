# Prueba: primera lámina TVS (Apache RTR 160 4V · clutch con slipper, fig. 8)

17-nov-2026 · skill `hacer-lamina` (sin cambios) · Opus 5.5 · sin commit.

**Entrega:** `motor/apache-clutch.html` (+ `datos/apache-clutch.json`, `datos/apache-clutch-arte.js`), archivo único `motor/prueba-apache-clutch.html`, catálogo `motor/catalogo/tvs-apache160-4v.json`. Validador: 0 errores (1 aviso: 1 y 21 casi encimados en el armado transparente; solo se ven al tocarlos). Medición final sin bloqueantes, medible 4,88.

**Figura elegida:** el catálogo trae dos clutch: la fig. 7 (sin slipper) y la fig. 8 (con slipper). Hice la 8 porque es la de las motos recientes, y lo dice el `cabeza.aviso`. «Cómo funciona» tiene un paso 6 nuevo, «Reduces de golpe», que muestra las rampas del slipper.

## Hermana: cuánto cubría cada una (medido antes de elegir)
| candidata | piezas de la fig. 8 que cubre (de 21; sin el kit 22) |
|---|---|
| `cb125f-clutch` | **15 (71 %)**: campana, buje, manzana, 2 tipos de disco, separadores, placa de presión, placa de los resortes, pin, resortes, tornillos, tuerca, 2 arandelas, balinera |
| `akt-embrague` | ~10 (48 %): tiene rampas de slipper, pero otra arquitectura |
| `boxer-embrague` | ~10 (48 %) |

Usé `cb125f-clutch` con `remapear_hermana.py`. Las 6 piezas sin hermana (resorte antibrinco y su asiento, pin adaptador, balín, retén y arandela de atrás) salieron de la biblioteca, y el balín es arte propio con 6 líneas.

## Catálogo TVS
`extraer_catalogo.py` **no lee el formato TVS** (columnas «No. | PARTE Nº | DESCRIPCIÓN | CANT. | SAP»): con `--figura 8` pide `--columna`, y con `--columna CANT.` devuelve una sola pieza basura («RETEN / CLUTCH»). La extraje a mano con pymupdf: 6 campos por fila, el SAP va a `nota`. Me tomó **~1,5 min**. El índice del PDF (p. 7) da la figura y la página sin mirar imágenes.

## Tabla contra las láminas anteriores
| lámina | hermana | tiempo con revisión | mediciones | tokens creación / revisora | medible | revisora mec. / UX (antes de corregir) | graves |
|---|---|---|---|---|---|---|---|
| Crypton · freno delantero | nmax-fig22 | 13 min | 1 | ~175 k / 104 k | 4,80 | 3,9 / 3,6 | 3 (de 7) |
| NKD · rueda trasera | no | 14 min | 2 | ~98 k / 91 k | 4,88 | 4,0 / 4,0 | 4 (de 13) |
| NMAX · horquilla | cb125f-horquilla | 13 (16 de reloj) | 1 | ~98 k / 108 k | 4,73 | 3,5 / 3,9 | 9 (de 15) |
| Boxer · carburador | no | 23 min | 4 | ~128 k / 91 k | 4,82 | 4,0 / 4,3 | 5 (de 15) |
| CB 125F · susp. trasera | no | 13 min | 2 | ~140 k / 96 k | 4,88 | 4,0 / 4,3 | 3 (de 15) |
| NKD · freno delantero | crypton-freno + nmax-fig26 | 16 min de reloj | 1 | ~162 k / 89 k | 4,88 | 4,2 / 4,4 | 4 (de 13) |
| **Apache 160 4V · clutch (TVS, marca nueva)** | **cb125f-clutch (71 %)** | **15 min por fases (~17 de reloj)** | **1 (+2 previas)** | **~86 k / 103 k** | **4,88** | **3,8 / 4,4** | **4 (de 14)** |

Por fase (real / meta): catálogo 2 / 1,5 · dibujo + contenido 8 / 4 · verificación 4 / 2,5 · revisión < 1 / 1,5 (13 de 14 hallazgos se aplicaron solos). Es la lámina con menos tokens de creación de la serie.

## Qué falló, con su sección de la skill
1. **Paso 1 (Catálogo):** no hay receta para TVS y el extractor falla en silencio: escribe 1 pieza basura en vez de avisar. Me costó 0,5 min sobre la meta.
2. **Paso 3b (hermana con otra numeración):** el remapeo copia la *mecánica* de la hermana, y eso fue el grave principal. Al cambiar las placas de nombre (placa elevadora → placa de los resortes), reescribí la ficha de los resortes como «entre la placa 13 y la placa 4», y así el camino de la fuerza no cierra. La revisora lo atrapó. Lo heredado de la Honda (67 dientes, 6003, 17 mm, «cuatro resortes», 0,9 L, 10-20 mm) lo limpié con un grep propio: `--rapido` no lo vio porque son cifras, no números de figura.
3. **Paso 2 / plantillas:** `plantillas_ficha.py --hermana` imprime pares cruzados («14 Tornillos ← ficha 13 de la hermana (Arandela del eje)»). Parece que solo es el mensaje, porque el contenido salió bien, pero confunde.
4. **Paso 3b (piezas nuevas):** tres errores cuestan una corrida cada uno y la skill no los dice: a las piezas que agrega el script les falta `et`, y sin él `separar_numeros.py` se cae con KeyError. `decision` solo acepta `cambia` y `reutiliza`, no `revisa`. Y `anc` es la posición armada, no la del despiece.
5. **Paso 6-7 (`--previa`):** dos bloqueantes, ambos bien atrapados. Uno era el estado del paso 6 de «Cómo funciona», demasiado largo (> ~20 caracteres). El otro, el retén y la arandela 100 % tapados por la campana en el desarme.
6. **Contenido:** el «retén» del catálogo TVS no es un sello de goma, y la plantilla de retén lo trató como tal (3 graves). En catálogos en español, «retén» puede ser un aro de retención.
7. **Ajeno a la skill:** perdí ~2 min con un comando que se quedó esperando stdin (`cat >> /dev/null`).

## Mejoras propuestas (para Auxiliares; la skill no se tocó)
- `extraer_catalogo.py`: soportar el formato TVS («No. | PARTE Nº | DESCRIPCIÓN | CANT. | SAP», una celda por línea en el texto) o, por lo menos, **fallar con un mensaje** si sale menos de 3 piezas. Agregar la línea TVS al paso 1.
- `remapear_hermana.py`: listar también las **cifras** de la hermana que la figura nueva no respalda (dientes, medidas en mm, cantidades en palabras, litros, juego libre), igual que ya lista «heredado sin respaldo».
- Paso 3b: una línea con lo mínimo de cada pieza agregada a mano (`et`, `anc` = posición armada) y los valores válidos de `decision`.
- `plantillas_ficha.py`: un tipo «aro de retención» para «retén» cuando la pieza está dentro del cárter húmedo (clutch, caja).
- Guía de la revisora / autocontrol: agregar la pregunta «¿cierra el camino de la fuerza?» (resortes → placa → discos → manzana) en clutch y frenos.

## Pendientes de la lámina
Papel exacto de las placas 4 y 13, orden de los pines 18-19-20 y lugar del retén y las arandelas; torques, largo de los resortes y espesor de los discos; puesto de cada tipo de disco y lado del resorte antibrinco. Todo esto necesita el manual de servicio. `garaje/intervalos/tvs_apache_rtr_160.json` no tiene tareas de aceite ni de clutch, así que «Cuándo» lleva la fuente del manual del propietario.
