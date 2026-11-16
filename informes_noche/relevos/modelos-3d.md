# Relevo — sesión "Modelos 3d"
(Iba en privado/relevos/, pero esa carpeta está bloqueada para los agentes en los permisos.)

## Reglas
- Reportar solo a "Auxiliares" (local_9657d3fe-d634-45af-9c61-9d6539d08def) y solo al TERMINAR una tarea completa: nada de "recibido" ni "sigo". 2–5 líneas.
- Sin commit, push ni despliegue hasta que el usuario lo pida por Auxiliares.
- Una sola medición o prueba pesada a la vez en todo el proyecto. Capturas solo si hacen falta (el panel del navegador suele estar oculto: medir con readPixels o `__visor.info()`).
- No tocar `construir.js` ni `rasgos.js`: son de la sesión "3D: fidelidad de las 24 motos a sus fotos" (local_02a45fd7-2879-4cef-b052-09559ddc6fd2). Las medidas las hace "Auditor 3D" (local_0527f3f5-c61f-4148-a735-459b6ff12066).
- Español; pocos tokens (CLAUDE.md).

## Archivos míos
- `garaje/static/garaje/js/moto3d.js`: entrada; escena, modos (estado/rayos/moto), noche/encender, personalización, carga en dos etapas.
- `garaje/static/garaje/js/moto3d/`: `geometria.js` (unirEstaticas, unirDecorado, subdividir), `cache.js` (IndexedDB, CACHE_VERSION=4), `comun.js` (CALIDAD: alta seg 0,72 / baja 0,42; ceder, medir), `texturas.js`.
- `garaje/static/garaje/js/moto3d-carga.js`: carga diferida + modulepreload (incluye rasgos.js; si fidelidad crea más módulos, sumarlos aquí y en `vista_3d.html`).
- `garaje/templates/garaje/vista_3d.html` (vitrina de la portada; postMessage entrar/salir/noche/dia; avisa "moto-lista") y `moto.html` (importmap + cargador tras la sección del visor).

## Estado actual (todo sin commit)
- Carga: primer cuadro sin sombras ni reflejos (luz de relleno) y getUniforms precalentado por tandas en un píxel del lienzo escondido. Después: reflejos (import dinámico de RoomEnvironment/DecalGeometry) + sombras con compileAsync y fundido de 300 ms; en la vitrina la entrada espera esa etapa. Calidad baja (móvil): una sola etapa, sin shadowMap, reflejos desde el inicio (19 programas).
- Rendimiento: unirEstaticas por material (ficha: dentro de cada pieza; vitrina: entre piezas). Antes de unir se restauran los materiales originales y luego se reaplica el modo. 30 fps en vitrina móvil. pagehide libera la GPU.
- Noche: luces siempre encendidas de noche; faro/stop desde `moto.anclas` (faro, stop, direccional_di/dd/ti/td) o extremos de M.luz/M.stop; cono de luz y halos con mezcla normal (lo aditivo no se ve en lienzo transparente).
- Calcas: recorte de la malla cerca de la calca antes de DecalGeometry.
- Debug en `__visor`: info().tiempos/etapas, cuadro() (ojo: llama a pintarVivo), sombras(true), pesadas(), cajas(), _moto/_esc/_ren.

## Pendientes
- Auditor 3D: medir móvil (tareas largas tras el primer cuadro, objetivo ≤200 ms) y 4G en Render (≤3 s; si no llega, el usuario decide minificar).
- ~~Cono y halos de noche en 6 familias~~ HECHO 2026-11-14 (por píxeles, iframes srcdoc con specs cambiadas): naked, clásica, carenada, semi, enduro, scooter → cono y halos visibles, faro al frente (0,72–0,95 del largo), stop atrás (0,08–0,17), aportan 3,5–6 % del cuadro. Fallo hallado: tipo "sport" sin carenado no arma faro delantero con M.luz ni ancla → el cono salía de la luz de placa. Protección en moto3d.js (faro detrás del centro = sin faro); Fidelidad ya le puso faro redondo (ancla 0,53/0,90); verificado: cono y halo delanteros al frente, stop atrás.
- Presupuesto ≤60 calls / ≤60k triángulos por moto: lo cumple la sesión de fidelidad en cada rediseño.

## Encuadre de la portada (2026-11-14, hecho, sin commit)
- CSS `.portada-carrusel` (tallerya.css, bloque ≥768): ≥1280 px el lienzo (35rem) se centra en el hueco entre el título y la ficha (left = margen del contenedor + 28,5rem), más alto que la moto y con máscara (bordes laterales y abajo desde 76 %) para que el cono y la sombra se desvanezcan. 768–1279: arriba a la derecha (36vw × 16rem), encima de la ficha. Móvil: máscara abajo desde 88 %.
- moto3d.js `ajustarTamano` (vitrina): encuadre normalizado por la caja real de cada modelo (`tamanoMoto()`: sin lo plano del piso ni el cono; se vuelve a medir tras la personalización porque los accesorios cambian el tamaño). Diagonal horizontal = 56 % del ancho (67 % en celular, ventana padre <768), alto ≤60 %, la cámara mira al centro de la caja; en celular el blanco baja 0,12 m. `__visor._cam/_ctl` para depurar.
- Medido por píxeles (panel oculto: hay que parar el carrusel y poner la moto en reposo, ver scratchpad medir_portada.js): 1944 → moto 1013–1257 (título hasta 981, ficha desde 1295); 1280 → 681–925 (543 / 963); 1279 → arriba, termina en y 285 (ficha 291); 768 → 535–667 (título 528); móvil igual que antes. Captura: informes_noche/relevos/portada-3d-1944.jpg.
- Sin sesión la portada es el dibujo SVG (portada-garaje), no el 3D: no tapa el texto; no lo toqué.
- Verificado (las 5 del carrusel + NMAX 2021, Dio, RC 200, Gixxer SF): todas ocupan 44–47 % del ancho en reposo; uniones de giros 0–135° sin tocar título ni ficha en 1944/1280/768; móvil sin corte abajo. Captura: informes_noche/relevos/portada-3d-aerox-1944.jpg.

## Otros cambios 2026-11-14 (sin commit)
- Cono del faro: ya no lo enciende `aplicarModo` (quedaba visible de día con opacidad 0 = 1 call); solo se ve de noche, encendida y en modo "moto".
- Visor de la moto: quitada la pestaña "Estado" (era igual a Rayos X). Rayos X es la vista por defecto; cualquier "estado" cae en rayos; `seleccionar()` desde Moto pasa a Rayos X; el realce de piezas con estado aplica en rayos. No había modo guardado en localStorage ni pruebas que lo mencionen.

## Más cambios 2026-11-14 (sin commit)
- Portada, zoom: el encuadre mide la moto por sus ruedas (entre ejes + radios) y los accesorios puestos (la caja de la carrocería variaba con la animación). La fracción del ancho la da la variable CSS `--encuadre` del carrusel (escritorio .85 con lienzo 38rem en CL+25.25rem hasta el borde inferior, desvanecido 6 % lados / 88 % abajo; tablet .56; móvil .67). A 1700 px las 5 motos miden ~390 px en reposo (87 % del hueco 753–1203) sin tocar ficha; a 45° rozan el final del párrafo (≤20 px, la Traviesa con baúl).
- Noche: luces solo con la moto encendida (`e = vivo.encendida || vitrina`); apagada de noche faro/stop/tablero/direccionales en 0, sin cono ni halos.
- Calcas de fábrica: `moto3d/calcas_fabrica.js` (datos por línea con regex, fuentes libres de Google Fonts por marca —Saira/Teko/Exo 2/Kanit/Orbitron/Racing Sans One/Rajdhani—, sin emblemas; atlas de una fila por calca). En moto3d.js `aplicarFabrica()`: ubica por zona (tanque/lateral/cola/frontal) con un rayo lateral, DecalGeometry más honda (≤0,3 m) y TODO en una malla = 1 call (~500–3000 vértices). Se carga en `extras()` aparte (si falla, reintenta y no tumba reflejos ni calcas propias). Personalizar → Calcas: subpestañas "De fábrica" (casillas + Restaurar todas) y "Personalizadas". Se guarda en `estilo.sin_fabrica` (models.limpiar_estilo valida ids, ≤8) + prueba nueva.
- Ojo: con RAYOS X por defecto la ficha arranca con ~120 llamadas (bordes de cada malla en rayos); en modo Moto ~50.
- Luces ancladas (2026-11-14): cono por lente faro principal, haz, halos chicos de faro/stop y ámbar de direccionales (solo al parpadear) nacen en `anclas.lamparas` (pos + dir, de construir.js/fidelidad). Verificado NKD, Aerox, RC 200 en 3/4 delantero y trasero. La Aerox trae 3 faros principal=true → 3 conos (avisado a fidelidad).
- Calcas de fábrica v2: formas nuevas (rayas, filete, número hueco `contorno`), color de gráfica por modelo con "vivo:#hex" (usa el secundario si es vivo y contrasta). NMAX y Aerox rehechas según sus fotos (manual_despiece/yamaha_*/fotos). Color por calca: `estilo.color_fabrica = {id: {p, s}}` (editor en "De fábrica" con principal/secundario y "Color original"; validado en models + prueba). Comparativa: informes_noche/relevos/calcas-fabrica-aerox-nmax.jpg.
- Rehechas según fotos (AKT 2026 / HF 100): NKD (flecha lima+bloque oscuro en el tanque, barra lima y "NKD" en la tapa), CR4 ("125" lima enorme, "CR4" hueco gris, filete en la cola), Dynamic Pro ("DYNAMIC" subiendo, filete lima, "125" en el escudo), Eco Deluxe (cuña plata/roja en tanque y tapa, "ECO DELUXE"). Formas nuevas "flecha" y "barra"; opción `angosto` (0–1) para formas más altas.
- Lote 2 según fotos: Gixxer (trazos claros, "GIXXER" del color de la versión, barra en la cola), GN 125 ("GN" rojo con borde oscuro sobre cuña roja, barra y "GN125F" en la tapa), Apache (zarpazos, "Apache" cursiva, "RTR"), Crypton (filete morado, "CRYPTON", "115", franja en el escudo), FZ25 ("FZ" plateado y "25"), MT-03 (barra celeste y "MT-03" cuadrado), XTZ ("XTZ"+cc plateado, bloques y barra). Forma nueva "trazos"; fuentes tvs_script y cuadrada. Comparativa: informes_noche/relevos/calcas-fabrica-6-motos.jpg. Verificadas sobre su propia geometría (specs de LineaMoto por línea, cargadas con la línea en vista-3d) midiendo el área de textura cubierta por calca (2.00 = completa en ambos costados): corregidos filete de la Dynamic Pro (salía cortado), bloques de la XTZ (cruzaban capas) y "125" de la CR4. Comparativa en 3/4: informes_noche/relevos/calcas-fabrica-6-motos-propias.png.
- Lote 3 según fotos: Pulsar NS ("200" con borde rojo, rayas, "NS"), Pulsar RS ("RS200", "PULSAR"), Duke ("200" naranja grande, filete, "DUKE"), RC 200 (cortes claros, "RC", "200" naranja, barra), CB125F ("CB" hueco, rayas rojas, "CB125F"), XR150L (cuña clara/oscura, "XR150L"), Dio ("Dio" cursiva), Wave, Boxer CT, Discover y Best (fotos pocas o dudosas: composición aproximada). Todas medidas sobre su geometría (2.00). Comparativa: informes_noche/relevos/calcas-fabrica-lote3.png.
- Pendiente: TT 125 sin fotos (queda la calca genérica).
- Primer cuadro de la ficha: boceto (materiales Lambert con el color de cada pieza, congelado como imagen sobre el lienzo) antes de compilar los sombreadores reales; aristas de Rayos X diferidas a requestIdleCallback (aplicarModo inicial 125→9 ms). Marcas nuevas en __visor.info().tiempos: unido, boceto, compilaAsync. Con el script del Auditor (copia en mi scratchpad/aud, salida mio-*.json): boceto 1,0–2,2 s (mediana ~1,4), cuadro real 1,1–3,0 s. Crypton móvil: 6 ms (pico 22), no se reproducen los 72 ms. Los "8 piezas blancas ffffff" del Auditor son el material invisible (MeshBasic visible:false) de las mallas agrupadas: artefacto de la prueba.
- Llamadas (2026-11-14): Rayos X 120→9 (bordes en 1 LineSegments, piezas sin estado con material visible:false pero tocables, piezas con estado agrupadas por estado/interna, la seleccionada aparte). Vista Moto: `agruparMoto()` junta por material todo lo fijo (sin ruedas ni gato) y deja las originales sin dibujar (siguen para calcas); calcas propias = 1 malla cada una. Ficha Moto: NKD 80→43, Aerox 71→45, NMAX acc. 80→47, RC 200 84→43; portada NKD 42. `info()` cuenta solo lo dibujado.

## Después de la 1 a.m. (2026-11-15) — resumen para retomar
Hecho (todo sin commit):
- Calcas de fábrica según fotos en 24/25 líneas (lotes 1–3 arriba); fuentes nuevas tvs_script/cuadrada; formas flecha, barra, trazos y opción `angosto`. Todas verificadas sobre su propia geometría (cobertura 2.00), re-verificadas tras los cambios de modelos de Fidelidad.
- Primer cuadro de la ficha: boceto Lambert + aristas de Rayos X diferidas (ver arriba). Boceto mediana ~1,4 s, cuadro real ~1,7 s (escritorio, método del Auditor). Reportado a Auxiliares.
Pendiente:
- TT 125: sin fotos, sigue con la calca genérica.
- Primer cuadro real >1,5 s: el resto es fuera del 3D (≈10 scripts de la página + three.js desde jsdelivr en frío). Sugerido preconnect a cdn.jsdelivr.net en la plantilla (no tocado; requiere aviso).
- Crypton móvil 72 ms del Auditor: no reproducido (6 ms); esperar nueva medición si insiste.
Archivos clave: `garaje/static/garaje/js/moto3d/calcas_fabrica.js` (LINEAS, FUENTES, dibujarForma), `garaje/static/garaje/js/moto3d.js` (bloque boceto antes de compileAsync, `bordes.listos`, marcas unido/boceto/compilaAsync). Scripts de medición en el scratchpad de la sesión (aud/medir2.mjs: `ACC=1 node medir2.mjs desktop|movil <ids>`), se pierden al reiniciar.

## Rayos X sin accesorios fantasma (2026-11-15, hecho, sin commit)
- Fallo: en Rayos X se veían en líneas el baúl, el parabrisas, etc. aunque no estuvieran puestos. Causa: `aplicarEstilo` oculta el GRUPO del accesorio (y de espejos, estilos de rin y escape de fábrica), pero `aplicarModo` solo miraba `obj.visible` de cada malla; los bordes y los grupos por estado se juntan en mallas colgadas de la raíz, así que no heredaban el padre oculto.
- Arreglo en moto3d.js: `ocultaArriba(o)` (recorre los padres hasta la raíz); solo entran a bordes (`conBorde`), a grupos con estado y a sombra las mallas que se ven de verdad. `aplicarPersonalizacion` en Rayos X llama a `aplicarModo()` (antes solo `agruparMoto`), así poner/quitar accesorios actualiza Rayos X al instante.
- Verificado (vértices de bordes en Rayos X — inicial / todos los accesorios / ninguno): NKD 125 15610/19308/15610; Traviesa (con baúl, cubremanos, led, parabrisas) 11788/11788/9872; Pulsar NS 200 16294/19788/16294; Aerox 155 10960/12928/10960. Vuelve igual tras restaurar y tras pasar por Moto. Rayos 6–11 calls / ≤21k tri; Moto 41–46 calls / ≤50k tri.
- Medir con el panel oculto: el visor espera al IntersectionObserver (innerHeight 0) y rAF no corre. Truco en scratchpad `rayos.js`: sustituir rAF por setTimeout y un IntersectionObserver falso, y `import('/static/garaje/js/moto3d.js?h=…')` (copia nueva del módulo).

## 7 líneas nuevas (2026-11-15, hecho, sin commit) — detalle en informes_noche/3d-motos-nuevas.md
- XR 190L y DR 150: `carroceriaEnduro` ahora toma una tabla de contornos por modelo (xtz, tt sin cambios; xr, dr nuevos) y se activa con `enduro.modelo` en rasgos.js; faro enduro `mascara` (inclinado con la horquilla, por delante de las barras, encima del guardabarros alto).
- Raider, Hunk 125R y FZ 2.0 declaran `familia: "naked"` (ya no caen en clásica); faros nuevos `raider` y `hunk`; FZ 2.0 usa el faro `fz`. Rasgo nuevo `guardaPintado` (Hunk, CT 125).
- Boxer CT 125: regla propia antes de `/boxer/` (carenado de faro en trapecio, aleación, colín largo). XTZ 150 ya usaba la XTZ.
- Calcas de fábrica de las 6 que faltaban en calcas_fabrica.js. Fotos en manual_despiece/<moto>/fotos (solo local).
- Medido: alta ≤43,8k tri, baja ≤25,3k, 38–40 calls; flotantes/llantas/luces/anclas 7/7 ok. Capturas: relevos/3d-motos-nuevas*.jpg.
- Medición sin el panel: `relevos/scripts-3d-nuevas/` (cdp.mjs abre Chrome headless con una sesión creada en el shell de Django y guarda la hoja de __vistas como JPG; vistas.sh, medir.sh, chequeo.sh).
- 2.ª ronda (15-11): guardafango enduro reubicado sobre la llanta (antes quedaba dentro del chasís; afecta a todas las enduro), FZ 2.0 con guardafango pintado, Hunk 150 (faro `bikini`), colores de fábrica por línea en `garaje/colores_fabrica.py` (Personalizar + color por defecto al registrar).
- 4.ª ronda (15-11): diferenciar motos parecidas. Rasgos nuevos `rinDiseno` (radios de aleación por línea) y `cintaRin`; `rinColor` de fábrica ya no lo tapa el secundario por defecto (moto3d.js aplicarPersonalizacion + `rinColor` en el retorno de construirMoto). XTZ 150 con máscara/tapas/guardafango negros. Tabla de pares en informes_noche/3d-motos-nuevas.md.
- 5.ª ronda (15-11): three 0.160.0 servido desde `garaje/static/garaje/vendor/three-0.160.0/` (importmap en `_importmap_3d.html`), modulepreload de three/moto3d/construir en la ficha, minificado de producción con `npm run js` → `build_js/` (settings: STATICFILES_DIRS solo si existe y DEBUG=0). Si se crea un módulo nuevo del 3D, minificar_3d.mjs ya toma todo `moto3d/*.js`.
- Presupuestos nuevos (propuestos y aplicados en este relevo): ≤60 calls, ≤60k tri alta / ≤35k baja, **JS del 3D ≤300 KB transferidos** (hoy 239), primer cuadro con GPU real y 4G rápida: boceto ≤1,5 s, cuadro real ≤2,5 s (≤3 s en Render).

### Correcciones de la auditoría (15-11-2026)
- Luces: transición día/noche instantánea si la pestaña está oculta o el visor fuera de vista; el neón (accesorio LED) solo encendida y de noche.
- NMAX/Aerox en baja: `toscoExtra` 1,35 en `panelAhusado` (CACHE_VERSION 7). Programas: letras de llanta/placa/asiento comparten sombreador y se sueltan los de la etapa sin sombras → 18–19 en alta.
- CT 100 de mandados y Discover deportiva (rasgos y calcas nuevos). Ver `informes_noche/3d-motos-nuevas.md`.
