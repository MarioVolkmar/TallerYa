"""Interruptor del piloto: con settings.PILOTO_OCULTAR_SOCIAL, foro, rodadas, Plus y referidos «no existen»:
las URLs responden 404 y las plantillas no pintan enlaces ni avisos (variable `oculta_social`). El código queda intacto."""
from django.conf import settings
from django.http import Http404

PREFIJOS_OCULTOS = ("/foro/", "/plus/", "/r/", "/cuenta/regalo/")


def contexto(request):
    return {"oculta_social": bool(getattr(settings, "PILOTO_OCULTAR_SOCIAL", False))}


class OcultarSocial:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "PILOTO_OCULTAR_SOCIAL", False) and (request.path + "/").startswith(PREFIJOS_OCULTOS):
            raise Http404
        return self.get_response(request)
