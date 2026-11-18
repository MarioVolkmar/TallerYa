import csv
import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST

from consola.permisos import solo_admin

from . import nucleo
from .models import ResumenDiario


@require_POST
def evento(request):
    """Eventos del navegador (abrir el 3D, tocar una pieza). Con CSRF; solo nombres de la lista NAVEGADOR."""
    try:
        cuerpo = json.loads(request.body or b"{}") if request.content_type == "application/json" else request.POST.dict()
    except ValueError:
        return HttpResponseBadRequest()
    nombre = str(cuerpo.get("nombre", ""))
    if nombre not in nucleo.NAVEGADOR:
        return HttpResponseBadRequest()
    datos = cuerpo.get("datos") if isinstance(cuerpo.get("datos"), dict) else {}
    nucleo.registrar_evento(request, nombre, **datos)
    return HttpResponse(status=204)


@solo_admin
def exportar(request):
    from .panel import periodo_de
    dias = periodo_de(request)
    desde = timezone.localdate() - timezone.timedelta(days=dias - 1)
    from .agregacion import agregar_pendientes
    agregar_pendientes()
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="metricas-{dias}d-{timezone.localdate()}.csv"'
    respuesta.write("﻿")  # Excel reconoce las tildes
    w = csv.writer(respuesta)
    w.writerow(["dia", "clave", "valor", "total", "unicos"])
    for r in (ResumenDiario.objects.filter(dia__gte=desde).exclude(clave="_hecho")
              .order_by("dia", "clave", "-total").values_list("dia", "clave", "valor", "total", "unicos")):
        w.writerow(r)
    return respuesta
