"""Colores de pintura de fábrica de cada línea, como se venden (o se vendieron) en Colombia.

Patrón simple: una lista por línea (se busca por nombre en "marca + línea", como el 3D) con (hex, nombre); el primero
es el más común y es el color por defecto al registrar la moto si el usuario no elige otro. Las fuentes de cada lista
están en informes_noche/3d-motos-nuevas.md. Las 33 líneas del catálogo tienen lista; una línea nueva sin lista usa la
paleta general (models.COLORES).
"""
import re

from .models import COLORES, COLORES_EXTRA

COLORES_FABRICA = [
    # (orden: las reglas específicas antes que las generales; p. ej. Hunk 150 antes que Hunk, XTZ 150 antes que XTZ 125)
    # ----- 8 líneas nuevas -----
    (r"hunk\s*150", [("#1b1b1b", "Negro"), ("#b5121b", "Rojo")]),
    (r"hunk\s*125", [("#1b1b1b", "Negro"), ("#c8102e", "Rojo y gris"), ("#1f5fbf", "Azul y gris")]),
    (r"\bxr\s*190", [("#c8102e", "Rojo"), ("#eeeeea", "Blanco"), ("#1b1b1b", "Negro"), ("#c9b48a", "Beige")]),
    (r"\bdr\s*150", [("#8c9196", "Gris"), ("#e8c51a", "Amarillo"), ("#1b1b1b", "Negro"), ("#1f4fa8", "Azul"),
                     ("#b5121b", "Rojo")]),
    (r"\bxtz\s*150", [("#1f3fa8", "Azul"), ("#1b1b1b", "Negro"), ("#eeeeea", "Blanco")]),
    (r"raider", [("#9a9fa3", "Gris California"), ("#1b1b1b", "Negro y plata"), ("#1f5fbf", "Azul Forza"),
                 ("#c62828", "Rojo racing"), ("#f2c018", "Amarillo racing")]),
    (r"\bfz\s*2(?!5)|\bfz-?s\b", [("#1d6fc4", "Azul"), ("#1b1b1b", "Negro"), ("#b5121b", "Rojo y negro")]),
    (r"boxer\s*ct\s*125|\bct\s*125", [("#eceeea", "Blanco"), ("#8a9096", "Gris"), ("#1b1b1b", "Negro"),
                                      ("#1f4fa8", "Azul"), ("#c62828", "Rojo")]),
    # ----- 25 líneas del catálogo inicial -----
    (r"\bnkd", [("#1b1b1b", "Negro"), ("#8a9096", "Gris"), ("#eceeea", "Blanco")]),
    # (CR4, TT, Dynamic, XTZ 125, Duke y RC 200 no tienen lista oficial: solo lo que las fotos confirman y, si no,
    # una paleta neutra genérica de negro y gris grafito)
    (r"\bcr4", [("#1b1b1b", "Negro con lima"), ("#3a3d40", "Gris grafito")]),
    (r"\btt\b", [("#1b1b1b", "Negro"), ("#3a3d40", "Gris grafito")]),
    (r"dynamic", [("#1b1b1b", "Negro con lima"), ("#3a3d40", "Gris grafito")]),
    (r"boxer", [("#1b1b1b", "Negro y azul"), ("#c62828", "Rojo"), ("#1f4fa8", "Azul"), ("#4f5d2f", "Verde")]),
    (r"discover", [("#1b1b1b", "Negro"), ("#9e1b1f", "Rojo"), ("#1f4fa8", "Azul"), ("#8a9096", "Gris"),
                   ("#e3c52f", "Amarillo")]),
    (r"pulsar\s*ns", [("#1b1b1b", "Negro"), ("#1f3a8a", "Azul"), ("#8a9096", "Gris")]),
    (r"pulsar\s*rs", [("#1b1b1b", "Negro"), ("#8a9096", "Gris"), ("#c62828", "Rojo")]),
    (r"\bcb\s*125", [("#c8102e", "Rojo"), ("#1b1b1b", "Negro"), ("#8a9096", "Gris")]),
    (r"\bxr\s*150", [("#c8102e", "Rojo"), ("#eeeeea", "Blanco"), ("#1b1b1b", "Negro")]),
    (r"\bdio\b", [("#1f4fa8", "Azul"), ("#c62828", "Rojo"), ("#8a9096", "Gris")]),
    (r"wave", [("#c8102e", "Rojo"), ("#eeeeea", "Blanco"), ("#1b1b1b", "Negro"), ("#8a9096", "Gris")]),
    (r"\bgn\s*125", [("#1b1b1b", "Negro"), ("#b8682a", "Cobre"), ("#1f3fa8", "Azul")]),
    (r"gixxer", [("#1f6fd1", "Azul"), ("#1b1b1b", "Negro"), ("#c62828", "Rojo"), ("#eeeeea", "Blanco")]),
    (r"\bbest\b", [("#c62828", "Rojo y negro"), ("#1b1b1b", "Negro")]),
    (r"nmax", [("#6f7478", "Gris"), ("#1b1b1b", "Negro"), ("#eeeeea", "Blanco"), ("#b5121b", "Rojo")]),
    (r"\bxtz", [("#1f3fa8", "Azul"), ("#1b1b1b", "Negro"), ("#3a3d40", "Gris grafito")]),
    (r"\bfz\s*25", [("#24357a", "Azul y negro"), ("#2a2c2e", "Negro mate"), ("#3d5a3a", "Verde y negro")]),
    (r"crypton", [("#8a9096", "Gris"), ("#eeeeea", "Blanco"), ("#3d6b3f", "Verde"), ("#e3c52f", "Amarillo")]),
    (r"\bmt-?03", [("#9aa0a4", "Gris"), ("#24357a", "Azul"), ("#1b1b1b", "Negro")]),
    (r"apache", [("#8a9096", "Gris"), ("#1f4fa8", "Azul"), ("#1b1b1b", "Negro")]),
    (r"duke", [("#eeeeea", "Blanco y naranja"), ("#1b1b1b", "Negro"), ("#3a3d40", "Gris grafito")]),
    (r"\brc\s*200", [("#1b1b1b", "Negro y naranja"), ("#3a3d40", "Gris grafito")]),
    (r"eco\s*deluxe", [("#1b1b1b", "Negro"), ("#8a9096", "Gris")]),
    (r"aerox", [("#1f5fbf", "Azul"), ("#6f7478", "Gris"), ("#1b1b1b", "Negro")]),
]
_REGLAS = [(re.compile(patron, re.I), colores) for patron, colores in COLORES_FABRICA]


def colores_de_fabrica(nombre):
    """Lista (hex, nombre) de la línea, la más común primero; vacía si la línea no tiene colores propios."""
    for regla, colores in _REGLAS:
        if regla.search(nombre or ""):
            return list(colores)
    return []


def color_por_defecto(nombre, otro="#c62828"):
    colores = colores_de_fabrica(nombre)
    return colores[0][0] if colores else otro


def paleta_personalizar(nombre):
    """Muestras de Personalizar: primero las de fábrica de la línea y luego la paleta general, sin repetir tonos."""
    fabrica = [(h, f"{n} (de fábrica)") for h, n in colores_de_fabrica(nombre)]
    vistos = {h.lower() for h, _ in fabrica}
    return fabrica + [(h, n) for h, n in COLORES + COLORES_EXTRA if h.lower() not in vistos]
