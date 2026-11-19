"""Crea una sesión de Django para un usuario (sin contraseña) e imprime la línea de JS que la pone en el navegador.
Uso: venv/Scripts/python.exe .claude/skills/optimizar-velocidad/sesion.py correo@x.com
Solo para el servidor local (127.0.0.1:8001). No imprime nada más que la clave de sesión local.
"""
import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY, get_user_model
from importlib import import_module

u = get_user_model().objects.get(email__iexact=sys.argv[1])
s = import_module(settings.SESSION_ENGINE).SessionStore()
s[SESSION_KEY] = str(u.pk)
s[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0] if getattr(settings, "AUTHENTICATION_BACKENDS", None) else "django.contrib.auth.backends.ModelBackend"
s[HASH_SESSION_KEY] = u.get_session_auth_hash()
s.create()
print(f'document.cookie = "{settings.SESSION_COOKIE_NAME}={s.session_key}; path=/"')
