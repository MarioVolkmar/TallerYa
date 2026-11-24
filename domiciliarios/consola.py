"""Acciones de /consola/ para verificar domiciliarios (se usan desde la ficha del usuario en Usuarios).

Mismo mecanismo que Usuarios, Bitácora y Mecánicos (consola.acciones): solo administradores, POST y bitácora.
Se registra desde DomiciliariosConfig.ready(); el contador de pendientes es el badge de Usuarios.
Las fotos se ven por domiciliarios:verificacion_foto (staff o dueño) y se borran al decidir.
"""
from consola.acciones import ErrorAccion, accion

from . import verificacion as verif
from .models import Verificacion

ESTADOS = dict(Verificacion.Estado.choices)
CAMPOS = {"estado": ("Estado", lambda o: o.get_estado_display()),
          "vence": ("Vence", lambda o: o.vence), "motivo": ("Motivo", lambda o: o.motivo)}


def _solo_pendiente(obj):
    if obj.estado != Verificacion.Estado.PENDIENTE:
        raise ErrorAccion("Esa solicitud ya se revisó.")


@accion("ruta.aprobar", modelo=Verificacion, nombre="Aprobar domiciliario", campos=CAMPOS,
        frase="Aprobó la verificación de domiciliario #{obj.pk}", exito="Listo: verificado. Fotos borradas y usuario avisado.")
def _aprobar(request, obj):
    _solo_pendiente(obj)
    verif.aprobar(obj, request.user)
    return {}


@accion("ruta.rechazar", modelo=Verificacion, nombre="Rechazar domiciliario", campos=CAMPOS,
        frase="Rechazó la verificación de domiciliario #{obj.pk}", exito="Listo: rechazada. Fotos borradas y usuario avisado.")
def _rechazar(request, obj):
    _solo_pendiente(obj)
    motivo = (request.POST.get("motivo") or request.POST.get("valor", "")).strip()
    if len(motivo) < 4:
        raise ErrorAccion("Escribe el motivo del rechazo (se le muestra al usuario).")
    verif.rechazar(obj, request.user, motivo)
    return {}


def pendientes():
    from .bandera import activo
    return Verificacion.objects.filter(estado=Verificacion.Estado.PENDIENTE).count() if activo() else 0
