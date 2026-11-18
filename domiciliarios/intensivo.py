"""Plan de uso intensivo: el plan de garaje.plan con intervalos adelantados y el ritmo de los km por semana.

Los manuales (Honda, Yamaha, Bajaj, AKT) piden servicios más seguidos en "condiciones severas": pare y arranque en
ciudad, carga, lluvia y polvo. Es justo el uso de un domiciliario. Los factores son una aproximación conservadora (se
dice en la página) y solo se aplican a las piezas que más sufren. Lo demás queda con el intervalo del manual.
"""
import copy

from django.utils import timezone

from garaje import intervalos
from garaje.models import TareaMantenimiento
from garaje.plan import GRAVEDAD, PlanMoto, _estado_tarea, nivel_tarea, ritmo_km

FACTORES = {
    TareaMantenimiento.Pieza.ACEITE: 0.7,
    TareaMantenimiento.Pieza.FILTRO_AIRE: 0.6,
    TareaMantenimiento.Pieza.CADENA: 0.75,
    TareaMantenimiento.Pieza.CORREA: 0.75,
    TareaMantenimiento.Pieza.FRENO_DEL: 0.75,
    TareaMantenimiento.Pieza.FRENO_TRAS: 0.75,
    TareaMantenimiento.Pieza.LLANTA_DEL: 0.8,
    TareaMantenimiento.Pieza.LLANTA_TRAS: 0.8,
}


def intervalo_intensivo(km, pieza):
    """Intervalo adelantado, redondeado a 100 km. None si la pieza no cambia."""
    factor = FACTORES.get(pieza)
    if not km or not factor:
        return None
    return max(100, round(km * factor / 100) * 100)


def ritmo_intensivo(moto, km_semana, hoy=None):
    """km por día: el declarado o el de las lecturas reales, el que sea mayor (mejor avisar antes que tarde)."""
    declarado = km_semana / 7
    real, estimado = ritmo_km(moto, hoy)
    return max(declarado, real) if real and not estimado else declarado


def plan_intensivo(moto, km_semana, hoy=None):
    hoy = hoy or timezone.localdate()
    ritmo = ritmo_intensivo(moto, km_semana, hoy)
    ultimos = {}
    for m in sorted(moto.mantenimientos.all(), key=lambda m: (m.fecha, m.km)):
        ultimos[m.tarea_id] = m
    pospuestas = {a.tarea_id for a in moto.ajustes.all() if a.pospuesta}
    propios = intervalos.de_linea(moto.linea, moto.modelo) if moto.linea_id else {}
    specs = moto.specs()
    plan = PlanMoto(moto=moto, km_por_dia=ritmo, ritmo_estimado=False)
    for tarea in TareaMantenimiento.objects.filter(activo=True).select_related("servicio"):
        if not tarea.aplica_a(specs):
            continue
        tarea = intervalos.aplicar(tarea, moto.linea, propios) if propios else tarea
        normal = tarea.intervalo_km
        nuevo = intervalo_intensivo(normal, tarea.pieza)
        if nuevo:
            tarea = copy.copy(tarea)
            tarea.intervalo_km = nuevo
        t = _estado_tarea(tarea, moto, ultimos.get(tarea.pk), ritmo, hoy)
        t.pospuesta = tarea.pk in pospuestas
        t.nivel = nivel_tarea(t.estado, t.km_restantes, t.dias_restantes, tarea.intervalo_km,
                              t.pospuesta or (t.supuesto and (t.progreso or 0) >= 1))
        t.intervalo_normal = normal
        t.intervalo_intensivo = nuevo
        t.dias_para = (t.fecha_estimada - hoy).days if t.fecha_estimada else None
        plan.tareas.append(t)
    plan.tareas.sort(key=lambda t: (-GRAVEDAD[t.estado], -(t.progreso or 0), t.tarea.orden))
    return plan


def al_dia(plan):
    """Mantenimiento al día: nada vencido ni urgente en el plan intensivo."""
    return not plan.por_nivel("vencido", "urgente")
