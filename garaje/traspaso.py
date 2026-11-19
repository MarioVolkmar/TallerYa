"""Traspaso de la moto al venderla: la moto pasa al garaje de quien la compra con su hoja de vida completa.

Qué viaja (es de la moto): los servicios de la hoja de vida (verificados y propios, con taller, fecha, km y notas),
los mantenimientos del plan, las lecturas de kilometraje, los servicios del panel de talleres (con su foto), la placa,
la matrícula y el aspecto del 3D.

Qué no viaja (es del dueño): los gastos, lo que pagó por cada servicio, las fotos o PDF del SOAT y la técnico-mecánica
(llevan su nombre y cédula) y sus fechas de vencimiento, el apodo, sus ajustes del plan (posponer, recordar), el recordatorio de pico y placa por
WhatsApp y sus pedidos de SOAT (quedan para el equipo, pero el nuevo dueño no los ve: ver Moto.dueno_desde).
También se cortan los enlaces públicos y los códigos de taller vigentes.
"""
from datetime import timedelta

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from notificaciones.models import Notificacion
from notificaciones.servicios import notificar

from .models import AjusteTarea, Moto, ServicioTaller, TraspasoMoto

DIAS_TRASPASO = 7


class TraspasoInvalido(Exception):
    """El enlace no existe, venció, ya se usó o no se puede aceptar."""


def vigente(moto):
    return moto.traspasos.filter(usado__isnull=True, cancelado__isnull=True,
                                 vence__gt=timezone.now()).order_by("-creado").first()


def bloqueo(moto):
    """Motivo por el que aún no se puede traspasar (texto) o None."""
    from tramites.models import PedidoSoat
    if moto.pedidos_soat.filter(estado__in=PedidoSoat.ACTIVOS).exists():
        return "Tienes un pedido de SOAT en curso para esta moto. Espera a que termine o cancélalo antes de venderla."
    return None


def crear(moto, vendedor):
    """Enlace nuevo de un solo uso (anula el anterior sin usar)."""
    ahora = timezone.now()
    moto.traspasos.filter(usado__isnull=True, cancelado__isnull=True).update(cancelado=ahora)
    return TraspasoMoto.objects.create(moto=moto, vendedor=vendedor, vence=ahora + timedelta(days=DIAS_TRASPASO))


def cancelar(moto):
    return moto.traspasos.filter(usado__isnull=True, cancelado__isnull=True).update(cancelado=timezone.now())


def buscar(token):
    """TraspasoMoto vigente para ese token, o None."""
    return (TraspasoMoto.objects.select_related("moto", "moto__linea", "moto__linea__marca",
                                                "moto__motociclista__usuario")
            .filter(token=token, usado__isnull=True, cancelado__isnull=True, vence__gt=timezone.now()).first())


def aceptar(token, comprador, max_motos):
    """Pasa la moto al garaje del comprador. Lanza TraspasoInvalido si no se puede."""
    perfil = getattr(comprador, "motociclista", None)
    with transaction.atomic():
        traspaso = TraspasoMoto.objects.select_for_update().filter(pk=getattr(buscar(token), "pk", None)).first()
        if not traspaso or not traspaso.vigente:
            raise TraspasoInvalido("Este enlace ya no sirve: venció, se usó o el vendedor lo canceló.")
        moto = Moto.objects.select_for_update().get(pk=traspaso.moto_id)
        vendedor = moto.motociclista.usuario
        if not perfil:
            raise TraspasoInvalido("Tu cuenta necesita un celular de motociclista para tener garaje.")
        if moto.motociclista_id == perfil.pk:
            raise TraspasoInvalido("Esta moto ya está en tu garaje.")
        if perfil.motos.count() >= max_motos:
            raise TraspasoInvalido(f"Tu garaje ya tiene {max_motos} motos. Elimina una para recibir esta.")
        if bloqueo(moto):
            raise TraspasoInvalido("El vendedor tiene un trámite de SOAT en curso con esta moto. Pídele que lo cierre.")
        # Actualización condicional: solo un envío gasta el enlace aunque lleguen dos a la vez
        ahora = timezone.now()
        if not TraspasoMoto.objects.filter(pk=traspaso.pk, usado__isnull=True).update(usado=ahora, comprador=comprador):
            raise TraspasoInvalido("Este enlace ya se usó.")
        _limpiar_lo_personal(moto, ahora)
        moto.motociclista = perfil
        moto.dueno_desde = ahora
        moto.save()
    _avisar(moto, vendedor, comprador, traspaso)
    return moto


def _limpiar_lo_personal(moto, ahora):
    for campo in ("soat_archivo", "tecno_archivo"):
        archivo = getattr(moto, campo)
        if archivo:
            archivo.delete(save=False)  # deja el campo vacío; se guarda con la moto
    # SOAT y técnico-mecánica son datos privados del dueño: no viajan ni las fechas (el comprador carga los suyos)
    moto.soat_vence = moto.tecno_vence = None
    moto.apodo = ""
    moto.pico_placa_whatsapp = False
    moto.pico_placa_enviado = None
    moto.gastos.all().delete()
    moto.hoja_vida.update(costo=None)
    ServicioTaller.objects.filter(moto=moto).update(costo=None)
    AjusteTarea.objects.filter(moto=moto).delete()
    moto.enlaces_hoja_vida.filter(revocado__isnull=True).update(revocado=ahora)
    moto.codigos_servicio.filter(usado__isnull=True, vence__gt=ahora).update(vence=ahora)
    moto.traspasos.filter(usado__isnull=True, cancelado__isnull=True).update(cancelado=ahora)
    # Perfil y verificaciones de domiciliario del vendedor dejan de apuntar a esta moto
    try:
        from domiciliarios.models import PerfilDomiciliario, Verificacion
    except ImportError:
        return
    PerfilDomiciliario.objects.filter(moto=moto).update(moto=None)
    Verificacion.objects.filter(moto=moto).update(moto=None)


def _avisar(moto, vendedor, comprador, traspaso):
    nombre = moto.nombre_completo
    notificar(comprador, f"traspaso-recibido:{traspaso.pk}", f"Tu {nombre} ya está en tu garaje",
              "Llegó con su hoja de vida completa. Revisa el plan de mantenimiento y sube tu SOAT.",
              url=reverse("garaje:hoja_vida", args=[moto.pk]), tipo=Notificacion.Tipo.GENERAL)
    notificar(vendedor, f"traspaso-entregado:{traspaso.pk}", f"Traspasaste tu {nombre}",
              "La moto y su hoja de vida ya están en la cuenta de quien la compró.",
              url=reverse("garaje:garaje"), tipo=Notificacion.Tipo.GENERAL)
