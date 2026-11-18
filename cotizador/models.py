"""Caché de cotizaciones de repuestos (piloto). Tablas propias: borrar la app no toca ninguna otra tabla."""
from datetime import timedelta

from django.db import models
from django.utils import timezone

VIGENCIA = timedelta(hours=24)


class Cotizacion(models.Model):
    """Una búsqueda de precios ya hecha. `clave` es la consulta normalizada: dos personas que cotizan la misma pieza
    de la misma moto comparten la fila (y la consulta a Mercado Libre)."""

    class Fuente(models.TextChoices):
        MERCADOLIBRE = "mercadolibre", "Mercado Libre"
        EJEMPLO = "ejemplo", "Ejemplo (sin credenciales)"

    clave = models.CharField(max_length=200, unique=True)
    consulta = models.CharField(max_length=200, help_text="Texto que se buscó (solo la pieza y la moto)")
    # Sin ForeignKey a garaje: la app se puede quitar sin migraciones en otras apps.
    parte_id = models.PositiveIntegerField("ParteDespiece.pk", null=True, blank=True, db_index=True)
    codigo = models.CharField("código de repuesto", max_length=30, blank=True)
    nombre = models.CharField("nombre de la pieza", max_length=120, blank=True)
    moto = models.CharField("marca y línea", max_length=120, blank=True)
    minimo = models.PositiveIntegerField(null=True, blank=True)
    tipico = models.PositiveIntegerField("típico (mediana)", null=True, blank=True)
    maximo = models.PositiveIntegerField(null=True, blank=True)
    vendedores = models.JSONField(default=list, blank=True,
                                  help_text="Hasta 5: titulo, precio, enlace, ciudad, vendedor")
    encontrados = models.PositiveSmallIntegerField(default=0, help_text="Resultados que devolvió la fuente")
    descartados = models.PositiveSmallIntegerField(default=0, help_text="Resultados filtrados por no ser la pieza")
    fuente = models.CharField(max_length=20, choices=Fuente.choices)
    pedidos = models.PositiveIntegerField(default=0, help_text="Veces que la pidieron (para el refresco nocturno)")
    consultado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-pedidos"]
        verbose_name = "cotización"
        verbose_name_plural = "cotizaciones"

    def __str__(self):
        return f"{self.consulta} · {self.tipico or '—'}"

    @property
    def vigente(self):
        return timezone.now() - self.consultado_en < VIGENCIA

    @property
    def es_ejemplo(self):
        return self.fuente == self.Fuente.EJEMPLO


class TokenMercadoLibre(models.Model):
    """Access token de Mercado Libre (dura 6 h) y su refresh token (de un solo uso: cada renovación trae uno nuevo,
    por eso se guarda aquí y no solo en una variable de entorno). Una sola fila."""

    access_token = models.CharField(max_length=300)
    refresh_token = models.CharField(max_length=300, blank=True)
    vence = models.DateTimeField()
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "token de Mercado Libre"
        verbose_name_plural = "token de Mercado Libre"
