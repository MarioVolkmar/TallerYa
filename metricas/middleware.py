"""Cuenta las páginas vistas por nombre de ruta (garaje:moto, no /garaje/12/). Una INSERT por página HTML servida.

No cuenta: estáticos, /media/, admin, la consola y el propio panel, peticiones que no sean GET 200 con HTML,
fetch/AJAX, precargas del navegador, bots conocidos, ni a quien pide no ser rastreado (DNT o Sec-GPC)."""
from django.conf import settings

from . import nucleo
from .models import Evento

EXCLUIDOS = ("/admin/", "/consola/", "/metricas/", "/media/", "/" + settings.STATIC_URL.strip("/") + "/", "/favicon",
             "/robots.txt", "/sw.js", "/manifest", "/tareas/", "/__")


class MedirUso:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        if (metodo := getattr(request, "_metricas_login", None)) and not getattr(request, "_metricas_registro", False):
            nucleo.registrar_evento(request, "inicio_sesion", metodo=metodo)
        if nucleo.activas() and self._es_pagina(request, respuesta) and nucleo.puede_medir(request):
            nucleo.guardar(request, Evento.VISTA, request.resolver_match.view_name)
        return respuesta

    @staticmethod
    def _es_pagina(request, respuesta):
        return (request.method == "GET" and respuesta.status_code == 200
                and respuesta.get("Content-Type", "").startswith("text/html")
                and getattr(request, "resolver_match", None) is not None and request.resolver_match.view_name
                and not request.path.startswith(EXCLUIDOS)
                and request.headers.get("X-Requested-With") is None
                and "prefetch" not in (request.headers.get("Sec-Purpose", "") + request.headers.get("Purpose", "")))
