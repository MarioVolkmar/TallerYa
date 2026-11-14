"""Agenda con franjas: horarios libres de un taller y reserva sin dobles (control de concurrencia)."""
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Count, F
from django.utils import timezone

from .models import HorarioTaller, SolicitudCita, Taller

# Estados que ocupan cupo en la franja
OCUPAN = [SolicitudCita.Estado.PENDIENTE, SolicitudCita.Estado.REPROGRAMADA, SolicitudCita.Estado.CONFIRMADA]
DIAS_ADELANTE = 30


class FranjaOcupada(Exception):
    pass


def horas_del_dia(taller, fecha, turnos=None):
    """Inicio de cada franja según los turnos de ese día de la semana (la franja debe caber antes del cierre)."""
    if turnos is None:
        turnos = taller.horarios.filter(dia=fecha.weekday())
    paso = timedelta(minutes=taller.duracion_franja)
    horas = []
    for t in turnos:
        if t.dia != fecha.weekday():
            continue
        inicio, fin = datetime.combine(fecha, t.abre), datetime.combine(fecha, t.cierra)
        while inicio + paso <= fin:
            horas.append(inicio.time())
            inicio += paso
    return sorted(set(horas))


def ocupadas(taller, fecha):
    filas = (SolicitudCita.objects.filter(taller=taller, fecha_preferida=fecha, hora__isnull=False, estado__in=OCUPAN)
             .values("hora").annotate(n=Count("pk")).order_by())
    return {f["hora"]: f["n"] for f in filas}


def franjas_libres(taller, fecha, turnos=None):
    """[(hora, cupos_libres)] para esa fecha; sin horas pasadas ni fechas fuera de rango."""
    hoy = timezone.localdate()
    if fecha < hoy or fecha > hoy + timedelta(days=DIAS_ADELANTE):
        return []
    horas = horas_del_dia(taller, fecha, turnos)
    if not horas:
        return []
    if fecha == hoy:
        ahora = timezone.localtime().time()
        horas = [h for h in horas if h > ahora]
    uso = ocupadas(taller, fecha)
    return [(h, taller.cupo_franja - uso.get(h, 0)) for h in horas if uso.get(h, 0) < taller.cupo_franja]


def proxima_fecha_libre(taller):
    """Primer día con alguna franja libre (para prellenar el formulario). Los turnos se leen una sola vez."""
    turnos = list(taller.horarios.all())
    if not turnos:
        return None
    dias = {t.dia for t in turnos}
    hoy = timezone.localdate()
    for n in range(DIAS_ADELANTE + 1):
        fecha = hoy + timedelta(days=n)
        if fecha.weekday() in dias and franjas_libres(taller, fecha, turnos):
            return fecha
    return None


def reservar(cita):
    """Guarda la cita si su franja aún tiene cupo. Bloquea la fila del taller durante la transacción para que
    dos reservas simultáneas no pasen ambas el conteo (en PostgreSQL bloquea la fila; en SQLite toma el candado
    de escritura). Lanza FranjaOcupada si ya no hay cupo."""
    taller = cita.taller
    with transaction.atomic():
        # El UPDATE "vacío" toma el candado antes de contar.
        Taller.objects.filter(pk=taller.pk).update(cupo_franja=F("cupo_franja"))
        cupo = Taller.objects.select_for_update().values_list("cupo_franja", flat=True).get(pk=taller.pk)
        if cita.hora not in horas_del_dia(taller, cita.fecha_preferida):
            raise FranjaOcupada("Ese horario no está en la agenda del taller.")
        if ocupadas(taller, cita.fecha_preferida).get(cita.hora, 0) >= cupo:
            raise FranjaOcupada("Alguien acaba de reservar ese horario. Elige otro.")
        cita.save()
    return cita


def turnos_por_dia(taller):
    """{dia: [turno, ...]} para mostrar y editar el horario."""
    datos = {}
    for t in taller.horarios.all():
        datos.setdefault(t.dia, []).append(t)
    return datos


def guardar_turnos(taller, turnos):
    """Reemplaza el horario: turnos = [(dia, abre, cierra), ...]."""
    with transaction.atomic():
        taller.horarios.all().delete()
        HorarioTaller.objects.bulk_create([HorarioTaller(taller=taller, dia=d, abre=a, cierra=c) for d, a, c in turnos])
