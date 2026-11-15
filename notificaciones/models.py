"""Modelo de notificación dentro del sitio: título, texto, enlace, tipo y si ya se leyó."""
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

    @property
    def accion(self):
        """Texto del botón: "Pedir SOAT", "Ver CDA"… (vacío si el aviso no lleva botón)."""
        from garaje.avisos import accion_de_clave
        return accion_de_clave(self.clave)

    @property
    def urgente(self):
        from garaje.avisos import es_urgente
        return not self.leida and es_urgente(self.clave)


class SuscripcionPush(models.Model):
    """Un celular o navegador que activó los avisos push de una persona (Web Push)."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="suscripciones_push")
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    agente = models.CharField(max_length=200, blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "suscripción push"
        verbose_name_plural = "suscripciones push"

    def __str__(self):
        return f"push de {self.usuario}"

    def como_dict(self):
        return {"endpoint": self.endpoint, "keys": {"p256dh": self.p256dh, "auth": self.auth}}
