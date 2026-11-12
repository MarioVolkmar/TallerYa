"""Reglas de negocio de cupones, canjes y referidos."""
from django.db import transaction
from django.utils import timezone

from talleres.models import Taller

from .models import CodigoCupon, Cupon, Motociclista


class CuponNoDisponible(Exception):
    pass


class ErrorCanje(Exception):
    pass


def normalizar_codigo(texto):
    limpio = "".join(c for c in texto.upper() if c.isalnum())
    if limpio.startswith("TY"):
        limpio = limpio[2:]
    return f"TY-{limpio}"


@transaction.atomic
def obtener_codigo(cupon, nombre, celular, ref=None):
    """Entrega el código del motociclista para ese cupón (el mismo si ya lo tenía).

    Un referido solo cuenta si el motociclista es nuevo, para que nadie
    se "adueñe" de usuarios que ya existían.
    """
    cupon = Cupon.objects.select_for_update().get(pk=cupon.pk)
    moto, nuevo = Motociclista.objects.get_or_create(celular=celular, defaults={"nombre": nombre})
    if nuevo and ref:
        referidor = Motociclista.objects.filter(codigo_referido=ref).exclude(pk=moto.pk).first()
        if referidor:
            moto.referido_por = referidor
            moto.save(update_fields=["referido_por"])

    existente = moto.codigos.filter(cupon=cupon, origen=CodigoCupon.Origen.OBTENIDO).first()
    if existente:
        return existente, False
    if not cupon.publico or not cupon.puede_emitirse():
        raise CuponNoDisponible("Este cupón ya no está disponible.")
    return CodigoCupon.objects.create(cupon=cupon, motociclista=moto), True


@transaction.atomic
def canjear(codigo_texto, pin):
    taller = Taller.objects.filter(pin_canje=pin.strip(), activo=True).first()
    if not taller:
        raise ErrorCanje("PIN incorrecto.")

    codigo = (
        CodigoCupon.objects.select_for_update()
        .select_related("cupon", "cupon__taller", "motociclista")
        .filter(codigo=normalizar_codigo(codigo_texto))
        .first()
    )
    if not codigo:
        raise ErrorCanje("Ese código no existe. Revisa que esté bien escrito.")
    if codigo.canjeado:
        fecha = timezone.localtime(codigo.canjeado_en).strftime("%d/%m/%Y %I:%M %p")
        raise ErrorCanje(f"Este código ya fue canjeado el {fecha}.")
    if not codigo.cupon.vigente:
        raise ErrorCanje("Este cupón ya venció o fue desactivado.")
    if not codigo.valido_en(taller):
        raise ErrorCanje(f"Este cupón es de otro taller ({codigo.cupon.taller}).")

    codigo.canjeado_en = timezone.now()
    codigo.canjeado_taller = taller
    codigo.save(update_fields=["canjeado_en", "canjeado_taller"])
    otorgar_premio_referido(codigo.motociclista)
    return codigo


def otorgar_premio_referido(moto):
    """Si quien canjeó llegó invitado, quien lo invitó recibe el cupón de premio (una sola vez)."""
    moto = Motociclista.objects.select_for_update().get(pk=moto.pk)
    if moto.premio_otorgado or not moto.referido_por_id:
        return None
    premio = Cupon.premio_actual()
    if not premio or not premio.puede_emitirse():
        return None
    codigo = CodigoCupon.objects.create(
        cupon=premio, motociclista=moto.referido_por,
        origen=CodigoCupon.Origen.PREMIO, referido=moto,
    )
    moto.premio_otorgado = True
    moto.save(update_fields=["premio_otorgado"])
    return codigo
