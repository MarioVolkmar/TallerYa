"""Emergencias: qué talleres están abiertos ahora según su horario (HorarioTaller) o porque abren 24 h."""
from django.utils import timezone


def abierto_ahora(taller, ahora=None, turnos=None):
    """True / False según el horario; None si el taller no ha registrado horario (no se sabe).
    `turnos` evita otra consulta cuando los horarios vienen precargados (prefetch_related("horarios"))."""
    if taller.abierto_24h:
        return True
    ahora = ahora or timezone.localtime()
    turnos = list(taller.horarios.all()) if turnos is None else turnos
    if not turnos:
        return None
    dia, hora = ahora.weekday(), ahora.time()
    return any(t.dia == dia and t.abre <= hora < t.cierra for t in turnos)


def ordenar_por_barrio(talleres, barrio):
    """Sin ubicación del navegador: primero los del barrio elegido, luego los de su ciudad y después el resto."""
    if not barrio:
        return talleres
    return sorted(talleres, key=lambda t: (t.barrio_id != barrio.pk, t.barrio.ciudad != barrio.ciudad))
