"""Vistas de la hoja de vida: la del dueño, la pública (por enlace) y la entrada del QR para el taller."""
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe

from . import hoja_vida, qr
from .forms_hoja_vida import RegistroPropioForm
from .models import EnlaceHojaVida
from .views import _moto_de, con_motociclista


@con_motociclista
def hoja_vida_moto(request, pk):
    moto = _moto_de(request, pk)
    form = RegistroPropioForm(moto=moto)
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "agregar":
            form = RegistroPropioForm(request.POST, moto=moto)
            if form.is_valid():
                registro = form.save(commit=False)
                registro.moto = moto
                registro.save()
                messages.success(request, "Servicio agregado a la hoja de vida.")
                return redirect("garaje:hoja_vida", moto.pk)
        elif accion == "codigo":
            hoja_vida.generar_codigo(moto)
            return redirect(reverse("garaje:hoja_vida", args=[moto.pk]) + "#codigo")
        elif accion == "compartir":
            hoja_vida.crear_enlace(moto)
            return redirect(reverse("garaje:hoja_vida", args=[moto.pk]) + "#compartir")
        elif accion == "revocar":
            hoja_vida.revocar_enlaces(moto)
            messages.success(request, "Listo: el enlace dejó de funcionar.")
            return redirect(reverse("garaje:hoja_vida", args=[moto.pk]) + "#compartir")
        elif accion == "eliminar":
            # Solo los propios: lo verificado por un taller no se borra desde aquí.
            borrados, _ = moto.hoja_vida.filter(pk=request.POST.get("registro"), verificado=False).delete()
            if borrados:
                messages.success(request, "Registro eliminado.")
            return redirect("garaje:hoja_vida", moto.pk)

    registros = list(moto.hoja_vida.select_related("taller"))
    codigo = hoja_vida.codigo_vigente(moto)
    enlace = hoja_vida.enlace_activo(moto)
    contexto = {"moto": moto, "registros": registros, "form": form, "resumen": hoja_vida.resumen(registros),
                "codigo": codigo, "enlace": enlace, "minutos_codigo": hoja_vida.MINUTOS_CODIGO}
    if codigo:
        contexto["qr_codigo"] = mark_safe(qr.svg(request.build_absolute_uri(
            reverse("garaje:servicio_codigo", args=[codigo.codigo])), "QR del código para el taller"))
    if enlace:
        contexto["url_enlace"] = request.build_absolute_uri(enlace.get_absolute_url())
        contexto["qr_enlace"] = mark_safe(qr.svg(contexto["url_enlace"], "QR de la hoja de vida"))
    return render(request, "garaje/hoja_vida.html", contexto)


def hoja_vida_publica(request, token):
    enlace = get_object_or_404(EnlaceHojaVida.objects.select_related("moto", "moto__linea", "moto__linea__marca"),
                               token=token, revocado__isnull=True)
    moto = enlace.moto
    registros = list(moto.hoja_vida.select_related("taller"))
    url = request.build_absolute_uri()
    respuesta = render(request, "garaje/hoja_vida_publica.html", {
        "moto": moto, "registros": registros, "resumen": hoja_vida.resumen(registros),
        "placa": hoja_vida.placa_enmascarada(moto.placa), "qr": mark_safe(qr.svg(url, "QR de esta hoja de vida")),
    })
    respuesta["X-Robots-Tag"] = "noindex, nofollow"
    respuesta["Referrer-Policy"] = "no-referrer"
    return respuesta


def servicio_codigo(request, codigo):
    """Lo que abre el QR que el motero le muestra al taller: lleva al panel del taller con el código puesto."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if getattr(request.user, "taller", None):
        try:
            destino = reverse("talleres:registrar_servicio")
        except NoReverseMatch:
            messages.info(request, f"Código {codigo}: el registro de servicios del panel aún no está disponible.")
            return redirect("/")
        return redirect(f"{destino}?codigo={hoja_vida.normalizar(codigo)}")
    messages.info(request, "Este código es para que lo escanee el taller que atiende la moto.")
    return redirect("garaje:garaje")
