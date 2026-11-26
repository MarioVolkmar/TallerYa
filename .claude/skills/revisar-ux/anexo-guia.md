# Guía de estilo de TallerYa (componentes reales)

Fuente: `talleres/static/talleres/css/tallerya.css` (estilo «papel recortado», oscuro) + Tailwind compilado (`tw.css`,
correr `npm run css` tras clases nuevas). **Congruencia primero:** antes de crear un estilo, busca aquí el componente (y en `tallerya.css` y las plantillas)
y reutilízalo. Si de verdad hace falta uno nuevo: que herede tokens y sombra dura, se justifique en el informe, se
agregue a esta guía y quede igual en todas las páginas donde aplica.

## Tokens
| Token | Valor | Uso |
|---|---|---|
| `--carbon` / `--carbon-2` | #111517 / #161c1e | fondo de página / fondo de campos |
| `--pizarra` / `--pizarra-2` | #1d2427 / #252e31 | tarjetas (`.papel`, degradado) |
| `--borde` | #354044 | bordes de chips y campos |
| `--crema` / `--crema-2` | #ede3cc / #c9bfa7 | texto principal / texto suave (`.text-suave`) |
| `--lava` / `--lava-2` | #f2611d / #ff9a3c | acción principal, números de sección, foco de campos |
| `--mostaza` | #e3a72f | etiquetas (`.etiqueta`), avisos, Plus, «pronto» |
| `--ok` / `--vencido` / `--desconocido` | #3fbf6b / #ff5a3c / #8a9096 | estados de mantenimiento |
| papel del plano | #fbf8f1 | fondo crema del dibujo del despiece |
| `--sombra-papel` | sombra suave + **5px 5px 0 #0b0e0f** | la sombra dura desplazada es la firma del sitio |

Texto oscuro sobre lava/mostaza/crema: `#1a0d05` (no negro puro). WhatsApp: `#1fae5b` con texto `#04140a`.

## Tipografía
- **Oswald** (500–700), en MAYÚSCULAS: títulos `.titulo`, botones `.btn`, etiquetas `.etiqueta` (mostaza, tracking .22em
  con rayita lava antes), chips de estado `.estado`/`.insignia`, números `.numero`.
- **Archivo** (400–700): todo el texto corrido; base 1.0625rem (17 px), interlineado 1.55, peso 500.
- El texto pequeño de Tailwind (`text-xs`/`text-sm`) ya va agrandado en el CSS: no bajar de `text-xs` ni usar px fijos < 12.

## Componentes y cuándo usarlos
| Caso | Usa | Nunca |
|---|---|---|
| Acción principal (una por vista o tarjeta) | `.btn.btn-lava` (degradado lava, sombra dura) | dos botones lava juntos |
| Acción secundaria | `.btn.btn-borde` (borde crema, hover relleno crema) o `.boton-seccion` en encabezados de sección (cápsula 40 px, ícono lava) | enlace subrayado suelto («ver», «Ajustes») |
| Acción terciaria en línea / filtro | `.boton-suave` (cápsula con borde fino) | texto subrayado |
| Destructiva | `.btn.btn-peligro`, siempre con confirmación | lava |
| Plus | `.btn.btn-plus` (dorado) | lava |
| Contactar por WhatsApp | `.btn.btn-whatsapp`; si flota, reservar espacio para que no tape horarios ni textos | — |
| Volver | `templates/parciales/volver.html` | flecha suelta |
| Dato corto / filtro / categoría | `.chip` (cápsula, borde `--borde`, texto crema-2), mayúscula inicial | texto plano con «·» |
| Estado (al día, pronto, vencido, sin datos) | `.estado .estado-ok/-pronto/-vencido/-desconocido` | colores sueltos |
| Sello sobre una tarjeta (verificado, Trabajo, nuevo) | `.insignia-lava`, `.insignia-verificado`, `.tc-chapa*`; si sobresale del borde, debe moverse con el hover de la tarjeta | chapa quieta mientras la tarjeta sube |
| Contenedor | `.papel` (pizarra, radio 18 px, sombra dura) | recuadro punteado, bordes grises planos |
| Tarjeta clicable | `.papel.tarjeta` (hover: sube -2/-3 px y crece la sombra; `.ver` en lava abre el gap); toda la tarjeta es el enlace | solo el título clicable |
| Encabezado de sección | `h2.titulo` con `<span class="numero">01</span>` (lava, Oswald) + `.boton-seccion` a la derecha para su acción | numerar secciones que no son una secuencia |
| Sección plegable | `.seccion-boton` + `.seccion-flecha` + `.seccion-cuerpo` | — |
| Mensaje del sistema (éxito, info) | `.mensaje` (borde izquierdo mostaza, sombra dura) o `.aviso-flotante` breve | alert rojo para todo |
| Aviso que pide acción | `.aviso-correo` (fondo mostaza 10 %, ícono mostaza, botón `.aviso-correo-boton`) | párrafo largo |
| Aviso de documento | `.aviso-doc-vencido/-pronto/-desconocido` | — |
| Aviso legal / letra menuda | párrafo `text-xs text-suave` al final; `.aviso-suave` para notas bajo un campo | recuadro, color o ícono que compita con el contenido |
| Formulario | `label.campo-label` + `.campo` (radio 12 px, foco lava con halo); errores `.error`; opciones `.opcion` (marcada = borde lava) | placeholder como única etiqueta |
| Sí/no | `label.interruptor` (input + `span[aria-hidden]` + `.sr-only` con el texto) **dentro** de la fila de su tarjeta (`.cajon-fila`) | checkbox suelto fuera de la tarjeta |
| Ajuste rápido de un dato dentro de una sección (uso de la moto en la agenda) | `.agenda-uso`: etiqueta Oswald pequeña + `select.campo` (44 px) + `.boton-seccion` «Cambiar» en la misma fila y una línea de ayuda `text-suave`; en celular la etiqueta va arriba | mandar a «Datos de la moto» para cambiar un solo dato que afecta la sección |
| Vacío | `{% include "parciales/vacio.html" with tam="chico" %}` (Chispa) + una frase de tú + **un botón** para salir del vacío (`.vacio-izq` en listas) | «—», «No hay datos», bloque vacío |
| Dato que falta en una ficha | botón secundario o chip con la acción («Agrega la placa») | «—» o «Sin información» |
| Número decorativo grande | `.numero-fantasma` (solo decoración, `pointer-events:none`) | — |
| Documento para imprimir o PDF (certificado de hoja de vida) | `.cert` (hoja clara `#fbf8f1`, texto `#111517`/`#354044`, marca en lava a 24 px, estados `.cert-verificado/-pendiente/-propio`) + `.cert-barra.no-imprimir` con «Imprimir / Guardar PDF» (lava); `@media print` oculta todo lo que no es `main` | pizarra oscura en papel; librerías de PDF |

## Espaciado y forma
- Radios: tarjetas 18 px, campos/avisos 12–16 px, botones/chips 999 px (cápsula).
- Padding de botones: grandes `px-5 py-3`; compactos `px-4 py-2.5` + `min-height:44px` en celular. Nunca un botón
  cuyo texto toque los bordes: si no cabe, texto más corto o ancho completo.
- Ritmo vertical: entre secciones `mt-10`/`mt-12`, dentro de una tarjeta `p-5 sm:p-6`, entre filas `gap-3`/`gap-4`.
- Margen lateral en celular ≥ 16 px; nada a sangre salvo visor 3D y plano del despiece.
- Foco: `:focus-visible` con contorno crema 2–3 px u halo lava (campos). Animaciones con `@media (prefers-reduced-motion: reduce)`.

## Textos
De tú, con calidez paisa sin exagerar; mayúscula inicial siempre (las mayúsculas de Oswald las pone el CSS: en la
plantilla se escribe «Cerrar jornada», no «CERRAR JORNADA»). Botones = verbo + objeto («Agendar cita»). Sin
instrucciones obvias ni «Haz clic aquí». Nombre de sección = su contenido.
- **Registro de mecánico** (`domicilio/css/registro.css`, nov-2026): opción tipo tarjeta con radio (`.rm-op`, atajos «Toda Medellín / Todo el Valle / Elegir»), interruptor en línea (`.rm-sw` + `.rm-tog`, casilla real escondida), bloque plegado opcional (`details.rm-opcional`) y barra fija de avance con «Seguir» (`.rm-barra`, sube sobre la barra inferior y empuja a Chispa). Reutilizar estos antes de inventar otros en formularios largos.
- **Descuentos de mecánicos** (nov-2026): por dentro son cupones; en lo nuevo se dice «descuento». Chapa del ticket `.insignia.ticket-domicilio` y chapa de tarjeta `.dom-chapa-descuento`, mismos colores que `.dom-chapa-taller` (fondo oscuro, mostaza, borde sólido). Lista y formulario reutilizan `.pt-cupon*` y `.cf-*` (ya en la base). Filtros de `/cupones/` = `.dir-chip` a 44 px + `select.campo`.

### Camino del motero (25-nov)
- `.ciclo` (`templates/parciales/ciclo.html`, datos de `talleres/ciclo.py`): pasos Pedida → Confirmada → En el taller/Trabajando → Lista → En tu hoja de vida → Calificada; hecho = punto `--ok` con ✓, actual = borde lava con su detalle; debajo `.ciclo-siguiente` con el único botón lava. A 375 px los pasos van en columna. Se usa en el detalle de la cita (Mis citas), `cita_publica` y `visita_publica`.
- `.en-curso` (`templates/parciales/en_curso.html`): franja «Tu moto … está en X · en reparación» con `boton-seccion`; verde (`.lista`) cuando está lista. En Mis citas y la página de la moto.
