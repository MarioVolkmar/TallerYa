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

from metricas.nucleo import registrar_evento

from . import menciones, reacciones
from .forms import PreguntaForm, RespuestaForm
from .models import Categoria, Reaccion, Voto, REPORTES_PARA_OCULTAR, Pregunta, Reporte, Respuesta

MAX_PUBLICACIONES_POR_HORA = 10


def _puede_publicar(usuario):
    """Freno básico contra spam: máximo de publicaciones por hora y usuario."""
    clave = f"foro-publicaciones:{usuario.pk}"
    n = cache.get(clave, 0)
    if n >= MAX_PUBLICACIONES_POR_HORA:
        return False
    cache.set(clave, n + 1, 3600)
    return True


NOMBRES_CORTOS = {"rutas": "Rutas", "repuestos": "Repuestos"}  # pestañas cortas (el nombre completo va en title)


def _sin(qd, *claves):
    copia = qd.copy()
    for c in claves:
        copia.pop(c, None)
    return copia.urlencode()


ORDENES = {"recientes": "Recientes", "votados": "Más votados", "respuestas": "Más respuestas", "vistas": "Más vistos"}


def lista(request):
    """Temas del foro: buscador, tema (categoría), marca y línea, sin respuesta, orden y páginas de 15."""
    preguntas = (
        Pregunta.objects.filter(visible=True)
        .select_related("autor", "marca", "linea", "autor__taller", "ultimo_autor", "ultimo_autor__taller")
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
    # "Sin respuesta" llega como filtro=… (enlaces viejos) o como orden=… (selector "Ordenar")
    sin_respuesta = f.get("filtro") == "sin-respuesta" or f.get("orden") == "sin-respuesta"
    if sin_respuesta:
        preguntas = preguntas.filter(num_respuestas=0)
    orden = f.get("orden") if f.get("orden") in ORDENES else "recientes"
    preguntas = preguntas.order_by({"recientes": "-ultima_actividad", "votados": "-num_votos", "respuestas": "-num_respuestas",
                                    "vistas": "-vistas"}[orden], "-ultima_actividad")

    sin_pagina = f.copy()
    sin_pagina.pop("pagina", None)
    sin_orden = sin_pagina.copy()
    sin_orden.pop("orden", None)
    sin_categoria = sin_pagina.copy()
    sin_categoria.pop("categoria", None)
    from garaje.models import LineaMoto
    # Vista por defecto (sin búsqueda, filtros, orden elegido ni página): "Recientes" arriba y los temas agrupados por
    # categoría. Con cualquier filtro u orden, la lista plana con páginas.
    agrupada = not any(f.get(k) for k in ("q", "categoria", "marca", "linea", "filtro", "orden", "pagina"))
    recientes, grupos = [], []
    if agrupada:
        recientes = list(preguntas[:5])
        grupos = _grupos_por_categoria(preguntas)
    return render(request, "foro/lista.html", {
        "agrupada": agrupada, "recientes": recientes, "grupos": grupos,
        "pagina": Paginator(preguntas, 15).get_page(f.get("pagina")),
        "marcas": Marca.objects.all(), "q": q, "marca": marca, "linea": linea, "categoria": categoria,
        "lineas": LineaMoto.objects.filter(marca_id=marca).order_by("nombre") if marca.isdigit() else [],
        "categorias": [(c, n, NOMBRES_CORTOS.get(c, n)) for c, n in Categoria.choices], "orden": orden, "ordenes": ORDENES,
        "orden_elegido": f.get("orden") if f.get("orden") in ORDENES else "", "qs_todos": _sin(sin_orden, "filtro"),
        "filtro": "sin-respuesta" if sin_respuesta else "",
        "qs_orden": sin_orden.urlencode(), "qs_categoria": sin_categoria.urlencode(), "qs_pagina": sin_pagina.urlencode(),
    })


def _grupos_por_categoria(preguntas, por_grupo=5):
    """Cada categoría con su total, la fecha del último tema y sus últimos temas (una consulta para los temas)."""
    from django.db.models import Max, Window
    from django.db.models.functions import RowNumber
    totales = {fila["categoria"]: fila for fila in Pregunta.objects.filter(visible=True).values("categoria")
               .annotate(n=Count("pk"), ultimo=Max("ultima_actividad")).order_by()}
    ultimos = {}
    for p in preguntas.annotate(fila=Window(RowNumber(), partition_by=[F("categoria")],
                                            order_by=F("ultima_actividad").desc())
                                ).filter(fila__lte=por_grupo).order_by("categoria", "-ultima_actividad"):
        ultimos.setdefault(p.categoria, []).append(p)
    grupos = [{"clave": clave, "nombre": nombre, "total": totales.get(clave, {}).get("n", 0),
               "ultimo": totales.get(clave, {}).get("ultimo"), "temas": ultimos.get(clave, [])}
              for clave, nombre in Categoria.choices]
    # Primero las categorías con actividad más reciente; las vacías al final
    return sorted(grupos, key=lambda g: (g["ultimo"] is None, -(g["ultimo"].timestamp() if g["ultimo"] else 0)))


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
            menciones.notificar_publicacion(pregunta, pregunta, request.user)
            registrar_evento(request, "foro_pregunta", categoria=pregunta.categoria)
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

    publicado, padre, form = publicar_respuesta(request, pregunta)
    if isinstance(publicado, Respuesta):
        messages.success(request, "¡Gracias por responder!")
        return redirect(publicado)
    if publicado:
        return publicado
    contexto = contexto_hilo(request, pregunta, padre, form)
    contexto["es_autor"] = request.user == pregunta.autor
    return render(request, "foro/pregunta.html", contexto)


def publicar_respuesta(request, pregunta, en_rodada=False):
    """POST de una respuesta (o comentario de rodada), en hilo si trae "padre". Devuelve (respuesta | None, padre, form).
    Si hay que redirigir sin publicar (sin sesión o padre inexistente) devuelve una respuesta HTTP como primer valor."""
    form = RespuestaForm(request.POST or None)
    padre = None
    if request.method != "POST":
        return None, None, form
    if not request.user.is_authenticated:
        return redirect_to_login(request.path), None, form
    padre_id = request.POST.get("padre", "")
    if padre_id.isdigit():  # responder a un mensaje concreto del mismo tema
        padre = Respuesta.objects.filter(pk=padre_id, pregunta=pregunta, visible=True).select_related("autor").first()
        if padre is None:
            messages.error(request, "Ese mensaje ya no está disponible. Tu respuesta no se publicó.")
            return redirect(request.path), None, form
    if form.is_valid():
        if not _puede_publicar(request.user):
            messages.error(request, "Has publicado mucho en poco tiempo. Intenta de nuevo en un rato.")
        else:
            respuesta = form.save(commit=False)
            respuesta.pregunta, respuesta.autor, respuesta.padre = pregunta, request.user, padre
            respuesta.save()
            menciones.notificar_publicacion(respuesta, pregunta, request.user, en_rodada=en_rodada)
            registrar_evento(request, "foro_respuesta", rodada=en_rodada)
            return respuesta, padre, form
    return None, padre, form


def contexto_hilo(request, pregunta, padre, form, por_votos=True):
    """Respuestas en hilo con menciones, reacciones, votos, reportes y formularios (temas del foro y rodadas)."""
    respuestas = list(pregunta.respuestas.filter(visible=True).select_related("autor", "autor__taller", "autor__perfil")
                      .annotate(num_votos=Count("votos")))
    if por_votos:  # primer nivel: la mejor respuesta primero, luego las más votadas; en hilo, orden de llegada
        respuestas.sort(key=lambda r: (r.pk != pregunta.mejor_respuesta_id, -r.num_votos, r.creado))
    else:
        respuestas.sort(key=lambda r: r.creado)
    hilo = menciones.armar_hilo(pregunta, respuestas, dict(pregunta.respuestas.values_list("pk", "padre_id")))
    usuarios = menciones.usuarios_por_id({i for r in respuestas for i in menciones.ids_mencionados(r.cuerpo)}
                                         | set(menciones.ids_mencionados(pregunta.cuerpo)))
    for r in respuestas:
        r.cuerpo_html = menciones.renderizar(r.cuerpo, usuarios)
    reacciones.adjuntar(pregunta, respuestas, request.user)
    mis_reportes, mis_votos = set(), set()
    if request.user.is_authenticated:
        mis_reportes = {f"respuesta-{i}" if i else f"pregunta-{p}" for p, i in
                        Reporte.objects.filter(usuario=request.user)
                        .filter(Q(pregunta=pregunta) | Q(respuesta__pregunta=pregunta))
                        .values_list("pregunta_id", "respuesta_id")}
        mis_votos = {("r", v) for v in Voto.objects.filter(usuario=request.user, respuesta__pregunta=pregunta)
                     .values_list("respuesta_id", flat=True)}
        if Voto.objects.filter(usuario=request.user, pregunta=pregunta).exists():
            mis_votos.add(("p", pregunta.pk))
    for r in respuestas:
        r.reportado = f"respuesta-{r.pk}" in mis_reportes
        r.vote_mio = ("r", r.pk) in mis_votos
    return {
        "pregunta": pregunta,
        "votos_pregunta": pregunta.votos.count(),
        "voto_pregunta_mio": ("p", pregunta.pk) in mis_votos,
        "respuestas": respuestas,
        "hilo": hilo,
        "cuerpo_pregunta": menciones.renderizar(pregunta.cuerpo, usuarios),
        # Formulario abierto bajo un mensaje: sin JavaScript (?responder=ID) o si volvió con errores
        "responder": padre.pk if padre else (int(request.GET["responder"]) if request.GET.get("responder", "").isdigit() else None),
        "form": RespuestaForm() if padre else form,
        "form_hilo": form if padre else None,
        "pregunta_reportada": f"pregunta-{pregunta.pk}" in mis_reportes,
        "opciones_reaccion": reacciones.opciones(),
        "motivos_reporte": reacciones.MOTIVOS_REPORTE,
        # Diálogo de reporte abierto sin JavaScript (?reportar=respuesta-12)
        "reporte_sin_js": _reporte_sin_js(request),
    }


def _reporte_sin_js(request):
    """URL del reporte si se pidió ?reportar=respuesta-12 (el diálogo se abre sin JavaScript)."""
    from django.urls import reverse
    tipo, _, pk = request.GET.get("reportar", "").partition("-")
    if request.user.is_authenticated and tipo in ("pregunta", "respuesta") and pk.isdigit():
        return reverse("foro:reportar", args=[tipo, int(pk)])
    return ""


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
    es_fetch = request.headers.get("X-Requested-With") == "fetch"

    def responder(texto, ok=True, nivel=messages.info):
        if es_fetch:
            return JsonResponse({"ok": ok, "mensaje": texto})
        nivel(request, texto)
        return redirect(objeto)

    if objeto.autor_id == request.user.pk:
        return responder("No puedes reportar tu propia publicación.", ok=False)
    motivos = dict(reacciones.MOTIVOS_REPORTE)
    clave = request.POST.get("motivo_tipo", "")
    detalle = request.POST.get("motivo", "").strip()
    if clave == "otro":
        motivo = f"Otro: {detalle}" if detalle else "Otro"
    elif clave in motivos:
        motivo = motivos[clave] + (f": {detalle}" if detalle else "")
    else:
        motivo = detalle
    try:
        with transaction.atomic():
            Reporte.objects.create(usuario=request.user, motivo=motivo[:200], **{tipo: objeto})
    except IntegrityError:
        return responder("Ya habías reportado esta publicación.", ok=False)

    if objeto.reportes.filter(revisado=False).count() >= REPORTES_PARA_OCULTAR:
        objeto.visible = False
        objeto.save(update_fields=["visible"])
        if tipo == "respuesta":
            objeto.pregunta.recalcular_actividad()
        if es_fetch:
            return JsonResponse({"ok": True, "oculta": True,
                                 "mensaje": "Gracias. La publicación quedó oculta mientras la revisamos."})
        messages.success(request, "Gracias. La publicación quedó oculta mientras la revisamos.")
        return redirect("foro:lista" if tipo == "pregunta" else objeto.pregunta)
    return responder("Gracias por avisar. Revisaremos la publicación.", nivel=messages.success)


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
    if objeto.autor_id == request.user.pk:  # lo propio no se vota
        if request.headers.get("X-Requested-With") == "fetch":
            return JsonResponse({"ok": False, "mensaje": "No puedes votar tu propia publicación."}, status=403)
        messages.info(request, "No puedes votar tu propia publicación.")
        return redirect(objeto)
    voto, creado = Voto.objects.get_or_create(usuario=request.user, **{tipo: objeto})
    if not creado:
        voto.delete()
    if request.headers.get("X-Requested-With") == "fetch":
        return JsonResponse({"votado": creado, "votos": objeto.votos.count()})
    return redirect(objeto)


@login_required
def sugerir_usuarios(request):
    """Autocompletado de @menciones: personas que ya participan en el foro (primero las de este tema). Nunca devuelve correos."""
    from django.contrib.auth import get_user_model
    q = request.GET.get("q", "").strip()[:30]
    base = (get_user_model().objects.filter(is_active=True).exclude(pk=request.user.pk)
            .filter(Q(preguntas__isnull=False) | Q(respuestas__isnull=False)).distinct().select_related("taller"))
    if q:
        base = base.filter(Q(first_name__icontains=q) | Q(taller__nombre__icontains=q))
    pregunta_id = request.GET.get("pregunta", "")
    del_tema = []
    if pregunta_id.isdigit():
        del_tema = list(base.filter(Q(preguntas__pk=pregunta_id) | Q(respuestas__pregunta_id=pregunta_id))
                        .order_by("first_name")[:8])
    vistos = {u.pk for u in del_tema}
    otros = [u for u in base.order_by("first_name")[:16] if u.pk not in vistos]
    return JsonResponse({"usuarios": [
        {"alias": menciones.alias(u), "nombre": menciones.nombre_publico(u),
         "detalle": "Taller" if getattr(u, "taller", None) else ("En este tema" if u.pk in vistos else "")}
        for u in (del_tema + otros)[:8]
    ]})



@login_required
@require_POST
def reaccionar(request, tipo, pk):
    """Pone, cambia o quita la reacción propia. Con fetch devuelve la fila de reacciones ya pintada."""
    from django.template.loader import render_to_string
    modelo = {"pregunta": Pregunta, "respuesta": Respuesta}.get(tipo)
    reaccion = request.POST.get("reaccion", "")
    if not modelo or reaccion not in Reaccion.Tipo.values:
        return redirect("foro:lista")
    objeto = get_object_or_404(modelo, pk=pk, visible=True)
    es_fetch = request.headers.get("X-Requested-With") == "fetch"
    if objeto.autor_id == request.user.pk:
        if es_fetch:
            return JsonResponse({"ok": False, "mensaje": "No puedes reaccionar a tu propia publicación."}, status=403)
        messages.info(request, "No puedes reaccionar a tu propia publicación.")
        return redirect(objeto)
    if reacciones.reaccionar(request.user, objeto, tipo, reaccion):
        reacciones.avisar_autor(objeto, tipo, request.user)
    if es_fetch:
        reacciones.estado(objeto, tipo, request.user)
        html = render_to_string("foro/_reacciones.html", {
            "obj": objeto, "tipo": tipo, "propio": False, "opciones_reaccion": reacciones.opciones(),
        }, request=request)
        return JsonResponse({"ok": True, "html": html})
    return redirect(objeto)


@login_required
def editar(request, tipo, pk):
    """Editar una pregunta o respuesta propia. Las menciones nuevas avisan (las ya avisadas no se repiten)."""
    modelo, formulario = {"pregunta": (Pregunta, PreguntaForm), "respuesta": (Respuesta, RespuestaForm)}.get(tipo, (None, None))
    if not modelo:
        return redirect("foro:lista")
    objeto = get_object_or_404(modelo, pk=pk, visible=True, autor=request.user)
    form = formulario(request.POST or None, instance=objeto)
    if request.method == "POST" and form.is_valid():
        objeto = form.save()
        pregunta = objeto if tipo == "pregunta" else objeto.pregunta
        if tipo == "pregunta" and form.has_changed():  # editar el tema lo vuelve a subir en "Recientes"
            from django.utils import timezone
            Pregunta.objects.filter(pk=pregunta.pk).update(ultima_actividad=timezone.now(), ultimo_autor=None)
        menciones.notificar_publicacion(objeto, pregunta, request.user)
        messages.success(request, "Cambios guardados.")
        return redirect(objeto)
    return render(request, "foro/editar.html", {"form": form, "objeto": objeto, "tipo": tipo})


@login_required
@require_POST
def eliminar(request, tipo, pk):
    """Eliminar lo propio. Las respuestas en hilo de una respuesta eliminada suben al mensaje de arriba."""
    modelo = {"pregunta": Pregunta, "respuesta": Respuesta}.get(tipo)
    if not modelo:
        return redirect("foro:lista")
    objeto = get_object_or_404(modelo, pk=pk, autor=request.user)
    if tipo == "respuesta":
        pregunta = objeto.pregunta
        with transaction.atomic():
            Respuesta.objects.filter(padre=objeto).update(padre=objeto.padre_id)
            objeto.delete()
            pregunta.recalcular_actividad()
        messages.success(request, "Tu respuesta se eliminó.")
        return redirect(pregunta)
    objeto.delete()
    messages.success(request, "Tu pregunta se eliminó.")
    return redirect("foro:lista")



def integrante(request, pk):
    """Actividad pública de una persona en el foro: conteos y sus respuestas o preguntas. Sin datos privados."""
    from django.contrib.auth import get_user_model
    from django.db.models import Min
    usuario = get_object_or_404(get_user_model().objects.select_related("taller", "perfil"), pk=pk, is_active=True)
    preguntas = Pregunta.objects.filter(autor=usuario, visible=True)
    respuestas = Respuesta.objects.filter(autor=usuario, visible=True, pregunta__visible=True)
    primera = min([f for f in (preguntas.aggregate(m=Min("creado"))["m"], respuestas.aggregate(m=Min("creado"))["m"]) if f],
                  default=usuario.date_joined)
    pestana = "preguntas" if request.GET.get("tab") == "preguntas" else "respuestas"
    if pestana == "preguntas":
        lista = preguntas.annotate(num_respuestas=Count("respuestas", filter=Q(respuestas__visible=True), distinct=True),
                                   num_votos=Count("votos", distinct=True)
                                   ).select_related("autor", "autor__taller", "marca", "linea", "ultimo_autor",
                                                    "ultimo_autor__taller").order_by("-creado")
    else:
        lista = respuestas.select_related("pregunta").order_by("-creado")
    pagina = Paginator(lista, 20).get_page(request.GET.get("pagina"))
    if pestana == "respuestas":  # extractos con "@Nombre" en vez del alias interno
        usuarios = menciones.usuarios_por_id({i for r in pagina for i in menciones.ids_mencionados(r.cuerpo)})
        for r in pagina:
            r.extracto = menciones.texto_plano(r.cuerpo, usuarios)
    return render(request, "foro/integrante.html", {
        "integrante": usuario, "nombre": menciones.nombre_publico(usuario), "desde": primera, "pestana": pestana,
        "pagina": pagina,
        "conteos": {
            "preguntas": preguntas.count(), "respuestas": respuestas.count(),
            "soluciones": Pregunta.objects.filter(visible=True, mejor_respuesta__autor=usuario).count(),
            "me_sirvio": Voto.objects.filter(Q(pregunta__autor=usuario) | Q(respuesta__autor=usuario)).count(),
        },
    })
