"""Sección Talleres: aprobar, pausar/reactivar, verificar y eliminar con eliminación segura."""
from django.db.models import Count, Q

from talleres.models import Taller
from talleres.precios import DIAS_RECORDATORIO, limite_vencimiento

from django.urls import reverse

from ..acciones import ErrorAccion, accion, eliminador, interruptor, motivo_de
from ..eliminacion import Dependencia, analizar
from ..forms import FiltroTalleres
from ..paginacion import paginar


def _avisar(taller, clave, titulo, texto):
    """Aviso al dueño del taller (si tiene cuenta). La clave lleva la hora: cada cambio avisa."""
    if taller.usuario_id:
        from django.utils import timezone
        from notificaciones.models import Notificacion
        from notificaciones.servicios import notificar
        notificar(taller.usuario, f"{clave}:{taller.pk}:{timezone.now():%Y%m%d%H%M%S%f}", titulo, texto,
                  taller.get_absolute_url(), Notificacion.Tipo.TALLER)


def _avisar_publicado(request, taller, valor):
    """Publicar o pausar un taller con cuenta le avisa (igual que la aprobación de /cuenta/administracion/)."""
    if valor:
        if taller.motivo_rechazo:
            taller.motivo_rechazo = ""
            taller.save(update_fields=["motivo_rechazo"])
        _avisar(taller, "taller-aprobado", "¡Tu taller ya está publicado!", f"{taller.nombre} aparece en el directorio de TallerYa.")
    else:
        _avisar(taller, "taller-pausado", "Tu taller quedó pausado",
                f"{taller.nombre} ya no aparece en el directorio. Escríbenos si crees que es un error.")


def _exigir_aprobacion(request, taller, valor):
    """Un taller dado de alta sin cuenta no se publica hasta que él apruebe su ficha (Ley 1581)."""
    if valor and taller.falta_aprobacion:
        raise ErrorAccion("El taller aún no aprobó su ficha. Envíale el enlace de revisión.")


interruptor("talleres.publicar", modelo=Taller, campo="activo", etiqueta="Publicado en el directorio",
            nombre="Pausar o reactivar taller", si="Reactivó", no="Pausó",
            describe="el taller #{pk} ({obj.nombre})", antes_de=_exigir_aprobacion, despues_de=_avisar_publicado)
@accion("talleres.rechazar", modelo=Taller, nombre="Rechazar taller",
        campos={"motivo_rechazo": ("Motivo del rechazo", lambda o: o.motivo_rechazo)},
        frase="Rechazó al taller #{obj.pk} ({obj.nombre}). Motivo: {obj.motivo_rechazo}",
        exito="Listo: {obj.nombre} quedó rechazado y se le avisó (si tiene cuenta).")
def _rechazar(request, obj):
    if obj.activo:
        raise ErrorAccion("Ese taller está publicado: pausa el taller en vez de rechazarlo.")
    obj.motivo_rechazo = motivo_de(request)
    obj.save(update_fields=["motivo_rechazo"])
    _avisar(obj, "taller-rechazado", "Tu taller no fue aprobado", f"Motivo: {obj.motivo_rechazo}. Corrige los datos y escríbenos para revisarlo de nuevo.")


interruptor("talleres.verificar", modelo=Taller, campo="verificado", etiqueta="Verificado",
            nombre="Verificar taller", si="Verificó", no="Quitó la verificación",
            describe="al taller #{pk} ({obj.nombre})")

interruptor("talleres.precios", modelo=Taller, campo="mostrar_precios", etiqueta="Muestra precios de mano de obra",
            nombre="Mostrar u ocultar precios del perfil", si="Activó los precios en", no="Ocultó los precios en",
            describe="el perfil del taller #{pk} ({obj.nombre})")

@accion("talleres.renovar_enlace", modelo=Taller, nombre="Renovar enlace de ficha",
        campos={"token_creado": ("Enlace de ficha creado", lambda o: o.token_creado.strftime("%d/%m/%Y %H:%M") if o.token_creado else "")},
        frase="Renovó el enlace de ficha del taller #{pk} ({obj.nombre})", exito="Enlace nuevo (vale 30 días; el anterior ya no sirve): {enlace}")
def _renovar_enlace(request, obj):
    if obj.origen_alta == Taller.Alta.CUENTA or obj.aprobado_por_taller:
        raise ErrorAccion("Este taller no tiene una ficha pendiente de aprobar.")
    obj.generar_token()
    obj.save(update_fields=["token_revision", "token_creado"])
    return {"ctx": {"enlace": request.build_absolute_uri(reverse("talleres:revisar_ficha", args=[obj.token_revision]))}}


REGLAS_ELIMINAR = [
    Dependencia("citas", "cita", lambda t: t.solicitudes.count(), True, "son historial de los moteros; despublícalo."),
    Dependencia("cupones con códigos entregados", "cupón con códigos entregados",
                lambda t: t.cupones.filter(codigos__isnull=False).distinct().count(), True,
                "hay códigos en manos de moteros; despublícalo."),
    Dependencia("servicios en hojas de vida", "servicio en hojas de vida",
                lambda t: t.servicios_registrados.count() + t.mantenimientos.count(), True,
                "son el historial de las motos; despublícalo."),
    Dependencia("cuentas vinculadas", "cuenta vinculada", lambda t: 1 if t.usuario_id else 0,
                efecto="la cuenta queda sin taller (rol Registro incompleto)."),
    Dependencia("reseñas", "reseña", lambda t: t.resenas.count(), efecto="se borran."),
    Dependencia("fotos", "foto", lambda t: t.fotos.count(), efecto="se borran."),
    Dependencia("cupones sin entregar", "cupón sin entregar",
                lambda t: t.cupones.filter(codigos__isnull=True).count(), efecto="se borran."),
]
eliminador("talleres.eliminar", modelo=Taller, reglas=REGLAS_ELIMINAR, describe="el taller #{pk} ({a[registro]})",
           nombre="Eliminar taller")


def seccion(request):
    form = FiltroTalleres(request.GET)
    datos = form.cleaned_data if form.is_valid() else {}
    qs = (Taller.objects.select_related("barrio", "usuario").annotate(n_citas=Count("solicitudes", distinct=True),
                                                                        n_precios_viejos=Count("precios", filter=Q(precios__actualizado__lt=limite_vencimiento()), distinct=True))
          .order_by("activo", "-creado"))  # primero los que esperan aprobación
    if datos.get("q"):
        q = datos["q"]
        qs = qs.filter(Q(nombre__icontains=q) | Q(barrio__nombre__icontains=q) | Q(responsable__icontains=q)
                       | Q(usuario__email__icontains=q))
    estado = datos.get("estado")
    if estado == "publicados":
        qs = qs.filter(activo=True)
    elif estado == "por_aprobar":
        qs = qs.filter(activo=False, motivo_rechazo="")
    elif estado == "rechazados":
        qs = qs.filter(activo=False).exclude(motivo_rechazo="")
    elif estado == "verificados":
        qs = qs.filter(verificado=True)
    datos_pagina = paginar(request, qs, "talleres")
    filas = [(t, analizar(t, REGLAS_ELIMINAR)) for t in datos_pagina["pagina"]]
    return "consola/talleres.html", {"form": form, "dias_precios": DIAS_RECORDATORIO, "filas": filas, **datos_pagina}
