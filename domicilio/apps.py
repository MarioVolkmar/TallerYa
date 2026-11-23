from django.apps import AppConfig


class DomicilioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "domicilio"
    verbose_name = "Mecánicos a domicilio"

    def ready(self):
        # Registra las acciones de la consola (aprobar, pausar, verificar): consola.acciones las busca por clave
        from . import consola  # noqa: F401
