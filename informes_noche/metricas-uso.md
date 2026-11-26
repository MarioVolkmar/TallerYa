# Métricas de uso de TallerYa (rama `claude/metricas-uso-a4d267`)

Medición propia en Django (app `metricas`), sin Google Analytics ni servicios externos, con un panel en
`/consola/?seccion=metricas`. Captura: `informes_noche/metricas-uso-panel.jpg` (datos de prueba).

## Qué se mide
- **Páginas vistas** por nombre de ruta de Django (`garaje:moto`, no `/garaje/12/`), con **dispositivo**
  (celular, tableta o escritorio, según el navegador) y **referente agrupado** (directo, Google, otros buscadores,
  WhatsApp, redes, otros sitios; también lee `?utm_source=whatsapp`). Nunca se guarda la URL de origen.
- **Funciones clave** con `registrar_evento(request, "nombre", **datos)` (una línea en cada vista):

  | Evento | Dónde |
  |---|---|
  | `registro` (correo/Google, motero/taller) | `cuentas.registro`, `_registro_taller`, `google_volver` |
  | `inicio_sesion` (correo/Google) | señal `user_logged_in` (dentro de la app; no se cuenta si fue el registro) |
  | `moto_creada`, `plan_visto`, `despiece_abierto` | `garaje.agregar`, `garaje.detalle`, `garaje.despiece_json` |
  | `pieza_vista`, `visor_3d` | navegador: `despiece.js` y `moto3d-carga.js` → `POST /metricas/evento/` (con CSRF) |
  | `busqueda_talleres` (término normalizado) | `talleres.directorio` |
  | `taller_visto`, `contacto` (WhatsApp/llamada) | `talleres.detalle`, `talleres.ir` |
  | `cupon_obtenido`, `cupon_canjeado` | `cupones.obtener`, `cupones.canjear_cupon` |
  | `foro_pregunta`, `foro_respuesta` | `foro.preguntar`, `foro.publicar_respuesta` |
  | `emergencias` (qué necesita) | `talleres.emergencias` |
  | `plus_solicitado`, `plus_activado` | `cuentas.solicitar_plus`; señal al pasar una suscripción a ACTIVA |

  `visor_3d` se cuenta cuando el 3D de la ficha de la moto llega a la pantalla y empieza a cargar (no en la portada).
- **Usuarios activos** (con cuenta): diarios, 7 y 30 días, y **retención semanal por cohorte de registro**.
- **Embudos**: visitantes → registro → moto creada → plan visto; taller visto → contacto → cupón canjeado.

## Qué NO se mide (privacidad, Ley 1581)
- Sin cookies nuevas ni scripts de terceros (la CSP sigue igual).
- **No se guardan IPs.** El anónimo es `sha256(sal del día + IP + navegador)[:16]`. La sal es aleatoria, vive en
  la base y **se borra al empezar el día siguiente**: ni nosotros podemos unir visitas de días distintos. Por eso,
  sin sesión, «visitantes» es una suma de visitantes por día y los activos semanales y mensuales son solo de cuentas.
- Con sesión se usa el id interno (`u<id>`), nunca el correo ni el nombre.
- Se respeta **DNT y Sec-GPC** (servidor y JS): no se registra nada.
- `registrar_evento` descarta claves personales (correo, celular, nombre, placa, documento…) y limita los valores
  a 60 caracteres. Los términos de búsqueda con 5 o más dígitos seguidos, `@` o enlaces se descartan.
- **No se cuenta**: estáticos, `/media/`, admin, consola, el panel, `/tareas/`, respuestas que no sean HTML 200,
  fetch/AJAX, precargas del navegador, bots conocidos (también las vistas previas de WhatsApp), ni al equipo
  administrador (`is_staff`; `METRICAS_EXCLUIR_STAFF=False` lo cambia).
- Eventos crudos: **90 días**. Después quedan solo los conteos diarios (`ResumenDiario`) y la tabla
  `ActividadSemanal` (id interno y semana) que necesita la retención.
- Agregué una viñeta en la política de privacidad (`templates/legal/privacidad.html`, sección 2).

## Cómo verlo
- Consola › **Métricas** (solo administradores; mismo `solo_admin` de la consola). Períodos de 7, 30 y 90 días.
  Muestra tarjetas, gráfico SVG por día (hecho en el servidor, sin librerías ni CDN), páginas y funciones más y
  menos usadas («candidatas a sobrar»: incluye las páginas vistas en el último año que no tuvieron visitas en el
  período y las funciones con 0 usos), embudos, dispositivos, referentes, términos buscados y retención. Botón **CSV**
  (`/metricas/exportar.csv?periodo=30`, con los resúmenes por día). Probado en celular (375 px) sin desplazamiento
  horizontal.
- Los días cerrados se resumen solos al abrir el panel; el día de hoy se calcula al vuelo.
- `manage.py agregar_metricas` resume y borra lo crudo de más de 90 días (`--dias N`). En `render.yaml` quedó
  documentado como cron **comentado** (también puede ir en el GitHub Actions de `/tareas/`, que es gratis).
- Para probar en local: base temporal migrada con `cargar_demo`, 244 eventos reales (cliente de pruebas) y 45 días
  sintéticos; servidor en el puerto 8017 (el 8013 lo usaba otra sesión). Nada de eso quedó en el repo ni tocó
  `C:\dev\TallerYa\db.sqlite3`.

## Costo en velocidad
- Una sola `INSERT` por página HTML medida (la sal se guarda en memoria del proceso; el hash cuesta 0,01 ms).
- Medido: `nucleo.guardar` = **2,2 ms** en SQLite en disco (casi todo es el fsync del commit) y **< 1 ms** en
  memoria. `/talleres/` completa: 26,2 ms → 30,2 ms (≈4 ms con ruido, SQLite local). En PostgreSQL de Render se
  espera ≈1 ms. La prueba `test_middleware_cuesta_pocos_ms` falla si pasa de 5 ms.
- El panel hace las consultas pesadas, pero solo cuando lo abre un administrador.
- Si algún día el tráfico lo pide: juntar los eventos en memoria y escribirlos en lote cada N segundos.

## Reversión
- Apagar sin desplegar: `METRICAS_ACTIVAS=0` (pruebas: apagada por defecto; se enciende con `override_settings`).
- Quitar del todo, fuera de `metricas/`: 3 líneas en `config/settings.py` (app, middleware, bandera), 1 en
  `config/urls.py`, 1 en `consola/secciones.py`, las llamadas `registrar_evento` (1 línea cada una y su import) en
  `cuentas`, `garaje`, `talleres`, `cupones` y `foro`, 1 línea `tyM.push` en `despiece.js` (2 sitios) y en
  `moto3d-carga.js`, el `<script metricas.js>` en `moto.html` y `diagnostico.html`, la viñeta de la política y el
  comentario de `render.yaml`. Luego `migrate metricas zero` antes de borrar la app.

## Pruebas
- `manage.py test metricas` (17): registra la vista, referentes, no hay IP en claro y el hash cambia con el día,
  DNT/GPC, exclusión de estáticos/bots/admin/consola/404, staff, id interno con sesión, bandera apagada, datos
  personales descartados, término de búsqueda, endpoint con CSRF y lista blanca, registro sin inicio de sesión doble,
  inicio de sesión con correo, costo en ms, agregación y purga a 90 días (idempotente), solo el admin ve panel y CSV.
- Suite completa: **656 pruebas OK** (26 s).

## Sugerido a futuro
- **Panel Plus del taller**: ya existe `talleres.estadisticas` (`EventoDiario`: visitas, WhatsApp y llamadas por
  taller). Se puede sumar lo de `metricas` filtrado por `datos.taller` (búsquedas que lo muestran, cupones obtenidos
  y canjeados, embudo propio visita → contacto → canje) como argumento de venta del Plus para talleres.
- **Alertas**: un correo semanal al fundador (con el mismo comando del cron) con la variación de registros, contactos
  y retención, y aviso si una función cae a 0 o si las páginas vistas bajan más de un 50 % (posible caída del sitio).
- Medir el tiempo de carga real en el navegador (`PerformanceNavigationTiming`) con el mismo endpoint, agregado por
  página.
- Panel de «tracción» para Ruta N / Capital Semilla: PDF de una página con MAU, crecimiento semanal y retención S4.

## 25-nov: resumen «Por semana» (rama `piloto`, sin commit)
**La rama `claude/metricas-uso-a4d267` ya estaba unida** desde el 18-nov (commit 276baa4): está en `piloto` y en
`main`, y `C:\dev\TallerYa-produccion` tiene los archivos de `metricas/`. No hubo cherry-pick ni migraciones nuevas.
Faltaba ver las cifras por semana; se agregó arriba de Consola › Métricas:

- Tabla de 6 semanas (lunes a domingo, la actual primero), sin depender del período: visitas por sección, usuarios
  nuevos por rol (motero, domiciliario, taller, mecánico, sin terminar), garaje, foro, cupones y trámites.
- Visitas, planes, despieces y 3D salen de la medición (cuentan desde el 18-nov o desde que esté encendida); lo demás
  se cuenta en la base y trae historia. No cuenta al equipo administrador (las fichas de diagnóstico anónimas sí se
  cuentan todas). Los datos de demostración cargados en la base también cuentan.
- «Proveedores» no aparece en usuarios nuevos: no tienen cuenta. «SOAT pagados» hoy es pago simulado.
- Solo conteos: no se guarda ningún dato nuevo. 14 consultas.
- Archivos: `metricas/semanas.py` (nuevo), `metricas/panel.py`, `metricas/templates/metricas/panel.html`,
  `metricas/static/metricas/panel.css`, `metricas/tests.py`.

### Verificación
- `manage.py test metricas`: 20 OK. Suite rápida: 1088 OK.
- `revisar-ux` **sobre una página de muestra** (cabecera y tabla reales, cifras inventadas), no sobre la consola:
  entrar como administrador dio 403 y se detuvo (una consulta para diagnosticarlo fue denegada por el modo
  automático). A 1280 y 375 px: sin scroll horizontal; en celular la tabla se desplaza de lado con el nombre fijo
  (el «desborde» del script es esa tabla dentro de su caja). Previo, sin tocar: botones de período de 42 px de alto
  y radio 9 px.
- Pendiente: mirarla en la consola real; anotar en `anexo-guia.md` la tabla con primera columna fija (otra sesión
  tiene ese archivo sin commit). Quedó en la base local una sesión de administrador creada con
  `revisar-ux/entrar.py` (la cookie del navegador se borró).
