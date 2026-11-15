"""Configuración de TallerYa. Valores sensibles y de producción vía variables de entorno."""
import os
import sys
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Variables locales desde .env (solo desarrollo; el archivo no va al repositorio). No pisa las que ya existan.
if (_env := BASE_DIR / ".env").exists():
    for _linea in _env.read_text(encoding="utf-8").splitlines():
        _linea = _linea.strip()
        if _linea and not _linea.startswith("#") and "=" in _linea:
            _clave, _valor = _linea.split("=", 1)
            os.environ.setdefault(_clave.strip(), _valor.strip().strip('"').strip("'"))


def env_bool(nombre, defecto=False):
    return os.environ.get(nombre, "1" if defecto else "0").lower() in ("1", "true", "si", "yes")


def env_lista(nombre, defecto=""):
    return [v.strip() for v in os.environ.get(nombre, defecto).split(",") if v.strip()]


# Seguro por defecto: DEBUG apagado salvo que DJANGO_DEBUG=1 (en local, ponlo en .env).
DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insegura-cambiar-en-produccion" if (DEBUG or sys.argv[1:2] == ["test"]) else "")
if not SECRET_KEY:
    raise RuntimeError("Falta la variable de entorno DJANGO_SECRET_KEY")

ALLOWED_HOSTS = env_lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_lista("DJANGO_CSRF_TRUSTED_ORIGINS")
# Render define este nombre automáticamente (ej: tallerya.onrender.com)
if render_host := os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "talleres",
    "cupones",
    "cuentas",
    "foro",
    "garaje",
    "notificaciones",
    "noticias",
    "logros",
    "tramites",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Comprime el HTML (~48 KB -> ~9 KB): carga más rápido con datos móviles. Los estáticos ya los comprime WhiteNoise.
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cuentas.roles.contexto",
                "notificaciones.servicios.contexto",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite en local; en producción DATABASE_URL apunta a PostgreSQL.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600, conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# El primero precarga taller/perfiles con el usuario; el de Django queda para sesiones ya abiertas con él.
AUTHENTICATION_BACKENDS = ["cuentas.backends.Backend", "django.contrib.auth.backends.ModelBackend"]

LOGIN_URL = "cuentas:entrar"
LOGIN_REDIRECT_URL = "talleres:inicio"
LOGOUT_REDIRECT_URL = "talleres:inicio"

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
# Documentos personales (SOAT, técnico-mecánica): fuera de MEDIA_ROOT para que /media/ nunca los sirva.
# Solo se entregan a su dueño desde la vista garaje:documento.
PRIVADO_ROOT = Path(os.environ.get("DJANGO_PRIVADO_ROOT", BASE_DIR / "privado"))

# Ingreso con Google: credenciales de un "ID de cliente de OAuth" (Google Cloud Console). Sin ellas, el botón no aparece.
# Web Push (claves VAPID; sin ellas no hay avisos push)
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:hola@tallerya.co")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Correo (recuperar contraseña). En local se imprime en la consola.
if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "TallerYa <no-responder@tallerya.co>")
# Dirección pública del sitio para los enlaces de correos enviados sin una visita (tareas programadas)
SITIO_URL = os.environ.get("SITIO_URL", "")

# Proxies delante de Django que añaden su salto a X-Forwarded-For (Render: 1). Sirve para saber la IP real de quien
# visita en los límites de intentos (cuentas/limites.py). En local, 0: se usa REMOTE_ADDR.
PROXIES_DE_CONFIANZA = int(os.environ.get("PROXIES_DE_CONFIANZA", "1" if os.environ.get("RENDER") else "0"))

# Seguridad en producción
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}

# --- TallerYa ---
# WhatsApp de TallerYa para recibir comprobantes de pago de Plus (solo números, con 57).
TALLERYA_WHATSAPP = os.environ.get("TALLERYA_WHATSAPP", "573000000000")
PLUS_PRECIO_MENSUAL = int(os.environ.get("PLUS_PRECIO_MENSUAL", "9900"))
PLUS_NEQUI = os.environ.get("PLUS_NEQUI", "300 000 0000")
PLUS_DIAS = 30

# Contacto de TallerYa para el footer. Lo que quede vacío no se muestra.
CONTACTO = {
    "whatsapp": os.environ.get("CONTACTO_WHATSAPP", ""),      # solo números con indicativo, ej: 573001234567
    "correo": os.environ.get("CONTACTO_CORREO", ""),
    "direccion": os.environ.get("CONTACTO_DIRECCION", ""),
    "ciudad": os.environ.get("CONTACTO_CIUDAD", "Medellín, Antioquia"),
    "horario": os.environ.get("CONTACTO_HORARIO", ""),        # ej: Lun-Vie 8am-6pm
    "instagram": os.environ.get("CONTACTO_INSTAGRAM", ""),    # usuario sin @
}

# Datos del responsable para las páginas legales (términos, tratamiento de datos). Complétalos antes de publicar.
LEGAL = {
    "razon_social": os.environ.get("LEGAL_RAZON_SOCIAL", "TallerYa"),
    "nit": os.environ.get("LEGAL_NIT", ""),
    "correo": os.environ.get("LEGAL_CORREO", ""),
    "ciudad": os.environ.get("LEGAL_CIUDAD", "Medellín, Antioquia, Colombia"),
    "actualizado": os.environ.get("LEGAL_ACTUALIZADO", "12 de noviembre de 2026"),
}

# WhatsApp (recordatorios de pico y placa). "consola" solo escribe en el log; "cloud" usa la API de Meta.
WHATSAPP_BACKEND = os.environ.get("WHATSAPP_BACKEND", "consola")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
WHATSAPP_PLANTILLA_PICO_PLACA = os.environ.get("WHATSAPP_PLANTILLA_PICO_PLACA", "recordatorio_pico_placa")
# Citas: propuesta de nueva fecha (motero, taller, fecha, hora, enlace) y cancelación (motero, taller, fecha, motivo)
WHATSAPP_PLANTILLA_REPROGRAMAR = os.environ.get("WHATSAPP_PLANTILLA_REPROGRAMAR", "cita_reprogramada")
WHATSAPP_PLANTILLA_CANCELAR = os.environ.get("WHATSAPP_PLANTILLA_CANCELAR", "cita_cancelada")
WHATSAPP_PLANTILLA_CONFIRMAR = os.environ.get("WHATSAPP_PLANTILLA_CONFIRMAR", "cita_confirmada")

# Noticiero motero: los titulares se refrescan solos (en segundo plano) cada pocas horas. Apagado en las pruebas.
import sys  # noqa: E402
NOTICIAS_AUTO = env_bool("NOTICIAS_AUTO", True) and sys.argv[1:2] != ["test"]

# Cachés: la de siempre en memoria (límites de intentos, vistas del foro) y una en disco para el despiece,
# que es caro de armar y sobrevive a reinicios del servidor. En las pruebas, todo en memoria.
import tempfile  # noqa: E402
# Con REDIS_URL (ej. Redis de Render) la caché "default" se comparte entre todos los procesos del servidor:
# los límites de intentos y los contadores valen igual sin importar qué proceso atienda la visita.
CACHES = {
    "default": (
        {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": os.environ["REDIS_URL"]}
        if os.environ.get("REDIS_URL") and sys.argv[1:2] != ["test"] else
        {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    ),
    # Lo pesado del despiece (~200 KB por catálogo): en la base de datos, para que sobreviva a reinicios y a que Render
    # duerma el servicio (su disco se borra). 100 entradas ≈ 4 versiones del código × 25 catálogos (≈ 20 MB como máximo).
    # Tabla propia: `manage.py createcachetable` (lo corre build.sh).
    "despiece": (
        {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "despiece"}
        if sys.argv[1:2] == ["test"] else
        {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "cache_despiece",
         "OPTIONS": {"MAX_ENTRIES": 100, "CULL_FREQUENCY": 3}}
    ),
    # Dibujos SVG de láminas y piezas: muchos (miles) y baratos de volver a dibujar; en disco, sin ocupar la base.
    "despiece_svg": (
        {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "despiece_svg"}
        if sys.argv[1:2] == ["test"] else
        {"BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
         "LOCATION": os.environ.get("DESPIECE_CACHE_DIR", os.path.join(tempfile.gettempdir(), "tallerya_despiece")),
         "OPTIONS": {"MAX_ENTRIES": 20000}}
    ),
}
