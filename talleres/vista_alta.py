"""Alta de talleres sin cuenta: autoregistro desde el celular y revisión/aprobación por enlace con token.
El taller queda NO publicado hasta que él apruebe su ficha (autorizando sus datos) y el equipo la publique en la consola."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from cuentas import limites
from cuentas.limites import ip_cliente

from .forms import RegistroTallerForm
from .forms_alta import AutoregistroForm, RevisionForm
from .models import Taller

ALTAS_HORA_IP = 5


def _sin_indexar(respuesta):
    respuesta["X-Robots-Tag"] = "noindex, nofollow"
    return respuesta


def autoregistro(request):
    """El taller llena su ficha desde el celular; queda «pendiente de revisión» hasta que la aprobemos."""
    ip = ip_cliente(request)
    form = AutoregistroForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if limites.superado(f"alta-taller:{ip}", ALTAS_HORA_IP):
            form.add_error(None, "Se enviaron muchos registros desde esta conexión. Intenta en una hora.")
        elif form.is_valid():
            taller = form.save(commit=False)
            taller.activo = False
            taller.origen_alta = Taller.Alta.AUTOREGISTRO
            taller.autoriza_datos = True
            taller.aprobado_por_taller, taller.aprobado_ip = timezone.now(), ip
            taller.generar_token()
            taller.save()
            form.save_m2m()
            limites.sumar(f"alta-taller:{ip}", 3600)
            return redirect("talleres:alta_enviada", token=taller.token_revision)
    return _sin_indexar(render(request, "talleres/autoregistro.html", {
        "form": form, "barrios_por_ciudad": RegistroTallerForm.barrios_por_ciudad()}))


def alta_enviada(request, token):
    taller = get_object_or_404(Taller.objects.exclude(origen_alta=Taller.Alta.CUENTA), token_revision=token)
    return _sin_indexar(render(request, "talleres/alta_enviada.html", {"taller": taller}))


def revisar_ficha(request, token):
    """Enlace sin cuenta: el taller ve su ficha, corrige y aprueba. Después de aprobar queda de solo lectura."""
    taller = get_object_or_404(Taller.objects.exclude(origen_alta=Taller.Alta.CUENTA), token_revision=token)
    if taller.aprobado_por_taller:
        return _sin_indexar(render(request, "talleres/revisar_ficha.html", {"taller": taller, "aprobada": True}))
    if taller.enlace_vencido:
        return _sin_indexar(render(request, "talleres/revisar_ficha.html", {"taller": taller, "vencida": True}, status=410))
    form = RevisionForm(request.POST or None, request.FILES or None, instance=taller)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if form.cleaned_data["autoriza"]:
            obj.autoriza_datos = True
            obj.aprobado_por_taller, obj.aprobado_ip = timezone.now(), ip_cliente(request)
        obj.save()
        form.save_m2m()
        if form.cleaned_data["autoriza"]:
            messages.success(request, "¡Listo! Aprobaste tu ficha. Un asesor de TallerYa la publica en breve.")
        else:
            messages.info(request, "Guardamos tus correcciones. Para publicar, marca la autorización y aprueba.")
        return redirect("talleres:revisar_ficha", token=token)
    return _sin_indexar(render(request, "talleres/revisar_ficha.html", {
        "taller": taller, "form": form, "aprobada": False,
        "barrios_por_ciudad": RegistroTallerForm.barrios_por_ciudad()}))
