"""Precios de referencia: rangos que publican los talleres y mediana de Medellín (solo con 3 o más talleres)."""
from datetime import timedelta
from statistics import median

from django.utils import timezone

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


def agrupar_formset(formset):
    """Formularios del formset agrupados por servicio, para la pantalla «Mis precios» (una tarjeta por servicio).
    Devuelve [{"id", "nombre", "forms"}] en el orden en que aparece cada servicio; los formularios sin servicio
    (extra vacíos) no se muestran: la pantalla agrega filas nuevas con JavaScript."""
    nombres = {str(s.pk): s.nombre for s in formset.empty_form.fields["servicio"].queryset}
    grupos = {}
    for f in formset.forms:
        sid = str(f["servicio"].value() or "")
        if not sid and not f.errors and not f.instance.pk:
            continue
        grupos.setdefault(sid, {"id": sid, "nombre": nombres.get(sid, "Elige el servicio"), "forms": []})["forms"].append(f)
    return list(grupos.values())


def medianas_por_clave(servicio_ids=None):
    """{servicio_id: {cilindraje_clave: [desde, hasta]}} con la mediana del sector, para sugerir una referencia."""
    clave = {nombre: c for c, nombre in CILINDRAJES}
    salida = {}
    for m in medianas_medellin():
        salida.setdefault(str(m["servicio_id"]), {})[clave.get(m["cilindraje"], "")] = [m["desde"], m["hasta"]]
    return salida


# Recordatorio: los precios de mano de obra se confirman cada 2-3 meses (a los 75 días se avisa).
DIAS_RECORDATORIO = 75


def limite_vencimiento(ahora=None):
    from django.utils import timezone
    return (ahora or timezone.now()) - timedelta(days=DIAS_RECORDATORIO)


def fecha_confirmacion(taller):
    """Fecha de la confirmación más antigua entre sus precios (la que manda para decir «confirmado el dd/mm»), o None."""
    from django.db.models import Min
    f = taller.precios.aggregate(f=Min("actualizado"))["f"]
    return timezone.localtime(f).date() if f else None


def necesita_confirmar(taller, ahora=None):
    """True si tiene precios y alguno lleva más de 75 días sin confirmarse."""
    return taller.precios.filter(actualizado__lt=limite_vencimiento(ahora)).exists()


def confirmar_vigentes(taller):
    """«Siguen vigentes»: renueva la fecha de todos sus precios sin cambiar los valores."""
    return taller.precios.update(actualizado=timezone.now())
