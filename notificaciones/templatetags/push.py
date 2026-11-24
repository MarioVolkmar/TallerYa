"""Tarjeta discreta para pedir el permiso de avisos push en el momento justo (el JS la muestra solo si hace falta)."""
from django import template

register = template.Library()

TEXTOS = {
    "taller": ("Actívalos para enterarte de las citas al instante",
               "Te avisamos en este celular cuando un cliente pida una cita."),
    "mecanico": ("Actívalos para enterarte de las solicitudes al instante",
                 "Te avisamos en este celular cuando alguien te pida una visita."),
    "motero": ("¿Quieres saber cuándo te respondan?",
               "Activa los avisos y te contamos al instante si confirman o cambian tu cita o visita."),
}


@register.inclusion_tag("notificaciones/_tarjeta_push.html", takes_context=True)
def tarjeta_push(context, tipo, una_vez=False):
    """`una_vez`: solo aparece justo después de pedir algo (bandera de sesión que se consume)."""
    request = context.get("request")
    mostrar = bool(request and request.user.is_authenticated)
    if mostrar and una_vez:
        mostrar = bool(request.session.pop("sugerir_push", False))
    titulo, texto = TEXTOS.get(tipo, TEXTOS["motero"])
    return {"mostrar": mostrar, "titulo": titulo, "texto": texto, "tipo": tipo}
