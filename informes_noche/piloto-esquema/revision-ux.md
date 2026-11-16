# Revisión UX e integración: piloto del freno delantero NMAX 155 (lámina 22)

Tercera revisora (UX e integración) · 15-nov-2026 · revisé `index.html` (v3 final) a 1024/800 px, 390 px y 360 px, y lo comparé con el despiece real (`/garaje/<id>/`, sección «00 Piezas y repuestos», con el caliper delantero abierto). La parte mecánica ya tiene visto bueno (4,67): aquí no la vuelvo a calificar.

Entregables: este informe y **`integrado.html`** (la muestra con los estilos del sitio). Para regenerarla si cambia `index.html`, ver `integracion/` al final.

## 1. Evaluación UX

| # | Criterio | Nota | Evidencia |
|---|---|---|---|
| 1 | Claridad del recorrido y jerarquía | **3** | La página son 6 secciones numeradas, todas al mismo nivel. A 800×690 el primer pantallazo es solo cabecera, aviso e introducción, y el dibujo empieza debajo del borde. «Contradicciones» y «Fuentes» (material interno para el equipo) pesan lo mismo que «Cómo funciona». Largo total: 5.973 px en computador y **10.239 px a 390 px**. Lo bueno: el orden lógico (ver → desarmar → entender → fallas → cuándo) está bien pensado. |
| 2 | Descubribilidad | **3** | En la vista armada los números están al 55 % de opacidad y lo único que dice que se puede tocar es una frase del texto. «Desarmar» sí se ve (botón lava). «Ver por dentro» y «Mostrar números» se entienden. A 360 px la fila de piezas se desliza y solo se ven 2 chips, con el tercero cortado (una pista débil). «Cómo funciona» solo se descubre bajando hasta la sección 2. |
| 3 | Carga cognitiva | **3,5** | Las fichas plegadas están bien: lo esencial a la vista y el resto en un desplegable (4). Pero **«Desarmar» recorre los 14 pasos en unos 3 s** (medido): el texto de cada paso, que es lo más pedagógico, pasa sin dar tiempo a leerlo, y hay que volver con «Paso ▶». Las etiquetas de causa (desgaste, calor, humedad…) suman color sin explicar qué significa cada uno. |
| 4 | Accesibilidad | **3** | Bien: `:focus-visible` en mostaza, números del dibujo con `tabindex`, `role=button`, nombre y Enter/Espacio, foco que salta al título de la ficha, `aria-pressed` en los interruptores, `prefers-reduced-motion` en CSS y en el encuadre, y 44 px en el celular. Por corregir: (a) `#textoPaso` es `aria-live` y durante «Desarmar» anuncia 14 cambios en 3 s; (b) `#ficha` es `aria-live` y vuelve a leer la ficha entera (más de 1.000 px de texto) en cada selección; (c) el SVG es `role="img"` pero tiene botones adentro: Chrome los expone, pero VoiceOver y otros pueden tratarlos como decorativos; (d) hay botones repetidos para el mismo número (9, 5 y 10 aparecen dos veces), lo que suma paradas de tabulador; (e) los números atenuados (mostaza al 55 % sobre carbón) quedan por debajo del contraste de texto. |
| 5 | Rendimiento y peso | **4** | Es un HTML de 96 KB sin imágenes, con 865 nodos (578 del SVG). Las animaciones son transformaciones CSS y no hay errores de consola. En el sitio habría que separar el motor (JS) de los datos (piezas, pasos, fichas) para que el código no se repita en cada lámina y se pueda cachear. |
| 6 | Uso con el pulgar (celular) | **3** | Los botones miden 44 px y los números 46 px; el par más cercano queda a 30 px entre centros, que está bien. Pero a 360 px el dibujo mide **242 px de alto**, y los controles, interruptores y texto ocupan otro tanto. **Al tocar una pieza la ficha aparece abajo y fuera de vista** (a 390 px su borde superior queda a 635 de 844 px y nada avisa que cambió). La ficha mide unos 1.175 px, así que para elegir otra pieza hay que volver a subir. El despiece explotado no se puede acercar (el visor del sitio sí tiene zoom). |
| 7 | Consistencia con TallerYa | **3** | Usa la misma paleta y las mismas fuentes, pero copiadas y con diferencias: crema `#efe6d2` contra `#ede3cc` y mostaza `#e8a92a` contra `#e3a72f`. Los botones van en Archivo con mayúscula inicial, mientras que en el sitio `.btn` es Oswald en mayúsculas. Los títulos no usan `.titulo` y las tarjetas tienen radio de 14 px contra los 18 px de `.papel`. Las secciones van numeradas «1…6» y en el sitio el `.numero` es «00/01». La ficha no tiene lo que sí trae la del sitio: «Pieza N.º», el estado del plan, «Ver guía», «Pedir repuesto» y «Talleres que lo hacen». |

**Promedio UX: 3,4 / 5.** Es un contenido excelente, con buena interacción en computador. Para integrarlo bien faltan sobre todo tres cosas: recorrido, celular y consistencia.

## 2. Cambios propuestos al piloto (priorizados, para la creadora; no edité `index.html`)

**P1, antes de calificarlo:**
1. **Ficha visible al tocar una pieza en el celular** (< 960 px). Que aparezca una barra fija abajo con número, nombre y botón «Ver ficha», que lleva a la ficha y le pasa el foco (así está hecho en `integrado.html`). Otra opción es una hoja inferior. No bajar la página sola, porque se pierde el dibujo.
2. **«Desarmar» más lento y legible**: unos 1,2–1,5 s por paso, o 0,6 s con «Pausa» siempre a mano. Con `prefers-reduced-motion`, saltar directo al despiece completo. Durante la reproducción, quitarle el `aria-live` a `#textoPaso` y anunciar solo el paso final.
3. **Pista de que se puede tocar** en la vista armada: una cápsula «Toca una pieza» que se va con la primera selección (en `integrado.html`, con latido solo si no hay reducción de movimiento), o los números al 80 % de opacidad en vez del 55 %.
4. **Sacar del recorrido del usuario «Contradicciones» y «Fuentes»**. Las contradicciones son para el equipo (van a `cambios.md` o a un informe aparte). Las fuentes quedan plegadas al final como «De dónde sale esta información».

**P2:**
5. `#ficha`: quitar `aria-live` y dejar solo el foco en el `h3`, que ya existe. En el SVG, cambiar `role="img"` por `role="group"` con `aria-label` y dejar un solo botón por número.
6. Agrupar las 4 vistas en pestañas: Piezas · Cómo funciona · Si falla · Cuándo. La página baja de 10.239 a unos 2.050 px a 360 px (medido en la muestra).
7. Botones e interruptores en una sola fila: «Desarmar» + ◀ ▶ + un selector de dos opciones (Números / Por dentro), como `.visor-modo` del sitio.
8. Darle significado a las etiquetas de causa: una leyenda la primera vez, o un `title`.

**P3:**
9. Zoom con pellizco o con los botones + − ⤢ en el despiece explotado del celular (reutilizar la lógica de `.plano`).
10. «Cómo funciona»: pausar la rueda cuando la sección no está a la vista (`IntersectionObserver`).

## 3. Plan de integración

### Dónde vive
- **Principal: dentro del despiece de la moto** («00 Piezas y repuestos» en `garaje/moto.html`). Cuando el sistema elegido tiene esquema, el visor muestra el esquema en vez de la lámina, con pestañas Piezas · Cómo funciona · Si falla · Cuándo, y en la barra lateral el sistema lleva la insignia «Esquema». El panel derecho sigue siendo la ficha del sitio, ampliada con los campos del piloto. Es lo que muestra `integrado.html`.
- **Guía de pieza (`.guia`)**: suma una sección «Cómo falla y por qué» (causas con su etiqueta) y «¿Se repara o se cambia?». También un enlace «Ver en el esquema», que abre el despiece con la pieza elegida (`TallerYaDespiece.abrirGuia` ya resuelve abrir por id).
- **Diagnóstico**: cuando un síntoma apunta al freno delantero, ofrecer la cadena de falla correspondiente («Si falla») y «Cómo funciona» como explicación, reutilizando `_visor_despiece_oculto.html`.
- No hace falta una página aparte. Si se quiere para SEO, una vista pública de solo lectura `/motos/<linea>/esquemas/<sistema>/` sin el estado del plan.

### Cómo se conecta con lo que ya hay
| Del piloto | Con qué del sitio |
|---|---|
| Ficha por pieza | `parte-ficha` de `despiece.js` (`elegir()`): «Pieza N.º», estado, barra del plan, «Ya le hice este mantenimiento», «Ver guía», «Pedir repuesto» (WhatsApp) |
| «Cuándo» (tabla) | Tareas del plan (`garaje/intervalos/nmax*.json`, migración del catálogo): cada fila enlaza a su tarea (`parte.tarea.ancla`) en vez de repetir el texto |
| «Talleres que lo hacen» | `/?servicio=<tarea.servicio>` (ya existe en la guía) |
| Nombres y números | `despiece_mapas/*.json` y `despiece_glosario.py` (aquí se corrigen las contradicciones 5, 6 y 8) |
| Fichas «qué es / cómo falla» | `despiece_fichas.py` (aquí se corrigen las contradicciones 2, 3, 9, 10 y 11) |

### Componentes y clases que reutiliza (comprobado en la muestra)
`.papel`, `.titulo`, `.numero`, `.separador`, `.btn .btn-lava / .btn-borde / .btn-whatsapp`, `.boton-seccion` (◀ ▶), `.visor-modo` (pestañas y selector), `.chip`, `.estado-*`, `.barra-*`, `.parte-ficha`, `.parte-tarea`, `.despiece / .despiece-sistemas / .despiece-visor / .despiece-panel`, `.visor-barra`, `.sistemas-*`, y la cabecera de `base.html`. Lo nuevo cabe en unas 90 líneas con el prefijo `esq-`: lienzo, pista, barra fija del celular, pestañas con `role=tab`, tabla y fuentes plegadas.

### Qué hay que generalizar para otras láminas
1. **Motor y datos por separado**: `garaje/static/garaje/js/esquema.js` (encuadre, pasos, selección, rayos X, interruptores, cómo funciona, cadenas) y un archivo de datos por lámina, `garaje/esquemas/<moto>-fig22.json`, con `piezas[]`, `pasos[]`, `fn[]`, `cadenas[]` y `fichas{}`.
2. **El arte**: hoy el SVG lo generan funciones JS (`arteCaliper()`, `extruir()`…). Hay dos caminos: (a) exportar el SVG ya armado (un `<g id="pz-N">` por pieza) desde un script, como `diagramas.py`, y guardarlo como estático; o (b) dejar las funciones de arte en un módulo por lámina. Recomiendo **(a)**: se puede cachear, no ejecuta JS para dibujar y sigue el mismo flujo que los dibujos del despiece.
3. **Fichas**: subir los campos nuevos (causas, decisión, «qué se compra», «arrastra») a `despiece_fichas.py` con la clave del catálogo, para que la guía y el esquema lean del mismo lugar.
4. **Estado del plan**: lo pone el servidor (como hoy `parte.tarea`), no el esquema.
5. **Vista Django**: `despiece_json` agrega `esquema_url` cuando el sistema lo tiene. `despiece.js` carga `esquema.js` bajo demanda (igual que el 3D) solo si se abre ese sistema.

### Esfuerzo estimado
| Trabajo | Esfuerzo |
|---|---|
| Separar motor/datos y exportar el SVG del freno NMAX | 1,5–2 días |
| Integrarlo en el visor de `moto.html` (pestañas, ficha unificada, plan, acciones, carga bajo demanda) | 1,5–2 días |
| Cambios P1–P2 de este informe | 1 día |
| Pruebas (vista JSON, accesibilidad básica, 360 px) | 0,5 día |
| **Primera lámina integrada** | **unos 5 días** |
| Cada lámina nueva (dibujo + pasos + fichas + revisión mecánica) | 1,5–3 días, casi todo de dibujo y contenido |

## 4. Muestra integrada: `integrado.html`
- Enlaza `tallerya.css` y `tw.css` reales con rutas relativas (`../../talleres/static/...`). Hay que abrirla desde la carpeta del proyecto. Si se abre como copia suelta o en una vista previa que no resuelve rutas relativas, se ve sin estilos.
- Tiene la cabecera del sitio con el logo real, las migas, la sección «00 Piezas y repuestos», la barra lateral de sistemas (Frenos abierto, «Caliper de freno delantero» con la insignia «Esquema»), el visor con las 4 pestañas (navegables con las flechas) y el panel de ficha (fijo en computador). La ficha muestra **estado del plan + Ver guía + Pedir repuesto + Talleres** justo bajo el nombre (datos del plan de muestra para pastillas, líquido, empaques y mangueras). Las fuentes van plegadas y en el celular hay una barra fija con la pieza elegida.
- El dibujo, los textos y el JS del piloto van **sin cambios**: se copian desde `index.html` y la capa de integración solo envuelve `seleccionar()`.
- Comprobado: sin errores de consola; a 1280 px salen 3 columnas; a 360 px no hay desborde (scrollWidth 360) y la página mide unos 2.050 px. Los botones miden 44 px, la barra fija aparece al tocar una pieza y se esconde cuando la ficha está a la vista, y «Si falla → número» cambia a la pestaña Piezas y elige la pieza.
- Para regenerarla: `venv/Scripts/python.exe informes_noche/piloto-esquema/integracion/armar_integrado.py informes_noche/piloto-esquema/integracion/plantilla_integrado.html`.
- Límites de la muestra: la barra lateral es estática, «Ver guía» abre el desplegable de la ficha (en el sitio abriría `.guia`) y los estados del plan son de ejemplo.
