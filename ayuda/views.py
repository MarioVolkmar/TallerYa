"""Endpoints del chat de Chispa. Devuelven JSON con la misma forma que tendrá la respuesta de un modelo de IA."""
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from . import motor


@never_cache
@require_GET
def catalogo_json(request):
    """Saludo (personalizado si hay sesión) y temas con sus preguntas, para pintar los chips."""
    return JsonResponse(motor.catalogo(request.user))


@never_cache
@require_GET
def preguntar(request):
    """Responde una pregunta del catálogo (?id=) o un texto libre (?q=)."""
    pregunta_id = (request.GET.get("id") or "").strip()[:60]
    texto = (request.GET.get("q") or "").strip()[:300]
    if not pregunta_id and not texto:
        return JsonResponse({"error": "Falta la pregunta."}, status=400)
    return JsonResponse(motor.responder(texto=texto, pregunta_id=pregunta_id, usuario=request.user))
