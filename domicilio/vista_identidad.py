"""Página «Verifica tu identidad» del mecánico y entrega protegida de las fotos (solo admins)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from consola.permisos import es_admin

from . import identidad as servicio
from .forms import IdentidadForm
from .models import IdentidadMecanico, MecanicoDomicilio


@login_required
def identidad(request):
    mecanico = MecanicoDomicilio.objects.filter(usuario=request.user).select_related("identidad").first()
    if not mecanico:
        return redirect("domicilio:registro")
    ident = getattr(mecanico, "identidad", None)
    estado = servicio.estado_para_panel(mecanico)
    form = None
    if estado not in ("enviada", "aprobada"):  # en revisión o aprobada no se reenvía
        form = IdentidadForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            d = form.cleaned_data
            servicio.enviar(mecanico, d["frente"], d["respaldo"], d["selfie"])
            messages.success(request, "Recibimos tus fotos. Una persona del equipo las revisa y te avisamos.")
            return redirect("domicilio:identidad")
    elif request.method == "POST":
        return redirect("domicilio:identidad")
    respuesta = render(request, "domicilio/identidad.html", {"m": mecanico, "ident": ident, "estado": estado, "form": form})
    respuesta["Cache-Control"] = "private, no-store"
    return respuesta


TIPO = "image/jpeg"  # siempre se re-codifican como JPEG al subirlas


@login_required
def identidad_foto(request, pk, campo):
    """Solo administradores activos; para cualquier otra persona es un 404 (no revela si existe)."""
    if campo not in IdentidadMecanico.CAMPOS_FOTO or not es_admin(request.user):
        raise Http404
    ident = IdentidadMecanico.objects.filter(pk=pk).first()
    archivo = getattr(ident, campo, None) if ident else None
    if not archivo:
        raise Http404
    try:
        respuesta = FileResponse(archivo.open("rb"), content_type=TIPO)
    except (FileNotFoundError, ValueError):
        raise Http404
    respuesta["Content-Disposition"] = f'inline; filename="identidad-{ident.pk}-{campo}.jpg"'
    respuesta["Cache-Control"] = "private, no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"
    respuesta["Content-Security-Policy"] = "default-src 'none'; sandbox"
    respuesta["X-Robots-Tag"] = "noindex"
    return respuesta
