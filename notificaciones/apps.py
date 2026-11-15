import logging

from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notificaciones"
    verbose_name = "notificaciones"

    def ready(self):
        from django.db.models.signals import post_save

        from .models import Notificacion
        from .push import enviar_notificacion

        def _al_crear(sender, instance, created, **kwargs):
            # Cada aviso nuevo del sitio sale también como push (si hay claves y la persona lo activó).
            if created:
                try:
                    enviar_notificacion(instance)
                except Exception:
                    logging.getLogger(__name__).exception("No se pudo enviar el push")

        post_save.connect(_al_crear, sender=Notificacion, dispatch_uid="notificacion_push")
