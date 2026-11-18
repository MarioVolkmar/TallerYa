from django.apps import AppConfig


class DomiciliariosConfig(AppConfig):
    """TallerYa Ruta: plan para domiciliarios. Todo detrás de settings.DOMICILIARIOS_ACTIVO (apagado por defecto)."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "domiciliarios"
    verbose_name = "Domiciliarios (TallerYa Ruta)"
