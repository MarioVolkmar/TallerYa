"""Página de etiquetado de modelos 3D de Tripo (solo staff): /garaje/etiquetar-3d/ y /garaje/etiquetar-3d/<modelo>/."""
import json

from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from consola.permisos import solo_admin

from . import etiquetas_3d as e3d


def _modelo_o_404(modelo):
    ruta = e3d.modelos().get(modelo)
    if not ruta:
        raise Http404("Modelo no encontrado")
    return ruta


@solo_admin
def indice(request):
    hechos = {p.stem for p in e3d.CARPETA.glob("*.json")}
    lista = [{"modelo": m, "hecho": m in hechos, "local": e3d.TRIPO_LOCAL in r.parents} for m, r in e3d.modelos().items()]
    return render(request, "garaje/etiquetar_3d_indice.html", {"lista": lista})


@solo_admin
def pagina(request, modelo):
    _modelo_o_404(modelo)
    return render(request, "garaje/etiquetar_3d.html", {"modelo": modelo, "datos": {
        "modelo": modelo, "piezas": e3d.PIEZAS, "acabados": e3d.ACABADOS,
        "etiquetas": e3d.etiquetas(modelo), "glosario": e3d.glosario(),
    }})


@solo_admin
def glb(request, modelo):
    return FileResponse(open(_modelo_o_404(modelo), "rb"), content_type="model/gltf-binary")


@solo_admin
@require_POST
def guardar(request, modelo):
    _modelo_o_404(modelo)
    try:
        partes = json.loads(request.body or b"{}").get("partes")
        datos, n = e3d.guardar(modelo, partes)
    except (ValueError, AttributeError) as error:
        return JsonResponse({"ok": False, "error": str(error)}, status=400)
    return JsonResponse({"ok": True, "partes": len(datos["partes"]), "glosario": n,
                         "partes_deducidas": [{"parte": p["parte"], "pieza": p["pieza"], "acabado": p["acabado"], "por_revisar": p["por_revisar"], "zonas": p["zonas"]} for p in datos["partes"]]})
