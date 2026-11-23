"""Coordenadas del taller a partir de su dirección y barrio (Nominatim de OpenStreetMap, gratuito).

Política de uso de Nominatim: un User-Agent que identifique la aplicación, máximo 1 consulta por segundo y caché.
Solo se envía la dirección comercial del taller y su barrio (nunca datos de personas). Si no hay respuesta,
el taller queda sin coordenadas y puede tomarlas con el GPS o ajustarlas a mano.
"""
import hashlib
import json
import urllib.parse
import urllib.request
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache

URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "TallerYa/1.0 (directorio de talleres)"
CACHE_SEGUNDOS = 60 * 60 * 24 * 30
# Valle de Aburrá (aprox.): descarta resultados de otra ciudad
LAT = (5.9, 6.6)
LNG = (-75.8, -75.2)


def _consultar(texto):
    """Primera respuesta de Nominatim para el texto, o None. Cacheada (también los vacíos)."""
    clave = "geo:" + hashlib.sha1(texto.lower().encode()).hexdigest()
    visto = cache.get(clave)
    if visto is not None:
        return visto or None
    params = urllib.parse.urlencode({"q": texto, "format": "json", "limit": 1, "countrycodes": "co"})
    try:
        pedido = urllib.request.Request(f"{URL}?{params}", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(pedido, timeout=5) as r:
            datos = json.load(r)
    except Exception:
        return None  # sin red o servicio caído: no se cachea, se reintenta después
    res = None
    if datos:
        lat, lng = float(datos[0]["lat"]), float(datos[0]["lon"])
        if LAT[0] <= lat <= LAT[1] and LNG[0] <= lng <= LNG[1]:
            res = (lat, lng)
    cache.set(clave, res or False, CACHE_SEGUNDOS)
    return res


def geocodificar(direccion, barrio, ciudad):
    """(latitud, longitud, exacta) o None. Primero la dirección completa (exacta); si no, el barrio (aproximada)."""
    if not getattr(settings, "GEOCODIFICAR_ACTIVO", False):
        return None
    for texto, exacta in ((f"{direccion}, {barrio}, {ciudad}, Antioquia", True), (f"{barrio}, {ciudad}, Antioquia", False)):
        if exacta and not (direccion or "").strip():
            continue
        r = _consultar(texto)
        if r:
            return Decimal(f"{r[0]:.6f}"), Decimal(f"{r[1]:.6f}"), exacta
    return None


def completar_ubicacion(taller):
    """Pone latitud/longitud al taller (sin guardar) si cambió la dirección o el barrio, o si no tiene. Devuelve True si cambió."""
    r = geocodificar(taller.direccion, taller.barrio.nombre, taller.barrio.ciudad)
    if not r:
        return False
    taller.latitud, taller.longitud, taller.ubicacion_exacta = r
    taller._geo_auto = True  # no fue una persona: Taller.save no la marca como exacta
    return True
