"""Etiquetas de TallerYa Ruta. Con la bandera DOMICILIARIOS_ACTIVO apagada ninguna pinta nada.

{% ruta_moto moto plan %}      página de la moto, junto a la agenda: franja de la moto de trabajo o el interruptor
{% ruta_portada %}             bloque breve «¿Trabajas en tu moto?» de la portada
{% ruta_menu as es_dm %}       True si el usuario tiene TallerYa Ruta (para «Mi ruta» en el menú)
"""
from datetime import timedelta

from django import template
from django.utils import timezone

from ..bandera import activo

register = template.Library()


def _motociclista(context):
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return None
    return getattr(request.user, "motociclista", None)


def _perfil(context):
    """PerfilDomiciliario del usuario (una consulta por petición)."""
    request = context.get("request")
    if request is None:
        return None
    if not hasattr(request, "_perfil_dm"):
        motociclista = _motociclista(context)
        from ..models import PerfilDomiciliario
        request._perfil_dm = (PerfilDomiciliario.objects.filter(motociclista=motociclista).first()
                              if motociclista else None)
    return request._perfil_dm


@register.simple_tag(takes_context=True)
def ruta_menu(context):
    return activo() and _perfil(context) is not None


@register.inclusion_tag("domiciliarios/_portada.html", takes_context=True)
def ruta_portada(context):
    if not activo():
        return {"mostrar": False}
    return {"mostrar": True, "es_domiciliario": _perfil(context) is not None, "request": context.get("request")}


@register.inclusion_tag("domiciliarios/_ruta_moto.html", takes_context=True)
def ruta_moto(context, moto, plan):
    if not activo():
        return {"mostrar": False}
    datos = {"mostrar": True, "moto": moto, "request": context.get("request"),
             "csrf_token": context.get("csrf_token"), "de_trabajo": bool(getattr(plan, "de_trabajo", False))}
    if not datos["de_trabajo"]:
        return datos
    from garaje import pico_placa
    from ..models import verificacion_vigente
    hoy = timezone.localdate()
    perfil = _perfil(context)
    datos.update({
        "pyp": pico_placa.resumen(moto, hoy),
        "manana_pyp": pico_placa.tiene_pico_placa(moto, hoy + timedelta(days=1))[0] if moto.placa else False,
        "km_dia": round(plan.km_por_dia) if plan.km_por_dia else None,
        "verificado": (vigente := verificacion_vigente(perfil, hoy) if perfil else None),
        "verif_pendiente": bool(perfil) and not vigente and perfil.verificaciones.filter(estado="pendiente").exists(),
        "jornada_hoy": perfil.jornadas.filter(fecha=hoy).exists() if perfil else False,
    })
    return datos


@register.simple_tag
def ruta_activa():
    return activo()
