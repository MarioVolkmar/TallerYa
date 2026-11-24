"""Sección Moderación: reportes del foro, preguntas, respuestas y reseñas. Ocultar/mostrar, eliminar y marcar revisado."""
from django.db.models import Count, Q

from foro.models import Pregunta, Reporte, Respuesta
from talleres.models import Resena

from django.utils import timezone

from ..acciones import accion, eliminador, interruptor
from ..eliminacion import Dependencia, analizar
from ..forms import FiltroModeracion
from ..paginacion import paginar

# ---------- Avisos al autor ----------
def _avisar_autor(autor, clave, titulo, motivo, url=""):
    """Notificación al autor con el motivo. La clave lleva la hora: ocultar dos veces avisa dos veces."""
    if not autor:
        return
    from notificaciones.models import Notificacion
    from notificaciones.servicios import notificar
    notificar(autor, f"{clave}:{timezone.now():%Y%m%d%H%M%S%f}", titulo, f"Motivo: {motivo}. Si crees que es un error, escríbenos.",
              url, Notificacion.Tipo.TALLER if "resena" in clave else Notificacion.Tipo.FORO)


def _cerrar_reportes(objeto):
    """Ocultar cierra los reportes de ese contenido; devuelve el cambio para la bitácora."""
    n = objeto.reportes.filter(revisado=False).update(revisado=True) if hasattr(objeto, "reportes") else 0
    return [{"campo": "reportes", "etiqueta": "Reportes cerrados", "antes": "—", "despues": str(n)}] if n else []


def _oculto(autor_de, titulo, url_de=lambda o: ""):
    def gancho(request, obj, valor):
        if valor:
            return []
        _avisar_autor(autor_de(obj), f"moderacion-oculto:{type(obj).__name__.lower()}:{obj.pk}", titulo, request.motivo, url_de(obj))
        return _cerrar_reportes(obj)
    return gancho


def _eliminado(autor_de, titulo):
    def gancho(request, obj, motivo):
        _avisar_autor(autor_de(obj), f"moderacion-eliminado:{type(obj).__name__.lower()}:{obj.pk}", titulo, motivo)
    return gancho


# ---------- Acciones ----------
interruptor("foro.pregunta_visible", modelo=Pregunta, campo="visible", etiqueta="Visible", nombre="Ocultar o mostrar pregunta",
            si="Volvió a mostrar", no="Ocultó", describe="la pregunta #{pk} del foro", motivo_al_apagar=True,
            despues_de=_oculto(lambda o: o.autor, "Ocultamos tu pregunta del foro", lambda o: o.get_absolute_url()))
interruptor("foro.respuesta_visible", modelo=Respuesta, campo="visible", etiqueta="Visible", nombre="Ocultar o mostrar respuesta",
            si="Volvió a mostrar", no="Ocultó", describe="la respuesta #{pk} del foro", motivo_al_apagar=True,
            despues_de=_oculto(lambda o: o.autor, "Ocultamos tu respuesta del foro", lambda o: o.pregunta.get_absolute_url()))
interruptor("resenas.visible", modelo=Resena, campo="visible", etiqueta="Visible", nombre="Ocultar o mostrar reseña",
            si="Volvió a mostrar", no="Ocultó", describe="la reseña #{pk} de {obj.taller.nombre}", motivo_al_apagar=True,
            despues_de=_oculto(lambda o: o.usuario, "Ocultamos tu reseña de un taller"))

REGLAS_PREGUNTA = [
    Dependencia("rodadas", "rodada", lambda p: 1 if hasattr(p, "rodada") else 0, True,
                "es la publicación de una rodada con asistentes; ocúltala."),
    Dependencia("respuestas", "respuesta", lambda p: p.respuestas.count(), efecto="se borran."),
    Dependencia("reportes", "reporte", lambda p: p.reportes.count(), efecto="se borran."),
]
REGLAS_RESPUESTA = [
    Dependencia("respuestas citándola", "respuesta citándola", lambda r: r.hijas.count(),
                efecto="se quedan sin la cita."),
    Dependencia("reportes", "reporte", lambda r: r.reportes.count(), efecto="se borran."),
]
REGLAS_RESENA = []

eliminador("foro.pregunta_eliminar", modelo=Pregunta, reglas=REGLAS_PREGUNTA, nombre="Eliminar pregunta",
           describe="la pregunta #{pk} del foro ({a[registro]})",
           avisar=_eliminado(lambda o: o.autor, "Eliminamos tu pregunta del foro"))
eliminador("foro.respuesta_eliminar", modelo=Respuesta, reglas=REGLAS_RESPUESTA, nombre="Eliminar respuesta",
           describe="la respuesta #{pk} del foro", avisar=_eliminado(lambda o: o.autor, "Eliminamos tu respuesta del foro"))
eliminador("resenas.eliminar", modelo=Resena, reglas=REGLAS_RESENA, nombre="Eliminar reseña",
           describe="la reseña #{pk} ({a[registro]})", avisar=_eliminado(lambda o: o.usuario, "Eliminamos tu reseña de un taller"))


@accion("foro.reporte_revisado", modelo=Reporte, nombre="Marcar reporte revisado",
        campos={"revisado": ("Revisado", lambda r: r.revisado)},
        frase="Marcó como revisado el reporte #{pk} del foro", exito="Reporte marcado como revisado.")
def reporte_revisado(request, reporte):
    reporte.revisado = True
    reporte.save(update_fields=["revisado"])


# ---------- Vista ----------
def _visibles(qs, estado):
    return qs.filter(visible=True) if estado == "visibles" else qs.filter(visible=False) if estado == "ocultas" else qs


def seccion(request):
    form = FiltroModeracion(request.GET)
    datos = form.cleaned_data if form.is_valid() else {}
    tipo, q, estado = datos.get("tipo") or "reportes", datos.get("q", ""), datos.get("estado")
    if tipo == "preguntas":
        qs = _visibles(Pregunta.objects.select_related("autor").annotate(n_resp=Count("respuestas")), estado)
        if q:
            qs = qs.filter(Q(titulo__icontains=q) | Q(cuerpo__icontains=q) | Q(autor__email__icontains=q))
        reglas = REGLAS_PREGUNTA
    elif tipo == "respuestas":
        qs = _visibles(Respuesta.objects.select_related("autor", "pregunta"), estado)
        if q:
            qs = qs.filter(Q(cuerpo__icontains=q) | Q(autor__email__icontains=q))
        reglas = REGLAS_RESPUESTA
    elif tipo == "resenas":
        qs = _visibles(Resena.objects.select_related("taller", "usuario"), estado)
        if q:
            qs = qs.filter(Q(comentario__icontains=q) | Q(nombre__icontains=q) | Q(taller__nombre__icontains=q))
        reglas = REGLAS_RESENA
    else:
        tipo = "reportes"
        qs = Reporte.objects.select_related("usuario", "pregunta", "respuesta__pregunta")
        ver = datos.get("reporte")
        if ver != "todos":
            qs = qs.filter(revisado=ver == "revisados")
        if q:
            qs = qs.filter(Q(motivo__icontains=q) | Q(pregunta__titulo__icontains=q) | Q(respuesta__cuerpo__icontains=q))
        reglas = None
    datos_pagina = paginar(request, qs.order_by("-pk"), "moderacion")
    filas = [(o, analizar(o, reglas) if reglas is not None else None) for o in datos_pagina["pagina"]]
    return "consola/moderacion.html", {"form": form, "tipo": tipo, "filas": filas, "ver_revisados": tipo == "reportes" and datos.get("reporte") == "revisados",
                                       **datos_pagina}
