"""Sección Citas: listado con filtros (estado, fechas, búsqueda) y cancelación por soporte con motivo."""
from django.db.models import Q

from talleres.models import SolicitudCita

from ..acciones import ErrorAccion, accion
from ..forms import FiltroCitas
from ..limites import LIMITES
from ..paginacion import paginar

ABIERTAS = (SolicitudCita.Estado.PENDIENTE, SolicitudCita.Estado.CONFIRMADA, SolicitudCita.Estado.REPROGRAMADA)


@accion("citas.cancelar", modelo=SolicitudCita, nombre="Cancelar cita",
        campos={"estado": ("Estado", lambda c: c.get_estado_display()),
                "motivo": ("Motivo de la cancelación", lambda c: c.motivo_cancelacion)},
        frase="Canceló la cita #{pk} en {obj.taller.nombre}", exito="Cita cancelada.")
def cancelar(request, cita):
    if cita.estado not in ABIERTAS:
        raise ErrorAccion(f"La cita ya está {cita.get_estado_display().lower()}; no se puede cancelar.")
    motivo = request.POST.get("motivo", "").strip()
    l = LIMITES["motivo"]
    if not l["min"] <= len(motivo) <= l["max"]:
        raise ErrorAccion(f"Escribe el motivo (entre {l['min']} y {l['max']} caracteres).")
    cita.estado = SolicitudCita.Estado.CANCELADA
    cita.motivo_cancelacion = f"Cancelada por TallerYa: {motivo}"[:l["max"]]
    cita.save(update_fields=["estado", "motivo_cancelacion"])


def seccion(request):
    form = FiltroCitas(request.GET)
    datos = form.cleaned_data if form.is_valid() else {}
    qs = SolicitudCita.objects.select_related("taller", "servicio", "usuario").order_by("-fecha_preferida", "-pk")
    if datos.get("q"):
        q = datos["q"]
        qs = qs.filter(Q(nombre__icontains=q) | Q(taller__nombre__icontains=q) | Q(moto__icontains=q)
                       | Q(usuario__email__icontains=q))
    if datos.get("estado") in SolicitudCita.Estado.values:
        qs = qs.filter(estado=datos["estado"])
    if datos.get("desde"):
        qs = qs.filter(fecha_preferida__gte=datos["desde"])
    if datos.get("hasta"):
        qs = qs.filter(fecha_preferida__lte=datos["hasta"])
    return "consola/citas.html", {"form": form, "estados": SolicitudCita.Estado.choices, "abiertas": ABIERTAS,
                                  **paginar(request, qs, "citas")}
