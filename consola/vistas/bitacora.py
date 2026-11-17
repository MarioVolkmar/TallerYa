"""Sección Bitácora: listado con filtros y detalle campo por campo (antes → después)."""
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ..acciones import ACCIONES
from ..forms import FiltroBitacora
from ..paginacion import paginar
from ..models import Bitacora


def seccion(request):
    if request.GET.get("id", "").isdigit():
        registro = get_object_or_404(Bitacora, pk=int(request.GET["id"]))
        regla = ACCIONES.get(registro.accion)
        return "consola/bitacora_detalle.html", {"r": registro, "nombre_accion": regla.nombre if regla else registro.accion}
    form = FiltroBitacora(request.GET)
    datos = form.cleaned_data if form.is_valid() else {}
    qs = Bitacora.objects.all()
    if datos.get("q"):
        qs = qs.filter(Q(frase__icontains=datos["q"]) | Q(objeto_repr__icontains=datos["q"])
                       | Q(actor_nombre__icontains=datos["q"]))
    if datos.get("accion"):
        qs = qs.filter(accion=datos["accion"])
    if datos.get("actor"):
        qs = qs.filter(actor_id=datos["actor"])
    if datos.get("objeto"):
        tipo, pk = datos["objeto"].split(":")
        qs = qs.filter(objeto_tipo=tipo, objeto_id=int(pk))
    if datos.get("desde"):
        qs = qs.filter(creado__date__gte=datos["desde"])
    if datos.get("hasta"):
        qs = qs.filter(creado__date__lte=datos["hasta"])
    actores = (Bitacora.objects.exclude(actor=None).values_list("actor_id", "actor_nombre").distinct()
               .order_by("actor_nombre"))
    return "consola/bitacora.html", {
        "form": form, **paginar(request, qs, "bitacora"),
        "acciones": sorted(((c, r.nombre) for c, r in ACCIONES.items()), key=lambda x: x[1]),
        "actores": list(dict(actores).items()), "hay_filtros": any(datos.values()) if datos else False,
    }
