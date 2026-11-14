from urllib.parse import quote

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.text import slugify

from .utils import codigo_aleatorio


class Barrio(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    ciudad = models.CharField(max_length=80, default="Medellín")

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    nombre = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Taller(models.Model):
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    descripcion = models.TextField(blank=True)
    responsable = models.CharField(max_length=120)
    whatsapp = models.CharField(max_length=20, help_text="Con indicativo, solo números. Ej: 573001234567")
    direccion = models.CharField(max_length=200)
    barrio = models.ForeignKey(Barrio, on_delete=models.PROTECT, related_name="talleres")
    horario = models.CharField(max_length=120, blank=True, help_text="Ej: Lun-Sáb 8am-6pm")
    servicios = models.ManyToManyField(Servicio, related_name="talleres")
    marcas = models.ManyToManyField(Marca, related_name="talleres", blank=True)
    foto = models.ImageField(upload_to="talleres/", blank=True)
    verificado = models.BooleanField(default=False)
    activo = models.BooleanField(default=False, help_text="Visible en el directorio")
    destacado = models.BooleanField(default=False, help_text="Plan pro: aparece primero")
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="taller",
        help_text="Cuenta del taller: sus respuestas en el foro salen con insignia de taller.",
    )
    pin_canje = models.CharField(
        "PIN de canje", max_length=6, unique=True, null=True, blank=True,
        help_text="El taller lo usa para validar cupones en /canjear/. Compártelo solo con el taller.",
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-destacado", "-verificado", "nombre"]
        verbose_name_plural = "talleres"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre) or "taller"
            slug, n = base, 2
            while Taller.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        if not self.pin_canje:
            self.pin_canje = self.generar_pin()
        super().save(*args, **kwargs)

    @staticmethod
    def generar_pin():
        while True:
            pin = codigo_aleatorio(6, "0123456789")
            if not Taller.objects.filter(pin_canje=pin).exists():
                return pin

    def get_absolute_url(self):
        return reverse("talleres:detalle", args=[self.slug])

    @property
    def calificacion(self):
        return self.resenas.filter(visible=True).aggregate(p=Avg("estrellas"))["p"]

    @property
    def ubicacion(self):
        """Dirección completa para buscar el taller en el mapa."""
        return f"{self.direccion}, {self.barrio.nombre}, {self.barrio.ciudad}, Antioquia, Colombia"

    @property
    def mapa_embebido(self):
        # Mapa de Google sin clave de API (se busca por la dirección: el taller no guarda coordenadas).
        return f"https://www.google.com/maps?q={quote(self.ubicacion)}&output=embed&hl=es"

    @property
    def como_llegar(self):
        return f"https://www.google.com/maps/dir/?api=1&destination={quote(self.ubicacion)}"

    @property
    def whatsapp_url(self):
        return f"https://wa.me/{self.whatsapp}?text={quote(f'Hola {self.nombre}, te encontré en TallerYa.')}"


class SolicitudCita(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADA = "confirmada", "Confirmada"
        ATENDIDA = "atendida", "Atendida"
        CANCELADA = "cancelada", "Cancelada"

    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name="solicitudes")
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=20)
    moto = models.CharField(max_length=80, help_text="Marca y modelo. Ej: Yamaha NMAX")
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True)
    fecha_preferida = models.DateField()
    detalle = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "solicitud de cita"
        verbose_name_plural = "solicitudes de cita"

    def __str__(self):
        return f"{self.nombre} → {self.taller} ({self.fecha_preferida})"


class FotoTaller(models.Model):
    """Fotos que el taller sube a su perfil (local, trabajos, equipo)."""
    MAXIMO = 8
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="talleres/galeria/")
    descripcion = models.CharField(max_length=120, blank=True)
    orden = models.PositiveSmallIntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["orden", "creado"]
        verbose_name = "foto del taller"
        verbose_name_plural = "fotos del taller"

    def __str__(self):
        return f"Foto de {self.taller}"


class Resena(models.Model):
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name="resenas")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="resenas", help_text="Cuenta que la escribió (si estaba conectada)")
    nombre = models.CharField(max_length=80)
    estrellas = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=600)
    visible = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "reseña"

    def __str__(self):
        return f"{self.estrellas}★ {self.taller} - {self.nombre}"
