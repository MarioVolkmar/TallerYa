"""Balance del domiciliario: lo que gana (jornadas) frente a lo que le cuesta la moto (garaje.gastos)."""
from datetime import timedelta

from django.utils import timezone

from garaje import gastos


def _periodo(perfil, moto, movs, puntos, desde, hasta):
    ingresos = [j for j in perfil.jornadas.all() if desde <= j.fecha <= hasta]
    ingreso = sum(j.ingreso for j in ingresos)
    gasto = sum(m.valor for m in movs if desde <= m.fecha <= hasta)
    km = gastos.km_periodo(moto, desde, hasta, puntos) if moto else 0
    return {
        "desde": desde, "ingreso": ingreso, "gasto": gasto, "neto": ingreso - gasto, "km": km, "dias": len(ingresos),
        "costo_km": round(gasto / km) if km and gasto else None,
        "ganancia_km": round(ingreso / km) if km and ingreso else None,
        "pct_gasto": min(100, round(gasto * 100 / ingreso)) if ingreso else None,
    }


def balance(perfil, hoy=None):
    hoy = hoy or timezone.localdate()
    moto = perfil.moto
    puntos = gastos._puntos(moto) if moto else []
    movs = gastos.movimientos(moto, puntos) if moto else []
    semana = _periodo(perfil, moto, movs, puntos, hoy - timedelta(days=hoy.weekday()), hoy)
    mes = _periodo(perfil, moto, movs, puntos, hoy.replace(day=1), hoy)
    mes["nombre"] = gastos.MESES[hoy.month - 1]
    return {"semana": semana, "mes": mes}
