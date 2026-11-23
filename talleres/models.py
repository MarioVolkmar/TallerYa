import secrets
from urllib.parse import quote

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify

from .utils import codigo_aleatorio


# Los 10 municipios del Área Metropolitana del Valle de Aburrá
CIUDADES = ["Medellín", "Bello", "Itagüí", "Envigado", "Sabaneta", "La Estrella", "Caldas", "Copacabana", "Girardota", "Barbosa"]


class Barrio(models.Model):
    """Barrio o zona (en Medellín, las comunas y corregimientos) de una ciudad del área metropolitana."""
    nombre = models.CharField(max_length=80)
    ciudad = models.CharField(max_length=80, default="Medellín", choices=[(c, c) for c in CIUDADES])

    class Meta:
        ordering = ["ciudad", "nombre"]
        constraints = [models.UniqueConstraint(fields=["nombre", "ciudad"], name="barrio_unico_por_ciudad")]

    def __str__(self):
        return self.nombre if self.ciudad == "Medellín" else f"{self.nombre} · {self.ciudad}"


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


NIVELES_PRECIO = [(1, "$ · Económico"), (2, "$$ · Intermedio"), (3, "$$$ · Premium")]


class Taller(models.Model):
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    descripcion = models.TextField("descripción corta", max_length=300, blank=True)
    # Información estandarizada del perfil (listas en talleres/perfil.py)
    equipo = models.JSONField("quiénes atienden", default=list, blank=True,
                              help_text='Lista de {"nombre", "rol", "anios", "especialidad"}')
    especialidades = models.JSONField(default=list, blank=True, help_text="Claves de perfil.ESPECIALIDADES")
    garantia_meses = models.PositiveSmallIntegerField("garantía en mano de obra (meses)", null=True, blank=True)
    compromisos = models.JSONField("cómo trabajamos", default=list, blank=True, help_text="Claves de perfil.COMPROMISOS")
    responsable = models.CharField(max_length=120)
    whatsapp = models.CharField(max_length=20, help_text="Con indicativo, solo números. Ej: 573001234567")
    direccion = models.CharField(max_length=200)
    barrio = models.ForeignKey(Barrio, on_delete=models.PROTECT, related_name="talleres")
    horario = models.CharField(max_length=120, blank=True, help_text="Ej: Lun-Sáb 8am-6pm")
    servicios = models.ManyToManyField(Servicio, related_name="talleres")
    marcas = models.ManyToManyField(Marca, related_name="talleres", blank=True)
    multimarca = models.BooleanField("Multimarca", default=False, help_text="Atiende todas las marcas: en la ficha dice «Multimarca» y el filtro por marca lo incluye siempre.")
    foto = models.ImageField(upload_to="talleres/", blank=True)
    verificado = models.BooleanField(default=False)
    activo = models.BooleanField(default=False, help_text="Visible en el directorio")
    destacado = models.BooleanField(default=False, help_text="Plan pro: aparece primero")
    nivel_precio = models.PositiveSmallIntegerField(
        "rango de precios", choices=NIVELES_PRECIO, null=True, blank=True,
        help_text="Lo indica el propio taller. Sirve para ordenar el directorio por precio.",
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="taller",
        help_text="Cuenta del taller: sus respuestas en el foro salen con insignia de taller.",
    )
    # PIN para validar cupones en /canjear/ sin la sesión del taller. Solo se guarda su hash (como una contraseña):
    # nadie, ni el equipo, puede leerlo. El taller lo genera en Mi taller y se le muestra una sola vez (nuevo_pin).
    pin_hash = models.CharField("PIN de canje (hash)", max_length=128, blank=True, editable=False)
    # Agenda con franjas: el taller define su horario (HorarioTaller), la duración de cada franja y el cupo
    mostrar_precios = models.BooleanField(
        "mostrar precios de mano de obra", default=False,
        help_text="Si está apagado, el perfil dice «Cotiza por WhatsApp» en vez de la tabla de precios de mano de obra.")
    # Alta: cómo llegó el taller. «cuenta» = registro normal; «asistido» = lo cargó el equipo con datos que dio el taller;
    # «autoregistro» = lo llenó el propio taller sin cuenta. Los dos últimos se revisan con un enlace con token.
    class Alta(models.TextChoices):
        CUENTA = "cuenta", "Con cuenta"
        ASISTIDO = "asistido", "Alta asistida"
        AUTOREGISTRO = "autoregistro", "Autoregistro"

    origen_alta = models.CharField("cómo se dio de alta", max_length=12, choices=Alta.choices, default=Alta.CUENTA)
    token_revision = models.CharField(max_length=40, unique=True, null=True, blank=True, editable=False)
    token_creado = models.DateTimeField("enlace de ficha creado", null=True, blank=True, editable=False)
    precios_aviso_enviado = models.DateTimeField("último correo de precios por confirmar", null=True, blank=True, editable=False)
    autoriza_datos = models.BooleanField("autorizó el tratamiento de datos (Ley 1581)", default=False)
    aprobado_por_taller = models.DateTimeField("el taller aprobó su ficha", null=True, blank=True, editable=False)
    aprobado_ip = models.GenericIPAddressField("IP de la aprobación", null=True, blank=True, editable=False)
    agenda_activa = models.BooleanField("reservas por franjas", default=False,
                                        help_text="El motero elige un horario libre al pedir la cita.")
    duracion_franja = models.PositiveSmallIntegerField("duración de la franja (min)", default=60,
                                                       choices=[(30, "30 min"), (45, "45 min"), (60, "1 hora"), (90, "1 h 30"), (120, "2 horas")])
    cupo_franja = models.PositiveSmallIntegerField("motos por franja", default=1,
                                                   validators=[MinValueValidator(1), MaxValueValidator(10)])
    # Emergencias
    atiende_emergencias = models.BooleanField("atiende emergencias", default=False)
    abierto_24h = models.BooleanField("abierto 24 horas", default=False)
    grua = models.BooleanField("tiene grúa", default=False)
    despinche_domicilio = models.BooleanField("despinche a domicilio", default=False)
    gasolina_domicilio = models.BooleanField("lleva gasolina a domicilio", default=False)
    # Ubicación del local (la pone el taller) para ordenar por cercanía en /emergencias; la del motero nunca se guarda
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # True si las coordenadas son del local (GPS tomado allí o dirección encontrada); False si son del barrio o no hay
    ubicacion_exacta = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-destacado", "-verificado", "nombre"]
        verbose_name_plural = "talleres"

    def __str__(self):
        return self.nombre

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        d = self.__dict__
        self._ubic0 = (d.get("direccion"), d.get("barrio_id"), d.get("latitud"), d.get("longitud"))

    def save(self, *args, **kwargs):
        # Dirección o barrio nuevos (y coordenadas no tocadas a mano): se calculan las coordenadas
        direccion0, barrio0, lat0, lng0 = getattr(self, "_ubic0", (None,) * 4)
        if (self.pk is None or direccion0 != self.direccion or barrio0 != self.barrio_id) and (self.latitud, self.longitud) == (lat0, lng0):
            from .geocodificar import completar_ubicacion
            if completar_ubicacion(self) and kwargs.get("update_fields"):
                kwargs["update_fields"] = {*kwargs["update_fields"], "latitud", "longitud", "ubicacion_exacta"}
        elif (self.latitud, self.longitud) != (lat0, lng0) and not getattr(self, "_geo_auto", False):
            self.ubicacion_exacta = self.latitud is not None  # las puso una persona (GPS o mapa)
        if not self.slug:
            base = slugify(self.nombre) or "taller"
            slug, n = base, 2
            while Taller.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)
        self._ubic0 = (self.direccion, self.barrio_id, self.latitud, self.longitud)
        self._geo_auto = False

    LARGO_PIN = 6

    def nuevo_pin(self):
        """Genera un PIN nuevo (el anterior deja de servir), guarda solo su hash y devuelve el PIN en claro para
        mostrarlo una vez. Distintos talleres pueden tener el mismo PIN: el taller nunca se busca por su PIN."""
        from django.contrib.auth.hashers import make_password
        pin = codigo_aleatorio(self.LARGO_PIN, "0123456789")
        self.pin_hash = make_password(pin)
        if self.pk:
            Taller.objects.filter(pk=self.pk).update(pin_hash=self.pin_hash)
        return pin

    def pin_correcto(self, pin):
        """Compara el PIN con el de ESTE taller (check_password compara en tiempo constante)."""
        from django.contrib.auth.hashers import check_password
        pin = (pin or "").strip()
        return bool(self.pin_hash and len(pin) == self.LARGO_PIN and pin.isdigit() and check_password(pin, self.pin_hash))

    @property
    def tiene_pin(self):
        return bool(self.pin_hash)

    def get_absolute_url(self):
        return reverse("talleres:detalle", args=[self.slug])

    @property
    def pendiente_de_revision(self):
        """Alta que espera: no publicada y que no es el registro normal con cuenta."""
        return not self.activo and self.origen_alta != self.Alta.CUENTA

    DIAS_ENLACE = 30

    def generar_token(self):
        """Enlace nuevo (el anterior deja de servir) que vence a los 30 días."""
        from django.utils import timezone
        self.token_revision = secrets.token_urlsafe(24)
        self.token_creado = timezone.now()
        return self.token_revision

    @property
    def enlace_vencido(self):
        from datetime import timedelta
        from django.utils import timezone
        desde = self.token_creado or self.creado
        return timezone.now() - desde > timedelta(days=self.DIAS_ENLACE)

    @property
    def falta_aprobacion(self):
        """Alta sin cuenta que el taller aún no aprobó (Ley 1581): no se puede publicar."""
        return self.origen_alta != self.Alta.CUENTA and not self.aprobado_por_taller

    @cached_property
    def calificacion(self):
        """Nota media de las reseñas visibles (se calcula una vez por objeto)."""
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
        return self.whatsapp_con_mensaje()

    def whatsapp_con_mensaje(self, moto="", servicio=""):
        """Enlace de WhatsApp con el mensaje ya escrito: moto y servicio si se conocen, y «te encontré en TallerYa»."""
        texto = f"Hola {self.nombre}, te encontré en TallerYa."
        if moto and servicio:
            texto += f" Tengo una {moto} y necesito: {servicio}."
        elif moto:
            texto += f" Tengo una {moto}."
        elif servicio:
            texto += f" Necesito: {servicio}."
        return f"https://wa.me/{self.whatsapp}?text={quote(texto)}"


class SolicitudCita(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADA = "confirmada", "Confirmada"
        REPROGRAMADA = "reprogramada", "Esperando al motero"
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
    hora = models.TimeField(null=True, blank=True, help_text="Hora acordada (si se acordó)")
    # Reprogramación: el taller propone otra fecha y el motero la acepta o la rechaza en un enlace
    fecha_propuesta = models.DateField(null=True, blank=True)
    hora_propuesta = models.TimeField(null=True, blank=True)
    nota_taller = models.CharField("nota del taller", max_length=200, blank=True)
    propuesta_rechazada = models.BooleanField(default=False)
    # Cotización del taller (privada entre el taller y el motero): rango de precio, qué incluye y hasta cuándo vale
    cotizacion_desde = models.PositiveIntegerField("cotización desde", null=True, blank=True)
    cotizacion_hasta = models.PositiveIntegerField("cotización hasta", null=True, blank=True)
    cotizacion_incluye = models.CharField("qué incluye la cotización", max_length=160, blank=True)
    cotizacion_vence = models.DateField("la cotización vale hasta", null=True, blank=True)
    motivo_cancelacion = models.CharField("motivo de la cancelación", max_length=200, blank=True)
    token = models.CharField(max_length=32, unique=True, null=True, blank=True, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="solicitudes_cita", help_text="Cuenta del motero (si pidió la cita conectado)")
    recordatorio_enviado = models.DateTimeField(null=True, blank=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        indexes = [models.Index(fields=["taller", "fecha_preferida", "hora"], name="cita_franja_idx")]
        verbose_name = "solicitud de cita"
        verbose_name_plural = "solicitudes de cita"

    def __str__(self):
        return f"{self.nombre} → {self.taller} ({self.fecha_preferida})"

    @property
    def cotizacion_vencida(self):
        from django.utils import timezone
        return bool(self.cotizacion_vence and self.cotizacion_vence < timezone.localdate())


class FotoTaller(models.Model):
    """Fotos (y videos cortos) que el taller sube a su perfil (local, trabajos, equipo).

    Un video es una entrada con `video`; `imagen` es entonces su póster (opcional: sin póster se muestra el
    primer cuadro del video)."""
    MAXIMO = 8
    MAXIMO_VIDEOS = 2
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="talleres/galeria/", blank=True)
    video = models.FileField(upload_to="talleres/videos/", blank=True,
                             help_text="MP4 o WEBM corto (máx. 20 MB). La imagen hace de póster.")
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
    respuesta = models.TextField("respuesta del taller", max_length=600, blank=True)
    respondida_en = models.DateTimeField(null=True, blank=True)
    visible = models.BooleanField(default=True)
    # Sello «verificada»: viene de un servicio registrado por el taller (id de garaje.ServicioTaller; sin FK para no
    # crear un ciclo de migraciones entre talleres y garaje).
    verificada = models.BooleanField(default=False)
    servicio_taller_id = models.PositiveIntegerField(null=True, blank=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "reseña"

    def __str__(self):
        return f"{self.estrellas}★ {self.taller} - {self.nombre}"


class TallerFavorito(models.Model):
    """Talleres que un usuario guardó con el corazón."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="talleres_favoritos")
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name="favoritos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["usuario", "taller"], name="favorito_unico")]
        ordering = ["-creado"]
        verbose_name = "taller favorito"
        verbose_name_plural = "talleres favoritos"

    def __str__(self):
        return f"{self.usuario} ♥ {self.taller}"


class EventoDiario(models.Model):
    """Conteo agregado por día de lo que pasa en el perfil del taller.
    Sin datos personales: solo taller, día, tipo y cuántas veces (no se guarda quién, ni IP, ni cookies)."""
    class Tipo(models.TextChoices):
        VISITA = "visita", "Visitas al perfil"
        WHATSAPP = "whatsapp", "Clics a WhatsApp"
        LLAMADA = "llamada", "Clics a llamar"

    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name="eventos")
    fecha = models.DateField()
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-fecha"]
        constraints = [models.UniqueConstraint(fields=["taller", "fecha", "tipo"], name="evento_unico_por_dia")]
        verbose_name = "evento diario"
        verbose_name_plural = "eventos diarios"

    def __str__(self):
        return f"{self.taller} · {self.fecha} · {self.get_tipo_display()}: {self.cantidad}"


DIAS_SEMANA = [(0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"), (4, "Viernes"), (5, "Sábado"), (6, "Domingo")]


class HorarioTaller(models.Model):
    """Un turno de atención (un día puede tener dos: mañana y tarde). Sirve para la agenda y para "abierto ahora"."""
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name="horarios")
    dia = models.PositiveSmallIntegerField(choices=DIAS_SEMANA)
    abre = models.TimeField()
    cierra = models.TimeField()

    class Meta:
        ordering = ["dia", "abre"]
        constraints = [
            models.UniqueConstraint(fields=["taller", "dia", "abre"], name="turno_unico"),
            models.CheckConstraint(condition=models.Q(cierra__gt=models.F("abre")), name="turno_cierra_despues"),
        ]
        verbose_name = "horario del taller"
        verbose_name_plural = "horarios del taller"

    def __str__(self):
        return f"{self.get_dia_display()} {self.abre:%H:%M}–{self.cierra:%H:%M}"


CILINDRAJES = [("", "Cualquier cilindraje"), ("baja", "Hasta 150 cc"), ("media", "150 a 400 cc"), ("alta", "Más de 400 cc")]


class PrecioServicio(models.Model):
    """Rango de precio "desde–hasta" que el taller publica por servicio (orientativo, no es una cotización)."""
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name="precios")
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name="precios")
    cilindraje = models.CharField(max_length=8, choices=CILINDRAJES, blank=True)
    desde = models.PositiveIntegerField("desde (COP)")
    hasta = models.PositiveIntegerField("hasta (COP)")
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["servicio__nombre", "cilindraje"]
        constraints = [
            models.UniqueConstraint(fields=["taller", "servicio", "cilindraje"], name="precio_unico_por_servicio"),
            models.CheckConstraint(condition=models.Q(hasta__gte=models.F("desde")), name="precio_hasta_mayor"),
        ]
        verbose_name = "precio de servicio"
        verbose_name_plural = "precios de servicios"

    def __str__(self):
        return f"{self.taller} · {self.servicio} {self.cilindraje}: {self.desde}–{self.hasta}"


