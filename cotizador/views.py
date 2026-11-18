"""Vistas del piloto. Devuelven el recuadro HTML que cotizar.js pone en la ficha de la pieza o en el plan.
Con COTIZADOR_ACTIVO apagado responden 404, como si la app no existiera."""
from functools import wraps

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from cuentas import limites
from garaje.models import ParteDespiece

from . import servicio

MAX_POR_HORA_USUARIO = 40  # cotizaciones por hora y persona (de la caché o no)
MAX_POR_HORA_IP = 80        # varias personas pueden compartir IP (wifi de un taller)


def solo_activo(vista):
    @wraps(vista)
    def envuelta(request, *args, **kwargs):
        if not settings.COTIZADOR_ACTIVO:
            raise Http404
        return vista(request, *args, **kwargs)
    return envuelta


def _frenado(request):
    """Reutiliza los frenos de cuentas/limites.py: True si la persona o su IP ya se pasaron."""
    claves = [(f"cotizador:ip:{limites.ip_cliente(request)}", MAX_POR_HORA_IP)]
    if request.user.is_authenticated:
        claves.append((f"cotizador:usuario:{request.user.pk}", MAX_POR_HORA_USUARIO))
    if any(limites.superado(c, m) for c, m in claves):
        return True
    for c, _ in claves:
        limites.sumar(c, 3600)
    return False


def _responder(request, parte):
    if _frenado(request):
        return render(request, "cotizador/_recuadro.html",
                      {"error": "Hiciste muchas cotizaciones seguidas. Espera un rato e inténtalo de nuevo."}, status=429)
    try:
        cot = servicio.cotizar(servicio.datos_parte(parte))
    except servicio.SinDatos:
        return render(request, "cotizador/_recuadro.html",
                      {"error": "No pudimos consultar los precios en este momento. Inténtalo más tarde."}, status=503)
    return render(request, "cotizador/_recuadro.html", {"c": cot, "parte": parte})


_PARTES = ParteDespiece.objects.select_related("lamina__despiece__linea__marca")


@require_GET
@solo_activo
def cotizar_parte(request, pk):
    """Pieza elegida en el despiece (por su id, el mismo que usa despiece.json)."""
    return _responder(request, get_object_or_404(_PARTES, pk=pk, lamina__despiece__activo=True))


@require_GET
@solo_activo
def cotizar_codigo(request):
    """Repuesto del plan de mantenimiento (por su código de repuesto)."""
    codigo = (request.GET.get("c") or "").strip()[:30]
    parte = _PARTES.filter(codigo=codigo, lamina__despiece__activo=True).first() if codigo else None
    if not parte:
        raise Http404
    return _responder(request, parte)
