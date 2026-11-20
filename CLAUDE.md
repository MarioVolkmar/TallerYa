# TallerYa — guía para agentes

Django (Python) para talleres de motos en Medellín. Todo en español (código, UI, commits).

## Mapa (no hace falta explorar)
- `config/` settings y urls · `templates/base.html` · CSS: base común `talleres/static/talleres/css/tallerya.css` + hojas por sección `talleres/css/secciones/<app>.css` (garaje, talleres, cuentas, foro, cupones, tramites), cargadas solo en las plantillas `<app>/...` por `{% css_seccion %}`; una clase que pase a usarse en otra sección va a la base
- Tailwind va compilado en `talleres/static/talleres/css/tw.css` (no hay CDN): tras usar clases de Tailwind nuevas, correr `npm run css` (config en `tailwind/`)
- Apps: `talleres` (directorio, portada), `cuentas` (login, Google, roles, Plus), `cupones`, `foro`, `notificaciones`, `garaje` (motos, plan de mantenimiento, 3D, despiece)
- Despiece: `garaje/diagramas.py` (dibujos SVG propios), `despiece_fichas.py`, `despiece_glosario.py`, `despiece_mapas/*.json`, `static/garaje/js/despiece.js`; importador `manage.py importar_despiece`
- 3D: `garaje/static/garaje/js/moto3d.js` (2200 líneas: leer por rangos)
- Python: `venv/Scripts/python.exe` · servidor: preview `tallerya` (puerto 8001)
- Solo local, nunca al repo ni a servicios externos: `despiece_local/`, `manual_despiece/`, `planos_a_generar/`, `media/`, `privado/`, `db.sqlite3`

## Pruebas
Al correr `manage.py test` ya son rápidas por defecto (`config/test_runner.py`): hash MD5 de contraseñas, paralelo (un proceso por núcleo físico, máx. 6; `--parallel 1` lo apaga) y **plantilla de la base de pruebas**: la primera corrida migra como siempre (~30 s) y guarda una copia en `%TEMP%/tallerya_pruebas/`; las siguientes la copian en <1 s. Cambiar o agregar cualquier migración la regenera sola (hash de los archivos de migraciones). `PRUEBAS_SIN_PLANTILLA=1` obliga a migrar. Comandos (todos con `venv/Scripts/python.exe`):
- **Rápida** (diaria / antes de commit): `manage.py test --exclude-tag=lenta -v 1` (777 pruebas; ~8 s de arranque + ~35-60 s según la carga de la máquina). Si solo cambió CSS/JS/plantillas/texto, ninguna.
- **Completa** (antes de desplegar, o si cambian modelos/migraciones, `config/`, `templates/base.html` o código compartido): `manage.py test -v 1` (823 pruebas, incluye las `@tag("lenta")`: despiece, diagnóstico, demo completo).
- **Focalizada**: `manage.py test garaje.tests.Clase -v 1` (~10 s de arranque fijo: imports y chequeos).
- Tiempos por prueba: `TEST_TIMING=archivo.json manage.py test --parallel 1`. `--keepdb` no hace falta (la plantilla ya evita migrar).
- Si otras sesiones tienen la CPU al 100 % (3D, otras pruebas), todo tarda el doble o más: no es una regresión.
- **Cambios visuales** (plantillas, CSS, JS de interfaz, textos): antes de entregarlos, correr la skill `revisar-ux` (script en 1280 y 375 px + lista; sin bloqueantes propios).
- **Velocidad**: los cambios que afecten la carga (JS, CSS, plantillas base, vistas con listas, 3D, despiece) se miden antes y después con la skill `optimizar-velocidad`.
- Pruebas nuevas: usar `tempfile.mkdtemp()` para archivos (seguro en paralelo), datos de partida en `setUpTestData` (no en `setUp`) y `@tag("lenta")` si pasan de ~2 s.

## Trabajar gastando pocos tokens (misma calidad)
Cada resultado de herramienta se queda en el contexto y se vuelve a pagar en cada turno siguiente.
- **Leer poco**: Grep antes que Read; Read con `offset`/`limit` en archivos grandes; no releer un archivo ya leído ni tras editarlo.
- **Salida corta**: limitar comandos (`| tail -20`, `| head -40`, `grep -c`, `-q`); pruebas con `-v 1`; nunca volcar JSON/SVG/HTML enteros, mostrar solo la parte relevante.
- **PDF de catálogos y manuales** (`despiece_local/`, `manual_despiece/`): son las fuentes de la página, así que **solo se leen; nunca se editan, mueven ni borran**. Leer solo lo necesario: primero ubicar la página (índice o búsqueda) y luego `Read` con `pages` solo de esa lámina y su tabla. Nunca el PDF entero: cada página es una imagen cara.
- **Imágenes = lo más caro** (~1.500 tokens c/u): para verificar texto o estructura usar `read_page`/`get_page_text`/`javascript_tool`, no capturas. Si hace falta ver: captura con `scale: 0.5` o `zoom` a la región; renders PNG de dibujos a ≤900 px de ancho o recortados a la zona cambiada. Una captura final como prueba, no una por iteración.
- **Navegador**: no repetir `resize_window`; agrupar pasos en `browser_batch` sin capturas intermedias.
- **Scripts repetidos**: si un script de verificación se usa más de 2 veces, guardarlo en el scratchpad y reutilizarlo en vez de reescribir heredocs.
- **Búsqueda amplia**: delegar a un subagente `Explore` (modelo `haiku`) y recibir solo la conclusión.
- **Sesiones cortas y enfocadas**: una tarea por sesión; al cambiar de tema, sesión nueva. Lo que deba persistir va a la memoria, no al historial.
- **Tope de contexto por sesión: ~150 mil en tareas livianas** (vistas, plantillas, CSS, pruebas, informes, coordinación) **y ~250 mil en las pesadas** (3D, láminas del despiece, skills grandes, funciones nuevas con diseño), porque un relevo en esas obliga a releer skill y archivos (el 99 % del gasto es releer el historial en cada turno; línea base 19-nov: 231 mil por turno). Al llegar: escribir una nota de relevo (qué se hizo, qué falta, archivos) en el informe o la memoria y seguir en una sesión nueva.
- **Aviso automático de contexto**: un hook (`.claude/herramientas/aviso_contexto.py`, en `.claude/settings.json`) avisa una vez al pasar ~150 mil tokens (tope de las livianas; las pesadas siguen) y otra a los 250 mil (tope de todas); no corta nada: termina el paso en curso, deja la nota de relevo y sigue en sesión nueva.
- **Salidas largas a archivo**: registros de pruebas, 3D, mediciones y builds se guardan en el scratchpad y se muestra solo el resumen (`> log.txt; tail -15 log.txt`).
- **Repartir trabajo entre sesiones**: cada ronda o tarea nueva va en una sesión NUEVA con relevo corto (memoria y archivos), no en una sesión larga; SendMessage solo para aclaraciones de una o dos líneas. Al abrir sesión o agente, indicar siempre `model` según la tabla de abajo. Antes de mandar trabajo a una sesión existente, mirar su tamaño: si pasa de su tope (150 mil liviana, 250 mil pesada), abrir otra.
- **Skills cortas**: el SKILL.md se carga entero en cada sesión que lo usa; dejar en él solo el flujo y las reglas, y mandar trampas, historiales y detalles a archivos aparte que se lean cuando haga falta.
- **Encargos a otras sesiones cortos**: apuntar a archivos e informes en vez de pegar contexto.
- Ejecutar sin narrar opciones descartadas; respuestas finales breves.

### Modelo según la tarea (no matar moscas a cañonazos)
| Modelo | Para qué |
|---|---|
| `haiku` | buscar en el código, bajar fotos o fuentes, correr pruebas e informar, auditorías con lista, consultas de estado, cambios mecánicos |
| `sonnet` (por defecto) | vistas y plantillas Django, CSS y arreglos UX acotados, fallas frecuentes, seguridad, medir velocidad, informes, coordinación |
| `opus` | 3D, láminas del despiece, funciones nuevas que piden diseño, errores difíciles |
| `fable` | respaldo para 3D o láminas cuando opus no alcance (cupo semanal propio) |

**Esfuerzo** (cuánto piensa antes de actuar; se elige con el modelo):
| Esfuerzo | Cuándo | Ejemplos |
|---|---|---|
| `low` | el resultado se sabe de antemano y es fácil de comprobar; un error no rompe nada | buscar, bajar archivos, correr pruebas, renombrar, mover textos, consultas de estado |
| `medium` (por defecto) | trabajo conocido con pocas decisiones, dentro de un patrón que ya existe | plantilla o vista nueva igual a otras, arreglo de CSS o UX, fallas de una moto, informes |
| `high` | varias piezas que encajan, decisiones de diseño o errores sin causa clara | función nueva, depurar, seguridad, optimizar velocidad, revisión mecánica |
| `xhigh` / `max` | solo cuando `high` ya falló o el resultado debe ser fiel a una referencia exigente | 3D con IoU exigente, láminas fieles al plano, migraciones delicadas de datos |

Regla rápida: si cabe en una frase y se verifica en un comando, `low`; si hay que decidir entre opciones, `high`. Subir un nivel solo después de un intento fallido, no por si acaso. **Sesiones `opus`: siempre `medium`** (decisión del usuario, 19-nov: rinde bien); `high` solo si `medium` ya falló en esa tarea. Medir el consumo: `python -I .claude/herramientas/uso_tokens.py` (semana actual contra la línea base).

## Coordinación
Puede haber varias sesiones a la vez en esta carpeta: no editar archivos que otra sesión está tocando (portada/entrar = sesión "Proyecto tallerYa"; dibujos del despiece = sesión de dibujos) sin avisar. No hacer commit sin que el usuario lo pida. Si una sesión deja relevo con pendientes, el coordinador lanza enseguida la que continúa (mismo modelo y esfuerzo), sin esperar a que se lo pidan.
