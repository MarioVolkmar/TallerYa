from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    class Tipo(models.TextChoices):
        MANTENIMIENTO = "mantenimiento", "Mantenimiento"
        DOCUMENTO = "documento", "Documento"
        FORO = "foro", "Foro"
        TALLER = "taller", "Taller"
        PLUS = "plus", "Plus"
        GENERAL = "general", "General"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones")
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.GENERAL)
    titulo = models.CharField(max_length=120)
    texto = models.CharField(max_length=300, blank=True)
    url = models.CharField(max_length=300, blank=True)
    # Evita repetir el mismo aviso: p. ej. "plan:3:vencido:<firma>" o "foro-respuesta:15".
    clave = models.CharField(max_length=160)
    leida = models.BooleanField(default=False)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada"]
        constraints = [models.UniqueConstraint(fields=["usuario", "clave"], name="notificacion_unica_por_usuario")]
        indexes = [models.Index(fields=["usuario", "leida"])]
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"

    def __str__(self):
        return f"{self.titulo} → {self.usuario}"
