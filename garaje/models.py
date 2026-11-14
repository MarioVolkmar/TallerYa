from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from cupones.models import Motociclista
from talleres.models import Marca, Servicio, Taller


class Tipo(models.TextChoices):
    SCOOTER = "scooter", "Scooter"
    SEMI = "semi", "Semiautomática"
    CALLE = "calle", "Calle / naked"
    SPORT = "sport", "Deportiva"
    ENDURO = "enduro", "Enduro / doble propósito"


class Freno(models.TextChoices):
    DISCO = "disco", "Disco"
    TAMBOR = "tambor", "Tambor"


class LineaMoto(models.Model):
    """Ficha técnica de una línea. Define la forma del modelo 3D y qué mantenimientos aplican."""

    class Transmision(models.TextChoices):
        CADENA = "cadena", "Cadena"
        CVT = "cvt", "Automática (correa CVT)"

    class Refrigeracion(models.TextChoices):
        AIRE = "aire", "Aire"
        LIQUIDO = "liquido", "Líquida (radiador)"

    class Suspension(models.TextChoices):
        MONO = "mono", "Monoamortiguador"
        DOBLE = "doble", "Doble amortiguador"

    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="lineas")
    nombre = models.CharField(max_length=80, help_text="Ej: NKD 125")
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.CALLE)
    cilindraje = models.PositiveSmallIntegerField(validators=[MinValueValidator(49), MaxValueValidator(1900)])
    transmision = models.CharField(max_length=8, choices=Transmision.choices, default=Transmision.CADENA)
    refrigeracion = models.CharField(max_length=8, choices=Refrigeracion.choices, default=Refrigeracion.AIRE)
    freno_delantero = models.CharField(max_length=8, choices=Freno.choices, default=Freno.DISCO)
    freno_trasero = models.CharField(max_length=8, choices=Freno.choices, default=Freno.TAMBOR)
    suspension_trasera = models.CharField(max_length=6, choices=Suspension.choices, default=Suspension.DOBLE)
    rin_delantero = models.PositiveSmallIntegerField("rin delantero (pulgadas)", default=17,
                                                     validators=[MinValueValidator(8), MaxValueValidator(23)])
    rin_trasero = models.PositiveSmallIntegerField("rin trasero (pulgadas)", default=17,
                                                   validators=[MinValueValidator(8), MaxValueValidator(23)])
    carenado = models.BooleanField(default=False, help_text="Carenado deportivo completo")
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["marca__nombre", "nombre"]
        verbose_name = "línea de moto"
        verbose_name_plural = "líneas de moto"
        constraints = [models.UniqueConstraint(fields=["marca", "nombre"], name="linea_unica_por_marca")]

    def __str__(self):
        return f"{self.marca} {self.nombre}"

    def specs(self):
        return {
            "tipo": self.tipo, "cilindraje": self.cilindraje, "transmision": self.transmision,
            "refrigeracion": self.refrigeracion, "freno_delantero": self.freno_delantero,
            "freno_trasero": self.freno_trasero, "suspension_trasera": self.suspension_trasera,
            "rin_delantero": self.rin_delantero, "rin_trasero": self.rin_trasero, "carenado": self.carenado,
        }


# Ficha por defecto cuando el usuario escribe una moto que no está en el catálogo.
SPECS_POR_TIPO = {
    Tipo.SCOOTER: dict(cilindraje=125, transmision="cvt", refrigeracion="aire", freno_delantero="disco",
                       freno_trasero="tambor", suspension_trasera="mono", rin_delantero=12, rin_trasero=10, carenado=False),
    Tipo.SEMI: dict(cilindraje=110, transmision="cadena", refrigeracion="aire", freno_delantero="tambor",
                    freno_trasero="tambor", suspension_trasera="doble", rin_delantero=17, rin_trasero=17, carenado=False),
    Tipo.CALLE: dict(cilindraje=150, transmision="cadena", refrigeracion="aire", freno_delantero="disco",
                     freno_trasero="tambor", suspension_trasera="doble", rin_delantero=17, rin_trasero=17, carenado=False),
    Tipo.SPORT: dict(cilindraje=250, transmision="cadena", refrigeracion="liquido", freno_delantero="disco",
                     freno_trasero="disco", suspension_trasera="mono", rin_delantero=17, rin_trasero=17, carenado=True),
    Tipo.ENDURO: dict(cilindraje=150, transmision="cadena", refrigeracion="aire", freno_delantero="disco",
                      freno_trasero="tambor", suspension_trasera="mono", rin_delantero=21, rin_trasero=18, carenado=False),
}

HEX = RegexValidator(r"^#[0-9a-fA-F]{6}$", "Color inválido (usa formato #RRGGBB).")

# Diseños de calcas disponibles (se dibujan en el navegador, no son imágenes de terceros)
DISENOS_CALCA = {
    "franjas": "Franjas de carreras", "llamas": "Llamas", "rayo": "Rayo", "cuadros": "Cuadros",
    "numero": "Número de carreras", "texto": "Texto propio", "tallerya": "Logo TallerYa",
}
ZONAS_CALCA = {"lateral": "Laterales", "frontal": "Frontal", "tanque": "Tanque", "cola": "Cola"}
MAX_CALCAS = 4

COLORES = [
    ("#c62828", "Rojo"), ("#1f4fa8", "Azul"), ("#1b1b1b", "Negro"), ("#e8e4da", "Blanco"),
    ("#8a9096", "Gris"), ("#f2611d", "Naranja"), ("#2f7d4a", "Verde"), ("#e3a72f", "Amarillo"),
]
# Más tonos para personalizar el modelo 3D (no aparecen en el formulario de registro).
COLORES_EXTRA = [("#c0c4c8", "Plata"), ("#5b3a8c", "Morado"), ("#e86fa6", "Rosa"), ("#1f9aa0", "Turquesa")]
COLORES_SECUNDARIOS = [
    ("#1c2022", "Negro"), ("#c0c4c8", "Plata"), ("#c9a227", "Dorado"), ("#c62828", "Rojo"),
    ("#1f4fa8", "Azul"), ("#f2f2ee", "Blanco"),
]


class AlmacenPrivado(FileSystemStorage):
    """Documentos personales en PRIVADO_ROOT (se lee en cada uso). No tienen URL pública: se sirven con permiso."""

    @property
    def base_location(self):
        return settings.PRIVADO_ROOT

    @property
    def location(self):
        return str(Path(settings.PRIVADO_ROOT).resolve())

    def url(self, name):
        raise ValueError("Los documentos privados no tienen URL pública; usa la vista garaje:documento.")


def almacen_privado():
    return AlmacenPrivado()


def ruta_documento(instancia, nombre):
    # Nombre aleatorio: no revela la placa ni el nombre original del archivo.
    return f"documentos/{uuid4().hex}{Path(nombre).suffix.lower()}"


DOCUMENTOS = {"soat": "SOAT", "tecno": "Técnico-mecánica"}
DIAS_AVISO_DOCUMENTO = 30


class Moto(models.Model):
    motociclista = models.ForeignKey(Motociclista, on_delete=models.CASCADE, related_name="motos")
    linea = models.ForeignKey(LineaMoto, on_delete=models.PROTECT, null=True, blank=True, related_name="motos")
    # Si la moto no está en el catálogo:
    marca_otra = models.CharField("marca", max_length=60, blank=True)
    linea_otra = models.CharField("línea", max_length=80, blank=True)
    tipo_otra = models.CharField("tipo", max_length=10, choices=Tipo.choices, blank=True)

    modelo = models.PositiveSmallIntegerField("modelo (año)", validators=[MinValueValidator(1980), MaxValueValidator(2100)])
    color = models.CharField(max_length=7, default="#c62828", validators=[HEX])
    color_secundario = models.CharField("color de rines y detalles", max_length=7, default="#1c2022", validators=[HEX])
    calcas = models.JSONField(default=list, blank=True, help_text="Calcas del modelo 3D: diseño, zona, color, tamaño y texto")
    apodo = models.CharField(max_length=40, blank=True, help_text="Opcional. Ej: La Negra")
    placa = models.CharField(max_length=8, blank=True, help_text="Opcional y privada. Ej: ABC12D")
    # Documentos (opcionales): fecha de vencimiento y una foto o PDF, solo visibles para el dueño.
    soat_vence = models.DateField("vencimiento del SOAT", null=True, blank=True)
    soat_archivo = models.FileField("foto o PDF del SOAT", storage=almacen_privado, upload_to=ruta_documento, blank=True)
    tecno_vence = models.DateField("vencimiento de la técnico-mecánica", null=True, blank=True)
    tecno_archivo = models.FileField("foto o PDF de la técnico-mecánica", storage=almacen_privado,
                                     upload_to=ruta_documento, blank=True)
    km_inicial = models.PositiveIntegerField("kilometraje al registrarla")
    km_actual = models.PositiveIntegerField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]

    def __str__(self):
        return self.apodo or self.nombre_completo

    @property
    def nombre_completo(self):
        base = str(self.linea) if self.linea else f"{self.marca_otra} {self.linea_otra}".strip()
        return f"{base} {self.modelo}"

    @property
    def tipo(self):
        return self.linea.tipo if self.linea else (self.tipo_otra or Tipo.CALLE)

    def specs(self):
        return self.linea.specs() if self.linea else {"tipo": self.tipo, **SPECS_POR_TIPO[self.tipo]}

    def get_absolute_url(self):
        return reverse("garaje:moto", args=[self.pk])

    @property
    def color_contraste(self):
        """Color para dibujar encima de la pintura de la moto: oscuro sobre colores claros y crema sobre oscuros."""
        n = int(self.color[1:], 16)
        claridad = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255
        return "#111517" if claridad > 0.6 else "#ede3cc"

    def documentos(self, hoy=None):
        """Estado de SOAT y técnico-mecánica para mostrar y recordar."""
        hoy = hoy or timezone.localdate()
        lista = []
        for clave, nombre in DOCUMENTOS.items():
            vence = getattr(self, f"{clave}_vence")
            dias = (vence - hoy).days if vence else None
            if dias is None:
                estado = "desconocido"
            elif dias < 0:
                estado = "vencido"
            elif dias <= DIAS_AVISO_DOCUMENTO:
                estado = "pronto"
            else:
                estado = "ok"
            lista.append({"clave": clave, "nombre": nombre, "vence": vence, "dias": dias, "estado": estado,
                          "dias_abs": abs(dias) if dias is not None else None,
                          "archivo": bool(getattr(self, f"{clave}_archivo"))})
        return lista

    def aviso_documentos(self, hoy=None):
        """Un recordatorio corto para la ficha de la moto, o None si todo está al día."""
        docs = self.documentos(hoy)
        vencidos = [d["nombre"] for d in docs if d["estado"] == "vencido"]
        if vencidos:
            return {"estado": "vencido", "texto": f"{' y '.join(vencidos)} vencido{'s' if len(vencidos) > 1 else ''}"}
        pronto = sorted((d for d in docs if d["estado"] == "pronto"), key=lambda d: d["dias"])
        if pronto:
            d = pronto[0]
            cuando = "hoy" if d["dias"] == 0 else f"en {d['dias']} día{'s' if d['dias'] != 1 else ''}"
            return {"estado": "pronto", "texto": f"{d['nombre']} vence {cuando}"}
        con_articulo = {"soat": "del SOAT", "tecno": "de la técnico-mecánica"}
        faltan = [con_articulo[d["clave"]] for d in docs if d["estado"] == "desconocido"]
        if faltan:
            return {"estado": "desconocido", "texto": f"Agrega la fecha {' y '.join(faltan)}"}
        return None

    @staticmethod
    def limpiar_calcas(calcas):
        """Valida la lista de calcas que llega del navegador. Devuelve la lista limpia o lanza ValueError."""
        if not isinstance(calcas, list) or len(calcas) > MAX_CALCAS:
            raise ValueError(f"Máximo {MAX_CALCAS} calcas.")
        def vector(valor, limite):
            # Tres números finitos dentro de ±limite (coordenadas del modelo 3D, en metros).
            if not isinstance(valor, (list, tuple)) or len(valor) != 3:
                raise ValueError("Ubicación de calca inválida.")
            try:
                v = [float(x) for x in valor]
            except (TypeError, ValueError):
                raise ValueError("Ubicación de calca inválida.")
            if any(x != x or abs(x) > limite for x in v):  # x != x detecta NaN
                raise ValueError("Ubicación de calca inválida.")
            return [round(x, 4) for x in v]

        limpias = []
        for c in calcas:
            if not isinstance(c, dict) or c.get("diseno") not in DISENOS_CALCA:
                raise ValueError("Calca inválida.")
            # Ubicación: un punto exacto sobre la carrocería (nuevo) o una zona fija (formato anterior).
            con_punto = c.get("punto") is not None
            if not con_punto and c.get("zona") not in ZONAS_CALCA:
                raise ValueError("Calca inválida.")
            color = str(c.get("color", "#ffffff"))
            HEX(color)
            try:
                tamano = min(1.6, max(0.4, float(c.get("tamano", 1))))
                posicion = min(1.0, max(-1.0, float(c.get("posicion", 0))))
                giro = min(180.0, max(-180.0, float(c.get("giro", 0))))
            except (TypeError, ValueError):
                raise ValueError("Tamaño, posición o giro inválidos.")
            texto = "".join(ch for ch in str(c.get("texto", ""))[:14] if ch.isprintable())
            limpia = {"diseno": c["diseno"], "color": color, "tamano": round(tamano, 2), "texto": texto,
                      "giro": round(giro, 1), "ambos": bool(c.get("ambos", False))}
            if con_punto:
                limpia["punto"] = vector(c["punto"], 3)
                normal = vector(c.get("normal"), 1.01)
                if sum(x * x for x in normal) < 0.25:
                    raise ValueError("Ubicación de calca inválida.")
                limpia["normal"] = normal
            else:
                limpia.update(zona=c["zona"], posicion=round(posicion, 2))
            limpias.append(limpia)
        return limpias


class LecturaKm(models.Model):
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="lecturas")
    km = models.PositiveIntegerField()
    fecha = models.DateField(default=timezone.localdate)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-creado"]
        verbose_name = "lectura de kilometraje"
        verbose_name_plural = "lecturas de kilometraje"

    def __str__(self):
        return f"{self.moto}: {self.km} km ({self.fecha})"


class TareaMantenimiento(models.Model):
    """Regla del plan de mantenimiento. Los intervalos son orientativos y se editan en el admin."""

    class Pieza(models.TextChoices):
        ACEITE = "aceite", "Aceite de motor"
        MOTOR = "motor", "Motor"
        FILTRO_AIRE = "filtro_aire", "Filtro de aire"
        BUJIA = "bujia", "Bujía"
        CADENA = "cadena", "Cadena y piñones"
        CORREA = "correa", "Correa CVT"
        FRENO_DEL = "freno_del", "Freno delantero"
        FRENO_TRAS = "freno_tras", "Freno trasero"
        LLANTA_DEL = "llanta_del", "Llanta delantera"
        LLANTA_TRAS = "llanta_tras", "Llanta trasera"
        SUSPENSION_DEL = "suspension_del", "Suspensión delantera"
        SUSPENSION_TRAS = "suspension_tras", "Suspensión trasera"
        BATERIA = "bateria", "Batería"
        REFRIGERACION = "refrigeracion", "Refrigeración"

    class Aplica(models.TextChoices):
        TODAS = "todas", "Todas las motos"
        CADENA = "cadena", "Con cadena"
        CVT = "cvt", "Con correa CVT"
        LIQUIDO = "liquido", "Con refrigeración líquida"
        DISCO_DEL = "disco_del", "Freno delantero de disco"
        TAMBOR_DEL = "tambor_del", "Freno delantero de tambor"
        DISCO_TRAS = "disco_tras", "Freno trasero de disco"
        TAMBOR_TRAS = "tambor_tras", "Freno trasero de tambor"

    clave = models.SlugField(unique=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=240, blank=True)
    pieza = models.CharField(max_length=20, choices=Pieza.choices)
    aplica = models.CharField(max_length=12, choices=Aplica.choices, default=Aplica.TODAS)
    intervalo_km = models.PositiveIntegerField(null=True, blank=True)
    intervalo_dias = models.PositiveIntegerField(null=True, blank=True)
    servicio = models.ForeignKey(
        Servicio, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Para sugerir talleres que ofrecen este servicio",
    )
    hazlo_tu = models.BooleanField("lo puede hacer el motociclista", default=False)
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "tarea de mantenimiento"
        verbose_name_plural = "tareas de mantenimiento"

    def __str__(self):
        return self.nombre

    def aplica_a(self, specs):
        reglas = {
            self.Aplica.TODAS: True,
            self.Aplica.CADENA: specs["transmision"] == "cadena",
            self.Aplica.CVT: specs["transmision"] == "cvt",
            self.Aplica.LIQUIDO: specs["refrigeracion"] == "liquido",
            self.Aplica.DISCO_DEL: specs["freno_delantero"] == "disco",
            self.Aplica.TAMBOR_DEL: specs["freno_delantero"] == "tambor",
            self.Aplica.DISCO_TRAS: specs["freno_trasero"] == "disco",
            self.Aplica.TAMBOR_TRAS: specs["freno_trasero"] == "tambor",
        }
        return reglas.get(self.aplica, False)


class SolicitudSoat(models.Model):
    """Pedido de cotización de SOAT. TallerYa aún no lo vende: el equipo lo gestiona desde el admin."""
    class Estado(models.TextChoices):
        NUEVA = "nueva", "Nueva"
        CONTACTADO = "contactado", "Contactado"
        CERRADA = "cerrada", "Cerrada"

    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="solicitudes_soat")
    placa = models.CharField(max_length=8, blank=True)
    celular = models.CharField(max_length=15)
    comentario = models.CharField(max_length=300, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.NUEVA)
    notas_internas = models.TextField(blank=True, help_text="Solo para el equipo de TallerYa")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "solicitud de SOAT"
        verbose_name_plural = "solicitudes de SOAT"

    def __str__(self):
        return f"SOAT · {self.moto} · {self.get_estado_display()}"

    @property
    def abierta(self):
        return self.estado != self.Estado.CERRADA


class AjusteTarea(models.Model):
    """Lo que la persona decidió sobre un mantenimiento pendiente: posponerlo o que le recuerden un día."""
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="ajustes")
    tarea = models.ForeignKey("TareaMantenimiento", on_delete=models.CASCADE, related_name="+")
    pospuesto_hasta = models.DateField(null=True, blank=True)
    recordar_el = models.DateField(null=True, blank=True)
    recordado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("moto", "tarea")]
        verbose_name = "ajuste de mantenimiento"

    def __str__(self):
        return f"{self.moto} · {self.tarea}"

    @property
    def pospuesta(self):
        return bool(self.pospuesto_hasta and self.pospuesto_hasta >= timezone.localdate())

    @property
    def recordatorio_pendiente(self):
        return bool(self.recordar_el and not self.recordado)


class Mantenimiento(models.Model):
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="mantenimientos")
    tarea = models.ForeignKey(TareaMantenimiento, on_delete=models.PROTECT, related_name="registros")
    km = models.PositiveIntegerField()
    fecha = models.DateField(default=timezone.localdate)
    taller = models.ForeignKey(Taller, on_delete=models.SET_NULL, null=True, blank=True, related_name="mantenimientos")
    taller_otro = models.CharField("otro taller", max_length=80, blank=True,
                                   help_text="Taller que no está en TallerYa (opcional)")
    notas = models.CharField(max_length=200, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-km"]

    def __str__(self):
        return f"{self.tarea} · {self.moto} · {self.km} km"

    @property
    def donde(self):
        """Dónde se hizo: un taller de TallerYa, otro taller, o vacío si lo hizo el dueño."""
        if self.taller:
            return str(self.taller)
        return self.taller_otro


# ---------------------------------------------------------------------------
# Despiece: láminas del catálogo de partes de una versión de moto
# ---------------------------------------------------------------------------
class Despiece(models.Model):
    """Catálogo de partes de una versión (ej: Yamaha NMAX BBE4 2024)."""

    linea = models.ForeignKey(LineaMoto, on_delete=models.CASCADE, related_name="despieces")
    version = models.CharField(max_length=20, help_text="Código de versión del catálogo. Ej: BBE4")
    anio = models.PositiveSmallIntegerField("año")
    fuente = models.URLField(blank=True, help_text="De dónde salió el catálogo")
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["linea", "-anio"]
        verbose_name_plural = "despieces"
        constraints = [models.UniqueConstraint(fields=["linea", "version"], name="despiece_unico_por_version")]

    def __str__(self):
        return f"{self.linea} · {self.version} ({self.anio})"

    @classmethod
    def para(cls, moto):
        """Elige el catálogo más cercano al año de la moto (prefiere el de su año o anterior)."""
        if not moto.linea_id:
            return None
        opciones = list(cls.objects.filter(linea_id=moto.linea_id, activo=True))
        if not opciones:
            return None
        return min(opciones, key=lambda d: (d.anio > moto.modelo, abs(d.anio - moto.modelo)))


class Lamina(models.Model):
    despiece = models.ForeignKey(Despiece, on_delete=models.CASCADE, related_name="laminas")
    figura = models.PositiveSmallIntegerField(help_text="Número de figura en el catálogo")
    titulo = models.CharField(max_length=120, help_text="Título original del catálogo")
    titulo_es = models.CharField("título en español", max_length=120, blank=True)
    pieza = models.CharField(max_length=20, choices=TareaMantenimiento.Pieza.choices,
                             help_text="Pieza del modelo 3D y del plan a la que corresponde")
    diagrama = models.CharField(
        max_length=30, blank=True,
        help_text="Diagrama propio de TallerYa (garaje/diagramas.py). Si está, se muestra en vez del plano del catálogo.",
    )
    imagen = models.ImageField(upload_to="despiece/", blank=True,
                               help_text="Plano original del catálogo (solo local; no se publica)")
    ancho = models.PositiveIntegerField(default=0)
    alto = models.PositiveIntegerField(default=0)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["despiece", "orden", "figura"]
        verbose_name = "lámina de despiece"
        verbose_name_plural = "láminas de despiece"
        constraints = [models.UniqueConstraint(fields=["despiece", "figura"], name="lamina_unica_por_figura")]

    def __str__(self):
        return f"FIG. {self.figura} {self.titulo_es or self.titulo}"

    @property
    def nombre(self):
        return self.titulo_es or self.titulo.capitalize()


class ParteDespiece(models.Model):
    lamina = models.ForeignKey(Lamina, on_delete=models.CASCADE, related_name="partes")
    ref = models.PositiveSmallIntegerField("ref.", help_text="Número de la pieza en el dibujo")
    codigo = models.CharField("código de repuesto", max_length=30)
    descripcion = models.CharField(max_length=120, help_text="Descripción original del catálogo")
    nombre_es = models.CharField("nombre en español", max_length=120, blank=True)
    ayuda = models.CharField("explicación", max_length=240, blank=True,
                             help_text="Qué es y cuándo revisarla, en palabras sencillas")
    cantidad = models.PositiveSmallIntegerField(default=1)
    nivel = models.PositiveSmallIntegerField(default=0, help_text="0 = pieza principal; 1+ = parte de un conjunto")
    tarea = models.ForeignKey(TareaMantenimiento, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="partes_despiece")
    # Posición en el dibujo, relativa (0 a 1). Vacía hasta marcarla en el admin.
    x = models.FloatField(null=True, blank=True)
    y = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["lamina", "ref", "pk"]
        verbose_name = "parte del despiece"
        verbose_name_plural = "partes del despiece"

    def __str__(self):
        return f"{self.ref} · {self.codigo} · {self.nombre}"

    @property
    def nombre(self):
        return self.nombre_es or self.descripcion.capitalize()

    @property
    def marcada(self):
        return self.x is not None and self.y is not None


@receiver(post_delete, sender=Moto)
def borrar_documentos(sender, instance, **kwargs):
    # Al eliminar una moto (o la cuenta), sus documentos personales se borran del disco.
    for campo in ("soat_archivo", "tecno_archivo"):
        archivo = getattr(instance, campo)
        if archivo:
            archivo.delete(save=False)
