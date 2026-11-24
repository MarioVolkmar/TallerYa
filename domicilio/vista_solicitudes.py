"""Solicitudes de visita a domicilio: la bandeja del mecánico (cotizar, confirmar, atender, cancelar) y la página del
motero para aceptar o rechazar la cotización. Mismo flujo que las citas de los talleres (talleres/views.py)."""
from datetime import date as fecha_tipo, time, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from talleres.utils import normalizar_celular
from talleres.views import _entero_pesos, _hora_texto

from .models import SolicitudVisita

ABIERTAS = [SolicitudVisita.Estado.PENDIENTE, SolicitudVisita.Estado.COTIZADA, SolicitudVisita.Estado.CONFIRMADA]


def _notificar(usuario, clave, titulo, texto, url):
    if usuario:
        from notificaciones.servicios import notificar
        notificar(usuario, clave, titulo, texto, url)


def guardar_solicitud(request, mecanico, servicio, zona, cuando, moto, detalle):
    """Guarda la solicitud del formulario «Solicitar visita» (si trae nombre y un celular válido) y avisa al mecánico."""
    nombre = " ".join(request.POST.get("nombre", "").split())[:80]
    try:
        telefono = normalizar_celular(request.POST.get("telefono", ""))
    except Exception:
        telefono = ""
    if not nombre or not telefono:
        return None
    from .vista_descuentos import codigo_disponible
    s = SolicitudVisita.objects.create(
        mecanico=mecanico, usuario=request.user if request.user.is_authenticated else None, nombre=nombre,
        telefono=telefono, moto=moto, servicio=servicio, zona=zona, cuando=cuando[:10], detalle=detalle,
        codigo_cupon=codigo_disponible(request.user, mecanico))  # su descuento de este mecánico queda anotado
    _notificar(mecanico.usuario, f"visita-nueva:{s.pk}", f"{nombre} te pidió una visita",
               f"{servicio or 'Diagnóstico'}{' · ' + moto if moto else ''}", reverse("domicilio:solicitudes"))
    return s


def _del_mecanico(request, pk):
    from .views import _perfil_de
    mecanico = _perfil_de(request.user)
    return mecanico, get_object_or_404(SolicitudVisita, pk=pk, mecanico=mecanico) if mecanico else None


@login_required
def solicitudes(request):
    from .views import _perfil_de
    mecanico = _perfil_de(request.user)
    if not mecanico:
        return redirect("domicilio:registro")
    todas = request.GET.get("ver") == "todas"
    lista = mecanico.solicitudes.select_related("servicio", "zona", "codigo_cupon", "codigo_cupon__cupon")
    if not todas:
        lista = lista.filter(estado__in=ABIERTAS)
    hoy = timezone.localdate()
    from .views import CUANDO
    lista = list(lista[:60])
    # Las que ya tienen su servicio en la hoja de vida de la moto (garaje.vista_servicio_mecanico)
    con_servicio = set(mecanico.servicios_hechos.exclude(estado="rechazado").filter(solicitud__isnull=False)
                       .values_list("solicitud_id", flat=True))
    for s in lista:
        s.cuando_texto = dict(CUANDO).get(s.cuando, "")
        s.servicio_registrado = s.pk in con_servicio
    return render(request, "domicilio/solicitudes.html", {
        "puede_registrar": mecanico.estado == mecanico.Estado.APROBADO,
        "m": mecanico, "lista": lista, "todas": todas, "hoy": hoy,
        "horas": [f"{h:02d}:{m:02d}" for h in range(6, 21) for m in (0, 30)],
    })


@login_required
@require_POST
def solicitud_estado(request, pk):
    _, s = _del_mecanico(request, pk)
    if s is None:
        return redirect("domicilio:registro")
    nuevo = request.POST.get("estado")
    if nuevo in (SolicitudVisita.Estado.CONFIRMADA, SolicitudVisita.Estado.ATENDIDA, SolicitudVisita.Estado.CANCELADA):
        s.estado = nuevo
        s.save(update_fields=["estado"])
        if nuevo == SolicitudVisita.Estado.ATENDIDA:
            _canjear_descuento(request, s)
        elif nuevo == SolicitudVisita.Estado.CANCELADA and s.codigo_cupon_id and not s.codigo_cupon.canjeado:
            s.codigo_cupon = None  # el código vuelve a quedar libre para otra visita
            s.save(update_fields=["codigo_cupon"])
        if nuevo != SolicitudVisita.Estado.ATENDIDA:
            _notificar(s.usuario, f"visita-{nuevo}:{s.pk}", f"{s.mecanico.nombre}: visita {s.get_estado_display().lower()}",
                       "Mira los detalles", s.get_absolute_url())
        messages.success(request, f"Solicitud de {s.nombre}: {s.get_estado_display().lower()}.")
    return redirect(reverse("domicilio:solicitudes") + f"#visita-{s.pk}")


def _canjear_descuento(request, s):
    """Al marcar la visita «Atendida», el descuento anotado queda usado (cuenta en el reporte del mecánico)."""
    if not s.codigo_cupon_id or s.codigo_cupon.canjeado:
        return
    from cupones.servicios import ErrorCanje, canjear_con_mecanico
    try:
        canjear_con_mecanico(s.codigo_cupon.codigo, s.mecanico, via="visita", usuario=request.user,
                             ip=request.META.get("REMOTE_ADDR"))
    except ErrorCanje as e:
        messages.warning(request, f"El cupón {s.codigo_cupon.codigo} no se pudo validar: {e}")
    else:
        messages.info(request, f"Cupón validado: {s.codigo_cupon.cupon.titulo}.")


@login_required
@require_POST
def solicitud_descuento(request, pk):
    """El mecánico anota el código de descuento que le dio el motero (por WhatsApp o en persona) en la solicitud;
    se valida que sea suyo y esté libre, y se usa al marcar la visita «Atendida»."""
    mecanico, s = _del_mecanico(request, pk)
    if s is None:
        return redirect("domicilio:registro")
    volver = reverse("domicilio:solicitudes") + f"#visita-{s.pk}"
    if s.estado not in ABIERTAS:
        return redirect(volver)
    from cupones.servicios import ErrorCanje, revisar_para_mecanico
    try:
        codigo = revisar_para_mecanico(request.POST.get("codigo", ""), mecanico)
    except ErrorCanje as e:
        messages.error(request, str(e))
        return redirect(volver)
    if codigo.visitas.exclude(pk=s.pk).filter(estado__in=ABIERTAS).exists():
        messages.error(request, "Ese cupón ya está anotado en otra visita.")
        return redirect(volver)
    s.codigo_cupon = codigo
    s.save(update_fields=["codigo_cupon"])
    messages.success(request, f"Anotamos el cupón «{codigo.cupon.titulo}»: se usa al marcar la visita atendida.")
    return redirect(volver)


@login_required
@require_POST
def solicitud_cotizar(request, pk):
    mecanico, s = _del_mecanico(request, pk)
    if s is None:
        return redirect("domicilio:registro")
    volver = reverse("domicilio:solicitudes") + f"#visita-{s.pk}"
    desde, hasta = _entero_pesos(request.POST.get("desde")), _entero_pesos(request.POST.get("hasta"))
    if not desde or not hasta or desde > hasta:
        messages.error(request, "Escribe el precio desde y hasta (el «hasta» no puede ser menor). Si es fijo, pon el mismo en los dos.")
        return redirect(volver)
    try:
        fecha = fecha_tipo.fromisoformat(request.POST.get("fecha", ""))
        hora = time.fromisoformat(request.POST.get("hora", ""))
    except ValueError:
        fecha = hora = None
    if not fecha or not hora or fecha < timezone.localdate():
        messages.error(request, "Elige la fecha (de hoy en adelante) y la hora de la visita.")
        return redirect(volver)
    dias = request.POST.get("vigencia", "5")
    dias = int(dias) if dias.isdigit() and 1 <= int(dias) <= 30 else 5
    s.cotizacion_desde, s.cotizacion_hasta = desde, hasta
    s.cotizacion_incluye = request.POST.get("incluye", "").strip()[:160]
    s.cotizacion_vence = timezone.localdate() + timedelta(days=dias)
    s.fecha_propuesta, s.hora_propuesta = fecha, hora
    s.nota = request.POST.get("nota", "").strip()[:200]
    s.estado, s.rechazada = SolicitudVisita.Estado.COTIZADA, False
    s.save()
    _notificar(s.usuario, f"visita-cotizada:{s.pk}:{desde}:{hasta}:{fecha}:{hora}", f"{mecanico.nombre} te cotizó la visita",
               f"{s.precio_texto} · {fecha:%d/%m} · {_hora_texto(hora)}. Acéptala o recházala.", s.get_absolute_url())
    from garaje.whatsapp import enviar_plantilla
    enviar_plantilla(s.telefono, getattr(settings, "WHATSAPP_PLANTILLA_VISITA_COTIZADA", "visita_cotizada"),
                     [s.nombre, mecanico.nombre, s.precio_texto, fecha.strftime("%d/%m"), _hora_texto(hora),
                      request.build_absolute_uri(s.get_absolute_url())])
    messages.success(request, f"Le enviamos la cotización a {s.nombre}. Te avisaremos cuando responda.")
    return redirect(volver)


def visita_publica(request, token):
    """Página del motero: ve su solicitud y acepta o rechaza la cotización (no necesita cuenta)."""
    s = get_object_or_404(SolicitudVisita.objects.select_related("mecanico", "servicio", "zona", "codigo_cupon__cupon"),
                          token=token)
    pendiente = s.estado == SolicitudVisita.Estado.COTIZADA
    if request.method == "POST" and pendiente:
        dueno = s.mecanico.usuario
        if request.POST.get("accion") == "aceptar" and s.cotizacion_vencida:
            messages.error(request, "Esta cotización ya venció. Escríbele al mecánico para que te envíe una nueva.")
        elif request.POST.get("accion") == "aceptar":
            s.estado = SolicitudVisita.Estado.CONFIRMADA
            s.save(update_fields=["estado"])
            _notificar(dueno, f"visita-aceptada:{s.pk}", f"{s.nombre} aceptó tu cotización",
                       f"Visita el {s.fecha_propuesta:%d/%m}", reverse("domicilio:solicitudes"))
            messages.success(request, "¡Listo! La visita quedó confirmada con ese precio.")
        else:
            s.estado, s.rechazada = SolicitudVisita.Estado.PENDIENTE, True
            s.save(update_fields=["estado", "rechazada"])
            _notificar(dueno, f"visita-rechazada:{s.pk}", f"{s.nombre} no aceptó tu cotización",
                       "Escríbele para acordar otra opción", reverse("domicilio:solicitudes"))
            messages.info(request, "Le avisamos al mecánico. Te escribirá si tiene otra opción.")
        return redirect(s.get_absolute_url())
    return render(request, "domicilio/visita_publica.html", {"s": s, "pendiente": pendiente,
                                                             "hora": _hora_texto(s.hora_propuesta)})
