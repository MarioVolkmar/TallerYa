# TallerYa — guía para agentes

Django (Python) para talleres de motos en Medellín. Todo en español (código, UI, commits).

## Mapa (no hace falta explorar)
- `config/` settings y urls · `templates/base.html` · CSS: `talleres/static/talleres/css/tallerya.css`
- Tailwind va compilado en `talleres/static/talleres/css/tw.css` (no hay CDN): tras usar clases de Tailwind nuevas, correr `npm run css` (config en `tailwind/`)
- Apps: `talleres` (directorio, portada), `cuentas` (login, Google, roles, Plus), `cupones`, `foro`, `notificaciones`, `garaje` (motos, plan de mantenimiento, 3D, despiece)
- Despiece: `garaje/diagramas.py` (dibujos SVG propios), `despiece_fichas.py`, `despiece_glosario.py`, `despiece_mapas/*.json`, `static/garaje/js/despiece.js`; importador `manage.py importar_despiece`
- 3D: `garaje/static/garaje/js/moto3d.js` (2200 líneas: leer por rangos)
- Python: `venv/Scripts/python.exe` · servidor: preview `tallerya` (puerto 8001)
- Solo local, nunca al repo ni a servicios externos: `despiece_local/`, `manual_despiece/`, `planos_a_generar/`, `media/`, `privado/`, `db.sqlite3`

## Pruebas
Al correr `manage.py test` ya son rápidas por defecto: hash MD5 de contraseñas y paralelo (hasta 6 procesos, `config/test_runner.py`; `--parallel 1` lo apaga). Comandos (todos con `venv/Scripts/python.exe`):
- **Rápida** (diaria / antes de commit): `manage.py test --exclude-tag=lenta -v 1` (~30 s, 485 pruebas). Si solo cambió CSS/JS/plantillas/texto, ninguna.
- **Completa** (antes de desplegar, o si cambian modelos/migraciones, `config/`, `templates/base.html` o código compartido): `manage.py test -v 1` (~30-45 s, 526 pruebas, incluye las `@tag("lenta")`: despiece y diagnóstico).
- **Focalizada**: `manage.py test garaje.tests.Clase -v 1`.
- Tiempos por prueba: `TEST_TIMING=archivo.json manage.py test --parallel 1`. `--keepdb` casi no ayuda (la base de pruebas SQLite es en memoria).
- Pruebas nuevas: usar `tempfile.mkdtemp()` para archivos (seguro en paralelo) y `@tag("lenta")` si pasan de ~2 s.

## Trabajar gastando pocos tokens (misma calidad)
Cada resultado de herramienta se queda en el contexto y se vuelve a pagar en cada turno siguiente.
- **Leer poco**: Grep antes que Read; Read con `offset`/`limit` en archivos grandes; no releer un archivo ya leído ni tras editarlo.
- **Salida corta**: limitar comandos (`| tail -20`, `| head -40`, `grep -c`, `-q`); pruebas con `-v 1`; nunca volcar JSON/SVG/HTML enteros, mostrar solo la parte relevante.
- **Imágenes = lo más caro** (~1.500 tokens c/u): para verificar texto o estructura usar `read_page`/`get_page_text`/`javascript_tool`, no capturas. Si hace falta ver: captura con `scale: 0.5` o `zoom` a la región; renders PNG de dibujos a ≤900 px de ancho o recortados a la zona cambiada. Una captura final como prueba, no una por iteración.
- **Navegador**: no repetir `resize_window`; agrupar pasos en `browser_batch` sin capturas intermedias.
- **Scripts repetidos**: si un script de verificación se usa más de 2 veces, guardarlo en el scratchpad y reutilizarlo en vez de reescribir heredocs.
- **Búsqueda amplia**: delegar a un subagente `Explore` (modelo `haiku`) y recibir solo la conclusión.
- **Sesiones cortas y enfocadas**: una tarea por sesión; al cambiar de tema, sesión nueva. Lo que deba persistir va a la memoria, no al historial.
- Ejecutar sin narrar opciones descartadas; respuestas finales breves.

## Coordinación
Puede haber varias sesiones a la vez en esta carpeta: no editar archivos que otra sesión está tocando (portada/entrar = sesión "Proyecto tallerYa"; dibujos del despiece = sesión de dibujos) sin avisar. No hacer commit sin que el usuario lo pida.
