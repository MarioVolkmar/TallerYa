"""Vistas de notificaciones: lista, panel en JSON, abrir (marca como leída y redirige) y marcar todas."""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST

from consola.ajustes import prefijos_apagados, sin_modulos_apagados
from .models import Notificacion
from .servicios import contar_urgentes


@login_required
def lista(request):
    return render(request, "notificaciones/lista.html", {"notificaciones": sin_modulos_apagados(request.user.notificaciones.all())[:60]})


@login_required
def panel(request):
    """Las últimas notificaciones para el desplegable de la campanita."""
    ultimas = sin_modulos_apagados(request.user.notificaciones.all())[:8]
    return JsonResponse({
        "sin_leer": sin_modulos_apagados(request.user.notificaciones.filter(leida=False)).count(),
        "urgentes": contar_urgentes(request.user),
        "notificaciones": [{
            "tipo": n.tipo, "titulo": n.titulo, "texto": n.texto, "leida": n.leida,
            "accion": n.accion, "urgente": n.urgente,
            "hace": "un momento" if (timezone.now() - n.creada).total_seconds() < 60 else timesince(n.creada).split(",")[0], "ir": reverse("notificaciones:ir", args=[n.pk]),
        } for n in ultimas],
    })


@login_required
def ir(request, pk):
    """Marca la notificación como leída y lleva a su página (solo rutas internas)."""
    notif = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    if not notif.leida:
        notif.leida = True
        notif.save(update_fields=["leida"])
    # La página que resuelve el aviso (pedir SOAT, CDA, talleres del servicio…), también para avisos viejos.
    from garaje.avisos import url_solucion
    destino = url_solucion(notif.clave) or notif.url
    interna = destino.startswith("/") and not destino.startswith("//") and not destino.startswith(prefijos_apagados())
    return redirect(destino if interna else "notificaciones:lista")


@login_required
@require_POST
def marcar_todas(request):
    request.user.notificaciones.filter(leida=False).update(leida=True)
    if request.headers.get("X-Requested-With") == "fetch":
        return JsonResponse({"ok": True})
    return redirect("notificaciones:lista")


# --- PWA y Web Push ---
import json  # noqa: E402

from django.conf import settings  # noqa: E402
from django.http import HttpResponse  # noqa: E402
from django.templatetags.static import static  # noqa: E402
from django.views.decorators.cache import cache_control, never_cache  # noqa: E402

from .models import SuscripcionPush  # noqa: E402


import time  # noqa: E402

VERSION_SW = str(int(time.time()))  # cambia en cada arranque/despliegue: renueva la caché


# 1 hora: el navegador lo pide en cada página; corto para que un despliegue (íconos con hash nuevo) llegue pronto.
@cache_control(max_age=3600, public=True)
def manifiesto(request):
    datos = {
        "name": "TallerYa", "short_name": "TallerYa",
        "description": "Talleres de motos en Medellín, tu garaje y avisos de mantenimiento.",
        "lang": "es-CO", "start_url": "/?origen=app", "scope": "/", "id": "/",
        "display": "standalone", "background_color": "#111517", "theme_color": "#111517",
        "icons": [
            {"src": static("talleres/img/pwa/icon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": static("talleres/img/pwa/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": static("talleres/img/pwa/icon-maskable-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    return HttpResponse(json.dumps(datos), content_type="application/manifest+json")


@never_cache
def service_worker(request):
    """Se sirve desde la raíz para que controle todo el sitio."""
    return render(request, "notificaciones/sw.js", {"version": VERSION_SW, "offline_url": reverse("notificaciones:sin_conexion"),
                                     "icono": static("talleres/img/pwa/icon-192.png"),
                                     "insignia": static("talleres/img/pwa/badge-96.png")},
                  content_type="application/javascript")


def sin_conexion(request):
    return render(request, "notificaciones/sin_conexion.html")


@login_required
def push_estado(request):
    return JsonResponse({
        "disponible": bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY),
        "clave": settings.VAPID_PUBLIC_KEY,
        "activa": request.user.suscripciones_push.exists(),
    })


@login_required
@require_POST
def push_suscribir(request):
    try:
        d = json.loads(request.body)
        endpoint, p256dh, auth = d["endpoint"], d["keys"]["p256dh"], d["keys"]["auth"]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    if not (isinstance(endpoint, str) and endpoint.startswith("https://") and len(endpoint) < 1000):
        return JsonResponse({"ok": False}, status=400)
    SuscripcionPush.objects.update_or_create(
        endpoint=endpoint,
        defaults={"usuario": request.user, "p256dh": str(p256dh)[:200], "auth": str(auth)[:100],
                  "agente": request.headers.get("User-Agent", "")[:200]},
    )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def push_desactivar(request):
    try:
        endpoint = json.loads(request.body).get("endpoint", "")
    except (ValueError, AttributeError):
        endpoint = ""
    qs = request.user.suscripciones_push.all()
    if endpoint:
        qs = qs.filter(endpoint=endpoint)
    qs.delete()
    return JsonResponse({"ok": True})
