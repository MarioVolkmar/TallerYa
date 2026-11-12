from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cupones.models import Cupon, Motociclista
from cupones.servicios import CuponNoDisponible, reclamar_regalo_mensual

from .forms import RegistroForm
from .models import Suscripcion

User = get_user_model()


def registro(request):
    if request.user.is_authenticated:
        return redirect("cuentas:mi_cuenta")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            usuario = User.objects.create_user(
                username=d["email"], email=d["email"], password=d["password1"], first_name=d["nombre"],
            )
            moto = form.motociclista_existente or Motociclista(celular=d["celular"], nombre=d["nombre"])
            if not moto.pk and (ref := request.session.get("ref")):
                moto.referido_por = Motociclista.objects.filter(codigo_referido=ref).first()
            moto.usuario = usuario
            moto.save()
        login(request, usuario)
        messages.success(request, f"¡Bienvenido a TallerYa, {d['nombre']}!")
        siguiente = request.GET.get("next", "")
        if url_has_allowed_host_and_scheme(siguiente, {request.get_host()}, require_https=request.is_secure()):
            return redirect(siguiente)
        return redirect("cuentas:mi_cuenta")
    return render(request, "cuentas/registro.html", {"form": form})


def motociclista_de(usuario):
    return getattr(usuario, "motociclista", None)


@login_required
def mi_cuenta(request):
    moto = motociclista_de(request.user)
    contexto = {"moto": moto}
    if moto:
        codigos = moto.codigos.select_related("cupon", "cupon__taller", "canjeado_taller")
        contexto.update({
            "disponibles": [c for c in codigos if not c.canjeado and c.cupon.vigente],
            "usados": [c for c in codigos if c.canjeado or not c.cupon.vigente][:10],
            "suscripcion": moto.suscripcion_activa,
            "solicitud": moto.suscripciones.filter(estado=Suscripcion.Estado.SOLICITADA).first(),
            "regalo": Cupon.regalo_actual(),
            "enlace_referido": request.build_absolute_uri(reverse("cupones:referido", args=[moto.codigo_referido])),
            "num_referidos": moto.referidos.count(),
        })
    if hasattr(request.user, "taller"):
        contexto["taller"] = request.user.taller
    contexto["preguntas"] = request.user.preguntas.filter(visible=True)[:5]
    return render(request, "cuentas/mi_cuenta.html", contexto)


def plus(request):
    moto = motociclista_de(request.user) if request.user.is_authenticated else None
    solicitud = moto.suscripciones.filter(estado=Suscripcion.Estado.SOLICITADA).first() if moto else None
    texto = "Hola TallerYa, quiero activar Plus."
    if moto:
        texto += f" Mi correo es {request.user.email}. Adjunto el comprobante de pago."
    return render(request, "cuentas/plus.html", {
        "moto": moto,
        "suscripcion": moto.suscripcion_activa if moto else None,
        "solicitud": solicitud,
        "precio": settings.PLUS_PRECIO_MENSUAL,
        "nequi": settings.PLUS_NEQUI,
        "dias": settings.PLUS_DIAS,
        "whatsapp_pago": f"https://wa.me/{settings.TALLERYA_WHATSAPP}?text={quote(texto)}",
        "exclusivos": Cupon.objects.disponibles().filter(solo_plus=True)[:3],
    })


@login_required
@require_POST
def solicitar_plus(request):
    moto = motociclista_de(request.user)
    if not moto:
        messages.error(request, "Tu cuenta no tiene un celular asociado. Escríbenos para ayudarte.")
        return redirect("cuentas:plus")
    if not moto.suscripciones.filter(estado=Suscripcion.Estado.SOLICITADA).exists():
        Suscripcion.objects.create(motociclista=moto)
    messages.success(request, "¡Solicitud recibida! Haz el pago y envíanos el comprobante por WhatsApp para activarte.")
    return redirect("cuentas:plus")


@login_required
@require_POST
def reclamar_regalo(request):
    moto = motociclista_de(request.user)
    if not moto:
        return redirect("cuentas:mi_cuenta")
    try:
        codigo, nuevo = reclamar_regalo_mensual(moto)
    except CuponNoDisponible as e:
        messages.error(request, str(e))
        return redirect("cuentas:mi_cuenta")
    if not nuevo:
        messages.info(request, "Ya reclamaste el regalo de este mes. Aquí está tu código.")
    return redirect(codigo)

