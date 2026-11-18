"""Sección «Mecánicos» de /consola/: aprobar, suspender y verificar perfiles de mecánicos a domicilio.

Usa el mismo mecanismo que las demás secciones (consola.acciones): permiso de administrador, POST y bitácora.
Se registra desde DomicilioConfig.ready() y la sección se declara en consola/secciones.py (una línea).
"""
from django.db.models import Count, Q

from consola.acciones import ErrorAccion, accion, interruptor
from consola.paginacion import paginar

from .estados import cambiar_estado
from .models import MecanicoDomicilio

ESTADOS = dict(MecanicoDomicilio.Estado.choices)


@accion("mecanicos.estado", modelo=MecanicoDomicilio, nombre="Cambiar estado de mecánico",
        campos={"estado": ("Estado", lambda o: o.get_estado_display())},
        frase="Cambió el estado del mecánico #{obj.pk} ({obj.nombre})", exito="Listo: {obj.nombre} quedó «{estado}».")
def _estado(request, obj):
    nuevo = request.POST.get("valor", "")
    if nuevo not in ESTADOS:
        raise ErrorAccion("Estado no válido.")
    cambiar_estado(obj, nuevo)
    return {"ctx": {"estado": ESTADOS[nuevo]}}


interruptor("mecanicos.verificar", modelo=MecanicoDomicilio, campo="verificado", etiqueta="Verificado",
            nombre="Verificar mecánico", si="Verificó", no="Quitó la verificación",
            describe="al mecánico #{pk} ({obj.nombre})")


def pendientes():
    return MecanicoDomicilio.objects.filter(estado=MecanicoDomicilio.Estado.PENDIENTE).count()


def seccion(request):
    qs = (MecanicoDomicilio.objects.select_related("usuario")
          .annotate(n_resenas=Count("resenas", filter=Q(resenas__visible=True)))
          .order_by("estado", "-creado"))  # "aprobado" < "pendiente" < "suspendido": se reordena abajo
    q = request.GET.get("q", "").strip()[:80]
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(whatsapp__icontains=q) | Q(usuario__email__icontains=q))
    estado = request.GET.get("estado", "")
    if estado in ESTADOS:
        qs = qs.filter(estado=estado)
    else:  # primero los que esperan revisión
        from django.db.models import Case, IntegerField, Value, When
        qs = qs.annotate(prioridad=Case(When(estado=MecanicoDomicilio.Estado.PENDIENTE, then=Value(0)),
                                        default=Value(1), output_field=IntegerField())).order_by("prioridad", "-creado")
    return "domicilio/consola_mecanicos.html", {"q": q, "estado": estado, "estados": ESTADOS.items(),
                                                **paginar(request, qs, "talleres")}
