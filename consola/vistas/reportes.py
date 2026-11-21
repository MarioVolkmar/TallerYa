"""Sección Reportes: vistas del perfil y clics en WhatsApp / llamar por taller, mes a mes (EventoDiario; sin datos
personales del visitante)."""
from datetime import date

from django.db.models import Q, Sum

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


def seccion(request):
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
