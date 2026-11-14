"""Vistas del foro: lista con filtros, publicar preguntas y respuestas, mejor respuesta, reportes y votos."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from notificaciones.models import Notificacion
from notificaciones.servicios import notificar

from talleres.models import Marca

from .forms import PreguntaForm, RespuestaForm
from .models import Categoria, Voto, REPORTES_PARA_OCULTAR, Pregunta, Reporte, Respuesta

MAX_PUBLICACIONES_POR_HORA = 10


def _puede_publicar(usuario):
    """Freno básico contra spam: máximo de publicaciones por hora y usuario."""
    clave = f"foro-publicaciones:{usuario.pk}"
    n = cache.get(clave, 0)
    if n >= MAX_PUBLICACIONES_POR_HORA:
        return False
    cache.set(clave, n + 1, 3600)
    return True


ORDENES = {"recientes": "Recientes", "votados": "Más votados", "respuestas": "Más respuestas", "vistas": "Más vistos"}


def lista(request):
    """Temas del foro: buscador, tema (categoría), marca y línea, sin respuesta, orden y páginas de 15."""
    preguntas = (
        Pregunta.objects.filter(visible=True)
        .select_related("autor", "marca", "linea", "autor__taller")
        .annotate(num_respuestas=Count("respuestas", filter=Q(respuestas__visible=True), distinct=True),
                  num_votos=Count("votos", distinct=True))
    )
    f = request.GET
    q = f.get("q", "").strip()
    if q:
        preguntas = preguntas.filter(Q(titulo__icontains=q) | Q(cuerpo__icontains=q) | Q(respuestas__cuerpo__icontains=q)).distinct()
    categoria = f.get("categoria", "")
    if categoria in Categoria.values:
        preguntas = preguntas.filter(categoria=categoria)
    marca = f.get("marca", "")
    if marca.isdigit():
        preguntas = preguntas.filter(marca_id=marca)
    linea = f.get("linea", "")
    if linea.isdigit():
        preguntas = preguntas.filter(linea_id=linea)
    if f.get("filtro") == "sin-respuesta":
        preguntas = preguntas.filter(num_respuestas=0)
    orden = f.get("orden") if f.get("orden") in ORDENES else "recientes"
    preguntas = preguntas.order_by({"recientes": "-creado", "votados": "-num_votos", "respuestas": "-num_respuestas",
                                    "vistas": "-vistas"}[orden], "-creado")

    sin_pagina = f.copy()
    sin_pagina.pop("pagina", None)
    sin_orden = sin_pagina.copy()
    sin_orden.pop("orden", None)
    sin_categoria = sin_pagina.copy()
    sin_categoria.pop("categoria", None)
    from garaje.models import LineaMoto
    return render(request, "foro/lista.html", {
        "pagina": Paginator(preguntas, 15).get_page(f.get("pagina")),
        "marcas": Marca.objects.all(), "q": q, "marca": marca, "linea": linea, "categoria": categoria,
        "lineas": LineaMoto.objects.filter(marca_id=marca).order_by("nombre") if marca.isdigit() else [],
        "categorias": Categoria.choices, "orden": orden, "ordenes": ORDENES,
        "filtro": f.get("filtro", ""),
        "qs_orden": sin_orden.urlencode(), "qs_categoria": sin_categoria.urlencode(), "qs_pagina": sin_pagina.urlencode(),
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
    pregunta = get_object_or_404(Pregunta.objects.select_related("autor", "marca", "linea", "autor__taller", "rodada"), pk=pk, visible=True)
    if getattr(pregunta, "rodada", None):  # las rodadas se ven (y se comentan) en su propia página
        return redirect(pregunta.rodada)
    if slug != pregunta.slug:
        return redirect(pregunta, permanent=True)
    _contar_vista(request, pregunta)

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
                if pregunta.autor_id != request.user.pk:
                    quien = getattr(getattr(request.user, "taller", None), "nombre", "") or request.user.first_name or "Alguien"
                    notificar(pregunta.autor, f"foro-respuesta:{respuesta.pk}", f"{quien} respondió tu pregunta",
                              pregunta.titulo, respuesta.get_absolute_url(), Notificacion.Tipo.FORO)
                messages.success(request, "¡Gracias por responder!")
                return redirect(respuesta)

    respuestas = list(pregunta.respuestas.filter(visible=True).select_related("autor", "autor__taller")
                      .annotate(num_votos=Count("votos")))
    # La mejor respuesta va primero; luego las más votadas
    respuestas.sort(key=lambda r: (r.pk != pregunta.mejor_respuesta_id, -r.num_votos, r.creado))
    mis_votos = set()
    if request.user.is_authenticated:
        mis_votos = {("r", v) for v in Voto.objects.filter(usuario=request.user, respuesta__pregunta=pregunta).values_list("respuesta_id", flat=True)}
        if Voto.objects.filter(usuario=request.user, pregunta=pregunta).exists():
            mis_votos.add(("p", pregunta.pk))
    for r in respuestas:
        r.vote_mio = ("r", r.pk) in mis_votos
    return render(request, "foro/pregunta.html", {
        "pregunta": pregunta,
        "votos_pregunta": pregunta.votos.count(),
        "voto_pregunta_mio": ("p", pregunta.pk) in mis_votos,
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
    if pregunta.mejor_respuesta_id and respuesta.autor_id != request.user.pk:
        notificar(respuesta.autor, f"foro-mejor:{respuesta.pk}", "Tu respuesta fue elegida como la mejor",
                  pregunta.titulo, respuesta.get_absolute_url(), Notificacion.Tipo.FORO)
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


def _contar_vista(request, pregunta):
    """Suma una vista por sesión (recargar la página no infla el contador)."""
    vistas = request.session.get("foro-vistas", [])
    if pregunta.pk in vistas:
        return
    Pregunta.objects.filter(pk=pregunta.pk).update(vistas=F("vistas") + 1)
    pregunta.vistas += 1
    request.session["foro-vistas"] = (vistas + [pregunta.pk])[-200:]


@login_required
@require_POST
def votar(request, tipo, pk):
    """Voto "me sirvió" (se quita si se vuelve a tocar). No se vota lo propio."""
    modelo = {"pregunta": Pregunta, "respuesta": Respuesta}.get(tipo)
    if not modelo:
        return redirect("foro:lista")
    objeto = get_object_or_404(modelo, pk=pk, visible=True)
    if objeto.autor_id == request.user.pk:
        messages.info(request, "No puedes votar tu propia publicación.")
        return redirect(objeto)
    voto, creado = Voto.objects.get_or_create(usuario=request.user, **{tipo: objeto})
    if not creado:
        voto.delete()
    if request.headers.get("X-Requested-With") == "fetch":
        return JsonResponse({"votado": creado, "votos": objeto.votos.count()})
    return redirect(objeto)
