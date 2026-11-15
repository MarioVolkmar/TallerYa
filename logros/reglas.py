"""Reglas de las insignias y cálculo de puntos.

Antiabuso: nada cuenta por publicar en bruto. Cada regla exige una señal de otra persona
(votos, solución elegida, asistentes) o la confirmación de un taller (servicio verificado o cupón canjeado),
cada logro tiene una referencia única (no se cuenta dos veces) y cada insignia tiene un tope por mes.
Garaje y cupones solo se leen.
"""
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Length
from django.utils import timezone

from .models import Canje, Logro

VOTOS_PARA_APORTE = 2          # votos "me sirvió" de otras personas
ASISTENTES_MINIMOS = 3         # una rodada de uno o dos no cuenta
LARGO_MINIMO_RESENA = 40       # caracteres


@dataclass(frozen=True)
class Insignia:
    clave: str
    nombre: str
    emoji: str
    descripcion: str
    puntos: int
    tope_mes: int


INSIGNIAS = {i.clave: i for i in [
    # "Moto al día" (clave "mantenimiento") dejó de dar puntos: el dueño la marcaba a mano. Sus logros viejos se conservan.
    Insignia("servicio", "Servicio verificado", "🔧", "Un taller confirmó un servicio en tu hoja de vida o canjeó un cupón tuyo en su local.", 25, 2),
    Insignia("aporte", "Aporte útil", "💡", f"Respuesta en el foro con {VOTOS_PARA_APORTE}+ votos o elegida como solución.", 20, 3),
    Insignia("rodada", "Viajero", "🛵", f"Asistió a una rodada de otra persona con {ASISTENTES_MINIMOS}+ asistentes.", 15, 4),
    Insignia("resena", "Buena reseña", "⭐", f"Reseña de un taller de {LARGO_MINIMO_RESENA}+ caracteres (una por taller).", 10, 2),
]}


def _inicio_mes():
    return timezone.localtime().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _otorgar(usuario, clave, referencias):
    """Crea logros nuevos hasta el tope del mes. Devuelve cuántos."""
    insignia = INSIGNIAS[clave]
    ya = set(Logro.objects.filter(usuario=usuario, clave=clave).values_list("referencia", flat=True))
    cupo = insignia.tope_mes - Logro.objects.filter(usuario=usuario, clave=clave, creado__gte=_inicio_mes()).count()
    nuevos = 0
    for ref in map(str, referencias):
        if cupo <= 0:
            break
        if ref in ya:
            continue
        try:
            with transaction.atomic():
                Logro.objects.create(usuario=usuario, clave=clave, referencia=ref, puntos=insignia.puntos)
        except IntegrityError:
            continue
        cupo -= 1
        nuevos += 1
    return nuevos


def _refs_servicios(usuario):
    """Servicios confirmados por un taller: registro verificado en la hoja de vida (con el código de un solo uso
    del dueño) o un cupón canjeado en el local. No cuentan los cupones comprados con puntos (no se farmea)."""
    from cupones.models import CodigoCupon
    from garaje.models import RegistroServicio
    perfil = getattr(usuario, "motociclista", None)
    if not perfil:
        return []
    hechos = [(r.creado, f"rs-{r.pk}") for r in RegistroServicio.objects.filter(moto__motociclista=perfil, verificado=True)
              .only("pk", "creado")]
    hechos += [(c.canjeado_en, f"cc-{c.pk}") for c in CodigoCupon.objects.filter(motociclista=perfil, canjeado_en__isnull=False)
               .exclude(origen=CodigoCupon.Origen.LOGROS).only("pk", "canjeado_en")]
    return [ref for _, ref in sorted(hechos)]


def _refs_aportes(usuario):
    from foro.models import Respuesta
    return list(
        Respuesta.objects.filter(autor=usuario, visible=True, pregunta__visible=True)
        .exclude(pregunta__autor=usuario)
        .annotate(n=Count("votos", distinct=True))
        .filter(Q(n__gte=VOTOS_PARA_APORTE) | Q(pregunta__mejor_respuesta=F("pk")))
        .order_by("creado").values_list("pk", flat=True)
    )


def _refs_rodadas(usuario):
    from foro.models import Asistencia, Rodada
    mias = Asistencia.objects.filter(usuario=usuario).values("rodada_id")  # subconsulta: así el conteo ve a todos
    return list(
        Rodada.objects.filter(pk__in=mias, fecha_hora__lt=timezone.now(), pregunta__visible=True)
        .exclude(organizador=usuario)
        .annotate(n=Count("asistencias", distinct=True)).filter(n__gte=ASISTENTES_MINIMOS)
        .order_by("fecha_hora").values_list("pk", flat=True)
    )


def _refs_resenas(usuario):
    from talleres.models import Resena
    talleres = (Resena.objects.filter(usuario=usuario, visible=True)
                .annotate(largo=Length("comentario")).filter(largo__gte=LARGO_MINIMO_RESENA)
                .order_by("creado").values_list("taller_id", flat=True))
    return list(dict.fromkeys(talleres))  # una por taller


REGLAS = {"servicio": _refs_servicios, "aporte": _refs_aportes, "rodada": _refs_rodadas, "resena": _refs_resenas}


def evaluar(usuario, claves=None):
    """Revisa las reglas (todas o solo `claves`) y otorga lo que falte. Es idempotente: la referencia
    única de cada logro impide sumar dos veces. Devuelve el número de logros nuevos."""
    if not getattr(usuario, "is_authenticated", False):
        return 0
    return sum(_otorgar(usuario, clave, REGLAS[clave](usuario)) for clave in (claves or REGLAS))


def puntos_disponibles(usuario):
    ganados = Logro.objects.filter(usuario=usuario).aggregate(s=Sum("puntos"))["s"] or 0
    gastados = Canje.objects.filter(usuario=usuario).aggregate(s=Sum("puntos"))["s"] or 0
    return ganados - gastados


def resumen(usuario):
    """Insignias del usuario con cuántas veces las ganó (para Mi cuenta y el perfil público)."""
    veces = dict(Logro.objects.filter(usuario=usuario).values("clave").annotate(n=Count("id")).values_list("clave", "n"))
    return [{"insignia": i, "veces": veces[c]} for c, i in INSIGNIAS.items() if veces.get(c)]


class PuntosInsuficientes(Exception):
    pass


@transaction.atomic
def canjear(usuario, cupon):
    """Cambia puntos por un código del cupón (lo emite cupones.servicios). Lanza PuntosInsuficientes o CuponNoDisponible."""
    from django.contrib.auth import get_user_model
    from cupones.servicios import CuponNoDisponible, emitir_por_logros
    get_user_model().objects.select_for_update().get(pk=usuario.pk)  # un canje a la vez por usuario
    perfil = getattr(usuario, "motociclista", None)
    if not perfil:
        raise CuponNoDisponible("Completa tu perfil de motociclista (celular) para recibir cupones.")
    if not cupon.puntos_logros:
        raise CuponNoDisponible("Este cupón no se canjea con puntos.")
    if puntos_disponibles(usuario) < cupon.puntos_logros:
        raise PuntosInsuficientes("Te faltan puntos para este cupón.")
    codigo = emitir_por_logros(perfil, cupon)
    Canje.objects.create(usuario=usuario, codigo=codigo, puntos=cupon.puntos_logros)
    return codigo
