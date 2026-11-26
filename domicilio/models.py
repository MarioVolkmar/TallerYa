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
        RECHAZADO = "rechazado", "Rechazado"

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
    multimarca = models.BooleanField("Multimarca", default=False, help_text="Atiende todas las marcas: la ficha dice «Multimarca».")
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
    motivo_rechazo = models.CharField("motivo del rechazo", max_length=200, blank=True)
    verificado = models.BooleanField(default=False, help_text="TallerYa revisó su identidad y experiencia")
    mostrar_precios = models.BooleanField(
        "mostrar precios de referencia", default=False,
        help_text="Si está apagado, la ficha dice «Cotiza por WhatsApp» en vez de la tabla de precios (como en los talleres).")
    notas_admin = models.TextField("notas internas", blank=True, help_text="Solo las ve el equipo de TallerYa")
    nota_al_mecanico = models.CharField("mensaje para el mecánico", max_length=240, blank=True,
                                        help_text="Lo ve el mecánico en «Mi perfil» (p. ej. qué le falta para aprobarlo)")
    # Verificación: la cédula nunca se guarda en claro. Solo una huella HMAC (detecta la misma cédula en dos
    # perfiles) y los 4 últimos dígitos (para que el equipo la coteje cuando el mecánico la muestre por video o en persona).
    cedula_huella = models.CharField("huella de la cédula", max_length=64, blank=True, editable=False, db_index=True)
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
    mecanico = models.ForeignKey(MecanicoDomicilio, verbose_name="mecánico", on_delete=models.CASCADE, related_name="fotos_trabajo")
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

    @property
    def zonas_texto(self):
        """«Todo el Valle de Aburrá», «Toda Medellín» o la lista de zonas (los atajos del formulario guardan todas)."""
        zonas = set(self.zonas.all())
        if not zonas:
            return ""
        todas = set(Zona.objects.all())
        if zonas == todas:
            return "todo el Valle de Aburrá"
        if zonas == {z for z in todas if z.ciudad == "Medellín"}:
            return "toda Medellín"
        return ", ".join(str(z) for z in sorted(zonas, key=lambda z: (z.orden, z.nombre)))


class PrecioMecanico(models.Model):
    """Rango «desde–hasta» que el mecánico publica por servicio y cilindraje, como talleres.PrecioServicio
    (mismos campos y nombres, así la ficha usa la misma tabla «Precios desde» del taller). Orientativo."""
    mecanico = models.ForeignKey(MecanicoDomicilio, verbose_name="mecánico", on_delete=models.CASCADE, related_name="precios")
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
    mecanico = models.ForeignKey(MecanicoDomicilio, verbose_name="mecánico", on_delete=models.CASCADE, related_name="favoritos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["usuario", "mecanico"], name="un_favorito_por_mecanico")]


class ResenaMecanico(models.Model):
    """Como talleres.Resena, pero solo con cuenta: una por cuenta y mecánico (si vuelve a calificar, se actualiza)."""
    mecanico = models.ForeignKey(MecanicoDomicilio, verbose_name="mecánico", on_delete=models.CASCADE, related_name="resenas")
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


class SolicitudVisita(models.Model):
    """Pedido de visita a domicilio que el motociclista le hace a un mecánico (también abre WhatsApp).

    Igual que la cita de un taller: el mecánico la cotiza (rango de precio, fecha y hora), el motociclista la acepta
    o la rechaza desde su enlace y, al terminar, el servicio puede quedar en la hoja de vida de la moto."""
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        COTIZADA = "cotizada", "Esperando al motero"
        CONFIRMADA = "confirmada", "Confirmada"
        ATENDIDA = "atendida", "Atendida"
        CANCELADA = "cancelada", "Cancelada"

    mecanico = models.ForeignKey(MecanicoDomicilio, verbose_name="mecánico", on_delete=models.CASCADE, related_name="solicitudes")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="visitas_pedidas")
    nombre = models.CharField(max_length=80)
    telefono = models.CharField("teléfono", max_length=15)
    moto = models.CharField(max_length=60, blank=True)
    servicio = models.ForeignKey(TipoServicio, on_delete=models.SET_NULL, null=True, blank=True)
    zona = models.ForeignKey(Zona, on_delete=models.SET_NULL, null=True, blank=True)
    cuando = models.CharField(max_length=10, blank=True)
    detalle = models.CharField(max_length=300, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True)
    fecha_propuesta = models.DateField(null=True, blank=True)
    hora_propuesta = models.TimeField(null=True, blank=True)
    cotizacion_desde = models.PositiveIntegerField(null=True, blank=True)
    cotizacion_hasta = models.PositiveIntegerField(null=True, blank=True)
    cotizacion_incluye = models.CharField(max_length=160, blank=True)
    cotizacion_vence = models.DateField(null=True, blank=True)
    nota = models.CharField("nota del mecánico", max_length=200, blank=True)
    rechazada = models.BooleanField("el motero no aceptó la cotización", default=False)
    # Descuento de TallerYa que el motero trae a la visita: queda canjeado cuando el mecánico la marca «Atendida»
    codigo_cupon = models.ForeignKey("cupones.CodigoCupon", on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="visitas", verbose_name="descuento")
    token = models.CharField(max_length=32, unique=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "solicitud de visita"
        verbose_name_plural = "solicitudes de visita"

    def __str__(self):
        return f"{self.nombre} → {self.mecanico} ({self.get_estado_display()})"

    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("domicilio:visita_publica", args=[self.token])

    @property
    def cotizacion_vencida(self):
        from django.utils import timezone
        return bool(self.cotizacion_vence and self.cotizacion_vence < timezone.localdate())

    @property
    def precio_texto(self):
        if not self.cotizacion_hasta:
            return ""
        p = lambda n: "$" + f"{n:,}".replace(",", ".")
        d, h = self.cotizacion_desde, self.cotizacion_hasta
        return p(h) if d == h else f"{p(d)} – {p(h)}"


def ruta_identidad(instancia, nombre):
    # Nombre aleatorio y extensión fija (la imagen ya se re-codificó como JPEG): no revela nada del documento.
    return f"identidad_mecanicos/{uuid4().hex}.jpg"


def _almacen_privado():
    # Fuera de MEDIA_ROOT (PRIVADO_ROOT): /media/ nunca las sirve; solo la vista identidad_foto, y solo a admins.
    from garaje.models import AlmacenPrivado
    return AlmacenPrivado()


class IdentidadMecanico(models.Model):
    """Verificación de identidad con foto de la cédula (frente y respaldo; selfie opcional). Sin fila = pendiente de enviar.
    Las fotos se borran al aprobar o rechazar (Ley 1581): queda el resultado, la fecha y quién revisó.
    La insignia «Verificado» (MecanicoDomicilio.verificado) solo se otorga al aprobar. `heredada`: mecánicos que ya tenían
    la insignia antes de este flujo; conservan la insignia y se les invita a respaldarla con la foto."""

    class Estado(models.TextChoices):
        ENVIADA = "enviada", "En revisión"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"

    mecanico = models.OneToOneField(MecanicoDomicilio, verbose_name="mecánico", on_delete=models.CASCADE, related_name="identidad")
    frente = models.FileField("cédula, frente", storage=_almacen_privado, upload_to=ruta_identidad, blank=True)
    respaldo = models.FileField("cédula, respaldo", storage=_almacen_privado, upload_to=ruta_identidad, blank=True)
    selfie = models.FileField("selfie con la cédula", storage=_almacen_privado, upload_to=ruta_identidad, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ENVIADA, db_index=True)
    motivo = models.CharField("motivo del rechazo", max_length=200, blank=True)
    heredada = models.BooleanField(default=False)
    autorizacion = models.DateTimeField("autorizó el tratamiento de datos", null=True, blank=True)
    revisado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    revisado_en = models.DateTimeField(null=True, blank=True)
    enviado = models.DateTimeField(null=True, blank=True)

    CAMPOS_FOTO = ("frente", "respaldo", "selfie")

    class Meta:
        verbose_name = "identidad de mecánico"
        verbose_name_plural = "identidades de mecánicos"

    def __str__(self):
        return f"Identidad de {self.mecanico} ({self.get_estado_display()})"

    @property
    def tiene_fotos(self):
        return any(getattr(self, c) for c in self.CAMPOS_FOTO)

    def borrar_fotos(self):
        for campo in self.CAMPOS_FOTO:
            archivo = getattr(self, campo)
            if archivo:
                archivo.delete(save=False)
