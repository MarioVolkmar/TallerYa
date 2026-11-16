# Revisión de textos y accesibilidad — 15 nov. 2026

Método: lectura y búsquedas sobre todas las plantillas, el CSS, los JS (sin 3D), los correos, el chat de Chispa y los mensajes de vistas/formularios; contraste calculado con la fórmula WCAG sobre los colores del CSS. Pruebas `cuentas talleres garaje`: 391 OK. Sin commit. No se verificó con lector de pantalla ni con captura (el panel del navegador estaba oculto).

## Corregido
| Área | Problema | Corrección |
|---|---|---|
| Teclado | No había enlace «Saltar al contenido» | Enlace nuevo en `base.html` (aparece al enfocar con Tab) + `id="contenido"` en `<main>`; estilo en `tallerya.css` |
| Foco visible | No existía regla global: dependía del anillo del navegador y varios elementos quitaban el contorno | Regla `:where(a, button, summary, select, [tabindex]):focus-visible` (contorno mostaza) con baja especificidad, para no pisar los foco propios; contorno al letrero de la portada |
| Movimiento | `prefers-reduced-motion` solo cubría animaciones sueltas | Regla general al final del CSS que reduce animaciones y transiciones |
| Diálogos | 5 `<dialog>` sin nombre accesible (calificar taller en Mi cuenta, registrar mantenimiento, eliminar moto, pedir cita, reseña del taller) | `aria-labelledby` apuntando al título de cada uno |
| Mensajes | Avisos y errores de formulario no se anunciaban | `role="alert"` (errores) / `role="status"` (avisos) en `base.html` y `_campos.html` |
| Contraste | Textos grises `#7d8285`, `#7d8486`, `#7d8580` (4,0–4,15:1: placeholders, «Ver todos los talleres»…, pasos y fuentes de CDA) y el progreso de insignias `#6f7678` (3,4:1) | Subidos a `#949b9d` (≥ 4,9:1 sobre las superficies oscuras) |
| Nombres | «tecnomecánica» en la escena de registro | «técnico-mecánica» (el resto ya era coherente: 44 «técnico-mecánica», «Mi garaje», «hoja de vida») |

## Ya estaba bien (sin cambios)
- Todas las `<img>` tienen `alt`; los botones de solo ícono (×, ‹, ›, ⤢, campana, chat) tienen `aria-label`; los íconos decorativos son `aria-hidden`.
- Campos y selectores con etiqueta (o `sr-only`); `lang="es"`; un `h1` por página (los repetidos están en ramas `{% if %}`).
- Menú móvil y campana con `aria-expanded`/`aria-controls`; diálogos nativos (Escape y foco gestionados por el navegador); pestañas del diagnóstico con flechas; chat de Chispa con `aria-haspopup` y Escape.
- Paleta principal: crema/crema-2/lava/mostaza sobre carbón y pizarra pasan AA (4,3–8,6:1; el peor caso es lava sobre pizarra-2, 4,3:1, solo para títulos grandes).
- Textos: sin inglés suelto, tildes correctas, tuteo y tono cercano en todos los mensajes revisados (≈120), botones con verbo; los correos son claros.

## Dudoso / para decidir
- **Botones lava con texto blanco** (si los hubiera): blanco sobre `#f2611d` da 3,2:1; hoy los botones usan texto oscuro (5,9:1), no hay que cambiarlos.
- **«Panel completo de Django»** (administración): jerga técnica, solo la ve el admin.
- **Correos:** si el usuario no tiene nombre queda «Hola ,». Conviene `{{ usuario.first_name|default:"" }}` con saludo alterno (requiere tocar plantillas de correo; no lo hice).
- **Mensajes de Python** (no se tocan): «Esta cita ya no se puede cancelar.» y «La foto pesa más de 6 MB.» dicen qué pasó pero no qué hacer.
- **Carrusel y escena de la portada, visor 3D:** animaciones en JS/SVG; la regla general de movimiento reducido cubre CSS, pero el autoavance del carrusel y el visor 3D deberían revisar `matchMedia('(prefers-reduced-motion)')` (archivos 3D no tocados).
- **Puntos del plano del despiece** (11–12 px): operables con teclado (tienen `:focus-visible`), pero pequeños para el tacto; son del dibujo.
- No se probó con lector de pantalla real (NVDA/TalkBack); conviene un recorrido corto del registro y el menú.
