"""Comprobante "mantenimiento al día": enlace firmado (sin tabla nueva) que vence a los 30 días.

El token lleva el id del perfil y su version_comprobante. Anular los enlaces sube la versión, así que los viejos dejan
de abrir. Nadie puede armar el enlace de otro: la firma usa SECRET_KEY (no hay IDOR posible por cambiar el número).
"""
from django.core import signing

SAL = "domiciliarios.comprobante"
VIGENCIA_DIAS = 30


def token(perfil):
    return signing.dumps({"p": perfil.pk, "v": perfil.version_comprobante}, salt=SAL, compress=True)


def leer(texto):
    """(perfil_id, version) o None si la firma no vale o ya venció."""
    try:
        datos = signing.loads(texto, salt=SAL, max_age=VIGENCIA_DIAS * 24 * 3600)
    except signing.BadSignature:  # incluye SignatureExpired
        return None
    if not isinstance(datos, dict) or not isinstance(datos.get("p"), int) or not isinstance(datos.get("v"), int):
        return None
    return datos["p"], datos["v"]


def placa_oculta(placa):
    placa = (placa or "").upper()
    return f"{placa[:3]}•••" if placa else ""
