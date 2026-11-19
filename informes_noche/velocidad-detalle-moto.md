# Velocidad del detalle de la moto (esquema del despiece) — 19-nov-2026

Moto 3 (NMAX 155), cuenta del dueño, servidor 8001. Medido con Chrome sin ventana: cuenta como pestaña visible, sin el freno
de segundo plano, con GPU real (Intel UHD, ANGLE D3D11). **Frío** = perfil nuevo: sin caché de red ni de shaders, como una
primera visita. **Tibio** = segunda carga. El «antes» y el «después» en frío se midieron **intercalados** (A, B, A, B), así
que los dos tuvieron la misma carga del equipo. Había otras sesiones usando la máquina y el mismo servidor, y hubo corridas
con esperas del servidor de 10 a 30 s: esas se descartaron.

## Causas encontradas

1. **Personalizar congelaba la página de 5 a 6 s en la primera visita.** Al recibir `moto3d-listo`, `personalizar.js`
   pintaba las esferas de acabado con el cajón cerrado. Para eso `vistaAcabado()` creaba **un segundo `WebGLRenderer` + PMREM**
   y compilaba 5 variantes del material físico de forma síncrona (`GetProgramiv` esperando a la GPU). Lo confirmó la traza
   (CDP Tracing). Esa tarea larga retenía el esquema, y el SVG «esperaba al 3D».
2. **El despiece quedaba en cola detrás del 3D.** `ceder()` (`moto3d/comun.js`) usa `scheduler.yield()`, cuyas
   continuaciones pasan **delante** de las demás tareas, así que la respuesta del `fetch` y el `requestIdleCallback` del
   despiece no llegaban hasta que el armado terminaba. En celular el JSON se pedía a los 11–17 s.
3. **`despiece.json` pesaba 522 KB** (61,7 KB comprimido), y el **60 % eran las guías** de las piezas (`guia`: 292 KB), que
   solo se leen al abrir «Ver guía».
4. GZip ya estaba activo (`GZipMiddleware`) para el JSON y el SVG. El SVG ya tenía `max-age` de 1 día y la versión en la URL.
   El HTML hace **38 consultas, sin N+1** (lo más repetido sale 2 veces: perfil de domiciliario, lecturas de km, registros,
   pico y placa), en unos 290 ms en el servidor.
5. La sospecha de que el armado del 3D se hubiera vuelto lento no se confirmó: `msArmado` da unos 0,86 s en frío y las
   etapas suman lo mismo que antes. Lo que queda lento en frío son **esperas de la GPU** dentro del 3D: crear el contexto
   WebGL (≈1,6 s) y enlazar los shaders de sombras después de «listo» (≈2,5 s). Ver «Pendiente».

## Cambios (sin commit)

- `garaje/static/garaje/js/personalizar.js`: las esferas de acabado se dibujan **solo al abrir el cajón**, o cuando el
  dedo o el puntero se acercan al botón Personalizar, **una por cuadro**. Verificado: al abrir salen las 5.
- `garaje/static/garaje/js/moto3d/comun.js`: `ceder()` sigue usando `scheduler.yield()`, pero **cada 120 ms cede un turno
  real** (al final de la cola) para que la red y los clics avancen. Es el único cambio del lado 3D: no toca `moto3d.js`,
  `construir.js` ni `glb.js`. `?modelo3d=glb` verificado (carga `nmax155.glb` y queda listo).
- `garaje/static/garaje/js/despiece.js`:
  - los datos se piden **de una vez** al cargar la página (27 KB comprimidos);
  - el esquema se arma con lo primero que pase: que se acerque a la pantalla (IntersectionObserver), que la página quede
    libre (máx. 1,5 s) o `moto3d-listo`;
  - las guías llegan aparte y se precargan en tiempo libre. «Ver guía» las espera si todavía no han llegado.
  - Versión `?v=20261118-b` en `moto.html` y `diagnostico.html`.
- `garaje/views.py` (`despiece_json`): sin `guia` (solo la marca `1`). `?guias=1` devuelve `{id: guía}`. **ETag +
  `Cache-Control: private, no-cache`**, con 304 si nada cambió (acepta el `W/` que agrega GZip).
- `garaje/tests.py`: `test_json_sin_guias_guias_aparte_y_etag`.

## Antes y después

Tiempos en segundos desde la navegación. El esquema cuenta en el `load` del `<img>` del dibujo.

| Medida | Ancho | Antes | Después |
|---|---|---|---|
| Esquema listo, frío | 1366 | 16,2 – 16,8 | **4,6 – 5,0** |
| 3D listo, frío | 1366 | 7,8 – 15,9 | 8,3 – 9,2 |
| Tarea larga máxima, frío | 1366 | 5,1 – 6,1 | **1,7 – 2,5** |
| Esquema listo, frío | 390 | 14,7 – 15,0 (16,8 / 48 con ruido) | **5,3 – 7,6** |
| 3D listo, frío | 390 | 10,9 – 13,5 | **6,4 – 8,7** |
| Tarea larga máxima, frío | 390 | 5,1 – 5,6 | **2,4 – 2,9** |
| Esquema listo, tibio | 1366 | 2,1 – 5,3 | **1,8 – 2,0** |
| 3D listo, tibio | 1366 | 3,0 – 10,2 | 2,6 – 3,3 |
| Esquema listo, tibio | 390 | 3,8 – 7,4 | **1,9 – 3,0** |
| `despiece.json` (sin comprimir / transferido) | — | 522 KB / 61,7 KB, en cada visita | **216 KB / 27 KB**; repetida: **0,3 KB (304)** |
| Guías (`?guias=1`, en tiempo libre) | — | (iban dentro del JSON) | 310 KB / 31 KB |
| SVG del esquema (`carcasa.svg`) | — | 230 KB / 49 KB (caché 1 día) | igual |
| HTML | — | 38 consultas, ≈290 ms en el servidor | igual (sin N+1) |
| Carga total (`load`), frío | 1366 | 5,0 – 6,3 | 4,6 – 5,0 |

Pruebas: `manage.py test -v 1` (completa, con las `@tag("lenta")` del despiece): **816 OK**. Skill `revisar-seguridad
--solo velocidad`: 0 fallas, 2 avisos bajos ya conocidos (ficha de moto: 35 consultas; pregunta del foro).

## Pendiente (para la sesión del 3D, no lo toqué)

- **Esperas de la GPU en `moto3d.js`** en la primera visita: `renderer.render` del boceto y la etapa de sombras enlazan
  shaders de forma síncrona (`GetProgramiv`) en tramos de 1 a 2,5 s (`__visor.info().pedazoMasLargo` ≈ 2,6 s).
  `compileAsync` + `KHR_parallel_shader_compile` sin consultar el estado antes de que esté listo los acortaría.
- **Primera apertura de Personalizar**: cada esfera de acabado nueva tarda ≈1 s (compila su variante de shader) y la
  primera ≈2–3 s (crea el renderizador y el PMREM). Ahora pasa al abrir el cajón, una por cuadro, y no al cargar la
  página. Se podría reutilizar el renderizador principal o precompilar con `compileAsync`.
- El SVG (230 KB) no se minimizó: las coordenadas ya van con 1 decimal y es de la sesión de dibujos (`diagramas.py`).
  Además tiene un `feDropShadow` sobre todo el grupo de piezas, que cuesta al rasterizar en celular.
- 4 consultas duplicadas en el HTML (domiciliarios, lecturas de km, registros, pico y placa): menores. Están en archivos
  que otras sesiones están tocando.

Scripts de medición (scratchpad, temporales): `medir.py` (tiempos, long tasks, `__visor.info()`, recursos), `traza.py`
(top de eventos del hilo principal) y `ab.py` (antes/después intercalado).
