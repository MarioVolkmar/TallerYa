"""«Domiciliario verificado»: revisar, aprobar o rechazar, y la vigencia de 6 meses con renovación por uso real.

Lo gratis (plan intensivo, cierre de jornada, Mi ruta) no pide verificación. La insignia y lo de Plus (descuentos de
los talleres aliados, comprobante, cupones exclusivos) sí.

Privacidad (Ley 1581): las fotos solo se guardan mientras se revisan (en PRIVADO_ROOT, nombre aleatorio, solo las ve el
dueño o el staff). Al aprobar o rechazar se borran: queda el resultado, la fecha y quién revisó.

Dos fotos: pantallazo del perfil de repartidor (con la placa o los datos de la moto) y foto de la moto con la placa.
Pendiente, anotado en informes_noche/ruta-integracion.md: confirmación en un taller aliado con PIN y código de flota.
"""
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import Jornada, Verificacion, verificacion_vigente


def vigencia_dias():
    return getattr(settings, "RUTA_VERIFICACION_DIAS", 182)


def _avisar(perfil, clave, titulo, texto):
    from notificaciones.models import Notificacion
    from notificaciones.servicios import notificar
    notificar(perfil.motociclista.usuario, clave, titulo, texto, reverse("domiciliarios:verificacion"),
              Notificacion.Tipo.PLUS)


def es_verificado(perfil, hoy=None):
    return verificacion_vigente(perfil, hoy) is not None


def pendiente(perfil):
    return perfil.verificaciones.filter(estado=Verificacion.Estado.PENDIENTE).first() if perfil and perfil.pk else None


@transaction.atomic
def aprobar(verificacion, revisor, ahora=None):
    """Aprueba y borra las fotos."""
    ahora = ahora or timezone.now()
    v = verificacion
    v.borrar_fotos()
    v.estado = Verificacion.Estado.APROBADA
    v.motivo = ""
    v.revisado_por = revisor
    v.revisado_en = ahora
    v.vence = timezone.localdate(ahora) + timedelta(days=vigencia_dias())
    v.save()
    _avisar(v.perfil, f"ruta-verif:{v.pk}:aprobada", "¡Ya eres domiciliario verificado!",
            f"Tu insignia y los beneficios Plus de TallerYa Ruta valen hasta el {v.vence:%d/%m/%Y}. Tus fotos ya se borraron.")
    return v


@transaction.atomic
def rechazar(verificacion, revisor, motivo, ahora=None):
    v = verificacion
    v.borrar_fotos()
    v.estado = Verificacion.Estado.RECHAZADA
    v.motivo = motivo[:200]
    v.revisado_por = revisor
    v.revisado_en = ahora or timezone.now()
    v.save()
    _avisar(v.perfil, f"ruta-verif:{v.pk}:rechazada", "No pudimos verificarte como domiciliario",
            f"Motivo: {v.motivo}. Tus fotos ya se borraron; puedes enviar otras.")
    return v


def km_por_jornada(perfil, desde, hasta):
    """[(fecha, km)] de las jornadas cerradas entre desde y hasta: km del tablero al cerrar menos los del cierre anterior
    (de hasta 3 días antes; un hueco mayor no se cuenta, no se sabe qué días rodó)."""
    jornadas = list(Jornada.objects.filter(perfil=perfil, fecha__gte=desde - timedelta(days=3), fecha__lte=hasta,
                                           km_fin__isnull=False).order_by("fecha").values_list("fecha", "km_fin"))
    filas = []
    for (f0, k0), (f1, k1) in zip(jornadas, jornadas[1:]):
        if f1 >= desde and (f1 - f0).days <= 3 and k1 >= k0:
            filas.append((f1, k1 - k0))
    return filas


def renovable(perfil, hoy=None):
    """Uso alto y constante: al menos RUTA_RENOVAR_DIAS jornadas con km en los últimos RUTA_RENOVAR_VENTANA días y una
    media de RUTA_RENOVAR_KM_DIA o más."""
    hoy = hoy or timezone.localdate()
    ventana = getattr(settings, "RUTA_RENOVAR_VENTANA", 30)
    filas = km_por_jornada(perfil, hoy - timedelta(days=ventana - 1), hoy)
    if len(filas) < getattr(settings, "RUTA_RENOVAR_DIAS", 14):
        return False
    return sum(km for _f, km in filas) / len(filas) >= getattr(settings, "RUTA_RENOVAR_KM_DIA", 80)


def revisar_vencimientos(hoy=None):
    """Lo corre el comando diario. Devuelve (renovadas, vencidas)."""
    hoy = hoy or timezone.localdate()
    renovadas = vencidas = 0
    for v in (Verificacion.objects.filter(estado=Verificacion.Estado.APROBADA, vence__lt=hoy)
              .select_related("perfil__motociclista__usuario")):
        if renovable(v.perfil, hoy):
            v.vence = hoy + timedelta(days=vigencia_dias())
            v.renovaciones += 1
            v.save(update_fields=["vence", "renovaciones"])
            renovadas += 1
            _avisar(v.perfil, f"ruta-verif:{v.pk}:renovada:{v.renovaciones}", "Tu verificación se renovó sola",
                    f"Tus jornadas muestran que sigues en ruta. Vale hasta el {v.vence:%d/%m/%Y}.")
        else:
            v.estado = Verificacion.Estado.VENCIDA
            v.save(update_fields=["estado"])
            vencidas += 1
            _avisar(v.perfil, f"ruta-verif:{v.pk}:vencida", "Tu verificación de domiciliario venció",
                    "Pasaron 6 meses sin jornadas suficientes para renovarla sola. Vuelve a subir la captura de tu perfil.")
    return renovadas, vencidas
