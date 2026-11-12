from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from cupones.models import Motociclista


class Suscripcion(models.Model):
    """TallerYa Plus. Se paga por Nequi/transferencia y se activa a mano desde el admin."""

    class Estado(models.TextChoices):
        SOLICITADA = "solicitada", "Solicitada (esperando pago)"
        ACTIVA = "activa", "Activa"
        CANCELADA = "cancelada", "Cancelada"

    motociclista = models.ForeignKey(Motociclista, on_delete=models.CASCADE, related_name="suscripciones")
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.SOLICITADA)
    inicia = models.DateField(null=True, blank=True)
    vence = models.DateField(null=True, blank=True)
    referencia_pago = models.CharField(
        max_length=120, blank=True, help_text="Ej: número de comprobante Nequi o nota de la transferencia",
    )
    notas = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "suscripción Plus"
        verbose_name_plural = "suscripciones Plus"

    def __str__(self):
        return f"{self.motociclista} · {self.get_estado_display()}"

    @property
    def vigente(self):
        return self.estado == self.Estado.ACTIVA and self.vence is not None and self.vence >= timezone.localdate()

    def activar(self, dias=None):
        """Activa o renueva. Si ya hay días Plus vigentes, los nuevos se suman al final."""
        hoy = timezone.localdate()
        otras = self.motociclista.suscripciones.filter(estado=self.Estado.ACTIVA, vence__gte=hoy).exclude(pk=self.pk)
        base = max([hoy, *(s.vence for s in otras), *([self.vence] if self.vigente else [])])
        if not self.vigente:
            self.inicia = hoy
        self.estado = self.Estado.ACTIVA
        self.vence = base + timedelta(days=dias or settings.PLUS_DIAS)
        self.save()
        # Una sola suscripción activa por motociclista: la nueva absorbe a las anteriores.
        otras.update(estado=self.Estado.CANCELADA)
