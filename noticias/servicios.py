"""Refresco automático del noticiero: si los titulares tienen más de unas horas, se actualizan en segundo plano."""
import logging
import threading
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from .models import FuenteNoticias

log = logging.getLogger(__name__)
CADA = timedelta(hours=3)
_candado = threading.Lock()


def refrescar_si_toca():
    if not getattr(settings, "NOTICIAS_AUTO", False):
        return
    viejas = FuenteNoticias.objects.filter(activa=True).filter(
        Q(ultima_lectura__isnull=True) | Q(ultima_lectura__lt=timezone.now() - CADA))
    if not viejas.exists() or not _candado.acquire(blocking=False):
        return

    def tarea():
        from .importar import importar_todas
        try:
            importar_todas()
        except Exception:
            log.exception("Falló el refresco de noticias")
        finally:
            connection.close()
            _candado.release()

    threading.Thread(target=tarea, daemon=True).start()
