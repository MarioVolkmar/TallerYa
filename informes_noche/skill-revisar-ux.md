# Skill `revisar-ux` (19-nov-2026)

**Qué es:** revisión de diseño y usabilidad que cualquier sesión corre antes de entregar un cambio visual, o para
auditar una página. Vive en `.claude/skills/revisar-ux/` (respaldo en `~/.claude/skills_respaldo/tallerya/revisar-ux/`,
anotada en `CATALOGO.md`; línea nueva en `CLAUDE.md`, sección Pruebas). No hay commit.

| Archivo | Para qué |
|---|---|
| `SKILL.md` | metas (≤ 10 min por página, ≤ 2 capturas, cero bloqueantes), flujo, tabla de falsos positivos, lista manual de 8 puntos, formato del informe y autocontrol |
| `anexo-guia.md` | guía de estilo sacada de `tallerya.css` y las plantillas: tokens, Oswald/Archivo, y qué componente usar en cada caso (botón lava / borde / `boton-seccion` / `boton-suave`, chips, estados, chapas, `.papel.tarjeta`, encabezado numerado, avisos, formularios, interruptor, vacío con Chispa) |
| `revisar_ux.js` | se pega en `javascript_tool`. Busca desbordes y scroll horizontal, texto cortado, texto tapado (por flotantes solo si no se puede sacar de debajo), toques < 44 px en celular (< 24 en escritorio), contraste AA, enlaces subrayados sueltos, minúscula inicial, «—»/None/celdas vacías y elementos sin nombre accesible. Se pega una sola vez: queda en `localStorage` y se vuelve a correr con un `<script>` en línea (la CSP bloquea `eval`) |
| `entrar.py` | crea una sesión de Django por correo, sin contraseña, e imprime la cookie |

**Prueba:** 3 páginas × 2 anchos, unos 12 min en total. El script tarda < 2 s por corrida. Lo que salió de la prueba
ya está corregido en la skill: la cabecera sticky daba falsos «tapados», el contraste daba 4,50 por redondeo, la minúscula
fallaba con `<strong>` al inicio, la CSP bloqueaba `eval`, con el panel oculto `innerWidth` da 0, y una captura
tomada durante la animación de entrada sale «apagada».

## Ronda 2 (19-nov): congruencia primero y preferencias que se aprenden
- **Regla n.º 1 de la lista: congruencia.** «¿Usa los componentes, colores, tipografías, espaciados y tono que ya
  existen?». Antes de crear un estilo hay que buscar su equivalente; uno nuevo se justifica, se agrega a la guía y queda
  igual en todas las páginas donde aplica.
- **El script marca lo que se sale de la guía:** `color-fuera` (texto, fondo o borde a más de 30 de la paleta, y bordes
  punteados), `fuente-fuera` (ni Oswald ni Archivo) y `radio-fuera` (fuera de 0–24 px o cápsula). Probado en
  `/garaje/3/`: 8 bordes punteados (aviso de documento sin fecha y lista de fuentes), blanco puro en la campanita,
  rosado suelto en «¿Te varaste?», un verde Tailwind y un radio de 19 px en `.tc-portada`.
- **`preferencias-usuario.md`** (segunda capa, punto 2 de la lista): 16 reglas con antes → después y fecha, sacadas
  de los informes de Ruta (rondas 2–5), la ficha del mecánico (ronda 3) y los criterios del piloto del despiece.
- **Paso de aprendizaje (§ 5):** quien arregle una corrección visual del usuario anota la regla general, sin duplicar
  y con fecha; si cambia un componente, actualiza la guía; si se puede detectar, la suma al script; y copia al respaldo.

## Hallazgos (solo reportados, nada corregido)

| Prioridad | Dónde | Problema | Arreglo sugerido |
|---|---|---|---|
| Importante | `/garaje/3/` · Documentos (SOAT y técnico-mecánica) | «Sin fecha» + «—» + «Agrega la fecha de vencimiento» + botón: el «—» no aporta y repite | Quitar el «—»; dejar «Sin fecha» y el botón «Agregar fecha» |
| Importante | `/garaje/3/` · Aceite de motor (tablero) | «Pasado por 0 km» se contradice (`garaje/views.py:453`, sale cuando vence por tiempo con 0 km) | Si km ≤ 0 y vence por tiempo: «Toca ya (por tiempo)» |
| Importante | `/garaje/3/` · ficha de la pieza 11 del despiece | chip «Toca ya» junto a «Faltan 350 km» | Usar el mismo criterio en el chip y en el texto (o explicar «por tiempo») |
| Importante | `/garaje/3/` · Pedir SOAT | botón de 98×26 px en celular | `min-height:44px` (o el mismo tamaño que «Agregar fecha») |
| Importante | `/garaje/3/` en celular | lo principal (estado de los sistemas: 11 requieren atención) queda debajo del visor 3D, fuera de la primera pantalla | Decisión del usuario: resumen de estado arriba del 3D en celular, o 3D más bajo |
| Importante | `/garaje/3/` · ficha de la pieza | «Ver más talleres» es un enlace subrayado suelto; «Pedir cita por WhatsApp» mide 18 px de alto | Pasarlos a `boton-suave` o `.btn-borde` compacto |
| Importante | `/mecanicos/wilson-arango-demo/` · Precios desde | celdas con «—» donde no ofrece ese rango de cc | «No aplica» en texto suave, o mostrar solo las columnas con precio |
| Importante | Todo el sitio en celular | el estándar de toque es 40 px (chips, `boton-seccion`, accesos, favorito/WhatsApp de la tarjeta, +/−/⤢ del despiece); 37–49 casos por página | Una regla general: `min-height:44px` en `.boton-seccion`, `.moto-acceso`, `.tc-fav`, `.tc-wa`, chips clicables y controles del plano bajo 768 px |
| Importante | Pie de página (todas) | enlaces de 16 px de alto, pegados | `padding-block:.6rem` en celular (o lista con más interlineado) |
| Detalle | Portada · Foro | «3 horas,2 minutos» (sin espacio; `inicio.html:234`, `timesince`) | Filtro «hace 3 h» con una sola unidad |
| Detalle | Portada · Rodadas | «viernes · 7:00 a.m.…» empieza en minúscula; los nombres se cortan con «…» en 375 px | «Viernes»; permitir 2 líneas (`line-clamp:2`) en vez de una sola línea con «…» |
| Detalle | Portada | «Ver los 17 talleres» arriba y «Ver todos los talleres» abajo repiten | Dejar uno |
| Detalle | Portada, `/garaje/3/` y ficha en celular | Chispa flotante tapa el borde de la tarjeta del buscador y la esquina del visor 3D (el script no lo ve: `pointer-events:none`) | Correrla más abajo o esconderla mientras haya una tarjeta o un visor debajo |
| Detalle | `/garaje/3/` · secciones | la numeración empieza en «00 Piezas y repuestos» | Empezar en 01 |
| Detalle | `/garaje/3/` · Pico y placa / agenda | «Agrega la placa» aparece dos veces | Dejar el aviso en una sola tarjeta |
| Detalle | `/garaje/3/` · «Resuelve 11 cosas en una sola visita» | párrafo con 11 servicios seguidos | «Hace 11 de tus pendientes» + chips con los 3 primeros y «+8» |
| Detalle | `/garaje/3/` · fuentes de fallas | «revisado el 2026-11-18» (ISO) | «revisado el 18 nov 2026» |
| Detalle | `/garaje/3/` · «Ver hoja de vida / gastos» | contraste 4,3:1 | Subir el color a crema-2 o lava-2 |
| Detalle | Ficha del mecánico · Cómo trabaja | «Te mandamos fotos / Te devolvemos» (plural de empresa en la ficha de una persona) | «Te manda fotos por WhatsApp», «Te devuelve las piezas cambiadas» |
| Detalle | Ficha del mecánico · Reseñas | barras de 5★ a 1★ con una sola reseña | Mostrar la distribución desde 3 reseñas |
| Detalle | Ficha del mecánico · Precios | «desde $30.000» y «se suma al servicio…» en minúscula como etiquetas sueltas | «Desde $30.000» / «Se suma al servicio» |

Sin bloqueantes: ninguna de las 3 páginas tiene scroll horizontal ni texto tapado por la barra inferior o por WhatsApp
en 375 ni en 1280 px. Lo que se repite en todo el sitio es el tamaño de toque en celular (40 px en vez de 44).
