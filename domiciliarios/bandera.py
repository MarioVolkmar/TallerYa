"""La bandera DOMICILIARIOS_ACTIVO: apagada, ninguna URL responde (404) y no aparece ningún enlace."""
from functools import wraps

from django.conf import settings
from django.http import Http404


def activo():
    from consola.ajustes import ajuste
    return ajuste("domiciliarios_activo")


def requiere_bandera(vista):
    @wraps(vista)
    def envuelta(request, *args, **kwargs):
        if not activo():
            raise Http404
        return vista(request, *args, **kwargs)
    return envuelta
