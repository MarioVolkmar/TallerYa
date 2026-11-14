"""Precios de referencia: rangos que publican los talleres y mediana de Medellín (solo con 3 o más talleres)."""
from statistics import median

from .models import CILINDRAJES, PrecioServicio

MINIMO_TALLERES = 3
NOMBRE_CILINDRAJE = dict(CILINDRAJES)


def _redondear(valor):
    return int(round(valor / 1000.0) * 1000)


def medianas_medellin(servicio_id=None):
    """[{servicio, cilindraje, desde, hasta, talleres}] por servicio y cilindraje, solo si lo publicaron
    al menos 3 talleres activos de Medellín. Una consulta."""
    filas = PrecioServicio.objects.filter(taller__activo=True, taller__barrio__ciudad="Medellín")
    if servicio_id:
        filas = filas.filter(servicio_id=servicio_id)
    grupos = {}
    for sid, nombre, cil, desde, hasta in filas.values_list("servicio_id", "servicio__nombre", "cilindraje", "desde", "hasta"):
        grupos.setdefault((nombre, cil, sid), []).append((desde, hasta))
    resultado = []
    for (nombre, cil, sid), rangos in sorted(grupos.items()):
        if len(rangos) < MINIMO_TALLERES:  # un taller publica una vez por servicio y cilindraje
            continue
        resultado.append({"servicio": nombre, "servicio_id": sid, "cilindraje": NOMBRE_CILINDRAJE.get(cil, ""),
                          "desde": _redondear(median(d for d, _ in rangos)),
                          "hasta": _redondear(median(h for _, h in rangos)), "talleres": len(rangos)})
    return resultado
