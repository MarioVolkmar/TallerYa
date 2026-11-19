"""Vistas de la hoja de vida: la del dueño, la pública (por enlace) y la entrada del QR para el taller."""
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from . import hoja_vida, qr, traspaso as traspasos
from logros.reglas import INSIGNIAS

from .forms_hoja_vida import RegistroPropioForm
from .models import EnlaceHojaVida
from .views import MAX_MOTOS, _moto_de, con_motociclista


@con_motociclista
def hoja_vida_moto(request, pk):
    moto = _moto_de(request, pk)
    form = RegistroPropioForm(moto=moto)
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "agregar":
            form = RegistroPropioForm(request.POST, moto=moto)
            if form.is_valid():
                hoja_vida.registrar_propio(moto, form.save(commit=False), form.cleaned_data.get("tarea"))
                messages.success(request, "Servicio agregado a la hoja de vida.")
                return redirect("garaje:hoja_vida", moto.pk)
        elif accion == "codigo":
            # "Mostrar código" de un registro pendiente (o solo_si_falta): reutiliza el vigente y lo liga a ese registro;
            # "Generar otro" sí crea uno nuevo.
            pendiente = moto.hoja_vida.filter(pk=request.POST.get("registro") or 0, verificado=False,
                                              taller__isnull=False).first()
            if pendiente or request.POST.get("solo_si_falta"):
                hoja_vida.codigo_para(moto, pendiente)
            else:
                hoja_vida.generar_codigo(moto)
            return redirect(reverse("garaje:hoja_vida", args=[moto.pk]) + "#codigo")
        elif accion == "compartir":
            hoja_vida.crear_enlace(moto)
            return redirect(reverse("garaje:hoja_vida", args=[moto.pk]) + "#compartir")
        elif accion == "revocar":
            hoja_vida.revocar_enlaces(moto)
            messages.success(request, "Listo: el enlace dejó de funcionar.")
            return redirect(reverse("garaje:hoja_vida", args=[moto.pk]) + "#compartir")
        elif accion == "vender":
            motivo = traspasos.bloqueo(moto)
            if motivo:
                messages.error(request, motivo)
            else:
                traspasos.crear(moto, request.user)
            return redirect(reverse("garaje:hoja_vida", args=[moto.pk]) + "#vender")
        elif accion == "cancelar_traspaso":
            traspasos.cancelar(moto)
            messages.success(request, "Listo: el enlace de traspaso dejó de funcionar.")
            return redirect(reverse("garaje:hoja_vida", args=[moto.pk]) + "#vender")
        elif accion == "eliminar":
            # Solo los propios: lo verificado por un taller no se borra desde aquí.
            # Si venía del plan, también se quita del plan (es el mismo mantenimiento).
            if hoja_vida.eliminar_propio(moto, request.POST.get("registro")):
                messages.success(request, "Registro eliminado.")
            return redirect("garaje:hoja_vida", moto.pk)

    registros = list(moto.hoja_vida.select_related("taller", "mecanico"))
    codigo = hoja_vida.codigo_vigente(moto)
    enlace = hoja_vida.enlace_activo(moto)
    contexto = {"moto": moto, "registros": registros, "form": form, "resumen": hoja_vida.resumen(registros),
                "codigo": codigo, "enlace": enlace, "minutos_codigo": hoja_vida.MINUTOS_CODIGO}
    if codigo:
        contexto["qr_codigo"] = mark_safe(qr.svg(request.build_absolute_uri(
            reverse("garaje:servicio_codigo", args=[codigo.codigo])), "QR del código para el taller"))
    traspaso = traspasos.vigente(moto)
    # Técnico-mecánica: dato privado del dueño (no sale en la página pública, el certificado ni el traspaso)
    contexto["tecno"] = next((d for d in moto.documentos() if d["clave"] == "tecno"), None)
    contexto.update({"traspaso": traspaso, "dias_traspaso": traspasos.DIAS_TRASPASO,
                     "gastos_total": moto.gastos.count()})
    if traspaso:
        contexto["url_traspaso"] = request.build_absolute_uri(traspaso.get_absolute_url())
        contexto["qr_traspaso"] = mark_safe(qr.svg(contexto["url_traspaso"], "QR para recibir la moto"))
    if enlace:
        contexto["url_enlace"] = request.build_absolute_uri(enlace.get_absolute_url())
        contexto["qr_enlace"] = mark_safe(qr.svg(contexto["url_enlace"], "QR de la hoja de vida"))
    return render(request, "garaje/hoja_vida.html", contexto)


@con_motociclista
@require_POST
def codigo_taller(request, pk):
    """Código de taller para mostrar ya mismo (aviso del despiece): reutiliza el vigente; JSON con QR y vencimiento."""
    moto = _moto_de(request, pk)
    # registro: "Mostrar código" de un pendiente → el código queda ligado a ese registro (se verifica ese mismo)
    pendiente = moto.hoja_vida.filter(pk=request.POST.get("registro") or 0, verificado=False, taller__isnull=False).first()
    if request.POST.get("nuevo"):
        codigo = hoja_vida.generar_codigo(moto, pendiente)
    else:
        codigo = hoja_vida.codigo_para(moto, pendiente)
    vence = timezone.localtime(codigo.vence)
    return JsonResponse({
        "codigo": codigo.codigo, "vence": vence.isoformat(),
        "vence_texto": date_format(vence, "g:i a").replace("a.m.", "a. m.").replace("p.m.", "p. m."),
        "qr": qr.svg(request.build_absolute_uri(reverse("garaje:servicio_codigo", args=[codigo.codigo])),
                     "QR del código para el taller"),
        "puntos": INSIGNIAS["servicio"].puntos,
    })


def hoja_vida_publica(request, token):
    enlace = get_object_or_404(EnlaceHojaVida.objects.select_related("moto", "moto__linea", "moto__linea__marca"),
                               token=token, revocado__isnull=True)
    moto = enlace.moto
    registros = list(moto.hoja_vida.select_related("taller", "mecanico"))
    url = request.build_absolute_uri()
    respuesta = render(request, "garaje/hoja_vida_publica.html", {
        "papeles": papeles_al_dia(moto), "moto": moto, "registros": registros, "resumen": hoja_vida.resumen(registros),
        "placa": hoja_vida.placa_enmascarada(moto.placa), "qr": mark_safe(qr.svg(url, "QR de esta hoja de vida")),
    })
    respuesta["X-Robots-Tag"] = "noindex, nofollow"
    respuesta["Referrer-Policy"] = "no-referrer"
    return respuesta


def papeles_al_dia(moto, hoy=None):
    """Vigencia del SOAT y la técnico-mecánica para lo compartido: solo la fecha registrada y si sigue vigente.
    Sin fecha no hay línea (nada de «sin dato»); los archivos y los pedidos de SOAT siguen privados."""
    hoy = hoy or timezone.localdate()
    lista = []
    for nombre, vence in (("SOAT", moto.soat_vence), ("Técnico-mecánica", moto.tecno_vence)):
        if vence:
            lista.append({"nombre": nombre, "vence": vence, "vigente": vence >= hoy})
    return lista


def _sin_rastro(respuesta):
    respuesta["X-Robots-Tag"] = "noindex, nofollow"
    respuesta["Referrer-Policy"] = "no-referrer"
    return respuesta


def hoja_vida_certificado(request, token):
    """Certificado imprimible (o PDF con «Guardar como PDF» del navegador) de la hoja de vida pública.
    Mismos datos que la página pública: sin dueño, sin costos y con la placa enmascarada."""
    enlace = get_object_or_404(EnlaceHojaVida.objects.select_related("moto", "moto__linea", "moto__linea__marca"),
                               token=token, revocado__isnull=True)
    moto = enlace.moto
    registros = list(moto.hoja_vida.select_related("taller", "mecanico"))
    url = request.build_absolute_uri(enlace.get_absolute_url())
    return _sin_rastro(render(request, "garaje/hoja_vida_certificado.html", {
        "papeles": papeles_al_dia(moto),
        "moto": moto, "registros": registros, "resumen": hoja_vida.resumen(registros), "url_publica": url,
        "placa": hoja_vida.placa_enmascarada(moto.placa), "emitido": timezone.localtime(),
        "marca": moto.linea.marca.nombre if moto.linea else moto.marca_otra,
        "qr": mark_safe(qr.svg(url, "QR para comprobar esta hoja de vida en TallerYa")),
    }))


def traspaso(request, token):
    """Lo que abre quien compra la moto: ve qué recibe y acepta con su sesión iniciada."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    pendiente = traspasos.buscar(token)
    if request.method == "POST" and pendiente:
        try:
            moto = traspasos.aceptar(token, request.user, MAX_MOTOS)
        except traspasos.TraspasoInvalido as e:
            messages.error(request, str(e))
            return redirect("garaje:traspaso", token)
        messages.success(request, f"Listo: tu {moto.nombre_completo} ya está en tu garaje con su hoja de vida.")
        return redirect("garaje:hoja_vida", moto.pk)
    contexto = {"traspaso": pendiente}
    if pendiente:
        moto = pendiente.moto
        registros = list(moto.hoja_vida.select_related("taller", "mecanico"))
        perfil = getattr(request.user, "motociclista", None)
        contexto.update({
            "moto": moto, "registros": registros, "resumen": hoja_vida.resumen(registros),
            "placa": hoja_vida.placa_enmascarada(moto.placa),
            "propia": perfil is not None and moto.motociclista_id == perfil.pk,
            "sin_perfil": perfil is None,
            "lleno": perfil is not None and perfil.motos.count() >= MAX_MOTOS, "max_motos": MAX_MOTOS,
        })
    return _sin_rastro(render(request, "garaje/traspaso.html", contexto, status=200 if pendiente else 410))


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
