"""Mecánicos a domicilio: mecánicos sin taller propio que van a donde está la moto.

TallerYa solo los promociona: el acuerdo, el pago y la garantía son entre el motociclista y el mecánico.
Un perfil solo sale en el listado público cuando un administrador lo aprueba (estado APROBADO).
"""
from urllib.parse import quote
from uuid import uuid4

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Zona(models.Model):
    """Comuna de Medellín o municipio del Valle de Aburrá donde un mecánico atiende (lista fija, ver migración 0002)."""
    nombre = models.CharField(max_length=80)
    ciudad = models.CharField(max_length=80, default="Medellín")
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "nombre"]
        constraints = [models.UniqueConstraint(fields=["nombre", "ciudad"], name="zona_unica_por_ciudad")]

    def __str__(self):
        return self.nombre if self.ciudad == "Medellín" else self.ciudad


class TipoServicio(models.Model):
    """Trabajos que se pueden hacer donde está la moto (lista fija, ver migración 0002)."""
    nombre = models.CharField(max_length=80, unique=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "servicio a domicilio"
        verbose_name_plural = "servicios a domicilio"

    def __str__(self):
        return self.nombre


def ruta_foto(instancia, nombre):
    # Nombre aleatorio y siempre .jpg: la foto se vuelve a codificar al subirla (sin EXIF ni el nombre original).
    return f"domicilio/{uuid4().hex}.jpg"


class MecanicoQuerySet(models.QuerySet):
    def publicados(self):
        return self.filter(estado=MecanicoDomicilio.Estado.APROBADO)


class MecanicoDomicilio(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente de revisión"
        APROBADO = "aprobado", "Aprobado (publicado)"
        SUSPENDIDO = "suspendido", "Suspendido"

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="mecanico_domicilio", help_text="Cuenta del mecánico (la única que lo edita)")
    nombre = models.CharField("nombre visible", max_length=80)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    foto = models.ImageField(upload_to=ruta_foto, blank=True)
    whatsapp = models.CharField("WhatsApp o celular", max_length=12,
                                help_text="Con indicativo, solo números. Ej: 573001234567")
    zonas = models.ManyToManyField(Zona, related_name="mecanicos", verbose_name="zonas donde atiende")
    servicios = models.ManyToManyField(TipoServicio, related_name="mecanicos", verbose_name="servicios que ofrece")
    marcas = models.ManyToManyField("talleres.Marca", related_name="mecanicos_domicilio", blank=True)
    anios_experiencia = models.PositiveSmallIntegerField("años de experiencia", default=0,
                                                         validators=[MaxValueValidator(60)])
    horario = models.CharField(max_length=120, blank=True, help_text="Ej: Lun-Sáb 7am-6pm")
    urgencias = models.BooleanField("atiende urgencias", default=False,
                                    help_text="Sale a atender motos varadas, también fuera de su horario")
    tarifa_visita = models.PositiveIntegerField("tarifa de visita orientativa (pesos)", null=True, blank=True,
                                                validators=[MaxValueValidator(1_000_000)],
                                                help_text="Lo que cobra por ir a ver la moto, sin repuestos")
    descripcion = models.TextField("descripción", max_length=600, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True)
    verificado = models.BooleanField(default=False, help_text="TallerYa revisó su identidad y experiencia")
    notas_admin = models.TextField("notas internas", blank=True, help_text="Solo las ve el equipo de TallerYa")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = MecanicoQuerySet.as_manager()

    class Meta:
        ordering = ["-verificado", "nombre"]
        verbose_name = "mecánico a domicilio"
        verbose_name_plural = "mecánicos a domicilio"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)[:80] or "mecanico"
            slug, n = base, 2
            while MecanicoDomicilio.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("domicilio:ficha", args=[self.slug])

    @property
    def publicado(self):
        return self.estado == self.Estado.APROBADO

    @property
    def iniciales(self):
        partes = [p for p in self.nombre.split() if p[:1].isalpha()]
        return "".join(p[0] for p in partes[:2]).upper() or "M"

    @property
    def whatsapp_url(self):
        texto = f"Hola {self.nombre}, te encontré en TallerYa (mecánicos a domicilio)."
        return f"https://wa.me/{self.whatsapp}?text={quote(texto)}"

    @property
    def tarifa_texto(self):
        from talleres.utils import pesos
        return pesos(self.tarifa_visita) if self.tarifa_visita else ""


class ResenaMecanico(models.Model):
    """Como talleres.Resena, pero solo con cuenta: una por cuenta y mecánico (si vuelve a calificar, se actualiza)."""
    mecanico = models.ForeignKey(MecanicoDomicilio, on_delete=models.CASCADE, related_name="resenas")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resenas_mecanicos")
    nombre = models.CharField(max_length=80)
    estrellas = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=600)
    visible = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "reseña de mecánico"
        verbose_name_plural = "reseñas de mecánicos"
        constraints = [models.UniqueConstraint(fields=["mecanico", "usuario"], name="una_resena_por_cuenta_y_mecanico")]

    def __str__(self):
        return f"{self.estrellas}★ {self.mecanico} - {self.nombre}"
