from django.conf import settings
from django.db import models

from . import reloj


class Bitacora(models.Model):
    """Una acción de administrador que salió bien. La escribe solo `consola.acciones`, nunca una vista a mano."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="+")
    actor_nombre = models.CharField("quién", max_length=200, help_text="Se guarda aparte por si borran la cuenta")
    accion = models.CharField(max_length=60, db_index=True, help_text="Clave de la regla, ej. usuarios.cambiar_rol")
    frase = models.CharField(max_length=300)
    objeto_tipo = models.CharField(max_length=60, db_index=True)
    objeto_id = models.PositiveIntegerField(null=True, db_index=True)
    objeto_repr = models.CharField(max_length=200, blank=True)
    cambios = models.JSONField(default=list, blank=True,
                               help_text='Lista de {"campo", "etiqueta", "antes", "despues"}')
    ip = models.GenericIPAddressField(null=True, blank=True)
    creado = models.DateTimeField(default=reloj.ahora, db_index=True)

    class Meta:
        ordering = ["-creado", "-pk"]
        verbose_name = "registro de la bitácora"
        verbose_name_plural = "bitácora"

    def __str__(self):
        return f"{self.creado:%Y-%m-%d %H:%M} · {self.actor_nombre}: {self.frase}"


class Ajuste(models.Model):
    """Un interruptor de la consola. Sin fila vale el valor inicial de código (ver consola/ajustes.py)."""

    clave = models.CharField(max_length=60, unique=True)
    valor = models.JSONField(default=bool)

    class Meta:
        verbose_name = "ajuste"
        verbose_name_plural = "ajustes"

    def __str__(self):
        from .ajustes import POR_CLAVE
        modulo = POR_CLAVE.get(self.clave)
        return modulo.etiqueta if modulo else self.clave

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .ajustes import invalidar
        invalidar()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        from .ajustes import invalidar
        invalidar()
