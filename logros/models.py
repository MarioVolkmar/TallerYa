"""Insignias ganadas (una fila por logro, con su referencia para no contar dos veces) y canjes de puntos por cupones."""
from django.conf import settings
from django.db import models


class Logro(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="logros")
    clave = models.CharField(max_length=30, db_index=True)  # ver reglas.INSIGNIAS
    referencia = models.CharField(max_length=40, help_text="Qué lo originó: mes, respuesta, rodada o taller")
    puntos = models.PositiveSmallIntegerField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        constraints = [models.UniqueConstraint(fields=["usuario", "clave", "referencia"], name="logro_unico")]

    def __str__(self):
        return f"{self.usuario} · {self.clave} ({self.referencia})"

    @property
    def insignia(self):
        from .reglas import INSIGNIAS
        return INSIGNIAS.get(self.clave)


class Canje(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="canjes_logros")
    codigo = models.OneToOneField("cupones.CodigoCupon", verbose_name="código", on_delete=models.PROTECT, related_name="canje_logros")
    puntos = models.PositiveIntegerField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.usuario} canjeó {self.puntos} pts"
