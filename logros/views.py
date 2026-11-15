"""Mis insignias: lo ganado, los puntos y el canje por cupones."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cupones.models import Cupon
from cupones.servicios import CuponNoDisponible

from . import reglas


def _movimientos(usuario, limite=20):
    """Historial único de puntos: insignias ganadas (+) y canjes (−), del más reciente al más antiguo."""
    filas = [{"tipo": "logro", "fecha": l.creado, "insignia": l.insignia, "puntos": l.puntos}
             for l in usuario.logros.order_by("-creado")[:limite]]
    filas += [{"tipo": "canje", "fecha": c.creado, "cupon": c.codigo.cupon, "codigo": c.codigo.codigo, "puntos": c.puntos}
              for c in usuario.canjes_logros.select_related("codigo", "codigo__cupon").order_by("-creado")[:limite]]
    return sorted(filas, key=lambda f: f["fecha"], reverse=True)[:limite]


@login_required
def mis_insignias(request):
    nuevos = reglas.evaluar(request.user)
    if nuevos:
        messages.success(request, f"¡Ganaste {nuevos} insignia{'s' if nuevos > 1 else ''} nueva{'s' if nuevos > 1 else ''}!")
    ganadas = {r["insignia"].clave: r["veces"] for r in reglas.resumen(request.user)}
    puntos = reglas.puntos_disponibles(request.user)
    cupones = list(Cupon.objects.vigentes().filter(puntos_logros__gt=0).select_related("taller").order_by("puntos_logros"))
    for c in cupones:
        c.faltan = max(c.puntos_logros - puntos, 0)
    return render(request, "logros/mis_insignias.html", {
        "insignias": [{"insignia": i, "veces": ganadas.get(c, 0)} for c, i in reglas.INSIGNIAS.items()],
        "puntos": puntos,
        "cupones": cupones,
        "movimientos": _movimientos(request.user),
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
