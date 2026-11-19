---
name: moto-3d-realista
description: Hace el 3D "realista" de un modelo de moto para el visor de TallerYa (GLB liviano, cuantizado, con piezas separadas y con nombre que se pintan con Personalizar), a partir de la ficha técnica y de fotos (de preferencia un visor 360° oficial) usadas solo como referencia, con control estricto de calidad (IoU de silueta, rasgos medidos en cm en dos vistas, bordes internos), plantillas por familia y un ciclo automático de un comando. Úsala cuando pidan "el 3D de la moto X", "un modelo más realista de la X", "GLB de la X para el visor" o mejorar el parecido del 3D de una línea.
---

# moto-3d-realista (v4)

Camino: **modelado paramétrico local** (numpy puro). La ficha JSON por moto define paneles con aristas vivas, lofts, barridos y tornos. El perfil se **mide** de las fotos y la calidad se controla con números, no a ojo. Sin servicios de pago ni cuentas. Historia y métricas: `informes_noche/skill-moto-3d.md`.

## Metas (medibles)

| Meta | Valor | Cómo se mide |
|---|---|---|
| **Tiempo de la siguiente moto** | **≤ 30 min de reloj** con visor 360° y plantilla de su familia; ≤ 45 min sin visor 360° o con familia nueva | reloj del pedido al GLB aprobado en el visor; anotar los minutos por etapa en el informe |
| Tiempo de máquina por iteración | ≤ 1 min (`ciclo.py`: 33 s en la NMAX) | lo imprime `ciclo.py` |
| Tokens | ≤ 150 k de contexto, ≤ 8 imágenes vistas | `get_usage`; cuadrículas y recortes a escala |
| Dinero | 0 | — |
| IoU de silueta | ≥ 0,85 en cada vista (poses atadas del visor 360°) | `iou.py --torno` |
| **Rasgos** | **todos cumplidos**: cada rasgo a ≤ 3 cm de su marca en **≥ 2 vistas ortogonales** (lateral der., lateral izq., frontal, trasera) | `revisar.py` |
| Bordes internos | reportar precisión y cobertura (NMAX v4: 0,44 / 0,75); no deben bajar entre versiones | `revisar.py` |
| Duplicados y sobrantes | `ok` en todas las combinaciones de Personalizar | `inventario_visor.js` |
| GLB | ≤ 1 MB (NMAX v4: 400 KB) | `generar.py` |

**Por qué los rasgos**: la v2 pasaba el IoU de silueta sin verse real (faro 8 cm alto, cola 7 cm larga, escape 11 cm largo). La silueta no ve dónde están las piezas por dentro del contorno; los rasgos sí.

## Entorno (una vez)

```
python -m venv C:\Users\volkm\.venvs\moto-3d
C:\Users\volkm\.venvs\moto-3d\Scripts\python.exe -m pip install numpy pillow onnxruntime
```
- Modelo de silueta: `modelos_3d_local/_herramientas/u2netp/u2netp.onnx` (rembg v0.0.0, Apache-2.0, 4,6 MB).
- `P=C:/Users/volkm/.venvs/moto-3d/Scripts/python.exe`, `S=.claude/skills/moto-3d-realista`, `L=modelos_3d_local/<moto>`. Correr siempre con `-I`.

## Flujo (con minutos objetivo; total ≤ 30)

1. **Medidas (3 min)**: una búsqueda web de la ficha técnica (entre ejes, largo, alto, asiento, ancho, rines y llantas). Cada medida con su fuente en `medidas`.
2. **Fotos por vista (5 min)**: buscar el visor 360° oficial en la página del modelo (sacar con JS las URL `...360...jpg`; NMAX: `yamaha-motor.co.jp/mc/lineup/nmax155/img/360view/2026_nmax155_1_{n}.jpg`). Luego, un comando:
   `$P -I $S/scripts/preparar_vistas.py $L --patron "<url con {n}>" --lateral <cuadro de la lateral derecha> --entre-ejes <m>`.
   Baja los 36 cuadros (solo `urllib`, nada se ejecuta), arma `v360_KK/` con foto y máscara (umbral ∪ u2netp) y escribe `vistas.json` (lateral der./izq., frontal, trasera, dos 3/4, si es ortogonal y px/m).
   - Sin visor 360°: fotos de estudio de revistas (Autocar India `/colours/`, BikeWale) o concesionarios, una carpeta por vista con `foto.jpg` + `FUENTE.txt`; máscaras con `siluetas.py`; IoU sin `--torno`.
   - Claude in Chrome puede no estar conectado: la búsqueda web y `urllib`/curl bastan para fotos públicas.
3. **Ficha desde la plantilla (5 min)**: `$P -I $S/scripts/escalar_ficha.py $S/motos/plantillas/<familia>.json $S/motos/<id>.json --entre-ejes .. --asiento .. --ancho .. [--r-del .. --r-tras .. --rin-del .. --rin-tras ..]`.
   - Después, alturas reales: `$P -I $S/scripts/perfil.py $L/v360_05/mascara.png --entre-ejes .. --estaciones -0.85:0.05:0.15 --techo 0.95` da estaciones `{x, ys, yt}` de partida en JSON.
   - Familias: `scooter` (NMAX v4). Para urbana, sport o doble propósito todavía no hay plantilla: hacer la primera con esta skill y guardarla en `motos/plantillas/`.
4. **Marcar rasgos (5 min)**: en `$L/rasgos.json`, la posición en px (foto completa) de cada rasgo en cada vista donde se vea. Hacer una cuadrícula de 25 px sobre la foto recortada (ver cómo en el informe), mirarla una vez y anotar; los ejes de las laterales salen solos de los apoyos de las llantas (centro del apoyo; alto = suelo − R·px/m). Rasgos de la NMAX (12): faros der./izq., punta de la nariz, puños y espejos der./izq., stop, punta del escape, escalón del asiento (mitad de la bajada), punta del parabrisas y punta del portaplaca. En la ficha, `rasgos` dice de qué nodo sale cada punto (`{"nodo", "lado", "punto": centro|min_x|max_y…, "en_x"}`): se calculan de la geometría, no se escriben a mano.
5. **Ciclo (≈ 1 min de máquina por vuelta)**: `$P -I $S/scripts/ciclo.py $S/motos/<id>.json $L garaje/static/garaje/modelos/<id>.glb --anterior <glb anterior>`.
   - Genera, corre el IoU en torno, la revisión estricta y la hoja comparativa. Imprime: IoU, rasgos cumplidos, bordes y qué rasgos fallan.
   - `$L/revision/revision.json` trae para cada rasgo y vista `mover_cm_derecha_abajo`: hacia dónde mover la pieza en la foto. Corregir la ficha y repetir. La NMAX v3 → v4 tomó 4 vueltas (rasgos 6/12 → 12/12).
   - `$L/revision/hoja_revision.jpg`: foto | render | líneas (rojo = modelo, verde = foto, amarillo = coinciden; azul = marca del rasgo y error). Mirar una sola vez, a escala ≤ 0,6.
   - **Ninguna pieza se da por buena si no calza en dos vistas ortogonales.** Las 3/4 son informativas: aun calibrando giro, cabeceo, escala y corrimiento con anclas, su cámara erra 6–15 cm (medido con el eje delantero).
6. **Ajuste automático (20 s por ronda)**: `$P -I $S/scripts/ajustar_ficha.py $S/motos/<id>.json $L <vistas> --piezas frontal,costados,asiento --rondas 1 --salida <scratchpad>/prueba.json`. Sube el IoU unas milésimas; volver a correr `ciclo.py` con la ficha ajustada y quedarse con ella solo si los rasgos siguen cumplidos.
7. **Detalle que se ve** (lo que hace que "parezca la moto"):
   - Filos vivos y caras planas: secciones con todos los puntos `duro`; filo diagonal del costado con `seccion2` + `mezcla`; lomo central en el frente.
   - **Dos tonos como la foto de color claro** (blanco o rojo, no la negra): en la NMAX el color va arriba del filo del costado, en el frente y en la franja del piso (boomerang); abajo del filo y el túnel son plástico negro (`costados` + `costados_bajo`).
   - Máscara de faros en cuña, faros en las esquinas, LED, rin de 5 brazos dobles, piloto con alas, direccionales en vástago, protector de escape.
   - Acabados: brillante en pintura y negro de piano; mate en plásticos negros (`plastico`).
8. **Placa** (Colombia, Res. 1421/2011 de MinTransporte: 235 × 105 mm): en `extras.placa` del portaplaca `{c, incl, tam}`, medidos en la lateral pura. Holgura de 0 a 5 mm entre la placa y la cara del portaplaca (medir con `glb.leer`: ver el informe).
9. **Visor (5 min)**: línea en `MODELOS` de `garaje/static/garaje/js/moto3d/glb.js` y **subir `?v=`** con cada GLB.
   - Abrir `/garaje/<pk>/vista-3d/?modelo3d=glb`, pegar `scripts/inventario_visor.js` y correr `await inventario({ estilo })` en las 8 combinaciones (sin accesorios; todos los accesorios con cada estilo de espejos; cada estilo de rin): `ok` en todas.
   - Captura comparativa: pegar `scripts/capturas_visor.js`, `await capturarVersion("vN")`, cambiar el GLB, recargar, `await capturarVersion("vN+1")` y `await panelVersiones("vN", "vN+1")`, y UNA captura de pantalla.
   - Hoja sin navegador, para cualquier par de versiones: `$P -I $S/scripts/comparar.py salida.jpg v3=a.glb v4=b.glb` (6 cámaras fijas, incluida la de arriba).

## Ficha JSON

- **Tipos de pieza**:
  - `panel`: loft con `seccion` poligonal (media sección `[u, v, duro]` de abajo-centro a arriba-centro; `duro` = arista viva, también en los extremos). Opcionales: `seccion2` + `mezcla` por estación (mismo número de puntos). Con `"eje": "y"` la sección va en planta: `cuna` hace una pieza en V con punta viva hacia adelante. Una sección puede empezar en `[0, v]` con v > −1 para cortar la pieza a lo alto (así se separan `costados` arriba y `costados_bajo` abajo del filo).
  - `loft`, `barrido`, `torno`, `caja`, `llanta`, `rin` (`partes`: `todo` | `brazos`), `aro`, `disco`, `arco`.
  - `espejo: true` duplica la pieza en −Z.
- **Secciones** en `secciones`: `costado_sup`/`costado_sup_alto` y `costado_inf`/`costado_inf_alto` (arriba y abajo del filo diagonal), `frontal` y `punta` (con lomo), `cuna`, `tunel`, `asiento`, `boomerang`, `escudo`, `caja`, `placa`, `lente`.
- **Nodo** `material.nombre`. Materiales: `pintura`, `pintura2`, `oscuro`, `asiento`, `chasis`, `rin`, `luz`, `stop`, `ambar`, `vidrio`, `metal`, `cromo`, `caucho`, `motor`, `carter`, `resorte`; los crea `glb.js` si faltan: `plastico`, `negro_brillo`, `vidrio_oscuro`; `acento` lo pinta Personalizar con el color secundario.
- **`extras`**: `pieza` (llanta_del, llanta_tras, freno_del, freno_tras, motor, correa, suspension_del, suspension_tras), `rin: true`, `aro: true`, `padre` (`espejos.fabrica`, `escapeFabrica`), `rol: "visor"`, `manubrio: {x, y, extremo}`, `acomodar: [{grupo, ref, a}]`, `placa: {c, incl, tam}`. Las piezas de mantenimiento que el GLB no trae quedan internas (solo Rayos X).
- **`rasgos`**: anclas fijas (`eje_del`, `eje_tras`: `[x, y, z]`) y rasgos calculados de la geometría (`{"nodo": "faros", "lado": -1}`, `{"nodo": "visor", "en_z": 0, "punto": "max_y"}`…). Al cambiar el nombre de una pieza, cambiar su rasgo.
- `base` (en las plantillas): `entre_ejes`, `asiento`, `ancho` de la moto de origen, para `escalar_ficha.py`.
- Nada de logos ni marcas.

## Trampas aprendidas (no repetir)

- **Revisar la foto de color claro antes de decidir los dos tonos**: en la foto negra no se ve qué es pintura y qué es plástico. La v3 tenía todo el costado pintado.
- **Marcas en 3/4 a ojo**: con la cuadrícula gruesa me equivoqué hasta 65 px (13 cm). Marcar con recortes ampliados ×2 y cuadrícula de 10 px, o no usar esa vista para rasgos.
- **Escribir con `encoding="utf-8"`**: en Windows `write_text` sin codificación falla con «−» o «°» y deja el archivo truncado.
- **Editar la ficha por copia**: un script que reemplaza una pieza en el dict de búsqueda y no en `ficha["piezas"]` no cambia nada (el protector de escape de la v3 nunca entró al GLB). Reemplazar en la lista y revisar con `comparar.py`.
- **La procedural reaparecía encima del GLB**: `moto3d.js` pone `visible = !userData.oculto` en cada cambio de modo. Ocultar con `visible=false` **y** `userData.oculto=true`.
- **Atributos cuantizados entrelazados**: el cargador descuantiza a Float32 (la fusión de mallas lee `.array` crudo).
- **Dobles con Personalizar**: lo procedural que se conserva estaba armado para la carrocería genérica; por eso el control corre todas las combinaciones.
- **Cajas engañan**: el control de flotantes mide contra vértices y por grupo entero. Para holguras finas (placa) medir contra el plano de la cara, no vértice a vértice.
- **Capturas con el panel oculto**: el lienzo mide 0 × 0 y es transparente: `setSize(900, 600, false)`, aspecto de la cámara y fondo claro. No centrar con `Box3.setFromObject(raiz)` (cuenta mallas ocultas). La hoja se muestra con `object-fit: contain` (si no, se estira con el tamaño de la ventana).
- **Comparar versiones en el visor**: capturas de una en `localStorage`, copiar el otro GLB encima, subir `?v=`, recargar; al final dejar el GLB nuevo y otro `?v=` más.
- La sesión local de prueba cae cuando otra sesión vuelve a sembrar la base: crearla justo antes de cada tanda.
- `ciclo.py` corre los scripts con `-I`, que ignora `PYTHONIOENCODING`: su salida se lee con `errors="replace"`.

## Reglas

- Fotos de internet: solo referencia de silueta, medidas y rasgos, en `modelos_3d_local/` (ignorada por git). Nunca textura, nunca al repo, nunca en informes (las hojas de revisión con fotos quedan locales; al informe van solo renders y capturas del visor).
- Nada se ejecuta de lo descargado.
- No iniciar sesión en sitios externos ni aceptar nada.
- El GLB va en `garaje/static/garaje/modelos/`: es geometría propia.
- Piloto apagado por defecto: solo con `?modelo3d=glb` o `localStorage.moto3d_glb = "1"`. Si el GLB falla, queda la procedural.

## Fuentes de las fotos de la NMAX 155 (solo referencia local)

| Carpeta | Fuente | Uso |
|---|---|---|
| `fotos/yamaha_jp_360/c1..c36.jpg` | visor 360° de https://www.yamaha-motor.co.jp/mc/lineup/nmax155/ | **principal**: `vistas.json` (v360_05, 23, 14, 32, 02, 27) y `rasgos.json` |
| `fotos/autocar_color_{1..4}` | https://www.autocarindia.com/bikes/yamaha/nmax-155/colours/ | **dos tonos** (en blanco y rojo se ve qué es pintura y qué plástico) |
| `fotos/yamaha_jp_000{1,2,3}` | comunicado https://global.yamaha-motor.com/jp/news/2026/0120/nmax.html | colores |
| `fotos/bikewale_trasera` | https://www.bikewale.com/yamaha-bikes/nmax-155/images/ | trasera (sin usar) |
| `frontal`, `trasera`, `lateral_2025_*`, `tresc_2020_*`, `casi_lateral_2025` | Wikimedia Commons (ver `FUENTE.txt`) | ronda 1 |
| (vista de arriba) | no hay en el visor 360° ni en la búsqueda (Yamaha Malasia, 1000PS, Paultan) | `comparar.py` trae la cámara de arriba para revisar anchos en planta del modelo |


## Ahorro de tokens
Registros largos (render, IoU, builds, pruebas, mediciones) a un archivo en el scratchpad; mostrar solo el resumen (`> log.txt; tail -15 log.txt`). Capturas solo como prueba final, a `scale: 0.5`. Tope de ~150 mil tokens de contexto: al llegar, nota de relevo y sesión nueva (ver CLAUDE.md, «Modelo según la tarea»).
