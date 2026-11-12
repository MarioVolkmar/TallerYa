from django.db import models
from django.db.models import Count, F, Q
from django.urls import reverse
from django.utils import timezone

from talleres.models import Taller
from talleres.utils import codigo_aleatorio


class Motociclista(models.Model):
    """Se identifica por su celular; no tiene cuenta ni contraseña."""

    nombre = models.CharField(max_length=120)
    celular = models.CharField(max_length=12, unique=True, help_text="Formato 57XXXXXXXXXX")
    codigo_referido = models.CharField(max_length=8, unique=True, editable=False)
    referido_por = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="referidos",
    )
    premio_otorgado = models.BooleanField(
        default=False, help_text="Ya se entregó el premio a quien lo invitó",
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.nombre} ({self.celular_oculto})"

    def save(self, *args, **kwargs):
        if not self.codigo_referido:
            while True:
                codigo = codigo_aleatorio(6)
                if not Motociclista.objects.filter(codigo_referido=codigo).exists():
                    break
            self.codigo_referido = codigo
        super().save(*args, **kwargs)

    @property
    def celular_oculto(self):
        return f"•••• {self.celular[-4:]}"


class CuponQuerySet(models.QuerySet):
    def vigentes(self):
        hoy = timezone.localdate()
        return self.filter(activo=True).filter(Q(valido_hasta__isnull=True) | Q(valido_hasta__gte=hoy))

    def disponibles(self):
        """Cupones que un motociclista puede obtener ahora mismo."""
        return (
            self.vigentes()
            .filter(publico=True)
            .filter(Q(taller__isnull=True) | Q(taller__activo=True))
            .annotate(num_emitidos=Count("codigos"))
            .filter(Q(cupo__isnull=True) | Q(cupo__gt=F("num_emitidos")))
            .select_related("taller", "taller__barrio")
        )


class Cupon(models.Model):
    taller = models.ForeignKey(
        Taller, on_delete=models.CASCADE, null=True, blank=True, related_name="cupones",
        help_text="Déjalo vacío si el cupón vale en cualquier taller aliado.",
    )
    titulo = models.CharField(max_length=120, help_text="Ej: 15% de descuento en cambio de aceite")
    condiciones = models.TextField(blank=True, help_text="Ej: No acumulable. Válido de lunes a viernes.")
    valido_hasta = models.DateField(null=True, blank=True, help_text="Vacío = sin vencimiento")
    cupo = models.PositiveIntegerField(null=True, blank=True, help_text="Máximo de códigos a entregar. Vacío = sin límite")
    activo = models.BooleanField(default=True)
    publico = models.BooleanField(
        default=True, help_text="Aparece en la lista de cupones. Desmárcalo para cupones que solo se dan como premio.",
    )
    premio_referido = models.BooleanField(
        "premio por referido", default=False,
        help_text="Se entrega a quien invita cuando su amigo canjea su primer cupón. Se usa el más reciente activo.",
    )
    creado = models.DateTimeField(auto_now_add=True)

    objects = CuponQuerySet.as_manager()

    class Meta:
        ordering = ["-creado"]
        verbose_name = "cupón"
        verbose_name_plural = "cupones"

    def __str__(self):
        return f"{self.titulo} · {self.taller or 'Todos los talleres'}"

    def get_absolute_url(self):
        return reverse("cupones:obtener", args=[self.pk])

    @property
    def vigente(self):
        return self.activo and (self.valido_hasta is None or self.valido_hasta >= timezone.localdate())

    def puede_emitirse(self):
        return self.vigente and (self.cupo is None or self.codigos.count() < self.cupo)

    @classmethod
    def premio_actual(cls):
        return cls.objects.vigentes().filter(premio_referido=True).order_by("-creado").first()


class CodigoCupon(models.Model):
    """Código único que recibe un motociclista y que el taller marca como canjeado."""

    class Origen(models.TextChoices):
        OBTENIDO = "obtenido", "Obtenido por el motociclista"
        PREMIO = "premio", "Premio por referido"

    cupon = models.ForeignKey(Cupon, on_delete=models.PROTECT, related_name="codigos")
    motociclista = models.ForeignKey(Motociclista, on_delete=models.CASCADE, related_name="codigos")
    codigo = models.CharField(max_length=9, unique=True, editable=False)
    origen = models.CharField(max_length=10, choices=Origen.choices, default=Origen.OBTENIDO)
    referido = models.ForeignKey(
        Motociclista, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
        help_text="Amigo cuyo canje generó este premio",
    )
    creado = models.DateTimeField(auto_now_add=True)
    canjeado_en = models.DateTimeField(null=True, blank=True)
    canjeado_taller = models.ForeignKey(
        Taller, on_delete=models.SET_NULL, null=True, blank=True, related_name="canjes",
    )

    class Meta:
        ordering = ["-creado"]
        verbose_name = "código de cupón"
        verbose_name_plural = "códigos de cupón"
        constraints = [
            models.UniqueConstraint(
                fields=["cupon", "motociclista"], condition=Q(origen="obtenido"),
                name="un_codigo_obtenido_por_cupon",
            ),
        ]

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        if not self.codigo:
            while True:
                codigo = f"TY-{codigo_aleatorio(6)}"
                if not CodigoCupon.objects.filter(codigo=codigo).exists():
                    break
            self.codigo = codigo
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("cupones:mi_cupon", args=[self.codigo])

    @property
    def canjeado(self):
        return self.canjeado_en is not None

    def valido_en(self, taller):
        return self.cupon.taller_id in (None, taller.pk)
