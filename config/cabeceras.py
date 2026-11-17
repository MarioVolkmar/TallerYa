"""Cabeceras de seguridad que Django no pone solo: Content-Security-Policy y Permissions-Policy.

CSP compatible con lo que hay hoy (probado en portada, garaje, 3D, despiece, foro, taller, canje y emergencias):
- script-src lleva 'unsafe-inline' porque ~40 plantillas tienen <script> en línea y algunos onload=; el paso siguiente
  es pasar a nonces (propuesto en informes_noche/revision-seguridad-velocidad.md). Aun así la política impide cargar
  scripts de otros dominios (jsQR y qrcode-generator van en cupones/static/cupones/vendor/), plugins (object-src), cambiar la
  <base>, enviar formularios a otros sitios y que otra página nos meta en un iframe.
- img-src admite https: por las fotos de noticias importadas; frame-src solo Google Maps.
Se aplica también en local (DEBUG) para que cualquier bloqueo se vea antes de desplegar.
"""
from django.conf import settings

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com data:",
    "img-src 'self' data: blob: https:",
    "media-src 'self' blob:",
    "connect-src 'self'",
    "worker-src 'self' blob:",
    "manifest-src 'self'",
    "frame-src 'self' https://www.google.com",  # 'self': el visor 3D de la moto va en un iframe en portada y bienvenida
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self' https://accounts.google.com",
    "frame-ancestors 'none'",
])
# Cámara: lector QR del canje de cupones; ubicación: emergencias y agenda. Nada más.
PERMISOS = "camera=(self), geolocation=(self), microphone=(), payment=(), usb=()"


class CabecerasSeguridad:
    def __init__(self, get_response):
        self.get_response = get_response
        self.csp = CSP + ("" if settings.DEBUG else "; upgrade-insecure-requests")

    def __call__(self, request):
        respuesta = self.get_response(request)
        if "Content-Security-Policy" not in respuesta:  # /media/ pone la suya, más estricta
            csp = self.csp
            # Vistas con @xframe_options_sameorigin (visor 3D): solo nuestras propias páginas pueden incrustarlas.
            if respuesta.get("X-Frame-Options", "").upper() == "SAMEORIGIN":
                csp = csp.replace("frame-ancestors 'none'", "frame-ancestors 'self'")
            respuesta["Content-Security-Policy"] = csp
        respuesta.setdefault("Permissions-Policy", PERMISOS)
        return respuesta
