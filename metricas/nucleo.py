"""Registro de uso: quién (seudónimo), desde qué dispositivo y de dónde llegó. Una sola escritura por registro.

`registrar_evento(request, "nombre", **datos)` se llama desde las vistas; nunca lanza errores ni frena la página.
"""
import hashlib
import logging
import re
import secrets
from urllib.parse import urlsplit

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from cuentas.limites import ip_cliente

log = logging.getLogger(__name__)

# Funciones que se miden. Las de `NAVEGADOR` también se aceptan desde el JS (POST /metricas/evento/).
EVENTOS = {
    "registro": "Registro de cuenta",
    "inicio_sesion": "Inicio de sesión",
    "moto_creada": "Moto creada en el garaje",
    "plan_visto": "Plan de mantenimiento visto",
    "despiece_abierto": "Despiece abierto",
    "pieza_vista": "Ficha de pieza vista",
    "visor_3d": "Visor 3D abierto",
    "busqueda_talleres": "Búsqueda de talleres",
    "taller_visto": "Taller visto",
    "contacto": "Contacto a un taller",
    "cupon_obtenido": "Cupón generado",
    "cupon_canjeado": "Cupón canjeado",
    "foro_pregunta": "Pregunta en el foro",
    "foro_respuesta": "Respuesta en el foro",
    "emergencias": "Emergencias usado",
    "plus_solicitado": "Plus solicitado",
    "plus_activado": "Plus activado",
}
NAVEGADOR = {"pieza_vista", "visor_3d"}

# Claves que nunca se guardan aunque alguien las pase por error.
CLAVES_PROHIBIDAS = re.compile(r"mail|correo|celular|telefono|tel$|nombre|ip$|placa|direccion|documento|cedula", re.I)
MAX_DATOS, MAX_TEXTO = 6, 60

BOTS = re.compile(
    r"bot|crawl|spider|slurp|facebookexternalhit|whatsapp|telegram|preview|curl|wget|python|httpx|aiohttp|java/|go-http"
    r"|headless|lighthouse|pingdom|uptime|monitor|scrapy|semrush|ahrefs|bingpreview|okhttp|axios|node-fetch", re.I)
CELULAR = re.compile(r"mobi|android|iphone|ipod|windows phone", re.I)
TABLETA = re.compile(r"ipad|tablet|kindle|silk", re.I)

REFERENTES = [
    ("google", re.compile(r"(^|\.)google\.")),
    ("buscadores", re.compile(r"bing\.|duckduckgo\.|yahoo\.|ecosia\.|brave\.")),
    ("whatsapp", re.compile(r"whatsapp\.|(^|\.)wa\.me$|l\.wl\.co")),
    ("redes", re.compile(r"facebook\.|(^|\.)fb\.|instagram\.|(^|\.)t\.co$|twitter\.|(^|\.)x\.com$|tiktok\.|youtube\."
                         r"|linkedin\.|threads\.")),
]
UTM = {"whatsapp": "whatsapp", "wa": "whatsapp", "facebook": "redes", "instagram": "redes", "fb": "redes", "ig": "redes",
       "tiktok": "redes", "google": "google"}

_sal_cache = {}


def activas():
    return getattr(settings, "METRICAS_ACTIVAS", False)


def no_rastrear(request):
    """El navegador pide no ser rastreado (Do Not Track o Global Privacy Control)."""
    return request.META.get("HTTP_DNT") == "1" or request.META.get("HTTP_SEC_GPC") == "1"


def es_bot(request):
    ua = request.META.get("HTTP_USER_AGENT", "")
    return not ua or bool(BOTS.search(ua))


def dispositivo(request):
    ua = request.META.get("HTTP_USER_AGENT", "")
    if TABLETA.search(ua):
        return "t"
    return "c" if CELULAR.search(ua) else "e"


def referente(request):
    """Grupo de origen: google, buscadores, whatsapp, redes, directo, interno u otros (nunca la URL completa)."""
    utm = request.GET.get("utm_source", "").lower()[:20]
    if utm in UTM:
        return UTM[utm]
    ref = request.META.get("HTTP_REFERER", "")
    if not ref:
        return "directo"
    host = (urlsplit(ref).hostname or "").lower()
    if not host:
        return "directo"
    if host == request.get_host().split(":")[0].lower():
        return "interno"
    for grupo, patron in REFERENTES:
        if patron.search(host):
            return grupo
    return "otros"


def sal_del_dia(dia):
    """Sal aleatoria guardada en la base (la comparten todos los procesos) que se borra al cambiar de día."""
    if dia in _sal_cache:
        return _sal_cache[dia]
    from .models import SalDiaria
    try:
        sal, creada = SalDiaria.objects.get_or_create(dia=dia, defaults={"valor": secrets.token_hex(32)})
    except IntegrityError:  # dos procesos a la vez
        sal, creada = SalDiaria.objects.get(dia=dia), False
    if creada:
        SalDiaria.objects.filter(dia__lt=dia).delete()
    _sal_cache.clear()
    _sal_cache[dia] = sal.valor
    return sal.valor


def visitante(request, dia):
    usuario = getattr(request, "user", None)
    if usuario is not None and usuario.is_authenticated:
        return f"u{usuario.pk}", usuario.pk
    huella = f"{sal_del_dia(dia)}|{ip_cliente(request)}|{request.META.get('HTTP_USER_AGENT', '')[:300]}"
    return hashlib.sha256(huella.encode()).hexdigest()[:16], None


def limpiar_datos(datos):
    limpios = {}
    for clave, valor in list(datos.items())[:MAX_DATOS]:
        if CLAVES_PROHIBIDAS.search(str(clave)):
            continue
        if isinstance(valor, bool) or isinstance(valor, int) and abs(valor) < 10**9:
            limpios[str(clave)[:20]] = valor
        elif valor is not None:
            limpios[str(clave)[:20]] = str(valor)[:MAX_TEXTO]
    return limpios


def puede_medir(request):
    if not activas() or no_rastrear(request) or es_bot(request):
        return False
    usuario = getattr(request, "user", None)
    excluir_staff = getattr(settings, "METRICAS_EXCLUIR_STAFF", True)
    return not (excluir_staff and usuario is not None and usuario.is_authenticated and usuario.is_staff)


def guardar(request, tipo, nombre, datos=None):
    from .models import Evento
    try:
        dia = timezone.localdate()
        quien, usuario_id = visitante(request, dia)
        Evento.objects.create(dia=dia, tipo=tipo, nombre=nombre[:60], visitante=quien, usuario_id=usuario_id,
                              dispositivo=dispositivo(request), referente=referente(request) if tipo == Evento.VISTA else "",
                              datos=limpiar_datos(datos or {}))
        return True
    except Exception:  # la medición nunca rompe la página
        log.exception("No se pudo registrar la métrica %s", nombre)
        return False


def registrar_evento(request, nombre, /, **datos):
    """Registra el uso de una función clave. Solo datos no personales (ids de taller, canal, categoría...)."""
    from .models import Evento
    if request is None or not puede_medir(request):
        return False
    if nombre == "registro":
        request._metricas_registro = True  # el inicio de sesión que sigue al registro no se cuenta aparte
    return guardar(request, Evento.FUNCION, nombre, datos)


TERMINO_PERSONAL = re.compile(r"\d{5,}|@|https?:|www\.")


def termino_busqueda(texto):
    """Normaliza el término buscado; descarta lo que pueda ser un dato personal (celulares, correos, enlaces)."""
    texto = " ".join((texto or "").lower().split())[:40]
    if not texto or TERMINO_PERSONAL.search(texto):
        return ""
    return texto
