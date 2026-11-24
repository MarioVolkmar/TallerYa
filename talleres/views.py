import re

from consola.ajustes import ajuste
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
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

from metricas.nucleo import registrar_evento, termino_busqueda

from .forms import PerfilTallerForm, RegistroTallerForm, equipo_de, equipo_formset, ResenaForm, SolicitudCitaForm
from . import agenda, estadisticas, negocio, perfil, subidas
from . import seo as seo_
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
    from domicilio.models import TallerDomicilio  # «Servicio a domicilio» (una consulta para todas las tarjetas)
    a_domicilio = set(TallerDomicilio.objects.filter(activo=True, taller__in=ids).values_list("taller", flat=True))
    for t in talleres:
        t.va_domicilio = t.pk in a_domicilio
        nota = notas.get(t.pk)
        t.prom = nota["prom"] if nota else None
        t.n_resenas = nota["n"] if nota else 0
        t.estrellas_pct = round((t.prom or 0) * 20)
        t.tiene_cupon = t.pk in con_cupon
        t.es_favorito = t.pk in favoritos
        servicios = list(t.servicios.all())
        t.servicios_vista, t.servicios_mas = servicios[:3], max(0, len(servicios) - 3)
        marcas = [m.nombre for m in t.marcas.all()]
        t.marcas_vista, t.marcas_mas = (["Multimarca"], 0) if t.multimarca else (marcas[:3], max(0, len(marcas) - 3))
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
    from proveedores.models import Proveedor
    from tramites.models import TarifaSoat
    soat = TarifaSoat.objects.filter(anio=timezone.localdate().year).order_by("valor").values_list("valor", flat=True).first()
    return {"rodadas_portada": rodadas, "preguntas_portada": preguntas,
            "soat_desde": soat, "cda_total": Proveedor.objects.publicados("cda").count()}


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


def directorio(request, fijos=None, seo=None):
    """Página de talleres: búsqueda, filtros, orden, favoritos y paginación.

    `fijos` y `seo` los usan las páginas por barrio y servicio (talleres/seo.py): mismos filtros, texto propio."""
    f = request.GET.copy()
    for clave, valor in (fijos or {}).items():
        f[clave] = str(valor)
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
        talleres = talleres.filter(Q(multimarca=True) | Q(pk__in=Taller.marcas.through.objects.filter(marca_id=f["marca"]).values("taller_id")))
    if f.get("verificados"):
        talleres = talleres.filter(verificado=True)
    if f.get("domicilio"):  # «Servicio a domicilio»: el mismo criterio de /mecanicos/ (TallerDomicilio activo; el taller ya es activo)
        talleres = talleres.filter(domicilio__activo=True)
    solo_favoritos = bool(f.get("favoritos")) and request.user.is_authenticated
    if solo_favoritos:
        talleres = talleres.filter(favoritos__usuario=request.user)
    if q or any(f.get(k) for k in ("barrio", "servicio", "marca", "verificados", "cupon", "domicilio")):
        registrar_evento(request, "busqueda_talleres", q=termino_busqueda(q), barrio=bool(f.get("barrio")),
                         servicio=bool(f.get("servicio")), marca=bool(f.get("marca")))
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
    for clave, nombre in (("favoritos", "Mis favoritos"), ("verificados", "Solo verificados"), ("cupon", "Con cupón"),
                          ("domicilio", "Servicio a domicilio")):
        if f.get(clave) and (clave != "favoritos" or solo_favoritos):
            activos.append({"nombre": nombre, "quitar": "?" + sin(clave)})

    activos_todos = Taller.objects.filter(activo=True)
    # Mediana de precios en Medellín del servicio elegido (solo si lo publicaron 3 o más talleres)
    referencia = precios_ref.medianas_medellin(int(f["servicio"])) if ajuste("precio_tipico") and f.get("servicio", "").isdigit() else []
    for r in referencia:
        r["desde_txt"], r["hasta_txt"] = pesos(r["desde"]), pesos(r["hasta"])
    return render(request, "talleres/directorio.html", {
        "seo_pagina": seo,
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
            **activos_todos.order_by().aggregate(total=Count("pk"), verificados=Count("pk", filter=Q(verificado=True))),
            "cupones": Cupon.objects.disponibles().filter(taller__activo=True).values("taller").distinct().count(),
        } if ajuste("cifras_directorio") else None,
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


# Freno contra spam y notas infladas: reseñas y citas que alguien (con o sin cuenta) puede enviar por hora.
MAX_RESENAS_POR_HORA, MAX_CITAS_POR_HORA = 3, 5


def _claves_publicar(request, taller, accion):
    from cuentas.limites import ip_cliente
    quien = f"u{request.user.pk}" if request.user.is_authenticated else ip_cliente(request)
    if accion == "cita":
        return f"citas:{quien}", MAX_CITAS_POR_HORA
    return f"resenas:{taller.pk}:{quien}", MAX_RESENAS_POR_HORA


def _bloqueo_publicar(request, taller, accion):
    """Mensaje de error si no se puede publicar la reseña o la cita; "" si sí."""
    from cuentas.limites import superado
    if accion != "cita" and request.user.is_authenticated and getattr(request.user, "taller", None) == taller:
        return "No puedes reseñar tu propio taller."
    clave, maximo = _claves_publicar(request, taller, accion)
    if superado(clave, maximo):
        return "Enviaste varias seguidas. Intenta de nuevo en un rato."
    return ""


def _contar_publicacion(request, taller, accion):
    from cuentas.limites import sumar
    sumar(_claves_publicar(request, taller, accion)[0], 3600)

def _sellar_verificada(resena, taller, usuario):
    """Reseña con sello «verificada»: el autor tiene un servicio de este taller ya verificado y aún sin reseñar."""
    from garaje.models import ServicioTaller
    usados = Resena.objects.filter(taller=taller, servicio_taller_id__isnull=False).values("servicio_taller_id")
    servicio = (ServicioTaller.objects.filter(taller=taller, estado=ServicioTaller.Estado.VERIFICADO,
                                              moto__motociclista__usuario=usuario)
                .exclude(pk__in=usados).order_by("-fecha", "-pk").first())
    if servicio:
        resena.verificada, resena.servicio_taller_id = True, servicio.pk


def _tabla_precios(taller):
    """Precios «desde» en tabla corta: una fila por servicio y una columna por cilindraje publicado."""
    from .models import CILINDRAJES

    precios = list(taller.precios.select_related("servicio"))
    usados = [c for c, _ in CILINDRAJES if any(p.cilindraje == c for p in precios)]
    cortos = {"": "Cualquier cc", "baja": "Hasta 150 cc", "media": "150–400 cc", "alta": "Más de 400 cc"}
    columnas = [(c, cortos.get(c, t)) for c, t in CILINDRAJES if c in usados]
    filas = {}
    for p in sorted(precios, key=lambda p: p.servicio.nombre):
        fila = filas.setdefault(p.servicio_id, {"pk": p.servicio_id, "servicio": p.servicio.nombre, "celdas": {}})
        fila["celdas"][p.cilindraje] = pesos(p.desde)
    for fila in filas.values():
        fila["celdas"] = [fila["celdas"].get(c, "") for c, _ in columnas]
    confirmado = min((p.actualizado for p in precios), default=None)
    return {"columnas": [t for _, t in columnas], "filas": list(filas.values()),
            "confirmado": timezone.localtime(confirmado).date() if confirmado else None}



def detalle(request, slug):
    taller = get_object_or_404(Taller.objects.select_related("barrio", "usuario__perfil").prefetch_related("servicios", "marcas", "horarios"),
                               slug=slug, activo=True)
    if request.method == "GET":
        estadisticas.registrar(request, taller, EventoDiario.Tipo.VISITA)
        registrar_evento(request, "taller_visto", taller=taller.pk)
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
    abrir = "resena" if request.GET.get("calificar") else ""  # desde el aviso "califica al taller"

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "cita":
            cita_form = SolicitudCitaForm(request.POST, taller=taller)
            form, msg, abrir = cita_form, "¡Solicitud enviada! El taller te contactará pronto.", "cita"
        else:
            resena_form = ResenaForm(request.POST)
            form, msg, abrir = resena_form, "¡Gracias por tu reseña!", "resena"
        bloqueo = _bloqueo_publicar(request, taller, accion)
        if bloqueo:
            messages.error(request, bloqueo)
            return redirect(taller)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.taller = taller
            if request.user.is_authenticated:
                obj.usuario = request.user  # reseña con autor; cita para el recordatorio del día antes
                if accion != "cita":
                    _sellar_verificada(obj, taller, request.user)
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
                _contar_publicacion(request, taller, accion)
                if accion == "cita":
                    request.session["sugerir_push"] = True  # la ficha ofrece activar avisos tras pedir la cita
                    _avisar(taller.usuario, f"cita-nueva:{obj.pk}", f"{obj.nombre} pidió una cita",
                            f"{obj.fecha_preferida:%d/%m}" + (f" a las {_hora_texto(obj.hora)}" if obj.hora else ""),
                            reverse("talleres:citas_taller"))
                messages.success(request, msg)
                return redirect(taller)

    resenas = list(taller.resenas.filter(visible=True))
    reparto = {n: 0 for n in range(5, 0, -1)}
    for r in resenas:
        reparto[r.estrellas] += 1
    # La nota media sale de las reseñas ya cargadas (evita otra consulta en la plantilla).
    taller.calificacion = sum(r.estrellas for r in resenas) / len(resenas) if resenas else None
    fotos = list(taller.fotos.all())
    tabla_precios = _tabla_precios(taller) if taller.mostrar_precios else None
    con_precio = {fila["pk"] for fila in tabla_precios["filas"]} if tabla_precios else set()
    if not taller.mostrar_precios:  # sin precios públicos: la tabla no se manda y todos los servicios van como chips
        tabla_precios, con_precio = {"columnas": [], "filas": []}, set()
    otros_servicios = [x for x in taller.servicios.all() if x.pk not in con_precio]
    cupones = Cupon.objects.disponibles().con_nota_taller().filter(Q(taller=taller) | Q(taller__isnull=True))
    equipo = perfil.equipo_limpio(taller.equipo)
    especialidades = perfil.especialidades_texto(taller.especialidades)
    marcas = [] if taller.multimarca else list(taller.marcas.all())
    compromisos = perfil.compromisos_lista(taller)
    # Numeración de las secciones según las que existan, para que siempre sea 01, 02, 03…
    nombres = ["ubicacion"] + (["equipo"] if equipo else []) + (["trabajo"] if especialidades or marcas or taller.multimarca or compromisos else [])         + (["cupones"] if cupones else []) + ["resenas"]
    numeros = {n: f"{i:02d}" for i, n in enumerate(nombres, start=1)}
    lugar = f"{taller.barrio.nombre}, {taller.barrio.ciudad}"
    servicios_txt = ", ".join(x.nombre.lower() for x in list(taller.servicios.all())[:4])
    seo_desc = (" ".join(taller.descripcion.split())[:170] + " " if taller.descripcion.strip() else "")
    seo_desc += f"Taller de motos en {lugar}." + (f" Servicios: {servicios_txt}." if servicios_txt else "")
    if especialidades:
        seo_desc += f" Especialistas en {', '.join(e.lower() for e in especialidades[:3])}."
    if taller.garantia_meses:
        seo_desc += f" Garantía de {taller.garantia_meses} mes{'es' if taller.garantia_meses > 1 else ''}."
    if resenas:
        seo_desc += f" Calificación {taller.calificacion:.1f}/5 ({len(resenas)} reseñas)."
    seo_desc += " Pide tu cita por WhatsApp."
    return render(request, "talleres/detalle.html", {
        "seo_titulo": f"{taller.nombre} · Taller de motos en {taller.barrio.nombre} · TallerYa",
        "seo_desc": seo_desc,
        "seo_img": taller.foto.url if taller.foto else "",
        "taller": taller,
        "resenas": resenas,
        "reparto": [(n, c, round(c * 100 / len(resenas)) if resenas else 0) for n, c in reparto.items()],
        "fotos": fotos,
        "tabla_precios": tabla_precios,
        "otros_servicios": otros_servicios,
        "estado_horario": perfil.estado_horario(taller, list(taller.horarios.all())),
        "equipo": equipo,
        "especialidades": especialidades,
        "marcas": marcas,
        "compromisos": compromisos,
        "cupones": cupones,
        "numeros": numeros,
        "datos_pleg": {
            "ubicacion": taller.barrio.nombre,
            "equipo": negocio.dato_cantidad(len(equipo), "persona", "personas"),
            "cupones": negocio.dato_cantidad(len(cupones), "cupón", "cupones"),
            "resenas": negocio.dato_resenas(taller.calificacion, len(resenas)),
        },
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
    # El equipo solo se toca si el formulario lo trae (un POST viejo o de otra pantalla no lo borra)
    equipo = equipo_formset(taller, request.POST if "equipo-TOTAL_FORMS" in request.POST else None)
    if request.method == "POST":
        nuevas = request.FILES.getlist("galeria")
        libres = FotoTaller.MAXIMO - taller.fotos.count()
        errores_fotos = []
        if len(nuevas) > libres:
            errores_fotos.append(f"Puedes tener máximo {FotoTaller.MAXIMO} fotos; te quedan {max(libres, 0)}.")
        for f in nuevas:  # el contenido manda: nombre y Content-Type los inventa quien sube (talleres/subidas.py)
            tipo = f.size <= 5 * 1024 * 1024 and subidas.tipo_real(f, subidas.IMAGENES)
            if not tipo:
                errores_fotos.append(f"«{f.name}» no se subió: usa JPG, PNG o WEBP de máximo 5 MB.")
            else:
                subidas.renombrar(f, tipo)
        video = request.FILES.get("video")
        if video:
            if len(nuevas) + 1 > libres:
                errores_fotos.append(f"Puedes tener máximo {FotoTaller.MAXIMO} fotos y videos; te quedan {max(libres, 0)}.")
            elif taller.fotos.exclude(video="").count() >= FotoTaller.MAXIMO_VIDEOS:
                errores_fotos.append(f"Puedes tener máximo {FotoTaller.MAXIMO_VIDEOS} videos.")
            elif video.size > 20 * 1024 * 1024 or not (tipo := subidas.tipo_real(video, subidas.VIDEOS)):
                errores_fotos.append(f"«{video.name}» no se subió: usa un video MP4 o WEBM de máximo 20 MB.")
            else:
                subidas.renombrar(video, tipo)
        equipo_ok = not equipo.is_bound or equipo.is_valid()
        if form.is_valid() and equipo_ok and not errores_fotos:
            taller = form.save(commit=False)
            if equipo.is_bound:
                taller.equipo = equipo_de(equipo)
            if not taller.activo and taller.motivo_rechazo:  # corrigió: vuelve a la fila de revisión
                taller.motivo_rechazo = ""
            taller.save()
            form.save_m2m()
            for i, f in enumerate(nuevas):
                FotoTaller.objects.create(taller=taller, imagen=f, orden=taller.fotos.count() + i)
            if video:
                FotoTaller.objects.create(taller=taller, video=video, orden=taller.fotos.count())
            messages.success(request, "¡Perfil actualizado!")
            return redirect("talleres:editar_perfil")
        for e in errores_fotos:
            messages.error(request, e)
    return render(request, "talleres/editar_perfil.html", {
        "form": form, "equipo": equipo, "completitud": _completitud(taller),
        "taller": taller, "fotos": taller.fotos.all(), "maximo": FotoTaller.MAXIMO,
        "url_alternar": reverse("talleres:alternar_precios"), "url_precios": reverse("talleres:precios"),
        "videos": taller.fotos.exclude(video="").count(), "maximo_videos": FotoTaller.MAXIMO_VIDEOS,
    })


@login_required
@require_POST
def eliminar_foto(request, pk):
    foto = get_object_or_404(FotoTaller, pk=pk, taller__usuario=request.user)
    foto.imagen.delete(save=False)
    foto.video.delete(save=False)
    foto.delete()
    messages.success(request, "Foto eliminada.")
    return redirect("talleres:editar_perfil")


def registro(request):
    # Ruta vieja: el registro de talleres es ahora el formulario corto /unete/ (sin cuenta, revisado antes de publicar).
    return redirect(reverse("talleres:autoregistro"))



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
    largo = len(taller.descripcion.strip())
    puntos = [
        ("Foto principal", bool(taller.foto)),
        ("Fotos del taller", taller.fotos.exists()),
        ("Descripción" if largo == 0 else f"Descripción (mínimo 40 caracteres: te faltan {40 - largo})", largo >= 40),
        ("Horario", bool(taller.horario.strip())),
        ("Servicios", taller.servicios.exists()),
        ("Marcas que atiendes", taller.marcas.exists()),
        ("Rango de precios", taller.nivel_precio is not None),
        ("Precios por servicio", taller.precios.exists()),
        ("Quiénes atienden", bool(perfil.equipo_limpio(taller.equipo))),
        ("Especialidades", bool(taller.especialidades)),
        ("Garantía o cómo trabajan", bool(taller.garantia_meses or taller.compromisos)),
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
CITAS_PANEL = 6




@login_required
def pin_canje(request):
    """PIN para validar cupones sin la sesión del taller. GET: si tiene y el enlace del equipo. POST: genera uno nuevo
    (el anterior deja de servir) y lo muestra una sola vez en esta respuesta (no va a mensajes ni cookies)."""
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    pin = None
    if request.method == "POST":
        pin = taller.nuevo_pin()
    enlace = request.build_absolute_uri(reverse("cupones:canjear") + f"?taller={taller.slug}")
    respuesta = render(request, "talleres/pin_canje.html", {"taller": taller, "pin": pin, "enlace": enlace})
    respuesta["Cache-Control"] = "no-store"
    return respuesta


@login_required
def panel(request):
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    hoy = timezone.localdate()
    citas = list(taller.solicitudes.select_related("servicio")[:60])
    citas.sort(key=lambda c: (ORDEN_CITAS[c.estado], c.fecha_preferida))
    abiertas = [c for c in citas if c.estado in ABIERTAS]
    resenas = taller.resenas.filter(visible=True)
    nota = negocio.nota(resenas)
    from cuentas.avatares import PREDISENADOS, svg_predisenado
    from cuentas.models import Perfil
    from garaje.servicio_taller import resumen_taller
    from . import precios as _precios
    from .panel_cifras import faltan_cortos, franja
    resumen = resumen_taller(taller, hoy)
    canjes_mes = CodigoCupon.objects.filter(canjeado_taller=taller, canjeado_en__date__gte=hoy.replace(day=1)).count()
    completitud = _completitud(taller)
    sin_responder = resenas.filter(respuesta="").count()
    tareas = negocio.tareas_comunes(
        por_responder=sum(c.estado == SolicitudCita.Estado.PENDIENTE for c in citas), url_solicitudes="#citas",
        precios_por_confirmar=_precios.necesita_confirmar(taller), url_precios=reverse("talleres:precios"),
        sin_responder=sin_responder, url_resenas="#resenas")
    if not (taller.latitud and taller.ubicacion_exacta):
        tareas.insert(len(tareas) - bool(sin_responder), negocio.tarea("Confirma la ubicación exacta de tu taller",
                                                                     reverse("talleres:editar_perfil") + "#ubicacion", "Confirmar"))
    return render(request, "talleres/panel.html", {
        "taller": taller,
        # «Por hacer» (talleres/_por_hacer.html, igual que el del mecánico)
        "tareas": tareas, "pct": completitud["pct"], "faltan_cortos": faltan_cortos(completitud["faltan"]),
        "url_perfil": reverse("talleres:editar_perfil"), "todo_al_dia": "citas", "palabra_perfil": "perfil",
        "url_alternar_precios": reverse("talleres:alternar_precios"), "mostrar_precios": taller.mostrar_precios,
        "url_precios": reverse("talleres:precios"), "url_validar": reverse("cupones:canjear"), "url_ver_cupones": "#cupones",
        "url_nuevo_cupon": reverse("talleres:cupon_nuevo"),
        "franja": franja([
            ("Citas esta semana", resumen["citas_semana"], resumen["citas_semana_ant"], "semana pasada", "",
             reverse("talleres:citas_taller") + "?estado=proximas", "lava", "Comparte tu página para recibir citas."),
            ("Servicios registrados", resumen["servicios_mes"], resumen["servicios_mes_ant"], "mes pasado", "",
             reverse("talleres:servicios_taller"), "verde", "Registra tus servicios: arman el historial de cada moto."),
            ("Calificación", f"{nota['prom']:.1f}".replace(".", ",") if nota["n"] else "", None, "",
             f"{nota['n']} reseña{'s' if nota['n'] != 1 else ''}", "#resenas", "mostaza", "Pídeles a tus clientes que te califiquen en tu página."),
            ("Cupones canjeados", canjes_mes, None, "", "este mes", "#cupones", "verde", "Crea un cupón para atraer moteros."),
            ("Te guardaron", taller.favoritos.count(), None, "", "moteros", "", "rosa", ""),
        ]),
        "n_precios": taller.precios.count(),
        "resumen": resumen,
        "perfil": Perfil.de(request.user),
        "avatares": [(clave, datos[0], svg_predisenado(clave, 52)) for clave, datos in PREDISENADOS.items()],
        "citas": negocio.tarjetas(abiertas[:CITAS_PANEL], taller, request),
        "n_abiertas": len(abiertas),
        "n_pendientes": sum(c.estado == SolicitudCita.Estado.PENDIENTE for c in citas),
        "n_citas_total": len(citas),
        # Primero las que faltan por responder; el resto está en la página de reseñas
        "resenas": negocio.resenas_panel(resenas),
        "sin_responder": sin_responder,
        "nota": nota,
        "favoritos": taller.favoritos.count(),
        "canjes_mes": canjes_mes,
        "cupones_activos": taller.cupones.vigentes().count(),
        "cupones": negocio.cupones_con_cifras(taller.cupones.all())[:8], "nombre_negocio": taller.nombre,
        "url_pin": reverse("talleres:pin_canje"),
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
    elif estado == SolicitudCita.Estado.CONFIRMADA and cita.estado != estado:
        cita.estado = estado
        cita.save(update_fields=["estado"])
        cuando = f"{cita.fecha_preferida:%d/%m}" + (f" a las {_hora_texto(cita.hora)}" if cita.hora else "")
        canales = _avisar_motero(
            cita, f"cita-confirmada:{cita.pk}:{cita.fecha_preferida}", f"{taller.nombre} confirmó tu cita",
            f"Te esperan el {cuando}.", taller.get_absolute_url(),
            settings.WHATSAPP_PLANTILLA_CONFIRMAR, [cita.nombre, taller.nombre, cuando])
        messages.success(request, f"Confirmaste la cita de {cita.nombre}." + (f" Le avisamos por {' y '.join(canales)}." if canales else ""))
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
    usuario = cita.usuario or getattr(Motociclista.objects.filter(celular=numero, usuario__isnull=False)
                                      .select_related("usuario").first(), "usuario", None)
    if usuario:
        _avisar(usuario, clave, titulo, texto, url)
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


def _pesos(n):
    return "$" + f"{n:,}".replace(",", ".")


def _entero_pesos(texto):
    """'$180.000' o '180000' → 180000; None si no es un monto válido."""
    digitos = re.sub(r"\D", "", texto or "")
    return int(digitos) if digitos and 0 < int(digitos) <= 50_000_000 else None


@login_required
@require_POST
def cotizar_cita(request, pk):
    """El taller responde la cita con un precio (rango), qué incluye, hasta cuándo vale y la fecha y hora.
    Queda «Esperando al motero» (como al reprogramar) y el motero la acepta o la rechaza desde su enlace."""
    import secrets
    from datetime import date as fecha_tipo, time, timedelta
    taller = _taller_de(request)
    cita = get_object_or_404(SolicitudCita, pk=pk, taller=taller)
    volver = _volver(request, reverse("talleres:panel") + "#citas")
    desde, hasta = _entero_pesos(request.POST.get("desde")), _entero_pesos(request.POST.get("hasta"))
    if not desde or not hasta or desde > hasta:
        messages.error(request, "Escribe el precio desde y hasta (el «hasta» no puede ser menor). Si es un precio fijo, pon el mismo en los dos.")
        return redirect(volver)
    try:
        fecha = fecha_tipo.fromisoformat(request.POST.get("fecha", ""))
        hora = time.fromisoformat(request.POST.get("hora", ""))
    except ValueError:
        fecha = hora = None
    if not fecha or not hora or fecha < timezone.localdate():
        messages.error(request, "Elige la fecha (de hoy en adelante) y la hora para la cita.")
        return redirect(volver)
    dias = request.POST.get("vigencia", "5")
    dias = int(dias) if dias.isdigit() and 1 <= int(dias) <= 30 else 5
    cita.cotizacion_desde, cita.cotizacion_hasta = desde, hasta
    cita.cotizacion_incluye = request.POST.get("incluye", "").strip()[:160]
    cita.cotizacion_vence = timezone.localdate() + timedelta(days=dias)
    cita.fecha_propuesta, cita.hora_propuesta = fecha, hora
    cita.nota_taller = request.POST.get("nota", "").strip()[:200]
    cita.estado, cita.propuesta_rechazada = SolicitudCita.Estado.REPROGRAMADA, False
    cita.token = cita.token or secrets.token_urlsafe(16)
    cita.save()
    precio = _pesos(desde) if desde == hasta else f"{_pesos(desde)} a {_pesos(hasta)}"
    enlace = request.build_absolute_uri(reverse("talleres:cita_publica", args=[cita.token]))
    canales = _avisar_motero(
        cita, f"cita-cotizada:{cita.pk}:{desde}:{hasta}:{fecha}:{hora}", f"{taller.nombre} te cotizó",
        f"{precio} · {fecha:%d/%m} · {_hora_texto(hora)}. Acéptala o recházala.",
        reverse("talleres:cita_publica", args=[cita.token]),
        getattr(settings, "WHATSAPP_PLANTILLA_COTIZACION", "cita_cotizada"),
        [cita.nombre, taller.nombre, precio, fecha.strftime("%d/%m"), _hora_texto(hora), enlace])
    via = f" por {' y '.join(canales)}" if canales else ""
    messages.success(request, f"Le enviamos la cotización a {cita.nombre}{via}. Te avisaremos cuando responda.")
    return redirect(volver.split("#")[0] + f"#cita-{cita.pk}")


def cita_publica(request, token):
    """Página del motero para aceptar o rechazar la nueva fecha que propone el taller (no necesita cuenta)."""
    cita = get_object_or_404(SolicitudCita.objects.select_related("taller", "servicio", "taller__barrio"), token=token)
    pendiente = cita.estado == SolicitudCita.Estado.REPROGRAMADA and cita.fecha_propuesta
    cotizada = bool(cita.cotizacion_hasta)
    if request.method == "POST" and pendiente:
        dueno = cita.taller.usuario
        if request.POST.get("accion") == "aceptar" and cotizada and cita.cotizacion_vencida:
            messages.error(request, "Esta cotización ya venció. Escríbele al taller para que te envíe una nueva.")
        elif request.POST.get("accion") == "aceptar":
            cita.fecha_preferida, cita.hora = cita.fecha_propuesta, cita.hora_propuesta
            cita.estado = SolicitudCita.Estado.CONFIRMADA
            cita.fecha_propuesta = cita.hora_propuesta = None
            cita.save()
            que = "la cotización" if cotizada else "la nueva fecha"
            _avisar(dueno, f"cita-aceptada:{cita.pk}:{cita.fecha_preferida}", f"{cita.nombre} aceptó {que}",
                    f"Cita confirmada para el {cita.fecha_preferida:%d/%m}", reverse("talleres:panel") + "#citas")
            messages.success(request, f"¡Listo! Tu cita quedó confirmada{' con ese precio' if cotizada else ' con la nueva fecha'}.")
        else:
            cita.estado, cita.propuesta_rechazada = SolicitudCita.Estado.PENDIENTE, True
            cita.save(update_fields=["estado", "propuesta_rechazada"])
            titulo = f"{cita.nombre} no aceptó la cotización" if cotizada else f"{cita.nombre} no puede en la nueva fecha"
            _avisar(dueno, f"cita-rechazada:{cita.pk}:{cita.fecha_propuesta}", titulo,
                    "Escríbele para acordar otra opción", reverse("talleres:panel") + "#citas")
            messages.info(request, "Le avisamos al taller. Te escribirán si tienen otra opción.")
        return redirect("talleres:cita_publica", token=token)
    precio = ""
    if cotizada:
        desde, hasta = cita.cotizacion_desde, cita.cotizacion_hasta
        precio = _pesos(hasta) if desde == hasta else f"{_pesos(desde)} – {_pesos(hasta)}"
    return render(request, "talleres/cita_publica.html", {"cita": cita, "pendiente": pendiente, "precio": precio,
                                                          "hora_propuesta": _hora_texto(cita.hora_propuesta),
                                                          "hora": _hora_texto(cita.hora)})


FILTROS_CITAS = [("hoy", "Hoy"), ("proximas", "Próximas"), ("pasadas", "Pasadas"), ("abiertas", "Por atender"), ("confirmada", "Confirmadas"), ("reprogramada", "Esperando al motero"),
                 ("atendida", "Atendidas"), ("cancelada", "Canceladas"), ("todas", "Todas")]


@login_required
def citas_taller(request):
    """Todas las citas del taller: por estado, búsqueda por nombre o moto y páginas de 15."""
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    hoy = timezone.localdate()
    citas = taller.solicitudes.select_related("servicio")
    # Todos los conteos en una sola consulta
    conteos = citas.order_by().aggregate(
        abiertas=Count("pk", filter=Q(estado__in=ABIERTAS)), todas=Count("pk"),
        hoy=Count("pk", filter=Q(fecha_preferida=hoy) & ~Q(estado=SolicitudCita.Estado.CANCELADA)),
        proximas=Count("pk", filter=Q(fecha_preferida__gt=hoy, estado__in=ABIERTAS)),
        pasadas=Count("pk", filter=Q(fecha_preferida__lt=hoy)),
        **{e: Count("pk", filter=Q(estado=e)) for e in SolicitudCita.Estado.values})
    filtro = request.GET.get("estado") or ("hoy" if conteos["hoy"] else "abiertas")
    if filtro not in dict(FILTROS_CITAS):
        filtro = "abiertas"
    if filtro == "hoy":
        citas = citas.filter(fecha_preferida=hoy).exclude(estado=SolicitudCita.Estado.CANCELADA).order_by("hora", "creado")
    elif filtro == "proximas":
        citas = citas.filter(fecha_preferida__gt=hoy, estado__in=ABIERTAS).order_by("fecha_preferida", "hora")
    elif filtro == "pasadas":
        citas = citas.filter(fecha_preferida__lt=hoy).order_by("-fecha_preferida")
    elif filtro == "abiertas":
        citas = citas.filter(estado__in=ABIERTAS).order_by("fecha_preferida")
    elif filtro != "todas":
        citas = citas.filter(estado=filtro).order_by("-fecha_preferida")
    else:
        citas = citas.order_by("-fecha_preferida")
    if q := request.GET.get("q", "").strip():
        citas = citas.filter(Q(nombre__icontains=q) | Q(moto__icontains=q) | Q(telefono__icontains=q))
    pagina = Paginator(citas, 15).get_page(request.GET.get("pagina"))
    return render(request, "talleres/citas_taller.html", {
        "taller": taller, "pagina": pagina, "tarjetas": negocio.tarjetas(pagina, taller, request), "filtro": filtro, "q": q,
        "filtros": [(clave, nombre, conteos.get(clave, 0)) for clave, nombre in FILTROS_CITAS],
        "hoy": hoy, "horas": [f"{h:02d}:{m:02d}" for h in range(6, 21) for m in (0, 30)],
    })


@login_required
def resenas_taller(request):
    """Todas las reseñas del taller: sin responder o todas, filtro por estrellas y páginas de 10."""
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    return render(request, "talleres/resenas_negocio.html", {
        "nombre": taller.nombre, "url_panel": reverse("talleres:panel"), "texto_panel": "Mi taller",
        "vacio": "Aún no tienes reseñas. Pídeles a tus clientes que te califiquen en tu página.",
        **negocio.contexto_resenas(request, taller.resenas.filter(visible=True))})


class _RedireccionContacto(HttpResponseRedirect):
    allowed_schemes = ["https", "tel"]


def _moto_y_servicio_para_wa(request, taller):
    """Moto del usuario (si tiene cuenta y moto) y servicio pedido (?servicio=<id>, solo uno que el taller ofrezca)."""
    moto = ""
    motero = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    if motero:
        primera = motero.motos.select_related("linea", "linea__marca").first()
        moto = primera.nombre_completo if primera else ""
    servicio = ""
    if request.GET.get("servicio", "").isdigit():
        s = taller.servicios.filter(pk=request.GET["servicio"]).first()
        servicio = s.nombre.lower() if s else ""
    return moto, servicio


def ir(request, slug, canal):
    """Cuenta el clic (sin datos personales) y lleva a WhatsApp o a la llamada."""
    taller = get_object_or_404(Taller.objects.only("pk", "nombre", "whatsapp", "usuario_id"), slug=slug, activo=True)
    registrar_evento(request, "contacto", canal="whatsapp" if canal == "whatsapp" else "llamada", taller=taller.pk)
    if canal == "whatsapp":
        estadisticas.registrar(request, taller, EventoDiario.Tipo.WHATSAPP)
        return _RedireccionContacto(taller.whatsapp_con_mensaje(*_moto_y_servicio_para_wa(request, taller)))
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
    import json
    from .forms import AgendaForm, leer_turnos
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
    if request.method == "POST":
        filas_json = request.POST.get("turnos_json", "[]")
    else:
        grupos = {}
        for dia, ts in agenda.turnos_por_dia(taller).items():
            for t in ts:
                grupos.setdefault((t.abre.strftime("%H:%M"), t.cierra.strftime("%H:%M")), []).append(dia)
        filas = [{"dias": sorted(d), "abre": a, "cierra": c} for (a, c), d in sorted(grupos.items(), key=lambda g: min(g[1]))]
        filas_json = json.dumps(filas or [{"dias": [0, 1, 2, 3, 4, 5], "abre": "08:00", "cierra": "18:00"}])
    return render(request, "talleres/agenda.html", {"taller": taller, "form": form, "filas_json": filas_json, "errores": errores})


@login_required
def precios_taller(request):
    """El taller publica rangos "desde–hasta" por servicio (cilindraje opcional)."""
    from .forms import precios_formset
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    Formset = precios_formset(taller)
    formset = Formset(request.POST or None, instance=taller, queryset=taller.precios.select_related("servicio"))
    if request.method == "POST" and request.POST.get("siguen_vigentes"):
        from . import precios as _precios
        _precios.confirmar_vigentes(taller)
        messages.success(request, "Listo: confirmaste que tus precios siguen vigentes.")
        return redirect("talleres:precios")
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, "Guardamos tus precios de referencia.")
        return redirect("talleres:precios")
    from . import precios as _precios
    import json
    return render(request, "talleres/precios.html", {"taller": taller, "formset": formset,
                                                     "grupos": _precios.agrupar_formset(formset),
                                                     "servicios": formset.empty_form.fields["servicio"].queryset,
                                                     "medianas": json.dumps(_precios.medianas_por_clave() if ajuste("precio_tipico") else {}),
                                                     "precio_tipico": ajuste("precio_tipico"),
                                                     "url_alternar": reverse("talleres:alternar_precios"),
                                                     "confirmado": _precios.fecha_confirmacion(taller),
                                                     "por_confirmar": _precios.necesita_confirmar(taller),
                                                     "sin_servicios": not taller.servicios.exists()})


@login_required
@require_POST
def alternar_precios(request):
    """Interruptor rápido del panel: mostrar u ocultar los precios de mano de obra en la página pública."""
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    taller.mostrar_precios = request.POST.get("valor") == "1"
    taller.save(update_fields=["mostrar_precios"])
    if request.headers.get("x-requested-with") == "fetch":  # interruptor sin recargar: sin mensaje ni redirección
        return HttpResponse(status=204)
    messages.success(request, "Tus precios ahora se ven en tu perfil." if taller.mostrar_precios
                     else "Ocultamos tus precios: tu perfil dice «Cotiza por WhatsApp».")
    return redirect("talleres:panel")


def emergencias(request):
    """Flujo "¿Te varaste?": el motero elige qué le pasó y ve quién lo atiende, abiertos ahora primero. La cercanía se
    calcula en el navegador con su ubicación (nunca se envía al servidor); si no la da, elige su barrio."""
    from . import emergencias as em
    from proveedores.models import Proveedor
    ahora = timezone.localtime()
    necesito = request.GET.get("necesito")
    necesito = necesito if necesito in em.OPCIONES else None
    filtro = em.OPCIONES[necesito][1] if necesito else {}
    registrar_evento(request, "emergencias", necesito=necesito or "inicio")
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
        gruas = em.ordenar_gruas(list(Proveedor.objects.publicados("grua")), barrio.ciudad if barrio else None, ahora)
        for g in gruas:
            g.tarifa_txt = pesos(g.precio_desde) if g.precio_desde else ""
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


def talleres_barrio(request, barrio):
    b = seo_.barrio_por_slug(barrio)
    n = Taller.objects.filter(activo=True, barrio=b).count()
    return directorio(request, {"barrio": b.pk}, seo_.textos_barrio(b, n))


def talleres_servicio(request, servicio):
    s = seo_.servicio_por_slug(servicio)
    n = Taller.objects.filter(activo=True, servicios=s).count()
    return directorio(request, {"servicio": s.pk}, seo_.textos_servicio(s, n))


def talleres_servicio_barrio(request, servicio, barrio):
    s, b = seo_.servicio_por_slug(servicio), seo_.barrio_por_slug(barrio)
    n = Taller.objects.filter(activo=True, servicios=s, barrio=b).count()
    if not n:
        raise Http404
    return directorio(request, {"servicio": s.pk, "barrio": b.pk}, seo_.textos_servicio(s, n, b))
