from django.apps import AppConfig


class ProveedoresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "proveedores"
    verbose_name = "Proveedores de servicios"

    def ready(self):
        # Registra las acciones de la consola (aprobar, pausar, verificar, enlace, eliminar)
        from . import consola  # noqa: F401
