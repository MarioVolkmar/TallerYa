"""Evalúa las insignias cuando ocurre el hecho, sin esperar a que el usuario abra /insignias/.

- Voto a una respuesta o solución elegida → "aporte" del autor de la respuesta.
- Reseña guardada → "resena" de quien la escribió.
- Servicio verificado por un taller o cupón canjeado en el local → "servicio" del dueño.
Lo que depende del tiempo (rodadas que ya pasaron) lo revisa
el comando diario `evaluar_logros`. Un fallo aquí nunca debe tumbar la acción del usuario.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from . import reglas

log = logging.getLogger(__name__)


def _evaluar(usuario, clave):
    if usuario is None:
        return
    try:
        reglas.evaluar(usuario, [clave])
    except Exception:  # noqa: BLE001
        log.exception("No se pudieron evaluar las insignias (%s) de %s", clave, usuario.pk)


@receiver(post_save, sender="foro.Voto")
def voto_guardado(sender, instance, created, **kwargs):
    if created and instance.respuesta_id:
        _evaluar(instance.respuesta.autor, "aporte")


@receiver(post_save, sender="foro.Pregunta")
def solucion_elegida(sender, instance, **kwargs):
    if instance.mejor_respuesta_id:
        _evaluar(instance.mejor_respuesta.autor, "aporte")


@receiver(post_save, sender="talleres.Resena")
def resena_guardada(sender, instance, **kwargs):
    _evaluar(instance.usuario, "resena")


@receiver(post_save, sender="garaje.RegistroServicio")
def servicio_verificado(sender, instance, **kwargs):
    if instance.verificado:
        _evaluar(getattr(instance.moto.motociclista, "usuario", None), "servicio")


@receiver(post_save, sender="cupones.CodigoCupon")
def cupon_canjeado(sender, instance, **kwargs):
    if instance.canjeado_en:
        _evaluar(getattr(instance.motociclista, "usuario", None), "servicio")
