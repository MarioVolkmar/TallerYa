"""Verificación de identidad del mecánico: enviar las fotos de la cédula, aprobar o rechazar.

La insignia «Verificado» solo se otorga aquí (aprobar). Las fotos viven en PRIVADO_ROOT y se borran al decidir."""
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import IdentidadMecanico, MecanicoDomicilio

E = IdentidadMecanico.Estado


def estado_para_panel(mecanico):
    """'pendiente' (sin enviar), 'enviada', 'aprobada', 'aprobada_heredada' o 'rechazada'."""
    ident = getattr(mecanico, "identidad", None) if mecanico.pk else None
    if ident is None:
        return "pendiente"
    if ident.estado == E.APROBADA and ident.heredada:
        return "aprobada_heredada"
    return ident.estado


def _avisar(mecanico, sufijo, titulo, texto):
    if not mecanico.usuario_id:
        return
    from notificaciones.models import Notificacion
    from notificaciones.servicios import notificar
    notificar(mecanico.usuario, f"mecanico-identidad:{mecanico.pk}:{sufijo}", titulo, texto,
              reverse("domicilio:identidad"), Notificacion.Tipo.GENERAL)


@transaction.atomic
def enviar(mecanico, frente, respaldo, selfie=None, ahora=None):
    """Guarda las fotos ya validadas y deja la solicitud «en revisión». Reemplaza las anteriores."""
    ahora = ahora or timezone.now()
    ident, _ = IdentidadMecanico.objects.get_or_create(mecanico=mecanico)
    ident.borrar_fotos()
    ident.frente, ident.respaldo = frente, respaldo
    if selfie:
        ident.selfie = selfie
    ident.estado = E.ENVIADA
    ident.motivo = ""
    ident.autorizacion = ident.enviado = ahora
    ident.save()
    from notificaciones.servicios import avisar_admins
    avisar_admins(f"identidad-mecanico:{mecanico.pk}:{ahora:%Y%m%d%H%M%S}", "Identidad de mecánico por revisar", mecanico.nombre)
    return ident


@transaction.atomic
def aprobar(ident, revisor, ahora=None):
    ahora = ahora or timezone.now()
    ident.borrar_fotos()
    ident.estado, ident.motivo, ident.heredada = E.APROBADA, "", False
    ident.revisado_por, ident.revisado_en = revisor, ahora
    ident.save()
    m = ident.mecanico
    if not m.verificado:
        m.verificado = True
        m.save(update_fields=["verificado", "actualizado"])
    _avisar(m, f"aprobada:{ahora:%Y%m%d%H%M%S}", "¡Identidad verificada!",
            "Tu perfil ya lleva la insignia «Verificado». Tus fotos de la cédula ya se borraron.")
    return ident


@transaction.atomic
def rechazar(ident, revisor, motivo, ahora=None):
    ahora = ahora or timezone.now()
    ident.borrar_fotos()
    ident.estado, ident.motivo, ident.heredada = E.RECHAZADA, motivo[:200], False
    ident.revisado_por, ident.revisado_en = revisor, ahora
    ident.save()
    m = ident.mecanico
    if m.verificado:  # sin identidad aprobada no hay insignia
        m.verificado = False
        m.save(update_fields=["verificado", "actualizado"])
    _avisar(m, f"rechazada:{ahora:%Y%m%d%H%M%S}", "No pudimos verificar tu identidad",
            f"Motivo: {ident.motivo}. Tus fotos ya se borraron; puedes enviar otras.")
    return ident


def puede_tener_insignia(mecanico):
    ident = getattr(mecanico, "identidad", None) if mecanico.pk else None
    return bool(ident and ident.estado == E.APROBADA)
