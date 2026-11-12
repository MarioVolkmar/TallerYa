from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify

from talleres.models import Marca

REPORTES_PARA_OCULTAR = 3


class Pregunta(models.Model):
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preguntas")
    titulo = models.CharField(max_length=150, help_text="Ej: ¿Cada cuánto cambio el aceite de una NKD 125?")
    cuerpo = models.TextField(max_length=3000)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name="preguntas")
    mejor_respuesta = models.OneToOneField(
        "Respuesta", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )
    visible = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return self.titulo

    @property
    def slug(self):
        return slugify(self.titulo)[:60] or "pregunta"

    def get_absolute_url(self):
        return reverse("foro:pregunta", args=[self.pk, self.slug])


class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name="respuestas")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="respuestas")
    cuerpo = models.TextField(max_length=3000)
    visible = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]

    def __str__(self):
        return f"Respuesta de {self.autor} a «{self.pregunta}»"

    def get_absolute_url(self):
        return f"{self.pregunta.get_absolute_url()}#r{self.pk}"


class Reporte(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reportes")
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, null=True, blank=True, related_name="reportes")
    respuesta = models.ForeignKey(Respuesta, on_delete=models.CASCADE, null=True, blank=True, related_name="reportes")
    motivo = models.CharField(max_length=200, blank=True)
    revisado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["revisado", "-creado"]
        constraints = [
            models.CheckConstraint(
                condition=Q(pregunta__isnull=False, respuesta__isnull=True) | Q(pregunta__isnull=True, respuesta__isnull=False),
                name="reporte_un_solo_objetivo",
            ),
            models.UniqueConstraint(fields=["usuario", "pregunta"], condition=Q(pregunta__isnull=False), name="un_reporte_por_pregunta"),
            models.UniqueConstraint(fields=["usuario", "respuesta"], condition=Q(respuesta__isnull=False), name="un_reporte_por_respuesta"),
        ]

    def __str__(self):
        return f"Reporte de {self.usuario} sobre {self.objetivo}"

    @property
    def objetivo(self):
        return self.pregunta or self.respuesta
