"""Módulos apagables desde /consola/ (Configuración): foro, Plus, referidos, mecánicos a domicilio, TallerYa Ruta…
Apagado un módulo, sus URLs responden 404 y las plantillas no pintan enlaces ni avisos (variables `foro_activo`,
`plus_activo`, `referidos_activo`, `mecanicos_activo`, `herramientas_activo`). El valor inicial sale del .env (consola/ajustes.py)."""
from django.http import Http404

from consola.ajustes import ajuste, modulos_prefijos


def contexto(request):
    return {
        "foro_activo": ajuste("foro_activo"),
        "plus_activo": ajuste("plus_activo"),
        "referidos_activo": ajuste("referidos_activo"),
        "mecanicos_activo": ajuste("mecanicos_activo"),
        "proveedores_registro": ajuste("proveedores_registro"),
        "herramientas_activo": ajuste("herramientas_activo"),
    }


class OcultarSocial:
    """Middleware: 404 en las rutas de los módulos apagados."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ruta = request.path + "/"
        for modulo, prefijos in modulos_prefijos():
            if ruta.startswith(prefijos) and not ajuste(modulo.clave):
                raise Http404
        return self.get_response(request)
