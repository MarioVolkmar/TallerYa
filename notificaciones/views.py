from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST

from .models import Notificacion


@login_required
def lista(request):
    return render(request, "notificaciones/lista.html", {"notificaciones": request.user.notificaciones.all()[:60]})


@login_required
def panel(request):
    """Las últimas notificaciones para el desplegable de la campanita."""
    ultimas = request.user.notificaciones.all()[:8]
    return JsonResponse({
        "sin_leer": request.user.notificaciones.filter(leida=False).count(),
        "notificaciones": [{
            "tipo": n.tipo, "titulo": n.titulo, "texto": n.texto, "leida": n.leida,
            "hace": timesince(n.creada).split(",")[0], "ir": reverse("notificaciones:ir", args=[n.pk]),
        } for n in ultimas],
    })


@login_required
def ir(request, pk):
    """Marca la notificación como leída y lleva a su página (solo rutas internas)."""
    notif = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    if not notif.leida:
        notif.leida = True
        notif.save(update_fields=["leida"])
    interna = notif.url.startswith("/") and not notif.url.startswith("//")
    return redirect(notif.url if interna else "notificaciones:lista")


@login_required
@require_POST
def marcar_todas(request):
    request.user.notificaciones.filter(leida=False).update(leida=True)
    if request.headers.get("X-Requested-With") == "fetch":
        return JsonResponse({"ok": True})
    return redirect("notificaciones:lista")
