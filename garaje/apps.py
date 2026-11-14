from django.apps import AppConfig


def _renovar_cache_despiece(**kwargs):
    """Si cambia un despiece, una lámina o una pieza (admin, importador), la caché del visor se renueva."""
    from django.core.cache import caches
    cache = caches["despiece"]
    cache.set("generacion", cache.get("generacion", 0) + 1, None)


class GarajeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "garaje"
    verbose_name = "Garaje y mantenimiento"

    def ready(self):
        from django.db.models.signals import post_delete, post_save
        for nombre in ("Despiece", "Lamina", "ParteDespiece"):
            modelo = self.get_model(nombre)
            post_save.connect(_renovar_cache_despiece, sender=modelo, dispatch_uid=f"cache-despiece-save-{nombre}")
            post_delete.connect(_renovar_cache_despiece, sender=modelo, dispatch_uid=f"cache-despiece-del-{nombre}")
