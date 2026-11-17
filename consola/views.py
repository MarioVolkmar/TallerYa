"""Consola de administración: una sola página (?seccion=...) y una sola vista para todas las acciones."""
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cuentas.limites import ip_cliente

from . import secciones
from .acciones import ACCIONES, ErrorAccion, correr
from .permisos import solo_admin


@solo_admin
def consola(request):
    clave = request.GET.get("seccion") or secciones.PREDETERMINADA
    seccion = secciones.POR_CLAVE.get(clave)
    if not seccion:
        raise Http404("Esa sección no existe.")
    filas, total = secciones.con_pendientes()
    if seccion.lista:
        plantilla, contexto = seccion.resolver()(request)
    else:
        plantilla, contexto = "consola/proximamente.html", {}
    return render(request, "consola/consola.html", {
        "seccion": seccion, "secciones": filas, "total_pendientes": total, "plantilla": plantilla,
        "pendientes_seccion": dict((s.key, n) for s, n in filas)[seccion.key], **contexto,
    })


def _volver(request):
    destino = request.POST.get("volver", "")
    if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}, request.is_secure()):
        return destino
    return reverse("consola:inicio")


@solo_admin
@require_POST
def ejecutar(request, clave, pk):
    """Patrón único: permiso → acción → bitácora → respuesta (JSON para fetch, mensaje + redirección sin JS)."""
    regla = ACCIONES.get(clave)
    if not regla:
        raise Http404("Acción desconocida.")
    obj = get_object_or_404(regla.modelo, pk=pk)
    por_fetch = request.headers.get("X-Requested-With") == "fetch"
    try:
        mensaje, extra = correr(regla, request, obj, ip=ip_cliente(request))
    except ErrorAccion as e:
        if por_fetch:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)
        messages.error(request, str(e))
        return redirect(_volver(request))
    if por_fetch:
        return JsonResponse({"ok": True, "mensaje": mensaje, **extra})
    if extra.get("contrasena"):
        mensaje += f" Contraseña temporal: {extra['contrasena']}"
    messages.success(request, mensaje)
    if extra.get("redirigir"):
        return redirect(reverse("consola:inicio") + extra["redirigir"])
    return redirect(_volver(request))
