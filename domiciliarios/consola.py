"""Sección «Domiciliarios» de /consola/: cola de verificaciones para aprobar o rechazar con motivo.

Mismo mecanismo que Usuarios, Bitácora y Mecánicos (consola.acciones): solo administradores, POST y bitácora.
Se registra desde DomiciliariosConfig.ready() y se declara en consola/secciones.py (una línea).
Las fotos se ven por domiciliarios:verificacion_foto (staff o dueño) y se borran al decidir.
"""
from django.db.models import Case, IntegerField, Q, Value, When

from consola.acciones import ErrorAccion, accion
from consola.paginacion import paginar

from . import verificacion as verif
from .models import Verificacion

ESTADOS = dict(Verificacion.Estado.choices)
CAMPOS = {"estado": ("Estado", lambda o: o.get_estado_display()),
          "vence": ("Vence", lambda o: o.vence), "motivo": ("Motivo", lambda o: o.motivo)}


def _solo_pendiente(obj):
    if obj.estado != Verificacion.Estado.PENDIENTE:
        raise ErrorAccion("Esa solicitud ya se revisó.")


@accion("ruta.aprobar", modelo=Verificacion, nombre="Aprobar domiciliario", campos=CAMPOS,
        frase="Aprobó la verificación de domiciliario #{obj.pk}", exito="Listo: verificado. Fotos borradas y usuario avisado.")
def _aprobar(request, obj):
    _solo_pendiente(obj)
    verif.aprobar(obj, request.user)
    return {}


@accion("ruta.rechazar", modelo=Verificacion, nombre="Rechazar domiciliario", campos=CAMPOS,
        frase="Rechazó la verificación de domiciliario #{obj.pk}", exito="Listo: rechazada. Fotos borradas y usuario avisado.")
def _rechazar(request, obj):
    _solo_pendiente(obj)
    motivo = request.POST.get("valor", "").strip()
    if len(motivo) < 4:
        raise ErrorAccion("Escribe el motivo del rechazo (se le muestra al usuario).")
    verif.rechazar(obj, request.user, motivo)
    return {}


def pendientes():
    from .bandera import activo
    return Verificacion.objects.filter(estado=Verificacion.Estado.PENDIENTE).count() if activo() else 0


def seccion(request):
    qs = Verificacion.objects.select_related("perfil__motociclista__usuario", "moto", "revisado_por")
    q = request.GET.get("q", "").strip()[:80]
    if q:
        qs = qs.filter(Q(perfil__motociclista__nombre__icontains=q) | Q(perfil__motociclista__usuario__email__icontains=q))
    estado = request.GET.get("estado", "")
    if estado in ESTADOS:
        qs = qs.filter(estado=estado)
    qs = qs.annotate(prioridad=Case(When(estado=Verificacion.Estado.PENDIENTE, then=Value(0)), default=Value(1),
                                    output_field=IntegerField())).order_by("prioridad", "creado" if not estado else "-creado")
    return "domiciliarios/consola_ruta.html", {"q": q, "estado": estado, "estados": ESTADOS.items(),
                                               **paginar(request, qs, "talleres")}
