# Contrato con el visor, verificar en la pagina y capturar

## Contrato con el visor (`moto3d/glb.js`)

**Lados (arreglado el 19-nov-2026):** dentro del GLB y de la moto genérica, x adelante, y arriba y **+z = izquierda del
piloto** (cadena, pata, caja del CVT; el escape va a **−z**). `exportar.py` ya lo deja así (las fichas trabajan con +z =
escape y se espeja al exportar). El visor espeja la raíz de la moto (`moto.raiz.scale.z = -1` en `moto3d.js`), así que
en la escena el escape queda en +z mundial, que con el frente en +x es la **derecha**, como en la moto real. No espejar
nada más por cuenta propia (ni el GLB ni `glb.js`): textos de textura se compensan con `espejarTextura` (`comun.js`) y las
calcas se proyectan en el mundo. Antes del arreglo todo el visor salía en espejo (escape a la izquierda).

**Chequeo del lado del escape (obligatorio en cada moto nueva o regenerada):**
1. En el GLB: el nodo `*.escape*` debe tener el centro en **z < 0**, y cadena/corona/caja del CVT en z > 0
   (lectura rápida del JSON del GLB: `translation` + centro de `min`/`max` del accesor de posiciones).
2. En la página, con `v = window.__visor`: centro del escape en el mundo (`localToWorld`) con **z > 0** y
   `v._moto.raiz.scale.z === -1`. Vista trasera (`v.vista(-2, 1.15, 0)`): el escape se ve a la derecha de la imagen
   y la placa se lee bien.
3. Comparar con al menos una foto real del lado del escape (casi todas: escape a la derecha, cadena a la izquierda;
   NMAX: escape a la derecha y CVT a la izquierda). Discos: mirar la foto (la NMAX lo lleva al lado opuesto del escape).

**Llantas torneadas (19-nov-2026):** el corte de Tripo nunca deja la llanta como rueda completa (donde toca guardabarros,
horquilla o basculante quedan caras en el cuerpo fijo) y al girar se veía el hueco dando vueltas. `glb.js`
(`tornearLlanta`) rehace todo nodo `caucho.*llanta*` con `eje` como sólido de revolución medido sobre la propia malla
(radio exterior por franjas de ancho, al 98 %; radio interior en el asiento del aro; 3 mm de holgura que tapa los pedazos
fijos) con el mismo labrado. Regla: en la ficha basta que la llanta lleve `eje` correcto y el ancho real; no hace falta
que salga completa ni regenerar. Aro y rayos siguen siendo los de Tripo. Chequeo: girar `r.pivote.rotation.z` 45° y
comparar con 0° de cerca (en la NKD, antes del arreglo, se veía una muesca arriba de la llanta delantera).

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

