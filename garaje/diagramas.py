"""Diagramas de despiece propios de TallerYa, en isométrico estilo manual técnico.

Cada diagrama arma sólidos 3D sencillos (ver isometrico.py), los "explota" a lo largo de su eje de
montaje y los proyecta en isométrico con líneas de eje y líneas guía hacia el número de cada pieza.
Son dibujos originales por tipo de sistema (sirven para cualquier marca). Cada pieza tiene un "puesto";
las partes de un catálogo se asignan a los puestos por palabras clave (REGLAS), sin marcar a mano.

    dibujar(clave)           → (svg, {puesto: (x, y)})   posición relativa (0..1) del número
    puesto_para(clave, desc) → nombre del puesto o None
    version(clave)           → huella del SVG (para el caché del navegador)
"""
import hashlib
from html import escape
import math
import re
import unicodedata
from functools import lru_cache

from . import isometrico as iso
from .isometrico import (BLANCO, CAUCHO, CAUCHO_CARA, FRICCION, HUECO, LADO_CLARO, LADO_MEDIO, OSCURO, ROJO,
                         Forma, Pieza, arandela, caja, cilindro, engranaje, estadio, hexagono, linea, oring, perno,
                         polilinea, prisma, puntos_en_cara, redondeado, resorte, retenedor, rodamiento, tuerca)

LADO = 1000
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
MENOS_Y = (0, -1, 0)


def P(puesto, formas, ancla, etiqueta=None, orden=None, padre=None, herraje=None):
    pieza = Pieza(puesto, ancla, etiqueta, orden, padre)
    pieza.herraje = herraje   # tornillería dibujada sin número: su tipo en la franja (h_tornillo, h_tuerca...)
    pieza.agregar(*formas)
    return pieza


def manguera(puntos, grosor=9, color=CAUCHO_CARA):
    """Manguera o cable: trazo grueso con contorno."""
    return [polilinea(puntos, grosor + 3), Forma([iso._p2(puntos)], "none", grosor, color, abierta=True)]


def curva(p0, p1, p2, n=16):
    """Curva cuadrática en 3D (para mangueras)."""
    return [tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t ** 2 * c for a, b, c in zip(p0, p1, p2))
            for t in (i / n for i in range(n + 1))]


# ---------------------------------------------------------------------------
# 1. Freno de disco
# ---------------------------------------------------------------------------
def _disco_petalo(c, r, grosor):
    """Disco de freno tipo pétalo: borde ondulado, pista de frenado, perforaciones y porta disco de 5 brazos."""
    borde = [(math.cos(t) * (r + 4 * math.cos(12 * t)), math.sin(t) * (r + 4 * math.cos(12 * t)))
             for t in (i * 2 * math.pi / 144 for i in range(144))]
    formas = prisma(c, X, borde, grosor, hueco=iso._circ2d(r * 0.56, 48), lado=LADO_MEDIO, cara="#f1f3f4")
    frente = iso._sum(c, (grosor / 2 + 0.5, 0, 0))
    # Pista de frenado (aro un poco más oscuro) y perforaciones en dos filas alternadas
    formas += cilindro(frente, X, r * 0.97, 0.6, ri=r * 0.66, lado=LADO_MEDIO, cara="#e6eaec", grosor=1.0)
    formas += puntos_en_cara(c, X, grosor + 1.5, r * 0.87, 18, 4.2) + puntos_en_cara(c, X, grosor + 1.5, r * 0.76, 18, 4.2)
    # Porta disco: estrella de 5 brazos con su maza
    brazos = []
    for i in range(5):
        t = i * 2 * math.pi / 5
        for dt, rr in ((-0.24, r * 0.3), (-0.09, r * 0.6), (0.09, r * 0.6), (0.24, r * 0.3)):
            brazos.append((math.cos(t + dt) * rr, math.sin(t + dt) * rr))
    formas += prisma(iso._sum(c, (grosor / 2 + 2, 0, 0)), X, brazos, 3, hueco=iso._circ2d(r * 0.16, 24),
                     lado=CAUCHO, cara="#7b8387", grosor=1.6)
    formas += puntos_en_cara(iso._sum(c, (3.5, 0, 0)), X, grosor, r * 0.24, 5, 3.6, color=OSCURO)
    return formas


def _freno_disco():
    Z_ = (0, 0, 1)
    cuerpo = redondeado(118, 66, 18)
    # Soporte del caliper: brazo en L con los dos agujeros de montaje en la barra y el pasador deslizante arriba
    soporte = [(-58, 30), (-38, 44), (-20, 40), (-12, 18), (40, -4), (62, -24), (60, -44), (36, -48), (-6, -22), (-40, -6), (-62, 4)]
    piezas = [
        # Cuerpo del caliper con sus dos cilindros, orejas de los pasadores y el canal de la manguera
        P("caliper", prisma((0, 0, 0), Z_, cuerpo, 52, lado=ROJO, cara="#f6cfc4")
          + prisma((0, 4, 28), Z_, redondeado(96, 50, 14), 4, lado="#d98c79", cara="#f9ddd5")
          + cilindro((-27, 2, 31), Z_, 19, 2, cara="#f0b6a6") + cilindro((27, 2, 31), Z_, 19, 2, cara="#f0b6a6")
          + cilindro((-56, 30, 0), Z_, 10, 52, ri=4.5, lado=ROJO, cara="#f6cfc4")
          + cilindro((56, 30, 0), Z_, 10, 52, ri=4.5, lado=ROJO, cara="#f6cfc4")
          + cilindro((20, 40, -6), Y, 8, 12, lado=ROJO, cara="#f6cfc4"), (0, 20, 26), (-70, -75), orden=2),
        # Purgador con su capuchón, arriba del cuerpo
        P("purgador", perno((-24, 70, -6), MENOS_Y, 26, 7) + cilindro((-24, 96, -6), Y, 6.5, 12, lado=CAUCHO, cara=CAUCHO_CARA),
          (-24, 92, -6), (-60, -45), orden=3),
        # Pistones (dos) y sus retenes, saliendo de los cilindros hacia abajo a la izquierda
        P("piston", cilindro((-27, 2, 84), Z_, 17, 26, cara="#fafafa") + cilindro((27, 2, 84), Z_, 17, 26, cara="#fafafa"),
          (-27, 2, 96), (-70, 30), orden=4),
        P("empaques", oring((-27, 2, 122), Z_, 18.5, 3.5) + oring((27, 2, 122), Z_, 18.5, 3.5)
          + oring((-27, 2, 138), Z_, 18.5, 3) + oring((27, 2, 138), Z_, 18.5, 3), (27, 2, 138), (-50, 60), orden=5),
        # Soporte (arriba a la derecha) con el pasador deslizante y sus guardapolvos
        P("soporte", prisma((30, 34, -112), Z_, soporte, 10, hueco=[(math.cos(i / 10 * 6.28) * 6 + 44, math.sin(i / 10 * 6.28) * 6 - 34)
                                                                         for i in range(10)], lado=LADO_MEDIO, cara="#f1f3f4")
          + cilindro((74, 0, -112), Z_, 5, 11, ri=2.5), (64, 20, -112), (60, 40), orden=1),
        # Guardapolvos de los pasadores: salen de las orejas del caliper hacia el soporte
        P("guardapolvo", cilindro((-56, 30, -42), Z_, 9, 16, ri=3.5, cara=CAUCHO_CARA, lado=CAUCHO)
          + cilindro((56, 30, -42), Z_, 9, 16, ri=3.5, cara=CAUCHO_CARA, lado=CAUCHO), (56, 38, -42), (60, -45), orden=1),
        P("pasador", cilindro((-26, 64, -90), Z_, 4.5, 38, cara=BLANCO) + cilindro((86, 64, -90), Z_, 4.5, 38, cara=BLANCO)
          + prisma((-26, 64, -112), Z_, hexagono(7), 6, lado=LADO_MEDIO), (-26, 64, -98), (-60, -50), orden=1),
        # Pastillas (par) debajo del cuerpo, con el resorte y la lámina antirruido
        # Pastillas: material de fricción sobre su placa metálica, con la oreja del pasador
        P("pastillas", prisma((70, -150, 10), Z_, redondeado(92, 40, 12), 7, lado=OSCURO, cara=FRICCION)
          + prisma((70, -150, 5), Z_, redondeado(100, 44, 12) , 2.5, lado=LADO_MEDIO, cara="#dfe3e4")
          + prisma((70, -150, 40), Z_, redondeado(92, 40, 12), 7, lado=OSCURO, cara=FRICCION)
          + prisma((70, -150, 45), Z_, redondeado(100, 44, 12), 2.5, lado=LADO_MEDIO, cara="#dfe3e4")
          + cilindro((118, -134, 25), Z_, 6, 44, ri=2.5, lado=LADO_MEDIO, cara="#dfe3e4"), (110, -166, 45), (50, 60), orden=3),
        P("resorte_pastillas", prisma((70, -100, 25), Y, [(-28, -9), (28, -9), (32, 0), (28, 9), (-28, 9), (-32, 0)], 2,
                                      hueco=redondeado(40, 7, 3), lado=LADO_MEDIO), (92, -100, 25), (60, -25), orden=4),
        P("lamina", prisma((70, -150, 74), Z_, redondeado(86, 38, 11), 1.5, lado=LADO_MEDIO, cara="#f4f5f5"), (34, -150, 74), (-65, 35), orden=4),
        # Disco aparte (abajo a la izquierda), con sus tornillos: solo en las láminas que lo traen
        P("disco", _disco_petalo((-170, -230, 230), 120, 5), (-170, -140, 230), (-80, 60), orden=0),
        P(None, perno((-170, -212, 238), Z_, 14, 6) + perno((-188, -236, 238), Z_, 14, 6), (-170, -212, 238), padre="disco", orden=1, herraje="h_tornillo"),
    ]
    lineas = [
        ("piston", linea((-27, 2, 26), (-27, 2, 150))), ("piston", linea((27, 2, 26), (27, 2, 150))),
        ("soporte", linea((30, 34, -26), (30, 34, -118))),
        ("pasador", linea((-26, 64, -30), (-26, 64, -116))),
        ("purgador", linea((-24, 34, -6), (-24, 104, -6))),
        ("pastillas", linea((70, -36, 25), (70, -122, 25))),
    ]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 2. Bomba de freno, depósito y mangueras
# ---------------------------------------------------------------------------
def _bomba_freno():
    tubo = curva((-30, -40, 0), (-40, -170, 40), (110, -230, 170))
    piezas = [
        # Cuerpo de la bomba: cilindro con su tapa del extremo, el soporte del espejo, la salida de la manguera
        # (abajo) y el pivote de la manigueta al final
        P("bomba", cilindro((10, 0, 0), X, 16, 104, lado="#d5d9da", cara="#eceeef")
          + cilindro((64, 0, 0), X, 13, 6, cara="#e3e6e7") + cilindro((-46, 0, 0), X, 19, 8, lado="#d5d9da")
          + cilindro((-30, -18, 0), Y, 11, 14, lado="#d5d9da") + cilindro((-56, 24, -8), Y, 8, 14, ri=3.5, lado="#d5d9da")
          + cilindro((62, 0, 34), Y, 10, 36, ri=3.5, lado="#d5d9da") + caja((40, 0, 22), (40, 18, 24)), (0, 0, 0), (-80, 60)),
        # Depósito integrado, con su visor del nivel del líquido
        P("deposito", prisma((4, 52, 0), Y, redondeado(74, 52, 15), 34, lado="#d5d9da", cara="#eceeef")
          + cilindro((4, 48, 27), Z, 9, 2, cara="#cfe6f1", lado="#9fbfcc"), (4, 52, 0), (-85, -10)),
        P("diafragma", prisma((4, 88, 0), Y, redondeado(66, 46, 13), 6, hueco=redondeado(40, 22, 8), lado=CAUCHO, cara=CAUCHO_CARA),
          (4, 88, 0), (-85, -25)),
        P("tapa", prisma((4, 112, 0), Y, redondeado(78, 56, 16), 6, lado=LADO_MEDIO, cara="#f4f5f5")
          + prisma((4, 112, 0), Y, redondeado(54, 32, 10), 1, lado=LADO_MEDIO, cara="#e8eaeb"), (4, 112, 0), (-80, -45)),
        P(None, perno((-22, 150, -14), MENOS_Y, 16, 5) + perno((22, 150, 14), MENOS_Y, 16, 5), (0, 150, 0), (70, -40), herraje="h_tornillo"),
        # Manigueta: brazo curvo con su punta redondeada y la ruedita de ajuste junto al pivote
        P("manigueta", prisma((92, -4, 70), Y, [(-30, -10), (10, -12), (60, -16), (110, -12), (140, -4), (144, 6), (112, 0),
                                                (60, -4), (10, 2), (-30, 14)], 8, lado=LADO_MEDIO, cara="#f1f3f4")
          + cilindro((62, -4, 52), Y, 9, 10, lado=OSCURO, cara=LADO_MEDIO), (140, -4, 70), (70, 50)),
        P("abrazadera", prisma((-75, 0, 0), X, redondeado(34, 44, 7), 20, hueco=iso._circ2d(15, 24)), (-75, 0, 0), (-70, 55)),
        P("interruptor", caja((48, -30, -20), (22, 12, 16), colores=(OSCURO, LADO_MEDIO, OSCURO)), (48, -30, -20), (70, -10)),
        P("kit_reparacion", cilindro((175, 0, 0), X, 10, 34) + oring((205, 0, 0), X, 10) + resorte((235, 0, 0), X, 7, 36, 6),
          (205, 0, 0), (60, -50)),
        P("banjo", perno((-30, -10, 0), MENOS_Y, 26, 9) + arandela((-30, -24, 0), Y, 11), (-30, -10, 0), (-75, 20)),
        P("manguera", manguera(tubo), tubo[8], (-80, 40)),
        P("soporte_manguera", caja((60, -205, 110), (18, 12, 18)), (60, -205, 110), (65, 30)),
        P("unidad_abs", caja((230, -230, 60), (80, 56, 70), colores=(LADO_MEDIO, BLANCO, LADO_CLARO))
          + cilindro((215, -195, 50), Y, 7, 12) + cilindro((245, -195, 70), Y, 7, 12), (230, -230, 60), (70, 40)),
    ]
    lineas = [linea((-120, 0, 0), (260, 0, 0)), linea((0, 20, 0), (0, 170, 0)), linea((-30, -50, 0), (-30, 30, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 3. Variador CVT, correa y clutch
# ---------------------------------------------------------------------------
def _cvt():
    zapatas = []
    for k in range(3):
        a0 = k * 2 * math.pi / 3 + 0.25
        arco = [(math.cos(a0 + i * 0.09) * 52, math.sin(a0 + i * 0.09) * 52) for i in range(19)]
        arco += [(math.cos(a0 + i * 0.09) * 36, math.sin(a0 + i * 0.09) * 36) for i in range(18, -1, -1)]
        zapatas += prisma((300, -130, 0), X, arco, 16, lado="#b9a07e", cara=FRICCION)
    piezas = [
        P(None, tuerca((-55, 130, 0), X, 11) + tuerca((440, -130, 0), X, 12), (-55, 130, 0), (-60, -50), herraje="h_tuerca"),
        P("polea_fija", cilindro((0, 130, 0), X, 80, 26, r2=26) + puntos_en_cara((0, 130, 0), X, 2, 55, 12, 4, color=LADO_MEDIO)
          # Aletas de ventilación curvas en la cara de la polea
          + [polilinea([(13.6, 130 + r * math.sin(t + 0.5 * (r - 30) / 45), r * math.cos(t + 0.5 * (r - 30) / 45)) for r in range(30, 76, 5)], 1.6)
             for t in (i * 2 * math.pi / 12 for i in range(12))],
          (0, 130, 0), (-80, -70)),
        P("polea_movil", cilindro((70, 130, 0), X, 24, 28, r2=74), (70, 130, 0), (-20, -95)),
        P("rodillos", cilindro((112, 175, 0), Z, 9, 15) + cilindro((118, 150, -24), Z, 9, 15) + cilindro((112, 115, 24), Z, 9, 15),
          (115, 160, 0), (40, -80)),
        P("deslizadores", caja((150, 180, 0), (8, 10, 14)) + caja((152, 150, -26), (8, 10, 14)), (150, 170, 0), (60, -60)),
        P("rampa", prisma((175, 130, 0), X, [(math.cos(t) * (40 + 10 * math.cos(3 * t)), math.sin(t) * (40 + 10 * math.cos(3 * t)))
                                               for t in [i * 2 * math.pi / 36 for i in range(36)]], 10, hueco=iso._circ2d(11, 20)),
          (175, 130, 0), (65, -40)),
        P("buje", cilindro((215, 130, 0), X, 13, 44, ri=8), (215, 130, 0), (60, -20)),
        P("correa", prisma((150, 0, -60), Z, estadio(300, 110), 22, hueco=estadio(276, 86), lado=CAUCHO, cara=CAUCHO_CARA,
                           hueco_color="#f6f2e7")
          # Dientes de la correa dentada marcados por dentro
          + [polilinea([(150 + x, y, -48.6) for x, y in estadio(282, 92, 24) + estadio(282, 92, 24)[:1]], 2.2, "#3a4144", "3 4")],
          (40, 0, -60), (-85, 30)),
        P("polea_trasera", cilindro((150, -130, 0), X, 64, 26, r2=22), (150, -130, 0), (-75, 50)),
        P("resorte_torque", resorte((210, -130, 0), X, 32, 70, 6), (210, -130, 0), (-30, 85)),
        P("zapatas", cilindro((300, -130, 0), X, 30, 10, ri=10) + zapatas, (300, -130, 0), (20, 85)),
        P("clutch", [], (290, -130, 30), (-60, 70)),
        P("resortes_zapatas", resorte((300, -60, 30), X, 5, 28, 6) + resorte((330, -60, -30), X, 5, 28, 6), (315, -60, 0), (60, -50)),
        P("campana", cilindro((380, -130, 0), X, 66, 46, ri=56, cara=LADO_CLARO, lado=LADO_MEDIO)
          # Nervios de refuerzo alrededor de la campana
          + [f for x in (366, 380, 394) for f in cilindro((x, -130, 0), X, 67.5, 2.5, ri=56, cara=LADO_MEDIO, lado=OSCURO, grosor=1)],
          (380, -130, 0), (60, 60)),
    ]
    lineas = [linea((-90, 130, 0), (260, 130, 0)), linea((100, -130, 0), (480, -130, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 4. Bomba de aceite y drenaje
# ---------------------------------------------------------------------------
def _aceite():
    carter = [(-90, 36), (-66, 72), (12, 78), (84, 54), (102, 6), (84, -42), (36, -60), (-36, -60), (-84, -30)]
    piezas = [
        P("carter", prisma((0, 60, 0), Z, carter, 44, lado="#e9e4d8", cara="#f7f4ec")
          + cilindro((40, 60, 23), Z, 22, 3, ri=9), (-40, 90, 20), (-70, -70)),
        P("bomba", prisma((150, 80, 100), Z, engranaje(46, 30), 10, hueco=iso._circ2d(12, 20)) + cilindro((150, 80, 100), Z, 16, 12),
          (150, 80, 100), (65, -55)),
        P(None, perno((200, 60, 140), (0, 0, -1), 22, 6) + perno((180, 30, 140), (0, 0, -1), 22, 6), (190, 45, 140), (70, 20), herraje="h_tornillo"),
        P("malla", cilindro((-20, -60, 30), Y, 15, 34, ri=9, cara="#f4f1e8") + puntos_en_cara((-20, -60, 30), Y, 34, 12, 8, 2.2),
          (-20, -60, 30), (-75, 0)),
        P("resorte", resorte((-20, -108, 30), Y, 11, 40, 6), (-20, -108, 30), (-75, 0)),
        P("oring", oring((-20, -142, 30), Y, 20), (-20, -142, 30), (-75, 10)),
        P("tapon", cilindro((-20, -165, 30), Y, 24, 12) + prisma((-20, -180, 30), Y, hexagono(17), 14, lado=LADO_MEDIO),
          (-20, -170, 30), (-75, 20)),
    ]
    lineas = [linea((-20, 10, 30), (-20, -200, 30)), linea((150, 80, 40), (150, 80, 150))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 5. Admisión y filtro de aire
# ---------------------------------------------------------------------------
def _admision():
    pliegues = [polilinea([(190 + x, 0 - 48, 136.5), (190 + x, 0 + 48, 136.5)], 1.2) for x in range(-92, 96, 8)]
    tubo = curva((260, 90, 60), (320, 40, 120), (300, -40, 160))
    piezas = [
        P("caja", prisma((150, 40, 0), Z, redondeado(240, 140, 34), 56, lado="#e9e4d8", cara="#f7f4ec"), (230, 90, 0), (60, -70)),
        P("filtro", prisma((190, 0, 130), Z, redondeado(210, 112, 18), 13, lado="#ece3cc", cara="#f9f4e4") + pliegues,
          (190, 0, 130), (-40, 95)),
        P("tapa", prisma((240, -50, 250), Z, redondeado(244, 144, 34), 14, lado="#e2dccc", cara="#f1ece0"), (300, -80, 250), (60, 70)),
        P("ducto", cilindro((15, 60, 0), X, 24, 64, r2=19, lado="#c7ccce", cara="#dfe3e4"), (15, 60, 0), (-30, -80)),
        P("cuerpo_aceleracion", caja((-45, 60, 0), (40, 52, 52)) + cilindro((-45, 60, 0), X, 18, 42, ri=14), (-45, 60, 0), (-60, -75)),
        P("motor_ralenti", caja((-45, 105, -10), (20, 18, 20), colores=(OSCURO, LADO_MEDIO, OSCURO)), (-45, 105, -10), (-60, -40)),
        P("inyector", cilindro((-95, 105, 10), Y, 7, 46, lado=OSCURO, cara=LADO_MEDIO) + cilindro((-95, 76, 10), Y, 3, 12),
          (-95, 105, 10), (-70, -50)),
        P("empaque", oring((-85, 50, 0), X, 19), (-85, 50, 0), (-65, 40)),
        P("multiple", cilindro((-125, 40, 0), X, 20, 36, r2=15), (-125, 40, 0), (-70, 60)),
        P("manguera", manguera(tubo, 7), tubo[8], (70, 40)),
        P(None, perno((140, -90, 290), (0, 0, -1), 24, 6) + perno((340, -80, 290), (0, 0, -1), 24, 6), (140, -90, 290), (-60, 60), herraje="h_tornillo"),
    ]
    lineas = [linea((150, 40, 30), (240, -50, 300)), linea((-160, 50, 0), (60, 60, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 6. Cilindro, culata y bujía
# ---------------------------------------------------------------------------
def _culata():
    aletas_culata = [f for k in range(4) for f in caja((0, 150 + k * 9, 0), (140, 2.5, 108), colores=(LADO_CLARO, BLANCO, LADO_CLARO), grosor=1.3)]
    aletas_cil = [f for k in range(5) for f in caja((0, 45 + k * 12, 0), (136, 3, 104), colores=(LADO_CLARO, BLANCO, LADO_CLARO), grosor=1.3)]
    bujia = (cilindro((140, 210, -40), Y, 4, 18) + prisma((140, 228, -40), Y, hexagono(10), 10, lado=LADO_MEDIO)
             + cilindro((140, 250, -40), Y, 8, 34, cara="#fbfaf6", lado="#f1eee6") + cilindro((140, 272, -40), Y, 3, 10))
    piezas = [
        P("tapa_valvulas", caja((0, 290, 0), (122, 34, 92)) + cilindro((0, 309, 0), Y, 20, 4), (0, 290, 0), (-90, -40)),
        P("empaque_tapa", caja((0, 255, 0), (120, 4, 90), colores=(CAUCHO, CAUCHO_CARA, CAUCHO), grosor=1.5), (40, 255, 30), (-90, 10)),
        P("culata", caja((0, 175, 0), (132, 64, 102)) + aletas_culata, (0, 175, 0), (-90, 30)),
        P("bujia", bujia, (140, 245, -40), (70, -40)),
        P("empaque_culata", prisma((0, 118, 0), Y, redondeado(128, 98, 10), 2, hueco=iso._circ2d(40, 32), lado="#c9cfd1"), (40, 118, 30), (-90, 20)),
        P("cilindro", caja((0, 72, 0), (122, 74, 96)) + aletas_cil + cilindro((0, 72, 0), Y, 40, 76, ri=36), (0, 72, 0), (-95, 40)),
        P("empaque_cilindro", prisma((0, 22, 0), Y, redondeado(118, 92, 10), 2, hueco=iso._circ2d(42, 32), lado="#c9cfd1"), (40, 22, 30), (-90, 30)),
        P("esparragos", cilindro((-150, 150, 40), Y, 4, 230) + cilindro((-150, 150, -40), Y, 4, 230), (-150, 220, 0), (-60, -50)),
        P(None, perno((150, 140, 60), MENOS_Y, 34, 7) + perno((170, 140, 20), MENOS_Y, 34, 7), (160, 140, 40), (70, 30), herraje="h_tornillo"),
        P("guias", cilindro((150, 40, 60), Y, 6, 14, ri=3) + cilindro((175, 40, 30), Y, 6, 14, ri=3), (160, 40, 45), (70, 40)),
    ]
    lineas = [linea((0, -10, 0), (0, 330, 0)), linea((140, 190, -40), (140, 290, -40))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 7. Válvulas y balancines
# ---------------------------------------------------------------------------
def _valvulas():
    def pila(x):
        return {
            "valvula": cilindro((x, 40, 0), Y, 3, 130) + cilindro((x, -28, 0), Y, 20, 8, r2=4),
            "sello": cilindro((x, 112, 0), Y, 6, 11, cara=CAUCHO_CARA, lado=CAUCHO),
            "base": arandela((x, 128, 0), Y, 17, 2.5),
            "resorte": resorte((x, 168, 0), Y, 15, 62, 7),
            "platillo": cilindro((x, 210, 0), Y, 10, 6, r2=16, ri=4),
            "cunas": caja((x - 4, 226, 0), (5, 12, 7)) + caja((x + 4, 226, 0), (5, 12, 7)),
        }
    a, e = pila(0), pila(170)
    balancin = [(-60, 6), (-50, 16), (40, 12), (66, 4), (66, -6), (40, -12), (-50, -14), (-62, -4)]
    levas = [(math.cos(t) * (14 + 7 * max(0, math.cos(t)) ** 3), math.sin(t) * (14 + 7 * max(0, math.cos(t)) ** 3))
             for t in [i * 2 * math.pi / 32 for i in range(32)]]
    piezas = [
        P("valvula_admision", a["valvula"], (0, -10, 0), (-80, 40)),
        P("valvula_escape", e["valvula"], (170, -10, 0), (70, 40)),
        P("sello", a["sello"] + e["sello"], (0, 112, 0), (-80, 10)),
        P("base_resorte", a["base"] + e["base"], (0, 128, 0), (-80, 25)),
        P("resortes", a["resorte"] + e["resorte"], (0, 168, 0), (-85, 0)),
        P("platillo", a["platillo"] + e["platillo"], (0, 210, 0), (-80, -10)),
        P("cunas", a["cunas"] + e["cunas"], (0, 226, 0), (-80, -30)),
        P("balancin", prisma((85, 285, 0), Z, balancin, 16, hueco=iso._circ2d(8, 16)), (60, 285, 0), (-60, -60)),
        P("eje_balancin", cilindro((85, 285, -70), Z, 6, 80), (85, 285, -100), (60, -50)),
        P("tornillo_calibracion", perno((150, 312, 0), MENOS_Y, 22, 6) + tuerca((150, 300, 0), Y, 7), (150, 312, 0), (65, -45)),
        P("arbol_levas", cilindro((85, 350, 40), Z, 8, 150) + prisma((85, 350, 10), Z, levas, 12) + prisma((85, 350, 50), Z, levas, 12),
          (85, 350, 90), (-70, -50)),
    ]
    lineas = [linea((0, -50, 0), (0, 250, 0)), linea((170, -50, 0), (170, 250, 0)), linea((85, 285, -130), (85, 285, 70))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 8. Radiador y refrigeración
# ---------------------------------------------------------------------------
def _radiador():
    panal = [polilinea([(9.5, -70, z), (9.5, 70, z)], 1.0, "#7f878a") for z in range(-56, 60, 7)]
    aspas = [(math.cos(t) * (50 if i % 2 == 0 else 20), math.sin(t) * (50 if i % 2 == 0 else 20))
             for i, t in enumerate(i * 2 * math.pi / 18 for i in range(18))]
    tubo = curva((0, -90, -40), (40, -170, 20), (140, -190, 90))
    piezas = [
        P("radiador", caja((0, 0, 0), (18, 150, 130)) + panal, (0, 40, 40), (-90, -40)),
        P("tapa", cilindro((0, 100, 45), Y, 13, 10) + cilindro((0, 108, 45), Y, 16, 4), (0, 104, 45), (-70, -50)),
        P("rejilla", prisma((90, 0, 0), X, redondeado(150, 170, 24), 6, lado=OSCURO, cara="#c3c9cb")
          + [polilinea([(93.5, y, -60), (93.5, y - 12, 60)], 2.2, "#7f878a") for y in range(-70, 75, 16)], (90, 40, -40), (70, -50)),
        P("carcasa_ventilador", cilindro((-70, 0, 0), X, 66, 24, ri=58, lado=LADO_MEDIO), (-70, 50, 30), (-80, -30)),
        P("ventilador", prisma((-115, 0, 0), X, aspas, 10, hueco=iso._circ2d(8, 16)), (-115, 0, 0), (-80, 40)),
        P("termostato", caja((80, -150, -90), (30, 26, 26)) + cilindro((80, -137, -90), Y, 8, 4), (80, -150, -90), (60, -30)),
        P("manguera", manguera(tubo, 12), tubo[8], (60, 40)),
        P("drenaje", perno((0, -110, 60), Y, 18, 7), (0, -110, 60), (-70, 30)),
        P("abrazaderas", arandela((40, -170, 25), Z, 16, 3) + arandela((120, -188, 80), Z, 16, 3), (40, -170, 25), (-60, 50)),
        P("empaques", oring((-30, 100, 45), Y, 12) + oring((-30, -110, 60), Y, 9), (-30, 100, 45), (-70, 30)),
        P(None, perno((140, 60, 0), (-1, 0, 0), 30, 6) + perno((140, -60, 0), (-1, 0, 0), 30, 6), (140, 60, 0), (70, 20), herraje="h_tornillo"),
    ]
    lineas = [linea((-150, 0, 0), (130, 0, 0)), linea((0, 90, 45), (0, 130, 45))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 9. Rueda
# ---------------------------------------------------------------------------
def _rueda():
    rin = cilindro((0, 0, 0), X, 108, 44, ri=24, cara="#f3f4f4", lado=LADO_MEDIO)
    a, u, v = iso.base(X)
    frente = (22, 0, 0)
    for k in range(5):
        ang = k * 2 * math.pi / 5 + 0.3
        ventana = []
        for i in range(9):
            t = ang + (i / 8) * 0.9
            ventana.append(iso._sum(frente, iso._mul(u, math.cos(t) * 92), iso._mul(v, math.sin(t) * 92)))
        for i in range(8, -1, -1):
            t = ang + 0.12 + (i / 8) * 0.66
            ventana.append(iso._sum(frente, iso._mul(u, math.cos(t) * 40), iso._mul(v, math.sin(t) * 40)))
        rin.append(Forma([iso._p2(ventana)], HUECO, 1.4))
    llanta = cilindro((0, 0, 0), X, 155, 58, ri=108, cara=CAUCHO_CARA, lado=CAUCHO, hueco_color="none")
    piezas = [
        P("llanta", llanta, (0, 130, 0), (-70, -70), orden=0),
        P("rin", rin, (0, -60, 60), (-80, 75), orden=1),
        P("valvula", cilindro((10, 100, 30), Y, 3, 22, lado=OSCURO), (10, 110, 30), (60, -60)),
        P("eje", cilindro((-300, 0, 0), X, 7, 200) + prisma((-405, 0, 0), X, hexagono(11), 10, lado=LADO_MEDIO), (-380, 0, 0), (-60, -60)),
        P("buje", cilindro((-200, 0, 0), X, 13, 44, ri=8), (-200, 0, 0), (-50, 60)),
        P("retenedores", retenedor((-165, 0, 0), X, 25) + retenedor((165, 0, 0), X, 25), (-165, 0, 0), (-60, -65)),
        P("rodamientos", rodamiento((-140, 0, 0), X, 23, 10) + rodamiento((140, 0, 0), X, 23, 10), (-140, 0, 0), (-50, 70)),
        P("sensor_abs", cilindro((-90, 0, 0), X, 58, 3, ri=42) + puntos_en_cara((-90, 0, 0), X, 3, 50, 28, 2.6), (-90, -40, 40), (-70, 60)),
        # Sensor de velocidad (o ABS) con su cable: va frente al anillo del encoder
        P("sensor_cable", caja((-96, 78, 52), (16, 26, 16), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + manguera([(-96, 92, 52), (-96, 130, 60), (-90, 170, 90), (-70, 200, 130)], 5, "#3c4447"),
          (-96, 84, 52), (-55, -60), orden=2),
        # Kit de reparación de la maza (rodamientos, retenes y espaciador), dentro de su recuadro como en el plano
        P("kit", rodamiento((-150, -230, 160), X, 20, 10) + retenedor((-122, -230, 160), X, 21) + cilindro((-80, -230, 160), X, 9, 46, ri=5)
          + retenedor((-38, -230, 160), X, 21) + rodamiento((-10, -230, 160), X, 20, 10),
          (20, -200, 160), (60, 40), orden=3),
        # Disco de freno al lado izquierdo de la maza (solo aparece en las láminas que lo traen)
        P("disco", _disco_petalo((-345, 0, 0), 92, 5), (-345, 70, 40), (-60, -70), orden=0),
        P(None, perno((-333, 18, 18), X, 12, 5) + perno((-333, -18, -18), X, 12, 5), (-333, 18, 18), padre="disco", orden=1, herraje="h_tornillo"),
        P(None, perno((-110, 30, 30), X, 14, 5) + perno((-110, -30, -30), X, 14, 5), (-110, 30, 30), (-60, -45), herraje="h_tornillo"),
        P(None, arandela((195, 0, 0), X, 13, 3), (195, 0, 0), (60, -55), herraje="h_arandela"),
        P(None, tuerca((225, 0, 0), X, 13), (225, 0, 0), (60, 45), herraje="h_tuerca"),
    ]
    lineas = [linea((-430, 0, 0), (260, 0, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 10. Suspensión delantera y dirección
# ---------------------------------------------------------------------------
def _botella(c):
    """Botella de la suspensión (aluminio): tubo con anillo de retén arriba y pata del eje con su agujero abajo."""
    x, y, z = c
    formas = cilindro((x, y + 4, z), Y, 20, 182, lado="#d6dbde", cara="#eef1f2")
    formas += cilindro((x, y + 92, z), Y, 22, 10, lado="#c9cfd2", cara="#eef1f2")              # anillo del retén
    formas += cilindro((x, y - 96, z), Y, 22, 14, r2=20, lado="#c9cfd2", cara="#eef1f2")       # cuello hacia la pata
    formas += cilindro((x, y - 112, z + 4), X, 17, 40, ri=7, lado="#c9cfd2", cara="#eef1f2")   # pata con el eje
    return formas


def _suspension_delantera():
    tijera = [(-130, -24), (-120, -30), (120, -30), (132, -22), (132, 22), (120, 30), (-120, 30), (-132, 22)]
    piezas = [
        P("barra_completa", cilindro((-170, 170, 0), Y, 14, 220, lado="#f4f6f6")
          + _botella((-170, -20, 0)), (-170, 60, 0), (-75, -40)),
        P("tapon", tuerca((90, 360, 0), Y, 15), (90, 360, 0), (65, -40)),
        P("barra_cromada", cilindro((90, 250, 0), Y, 14, 180, lado="#f4f6f6"), (90, 250, 0), (70, -30)),
        P("guardapolvo", retenedor((90, 140, 0), Y, 19, 8), (90, 140, 0), (70, -10)),
        P("retenedor", retenedor((90, 118, 0), Y, 19, 7), (90, 118, 0), (70, 15)),
        P("botella", _botella((90, 0, 0)), (90, -30, 0), (70, 30)),
        P("resorte", resorte((180, 200, 0), Y, 11, 190, 16), (180, 220, 0), (70, -40)),
        P("cilindro_amortiguador", cilindro((180, 20, 0), Y, 7, 120, lado=LADO_MEDIO), (180, 20, 0), (70, 30)),
        P("tijera", prisma((-30, 250, -180), Y, tijera, 22, hueco=None, lado=LADO_MEDIO, cara="#f4f5f5")
          # Abrazaderas de las barras en los extremos y el agujero del eje al centro
          + cilindro((-150, 250, -180), Y, 24, 23, ri=14, lado=LADO_MEDIO, cara="#f4f5f5")
          + cilindro((90, 250, -180), Y, 24, 23, ri=14, lado=LADO_MEDIO, cara="#f4f5f5")
          + cilindro((-30, 250, -180), Y, 14, 23.5, ri=8), (-90, 250, -180), (-70, 40)),
        P("eje_direccion", cilindro((-30, 340, -180), Y, 11, 160), (-30, 340, -180), (-70, -20)),
        P("rodamientos_direccion", rodamiento((-30, 440, -180), Y, 22, 9), (-30, 440, -180), (-70, -30)),
        P("tazas", cilindro((-30, 462, -180), Y, 25, 5, ri=13), (-30, 462, -180), (60, -40)),
        P(None, perno((60, 420, -140), MENOS_Y, 30, 7) + perno((90, 420, -100), MENOS_Y, 30, 7), (75, 420, -120), (65, -30), herraje="h_tornillo"),
    ]
    lineas = [linea((90, -150, 0), (90, 390, 0)), linea((180, -60, 0), (180, 310, 0)), linea((-30, 230, -180), (-30, 490, -180))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 11. Basculante y amortiguadores
# ---------------------------------------------------------------------------
def _amortiguadores():
    def amortiguador(x, z):
        return (cilindro((x, 230, z), Z, 11, 22, ri=5) + cilindro((x, 195, z), Y, 15, 48, lado=OSCURO, cara=LADO_MEDIO)
                + cilindro((x, 120, z), Y, 7, 110, lado="#f4f6f6") + resorte((x, 125, z), Y, 22, 120, 9)
                + cilindro((x, 55, z), Y, 13, 26, lado=OSCURO, cara=LADO_MEDIO) + cilindro((x, 32, z), Z, 11, 22, ri=5))
    brazo = [(-230, -20), (-210, -46), (60, -70), (170, -60), (220, -20), (220, 30), (170, 60), (60, 50), (-210, 26), (-232, 10)]
    piezas = [
        P("amortiguador", amortiguador(-90, 0) + amortiguador(60, -120), (-90, 140, 0), (-80, -40)),
        P("basculante", prisma((40, -140, 0), Z, brazo, 52, hueco=iso._circ2d(26, 24), lado=LADO_CLARO)
          # Panel rebajado (sección de caja), ranura del eje trasero y tensor de cadena con su tornillo
          + prisma((-92, -140, 26.5), Z, redondeado(150, 50, 22), 1.2, lado=LADO_MEDIO, cara="#e8ecee", grosor=1.2)
          + prisma((172, -140, 26.5), Z, estadio(70, 18), 1.4, lado=OSCURO, cara=HUECO, grosor=1.4)
          + caja((232, -140, 0), (16, 26, 44), colores=(LADO_MEDIO, BLANCO, LADO_CLARO))
          + perno((250, -140, 0), (-1, 0, 0), 40, 7)
          + cilindro((-180, -138, 0), Z, 16, 60, ri=8), (120, -140, 0), (60, 60)),
        P("bujes", cilindro((-180, -138, 70), Z, 12, 18, cara=CAUCHO_CARA, lado=CAUCHO)
          + cilindro((-180, -138, 100), Z, 12, 18, cara=CAUCHO_CARA, lado=CAUCHO), (-180, -138, 85), (-70, 40)),
        P(None, perno((-90, 230, -60), Z, 60, 8) + perno((-180, -138, -80), Z, 150, 9), (-90, 230, -60), (-70, -40), herraje="h_tornillo"),
        P(None, arandela((-90, 230, 40), Z, 10, 2.5) + arandela((-180, -138, 130), Z, 13, 2.5), (-90, 230, 40), (60, -40), herraje="h_arandela"),
        P(None, tuerca((-90, 230, 60), Z, 9) + tuerca((-180, -138, 150), Z, 11), (-180, -138, 150), (-60, 40), herraje="h_tuerca"),
        P("retenedor", retenedor((130, -140, 60), Z, 27, 7), (130, -140, 60), (60, 40)),
    ]
    lineas = [linea((-90, 230, -100), (-90, 230, 90)), linea((-180, -138, -100), (-180, -138, 180))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 12. Sistema eléctrico y batería
# ---------------------------------------------------------------------------
def _bateria(c):
    """Batería de moto: caja oscura con tapa clara, bornes (+ rojo, − negro), etiqueta y ventila."""
    x, y, z = c
    formas = caja((x, y - 6, z), (110, 68, 70), colores=("#4c5458", "#6b7579", "#3f474b"))
    formas += caja((x, y + 34, z), (114, 12, 74), colores=("#8a9498", "#c9d0d3", "#7a8488"))       # tapa
    formas += caja((x + 56, y - 8, z), (1, 34, 52), colores=("#f26522", "#f26522", "#f26522"), grosor=1)   # etiqueta naranja
    formas += caja((x, y - 8, z + 36), (78, 30, 1), colores=("#e8a93a",) * 3, grosor=1)             # banda mostaza al frente
    formas += cilindro((x - 34, y + 46, z + 20), Y, 7, 12, lado="#b84a3a", cara="#e7705a")       # borne +
    formas += cilindro((x + 34, y + 46, z + 20), Y, 7, 12, lado=CAUCHO, cara=CAUCHO_CARA)        # borne −
    formas += caja((x, y + 41, z - 22), (40, 3, 8), colores=(OSCURO, LADO_MEDIO, OSCURO), grosor=1)   # ventila
    return formas


def _electrico():
    arnes = curva((-220, -40, 60), (-60, -10, 160), (160, -60, 120)) + curva((160, -60, 120), (260, -90, 80), (320, -60, -20))[1:]
    fusibles = []
    for i, c in enumerate(["#8fb8d4", "#f0cd7c", "#e7a08f", "#9cc7a6"]):
        fusibles += caja((-150 + i * 22, 70, -80), (14, 24, 6), colores=(c, c, c), grosor=1.5)
    piezas = [
        P("bateria", _bateria((0, 40, 0)), (0, 60, 0), (60, -70)),
        P("fusibles", fusibles, (-120, 80, -80), (-60, -60)),
        P("rele", caja((-160, 0, 40), (32, 32, 26), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + caja((-160, 18, 40), (34, 4, 28), colores=(CAUCHO, CAUCHO_CARA, CAUCHO))
          + [f for i in (-8, 0, 8) for f in caja((-160 + i, -20, 40), (3, 8, 6), colores=("#d8b36a",) * 3, grosor=1)],
          (-160, 0, 40), (-70, -30)),
        P("arnes", manguera(arnes, 7, "#7a8488"), arnes[10], (-60, 60)),
        P("switch", cilindro((200, 40, -40), Y, 26, 30) + caja((200, 58, -40), (8, 6, 16), colores=(CAUCHO,) * 3), (200, 40, -40), (60, -50)),
        P("llave", prisma((280, -20, 60), Z, redondeado(40, 62, 16), 12, lado=OSCURO, cara=LADO_MEDIO), (280, -20, 60), (60, 30)),
        P("sensor_pata", caja((-200, -110, 140), (34, 20, 22), colores=(OSCURO, LADO_MEDIO, OSCURO)), (-200, -110, 140), (-60, 40)),
        P("modulo", caja((80, -140, 200), (70, 20, 50), colores=(OSCURO, LADO_MEDIO, OSCURO))
          # Aletas de disipación del regulador / módulo
          + [f for i in range(-3, 4) for f in caja((80 + i * 9, -126, 200), (3, 8, 48), colores=(OSCURO, LADO_CLARO, LADO_MEDIO), grosor=1)],
          (80, -140, 200), (60, 40)),
        P(None, perno((0, 140, 30), MENOS_Y, 20, 6), (0, 140, 30), (60, -40), herraje="h_tornillo"),
    ]
    return piezas, []


# ---------------------------------------------------------------------------
# 13. Kit de arrastre: cadena, piñón de salida y corona (motos de cadena)
# ---------------------------------------------------------------------------
def _yz(cy, cz, r, desde, hasta, n=14, x=0):
    """Puntos de un arco en el plano vertical de la cadena (Y arriba, Z a lo largo de la moto)."""
    return [(x, cy + r * math.sin(desde + (hasta - desde) * i / n), cz + r * math.cos(desde + (hasta - desde) * i / n))
            for i in range(n + 1)]


# ---------------------------------------------------------------------------
# 14. Freno de tambor (campana, bandas, resortes y leva)
# ---------------------------------------------------------------------------
def _freno_tambor():
    def banda(lado):
        arco = [(math.cos(t) * 92, math.sin(t) * 92 * lado) for t in [i * 0.15 + 0.25 for i in range(19)]]
        interior = [(math.cos(t) * 72, math.sin(t) * 72 * lado) for t in [i * 0.15 + 0.25 for i in range(18, -1, -1)]]
        return arco + interior
    def zapata(lado, x):
        return (prisma((x, 0, 0), X, banda(lado), 16, lado=LADO_MEDIO, cara="#f4f1e8")
                + prisma((x + 9, 0, 0), X, [(math.cos(t) * 92, math.sin(t) * 92 * lado) for t in [i * 0.15 + 0.25 for i in range(19)]]
                         + [(math.cos(t) * 84, math.sin(t) * 84 * lado) for t in [i * 0.15 + 0.25 for i in range(18, -1, -1)]],
                         3, lado=OSCURO, cara=FRICCION))
    piezas = [
        P("campana", cilindro((-150, 0, 0), X, 112, 40, ri=98, cara="#f3f4f4", lado=LADO_MEDIO) + cilindro((-175, 0, 0), X, 40, 12, ri=14),
          (-150, 100, 50), (-70, -70), orden=0),
        P("plato", cilindro((120, 0, 0), X, 108, 10, ri=16, cara="#f6f6f4", lado=LADO_MEDIO), (120, -70, -70), (60, 70), orden=0),
        P("bandas", zapata(1, 40) + zapata(-1, 40), (40, 0, 90), (-60, -60), orden=1),
        P("resortes", resorte((40, 0, 70), Y, 6, 48, 7) + resorte((40, 0, -70), Y, 6, 48, 7), (40, 30, 70), (60, -55), orden=2),
        P("leva", cilindro((70, 0, 92), X, 13, 70) + prisma((36, 0, 92), X, [(-6, -14), (6, -14), (8, 14), (-8, 14)], 10, lado=LADO_MEDIO),
          (70, 0, 92), (70, -30), orden=2),
        P("palanca", prisma((150, 30, 92), X, [(-10, -12), (10, -12), (12, 110), (-12, 110)], 10, lado=OSCURO, cara=LADO_MEDIO),
          (150, 120, 92), (60, -60), orden=3),
        P("indicador", prisma((140, 0, 92), X, [(0, -20), (22, -4), (22, 4), (0, 20)], 4, lado="#c9a227", cara="#f0cd7c"),
          (140, -20, 100), (70, 40), orden=3),
        P("retenedor", retenedor((180, 0, 0), X, 22), (180, 0, 0), (60, 30), orden=3),
        P(None, tuerca((200, 0, 0), X, 12) + tuerca((170, 120, 92), X, 7), (200, 0, 0), (60, 60), orden=4, herraje="h_tuerca"),
        P(None, perno((160, 110, 92), X, 30, 6), (160, 110, 92), (60, -30), orden=4, herraje="h_tornillo"),
    ]
    lineas = [linea((-230, 0, 0), (240, 0, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 15. Encendido: bujía, capuchón, bobina, CDI/regulador y magneto
# ---------------------------------------------------------------------------
def _encendido():
    cable = curva((-60, 40, 120), (40, 90, 60), (130, 30, -20))
    piezas = [
        P("magneto", cilindro((-60, -80, -140), Z, 96, 40, ri=20, cara="#f3f4f4", lado=LADO_MEDIO)
          + puntos_en_cara((-60, -80, -140), Z, 40, 66, 8, 9, color="#c9a227"), (-60, 10, -140), (-70, -60), orden=0),
        P("estator", cilindro((-60, -80, -80), Z, 64, 22, ri=22, cara="#e9d3a8", lado="#c9a227"), (-60, -40, -80), (-75, 40), orden=1),
        P("bujia", cilindro((-60, 80, 120), Y, 9, 50, cara=BLANCO) + prisma((-60, 120, 120), Y, hexagono(11), 16, lado=LADO_MEDIO)
          + cilindro((-60, 150, 120), Y, 7, 40, cara="#f4f1e8", lado="#e9e4d8"), (-60, 150, 120), (-60, -60), orden=2),
        P("capuchon", cilindro((-60, 215, 120), Y, 13, 46, cara=CAUCHO_CARA, lado=CAUCHO), (-60, 225, 120), (-60, -50), orden=3),
        # Antivibrante (caucho) del capuchón: el sello que entra sobre la bujía, separado en el despiece
        P("antivibrante", cilindro((-60, 182, 120), Y, 15, 12, ri=8, cara="#7b8385", lado=CAUCHO), (-60, 182, 135), (60, -10), orden=3),
        P("cables", manguera([(-60, 230, 120)] + cable, 6, "#5d666a"), cable[6], (-30, 60), orden=2),
        P("bobina", caja((150, 30, -20), (70, 50, 40), colores=(OSCURO, LADO_MEDIO, OSCURO)), (150, 50, -20), (60, -60), orden=2),
        P("cdi", caja((180, -90, 120), (80, 18, 55), colores=(OSCURO, LADO_MEDIO, OSCURO)), (180, -90, 120), (60, 40), orden=2),
        P("regulador", caja((250, 60, 160), (60, 22, 60), colores=("#5d666a", "#7a8488", "#4c5458"))
          + [f for i in range(5) for f in caja((250, 75, 160 - 24 + i * 12), (60, 6, 3), colores=("#4c5458",) * 3, grosor=1)],
          (250, 70, 160), (60, -40), orden=3),
        P(None, perno((150, 60, 20), Z, 18, 5) + perno((-10, -80, -110), Z, 18, 5), (150, 60, 20), (60, 30), orden=4, herraje="h_tornillo"),
    ]
    return piezas, [linea((-60, 60, 120), (-60, 260, 120))]


# ---------------------------------------------------------------------------
# 16. Caja de cambios y piñón de salida
# ---------------------------------------------------------------------------
def _transmision():
    yp, ys = 95, -70                               # eje principal (arriba) y eje de salida (abajo)
    radios_p, radios_s = [24, 30, 36, 42, 48], [66, 60, 54, 48, 42]

    def engrane(x, y, r):
        return prisma((x, y, 0), X, engranaje(r, max(12, int(r * .62))), 13, hueco=iso._circ2d(9), cara="#f6f6f4", lado=LADO_MEDIO)
    horquilla = [(-26, -6), (-26, 34), (-16, 34), (-16, 6), (16, 6), (16, 34), (26, 34), (26, -6), (6, -6), (6, -40), (-6, -40), (-6, -6)]
    cadena = _yz(ys, 0, 44, math.pi, 2 * math.pi, 12, x=330)
    cadena = [(330, cadena[-1][1], -230)] + cadena[::-1] + [(330, cadena[0][1], -230)]
    piezas = [
        P("eje_principal", cilindro((40, yp, 0), X, 8, 430), (-170, yp, 0), (-60, -55), orden=0),
        P("engranajes", [f for i, r in enumerate(radios_p) for f in engrane(-110 + i * 58, yp, r)], (-110 + 2 * 58, yp + 36, 0), (-20, -95), orden=1),
        P("eje_salida", cilindro((50, ys, 0), X, 9, 470), (-180, ys, 0), (-65, 55), orden=0),
        P("engranajes_salida", [f for i, r in enumerate(radios_s) for f in engrane(-110 + i * 58, ys, r)], (-110 + 3 * 58, ys - 50, 0), (40, 95), orden=1),
        P("horquillas", [f for k in range(3) for f in prisma((-80 + k * 100, yp + 125, 0), X, horquilla, 6, lado=LADO_MEDIO, cara="#f1f1ee")],
          (20, yp + 150, 0), (-60, -50), orden=2),
        P("tambor_selector", cilindro((20, yp + 200, 0), X, 17, 230)
          + [f for k in range(3) for f in cilindro((-60 + k * 80, yp + 200, 0), X, 18, 4, cara=HUECO)], (130, yp + 200, 0), (60, -50), orden=1),
        P("rodamientos", rodamiento((-200, yp, 0), X, 17, 10) + rodamiento((-215, ys, 0), X, 19, 10), (-200, yp, 0), (-60, 45), orden=2),
        P("reten", retenedor((285, ys, 0), X, 17), (285, ys, 0), (60, -55), orden=2),
        P("pinon", prisma((330, ys, 0), X, engranaje(38, 14, 7), 9, hueco=iso._circ2d(10), cara="#f6f6f4", lado=LADO_MEDIO),
          (330, ys + 38, 0), (70, -40), orden=3),
        P("cadena", manguera(cadena, 8, "#7a8488"), cadena[-1], (60, 40), orden=2),
    ]
    lineas = [linea((-260, yp, 0), (300, yp, 0)), linea((-260, ys, 0), (380, ys, 0)), linea((-140, yp + 200, 0), (180, yp + 200, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 17. Carcasa del motor, tapa del clutch y filtro de aceite
# ---------------------------------------------------------------------------
# Perfil lateral del cárter (u = adelante, v = arriba): boca del cilindro arriba, lóbulo de la caja atrás, sumidero abajo
_CARTER = [(-160, -20), (-152, 48), (-118, 86), (-62, 96), (-46, 128), (46, 128), (62, 100), (118, 90), (156, 46),
           (166, -18), (142, -82), (78, -116), (-14, -124), (-98, -104), (-146, -62)]
_TAPA_CLUTCH = [(-64, 36), (-44, 84), (26, 96), (94, 66), (118, 4), (98, -60), (24, -92), (-48, -64)]


def _media_carcasa(x0, grueso=60):
    """Una mitad del cárter (eje X = lado de la moto): cuerpo, boca del cilindro, alojamientos de los ejes,
    tornillos del borde, orejas de montaje y nervios. Con eje X, el punto (u, v) del perfil queda en z = -u, y = v."""
    cara = x0 + grueso / 2
    f = prisma((x0, 0, 0), X, _CARTER, grueso, lado="#e6e0d2", cara="#f6f3eb")
    # Boca del cilindro en la cubierta superior y los espárragos
    f += cilindro((x0, 129, 0), Y, 30, 3, ri=24, cara="#efe9dc")
    f += cilindro((x0, 150, 34), Y, 3.5, 40, cara=BLANCO) + cilindro((x0, 150, -34), Y, 3.5, 40, cara=BLANCO)
    # Alojamientos: cigüeñal (grande) y los dos ejes de la caja
    for (u, v, r) in ((0, 8, 44), (92, -40, 27), (62, -84, 19)):
        f += cilindro((cara + 3, v, -u), X, r, 6, ri=r * 0.5, cara="#efe9dc", lado="#ddd5c4")
        f += cilindro((cara + 6.5, v, -u), X, r * 0.5, 1, ri=r * 0.42, cara=HUECO, grosor=1)
    # Nervios de refuerzo entre los alojamientos
    for a, b in (((0, 8), (92, -40)), ((0, 8), (62, -84)), ((0, 8), (-120, 40)), ((0, 8), (-90, -90))):
        f.append(polilinea([(cara + 1, a[1], -a[0]), (cara + 1, b[1], -b[0])], 2.4, "#cfc6b2"))
    # Tornillos alrededor del borde
    for (u, v) in _CARTER[::2]:
        f += cilindro((cara + 2, v * 0.9, -u * 0.9), X, 6.5, 4, ri=2.6, lado=LADO_MEDIO, cara="#e9e4d8", grosor=1.4)
    # Orejas de montaje al chasis (adelante arriba y atrás abajo)
    f += cilindro((x0, 62, 168), X, 12, grueso, ri=5, lado="#e6e0d2", cara="#f6f3eb")
    f += cilindro((x0, -74, -158), X, 12, grueso, ri=5, lado="#e6e0d2", cara="#f6f3eb")
    return f


def _tapa_clutch(c):
    """Tapa del clutch: placa con la cúpula del clutch y tornillos alrededor."""
    x, y, z = c
    f = prisma(c, X, _TAPA_CLUTCH, 24, lado="#ddd6c7", cara="#f0ebdf")
    f += cilindro((x + 18, y + 4, z - 28), X, 58, 12, cara="#f3efe6", lado="#ddd6c7")       # cúpula del clutch
    f += cilindro((x + 25, y + 4, z - 28), X, 22, 2, cara="#e9e3d6", lado="#ddd6c7")
    for (u, v) in _TAPA_CLUTCH:
        f += prisma((x + 14, y + v * 0.88, z - u * 0.88), X, hexagono(5), 4, lado=LADO_MEDIO)
    return f


def _carcasa():
    piezas = [
        P("carcasa_izq", _media_carcasa(-170), (-170, 128, 30), (-70, -70), orden=0),
        P("empaques", prisma((-92, 0, 0), X, _CARTER, 2, hueco=[(u * .93, v * .93) for u, v in _CARTER], lado="#8d9391", cara="#a9aeac")
          + prisma((84, 10, 20), X, _TAPA_CLUTCH, 2, hueco=[(u * .9, v * .9) for u, v in _TAPA_CLUTCH], lado="#8d9391", cara="#a9aeac"),
          (-92, 110, -40), (-30, -85), orden=1),
        P("carcasa_der", _media_carcasa(0), (0, 128, -30), (40, -95), orden=2),
        P("rodamientos", rodamiento((-118, 8, 0), X, 30, 14) + rodamiento((-122, -40, -92), X, 18, 10), (-118, 8, 0), (-70, 50), orden=1),
        P("reten", retenedor((-230, 8, 0), X, 24), (-230, 8, 0), (-60, 40), orden=1),
        P("swiche", cilindro((-220, -80, 60), X, 9, 20, lado=OSCURO, cara=LADO_MEDIO) + cilindro((-235, -80, 60), X, 3, 14),
          (-225, -80, 60), (-60, 55), orden=1),
        P("tapa_clutch", _tapa_clutch((110, 10, 20)), (110, 96, 0), (50, -80), orden=3),
        P("visor", cilindro((126, -52, 70), X, 12, 4, cara="#cfe6f1", lado="#9fbfcc"), (126, -52, 70), (70, 30), orden=4),
        P("tapon_llenado", cilindro((110, 110, -20), Y, 9, 22) + cilindro((110, 126, -20), Y, 13, 8, lado=OSCURO),
          (110, 130, -20), (60, -50), orden=4),
        P("filtro", cilindro((215, 30, -20), X, 26, 40, ri=10, cara="#f9f4e4", lado="#e6dcc0")
          + [polilinea([(196, 30 + math.sin(t) * 26, -20 + math.cos(t) * 26), (234, 30 + math.sin(t) * 26, -20 + math.cos(t) * 26)], 1)
             for t in [i * 0.5 for i in range(13)]], (215, 56, -20), (60, -55), orden=5),
        P("tapa_filtro", cilindro((270, 30, -20), X, 32, 10) + perno((285, 55, -40), X, 16, 5), (270, 30, -20), (60, 40), orden=6),
        P("bomba", prisma((60, -60, 70), X, engranaje(28, 18), 10, hueco=iso._circ2d(7)), (60, -60, 70), (50, 70), orden=3),
        P("malla", cilindro((0, -170, 20), Y, 14, 40, ri=8, cara="#f4f1e8") + puntos_en_cara((0, -170, 20), Y, 40, 11, 8, 2),
          (0, -170, 20), (-70, 10), orden=1),
        P("tapon", cilindro((0, -220, 20), Y, 20, 10) + prisma((0, -233, 20), Y, hexagono(14), 12, lado=LADO_MEDIO),
          (0, -225, 20), (-70, 20), orden=1),
    ]
    lineas = [("carcasa_der", linea((-260, 8, 0), (300, 8, 0))), ("malla", linea((0, -124, 20), (0, -255, 20))),
              ("filtro", linea((150, 30, -20), (300, 30, -20)))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 18. Rueda trasera con arrastre (corona, porta sprocket, cauchos, disco, tensores)
# ---------------------------------------------------------------------------
def _arrastre_trasero():
    """Corona, porta sprocket con sus cauchos y cadena, al lado izquierdo de la rueda trasera (eje X)."""
    cadena = _yz(0, 0, 106, 0.2, math.pi - 0.2, 14, x=345)
    cadena = [(345, cadena[0][1], 330)] + cadena + [(345, cadena[-1][1], 330)]
    return [
        P("cauchos", [f for k in range(4) for f in caja((270, math.sin(k * 1.57 + .8) * 46, math.cos(k * 1.57 + .8) * 46), (16, 20, 20),
                                                         colores=(CAUCHO, CAUCHO_CARA, CAUCHO))], (270, -40, 40), (40, 70), orden=2),
        P("porta_sprocket", cilindro((305, 0, 0), X, 70, 26, ri=18, cara=LADO_CLARO, lado=LADO_MEDIO), (305, 55, -40), (40, -80), orden=3),
        P("corona", prisma((345, 0, 0), X, engranaje(104, 42, 9), 6, hueco=iso._circ2d(24), cara="#f6f6f4", lado=LADO_MEDIO)
          + puntos_en_cara((345, 0, 0), X, 6, 48, 4, 6), (345, 90, -40), (60, -60), orden=4),
        P("cadena", manguera(cadena, 8, "#7a8488"), cadena[-1], (50, 40), orden=5),
    ]


def _rueda_trasera():
    piezas, _ = _rueda()
    piezas += [
        P("tensores", caja((-450, 0, 0), (14, 26, 70), colores=(LADO_MEDIO, BLANCO, LADO_CLARO)) + perno((-450, 0, 40), Z, 46, 6),
          (-450, 0, 30), (-50, 60), orden=0),
    ] + _arrastre_trasero()
    lineas = [linea((-480, 0, 0), (380, 0, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 19. Rueda trasera con freno de tambor y arrastre
# ---------------------------------------------------------------------------
def _rueda_tambor():
    def zapata(lado, x, r=64, ri=50):
        arco = [(math.cos(t) * r, math.sin(t) * r * lado) for t in [i * 0.15 + 0.25 for i in range(19)]]
        return (prisma((x, 0, 0), X, arco + [(math.cos(t) * ri, math.sin(t) * ri * lado) for t in [i * 0.15 + 0.25 for i in range(18, -1, -1)]],
                       12, lado=LADO_MEDIO, cara="#f4f1e8")
                + prisma((x + 7, 0, 0), X, arco + [(math.cos(t) * (r - 6), math.sin(t) * (r - 6) * lado)
                                                   for t in [i * 0.15 + 0.25 for i in range(18, -1, -1)]], 2, lado=OSCURO, cara=FRICCION))
    piezas = [q for q in _rueda()[0] if q.puesto not in ("sensor_abs", "sensor_cable", "disco") and q.padre != "disco"]
    piezas += [
        P("campana", cilindro((-250, 0, 0), X, 80, 30, ri=70, cara="#f3f4f4", lado=LADO_MEDIO), (-250, 72, 40), (-50, -80), orden=0),
        P("bandas", zapata(1, -305) + zapata(-1, -305), (-305, 0, 62), (-40, -80), orden=1),
        P("resortes", resorte((-300, 0, 48), Y, 5, 34, 6) + resorte((-300, 0, -48), Y, 5, 34, 6), (-300, 20, 48), (40, -70), orden=2),
        P("leva", cilindro((-330, 0, 64), X, 9, 50), (-330, 0, 64), (-60, -40), orden=2),
        P("plato", cilindro((-365, 0, 0), X, 76, 8, ri=12, cara="#f6f6f4", lado=LADO_MEDIO), (-365, -55, -50), (-50, 70), orden=1),
        P("palanca", prisma((-385, 22, 64), X, [(-8, -9), (8, -9), (9, 80), (-9, 80)], 8, lado=OSCURO, cara=LADO_MEDIO),
          (-385, 95, 64), (-50, -50), orden=3),
        P("indicador", prisma((-392, 0, 64), X, [(0, -14), (16, -3), (16, 3), (0, 14)], 3, lado="#c9a227", cara="#f0cd7c"),
          (-392, -12, 70), (-60, 30), orden=3),
        P("tensores", caja((-520, 0, 0), (14, 26, 70), colores=(LADO_MEDIO, BLANCO, LADO_CLARO)) + perno((-520, 0, 40), Z, 46, 6),
          (-520, 0, 30), (-50, 60), orden=0),
    ] + _arrastre_trasero()
    return piezas, [linea((-550, 0, 0), (380, 0, 0))]


# ---------------------------------------------------------------------------
# 20. Freno completo: bomba, depósito, manguera, caliper y pedal en una sola lámina
# ---------------------------------------------------------------------------
def _mover(pieza, d):
    """Corre una pieza ya proyectada: como la proyección es lineal, un corrimiento 3D es un corrimiento 2D fijo."""
    ox, oy = iso.proyectar(d)
    for forma in pieza.formas:
        forma.anillos = [[(x + ox, y + oy) for x, y in anillo] for anillo in forma.anillos]
    if pieza.ancla3d is not None:
        pieza.ancla3d = tuple(a + b for a, b in zip(pieza.ancla3d, d))
    return pieza


def _freno_completo():
    CALIPER = (250, -330, -40)                       # el caliper va abajo a la derecha de la bomba
    bomba = [q for q in _bomba_freno()[0] if q.puesto not in ("manguera", "unidad_abs", "soporte_manguera")]
    caliper = [_mover(q, CALIPER) for q in _freno_disco()[0] if q.puesto != "disco" and q.padre != "disco"]
    entrada = tuple(a + b for a, b in zip(CALIPER, (20, 46, -6)))           # entrada de la manguera en el caliper
    tubo = curva((-30, -40, 0), (-70, -230, 30), (entrada[0] - 60, entrada[1] + 90, entrada[2] + 40)) \
        + curva((entrada[0] - 60, entrada[1] + 90, entrada[2] + 40), (entrada[0] - 10, entrada[1] + 60, entrada[2] + 10), entrada)[1:]
    pedal = [(-12, -14), (150, -26), (176, -20), (180, -6), (160, 4), (20, 18), (-10, 16), (-24, 0)]
    piezas = bomba + caliper + [
        P("manguera", manguera(tubo, 8), tubo[10], (-80, 30), orden=2),
        # Guías (grapas) de la manguera a lo largo del recorrido
        P("guia_manguera", caja(tubo[8], (16, 10, 16), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + caja(tubo[20], (16, 10, 16), colores=(OSCURO, LADO_MEDIO, OSCURO)), tubo[20], (60, -30), orden=3),
        # Soporte del depósito (en los frenos traseros el tanque va aparte, atornillado al chasis)
        P("soporte_deposito", prisma((-70, 40, -60), Z, [(-14, 40), (14, 40), (18, -30), (6, -60), (-10, -60), (-18, -30)], 6,
                                     hueco=iso._circ2d(5, 12), lado=LADO_MEDIO), (-70, 20, -60), (-70, -20), orden=1),
        # Pedal del freno trasero con su caucho, el resorte de retorno y el eje
        P("pedal", prisma((-240, -470, 140), Z, pedal, 12, hueco=iso._circ2d(9, 20), lado=LADO_MEDIO, cara="#f1f3f4")
          + cilindro((-240 + 172, -470 - 13, 140 + 14), Z, 11, 26, cara=CAUCHO_CARA, lado=CAUCHO)
          + resorte((-240 + 40, -470 + 30, 150), Y, 6, 46, 7) + cilindro((-240, -470, 120), Z, 8, 46), (-180, -480, 146), (-60, 50), orden=1),
    ]
    lineas = [("bomba", linea((-120, 0, 0), (260, 0, 0))), ("deposito", linea((0, 20, 0), (0, 170, 0))),
              ("piston", linea((CALIPER[0] - 27, CALIPER[1] + 2, CALIPER[2] + 26), (CALIPER[0] - 27, CALIPER[1] + 2, CALIPER[2] + 150))),
              ("pastillas", linea((CALIPER[0] + 70, CALIPER[1] - 36, CALIPER[2] + 25), (CALIPER[0] + 70, CALIPER[1] - 122, CALIPER[2] + 25)))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# Franja de tornillería: va debajo de cada dibujo para que toda pieza pequeña tenga su número.
# ---------------------------------------------------------------------------
def _circlip(c, r):
    ext = [(math.cos(t) * r, math.sin(t) * r) for t in [0.5 + i * (2 * math.pi - 1) / 20 for i in range(21)]]
    return prisma(c, Y, ext + [(x * .78, y * .78) for x, y in ext[::-1]], 2.5, lado=LADO_MEDIO)


HERRAJES = [  # (puesto, nombre en la franja, palabras clave en español e inglés, sin tildes)
    ("h_arandela", "Arandelas", ["ARANDELA", "ARAND", "WASHER", "PLATINA", "PLACA", "PLATE"]),
    ("h_tornillo", "Tornillos", ["TORNILLO", "PERNO", "ESPARRAGO", "REMACHE", "BOLT", "SCREW", "STUD", "RIVET"]),
    ("h_tuerca", "Tuercas", ["CONTRATUERCA", "TUERCA", "NUT"]),
    ("h_seguro", "Seguros", ["ANILLO", "PIN SEGURO", "PIN DE SEGURIDAD", "PIN SEGURIDAD", "SEGURO", "CIRCLIP", "SNAP"]),
    ("h_pin", "Pines", ["PIN", "PASADOR", "CHAVETA", "GUIA DE CENTRADO", "ESPIGA", "DOWEL", "COTTER", "KEY"]),
    ("h_empaque", "Empaques", ["EMPAQUETADURA", "EMPAQUE", "O-RING", "ORING", "JUNTA", "SELLO", "RETENEDOR", "RETEN", "GASKET", "SEAL"]),
    ("h_abrazadera", "Abrazaderas", ["ABRAZADERA", "GRAPA", "SUJETADOR", "BANDA", "CORREA", "CLAMP", "CLIP", "BAND"]),
    ("h_buje", "Bujes", ["BUJE", "CASQUILLO", "ESPACIADOR", "SEPARADOR", "DISTANCIADOR", "COLLAR", "SPACER", "BUSH"]),
    ("h_rodamiento", "Rodamientos", ["RODAMIENTO", "BALINERA", "COJINETE", "RODILLO", "BEARING"]),
    ("h_caucho", "Cauchos", ["CAUCHO", "ANTIVIBRANTE", "AMORTIGUADOR", "DAMPER", "GROMMET", "CUSHION", "RUBBER", "STOPPER", "BUMP", "ABSORBER"]),
    ("h_resorte", "Resortes", ["RESORTE", "SPRING"]),
    ("h_tapa", "Tapas y tapones", ["TAPA", "TAPON", "CUBIERTA", "CAP", "COVER", "PLUG"]),
    ("h_manguera", "Mangueras y tubos", ["MANGUERA", "TUBO", "CONDUCTO", "DUCTO", "HOSE", "PIPE", "TUBE"]),
    ("h_cable", "Cables", ["CABLE", "ARNES", "LEAD", "WIRE"]),
    ("h_electrico", "Eléctricos", ["SWICHE", "SWITCH", "SENSOR", "INTERRUPTOR", "PITO", "HORN", "BOBINA", "RELE", "RELAY",
                                   "DIODO", "DIODE", "FLASHER", "UNIDAD", "COIL", "ECU", "CONTROL UNIT", "BUZZER", "ARRANQUE", "SW"]),
    ("h_soporte", "Soportes", ["SOPORTE", "BRACKET", "BRKT", "STAY", "HOLDER", "GUIA", "GUIDE", "SOSTEN"]),
    ("h_etiqueta", "Calcomanías", ["CALCOMANIA", "ETIQUETA", "EMBLEMA", "LABEL", "EMBLEM", "STICKER", "GRAPHIC"]),
    ("h_eje", "Ejes", ["EJE", "VARILLA", "SHAFT", "ROD", "AXLE"]),
    ("h_valvula", "Válvulas", ["VALVULA", "VALVE"]),
    ("h_engranaje", "Piñones y levas", ["PINON", "ENGRANAJE", "LEVA", "LEVAS", "ARBOL", "CADENILLA", "GEAR", "CAM", "CLUTCH",
                                        "MANZANA", "PORTADISCOS", "PRESIONAD", "BALANCIN"]),
    ("h_tanque", "Tanques", ["TANQUE", "RESERVORIO", "TANK", "RESERVOIR", "COOLER"]),
    ("h_protector", "Protectores", ["PROTECTOR", "GUARDACADENA", "GUARDABARRO", "BAQUELA", "REFLECTOR", "FENDER", "GUARD"]),
    ("h_otros", "Otras piezas", []),
]
_HERRAJES_RE = [(puesto, re.compile(r"\b(" + "|".join(re.escape(p) for p in palabras) + r")(S|ES)?\b"))
                for puesto, _, palabras in HERRAJES if palabras]


# Piezas que se dibujan junto a otra aunque la lámina no les dé número (el sensor sin su anillo del encoder no se entiende)
ACOMPANANTES = {"sensor_cable": ("sensor_abs",)}
# Dónde va un subconjunto al elegirlo (el kit de la maza: en los rodamientos, los retenes y el buje)
DESTINO_SUBCONJUNTO = {"kit": ("rodamientos", "retenedores", "buje")}

DESTINO_POR_TIPO = {
    "h_rodamiento": ["rodamientos", "rodamientos_direccion", "porta_sprocket"],
    "h_empaque": ["retenedores", "retenedor", "reten", "empaques", "empaque", "oring", "sello", "empaque_culata", "empaque_tapa"],
    "h_seguro": ["rodamientos", "retenedores", "retenedor", "pasador", "eje", "eje_principal", "eje_salida"],
    "h_buje": ["buje", "bujes", "porta_sprocket"],
    "h_caucho": ["cauchos"],
    "h_pin": ["pasador", "guias"],
    "h_abrazadera": ["abrazaderas", "abrazadera", "manguera"],
    "h_resorte": ["resorte", "resortes", "resorte_torque", "resortes_zapatas"],
    "h_tapa": ["tapa", "tapon", "tapa_clutch", "tapa_valvulas"],
    "h_manguera": ["manguera", "ducto"],
    "h_cable": ["arnes", "cables", "interruptor", "sensor_cable"],
    "h_electrico": ["interruptor", "swiche", "modulo", "rele", "switch", "cdi"],
    "h_soporte": ["soporte", "abrazadera", "soporte_manguera", "basculante"],
    "h_eje": ["eje", "eje_principal", "eje_salida", "eje_direccion"],
}


def herraje_para(descripcion):
    """Puesto de la franja de tornillería para una pieza que el dibujo no tiene ("h_otros" si no se reconoce)."""
    texto = _sin_tildes(descripcion.upper())
    for puesto, patron in _HERRAJES_RE:
        if patron.search(texto):
            return puesto
    return "h_otros"


_FIGURAS_HERRAJES = {
        "h_arandela": lambda c: arandela(c, Y, 17, 3),
        "h_tornillo": lambda c: perno(iso._sum(c, (0, 22, 0)), MENOS_Y, 40, 9),
        "h_tuerca": lambda c: tuerca(c, Y, 13),
        "h_seguro": lambda c: _circlip(c, 17),
        "h_pin": lambda c: cilindro(c, Y, 4.5, 44, cara=BLANCO),
        "h_empaque": lambda c: oring(c, Y, 17, 3.5),
        "h_abrazadera": lambda c: cilindro(c, Y, 16, 8, ri=14, cara=LADO_CLARO) + caja(iso._sum(c, (14, 0, 14)), (10, 8, 10)),
        "h_buje": lambda c: cilindro(c, Y, 11, 26, ri=6),
        "h_rodamiento": lambda c: rodamiento(c, Y, 18, 9),
        "h_caucho": lambda c: cilindro(c, Y, 14, 18, ri=4, cara=CAUCHO_CARA, lado=CAUCHO),
        "h_resorte": lambda c: resorte(iso._sum(c, (0, -22, 0)), Y, 10, 44, 7),
        "h_tapa": lambda c: cilindro(c, Y, 16, 10, lado=LADO_MEDIO) + cilindro(iso._sum(c, (0, 9, 0)), Y, 9, 8, lado=LADO_MEDIO),
        "h_manguera": lambda c: manguera(curva(iso._sum(c, (-24, -14, 0)), iso._sum(c, (0, 30, 0)), iso._sum(c, (24, -14, 0))), 7),
        "h_cable": lambda c: manguera(curva(iso._sum(c, (-26, 6, 0)), iso._sum(c, (0, -26, 0)), iso._sum(c, (22, 14, 0))), 3, "#3c4447")
          + caja(iso._sum(c, (24, 16, 0)), (10, 10, 12), colores=(OSCURO, LADO_MEDIO, OSCURO)),
        "h_electrico": lambda c: caja(c, (26, 18, 22), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + cilindro(iso._sum(c, (-6, 13, 0)), Y, 2.5, 8) + cilindro(iso._sum(c, (6, 13, 0)), Y, 2.5, 8),
        "h_soporte": lambda c: prisma(c, Z, [(-20, -14), (20, -14), (20, -4), (-6, -4), (-6, 22), (-20, 22)], 5,
                                      hueco=iso._circ2d(3.5, 12), lado=LADO_MEDIO),
        "h_etiqueta": lambda c: prisma(c, Z, redondeado(40, 24, 5), 1.5, lado="#e3a72f", cara="#f2c94c")
          + [polilinea([iso._sum(c, (-14, 4, 1)), iso._sum(c, (14, 4, 1))], 2, "#b8461a"),
             polilinea([iso._sum(c, (-14, -3, 1)), iso._sum(c, (6, -3, 1))], 2, "#b8461a")],
        "h_eje": lambda c: cilindro(c, X, 5, 56) + prisma(iso._sum(c, (-28, 0, 0)), X, hexagono(7), 5, lado=LADO_MEDIO),
        "h_valvula": lambda c: cilindro(iso._sum(c, (0, 6, 0)), Y, 3, 44, cara=BLANCO)
          + cilindro(iso._sum(c, (0, -18, 0)), Y, 13, 3, r2=4, lado=LADO_MEDIO),
        "h_engranaje": lambda c: prisma(c, Z, engranaje(22, 16), 7, hueco=iso._circ2d(6), cara="#f6f6f4", lado=LADO_MEDIO),
        "h_tanque": lambda c: prisma(c, Y, redondeado(30, 22, 9), 34, lado="#d9e6ec", cara="#eef5f8")
          + cilindro(iso._sum(c, (0, 21, 0)), Y, 7, 8, lado=OSCURO),
        "h_protector": lambda c: prisma(c, Z, [(-26, -6), (-14, 10), (12, 14), (28, 4), (24, -2), (10, 6), (-12, 2), (-22, -10)], 6,
                                        lado=OSCURO, cara=LADO_MEDIO),
        "h_otros": lambda c: caja(c, (24, 24, 24), colores=(LADO_MEDIO, BLANCO, LADO_CLARO)),
}
_ORDEN_HERRAJES = [puesto for puesto, _, _ in HERRAJES]
PASO = 56           # separación entre números (unidades del lienzo de 1000). En pantalla el dibujo se ve a ~0,7 px por unidad
                    # y un número de dos cifras mide ~30 × 25 px (~43 × 36 unidades): 56 deja aire entre uno y otro.
PASO_ANCHO = 66      # en la franja, a lo ancho: deja lugar a la insignia ×N del número de al lado
_PIE = 968          # línea del nombre del dibujo


def grupos_desde_texto(texto):
    """'h_arandela:3,h_pin:2' → (('h_arandela', 3), ('h_pin', 2)) en el orden de HERRAJES. Ignora lo que no reconoce."""
    cuenta = {}
    for trozo in (texto or "").split(","):
        nombre, _, n = trozo.partition(":")
        if nombre in _ORDEN_HERRAJES and n.isdigit():
            cuenta[nombre] = max(1, min(60, int(n)))
    return tuple((g, cuenta[g]) for g in _ORDEN_HERRAJES if g in cuenta)


def grupos_a_texto(grupos):
    return ",".join(f"{g}:{n}" for g, n in grupos)


def _columnas(grupos):
    """Disposición de la franja: [(centro, ancho, números por fila)] y filas necesarias.

    Cada grupo recibe un ancho según cuántos números lleva, buscando el menor número de filas que quepa a lo ancho
    (así un grupo con 20 tornillos no apila 10 filas en una columna angosta)."""
    total = LADO - 60
    minimo = min(110, total / len(grupos))
    for filas in range(1, 61):
        anchos = [max(minimo, math.ceil(n / filas) * PASO_ANCHO + 16) for _, n in grupos]
        if sum(anchos) <= total:
            break
    extra = (total - sum(anchos)) / len(grupos)
    anchos = [min(a + extra, max(a, 220)) for a in anchos]
    x = (LADO - sum(anchos)) / 2
    columnas = []
    for (g, n), a in zip(grupos, anchos):
        columnas.append((x + a / 2, a, max(1, int((a - 16) // PASO_ANCHO))))
        x += a
    filas = max(math.ceil(n / pf) for (_, n), (_, _, pf) in zip(grupos, columnas))
    return columnas, filas


DIAGRAMAS = {
    "freno_disco": ("Freno de disco", _freno_disco),
    "bomba_freno": ("Bomba de freno y líquido", _bomba_freno),
    "cvt": ("Variador, correa y clutch", _cvt),
    "aceite": ("Bomba de aceite y drenaje", _aceite),
    "admision": ("Admisión y filtro de aire", _admision),
    "culata": ("Cilindro, culata y bujía", _culata),
    "valvulas": ("Válvulas", _valvulas),
    "radiador": ("Radiador y refrigeración", _radiador),
    "rueda": ("Rueda", _rueda),
    "suspension_delantera": ("Suspensión delantera y dirección", _suspension_delantera),
    "amortiguadores": ("Basculante y amortiguadores", _amortiguadores),
    "electrico": ("Sistema eléctrico y batería", _electrico),
    "freno_tambor": ("Freno de tambor", _freno_tambor),
    "encendido": ("Encendido y bujía", _encendido),
    "transmision": ("Caja de cambios y piñón de salida", _transmision),
    "carcasa": ("Carcasa, tapa del clutch y filtro de aceite", _carcasa),
    "rueda_trasera": ("Rueda trasera y arrastre", _rueda_trasera),
    "rueda_tambor": ("Rueda trasera, freno de tambor y arrastre", _rueda_tambor),
    "freno_completo": ("Freno: bomba, manguera y caliper", _freno_completo),
}

# Reglas: palabra clave del catálogo (en inglés) → puesto. Gana la primera que coincida.
REGLAS = {
    "freno_disco": [("BRAKE PAD", "pastillas"), ("SUPPORT, PAD", "resorte_pastillas"), ("PIN, PAD", "pasador"), ("CLIP", "pasador"),
                    ("DISK", "disco"), ("SEAL KIT", "empaques"), ("PISTON", "piston"), ("CALIPER ASSY", "caliper"),
                    ("BLEED", "purgador"), ("SUPT", "soporte"), ("BRACKET", "soporte"), ("BOOT", "guardapolvo"), ("SHIM", "lamina")],
    "bomba_freno": [("CAP, RESERVOIR", "tapa"), ("DIAPHRAGM", "diafragma"), ("PLATE, DIAPHRAGM", "diafragma"), ("CYLINDER KIT", "kit_reparacion"),
                    ("MASTER CYLINDER ASSY", "bomba"), ("BRACKET, MASTER", "abrazadera"), ("LEVER", "manigueta"), ("STOP SWITCH", "interruptor"),
                    ("SWITCH", "interruptor"), ("HOSE, BRAKE", "manguera"), ("BOLT, UNION", "banjo"), ("WASHER", "banjo"),
                    ("HOLDER, BRAKE HOSE", "soporte_manguera"), ("HYDRAULIC", "unidad_abs"), ("HU ASSY", "unidad_abs"), ("PIPE", "manguera")],
    "cvt": [("V-BELT", "correa"), ("WEIGHT SET", "rodillos"), ("SLIDER", "deslizadores"), ("CAM", "rampa"),
            ("PRIMARY SLIDING SHEAVE", "polea_movil"), ("SHEAVE, PRIMARY FIXED", "polea_fija"), ("PRIMARY FIXED", "polea_fija"),
            ("CLUTCH WEIGHT SHOE", "zapatas"), ("SPRING, CLUTCH WEIGHT", "resortes_zapatas"), ("DAMPER, CLUTCH WEIGHT", "zapatas"),
            ("CLUTCH CARRIER", "clutch"), ("CLUTCH HOUSING", "campana"), ("SPRING, SECONDARY", "resorte_torque"),
            ("SEAT, SECONDARY", "resorte_torque"), ("SECONDARY", "polea_trasera"), ("COLLAR", "buje"), ("BUSH", "buje"),
            ("BEARING", "polea_trasera"), ("SEAL", "polea_trasera"), ("PIN, GUIDE", "polea_trasera"), ("CIRCLIP", "clutch")],
    "aceite": [("PLUG,DRAIN", "tapon"), ("PLUG, DRAIN", "tapon"), ("STRAINER", "malla"), ("SPRING", "resorte"), ("O-RING", "oring"),
               ("OIL PUMP", "bomba")],
    "admision": [("ELEMENT", "filtro"), ("CAP, CLEANER", "tapa"), ("CASE, AIR CLEANER", "caja"), ("JOINT", "ducto"), ("DUCT", "ducto"),
                 ("THROTTLE BODY", "cuerpo_aceleracion"), ("INJECTOR", "inyector"), ("STEPPING", "motor_ralenti"),
                 ("GASKET, MANIFOLD", "empaque"), ("MANIFOLD", "multiple"), ("PIPE", "manguera"), ("HOSE", "manguera"),
                 ("O-RING", "empaque")],
    "culata": [("PLUG, SPARK", "bujia"), ("COVER, CYLINDER HEAD", "tapa_valvulas"), ("GASKET, HEAD COVER", "empaque_tapa"),
               ("GASKET, CYLINDER HEAD", "empaque_culata"), ("CYLINDER HEAD", "culata"), ("GASKET, CYLINDER", "empaque_cilindro"),
               ("CYLINDER", "cilindro"), ("BOLT, STUD", "esparragos"), ("PIN, DOWEL", "guias")],
    "valvulas": [("VALVE, INTAKE", "valvula_admision"), ("VALVE, EXHAUST", "valvula_escape"), ("SPRING, VALVE", "resortes"),
                 ("RETAINER, VALVE", "platillo"), ("LOCK, VALVE", "cunas"), ("SEAT, VALVE", "base_resorte"), ("SEAL, VALVE", "sello"),
                 ("ROCKER ARM", "balancin"), ("SHAFT, ROCKER", "eje_balancin"), ("ADJUSTING", "tornillo_calibracion"), ("NUT", "tornillo_calibracion"),
                 ("CAMSHAFT", "arbol_levas"), ("GUIDE, VALVE", "sello")],
    "radiador": [("CAP, RADIATOR", "tapa"), ("RADIATOR ASSY", "radiador"), ("COVER, RADIATOR", "rejilla"), ("THERMOSTAT", "termostato"),
                 ("CASE, FAN", "carcasa_ventilador"), ("FAN", "ventilador"), ("COCK, DRAIN", "drenaje"), ("HOSE CLAMP", "abrazaderas"),
                 ("CLAMP", "abrazaderas"), ("HOSE", "manguera"), ("PIPE", "manguera"), ("O-RING", "empaques"), ("GASKET", "empaques"),
                 ("DAMPER", "empaques"), ("GROMMET", "empaques")],
    "rueda": [("DISK", "disco"), ("DISC", "disco"), ("TIRE", "llanta"), ("CAST WHEEL", "rin"), ("AXLE", "eje"), ("BEARING", "rodamientos"), ("OIL SEAL", "retenedores"),
              ("COLLAR", "buje"), ("VALVE, RIM", "valvula"), ("ROTOR, SENSOR", "sensor_abs")],
    "suspension_delantera": [("FRONT FORK ASSY", "barra_completa"), ("INNER TUBE", "barra_cromada"), ("TUBE, OUTER", "botella"),
                             ("SPRING", "resorte"), ("CYLINDER COMP", "cilindro_amortiguador"), ("SEAL, DUST", "guardapolvo"),
                             ("OIL SEAL", "retenedor"), ("BOLT, CAP", "tapon"), ("UNDER BRACKET", "tijera"), ("SPINDLE", "eje_direccion"),
                             ("BEARING", "rodamientos_direccion"), ("RACE", "tazas"), ("COVER, BALL", "tazas"), ("RETAINER, BALL", "rodamientos_direccion"),
                             ("ROD", "cilindro_amortiguador")],
    "amortiguadores": [("SHOCK ABSORBER", "amortiguador"), ("ARM, REAR", "basculante"), ("COLLAR", "bujes"), ("BUSH", "bujes"),
                       ("OIL SEAL", "retenedor")],
    "electrico": [("BATTERY", "bateria"), ("FUSE", "fusibles"), ("RELAY", "rele"), ("WIRE HARNESS", "arnes"), ("LEAD", "arnes"),
                  ("MAIN SWITCH", "switch"), ("XMTR", "llave"), ("REMOTE CONTROL", "modulo"), ("SWITCH, SIDE STAND", "sensor_pata")],
    "freno_tambor": [("INDICATOR", "indicador"), ("PLATE, BRAKE SHOE", "plato"), ("PANEL", "plato"), ("SHOE", "bandas"),
                     ("SPRING", "resortes"), ("CAM", "leva"), ("LEVER", "palanca"), ("ARM", "palanca"), ("SEAL", "retenedor")],
    "encendido": [("PLUG, SPARK", "bujia"), ("SPARK", "bujia"), ("CAP, PLUG", "capuchon"), ("PLUG CAP", "capuchon"),
                  ("IGNITION COIL", "bobina"), ("STATOR", "estator"), ("COIL", "bobina"), ("ROTOR", "magneto"), ("FLYWHEEL", "magneto"),
                  ("C.D.I", "cdi"), ("CDI", "cdi"), ("ECU", "cdi"), ("RECTIFIER", "regulador"), ("REGULATOR", "regulador"),
                  ("LEAD", "cables"), ("WIRE", "cables")],
    "transmision": [("AXLE, MAIN", "eje_principal"), ("MAIN AXLE", "eje_principal"), ("AXLE, DRIVE", "eje_salida"),
                    ("DRIVE AXLE", "eje_salida"), ("SPROCKET", "pinon"), ("PINION", "engranajes"), ("WHEEL", "engranajes_salida"),
                    ("GEAR", "engranajes"), ("FORK, SHIFT", "horquillas"), ("SHIFT FORK", "horquillas"), ("CAM, SHIFT", "tambor_selector"),
                    ("SHIFT CAM", "tambor_selector"), ("CHAIN", "cadena"), ("OIL SEAL", "reten"), ("BEARING", "rodamientos")],
    "carcasa": [("CRANKCASE 1", "carcasa_izq"), ("CRANKCASE 2", "carcasa_der"), ("COVER, CRANKCASE", "tapa_clutch"),
                ("CRANKCASE", "carcasa_der"), ("COVER", "tapa_clutch"), ("LEVEL", "visor"), ("GAUGE", "tapon_llenado"),
                ("FILLER", "tapon_llenado"), ("ELEMENT", "filtro"), ("OIL CLEANER", "filtro"), ("STRAINER", "malla"),
                ("SCREEN", "malla"), ("PLUG", "tapon"), ("SWITCH", "swiche"), ("NEUTRAL", "swiche"), ("GASKET", "empaques"),
                ("OIL SEAL", "reten"), ("BEARING", "rodamientos"), ("PUMP", "bomba")],
}
REGLAS["rueda_trasera"] = [("SPROCKET", "corona"), ("CLUTCH HUB", "porta_sprocket"), ("HUB, CLUTCH", "porta_sprocket"),
                           ("DAMPER", "cauchos"), ("CHAIN", "cadena"), ("DISK", "disco"), ("DISC", "disco"), ("PULLER", "tensores"),
                           ("ADJUSTER", "tensores")] + REGLAS["rueda"]


# Lo mismo para los catálogos en español (Auteco: Bajaj, KTM, TVS). Sin tildes; se comparan sin tildes.
REGLAS_ES = {
    "freno_disco": [("RESORTE PASTA", "resorte_pastillas"), ("PIN PASTA", "pasador"), ("PASADOR", "pasador"), ("PASTA", "pastillas"),
                    ("PASTILLA", "pastillas"), ("DISCO", "disco"), ("RETENES", "empaques"), ("EMPAQUETADURA", "empaques"),
                    ("PISTON", "piston"), ("CALIPER", "caliper"), ("SANGRADO", "purgador"), ("PURGA", "purgador"),
                    ("GUARDAPOLVO", "guardapolvo"), ("SOPORTE", "soporte")],
    "bomba_freno": [("TAPA", "tapa"), ("DIAFRAGMA", "diafragma"), ("KIT", "kit_reparacion"), ("BOMBA", "bomba"),
                    ("ABRAZADERA", "abrazadera"), ("MANIGUETA", "manigueta"), ("PALANCA", "manigueta"), ("SWICHE", "interruptor"),
                    ("INTERRUPTOR", "interruptor"), ("MANGUERA", "manguera"), ("BANJO", "banjo"), ("ARANDELA", "banjo")],
    "aceite": [("TAPON", "tapon"), ("DRENAJE", "tapon"), ("CEDAZO", "malla"), ("MALLA", "malla"), ("REJILLA", "malla"),
               ("FILTRO", "malla"), ("RESORTE", "resorte"), ("ORING", "oring"), ("EMPAQUE", "oring"), ("BOMBA", "bomba")],
    "admision": [("TAPA", "tapa"), ("CAJA", "caja"), ("FILTRO", "filtro"), ("ELEMENTO", "filtro"), ("ESPUMA", "filtro"),
                 ("CONDUCTO", "ducto"), ("CUERPO", "cuerpo_aceleracion"), ("INYECTOR", "inyector"), ("MULTIPLE", "multiple"),
                 ("MANGUERA", "manguera"), ("EMPAQUE", "empaque")],
    "culata": [("BUJIA", "bujia"), ("EMPAQUE TAPA", "empaque_tapa"), ("TAPA CULATA", "tapa_valvulas"), ("EMPAQUE CULATA", "empaque_culata"),
               ("CULATA", "culata"), ("EMPAQUE CILINDRO", "empaque_cilindro"), ("CILINDRO", "cilindro"), ("ESPARRAGO", "esparragos"),
               ("GUIA", "guias")],
    "valvulas": [("ADMISION", "valvula_admision"), ("ESCAPE", "valvula_escape"), ("KIT VALVULAS", "valvula_admision"),
                 ("ARANDELA", "platillo"), ("RESORTE", "resortes"), ("CUNA", "cunas"), ("RETEN", "sello"), ("SELLO", "sello"),
                 ("EJE BALANCIN", "eje_balancin"), ("BALANCIN", "balancin"), ("CALIBRA", "tornillo_calibracion"),
                 ("TUERCA", "tornillo_calibracion"), ("LEVAS", "arbol_levas"), ("GUIA", "sello")],
    "radiador": [("TAPA", "tapa"), ("CUBIERTA", "rejilla"), ("PROTECTOR", "rejilla"), ("RADIADOR", "radiador"),
                 ("TERMOSTATO", "termostato"), ("VENTILADOR", "ventilador"), ("ABRAZADERA", "abrazaderas"), ("MANGUERA", "manguera"),
                 ("CONDUCTO", "manguera"), ("TUBO", "manguera"), ("EMPAQUE", "empaques"), ("ORING", "empaques"),
                 ("ANTIVIBRANTE", "empaques")],
    "rueda": [("LLANTA", "llanta"), ("NEUMATICO", "llanta"), ("RIN", "rin"), ("EJE", "eje"), ("RODAMIENTO", "rodamientos"),
              ("BALINERA", "rodamientos"), ("RETEN", "retenedores"), ("BUJE", "buje"), ("VALVULA", "valvula")],
    "suspension_delantera": [("COMPLET", "barra_completa"), ("GUARDAPOLVO", "guardapolvo"), ("RETEN", "retenedor"),
                             ("RESORTE", "resorte"), ("BOTELLA", "botella"), ("CILINDRO", "cilindro_amortiguador"),
                             ("TAPON", "tapon"), ("TIJERA", "tijera"), ("EJE DIRECCION", "eje_direccion"), ("BALIN", "rodamientos_direccion"),
                             ("RODAMIENTO", "rodamientos_direccion"), ("CUNA", "tazas"), ("TAZA", "tazas"), ("TUBO", "barra_cromada"),
                             ("BARRA", "barra_cromada")],
    "amortiguadores": [("AMORTIGUADOR", "amortiguador"), ("BRAZO", "basculante"), ("BUJE", "bujes"), ("RETEN", "retenedor")],
    "electrico": [("BATERIA", "bateria"), ("FUSIBLE", "fusibles"), ("RELE", "rele"), ("ARNES", "arnes"), ("CABLE", "arnes"),
                  ("SWICHE", "switch")],
    "freno_tambor": [("INDICADOR", "indicador"), ("LEVA", "leva"), ("PORTA BANDAS", "plato"), ("PORTABANDAS", "plato"),
                     ("BANDA", "bandas"), ("RESORTE", "resortes"), ("PALANCA", "palanca"), ("CAMPANA", "campana"),
                     ("RETEN", "retenedor")],
    "encendido": [("ANTIVIBRANTE CAPUCHON", "antivibrante"), ("BOBINA DE ALTA", "bobina"), ("BOBINA ALTA", "bobina"),
                  ("CAPUCHON", "capuchon"), ("BUJIA", "bujia"), ("BOBINA ENCENDIDO", "bobina"), ("BOBINA DE ENCENDIDO", "bobina"),
                  ("BOBINA ALTA", "bobina"), ("ESTATOR", "estator"), ("PLATO", "estator"), ("BOBINA", "estator"),
                  ("VOLANTE", "magneto"), ("MAGNETO", "magneto"), ("C.D.I", "cdi"), ("CDI", "cdi"), ("ECU", "cdi"),
                  ("REGULADOR", "regulador"), ("CABLE", "cables")],
    "transmision": [("ANILLO", None), ("ARANDELA", None), ("BUJE", None), ("PIN ", None), ("PINON SALIDA", "pinon"),
                    ("PINON DE SALIDA", "pinon"), ("PINON DELANTERO", "pinon"), ("KIT REPARACION EJE SALIDA", "eje_salida"),
                    ("KIT SPROCKET", "cadena"), ("SPROCKET", "pinon"), ("EJE DE SALIDA", "eje_salida"), ("EJE SALIDA", "eje_salida"),
                    ("EJE SECUNDARIO", "eje_salida"), ("CONTRAEJE", "eje_salida"), ("EJE CLUTCH", "eje_principal"),
                    ("EJE PRINCIPAL", "eje_principal"), ("EJE PRIMARIO", "eje_principal"), ("ENGRANAJE DE RUEDA", "engranajes_salida"),
                    ("RUEDA", "engranajes_salida"), ("ENGRANAJE", "engranajes"), ("PINON", "engranajes"), ("HORQUILLA", "horquillas"),
                    ("TAMBOR", "tambor_selector"), ("SELECTOR", "tambor_selector"), ("CADENILLA", None), ("CADENA", "cadena"),
                    ("RETEN", "reten"), ("RODAMIENTO", "rodamientos"), ("BALINERA", "rodamientos"), ("RODILLO", "rodamientos")],
    "carcasa": [("ANILLO", None), ("ARANDELA", None), ("PIN ", None), ("GUIA DE CENTRADO", None), ("O-RING", None),
                ("CARCASA IZQ", "carcasa_izq"), ("CARCASA DER", "carcasa_der"), ("MOTOR COMPLETO", "carcasa_der"),
                ("TAPA FILTRO", "tapa_filtro"), ("CUBIERTA FILTRO", "tapa_filtro"), ("CUBIERTA CLUTCH", "tapa_clutch"),
                ("TAPA CLUTCH", "tapa_clutch"), ("CUBIERTA EMBRAGUE", "tapa_clutch"), ("CARCASA", "carcasa_der"),
                ("CUBIERTA", "tapa_clutch"), ("VISOR", "visor"), ("MIRILLA", "visor"), ("VARILLA", "tapon_llenado"),
                ("LLENADO", "tapon_llenado"), ("FILTRO", "filtro"), ("CEDAZO", "malla"), ("MALLA", "malla"), ("REJILLA", "malla"),
                ("TAPON", "tapon"), ("DRENAJE", "tapon"), ("SWICHE", "swiche"), ("SENSOR", "swiche"), ("INTERRUPTOR", "swiche"),
                ("EMPAQUE", "empaques"), ("JUNTA", "empaques"), ("RETEN", "reten"), ("RODAMIENTO", "rodamientos"),
                ("BALINERA", "rodamientos"), ("BOMBA", "bomba"), ("INYECTOR", "bomba")],
}
REGLAS_ES["rueda_trasera"] = [("PORTA SPROCKET", "porta_sprocket"), ("PORTASPROCKET", "porta_sprocket"), ("CAUCHO", "cauchos"),
                              ("KIT SPROCKET", "cadena"), ("SPROCKET", "corona"), ("CORONA", "corona"), ("CADENA", "cadena"),
                              ("EMPATE", "cadena"), ("SENSOR", None), ("DISCO", "disco"), ("TENSOR", "tensores"),
                              ("TIRADOR", "tensores"), ("CABRECADENA", "tensores")] + REGLAS_ES["rueda"]


_EXTRA_ES = {
    "transmision": [("EJE CAJA", "eje_principal"), ("CANASTILLA", "rodamientos"), ("ARAND", None)],
    "encendido": [("UNA VIA", "magneto"), ("SENSOR", "magneto"), ("CONDENSADOR", "cdi")],
    "valvulas": [("GORRO", "sello"), ("LEVANTADOR", "balancin"), ("KIT REPARACION", "valvula_admision")],
    "culata": [("GUIA DE VALVULA", "guias"), ("GUIA VALVULA", "guias")],
    "rueda": [("RADIOS", "rin"), ("SENSOR", "sensor_abs"), ("DISCO", "disco"), ("UNIDAD DE ENGRANAJE", "buje"), ("GUARDAPOLVO", "retenedores"),
              ("TUBO", "llanta")],
    "suspension_delantera": [("METAL CORREDIZO", "botella"), ("CAMISA", "botella"), ("PROTECTOR TUBO", "guardapolvo"),
                             ("ANILLOS DEL PISTON", "cilindro_amortiguador"), ("PISTON", "cilindro_amortiguador"),
                             ("SUSPENSION DELANTERA", "barra_completa"), ("SOPORTE DE LA MANGUERA", None)],
    "amortiguadores": [("TENSOR", "basculante"), ("CABRECADENA", "basculante"), ("PROTECTOR CADENA", "basculante"),
                       ("GUARDACADENA", "basculante"), ("EJE", "basculante"), ("BOQUILLA", "basculante")],
    "bomba_freno": [("TANQUE", "deposito"), ("DEPOSITO", "deposito"), ("CILINDRO MAESTRO", "bomba"), ("LEVA", "manigueta"),
                    ("SOPORTE", "abrazadera"), ("UNION", "banjo"), ("CUBIERTA PARA POLVO", "kit_reparacion")],
    "electrico": [("INSTALACION", "arnes"), ("TERMINAL", "arnes"), ("FLASHER", "modulo"), ("DIODO", "modulo"),
                  ("RECTIFICADOR", "modulo"), ("REGULADOR", "modulo"), ("UNIDAD", "modulo"), ("INTERRUPTOR", "switch")],
    "radiador": [("GUIA DE AIRE", "rejilla")],
    "admision": [("RESONADOR", "ducto"), ("EMBUDO", "ducto"), ("PROTECTOR", "tapa")],
    "rueda_trasera": [("EMBRAGUE DE MASA", "porta_sprocket"), ("SENSOR", "sensor_abs"), ("GUARDAPOLVO", "retenedores"),
                      ("RADIOS", "rin"), ("TUBO", "llanta")],
    "carcasa": [("SWICHE", "swiche")],
}
# Lo mismo en inglés (catálogos Yamaha)
_EXTRA_EN = {
    "suspension_delantera": [("METAL, SLIDE", "botella"), ("BOOT", "guardapolvo"), ("CAP", "tapon")],
    "culata": [("GUIDE, VALVE", "guias")],
    "bomba_freno": [("JOINT", "banjo"), ("HOLDER", "soporte_manguera"), ("MASTER CYLINDER", "bomba"), ("COVER, DUST", "kit_reparacion"),
                    ("TANK", "deposito"), ("HOSE, RESERVOIR", "manguera"), ("RESERVOIR TANK", "deposito")],
    "electrico": [("STOP SWITCH", "switch"), ("DIODE", "modulo"), ("RECTIFIER", "modulo"), ("FLASHER", "modulo")],
    "rueda_trasera": [("CLUTCH, HUB", "porta_sprocket")],
    "aceite": [("COVER, OIL ELEMENT", "tapon"), ("ELEMENT", "malla"), ("OIL CLEANER", "malla"), ("PUMP", "bomba")],
    "valvulas": [("ROCKER", "balancin")],
    "amortiguadores": [("PIVOT", "basculante"), ("CASE, CHAIN", "basculante"), ("REAR ARM", "basculante"), ("THRUST", "bujes")],
    "rueda": [("GEAR UNIT", "buje")],
}
for _clave, _reglas in _EXTRA_EN.items():
    REGLAS[_clave] = _reglas + REGLAS[_clave]
_EXTRA_ES["admision"] += [("TAPON", "tapa"), ("CONECTOR", "ducto")]
_EXTRA_ES["freno_tambor"] = [("VELOCIMETRO", "plato")]
_RENOMBRE_TAMBOR = {"retenedor": "retenedores", "tuercas": "tuerca"}
for _clave, _reglas in _EXTRA_ES.items():
    REGLAS_ES[_clave] = _reglas + REGLAS_ES[_clave]


_EXTRA_ES["rueda_tambor"] = [("VELOCIMETRO", "buje"), ("UNION CADENA", "cadena"), ("PALANCA", "palanca"), ("LEVA", "leva")]
REGLAS["rueda_tambor"] = [("BRAKE SHOE", "bandas"), ("SHOE", "bandas"), ("CAMSHAFT LEVER", "palanca"), ("LEVER, CAMSHAFT", "palanca"),
                          ("CAMSHAFT", "leva"), ("INDICATOR", "indicador"), ("PLATE, BRAKE SHOE", "plato"), ("PANEL", "plato"),
                          ("SPRING, TENSION", "resortes")] + [(w, None if q in ("disco", "sensor_abs") else q) for w, q in REGLAS["rueda_trasera"]]
REGLAS_ES["rueda_tambor"] = (_EXTRA_ES["rueda_tambor"]
                             + [(w, _RENOMBRE_TAMBOR.get(q, q)) for w, q in REGLAS_ES["freno_tambor"] if w not in ("TUERCA", "ARANDELA", "TORNILLO", "RETEN")]
                             + [(w, None if q in ("disco", "sensor_abs") else q) for w, q in REGLAS_ES["rueda_trasera"]])


REGLAS_ES["freno_completo"] = ([("TORNILLO MANGUERA", "banjo"), ("GUIA MANGUERA", "guia_manguera"), ("CABLE SWICHE", "interruptor"),
                                ("TAPA", "tapa"), ("ABRAZADERA", "abrazadera"),
                                ("SOPORTE TANQUE", "soporte_deposito"), ("SOPORTE CALIPER", "soporte"), ("PISTON BOMBA", "kit_reparacion"),
                                ("RESORTE PEDAL", "pedal"), ("CAUCHO PEDAL", "pedal"), ("BUJE PEDAL", "pedal"), ("PEDAL", "pedal"),
                                ("PLATINA BOMBA", "diafragma"), ("AISLANTE", "lamina"), ("PIN PASTA", "pasador"), ("RESORTE PASTA", "resorte_pastillas"),
                                ("PASTA", "pastillas"), ("CALIPER", "caliper"), ("SWITCH", "interruptor")]
                               + REGLAS_ES["bomba_freno"] + [r for r in REGLAS_ES["freno_disco"] if r[1] != "disco"])
REGLAS["freno_completo"] = ([("PEDAL", "pedal"), ("HOLDER", "guia_manguera"), ("CALIPER", "caliper")]
                            + [r for r in REGLAS["bomba_freno"] if r[1] not in ("unidad_abs", "soporte_manguera")]
                            + [r for r in REGLAS["freno_disco"] if r[1] != "disco"])


# Piezas que el dibujo sí tiene pero a las que ninguna regla llegaba (salían en "Otras piezas")
for _clave, _reglas in {
    "rueda": [("TUBE", "llanta"), ("HUB", "buje"), ("RIM", "rin"), ("SPOKE", "rin"), ("BALANCER", "rin"), ("RING, WHEEL", "rin")],
    "rueda_trasera": [("END", "tensores"), ("BALANCER", "rin"), ("TUBE", "llanta"), ("RIM", "rin")],
    "rueda_tambor": [("BAR, TENSION", "palanca"), ("TUBE", "llanta"), ("HUB", "buje"), ("RIM", "rin"), ("SPOKE", "rin")],
    "freno_disco": [("PAD, SUPPORT", "resorte_pastillas"), ("SPRING, PAD", "resorte_pastillas"), ("DISC, BRAKE", "disco"),
                    ("CAP", "purgador"), ("PLUG", "purgador")],
    "radiador": [("RADIATOR COMP", "radiador"), ("BLOWER", "ventilador"), ("GUIDE, AIR", "rejilla"), ("DUCT", "rejilla")],
    "bomba_freno": [("BRAKE HOSE", "manguera"), ("HOSE", "manguera")],
    "admision": [("RESONATOR", "ducto"), ("FUNNEL", "ducto"), ("AIR CLEANER ASSY", "caja"), ("CAP", "tapa"), ("SOLENOID", "motor_ralenti")],
    "amortiguadores": [("NIPPLE", "basculante"), ("HOLDER, BRAKE HOSE", "basculante")],
    "valvulas": [("LIFTER", "balancin"), ("SPRING, COIL", "resortes")],
    "aceite": [("FILTER", "malla")],
    "electrico": [("ECU", "modulo")],
}.items():
    REGLAS[_clave] = _reglas + REGLAS[_clave]
for _clave, _reglas in {
    "suspension_delantera": [("HORQUILLA INFERIOR", "tijera"), ("SUSPENSION", "barra_completa")],
    "amortiguadores": [("GUARDAPOLVO", "retenedor")],
    "freno_disco": [("AISLANTE", "lamina")],
    "carcasa": [("GUIA CABLE CLUTCH", "tapa_clutch"), ("EMPUJADOR CLUTCH", "tapa_clutch"), ("EJE INTERNO CLUTCH", "tapa_clutch")],
    "electrico": [("12V", "bateria")],
}.items():
    REGLAS_ES[_clave] = _reglas + REGLAS_ES[_clave]


for _clave in ("rueda", "rueda_trasera"):
    REGLAS[_clave] = [("ROTOR, SENSOR", "sensor_abs"), ("SENSOR", "sensor_cable"), ("LEAD", "sensor_cable")] + REGLAS[_clave]
    REGLAS_ES[_clave] = [("KIT REPARACION", "kit"), ("CABLE SENSOR", "sensor_cable"), ("SENSOR DISCO", "sensor_abs"),
                         ("ENCODER", "sensor_abs"), ("ANILLO SENSOR", "sensor_abs"), ("SENSOR", "sensor_cable"),
                         ("BUJE EJE", "buje")] + REGLAS_ES[_clave]
REGLAS_ES["rueda_tambor"] = [r for r in REGLAS_ES["rueda_tambor"] if r[1] not in ("sensor_cable",)]


# Congruencia: la regla específica gana a la general (p. ej. "Manguera radiador" es manguera, no radiador)
for _clave, _reglas in {
    "radiador": [("MANGUERA", "manguera"), ("VENTILADOR", "ventilador"), ("CONECTOR TERMOSTATO", "termostato"),
                 ("TERMOSTATO", "termostato"), ("TAPA TANQUE", "tapa")],
    "valvulas": [("EJE DEL BALANCIN", "eje_balancin"), ("EJE BALANCIN", "eje_balancin"), ("BALANCIN", "balancin"),
                 ("RETEN", "sello"), ("SELLO", "sello"), ("CUNA", "cunas"), ("KIT RETENES", "sello")],
    "admision": [("CONDUCTO", "ducto"), ("MANGUERA", "manguera"), ("CUBIERTA FILTRO", "tapa"), ("EMPAQUE", "empaque")],
    "rueda": [("VALVULA", "valvula"), ("RODAMIENTO", "rodamientos"), ("BALINERA", "rodamientos"), ("RETEN", "retenedores")],
    "rueda_trasera": [("PORTA", "porta_sprocket"), ("VALVULA", "valvula"), ("RODAMIENTO", "rodamientos"),
                      ("BALINERA", "rodamientos"), ("RETEN", "retenedores"), ("BUJE RIN", "buje")],
    "rueda_tambor": [("PORTA", "porta_sprocket"), ("VALVULA", "valvula"), ("RODAMIENTO", "rodamientos"), ("BALINERA", "rodamientos"),
                     ("RETEN", "retenedores"), ("BUJE RIN", "buje"), ("O-RING", None)],
    "suspension_delantera": [("RESORTE", "resorte"), ("GUARDAPOLVO", "guardapolvo"), ("KIT RETENES", "retenedor"),
                             ("BOTELLA", "botella"), ("TUBO SUSPENSION", "barra_cromada"), ("PISTON", "cilindro_amortiguador")],
    "bomba_freno": [("ABRAZADERA", "abrazadera"), ("SOPORTE MANGUERA", "soporte_manguera"), ("GUIA MANGUERA", "soporte_manguera")],
    "carcasa": [("EMPAQUE CARCASA", "empaques"), ("JUNTA CARCASA", "empaques"), ("TAPON CARCASA", "tapon"), ("BUJE CARCASA", None)],
    "electrico": [("CABLE", "arnes")],
    "transmision": [("RETEN EJE", "reten"), ("BALINERA EJE", "rodamientos")],
    "freno_completo": [("MANGUERA TANQUE", "manguera"), ("KIT RETENES", "empaques"), ("KIT GUARDAPOLVO", "guardapolvo")],
}.items():
    REGLAS_ES[_clave] = _reglas + REGLAS_ES[_clave]
# La regla "SUSPENSION" sola era demasiado amplia ("Resorte suspensión" no es la barra completa)
REGLAS_ES["suspension_delantera"] = [r for r in REGLAS_ES["suspension_delantera"] if r != ("SUSPENSION", "barra_completa")]
REGLAS_ES["suspension_delantera"].insert(0, ("SUSPENSION DELANTERA", "barra_completa"))
REGLAS_ES["suspension_delantera"].insert(1, ("SUSPENSION IZQ", "barra_completa"))
REGLAS_ES["suspension_delantera"].insert(2, ("SUSPENSION DER", "barra_completa"))
for _clave, _reglas in {
    "bomba_freno": [("HOLDER", "soporte_manguera"), ("BRACKET", "abrazadera"), ("GUIDE", "soporte_manguera"), ("CLAMP", "soporte_manguera")],
    "radiador": [("HOSE", "manguera"), ("FAN", "ventilador")],
    "rueda": [("VALVE", "valvula")],
    "rueda_trasera": [("VALVE", "valvula"), ("BEARING", "rodamientos"), ("OIL SEAL", "retenedores")],
    "valvulas": [("SHAFT, ROCKER", "eje_balancin"), ("ROCKER", "balancin"), ("SEAL", "sello")],
}.items():
    REGLAS[_clave] = _reglas + REGLAS[_clave]


def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


# Palabras que delatan una descripción en español (para no aplicarle las reglas en inglés: "ROD" está en "RODAMIENTO").
_ES = re.compile(r"\b(TORNILLO|ARANDELA|TUERCA|BUJE|RESORTE|EMPAQUE|SOPORTE|TAPA|TAPON|PASTAS?|FRENO|DELANTER[OA]|TRASER[OA]|"
                 r"FILTRO|ACEITE|AIRE|BUJIA|VALVULAS?|RADIADOR|LLANTA|RODAMIENTO|RETEN\w*|AMORTIGUADOR|BATERIA|BOMBA|MANGUERA|"
                 r"CAJA|CUBIERTA|CILINDRO|CULATA|DISCO|GUARDAPOLVO|BRAZO|CADENA|ABRAZADERA|ANILLO|CAUCHO|PLATINA|ESPARRAGO|"
                 r"ADMISION|ESCAPE|SANGRADO|CONDUCTO|NEUMATICO|DIAFRAGMA|TANQUE|LIQUIDO|PIN|BALINERA|CAPUCHON|TORRE|"
                 r"BOBINA|ESTATOR|VOLANTE|MAGNETO|REGULADOR|BANDAS?|CAMPANA|LEVA|PINON|CORONA|EMPATE|TENSOR|TIRADOR|"
                 r"GUARDACADENA|CADENILLA|PALANCA|INDICADOR|EJE|CARCASA|SWICHE|TERMOSTATO|VENTILADOR|TUBO|ENGRANAJE|"
                 r"BALANCIN(ES)?|GUIA|CONECTOR|DEPOSITO|MANIGUETA|FUSIBLE|PITO|DIODO|COMPLET[OA]|IZQUIERD[OA]|DERECH[OA]|"
                 r"JUEGO|RIN|RADIOS|CAMISA|TELESCOPICO|PLATO|PORTABANDAS|EMBRAGUE|RESONADOR|EMBUDO|SENSOR VELOCIDAD|"
                 r"VELOCIMETRO|GORRO|LEVANTADOR|CANASTILLA|CONDENSADOR|RECTIFICADOR|INSTALACION|INTERRUPTOR|UNION|"
                 r"SUSPENSION|CORREDIZO|BASCULANTE|BARCULANTE|CABRECADENA|PROTECTOR|ESPACIADOR|SEPARADOR|ARAND|PORTA)\b")


def _palabra(palabra, texto):
    """La regla vale como palabra completa (o como prefijo, si es larga): "RIN" no está en "RING", "ROD" no en "RODAMIENTO"."""
    return re.search(r"\b" + re.escape(palabra) + (r"" if len(palabra) >= 6 else r"(S|ES)?\b"), texto) is not None


def puesto_en_dibujo(clave, descripcion):
    """Puesto de la pieza en el dibujo del sistema, o None si el dibujo no la tiene."""
    texto = descripcion.upper().lstrip(". ")
    sin_tildes = _sin_tildes(texto)
    if _ES.search(sin_tildes):
        puesto = next((p for palabra, p in REGLAS_ES.get(clave, []) if palabra in sin_tildes), None)
        if puesto:
            return puesto
        # Catálogo en inglés con alguna palabra que también es española ("PIN, PAD"): reglas en inglés, palabra completa
        return next((p for palabra, p in REGLAS.get(clave, []) if _palabra(palabra, texto)), None)
    for palabra, p in REGLAS.get(clave, []):
        if palabra in texto:
            return p
    # Texto sin palabras típicas del español: las reglas en español, solo con palabra completa
    return next((p for palabra, p in REGLAS_ES.get(clave, []) if _palabra(palabra, sin_tildes)), None)


# Tornillería menuda: siempre va a la franja de abajo (con su ícono), aunque el dibujo tenga dónde ponerla.
# Así todas las láminas muestran sus piezas pequeñas abajo y el dibujo queda limpio para las piezas grandes.
SIEMPRE_EN_FRANJA = {"h_tornillo", "h_tuerca", "h_arandela", "h_seguro", "h_pin"}
# Excepción: piezas pequeñas que el dibujo muestra con su propio lugar (los pines de las pastillas, el purgador...).
CON_LUGAR_PROPIO = {"pasador", "purgador", "banjo", "esparragos", "tornillo_calibracion", "cunas", "guias", "empate"}


def puesto_para(clave, descripcion):
    """Toda pieza tiene puesto: la del dibujo del sistema o, si no está dibujada, la de la franja de tornillería."""
    herraje = herraje_para(descripcion)
    propio = puesto_en_dibujo(clave, descripcion)
    if herraje in SIEMPRE_EN_FRANJA and propio not in CON_LUGAR_PROPIO:
        return herraje
    return propio or herraje


# Piezas que no todas las motos tienen: si la lámina no las trae, no se dibujan (las demás quedan tenues, como contexto)
OPCIONALES = {"pedal", "kit", "sensor_cable", "sensor_abs", "unidad_abs", "soporte_deposito", "guia_manguera", "manigueta"}


def _queda(pieza, usadas):
    """Con `usadas` (puestos que trae la lámina) se dibujan solo esas piezas, como en el plano de la marca."""
    if usadas is None:
        return True
    if pieza.puesto is not None:
        return pieza.puesto in usadas
    return pieza.padre is None or pieza.padre in usadas


@lru_cache(maxsize=512)
def dibujar_lamina(clave, grupos=None, usadas=None, titulo=None):
    """Dibujo de una lámina con su franja de tornillería.

    grupos: (('h_arandela', 3), ...) = grupos de la franja y cuántos números lleva cada uno (None = todos, uno c/u).
    Devuelve dict con svg, puestos (punto de la etiqueta de cada pieza del dibujo), anclas (punto de la pieza),
    casillas ({grupo: [(x, y), ...]} un lugar por número en la franja) y alto (fin del área del dibujo). Todo en 0..1.
    """
    nombre, funcion = DIAGRAMAS[clave]
    if grupos is None:
        grupos = tuple((g, 1) for g in _ORDEN_HERRAJES)
    cuerpo_f, casillas = "", {}
    alto = 940
    if grupos:
        columnas, filas = _columnas(grupos)
        y_icono, y_numeros = 884, 820                      # fila de íconos y primera fila de números (hacia arriba)
        arriba = y_numeros - (filas - 1) * PASO - 36
        alto = arriba - 12
        nombres = {g: n for g, n, _ in HERRAJES}
        for (g, n), (cx, ancho, por_fila) in zip(grupos, columnas):
            icono = P(g, _FIGURAS_HERRAJES[g]((0, 0, 0)), (0, 0, 0))
            dibujo, _ = iso.componer([icono], [], LADO, margen=2, marco=(cx - 24, y_icono - 24, 48, 48))
            cuerpo_f += (f'<rect x="{cx - ancho / 2 + 5:.1f}" y="{arriba:.1f}" width="{ancho - 10:.1f}" height="{944 - arriba:.1f}"'
                         f' rx="12" fill="#f3eee2" stroke="#e4dccb" stroke-width="1.2"/>'
                         f'<g class="pieza" data-puesto="{g}">{dibujo.split("<g class=\"guias\">")[0]}</g>'
                         f'<text x="{cx:.1f}" y="{928}" text-anchor="middle" font-family="Barlow, Arial, sans-serif"'
                         f' font-size="{14 if ancho >= 100 else 12}" font-weight="600" fill="#6f6857">{nombres[g]}</text>')
            lugares = []
            columnas_grupo = min(por_fila, n)
            filas_grupo = math.ceil(n / columnas_grupo)
            for i in range(n):
                fila, col = divmod(i, columnas_grupo)
                x = cx + (col - (columnas_grupo - 1) / 2) * PASO_ANCHO
                y = y_numeros - (filas_grupo - 1 - fila) * PASO     # la última fila queda justo encima del ícono
                lugares.append((round(x / LADO, 4), round(y / LADO, 4)))
            casillas[g] = lugares
    piezas, lineas = funcion()
    # Las líneas de eje pueden ir atadas a una pieza: (puesto, línea). Sin ella, se van con la pieza.
    if usadas is not None:
        quedan = []
        for q in piezas:
            dueno = q.puesto or q.padre
            if dueno is None or dueno in usadas:
                quedan.append(q)
            elif dueno not in OPCIONALES:
                q.contexto = True          # sin número en esta lámina: tenue, para no perder el detalle del conjunto
                quedan.append(q)
        piezas = quedan
    dibujadas = {q.puesto for q in piezas if q.puesto}
    lineas = [l[1] if isinstance(l, tuple) else l for l in lineas if not isinstance(l, tuple) or l[0] in dibujadas]
    cuerpo, puestos = iso.componer(piezas, lineas, LADO, margen=110, marco=(0, 0, LADO, alto), guias_fijas=False)
    cajas = [q.caja_svg for q in piezas if q.caja_svg]
    contorno = ((min(c[0] for c in cajas) / LADO, min(c[1] for c in cajas) / LADO,
                 max(c[2] for c in cajas) / LADO, max(c[3] for c in cajas) / LADO) if cajas else (0.2, 0.1, 0.8, alto / LADO))
    anclas = {q.puesto: (round(q.ancla_svg[0] / LADO, 4), round(q.ancla_svg[1] / LADO, 4)) for q in piezas if q.puesto}
    # Dónde quedó dibujada la tornillería sin número, por tipo de la franja (para señalar dónde va una pieza de la franja)
    herrajes = {}
    for q in piezas:
        if getattr(q, "herraje", None):
            herrajes.setdefault(q.herraje, []).append((round(q.ancla_svg[0] / LADO, 4), round(q.ancla_svg[1] / LADO, 4)))
    if grupos:
        cuerpo += f'<line x1="30" y1="{alto + 4:.1f}" x2="{LADO - 30}" y2="{alto + 4:.1f}" stroke="#d9d1bf" stroke-width="1.5"/>' + cuerpo_f
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LADO} {LADO}" width="{LADO}" height="{LADO}">'
        '<defs><pattern id="cuadricula" width="40" height="40" patternUnits="userSpaceOnUse">'
        '<path d="M40 0H0V40" fill="none" stroke="#ece6d8" stroke-width="1"/></pattern>'
        '<filter id="sombra-piezas" x="-5%" y="-5%" width="110%" height="115%">'
        '<feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#5a4a2a" flood-opacity=".16"/></filter></defs>'
        f'<rect width="{LADO}" height="{LADO}" fill="#fdfcf8"/>'
        f'<rect width="{LADO}" height="{LADO}" fill="url(#cuadricula)"/>'
        f'<g filter="url(#sombra-piezas)">{cuerpo}</g>'
        # Rótulo de la lámina, como en los planos técnicos: sistema a la izquierda y sello de TallerYa a la derecha
        f'<rect x="30" y="952" width="{LADO - 60}" height="30" rx="8" fill="#f3eee2" stroke="#e4dccb" stroke-width="1.2"/>'
        f'<circle cx="48" cy="967" r="5" fill="#f26522"/>'
        f'<text x="62" y="973" font-family="Oswald, Barlow, Arial, sans-serif" font-size="17" font-weight="700" letter-spacing="1.5"'
        f' fill="#2b3134">{escape((titulo or nombre).upper()[:70])}</text>'
        f'<text x="{LADO - 46}" y="973" text-anchor="end" font-family="Oswald, Barlow, Arial, sans-serif" font-size="14"'
        f' font-weight="600" letter-spacing="2" fill="#a39b88">DIBUJO TALLER<tspan fill="#f26522">YA</tspan></text></svg>'
    )
    return {"svg": svg, "puestos": puestos, "anclas": anclas, "casillas": casillas, "alto": round(alto / LADO, 4),
            "herrajes": herrajes, "contorno": tuple(round(v, 4) for v in contorno)}


def dibujar(clave, grupos=None):
    """(svg, puestos): puestos del dibujo y, para la franja, el primer lugar de cada grupo."""
    d = dibujar_lamina(clave, grupos)
    puestos = dict(d["puestos"])
    puestos.update({g: lugares[0] for g, lugares in d["casillas"].items()})
    return d["svg"], puestos


def version(clave, grupos=None, usadas=None, titulo=None):
    """Huella corta del SVG, para que el navegador pida el dibujo nuevo cuando cambia."""
    return hashlib.sha1(dibujar_lamina(clave, grupos, usadas, titulo)["svg"].encode()).hexdigest()[:10]


def _una_unidad(formas):
    """Agrupa las formas que se tocan (en el dibujo) y devuelve el grupo más grande: una sola unidad de la pieza."""
    cajas = []
    for f in formas:
        pts = [q for anillo in f.anillos for q in anillo]
        xs, ys = [x for x, _ in pts], [y for _, y in pts]
        cajas.append((min(xs) - 3, min(ys) - 3, max(xs) + 3, max(ys) + 3))
    grupo = list(range(len(formas)))

    def raiz(i):
        while grupo[i] != i:
            grupo[i] = grupo[grupo[i]]
            i = grupo[i]
        return i
    for i, a in enumerate(cajas):
        for j in range(i):
            b = cajas[j]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                grupo[raiz(i)] = raiz(j)
    grupos = {}
    for i in range(len(formas)):
        grupos.setdefault(raiz(i), []).append(i)

    def area(ids):
        return ((max(cajas[i][2] for i in ids) - min(cajas[i][0] for i in ids))
                * (max(cajas[i][3] for i in ids) - min(cajas[i][1] for i in ids)))
    elegido = max(grupos.values(), key=area)
    return [formas[i] for i in sorted(elegido)]


@lru_cache(maxsize=1024)
def dibujar_pieza(clave, puesto):
    """La pieza de un puesto, sola y en grande, para la guía (sin números, líneas guía ni franja). None si no existe."""
    if puesto == "h_otros":
        return None                      # "Otras piezas" no tiene una forma propia (sería un cubo): sin imagen
    if puesto in _FIGURAS_HERRAJES:
        formas = [_FIGURAS_HERRAJES[puesto]((0, 0, 0))]
    else:
        formas = [q.formas for q in DIAGRAMAS[clave][1]()[0] if q.puesto == puesto or (q.puesto is None and q.padre == puesto)]
    # Algunos puestos son solo un ancla para el número (sin formas propias): no hay nada que mostrar
    formas = [f for f in formas if any(a for forma in f for a in forma.anillos)]
    if not formas:
        return None
    # Si la pieza viene en varias unidades separadas (dos rodamientos, dos tornillos...), se muestra una sola
    sola = Pieza(None, None)
    sola.agregar(*_una_unidad([forma for f in formas for forma in f]))
    lado = 600
    cuerpo, _ = iso.componer([sola], [], lado, margen=110, transparencia=False)   # mismo encuadre para todas
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}" width="{lado}" height="{lado}">'
            '<defs><pattern id="cuadricula" width="30" height="30" patternUnits="userSpaceOnUse">'
            '<path d="M30 0H0V30" fill="none" stroke="#ece6d8" stroke-width="1"/></pattern></defs>'
            f'<rect width="{lado}" height="{lado}" fill="#fdfcf8"/><rect width="{lado}" height="{lado}" fill="url(#cuadricula)"/>'
            f'{cuerpo}</svg>')


def version_pieza(clave, puesto):
    """Huella del dibujo de una pieza sola (la guía): cambia la dirección cuando cambia el dibujo, así no se ve la vieja."""
    svg = dibujar_pieza(clave, puesto)
    return hashlib.sha1(svg.encode()).hexdigest()[:10] if svg else ""


def usadas_desde_texto(clave, texto):
    """'caliper,pastillas' → frozenset de puestos que existen en el dibujo (lo demás se ignora)."""
    validos = dibujar_lamina(clave, ())["puestos"]
    return frozenset(p for p in (texto or "").split(",") if p in validos) or None


def usadas_a_texto(usadas):
    return ",".join(sorted(usadas or ()))


def ubicar_numeros(clave, asignaciones, anchos=frozenset()):
    """Reparte los números de una lámina sin que se monten.

    asignaciones: [(clave_numero, puesto)] (una por número distinto). Devuelve ({clave_numero: (x, y)}, grupos).
    En el dibujo, los números de un mismo puesto salen en filas desde la etiqueta, alejándose de la pieza, y luego
    se separan entre todos. En la franja, cada grupo muestra sus números ordenados encima de su ícono.
    """
    base = dibujar_lamina(clave, ())["puestos"]
    dibujo = [(k, p) for k, p in asignaciones if p in base]
    usadas = frozenset(p for _, p in dibujo) or None
    if usadas:
        usadas = usadas | frozenset(q for p in usadas for q in ACOMPANANTES.get(p, ()) if q in base)
    franja = [(k, p if p in _ORDEN_HERRAJES else "h_otros") for k, p in asignaciones if p not in base]
    cuenta = {}
    for _, g in franja:
        cuenta[g] = cuenta.get(g, 0) + 1
    grupos = tuple((g, cuenta[g]) for g in _ORDEN_HERRAJES if g in cuenta)
    d = dibujar_lamina(clave, grupos, usadas)
    pos = {}
    usados = {}
    for k, g in franja:
        i = usados.get(g, 0)
        usados[g] = i + 1
        pos[k] = d["casillas"][g][i]
    # Dibujo: los números van afuera, en una columna a cada lado del contorno del dibujo, a la altura de su pieza
    # (cada uno con una línea fina hasta ella, que dibuja el visor). Así no tapan las piezas.
    paso = PASO / LADO
    x0, y0, x1, y1 = d["contorno"]
    techo, piso = d["alto"] - 0.035, 0.04
    centro = (x0 + x1) / 2
    items = []
    for k, p in dibujo:
        ax, ay = d["anclas"].get(p, d["puestos"].get(p, (centro, (y0 + y1) / 2)))
        items.append((k, ax, ay))
    izquierda = [it for it in items if it[1] < centro]
    derecha = [it for it in items if it[1] >= centro]
    # Equilibra los lados si uno queda muy cargado (pasan los más cercanos al centro)
    while len(izquierda) > len(derecha) + 3:
        mover = max(izquierda, key=lambda it: it[1])
        izquierda.remove(mover)
        derecha.append(mover)
    while len(derecha) > len(izquierda) + 3:
        mover = min(derecha, key=lambda it: it[1])
        derecha.remove(mover)
        izquierda.append(mover)
    for lado_items, x_col, hacia_afuera in ((izquierda, x0 - 0.06, -1), (derecha, x1 + 0.06, 1)):
        if not lado_items:
            continue
        lado_items.sort(key=lambda it: it[2])
        capacidad = int((techo - piso) / paso) + 1
        escalonado = len(lado_items) > capacidad
        hueco = paso * (0.56 if escalonado else 1.0)
        ys = []
        for _, _, ay in lado_items:                       # hacia abajo, sin montarse
            ys.append(max(ay, ys[-1] + hueco) if ys else max(ay, piso))
        if ys[-1] > techo:                                # si se pasa del área, se corre hacia arriba
            ys[-1] = techo
            for i in range(len(ys) - 2, -1, -1):
                ys[i] = min(ys[i], ys[i + 1] - hueco)
        for i, (k, _, _) in enumerate(lado_items):
            x = x_col + (hacia_afuera * 0.065 if escalonado and i % 2 else 0)
            pos[k] = (round(min(0.965, max(0.035, x)), 4), round(min(techo, max(piso, ys[i])), 4))
    return pos, grupos, usadas
