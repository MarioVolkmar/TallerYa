---
name: moto-3d-tripo
description: Convierte un modelo 3D de moto generado con Tripo (un GLB de una sola malla, millones de triángulos y textura horneada) en el GLB liviano que usa el visor de TallerYa, con piezas separadas y con nombre, bordes lisos entre piezas, luces y discos limpios, placa en su sitio y piezas internas con forma real para Rayos X. Úsala cuando el usuario envíe un GLB de Tripo de una moto y pida «reconstruir», «adaptar» o «montar en la página» ese modelo, o pulir uno ya convertido.
---

# moto-3d-tripo

Toma el modelo de Tripo como base y lo deja como modelo realista de la línea. Motos hechas: NMAX 155 (58,6 MB y
1,9 M de triángulos con textura → 1,2 MB, 64 piezas) y AKT NKD 125 (0,8 MB y 47 mil triángulos sin textura →
0,96 MB, 55 piezas) y Bajaj Boxer CT 100 (49 mil triángulos sin textura → 1,03 MB, 54 piezas, `fichas/boxer100.py`) y Yamaha XTZ 150
(48 mil sin textura, girada → 0,97 MB, 52 piezas, `fichas/xtz150.py`).

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

`S` = carpeta `scripts/` de esta skill, `T` = carpeta de trabajo. El GLB de entrada se copia a una carpeta propia: es
un archivo descargado.

1. **Inspeccionar antes de nada** (cabecera JSON del GLB): cuántos triángulos y si trae textura. Tripo entrega dos
   clases de archivo y cada una va por un camino:
   | Entrada | Simplificar | Reglas |
   |---|---|---|
   | Pesado con textura (NMAX: 58,6 MB, 1,9 M de triángulos) | sí, pasos 3 y 5 | forma + color (`m.color()`) |
   | Liviano sin textura ni UV (NKD: 0,8 MB, 47 mil) | no: copiar `w_*.bin` a `s_*.bin` y no poner `RAZON` | solo forma |
2. `extraer.py entrada.glb T` y `preparar.py T <distancia entre ejes en m> [giro]` (de la ficha de la moto; `preparar`
   mide los ejes por la huella de las llantas y escala). Si Tripo entregó la moto a lo largo de z (XTZ 150), `preparar`
   se detiene y pide `giro` 90 (manubrio en +z) o 270 (en −z). Guarda los centros de rueda en `w.json`, y `medir.py`
   (`S T`) parte de ahí con un ajuste iterativo: ya no trae los de la NKD fijos.
3. Solo si es pesado: `node simplificar.mjs T 160000` (en una carpeta con `npm install meshoptimizer`).
4. **Ficha de la moto**: copiar `fichas/nkd125.py` a `fichas/<moto>.py` y ajustar. La ficha tiene `cortar(m)` (reglas
   sobre `motor.Corte`), `internos(k)` (piezas de Rayos X con `formas.py`) y, opcionales, `RAZON`, `MEZCLA`, `ISLAS`.
   **El motor (`motor.py`) no sabe nada de ninguna moto**: campos, plantillas, pliegues, ruedas, disco nuevo, reparto,
   islas y render de revisión viven ahí.
5. **Una vuelta = un comando**: `ciclo.py S T S/fichas/<moto>.py T/salida.glb [--ver "der;640;None+atras;1100;(caja)"]
   [--solo stop,faro] [--hasta cortar] [--N carpeta_meshoptimizer]`. Corta, aligera por pieza (solo si la ficha trae
   `RAZON`), hace los internos y exporta; imprime el cronómetro por paso y lo agrega a `T/tiempos.jsonl`.
   Lo lento (suavizados, pliegues, componentes) se guarda en `T/cache` por la huella de sus datos: cambiar una regla
   no recalcula las demás.
6. Copiar a `garaje/static/garaje/modelos/`, registrar en `MODELOS_TRIPO` de `moto3d/glb.js` y subir `?v=`. La clave
   es una expresión regular contra el nombre de la línea ("Boxer CT 100"): con espacios, usar `"boxer[ _-]*ct[ _-]*100"`
   y que no choque con otra línea (la CT 125).

`fichas/nmax155_cortar.py` y `nmax155_internos.py` son la ficha de la NMAX en el formato viejo (un programa
suelto por paso, con `por_pieza.mjs` y `exportar.py` aparte): sirven de ejemplo de reglas **por color**; para
retocar la NMAX conviene pasarlas antes al formato nuevo.

### Tiempos medidos

| Paso | NMAX (formato viejo) | NKD (motor + ficha) | Boxer CT 100 | XTZ 150 |
|---|---|---|---|---|
| Extraer + preparar | ~1 min | 2,5 s | 3 s |
| Simplificar | ~1 min | no hizo falta | no hizo falta |
| Una vuelta cortar → exportar | 1,5–2 min | 4,4 s (14 s con render de revisión) | 6 s (11 s con render) |
| Render de revisión, por vista | ~20 s | 3,4 s | ~1,5 s |
| Vueltas hasta la primera entrega | ~25 | 5 | 5 (6 renders leídos) |
| Del GLB a la página | varias horas | ~25 min | ~13 min (con pruebas y capturas) | ~17 min (3 vueltas, 6 renders) |

Lo que más pesa ahora no es la máquina sino **mirar**: cada render o captura que se lee cuesta más que la vuelta.
Pedir en un solo `--ver` todas las vistas de una ronda y en la página armar una hoja de varias vistas por captura.

### Modelos sin textura (aprendido en la NKD)

- No hay `claro` ni `oscuro`: la pintura se delimita con **plantillas en la vista lateral `(x, y)`** (tanque, asiento,
  tapas) más un tope en `|z|`, con el borde llevado al pliegue (`m.pliegue`). Los pliegues entre tanque, asiento y
  tapa vienen bien marcados en la malla y el borde sale limpio.
- Medir antes de dibujar (`scripts/medir.py`, hecho para la NKD: ajustar los centros de rueda y las cajas): ruedas con `m.rueda`, histograma de `z` cerca del eje
  para hallar el plano del disco, y cajas de los bultos lejos del plano medio (direccionales, reflectores, espejos).
- **Direccional de gota**: el cuerpo es una caja en `(x, y, |z|)`; la mica es la mitad que mira hacia afuera del eje
  (`gotas()` en la ficha de la NKD). Un nodo por lado para que cada una tenga su halo.
- Faro redondo: círculo en `(z, y)` **sin** `pliegue` (el relieve interno del lente se lleva el borde) y con el tope
  en `x` bien atrás del lente: el lente va inclinado y un tope justo lo corta por arriba.
- Rueda de rayos: `rin` = todo lo que queda dentro del aro y cerca del plano medio (aro, rayos y manzana juntos).
- Islas: con piezas delgadas (barras, tallos) bajar `ISLAS = {"isla": 24}`; con 60 se las come la pieza vecina.
- **Mirar los dos lados antes de quitar algo** (Boxer): en la vista de atrás parecía haber un silenciador a cada lado
  (Tripo suele hacer la moto simétrica), pero el de la izquierda era el guardacadena. Confirmar con `izq` y `der`.
- **Guardabarros pegado a la llanta** (Boxer): Tripo los funde y el radio no los separa. Se separan por el ancho: la
  llanta no pasa de |z| 0,037 y las faldas del guardabarros van a 0,04–0,075; arriba, lo que pasa de R + 0,012. Rango
  de ángulos según el modelo (en la Boxer cubre de 45° a −150°: arriba y atrás).
- **Tripo repite piezas a los dos lados** (XTZ 150: el silenciador alto, que solo va a la derecha, salió también a la
  izquierda): la copia falsa va a `_quitar` (rígida en `ISLAS`, así no queda nada colgando).
- **Deformar tras cortar**: `m.deformaciones.append(fn)` (fn recibe y devuelve las posiciones) se aplica a la malla ya
  cortada, por región y no por pieza, así no se abren grietas entre piezas (XTZ: rin 21 estirado alrededor del eje).
- **Mirar en la foto de qué lado van los discos** (XTZ: los dos a la derecha; el disco del modelo estaba a la izquierda).
- **Las dos ruedas pueden salir del mismo tamaño** aunque la moto real tenga 21" y 18" (XTZ): el rin se mide en el
  perfil (`PERFIL = True`: salto de |z| de ~0,015 a ~0,035), no se calcula con las pulgadas.
- **Ruedas de distinto tamaño** (Boxer: la delantera 10 % grande): en la ficha `ESCALAR = [{"piezas": ["llanta_del", "aro_del",
  "rayos_del", "tambor_del"], "eje": "eje_del", "factor": 0.906}]` y `NIVELAR = True`. `exportar.py` escala esas piezas
  alrededor del eje y gira toda la moto en (x, y) alrededor del eje trasero para que las dos ruedas toquen el piso, con ejes,
  placa, pantallas, manubrio, acomodar y calcas. El guardabarros queda con más holgura sobre la llanta.
- Guardabarros: la falda de adentro baja hasta R − 0,08 junto a la llanta; la cara que mira al eje es guardabarros.
- Perfil radial de la rueda: `PERFIL = True` en la ficha de la Boxer imprime el |z| (p90) por anillo de 1 cm.

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

Si el usuario no tiene una moto de esa línea, lo más rápido y sin tocar la base (XTZ 150): abrir una de sus motos,
`fetch` de la misma página, cambiar `linea` en el JSON de `#datos-moto`, `document.write`, `window.__visor = null` y
volver a importar `moto3d.js` con `?x=<fecha>` (los módulos quedan en caché y no se vuelven a ejecutar solos). Si no:
en `manage.py shell`, copiar una de sus motos con `pk=None`, la línea
nueva y un apodo de prueba; revisar en `/garaje/<pk nuevo>/` y borrarla al terminar (comprobando el apodo antes). Si el
visor abre en Rayos X, clic en `#visor [data-modo="moto"]`.

`/garaje/<pk>/` (las líneas de `MODELOS_TRIPO` cargan su modelo por defecto). Con el panel del navegador oculto la
página mide **0 px de ancho** y el visor no arranca: primero `resize_window` a 1280 × 800, recargar, llevar `#visor`
a la vista (`scrollIntoView`) y, si aún no arranca, insertar a mano el `<script type="module">` de `script[data-modulo]`, esperar
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

## Ajustes tras la revisión del usuario en la NKD (19-nov-2026)

- **Rueda de rayos en tres piezas**: `caucho.llanta_*`, `metal.aro_*` con `aro: true` y `cromo.rayos_*` con `rin: true`.
  Con todo en `rin.*`, el color de rines de Personalizar pintaba la rueda entera; así pinta solo el aro, como en la
  moto genérica, y los rayos se esconden al elegir otro estilo de rin.
- **La rueda del modelo no es un círculo perfecto**: el ajuste sale de la mitad de abajo y arriba la banda de rodadura
  llega a R + 0,02. Con el tope de la llanta en R + 0,008, ese pedazo caía en el guardabarros y se pintaba con la moto
  (lo vio el usuario al cambiar de color). Medir el radio por ángulo y dar tope holgado fuera del guardabarros; debajo
  de él, la llanta es la corona que mira hacia afuera del eje. **Probar siempre un color vivo de pintura** y mirar
  ruedas y cables: en una moto negra estos derrames no se ven.
- **Lista de salida antes de entregar** (tres cosas que el usuario vio «en el aire» en la NKD):
  1. Mallas genéricas que siguen visibles: en la consola, listar las mallas visibles sin `userData.glb`; solo deben
     quedar pata y placa. Un `vidrio` es el visor genérico: falta `rol: "visor_fijo"` en algún nodo.
  2. Calcas de fábrica: definir siempre `calcas_fabrica` con `en: [x, y]` sobre el modelo; la posición relativa de la
     línea genérica se sale del tanque. Mirarlas de cerca desde los dos lados.
  3. Pantallas: si la cara del modelo no es plana, no poner el plano encima; hacer una carcasa (`m.extra` con
     `formas.revolucion`) que salga de la cara y asentar la pantalla sobre ella.
- **Tablero**: `pantalla` acepta una lista. Reloj redondo: `{c, n, tam: [diámetro, diámetro], redonda: true, dibujo:
  "velocimetro" | "tacometro"}` (uno por reloj); el rectangular de la NMAX sigue igual. Apagada se ve negra.
- **Tanque arrugado**: la malla de Tripo trae arrugas reales. En la ficha, `ALISAR = {"pintura.tanque": 10, …}` alisa la
  superficie (solo vértices interiores, sin encoger) y `SUAVE = 3` alisa las normales de las piezas lisas.
- **Labrado de llantas**: lo pone `glb.js` solo a todo nodo `caucho.llanta_*` con `eje` (relieve envuelto alrededor
  del eje; no hace falta UV en el GLB). Vale para todas las motos.
- **Pata**: la animación de meter y sacar el gato mueve `moto.pata`, la pata de la moto genérica, que se conserva con
  el GLB. No recortar una pata propia del modelo como pieza móvil.
- **Ojo, por confirmar**: el visor pone el escape en −z y con x adelante e y arriba eso es la izquierda del piloto;
  el modelo se exporta espejado para seguir esa convención (escape, disco y cadena quedan del lado contrario al real).

## Capturar con el panel oculto

Si al navegar sale la página «Sin conexión» o el visor carga un `glb.js` viejo, es el service worker del sitio dentro
del panel (sus peticiones fallan y responde desde caché): `(await navigator.serviceWorker.getRegistrations())` y
`unregister()` en la página, y volver a navegar. Confirmar siempre qué `?v=` cargó: `v._moto.raiz.userData.glb`.

`screenshot` recorta distinto según el tamaño del panel. Lo estable: `<img>` fijo a `100vw × 100vh` con
`object-fit: contain`, cargado con `canvas.toDataURL()` justo después de `render`. Antes de mover la cámara:
`v._ctl.enableDamping = false; v._ctl.update()` (si no, arrastra el giro pendiente de Personalizar). La página no deja
enviar la imagen a otro puerto (política de contenido).

Para gastar pocas capturas: una función que rinde varias vistas `[posición, objetivo, fov]` en un solo lienzo de
2 × 3 y lo muestra en el `<img>` (sin `await img.decode()`: con el panel oculto no termina nunca). La captura queda
guardada en disco (la ruta sale en el resultado de `screenshot`) y de ahí se copia para enviarla al usuario. Para
revisar bordes en una moto negra, cambiar `M.pintura.color` solo en memoria y devolverlo después.

## Errores ya vistos

- Clasificar por cara → bordes dentados. Siempre recortar por campo.
- Los discos del modelo son pintura sobre una superficie plana: los agujeros no existen. Se regeneran.
- La luz trasera viene gris en la textura y se confunde con la pintura: va por plantilla.
- Si el dato `placa` no llega al GLB, la placa queda en la posición genérica (debajo del guardafango).
- Sin `rol: "visor_fijo"` queda flotando el visor de la moto genérica.
- El modelo de Tripo trae errores de anatomía (en la NMAX, del lado izquierdo no hay tapa de transmisión): avisar.
