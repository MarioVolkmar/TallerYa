"""Citas del motero con talleres: lista en Mi cuenta, detalle, cancelar y archivo de calendario (.ics).

El modelo y la agenda son de la app talleres (solo lectura aquí). Para avisar al taller se reutiliza su _avisar.
"""
from datetime import datetime, time, timedelta
from datetime import timezone as zona
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from talleres.models import SolicitudCita

ACTIVAS = (SolicitudCita.Estado.PENDIENTE, SolicitudCita.Estado.CONFIRMADA, SolicitudCita.Estado.REPROGRAMADA)
CANCELABLES = (SolicitudCita.Estado.PENDIENTE, SolicitudCita.Estado.CONFIRMADA, SolicitudCita.Estado.REPROGRAMADA)
DURACION = timedelta(hours=1)


def _base(usuario):
    return (SolicitudCita.objects.filter(usuario=usuario)
            .select_related("taller", "taller__barrio", "taller__usuario__perfil", "servicio"))


def _iniciales(taller):
    palabras = [w for w in taller.nombre.split() if len(w) > 2] or taller.nombre.split()
    return "".join(w[0] for w in palabras[:2]).upper()


def _preparar(citas):
    for c in citas:
        c.taller.iniciales = _iniciales(c.taller)
        c.taller.tono = (c.taller.pk * 47) % 360
    return citas


def _visitas(usuario):
    """Visitas a domicilio que el motero pidió con su cuenta (van en la misma lista que las citas)."""
    from domicilio.models import SolicitudVisita
    from talleres.negocio import estado_texto
    visitas = list(SolicitudVisita.objects.filter(usuario=usuario).select_related("mecanico", "servicio"))
    for v in visitas:
        v.es_visita = True
        v.fecha_orden = v.fecha_propuesta or timezone.localtime(v.creado).date()
        v.hora = v.hora_propuesta
        v.estado_texto = estado_texto(v)
        v.mecanico.tono = (v.mecanico.pk * 47 + 180) % 360
    return visitas


def citas_de(usuario):
    """Para Mi cuenta: próximas (de la más cercana a la más lejana) y anteriores (atendidas, canceladas o pasadas).
    Incluye las visitas a domicilio: es el mismo camino (pedir → confirmar → atender → calificar)."""
    from domicilio.models import SolicitudVisita
    hoy = timezone.localdate()
    citas = _preparar(list(_base(usuario)))
    for c in citas:
        c.fecha_orden = c.fecha_preferida
    abiertas_visita = (SolicitudVisita.Estado.PENDIENTE, SolicitudVisita.Estado.COTIZADA, SolicitudVisita.Estado.CONFIRMADA)
    todas = citas + _visitas(usuario)

    def activa(c):
        if getattr(c, "es_visita", False):
            return c.estado in abiertas_visita and c.fecha_orden >= hoy - timedelta(days=0 if c.fecha_propuesta else 30)
        return c.estado in ACTIVAS and c.fecha_preferida >= hoy

    clave = lambda c: (c.fecha_orden, c.hora or time.min)  # noqa: E731
    proximas = sorted((c for c in todas if activa(c)), key=clave)
    anteriores = sorted((c for c in todas if not activa(c)), key=clave, reverse=True)[:20]
    from talleres.ciclo import en_curso
    return {"citas_proximas": proximas, "citas_anteriores": anteriores, "en_curso": en_curso(usuario)}


def _whatsapp(cita):
    numero = "".join(ch for ch in cita.taller.whatsapp if ch.isdigit())
    if not numero:
        return ""
    texto = (f"Hola {cita.taller.nombre}, soy {cita.nombre}. Te escribo por mi cita del "
             f"{cita.fecha_preferida:%d/%m}{f' a las {cita.hora:%I:%M %p}' if cita.hora else ''} (vía TallerYa).")
    return f"https://wa.me/{numero}?text={quote(texto)}"


@login_required
def detalle(request, pk):
    cita = get_object_or_404(_base(request.user), pk=pk)
    _preparar([cita])
    t = cita.taller
    lugar = quote(f"{t.nombre}, {t.direccion}, {t.barrio}, Antioquia, Colombia")
    destino = f"{t.latitud},{t.longitud}" if t.latitud and t.longitud else lugar
    from talleres.ciclo import estado as estado_ciclo
    from talleres.views import _pesos
    precio = ""
    if cita.cotizacion_hasta:
        d, h = cita.cotizacion_desde, cita.cotizacion_hasta
        precio = _pesos(h) if d == h else f"{_pesos(d)} a {_pesos(h)}"
    return render(request, "cuentas/cita_detalle.html", {
        "cita": cita, "ciclo": estado_ciclo(cita, request.user), "precio": precio,
        "cancelable": cita.estado in CANCELABLES,
        "whatsapp": _whatsapp(cita),
        "mapa_url": f"https://www.google.com/maps?q={destino}&output=embed",
        "como_llegar": f"https://www.google.com/maps/dir/?api=1&destination={destino}",
    })


@login_required
@require_POST
def cancelar(request, pk):
    """El motero cancela: queda el motivo y se avisa al taller (misma notificación que usa la app talleres)."""
    cita = get_object_or_404(_base(request.user), pk=pk)
    volver = reverse("cuentas:cita", args=[cita.pk])
    if cita.estado not in CANCELABLES:
        messages.info(request, "Esta cita ya no se puede cancelar.")
        return redirect(volver)
    motivo = request.POST.get("motivo", "").strip()[:150]
    cita.estado = SolicitudCita.Estado.CANCELADA
    cita.motivo_cancelacion = f"Cancelada por el motero{': ' + motivo if motivo else ''}"[:200]
    cita.save(update_fields=["estado", "motivo_cancelacion"])
    if cita.taller.usuario:
        from talleres.views import _avisar
        _avisar(cita.taller.usuario, f"cita-cancelada-motero:{cita.pk}", f"{cita.nombre} canceló su cita",
                f"{cita.fecha_preferida:%d/%m}{' · ' + motivo if motivo else ''}", reverse("talleres:citas_taller"))
    messages.success(request, f"Cancelaste tu cita con {cita.taller.nombre}. Le avisamos al taller.")
    return redirect(volver)


def _ics_texto(valor):
    return str(valor).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


@login_required
def ics(request, pk):
    """Archivo de calendario con la cita (hora acordada; sin hora, evento de todo el día)."""
    cita = get_object_or_404(_base(request.user), pk=pk)
    t = cita.taller
    ahora = timezone.now().strftime("%Y%m%dT%H%M%SZ")
    if cita.hora:
        inicio = timezone.make_aware(datetime.combine(cita.fecha_preferida, cita.hora))
        fin = inicio + DURACION
        utc = lambda d: d.astimezone(zona.utc).strftime("%Y%m%dT%H%M%SZ")  # noqa: E731
        fechas = [f"DTSTART:{utc(inicio)}", f"DTEND:{utc(fin)}"]
    else:
        fechas = [f"DTSTART;VALUE=DATE:{cita.fecha_preferida:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{cita.fecha_preferida + timedelta(days=1):%Y%m%d}"]
    resumen = f"Cita en {t.nombre}" + (f" · {cita.servicio}" if cita.servicio else "")
    descripcion = f"Moto: {cita.moto}. " + (f"Nota: {cita.detalle}. " if cita.detalle else "") + "Agendada en TallerYa."
    lineas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//TallerYa//Citas//ES", "CALSCALE:GREGORIAN", "BEGIN:VEVENT",
              f"UID:cita-{cita.pk}@tallerya", f"DTSTAMP:{ahora}", *fechas,
              f"SUMMARY:{_ics_texto(resumen)}", f"LOCATION:{_ics_texto(f'{t.direccion}, {t.barrio}')}",
              f"DESCRIPTION:{_ics_texto(descripcion)}", "END:VEVENT", "END:VCALENDAR"]
    respuesta = HttpResponse("\r\n".join(lineas) + "\r\n", content_type="text/calendar; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="cita-tallerya-{cita.pk}.ics"'
    return respuesta
