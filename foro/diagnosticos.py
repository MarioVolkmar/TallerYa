"""Diagnósticos guiados citados en el foro (ver DiagnosticoCompartido y garaje.vista_diagnostico.resumen_diagnostico).

Decisión: se guarda un resumen inmutable al publicar, no solo la URL. La URL depende de la moto del autor (privada) y
de reglas del diagnóstico que pueden cambiar; el resumen congela lo que el autor vio y solo lleva datos públicos."""
from garaje import diagnostico as dx
from garaje.vista_diagnostico import diagnosticos_recientes, resumen_diagnostico

from .models import DiagnosticoCompartido, Pregunta

SISTEMAS = sorted({r["sistema"] for r in dx.RESULTADOS.values()})
ERROR = "Ese diagnóstico ya no está disponible para citarlo. Vuelve a hacerlo y compártelo desde el resultado."


def opciones(request):
    """Diagnósticos de la sesión de esta persona, para el selector «Adjuntar un diagnóstico»."""
    if not request.user.is_authenticated:
        return []
    return [{"consulta": d["consulta"], "etiqueta": " · ".join(x for x in (d.get("moto"), d.get("sintoma"), d.get("causa")) if x)}
            for d in diagnosticos_recientes(request)]


def adjuntar(request):
    """Lee el campo «diagnostico» del POST. Devuelve (resumen | None, error | None); se guarda con guardar().

    Solo se aceptan consultas que esta persona vio (su sesión) y que resuelven con SUS motos: sin IDOR."""
    consulta = request.POST.get("diagnostico", "").strip()
    if not consulta:
        return None, None
    if consulta not in {d["consulta"] for d in diagnosticos_recientes(request)}:
        return None, ERROR
    resumen = resumen_diagnostico(consulta, request.user)
    if not resumen:
        return None, ERROR
    return resumen, None


def guardar(usuario, resumen):
    return DiagnosticoCompartido.desde_resumen(usuario, resumen) if resumen else None


def vista_previa(request, consulta):
    """Resumen (sin guardar) para mostrar la tarjeta en el formulario, o None si no es de esta persona."""
    if not consulta or consulta not in {d["consulta"] for d in diagnosticos_recientes(request)}:
        return None
    return resumen_diagnostico(consulta, request.user)


def parecidos(pregunta, limite=4):
    """Otros temas que citan un diagnóstico con el mismo resultado (o, si no hay, del mismo sistema)."""
    d = pregunta.diagnostico
    if not d:
        return []
    base = Pregunta.objects.filter(visible=True, rodada__isnull=True).exclude(pk=pregunta.pk).order_by("-ultima_actividad")
    mismos = list(base.filter(diagnostico__clave=d.clave)[:limite])
    if len(mismos) < limite:
        mismos += list(base.filter(diagnostico__sistema=d.sistema).exclude(pk__in=[p.pk for p in mismos])[:limite - len(mismos)])
    return mismos
