from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class FuenteNoticias(models.Model):
    """Medio del que se traen titulares por RSS/Atom. Solo se guarda el titular, un resumen corto y el enlace a la nota."""

    nombre = models.CharField(max_length=80)
    url = models.URLField("dirección del RSS o Atom", unique=True)
    sitio = models.URLField(blank=True)
    solo_motos = models.BooleanField(default=True, help_text="Medio general: solo guarda notas de motos, tránsito o trámites")
    internacional = models.BooleanField(default=False, help_text="Medio de otro país: sus notas de tránsito o trámites no aplican en Colombia")
    activa = models.BooleanField(default=True)
    ultima_lectura = models.DateTimeField("última lectura", null=True, blank=True)
    ultimo_error = models.CharField("último error", max_length=200, blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "fuente de noticias"
        verbose_name_plural = "fuentes de noticias"

    def __str__(self):
        return self.nombre


class Articulo(models.Model):
    """Noticia motera. Las importadas enlazan a su fuente (sin cuerpo); las propias tienen cuerpo y página en TallerYa."""

    class Categoria(models.TextChoices):
        ACTUALIDAD = "actualidad", "Actualidad"
        LANZAMIENTO = "lanzamiento", "Lanzamientos"
        TRANSITO = "transito", "Tránsito y movilidad"
        TRAMITES = "tramites", "Trámites"
        CONSEJO = "consejo", "Consejos"

    titulo = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    categoria = models.CharField("categoría", max_length=12, choices=Categoria.choices, default=Categoria.ACTUALIDAD)
    resumen = models.CharField(max_length=300, help_text="Una o dos frases: se ven en la tarjeta")
    cuerpo = models.TextField(blank=True, help_text="Vacío = la noticia abre en su fuente. Separa los párrafos con una línea en blanco.")
    imagen = models.ImageField(upload_to="noticias/", blank=True)
    fuente = models.CharField(max_length=120, blank=True, help_text="Ej: Secretaría de Movilidad de Medellín")
    fuente_url = models.URLField(max_length=500, blank=True, db_index=True)
    origen = models.ForeignKey(FuenteNoticias, on_delete=models.SET_NULL, null=True, blank=True, related_name="articulos")
    internacional = models.BooleanField(default=False)
    lectura_min = models.PositiveSmallIntegerField("minutos de lectura", default=2)
    publicado = models.BooleanField(default=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "noticia"
        verbose_name_plural = "noticias"

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)[:160] or "noticia"
            slug, n = base, 2
            while Articulo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("noticias:articulo", args=[self.slug])

    @property
    def externo(self):
        return not self.cuerpo.strip() and bool(self.fuente_url)

    @property
    def enlace(self):
        return self.fuente_url if self.externo else self.get_absolute_url()

    @property
    def hace(self):
        segundos = max(0, (timezone.now() - self.fecha).total_seconds())
        if segundos < 3600:
            return f"hace {max(1, int(segundos // 60))} min"
        if segundos < 86400:
            return f"hace {int(segundos // 3600)} h"
        dias = int(segundos // 86400)
        return "ayer" if dias == 1 else (f"hace {dias} días" if dias < 30 else self.fecha.strftime("%d/%m/%Y"))

    @property
    def parrafos(self):
        return [p.strip() for p in self.cuerpo.split("\n\n") if p.strip()]
