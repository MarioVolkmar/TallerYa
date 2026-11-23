"""Sección Cupones: vigentes, vencidos y desactivados; activar o desactivar y eliminar con eliminación segura."""
from django.db.models import Count, Q

from cupones.models import Cupon

from .. import reloj
from ..acciones import eliminador, interruptor
from ..eliminacion import Dependencia, analizar
from ..forms import FiltroCupones
from ..paginacion import paginar

interruptor("cupones.activo", modelo=Cupon, campo="activo", etiqueta="Activo", nombre="Activar o desactivar cupón",
            si="Activó", no="Desactivó", describe="el cupón #{pk} ({obj.titulo})")

REGLAS_ELIMINAR = [
    Dependencia("códigos entregados", "código entregado", lambda c: c.codigos.count(), True,
                "hay moteros con ese cupón; desactívalo para que no se entreguen más."),
]
eliminador("cupones.eliminar", modelo=Cupon, reglas=REGLAS_ELIMINAR, describe="el cupón #{pk} ({a[registro]})",
           nombre="Eliminar cupón")


def estado_de(cupon, hoy):
    if not cupon.activo:
        return "desactivado", "Desactivado"
    if cupon.valido_hasta and cupon.valido_hasta < hoy:
        return "vencido", "Vencido"
    return "vigente", "Vigente"


def seccion(request):
    form = FiltroCupones(request.GET)
    datos = form.cleaned_data if form.is_valid() else {}
    hoy = reloj.hoy()
    qs = (Cupon.objects.select_related("taller", "mecanico")
          .annotate(n_codigos=Count("codigos", distinct=True),
                    n_canjes=Count("codigos", filter=Q(codigos__canjeado_en__isnull=False), distinct=True))
          .order_by("-activo", "-pk"))
    if datos.get("q"):
        qs = qs.filter(Q(titulo__icontains=datos["q"]) | Q(taller__nombre__icontains=datos["q"])
                       | Q(mecanico__nombre__icontains=datos["q"]))
    if datos.get("de") == "talleres":
        qs = qs.filter(mecanico__isnull=True)
    elif datos.get("de") == "mecanicos":
        qs = qs.filter(mecanico__isnull=False)
    vigente = Q(valido_hasta__isnull=True) | Q(valido_hasta__gte=hoy)
    estado = datos.get("estado")
    if estado == "vigentes":
        qs = qs.filter(vigente, activo=True)
    elif estado == "vencidos":
        qs = qs.filter(activo=True, valido_hasta__lt=hoy)
    elif estado == "desactivados":
        qs = qs.filter(activo=False)
    datos_pagina = paginar(request, qs, "cupones")
    filas = [(c, estado_de(c, hoy), analizar(c, REGLAS_ELIMINAR)) for c in datos_pagina["pagina"]]
    return "consola/cupones.html", {"form": form, "filas": filas, **datos_pagina}
