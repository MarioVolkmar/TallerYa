"""Cuentas de gastos y consumo de una moto: km/galón entre tanqueos llenos, costo por km, mes y tipo.

Los servicios con costo de la hoja de vida cuentan como gasto de tipo "servicio" sin copiarse a Gasto,
así nunca se registran dos veces.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.utils import timezone

from .models import Gasto

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
TIPOS = dict(Gasto.Tipo.choices)


@dataclass
class Movimiento:
    fecha: date
    tipo: str
    valor: int
    km: int | None
    descripcion: str
    gasto: Gasto | None = None  # None: viene de la hoja de vida

    @property
    def tipo_nombre(self):
        return TIPOS[self.tipo]


def movimientos(moto):
    """Gastos registrados + servicios con costo de la hoja de vida, del más reciente al más viejo."""
    lista = [Movimiento(g.fecha, g.tipo, g.valor, g.km, g.notas or (f"{g.galones} gal" if g.galones else ""), g)
             for g in moto.gastos.all()]
    lista += [Movimiento(r.fecha, Gasto.Tipo.SERVICIO, r.costo, r.km, r.servicios)
              for r in moto.hoja_vida.filter(costo__gt=0)]
    return sorted(lista, key=lambda m: (m.fecha, m.km or 0), reverse=True)


def rendimiento(tanqueos):
    """Tramos entre dos tanqueos llenos: km recorridos / galones echados después del primero.

    Un tanqueo sin km o sin galones rompe la cadena (no se puede saber cuánto gastó).
    """
    tramos, desde, galones = [], None, Decimal(0)
    for t in sorted(tanqueos, key=lambda t: (t.km or 0, t.fecha, t.creado)):
        if t.km is None or not t.galones:
            desde, galones = None, Decimal(0)
            continue
        if desde is not None:
            galones += t.galones
        if t.tanque_lleno:
            if desde is not None and t.km > desde.km and galones > 0:
                tramos.append({"desde": desde, "hasta": t, "km": t.km - desde.km, "galones": galones,
                               "km_galon": round(float((t.km - desde.km) / galones), 1)})
            desde, galones = t, Decimal(0)
    km = sum(tr["km"] for tr in tramos)
    gal = sum((tr["galones"] for tr in tramos), Decimal(0))
    return {"tramos": tramos, "promedio": round(float(km / gal), 1) if gal else None,
            "ultimo": tramos[-1]["km_galon"] if tramos else None}


def _mes(fecha, atras):
    indice = fecha.year * 12 + fecha.month - 1 - atras
    return indice // 12, indice % 12 + 1


def resumen(moto, hoy=None, meses=6):
    hoy = hoy or timezone.localdate()
    movs = movimientos(moto)
    total = sum(m.valor for m in movs)

    del_mes = [m for m in movs if (m.fecha.year, m.fecha.month) == (hoy.year, hoy.month)]
    por_tipo = {}
    for m in movs:
        por_tipo[m.tipo] = por_tipo.get(m.tipo, 0) + m.valor
    tipos = sorted(({"clave": k, "nombre": TIPOS[k], "total": v} for k, v in por_tipo.items()), key=lambda t: -t["total"])
    for t in tipos:
        t["pct"] = round(t["total"] * 100 / total) if total else 0

    serie = []
    for atras in range(meses - 1, -1, -1):
        anio, mes = _mes(hoy, atras)
        serie.append({"anio": anio, "mes": mes, "etiqueta": MESES[mes - 1],
                      "total": sum(m.valor for m in movs if (m.fecha.year, m.fecha.month) == (anio, mes))})
    tope = max((s["total"] for s in serie), default=0)
    for i, s in enumerate(serie):
        s["alto"] = round(s["total"] * 100 / tope) if tope else 0
        s["x"] = i * 50 + 10
        s["y"] = 110 - s["alto"]
        s["corto"] = (f"{s['total'] / 1_000_000:.1f}M".replace(".0M", "M") if s["total"] >= 1_000_000
                      else f"{round(s['total'] / 1000)}k" if s["total"] >= 1000 else str(s["total"]))

    con_km = [m.km for m in movs if m.km is not None]
    km_desde = min(con_km) if con_km else moto.km_inicial
    recorridos = moto.km_actual - km_desde
    tanqueos = list(moto.gastos.filter(tipo=Gasto.Tipo.TANQUEO))
    consumo = rendimiento(tanqueos)
    km_tramos = sum(tr["km"] for tr in consumo["tramos"])
    valor_tramos = sum(t.valor for t in tanqueos if any(tr["desde"].km < (t.km or -1) <= tr["hasta"].km
                                                         for tr in consumo["tramos"]))
    return {
        "movimientos": movs, "total": total, "mes_total": sum(m.valor for m in del_mes), "mes_nombre": MESES[hoy.month - 1],
        "tipos": tipos, "serie": serie, "tope": tope, "consumo": consumo,
        "km_recorridos": recorridos if recorridos > 0 else None,
        "costo_km": round(total / recorridos) if recorridos > 0 and total else None,
        "combustible_km": round(valor_tramos / km_tramos) if km_tramos else None,
    }
