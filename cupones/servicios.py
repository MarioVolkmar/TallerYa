"""Reglas de negocio de cupones, canjes y referidos."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone


from .models import CodigoCupon, Cupon, Motociclista


class CuponNoDisponible(Exception):
    pass


class ErrorCanje(Exception):
    pass


def es_domiciliario_verificado(motociclista):
    from domiciliarios.bandera import activo
    from domiciliarios.models import PerfilDomiciliario, verificacion_vigente
    if not activo() or not motociclista or not motociclista.pk:
        return False
    return verificacion_vigente(PerfilDomiciliario.objects.filter(motociclista=motociclista).first()) is not None


class RequiereVerificacion(Exception):
    """Cupón de TallerYa Ruta: solo para domiciliarios con la verificación vigente."""


class RequierePlus(CuponNoDisponible):
    pass


def normalizar_codigo(texto):
    limpio = "".join(c for c in texto.upper() if c.isalnum())
    if limpio.startswith("TY"):
        limpio = limpio[2:]
    return f"TY-{limpio}"


@transaction.atomic
def obtener_codigo_para(moto, cupon):
    """Variante para usuarios con sesión iniciada: ya sabemos quién es el motociclista."""
    return obtener_codigo(cupon, moto.nombre, moto.celular)


@transaction.atomic
def reclamar_regalo_mensual(moto):
    """Un código del cupón de regalo por mes calendario para suscriptores Plus."""
    if not moto.es_plus:
        raise RequierePlus("El regalo mensual es para suscriptores de TallerYa Plus.")
    regalo = Cupon.regalo_actual()
    if not regalo or not regalo.puede_emitirse():
        raise CuponNoDisponible("Este mes no hay regalo disponible. ¡Vuelve pronto!")
    hoy = timezone.localdate()
    ya = moto.codigos.filter(
        origen=CodigoCupon.Origen.REGALO, creado__year=hoy.year, creado__month=hoy.month,
    ).first()
    if ya:
        return ya, False
    return CodigoCupon.objects.create(cupon=regalo, motociclista=moto, origen=CodigoCupon.Origen.REGALO), True


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
    if cupon.solo_plus and not moto.es_plus:
        raise RequierePlus("Este cupón es exclusivo para suscriptores de TallerYa Plus.")
    if cupon.solo_domiciliarios and not es_domiciliario_verificado(moto):
        raise RequiereVerificacion("Este cupón es solo para domiciliarios verificados de TallerYa Ruta.")
    if not cupon.publico or cupon.regalo_mensual or not cupon.puede_emitirse():
        raise CuponNoDisponible("Este cupón ya no está disponible.")
    return CodigoCupon.objects.create(cupon=cupon, motociclista=moto), True


def buscar_codigo(codigo_texto):
    """El código para la vista previa del canje (sin canjearlo). Lanza ErrorCanje si no existe."""
    codigo = (CodigoCupon.objects.select_related("cupon", "cupon__taller", "motociclista", "canjeado_taller")
              .filter(codigo=normalizar_codigo(codigo_texto)).first())
    if not codigo:
        raise ErrorCanje(NO_VALIDO)
    return codigo


# --- Canje -----------------------------------------------------------------------------------------------------
# Con la sesión del taller abierta, el taller es esa cuenta. Sin sesión, el taller es el que la persona elige (o el que
# trae el enlace /canjear/?taller=...) y el PIN se compara SOLO con el de ese taller: nunca se busca un taller por su
# PIN. Mientras el PIN no esté comprobado, los errores no dicen si el código existe.
NO_VALIDO = "Ese código no es válido. Revisa que esté bien escrito."
CODIGO_O_PIN = "El código o el PIN no son correctos."
PIN_FALLOS_MAX, PIN_BLOQUEO = 5, 15 * 60   # por taller: 5 PIN errados bloquean el PIN de ese taller 15 min
IDEMPOTENCIA = timedelta(minutes=5)          # reenviar el mismo canje (doble clic, recargar) no da error


class PinBloqueado(ErrorCanje):
    pass


def _clave_pin(taller):
    return f"pin-canje:{taller.pk}"


def canjear(codigo_texto, pin=None, taller=None, *, taller_elegido=None, usuario=None, ip=None):
    """Canjea un código. `taller`: el de la sesión (sin PIN). Sin sesión: `taller_elegido` + `pin` de ese taller.
    Devuelve el CodigoCupon (con `.repetido=True` si ese mismo taller ya lo había canjeado hace un momento)."""
    from cuentas import limites
    via = "cuenta"
    if taller is None:
        via, taller = "pin", taller_elegido
        if taller is None:
            raise ErrorCanje("Elige tu taller y escribe su PIN (o entra con la cuenta del taller).")
        if limites.superado(_clave_pin(taller), PIN_FALLOS_MAX):
            raise PinBloqueado("Demasiados PIN errados para este taller. Espera 15 minutos o entra con la cuenta del taller.")
        if not taller.activo or not taller.pin_correcto(pin):
            limites.sumar(_clave_pin(taller), PIN_BLOQUEO)
            raise ErrorCanje(CODIGO_O_PIN)
    elif not taller.activo:
        raise ErrorCanje("Tu taller aún no está publicado: todavía no puede validar cupones.")

    with transaction.atomic():
        codigo = (CodigoCupon.objects.select_for_update()
                  .select_related("cupon", "cupon__taller", "motociclista", "motociclista__usuario")
                  .filter(codigo=normalizar_codigo(codigo_texto)).first())
        if not codigo:
            raise ErrorCanje(NO_VALIDO)
        if codigo.canjeado:
            if codigo.canjeado_taller_id == taller.pk and timezone.now() - codigo.canjeado_en < IDEMPOTENCIA:
                codigo.repetido = True
                return codigo
            fecha = timezone.localtime(codigo.canjeado_en).strftime("%d/%m/%Y %I:%M %p")
            raise ErrorCanje(f"Este cupón ya se usó el {fecha}.")
        if not codigo.cupon.vigente:
            raise ErrorCanje("Este cupón ya venció o fue desactivado.")
        if not codigo.valido_en(taller):
            raise ErrorCanje(f"Este cupón es de otro taller ({codigo.cupon.taller}).")
        # Actualización condicional: aunque dos talleres (o dos clics) lleguen a la vez, solo uno la gana
        ahora = timezone.now()
        por = usuario if (usuario and usuario.is_authenticated) else None
        ganado = CodigoCupon.objects.filter(pk=codigo.pk, canjeado_en__isnull=True).update(
            canjeado_en=ahora, canjeado_taller=taller, canje_via=via, canje_ip=ip, canjeado_por=por)
        if not ganado:
            raise ErrorCanje("Este cupón se acaba de usar.")
        codigo.canjeado_en, codigo.canjeado_taller, codigo.canje_via, codigo.canje_ip, codigo.canjeado_por = (
            ahora, taller, via, ip, por)
        # mismo valor otra vez, solo para que corran las señales (logros) que update() no dispara
        codigo.save(update_fields=["canjeado_en", "canjeado_taller", "canje_via", "canje_ip", "canjeado_por"])
        codigo.repetido = False
        otorgar_premio_referido(codigo.motociclista)
        transaction.on_commit(lambda: _avisar_canje(codigo))
    if via == "pin":
        limites.limpiar(_clave_pin(taller))
    return codigo


def _avisar_canje(codigo):
    """El dueño del cupón se entera de cada canje (si alguien usó su código sin él, lo ve de inmediato)."""
    from django.urls import reverse
    from notificaciones.servicios import notificar
    usuario = codigo.motociclista.usuario
    if usuario:
        cuando = timezone.localtime(codigo.canjeado_en).strftime("%d/%m %I:%M %p").lower()
        notificar(usuario, f"canje:{codigo.pk}", f"Usaste tu cupón en {codigo.canjeado_taller}",
                  f"{codigo.cupon.titulo} · {cuando}. ¿No fuiste tú? Escríbenos desde Mi cuenta.",
                  reverse("cuentas:mi_cuenta") + "#cupones")


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


@transaction.atomic
def emitir_por_logros(moto, cupon):
    """Código de un cupón canjeable con puntos de insignias. Máximo uno por cupón y mes.

    Los puntos los descuenta la app logros; aquí solo se valida el cupón y se crea el código.
    """
    cupon = Cupon.objects.select_for_update().get(pk=cupon.pk)
    if not cupon.puntos_logros:
        raise CuponNoDisponible("Este cupón no se canjea con puntos.")
    if not cupon.puede_emitirse():
        raise CuponNoDisponible("Este cupón ya no está disponible.")
    if cupon.solo_plus and not moto.es_plus:
        raise RequierePlus("Este cupón es exclusivo para suscriptores de TallerYa Plus.")
    if cupon.solo_domiciliarios and not es_domiciliario_verificado(moto):
        raise RequiereVerificacion("Este cupón es solo para domiciliarios verificados de TallerYa Ruta.")
    hoy = timezone.localdate()
    if moto.codigos.filter(cupon=cupon, origen=CodigoCupon.Origen.LOGROS,
                           creado__year=hoy.year, creado__month=hoy.month).exists():
        raise CuponNoDisponible("Ya canjeaste este cupón este mes. Vuelve el próximo.")
    return CodigoCupon.objects.create(cupon=cupon, motociclista=moto, origen=CodigoCupon.Origen.LOGROS)
