# Preparar el despliegue en Render (sin desplegar) — 15 nov. 2026

**Archivos revisados:** `render.yaml`, `build.sh`, `config/settings.py`, `config/urls.py`, `.env.example`, `.github/workflows/avisos.yml` y `despiece.yml`, `requirements.txt` y `.gitignore`.

**Lo que ya está bien hecho:**
- WhiteNoise con `CompressedManifestStaticFilesStorage` cuando `DEBUG=0`.
- `collectstatic`, `migrate` y `createcachetable` en el build. `build.sh` es ejecutable en git.
- `tw.css` compilado y en el repositorio.
- Postgres por `DATABASE_URL`, y `SECRET_KEY` obligatoria con `DEBUG=0`.
- `ALLOWED_HOSTS` y CSRF se llenan solos con `RENDER_EXTERNAL_HOSTNAME`.
- Cookies seguras, HSTS y redirección a HTTPS con `DEBUG=0`. `PROXIES_DE_CONFIANZA=1` en Render.
- La caché del despiece va en la base, así que sobrevive a reinicios.
- Cron gratis por GitHub Actions con reintentos para despertar el servicio.
- Documentos personales (`privado/`) fuera de `/media/`.

**Único cambio hecho:** se completó `.env.example` con todas las variables que lee `settings.py` y faltaban: producción, Plus, contacto, legal, WhatsApp y otras. Van **comentadas**, así que en local no cambia nada. `render.yaml` no se tocó: lo que sugiero cambiar ahí va abajo.

> Los precios son aproximados, de la tabla pública de Render y los proveedores; confírmalos antes de pagar.

## Prioridad 1 — sin esto no se puede abrir a usuarios reales

| # | Qué falta | Detalle | Costo aprox. |
|---|---|---|---|
| 1 | **Planes de pago en `render.yaml`** | Hoy dice `plan: free` en la web y en la base. La base **gratis de Render se borra a los 30 días** y la web gratis se duerme a los 15 minutos (el primer usuario espera unos 50 s). Cambiar a `plan: starter` (web) y a un plan pago de Postgres (Basic-256MB). | Web Starter ≈ 7 USD/mes. Postgres Basic ≈ 6–7 USD/mes. |
| 2 | **Archivos subidos (media y privado)** | `STORAGES.default` es el disco local y **en Render se borra en cada despliegue**. Afecta fotos de talleres, avatares, imágenes de láminas y PDF de SOAT y técnico-mecánica. Lo más simple, porque no toca código: un **disco persistente** montado en `/var/data`, con `DJANGO_MEDIA_ROOT=/var/data/media` y `DJANGO_PRIVADO_ROOT=/var/data/privado`. Los dos ya están en settings. Contra: con disco no hay despliegue sin cortes ni más de una instancia. La alternativa es Cloudflare R2 o S3 con `django-storages`: requiere código, y `privado/` tendría que ir a un bucket privado con URLs firmadas. | Disco ≈ 0,25 USD por GB al mes (1–5 GB bastan para empezar). R2: gratis hasta 10 GB. |
| 3 | **Apagar los datos demo** | En `render.yaml` está `CARGAR_DEMO: "1"`. `cargar_demo` crea talleres y reseñas ficticias y la **cuenta demo con su clave escrita en el repositorio** (`DEMO_CLAVE`), así que cualquiera podría entrar con ella. Para el lanzamiento: `CARGAR_DEMO=0`. Si ya se cargó, borrar esos datos. | — |
| 4 | **`SITIO_URL`** | No está en `render.yaml`. Sin ella, los enlaces de los correos que mandan las tareas programadas (avisos, citas) quedan sin dominio. Agregarla con `sync: false` (`https://tallerya.onrender.com` o el dominio propio). | — |
| 5 | **Correo (SMTP)** | Sin `EMAIL_HOST` los correos salen por la consola, así que en producción **no llegan** la recuperación de contraseña, la verificación ni los avisos. Faltan en `render.yaml`: `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` (con `sync: false`). Proveedor: Brevo, Resend o Amazon SES. Configurar SPF y DKIM en el dominio para no caer en spam. | Brevo: gratis hasta unos 300/día. SES: unos 0,10 USD por cada 1.000. |
| 6 | **Secretos de GitHub para el cron** | `avisos.yml` y `despiece.yml` necesitan `TALLERYA_URL` y `TAREAS_TOKEN` en GitHub › Settings › Secrets. El mismo token va en Render, con al menos 20 caracteres. Sin ellos no salen los avisos de SOAT, técnico-mecánica ni pico y placa, los recordatorios de citas ni las insignias. Probar con «Run workflow». | Gratis. |
| 7 | **Datos del despiece en producción** | Las láminas y tablas de partes se importan en local (`importar_despiece`, que lee `despiece_local/`) y viven en la **base local y en `media/`**. Producción arranca sin ellas. Falta decidir cómo llevarlas: por ejemplo, `dumpdata` de las tablas del despiece más una copia de las imágenes al disco o bucket. **Cuidado legal:** las imágenes sacadas de catálogos de fábrica son de terceros (Yamaha y otros) y no deben publicarse; solo los dibujos propios (`diagramas.py`). Decisión del usuario. | — |

## Prioridad 2 — antes de promocionar el sitio

| # | Qué falta | Detalle | Costo aprox. |
|---|---|---|---|
| 8 | **Google OAuth** | Faltan `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en Render (sin ellos el botón no aparece, no falla). En Google Cloud: agregar la URI `https://<dominio>/cuenta/google/volver/` y publicar la pantalla de consentimiento, con política de privacidad (`/legal/…`). | Gratis. |
| 9 | **Dominio propio** | Si se usa `tallerya.co` u otro: `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS` (las dos con el dominio), `SITIO_URL`, la URI de Google y SPF/DKIM del correo. Cuando esté estable, subir `DJANGO_HSTS_SECONDS` a 31536000. | Dominio .co ≈ 25–40 USD/año. |
| 10 | **Datos legales y de contacto** | `LEGAL_NIT`, `LEGAL_CORREO` y `LEGAL_RAZON_SOCIAL` están vacíos, así que las páginas de términos y de tratamiento de datos (Ley 1581) salen incompletas. También faltan `CONTACTO_*` para el pie de página. | — |
| 11 | **Plus: Nequi y WhatsApp reales** | `TALLERYA_WHATSAPP` y `PLUS_NEQUI` traen valores de ejemplo (`573000000000`, `300 000 0000`). En `render.yaml` ya se piden (`sync: false`), pero hay que llenarlos. | — |
| 12 | **WhatsApp Cloud API** | `WHATSAPP_BACKEND=consola`: hoy los recordatorios solo se escriben en el log. Para activarlos: app en Meta Business verificada, número propio, `WHATSAPP_TOKEN` permanente, `WHATSAPP_PHONE_ID` y **3 plantillas aprobadas** (`recordatorio_pico_placa`, `cita_reprogramada`, `cita_cancelada`). La verificación del negocio tarda días. | Cobro por mensaje de plantilla «utilidad»: centavos de dólar por mensaje en Colombia (ver la tabla de Meta). |
| 13 | **Timeout de gunicorn** | `startCommand: gunicorn config.wsgi:application` usa el límite por defecto de 30 s. El precalentado del despiece (`/tareas/despiece/`) y la portada en frío pueden acercarse a eso. Sugerencia: `gunicorn config.wsgi:application --timeout 60`. | — |

## Prioridad 3 — mejoras y cosas que vigilar

| # | Qué | Detalle | Costo aprox. |
|---|---|---|---|
| 14 | Caché compartida (Redis) | Sin `REDIS_URL`, cada proceso de gunicorn (`WEB_CONCURRENCY=2`) tiene su propia caché en memoria. Los límites de intentos de login y los contadores valen «por proceso», o sea que se puede intentar el doble. Aceptable al comenzar; con tráfico, Render Key Value. | Plan gratis (25 MB, sin persistencia) o Starter ≈ 10 USD/mes. |
| 15 | Noticias en segundo plano | `NOTICIAS_AUTO` lanza un hilo **por proceso**, así que con 2 procesos las noticias se descargan dos veces. Inofensivo. Si molesta, `NOTICIAS_AUTO=0` y llevarlo al cron. | — |
| 16 | `/media/` servido por Django | `config/urls.py:22` sirve `/media/` con `django.views.static.serve` siempre, también en producción. Con el disco persistente funciona, pero es lento con muchas fotos. Con R2 o S3 esa línea sobra. | — |
| 17 | Caché de dibujos SVG | `despiece_svg` usa la carpeta temporal y se borra en cada despliegue. Es intencional: es barata de rehacer. | — |
| 18 | Copias de seguridad | Los Postgres pagos de Render tienen recuperación a un punto en el tiempo. El disco persistente tiene instantáneas diarias. Revisar la retención. | Incluido. |
| 19 | Health check | `healthCheckPath: /` arma la portada completa en cada chequeo. Una ruta ligera (`/salud/`) sería mejor, pero requiere vista (lo dejo anotado; la sesión de seguridad trabaja vistas). | — |
| 20 | Superusuario | `DJANGO_SUPERUSER_*` en el primer despliegue. Después conviene borrar `DJANGO_SUPERUSER_PASSWORD` del panel. | — |

## Qué no debe subirse (ya está en `.gitignore`, verificado)
`db.sqlite3`, `.env`, `media/`, `privado/`, `staticfiles/`, `despiece_local/`, `manual_despiece/`, `planos_a_generar/`, `node_modules/`, `venv/`.

**Pendiente de decidir:** `informes_noche/` está sin seguimiento. Tiene informes internos y capturas (`relevos/*.jpg`). O se agrega a `.gitignore` o se sube a propósito; no se cambió.

## Costo mensual estimado (mínimo serio)
| Concepto | USD/mes |
|---|---|
| Web Starter | ≈ 7 |
| Postgres Basic-256MB | ≈ 6–7 |
| Disco persistente de 2 GB | ≈ 0,5 |
| Correo (Brevo gratis) | 0 |
| Cron (GitHub Actions) | 0 |
| **Total** | **≈ 14–15 USD/mes**, más el dominio (unos 3 USD/mes) y WhatsApp por uso. |

Coincide con lo ya conversado: unos 15–20 USD al mes.

## Orden sugerido el día del despliegue
1. Cambiar en `render.yaml` los planes, `CARGAR_DEMO=0`, el disco y `SITIO_URL`, más el correo y Google con `sync: false`.
2. Crear el Blueprint y llenar los secretos.
3. Esperar el build y entrar con el superusuario.
4. Cargar los datos del despiece que sí se puedan publicar.
5. Poner los secretos en GitHub y correr «Tareas diarias» a mano.
6. Probar la recuperación de contraseña (correo), el ingreso con Google y la subida de un SOAT; luego redesplegar y comprobar que el archivo sigue ahí.
