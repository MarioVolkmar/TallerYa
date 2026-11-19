"""Quien se registró como domiciliario (sin moto aún) queda con su primera moto marcada «La uso para trabajar»."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from garaje.models import Moto

from .models import PerfilDomiciliario


@receiver(post_save, sender=Moto, dispatch_uid="domiciliarios_moto_de_trabajo")
def primera_moto_de_trabajo(sender, instance, created, raw=False, **kwargs):
    # Solo con la primera moto: si después apagó el interruptor y agrega otra, no se marca sola
    if created and not raw and not Moto.objects.filter(motociclista_id=instance.motociclista_id).exclude(pk=instance.pk).exists():
        PerfilDomiciliario.objects.filter(motociclista_id=instance.motociclista_id, moto__isnull=True).update(moto=instance)
