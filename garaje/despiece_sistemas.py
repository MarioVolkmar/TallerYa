"""Sistemas del despiece: una sola tabla para todas las motos.

Todas las motos muestran la misma lista, en el mismo orden y con los mismos nombres; solo cambia según la
transmisión (cadena o automática) y si es refrigerada por líquido. Un sistema sin láminas se muestra igual,
con el aviso "Sin piezas en el catálogo".
"""
import re

_COMUNES_ANTES = ["Motor", "Lubricación", "Admisión", "Escape"]
_COMUNES_DESPUES = ["Refrigeración", "Frenos", "Ruedas", "Suspensión", "Eléctrico"]
SISTEMAS = {
    # El clutch va con la caja: comparten el eje principal y la carcasa
    "cadena": _COMUNES_ANTES + ["Caja de cambios y clutch", "Kit de arrastre"] + _COMUNES_DESPUES,
    "cvt": _COMUNES_ANTES + ["Transmisión CVT", "Transmisión final"] + _COMUNES_DESPUES,
}

# Orden de los subgrupos dentro de cada sistema
ORDEN_SUBGRUPOS = ["Cilindro y pistón", "Culata", "Válvulas y distribución", "Cárter y tapas", "Filtro de aire", "Carburador",
                   "Cuerpo de aceleración e inyección", "Caja de cambios", "Clutch", "Delantero", "Trasero", "Bomba y líquido",
                   "Delantera", "Trasera", "Delantera y trasera", "Delantera y dirección", "Trasera y basculante",
                   "Arranque", "Encendido y bujías", "Batería y sistema eléctrico"]

# Por el dibujo de la lámina
_POR_DIAGRAMA = {
    "culata": ("Motor", "Culata"), "cilindro_piston": ("Motor", "Cilindro y pistón"),
    "valvulas": ("Motor", "Válvulas y distribución"), "distribucion": ("Motor", "Válvulas y distribución"),
    "carcasa": ("Motor", "Cárter y tapas"),
    "transmision": ("Caja de cambios y clutch", "Caja de cambios"), "clutch": ("Caja de cambios y clutch", "Clutch"),
    "aceite": ("Lubricación", ""),
    "admision": ("Admisión", "Filtro de aire"), "carburador": ("Admisión", "Carburador"),
    "inyeccion": ("Admisión", "Cuerpo de aceleración e inyección"),
    "escape": ("Escape", ""), "radiador": ("Refrigeración", ""),
    "cvt": ("Transmisión CVT", ""), "caja_secundaria": ("Transmisión final", ""),
    "bomba_freno": ("Frenos", "Bomba y líquido"), "bombas_abs": ("Frenos", "Bomba y líquido"),
    "freno_trasero": ("Frenos", "Trasero"),
    "rueda_trasera": ("Ruedas", "Trasera"), "rueda_tambor": ("Ruedas", "Trasera"),
    "suspension_delantera": ("Suspensión", "Delantera y dirección"), "amortiguadores": ("Suspensión", "Trasera y basculante"),
    "encendido": ("Eléctrico", "Encendido y bujías"), "electrico": ("Eléctrico", "Batería y sistema eléctrico"),
}
# Láminas sin dibujo propio: por la pieza de mantenimiento
_POR_PIEZA = {
    "freno_del": ("Frenos", "Delantero"), "freno_tras": ("Frenos", "Trasero"),
    "llanta_del": ("Ruedas", "Delantera"), "llanta_tras": ("Ruedas", "Trasera"), "motor": ("Motor", ""),
    "bujia": ("Eléctrico", "Encendido y bujías"), "filtro_aire": ("Admisión", "Filtro de aire"), "aceite": ("Lubricación", ""),
    "refrigeracion": ("Refrigeración", ""), "correa": ("Transmisión CVT", ""), "cadena": ("Kit de arrastre", ""),
    "suspension_del": ("Suspensión", "Delantera y dirección"), "suspension_tras": ("Suspensión", "Trasera y basculante"),
    "bateria": ("Eléctrico", "Batería y sistema eléctrico"),
}


def _lado(pieza, nombre):
    tras = bool(re.search(r"tras", pieza or "", re.I) or re.search(r"traser", nombre or "", re.I))
    dela = bool(re.search(r"_del$", pieza or "") or re.search(r"delanter", nombre or "", re.I))
    return "Trasero" if tras and not dela else "Delantero" if dela and not tras else None


def sistema_de(diagrama, pieza, nombre, vista_id="", forzado=None):
    """(sistema, subgrupo) de una lámina (o de una de sus vistas)."""
    if forzado:
        return tuple(forzado) if isinstance(forzado, (list, tuple)) else (forzado, "")
    nombre = nombre or ""
    # El motor de arranque, el bendix y el embrague del arranque van con lo eléctrico (no son el clutch principal)
    if re.search(r"arranque|bendix|starter", nombre, re.I):
        return ("Eléctrico", "Arranque")
    if str(vista_id).endswith("-arrastre"):
        return ("Kit de arrastre", "")
    # La lámina del aceite manda aunque use el dibujo del cárter (Apache, Boxer, Discover, NS/RS 200)
    if pieza == "aceite":
        return ("Lubricación", "")
    if diagrama in _POR_DIAGRAMA:
        return _POR_DIAGRAMA[diagrama]
    if diagrama in ("freno_disco", "freno_tambor", "freno_completo"):
        return ("Frenos", _lado(pieza, nombre) or "Delantero")
    if diagrama == "rueda":   # por el nombre: "Llantas y rines" trae las dos ruedas
        tras, dela = re.search(r"traser", nombre, re.I), re.search(r"delanter", nombre, re.I)
        return ("Ruedas", "Trasera" if tras and not dela else "Delantera" if dela and not tras else "Delantera y trasera")
    return _POR_PIEZA.get(pieza, ("Otros", ""))


def sistemas_de(linea):
    """Lista completa de sistemas de la moto, en orden: por su transmisión y su refrigeración."""
    lista = list(SISTEMAS["cvt" if getattr(linea, "transmision", "") == "cvt" else "cadena"])
    if getattr(linea, "refrigeracion", "") != "liquido":
        lista.remove("Refrigeración")
    return lista
