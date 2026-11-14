"""Mis insignias: lo ganado, los puntos y el canje por cupones."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cupones.models import Cupon
from cupones.servicios import CuponNoDisponible

from . import reglas


@login_required
def mis_insignias(request):
    nuevos = reglas.evaluar(request.user)
    if nuevos:
        messages.success(request, f"¡Ganaste {nuevos} insignia{'s' if nuevos > 1 else ''} nueva{'s' if nuevos > 1 else ''}!")
    ganadas = {r["insignia"].clave: r["veces"] for r in reglas.resumen(request.user)}
    return render(request, "logros/mis_insignias.html", {
        "insignias": [{"insignia": i, "veces": ganadas.get(c, 0)} for c, i in reglas.INSIGNIAS.items()],
        "puntos": reglas.puntos_disponibles(request.user),
        "cupones": Cupon.objects.vigentes().filter(puntos_logros__gt=0).select_related("taller").order_by("puntos_logros"),
        "logros": request.user.logros.all()[:20],
        "canjes": request.user.canjes_logros.select_related("codigo", "codigo__cupon")[:10],
        "tiene_perfil": hasattr(request.user, "motociclista"),
    })


@login_required
@require_POST
def canjear(request, pk):
    cupon = get_object_or_404(Cupon, pk=pk, puntos_logros__gt=0)
    try:
        codigo = reglas.canjear(request.user, cupon)
    except (reglas.PuntosInsuficientes, CuponNoDisponible) as e:
        messages.error(request, str(e))
        return redirect("logros:mis_insignias")
    messages.success(request, f"¡Listo! Tu código es {codigo.codigo}.")
    return redirect(codigo)
