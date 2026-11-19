"""Modelos del foro: preguntas por categoría, respuestas (con mejor respuesta), reportes de moderación y votos."""
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify

from talleres.models import Marca

REPORTES_PARA_OCULTAR = 3


class Categoria(models.TextChoices):
    MANTENIMIENTO = "mantenimiento", "Mantenimiento"
    FALLAS = "fallas", "Fallas y ruidos"
    RUTAS = "rutas", "Rutas y paseos"
    REPUESTOS = "repuestos", "Compra y venta de repuestos"
    TALLERES = "talleres", "Talleres"
    DOMICILIARIOS = "domiciliarios", "Domiciliarios"  # TallerYa Ruta: solo se ofrece con DOMICILIARIOS_ACTIVO
    GENERAL = "general", "General"


class Pregunta(models.Model):
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preguntas")
    titulo = models.CharField(max_length=150, help_text="Ej: ¿Cada cuánto cambio el aceite de una NKD 125?")
    cuerpo = models.TextField(max_length=3000)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name="preguntas")
    linea = models.ForeignKey("garaje.LineaMoto", on_delete=models.SET_NULL, null=True, blank=True, related_name="preguntas",
                              verbose_name="línea de moto")
    categoria = models.CharField(max_length=15, choices=Categoria.choices, default=Categoria.GENERAL, db_index=True)
    vistas = models.PositiveIntegerField(default=0)
    mejor_respuesta = models.OneToOneField(
        "Respuesta", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )
    visible = models.BooleanField(default=True)
    diagnostico = models.ForeignKey("DiagnosticoCompartido", on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="preguntas", verbose_name="diagnóstico citado")
    creado = models.DateTimeField(auto_now_add=True)
    # Última interacción (creación, respuesta nueva o edición de la pregunta): ordena "Recientes" y los grupos.
    ultima_actividad = models.DateTimeField("última actividad", null=True, blank=True, db_index=True)
    # Autor de la última respuesta (vacío si lo último fue crear o editar la pregunta)
    ultimo_autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="+", verbose_name="autor de la última respuesta")

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if self.ultima_actividad is None:
            from django.utils import timezone
            self.ultima_actividad = timezone.now()
        super().save(*args, **kwargs)

    def recalcular_actividad(self):
        """Vuelve a calcular la última actividad desde las respuestas visibles (tras borrar u ocultar una)."""
        ultima = self.respuestas.filter(visible=True).order_by("-creado").first()
        if ultima and ultima.creado > self.creado:
            self.ultima_actividad, self.ultimo_autor_id = ultima.creado, ultima.autor_id
        else:
            self.ultima_actividad, self.ultimo_autor_id = self.creado, None
        Pregunta.objects.filter(pk=self.pk).update(ultima_actividad=self.ultima_actividad, ultimo_autor_id=self.ultimo_autor_id)

    @property
    def slug(self):
        return slugify(self.titulo)[:60] or "pregunta"

    def get_absolute_url(self):
        return reverse("foro:pregunta", args=[self.pk, self.slug])


class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name="respuestas")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="respuestas")
    # Mensaje al que responde dentro del tema (vacío = responde a la pregunta). Si se borra, la respuesta sube de nivel.
    padre = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="hijas",
                              verbose_name="en respuesta a")
    cuerpo = models.TextField(max_length=3000)
    visible = models.BooleanField(default=True)
    diagnostico = models.ForeignKey("DiagnosticoCompartido", on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="respuestas", verbose_name="diagnóstico citado")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]

    def __str__(self):
        return f"Respuesta de {self.autor} a «{self.pregunta}»"

    def save(self, *args, **kwargs):
        nueva = self._state.adding
        super().save(*args, **kwargs)
        if nueva and self.visible:  # una respuesta nueva sube el tema en "Recientes"
            Pregunta.objects.filter(pk=self.pregunta_id).update(ultima_actividad=self.creado, ultimo_autor_id=self.autor_id)

    def get_absolute_url(self):
        return f"{self.pregunta.get_absolute_url()}#r{self.pk}"


class Reporte(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reportes")
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, null=True, blank=True, related_name="reportes")
    respuesta = models.ForeignKey(Respuesta, on_delete=models.CASCADE, null=True, blank=True, related_name="reportes")
    motivo = models.CharField(max_length=200, blank=True)
    revisado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["revisado", "-creado"]
        constraints = [
            models.CheckConstraint(
                condition=Q(pregunta__isnull=False, respuesta__isnull=True) | Q(pregunta__isnull=True, respuesta__isnull=False),
                name="reporte_un_solo_objetivo",
            ),
            models.UniqueConstraint(fields=["usuario", "pregunta"], condition=Q(pregunta__isnull=False), name="un_reporte_por_pregunta"),
            models.UniqueConstraint(fields=["usuario", "respuesta"], condition=Q(respuesta__isnull=False), name="un_reporte_por_respuesta"),
        ]

    def __str__(self):
        return f"Reporte de {self.usuario} sobre {self.objetivo}"

    @property
    def objetivo(self):
        return self.pregunta or self.respuesta


class Voto(models.Model):
    """Voto "me sirvió" de un usuario a una pregunta o a una respuesta (uno por usuario y publicación)."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votos_foro")
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, null=True, blank=True, related_name="votos")
    respuesta = models.ForeignKey(Respuesta, on_delete=models.CASCADE, null=True, blank=True, related_name="votos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(pregunta__isnull=False, respuesta__isnull=True) | Q(pregunta__isnull=True, respuesta__isnull=False),
                name="voto_un_solo_objetivo",
            ),
            models.UniqueConstraint(fields=["usuario", "pregunta"], condition=Q(pregunta__isnull=False), name="un_voto_por_pregunta"),
            models.UniqueConstraint(fields=["usuario", "respuesta"], condition=Q(respuesta__isnull=False), name="un_voto_por_respuesta"),
        ]



class Reaccion(models.Model):
    """Reacción con emoji a una pregunta o respuesta (una por usuario y mensaje; se cambia o se quita).
    "Me sirvió" no es una reacción: es el Voto, que cuenta para ordenar y para la solución."""

    class Tipo(models.TextChoices):
        GUSTA = "gusta", "Me gusta"
        ENCANTA = "encanta", "Me encanta"
        DIVIERTE = "divierte", "Me divierte"
        PREOCUPA = "preocupa", "Me preocupa"
        DESACUERDO = "desacuerdo", "No estoy de acuerdo"

    EMOJI = {"gusta": "👍", "encanta": "❤️", "divierte": "😄", "preocupa": "😟", "desacuerdo": "👎"}

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reacciones_foro")
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, null=True, blank=True, related_name="reacciones")
    respuesta = models.ForeignKey(Respuesta, on_delete=models.CASCADE, null=True, blank=True, related_name="reacciones")
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "reacción"
        verbose_name_plural = "reacciones"
        constraints = [
            models.CheckConstraint(
                condition=Q(pregunta__isnull=False, respuesta__isnull=True) | Q(pregunta__isnull=True, respuesta__isnull=False),
                name="reaccion_un_solo_objetivo",
            ),
            models.UniqueConstraint(fields=["usuario", "pregunta"], condition=Q(pregunta__isnull=False), name="una_reaccion_por_pregunta"),
            models.UniqueConstraint(fields=["usuario", "respuesta"], condition=Q(respuesta__isnull=False), name="una_reaccion_por_respuesta"),
        ]

    def __str__(self):
        return f"{self.EMOJI.get(self.tipo, '')} {self.usuario} → {self.pregunta or self.respuesta}"

class Rodada(models.Model):
    """Rodada o evento: sus comentarios y reportes son los de su pregunta del foro (tema "Rutas y paseos")."""

    class Nivel(models.TextChoices):
        PRINCIPIANTE = "principiante", "Principiante · ritmo suave"
        INTERMEDIO = "intermedio", "Intermedio"
        AVANZADO = "avanzado", "Avanzado · ruta exigente"

    pregunta = models.OneToOneField(Pregunta, on_delete=models.CASCADE, related_name="rodada")
    organizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rodadas_organizadas")
    fecha_hora = models.DateTimeField("fecha y hora", db_index=True)
    punto_encuentro = models.CharField(
        "punto de encuentro", max_length=150,
        help_text="Un lugar público: estación del metro, parque, bomba de gasolina. Nunca una casa o apartamento.",
    )
    destino = models.CharField("destino o ruta", max_length=200, help_text="Ej: Santa Elena por Las Palmas, regreso por Guarne")
    nivel = models.CharField(max_length=15, choices=Nivel.choices, default=Nivel.PRINCIPIANTE)
    cupo = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Déjalo vacío si no hay límite.")

    class Meta:
        ordering = ["fecha_hora"]

    def __str__(self):
        return self.pregunta.titulo

    @property
    def titulo(self):
        return self.pregunta.titulo

    @property
    def pasada(self):
        from django.utils import timezone
        return self.fecha_hora < timezone.now()

    def get_absolute_url(self):
        return reverse("foro:rodada", args=[self.pk])


class Asistencia(models.Model):
    """Un "Voy" de un usuario a una rodada."""
    rodada = models.ForeignKey(Rodada, on_delete=models.CASCADE, related_name="asistencias")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="asistencias_rodada")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]
        constraints = [models.UniqueConstraint(fields=["rodada", "usuario"], name="un_voy_por_rodada")]


class DiagnosticoCompartido(models.Model):
    """Resumen inmutable de un diagnóstico guiado citado en el foro (los diagnósticos no se guardan: son una URL).

    Lo arma el servidor al publicar (garaje.vista_diagnostico.resumen_diagnostico) desde una consulta que el autor vio
    en su sesión y con sus propias motos. Solo datos públicos de la moto: marca, modelo y año; nunca placa ni dueño."""
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diagnosticos_compartidos")
    clave = models.CharField("resultado", max_length=40, db_index=True)
    sintoma_clave = models.CharField(max_length=40)
    sintoma = models.CharField("síntoma", max_length=80)
    marca = models.CharField(max_length=60, blank=True)
    modelo = models.CharField(max_length=80, blank=True)
    anio = models.PositiveSmallIntegerField("año", null=True, blank=True)
    causa = models.CharField("causa probable", max_length=200)
    sistema = models.CharField(max_length=60, db_index=True)
    subgrupo = models.CharField(max_length=80, blank=True)
    urgencia = models.CharField(max_length=20)
    revisa = models.CharField("revisa tú mismo", max_length=300, blank=True)
    piezas = models.JSONField("piezas sugeridas", default=list, blank=True)
    enlace = models.CharField(max_length=500, help_text="Abre el mismo diagnóstico (con el despiece de la línea, no la moto)")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "diagnóstico compartido"
        verbose_name_plural = "diagnósticos compartidos"

    def __str__(self):
        return f"{self.sintoma}: {self.causa}"

    @property
    def moto(self):
        return " ".join(str(x) for x in (self.marca, self.modelo, self.anio) if x)

    @classmethod
    def desde_resumen(cls, autor, resumen):
        campos = {f.name for f in cls._meta.fields} - {"id", "autor", "creado"}
        return cls.objects.create(autor=autor, **{k: v for k, v in resumen.items() if k in campos})
