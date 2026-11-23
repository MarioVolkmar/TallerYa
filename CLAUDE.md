# TallerYa — guía para agentes

Django (Python) para talleres de motos en Medellín. Todo en español (código, UI, commits).

## Mapa (no hace falta explorar)
- `config/` settings y urls · `templates/base.html` · CSS: base común `talleres/static/talleres/css/tallerya.css` + hojas por sección `talleres/css/secciones/<app>.css` (garaje, talleres, cuentas, foro, cupones, tramites), cargadas solo en las plantillas `<app>/...` por `{% css_seccion %}`; una clase que pase a usarse en otra sección va a la base
- Tailwind va compilado en `talleres/static/talleres/css/tw.css` (no hay CDN): tras usar clases de Tailwind nuevas, correr `npm run css` (config en `tailwind/`)
- Apps: `talleres` (directorio, portada), `cuentas` (login, Google, roles, Plus), `cupones`, `foro`, `notificaciones`, `garaje` (motos, plan de mantenimiento, 3D, despiece)
- Despiece: `garaje/diagramas.py` (dibujos SVG propios), `despiece_fichas.py`, `despiece_glosario.py`, `despiece_mapas/*.json`, `static/garaje/js/despiece.js`; importador `manage.py importar_despiece`
- 3D: `garaje/static/garaje/js/moto3d.js` (2200 líneas: leer por rangos) · **Regla del usuario para modelos de Tripo:** la geometría de Tripo NO se cambia; solo se permite poner la placa, arreglar piezas flotando y corregir errores puntuales que el usuario señale (nada de llantas, rines, farolas ni piezas propias o del visor encima)
- Python: `venv/Scripts/python.exe` · servidor: preview `tallerya` (puerto 8001)
- Blender 5.3 sin ventana: `"/c/Program Files/Blender Foundation/Blender 5.3/blender.exe" -b --factory-startup --python script.py -- args` (scripts en el scratchpad o en la carpeta de la herramienta; salida a log) · GLB: `npx gltf-transform validate|inspect|weld|simplify|quantize archivo.glb` (meshopt aún no: el visor no tiene el decodificador)
- Solo local, nunca al repo ni a servicios externos: `despiece_local/`, `manual_despiece/`, `planos_a_generar/`, `media/`, `privado/`, `db.sqlite3`

## Pruebas
`manage.py test` ya es rápido (`config/test_runner.py`): MD5, paralelo (un proceso por núcleo físico, máx. 6; `--parallel 1` lo apaga) y plantilla de la base en `%TEMP%/tallerya_pruebas/` (la primera corrida migra ~30 s; luego <1 s; se regenera sola al cambiar migraciones; `PRUEBAS_SIN_PLANTILLA=1` obliga a migrar). Todo con `venv/Scripts/python.exe`:
- **Rápida** (diaria / antes de commit): `manage.py test --exclude-tag=lenta -v 1` (777 pruebas; ~1 min). Si solo cambió CSS/JS/plantillas/texto, ninguna.
- **Completa** (antes de desplegar, o si cambian modelos/migraciones, `config/`, `templates/base.html` o código compartido): `manage.py test -v 1` (823, incluye `@tag("lenta")`).
- **Focalizada**: `manage.py test garaje.tests.Clase -v 1` (~10 s de arranque).
- Tiempos por prueba: `TEST_TIMING=archivo.json manage.py test --parallel 1`. `--keepdb` no hace falta. Con la CPU al 100 % por otras sesiones todo tarda el doble: no es regresión.
- **Cambios visuales** (plantillas, CSS, JS de interfaz, textos): antes de entregarlos, skill `revisar-ux` (1280 y 375 px; sin bloqueantes propios).
- **Velocidad**: cambios que afecten la carga (JS, CSS, plantillas base, vistas con listas, 3D, despiece) se miden antes y después con `optimizar-velocidad`.
- Pruebas nuevas: `tempfile.mkdtemp()` para archivos, datos de partida en `setUpTestData`, `@tag("lenta")` si pasan de ~2 s.

## Trabajar gastando pocos tokens (misma calidad)
Cada resultado de herramienta se queda en el contexto y se vuelve a pagar en cada turno.
- **Leer poco**: Grep antes que Read; Read con `offset`/`limit` en archivos grandes; no releer un archivo ya leído ni tras editarlo.
- **Salida corta**: `| tail -20`, `| head -40`, `grep -c`, `-q`; pruebas con `-v 1`; nunca volcar JSON/SVG/HTML enteros. Salidas largas (pruebas, 3D, mediciones, builds) a un archivo del scratchpad y mostrar solo el resumen.
- **PDF de catálogos y manuales** (`despiece_local/`, `manual_despiece/`): fuentes de la página; **solo se leen, nunca se editan, mueven ni borran**. Ubicar la página (índice o búsqueda) y `Read` con `pages` solo de esa lámina y su tabla; nunca el PDF entero.
- **Imágenes = lo más caro** (~1.500 tokens c/u): para texto o estructura usar `read_page`/`get_page_text`/`javascript_tool`. Si hace falta ver: `scale: 0.5` o `zoom` a la región; PNG a ≤900 px o recortados. Una captura final como prueba, no una por iteración.
- **Navegador**: no repetir `resize_window`; agrupar pasos en `browser_batch` sin capturas intermedias.
- **Scripts repetidos** más de 2 veces: guardarlos en el scratchpad.
- **Búsqueda amplia**: subagente `Explore` (modelo `haiku`) y recibir solo la conclusión.
- **Tope de contexto por sesión: ~250 mil en tareas livianas** (vistas, plantillas, CSS, pruebas, informes, coordinación) **y ~300 mil en las pesadas** (3D, láminas del despiece, skills grandes, funciones nuevas con diseño); **300 mil es el techo de todas** (decisión del usuario, 23-nov: con 150 mil las sesiones se cortaban a mitad de encargo y cada relevo repaga el arranque). Al llegar al tope: **terminar el encargo en curso** (y sus ajustes cortos), no aceptar encargos nuevos y, al terminar, escribir una nota de relevo (qué se hizo, qué falta, archivos) en el informe o la memoria; un relevo a mitad de encargo cuesta más que terminarlo. Al llegar al techo: solo el paso en curso y relevo. Un hook (`.claude/herramientas/aviso_contexto.py`) avisa una vez a ~250 mil y otra a 300 mil; no corta nada.
- **Repartir entre sesiones**: una sesión nueva arranca en ~81 mil medidos el 23-nov (casi todo es el sistema y las herramientas; CLAUDE.md y memorias son ~4 mil), más la skill y el relevo que lea, y lo recupera tras ~8-10 turnos. Más rondas de la MISMA moto o tarea siguen en la misma sesión mientras esté bajo su tope; otro tema, o una sesión que pasó su tope, va a una sesión NUEVA con relevo corto (memoria y archivos), una tarea por sesión. Memorias de relevo cortas (estado actual y trampas vigentes; historial en archivo aparte), borradas al commitear su trabajo; SendMessage solo para aclaraciones o ajustes cortos. Al abrir sesión o agente indicar siempre `model` según la tabla; antes de mandar trabajo a una existente, mirar su tamaño.
- **Skills cortas**: el SKILL.md se carga entero; solo flujo y reglas, trampas e historiales en archivos aparte. **Encargos a otras sesiones cortos** (~150-250 palabras; quedan en el contexto del coordinador para siempre): qué hacer, criterio de «listo», restricciones (qué no tocar, sin commit) y dónde leer el resto (archivos, memoria de relevo); no explicar lo que la sesión puede leer en el código. **Archivar** las sesiones terminadas (sin trabajo vivo) al cerrar cada tanda: la lista de sesiones vinculadas se repite en cada aviso.
- Ejecutar sin narrar opciones descartadas; respuestas finales breves.

### Modelo según la tarea (no matar moscas a cañonazos)
| Modelo | Para qué |
|---|---|
| `haiku` | buscar en el código, bajar fotos o fuentes, correr pruebas e informar, auditorías con lista, consultas de estado, cambios mecánicos |
| `sonnet` (por defecto) | vistas y plantillas Django, CSS y arreglos UX acotados, fallas frecuentes, seguridad, medir velocidad, informes, coordinación |
| `opus` | 3D, láminas del despiece, funciones nuevas que piden diseño, errores difíciles |
| `fable` | respaldo para 3D o láminas cuando opus no alcance (cupo semanal propio) |

**Esfuerzo** (se elige con el modelo):
| Esfuerzo | Cuándo | Ejemplos |
|---|---|---|
| `low` | resultado conocido y fácil de comprobar; un error no rompe nada | buscar, bajar archivos, correr pruebas, renombrar, mover textos, estado |
| `medium` (por defecto) | trabajo conocido con pocas decisiones, dentro de un patrón existente | plantilla o vista igual a otras, arreglo de CSS o UX, fallas de una moto, informes |
| `high` | varias piezas que encajan, decisiones de diseño o errores sin causa clara | función nueva, depurar, seguridad, optimizar velocidad, revisión mecánica |
| `xhigh` / `max` | solo cuando `high` ya falló o debe ser fiel a una referencia exigente | 3D con IoU exigente, láminas fieles al plano, migraciones delicadas |

Si cabe en una frase y se verifica en un comando, `low`; si hay que decidir entre opciones, `high`. Subir un nivel solo tras un intento fallido. **Sesiones `opus`: siempre `medium`** (decisión del usuario, 19-nov); `high` solo si `medium` ya falló. Medir consumo: `python -I .claude/herramientas/uso_tokens.py` (topes nuevos desde el 23-nov, comparar el 30-nov).

## Coordinación
Puede haber varias sesiones a la vez en esta carpeta: no editar archivos que otra sesión está tocando (portada/entrar = sesión "Proyecto tallerYa"; dibujos del despiece = sesión de dibujos) sin avisar. No hacer commit sin que el usuario lo pida. Si una sesión deja relevo con pendientes, el coordinador lanza enseguida la que continúa (mismo modelo y esfuerzo), sin esperar a que se lo pidan.
