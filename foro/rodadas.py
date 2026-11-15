"""Rodadas y eventos: lista (próximas primero, pasadas archivadas), crear, ver y el botón "Voy".

Cada rodada tiene su pregunta del foro (tema "Rutas y paseos"): los comentarios son sus respuestas
y se moderan y reportan igual que el resto del foro. Si la pregunta queda oculta, la rodada también.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from notificaciones.models import Notificacion
from notificaciones.servicios import notificar

from .forms import RespuestaForm, RodadaForm
from .models import Asistencia, Categoria, Pregunta, Respuesta, Rodada
from .views import _puede_publicar


def _visibles():
    return (Rodada.objects.filter(pregunta__visible=True)
            .select_related("pregunta", "organizador", "organizador__taller")
            .annotate(num_asistentes=Count("asistencias", distinct=True)))


def lista(request):
    ahora = timezone.now()
    pasadas = request.GET.get("ver") == "pasadas"
    rodadas = _visibles().filter(fecha_hora__lt=ahora).order_by("-fecha_hora") if pasadas \
        else _visibles().filter(fecha_hora__gte=ahora).order_by("fecha_hora")
    # Las dos pestañas se cuentan en una sola consulta
    conteos = Rodada.objects.filter(pregunta__visible=True).aggregate(
        proximas=Count("pk", filter=Q(fecha_hora__gte=ahora)), pasadas=Count("pk", filter=Q(fecha_hora__lt=ahora)))
    return render(request, "foro/rodadas.html", {
        "pagina": Paginator(rodadas, 12).get_page(request.GET.get("pagina")), "pasadas": pasadas,
        "num_proximas": conteos["proximas"], "num_pasadas": conteos["pasadas"],
    })


@login_required
def crear(request):
    form = RodadaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not _puede_publicar(request.user):
            messages.error(request, "Has publicado mucho en poco tiempo. Intenta de nuevo en un rato.")
        else:
            d = form.cleaned_data
            with transaction.atomic():
                pregunta = Pregunta.objects.create(
                    autor=request.user, titulo=d["titulo"], categoria=Categoria.RUTAS,
                    cuerpo=d["cuerpo"] or f"Rodada a {d['destino']}. ¡Comenta si vas o si tienes dudas!",
                )
                rodada = Rodada.objects.create(
                    pregunta=pregunta, organizador=request.user, fecha_hora=d["fecha_hora"],
                    punto_encuentro=d["punto_encuentro"], destino=d["destino"], nivel=d["nivel"], cupo=d["cupo"],
                )
                Asistencia.objects.create(rodada=rodada, usuario=request.user)  # quien organiza, va
            messages.success(request, "¡Rodada publicada! Compártela con tu parche.")
            return redirect(rodada)
    return render(request, "foro/rodada_crear.html", {"form": form})


def detalle(request, pk):
    rodada = get_object_or_404(_visibles(), pk=pk)
    pregunta = rodada.pregunta
    from .views import contexto_hilo, publicar_respuesta
    publicado, padre, form = publicar_respuesta(request, pregunta, en_rodada=True)
    if isinstance(publicado, Respuesta):
        messages.success(request, "Comentario publicado.")
        return redirect(f"{rodada.get_absolute_url()}#r{publicado.pk}")
    if publicado:
        return publicado
    hilo = contexto_hilo(request, pregunta, padre, form, por_votos=False)

    asistentes = [a.usuario for a in rodada.asistencias.select_related("usuario", "usuario__taller", "usuario__perfil")]
    voy = request.user.is_authenticated and any(u.pk == request.user.pk for u in asistentes)
    comentarios = hilo["respuestas"]
    # Organizador primero; cupo en porcentaje para la barra
    asistentes.sort(key=lambda u: u.pk != rodada.organizador_id)
    ocupado = round(100 * len(asistentes) / rodada.cupo) if rodada.cupo else None
    # Mapa por texto, como en la ficha de los talleres (sin clave de API: la rodada no guarda coordenadas)
    from urllib.parse import quote
    lugar = quote(f"{rodada.punto_encuentro}, Valle de Aburrá, Antioquia")
    return render(request, "foro/rodada.html", {
        **hilo, "url_publicar": rodada.get_absolute_url(), "es_autor": False,
        "rodada": rodada, "pregunta": pregunta, "asistentes": asistentes, "voy": voy,
        "lleno": rodada.cupo is not None and len(asistentes) >= rodada.cupo,
        "comentarios": comentarios,
        "es_organizador": request.user.pk == rodada.organizador_id,
        "rodada_reportada": hilo["pregunta_reportada"],
        "ocupado": min(ocupado, 100) if ocupado is not None else None,
        "casi_lleno": ocupado is not None and ocupado >= 80,
        "rodadas_organizadas": Rodada.objects.filter(organizador_id=rodada.organizador_id, pregunta__visible=True).count(),
        "mapa_embebido": f"https://www.google.com/maps?q={lugar}&output=embed&hl=es",
        "url_google_maps": f"https://www.google.com/maps/search/?api=1&query={lugar}",
        "url_waze": f"https://waze.com/ul?q={lugar}&navigate=yes",
    })


@login_required
@require_POST
def voy(request, pk):
    """Apuntarse o bajarse de la rodada. Con cupo lleno no entra nadie más; las pasadas ya no cambian."""
    with transaction.atomic():
        rodada = get_object_or_404(Rodada.objects.select_for_update().select_related("pregunta"), pk=pk, pregunta__visible=True)
        if rodada.pasada:
            messages.info(request, "Esta rodada ya pasó.")
            return redirect(rodada)
        actual = rodada.asistencias.filter(usuario=request.user).first()
        if actual:
            if rodada.organizador_id == request.user.pk:
                messages.info(request, "Quien organiza no puede bajarse. Si se cancela, avísalo en los comentarios.")
            else:
                actual.delete()
                messages.success(request, "Listo, ya no estás en la lista.")
        elif rodada.cupo is not None and rodada.asistencias.count() >= rodada.cupo:
            messages.error(request, "El cupo de esta rodada está lleno.")
        else:
            Asistencia.objects.create(rodada=rodada, usuario=request.user)
            messages.success(request, "¡Quedaste en la lista! Nos vemos en el punto de encuentro.")
    return redirect(rodada)
