# Ficha de la Yamaha XTZ 125 para ciclo.py: misma malla de Tripo que la XTZ 150 (geometria practicamente igual, segun el
# usuario) y las mismas reglas de fichas/xtz150.py, cambiando solo lo que difiere en las fotos reales y el manual:
#   - Freno trasero de TAMBOR (manual del propietario XTZ125 y foto lateral): sin disco trasero; queda el tambor que ya trae
#     la malla de Tripo. Disco delantero de 220 mm, a la derecha (fotos).
#   - Rines 21/18 como la 150 (manual: 80/90-21 y 110/80-18): se conserva la deformacion del rin delantero.
#   - Un solo escape a la derecha con protector plateado (fotos): igual que la 150.
#   - Pintura (8 fotos: Galgo azul 2026 x6, negra 2026 x2 locales, azul y blanca anterior): del color de la moto van tanque con
#     aletas, farola, guardabarros delantero, tapas laterales, cubierta bajo el asiento y colin. Asiento, guardabarros trasero
#     y base del asiento, negros. Basculante negro (no plateado como en la 150).
#   - Calca: «XTZ» grande blanca en la aleta del tanque, con el «125».
# Distancia entre ejes real 1,34 m (ficha Yamaha Argentina); se deja la malla de la 150 a 1,36 m (diferencia de 1,5 %).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xtz150 as base  # noqa: E402

EJES = base.EJES
MEZCLA = base.MEZCLA
ISLAS = base.ISLAS
SUAVE = base.SUAVE
PERFIL = False

RENOMBRAR = {
    "plastico.guardabarros_del": "pintura.guardabarros_del",
    "plastico.tanque": "pintura.tanque",
    "plastico.tapa_lateral": "pintura.tapa_lateral",
    "plastico.cubierta_lateral": "pintura.cubierta_lateral",
    "plastico.colin": "pintura.colin",
    "metal.basculante": "oscuro.basculante",
    "metal.manzana_tras": "metal.tambor_tras",
    # foto de Galgo (azul): la farola de la 125 es toda del color alrededor del faro, sin visor ahumado ni marco negro
    "vidrio_oscuro.visor": "pintura.farola_alta",
    "plastico.marco_faro": "pintura.marco_faro",
}
QUITAR = {"disco.disco_tras", "pintura.franja_lateral"}   # tambor atras; la tapa entera ya va pintada
ZONAS = {"pintura.tanque": ["tanque"], "pintura.tapa_lateral": ["lateral"], "pintura.cubierta_lateral": ["lateral"],
         "pintura.colin": ["lateral"], "pintura.guardabarros_del": ["guardabarros"]}
ALISAR = {RENOMBRAR.get(k, k): v for k, v in base.ALISAR.items()}

CALCAS = [
    {"id": "nombre", "nombre": "Nombre XTZ", "tipo": "texto", "texto": "XTZ", "zona": ["tanque"], "cara": "lado",
     "en": [0.17, 0.86], "ancho": 0.26, "giro": -12, "color": "vivo:#ffffff"},
    {"id": "cilindraje", "nombre": "125", "tipo": "texto", "texto": "125", "zona": ["tanque"], "cara": "lado",
     "en": [0.30, 0.80], "ancho": 0.07, "giro": -12, "color": "vivo:#ffffff"},
]


class _Ficha125:
    """Pasa todo al Corte real, pero renombra, quita o ajusta las reglas de la XTZ 150 que difieren en la 125."""

    def __init__(self, m):
        self._m = m

    def __getattr__(self, k):
        return getattr(self._m, k)

    def regla(self, nombre, campo, **extras):
        if nombre in QUITAR:
            return None
        if nombre == "pintura.aleta" and "calcas_fabrica" in extras:
            extras["calcas_fabrica"] = CALCAS
        nombre = RENOMBRAR.get(nombre, nombre)
        if nombre in ZONAS:
            extras.setdefault("zonas", ZONAS[nombre])
        return self._m.regla(nombre, campo, **extras)

    def disco(self, nombre, cx, cy, zc, R, pieza, **kw):
        if nombre in QUITAR:
            return None
        if nombre == "disco.disco_del":
            R = 0.110   # 220 mm
        return self._m.disco(nombre, cx, cy, zc, R, pieza, **kw)


def cortar(m):
    base.cortar(_Ficha125(m))


def internos(k):
    """Rayos X: el motor 124 cc de aire con carburador es de la misma familia; se reutilizan los internos de la 150."""
    pon = k.pon

    def pon125(nombre, *a, **kw):   # la 125 lleva carburador, no cuerpo de aceleracion
        return pon("oscuro.carburador" if nombre == "oscuro.cuerpo_aceleracion" else nombre, *a, **kw)

    k.pon = pon125
    try:
        base.internos(k)
    finally:
        k.pon = pon
