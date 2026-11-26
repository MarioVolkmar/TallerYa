"""Ajustes de la consola: interruptores de módulos que el superadmin prende y apaga sin tocar el .env.

`ajuste("foro_activo")` lee la fila de `Ajuste` si existe; si no, usa el valor inicial de código (que sale del .env /
settings). Las lecturas van a una caché corta; guardar un ajuste la invalida en el acto.
"""
from dataclasses import dataclass
from typing import Callable

from django.conf import settings
from django.core.cache import cache

CACHE_CLAVE = "consola:ajustes"
CACHE_SEGUNDOS = 10


def _social():
    return not getattr(settings, "PILOTO_OCULTAR_SOCIAL", False)


def _bandera(nombre):
    return lambda: bool(getattr(settings, nombre, False))


@dataclass(frozen=True)
class Modulo:
    clave: str
    etiqueta: str
    descripcion: str
    inicial: Callable
    prefijos: tuple = ()  # rutas que dan 404 con el módulo apagado


MODULOS = [
    Modulo("foro_activo", "Foro y rodadas", "Preguntas, respuestas y rodadas de la comunidad. Apagado: /foro/ da 404 y desaparece del menú y la portada.",
           _social, ("/foro/",)),
    Modulo("plus_activo", "TallerYa Plus", "Suscripción Plus y su página. Apagado: /plus/ da 404 y no se ofrece en ningún lado.",
           _social, ("/plus/",)),
    Modulo("referidos_activo", "Referidos", "«Invita y gana» y regalos entre cuentas. Apagado: /r/ y los regalos dan 404.",
           _social, ("/r/", "/cuenta/regalo/")),
    Modulo("mecanicos_activo", "Mecánicos a domicilio", "Directorio, registro y solicitudes de mecánicos que van a donde está la moto.",
           lambda: True, ("/mecanicos/",)),
    Modulo("proveedores_registro", "Inscripción de proveedores («Soy proveedor»)",
           "Formulario público para que grúas, CDA y demás proveedores se inscriban; llegan «Por revisar» a Consola › Proveedores. Apagado: /proveedores/unete/ da 404 (el alta asistida sigue).",
           lambda: True, ("/proveedores/unete/",)),
    Modulo("herramientas_activo", "Herramientas del negocio (agenda, motos en el taller, recordatorios)",
           "Para talleres y mecánicos a domicilio: agenda de citas del día, motos en curso con aviso al cliente cuando está lista y recordatorios de mantenimiento a sus clientes. Apagado: /mi-negocio/ da 404, sale del menú y no se envían los recordatorios.",
           lambda: True, ("/mi-negocio/",)),
    Modulo("domiciliarios_activo", "TallerYa Ruta (domiciliarios)", "Plan para domiciliarios: panel, verificaciones, cupones y avisos de ruta.",
           _bandera("DOMICILIARIOS_ACTIVO")),
    Modulo("cotizador_activo", "Cotizador de repuestos", "Piloto del cotizador de repuestos.", _bandera("COTIZADOR_ACTIVO")),
    Modulo("fallas_activo", "Fallas frecuentes", "Sección «Lo que más les pasa a las…» en la página de cada moto.",
           _bandera("FALLAS_FRECUENTES_ACTIVO")),
]
# Ajustes de presentación (no son módulos: no tienen rutas que apagar). Aparecen aparte en Configuración.
PRESENTACION = [
    Modulo("cifras_directorio", "Mostrar cifras en el directorio",
           "Caja con el total de talleres, verificados y con cupón en el encabezado «Talleres de confianza».", lambda: False),
    Modulo("precio_tipico", "Mostrar precio típico por servicio",
           "Nota en el directorio con el precio típico de un servicio en Medellín (con 3 talleres o más) y la referencia en «Mis precios». Apagado: no se muestra ni se calcula.",
           lambda: False),
]
POR_CLAVE = {m.clave: m for m in MODULOS + PRESENTACION}


def _guardados():
    datos = cache.get(CACHE_CLAVE)
    if datos is None:
        from .models import Ajuste
        datos = dict(Ajuste.objects.values_list("clave", "valor"))
        cache.set(CACHE_CLAVE, datos, CACHE_SEGUNDOS)
    return datos


def ajuste(clave):
    """Valor efectivo del ajuste: el guardado, o el inicial de código."""
    guardado = _guardados().get(clave)
    if guardado is not None:
        return bool(guardado)
    return bool(POR_CLAVE[clave].inicial())


def invalidar():
    cache.delete(CACHE_CLAVE)


def modulos_prefijos():
    return [(m, m.prefijos) for m in MODULOS if m.prefijos]


def prefijos_apagados():
    """Rutas de los módulos apagados (para filtrar avisos y enlaces guardados)."""
    return tuple(p for m, ps in modulos_prefijos() if not ajuste(m.clave) for p in ps)


def sin_modulos_apagados(consulta):
    """Quita de un queryset de Notificacion las que llevan a un módulo apagado."""
    for p in prefijos_apagados():
        consulta = consulta.exclude(url__startswith=p)
    return consulta
