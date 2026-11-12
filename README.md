# TallerYa

Directorio de talleres de motos en Medellín, con cupones, referidos, suscripción Plus y foro. Hecho en Django.

## Funciones

**Fase 1: directorio**
- Buscar talleres por texto, barrio, servicio y marca.
- Perfil del taller con servicios, marcas, horario, WhatsApp y calificación.
- Pedir cita y dejar reseña.
- Registro de talleres, que quedan inactivos hasta aprobarlos en el admin.

**Fase 2: cupones y referidos** (app `cupones`)
- Los cupones se crean en el admin, para un taller o para todos los talleres, con vencimiento y cupo opcionales.
- El motociclista obtiene un código único (`TY-XXXXXX`) con su nombre y celular.
- El taller canjea en `/canjear/` con su PIN de 6 dígitos (está en el admin). Los intentos fallidos se bloquean un rato.
- Referidos: cuando un amigo nuevo canjea su primer cupón, quien lo invitó recibe el cupón marcado como "premio por referido".

**Fase 3: cuentas, Plus y foro** (apps `cuentas` y `foro`)
- Cuentas con correo y contraseña, y recuperación de contraseña por correo.
- Al registrarse con un celular que ya tiene cupones, se pide uno de esos códigos para enlazarlos.
- TallerYa Plus: el motociclista lo solicita, paga por Nequi y envía el comprobante por WhatsApp. Tú lo activas en el admin (Suscripciones Plus → acción "Activar / renovar").
  - Beneficios: cupones marcados "solo Plus" y un cupón de regalo al mes.
- Foro: pregunta y responde cualquier usuario con cuenta. Hay mejor respuesta e insignia para las cuentas de taller (se vincula una cuenta al taller en el admin).
  - Con 3 reportes, una publicación se oculta hasta que la revises.

**Mi garaje: mantenimiento y modelo 3D** (app `garaje`)
- El motociclista agrega su moto: marca y línea del catálogo (o "otra"), modelo, color y kilometraje.
- Cada línea tiene una ficha técnica que se edita en el admin: tipo, cilindraje, transmisión, refrigeración, frenos, suspensión y rines.
  - La ficha define qué tareas aplican (cadena o correa CVT, pastillas o bandas, refrigerante, etc.).
  - También define la forma del modelo 3D.
- Cada actualización de kilometraje queda registrada. Cada tarea se marca "Al día", "Pronto" (80 %) o "Toca ya" según los km y el tiempo desde su último registro.
  - Con una semana de lecturas se estima la fecha de cada cambio.
- Se sugieren talleres que ofrecen el servicio que toca, con sus cupones.
- El modelo 3D (Three.js) se arma con la ficha y el color de la moto. En modo "Estado" cada pieza se colorea y al tocarla muestra qué necesita.
- El catálogo inicial (24 líneas) y el plan de mantenimiento (18 tareas) se cargan con una migración. Las fichas e intervalos son orientativos.

## Correr en local (Windows)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_demo
python manage.py createsuperuser
python manage.py runserver
```
Abrir http://127.0.0.1:8000 (admin en `/admin`). `cargar_demo` imprime los PIN de canje de los talleres demo.

Tests: `python manage.py test`

## Fase 4: publicar en Render
El repositorio incluye `render.yaml` (Blueprint), `build.sh` y `.env.example`.

1. Crea una cuenta en https://render.com y conecta tu GitHub.
2. Ve a **New → Blueprint** y elige el repositorio `TallerYa`. Render crea la base de datos PostgreSQL y el servicio web.
3. Cuando te los pida, completa:
   - `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`: el administrador se crea en el primer despliegue.
   - `TALLERYA_WHATSAPP` y `PLUS_NEQUI`: los datos para cobrar Plus.
4. Cada `git push` a `main` vuelve a desplegar el sitio.

Para tener en cuenta en producción:
- **Plan gratuito**: el servicio se "duerme" sin visitas y tarda en despertar. La base de datos gratuita de Render vence a los 30 días, así que para datos reales usa un plan pago.
- **Correo**: configura `EMAIL_HOST` y las demás variables de correo (por ejemplo Brevo o SendGrid) para que funcione "Olvidé mi contraseña".
- **Fotos de talleres**: el disco de Render se borra en cada despliegue. Monta un Disk y apunta `DJANGO_MEDIA_ROOT` a él, o usa S3 o Cloudinary.
- **Dominio propio**: agrégalo en Render y en `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS`.
- **Tailwind**: se carga desde su CDN. Más adelante conviene compilarlo para que la página cargue más rápido.
