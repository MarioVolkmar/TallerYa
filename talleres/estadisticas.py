"""Panel del taller: registro liviano de eventos (agregado por día) y resumen del mes contra el mes anterior.

No se guardan datos personales ni se usan cookies para rastrear: solo se suma 1 al contador del día.
No se cuentan bots ni las visitas del propio taller."""
import re
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, F, Q

from .models import EventoDiario

BOTS = re.compile(
    r"bot|crawl|spider|slurp|scrap|facebookexternalhit|whatsapp|telegram|preview|headless|lighthouse|"
    r"curl|wget|python-requests|httpx|aiohttp|go-http|java/|okhttp|monitor|pingdom|uptime", re.I)

# Lo que sería "Plus taller" más adelante. Hoy no se cobra nada: solo se muestra como "próximamente".
PLUS_TALLER = [
    ("historial", "Historial de 12 meses y descarga en CSV"),
    ("barrio", "Comparación con talleres de tu barrio"),
    ("destacado", "Aparecer primero en el directorio"),
    ("recordatorios", "Recordatorios de mantenimiento a tus clientes"),
]


def tiene_plus_taller(taller):
    """Punto único para activar Plus taller cuando exista el plan. Por ahora nadie lo tiene (no se cobra)."""
    return False


def es_bot(request):
    ua = request.META.get("HTTP_USER_AGENT", "")
    if not ua or BOTS.search(ua):
        return True
    # Precargas del navegador (no son una visita real)
    proposito = (request.META.get("HTTP_SEC_PURPOSE", "") + request.META.get("HTTP_PURPOSE", "")).lower()
    return "prefetch" in proposito or "prerender" in proposito


def contable(request, taller):
    if request.method not in ("GET", "POST") or es_bot(request):
        return False
    usuario = request.user
    return not (usuario.is_authenticated and taller.usuario_id == usuario.pk)


def registrar(request, taller, tipo, fecha=None):
    """Suma 1 al contador del día. Devuelve True si se contó."""
    from django.utils import timezone
    if not contable(request, taller):
        return False
    fecha = fecha or timezone.localdate()
    filtro = {"taller": taller, "fecha": fecha, "tipo": tipo}
    if not EventoDiario.objects.filter(**filtro).update(cantidad=F("cantidad") + 1):
        try:
            with transaction.atomic():
                EventoDiario.objects.create(cantidad=1, **filtro)
        except IntegrityError:  # otra petición lo creó al mismo tiempo
            EventoDiario.objects.filter(**filtro).update(cantidad=F("cantidad") + 1)
    return True


def _periodos(hoy):
    """Mes actual hasta hoy y el mismo tramo del mes anterior (comparación justa a mitad de mes)."""
    inicio = hoy.replace(day=1)
    fin_ant = inicio - timedelta(days=1)
    inicio_ant = fin_ant.replace(day=1)
    tope_ant = min(inicio_ant + (hoy - inicio), fin_ant)
    return (inicio, hoy), (inicio_ant, tope_ant)


def _variacion(actual, anterior):
    if anterior in (None, 0):
        return None if not actual else "nuevo"
    return round((actual - anterior) * 100 / anterior)


def resumen(taller, hoy):
    """Cifras del mes contra el mismo tramo del mes anterior, y la serie diaria de los últimos 30 días.
    Tres consultas: eventos, canjes y reseñas."""
    from cupones.models import CodigoCupon
    (ini, fin), (ini_a, fin_a) = _periodos(hoy)
    desde = min(ini_a, hoy - timedelta(days=29))
    filas = list(EventoDiario.objects.filter(taller=taller, fecha__gte=desde, fecha__lte=hoy)
                 .values_list("fecha", "tipo", "cantidad"))
    suma = {}
    for fecha, tipo, n in filas:
        for clave, (a, b) in (("act", (ini, fin)), ("ant", (ini_a, fin_a))):
            if a <= fecha <= b:
                suma[(clave, tipo)] = suma.get((clave, tipo), 0) + n
    rango = lambda a, b: Q(canjeado_en__date__gte=a, canjeado_en__date__lte=b)
    canjes = CodigoCupon.objects.filter(canjeado_taller=taller).aggregate(
        act=Count("pk", filter=rango(ini, fin)), ant=Count("pk", filter=rango(ini_a, fin_a)))
    r = lambda a, b: Q(creado__date__gte=a, creado__date__lte=b)
    res = taller.resenas.filter(visible=True).aggregate(
        act=Count("pk", filter=r(ini, fin)), ant=Count("pk", filter=r(ini_a, fin_a)),
        nota_act=Avg("estrellas", filter=r(ini, fin)), nota_ant=Avg("estrellas", filter=r(ini_a, fin_a)))

    def cifra(clave, nombre, act, ant, decimal=False):
        return {"clave": clave, "nombre": nombre, "actual": act, "anterior": ant, "decimal": decimal,
                "variacion": _variacion(act, ant) if not decimal else None,
                "diferencia": round(act - ant, 1) if decimal and act is not None and ant is not None else None}

    T = EventoDiario.Tipo
    cifras = [cifra(t.value, t.label, suma.get(("act", t.value), 0), suma.get(("ant", t.value), 0)) for t in T]
    cifras += [cifra("canjes", "Cupones canjeados", canjes["act"], canjes["ant"]),
               cifra("resenas", "Reseñas nuevas", res["act"], res["ant"]),
               cifra("nota", "Calificación del mes", res["nota_act"], res["nota_ant"], decimal=True)]
    # Serie de 30 días (visitas y contactos) para las barras
    por_dia = {}
    for fecha, tipo, n in filas:
        d = por_dia.setdefault(fecha, {"visitas": 0, "contactos": 0})
        d["visitas" if tipo == T.VISITA else "contactos"] += n
    serie = [{"fecha": hoy - timedelta(days=i), **por_dia.get(hoy - timedelta(days=i), {"visitas": 0, "contactos": 0})}
             for i in range(29, -1, -1)]
    tope = max([d["visitas"] + d["contactos"] for d in serie] + [1])
    for d in serie:
        d["alto_v"] = round(d["visitas"] * 100 / tope)
        d["alto_c"] = round(d["contactos"] * 100 / tope)
    return {"cifras": cifras, "serie": serie, "periodo": (ini, fin), "periodo_ant": (ini_a, fin_a)}
