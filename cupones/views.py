from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from metricas.nucleo import registrar_evento

from .forms import CanjeForm, ObtenerCuponForm
from .models import CodigoCupon, Cupon, Motociclista
from consola.ajustes import ajuste
from .servicios import (CuponNoDisponible, ErrorCanje, RequierePlus, RequiereVerificacion, buscar_codigo, canjear, obtener_codigo,
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


def _filtros_lista(request, cupones):
    """Filtros de la página de descuentos: tipo (talleres / a domicilio), servicio y barrio del taller o zona del
    mecánico. Los servicios de talleres y mecánicos son listas distintas: se comparan por nombre."""
    from domicilio.models import TipoServicio, Zona
    from talleres.models import Barrio, Servicio
    g = request.GET
    tipo = g.get("tipo") if g.get("tipo") in ("talleres", "domicilio") else ""
    servicio = g.get("servicio", "")[:80]
    donde = g.get("donde", "")
    if tipo == "talleres":
        cupones = cupones.filter(mecanico__isnull=True)
    elif tipo == "domicilio":
        cupones = cupones.filter(mecanico__isnull=False)
    nombres = sorted(set(Servicio.objects.values_list("nombre", flat=True)) | set(TipoServicio.objects.values_list("nombre", flat=True)))
    if servicio in nombres:
        cupones = cupones.filter(Q(taller__servicios__nombre=servicio) | Q(mecanico__servicios__nombre=servicio)).distinct()
    else:
        servicio = ""
    barrios = list(Barrio.objects.filter(talleres__activo=True).distinct().order_by("ciudad", "nombre"))
    zonas = list(Zona.objects.filter(mecanicos__estado="aprobado").distinct().order_by("orden", "nombre"))
    clase, _, pk = donde.partition("-")
    if clase == "b" and pk.isdigit():
        cupones = cupones.filter(taller__barrio_id=int(pk))
    elif clase == "z" and pk.isdigit():
        cupones = cupones.filter(mecanico__zonas=int(pk))
    else:
        donde = ""
    barrios = [(f"b-{b.pk}", b.nombre if b.ciudad == "Medellín" else f"{b.nombre} ({b.ciudad})") for b in barrios]
    zonas = [(f"z-{z.pk}", z.nombre) for z in zonas]
    return cupones, {"tipo": tipo, "servicio": servicio, "donde": donde, "servicios": nombres, "barrios": barrios,
                     "zonas": zonas, "filtrando": bool(tipo or servicio or donde),
                     "hay_domicilio": Cupon.objects.disponibles().filter(mecanico__isnull=False).exists()}


def lista(request):
    todos = Cupon.objects.disponibles().con_nota_taller()
    cupones, filtros = _filtros_lista(request, todos)
    puntos = None
    if request.user.is_authenticated:
        from logros.reglas import puntos_disponibles
        puntos = puntos_disponibles(request.user)
    return render(request, "cupones/lista.html", {
        "cupones": cupones,
        # Los que también se pueden canjear con los puntos de las insignias, del más barato al más caro
        "por_puntos": _por_puntos(todos, puntos),
        "f": filtros,
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
            return redirect("cuentas:plus" if ajuste("plus_activo") else "cupones:lista")
        except RequiereVerificacion as e:
            messages.info(request, str(e))
            return redirect("domiciliarios:verificacion")
        except CuponNoDisponible as e:
            messages.error(request, str(e))
            return redirect("cupones:lista")
        if not nuevo:
            messages.info(request, "Ya tenías este cupón. Aquí está tu código.")
        else:
            registrar_evento(request, "cupon_obtenido", cupon=cupon.pk)
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
    from cuentas.limites import ip_cliente  # detrás del proxy de Render, REMOTE_ADDR es la misma para todos
    return ip_cliente(request)


COOKIE_TALLER = "taller_canje"  # el taller elegido para el PIN se recuerda en este dispositivo (firmado, 180 días)


def canjear_cupon(request):
    """Canje de cupones. Con la sesión del taller abierta no pide PIN. Sin sesión: el taller elegido (o el del enlace
    /canjear/?taller=<slug>) y su PIN. Al escanear el QR llega ?codigo=... y se muestra una vista previa."""
    taller = getattr(request.user, "taller", None) if request.user.is_authenticated else None
    if taller and not taller.activo:
        taller = None
    recordado = request.GET.get("taller") or request.get_signed_cookie(COOKIE_TALLER, default="", salt=COOKIE_TALLER)
    inicial = {"codigo": request.GET.get("codigo", ""), "taller": recordado}
    form = CanjeForm(request.POST or None, initial=inicial)
    clave = f"canje-intentos:{_ip(request)}"
    bloqueado = cache.get(clave, 0) >= MAX_INTENTOS_CANJE
    resultado, vista = None, None

    if request.method == "POST" and bloqueado:
        form.is_valid()
        form.add_error(None, "Demasiados intentos fallidos. Espera 15 minutos e inténtalo de nuevo.")
    elif request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        if not taller and not d.get("pin"):
            form.add_error("pin", "Escribe el PIN de tu taller (o entra con la cuenta del taller).")
        else:
            try:
                resultado = canjear(d["codigo"], d.get("pin"), taller=taller, taller_elegido=d.get("taller"),
                                    usuario=request.user, ip=_ip(request))
            except ErrorCanje as e:
                cache.set(clave, cache.get(clave, 0) + 1, BLOQUEO_SEGUNDOS)
                form.add_error(None, str(e))
            else:
                registrar_evento(request, "cupon_canjeado", con_sesion=bool(taller))
                form = CanjeForm(initial={"taller": d.get("taller").slug if d.get("taller") else ""})
    elif request.method == "GET" and inicial["codigo"]:
        form.cleaned_data = {}  # formulario sin enviar: add_error lo necesita (antes, un código malo daba error 500)
        if bloqueado:  # la vista previa también cuenta: sin freno, servía para adivinar códigos válidos
            form.add_error(None, "Demasiados intentos fallidos. Espera 15 minutos e inténtalo de nuevo.")
        else:
            try:
                vista = buscar_codigo(inicial["codigo"])
                vista.otro_taller = bool(taller and not vista.valido_en(taller))
            except ErrorCanje as e:
                cache.set(clave, cache.get(clave, 0) + 1, BLOQUEO_SEGUNDOS)
                form.add_error(None, str(e))

    respuesta = render(request, "cupones/canjear.html", {"form": form, "resultado": resultado, "vista": vista,
                                                         "taller": taller})
    if resultado and resultado.canje_via == "pin":
        respuesta.set_signed_cookie(COOKIE_TALLER, resultado.canjeado_taller.slug, salt=COOKIE_TALLER,
                                    max_age=180 * 24 * 3600, httponly=True, samesite="Lax",
                                    secure=request.is_secure())
    return respuesta
