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
    """Taller con descuento para domiciliarios verificados con Plus. Lo marca el equipo desde el admin.
    No se muestra en el directorio: solo dentro de TallerYa Ruta (Mi ruta y la presentación)."""

    taller = models.OneToOneField("talleres.Taller", on_delete=models.CASCADE, related_name="aliado_domiciliarios")
    descuento = models.CharField(max_length=120, help_text="Lo usan los domiciliarios verificados con Plus. Ej: 10% en mano de obra")
    activo = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "taller__nombre"]
        verbose_name = "descuento de taller para domiciliarios"
        verbose_name_plural = "descuentos de talleres para domiciliarios"

    def __str__(self):
        return f"{self.taller} · {self.descuento}"


def ruta_verificacion(instancia, nombre):
    # Nombre aleatorio y la extensión del contenido real (forms.py ya la validó): no revela nombre, placa ni plataforma.
    from pathlib import Path
    from uuid import uuid4
    return f"verificacion_ruta/{uuid4().hex}{Path(nombre).suffix.lower()}"


def _almacen_privado():
    # Fuera de MEDIA_ROOT (PRIVADO_ROOT): /media/ nunca las sirve; solo la vista verificacion_foto, al dueño o al staff.
    from garaje.models import AlmacenPrivado
    return AlmacenPrivado()


class Verificacion(models.Model):
    """«Domiciliario verificado» con dos fotos: el pantallazo del perfil de repartidor en la app (donde se ve la moto: placa
    o datos del vehículo) y una foto de la moto con la placa visible. El revisor compara las dos placas con la de una moto
    de su garaje. Las fotos se borran al aprobar o rechazar: queda solo el resultado (Ley 1581)."""

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Por revisar"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"
        VENCIDA = "vencida", "Vencida"

    perfil = models.ForeignKey(PerfilDomiciliario, on_delete=models.CASCADE, related_name="verificaciones")
    plataforma = models.CharField(max_length=20, choices=PLATAFORMAS)
    captura = models.FileField("pantallazo del perfil en la app", storage=_almacen_privado, upload_to=ruta_verificacion,
                               blank=True)
    foto_moto = models.FileField("foto de la moto con la placa", storage=_almacen_privado, upload_to=ruta_verificacion,
                                 blank=True)
    moto = models.ForeignKey("garaje.Moto", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
                             verbose_name="moto del garaje que se verifica")
    autorizacion = models.DateTimeField("autorizó el tratamiento de datos")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True)
    motivo = models.CharField("motivo del rechazo", max_length=200, blank=True)
    revisado_por = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    revisado_en = models.DateTimeField(null=True, blank=True)
    vence = models.DateField(null=True, blank=True)
    renovaciones = models.PositiveSmallIntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "verificación de domiciliario"
        verbose_name_plural = "verificaciones de domiciliarios"

    def __str__(self):
        return f"{self.perfil.motociclista} · {self.get_estado_display()}"

    @property
    def tiene_fotos(self):
        return bool(self.captura or self.foto_moto)

    def borrar_fotos(self):
        """Borra los archivos del disco y vacía los campos (no guarda: lo hace quien llama)."""
        for campo in (self.captura, self.foto_moto):
            if campo:
                campo.delete(save=False)


def verificacion_vigente(perfil, hoy=None):
    """La verificación aprobada y sin vencer del perfil, o None."""
    if not perfil or not perfil.pk:
        return None
    hoy = hoy or timezone.localdate()
    return (perfil.verificaciones.filter(estado=Verificacion.Estado.APROBADA, vence__gte=hoy)
            .order_by("-vence").first())
