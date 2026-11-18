from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from cupones.models import Motociclista

PLATAFORMAS = [
    ("rappi", "Rappi"), ("didi", "DiDi Food"), ("ifood", "iFood"), ("picap", "Picap"),
    ("mensajeria", "Mensajería"), ("restaurante", "Domicilios de un negocio"), ("otra", "Otra"),
]


class PerfilDomiciliario(models.Model):
    """El motero se marca como domiciliario: con esto se calcula el plan intensivo y el balance."""

    motociclista = models.OneToOneField(Motociclista, on_delete=models.CASCADE, related_name="domiciliario")
    moto = models.ForeignKey("garaje.Moto", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
                             verbose_name="moto con la que trabaja")
    plataformas = models.JSONField(default=list, blank=True, help_text="Claves de domiciliarios.models.PLATAFORMAS")
    km_semana = models.PositiveIntegerField("km por semana", validators=[MinValueValidator(50), MaxValueValidator(5000)])
    dias_semana = models.PositiveSmallIntegerField("días que trabaja a la semana", default=6,
                                                   validators=[MinValueValidator(1), MaxValueValidator(7)])
    # Sube al anular los enlaces del comprobante: los enlaces viejos llevan la versión anterior y dejan de abrir.
    version_comprobante = models.PositiveIntegerField(default=1, editable=False)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "domiciliario"
        verbose_name_plural = "domiciliarios"

    def __str__(self):
        return f"{self.motociclista} · {self.km_semana} km/semana"

    @property
    def nombres_plataformas(self):
        nombres = dict(PLATAFORMAS)
        return [nombres[p] for p in self.plataformas if p in nombres]


class Jornada(models.Model):
    """Cierre del día: lo que ganó. Los km van a garaje.LecturaKm y la gasolina a garaje.Gasto (no se duplican aquí)."""

    perfil = models.ForeignKey(PerfilDomiciliario, on_delete=models.CASCADE, related_name="jornadas")
    fecha = models.DateField(default=timezone.localdate)
    ingreso = models.PositiveIntegerField("lo que ganó (COP)", validators=[MaxValueValidator(3_000_000)])
    km_fin = models.PositiveIntegerField("km al cerrar", null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        constraints = [models.UniqueConstraint(fields=["perfil", "fecha"], name="una_jornada_por_dia")]

    def __str__(self):
        return f"{self.perfil.motociclista} · {self.fecha:%d/%m/%Y} · ${self.ingreso}"


class TallerAliado(models.Model):
    """Taller apto para domiciliarios: atiende en el día o en horario extendido. Lo marca el equipo desde el admin."""

    taller = models.OneToOneField("talleres.Taller", on_delete=models.CASCADE, related_name="aliado_domiciliarios")
    en_el_dia = models.BooleanField("servicio en el día", default=True,
                                    help_text="Cambio de aceite, frenos o cadena sin dejar la moto de un día para otro")
    horario_extendido = models.BooleanField(default=False, help_text="Abre antes de las 7 a. m. o cierra después de las 7 p. m.")
    horario_texto = models.CharField("horario para domiciliarios", max_length=80, blank=True, help_text="Ej: Lun-Sáb 6am-9pm")
    descuento = models.CharField(max_length=120, blank=True, help_text="Solo lo ven los domiciliarios con Plus. Ej: 10% en mano de obra")
    activo = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "taller__nombre"]
        verbose_name = "taller aliado de domiciliarios"
        verbose_name_plural = "talleres aliados de domiciliarios"

    def __str__(self):
        return str(self.taller)
