"""Modelos del foro: preguntas por categoría, respuestas (con mejor respuesta), reportes de moderación y votos."""
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify

from talleres.models import Marca

REPORTES_PARA_OCULTAR = 3


class Categoria(models.TextChoices):
    MANTENIMIENTO = "mantenimiento", "Mantenimiento"
    FALLAS = "fallas", "Fallas y ruidos"
    RUTAS = "rutas", "Rutas y paseos"
    REPUESTOS = "repuestos", "Compra y venta de repuestos"
    TALLERES = "talleres", "Talleres"
    GENERAL = "general", "General"


class Pregunta(models.Model):
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preguntas")
    titulo = models.CharField(max_length=150, help_text="Ej: ¿Cada cuánto cambio el aceite de una NKD 125?")
    cuerpo = models.TextField(max_length=3000)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name="preguntas")
    linea = models.ForeignKey("garaje.LineaMoto", on_delete=models.SET_NULL, null=True, blank=True, related_name="preguntas",
                              verbose_name="línea de moto")
    categoria = models.CharField(max_length=15, choices=Categoria.choices, default=Categoria.GENERAL, db_index=True)
    vistas = models.PositiveIntegerField(default=0)
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


class Voto(models.Model):
    """Voto "me sirvió" de un usuario a una pregunta o a una respuesta (uno por usuario y publicación)."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votos_foro")
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, null=True, blank=True, related_name="votos")
    respuesta = models.ForeignKey(Respuesta, on_delete=models.CASCADE, null=True, blank=True, related_name="votos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(pregunta__isnull=False, respuesta__isnull=True) | Q(pregunta__isnull=True, respuesta__isnull=False),
                name="voto_un_solo_objetivo",
            ),
            models.UniqueConstraint(fields=["usuario", "pregunta"], condition=Q(pregunta__isnull=False), name="un_voto_por_pregunta"),
            models.UniqueConstraint(fields=["usuario", "respuesta"], condition=Q(respuesta__isnull=False), name="un_voto_por_respuesta"),
        ]


class Rodada(models.Model):
    """Rodada o evento: sus comentarios y reportes son los de su pregunta del foro (tema "Rutas y paseos")."""

    class Nivel(models.TextChoices):
        PRINCIPIANTE = "principiante", "Principiante · ritmo suave"
        INTERMEDIO = "intermedio", "Intermedio"
        AVANZADO = "avanzado", "Avanzado · ruta exigente"

    pregunta = models.OneToOneField(Pregunta, on_delete=models.CASCADE, related_name="rodada")
    organizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rodadas_organizadas")
    fecha_hora = models.DateTimeField("fecha y hora", db_index=True)
    punto_encuentro = models.CharField(
        "punto de encuentro", max_length=150,
        help_text="Un lugar público: estación del metro, parque, bomba de gasolina. Nunca una casa o apartamento.",
    )
    destino = models.CharField("destino o ruta", max_length=200, help_text="Ej: Santa Elena por Las Palmas, regreso por Guarne")
    nivel = models.CharField(max_length=15, choices=Nivel.choices, default=Nivel.PRINCIPIANTE)
    cupo = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Déjalo vacío si no hay límite.")

    class Meta:
        ordering = ["fecha_hora"]

    def __str__(self):
        return self.pregunta.titulo

    @property
    def titulo(self):
        return self.pregunta.titulo

    @property
    def pasada(self):
        from django.utils import timezone
        return self.fecha_hora < timezone.now()

    def get_absolute_url(self):
        return reverse("foro:rodada", args=[self.pk])


class Asistencia(models.Model):
    """Un "Voy" de un usuario a una rodada."""
    rodada = models.ForeignKey(Rodada, on_delete=models.CASCADE, related_name="asistencias")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="asistencias_rodada")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]
        constraints = [models.UniqueConstraint(fields=["rodada", "usuario"], name="un_voy_por_rodada")]
