"""Roles de TallerYa: motero, taller y administrador.

No hay un campo aparte: el rol sale de lo que la cuenta ya tiene.
- Administrador: cuenta de staff de Django (gestiona talleres y usuarios).
- Taller: la cuenta está vinculada a un Taller (Taller.usuario).
- Motero: la cuenta tiene perfil de motociclista (garaje, cupones, Plus).
"""

ADMIN = "admin"
TALLER = "taller"
MOTERO = "motero"
SIN_PERFIL = "sin_perfil"

NOMBRES = {ADMIN: "Administrador", TALLER: "Taller", MOTERO: "Motero", SIN_PERFIL: "Sin perfil"}


def rol_de(usuario):
    if not usuario or not usuario.is_authenticated:
        return None
    if usuario.is_staff:
        return ADMIN
    if getattr(usuario, "taller", None):
        return TALLER
    if getattr(usuario, "motociclista", None):
        return MOTERO
    return SIN_PERFIL


def contexto(request):
    """Procesador de contexto: deja `rol` y `rol_nombre` disponibles en todas las plantillas."""
    from .google import configurado
    rol = rol_de(getattr(request, "user", None))
    from django.conf import settings
    return {"rol": rol, "rol_nombre": NOMBRES.get(rol, ""), "google_disponible": configurado(),
            "contacto": getattr(settings, "CONTACTO", {})}
