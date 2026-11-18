"""Roles de TallerYa: motero, taller y administrador.

No hay un campo aparte: el rol sale de lo que la cuenta ya tiene.
- Administrador: cuenta de staff de Django (gestiona talleres y usuarios).
- Taller: la cuenta está vinculada a un Taller (Taller.usuario).
- Motero: la cuenta tiene perfil de motociclista (garaje, cupones, Plus).
- Mecánico a domicilio: la cuenta solo tiene perfil de mecánico (domicilio.MecanicoDomicilio). Si además es motero,
  manda el rol motero (sus funciones no cambian) y el perfil de mecánico se edita en /mecanicos/mi-perfil/.
"""

ADMIN = "admin"
TALLER = "taller"
MOTERO = "motero"
MECANICO = "mecanico"
SIN_PERFIL = "sin_perfil"

NOMBRES = {ADMIN: "Administrador", TALLER: "Taller", MOTERO: "Motero", MECANICO: "Mecánico a domicilio", SIN_PERFIL: "Sin perfil"}


def rol_de(usuario):
    if not usuario or not usuario.is_authenticated:
        return None
    if usuario.is_staff:
        return ADMIN
    if getattr(usuario, "taller", None):
        return TALLER
    if getattr(usuario, "motociclista", None):
        return MOTERO
    if getattr(usuario, "mecanico_domicilio", None):
        return MECANICO
    return SIN_PERFIL


def contexto(request):
    """Procesador de contexto: deja `rol` y `rol_nombre` disponibles en todas las plantillas."""
    from .google import configurado
    rol = rol_de(getattr(request, "user", None))
    from django.conf import settings
    usuario = getattr(request, "user", None)
    perfil = getattr(usuario, "perfil", None) if usuario is not None and usuario.is_authenticated else None
    return {"rol": rol, "rol_nombre": NOMBRES.get(rol, ""), "google_disponible": configurado(),
            "contacto": getattr(settings, "CONTACTO", {}),
            # Aviso para confirmar el correo (solo cuentas nuevas sin verificar)
            "correo_pendiente": usuario.email if perfil and not perfil.correo_verificado else ""}
