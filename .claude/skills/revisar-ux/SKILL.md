---
name: revisar-ux
description: Revisión de diseño y usabilidad de TallerYa, con la congruencia con la línea de diseño existente como regla n.º 1 y las preferencias aprendidas del usuario como segunda capa, ANTES de entregar cualquier cambio visual (plantilla, CSS, JS de interfaz, textos) y para auditar una página entera. Corre un script en el navegador (desbordes, solapes con flotantes, toques < 44 px, contraste, enlaces sueltos, minúsculas, «—» y vacíos) a 1280 y 375 px, repasa una lista corta (jerarquía, consistencia con la guía de estilo, estados, textos, celular, accesibilidad, interacción) y entrega hallazgos priorizados con su arreglo. Úsala cuando digas "listo" sobre algo que se ve, cuando el usuario corrija un detalle visual (para anotar la regla), o cuando pidan "revisar diseño", "revisar UX", "¿se ve bien en el celular?", "auditar la página X".
---

# Revisar UX (TallerYa)

**Lo más importante es la congruencia:** cada cambio mantiene la línea de diseño que la página ya tiene (componentes,
colores, tipografías, espaciados y tono de [anexo-guia.md](anexo-guia.md)). Encima va una segunda capa con los gustos
que el usuario ya expresó ([preferencias-usuario.md](preferencias-usuario.md)), que crece con cada corrección (§ 5).

**Metas:** ≤ 10 min por página · ≤ 2 capturas (una por ancho) · cero hallazgos **bloqueantes** al entregar.
La mayoría entra desde el **celular**: 375 px manda. El usuario ya corrigió a mano botones apretados, enlaces sueltos,
«—» sin sentido, horarios tapados por WhatsApp, chapas que no seguían el hover, avisos legales gritones, secciones mal
nombradas e instrucciones obvias: esta skill existe para que no le llegue nada de eso.

## 1. Script (lo mecánico, ~1 min)

1. `preview_start {name:"tallerya"}`. Si dice que 8001 estaba ocupado (otra sesión tiene su servidor en esta carpeta),
   el tuyo no arranca: `preview_stop` y navega a `http://127.0.0.1:8001/` (mismo código). Si la página pide sesión y el
   panel no la tiene: `venv/Scripts/python.exe .claude/skills/revisar-ux/entrar.py <correo>` imprime `sessionid=…`;
   en `javascript_tool`: `document.cookie="sessionid=…; path=/"` y navega. Nunca contraseñas.
2. **1280 px** con `resize_window width:1280 height:800` (si el panel está oculto, `innerWidth` da 0 sin esto). Pega
   `revisar_ux.js` entero en `javascript_tool` **una sola vez** (léelo una vez con Read; no lo reescribas): queda en
   `localStorage`. En las demás páginas y anchos, sin volver a pegarlo (la CSP bloquea `eval`, no los scripts en línea):
   ```js
   const s=document.createElement('script'); s.textContent='window.__uxRes='+localStorage.revisarUX; document.head.append(s); s.remove(); window.__uxRes
   ```
   Devuelve `{scrollH, total, hallazgos:[{t,n,ej}]}`; el detalle queda en `window.__ux` (`__ux['toque<44']`).
3. **375 px** (`preset:"mobile"`, recargar, esperar ~1,5 s) y otra vez. Sin capturas intermedias.
4. Interpreta, no copies: cada tipo puede tener falsos positivos (abajo). Confirma con `__ux.<tipo>` o `read_page`, no con capturas.
   Ruido conocido del sitio que no se reporta cada vez: estrellas (`.tc-estrellas`, capa gris decorativa), `span.off` del
   rango de precio, dígitos de relleno del odómetro, contador de la campanita, enlaces del pie (ya listados abajo).

| Tipo | Qué es | Falso positivo típico |
|---|---|---|
| `color-fuera` | color de texto, fondo o borde a más de 30 de la paleta de la guía, y bordes punteados | ilustraciones, colores de pintura de la moto, fotos |
| `fuente-fuera` | fuente que no es Oswald ni Archivo | emojis, código |
| `radio-fuera` | radio que no es de la escala (0–24 px o cápsula) | — |
| `desborde` / `scrollH` | algo se sale del ancho; scroll horizontal | carrusel con `overflow-x:auto` (ya se excluye) |
| `tapado-por-flotante` / `solape` | texto bajo un botón, la barra inferior o un flotante | contenido detrás de un `<dialog>` abierto |
| `texto-cortado` | ellipsis u overflow que corta | ellipsis intencional con `title` |
| `toque<24` / `toque<44` | objetivo de toque chico | íconos con área extendida por `::after` (el script no la ve) |
| `contraste` | < 4,5:1 (3:1 grande) | texto sobre degradado de varias capas: confirmar a ojo |
| `enlace-suelto` | enlace subrayado fuera de una frase | — (casi siempre real: pásalo a botón o chip) |
| `minuscula` | chip, etiqueta, botón o frase en minúscula | unidades (km, cc) ya se excluyen |
| `dato-vacio` | «—», «None», celda vacía | — |
| `sin-nombre` | botón/enlace solo ícono sin `aria-label`, img sin alt, campo sin label | — |

Puntos ciegos del script (mirarlos en la lista manual): capas con `pointer-events:none` o pseudo-elementos que tapen
texto (p. ej. Chispa flotando sobre el borde de una tarjeta o los controles del 3D), texto sobre fotos (no mide
contraste), objetivos agrandados con `::after`, y todo lo que es de sentido (textos, jerarquía, coherencia de datos).

## 2. Lista manual (lo que el script no ve)

Repásala sobre la página, con `get_page_text`/`read_page`, **en este orden**. Cada punto que falle es un hallazgo.
1. **Congruencia (regla n.º 1)**: ¿usa los componentes, colores, tipografías, espaciados y tono que ya existen en la
   página? Antes de crear un estilo, busca su equivalente (`Grep` en `tallerya.css` y en las plantillas por la clase o
   por el caso de [anexo-guia.md](anexo-guia.md)) y reutilízalo. Un estilo o componente nuevo solo se acepta si (a) se
   justifica en el informe (qué caso no cubre la guía), (b) se agrega a `anexo-guia.md` y (c) queda igual en todas las
   páginas donde aplica (busca los otros lugares con el mismo caso). Lo que marque `color-fuera`, `fuente-fuera` o
   `radio-fuera` en tu cambio va al token o la clase más cercana.
2. **Preferencias del usuario**: repasa [preferencias-usuario.md](preferencias-usuario.md) regla por regla (nada
   punteado, sin enlaces sueltos, controles dentro de su tarjeta, chapas que siguen el hover, protagonista primero,
   sellos solo positivos, legales discretos, sin instrucciones obvias, mayúscula inicial, secciones bien nombradas…).
3. **Jerarquía**: lo que el usuario vino a hacer está arriba y es el único botón lava; lo secundario es discreto
   (botón secundario, chip, ícono) y lo legal va al final en texto pequeño `text-suave`, nunca en recuadro llamativo.
4. **Estados**: vacío, cargando, error y sin datos diseñados. Un dato que falta es una **acción** («Agrega la placa»,
   botón secundario), nunca «—» ni «No disponible». Ningún bloque vacío visible.
5. **Textos**: de tú, cortos, mayúscula inicial, sin jerga técnica innecesaria. Datos coherentes entre sí (un chip
   «Toca ya» no va junto a «Faltan 350 km»; nada de «Pasado por 0 km»). Fechas en español («18 nov 2026», no ISO).
   Una ficha de una persona habla de ella en 3.ª persona («Te manda fotos»), no en plural de empresa. Sin instrucciones obvias
   («Toca uno para…», «Haz clic aquí»). El nombre de cada sección dice lo que hay dentro (no «Papeles» sobre un
   diagnóstico). Listas que no parezcan fallas (guiones = problemas; usa ✓ o chips para lo revisado).
6. **Celular 375 px**: sin scroll horizontal; botones con texto holgado (si no cabe, texto más corto o el botón a
   ancho completo, nunca letras apretadas); nada tapado por WhatsApp, la barra inferior o avisos flotantes; textos
   que no se cortan; interruptores y controles **dentro** de su tarjeta.
7. **Accesibilidad**: contraste AA, foco visible (`:focus-visible`) en todo lo clicable, `aria-label` en íconos,
   todo alcanzable con Tab en orden lógico, animaciones apagadas con `prefers-reduced-motion`.
8. **Interacción**: hover y foco se ven en todo el componente a la vez (tarjeta + su chapa + su flecha); lo que no es
   clicable no parece clicable; en celular no se depende del hover.
9. **Rendimiento percibido**: lo importante (nombre, estado, acción principal) se pinta sin esperar al 3D, mapas,
   fotos o fetch; lo pesado va con `loading="lazy"` o diferido y con un espacio reservado (sin saltos).

## 3. Informe

**Una captura final por ancho** (`scale:0.5` en 375, `0.4` en 1280), solo al terminar y ~2 s después de cargar o
cambiar el ancho: las animaciones de entrada (`pm-subir`, 0,7 s + retrasos) y el repintado tras `resize_window` salen
como página «apagada» y llevan a falsos hallazgos. Si algo se ve raro, confírmalo con `getComputedStyle`/`zoom`, no con
otra captura completa. Tabla priorizada:

| Prioridad | Dónde (página · componente) | Problema | Arreglo sugerido |
|---|---|---|---|

- **Bloqueante**: impide usar o entender (scroll horizontal, acción tapada, texto ilegible, `None` visible, botón sin nombre).
- **Importante**: rompe la congruencia o una preferencia del usuario, o confunde (enlace suelto, «—», sección mal nombrada, toque < 44 en acción frecuente, contraste < 4,5).
- **Detalle**: pulido (minúscula, espaciado, hover incompleto, texto mejorable).

Antes de entregar un cambio: arregla los bloqueantes e importantes **que tu cambio introdujo**; lo previo se reporta,
no se toca sin pedirlo. En una auditoría: solo se reporta.

## 4. Autocontrol (antes de decir «listo»)
- [ ] Script corrido en 1280 y 375 sobre la página final (no sobre una versión anterior).
- [ ] Ningún bloqueante propio; cada importante arreglado o justificado en el informe.
- [ ] Lista manual repasada entera (9 puntos, congruencia y preferencias primero), no solo el script.
- [ ] Ningún estilo nuevo sin justificar ni sin sumarlo a `anexo-guia.md`.
- [ ] ≤ 2 capturas en toda la revisión. Si usaste más, anótalo para mejorar la skill.
- [ ] Si una regla de la guía falta o no cuadra con lo que el usuario aprobó, actualiza `anexo-guia.md` (y el respaldo).

## 5. Aprendizaje (cada vez que el usuario corrija algo visual)
La skill aprende de cómo le gustan los detalles. La sesión que arregla una corrección visual del usuario, al terminar:
1. Escribe la regla general detrás de la corrección (no el caso suelto) en `preferencias-usuario.md`, con antes →
   después, fecha y página. Si ya hay una regla parecida, amplía su ejemplo; **no dupliques**. Si contradice una
   vieja, reemplázala.
2. Si la corrección cambia un componente (p. ej. un botón nuevo aprobado), actualiza también `anexo-guia.md`.
3. Si se puede detectar con el script (p. ej. un patrón de clase o de estilo), súmalo a `revisar_ux.js`.
4. Copia los archivos cambiados a `~/.claude/skills_respaldo/tallerya/revisar-ux/`.
