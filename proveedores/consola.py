"""Sección «Proveedores» de /consola/: grúas, CDA, SOAT y demás categorías. Aprobar, pausar o reactivar, verificar,
renovar el enlace de revisión y eliminar, todo con el mecanismo común (consola.acciones: permiso, POST y bitácora).
Se registra desde ProveedoresConfig.ready() y la sección se declara en consola/secciones.py (una línea)."""

from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404
from django.urls import reverse

from consola import reloj
from consola.acciones import ErrorAccion, accion, eliminador, interruptor
from consola.eliminacion import Dependencia, analizar
from consola.paginacion import paginar

from .models import Categoria, EventoProveedor, Proveedor

ESTADOS = dict(Proveedor.Estado.choices)
E = Proveedor.Estado


def pendientes():
    return Proveedor.objects.filter(estado=E.POR_REVISAR).count()


@accion("proveedores.estado", modelo=Proveedor, nombre="Cambiar estado de proveedor",
        campos={"estado": ("Estado", lambda o: o.get_estado_display())},
        frase="Cambió el estado del proveedor #{obj.pk} ({obj.nombre})", exito="Listo: {obj.nombre} quedó «{estado}».")
def _estado(request, obj):
    nuevo = request.POST.get("valor", "")
    if nuevo not in ESTADOS:
        raise ErrorAccion("Estado no válido.")
    if nuevo == E.PUBLICADO and obj.falta_aprobacion:
        raise ErrorAccion("El proveedor aún no aprobó su ficha (Ley 1581). Reenvíale el enlace de revisión.")
    obj.estado = nuevo
    obj.save(update_fields=["estado", "actualizado"])
    return {"ctx": {"estado": ESTADOS[nuevo]}}


interruptor("proveedores.verificar", modelo=Proveedor, campo="verificado", etiqueta="Verificado",
            nombre="Verificar proveedor", si="Verificó", no="Quitó la verificación",
            describe="al proveedor #{pk} ({obj.nombre})")


def enlace_de(request, obj):
    return request.build_absolute_uri(reverse("proveedores:revisar", args=[obj.token_revision]))


@accion("proveedores.renovar_enlace", modelo=Proveedor, nombre="Renovar enlace de ficha de proveedor",
        campos={"token_creado": ("Enlace de ficha creado",
                                 lambda o: o.token_creado.strftime("%d/%m/%Y %H:%M:%S") if o.token_creado else "")},
        frase="Renovó el enlace de ficha del proveedor #{pk} ({obj.nombre})",
        exito="Enlace nuevo (vale 30 días; el anterior ya no sirve): {enlace}")
def _renovar_enlace(request, obj):
    if obj.origen_alta == Proveedor.Alta.EQUIPO or obj.aprobado_por_proveedor:
        raise ErrorAccion("Este proveedor no tiene una ficha pendiente de aprobar.")
    obj.generar_token()
    obj.save(update_fields=["token_revision", "token_creado"])
    return {"ctx": {"enlace": enlace_de(request, obj)}}


REGLAS_ELIMINAR = [
    Dependencia("días con clics registrados", "día con clics registrados", lambda p: p.eventos.count(),
                efecto="se borran sus contadores."),
]
eliminador("proveedores.eliminar", modelo=Proveedor, reglas=REGLAS_ELIMINAR,
           describe="el proveedor #{pk} ({a[registro]})", nombre="Eliminar proveedor")


def _reporte(request, pk):
    from consola.vistas.reportes import _meses, _por_mes
    p = get_object_or_404(Proveedor, pk=pk if str(pk).isdigit() else 0)
    T = EventoProveedor.Tipo
    desde = _meses(reloj.hoy())[-1]
    acum = {}
    for e in p.eventos.filter(fecha__gte=desde):
        d = acum.setdefault((e.fecha.year, e.fecha.month), {})
        d[e.tipo] = d.get(e.tipo, 0) + e.cantidad
    filas = _por_mes(reloj.hoy(), acum, (T.WHATSAPP, T.LLAMADA))
    return "consola/reporte_detalle.html", {
        "quien": p.nombre, "ficha": reverse("proveedores:editar", args=[p.pk]), "volver": "?seccion=proveedores",
        "columnas": [("Clics a WhatsApp", T.WHATSAPP), ("Clics a llamar", T.LLAMADA)],
        "filas": filas, "total": {c: sum(f[c] for f in filas) for c in (T.WHATSAPP, T.LLAMADA)},
        "nota": "Se cuentan los clics desde Emergencias y Técnico-mecánica. «Ver ficha pública» abre la edición: los proveedores aún no tienen página propia.",
    }


def seccion(request):
    if request.GET.get("reporte"):
        return _reporte(request, request.GET["reporte"])
    categorias = list(Categoria.objects.annotate(n=Count("proveedores")))
    qs = Proveedor.objects.select_related("categoria")
    q = request.GET.get("q", "").strip()[:80]
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(whatsapp__icontains=q) | Q(telefono__icontains=q)
                       | Q(responsable__icontains=q) | Q(municipio__icontains=q))
    cat = request.GET.get("categoria", "")
    if cat and any(c.slug == cat for c in categorias):
        qs = qs.filter(categoria__slug=cat)
    else:
        cat = ""
    estado = request.GET.get("estado", "")
    if estado in ESTADOS:
        qs = qs.filter(estado=estado)
    else:
        estado = ""
    # Primero los que esperan revisión; luego por categoría y nombre
    qs = qs.annotate(prioridad=Case(When(estado=E.POR_REVISAR, then=Value(0)), When(estado=E.PUBLICADO, then=Value(1)),
                                    default=Value(2), output_field=IntegerField())
                     ).order_by("prioridad", "categoria__orden", "nombre")
    datos = paginar(request, qs, "talleres")
    filas = [(p, analizar(p, REGLAS_ELIMINAR)) for p in datos["pagina"]]
    return "proveedores/consola_lista.html", {
        "q": q, "categoria": cat, "estado": estado, "estados": ESTADOS.items(), "categorias": categorias,
        "filas": filas, **datos}
