from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CanjeForm, ObtenerCuponForm
from .models import CodigoCupon, Cupon, Motociclista
from .servicios import (CuponNoDisponible, ErrorCanje, RequierePlus, buscar_codigo, canjear, obtener_codigo,
                        obtener_codigo_para)

SESION_REF = "ref"
MAX_INTENTOS_CANJE = 8
BLOQUEO_SEGUNDOS = 15 * 60


def _por_puntos(cupones, puntos):
    """Cupones canjeables con puntos de insignias, del más barato al más caro, con cuántos puntos le faltan al usuario."""
    lista = sorted((c for c in cupones if c.puntos_logros), key=lambda c: c.puntos_logros)
    for c in lista:
        c.faltan = max(c.puntos_logros - puntos, 0) if puntos is not None else 0
    return lista


def lista(request):
    cupones = Cupon.objects.disponibles().con_nota_taller()
    puntos = None
    if request.user.is_authenticated:
        from logros.reglas import puntos_disponibles
        puntos = puntos_disponibles(request.user)
    return render(request, "cupones/lista.html", {
        "cupones": cupones,
        # Los que también se pueden canjear con los puntos de las insignias, del más barato al más caro
        "por_puntos": _por_puntos(cupones, puntos),
        "mis_puntos": puntos,
        "invitado": SESION_REF in request.session,
    })


def obtener(request, pk):
    cupon = get_object_or_404(Cupon.objects.disponibles().con_nota_taller(), pk=pk)
    moto = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None

    if cupon.solo_plus and not moto:
        messages.info(request, "Este cupón es exclusivo de TallerYa Plus. Entra o crea tu cuenta para obtenerlo.")
        return redirect_to_login(request.get_full_path())

    form = ObtenerCuponForm(request.POST or None)
    if request.method == "POST" and (moto or form.is_valid()):
        try:
            if moto:
                codigo, nuevo = obtener_codigo_para(moto, cupon)
            else:
                celular = form.cleaned_data["celular"]
                if Motociclista.objects.filter(celular=celular, usuario__isnull=False).exists():
                    messages.info(request, "Ese celular tiene una cuenta en TallerYa. Entra para obtener tu cupón.")
                    return redirect_to_login(request.get_full_path())
                codigo, nuevo = obtener_codigo(
                    cupon, form.cleaned_data["nombre"], celular, ref=request.session.get(SESION_REF),
                )
        except RequierePlus as e:
            messages.info(request, str(e))
            return redirect("cuentas:plus")
        except CuponNoDisponible as e:
            messages.error(request, str(e))
            return redirect("cupones:lista")
        if not nuevo:
            messages.info(request, "Ya tenías este cupón. Aquí está tu código.")
        return redirect(codigo)
    return render(request, "cupones/obtener.html", {"cupon": cupon, "form": form, "moto": moto})


def mi_cupon(request, codigo):
    codigo = get_object_or_404(
        CodigoCupon.objects.select_related("cupon", "cupon__taller", "cupon__taller__barrio", "motociclista", "canjeado_taller"),
        codigo=codigo,
    )
    moto = codigo.motociclista
    enlace = request.build_absolute_uri(reverse("cupones:referido", args=[moto.codigo_referido]))
    texto = f"Te regalo cupones para el taller de tu moto en TallerYa: {enlace}"
    return render(request, "cupones/mi_cupon.html", {
        "codigo": codigo,
        "url_canje": request.build_absolute_uri(reverse("cupones:canjear")) + "?codigo=" + codigo.codigo,
        "moto": moto,
        "enlace_referido": enlace,
        "whatsapp_compartir": f"https://wa.me/?text={quote(texto)}",
        "invitacion_whatsapp": texto,
        "premios": moto.codigos.filter(origen__in=[CodigoCupon.Origen.PREMIO, CodigoCupon.Origen.REGALO]).select_related("cupon").exclude(pk=codigo.pk),
        "num_referidos": moto.referidos.count(),
    })


def referido(request, codigo):
    if Motociclista.objects.filter(codigo_referido=codigo.upper()).exists():
        request.session[SESION_REF] = codigo.upper()
        messages.info(request, "¡Un amigo te invitó! Elige un cupón para tu moto.")
    return redirect("cupones:lista")


def _ip(request):
    return request.META.get("REMOTE_ADDR", "desconocida")


def canjear_cupon(request):
    """Canje de cupones. Con la sesión del taller abierta no pide PIN. Al escanear el QR llega ?codigo=... y se
    muestra una vista previa del cupón antes de canjearlo."""
    taller = getattr(request.user, "taller", None) if request.user.is_authenticated else None
    if taller and not taller.activo:
        taller = None
    inicial = {"codigo": request.GET.get("codigo", "")}
    form = CanjeForm(request.POST or None, initial=inicial)
    clave = f"canje-intentos:{_ip(request)}"
    bloqueado = cache.get(clave, 0) >= MAX_INTENTOS_CANJE
    resultado, vista = None, None

    if request.method == "POST" and bloqueado:
        form.is_valid()
        form.add_error(None, "Demasiados intentos fallidos. Espera 15 minutos e inténtalo de nuevo.")
    elif request.method == "POST" and form.is_valid():
        if not taller and not form.cleaned_data.get("pin"):
            form.add_error("pin", "Escribe el PIN de tu taller (o entra con la cuenta del taller).")
        else:
            try:
                resultado = canjear(form.cleaned_data["codigo"], form.cleaned_data.get("pin"), taller=taller)
            except ErrorCanje as e:
                cache.set(clave, cache.get(clave, 0) + 1, BLOQUEO_SEGUNDOS)
                form.add_error(None, str(e))
            else:
                form = CanjeForm()
    elif request.method == "GET" and inicial["codigo"]:
        try:
            vista = buscar_codigo(inicial["codigo"])
            vista.otro_taller = bool(taller and not vista.valido_en(taller))
        except ErrorCanje as e:
            form.add_error(None, str(e))

    return render(request, "cupones/canjear.html", {"form": form, "resultado": resultado, "vista": vista, "taller": taller})
