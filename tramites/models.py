"""SOAT y revisión técnico-mecánica: tarifas oficiales (cargadas desde el admin, con su fuente) y CDA aliados.

Ningún precio está escrito en el código: si el equipo no ha cargado la tarifa del año, la página lo dice.
"""
from django.db import models

from talleres.models import CIUDADES


class TarifaSoat(models.Model):
    """Tarifa del SOAT para motos de un año. Las fija el Gobierno cada año; se copian de la fuente oficial."""
    class Categoria(models.TextChoices):
        MENOS_100 = "moto_100", "Motos de menos de 100 cc"
        DE_100_A_200 = "moto_100_200", "Motos de 100 a 200 cc"
        MAS_200 = "moto_200", "Motos de más de 200 cc"

    anio = models.PositiveSmallIntegerField("año")
    categoria = models.CharField(max_length=16, choices=Categoria.choices)
    valor = models.PositiveIntegerField("valor total a pagar (COP)")
    fuente = models.URLField(help_text="De dónde sale el valor (Fasecolda, Superfinanciera, aseguradora)")
    nota = models.CharField(max_length=200, blank=True, help_text="Ej.: incluye el descuento para motos de bajo cilindraje")

    class Meta:
        ordering = ["-anio", "categoria"]
        constraints = [models.UniqueConstraint(fields=["anio", "categoria"], name="tarifa_soat_unica")]
        verbose_name = "tarifa de SOAT"
        verbose_name_plural = "tarifas de SOAT"

    def __str__(self):
        return f"{self.anio} · {self.get_categoria_display()}"

    @classmethod
    def categoria_para(cls, cilindraje):
        if not cilindraje:
            return None
        if cilindraje < 100:
            return cls.Categoria.MENOS_100
        return cls.Categoria.DE_100_A_200 if cilindraje <= 200 else cls.Categoria.MAS_200


def _ruta_pedido(instancia, nombre):
    # Nombre aleatorio: no revela la placa ni el nombre original del archivo.
    from pathlib import Path
    from uuid import uuid4
    return f"soat/{uuid4().hex}{Path(nombre).suffix.lower()}"


def _almacen():
    from garaje.models import almacen_privado
    return almacen_privado()


class PedidoSoat(models.Model):
    """Pedido de SOAT dentro de TallerYa. Mientras no haya aseguradora aliada, el equipo lo gestiona a mano
    (enlace de pago y PDF de la póliza) y el pago es simulado (ver tramites/pagos.py)."""
    class Estado(models.TextChoices):
        RECIBIDO = "recibido", "Recibido"
        EN_PROCESO = "en_proceso", "En proceso"
        LISTA_PAGAR = "lista_pagar", "Lista para pagar"
        PAGADA = "pagada", "Pagada"
        EMITIDA = "emitida", "Emitida"
        CANCELADA = "cancelada", "Cancelada"

    class TipoDocumento(models.TextChoices):
        CC = "CC", "Cédula de ciudadanía"
        CE = "CE", "Cédula de extranjería"
        PPT = "PPT", "Permiso por protección temporal"
        PA = "PA", "Pasaporte"
        NIT = "NIT", "NIT"

    ACTIVOS = (Estado.RECIBIDO, Estado.EN_PROCESO, Estado.LISTA_PAGAR, Estado.PAGADA)
    PASOS = (Estado.RECIBIDO, Estado.EN_PROCESO, Estado.LISTA_PAGAR, Estado.PAGADA, Estado.EMITIDA)

    moto = models.ForeignKey("garaje.Moto", on_delete=models.CASCADE, related_name="pedidos_soat")
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.RECIBIDO)
    # Datos de la moto al momento del pedido (para la póliza, aunque luego cambie el garaje)
    placa = models.CharField(max_length=8)
    linea = models.CharField("línea", max_length=120)
    cilindraje = models.PositiveSmallIntegerField()
    categoria = models.CharField(max_length=16, choices=TarifaSoat.Categoria.choices)
    valor = models.PositiveIntegerField("valor (tarifa de ley)", null=True, blank=True)
    # Tomador / propietario
    tipo_documento = models.CharField(max_length=4, choices=TipoDocumento.choices, default=TipoDocumento.CC)
    numero_documento = models.CharField("número de documento", max_length=20)
    nombre_completo = models.CharField(max_length=120)
    chasis_motor = models.CharField("número de chasis (VIN) o de motor", max_length=40, blank=True)
    tarjeta_propiedad = models.FileField("foto de la tarjeta de propiedad", storage=_almacen, upload_to=_ruta_pedido,
                                         blank=True)
    correo = models.EmailField()
    direccion = models.CharField("dirección", max_length=160)
    celular = models.CharField(max_length=10)
    acepta_datos_en = models.DateTimeField("autorizó el tratamiento de datos (Ley 1581)")
    # Lo que llena el equipo
    enlace_pago = models.URLField("enlace de pago", blank=True, help_text="Lo da la aseguradora o agencia aliada")
    poliza = models.FileField("PDF de la póliza", storage=_almacen, upload_to=_ruta_pedido, blank=True)
    numero_poliza = models.CharField("número de póliza", max_length=40, blank=True)
    inicio_vigencia = models.DateField("inicio de vigencia", null=True, blank=True)
    notas_internas = models.TextField(blank=True, help_text="Solo para el equipo de TallerYa")
    pago_simulado = models.BooleanField(default=False, editable=False)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    pagado_en = models.DateTimeField(null=True, blank=True)
    emitido_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "pedido de SOAT"
        verbose_name_plural = "pedidos de SOAT"

    def __str__(self):
        return f"SOAT {self.placa} · {self.get_estado_display()}"

    @property
    def activo(self):
        return self.estado in self.ACTIVOS

    def pasos(self):
        """Para la línea de estado: (etiqueta, hecho, actual)."""
        if self.estado == self.Estado.CANCELADA:
            return []
        i = self.PASOS.index(self.estado)
        return [(e.label, k < i, k == i) for k, e in enumerate(self.PASOS)]

    def cambiar_estado(self, nuevo):
        """Cambia el estado y hace lo que trae: fechas, avisos y la nueva fecha de vencimiento del SOAT."""
        from django.utils import timezone
        anterior, self.estado = self.estado, nuevo
        ahora = timezone.now()
        if nuevo == self.Estado.PAGADA and not self.pagado_en:
            self.pagado_en = ahora
        if nuevo == self.Estado.EMITIDA:
            self.emitido_en = self.emitido_en or ahora
            self.inicio_vigencia = self.inicio_vigencia or timezone.localdate()
        self.save()
        if anterior != nuevo:
            self._al_cambiar(nuevo)

    def _al_cambiar(self, nuevo):
        from django.urls import reverse
        from garaje.models import sumar_anios
        from notificaciones.models import Notificacion
        from notificaciones.servicios import notificar
        usuario = self.moto.motociclista.usuario
        url = f"{reverse('tramites:soat')}?moto={self.moto_id}"
        if nuevo == self.Estado.LISTA_PAGAR:
            notificar(usuario, f"pedido-soat:{self.pk}:lista", "Tu SOAT está listo para pagar",
                      f"{self.linea} · {self.placa}", url, Notificacion.Tipo.DOCUMENTO)
        elif nuevo == self.Estado.EMITIDA:
            notificar(usuario, f"pedido-soat:{self.pk}:emitida", "Tu SOAT quedó emitido",
                      f"{self.linea} · {self.placa}. Descarga tu póliza.", url, Notificacion.Tipo.DOCUMENTO)
            # La póliza dura un año: así funcionan los avisos de vencimiento del garaje
            self.moto.soat_vence = sumar_anios(self.inicio_vigencia, 1)
            self.moto.save(update_fields=["soat_vence"])
