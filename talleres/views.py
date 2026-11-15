from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from cupones.models import CodigoCupon, Cupon
from django.utils import timezone
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F, FloatField, OuterRef, Subquery
from django.db.models.functions import Coalesce, Lower
from django.views.decorators.http import require_POST

from .forms import PerfilTallerForm, RegistroTallerForm, ResenaForm, SolicitudCitaForm
from . import agenda, estadisticas
from . import precios as precios_ref
from .models import Barrio, EventoDiario, FotoTaller, Marca, Resena, Servicio, SolicitudCita, Taller, TallerFavorito
from .utils import normalizar_celular, pesos


PALABRAS_MENORES = {"de", "del", "la", "el", "los", "las", "y"}


def _favoritos_de(usuario, ids):
    if not getattr(usuario, "is_authenticated", False):
        return set()
    return set(TallerFavorito.objects.filter(usuario=usuario, taller__in=ids).values_list("taller", flat=True))


def _preparar_tarjetas(talleres, usuario=None):
    """Datos extra para las tarjetas: reseñas, cupón vigente, favorito, iniciales y tono del avatar (consultas fijas)."""
    ids = [t.pk for t in talleres]
    notas = {r["taller"]: r for r in Resena.objects.filter(visible=True, taller__in=ids)
             .values("taller").annotate(prom=Avg("estrellas"), n=Count("id"))}
    con_cupon = set(Cupon.objects.disponibles().filter(taller__in=ids).values_list("taller", flat=True))
    favoritos = _favoritos_de(usuario, ids)
    for t in talleres:
        nota = notas.get(t.pk)
        t.prom = nota["prom"] if nota else None
        t.n_resenas = nota["n"] if nota else 0
        t.estrellas_pct = round((t.prom or 0) * 20)
        t.tiene_cupon = t.pk in con_cupon
        t.es_favorito = t.pk in favoritos
        servicios = list(t.servicios.all())
        t.servicios_vista, t.servicios_mas = servicios[:3], max(0, len(servicios) - 3)
        marcas = [m.nombre for m in t.marcas.all()]
        t.marcas_vista, t.marcas_mas = marcas[:3], max(0, len(marcas) - 3)
        palabras = [p for p in t.nombre.split() if p.lower() not in PALABRAS_MENORES] or [t.nombre]
        t.iniciales = "".join(p[0] for p in palabras[:2]).upper()
        t.tono = (t.pk * 47) % 360
    return talleres


def _base_talleres():
    # usuario__perfil: el logo de la tarjeta usa el avatar de la cuenta del taller (evita 2 consultas por tarjeta)
    return (Taller.objects.filter(activo=True).select_related("barrio", "usuario__perfil")
            .prefetch_related("servicios", "marcas"))


def inicio(request):
    taller = _taller_de(request) if request.user.is_authenticated else None
    if taller:  # las cuentas de taller tienen su propio inicio
        return _inicio_taller(request, taller)
    from noticias.models import Articulo
    from noticias.servicios import refrescar_si_toca
    refrescar_si_toca()
    # Noticiero: la principal es colombiana; de las internacionales, máximo dos.
    recientes = list(Articulo.objects.filter(publicado=True).exclude(categoria=Articulo.Categoria.CONSEJO)[:30])
    nacionales = [a for a in recientes if not a.internacional]
    noticias = nacionales[:1] or recientes[:1]
    internacionales = 0
    for a in recientes:
        if len(noticias) == 5:
            break
        if a in noticias or (a.internacional and internacionales == 2):
            continue
        internacionales += a.internacional
        noticias.append(a)
    motero = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    # En el inicio solo una muestra: destacados primero y luego los mejor calificados. El directorio tiene todos.
    # La base de datos elige los 4 (en vez de traer todos los talleres para mostrar solo esos).
    visibles = Q(resenas__visible=True)
    destacados = _preparar_tarjetas(list(
        _base_talleres()
        .annotate(prom_orden=Avg("resenas__estrellas", filter=visibles), n_orden=Count("resenas", filter=visibles))
        .order_by("-destacado", F("prom_orden").desc(nulls_last=True), "-n_orden", "-verificado", "nombre")[:4]
    ), request.user)
    motos_portada = list(motero.motos.select_related("linea", "linea__marca")) if motero else []
    return render(request, "talleres/inicio.html", {
        "motero": motero,
        "motos_portada": motos_portada,
        "destacados": destacados,
        "total_talleres": Taller.objects.filter(activo=True).count(),
        "barrios": Barrio.objects.filter(talleres__activo=True).distinct(),
        "servicios_rapidos": Servicio.objects.filter(talleres__activo=True).annotate(n=Count("talleres")).order_by("-n")[:6],
        "noticias": noticias or list(Articulo.objects.filter(publicado=True)[:5]),
        **_comunidad_portada(),
    })


def _comunidad_portada():
    """Próximas rodadas (1 consulta, con asistentes contados) y preguntas recientes del foro (1 consulta)."""
    from django.utils import timezone

    from foro.models import Pregunta
    from foro.rodadas import _visibles
    rodadas = list(_visibles().filter(fecha_hora__gte=timezone.now()).order_by("fecha_hora")[:3])
    preguntas = list(Pregunta.objects.filter(visible=True, rodada__isnull=True)
                     .annotate(n_resp=Count("respuestas", filter=Q(respuestas__visible=True)))
                     .order_by("-creado")[:3])
    from tramites.models import CentroCDA, TarifaSoat
    soat = TarifaSoat.objects.filter(anio=timezone.localdate().year).order_by("valor").values_list("valor", flat=True).first()
    return {"rodadas_portada": rodadas, "preguntas_portada": preguntas,
            "soat_desde": soat, "cda_total": CentroCDA.objects.filter(activo=True).count()}


ORDENES = {"recomendados": "Recomendados", "calificacion": "Mejor calificados", "resenas": "Más reseñas",
           "precio": "Menor precio", "nombre": "A–Z"}
POR_PAGINA = 8
# Criterio de cada orden (el desempate común se agrega en la vista)
ORDEN_SQL = {
    "calificacion": ["-prom_orden", "-n_orden"],
    "resenas": ["-n_orden", "-prom_orden"],
    "precio": [F("nivel_precio").asc(nulls_last=True), "-prom_orden"],  # sin precio, al final
    "nombre": [Lower("nombre")],
    "recomendados": ["-destacado", "-verificado", "-prom_orden"],
}


def directorio(request):
    """Página de talleres: búsqueda, filtros, orden, favoritos y paginación."""
    f = request.GET
    talleres = _base_talleres()
    if q := f.get("q", "").strip():
        # El filtro por servicio va en subconsulta: así no se duplican filas ni hace falta DISTINCT.
        talleres = talleres.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(barrio__nombre__icontains=q)
                                   | Q(pk__in=Taller.servicios.through.objects
                                       .filter(servicio__nombre__icontains=q).values("taller_id")))
    if f.get("barrio", "").isdigit():
        talleres = talleres.filter(barrio_id=f["barrio"])
    if f.get("servicio", "").isdigit():
        talleres = talleres.filter(servicios__id=f["servicio"])
    if f.get("marca", "").isdigit():
        talleres = talleres.filter(marcas__id=f["marca"])
    if f.get("verificados"):
        talleres = talleres.filter(verificado=True)
    solo_favoritos = bool(f.get("favoritos")) and request.user.is_authenticated
    if solo_favoritos:
        talleres = talleres.filter(favoritos__usuario=request.user)
    if f.get("cupon"):
        talleres = talleres.filter(pk__in=Cupon.objects.disponibles().filter(taller__isnull=False)
                                   .values_list("taller", flat=True))
    # Nota y número de reseñas calculados por la base de datos: ordena y pagina allí, y solo se preparan
    # las tarjetas de la página visible (antes se cargaban todos los talleres en cada visita).
    resenas = Resena.objects.filter(taller=OuterRef("pk"), visible=True).order_by().values("taller")
    talleres = talleres.annotate(
        prom_orden=Coalesce(Subquery(resenas.annotate(p=Avg("estrellas")).values("p")), 0.0, output_field=FloatField()),
        n_orden=Coalesce(Subquery(resenas.annotate(c=Count("pk")).values("c")), 0),
    )
    orden = f.get("orden") if f.get("orden") in ORDENES else "recomendados"
    talleres = talleres.order_by(*ORDEN_SQL[orden], "-destacado", "-verificado", "nombre", "pk")

    paginador = Paginator(talleres, POR_PAGINA)
    pagina = paginador.get_page(f.get("pagina"))
    pagina.object_list = _preparar_tarjetas(list(pagina.object_list), request.user)

    def sin(*claves):
        resto = f.copy()
        for c in claves + ("pagina",):
            resto.pop(c, None)
        return resto.urlencode()

    # Filtros activos como etiquetas que se pueden quitar
    activos = []
    if q:
        activos.append({"nombre": f"“{q}”", "quitar": "?" + sin("q")})
    for clave, modelo in (("barrio", Barrio), ("servicio", Servicio), ("marca", Marca)):
        if f.get(clave, "").isdigit() and (obj := modelo.objects.filter(pk=f[clave]).first()):
            activos.append({"nombre": str(obj), "quitar": "?" + sin(clave)})
    for clave, nombre in (("favoritos", "Mis favoritos"), ("verificados", "Solo verificados"), ("cupon", "Con cupón")):
        if f.get(clave) and (clave != "favoritos" or solo_favoritos):
            activos.append({"nombre": nombre, "quitar": "?" + sin(clave)})

    activos_todos = Taller.objects.filter(activo=True)
    # Mediana de precios en Medellín del servicio elegido (solo si lo publicaron 3 o más talleres)
    referencia = precios_ref.medianas_medellin(int(f["servicio"])) if f.get("servicio", "").isdigit() else []
    for r in referencia:
        r["desde_txt"], r["hasta_txt"] = pesos(r["desde"]), pesos(r["hasta"])
    return render(request, "talleres/directorio.html", {
        "referencia": referencia,
        "pagina": pagina,
        "rango": paginador.get_elided_page_range(pagina.number, on_each_side=1, on_ends=1),
        "qs_pagina": sin(),
        "qs_orden": sin("orden"),
        "filtros": f,
        "filtros_activos": activos,
        "orden": orden,
        "ordenes": ORDENES,
        "stats": {
            "total": activos_todos.count(),
            "verificados": activos_todos.filter(verificado=True).count(),
            "cupones": Cupon.objects.disponibles().filter(taller__activo=True).values("taller").distinct().count(),
        },
        "barrios": Barrio.objects.filter(talleres__activo=True).distinct(),
        "servicios": Servicio.objects.filter(talleres__activo=True).distinct(),
        "marcas": Marca.objects.filter(talleres__activo=True).distinct(),
    })


@require_POST
def favorito(request, slug):
    """Guarda o quita un taller de favoritos. Responde JSON al corazón (fetch) y redirige si no hay JavaScript."""
    taller = get_object_or_404(Taller, slug=slug, activo=True)
    es_fetch = request.headers.get("X-Requested-With") == "fetch"
    if not request.user.is_authenticated:
        entrar = f"{reverse(settings.LOGIN_URL)}?next={taller.get_absolute_url()}"
        return JsonResponse({"entrar": entrar}, status=401) if es_fetch else redirect(entrar)
    fav, creado = TallerFavorito.objects.get_or_create(usuario=request.user, taller=taller)
    if not creado:
        fav.delete()
    if es_fetch:
        return JsonResponse({"favorito": creado})
    destino = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(destino, {request.get_host()}, require_https=request.is_secure()):
        destino = taller.get_absolute_url()
    return redirect(destino)


def detalle(request, slug):
    taller = get_object_or_404(Taller.objects.select_related("barrio", "usuario__perfil").prefetch_related("servicios", "marcas"),
                               slug=slug, activo=True)
    if request.method == "GET":
        estadisticas.registrar(request, taller, EventoDiario.Tipo.VISITA)
    taller.es_favorito = bool(_favoritos_de(request.user, [taller.pk]))
    motero = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    inicial_cita = {}
    # Una sola consulta de motos: la lista sirve para el formulario y la primera para prellenar la cita.
    mis_motos = [m.nombre_completo for m in motero.motos.select_related("linea", "linea__marca")] if motero else []
    if motero:
        inicial_cita = {"nombre": motero.nombre, "telefono": motero.celular, "moto": mis_motos[0] if mis_motos else ""}
    if request.GET.get("servicio", "").isdigit():
        inicial_cita["servicio"] = request.GET["servicio"]
    cita_form = SolicitudCitaForm(taller=taller, initial=inicial_cita)
    resena_form = ResenaForm(initial={"nombre": request.user.first_name} if request.user.is_authenticated else None)
    abrir = ""

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "cita":
            cita_form = SolicitudCitaForm(request.POST, taller=taller)
            form, msg, abrir = cita_form, "¡Solicitud enviada! El taller te contactará pronto.", "cita"
        else:
            resena_form = ResenaForm(request.POST)
            form, msg, abrir = resena_form, "¡Gracias por tu reseña!", "resena"
        if form.is_valid():
            obj = form.save(commit=False)
            obj.taller = taller
            if request.user.is_authenticated:
                obj.usuario = request.user  # reseña con autor; cita para el recordatorio del día antes
            try:
                if accion == "cita" and taller.agenda_activa:
                    agenda.reservar(obj)
                    msg = (f"¡Reservaste el {obj.fecha_preferida:%d/%m} a las {_hora_texto(obj.hora)}! "
                           "El taller la confirma pronto; te recordaremos el día antes.")
                else:
                    obj.save()
            except agenda.FranjaOcupada as e:
                form.add_error("hora" if "hora" in form.fields else None, str(e))
            else:
                messages.success(request, msg)
                return redirect(taller)

    resenas = list(taller.resenas.filter(visible=True))
    reparto = {n: 0 for n in range(5, 0, -1)}
    for r in resenas:
        reparto[r.estrellas] += 1
    # La nota media sale de las reseñas ya cargadas (evita otra consulta en la plantilla).
    taller.calificacion = sum(r.estrellas for r in resenas) / len(resenas) if resenas else None
    fotos = list(taller.fotos.all())
    precios = [{"servicio": p.servicio.nombre, "cilindraje": p.get_cilindraje_display() if p.cilindraje else "",
                "desde": pesos(p.desde), "hasta": pesos(p.hasta)} for p in taller.precios.select_related("servicio")]
    cupones = Cupon.objects.disponibles().con_nota_taller().filter(Q(taller=taller) | Q(taller__isnull=True))
    # Numeración de las secciones según las que existan, para que siempre sea 01, 02, 03…
    nombres = ["sobre", "servicios"] + (["fotos"] if fotos else []) + (["cupones"] if cupones else []) + ["resenas"]
    numeros = {n: f"{i:02d}" for i, n in enumerate(nombres, start=1)}
    return render(request, "talleres/detalle.html", {
        "taller": taller,
        "resenas": resenas,
        "reparto": [(n, c, round(c * 100 / len(resenas)) if resenas else 0) for n, c in reparto.items()],
        "fotos": fotos,
        "precios": precios,
        "cupones": cupones,
        "numeros": numeros,
        "cita_form": cita_form,
        "resena_form": resena_form,
        "abrir": abrir,
        "mis_motos": mis_motos,
        "es_mio": request.user.is_authenticated and getattr(request.user, "taller", None) == taller,
    })


@login_required
def editar_perfil(request):
    """El taller arma su perfil: descripción, horario, servicios, marcas, portada y galería."""
    taller = getattr(request.user, "taller", None)
    if not taller:
        messages.info(request, "Esta sección es para cuentas de taller.")
        return redirect("cuentas:mi_cuenta")
    form = PerfilTallerForm(request.POST or None, request.FILES or None, instance=taller)
    if request.method == "POST":
        nuevas = request.FILES.getlist("galeria")
        libres = FotoTaller.MAXIMO - taller.fotos.count()
        errores_fotos = []
        if len(nuevas) > libres:
            errores_fotos.append(f"Puedes tener máximo {FotoTaller.MAXIMO} fotos; te quedan {max(libres, 0)}.")
        for f in nuevas:
            if f.size > 5 * 1024 * 1024 or (f.content_type or "") not in ("image/jpeg", "image/png", "image/webp"):
                errores_fotos.append(f"«{f.name}» no se subió: usa JPG, PNG o WEBP de máximo 5 MB.")
        if form.is_valid() and not errores_fotos:
            form.save()
            for i, f in enumerate(nuevas):
                FotoTaller.objects.create(taller=taller, imagen=f, orden=taller.fotos.count() + i)
            messages.success(request, "¡Perfil actualizado!")
            return redirect("talleres:editar_perfil")
        for e in errores_fotos:
            messages.error(request, e)
    return render(request, "talleres/editar_perfil.html", {
        "form": form, "taller": taller, "fotos": taller.fotos.all(), "maximo": FotoTaller.MAXIMO,
    })


@login_required
@require_POST
def eliminar_foto(request, pk):
    foto = get_object_or_404(FotoTaller, pk=pk, taller__usuario=request.user)
    foto.imagen.delete(save=False)
    foto.delete()
    messages.success(request, "Foto eliminada.")
    return redirect("talleres:editar_perfil")


def registro(request):
    # Los talleres ahora se registran con cuenta propia (rol "taller").
    return redirect(reverse("cuentas:registro") + "?tipo=taller")



# ---------------- Páginas legales ----------------
PAGINAS_LEGALES = {
    "terminos": "Términos y condiciones",
    "privacidad": "Política de tratamiento de datos personales",
    "cupones": "Condiciones de los cupones",
    "cookies": "Política de cookies",
}


def legal(request, pagina):
    from django.conf import settings
    from django.http import Http404

    if pagina not in PAGINAS_LEGALES:
        raise Http404
    return render(request, f"legal/{pagina}.html", {
        "pagina": pagina, "titulo_legal": PAGINAS_LEGALES[pagina], "paginas_legales": PAGINAS_LEGALES,
        "legal": settings.LEGAL,
    })


# ---------------- Panel del taller ----------------
def _volver(request, defecto):
    """Después de una acción, vuelve a la página desde donde se hizo (si es de este sitio)."""
    destino = request.POST.get("volver", "")
    if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}, require_https=request.is_secure()):
        return destino
    return defecto


def _taller_de(request):
    return getattr(request.user, "taller", None)


def _completitud(taller):
    """Qué le falta al perfil para verse completo en el directorio."""
    puntos = [
        ("Foto principal", bool(taller.foto)),
        ("Fotos del taller", taller.fotos.exists()),
        ("Descripción", len(taller.descripcion.strip()) >= 40),
        ("Horario", bool(taller.horario.strip())),
        ("Servicios", taller.servicios.exists()),
        ("Marcas que atiendes", taller.marcas.exists()),
        ("Rango de precios", taller.nivel_precio is not None),
    ]
    hechos = sum(ok for _, ok in puntos)
    return {"pct": round(hechos * 100 / len(puntos)), "faltan": [n for n, ok in puntos if not ok]}


def _hora_texto(h):
    return f"{h.hour % 12 or 12}:{h.minute:02d} {'a. m.' if h.hour < 12 else 'p. m.'}" if h else ""


def _whatsapp_cita(cita, taller, request=None):
    try:
        numero = normalizar_celular(cita.telefono)
    except Exception:
        return ""
    servicio = f" para {cita.servicio.nombre.lower()}" if cita.servicio else ""
    if cita.estado == SolicitudCita.Estado.REPROGRAMADA and cita.fecha_propuesta and request is not None:
        cuando = cita.fecha_propuesta.strftime("%d/%m") + (f" a las {_hora_texto(cita.hora_propuesta)}" if cita.hora_propuesta else "")
        enlace = request.build_absolute_uri(reverse("talleres:cita_publica", args=[cita.token]))
        texto = (f"Hola {cita.nombre}, te escribimos de {taller.nombre}. Para tu cita{servicio} te proponemos el {cuando}."
                 f"{' ' + cita.nota_taller if cita.nota_taller else ''} Confírmanos aquí: {enlace}")
    else:
        texto = (f"Hola {cita.nombre}, te escribimos de {taller.nombre} por tu solicitud de cita{servicio} "
                 f"el {cita.fecha_preferida.strftime('%d/%m')}.")
    return f"https://wa.me/{numero}?text={quote(texto)}"


ORDEN_CITAS = {SolicitudCita.Estado.PENDIENTE: 0, SolicitudCita.Estado.REPROGRAMADA: 1, SolicitudCita.Estado.CONFIRMADA: 2,
               SolicitudCita.Estado.ATENDIDA: 3, SolicitudCita.Estado.CANCELADA: 4}
ABIERTAS = [SolicitudCita.Estado.PENDIENTE, SolicitudCita.Estado.REPROGRAMADA, SolicitudCita.Estado.CONFIRMADA]
CITAS_PANEL, RESENAS_PANEL = 6, 4


def _nota(resenas):
    nota = resenas.aggregate(prom=Avg("estrellas"), n=Count("id"))
    nota["pct"] = round((nota["prom"] or 0) * 20)
    return nota


@login_required
def panel(request):
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    hoy = timezone.localdate()
    citas = list(taller.solicitudes.select_related("servicio")[:60])
    for c in citas:
        c.whatsapp_url = _whatsapp_cita(c, taller, request)
        c.vencida = c.estado == SolicitudCita.Estado.PENDIENTE and c.fecha_preferida < hoy
    citas.sort(key=lambda c: (ORDEN_CITAS[c.estado], c.fecha_preferida))
    abiertas = [c for c in citas if c.estado in ABIERTAS]
    resenas = taller.resenas.filter(visible=True)
    nota = _nota(resenas)
    from cuentas.avatares import PREDISENADOS, svg_predisenado
    from cuentas.models import Perfil
    return render(request, "talleres/panel.html", {
        "taller": taller,
        "perfil": Perfil.de(request.user),
        "avatares": [(clave, datos[0], svg_predisenado(clave, 52)) for clave, datos in PREDISENADOS.items()],
        "completitud": _completitud(taller),
        "citas": abiertas[:CITAS_PANEL],
        "n_abiertas": len(abiertas),
        "n_pendientes": sum(c.estado == SolicitudCita.Estado.PENDIENTE for c in citas),
        "n_citas_total": len(citas),
        # Primero las que faltan por responder; el resto está en la página de reseñas
        "resenas": sorted(resenas.order_by("-creado")[:20], key=lambda r: bool(r.respuesta))[:RESENAS_PANEL],
        "sin_responder": resenas.filter(respuesta="").count(),
        "nota": nota,
        "favoritos": taller.favoritos.count(),
        "canjes_mes": CodigoCupon.objects.filter(canjeado_taller=taller, canjeado_en__date__gte=hoy.replace(day=1)).count(),
        "cupones": taller.cupones.annotate(entregados=Count("codigos", distinct=True),
                                           canjeados=Count("codigos", filter=Q(codigos__canjeado_en__isnull=False), distinct=True),
                                           num_emitidos=F("entregados"))  # Cupon.restantes lo reutiliza sin consultar
                   .order_by("-activo", "-creado")[:8],
        "estados": SolicitudCita.Estado,
        "hoy": timezone.localdate(),
        "horas": [f"{h:02d}:{m:02d}" for h in range(6, 21) for m in (0, 30)],
    })


@login_required
@require_POST
def cambiar_estado_cita(request, pk):
    taller = _taller_de(request)
    cita = get_object_or_404(SolicitudCita, pk=pk, taller=taller)
    estado = request.POST.get("estado")
    if estado == SolicitudCita.Estado.CANCELADA:
        cita.estado = estado
        cita.motivo_cancelacion = request.POST.get("motivo", "").strip()[:200]
        cita.save(update_fields=["estado", "motivo_cancelacion"])
        canales = _avisar_motero(
            cita, f"cita-cancelada:{cita.pk}", f"{taller.nombre} canceló tu cita",
            cita.motivo_cancelacion or f"Tu cita del {cita.fecha_preferida:%d/%m} fue cancelada.", taller.get_absolute_url(),
            settings.WHATSAPP_PLANTILLA_CANCELAR,
            [cita.nombre, taller.nombre, cita.fecha_preferida.strftime("%d/%m"), cita.motivo_cancelacion or "sin motivo"])
        messages.success(request, f"Cancelaste la cita de {cita.nombre}." + (f" Le avisamos por {' y '.join(canales)}." if canales else ""))
    elif estado in SolicitudCita.Estado.values:
        cita.estado = estado
        cita.save(update_fields=["estado"])
        messages.success(request, f"Cita de {cita.nombre}: {cita.get_estado_display().lower()}.")
    return redirect(_volver(request, reverse("talleres:panel") + "#citas"))


@login_required
@require_POST
def responder_resena(request, pk):
    taller = _taller_de(request)
    resena = get_object_or_404(Resena, pk=pk, taller=taller)
    texto = request.POST.get("respuesta", "").strip()[:600]
    resena.respuesta = texto
    resena.respondida_en = timezone.now() if texto else None
    resena.save(update_fields=["respuesta", "respondida_en"])
    messages.success(request, "Respuesta publicada en tu página." if texto else "Quitamos tu respuesta.")
    return redirect(_volver(request, reverse("talleres:panel") + "#resenas"))


@login_required
def cupon_taller(request, pk=None):
    """Crear o editar un cupón del propio taller."""
    from cupones.forms import CuponTallerForm
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    cupon = get_object_or_404(Cupon, pk=pk, taller=taller) if pk else None
    form = CuponTallerForm(request.POST or None, instance=cupon)
    if request.method == "POST" and form.is_valid():
        nuevo = form.save(commit=False)
        nuevo.taller = taller
        if not cupon:  # los del taller son públicos (sin premios ni regalos; "solo Plus" lo elige el taller)
            nuevo.publico, nuevo.premio_referido, nuevo.regalo_mensual = True, False, False
        nuevo.save()
        messages.success(request, "Cupón publicado: ya aparece en tu página y en la lista de cupones." if not cupon else "Cupón actualizado.")
        return redirect(reverse("talleres:panel") + "#cupones")
    return render(request, "talleres/cupon_form.html", {"form": form, "cupon": cupon, "taller": taller})


@login_required
@require_POST
def pausar_cupon(request, pk):
    taller = _taller_de(request)
    cupon = get_object_or_404(Cupon, pk=pk, taller=taller)
    cupon.activo = not cupon.activo
    cupon.save(update_fields=["activo"])
    messages.success(request, "Cupón activado." if cupon.activo else "Cupón pausado: ya no se entrega (los que ya tienen los moteros siguen sirviendo hasta su fecha).")
    return redirect(reverse("talleres:panel") + "#cupones")


def _inicio_taller(request, taller, noticias=None):
    """Inicio de una cuenta de taller: hoy, la semana, la agenda por días, el mes y accesos rápidos."""
    from datetime import timedelta
    from foro.models import Pregunta
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    abiertas = list(taller.solicitudes.select_related("servicio")
                    .filter(estado__in=ABIERTAS,
                            fecha_preferida__gte=hoy - timedelta(days=7))
                    .order_by("fecha_preferida", "creado"))
    for c in abiertas:
        c.whatsapp_url = _whatsapp_cita(c, taller, request)
    # Agenda: hoy, mañana y el resto de la semana (las pendientes de días pasados van aparte)
    dias = {}
    for c in abiertas:
        if c.fecha_preferida < hoy:
            clave = "atrasadas"
        elif c.fecha_preferida == hoy:
            clave = "hoy"
        elif c.fecha_preferida == hoy + timedelta(days=1):
            clave = "manana"
        else:
            clave = "despues"
        dias.setdefault(clave, []).append(c)
    agenda = [(clave, titulo, dias[clave]) for clave, titulo in
              (("atrasadas", "Fecha pasada sin cerrar"), ("hoy", "Hoy"), ("manana", "Mañana"), ("despues", "Próximos días"))
              if dias.get(clave)]
    nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    semana = [{"fecha": hoy + timedelta(days=n), "dia": nombres[(hoy + timedelta(days=n)).weekday()],
               "n": sum(c.fecha_preferida == hoy + timedelta(days=n) for c in abiertas)} for n in range(7)]
    resenas = taller.resenas.filter(visible=True)
    preguntas = (Pregunta.objects.filter(visible=True)
                 .filter(Q(marca__in=taller.marcas.all()) | Q(marca__isnull=True))
                 .exclude(autor=request.user).exclude(respuestas__autor=request.user)
                 .annotate(n_respuestas=Count("respuestas", filter=Q(respuestas__visible=True)))
                 .order_by("n_respuestas", "-creado").distinct()[:3])
    hora = timezone.localtime().hour
    return render(request, "talleres/inicio_taller.html", {
        "taller": taller,
        "hoy": hoy,
        "saludo": "Buenos días" if hora < 12 else "Buenas tardes" if hora < 19 else "Buenas noches",
        "completitud": _completitud(taller),
        "agenda": agenda,
        "semana": semana,
        "max_semana": max([d["n"] for d in semana] + [1]),
        "citas_hoy": len(dias.get("hoy", [])),
        "n_pendientes": sum(c.estado == SolicitudCita.Estado.PENDIENTE for c in abiertas),
        "sin_responder": resenas.filter(respuesta="").count(),
        "ultima_resena": resenas.filter(respuesta="").first(),
        "nota": resenas.aggregate(prom=Avg("estrellas"), n=Count("id")),
        "mes": {
            "atendidas": taller.solicitudes.filter(estado=SolicitudCita.Estado.ATENDIDA, fecha_preferida__gte=inicio_mes).count(),
            "solicitudes": taller.solicitudes.filter(creado__date__gte=inicio_mes).count(),
            "resenas": resenas.filter(creado__date__gte=inicio_mes).count(),
            "canjes": CodigoCupon.objects.filter(canjeado_taller=taller, canjeado_en__date__gte=inicio_mes).count(),
        },
        "cupones_activos": taller.cupones.vigentes().count(),
        "favoritos": taller.favoritos.count(),
        "preguntas": preguntas,
    })


def _avisar_motero(cita, clave, titulo, texto, url, plantilla, parametros):
    """Le avisa al motero de la cita: en TallerYa (si tiene cuenta con ese celular) y por WhatsApp (envío automático).
    Devuelve los canales por los que salió."""
    from cupones.models import Motociclista
    from garaje.whatsapp import enviar_plantilla
    canales = []
    try:
        numero = normalizar_celular(cita.telefono)
    except Exception:
        return canales
    moto = Motociclista.objects.filter(celular=numero, usuario__isnull=False).select_related("usuario").first()
    if moto:
        _avisar(moto.usuario, clave, titulo, texto, url)
        canales.append("TallerYa")
    if enviar_plantilla(numero, plantilla, parametros):
        canales.append("WhatsApp")
    return canales


def _avisar(usuario, clave, titulo, texto, url):
    if not usuario:
        return
    from notificaciones.servicios import notificar
    notificar(usuario, clave, titulo, texto, url)


@login_required
@require_POST
def reprogramar_cita(request, pk):
    """El taller propone otra fecha (y hora). El motero la acepta o la rechaza desde un enlace."""
    import secrets
    from datetime import date as fecha_tipo, time
    taller = _taller_de(request)
    cita = get_object_or_404(SolicitudCita, pk=pk, taller=taller)
    try:
        fecha = fecha_tipo.fromisoformat(request.POST.get("fecha", ""))
    except ValueError:
        fecha = None
    if not fecha or fecha < timezone.localdate():
        messages.error(request, "Elige una fecha de hoy en adelante para reprogramar.")
        return redirect(reverse("talleres:panel") + "#citas")
    try:
        hora = time.fromisoformat(request.POST.get("hora", ""))
    except ValueError:
        messages.error(request, "Elige la hora que le propones al motero.")
        return redirect(_volver(request, reverse("talleres:panel") + "#citas"))
    cita.fecha_propuesta, cita.hora_propuesta = fecha, hora
    cita.nota_taller = request.POST.get("nota", "").strip()[:200]
    cita.estado, cita.propuesta_rechazada = SolicitudCita.Estado.REPROGRAMADA, False
    cita.token = cita.token or secrets.token_urlsafe(16)
    cita.save()
    enlace = request.build_absolute_uri(reverse("talleres:cita_publica", args=[cita.token]))
    canales = _avisar_motero(
        cita, f"cita-reprogramada:{cita.pk}:{cita.fecha_propuesta}:{cita.hora_propuesta}",
        f"{taller.nombre} te propone otra fecha", f"Para tu cita: {fecha:%d/%m} · {_hora_texto(hora)}. Acéptala o recházala.",
        reverse("talleres:cita_publica", args=[cita.token]),
        settings.WHATSAPP_PLANTILLA_REPROGRAMAR, [cita.nombre, taller.nombre, fecha.strftime("%d/%m"), _hora_texto(hora), enlace])
    via = f" por {' y '.join(canales)}" if canales else ""
    messages.success(request, f"Le enviamos la propuesta a {cita.nombre}{via}. La cita queda en espera hasta que la acepte; "
                              "te avisaremos cuando responda.")
    return redirect(_volver(request, reverse("talleres:panel")) .split("#")[0] + f"#cita-{cita.pk}")


def cita_publica(request, token):
    """Página del motero para aceptar o rechazar la nueva fecha que propone el taller (no necesita cuenta)."""
    cita = get_object_or_404(SolicitudCita.objects.select_related("taller", "servicio", "taller__barrio"), token=token)
    pendiente = cita.estado == SolicitudCita.Estado.REPROGRAMADA and cita.fecha_propuesta
    if request.method == "POST" and pendiente:
        dueno = cita.taller.usuario
        if request.POST.get("accion") == "aceptar":
            cita.fecha_preferida, cita.hora = cita.fecha_propuesta, cita.hora_propuesta
            cita.estado = SolicitudCita.Estado.CONFIRMADA
            cita.fecha_propuesta = cita.hora_propuesta = None
            cita.save()
            _avisar(dueno, f"cita-aceptada:{cita.pk}:{cita.fecha_preferida}", f"{cita.nombre} aceptó la nueva fecha",
                    f"Cita confirmada para el {cita.fecha_preferida:%d/%m}", reverse("talleres:panel") + "#citas")
            messages.success(request, "¡Listo! Tu cita quedó confirmada con la nueva fecha.")
        else:
            cita.estado, cita.propuesta_rechazada = SolicitudCita.Estado.PENDIENTE, True
            cita.save(update_fields=["estado", "propuesta_rechazada"])
            _avisar(dueno, f"cita-rechazada:{cita.pk}:{cita.fecha_propuesta}", f"{cita.nombre} no puede en la nueva fecha",
                    "Escríbele para acordar otra", reverse("talleres:panel") + "#citas")
            messages.info(request, "Le avisamos al taller que esa fecha no te sirve. Te escribirán para acordar otra.")
        return redirect("talleres:cita_publica", token=token)
    return render(request, "talleres/cita_publica.html", {"cita": cita, "pendiente": pendiente,
                                                          "hora_propuesta": _hora_texto(cita.hora_propuesta),
                                                          "hora": _hora_texto(cita.hora)})


FILTROS_CITAS = [("abiertas", "Por atender"), ("confirmada", "Confirmadas"), ("reprogramada", "Esperando al motero"),
                 ("atendida", "Atendidas"), ("cancelada", "Canceladas"), ("todas", "Todas")]


@login_required
def citas_taller(request):
    """Todas las citas del taller: por estado, búsqueda por nombre o moto y páginas de 15."""
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    filtro = request.GET.get("estado", "abiertas")
    if filtro not in dict(FILTROS_CITAS):
        filtro = "abiertas"
    citas = taller.solicitudes.select_related("servicio")
    # Todos los conteos en una sola consulta
    conteos = citas.order_by().aggregate(
        abiertas=Count("pk", filter=Q(estado__in=ABIERTAS)), todas=Count("pk"),
        **{e: Count("pk", filter=Q(estado=e)) for e in SolicitudCita.Estado.values})
    if filtro == "abiertas":
        citas = citas.filter(estado__in=ABIERTAS).order_by("fecha_preferida")
    elif filtro != "todas":
        citas = citas.filter(estado=filtro).order_by("-fecha_preferida")
    else:
        citas = citas.order_by("-fecha_preferida")
    if q := request.GET.get("q", "").strip():
        citas = citas.filter(Q(nombre__icontains=q) | Q(moto__icontains=q) | Q(telefono__icontains=q))
    pagina = Paginator(citas, 15).get_page(request.GET.get("pagina"))
    hoy = timezone.localdate()
    for c in pagina:
        c.whatsapp_url = _whatsapp_cita(c, taller, request)
        c.vencida = c.estado == SolicitudCita.Estado.PENDIENTE and c.fecha_preferida < hoy
    return render(request, "talleres/citas_taller.html", {
        "taller": taller, "pagina": pagina, "filtro": filtro, "q": q,
        "filtros": [(clave, nombre, conteos.get(clave, 0)) for clave, nombre in FILTROS_CITAS],
        "hoy": hoy, "horas": [f"{h:02d}:{m:02d}" for h in range(6, 21) for m in (0, 30)],
    })


@login_required
def resenas_taller(request):
    """Todas las reseñas del taller: sin responder o todas, filtro por estrellas y páginas de 10."""
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    todas = taller.resenas.filter(visible=True)
    filtro = request.GET.get("ver", "todas")
    resenas = todas.filter(respuesta="") if filtro == "sin_responder" else todas
    estrellas = request.GET.get("estrellas", "")
    if estrellas in {"1", "2", "3", "4", "5"}:
        resenas = resenas.filter(estrellas=int(estrellas))
    reparto = {r["estrellas"]: r["n"] for r in todas.values("estrellas").annotate(n=Count("id"))}
    nota = _nota(todas)
    return render(request, "talleres/resenas_taller.html", {
        "taller": taller, "pagina": Paginator(resenas.order_by("-creado"), 10).get_page(request.GET.get("pagina")),
        "filtro": filtro, "estrellas": estrellas, "nota": nota, "sin_responder": todas.filter(respuesta="").count(),
        "reparto": [(e, reparto.get(e, 0), round(reparto.get(e, 0) * 100 / nota["n"]) if nota["n"] else 0) for e in (5, 4, 3, 2, 1)],
    })


class _RedireccionContacto(HttpResponseRedirect):
    allowed_schemes = ["https", "tel"]


def ir(request, slug, canal):
    """Cuenta el clic (sin datos personales) y lleva a WhatsApp o a la llamada."""
    taller = get_object_or_404(Taller.objects.only("pk", "nombre", "whatsapp", "usuario_id"), slug=slug, activo=True)
    if canal == "whatsapp":
        estadisticas.registrar(request, taller, EventoDiario.Tipo.WHATSAPP)
        return _RedireccionContacto(taller.whatsapp_url)
    estadisticas.registrar(request, taller, EventoDiario.Tipo.LLAMADA)
    return _RedireccionContacto(f"tel:+{taller.whatsapp}")


@login_required
def estadisticas_taller(request):
    """Panel del taller: visitas, contactos, canjes y reseñas del mes contra el mes anterior."""
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    datos = estadisticas.resumen(taller, timezone.localdate())
    return render(request, "talleres/estadisticas.html", {
        "taller": taller, **datos,
        "plus": estadisticas.PLUS_TALLER, "es_plus": estadisticas.tiene_plus_taller(taller),
        "url_servicio_verificado": reverse("talleres:registrar_servicio"),
    })


@login_required
def registrar_servicio(request):
    """El taller registra un servicio verificado en la hoja de vida de una moto, con el código que le muestra
    el motero (QR o 6 caracteres). Modelo, formulario y reglas viven en garaje; aquí solo va la pantalla."""
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    try:
        from garaje.forms_hoja_vida import ServicioTallerForm
    except ImportError:
        ServicioTallerForm = None
    form = None
    if ServicioTallerForm:
        if request.method == "POST":
            form = ServicioTallerForm(request.POST, taller=taller)
            if form.is_valid() and form.guardar():
                messages.success(request, "Registrado y verificado en la hoja de vida de la moto.")
                return redirect("talleres:registrar_servicio")
        else:
            form = ServicioTallerForm(taller=taller, initial={"codigo": request.GET.get("codigo", "").strip()[:12],
                                                               "fecha": timezone.localdate()})
    return render(request, "talleres/registrar_servicio.html", {
        "taller": taller, "form": form, "moto": getattr(getattr(form, "codigo_obj", None), "moto", None)})


def franjas(request, slug):
    """Horarios libres de un día (JSON) para el formulario de cita."""
    from datetime import date
    taller = get_object_or_404(Taller.objects.only("pk", "duracion_franja", "cupo_franja", "agenda_activa"), slug=slug, activo=True)
    try:
        fecha = date.fromisoformat(request.GET.get("fecha", ""))
    except ValueError:
        return JsonResponse({"franjas": []}, status=400)
    libres = agenda.franjas_libres(taller, fecha) if taller.agenda_activa else []
    return JsonResponse({"franjas": [{"hora": h.strftime("%H:%M"), "texto": _hora_texto(h), "libres": n} for h, n in libres]})


@login_required
def agenda_taller(request):
    """El taller define su horario por días (hasta dos turnos), la duración de la franja y el cupo."""
    from .forms import AgendaForm, leer_turnos
    from .models import DIAS_SEMANA
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    form = AgendaForm(request.POST or None, instance=taller)
    errores = []
    if request.method == "POST":
        turnos, errores = leer_turnos(request.POST)
        if form.is_valid() and not errores:
            if form.cleaned_data["agenda_activa"] and not turnos:
                errores.append("Para recibir reservas por franjas, escribe al menos un turno.")
            else:
                form.save()
                agenda.guardar_turnos(taller, turnos)
                messages.success(request, "Guardamos tu agenda y tu horario.")
                return redirect("talleres:agenda")
    por_dia = agenda.turnos_por_dia(taller)
    dias = []
    for dia, nombre in DIAS_SEMANA:
        t = por_dia.get(dia, [])

        def valor(n, campo, dia=dia, t=t):
            if request.method == "POST":
                return request.POST.get(f"d{dia}_{n}_{campo}", "")
            return getattr(t[n - 1], campo).strftime("%H:%M") if len(t) >= n else ""
        dias.append({"dia": dia, "nombre": nombre, "turnos": [(n, valor(n, "abre"), valor(n, "cierra")) for n in (1, 2)]})
    return render(request, "talleres/agenda.html", {"taller": taller, "form": form, "dias": dias, "errores": errores})


@login_required
def precios_taller(request):
    """El taller publica rangos "desde–hasta" por servicio (cilindraje opcional)."""
    from .forms import precios_formset
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    Formset = precios_formset(taller)
    formset = Formset(request.POST or None, instance=taller, queryset=taller.precios.select_related("servicio"))
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, "Guardamos tus precios de referencia.")
        return redirect("talleres:precios")
    return render(request, "talleres/precios.html", {"taller": taller, "formset": formset,
                                                     "sin_servicios": not taller.servicios.exists()})


def emergencias(request):
    """Flujo "¿Te varaste?": el motero elige qué le pasó y ve quién lo atiende, abiertos ahora primero. La cercanía se
    calcula en el navegador con su ubicación (nunca se envía al servidor); si no la da, elige su barrio."""
    from . import emergencias as em
    from .models import Grua
    ahora = timezone.localtime()
    necesito = request.GET.get("necesito")
    necesito = necesito if necesito in em.OPCIONES else None
    filtro = em.OPCIONES[necesito][1] if necesito else {}
    talleres = list(Taller.objects.filter(activo=True, atiende_emergencias=True, **filtro)
                    .select_related("barrio").prefetch_related("horarios").order_by("-abierto_24h", "nombre"))
    barrio = None
    if request.GET.get("barrio", "").isdigit():
        barrio = Barrio.objects.filter(pk=request.GET["barrio"]).first()
    talleres = em.ordenar_por_barrio(talleres, barrio)
    grupos = {True: [], None: [], False: []}
    for t in talleres:
        t.abierto = em.abierto_ahora(t, ahora, list(t.horarios.all()))
        grupos[t.abierto].append(t)
    gruas = []
    if necesito in em.CON_GRUAS:
        gruas = em.ordenar_gruas(list(Grua.objects.filter(activo=True)), barrio.ciudad if barrio else None, ahora)
        for g in gruas:
            g.tarifa_txt = pesos(g.tarifa_desde) if g.tarifa_desde else ""
    moto = None
    perfil = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    if perfil:
        moto = perfil.motos.select_related("linea", "linea__marca").first()
    return render(request, "talleres/emergencias.html", {
        "abiertos": grupos[True], "sin_horario": grupos[None], "cerrados": grupos[False],
        "barrio": barrio, "barrios": Barrio.objects.all(), "ahora": ahora,
        "opciones": [(k, txt) for k, (txt, _) in em.OPCIONES.items()], "necesito": necesito,
        "gruas": gruas, "mostrar_gruas": necesito in em.CON_GRUAS,
        "mensaje_grua": em.mensaje_grua(moto.nombre_completo if moto else None),
    })
