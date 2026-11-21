import re
from datetime import timedelta
import secrets
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
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
    "numero": "Número de carreras", "texto": "Texto propio", "tallerya": "Logo TallerYa", "imagen": "Subir imagen",
}
# Calca con imagen propia: data URL PNG/JPEG/WebP ya reducido en el navegador (≤256 px). Tope en caracteres.
MAX_IMAGEN_CALCA = 200_000
PREFIJOS_IMAGEN_CALCA = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")
ZONAS_CALCA = {"lateral": "Laterales", "frontal": "Frontal", "tanque": "Tanque", "cola": "Cola"}
MAX_CALCAS = 4

COLORES = [
    ("#c62828", "Rojo"), ("#1f4fa8", "Azul"), ("#1b1b1b", "Negro"), ("#e8e4da", "Blanco"),
    ("#8a9096", "Gris"), ("#f2611d", "Naranja"), ("#2f7d4a", "Verde"), ("#e3a72f", "Amarillo"),
]
# Más tonos para personalizar el modelo 3D (no aparecen en el formulario de registro).
COLORES_EXTRA = [("#c0c4c8", "Plata"), ("#5b3a8c", "Morado"), ("#e86fa6", "Rosa"), ("#1f9aa0", "Turquesa")]
ID_CALCA_FABRICA = re.compile(r"[a-z][a-z0-9_]{0,23}")  # ids de las calcas de fábrica (moto3d/calcas_fabrica.js)
# Opciones de estilo del modelo 3D (el navegador muestra solo las que le quedan a cada tipo de moto)
ACABADOS_3D = ("brillante", "mate", "satinado", "metalizado", "perlado")
RINES_3D = ("fabrica", "radios", "aleacion", "estrella")
ACCESORIOS_3D = ("baul", "cubremanos", "parabrisas", "exploradoras", "sliders", "escape", "protector", "led")
ESPEJOS_3D = ("fabrica", "redondos", "puntas")

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


def sumar_anios(fecha, anios):
    """Misma fecha N años después (el 29 de febrero pasa al 28 si el año no es bisiesto)."""
    try:
        return fecha.replace(year=fecha.year + anios)
    except ValueError:
        return fecha.replace(year=fecha.year + anios, day=28)


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
    estilo = models.JSONField(default=dict, blank=True,
                              help_text="Estilo del modelo 3D: acabado, segundo tono, colores de chasis y asiento, rin y accesorios")
    apodo = models.CharField(max_length=40, blank=True, help_text="Opcional. Ej: La Negra")
    placa = models.CharField(max_length=8, blank=True, help_text="Opcional y privada. Ej: ABC12D")
    # Documentos (opcionales): fecha de vencimiento y una foto o PDF, solo visibles para el dueño.
    soat_vence = models.DateField("vencimiento del SOAT", null=True, blank=True)
    soat_archivo = models.FileField("foto o PDF del SOAT", storage=almacen_privado, upload_to=ruta_documento, blank=True)
    tecno_vence = models.DateField("vencimiento de la técnico-mecánica", null=True, blank=True)
    tecno_archivo = models.FileField("foto o PDF de la técnico-mecánica", storage=almacen_privado,
                                     upload_to=ruta_documento, blank=True)
    matricula = models.DateField("fecha de matrícula", null=True, blank=True,
                                 help_text="Sirve para calcular la primera técnico-mecánica (a los 2 años)")
    perfil_uso = models.CharField(
        "¿cómo la usas?", max_length=12, blank=True,
        choices=[("fines_semana", "Solo fines de semana y paseos"), ("ciudad", "Ciudad, a diario"),
                 ("trabajo", "Trabajo o domicilios"), ("carretera", "Mucha carretera")],
        help_text="Con esto estimamos cuántos km recorres al día hasta tener tus lecturas")
    km_inicial = models.PositiveIntegerField("kilometraje al registrarla")
    km_actual = models.PositiveIntegerField()
    # Última vez que dijo «no ahora» a la confirmación de km: no se le vuelve a preguntar en unos días
    km_pregunta_pospuesta = models.DateField(null=True, blank=True, editable=False)
    # Pico y placa (solo si tiene placa)
    aviso_pico_placa = models.BooleanField("avisarme del pico y placa en TallerYa", default=True)
    pico_placa_whatsapp = models.BooleanField("recordarme el pico y placa por WhatsApp", default=False)
    pico_placa_enviado = models.DateField(null=True, blank=True, editable=False,
                                          help_text="Último día por el que se envió el recordatorio por WhatsApp")
    # Desde cuándo es de este dueño (solo si llegó por traspaso): lo de antes que sea personal del dueño anterior
    # (p. ej. pedidos de SOAT con sus datos) no se le muestra al nuevo.
    dueno_desde = models.DateTimeField(null=True, blank=True, editable=False)
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
    def nombre_corto(self):
        """Solo la línea ("Pulsar NS 200"), sin marca ni año, para espacios estrechos como la ficha de la portada."""
        if self.apodo:
            return self.apodo
        return (self.linea.nombre if self.linea else self.linea_otra or self.marca_otra) or self.nombre_completo

    @property
    def tipo(self):
        return self.linea.tipo if self.linea else (self.tipo_otra or Tipo.CALLE)

    def specs(self):
        if not self.linea:
            return {"tipo": self.tipo, **SPECS_POR_TIPO[self.tipo]}
        specs = self.linea.specs()
        # Una versión de la línea puede diferir de la ficha general (la Gixxer 150 2015 traía tambor atrás; la 2020, disco):
        # manda la del despiece que corresponde al año de la moto
        if self.modelo:
            despiece = Despiece.para(self)
            if despiece and despiece.especificaciones:
                specs = {**specs, **despiece.especificaciones}
        return specs

    def get_absolute_url(self):
        return reverse("garaje:moto", args=[self.pk])

    def pedidos_soat_del_dueno(self):
        """Pedidos de SOAT de quien la tiene hoy: los del dueño anterior (con sus datos) no se muestran."""
        pedidos = self.pedidos_soat.all()
        return pedidos.filter(creado__gte=self.dueno_desde) if self.dueno_desde else pedidos

    @property
    def color_contraste(self):
        """Color para dibujar encima de la pintura de la moto: oscuro sobre colores claros y crema sobre oscuros."""
        n = int(self.color[1:], 16)
        claridad = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255
        return "#111517" if claridad > 0.6 else "#ede3cc"

    def documentos(self, hoy=None):
        """Estado de SOAT y técnico-mecánica para mostrar y recordar (escala única de garaje.avisos)."""
        from .avisos import nivel_documento, texto_vence
        hoy = hoy or timezone.localdate()
        lista = []
        for clave, nombre in DOCUMENTOS.items():
            vence = getattr(self, f"{clave}_vence")
            estimado = False
            if clave == "tecno" and not vence and self.matricula:
                # Sin fecha de la última revisión: la primera va a los 2 años de la matrícula (Ley 769 de 2002, art. 52).
                primera = sumar_anios(self.matricula, 2)
                if primera >= hoy:
                    vence, estimado = primera, True
            dias = (vence - hoy).days if vence else None
            estado = nivel_documento(dias)
            lista.append({"clave": clave, "nombre": nombre, "vence": vence, "dias": dias, "estado": estado,
                          "estimado": estimado, "texto": texto_vence(dias),
                          "dias_abs": abs(dias) if dias is not None else None,
                          # Vigencia que le queda sobre un año (para la barra)
                          "pct": max(0, min(100, round(dias * 100 / 365))) if dias is not None else 0,
                          "archivo": bool(getattr(self, f"{clave}_archivo"))})
        return lista

    def aviso_documentos(self, hoy=None):
        """Un recordatorio corto para la ficha de la moto, o None si todo está al día."""
        docs = self.documentos(hoy)
        vencidos = [d["nombre"] for d in docs if d["estado"] == "vencido"]
        if vencidos:
            return {"estado": "vencido", "texto": f"{' y '.join(vencidos)} vencido{'s' if len(vencidos) > 1 else ''}"}
        pronto = sorted((d for d in docs if d["estado"] in ("urgente", "pronto")), key=lambda d: d["dias"])
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
    def limpiar_estilo(estilo):
        """Valida el estilo del modelo 3D que llega del navegador. Devuelve el dict limpio o lanza ValueError."""
        if not isinstance(estilo, dict):
            raise ValueError("Estilo inválido.")
        limpio = {}
        acabado = estilo.get("acabado") or "brillante"
        if acabado not in ACABADOS_3D:
            raise ValueError("Acabado inválido.")
        if acabado != "brillante":
            limpio["acabado"] = acabado
        for campo in ("color2", "chasis", "asiento", "led"):
            valor = estilo.get(campo) or ""
            if valor:
                HEX(str(valor))
                limpio[campo] = str(valor).lower()
        espejos = estilo.get("espejos") or "fabrica"
        if espejos not in ESPEJOS_3D:
            raise ValueError("Retrovisores inválidos.")
        if espejos != "fabrica":
            limpio["espejos"] = espejos
        rin = estilo.get("rin") or "fabrica"
        if rin not in RINES_3D:
            raise ValueError("Rin inválido.")
        if rin != "fabrica":
            limpio["rin"] = rin
        accesorios = estilo.get("accesorios") or []
        if not isinstance(accesorios, list) or any(a not in ACCESORIOS_3D for a in accesorios):
            raise ValueError("Accesorio inválido.")
        if accesorios:
            limpio["accesorios"] = sorted(set(accesorios))
        # Calcas de fábrica que el usuario quitó (ids cortos: "nombre", "cilindrada", "franja"…)
        sin_fabrica = estilo.get("sin_fabrica") or []
        if (not isinstance(sin_fabrica, list) or len(sin_fabrica) > 8
                or any(not isinstance(i, str) or not ID_CALCA_FABRICA.fullmatch(i) for i in sin_fabrica)):
            raise ValueError("Calcas de fábrica inválidas.")
        if sin_fabrica:
            limpio["sin_fabrica"] = sorted(set(sin_fabrica))
        # Colores que el usuario le puso a cada calca de fábrica: {id: {"p": principal, "s": secundario}}
        colores = estilo.get("color_fabrica") or {}
        if not isinstance(colores, dict) or len(colores) > 8:
            raise ValueError("Colores de calcas de fábrica inválidos.")
        limpios = {}
        for clave, par in colores.items():
            if not ID_CALCA_FABRICA.fullmatch(str(clave)) or not isinstance(par, dict) or set(par) - {"p", "s"}:
                raise ValueError("Colores de calcas de fábrica inválidos.")
            propio = {}
            for slot, valor in par.items():
                HEX(str(valor))
                propio[slot] = str(valor).lower()
            if propio:
                limpios[clave] = propio
        if limpios:
            limpio["color_fabrica"] = limpios
        return limpio

    @staticmethod
    def limpiar_imagen_calca(imagen):
        """Valida la imagen propia de una calca: data URL de imagen, base64 válido y liviano."""
        import base64
        import binascii
        if not isinstance(imagen, str) or len(imagen) > MAX_IMAGEN_CALCA or not imagen.startswith(PREFIJOS_IMAGEN_CALCA):
            raise ValueError("La imagen de la calca no es válida o es muy pesada.")
        try:
            datos = base64.b64decode(imagen.split(",", 1)[1], validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("La imagen de la calca no es válida.")
        # Firma del archivo: PNG, JPEG o WebP de verdad (no otra cosa con el prefijo cambiado)
        if not (datos.startswith(b"\x89PNG") or datos.startswith(b"\xff\xd8") or (datos[:4] == b"RIFF" and datos[8:12] == b"WEBP")):
            raise ValueError("La imagen de la calca no es válida.")
        return imagen

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
            if c["diseno"] == "imagen":
                limpia["imagen"] = Moto.limpiar_imagen_calca(c.get("imagen"))
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
    # Confirmada con un toque a partir de una estimación (no la escribió el motero ni la vio un taller)
    estimada = models.BooleanField(default=False)
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
    variante = models.CharField(max_length=40, blank=True,
                                help_text="Cómo se distingue de otra versión de la misma línea (ej: Carburador, FI ABS)")
    especificaciones = models.JSONField(default=dict, blank=True,
                                        help_text='Lo que esta versión cambia de la ficha de la línea, ej: {"freno_trasero": "tambor"}')
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
        """Entre los catálogos activos de la línea, el que corresponde al año de la moto: el de año igual o anterior más
        cercano (una Gixxer 2017 usa el de 2015, una 2021 el de 2020); si la moto es más vieja que todos, el más antiguo."""
        if not moto.linea_id:
            return None
        # Se guarda en la moto mientras dure la petición: la ficha lo pide varias veces (specs, plan, despiece).
        clave = (moto.linea_id, moto.modelo)
        guardado = getattr(moto, "_despiece_para", None)
        if guardado and guardado[0] == clave:
            return guardado[1]
        opciones = list(cls.objects.filter(linea_id=moto.linea_id, activo=True))
        elegido = min(opciones, key=lambda d: (d.anio > moto.modelo, abs(d.anio - moto.modelo))) if opciones else None
        moto._despiece_para = (clave, elegido)
        return elegido

    @classmethod
    def precargar(cls, motos):
        """Deja elegido el catálogo de varias motos con una sola consulta (Mi garaje), para que para() no consulte."""
        por_linea = {}
        for d in cls.objects.filter(linea_id__in={m.linea_id for m in motos if m.linea_id}, activo=True):
            por_linea.setdefault(d.linea_id, []).append(d)
        for m in motos:
            if m.linea_id:
                opciones = por_linea.get(m.linea_id, [])
                m._despiece_para = ((m.linea_id, m.modelo), min(
                    opciones, key=lambda d: (d.anio > m.modelo, abs(d.anio - m.modelo))) if opciones else None)


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


class ReglaPicoPlaca(models.Model):
    """Rotación de pico y placa para motos. Se carga desde el admin con cada decreto (cambia cada semestre)."""

    class Digito(models.TextChoices):
        PRIMERO = "primero", "Primer número de la placa"
        ULTIMO = "ultimo", "Último número de la placa"

    ciudad = models.CharField(max_length=60, default="Medellín")
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(null=True, blank=True, help_text="Vacío: rige hasta que empiece la siguiente rotación")
    digito = models.CharField("número que cuenta", max_length=8, choices=Digito.choices, default=Digito.PRIMERO)
    lunes = models.CharField(max_length=20, blank=True, help_text="Dígitos separados por coma. Ej: 5,8")
    martes = models.CharField(max_length=20, blank=True)
    miercoles = models.CharField("miércoles", max_length=20, blank=True)
    jueves = models.CharField(max_length=20, blank=True)
    viernes = models.CharField(max_length=20, blank=True)
    fin_por_verificar = models.BooleanField("fecha de fin por verificar", default=False,
                                            help_text="La fecha de fin viene de la prensa, no del decreto")
    horario = models.CharField(max_length=80, default="5:00 a. m. a 8:00 p. m.")
    fuente = models.CharField(max_length=120, blank=True)
    fuente_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-vigente_desde"]
        verbose_name = "regla de pico y placa"
        verbose_name_plural = "reglas de pico y placa"

    def __str__(self):
        return f"{self.ciudad} desde {self.vigente_desde:%d/%m/%Y}"

    DIAS = ("lunes", "martes", "miercoles", "jueves", "viernes")

    def digitos(self, dia_semana):
        """Dígitos restringidos para un día (0 = lunes). Fines de semana: ninguno."""
        if dia_semana > 4:
            return []
        return [d.strip() for d in getattr(self, self.DIAS[dia_semana]).split(",") if d.strip()]


# ---------------------------------------------------------------------------
# Hoja de vida: servicios de la moto (los del taller, verificados con un código que muestra el dueño)
# ---------------------------------------------------------------------------
class RegistroServicio(models.Model):
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="hoja_vida")
    fecha = models.DateField(default=timezone.localdate)
    km = models.PositiveIntegerField("kilometraje")
    servicios = models.CharField("qué se le hizo", max_length=300)
    notas = models.CharField(max_length=300, blank=True)
    costo = models.PositiveIntegerField("costo (COP)", null=True, blank=True)
    taller = models.ForeignKey(Taller, on_delete=models.SET_NULL, null=True, blank=True, related_name="servicios_registrados")
    taller_otro = models.CharField("otro taller", max_length=80, blank=True)
    # Mecánico a domicilio de TallerYa que lo hizo (en vez de un taller; nunca los dos)
    mecanico = models.ForeignKey("domicilio.MecanicoDomicilio", on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="servicios_registrados", verbose_name="mecánico a domicilio")
    # Solo lo marca el sistema cuando lo registra un taller con el código del dueño.
    verificado = models.BooleanField(default=False, editable=False)
    # Una sola fuente de historial: el mantenimiento del plan que este registro representa (si viene de la ficha,
    # del despiece o de "poner al día", o si al agregarlo aquí se eligió qué mantenimiento cubre).
    mantenimiento = models.OneToOneField("Mantenimiento", on_delete=models.SET_NULL, null=True, blank=True,
                                         editable=False, related_name="registro_hoja")
    # Si lo registró el taller desde su panel (cita, código o placa): el servicio completo con foto y tareas.
    servicio_taller = models.ForeignKey("ServicioTaller", on_delete=models.SET_NULL, null=True, blank=True,
                                        editable=False, related_name="registros")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-km", "-creado"]
        verbose_name = "registro de servicio"
        verbose_name_plural = "hoja de vida (servicios)"
        constraints = [models.CheckConstraint(condition=Q(taller__isnull=True) | Q(mecanico__isnull=True),
                                              name="registro_taller_o_mecanico")]

    def __str__(self):
        return f"{self.moto} · {self.fecha:%d/%m/%Y} · {self.servicios[:40]}"

    @property
    def estado_verificacion(self):
        """verificado · pendiente (con un taller de TallerYa que aún no lo confirma) · propio."""
        return "verificado" if self.verificado else "pendiente" if self.taller_id else "propio"

    @property
    def donde(self):
        if self.taller:
            return str(self.taller)
        if self.mecanico:
            return f"Mecánico a domicilio: {self.mecanico.nombre}"
        return self.taller_otro


class CodigoServicio(models.Model):
    """Código corto de un solo uso que el dueño le muestra al taller para que registre un servicio verificado."""
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="codigos_servicio")
    codigo = models.CharField(max_length=8, unique=True)
    vence = models.DateTimeField()
    usado = models.DateTimeField(null=True, blank=True)
    # Registro pendiente que este código va a verificar (el motero lo anotó con ese taller): el taller lo verifica
    # a él en vez de crear otro.
    registro = models.ForeignKey("RegistroServicio", on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="codigos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "código de servicio"
        verbose_name_plural = "códigos de servicio"

    def __str__(self):
        return f"{self.codigo} · {self.moto}"

    @property
    def vigente(self):
        return self.usado is None and self.vence > timezone.now()


def ruta_foto_servicio(instancia, nombre):
    return f"servicios/{uuid4().hex}{Path(nombre).suffix.lower()}"


class ServicioTaller(models.Model):
    """Servicio que el taller registra desde su panel (al cerrar una cita, con el código/QR del dueño o por placa).
    Con cita o código queda verificado de una vez; por placa espera a que el dueño lo confirme desde su aviso.
    Al verificarse alimenta la hoja de vida y el plan de mantenimiento (garaje.servicio_taller.aplicar)."""

    class Estado(models.TextChoices):
        POR_CONFIRMAR = "por_confirmar", "Esperando al dueño"
        VERIFICADO = "verificado", "Verificado"
        RECHAZADO = "rechazado", "No reconocido por el dueño"

    class Origen(models.TextChoices):
        CITA = "cita", "Cita"
        CODIGO = "codigo", "Código o QR del dueño"
        PLACA = "placa", "Búsqueda por placa"
        VISITA = "visita", "Visita a domicilio"

    # Lo hace un taller o un mecánico a domicilio (uno de los dos, nunca ambos)
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, null=True, blank=True, related_name="servicios_taller")
    mecanico = models.ForeignKey("domicilio.MecanicoDomicilio", on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="servicios_hechos", verbose_name="mecánico a domicilio")
    solicitud = models.ForeignKey("domicilio.SolicitudVisita", on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="servicios_hechos")
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="servicios_taller")
    cita = models.ForeignKey("talleres.SolicitudCita", on_delete=models.SET_NULL, null=True, blank=True,
                             related_name="servicios_hechos")
    fecha = models.DateField(default=timezone.localdate)
    km = models.PositiveIntegerField("kilometraje")
    tareas = models.ManyToManyField(TareaMantenimiento, blank=True, related_name="+")
    otros = models.CharField("otros trabajos", max_length=200, blank=True)
    costo = models.PositiveIntegerField("valor (COP)", null=True, blank=True)
    notas = models.CharField("nota para el dueño", max_length=300, blank=True)
    foto = models.ImageField(upload_to=ruta_foto_servicio, blank=True)
    estado = models.CharField(max_length=14, choices=Estado.choices, default=Estado.POR_CONFIRMAR)
    origen = models.CharField(max_length=8, choices=Origen.choices)
    respondido = models.DateTimeField(null=True, blank=True)
    # Bitácora: qué cuenta lo registró y desde qué IP (el taller y la fecha ya están arriba)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name="+", editable=False)
    ip = models.GenericIPAddressField(null=True, blank=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-creado"]
        verbose_name = "servicio registrado por el taller"
        verbose_name_plural = "servicios registrados por talleres"
        constraints = [models.CheckConstraint(
            condition=(Q(taller__isnull=False) & Q(mecanico__isnull=True)) | (Q(taller__isnull=True) & Q(mecanico__isnull=False)),
            name="servicio_de_taller_o_mecanico")]

    def __str__(self):
        return f"{self.prestador} · {self.moto} · {self.fecha:%d/%m/%Y}"

    @property
    def prestador(self):
        """Quién lo hizo: el taller o el mecánico a domicilio."""
        return self.taller or self.mecanico

    @property
    def prestador_texto(self):
        return self.taller.nombre if self.taller else f"Mecánico a domicilio: {self.mecanico.nombre}"

    def get_absolute_url(self):
        return reverse("garaje:servicio_taller", args=[self.pk])

    @property
    def dueno(self):
        return self.moto.motociclista.usuario

    def resumen(self):
        """Lo que se hizo en una línea: tareas del plan y otros trabajos."""
        partes = [t.nombre for t in self.tareas.all()]
        if self.otros:
            partes.append(self.otros)
        return ", ".join(partes)


def token_enlace():
    return secrets.token_urlsafe(24)


class EnlaceHojaVida(models.Model):
    """Enlace público (sin nombre, placa enmascarada) para mostrar la hoja de vida, p. ej. al vender la moto."""
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="enlaces_hoja_vida")
    token = models.CharField(max_length=40, unique=True, default=token_enlace, editable=False)
    creado = models.DateTimeField(auto_now_add=True)
    revocado = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "enlace de hoja de vida"
        verbose_name_plural = "enlaces de hoja de vida"

    def __str__(self):
        return f"Hoja de vida de {self.moto}{' (revocado)' if self.revocado else ''}"

    def get_absolute_url(self):
        return reverse("garaje:hoja_vida_publica", args=[self.token])


def token_traspaso():
    return secrets.token_urlsafe(24)


class TraspasoMoto(models.Model):
    """Enlace de un solo uso para pasarle la moto (con su hoja de vida) a quien la compra. Queda como registro."""
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="traspasos")
    token = models.CharField(max_length=40, unique=True, default=token_traspaso, editable=False)
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    comprador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="+")
    vence = models.DateTimeField()
    usado = models.DateTimeField(null=True, blank=True)
    cancelado = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "traspaso de moto"
        verbose_name_plural = "traspasos de motos"

    def __str__(self):
        return f"Traspaso de {self.moto}{' (hecho)' if self.usado else ''}"

    @property
    def vigente(self):
        return self.usado is None and self.cancelado is None and self.vence > timezone.now()

    def get_absolute_url(self):
        return reverse("garaje:traspaso", args=[self.token])


# ---------------------------------------------------------------------------
# Gastos y consumo (los servicios con costo de la hoja de vida se suman aparte, sin duplicarlos)
# ---------------------------------------------------------------------------
class Gasto(models.Model):
    class Tipo(models.TextChoices):  # íconos y colores: garaje.gastos.CATEGORIAS
        GASOLINA = "gasolina", "Gasolina"
        ACEITE = "aceite", "Aceite y lubricantes"
        SERVICIO = "servicio", "Servicio en taller"
        REPUESTO = "repuesto", "Repuestos"
        LLANTAS = "llantas", "Llantas"
        LAVADA = "lavada", "Lavada"
        ACCESORIOS = "accesorios", "Accesorios y equipo"
        SOAT = "soat", "SOAT"
        TECNO = "tecno", "Técnico-mecánica"
        PARQUEADERO = "parqueadero", "Parqueadero"
        MULTA = "multa", "Multas"
        OTRO = "otro", "Otro"

    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name="gastos")
    fecha = models.DateField(default=timezone.localdate)
    tipo = models.CharField("categoría", max_length=12, choices=Tipo.choices, default=Tipo.GASOLINA)
    valor = models.PositiveIntegerField("valor (COP)")
    # Ya no se piden en el formulario (los km salen de las lecturas y los galones se estiman con el precio);
    # se conservan para no perder lo que se registró antes.
    galones = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    km = models.PositiveIntegerField("kilometraje", null=True, blank=True)
    tanque_lleno = models.BooleanField("tanque lleno", default=False)
    notas = models.CharField(max_length=120, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-creado"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.moto} · ${self.valor}"


# ---------- Ficha pública de un diagnóstico (piloto, paso 4) ----------
VIGENCIA_FICHA_DIAS = 30


def ruta_foto_ficha(instancia, nombre):
    return f"diagnosticos/{uuid4().hex}.jpg"


class FichaDiagnostico(models.Model):
    """Foto fija de un diagnóstico que el motero envía a un taller o a un mecánico a domicilio por WhatsApp.
    Se abre con un token no adivinable, sin cuenta, y vence a los 30 días. Solo guarda moto (marca, modelo, año),
    km, síntoma, causa y fotos: nunca placa, nombre, teléfono ni dueño."""

    class Destino(models.TextChoices):
        TALLER = "taller", "Taller"
        DOMICILIO = "domicilio", "Mecánico a domicilio"

    token = models.CharField(max_length=48, unique=True, editable=False)
    consulta = models.CharField(max_length=300, blank=True, help_text="Respuestas del diagnóstico (para reabrirlo)")
    moto = models.CharField(max_length=140, blank=True)
    km = models.PositiveIntegerField(null=True, blank=True)
    km_estimado = models.BooleanField(default=False)
    sintoma = models.CharField(max_length=80)
    causa = models.CharField(max_length=200)
    sistema = models.CharField(max_length=80, blank=True)
    urgencia = models.CharField(max_length=12, blank=True)
    revisa = models.CharField(max_length=300, blank=True)
    piezas = models.JSONField(default=list, blank=True)
    enlace = models.CharField("enlace al diagnóstico", max_length=300, blank=True)
    destino = models.CharField(max_length=10, choices=Destino.choices)
    taller = models.ForeignKey(Taller, on_delete=models.SET_NULL, null=True, blank=True, related_name="fichas_diagnostico")
    mecanico = models.ForeignKey("domicilio.MecanicoDomicilio", on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="fichas_diagnostico")
    creado = models.DateTimeField(auto_now_add=True)
    vence = models.DateTimeField()
    vistas = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "ficha de diagnóstico"
        verbose_name_plural = "fichas de diagnóstico"

    def __str__(self):
        return f"{self.sintoma} · {self.moto or 'sin moto'}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(24)
        if not self.vence:
            self.vence = timezone.now() + timedelta(days=VIGENCIA_FICHA_DIAS)
        super().save(*args, **kwargs)

    @property
    def vencida(self):
        return timezone.now() >= self.vence

    def get_absolute_url(self):
        return reverse("garaje:ficha_diagnostico", args=[self.token])


class FotoFichaDiagnostico(models.Model):
    ficha = models.ForeignKey(FichaDiagnostico, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to=ruta_foto_ficha)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "pk"]


@receiver(post_delete, sender=FotoFichaDiagnostico)
def _borrar_archivo_foto_ficha(sender, instance, **kwargs):
    if instance.imagen:
        instance.imagen.delete(save=False)
