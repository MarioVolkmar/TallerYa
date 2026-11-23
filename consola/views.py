"""Consola de administración: una sola página (?seccion=...) y una sola vista para todas las acciones."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cuentas.limites import ip_cliente

from . import ajustes, secciones
from .acciones import ACCIONES, ErrorAccion, correr
from .models import Ajuste
from .permisos import es_superusuario, solo_admin, solo_superusuario


@solo_admin
def consola(request):
    clave = request.GET.get("seccion") or secciones.PREDETERMINADA
    seccion = secciones.POR_CLAVE.get(clave)
    if not seccion:
        raise Http404("Esa sección no existe.")
    if seccion.superusuario and not es_superusuario(request.user):
        raise PermissionDenied("Solo para el superusuario.")
    filas, total = secciones.con_pendientes()
    filas = [(s, n) for s, n in filas if not s.superusuario or es_superusuario(request.user)]
    pendientes_seccion = dict((s.key, n) for s, n in filas)[seccion.key]
    filas = [(s, n) for s, n in filas if s.en_menu and s.lista]  # las «pronto» (sin vista) no salen en el menú
    if seccion.lista:
        plantilla, contexto = seccion.resolver()(request)
    else:
        plantilla, contexto = "consola/proximamente.html", {}
    return render(request, "consola/consola.html", {
        "seccion": seccion, "secciones": filas, "total_pendientes": total, "plantilla": plantilla,
        "pendientes_seccion": pendientes_seccion, **contexto,
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
    if regla.superusuario and not es_superusuario(request.user):
        raise PermissionDenied("Solo para el superusuario.")
    obj = get_object_or_404(regla.modelo, pk=pk)
    return _correr(request, regla, obj)


@solo_superusuario
@require_POST
def ajuste(request, clave):
    """Prende o apaga un módulo (POST valor=1/0). La fila del ajuste nace aquí con el valor efectivo de hoy."""
    modulo = ajustes.POR_CLAVE.get(clave)
    if not modulo:
        raise Http404("Ese módulo no existe.")
    obj, _ = Ajuste.objects.get_or_create(clave=clave, defaults={"valor": ajustes.ajuste(clave)})
    return _correr(request, ACCIONES["ajustes.cambiar"], obj)


def _correr(request, regla, obj):
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
