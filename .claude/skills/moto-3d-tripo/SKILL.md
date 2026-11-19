---
name: moto-3d-tripo
description: Convierte un modelo 3D de moto generado con Tripo (un GLB de una sola malla, millones de triángulos y textura horneada) en el GLB liviano que usa el visor de TallerYa, con piezas separadas y con nombre, bordes lisos entre piezas, luces y discos limpios, placa en su sitio y piezas internas con forma real para Rayos X. Úsala cuando el usuario envíe un GLB de Tripo de una moto y pida «reconstruir», «adaptar» o «montar en la página» ese modelo, o pulir uno ya convertido.
---

# moto-3d-tripo

Toma el modelo de Tripo como base y lo deja listo para `?modelo3d=tripo`. Primera moto hecha: NMAX 155
(58,6 MB y 1,9 M de triángulos → 1,5 MB y 98 mil, 60 piezas).

## Idea central

El modelo llega como **una sola malla fundida**. No se clasifica triángulo por triángulo (queda dentado): cada
pieza es un **campo por vértice** (positivo = adentro) y las caras que el borde atraviesa **se parten por donde el
campo vale cero**. Los campos se arman con tres ingredientes:

- **Regiones analíticas**: radios respecto a los ejes de rueda, planos, bandas (`banda(v, a, b)`).
- **Plantillas**: polígonos dibujados sobre la vista de frente o de atrás (faros, direccionales, stop). Son la forma
  de dar bordes exactos a las luces, que en la textura de 512 px no se distinguen bien.
- **Color suavizado** de la textura (claro = pintura, cálido = dorado o ámbar).

Se combinan con mínimo (Y), máximo (O) y signo contrario (NO), y se aplican **en orden de prioridad**.

## Pasos (todos con `venv/Scripts/python.exe -I`, carpeta de trabajo en el scratchpad)

`S` = carpeta `scripts/` de esta skill, `T` = carpeta de trabajo, `N` = carpeta con `npm install meshoptimizer`
(copiar ahí los dos `.mjs`). El GLB de entrada se copia a una carpeta propia: es un archivo descargado.

1. `extraer.py entrada.glb T` → posiciones, normales, UV, índices y texturas.
2. `preparar.py T` → color por vértice, suelda por posición, mide los ejes por la huella de las llantas y escala a
   la distancia entre ejes real (**cambiar el 1.34** por la de la ficha de la moto).
3. `node simplificar.mjs T 160000` → primera reducción, cuidando normales y color.
4. `cortar.py S T` → reparte en piezas (`--ver "frente;1000;(caja)+atras;1000;(caja)"` pinta el corte para revisar).
   **Aquí están las reglas de la moto**: copiar el archivo y ajustar regiones y plantillas mirando las vistas con
   cuadrícula (`ver2.py`). Los discos se quitan y se generan nuevos (corona con agujeros reales).
5. `node por_pieza.mjs T` → segunda reducción por pieza con el borde bloqueado (no abre rendijas).
6. `internos.py S T` → batería, cárter y aceite, bujía, filtro de aire, radiador, cigüeñal, pistón y correa con
   poleas, hechos con `formas.py` (revolución, tubo, extrusión con bisel). Van con `interno: true`.
7. `exportar.py S T salida.glb` → GLB cuantizado, espejado (el visor pone el escape en −z) y con normales lisas en
   pintura, lentes y visor (mezcla con la normal geométrica: sin eso los reflejos salen arrugados).
8. Copiar a `garaje/static/garaje/modelos/`, registrar en `MODELOS_TRIPO` de `moto3d/glb.js` y subir `?v=`.

## Contrato con el visor (`moto3d/glb.js`)

Nodo = `material.parte`; el material sale de `moto.M` (más `plastico`, `negro_brillo`, `titanio`, `dorado`,
`faro`, `disco`, que crea `glb.js`). Extras por nodo:

| Extra | Efecto |
|---|---|
| `pieza` | Va al grupo de mantenimiento y reemplaza lo genérico (llantas, frenos, suspensión, motor, correa…) |
| `eje: [x, y]` | Centro real de la rueda: el pivote se lleva ahí para que gire sin cabecear |
| `rin`, `padre` | Rin de fábrica; grupo destino (`escapeFabrica`, `espejos.fabrica`) |
| `placa: {c, incl, tam}` | Dónde va la placa (se mide sobre el guardafango) |
| `manubrio`, `acomodar` | Reubican espejos y accesorios de Personalizar |
| `rol: "visor_fijo"` | Oculta el visor genérico sin esconder el del modelo |
| `interno: true` | Solo se ve en Rayos X |
| `sin: ["accesorios.parabrisas", "espejos.puntas"…]` | Quita de la moto opciones de Personalizar cuya pieza genérica desentona con el modelo; el cajón deja de ofrecerlas (decisión del usuario, 19-nov-2026: en la NMAX se quitaron parabrisas alto, cubremanos y retrovisores alternativos; quedan baúl y luz LED) |

## Verificar en la página

`/garaje/<pk>/?modelo3d=tripo`. Con el panel del navegador oculto el visor no arranca solo (usa
`requestAnimationFrame`): insertar a mano el `<script type="module">` de `script[data-modulo]`, esperar
`window.__visor` y pintar con `v._ren.render(v._esc, v._cam)` antes de cada captura. Revisar siempre de cerca:
faros, direccionales, stop, discos, cola con la placa, uniones entre pintura y plástico, y Rayos X.

## Reglas para bordes limpios (aprendidas en la NMAX)

- **El borde de una luz lo define solo su plantilla.** Nada de condiciones de normal en la misma regla: meten un
  segundo borde irregular. Para descartar lo que queda detrás, un plano (`x - 0.55`).
- **La plantilla es solo una guía: el borde final va al pliegue del modelo** (`malla.a_pliegues`, en `cortar.py`
  `pliegue(dist, valido, banda)`). Dentro de una franja de ~1 cm a cada lado de la plantilla, cada vértice se queda
  con el lado al que llega más barato, y cruzar un pliegue o un cambio de tono cuesta caro. Así el lente del faro
  sigue su hueco real. No usarlo para detalles **dentro** de un lente (los ojos del faro): ahí el relieve es ruido
  y el borde sale rasgado.
- **Antes de dibujar la plantilla de una luz, mirar el original desde tres vistas** (arriba, lado y atrás, con
  `ver2.py` a ~2000 px/m) y dibujarla en la vista donde se ve la **arista que la delimita**. En la cola de la NMAX el
  stop envuelve la esquina hasta una arista inclinada que solo se ve de lado, y la direccional es un triángulo largo
  sobre el costado: definidos desde atrás se veían desbordados desde arriba. Revisar el resultado en esas mismas
  tres vistas, no solo en la que se dibujó.
- **Una plantilla vista desde atrás también pinta los costados** que caen dentro de su silueta (el stop se derramaba
  por los lados de la cola): acotar con un plano o una segunda condición de región.
- **La plantilla se dibuja en la vista hacia donde mira el lente**: faro y stop de frente o de atrás `(z, y)`; la
  direccional delantera mira de lado y va en `(x, y)`. Dibujada de frente salía con dientes y una franja de pintura.
- **Pintura contra plástico**: el campo `claro` se cierra (`malla.cerrar`), se abre (`malla.abrir`) y se suaviza antes
  de cortar. Sin eso, las líneas oscuras de la textura dejan astillas negras dentro de la pintura.
- **Mirar el original antes de nombrar una luz**: en la NMAX el stop se comía las direccionales traseras (los dos
  triángulos a los lados); los cilindros dorados son depósitos de amortiguador, no direccionales.
- Piezas de un solo color con sombras en la textura (depósito dorado): por región, no por color.

## Luces, tablero y calcas (extras que entiende `glb.js`)

- `lampara: {tipo: "faro" | "stop" | "direccional"}`: un nodo por lente y por lado. El visor saca de ahí el haz, los
  halos y el parpadeo de «Encender»; sin eso salen de donde estaban las luces de la moto genérica.
- Las direccionales **delanteras** de la NMAX también son de mica transparente con bombillo ámbar (`mica_dir`), en
  la parte baja del frontal.
- Para capturar el parpadeo real: `v.vivo(true, true)` y esperar a que `M.mica_dir.emissiveIntensity > 3` antes de
  pintar (con el panel oculto el ciclo corre lento y un tiempo fijo no acierta).
- `pantalla: {c, n, tam}`: plano con el dibujo del tablero digital; usa `M.pantalla`, que el visor enciende solo.
  El dibujo va solo en la luz emitida (`emissiveMap`, color casi negro, `userData.soloEncendida`): apagada, negra.
  Va en el recuadro que trae el modelo (buscar la zona clara y plana), no donde «debería» ir.
- `zonas: [...]` en cada panel pintado: sin eso no se pueden pegar calcas propias en `pintura2` ni salen las de
  fábrica (que buscan la zona `lateral`).
- `calcas_fabrica: [...]` (en el panel `lateral`): calcas de fábrica propias del modelo, cada una con `en: [x, y]`
  (punto exacto sobre la moto) en vez de la posición relativa de la línea. Se toman de una foto lateral de la moto
  real; siguen la regla de `calcas_fabrica.js`: texto con tipografía libre, nunca el emblema de la marca.
- **Dos piezas vecinas que no deben montarse comparten un solo campo de borde** (la arista entre stop y micas):
  una usa `campo - SEP` y la otra `-campo - SEP`; el filete de carrocería que queda en medio las deja definidas.
- **Confirmar con fuentes qué es cada luz, y no solo con una foto apagada.** En la NMAX las direccionales traseras
  van dentro de la unidad del stop, con mica transparente y bombillo ámbar (los triángulos junto al stop, material
  `mica_dir`: clara apagada, ámbar al parpadear); el óvalo ámbar del tallo del guardafango es un **reflector**
  (material `reflector`, no alumbra). Una foto lateral apagada engaña: lo único ámbar que se ve es el reflector.
  Buscar cómo se cambia el bombillo o fotos con la luz encendida.
- `acomodar`: revisar baúl y parabrisas con la moto personalizada; quedan flotando si el punto no toca el modelo.

## Capturar con el panel oculto

`screenshot` recorta distinto según el tamaño del panel. Lo estable: `<img>` fijo a `100vw × 100vh` con
`object-fit: contain`, cargado con `canvas.toDataURL()` justo después de `render`. Antes de mover la cámara:
`v._ctl.enableDamping = false; v._ctl.update()` (si no, arrastra el giro pendiente de Personalizar). La página no deja
enviar la imagen a otro puerto (política de contenido).

## Errores ya vistos

- Clasificar por cara → bordes dentados. Siempre recortar por campo.
- Los discos del modelo son pintura sobre una superficie plana: los agujeros no existen. Se regeneran.
- La luz trasera viene gris en la textura y se confunde con la pintura: va por plantilla.
- Si el dato `placa` no llega al GLB, la placa queda en la posición genérica (debajo del guardafango).
- Sin `rol: "visor_fijo"` queda flotando el visor de la moto genérica.
- El modelo de Tripo trae errores de anatomía (en la NMAX, del lado izquierdo no hay tapa de transmisión): avisar.
