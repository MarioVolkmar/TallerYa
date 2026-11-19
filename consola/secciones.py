"""Secciones de la consola, declaradas en una lista: agregar una es agregar una línea.

vista: ruta "modulo.funcion" que recibe (request) y devuelve (plantilla, contexto), o None si aún no existe (fase 2).
badge: funcion() -> int con los pendientes de esa sección (o None).
"""
from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Optional


def _talleres_pendientes():
    from talleres.models import Taller
    return Taller.objects.filter(activo=False).count()


def _plus_solicitadas():
    from cuentas.models import Suscripcion
    return Suscripcion.objects.filter(estado=Suscripcion.Estado.SOLICITADA).count()


def _reportes_foro():
    from foro.models import Reporte
    return Reporte.objects.filter(revisado=False).count()


def _citas_pendientes():
    from talleres.models import SolicitudCita
    return SolicitudCita.objects.filter(estado=SolicitudCita.Estado.PENDIENTE).count()


def _domiciliarios_pendientes():
    from domiciliarios.consola import pendientes
    return pendientes()


def _mecanicos_pendientes():
    from domicilio.consola import pendientes
    return pendientes()


@dataclass
class Seccion:
    key: str
    label: str
    icon: str
    vista: Optional[str] = None
    badge: Optional[Callable] = None
    descripcion: str = ""

    @property
    def lista(self):
        return self.vista is not None

    def resolver(self):
        modulo, funcion = self.vista.rsplit(".", 1)
        return getattr(import_module(modulo), funcion)


SECCIONES = [
    Seccion("resumen", "Resumen", "tablero", descripcion="KPI, actividad reciente y lo que requiere atención."),
    Seccion("usuarios", "Usuarios", "personas", "consola.vistas.usuarios.seccion"),
    Seccion("talleres", "Talleres", "taller", "consola.vistas.talleres.seccion", badge=_talleres_pendientes,
            descripcion="Aprobar o rechazar registros de talleres. Mientras tanto: Administración › Talleres por aprobar."),
    Seccion("mecanicos", "Mecánicos a domicilio", "personas", "domicilio.consola.seccion", badge=_mecanicos_pendientes,
            descripcion="Aprobar, suspender y verificar perfiles de mecánicos a domicilio."),
    Seccion("domiciliarios", "Domiciliarios", "personas", "domiciliarios.consola.seccion", badge=_domiciliarios_pendientes,
            descripcion="TallerYa Ruta: aprobar o rechazar verificaciones de domiciliarios (las fotos se borran al decidir)."),
    Seccion("citas", "Citas y servicios", "calendario", "consola.vistas.citas.seccion", badge=_citas_pendientes,
            descripcion="Citas pedidas a los talleres y servicios registrados en la hoja de vida."),
    Seccion("plus", "Pagos y Plus", "estrella", badge=_plus_solicitadas,
            descripcion="Solicitudes de TallerYa Plus por Nequi/transferencia: activar, renovar, cancelar."),
    Seccion("cupones", "Cupones", "cupon", "consola.vistas.cupones.seccion", descripcion="Cupones de los talleres, códigos entregados y canjes."),
    Seccion("moderacion", "Moderación", "bandera", "consola.vistas.moderacion.seccion", badge=_reportes_foro,
            descripcion="Reportes del foro y reseñas de talleres."),
    Seccion("metricas", "Métricas", "grafica", "metricas.panel.seccion"),
    Seccion("reportes", "Reportes", "grafica", descripcion="Rangos de fechas, por mes, rankings; Excel y PDF."),
    Seccion("catalogos", "Catálogos", "lista", descripcion="Barrios, servicios, marcas y líneas de moto."),
    Seccion("notificaciones", "Notificaciones", "campana", descripcion="Notificaciones y correos enviados con su estado."),
    Seccion("configuracion", "Configuración", "ajustes", descripcion="Valores clave/valor con valores por defecto en código."),
    Seccion("bitacora", "Bitácora", "libro", "consola.vistas.bitacora.seccion"),
]
POR_CLAVE = {s.key: s for s in SECCIONES}
PREDETERMINADA = "usuarios"


def con_pendientes():
    """[(seccion, pendientes)] y el total. Cada badge cuesta una consulta COUNT."""
    filas = [(s, (s.badge() if s.badge else 0)) for s in SECCIONES]
    return filas, sum(n for _, n in filas)
