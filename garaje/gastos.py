"""Cuentas de gastos de una moto: cuánto se gasta y cuánto se recorre.

- Los km salen de las lecturas de kilometraje de la moto (no del formulario de gastos).
- Los galones se estiman con el precio de referencia de garaje/combustible.py (nunca se muestran como exactos).
- Los servicios con costo de la hoja de vida cuentan como gasto "Servicio en taller" sin copiarse a Gasto,
  así nunca se registran dos veces.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from django.utils import timezone

from . import combustible
from .models import Gasto

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# Categorías: color e ícono (trazo SVG de 24×24) en un solo lugar; los nombres vienen de Gasto.Tipo.
_ESTILO = {
    "gasolina": ("#f2611d", "M4 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16M3 21h12M14 9h2l3 3v6a1.5 1.5 0 0 1-3 0v-3h-2M7 7h4"),
    "aceite": ("#e3a72f", "M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z"),
    "servicio": ("#3fbf6b", "M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z"),
    "repuesto": ("#5fb3b3", "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"),
    "llantas": ("#9aa3a8", "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"),
    "lavada": ("#6aa8ff", "M7 14s-3 3.5-3 5.5a3 3 0 0 0 6 0C10 17.5 7 14 7 14zM17 4s-4 4.5-4 7a4 4 0 0 0 8 0c0-2.5-4-7-4-7z"),
    "accesorios": ("#b48cff", "M4 15a8 8 0 0 1 16 0v3H4zM12 7v4h8"),
    "soat": ("#4f7cff", "M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6z"),
    "tecno": ("#d46bd1", "M9 4h6v3H9zM7 5H5v16h14V5h-2M9 14l2 2 4-4"),
    "parqueadero": ("#c9b37a", "M5 3h14v18H5zM10 17V7h3a3 3 0 0 1 0 6h-3"),
    "multa": ("#ff5a3c", "M12 3 2 21h20zM12 10v5M12 18h.01"),
    "otro": ("#8d9496", "M5 12h.01M12 12h.01M19 12h.01"),
}
CATEGORIAS = {clave: {"clave": clave, "nombre": nombre, "color": _ESTILO[clave][0], "icono": _ESTILO[clave][1]}
              for clave, nombre in Gasto.Tipo.choices}


@dataclass
class Movimiento:
    fecha: date
    tipo: str
    valor: int
    descripcion: str
    gasto: Gasto | None = None  # None: viene de la hoja de vida
    registro: object = None  # RegistroServicio de la hoja de vida (taller, verificado, mantenimiento del plan)
    km_aprox: int | None = None  # km de esa fecha según las lecturas (exacto si viene de la hoja de vida)

    @property
    def categoria(self):
        return CATEGORIAS.get(self.tipo, CATEGORIAS["otro"])

    @property
    def galones(self):
        """Galones estimados (solo gasolina)."""
        return combustible.galones_estimados(self.valor) if self.tipo == Gasto.Tipo.GASOLINA else None

    @property
    def galones_texto(self):
        return f"≈ {self.galones:.1f} gal estimados".replace(".", ",") if self.galones else ""


def _km_en(puntos, fecha):
    """Último kilometraje conocido hasta esa fecha (puntos ordenados por fecha)."""
    antes = [km for f, km in puntos if f <= fecha]
    return max(antes) if antes else None


def _puntos(moto):
    """(fecha, km) de las lecturas más el km con que se registró la moto, ordenados por fecha."""
    return sorted([(timezone.localtime(moto.creado).date(), moto.km_inicial)] + list(moto.lecturas.values_list("fecha", "km")))


def movimientos(moto, puntos=None):
    """Gastos registrados + servicios con costo de la hoja de vida, del más reciente al más viejo."""
    puntos = _puntos(moto) if puntos is None else puntos
    lista = [Movimiento(g.fecha, g.tipo, g.valor, g.notas, g, km_aprox=_km_en(puntos, g.fecha)) for g in moto.gastos.all()]
    lista += [Movimiento(r.fecha, Gasto.Tipo.SERVICIO, r.costo, r.servicios, registro=r, km_aprox=r.km)
              for r in moto.hoja_vida.filter(costo__gt=0).select_related("taller", "mantenimiento__tarea")]
    return sorted(lista, key=lambda m: (m.fecha, m.gasto.creado if m.gasto else m.fecha), reverse=True)


def km_periodo(moto, desde, hasta, puntos=None):
    """Km recorridos entre dos fechas según las lecturas (y el km con que se registró la moto). None si faltan datos."""
    puntos = _puntos(moto) if puntos is None else puntos
    antes = [km for f, km in puntos if f < desde]
    dentro = [km for f, km in puntos if desde <= f <= hasta]
    if not dentro or (not antes and len(dentro) < 2):
        return None
    inicio = max(antes) if antes else min(dentro)
    km = max(dentro) - inicio
    return km if km > 0 else None


def _mes(fecha, atras):
    indice = fecha.year * 12 + fecha.month - 1 - atras
    return indice // 12, indice % 12 + 1


def _por_categoria(movs):
    totales = {}
    for m in movs:
        totales[m.tipo] = totales.get(m.tipo, 0) + m.valor
    total = sum(totales.values())
    return [{**CATEGORIAS.get(k, CATEGORIAS["otro"]), "total": v, "pct": round(v * 100 / total) if total else 0}
            for k, v in sorted(totales.items(), key=lambda kv: -kv[1])]


def resumen(moto, hoy=None, meses=6):
    hoy = hoy or timezone.localdate()
    puntos = _puntos(moto)  # las lecturas, una sola vez para la lista y el km del mes
    movs = movimientos(moto, puntos)
    inicio_mes = hoy.replace(day=1)
    del_mes = [m for m in movs if inicio_mes <= m.fecha <= hoy]
    mes_total = sum(m.valor for m in del_mes)
    km_mes = km_periodo(moto, inicio_mes, hoy, puntos)
    galones_mes = sum(m.galones or 0 for m in del_mes)

    serie = []
    for atras in range(meses - 1, -1, -1):
        anio, mes = _mes(hoy, atras)
        del_periodo = [m for m in movs if (m.fecha.year, m.fecha.month) == (anio, mes)]
        # "categorias" por mes: al tocar la barra, "En qué se va" muestra el reparto de ese mes
        serie.append({"etiqueta": MESES[mes - 1], "total": sum(m.valor for m in del_periodo),
                      "categorias": _por_categoria(del_periodo)})
    tope = max((s["total"] for s in serie), default=0)
    for i, s in enumerate(serie):
        s["alto"] = round(s["total"] * 100 / tope) if tope else 0
        s["x"] = i * 50 + 10
        s["y"] = 110 - s["alto"]
        s["corto"] = (f"{s['total'] / 1_000_000:.1f}M".replace(".0M", "M") if s["total"] >= 1_000_000
                      else f"{round(s['total'] / 1000)}k" if s["total"] >= 1000 else str(s["total"]))

    return {
        "movimientos": movs, "total": sum(m.valor for m in movs), "categorias": _por_categoria(movs),
        "mes_total": mes_total, "mes_nombre": MESES[hoy.month - 1], "serie": serie, "tope": tope,
        "km_mes": km_mes,
        "costo_km": round(mes_total / km_mes) if km_mes and mes_total else None,
        # Solo con datos suficientes: al menos medio galón estimado y km en el mes.
        "km_galon": round(km_mes / galones_mes, 1) if km_mes and galones_mes >= 0.5 else None,
        "precio_galon": combustible.PRECIO_GALON_CORRIENTE, "precio_por_verificar": combustible.POR_VERIFICAR,
        "precio_fecha": combustible.VIGENTE_DESDE, "precio_fuente": combustible.FUENTE,
        "precio_fuente_url": combustible.FUENTE_URL,
    }
