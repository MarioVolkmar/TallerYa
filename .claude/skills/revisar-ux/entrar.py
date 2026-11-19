"""Crea una sesión de Django para un usuario (por correo) sin contraseña e imprime la cookie para el navegador.

Uso:  venv/Scripts/python.exe .claude/skills/revisar-ux/entrar.py correo@ejemplo.com
Luego, en javascript_tool del preview:  document.cookie = "sessionid=<valor>; path=/"; location.reload()
Solo local (base de desarrollo). La sesión vence como cualquier otra.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()
from django.conf import settings  # noqa: E402
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY, get_user_model  # noqa: E402
from importlib import import_module  # noqa: E402

correo = sys.argv[1] if len(sys.argv) > 1 else ""
u = get_user_model().objects.filter(email__iexact=correo).first()
if not u:
    sys.exit(f"No hay usuario con el correo {correo!r}")
s = import_module(settings.SESSION_ENGINE).SessionStore()
s[SESSION_KEY] = str(u.pk)
s[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0] if getattr(settings, "AUTHENTICATION_BACKENDS", None) else "django.contrib.auth.backends.ModelBackend"
s[HASH_SESSION_KEY] = u.get_session_auth_hash()
s.create()
print(f'{settings.SESSION_COOKIE_NAME}={s.session_key}')
