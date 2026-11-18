"""Eventos que no necesitan tocar las vistas: inicio de sesión (correo o Google) y activación de Plus."""
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from . import nucleo


@receiver(user_logged_in, dispatch_uid="metricas_inicio_sesion")
def inicio_sesion(sender, request, user, **kwargs):
    """Se anota y el middleware lo registra al final: si en la misma petición hubo registro, no cuenta aparte."""
    if request is not None:
        ruta = getattr(getattr(request, "resolver_match", None), "url_name", "") or ""
        request._metricas_login = "google" if "google" in ruta else "correo"


def _conectar_plus():
    from cuentas.models import Suscripcion

    @receiver(pre_save, sender=Suscripcion, dispatch_uid="metricas_plus_antes")
    def antes(sender, instance, **kwargs):
        instance._metricas_estado_previo = (
            sender.objects.filter(pk=instance.pk).values_list("estado", flat=True).first() if instance.pk else None)

    @receiver(post_save, sender=Suscripcion, dispatch_uid="metricas_plus_despues")
    def despues(sender, instance, **kwargs):
        if not nucleo.activas() or instance.estado != sender.Estado.ACTIVA:
            return
        if getattr(instance, "_metricas_estado_previo", None) == sender.Estado.ACTIVA:
            return  # renovación o edición: ya estaba activa
        from django.utils import timezone

        from .models import Evento
        usuario_id = getattr(instance.motociclista, "usuario_id", None)
        Evento.objects.create(dia=timezone.localdate(), tipo=Evento.FUNCION, nombre="plus_activado",
                              visitante=f"u{usuario_id}" if usuario_id else "sistema", usuario_id=usuario_id)


_conectar_plus()
