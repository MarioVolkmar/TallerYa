from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from talleres.models import Marca

from .forms import PreguntaForm, RespuestaForm
from .models import REPORTES_PARA_OCULTAR, Pregunta, Reporte, Respuesta

MAX_PUBLICACIONES_POR_HORA = 10


def _puede_publicar(usuario):
    """Freno básico contra spam: máximo de publicaciones por hora y usuario."""
    clave = f"foro-publicaciones:{usuario.pk}"
    n = cache.get(clave, 0)
    if n >= MAX_PUBLICACIONES_POR_HORA:
        return False
    cache.set(clave, n + 1, 3600)
    return True


def lista(request):
    preguntas = (
        Pregunta.objects.filter(visible=True)
        .select_related("autor", "marca", "autor__taller")
        .annotate(num_respuestas=Count("respuestas", filter=Q(respuestas__visible=True)))
        .order_by("-creado")
    )
    q = request.GET.get("q", "").strip()
    if q:
        preguntas = preguntas.filter(Q(titulo__icontains=q) | Q(cuerpo__icontains=q))
    marca = request.GET.get("marca", "")
    if marca.isdigit():
        preguntas = preguntas.filter(marca_id=marca)
    if request.GET.get("filtro") == "sin-respuesta":
        preguntas = preguntas.filter(num_respuestas=0)

    pagina = Paginator(preguntas, 15).get_page(request.GET.get("pagina"))
    return render(request, "foro/lista.html", {
        "pagina": pagina, "marcas": Marca.objects.all(), "q": q, "marca": marca,
        "filtro": request.GET.get("filtro", ""),
    })


@login_required
def preguntar(request):
    form = PreguntaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not _puede_publicar(request.user):
            messages.error(request, "Has publicado mucho en poco tiempo. Intenta de nuevo en un rato.")
        else:
            pregunta = form.save(commit=False)
            pregunta.autor = request.user
            pregunta.save()
            messages.success(request, "¡Pregunta publicada! Vuelve pronto para ver las respuestas.")
            return redirect(pregunta)
    return render(request, "foro/preguntar.html", {"form": form})


def pregunta(request, pk, slug=None):
    pregunta = get_object_or_404(Pregunta.objects.select_related("autor", "marca", "autor__taller"), pk=pk, visible=True)
    if slug != pregunta.slug:
        return redirect(pregunta, permanent=True)

    form = RespuestaForm(request.POST or None)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect_to_login(pregunta.get_absolute_url())
        if form.is_valid():
            if not _puede_publicar(request.user):
                messages.error(request, "Has publicado mucho en poco tiempo. Intenta de nuevo en un rato.")
            else:
                respuesta = form.save(commit=False)
                respuesta.pregunta = pregunta
                respuesta.autor = request.user
                respuesta.save()
                messages.success(request, "¡Gracias por responder!")
                return redirect(respuesta)

    respuestas = list(pregunta.respuestas.filter(visible=True).select_related("autor", "autor__taller"))
    # La mejor respuesta va primero
    respuestas.sort(key=lambda r: r.pk != pregunta.mejor_respuesta_id)
    return render(request, "foro/pregunta.html", {
        "pregunta": pregunta,
        "respuestas": respuestas,
        "form": form,
        "es_autor": request.user == pregunta.autor,
    })


@login_required
@require_POST
def marcar_mejor(request, pk):
    respuesta = get_object_or_404(Respuesta, pk=pk, visible=True, pregunta__autor=request.user)
    pregunta = respuesta.pregunta
    pregunta.mejor_respuesta = None if pregunta.mejor_respuesta_id == respuesta.pk else respuesta
    pregunta.save(update_fields=["mejor_respuesta"])
    return redirect(respuesta)


@login_required
@require_POST
def reportar(request, tipo, pk):
    modelo = {"pregunta": Pregunta, "respuesta": Respuesta}.get(tipo)
    if not modelo:
        return redirect("foro:lista")
    objeto = get_object_or_404(modelo, pk=pk, visible=True)
    if objeto.autor_id == request.user.pk:
        messages.info(request, "No puedes reportar tu propia publicación.")
        return redirect(objeto)
    try:
        with transaction.atomic():
            Reporte.objects.create(usuario=request.user, motivo=request.POST.get("motivo", "")[:200], **{tipo: objeto},
            )
    except IntegrityError:
        messages.info(request, "Ya habías reportado esta publicación.")
        return redirect(objeto)

    if objeto.reportes.filter(revisado=False).count() >= REPORTES_PARA_OCULTAR:
        objeto.visible = False
        objeto.save(update_fields=["visible"])
        messages.success(request, "Gracias. La publicación quedó oculta mientras la revisamos.")
        return redirect("foro:lista" if tipo == "pregunta" else objeto.pregunta)
    messages.success(request, "Gracias por avisar. Revisaremos la publicación.")
    return redirect(objeto)
