"""Sección Reportes: vistas del perfil y clics en WhatsApp / llamar por taller, mes a mes (EventoDiario; sin datos
personales del visitante)."""
from datetime import date

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404

from talleres.models import EventoDiario, Taller

from .. import reloj

T = EventoDiario.Tipo
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]


def _meses(hoy, n=12):
    salida, a, m = [], hoy.year, hoy.month
    for _ in range(n):
        salida.append(date(a, m, 1))
        a, m = (a, m - 1) if m > 1 else (a - 1, 12)
    return salida


def _mes_pedido(valor, opciones):
    try:
        a, m = valor.split("-")
        d = date(int(a), int(m), 1)
    except (ValueError, AttributeError):
        return opciones[0]
    return d if d in opciones else opciones[0]


def _por_mes(hoy, filas_por_mes, columnas):
    """12 meses (el más reciente primero) con las columnas pedidas; filas_por_mes: {(año, mes): {col: n}}."""
    salida = []
    for d in _meses(hoy):
        datos = filas_por_mes.get((d.year, d.month), {})
        salida.append({"mes": f"{MESES[d.month - 1].capitalize()} {d.year}", **{c: datos.get(c, 0) for c in columnas}})
    return salida


def _detalle_taller(request, pk):
    taller = get_object_or_404(Taller, pk=pk if str(pk).isdigit() else 0)
    desde = _meses(reloj.hoy())[-1]
    acum = {}
    for e in EventoDiario.objects.filter(taller=taller, fecha__gte=desde):
        acum.setdefault((e.fecha.year, e.fecha.month), {})[e.tipo] = acum.get((e.fecha.year, e.fecha.month), {}).get(e.tipo, 0) + e.cantidad
    filas = _por_mes(reloj.hoy(), acum, (T.VISITA, T.WHATSAPP, T.LLAMADA))
    total = {c: sum(f[c] for f in filas) for c in (T.VISITA, T.WHATSAPP, T.LLAMADA)}
    return "consola/reporte_detalle.html", {
        "quien": taller.nombre, "ficha": taller.get_absolute_url(), "volver": "?seccion=talleres",
        "columnas": [("Vistas del perfil", T.VISITA), ("Clics a WhatsApp", T.WHATSAPP), ("Clics a llamar", T.LLAMADA)],
        "filas": filas, "total": total, "nota": "",
    }


def _detalle_mecanico(request, pk):
    from django.db.models import Count
    from domicilio.models import MecanicoDomicilio, ResenaMecanico, SolicitudVisita
    m = get_object_or_404(MecanicoDomicilio, pk=pk if str(pk).isdigit() else 0)
    desde = _meses(reloj.hoy())[-1]
    acum = {}
    from cupones.models import CodigoCupon
    fuentes = ((SolicitudVisita.objects.filter(mecanico=m, creado__date__gte=desde), "creado", "solicitudes"),
               (ResenaMecanico.objects.filter(mecanico=m, creado__date__gte=desde), "creado", "resenas"),
               # Descuentos: tomados por moteros y usados con el mecánico (por dentro son cupones)
               (CodigoCupon.objects.filter(cupon__mecanico=m, creado__date__gte=desde), "creado", "descuentos"),
               (CodigoCupon.objects.filter(canjeado_mecanico=m, canjeado_en__date__gte=desde), "canjeado_en", "canjes"))
    for qs, campo, col in fuentes:
        for e in qs.values_list(campo, flat=True):
            d = acum.setdefault((e.year, e.month), {})
            d[col] = d.get(col, 0) + 1
    cols = ("solicitudes", "resenas", "descuentos", "canjes")
    filas = _por_mes(reloj.hoy(), acum, cols)
    total = {c: sum(f[c] for f in filas) for c in cols}
    return "consola/reporte_detalle.html", {
        "quien": m.nombre, "ficha": m.get_absolute_url(), "volver": "?seccion=mecanicos",
        "columnas": [("Solicitudes de visita", "solicitudes"), ("Reseñas nuevas", "resenas"),
                     ("Descuentos tomados", "descuentos"), ("Descuentos usados", "canjes")],
        "filas": filas, "total": total,
        "nota": "Aún no se cuentan las vistas del perfil ni los clics a WhatsApp o llamar de los mecánicos; solo solicitudes, reseñas y descuentos.",
    }


def seccion(request):
    if request.GET.get("taller"):
        return _detalle_taller(request, request.GET["taller"])
    if request.GET.get("mecanico"):
        return _detalle_mecanico(request, request.GET["mecanico"])
    opciones = _meses(reloj.hoy())
    mes = _mes_pedido(request.GET.get("mes", ""), opciones)
    siguiente = date(mes.year + (mes.month == 12), mes.month % 12 + 1, 1)
    en_mes = Q(eventos__fecha__gte=mes, eventos__fecha__lt=siguiente)
    filas = (Taller.objects.filter(activo=True)
             .annotate(vistas=Sum("eventos__cantidad", filter=en_mes & Q(eventos__tipo=T.VISITA)),
                       clics_wa=Sum("eventos__cantidad", filter=en_mes & Q(eventos__tipo=T.WHATSAPP)),
                       llamadas=Sum("eventos__cantidad", filter=en_mes & Q(eventos__tipo=T.LLAMADA)))
             .only("pk", "nombre", "slug"))
    filas = sorted(({"taller": t, "vistas": t.vistas or 0, "whatsapp": t.clics_wa or 0, "llamadas": t.llamadas or 0}
                    for t in filas), key=lambda f: (-f["vistas"], f["taller"].nombre.lower()))
    total = {k: sum(f[k] for f in filas) for k in ("vistas", "whatsapp", "llamadas")}
    return "consola/reportes.html", {
        "meses": [(d.strftime("%Y-%m"), f"{MESES[d.month - 1].capitalize()} {d.year}") for d in opciones],
        "mes_actual": mes.strftime("%Y-%m"), "mes_texto": f"{MESES[mes.month - 1]} de {mes.year}",
        "filas": filas, "total": total,
    }
