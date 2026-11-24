"""«Mis servicios» del mecánico a domicilio: lo que registró en la hoja de vida de las motos y las visitas
atendidas que aún no tienen su servicio registrado (equivalente a «Servicios» del taller)."""
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from garaje.models import ServicioTaller

from .models import SolicitudVisita


@login_required
def servicios(request):
    mecanico = getattr(request.user, "mecanico_domicilio", None)
    if not mecanico:
        return redirect("domicilio:registro")
    hechos = (mecanico.servicios_hechos.exclude(estado=ServicioTaller.Estado.RECHAZADO)
              .select_related("moto", "moto__linea", "moto__linea__marca", "solicitud").prefetch_related("tareas"))
    pagina = Paginator(mecanico.servicios_hechos.select_related("moto", "moto__linea", "moto__linea__marca", "solicitud")
                       .prefetch_related("tareas"), 15).get_page(request.GET.get("pagina"))
    sin_registrar = list(mecanico.solicitudes.filter(estado=SolicitudVisita.Estado.ATENDIDA)
                         .exclude(servicios_hechos__isnull=False).order_by("-creado")[:10])
    from django.utils import timezone
    hoy = timezone.localdate()
    n_mes = hechos.filter(fecha__gte=hoy.replace(day=1)).count()
    n_conf = hechos.filter(estado=ServicioTaller.Estado.POR_CONFIRMAR).count()
    return render(request, "domicilio/servicios.html", {
        "m": mecanico, "pagina": pagina, "sin_registrar": sin_registrar,
        "resumen": {"servicios_mes": n_mes, "por_confirmar": n_conf, "servicios_total": hechos.count()},
    })
