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
        if self.motociclista.usuario_id:
            from django.urls import reverse

            from notificaciones.models import Notificacion
            from notificaciones.servicios import notificar
            notificar(self.motociclista.usuario, f"plus:{self.pk}:{self.vence}", "TallerYa Plus activo",
                      f"Tienes Plus hasta el {self.vence:%d/%m/%Y}.", reverse("cuentas:plus"), Notificacion.Tipo.PLUS)
        # Una sola suscripción activa por motociclista: la nueva absorbe a las anteriores.
        otras.update(estado=self.Estado.CANCELADA)


def ruta_avatar(instancia, nombre):
    # Nombre aleatorio: la foto no lleva el correo ni el nombre original del archivo.
    from uuid import uuid4
    return f"avatares/{uuid4().hex}.jpg"


class Perfil(models.Model):
    """Datos de la cuenta que sirven para cualquier rol (motero, taller o administrador)."""

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    avatar_foto = models.ImageField("foto de perfil", upload_to=ruta_avatar, blank=True)
    avatar_predisenado = models.CharField("avatar prediseñado", max_length=20, blank=True)
    google_sub = models.CharField("ID de Google", max_length=64, unique=True, null=True, blank=True, editable=False,
                                  help_text="Identificador de la cuenta de Google vinculada (no es el correo)")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfiles"

    def __str__(self):
        return f"Perfil de {self.usuario}"

    @classmethod
    def de(cls, usuario):
        perfil, _ = cls.objects.get_or_create(usuario=usuario)
        return perfil
