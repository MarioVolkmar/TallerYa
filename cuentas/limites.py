"""Límites de frecuencia sencillos sobre la caché "default" (Redis en producción, memoria en local y pruebas).

ip_cliente: detrás del proxy de Render, REMOTE_ADDR es la IP del proxy (la misma para todo el mundo); por eso se lee
X-Forwarded-For contando desde la derecha tantos saltos como proxies de confianza haya (settings.PROXIES_DE_CONFIANZA).
Las entradas de la izquierda las puede inventar el cliente y nunca se usan.
"""
from django.conf import settings
from django.core.cache import cache


def ip_cliente(request):
    saltos = getattr(settings, "PROXIES_DE_CONFIANZA", 0)
    if saltos:
        ips = [ip.strip() for ip in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if ip.strip()]
        if len(ips) >= saltos:
            return ips[-saltos]
    return request.META.get("REMOTE_ADDR", "desconocida")


def superado(clave, maximo):
    """True si ya se llegó al máximo de intentos de esa clave."""
    return cache.get(f"limite:{clave}", 0) >= maximo


def sumar(clave, segundos):
    """Cuenta un intento más; la ventana empieza con el primero."""
    clave = f"limite:{clave}"
    if not cache.add(clave, 1, segundos):
        try:
            cache.incr(clave)
        except ValueError:  # expiró entre add e incr
            cache.set(clave, 1, segundos)


def limpiar(clave):
    cache.delete(f"limite:{clave}")
