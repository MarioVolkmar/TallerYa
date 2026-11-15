"""Tareas programadas por HTTP: un programador gratuito (GitHub Actions) llama aquí a diario.

Protegido con el token de la variable de entorno TAREAS_TOKEN (cabecera "Authorization: Bearer <token>").
Sin token configurado, las rutas no existen (404). Solo corre los comandos de la lista fija TAREAS, nunca uno
que venga en la petición. Todos son idempotentes: llamarlos de más no repite avisos.
"""
import hmac
import os
from io import StringIO

from django.core.management import call_command
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# nombre en la URL → comando de manage.py (lista cerrada)
TAREAS = {
    "avisos": "avisar_vencimientos",  # 5:30 a. m.: SOAT, técnico-mecánica y pico y placa del día
    "citas": "recordar_citas",        # 6:00 p. m.: citas de mañana (app talleres)
    "logros": "evaluar_logros",       # insignias de rodadas pasadas y "Moto al día" (app logros)
    "despiece": "precalentar_despiece",  # tras cada despliegue: arma la caché del despiece (por tandas de 15 s)
}


@csrf_exempt
@require_POST
def tarea(request, nombre="avisos"):
    token = os.environ.get("TAREAS_TOKEN", "")
    if len(token) < 20 or nombre not in TAREAS:  # sin token (o uno trivial) las tareas no se exponen
        raise Http404
    enviado = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not hmac.compare_digest(enviado.encode(), token.encode()):
        return JsonResponse({"error": "no autorizado"}, status=403)
    salida = StringIO()
    call_command(TAREAS[nombre], stdout=salida)
    return JsonResponse({"tarea": nombre, "resultado": salida.getvalue().strip()})
