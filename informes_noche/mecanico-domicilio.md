# Mecánicos a domicilio — informe (18-nov-2026)

Sección nueva para promocionar mecánicos **sin taller propio** que van a donde está la moto. Todo en local, **sin commit**.
Suite completa en verde: `manage.py test -v 1` → **661 pruebas OK** (23 nuevas en `domicilio/tests.py`).

## Qué quedó hecho

| Parte | Dónde |
|---|---|
| App nueva `domicilio`: `MecanicoDomicilio`, `Zona`, `TipoServicio`, `ResenaMecanico` + migraciones 0001 y 0002 (siembra 17 zonas de Medellín, 9 municipios y 12 servicios) | `domicilio/models.py`, `domicilio/migrations/` |
| Registro (crea cuenta si no hay sesión) y edición del propio perfil | `/mecanicos/registro/`, `/mecanicos/mi-perfil/` |
| Listado público con búsqueda, filtro por zona, servicio, «atiende urgencias» y «solo verificados»; orden: verificados, nota, nº de reseñas | `/mecanicos/` |
| Ficha con WhatsApp (wa.me con mensaje), llamar, zonas, tarifa, reseñas con reparto de estrellas | `/mecanicos/<slug>/` |
| Aviso visible «TallerYa solo los promociona: acuerdo, pago y garantía entre tú y el mecánico» (listado, ficha y registro) | `domicilio/templates/domicilio/_aviso.html` |
| Moderación: estado pendiente / aprobado / suspendido + «verificado». Admin de Django (acciones Aprobar, Suspender, Volver a pendiente; avisa al mecánico) y sección **Mecánicos a domicilio** en `/consola/` (con contador de pendientes y bitácora) | `domicilio/admin.py`, `domicilio/consola.py`, `domicilio/estados.py` |
| Rol nuevo `mecanico` («Mecánico a domicilio») en `cuentas/roles.py`; `/cuenta/` lo lleva a su perfil; la consola de usuarios ya lo nombra bien | `cuentas/roles.py`, `cuentas/views.py`, `consola/vistas/usuarios.py` |
| Navegación: «A domicilio» en el menú de escritorio y «Mecánicos a domicilio» en el menú del celular | `templates/base.html` |
| Portada: un chip discreto «🛵 Mecánico a domicilio» al final de «Lo más buscado» | `talleres/templates/talleres/inicio.html` (1 línea) |
| Crear cuenta: una línea «¿Eres mecánico y no tienes taller? Regístrate…» | `cuentas/templates/cuentas/registro_elegir.html` (1 línea) |
| Demo: 6 mecánicos ficticios (nombres con «(demo)», celulares 573000000101–106; 5 aprobados y 1 pendiente) y 3 reseñas firmadas por la cuenta demo del garaje si existe. Entra en `cargar_demo` (CARGAR_DEMO=1) y en `manage.py cargar_demo_domicilio` | `domicilio/demo.py` |
| SEO: listado y fichas indexables y en `sitemap.xml`; registro y mi-perfil con noindex; ficha no publicada con noindex | `talleres/seo.py` |

## Para probar

- `http://localhost:8001/mecanicos/` (ya cargué los 6 de demo en tu `db.sqlite3` local; para repetir: `venv/Scripts/python.exe manage.py cargar_demo_domicilio`).
- Ficha: `http://localhost:8001/mecanicos/wilson-arango-demo/`. El pendiente (`mauricio-henao-demo`) da 404 a un anónimo.
- Registro: `http://localhost:8001/mecanicos/registro/` (sin sesión pide correo y contraseña; con sesión de motero solo el perfil).
- Moderar: `http://localhost:8001/consola/?seccion=mecanicos` o `/admin/domicilio/mecanicodomicilio/`.
- Lo verifiqué en el navegador: listado, filtros, ficha, 404 del pendiente, registro con cuenta nueva, edición y redirección de `/cuenta/`. La cuenta de prueba que creé para eso la borré después.

## Decisiones (y por qué)

1. **App aparte, no dentro de `talleres`**: el taller tiene dirección, mapa, agenda, citas, PIN y cupones; el mecánico no tiene nada de eso. Solo se reutilizan `Marca`, el normalizador de celular, el formulario de cuenta (`CuentaTallerForm`), la validación de fotos y las clases CSS del directorio (`.dir-*`, `.tc-*`).
2. **Zonas como tabla propia** (comunas de Medellín + municipios), no los barrios de `talleres`: un mecánico atiende zonas amplias, y los barrios están pensados para direcciones. Editables desde el admin.
3. **Servicios como lista propia**: los de taller («Kit de arrastre», «Revisión técnico-mecánica»…) no encajan todos a domicilio; agregué «Batería y arranque», «Llantas y despinche» y «Revisión antes de comprar moto usada».
4. **Reseñas solo con cuenta** (en talleres también se aceptan anónimas): sin taller físico es más fácil inflar perfiles. Una reseña por cuenta y mecánico (si vuelve a calificar, se actualiza); nadie se califica a sí mismo; solo perfiles publicados; límite 3/hora por mecánico y 10/día por cuenta. Sin respuesta del mecánico a las reseñas por ahora.
5. **Editar un perfil aprobado no lo vuelve a pendiente**: más simple para el mecánico. El riesgo (cambiar nombre o foto tras aprobado) se cubre con «Suspender». Si prefieres re-moderar, es una línea en `views.mi_perfil`.
6. **Una cuenta de taller no puede ser también mecánico** (se le pide usar otra cuenta); un **motero sí** puede tener perfil de mecánico: conserva el rol motero y edita su perfil en `/mecanicos/mi-perfil/` (enlace en el listado).
7. **WhatsApp directo a wa.me** (sin la redirección con estadísticas que usan los talleres): no hay panel de estadísticas para mecánicos todavía.

## Seguridad

- Sin IDOR: la edición es `/mecanicos/mi-perfil/` sin id; el perfil se busca por `request.user`. Estado y «verificado» no están en el formulario (probado que mandarlos no hace nada). Acciones de consola con `solo_admin` + POST + bitácora (probado 403 a no-staff).
- CSRF en todos los formularios (probado 403 sin token). Registro con el mismo freno por IP que `/cuenta/registro/` (20/hora).
- Foto: firma real + Pillow (`talleres/subidas.tipo_real`), máx. 5 MB, se vuelve a codificar como JPEG 480×480 sin EXIF y nombre aleatorio `domicilio/<uuid>.jpg` (probado que un HTML disfrazado de .jpg se rechaza).
- CSP sin cambios (no hay dominios nuevos; wa.me es navegación). Sin `|safe` ni `innerHTML`.
- `revisar.py --sin-red`: ninguna FALLA ni AVISO de lo nuevo (solo los avisos de siempre: `unsafe-inline`, HSTS corto, estáticos pesados). Agregué `mecanicos/` y `mecanicos/registro/` a `PUBLICAS` en `config/tests_seguridad.py` (el barrido anónimo lo pide a propósito).
- Velocidad: el listado hace el mismo número de consultas con 4 o 12 mecánicos (prueba `VelocidadTests`).

## Pendiente / para decidir

- **¿Cobrar o destacar como Plus?** Sugerencia: gratis al inicio para llenar el listado; luego «Destacado» pago (sale primero, insignia) como `Taller.destacado`. Falta el campo `destacado` (no lo agregué para no adelantar la decisión).
- **Verificación**: definir qué revisa el equipo antes de marcar «verificado» (cédula, referencias, fotos de trabajos).
- **Consola de usuarios**: muestra el rol «Mecánico a domicilio», pero el filtro por rol aún no tiene esa opción (siguen saliendo en «Registro incompleto» al filtrar) y no se puede asignar ese rol desde ahí.
- Posibles mejoras: respuesta del mecánico a reseñas, fotos de trabajos, botón «¿Te varaste?» que también sugiera mecánicos con urgencias, estadísticas de clics a WhatsApp.
- **Coordinación**: los cambios en `inicio.html` y `registro_elegir.html` son de una línea cada uno (otra sesión toca portada/entrar).
- `npm run css` corrido (tw.css creció ~120 bytes).

## Archivos tocados

Nuevos: `domicilio/` completo (`__init__.py`, `apps.py`, `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `consola.py`,
`estados.py`, `demo.py`, `tests.py`, `migrations/0001_initial.py`, `migrations/0002_zonas_y_servicios.py`,
`management/commands/cargar_demo_domicilio.py`, `static/domicilio/css/domicilio.css`, `templates/domicilio/{listado,ficha,registro,mi_perfil,consola_mecanicos,_tarjeta,_aviso,_campos}.html`),
`informes_noche/mecanico-domicilio.md`, `informes_noche/mecanico-domicilio-celular.jpg`.

Modificados: `config/settings.py` (INSTALLED_APPS), `config/urls.py`, `config/tests_seguridad.py` (PUBLICAS), `cuentas/roles.py`,
`cuentas/views.py` (mi_cuenta), `cuentas/templates/cuentas/registro_elegir.html`, `consola/secciones.py`, `consola/vistas/usuarios.py`,
`templates/base.html`, `talleres/templates/talleres/inicio.html`, `talleres/management/commands/cargar_demo.py`, `talleres/seo.py`,
`talleres/static/talleres/css/tw.css`.
