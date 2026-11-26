"""Medición de uso propia (Ley 1581): sin IPs en claro, sin cookies nuevas, crudos 90 días y luego solo agregados.

- Evento: una fila por página vista o por función usada. `visitante` es "u<id>" con sesión o un hash de IP+navegador con
  sal del día (la sal se borra al cambiar de día: nadie, ni nosotros, puede unir visitas de días distintos).
- ResumenDiario: los conteos por día que se conservan para siempre.
- ActividadSemanal: qué usuarios con cuenta usaron la página cada semana (solo id interno), para la retención por cohorte.
"""
from django.db import models
from django.utils import timezone


class Evento(models.Model):
    VISTA, FUNCION = "v", "e"
    TIPOS = [(VISTA, "Página vista"), (FUNCION, "Función usada")]
    DISPOSITIVOS = [("c", "Celular"), ("t", "Tableta"), ("e", "Escritorio")]

    creado = models.DateTimeField(default=timezone.now)
    dia = models.DateField("día", db_index=True)
    tipo = models.CharField(max_length=1, choices=TIPOS)
    nombre = models.CharField(max_length=60)
    visitante = models.CharField(max_length=20)
    usuario_id = models.PositiveIntegerField(null=True, blank=True)
    dispositivo = models.CharField(max_length=1, choices=DISPOSITIVOS, default="e")
    referente = models.CharField(max_length=12, blank=True)
    datos = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "evento de uso"
        verbose_name_plural = "eventos de uso"
        indexes = [models.Index(fields=["dia", "tipo", "nombre"], name="metricas_dia_tipo_nombre")]

    def __str__(self):
        return f"{self.dia} {self.get_tipo_display()} {self.nombre}"


class ResumenDiario(models.Model):
    """clave: vista | evento | dispositivo | referente | busqueda | activos | _hecho."""
    dia = models.DateField("día")
    clave = models.CharField(max_length=20)
    valor = models.CharField(max_length=80, blank=True)
    total = models.PositiveIntegerField(default=0)
    unicos = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "resumen diario"
        verbose_name_plural = "resúmenes diarios"
        constraints = [models.UniqueConstraint(fields=["dia", "clave", "valor"], name="metricas_resumen_unico")]


class ActividadSemanal(models.Model):
    usuario_id = models.PositiveIntegerField()
    semana = models.DateField(help_text="Lunes de la semana")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["usuario_id", "semana"], name="metricas_actividad_unica")]


class SalDiaria(models.Model):
    """Sal aleatoria del día para el hash del visitante anónimo. Se borra al empezar el día siguiente."""
    dia = models.DateField("día", unique=True)
    valor = models.CharField(max_length=64)
