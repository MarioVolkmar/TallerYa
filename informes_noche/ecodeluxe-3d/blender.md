# Eco Deluxe 100: segunda pasada con Blender 5.3

**Resultado**: `garaje/static/garaje/modelos/ecodeluxe100_tripo.glb` pasa a `?v=4` (único cambio en `moto3d/glb.js`).
Capturas del visor real: `blender_lateral.png` y `blender_tres_cuartos.png` (negro de fábrica, luces encendidas).
Respaldo de la v2: `herramientas_3d/ecodeluxe100/blender/ecodeluxe100_tripo_v2_respaldo.glb`. Sin commit.

| | v2 (numpy + meshoptimizer) | v4 (Blender) |
|---|---|---|
| Peso | 1,41 MB | **1,17 MB** (−17 %) |
| Triángulos | 103.266 | **82.231** (−20 %) |
| Vértices | 61.026 | 51.926 |
| Normales | promediadas en todo (sin aristas) | **suavizado por ángulo** (aristas vivas en paneles) |
| Lente del faro | disco de borde serrado | **elipse limpia** apenas abombada |
| Calcas de fábrica | las genéricas de la línea (cuña plata y roja) | **propias, ubicadas en metros** (`extras.calcas_fabrica`) |

## Flujo (scripts en `herramientas_3d/ecodeluxe100/blender/`)

1. `geometria.py` (Blender sin ventana): importa el GLB del visor (Blender lee la cuantización), y por pieza:
   une vértices a 0,4 mm (≈ 175 duplicados en total, la mayoría en escape, chasis y rayos), quita caras degeneradas,
   tapa huecos de hasta 12 lados (≈ 75 huecos chicos; nunca en las láminas abiertas marcadas `doble`), orienta las
   normales por isla (en 11 piezas el recálculo empeoraba y quedó la orientación de Tripo), **Decimate** con razón por
   material (pintura 0,72, sillín 0,6, chasis y plástico 0,8, metal 0,85; llantas, rayos, luces y direccionales
   intactas) y **suavizado por ángulo** (pintura y negro brillante 38°, motor 35°, sillín 55°, caucho 60°).
   El lente del faro se rehace como elipse ajustada a sus vértices (plano por PCA). Los 19 internos de Rayos X no
   se tocan. Exporta en float con nombres y extras intactos (verificado).
2. `postproceso.py` (Python del venv): recuantiza igual que el original (posiciones int16, normales int8,
   KHR_mesh_quantization, índices uint16, mismo orden de nodos `material.parte`), conserva todos los extras y suma
   acabados PBR y calcas. El exportador de Blender no cuantiza ni escribe este formato, por eso el post-proceso.
3. `render.py`: render Eevee de revisión (800 px) con PBR aproximado por prefijo. La silueta queda igual a la de Tripo.

## Materiales PBR

El visor no lee UV ni texturas ni color por vértice del GLB: el material sale del prefijo del nodo (pintura
brillante con barniz, plástico mate, cromo, caucho, vinilo, luces emisivas) y de `extras.acabado`. Se sumaron:
aros de aluminio pulido (rugosidad 0,24, metálico 0,95), **sillín de vinilo** (rugosidad 0,62 + `sheen` 0,35 y barniz
leve), plásticos inyectados mate (guardabarros trasero e interior, cubiertas de horquilla), puños de caucho y espejos
con barniz. Se mantienen los acabados de v2 (tambores, horquilla, escape, zamak, cilindro).

**AO horneada: no se hizo.** Necesita que `glb.js` lea `COLOR_0` (1 byte por vértice ≈ +50 kB) o UV + textura; es un
cambio del visor compartido por todas las motos, mejor decidirlo aparte.

## Calcas de fábrica

Medidas sobre `1_lateral.jpg` (1,9 mm por píxel tomando los ejes a ±0,6175 m): cuña plateada y blanca en el costado
del tanque (`en` [0,11, 0,715], 30 cm), trazos grises en la tapa lateral y «ECO DELUXE» debajo (17 cm). Sin el
logotipo de la marca. Se reemplaza la cuña plata y roja de `calcas_fabrica.js` solo para este GLB.

## Verificación en el visor (`/garaje/60/`, usuario de prueba)

Carga `?v=4` sin errores de consola; 71 mallas, 19 internas. Rayos X muestra los 19 internos y Moto los oculta.
Personalizar en rojo pinta las 6 piezas de pintura sin derrames en ruedas, chasis, motor ni sillín (captura a
375 px). Ninguna pieza flotando (todas las cajas tocan otra a menos de 1 cm). Calcas: 3 de fábrica listadas.

## Pendiente

- La cuña del tanque se ve como dos franjas finas, más delgada que la gráfica de la foto. Para que se parezca más
  haría falta una forma nueva en `calcas_fabrica.js`.
- Parrilla blanca: sigue fundida en el colín (Tripo no la separa).
- Blender 5.3 con Vulkan se cae (`vk_texture_pool.cc`) al hacer un segundo render en la misma corrida: un render por
  corrida o `--gpu-backend opengl`.
- Moto de prueba pk 60: borrarla cuando ya no haga falta.

## Arreglos farola, llantas y direccionales (v5, 21-nov)

`?v=5`, **1,25 MB**, 87.346 triángulos, 75 nodos, `gltf-transform validate` sin errores ni avisos. Script:
`herramientas_3d/ecodeluxe100/blender/arreglos_v5.py` (numpy; lee y escribe con `glbio.py`, mismo formato cuantizado).
Entrada: respaldo de la v4 (`ecodeluxe100_tripo_v4_respaldo.glb`) y la mica curva de la v2. Capturas: `arreglo_lateral.png`,
`arreglo_tres_cuartos.png` y `arreglo_luces.png`. No hizo falta Blender ni tocar el visor, solo `?v=`.

| Falla | Causa | Arreglo |
|---|---|---|
| Farola: un disco flotando | El lente de Tripo se recortó en v1 con un círculo sobre el carenado, que quedó con un **hueco de 15 cm de fondo**. La v4 cambió ese lente curvo por una **elipse plana** puesta delante del hueco. No había farola genérica del visor encima. | La **mica curva de Tripo** vuelve (`vidrio.mica_faro`, de la v2, transparente; el borde serrado queda escondido). Se le suman un **aro cromado** de 6,5 mm sobre el borde (`cromo.aro_faro`), un **reflector** parabólico de 5,5 cm (`cromo.reflector_faro`), que tapa el hueco, y un **bombillo** en el foco (`luz.faro`, con `lampara: faro`: de ahí salen el haz y el halo). |
| Llantas grandes para el rin | La escala por distancia entre ejes deja la llanta bien (r 0,306 m; 2.75-18 adelante y 3.00-18 atrás miden unos 0,59-0,61 m). El que quedó chico fue el **aro de Tripo**: pestaña a 0,218-0,224 m, cuando un rin de 18" asienta a 0,229 m. El flanco medía 9 cm (lo real es ~7). El visor tornea la llanta midiendo la malla, con 3 mm de holgura: no la agranda. | Aro escalado **parejo** alrededor del eje hasta la pestaña de 0,236 m (×1,054 atrás, ×1,084 adelante). Rayos estirados solo de la maza hacia afuera, hasta el aro nuevo. El talón de la llanta se lleva al aro y el exterior sigue igual (sigue pisando el piso). Ahora el perfil es de 70-80 mm sobre el aro cromado. |
| Direccionales mal pintadas | Tripo deja cada direccional como **una sola pieza**, cuello y cuerpo juntos, y toda iba en `ambar`. | Cada una se corta con planos, partiendo los triángulos del borde: **vástago** (`oscuro.vastago_direccionales`), **carcasa** de atrás (`negro_brillo.carcasa_direccionales`) y **mica ámbar** de adelante (las delanteras) o de atrás (las traseras), que conserva su nombre y `lampara: direccional`. Es la que se enciende. |

Verificado en `/garaje/60/vista-3d/` a 1280 y 375 px: el 3D carga con 76 mallas y sin desborde. En la consola quedan «unknown error when fetching the script»,
que vienen del panel oculto y no del 3D, y un 404 de una prueba mía al prefijo `three/addons/` del importmap. Para la captura de
luces subí `M.luz` a 2,6, como hace «Encender». La ficha `/garaje/60/` no arrancaba el 3D en el panel del navegador porque
está oculto y ahí `requestAnimationFrame` no corre. Pasa igual con `?modelo3d=procedural`: no es por el GLB.
Pendiente: el bombillo encendido es un punto chico. Si se quiere más brillo con la luz prendida, se puede usar un
emisor más grande dentro del reflector.

## Paquetes recomendados (no instalé nada)

| Paquete | Qué es / origen | Peso | Qué mejora | Confianza |
|---|---|---|---|---|
| **gltf-transform** (`@gltf-transform/cli`, npm) | CLI de Don McCurdy para optimizar glTF; github.com/donmccurdy/glTF-Transform | ≈ 15 MB en node_modules | `meshopt`/`quantize`/`weld`/`simplify` en un comando; validar el GLB; comprimir con EXT_meshopt_compression (−40-60 % de peso) | Alta: MIT, muy usado (three.js, Khronos) |
| **meshoptimizer** (ya está como dependencia de `simp.mjs`) | zeux/meshoptimizer | < 1 MB | Si el visor carga `MeshoptDecoder` (three.js lo trae en examples), los GLB bajarían a ~0,5 MB | Alta: MIT, de Arseny Kapoulkine |
| **glTF-Validator** (Khronos, npm `gltf-validator`) | validador oficial | ≈ 3 MB | Detectar errores de formato antes de publicar | Alta: Khronos |
| Texturas PBR CC0 (ambientCG / Poly Haven) | bibliotecas de dominio público | 0,2-1 MB por material a 512 px | Grano del plástico y del vinilo con normal map; requiere UV y que el visor lea texturas | Alta (CC0), pero suma peso y trabajo en el visor |

No hace falta ningún complemento de Blender: todo lo de este flujo viene incluido (importador/exportador glTF,
Decimate, bmesh, Eevee).
