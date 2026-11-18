"""Cambiar el estado de moderación de un mecánico (lo usan el admin de Django y la consola) y avisarle."""
from .models import MecanicoDomicilio

TEXTOS = {
    MecanicoDomicilio.Estado.APROBADO: ("¡Tu perfil de mecánico ya está publicado!",
                                        "{nombre} aparece en Mecánicos a domicilio de TallerYa."),
    MecanicoDomicilio.Estado.SUSPENDIDO: ("Tu perfil de mecánico quedó suspendido",
                                          "Ya no aparece en el listado. Escríbenos si crees que es un error."),
}


def cambiar_estado(mecanico, estado):
    """Guarda el estado nuevo y avisa al mecánico (una notificación por cambio). Devuelve True si cambió."""
    if mecanico.estado == estado:
        return False
    mecanico.estado = estado
    mecanico.save(update_fields=["estado", "actualizado"])
    if mecanico.usuario_id and estado in TEXTOS:
        from notificaciones.models import Notificacion
        from notificaciones.servicios import notificar
        titulo, texto = TEXTOS[estado]
        notificar(mecanico.usuario, f"mecanico-{estado}:{mecanico.pk}:{mecanico.actualizado:%Y%m%d%H%M%S}", titulo,
                  texto.format(nombre=mecanico.nombre), mecanico.get_absolute_url(), Notificacion.Tipo.GENERAL)
    return True
