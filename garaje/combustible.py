"""Precio de referencia del galón de gasolina corriente en Medellín, para estimar galones a partir del valor.

Archivo de datos editable: al cambiar el precio, actualizar también la fecha y la fuente.
"""
from datetime import date

PRECIO_GALON_CORRIENTE = 16_251  # COP por galón, gasolina corriente en Medellín (referencia; varía por estación)
VIGENTE_DESDE = date(2026, 11, 1)  # suele cambiar al inicio de cada mes
# Vacío = "por verificar". Consultada el 2026-11-14: tabla de precios vigentes desde el 1-nov-2026, 13 ciudades.
FUENTE = "CREG"
FUENTE_URL = "https://creg.gov.co/publicaciones/15565/precios-de-combustibles-liquidos/"
POR_VERIFICAR = not FUENTE


def galones_estimados(valor):
    """Galones aproximados que compra ese valor; None si no hay precio."""
    return round(valor / PRECIO_GALON_CORRIENTE, 1) if valor and PRECIO_GALON_CORRIENTE else None
