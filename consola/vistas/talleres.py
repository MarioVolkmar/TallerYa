"""Sección Talleres: aprobar/publicar, despublicar, verificar y eliminar con eliminación segura."""
from django.db.models import Count, Q

from talleres.models import Taller

from ..acciones import eliminador, interruptor
from ..eliminacion import Dependencia, analizar
from ..forms import FiltroTalleres
from ..paginacion import paginar


def _avisar_publicado(request, taller, valor):
    """Al publicar un taller con cuenta, se le avisa (igual que la aprobación de /cuenta/administracion/)."""
    if valor and taller.usuario_id:
        from notificaciones.models import Notificacion
        from notificaciones.servicios import notificar
        notificar(taller.usuario, f"taller-aprobado:{taller.pk}", "¡Tu taller ya está publicado!",
                  f"{taller.nombre} aparece en el directorio de TallerYa.", taller.get_absolute_url(),
                  Notificacion.Tipo.TALLER)


interruptor("talleres.publicar", modelo=Taller, campo="activo", etiqueta="Publicado en el directorio",
            nombre="Publicar o despublicar taller", si="Publicó", no="Despublicó",
            describe="el taller #{pk} ({obj.nombre})", despues_de=_avisar_publicado)
interruptor("talleres.verificar", modelo=Taller, campo="verificado", etiqueta="Verificado",
            nombre="Verificar taller", si="Verificó", no="Quitó la verificación",
            describe="al taller #{pk} ({obj.nombre})")

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
    qs = (Taller.objects.select_related("barrio", "usuario").annotate(n_citas=Count("solicitudes", distinct=True))
          .order_by("activo", "-creado"))  # primero los que esperan aprobación
    if datos.get("q"):
        q = datos["q"]
        qs = qs.filter(Q(nombre__icontains=q) | Q(barrio__nombre__icontains=q) | Q(responsable__icontains=q)
                       | Q(usuario__email__icontains=q))
    estado = datos.get("estado")
    if estado == "publicados":
        qs = qs.filter(activo=True)
    elif estado == "por_aprobar":
        qs = qs.filter(activo=False)
    elif estado == "verificados":
        qs = qs.filter(verificado=True)
    datos_pagina = paginar(request, qs, "talleres")
    filas = [(t, analizar(t, REGLAS_ELIMINAR)) for t in datos_pagina["pagina"]]
    return "consola/talleres.html", {"form": form, "filas": filas, **datos_pagina}
