"""Sección «Mecánicos» de /consola/: aprobar, pausar y verificar perfiles de mecánicos a domicilio.

Usa el mismo mecanismo que las demás secciones (consola.acciones): permiso de administrador, POST y bitácora.
Se registra desde DomicilioConfig.ready() y la sección se declara en consola/secciones.py (una línea).
"""
from django.db.models import Count, Q

from consola.acciones import ErrorAccion, accion, interruptor, motivo_de
from consola.paginacion import paginar

from . import identidad
from .estados import cambiar_estado
from .models import IdentidadMecanico, MecanicoDomicilio

ESTADOS = dict(MecanicoDomicilio.Estado.choices)


@accion("mecanicos.estado", modelo=MecanicoDomicilio, nombre="Cambiar estado de mecánico",
        campos={"estado": ("Estado", lambda o: o.get_estado_display())},
        frase="Cambió el estado del mecánico #{obj.pk} ({obj.nombre})", exito="Listo: {obj.nombre} quedó «{estado}».")
def _estado(request, obj):
    nuevo = request.POST.get("valor", "")
    if nuevo not in ESTADOS or nuevo == MecanicoDomicilio.Estado.RECHAZADO:  # rechazar va por su acción, con motivo
        raise ErrorAccion("Estado no válido.")
    cambiar_estado(obj, nuevo)
    return {"ctx": {"estado": ESTADOS[nuevo]}}


@accion("mecanicos.rechazar", modelo=MecanicoDomicilio, nombre="Rechazar mecánico",
        campos={"estado": ("Estado", lambda o: o.get_estado_display()), "motivo_rechazo": ("Motivo", lambda o: o.motivo_rechazo)},
        frase="Rechazó al mecánico #{obj.pk} ({obj.nombre}). Motivo: {obj.motivo_rechazo}",
        exito="Listo: {obj.nombre} quedó rechazado y se le avisó.")
def _rechazar(request, obj):
    if obj.estado == MecanicoDomicilio.Estado.RECHAZADO:
        raise ErrorAccion("Ese perfil ya está rechazado.")
    cambiar_estado(obj, MecanicoDomicilio.Estado.RECHAZADO, motivo_de(request))


def _exigir_identidad(request, obj, valor):
    if valor and not identidad.puede_tener_insignia(obj):
        raise ErrorAccion("La insignia solo se otorga con la identidad aprobada: revisa su cédula en «Por aprobar».")


interruptor("mecanicos.verificar", modelo=MecanicoDomicilio, campo="verificado", etiqueta="Verificado",
            nombre="Verificar mecánico", si="Verificó", no="Quitó la verificación",
            describe="al mecánico #{pk} ({obj.nombre})", antes_de=_exigir_identidad)


def _identidad_enviada(obj):
    ident = getattr(obj, "identidad", None)
    if not ident or ident.estado != IdentidadMecanico.Estado.ENVIADA:
        raise ErrorAccion("Ese mecánico no tiene una identidad por revisar.")
    return ident


@accion("mecanicos.identidad_aprobar", modelo=MecanicoDomicilio, nombre="Aprobar identidad de mecánico",
        campos={"verificado": ("Verificado", lambda o: o.verificado)},
        frase="Aprobó la identidad del mecánico #{obj.pk} ({obj.nombre}) y le dio la insignia",
        exito="Listo: {obj.nombre} quedó verificado y se le avisó.")
def _identidad_aprobar(request, obj):
    identidad.aprobar(_identidad_enviada(obj), request.user)
    return {"registrar_sin_cambios": True}


@accion("mecanicos.identidad_rechazar", modelo=MecanicoDomicilio, nombre="Rechazar identidad de mecánico",
        campos={"verificado": ("Verificado", lambda o: o.verificado)},
        frase="Rechazó la identidad del mecánico #{obj.pk} ({obj.nombre}). Motivo: {motivo}",
        exito="Listo: se rechazó la identidad de {obj.nombre} y se le avisó.")
def _identidad_rechazar(request, obj):
    ident = _identidad_enviada(obj)
    motivo = motivo_de(request)
    identidad.rechazar(ident, request.user, motivo)
    return {"ctx": {"motivo": motivo}, "registrar_sin_cambios": True}


def con_algo_por_revisar():
    """Perfiles por aprobar o con la identidad (foto de la cédula) esperando revisión."""
    return MecanicoDomicilio.objects.filter(Q(estado=MecanicoDomicilio.Estado.PENDIENTE)
                                            | Q(identidad__estado=IdentidadMecanico.Estado.ENVIADA))


def pendientes():
    return con_algo_por_revisar().count()


def seccion(request):
    qs = (MecanicoDomicilio.objects.select_related("usuario")
          .annotate(n_resenas=Count("resenas", filter=Q(resenas__visible=True), distinct=True),
                    n_fotos=Count("fotos_trabajo", distinct=True))
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
