"""Solo entra el rol administrador (cuenta de staff activa). Se verifica en cada vista y en cada acción."""
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def es_admin(usuario):
    return bool(usuario and usuario.is_authenticated and usuario.is_active and usuario.is_staff)


def solo_admin(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
        if not es_admin(request.user):
            raise PermissionDenied("Solo para administradores.")
        return vista(request, *args, **kwargs)
    return envoltura
