# TallerYa

Plataforma web para motociclistas y talleres de motos del Valle de Aburrá (Medellín). El motociclista lleva su moto al día (plan de mantenimiento, SOAT, técnico-mecánica, pico y placa) y encuentra un taller de confianza. El taller recibe citas, reseñas y clientes que llegan con cupones.

Hecho en Django 5.2 (Python), con Tailwind compilado y Three.js para el modelo 3D. Todo el código, la interfaz y los commits están en español.

## Apps

| App | Qué hace |
| --- | --- |
| `talleres` | Portada y directorio: buscar por texto, barrio, servicio, marca y rango de precio; perfil del taller con fotos, horario, WhatsApp y reseñas; citas (pedir, reprogramar, cancelar); favoritos; panel del taller. Los talleres nuevos quedan inactivos hasta aprobarlos en el admin. |
| `cuentas` | Registro e ingreso con correo o con Google, verificación de correo, recuperación de contraseña, roles (motociclista, taller, admin), avatares y aceptación de términos. También TallerYa Plus: suscripción mensual que se paga por Nequi y se activa en el admin. |
| `cupones` | Cupones para un taller o para todos, con vencimiento y cupo. El motociclista obtiene un código único (`TY-XXXXXX`). El taller lo canjea en `/canjear/` con su PIN de 6 dígitos, y los intentos fallidos se bloquean un rato. Referidos: quien invita recibe un premio cuando su amigo canjea su primer cupón. Hay cupones "solo Plus" y un regalo mensual para los suscriptores. |
| `foro` | Preguntas y respuestas entre usuarios con cuenta, con mejor respuesta e insignia para las cuentas de taller. Con 3 reportes, una publicación se oculta hasta que un admin la revise. |
| `tramites` | SOAT (tarifa de ley y pedido dentro de la app; el pago es una simulación mientras no haya aliado) y CDA para la técnico-mecánica. |
| `logros` | Insignias y puntos (servicio verificado, aporte útil, viajero, buena reseña) canjeables por cupones. |
| `noticias` | Titulares de fuentes RSS/Atom y artículos de consejo. |
| `notificaciones` | Avisos dentro del sitio (citas, Plus, SOAT, etc.). |
| `garaje` | "Mi garaje": motos, kilometraje e historial; plan de mantenimiento por línea de moto; SOAT, técnico-mecánica y documentos privados; cotización de SOAT; avisos de pico y placa por WhatsApp; modelo 3D; despiece interactivo (ver [docs/despiece.md](docs/despiece.md)). |

### Mi garaje en detalle

- Cada línea del catálogo tiene una ficha técnica editable en el admin: tipo, cilindraje, transmisión, refrigeración, frenos, suspensión y rines.
  - La ficha decide qué tareas aplican (cadena o correa CVT, pastillas o bandas, refrigerante…) y la forma del modelo 3D.
- Cada tarea se marca "Al día", "Pronto" (80 %) o "Toca ya" según los km y el tiempo desde su último registro. Con una semana de lecturas de kilometraje se estima la fecha de cada cambio.
- Se sugieren talleres que ofrecen el servicio que toca, con sus cupones.
- El modelo 3D (`garaje/static/garaje/js/moto3d.js`) se arma con la ficha y el color de la moto. En modo "Estado" cada pieza se colorea según lo que necesita.
- Los documentos personales (SOAT, técnico-mecánica) se guardan fuera de `MEDIA_ROOT`, en `DJANGO_PRIVADO_ROOT`, y solo los ve el dueño de la moto.
- El catálogo inicial y el plan de mantenimiento se cargan con migraciones. Las fichas e intervalos son orientativos.

## Instalar y correr en local (Windows)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python manage.py migrate
python manage.py cargar_demo
python manage.py createsuperuser
python manage.py runserver 8001
```

Abrir http://127.0.0.1:8001 (admin en `/admin`). `cargar_demo` imprime los PIN de canje de los talleres demo.

- `requirements.txt` trae lo que usa el servidor. `requirements-dev.txt` agrega PyMuPDF, que solo hace falta para importar catálogos de despiece.
- `.env` es opcional: sin `GOOGLE_CLIENT_ID` no aparece el ingreso con Google, y sin `EMAIL_HOST` los correos salen por la consola.
- **Tailwind** va compilado en `talleres/static/talleres/css/tw.css` (no hay CDN). Si usas clases nuevas de Tailwind en una plantilla, recompila con `npm install` (la primera vez) y luego `npm run css`. Mientras trabajas puedes dejar `npm run css:vigilar` corriendo. La configuración está en `tailwind/`.

### Pruebas

```bash
python manage.py test garaje -v 1
python manage.py test
```

La primera corre solo una app. La segunda es la suite completa (unos 2 minutos): córrela cuando cambien modelos, migraciones, `config/` o `templates/base.html`, y antes de desplegar.

## Comandos de `manage.py`

| Comando | Qué hace |
| --- | --- |
| `cargar_demo` | Carga barrios, servicios, marcas, talleres, cupones y foro de ejemplo. Se puede repetir: no duplica nada. |
| `importar_despiece <pdf> <mapa.json>` | Importa las láminas de un catálogo de partes en PDF según un mapa JSON. Opciones: `--reemplazar` borra y vuelve a crear las láminas (se pierden las marcas hechas a mano); `--reenlazar` actualiza las láminas existentes sin borrarlas. Solo en local, con `requirements-dev.txt`. Detalle en [docs/despiece.md](docs/despiece.md). |
| `traducir_despiece` | Vuelve a calcular el nombre en español y la explicación de todas las piezas con el glosario, sin tocar las marcas. Úsalo después de mejorar `garaje/despiece_glosario.py`. |
| `recordar_pico_placa` | Envía por WhatsApp el recordatorio de pico y placa de mañana a quienes lo activaron. Pensado para correr cada tarde con un cron. |
| `avisar_vencimientos` | Crea los avisos de SOAT y técnico-mecánica (30, 15 y 3 días antes) y de pico y placa. Pensado para un cron diario temprano. |
| `recordar_citas` | Envía la notificación de recordatorio de las citas de mañana. No repite avisos. Pensado para un cron diario (p. ej. 6 p. m.). |
| `evaluar_logros` | Otorga la insignia *Viajero* de las rodadas que ya pasaron (las demás insignias llegan al momento). Pensado para un cron cada noche. |
| `precalentar_despiece` | Arma y guarda en caché el despiece de todas las motos, para que nadie espere tras un despliegue. Lo dispara `.github/workflows/despiece.yml` después de cada push. |
| `importar_noticias` | Trae los titulares nuevos de las fuentes de noticias (RSS/Atom). |

Ejemplo de importación:

```bash
python manage.py importar_despiece despiece_local/N-MAX-BBE4-2024.pdf garaje/despiece_mapas/yamaha_nmax_bbe4.json
```

## Variables de entorno

Las principales (ver `config/settings.py` y `.env.example`):

| Variable | Para qué |
| --- | --- |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DATABASE_URL` | Lo básico de Django. Sin `DATABASE_URL` se usa `db.sqlite3`. |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `SITIO_URL` | Dominio del sitio y enlaces en los correos. |
| `DJANGO_MEDIA_ROOT`, `DJANGO_PRIVADO_ROOT` | Fotos públicas y documentos privados. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Ingreso con Google. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | Correo saliente (verificación, recuperar contraseña). |
| `PLUS_PRECIO_MENSUAL`, `PLUS_NEQUI`, `TALLERYA_WHATSAPP` | Cobro de Plus (por defecto $9.900 al mes). |
| `WHATSAPP_BACKEND`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_PLANTILLA_*` | Envío de mensajes de WhatsApp (pico y placa, citas). |
| `CONTACTO_*`, `LEGAL_*` | Datos de contacto y legales que salen en las páginas legales. |

## Desplegar en Render

El repositorio trae `render.yaml` (Blueprint) y `build.sh`.

1. Crea una cuenta en https://render.com y conecta tu GitHub.
2. Ve a **New → Blueprint** y elige el repositorio. Render crea la base de datos PostgreSQL y el servicio web (gunicorn).
3. Cuando te los pida, completa:
   - `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`: el administrador se crea en el primer despliegue.
   - `TALLERYA_WHATSAPP` y `PLUS_NEQUI`: los datos para cobrar Plus.
4. Cada `git push` a `main` vuelve a desplegar el sitio.

En cada despliegue, `build.sh` hace esto:

1. Instala dependencias.
2. Recompila Tailwind si hay Node; si no, usa el `tw.css` del repositorio.
3. Junta los estáticos (whitenoise) y aplica migraciones.
4. Carga los datos demo si `CARGAR_DEMO=1`.
5. Crea el administrador.

Antes de producción, ten en cuenta:

- **Plan gratuito**: el servicio se duerme sin visitas y tarda en despertar. La base de datos gratuita vence a los 30 días, así que para datos reales usa un plan pago.
- **Correo**: configura las variables `EMAIL_*` (por ejemplo con Brevo o SendGrid) o no saldrán los correos de verificación ni los de recuperar contraseña.
- **Archivos**: el disco de Render se borra en cada despliegue. Monta un Disk y apunta `DJANGO_MEDIA_ROOT` y `DJANGO_PRIVADO_ROOT` a él, o usa S3 o Cloudinary.
- **Despiece**: las láminas y sus imágenes se generan en local con `importar_despiece` y quedan en la base de datos y en `media/`. Hay que llevarlas a producción aparte (ver [docs/despiece.md](docs/despiece.md)).
- **Dominio propio**: agrégalo en Render y en `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS`.
- **Cron**: programa `recordar_pico_placa`, `avisar_vencimientos`, `recordar_citas`, `evaluar_logros` (y `importar_noticias` si lo usas) como Cron Job de Render.

## Carpetas que nunca van al repositorio

`despiece_local/`, `manual_despiece/`, `planos_a_generar/`, `media/`, `privado/` y `db.sqlite3` son solo locales. Allí están, entre otras cosas, los catálogos de los fabricantes, que no se publican.
