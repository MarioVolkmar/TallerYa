from django.apps import AppConfig


class ConsolaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "consola"
    verbose_name = "Consola de administración"

    def ready(self):
        # Registra las acciones declaradas (@accion) de cada sección
        from .vistas import citas, configuracion, cupones, moderacion, talleres, usuarios  # noqa: F401
