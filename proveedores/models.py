"""Proveedores de servicios para la moto que no son talleres: grúas, CDA, SOAT y las categorías que el equipo agregue
(lavaderos, parqueaderos…). Un solo modelo con campos comunes; lo propio de cada categoría va en `extras`, y la
categoría dice cuáles aplican (CAMPOS_EXTRA).

Alta: «equipo» = datos públicos cargados por el equipo (lo que venía de Grua y CentroCDA); «asistido» = lo cargó el
equipo con lo que dio el proveedor; «autoregistro» = lo llenó el propio proveedor. Los dos últimos solo se publican
cuando el proveedor aprueba su ficha por el enlace con token (autorización Ley 1581).
"""
import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from talleres.models import CIUDADES

ICONOS = [("🚚", "🚚 Grúa"), ("🔧", "🔧 Revisión / taller"), ("🛡️", "🛡️ Seguro"), ("🧽", "🧽 Lavadero"),
          ("🅿️", "🅿️ Parqueadero"), ("⛽", "⛽ Combustible"), ("🛞", "🛞 Llantas"), ("🏍️", "🏍️ Moto"), ("📍", "📍 Otro")]

VEHICULOS = [("planchon", "Planchón"), ("cama", "Cama (plataforma)"), ("ambos", "Planchón y cama")]

# Campos propios que una categoría puede pedir. clave: (etiqueta, tipo, opciones)
CAMPOS_EXTRA = {
    "vehiculo": ("Lleva motos en", "opcion", VEHICULOS),
    "agenda": ("Agenda citas (se puede reservar hora)", "si_no", None),
}
CAMPOS_EXTRA_OPCIONES = [(k, v[0]) for k, v in CAMPOS_EXTRA.items()]


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True, help_text="En plural: «Grúas», «Lavaderos»")
    singular = models.CharField(max_length=60, help_text="«Grúa», «Lavadero»")
    slug = models.SlugField(max_length=60, unique=True, editable=False)
    icono = models.CharField(max_length=4, choices=ICONOS, default="📍")
    descripcion = models.CharField("descripción", max_length=200, blank=True,
                                   help_text="Una línea para el formulario «Soy proveedor»")
    etiqueta_precio = models.CharField("cómo se llama el precio", max_length=60, default="Precio de referencia desde",
                                       help_text="Ej.: «Tarifa base desde», «Revisión de moto desde»")
    campos = models.JSONField("campos propios", default=list, blank=True,
                              help_text="Campos que solo aplican a esta categoría")
    inscripcion = models.BooleanField("aparece en «Soy proveedor»", default=True)
    orden = models.PositiveSmallIntegerField(default=10)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "categoría de proveedor"
        verbose_name_plural = "categorías de proveedor"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.singular or self.nombre)[:50] or "categoria"
            slug, n = base, 2
            while Categoria.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)


class ProveedorQuerySet(models.QuerySet):
    def publicados(self, categoria=None):
        qs = self.filter(estado=Proveedor.Estado.PUBLICADO)
        return qs.filter(categoria__slug=categoria) if categoria else qs


def _solo_digitos(valor):
    numero = "".join(ch for ch in (valor or "") if ch.isdigit())
    return "57" + numero if len(numero) == 10 else numero  # celular o fijo colombiano sin indicativo


class Proveedor(models.Model):
    class Estado(models.TextChoices):
        POR_REVISAR = "por_revisar", "Por revisar"
        PUBLICADO = "publicado", "Publicado"
        PAUSADO = "pausado", "Pausado"

    class Alta(models.TextChoices):
        EQUIPO = "equipo", "Cargado por el equipo"
        ASISTIDO = "asistido", "Alta asistida"
        AUTOREGISTRO = "autoregistro", "Autoregistro"

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="proveedores", verbose_name="categoría")
    nombre = models.CharField(max_length=120)
    responsable = models.CharField("persona de contacto", max_length=80, blank=True)
    whatsapp = models.CharField(max_length=15, blank=True, help_text="Celular con WhatsApp. Ej: 3001234567")
    telefono = models.CharField("teléfono", max_length=20, blank=True, help_text="Si es distinto del WhatsApp")
    municipio = models.CharField("municipio de la sede", max_length=40, blank=True, choices=[(c, c) for c in CIUDADES])
    zonas = models.JSONField("municipios que atiende", default=list, blank=True)
    barrios = models.CharField("barrios o sectores", max_length=200, blank=True)
    direccion = models.CharField("dirección", max_length=160, blank=True)
    sitio_web = models.URLField("sitio web", blank=True)
    abierto_24h = models.BooleanField("24 horas", default=False)
    abre = models.TimeField(null=True, blank=True)
    cierra = models.TimeField(null=True, blank=True, help_text="Puede ser después de medianoche (ej. 02:00)")
    horario = models.CharField("horario (texto)", max_length=120, blank=True, help_text="Ej.: Lun a sáb 7 a. m. a 6 p. m.")
    descripcion = models.TextField("descripción", max_length=600, blank=True)
    foto = models.ImageField("foto o logo", upload_to="proveedores/", blank=True)
    precio_desde = models.PositiveIntegerField("precio de referencia desde (COP)", null=True, blank=True)
    precio_fuente = models.CharField("de dónde sale el precio", max_length=200, blank=True)
    aliado = models.BooleanField(default=False, help_text="Aliado de TallerYa: sale primero y con su beneficio")
    beneficio = models.CharField(max_length=120, blank=True, help_text="Ej.: 10 % menos mostrando TallerYa")
    extras = models.JSONField(default=dict, blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.POR_REVISAR)
    verificado = models.BooleanField(default=False)
    origen_alta = models.CharField("cómo se dio de alta", max_length=12, choices=Alta.choices, default=Alta.ASISTIDO)
    token_revision = models.CharField(max_length=40, unique=True, null=True, blank=True, editable=False)
    token_creado = models.DateTimeField("enlace de ficha creado", null=True, blank=True, editable=False)
    autoriza_datos = models.BooleanField("autorizó el tratamiento de datos (Ley 1581)", default=False)
    aprobado_por_proveedor = models.DateTimeField("el proveedor aprobó su ficha", null=True, blank=True, editable=False)
    aprobado_ip = models.GenericIPAddressField("IP de la aprobación", null=True, blank=True, editable=False)
    demo = models.BooleanField(default=False, help_text="Dato de muestra: no es una empresa real")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = ProveedorQuerySet.as_manager()

    class Meta:
        ordering = ["-aliado", "nombre"]
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"

    def __str__(self):
        return self.nombre

    DIAS_ENLACE = 30

    def generar_token(self):
        """Enlace nuevo (el anterior deja de servir) que vence a los 30 días."""
        self.token_revision = secrets.token_urlsafe(24)
        self.token_creado = timezone.now()
        return self.token_revision

    @property
    def enlace_vencido(self):
        return timezone.now() - (self.token_creado or self.creado) > timedelta(days=self.DIAS_ENLACE)

    @property
    def falta_aprobacion(self):
        """Alta del proveedor (asistida o autoregistro) que él aún no aprobó: no se puede publicar."""
        return self.origen_alta != self.Alta.EQUIPO and not self.aprobado_por_proveedor

    @property
    def publicado(self):
        return self.estado == self.Estado.PUBLICADO

    # Contacto listo para enlaces (acepta números con o sin indicativo)
    @property
    def wa_numero(self):
        return _solo_digitos(self.whatsapp)

    @property
    def tel_numero(self):
        return _solo_digitos(self.telefono or self.whatsapp)

    # Campos propios de la categoría
    @property
    def vehiculo(self):
        return self.extras.get("vehiculo", "")

    @property
    def vehiculo_txt(self):
        return dict(VEHICULOS).get(self.vehiculo, "")

    @property
    def agenda(self):
        return bool(self.extras.get("agenda"))


class EventoProveedor(models.Model):
    """Clics a WhatsApp y a llamar, agregados por día. Sin datos personales (igual que EventoDiario de talleres)."""
    class Tipo(models.TextChoices):
        WHATSAPP = "whatsapp", "Clics a WhatsApp"
        LLAMADA = "llamada", "Clics a llamar"

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name="eventos")
    fecha = models.DateField()
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-fecha"]
        constraints = [models.UniqueConstraint(fields=["proveedor", "fecha", "tipo"], name="evento_proveedor_unico")]
        verbose_name = "evento de proveedor"
        verbose_name_plural = "eventos de proveedor"

    def __str__(self):
        return f"{self.proveedor} · {self.fecha} · {self.get_tipo_display()}: {self.cantidad}"
