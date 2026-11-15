# Revisión en celular (360 y 390 px) — noche del 15 nov. 2026

**Cómo se midió.** Cada página se cargó en un marco de 360 y de 390 px de ancho (sin barra de desplazamiento, como en un teléfono), con y sin sesión (cuenta demo `moto.demo@tallerya.local`). Un script revisó:
- elementos que se salen del ancho de la pantalla;
- botones, campos y selectores de menos de 40 px de alto;
- diálogos y paneles más altos que la pantalla.

Para el diálogo de registro, el menú, la campana y la guía de pieza se abrieron los paneles y se midieron. Se tomó una sola captura, de la guía de pieza.

**Ojo con la medida clásica.** `html, body { overflow-x: clip }` (tallerya.css:2308) hace que `scrollWidth > innerWidth` **nunca** se cumpla: lo que se sale queda **cortado sin aviso** en vez de dar barra horizontal. Por eso se midió cada elemento contra el borde de la pantalla.

Todos los cambios son CSS en `talleres/static/talleres/css/tallerya.css`: dos líneas editadas y un bloque `@media (max-width: 640px)` al final. No hay clases de Tailwind nuevas, así que no hizo falta `npm run css`. No se tocaron plantillas, vistas ni archivos de 3D o diagnóstico.

## Hallazgos y correcciones

| Página | 360 / 390 | Qué se corrigió |
|---|---|---|
| Portada (con y sin sesión) | OK | Flechas «Moto anterior/siguiente» de 32 a 40 px. |
| Menú móvil | OK | El botón «Menú» pasa de 38 a 40 px. El panel cabe (556 px, con scroll propio). |
| Campana (notificaciones) | OK | Botón de 32 a 40 px. El panel cabe (446 px). |
| **Talleres** | **Corregido** | **Desborde real**: la cuadrícula `.dir-cuerpo` no tenía columnas y se estiraba al contenido. Filtros y tarjetas medían 509 px en una pantalla de 360, cortados a la derecha. Ahora `grid-template-columns: minmax(0,1fr)`. Corazón de favorito de 38 a 40 px. |
| Detalle de taller | OK | «★ Escribir reseña» (`.boton-seccion`) de 34 a 40 px. |
| Cupones | OK | — |
| Foro: lista | OK | — |
| Foro: pregunta | OK | «Me sirvió» y acciones (`.fo-accion`) de 32 a 40 px. Reacciones de 37 a 40 px. |
| Foro: integrante | OK | — |
| Foro: nueva pregunta | OK | Sin sesión manda a Entrar (OK). |
| Rodadas: lista y detalle | OK | Las mismas acciones del foro, a 40 px. |
| Mi garaje | OK | — |
| **Detalle de moto** | **Corregido** | **Desborde real** en «Hoja de vida» (lista corta, `.hv-mini`): la cuadrícula sin columnas medía 373 px y los nombres no se recortaban. Ahora usa `minmax(0,1fr)` y se ven los «…». Botones del visor («Rayos X/Moto», «Centrar»), títulos plegables de sección, pestañas de sistemas del despiece, «Otras piezas» y zoom del plano: ahora de 40 px. |
| Agenda / Lo urgente | OK | — |
| Despiece y guía de pieza | OK | La guía (panel fijo) mide 607 px, con scroll propio y sin salirse. Los puntos numerados del dibujo (11–12 px) no se tocaron: son marcas sobre el plano con zoom, y ese archivo es de la sesión de dibujos. |
| Diálogo «Registrar lo que hice» | OK | Mide 652 de 740 px, con `max-height` y scroll. El botón × pasa de 32 a 40 px. |
| Historial (en la moto) | OK | Selectores de fecha de 37 a 40 px. |
| Gastos | OK | Chips de filtro de 26 a 40 px. |
| **Hoja de vida** | **Corregido** | La fila de chips («Todos / Verificados / Pendientes / Registrados por mí») se salía 10 px a 360. Ahora se desliza de lado dentro de su píldora. «Eliminar» de 29 a 40 px y «Desactivar» de 18 a 40 px. |
| Papeles: SOAT y técnico-mecánica | OK | — |
| Emergencias | OK | — |
| Mi cuenta | OK | Chips de filtro, «Ver 1 más», «Historial con este taller», «★ Calificar taller» y «Copiar», a 40 px. |
| Plus, Insignias, Notificaciones | OK | — |
| Entrar / Registro / Diagnóstico (inicio) | OK | — |
| Diagnóstico nuevo (esquema diferido y pestañas por lámina), revisado tras la pausa | OK | Recorrido moto → «Ruido extraño» → motor → «tic» hasta el resultado. Pestañas de 44 px que pasan a otra fila si no caben (`.fo-pestanas`, flex-wrap). El esquema cargado al cambiar de pestaña cabe (borde derecho en 330 de 360 y 361 de 390). Nada se sale y no hay botones chicos. Sin cambios. |

**Resultado final:** las 21 páginas (más el menú, la campana, el diálogo y la guía) quedan sin elementos fuera de la pantalla a 360 y 390 px, y sin botones de menos de 40 px, salvo lo que sigue.

## Lo que quedó sin cambiar (discutible)
- **Portada, botón día/noche** (`.portada-noche`, 35 px): la portada es de la sesión «Proyecto tallerYa». Basta con `min-height: 40px` en el mismo bloque si lo aprueban.
- **«Mostrar contraseña»** en Registro (32 px): es un ícono dentro del campo, que ya mide más de 40 px. Se dejó así.
- **Campo «Tu enlace para invitar»** en Mi cuenta (20 px): es texto de solo lectura con su botón «Copiar» al lado (ya de 40 px).
- **Puntos del plano del despiece**: no se tocaron (ver arriba).
- El bloque nuevo también agranda en celular botones de áreas de otras sesiones (visor 3D y despiece). Es solo `min-height`, `width` y `height`: no cambia comportamiento ni JS.
- Durante la revisión el navegador del panel quedó con la sesión de la cuenta demo (antes tenía la del taller demo).
