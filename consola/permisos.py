"""Solo entra el rol administrador (cuenta de staff activa). Se verifica en cada vista y en cada acción."""
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def es_admin(usuario):
    return bool(usuario and usuario.is_authenticated and usuario.is_active and usuario.is_staff)


def es_superusuario(usuario):
    return es_admin(usuario) and usuario.is_superuser


def solo_superusuario(vista):
    """Como solo_admin, pero exige además ser superusuario (ajustes que afectan a todo el sitio)."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
        if not es_superusuario(request.user):
            raise PermissionDenied("Solo para el superusuario.")
        return vista(request, *args, **kwargs)
    return envoltura


def solo_admin(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
        if not es_admin(request.user):
            raise PermissionDenied("Solo para administradores.")
        return vista(request, *args, **kwargs)
    return envoltura


def pagina_de_consola(vista):
    """Para las páginas propias dentro del marco de la consola (formularios de alta, categorías…): los enlaces de la
    barra lateral son relativos (?seccion=X), así que si llegan aquí se sale del formulario a esa sección."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if request.method == "GET" and request.GET.get("seccion"):
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(reverse("consola:inicio") + "?" + request.GET.urlencode())
        return vista(request, *args, **kwargs)
    return solo_admin(envoltura)
