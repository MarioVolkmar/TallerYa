from django.apps import AppConfig


def _renovar_cache_despiece(**kwargs):
    """Si cambia un despiece, una lámina o una pieza (admin, importador), la caché del visor se renueva."""
    from django.core.cache import caches
    cache = caches["despiece"]
    cache.set("generacion", cache.get("generacion", 0) + 1, None)


def _mantenimiento_a_hoja_vida(sender, instance, created, raw=False, **kwargs):
    """Todo mantenimiento del plan (ficha, despiece, poner al día, admin, demo) queda también en la hoja de vida."""
    if created and not raw:
        from .hoja_vida import desde_mantenimiento
        from .plan import es_sin_idea
        if not es_sin_idea(instance):  # "Sin idea" no es un servicio hecho
            desde_mantenimiento(instance)


def _quitar_de_hoja_vida(sender, instance, **kwargs):
    """Si se borra un mantenimiento del plan, su registro propio (no el verificado) sale de la hoja de vida."""
    from .models import RegistroServicio
    RegistroServicio.objects.filter(mantenimiento=instance, verificado=False).delete()


class GarajeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "garaje"
    verbose_name = "Garaje y mantenimiento"

    def ready(self):
        from django.db.models.signals import post_delete, post_save, pre_delete
        mantenimiento = self.get_model("Mantenimiento")
        post_save.connect(_mantenimiento_a_hoja_vida, sender=mantenimiento, dispatch_uid="mantenimiento-hoja-vida")
        pre_delete.connect(_quitar_de_hoja_vida, sender=mantenimiento, dispatch_uid="mantenimiento-quitar-hoja")
        for nombre in ("Despiece", "Lamina", "ParteDespiece"):
            modelo = self.get_model(nombre)
            post_save.connect(_renovar_cache_despiece, sender=modelo, dispatch_uid=f"cache-despiece-save-{nombre}")
            post_delete.connect(_renovar_cache_despiece, sender=modelo, dispatch_uid=f"cache-despiece-del-{nombre}")
