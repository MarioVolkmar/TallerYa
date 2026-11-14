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
- Focalizadas: `venv/Scripts/python.exe manage.py test garaje.tests.Clase -v 1`. Solo CSS/texto: ninguna.
- Antes de un commit: solo las apps tocadas (`git status` → `manage.py test garaje cuentas -v 1`); si solo cambió CSS/JS/plantillas/texto, ninguna.
- Suite completa (134 pruebas, ~2 min) solo si el cambio toca modelos/migraciones, `config/` (settings, urls), `templates/base.html` o código compartido entre apps, o antes de desplegar en Render.

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
