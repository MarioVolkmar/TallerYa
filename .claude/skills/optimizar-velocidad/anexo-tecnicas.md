# Técnicas por capa (cuándo usar cada una)

Cada fila: **síntoma medido → técnica → cuidado**. Esfuerzo S/M/L. En TallerYa ya hay: GZip (HTML y JSON), WhiteNoise con
hash y `.gz/.br` (estáticos, en producción), JS 3D minificado (`npm run js` → `build_js/`), ETag en `despiece.json`,
esquema desacoplado del 3D, guías del despiece aparte.

## Servidor (Django)
| Síntoma | Técnica | Cuidado |
|---|---|---|
| Consultas crecen con N elementos; `--top` muestra la misma SQL N veces | `select_related` (FK/1-1) y `prefetch_related` (inversas, M2M; `Prefetch(queryset=…)` para filtrar) | Prueba con 1 vs N o `assertNumQueries` (`garaje/tests_velocidad.py`) |
| Misma SQL 2 veces en una vista (no N+1) | Calcular una vez y pasarla al contexto; `@cached_property` en el modelo | Context processors que se repiten en `base.html` |
| > 300 ms con pocas consultas | Perfilar (`cProfile` sobre `servidor.py`); caché de fragmento `{% cache %}` o `cache.get_or_set` para lo que no depende del usuario | Clave con versión; invalidar al guardar |
| JSON/SVG que no cambia | `ETag`/`Last-Modified` + `Cache-Control: private, no-cache` (revalida, 304) o `max-age` largo con versión en la URL | Lo privado nunca `public` |
| HTML > 40 KB gzip | Partir: lo de abajo del pliegue por `fetch` o `<template>` diferido | SEO de páginas públicas |
| Estáticos | Brotli/gzip y hash los da WhiteNoise (`EstaticosComprimidos`); `max-age` de un año solo para archivos con hash | `?v=` a mano en lo que no pasa por `{% static %}` |

## Página
| Síntoma | Técnica | Cuidado |
|---|---|---|
| FCP alto con CSS grande (`tallerya.css` 469 KB bruto) | CSS por página: base común + hojas por sección (garaje, foro, consola) cargadas solo donde se usan; o CSS crítico en línea y el resto con `media="print" onload` | Probar con `revisar-ux` las páginas que pierden reglas |
| Fuentes de Google bloquean | `preconnect` a fonts.gstatic, menos pesos (hoy 7), `display=swap` (ya), o servirlas locales en woff2 con `preload` | Saltos de texto (CLS) |
| Tarea larga de **Layout/UpdateLayoutTree** con DOM chico | Selectores caros (`:has()` ×27), `backdrop-filter`, `@container`: limitarlos; `content-visibility: auto` + `contain-intrinsic-size` en secciones de abajo | Verificar que nada salte al hacer scroll |
| JS que no hace falta al pintar | `defer` o `type="module"` (diferido por defecto); `import()` al usarlo | Orden entre scripts que dependen uno del otro |
| Algo pesado abajo del pliegue (mapa, 3D, esquema, carruseles) | `IntersectionObserver` con `rootMargin: "200px"` para cargarlo al acercarse; `requestIdleCallback` con `timeout` como respaldo | El usuario que entra por un ancla (`#despiece`) |
| Imágenes | `srcset`/`sizes` + WebP/AVIF, `width`/`height` siempre, `loading="lazy"` abajo del pliegue y `fetchpriority="high"` en la del LCP | `loading="lazy"` en imágenes de diálogos ocultos (no se piden hasta mostrarse) |

## Esquema o despiece
| Síntoma | Técnica | Cuidado |
|---|---|---|
| JSON inicial grande | Solo lo que pinta el primer dibujo; el resto (guías, fichas largas, otras figuras) bajo demanda o en tiempo libre | «Ver guía» espera si no ha llegado |
| SVG > 60 KB br o rasterizado lento | Minificar (1 decimal, sin metadatos, `<use>` para repetidos), quitar `filter` (`feDropShadow`) sobre grupos grandes: sombra con una copia desplazada o CSS | Los dibujos son de la sesión de dibujos (`diagramas.py`): proponer allí |
| Se pide en cada visita | ETag (ya) o versión en la URL + `max-age` | Al cambiar el dibujo, cambiar la versión |
| El esquema espera al 3D | Que no comparta cola: `ceder()` del 3D cede un turno real cada 120 ms (ya); el esquema arranca por IntersectionObserver o a 1,5 s máx. | No volver a encadenarlo a `moto3d-listo` |

## 3D (three.js)
| Síntoma | Técnica | Cuidado |
|---|---|---|
| GLB > 400 KB | Cuantizar (`gltf-transform quantize`), meshopt (`EXT_meshopt_compression`, decodificador de ~20 KB) antes que Draco (decodificador WASM de ~300 KB: solo vale para modelos > 1 MB); simplificar mallas (`simplify`) y quitar caras ocultas | Las piezas con nombre deben seguir separadas para Personalizar |
| `armada − escena` grande o `pedazoMasLargo` > 100 ms en el armado | Trocear el armado (`ceder()` entre piezas), `requestIdleCallback` para lo secundario, geometría en un Worker (`OffscreenCanvas` no hace falta: solo los buffers, transferibles) | Que el esquema y los toques no queden detrás |
| `compilaAsync − boceto` grande en frío, `GPUTask` largas en la traza | `renderer.compileAsync()` **sin** dibujar ni pedir estado antes de que termine (con `KHR_parallel_shader_compile`, cualquier `render` o `getProgramParameter` previo vuelve síncrona la espera); menos variantes de material (mismos defines, `onBeforeCompile` compartido); sombras después del primer cuadro (ya) y con un solo programa | Medir en frío: en tibio la caché de shaders oculta el problema |
| Otro script se cuelga de `moto3d-listo` con trabajo pesado (p. ej. `personalizar.js`) | Que el listener solo marque y difiera el trabajo a `requestIdleCallback` o al abrir su panel; reutilizar el renderer principal en vez de crear otro | Abrir el panel debe seguir sintiéndose inmediato (precalentar al acercarse) |
| Celular lento (`calidad: baja` y aún lento) | Calidad adaptativa: `setPixelRatio(min(dpr, 1.5))`, sin sombras ni reflejos en baja, bajar a 30 fps, medir el primer cuadro y bajar si > 50 ms | Que la moto siga viéndose bien en la vitrina |
| Se arma aunque nadie lo mire | No cargar el módulo hasta que el visor esté a ≤ 1 pantalla (IntersectionObserver) o el usuario toque; mostrar una imagen fija mientras | El visor está arriba en `/garaje/<id>/`: ahí sí se ve al entrar; vale para el 3D de abajo y de otras páginas |
