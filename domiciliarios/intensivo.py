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
    """km por día: los reales (lecturas del tablero y cierres de jornada) cuando hay al menos una semana de datos; si
    no, los declarados en km por semana."""
    real, estimado = ritmo_km(moto, hoy)
    return real if real and not estimado else km_semana / 7


def km_semana_sugerido(moto):
    """Para crear el perfil desde el interruptor de la moto: el ritmo real si lo hay, si no unos 1.200 km/semana."""
    real, estimado = ritmo_km(moto)
    km = round(real * 7) if real and not estimado else 1200
    return min(5000, max(50, km))


def precargar_trabajo(motos):
    """Para listas de motos (Mi garaje, Mi cuenta, avisos): una sola consulta en vez de una por moto."""
    from .bandera import activo
    from .models import PerfilDomiciliario
    if not activo() or not motos:
        return
    por_moto = {p.moto_id: p for p in PerfilDomiciliario.objects.filter(moto__in=[m.pk for m in motos])}
    for m in motos:
        m._perfil_trabajo = por_moto.get(m.pk)


def perfil_de_trabajo(moto):
    """El perfil de domiciliario si esta moto es «la uso para trabajar» (y la bandera está prendida); si no, None."""
    from .bandera import activo
    from .models import PerfilDomiciliario
    if not activo() or not getattr(moto, "pk", None):
        return None
    cache = getattr(moto, "_perfil_trabajo", False)
    if cache is False:
        cache = PerfilDomiciliario.objects.filter(moto=moto).first()
        moto._perfil_trabajo = cache
    return cache


def plan_intensivo(moto, km_semana, hoy=None, tareas=None):
    hoy = hoy or timezone.localdate()
    ritmo = ritmo_intensivo(moto, km_semana, hoy)
    ultimos = {}
    for m in sorted(moto.mantenimientos.all(), key=lambda m: (m.fecha, m.km)):
        ultimos[m.tarea_id] = m
    pospuestas = {a.tarea_id for a in moto.ajustes.all() if a.pospuesta}
    propios = intervalos.de_linea(moto.linea, moto.modelo) if moto.linea_id else {}
    specs = moto.specs()
    plan = PlanMoto(moto=moto, km_por_dia=ritmo, ritmo_estimado=False)
    plan.de_trabajo = True  # la página de la moto y los avisos lo usan (tarjeta Mi ruta, alertas en días)
    if tareas is None:
        tareas = TareaMantenimiento.objects.filter(activo=True).select_related("servicio")
    for tarea in tareas:
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
