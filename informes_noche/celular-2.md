# Revisión en celular, 2.ª pasada (360 y 390 px) — 15 nov. 2026

**Método.** Igual que `celular.md`: cada página se midió con script (elementos fuera del ancho de pantalla, descontando los que están dentro de contenedores con scroll propio; botones/campos/enlaces-botón de menos de 40 px) y se confirmó con capturas pequeñas. Se revisó con la cuenta demo (390 px), sin sesión y con la cuenta de prueba sin motos (360 y 390 px). Menú móvil y campana abiertos y medidos.

**Resultado:** ningún elemento se sale de la pantalla en ninguna página revisada. Todo lo corregido es CSS en un bloque nuevo `@media (max-width: 640px)` en `talleres/static/talleres/css/tallerya.css` (junto al de la 1.ª revisión). Sin clases Tailwind nuevas (no hizo falta `npm run css`), sin plantillas ni Python.

| Página | Problema | Corrección |
|---|---|---|
| Portada sin sesión | Escena completa, texto sin tapar (en 360 y 390). Nada que corregir | — |
| Portada con sesión / sin motos (cuenta de prueba) | Escena «Aquí va tu moto» bien; el enlace «Mi garaje / Agrega tu moto» medía 35 px | `.portada-ficha > a` a 40 px |
| Portada, Comunidad (rodadas + foro) | Sin problemas | — |
| Primer uso (`/garaje/agregar/?guia=1` y `/bienvenida/1/`) | Sin problemas | — |
| Menú móvil | «Plus» 37 px y «cuenta» 39 px | `min-height: 40px` |
| Talleres, SEO por barrio | Círculo de WhatsApp 37 px; chips de orden («Recomendados…») 32 px; «Limpiar filtros» 19 px; chip de filtro activo 30 px; paginación 38 px | todo a 40 px |
| Técnico-mecánica / SOAT | Chips de moto 32 px; «Cómo llegar →» 21 px | 40 px |
| Detalle de taller | «Cómo llegar» del mapa 34 px | 40 px |
| Mi cuenta | WhatsApp de actividad 35 px, «Cómo ganarlas» 35 px, «CAMBIAR» 25 px; barra «Instalar app» y push caben bien (forzadas visibles para medir) | 40 px |
| Diagnóstico | Chips de moto 37 px | 40 px |
| Detalle de moto (demo) | Accesos «Hoja de vida / Gastos / ¿Qué le pasa…», «Ver hoja de vida», «Agregar fecha», WhatsApp y «Cómo llegar» de talleres cercanos 26–37 px | 40 px |
| Gastos | enlace «hoja de vida» 25 px | 40 px |
| Foro, Rodadas, Cupones, Plus, Emergencias, Hoja de vida, Entrar | Sin problemas | — |

## Sin cambiar / anotado
- **Portada sin motos:** el recuadro punteado del «puesto» se corta en el borde derecho; parece intencional (sesión de la portada, no se tocó).
- **Portada sin sesión:** el letrero «Ver talleres» de la escena mide 37 px de alto (es parte del dibujo).
- **Enlaces de texto dentro de tarjetas** (nombre de taller en cupones/actividad, «Ver los 11», teléfono y «Sitio web» en CDA, 18–26 px): son líneas de texto; subirlas rompería el ritmo. Si se quiere, añadir padding vertical.
- **Mapa de las tarjetas de CDA:** en el panel el iframe de Google Maps sale en blanco (el panel no lo carga); el marco y el «Ver en el mapa ↗» están bien. Conviene mirarlo en un celular real.
- **No revisado** por no tener credenciales y no crear sesiones a mano: panel del taller, registrar servicio, detalle de cita (`/cita/<token>/`), foro/rodadas con cuenta propia, visor 3D y «Personalizar: calcas de fábrica» (la 1.ª revisión los midió sin problemas; no se tocan archivos 3D). Barra «Instalar app» solo aparece en navegadores instalables.
- Otra sesión añade CSS al final de `tallerya.css`; mi bloque quedó antes de «Portada de un motero sin motos».
- El servidor `tallerya` (8001) ya estaba en uso por otra sesión; se usó ese. La sesión del navegador del panel quedó con la cuenta de prueba sin motos.

## Añadido tras el aviso de Auxiliares (portada)
- **Motero sin motos** (360 px): silueta, puesto punteado y «+ Aquí va tu moto» caben, sin elementos fuera de pantalla ni botones chicos. OK.
- **Sin sesión, ficha «Talleres verificados · Cita por WhatsApp»** (360 px): en fila, «Talleres verificados» partía en 2 líneas y «Cita por WhatsApp» también, desalineadas. Corregido apilándola en columna en celular (`.portada-garaje .portada-ficha`, dentro de mi bloque `@media`). **No pude verificarlo con captura**: el panel del navegador se ocultó y el servidor se estaba reiniciando; conviene mirarla.
- Al final de `tallerya.css` hay líneas repetidas (`@keyframes pm-vacio-latir`, el `@media (prefers-reduced-motion)` y `.portada-garaje .portada-ficha strong`, dos veces): inofensivo, pero sobra una copia.
- El service worker nuevo puede dejar una página «Sin conexión» en caché si el servidor local se reinicia mientras se prueba; se arregla recargando (o quitando el service worker).
