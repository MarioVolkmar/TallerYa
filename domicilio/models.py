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
from django.utils.crypto import salted_hmac
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
    # Como en el perfil del taller (talleres/perfil.py): listas cerradas para que se puedan comparar
    especialidades = models.JSONField(default=list, blank=True, help_text="Claves de talleres.perfil.ESPECIALIDADES")
    compromisos = models.JSONField("cómo trabaja", default=list, blank=True, help_text="Claves de talleres.perfil.COMPROMISOS")
    garantia_meses = models.PositiveSmallIntegerField("garantía en mano de obra (meses)", null=True, blank=True,
                                                      validators=[MaxValueValidator(24)])
    herramientas = models.CharField("herramientas y equipo que lleva", max_length=200, blank=True,
                                    help_text="Separadas por comas. Ej: escáner, multímetro, compresor, gato de moto")
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True)
    verificado = models.BooleanField(default=False, help_text="TallerYa revisó su identidad y experiencia")
    notas_admin = models.TextField("notas internas", blank=True, help_text="Solo las ve el equipo de TallerYa")
    nota_al_mecanico = models.CharField("mensaje para el mecánico", max_length=240, blank=True,
                                        help_text="Lo ve el mecánico en «Mi perfil» (p. ej. qué le falta para aprobarlo)")
    # Verificación: la cédula nunca se guarda en claro. Solo una huella HMAC (detecta la misma cédula en dos
    # perfiles) y los 4 últimos dígitos (para que el equipo la coteje cuando el mecánico la muestre por video o en persona).
    cedula_huella = models.CharField(max_length=64, blank=True, editable=False, db_index=True)
    cedula_ultimos = models.CharField("cédula (4 últimos dígitos)", max_length=4, blank=True, editable=False)
    referencias = models.TextField("referencias", max_length=400, blank=True,
                                   help_text="Nombre y celular de 1 o 2 clientes o talleres que lo recomienden. "
                                             "Solo las ve el equipo de TallerYa.")
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

    @staticmethod
    def huella_cedula(numero):
        digitos = "".join(c for c in str(numero) if c.isdigit())
        return salted_hmac("domicilio.cedula", digitos, algorithm="sha256").hexdigest() if digitos else ""

    def poner_cedula(self, numero):
        digitos = "".join(c for c in str(numero) if c.isdigit())
        self.cedula_huella = self.huella_cedula(digitos)
        self.cedula_ultimos = digitos[-4:]

    def pasos(self):
        """Lista de lo que le falta o ya tiene el perfil: (texto, hecho, obligatorio). La ve el mecánico en Mi perfil."""
        usuario = self.usuario
        perfil = getattr(usuario, "perfil", None) if usuario else None
        return [
            ("Datos básicos, zonas y servicios", bool(self.pk and self.zonas.exists() and self.servicios.exists()), True),
            ("Cédula registrada (para verificar tu identidad)", bool(self.cedula_huella), True),
            ("Correo confirmado", bool(perfil and perfil.correo_verificado), False),
            ("Foto tuya o trabajando", bool(self.foto), False),
            ("Descripción de tu experiencia (40+ caracteres)", len(self.descripcion.strip()) >= 40, False),
            ("Fotos de trabajos que hayas hecho", bool(self.pk and self.fotos_trabajo.exists()), False),
            ("En qué eres bueno y cómo trabajas", bool(self.especialidades or self.compromisos), False),
            ("Precios de referencia por servicio", bool(self.pk and self.precios.exists()), False),
            ("Una o dos referencias", bool(self.referencias.strip()), False),
        ]

    @property
    def herramientas_lista(self):
        return [h.strip()[:1].upper() + h.strip()[1:] for h in self.herramientas.split(",") if h.strip()][:12]

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


def ruta_trabajo(instancia, nombre):
    return f"domicilio/trabajos/{uuid4().hex}.jpg"


class FotoTrabajo(models.Model):
    """Fotos de trabajos del mecánico (prueba de experiencia). Se re-codifican como JPEG sin EXIF al subirlas."""
    MAXIMO = 4
    mecanico = models.ForeignKey(MecanicoDomicilio, on_delete=models.CASCADE, related_name="fotos_trabajo")
    imagen = models.ImageField(upload_to=ruta_trabajo)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]
        verbose_name = "foto de trabajo"
        verbose_name_plural = "fotos de trabajos"


class TallerQuerySet(models.QuerySet):
    def publicados(self):
        return self.filter(activo=True, taller__activo=True)


class TallerDomicilio(models.Model):
    """«También atiendo a domicilio» de un taller del directorio.

    Decisión: modelo ligero aparte (uno a uno con el taller) y no un perfil genérico mecánico/taller. El taller ya
    tiene nombre, foto, WhatsApp, reseñas, verificación y su propia moderación (Taller.activo); aquí solo va lo que
    añade el servicio a domicilio, reutilizando las mismas Zona y TipoServicio que los mecánicos independientes.
    Sale en /mecanicos/ cuando está activo y el taller está aprobado (activo en el directorio).
    """
    taller = models.OneToOneField("talleres.Taller", on_delete=models.CASCADE, related_name="domicilio")
    activo = models.BooleanField("también atiendo a domicilio", default=False)
    zonas = models.ManyToManyField(Zona, related_name="talleres_domicilio", blank=True, verbose_name="zonas donde atiende")
    servicios = models.ManyToManyField(TipoServicio, related_name="talleres_domicilio", blank=True,
                                       verbose_name="servicios a domicilio")
    tarifa_visita = models.PositiveIntegerField("tarifa de visita orientativa (pesos)", null=True, blank=True,
                                                validators=[MaxValueValidator(1_000_000)])
    urgencias = models.BooleanField("atiende urgencias a domicilio", default=False)
    actualizado = models.DateTimeField(auto_now=True)

    objects = TallerQuerySet.as_manager()

    class Meta:
        verbose_name = "servicio a domicilio de taller"
        verbose_name_plural = "servicios a domicilio de talleres"

    def __str__(self):
        return f"{self.taller} ({'activo' if self.activo else 'apagado'})"

    @property
    def tarifa_texto(self):
        from talleres.utils import pesos
        return pesos(self.tarifa_visita) if self.tarifa_visita else ""


class PrecioMecanico(models.Model):
    """Rango «desde–hasta» que el mecánico publica por servicio y cilindraje, como talleres.PrecioServicio
    (mismos campos y nombres, así la ficha usa la misma tabla «Precios desde» del taller). Orientativo."""
    mecanico = models.ForeignKey(MecanicoDomicilio, on_delete=models.CASCADE, related_name="precios")
    servicio = models.ForeignKey(TipoServicio, on_delete=models.CASCADE, related_name="precios_mecanicos")
    cilindraje = models.CharField(max_length=8, choices=[("", "Cualquier cilindraje"), ("baja", "Hasta 150 cc"),
                                                         ("media", "150 a 400 cc"), ("alta", "Más de 400 cc")], blank=True)
    desde = models.PositiveIntegerField("desde (COP)")
    hasta = models.PositiveIntegerField("hasta (COP)")
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["servicio__nombre", "cilindraje"]
        constraints = [
            models.UniqueConstraint(fields=["mecanico", "servicio", "cilindraje"], name="precio_mecanico_unico"),
            models.CheckConstraint(condition=models.Q(hasta__gte=models.F("desde")), name="precio_mecanico_hasta_mayor"),
        ]
        verbose_name = "precio de mecánico"
        verbose_name_plural = "precios de mecánicos"

    def __str__(self):
        return f"{self.mecanico} · {self.servicio} {self.cilindraje}: {self.desde}–{self.hasta}"


class MecanicoFavorito(models.Model):
    """Mecánicos guardados por una cuenta (como talleres.TallerFavorito)."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mecanicos_favoritos")
    mecanico = models.ForeignKey(MecanicoDomicilio, on_delete=models.CASCADE, related_name="favoritos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["usuario", "mecanico"], name="un_favorito_por_mecanico")]


class ResenaMecanico(models.Model):
    """Como talleres.Resena, pero solo con cuenta: una por cuenta y mecánico (si vuelve a calificar, se actualiza)."""
    mecanico = models.ForeignKey(MecanicoDomicilio, on_delete=models.CASCADE, related_name="resenas")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resenas_mecanicos")
    nombre = models.CharField(max_length=80)
    estrellas = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=600)
    respuesta = models.TextField("respuesta del mecánico", max_length=600, blank=True)
    respondida_en = models.DateTimeField(null=True, blank=True)
    visible = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "reseña de mecánico"
        verbose_name_plural = "reseñas de mecánicos"
        constraints = [models.UniqueConstraint(fields=["mecanico", "usuario"], name="una_resena_por_cuenta_y_mecanico")]

    def __str__(self):
        return f"{self.estrellas}★ {self.mecanico} - {self.nombre}"
