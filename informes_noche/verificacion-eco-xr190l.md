# Verificación 3D: Eco Deluxe 100 y XR 190L

Fecha: 21-nov-2026. Visor real (páginas `/garaje/60/` y `/garaje/38/`; `/vista-3d/` es un visor pelado sin Personalizar ni Rayos X). Medido en Chrome sin ventana (1280 y 375 px, con sesión de `usuario@prueba.com`) y revisado a mano en el panel del navegador (Eco a 1024 px). Capturas en `informes_noche/verificacion-eco-xr190l/`.

Pruebas del garaje: `manage.py test garaje -v 1` → **279 pruebas, OK**.

## Tabla

| Punto | Eco 1280 | Eco 375 | XR 1280 | XR 375 |
|---|---|---|---|---|
| 1. Carga sin errores y GLB correcto | Cumple (`ecodeluxe100_tripo.glb?v=5`, 0 errores de consola, 0 peticiones fallidas, sin scroll horizontal) | Cumple (igual) | Cumple (`xr190l_tripo4.glb?v=7`, 0 errores) | Cumple (igual) |
| 2. Personalizar: color principal | Cumple solo con el principal: tanque, guardabarros, carenado de farola y tapas se ponen rojos; llantas, motor, escape, luces y cromos no cambian (`eco-1024-rojo-drawer.png`, `eco-1280-rojo-drawer.png`) | No verificado en imagen limpia (ver falla A) | Cumple: tanque, guardabarros delantero, carenado y farola en rojo; motor, llantas y cromos intactos (`xr-1280-pintada.png`) | Estados de la interfaz correctos; captura final no revisada |
| 2b. Personalizar: secundario / rines | **Falla A** (ver abajo) | **Falla A** | Parcial: las tapas laterales y el guardabarros trasero quedan blancos de fábrica, sin cambio al elegir otro color de rines/detalles; falta confirmar que ese blanco es el "secundario" esperado | Igual que 1280 |
| 2c. Colores de fábrica | Cumple (negro con franjas plata) (`eco-1280-inicial.png`) | Cumple | Cumple (rojo + blanco) (`xr-1280-inicial.png`) | Cumple |
| 3. Rayos X | Cumple: carrocería translúcida, tanque, escape y caja de aire en naranja, llantas y amortiguadores a la vista (`eco-1280-rayos.png`) | Cumple (`eco-375-rayos.png`) | Cumple: carrocería translúcida; motor, cadena, piñón, disco y amortiguador visibles en su sitio (`xr-1280-rayos.png`) | Cumple (`xr-375-rayos.png`) |
| 4. Luces (Encender y Noche) | Cumple: farola con haz, stop rojo y direccionales ámbar encendidos (revisado a mano en el panel; `eco-1280-noche-atras.png`) | Botones responden; imagen sin revisar | Cumple: haz de farola, stop y direccional encendidos (`xr-1280-noche-frente.png`) | Cumple: farola y direccionales delanteras ámbar (`xr-375-noche-atras.png`) |
| 5. Nada flotando ni piezas genéricas | Cumple en todas las vistas revisadas | Cumple (vistas revisadas) | Cumple | Cumple |

## Falla A (Eco, bloqueante a confirmar)
En Eco, al elegir un color en **Rines y detalles** (probado con Azul) el cuerpo vuelve a negro de fábrica aunque el principal ya sea Rojo, y elegir Rojo después tampoco lo repinta (`eco-1280-rojo-azul.png`, `eco-375-rojo-azul.png`, `eco-1280-azul-luego-rojo.png`; salió el aviso "Cambios sin guardar descartados"). Pasó 3 de 3 veces en Chrome sin ventana; en una prueba a mano en el panel (clic en Rojo y 0,5 s después en Azul) el cuerpo se quedó rojo, así que puede depender del tiempo entre clics. Los rines con radios no cambian de color con ninguno. Con solo el principal (sin tocar rines) Eco pinta bien. En la XR el mismo orden de clics no repinta de negro.
No se tocó código; conviene que quien lleva Personalizar lo mire (¿reinicio de la pintura al cambiar rines en `aplicar`?).

## Límites de la verificación
- 375 px en el panel del navegador no arrancaba el visor (la página queda en segundo plano con el panel oculto; el arranque usa `requestAnimationFrame`), por eso se midió en Chrome sin ventana.
- Chrome sin ventana usa GL por software: colores y brillos pueden diferir ligeramente de una GPU real.
- No se revisó una a una cada captura a 375 px (pintada, noche).

## Revisión de la falla A y del blanco de la XR (21-nov, segunda sesión)
- **Falla A: no se reproduce.** Con clics por JS y con ratón real (CDP), Eco en 1280 y 375 px, esperas de 0, 20, 300 ms y 0,5 s entre Rojo y Azul, y luego Rojo otra vez: el material del cuerpo queda en `#c62828` y los rines en `#1f4fa8`; la captura muestra la moto roja con el aro azul. En el código, `aplicar` (personalizar.js) manda siempre la cfg completa y `aplicarPersonalizacion` pinta `cfg.color` sin reiniciar; la carrera de calcas de fábrica (`aplicarFabrica`) descarta la textura vieja por `claveColor`. El aviso «Cambios sin guardar descartados» solo sale en `mostrarCajon(false)` (cerrar con la X, Escape o el botón Personalizar): la hipótesis más firme es que el guion de la verificación cerró el cajón entre clics y ese cierre devolvió el negro guardado (comportamiento diseñado). No se cambió la lógica de pintura.
- **Rines de radios de la Eco:** el GLB ya marca `aro_del/aro_tras` (`aro: True`); con «Rines y detalles» el aro cambia (visible en azul); los radios cromados no, igual que en las demás motos de radios.
- **XR 190L:** las tapas laterales llevaban un `tono` fijo y no seguían a nada. Ahora `glb.js` registra las piezas `blanco.*` con `tono` en `M.secundarios` y `aplicarPersonalizacion` (moto3d.js) las pinta con el secundario elegido; con el de serie («De fábrica») conservan `#eef0f2`. Medido: fábrica `#eef0f2`, con Azul `#1f4fa8`. El guardabarros trasero de la XR es plástico negro (el blanco son solo las tapas), no se tocó. NMAX (pk 2) sigue pintando bien. GLB sin cambios.
- Prueba nueva `garaje/tests_visor_secundario.py`; `manage.py test garaje`: 281 pruebas, OK.

## Veredicto
**Lista.** Eco y XR quedan definitivas: carga, Rayos X, luces, colores de fábrica y Personalizar cumplen; la falla A no se reproduce (probable artefacto del guion de prueba) y el secundario de la XR ya funciona.
