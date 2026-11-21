# Método Eco Deluxe 100: de un Tripo a un GLB para el visor (base para una skill)

Resultado: `garaje/static/garaje/modelos/ecodeluxe100_tripo.glb` en `?v=5`, con 1,25 MB y 87 mil triángulos. El usuario
la juzgó la mejor de todas, sobre todo por las luces. Detalle de cada pasada en `informe.md` (v2) y `blender.md` (v4 y v5).

## Pasos en orden

| # | Paso | Script | Qué hace |
|---|---|---|---|
| 1 | Identificar partes | `privado/tripo/ecodeluxe100/scripts/stats.py`, `vistas.py`, `islas.py` | Caja de cada parte y render de puntos con su número en 4 vistas, comparado con la foto. Cada parte resultó una isla. |
| 2 | Armar | `.../scripts/armar.py` | **Ejes**: Tripo trae z adelante y −x del lado del escape; el visor quiere x adelante y el escape en −z. Es una reflexión, así que **hay que invertir el orden de los vértices**. **Escala uniforme** sacada de la distancia entre ejes de la ficha; después se comprueban el largo y el diámetro de la llanta, sin estirar ningún eje. Agrupa partes por pieza real con nombre `material.pieza`, parte las que son dos piezas y refleja los pares que Tripo dejó de un solo lado (tapa lateral, direccionales traseras). |
| 3 | Aligerar | `.../scripts/simp.mjs` (meshoptimizer, borde bloqueado) | Razón por material: llantas 12 % (el visor las tornea igual), luces 60 %, pintura 40 %, resto 30 %. |
| 4 | Escribir el GLB | `.../scripts/escribir.py` | Formato del visor: posiciones int16 y normales int8 (KHR_mesh_quantization), índices uint16 y `extras` por nodo (ver abajo). |
| 5 | Limpiar con Blender | `herramientas_3d/ecodeluxe100/blender/geometria.py` | Une vértices a 0,4 mm, quita caras degeneradas, tapa huecos de ≤ 12 lados (nunca en láminas `doble`), orienta normales por isla, Decimate por material y **suavizado por ángulo** (pintura 38°, motor 35°, sillín 55°, caucho 60°). No toca los internos. |
| 6 | Recuantizar y acabados | `.../blender/postproceso.py` | El exportador de Blender no escribe el formato cuantizado: aquí se recuantiza, se conservan los extras y se suman `acabado` PBR y `calcas_fabrica`. |
| 7 | Render de revisión | `.../blender/render.py` | Eevee de 800 px. Un render por corrida: con Vulkan se cae en el segundo (o usar `--gpu-backend opengl`). |
| 8 | Arreglos finales | `.../blender/arreglos_v5.py` + `glbio.py` | numpy puro: farola armada, rin a su medida y direccionales en piezas. `glbio.py` lee y escribe el formato del visor y sirve para cualquier moto. |

Validar siempre con `npx gltf-transform validate`, subir `?v=` en `MODELOS_TRIPO` de `moto3d/glb.js` (único cambio) y
mirar el resultado en `/garaje/<pk>/vista-3d/`.

## Luces (lo que más gustó)

- **Faro = 4 piezas**:
  - `vidrio.mica_faro`: la mica **curva de Tripo**, transparente. Nunca un disco plano. El borde serrado se recorta un poco y queda tapado por el aro.
  - `cromo.aro_faro`: tubo elíptico de 6,5 mm que sigue el borde de la mica. La x del borde se mide por sectores de ángulo.
  - `cromo.reflector_faro`: paraboloide de 5,5 cm detrás de la mica, que tapa el hueco del carenado.
  - `luz.faro`: bombillo de media esfera en el foco, con `extras.lampara {tipo: "faro"}`. El visor saca el haz y el halo de las normales y la caja de **ese** nodo, por eso la lámpara debe mirar hacia adelante.
- **Direccionales**: se cortan con planos, partiendo los triángulos del borde (`cortar()` en `arreglos_v5.py`). Quedan en `oscuro.vastago_*`, `negro_brillo.carcasa_*` y la **mica `ambar.direccional_*`** (con `lampara: direccional`): la mitad que da adelante en las delanteras y atrás en las traseras. El visor la hace parpadear.
- **Stop**: `stop.stop` emisivo rojo. Reflectores: `reflector.*`, que no alumbran.

## Materiales

- El visor **no lee** UV, texturas ni color por vértice del GLB. El material sale del **prefijo del nodo** (`pintura`, `negro_brillo`, `plastico`, `chasis`, `metal`, `cromo`, `motor`, `carter`, `caucho`, `asiento`, `oscuro`, `vidrio`, `luz`, `stop`, `ambar`, `reflector`).
- `extras.acabado` agrega PBR propio sin tocar el material compartido: aro de aluminio pulido, sillín de vinilo con sheen, plástico inyectado mate, tambores, zamak y pintura de escape.
- Personalizar pinta lo que va en `pintura`. Hay que verificarlo con rojo vivo: no debe derramarse a ruedas ni chasis.
- Otros extras útiles:
  - `eje` y `pieza` en las ruedas (giran y el visor tornea la llanta)
  - `aro` y `rin`
  - `doble` en las láminas abiertas
  - `rol: "visor_fijo"` en la farola (esconde el visor genérico)
  - `padre: "escapeFabrica"` en el escape (esconde el escape genérico)
  - `placa`, `manubrio`, `pantalla` (reloj) y `zonas` (calcas)
  - `interno` para Rayos X: se copiaron los 19 internos de la Boxer CT 100, trasladados al motor.

## Trampas

- **Rin chico**: Tripo deja el aro unos 2 cm más chico que un rin de 18" (asiento a 0,229 m de radio, pestaña a ~0,236 m), y la llanta parece enorme. Hay que medir el aro contra la ficha y escalarlo **parejo** alrededor del eje. Los rayos se estiran solo de la maza hacia afuera y el talón de la llanta va al aro. El radio exterior de la llanta no se toca: es la altura del eje y apoya en el piso.
- **No reemplazar geometría de Tripo por formas planas** (la elipse de la v4 fue el error). Si hay que rehacer algo, se construye alrededor de la superficie de Tripo.
- Recortar el lente deja un **hueco en el carenado**: siempre hay que taparlo (reflector) y cubrir el corte (aro).
- La reflexión de ejes invierte el sentido de las caras: hay que invertir los índices o todo sale al revés.
- Si al visor le falta `padre` o `rol`, deja la pieza genérica dibujada encima. Hay que revisarlo en el visor buscando mallas visibles que no sean del GLB. La pata lateral genérica sigue visible porque es pieza protegida: falta resolverlo.
- Panel del navegador oculto: `requestAnimationFrame` no corre y la ficha `/garaje/<pk>/` no arranca el 3D. Hay que usar `/vista-3d/`, esperar ~1,5 s después de mover la cámara (`__visor.vista` o `_ctl`) y llamar a `__visor.cuadro()` antes de la captura.
- `__visor._reencuadrar()` devuelve cientos de puntos: no hay que imprimirlo.
- Blender con 8 GB de RAM: uno solo a la vez.

## Qué cambiaría

- **Llantas integradas con el rin** (lo único que el usuario pidió mejorar): hoy el visor tornea la llanta con un perfil medido y queda una franja entre el talón y la pestaña del aro. Haría el talón **dentro** de la pestaña (radio interior = pestaña − 4 mm) y una pestaña con labio redondeado. Habría que pasar al visor un perfil fijo (`extras.torno` con radios de talón y pestaña), activado solo por el GLB que lo pida.
- Bombillo encendido más vistoso: un emisor más grande dentro del reflector, o un anillo emisivo.
- Sumar al script final los pasos 1-4, que hoy viven en `privado/`, para que todo el flujo esté en `herramientas_3d/<moto>/` y un modelo de una sola malla entre por la misma puerta. Antes de armar haría falta un paso de despiece (islas, bisect por planos y normales).
