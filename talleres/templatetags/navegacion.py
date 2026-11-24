"""Navegación de base.html: qué sección del menú está activa según la ruta.

Se usa como {% seccion_activa as sec %} y luego {% if sec == "garaje" %}aria-current="true"{% endif %}.
"""
from django import template

register = template.Library()

# Prefijo de ruta -> sección del menú. El primero que coincide gana (los más específicos van antes).
SECCIONES = (
    ("/mi-taller/citas", "taller_citas"),
    ("/mi-taller/cita/", "taller_citas"),
    ("/mi-taller/perfil", "taller_perfil"),
    ("/mi-taller/agenda", "taller_agenda"),
    ("/mi-taller/registrar-servicio", "taller_registrar"),
    ("/mi-taller/servicios", "taller_servicios"),
    ("/mi-taller/resenas", "taller_resenas"),
    ("/mi-taller/precios", "taller_mas"),
    ("/mi-taller/estadisticas", "taller_mas"),
    ("/mi-taller/cupones", "taller_mas"),
    ("/mi-taller", "taller_panel"),
    ("/canjear", "taller_canjear"),
    ("/talleres", "talleres"),
    ("/taller/", "talleres"),
    ("/mecanicos/mi-panel/servicios", "mecanico_servicios"),
    ("/mecanicos/mi-panel", "mecanico_panel"),
    ("/mecanicos/mi-perfil/solicitudes", "mecanico_solicitudes"),
    ("/mecanicos/mi-perfil/precios", "mecanico_precios"),
    ("/mecanicos/mi-perfil", "mecanico_perfil"),
    ("/mecanicos/registrar-servicio", "mecanico_registrar"),
    ("/mecanicos", "talleres"),
    ("/garaje", "garaje"),
    ("/bienvenida", "garaje"),
    ("/diagnostico", "garaje"),
    ("/soat", "garaje"),
    ("/tecnomecanica", "garaje"),
    ("/domiciliarios", "garaje"),
    ("/foro", "comunidad"),
    ("/cupones", "cupones"),
    ("/cupon/", "cupones"),
    ("/emergencias", "emergencias"),
    ("/consola", "consola"),
)


def seccion_de(ruta):
    if ruta == "/":
        return "inicio"
    for prefijo, seccion in SECCIONES:
        if ruta.startswith(prefijo):
            return seccion
    return ""


@register.simple_tag(takes_context=True)
def seccion_activa(context):
    request = context.get("request")
    return seccion_de(request.path) if request else ""


@register.simple_tag(takes_context=True)
def pendientes_rol(context):
    """Números para las insignias del menú según el rol (citas por responder, solicitudes nuevas, aprobaciones).

    Solo consulta lo del rol que está viendo la página; el motociclista y el visitante no gastan consultas."""
    rol, usuario = context.get("rol"), getattr(context.get("request"), "user", None)
    try:
        if rol == "taller":
            from talleres.models import SolicitudCita
            taller = getattr(usuario, "taller", None)
            if taller:
                return {"citas": SolicitudCita.objects.filter(taller=taller, estado=SolicitudCita.Estado.PENDIENTE).count()}
        elif rol == "mecanico":
            from domicilio.models import SolicitudVisita
            mecanico = getattr(usuario, "mecanico_domicilio", None)
            if mecanico:
                return {"solicitudes": SolicitudVisita.objects.filter(mecanico=mecanico, estado=SolicitudVisita.Estado.PENDIENTE).count()}
        elif rol == "admin":
            from consola import secciones as s
            por_seccion = {"talleres": s._talleres_pendientes(), "mecanicos": s._mecanicos_pendientes(),
                           "usuarios": s._domiciliarios_pendientes(), "proveedores": s._proveedores_pendientes()}
            mayor = max(por_seccion, key=por_seccion.get)
            return {**por_seccion, "moderacion": s._reportes_foro(),
                    "aprobaciones": sum(por_seccion.values()),
                    # la Aprobaciones lleva a la sección con más pendientes (a talleres si no hay ninguno)
                    "aprobaciones_a": mayor if por_seccion[mayor] else "talleres"}
    except Exception:  # una insignia nunca debe tumbar la página
        pass
    return {}
