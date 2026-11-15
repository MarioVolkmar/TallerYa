"""Diagramas de despiece propios de TallerYa, en isométrico estilo manual técnico.

Cada diagrama arma sólidos 3D sencillos (ver isometrico.py), los "explota" a lo largo de su eje de
montaje y los proyecta en isométrico con líneas de eje y líneas guía hacia el número de cada pieza.
Son dibujos originales por tipo de sistema (sirven para cualquier marca). Cada pieza tiene un "puesto";
las partes de un catálogo se asignan a los puestos por palabras clave (REGLAS), sin marcar a mano.

    dibujar(clave)           → (svg, {puesto: (x, y)})   posición relativa (0..1) del número
    puesto_para(clave, desc) → nombre del puesto o None
    version(clave)           → huella del SVG (para el caché del navegador)
"""
import copy
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


def cadena_eslabones(puntos, grosor=8):
    """Cadena de transmisión: trazo oscuro con los eslabones marcados (no una manguera lisa)."""
    return manguera(puntos, grosor, "#5d666a") + [polilinea(puntos, grosor * .45, "#c9ced0", guiones="3 3")]


def seguro_pin(c, eje, r, grosor=1.6):
    """Pin seguro (anillo elástico): aro delgado de alambre con su abertura, no un anillo grueso."""
    ext = [(math.cos(a) * r, math.sin(a) * r) for a in [0.45 + i * (2 * math.pi - 0.9) / 24 for i in range(25)]]
    return prisma(c, eje, ext + [(x * .84, y * .84) for x, y in ext[::-1]], grosor, lado=LADO_MEDIO, cara="#dfe3e4")


def bujia_real(c, eje=(0, 1, 0), escala=1.0):
    """Bujía desde la punta (electrodo en `c`) hacia el terminal: electrodo, rosca, arandela, hexágono, aislador de
    porcelana con sus anillos y el terminal donde entra el capuchón."""
    a, k = eje, escala
    en = lambda d: tuple(ci + ai * d * k for ci, ai in zip(c, a))
    f = cilindro(en(2), a, 1.2 * k, 4, lado=OSCURO)                                    # electrodo central
    f += cilindro(en(13), a, 4 * k, 18 * k, lado=LADO_MEDIO, cara="#dfe3e4") + iso.roscas(en(13), a, 4 * k, 16 * k, 2.5)
    f += cilindro(en(23), a, 6.5 * k, 2 * k, lado=LADO_MEDIO)                            # arandela de sello
    f += prisma(en(29), a, hexagono(8.5 * k), 10 * k, lado=LADO_MEDIO, cara="#e6e9ea")   # hexágono (llave de bujía)
    f += cilindro(en(46), a, 5.5 * k, 24 * k, r2=4.5 * k, cara="#fbfaf6", lado="#ece8de")  # porcelana
    for d in (40, 46, 52):
        f += cilindro(en(d), a, 5.8 * k, 1.5 * k, cara="#fbfaf6", lado="#ddd8cc")
    f += cilindro(en(62), a, 2.4 * k, 8 * k, lado=LADO_MEDIO) + cilindro(en(66), a, 3.4 * k, 3 * k, lado=LADO_MEDIO)
    return f


def grapa_manguera(c, r=6):
    """Guía o grapa de manguera: aro que la abraza y pestaña para atornillarla al chasis."""
    x, y, z = c
    return (caja((x + r + 5, y, z), (10, 3, 10), colores=(OSCURO, LADO_MEDIO, OSCURO))
            + cilindro(c, Y, r + 2, 9, ri=r, lado=OSCURO, cara=LADO_MEDIO))


def tapon_perno(base_cabeza, eje, largo, d, cabeza=None):
    """Tapón de drenaje o de llenado: tornillo de cabeza hexagonal con su arandela de sello bajo la cabeza."""
    a = eje
    arandela_c = tuple(b + x * 1.2 for b, x in zip(base_cabeza, a))
    return perno(base_cabeza, a, largo, d, cabeza or d * 1.7) + arandela(arandela_c, a, d * .95, 2, color="#e8c9a0", lado="#c9a227")


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
def _bomba_mano(lado=1, sufijo="", con_linea=True):
    """Bomba de freno de manubrio. lado=1: derecha (freno delantero); lado=-1: izquierda (freno trasero de las scooter),
    con la manigueta hacia afuera. El sufijo distingue los puestos de la segunda bomba ("_trasera")."""
    s = lado
    tubo = curva((-30 * s, -40, 0), (-40 * s, -170, 40), (110 * s, -230, 170))
    manigueta = [(-30, -10), (10, -12), (60, -16), (110, -12), (140, -4), (144, 6), (112, 0), (60, -4), (10, 2), (-30, 14)]
    piezas = [
        # Cuerpo de la bomba: cilindro con su tapa del extremo, el soporte del espejo, la salida de la manguera
        # (abajo) y el pivote de la manigueta al final
        P("bomba" + sufijo, cilindro((10 * s, 0, 0), X, 16, 104, lado="#d5d9da", cara="#eceeef")
          + cilindro((64 * s, 0, 0), X, 13, 6, cara="#e3e6e7") + cilindro((-46 * s, 0, 0), X, 19, 8, lado="#d5d9da")
          + cilindro((-30 * s, -18, 0), Y, 11, 14, lado="#d5d9da") + cilindro((-56 * s, 24, -8), Y, 8, 14, ri=3.5, lado="#d5d9da")
          + cilindro((62 * s, 0, 34), Y, 10, 36, ri=3.5, lado="#d5d9da") + caja((40 * s, 0, 22), (40, 18, 24)), (0, 0, 0), (-80 * s, 60)),
        # Depósito integrado, con su visor del nivel del líquido
        P("deposito" + sufijo, prisma((4 * s, 52, 0), Y, redondeado(74, 52, 15), 34, lado="#d5d9da", cara="#eceeef")
          + cilindro((4 * s, 48, 27), Z, 9, 2, cara="#cfe6f1", lado="#9fbfcc"), (4 * s, 52, 0), (-85 * s, -10)),
        P("diafragma" + sufijo, prisma((4 * s, 88, 0), Y, redondeado(66, 46, 13), 6, hueco=redondeado(40, 22, 8), lado=CAUCHO, cara=CAUCHO_CARA),
          (4 * s, 88, 0), (-85 * s, -25)),
        P("tapa" + sufijo, prisma((4 * s, 112, 0), Y, redondeado(78, 56, 16), 6, lado=LADO_MEDIO, cara="#f4f5f5")
          + prisma((4 * s, 112, 0), Y, redondeado(54, 32, 10), 1, lado=LADO_MEDIO, cara="#e8eaeb"), (4 * s, 112, 0), (-80 * s, -45)),
        P(None, perno((-22 * s, 150, -14), MENOS_Y, 16, 5) + perno((22 * s, 150, 14), MENOS_Y, 16, 5), (0, 150, 0), (70 * s, -40), herraje="h_tornillo"),
        # Manigueta: brazo curvo con su punta redondeada y la ruedita de ajuste junto al pivote (hacia afuera del manubrio)
        P("manigueta" + sufijo, prisma((92 * s, -4, 70), Y, [(u * s, v) for u, v in manigueta], 8, lado=LADO_MEDIO, cara="#f1f3f4")
          + cilindro((62 * s, -4, 52), Y, 9, 10, lado=OSCURO, cara=LADO_MEDIO), (140 * s, -4, 70), (70 * s, 50)),
        P("abrazadera" + sufijo, prisma((-75 * s, 0, 0), X, redondeado(34, 44, 7), 20, hueco=iso._circ2d(15, 24)), (-75 * s, 0, 0), (-70 * s, 55)),
        P("interruptor" + sufijo, caja((48 * s, -30, -20), (16, 9, 12), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + cilindro((38 * s, -30, -20), X, 2.5, 6, lado=LADO_MEDIO)
          + caja((52 * s, -30, -12), (3, 2, 6), colores=("#d8b36a",) * 3, grosor=1) + caja((44 * s, -30, -12), (3, 2, 6), colores=("#d8b36a",) * 3, grosor=1),
          (48 * s, -30, -20), (70 * s, -10)),
        P("kit_reparacion" + sufijo, cilindro((175 * s, 0, 0), X, 10, 34) + oring((205 * s, 0, 0), X, 10) + resorte((235 * s, 0, 0), X, 7, 36, 6),
          (205 * s, 0, 0), (60 * s, -50)),
        P("banjo" + sufijo, perno((-30 * s, -10, 0), MENOS_Y, 26, 9) + arandela((-30 * s, -24, 0), Y, 11), (-30 * s, -10, 0), (-75 * s, 20)),
    ]
    if con_linea:
        piezas += [
            P("manguera" + sufijo, manguera(tubo), tubo[8], (-80 * s, 40)),
            P("soporte_manguera" + sufijo, grapa_manguera((60 * s, -205, 110), 7), (60 * s, -205, 110), (65 * s, 30)),
        ]
    return piezas


def _bomba_freno():
    piezas = _bomba_mano(1) + [
        P("unidad_abs", caja((230, -230, 60), (80, 56, 70), colores=(LADO_MEDIO, BLANCO, LADO_CLARO))
          + cilindro((215, -195, 50), Y, 7, 12) + cilindro((245, -195, 70), Y, 7, 12), (230, -230, 60), (70, 40)),
    ]
    lineas = [linea((-120, 0, 0), (260, 0, 0)), linea((0, 20, 0), (0, 170, 0)), linea((-30, -50, 0), (-30, 30, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 2b. Dos bombas de mano con ABS (scooter: freno trasero también de manigueta). Derecha = delantero, izquierda = trasero.
#     Las mangueras de cada bomba bajan a la unidad ABS y de ella salen los tubos hacia cada caliper.
# ---------------------------------------------------------------------------
def _bombas_abs():
    D, I = 230, -230                                       # bomba derecha (delantero) e izquierda (trasero)
    derecha = [_mover(q, (D, 0, 0)) for q in _bomba_mano(1, con_linea=False)]
    izquierda = [_mover(q, (I, 0, 0)) for q in _bomba_mano(-1, "_trasera", con_linea=False)]
    abs_c = (0, -300, 40)
    m1 = curva((D - 30, -40, 0), (D - 20, -200, 20), (abs_c[0] + 30, abs_c[1] + 40, abs_c[2]))
    m2 = curva((I + 30, -40, 0), (I + 20, -200, 20), (abs_c[0] - 30, abs_c[1] + 40, abs_c[2]))
    t1 = curva((abs_c[0] + 30, abs_c[1] - 30, abs_c[2]), (160, -420, 120), (300, -470, 200))
    t2 = curva((abs_c[0] - 30, abs_c[1] - 30, abs_c[2]), (-160, -420, 120), (-300, -470, 200))
    piezas = derecha + izquierda + [
        P("manguera", manguera(m1), m1[8], (70, 30), orden=2),
        P("manguera_trasera", manguera(m2), m2[8], (-70, 30), orden=2),
        P("unidad_abs", caja(abs_c, (90, 60, 74), colores=(LADO_MEDIO, BLANCO, LADO_CLARO))
          + caja((abs_c[0], abs_c[1] + 14, abs_c[2] - 50), (60, 34, 26), colores=(OSCURO, LADO_MEDIO, OSCURO))      # motor y conector
          + [f for dx in (-30, -10, 10, 30) for f in cilindro((abs_c[0] + dx, abs_c[1] + 34, abs_c[2] + 10), Y, 6, 8)],
          (abs_c[0], abs_c[1] + 30, abs_c[2]), (70, 50), orden=3),
        P("tubos", manguera(t1, 5, "#c9ced0") + manguera(t2, 5, "#c9ced0"), t1[10], (70, 40), orden=2),
        P("guia_manguera", grapa_manguera(m1[10]) + grapa_manguera(m2[10])
          + grapa_manguera(t1[8]), m1[10], (60, -30), orden=3),
        P("soporte_abs", prisma((abs_c[0], abs_c[1] - 52, abs_c[2]), Y, redondeado(130, 70, 10), 4, lado=LADO_MEDIO, cara="#e9ecec"),
          (abs_c[0] + 50, abs_c[1] - 52, abs_c[2]), (70, 30), orden=1),
    ]
    lineas = [linea((I - 140, 0, 0), (D + 140, 0, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 2c. Bomba trasera de pie: cilindro atornillado al chasis, varilla con horquilla hacia el pedal y depósito aparte
#     unido por una manguera corta (no es una bomba de manubrio).
# ---------------------------------------------------------------------------
def _bomba_pie():
    gris, claro = "#d5d9da", "#eceeef"
    deposito = (-110, 120, 0)
    mdep = curva((deposito[0], deposito[1] - 40, 0), (-80, 40, 0), (-18, 30, 0))
    return [
        P("bomba", cilindro((0, 0, 0), Y, 15, 96, lado=gris, cara=claro)
          + prisma((0, 20, 0), Z, redondeado(70, 22, 8), 18, lado=gris, cara=claro)                          # brida de montaje
          + cilindro((-26, 20, 10), Z, 5, 1, cara=HUECO, grosor=1) + cilindro((26, 20, 10), Z, 5, 1, cara=HUECO, grosor=1)
          + cilindro((-14, 30, 0), X, 6, 16, lado=gris, cara=claro), (0, 0, 0), (-80, 60)),                    # entrada del depósito
        P("varilla", cilindro((0, -80, 0), Y, 4, 70) + tuerca((0, -62, 0), Y, 6)
          + caja((0, -122, 0), (16, 22, 14), colores=(LADO_MEDIO, "#eef0f0", LADO_CLARO))
          + cilindro((0, -126, 0), Z, 3.5, 22), (0, -122, 0), (-70, 40)),
        P("guardapolvo", cilindro((0, -56, 0), Y, 9, 20, r2=5, lado=CAUCHO, cara=CAUCHO_CARA), (0, -56, 0), (70, 20)),
        P("deposito", prisma(deposito, Y, redondeado(46, 34, 10), 58, lado="#e6e9ea", cara="#f4f6f6")
          + [polilinea([(deposito[0] - 23.5, deposito[1] + k, deposito[2] + 8), (deposito[0] - 23.5, deposito[1] + k, deposito[2] - 8)], 1, "#8f9597")
             for k in (-12, 10)], (deposito[0], deposito[1], deposito[2]), (-85, -10)),
        P("diafragma", prisma((deposito[0], deposito[1] + 40, 0), Y, redondeado(42, 30, 9), 5, lado=CAUCHO, cara=CAUCHO_CARA),
          (deposito[0], deposito[1] + 40, 0), (-85, -25)),
        P("tapa", cilindro((deposito[0], deposito[1] + 58, 0), Y, 22, 10, lado=LADO_MEDIO, cara="#f4f5f5"), (deposito[0], deposito[1] + 58, 0), (-80, -45)),
        P("manguera_deposito", manguera(mdep, 6), mdep[8], (-70, 10)),
        P("kit_reparacion", cilindro((90, 20, 0), Y, 10, 30) + oring((90, 44, 0), Y, 10) + resorte((90, 74, 0), Y, 7, 36, 6), (90, 44, 0), (60, -50)),
        P("banjo", perno((0, 70, 0), MENOS_Y, 26, 9) + arandela((0, 56, 0), Y, 11), (0, 70, 0), (70, -20)),
        P("interruptor", cilindro((60, -40, 30), Y, 6, 30, lado=OSCURO, cara=LADO_MEDIO) + resorte((60, -70, 30), Y, 4, 26, 6), (60, -40, 30), (70, 10)),
    ]


def _freno_trasero():
    """Freno trasero de disco completo: bomba de pie con su depósito, manguera, caliper y pedal."""
    CALIPER = (260, -330, -40)
    caliper = [_mover(q, CALIPER) for q in _freno_disco()[0] if q.puesto != "disco" and q.padre != "disco"]
    entrada = tuple(a + b for a, b in zip(CALIPER, (20, 46, -6)))
    tubo = curva((0, 82, 0), (120, 160, 40), (entrada[0] - 60, entrada[1] + 160, entrada[2] + 40)) \
        + curva((entrada[0] - 60, entrada[1] + 160, entrada[2] + 40), (entrada[0] - 10, entrada[1] + 60, entrada[2] + 10), entrada)[1:]
    pedal = [(-12, -14), (150, -26), (176, -20), (180, -6), (160, 4), (20, 18), (-10, 16), (-24, 0)]
    piezas = _bomba_pie() + caliper + [
        P("manguera", manguera(tubo, 8), tubo[12], (80, 30), orden=2),
        P("guia_manguera", grapa_manguera(tubo[10])
          + grapa_manguera(tubo[22]), tubo[22], (60, -30), orden=3),
        P("soporte_deposito", prisma((-110, 60, -20), Z, [(-14, 40), (14, 40), (18, -30), (6, -60), (-10, -60), (-18, -30)], 6,
                                     hueco=iso._circ2d(5, 12), lado=LADO_MEDIO), (-110, 40, -20), (-70, -20), orden=1),
        # Pedal: su brazo corto sube a la horquilla de la varilla de la bomba
        P("pedal", prisma((-150, -200, 60), Z, pedal, 12, hueco=iso._circ2d(9, 20), lado=LADO_MEDIO, cara="#f1f3f4")
          + cilindro((-150 + 172, -200 - 13, 60 + 14), Z, 11, 26, cara=CAUCHO_CARA, lado=CAUCHO)
          + resorte((-150 + 40, -200 + 30, 70), Y, 6, 46, 7) + cilindro((-150, -200, 40), Z, 8, 46), (-90, -210, 66), (-60, 50), orden=1),
    ]
    lineas = [("bomba", linea((0, -140, 0), (0, 160, 0))),
              ("pastillas", linea((CALIPER[0] + 70, CALIPER[1] - 36, CALIPER[2] + 25), (CALIPER[0] + 70, CALIPER[1] - 122, CALIPER[2] + 25)))]
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
          + [polilinea([(13.6, 130 + r * math.sin(t + 0.5 * (r - 30) / 45), r * math.cos(t + 0.5 * (r - 30) / 45)) for r in range(30, 76, 5)], 2.6, "#7d8487")
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
def _rotor_interior(r, lobulos=4):
    """Rotor interior de la bomba trocoidal: estrella de lóbulos redondeados."""
    return [((r + 5 * math.cos(lobulos * t)) * math.cos(t), (r + 5 * math.cos(lobulos * t)) * math.sin(t))
            for t in [i * 2 * math.pi / 64 for i in range(64)]]


def _aceite():
    """Como en los planos: la mitad del cárter de referencia; la bomba (con su piñón) montada en la cara del cárter,
    y abajo, en el sumidero, la malla con su resorte, el O-ring y el tapón de drenaje. El filtro de papel y su tapa solo
    aparecen en las motos que lo tienen (no todas: las scooter y muchas 125 solo llevan malla)."""
    al_cara, al_lado = "#f4f2ec", "#dcd7cb"
    xd, zd = -60, 14                               # eje del drenaje, bajo el sumidero del cárter
    # Bomba trocoidal explotada a lo largo de X, saliendo de la cara del cárter: cuerpo, rotores, tapa y piñón
    by, bz = -30, -70
    cuerpo = cilindro((14, by, bz), X, 34, 22, lado=al_lado, cara=al_cara) + cilindro((26, by, bz), X, 25, 1, cara=HUECO, grosor=1)
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.5
        cuerpo += cilindro((14, by + 40 * math.sin(a), bz + 40 * math.cos(a)), X, 7, 22, ri=3, lado=al_lado, cara=al_cara)
    exterior = prisma((44, by, bz), X, iso._circ2d(25, 48), 9, hueco=_rotor_interior(16, 5), lado=LADO_MEDIO, cara="#e9ecec")
    interior = prisma((62, by, bz), X, _rotor_interior(12, 4), 9, hueco=iso._circ2d(4, 16), lado=LADO_MEDIO, cara="#f3f3ef")
    tapa = prisma((82, by, bz), X, iso._circ2d(34, 48), 6, lado=al_lado, cara=al_cara)
    pinon = (cilindro((100, by, bz), X, 5, 50) + prisma((112, by, bz), X, engranaje(36, 34, 3.5), 7, hueco=iso._circ2d(9, 16),
                                                        cara="#f6f6f4", lado=LADO_MEDIO)
             + [f for k in range(4) for f in cilindro((116, by + 16 * math.sin(k * 1.571), bz + 16 * math.cos(k * 1.571)), X, 3, 1, cara=HUECO, grosor=1)])
    # Filtro de papel (cartucho plisado) y su tapa: solo si la lámina los trae
    pliegues = [polilinea([(60, 70 + 24 * math.sin(t), 150 + 24 * math.cos(t)), (100, 70 + 24 * math.sin(t), 150 + 24 * math.cos(t))], 1)
                for t in [i * math.pi / 9 for i in range(18)]]
    filtro = cilindro((80, 70, 150), X, 24, 40, ri=8, cara="#f7efd6", lado="#e2d5ad") + pliegues
    tapa_filtro = (cilindro((140, 70, 150), X, 32, 14, lado=al_lado, cara=al_cara)
                   + [f for k in range(3) for f in cilindro((148, 70 + 27 * math.sin(k * 2.094), 150 + 27 * math.cos(k * 2.094)), X, 5, 4, ri=2, lado=LADO_MEDIO)])
    # Malla (cedazo): marco con la tela metálica, que entra en el sumidero
    malla = (cilindro((xd, -150, zd), Y, 16, 4, cara="#d9dcdc", lado=LADO_MEDIO) + cilindro((xd, -186, zd), Y, 16, 4, cara="#d9dcdc", lado=LADO_MEDIO)
             + cilindro((xd, -168, zd), Y, 15, 32, ri=10, cara="#eef0ef", lado="#cfd5d7")
             + [polilinea([(xd + 15.3 * math.cos(t), -152, zd + 15.3 * math.sin(t)), (xd + 15.3 * math.cos(t + .5), -184, zd + 15.3 * math.sin(t + .5))], .8, "#9aa2a5")
                for t in [i * math.pi / 10 for i in range(-3, 13)]])
    # Tapón de drenaje: tapa ancha con pestaña y estrías (scooter) sobre su rosca
    tapon = (cilindro((xd, -282, zd), Y, 26, 12, lado=LADO_MEDIO, cara="#eef0f0")
             + [polilinea([(xd + 26.3 * math.cos(t), -276, zd + 26.3 * math.sin(t)), (xd + 26.3 * math.cos(t), -288, zd + 26.3 * math.sin(t))], 1, "#9aa2a5")
                for t in [i * math.pi / 8 for i in range(-3, 9)]]
             + cilindro((xd, -272, zd), Y, 29, 4, lado=LADO_MEDIO, cara="#e6e9e9")
             + cilindro((xd, -256, zd), Y, 20, 26, ri=8, lado=LADO_MEDIO, cara="#eef0f0") + iso.roscas((xd, -256, zd), Y, 20, 24, 4))
    piezas = [
        P("carter", _media_carcasa(-60), (-60, 128, 30), (-70, -70)),
        P("bomba", cuerpo + exterior + interior + tapa, (44, by + 25, bz), (65, -55)),
        P("pinon_bomba", pinon, (112, by + 36, bz), (65, -40)),
        P(None, perno((140, by + 16, bz), X, 26, 5) + perno((140, by - 16, bz), X, 26, 5), (150, by + 16, bz), (70, 20), herraje="h_tornillo"),
        P("filtro", filtro, (80, 94, 150), (-70, -50)),
        P("tapa_filtro", tapa_filtro, (140, 102, 150), (-70, -20)),
        P("malla", malla, (xd, -168, zd), (-75, 0)),
        P("resorte", resorte((xd, -212, zd), Y, 11, 40, 6), (xd, -212, zd), (-75, 0)),
        P("oring", oring((xd, -240, zd), Y, 22), (xd, -240, zd), (-75, 10)),
        P("tapon", tapon, (xd, -282, zd), (-75, 20)),
    ]
    lineas = [linea((xd, -124, zd), (xd, -300, zd)), linea((-40, by, bz), (160, by, bz))]
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
        P("motor_ralenti", cilindro((-45, 105, -10), Y, 10, 18, lado=OSCURO, cara=LADO_MEDIO) + caja((-45, 118, -10), (10, 8, 12), colores=(CAUCHO,) * 3)
          + cilindro((-45, 92, -10), Y, 3.5, 10, lado=LADO_MEDIO), (-45, 105, -10), (-60, -40)),
        P("inyector", cilindro((-95, 105, 10), Y, 6, 40, lado=OSCURO, cara=LADO_MEDIO) + caja((-86, 118, 10), (10, 10, 9), colores=(CAUCHO,) * 3)
          + oring((-95, 126, 10), Y, 7, 3) + oring((-95, 85, 10), Y, 7, 3) + cilindro((-95, 76, 10), Y, 3, 12, lado=LADO_MEDIO),
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
# Colores por material, para que cada pieza se distinga de la de al lado
_ALUMINIO = ("#f4f2ec", "#dcd7cb")       # culata y tapa (cara, lado)
_HIERRO = ("#e3e7e8", "#bfc6c9")         # cilindro
_EMPAQUE_METAL = ("#c9a27a", "#a77f58")  # empaque de culata (lámina metálica cobriza)
_EMPAQUE_PAPEL = ("#eadcb4", "#cdbb8c")  # empaque de la base del cilindro
_ESQUINAS = [(48, 36), (-48, 36), (48, -36), (-48, -36)]   # espárragos (x, z)


def _huecos_esparragos(y, r=4.5):
    return [f for x, z in _ESQUINAS for f in cilindro((x, y, z), Y, r, 1, cara=HUECO, lado=HUECO, grosor=1)]


def _empaque_plano(y, colores, agujero=40, ancho=132, fondo=102):
    cara, lado = colores
    return (prisma((0, y, 0), Y, redondeado(ancho, fondo, 14), 2.5, hueco=iso._circ2d(agujero, 36), lado=lado, cara=cara, grosor=1.6)
            + _huecos_esparragos(y + 1.6))


def _aletas(y0, n, paso, ancho, fondo, colores):
    cara, lado = colores
    return [f for k in range(n) for f in prisma((0, y0 + k * paso, 0), Y, redondeado(ancho, fondo, 16), 3.2, lado=lado, cara=cara, grosor=1.2)]


def _perfil(texto):
    """'l1c2d59v4b1' → refrigeración líquida, 2 cilindros, 59 mm de diámetro, 4 válvulas (DOHC), 1 bujía por cilindro."""
    p = {"l": 0, "c": 1, "d": 57, "v": 2, "b": 1, "m": 0, "h": 0, "e": 0, "s": 0, "i": 0, "u": 0}
    for letra, numero in re.findall(r"([lcdvbmhesiu])(\d+)", texto or ""):
        p[letra] = int(numero)
    p["c"] = max(1, min(p["c"], 4))
    return p


def _bloque_motor(p):
    """Medidas del bloque según el perfil: radio del cilindro, centros de los cilindros, ancho y fondo."""
    r = max(30.0, min(46.0, p["d"] * 0.7))
    paso = 2 * r + 30
    xs = [(i - (p["c"] - 1) / 2) * paso for i in range(p["c"])]
    ancho = p["c"] * (2 * r + 30) + 16
    fondo = 2 * r + 28
    esquinas = sorted({(round(xc + sx * (r + 9)), round(sz * (r - 2))) for xc in xs for sx in (-1, 1) for sz in (-1, 1)})
    return r, xs, ancho, fondo, esquinas


def _aletas_bloque(y0, n, paso, ancho, fondo, colores):
    cara, lado = colores
    return [f for k in range(n) for f in prisma((0, y0 + k * paso, 0), Y, redondeado(ancho, fondo, 16), 3.2, lado=lado, cara=cara, grosor=1.2)]


def _plancha_empaque(y, ancho, fondo, r, xs, esquinas, colores):
    """Empaque plano: lámina del tamaño del bloque con el hueco de cada cilindro y de cada espárrago."""
    cara, lado = colores
    f = prisma((0, y, 0), Y, redondeado(ancho, fondo, 14), 2.5, lado=lado, cara=cara, grosor=1.6)
    for xc in xs:
        f += cilindro((xc, y + 1.4, 0), Y, r + 2, .6, cara=HUECO, lado=HUECO, grosor=1)
    for x, z in esquinas:
        f += cilindro((x, y + 1.4, z), Y, 4.5, .6, cara=HUECO, lado=HUECO, grosor=1)
    return f


def _bloque_cilindro(y, alto, p, r, xs, ancho, fondo):
    """Cilindro(s): con aletas si es de aire; liso, con la camisa de agua y la entrada del refrigerante si es líquido."""
    fe_cara, fe_lado = _HIERRO
    f = caja((-ancho / 2 - 8, y, -fondo * .22), (22, alto, 22), colores=(fe_lado, fe_cara, fe_lado))        # túnel de la cadenilla
    if p["l"]:
        f += prisma((0, y, 0), Y, redondeado(ancho - 6, fondo - 4, 18), alto, lado=fe_lado, cara=fe_cara)
        f += [polilinea([(x, y + alto / 2 + .5, z) for x, z in _contorno_camisa(ancho - 26, fondo - 22)], 1.3, "#9aa3a7")]
        f += cilindro((xs[-1], y - alto * .2, fondo / 2 + 10), Z, 9, 22, ri=5, lado=fe_lado, cara=fe_cara)  # entrada del refrigerante
    else:
        f += _aletas_bloque(y - alto / 2 + 8, int(alto // 13), 13, ancho + 14, fondo + 12, _HIERRO)
    for xc in xs:
        f += cilindro((xc, y, 0), Y, r + 4, alto, ri=r - 3, cara=fe_cara, lado=fe_lado)
    return f


def _contorno_camisa(ancho, fondo):
    puntos = redondeado(ancho, fondo, 16)
    return [(u, v) for u, v in puntos] + [puntos[0]]


def _culata(perfil=None):
    p = _perfil(perfil)
    r, xs, ancho, fondo, esquinas = _bloque_motor(p)
    al_cara, al_lado = _ALUMINIO
    dohc = bool(p.get("h"))
    # Tapa de válvulas: con dos "lomos" de árboles de levas si es DOHC; con nervios y tapones de calibración si es SOHC
    tapa = prisma((0, 372, 0), Y, redondeado(ancho - 14, fondo - 10, 26), 26, lado=al_lado, cara=al_cara)
    if dohc:
        for z in (-fondo * .22, fondo * .22):
            tapa += cilindro((0, 388, z), X, 13, ancho - 46, lado=al_lado, cara=al_cara)
    else:
        tapa += [polilinea([(x, 385.5, -fondo * .3), (x, 385.5, fondo * .3)], 1.6, "#c9c3b4") for x in
                 [xs[0] - r * .7 + k * r * .47 for k in range(int(len(xs) * 4))]]
        for xc in xs:
            tapa += cilindro((xc - r * .9, 392, fondo * .2), Y, 10, 10, lado=LADO_MEDIO, cara="#e9e6de")
            tapa += cilindro((xc + r * .9, 392, fondo * .2), Y, 10, 10, lado=LADO_MEDIO, cara="#e9e6de")
    # Culata: bloque con aletas (aire) o liso con la salida del refrigerante (líquido); puertos por cilindro
    culata = caja((-ancho / 2 - 8, 262, -fondo * .22), (24, 60, 20), colores=(al_lado, al_cara, al_lado))
    culata += prisma((0, 262, 0), Y, redondeado(ancho, fondo, 14), 60, lado=al_lado, cara=al_cara)
    if p["l"]:
        culata += cilindro((xs[-1] + r * .4, 292, -fondo / 2 - 12), Z, 10, 26, ri=6, lado=al_lado, cara=al_cara)   # salida del agua
        culata += caja((xs[-1] + r * .4, 292, -fondo / 2 + 4), (30, 22, 14), colores=(al_lado, al_cara, al_lado))
    else:
        culata += _aletas_bloque(236, 4, 13, ancho + 14, fondo + 12, _ALUMINIO)
    for xc in xs:
        culata += cilindro((xc, 294, 0), Y, 12, 4, cara=HUECO, lado=al_lado)                                       # bujía
        culata += cilindro((xc, 250, fondo / 2 + 14), Z, r * .45, 28, ri=r * .3, lado=al_lado, cara=al_cara)      # escape
        if p["c"] == 1:
            culata += cilindro((-ancho / 2 - 22, 262, fondo * .1), X, r * .4, 28, ri=r * .28, lado=al_lado, cara=al_cara)
        else:
            culata += cilindro((xc, 268, -fondo / 2 - 14), Z, r * .4, 28, ri=r * .28, lado=al_lado, cara=al_cara)
    # Bujías: una por cilindro (o tres en las de triple chispa), dibujadas aparte, a la derecha
    def una_bujia(x, z, escala=1.0):
        return bujia_real((x, 344, z), Y, escala)
    bujias, x0 = [], ancho / 2 + 60
    for k in range(p["c"] * p["b"]):
        bujias += una_bujia(x0 + k * 30, -20, 1.0 if k % max(1, p["b"]) == 0 else .8)
    piezas = [
        P("tapa_valvulas", tapa, (0, 385, 0), (-90, -40), orden=6),
        P("empaque_tapa", prisma((0, 334, 0), Y, redondeado(ancho - 14, fondo - 10, 26), 3, hueco=redondeado(ancho - 28, fondo - 24, 20),
                                 lado=CAUCHO, cara=CAUCHO_CARA, grosor=1.5), (ancho / 2 - 14, 334, 30), (-90, 0), orden=5),
        P("bujia", bujias, (x0, 392, -20), (70, -40), orden=7),
        P("culata", culata, (0, 262, 0), (-95, 20), orden=4),
        P("empaque_culata", _plancha_empaque(196, ancho, fondo, r, xs, esquinas, _EMPAQUE_METAL), (ancho / 2 - 14, 197, 30), (-90, 20), orden=3),
        P("cilindro", _bloque_cilindro(70, 108, p, r, xs, ancho, fondo), (0, 70, 0), (-95, 30), orden=2),
        P("empaque_cilindro", _plancha_empaque(-20, ancho, fondo, r + 2, xs, esquinas, _EMPAQUE_PAPEL), (ancho / 2 - 14, -19, 30), (-90, 30), orden=1),
        P("guias", [f for x, z in esquinas[:2] for f in cilindro((x, 166, z), Y, 6, 16, ri=3, cara="#e9ecec")], (esquinas[0][0], 166, esquinas[0][1]),
          (70, 20), orden=3),
        P("esparragos", [f for x, z in ((ancho / 2 + 30, -60), (ancho / 2 + 46, -40)) for f in cilindro((x, 150, z), Y, 4, 150)
                         + roscas_simple((x, 222, z))], (ancho / 2 + 38, 190, -50), (70, 10), orden=0),
        P(None, perno((ancho / 2 + 40, -40, 70), MENOS_Y, 34, 7) + perno((ancho / 2 + 66, -40, 40), MENOS_Y, 34, 7),
          (ancho / 2 + 53, -40, 55), (70, 30), herraje="h_tornillo"),
        P("anillos", [f for xc in xs for f in _anillos((xc, -66, 0), r * .93)], (xs[0] + r, -57, 0), (70, 10), orden=1),
        P("piston", [f for xc in xs for f in _piston((xc, -120, 0), r * .9)], (xs[0], -110, 0), (-90, 40), orden=1),
        P("pasador", [f for xc in xs for f in cilindro((xc, -124, 100), Z, 9, 64, ri=5, cara="#e9ecec")], (xs[0], -124, 120), (70, 30), orden=2),
        P("seguros_piston", [f for xc in xs for f in seguro_pin((xc, -124, 148), Z, 9) + seguro_pin((xc, -124, 56), Z, 9)],
          (xs[0], -124, 148), (70, 40), orden=2),
    ]
    lineas = [linea((xc, -150, 0), (xc, 420, 0)) for xc in xs]
    return piezas, lineas


def roscas_simple(c):
    """Cuatro líneas de rosca en la punta de un espárrago."""
    x, y, z = c
    return [polilinea([(x - 4, y - k * 4, z), (x + 4, y - k * 4 - 2, z)], 1) for k in range(4)]



# ---------------------------------------------------------------------------
# 7. Válvulas y balancines
# ---------------------------------------------------------------------------
def _valvulas(perfil=None):
    """Válvulas, resortes, cuñas y sellos, con los balancines y el árbol de levas. Con cuatro válvulas por cilindro van dos
    de admisión y dos de escape, y cada balancín termina en horquilla para empujar las dos (como en la Pulsar NS 200)."""
    p = _perfil(perfil)
    cuatro = p["v"] >= 4
    zs = (-24, 24) if cuatro else (0,)

    def pila(x, z):
        return {
            "valvula": cilindro((x, 40, z), Y, 3, 130) + cilindro((x, -28, z), Y, 20 if not cuatro else 16, 8, r2=4),
            "sello": cilindro((x, 110, z), Y, 6, 8, ri=3, cara=CAUCHO_CARA, lado=CAUCHO)
                     + cilindro((x, 116, z), Y, 5, 4, r2=3.6, ri=3, cara=CAUCHO_CARA, lado=CAUCHO) + resorte((x, 116, z), Y, 5.4, 3, 2, 1.2),
            "base": arandela((x, 128, z), Y, 15, 2.5),
            "resorte": resorte((x, 168, z), Y, 13 if cuatro else 15, 62, 7),
            "platillo": cilindro((x, 210, z), Y, 9, 6, r2=14, ri=4),
            "cunas": prisma((x - 3, 226, z), Y, [(-math.cos(a) * 5, math.sin(a) * 5) for a in [i * math.pi / 8 for i in range(-4, 5)]], 12,
                            lado=LADO_MEDIO, cara="#e6e9ea")
                     + prisma((x + 3, 226, z), Y, [(math.cos(a) * 5, math.sin(a) * 5) for a in [i * math.pi / 8 for i in range(-4, 5)]], 12,
                              lado=LADO_MEDIO, cara="#e6e9ea"),
        }
    adm = [pila(0, z) for z in zs]
    esc = [pila(170, z) for z in zs]
    junta = lambda clave: [f for q in adm + esc for f in q[clave]]
    balancin = [(-60, 6), (-50, 16), (40, 12), (66, 4), (66, -6), (40, -12), (-50, -14), (-62, -4)]
    levas = [(math.cos(t) * (14 + 7 * max(0, math.cos(t)) ** 3), math.sin(t) * (14 + 7 * max(0, math.cos(t)) ** 3))
             for t in [i * 2 * math.pi / 32 for i in range(32)]]
    brazos = prisma((85, 285, 0), Z, balancin, 16, hueco=iso._circ2d(8, 16))
    if cuatro:                                            # horquilla: una punta sobre cada válvula
        brazos += caja((22, 274, 0), (14, 10, 64), colores=(LADO_MEDIO, BLANCO, LADO_CLARO))
        brazos += caja((148, 274, 0), (14, 10, 64), colores=(LADO_MEDIO, BLANCO, LADO_CLARO))
    calibra = [f for z in zs for f in perno((150, 312, z), MENOS_Y, 22, 6) + tuerca((150, 300, z), Y, 7)]
    piezas = [
        P("valvula_admision", [f for q in adm for f in q["valvula"]], (0, -10, zs[0]), (-80, 40)),
        P("valvula_escape", [f for q in esc for f in q["valvula"]], (170, -10, zs[-1]), (70, 40)),
        P("sello", junta("sello"), (0, 112, zs[0]), (-80, 10)),
        P("base_resorte", junta("base"), (0, 128, zs[0]), (-80, 25)),
        P("resortes", junta("resorte"), (0, 168, zs[0]), (-85, 0)),
        P("platillo", junta("platillo"), (0, 210, zs[0]), (-80, -10)),
        P("cunas", junta("cunas"), (0, 226, zs[0]), (-80, -30)),
        P("balancin", brazos, (60, 285, 0), (-60, -60)),
        P("eje_balancin", cilindro((85, 285, -70), Z, 6, 80), (85, 285, -100), (60, -50)),
        P("tornillo_calibracion", calibra, (150, 312, zs[-1]), (65, -45)),
        P("arbol_levas", cilindro((85, 350, 40), Z, 8, 150) + prisma((85, 350, 10), Z, levas, 12) + prisma((85, 350, 50), Z, levas, 12),
          (85, 350, 90), (-70, -50)),
    ]
    lineas = [linea((0, -50, z), (0, 250, z)) for z in zs] + [linea((170, -50, z), (170, 250, z)) for z in zs] \
        + [linea((85, 285, -130), (85, 285, 70))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 8. Radiador y refrigeración
# ---------------------------------------------------------------------------
def _radiador():
    """Refrigeración líquida como en los planos: radiador con su tapa, ventilador detrás, rejilla adelante; manguera de
    arriba (termostato → radiador), de abajo (radiador → tubo en T → bomba de agua) y el depósito de expansión con la suya."""
    panal = [polilinea([(9.5, -70, z), (9.5, 70, z)], 1.0, "#7f878a") for z in range(-56, 60, 7)]
    aspas = [(math.cos(t) * (50 if i % 2 == 0 else 20), math.sin(t) * (50 if i % 2 == 0 else 20))
             for i, t in enumerate(i * 2 * math.pi / 18 for i in range(18))]
    superior = curva((0, 70, -60), (60, 120, -150), (150, 60, -200))                # del termostato (motor) al radiador
    inferior = curva((0, -70, 60), (40, -150, 40), (110, -190, -60))                 # del radiador al tubo en T
    hacia_bomba = curva((110, -190, -60), (160, -220, -120), (210, -200, -170))      # del tubo en T a la bomba de agua
    deposito = (40, -60, 170)
    al_deposito = curva((0, 105, 30), (30, 60, 140), (deposito[0], deposito[1] + 50, deposito[2]))
    piezas = [
        P("radiador", caja((0, 0, 0), (18, 150, 130)) + panal + cilindro((0, 70, -60), Z, 9, 20) + cilindro((0, -70, 60), Z, 9, 20),
          (0, 40, 40), (-90, -40)),
        P("tapa", cilindro((0, 100, 30), Y, 13, 10) + cilindro((0, 108, 30), Y, 16, 4), (0, 104, 30), (-70, -50)),
        P("rejilla", prisma((90, 0, 0), X, redondeado(150, 170, 24), 6, lado=OSCURO, cara="#c3c9cb")
          + [polilinea([(93.5, y, -60), (93.5, y - 12, 60)], 2.2, "#7f878a") for y in range(-70, 75, 16)], (90, 40, -40), (70, -50)),
        P("carcasa_ventilador", cilindro((-70, 0, 0), X, 66, 24, ri=58, lado=LADO_MEDIO), (-70, 50, 30), (-80, -30)),
        P("ventilador", prisma((-115, 0, 0), X, aspas, 10, hueco=iso._circ2d(8, 16)), (-115, 0, 0), (-80, 40)),
        P("termostato", cilindro((160, 66, -210), Y, 17, 3, ri=7, lado="#b08d3c", cara="#d8b36a")
          + cilindro((160, 54, -210), Y, 7, 16, lado="#b08d3c", cara="#d8b36a") + resorte((160, 52, -210), Y, 10, 18, 4, 1.8)
          + cilindro((160, 76, -210), Y, 4, 10, lado=LADO_MEDIO), (160, 60, -210), (60, -30)),
        P("manguera", manguera(superior, 12), superior[8], (60, -40)),
        P("manguera_inferior", manguera(inferior, 12) + manguera(hacia_bomba, 12), inferior[8], (60, 40)),
        P("tubo_t", cilindro((110, -190, -60), X, 9, 30) + cilindro((110, -200, -60), Y, 7, 20), (110, -190, -60), (60, 50)),
        P("deposito", prisma(deposito, Y, redondeado(60, 40, 10), 90, lado="#d9dedf", cara="#eef1f1")
          + [polilinea([(deposito[0] - 30.5, deposito[1] + k, deposito[2] + 12), (deposito[0] - 30.5, deposito[1] + k, deposito[2] - 12)], 1.2, "#7f878a")
             for k in (-20, 20)], (deposito[0], deposito[1], deposito[2]), (70, 30)),
        P("tapa_deposito", cilindro((deposito[0], deposito[1] + 54, deposito[2]), Y, 14, 10, lado=LADO_MEDIO, cara="#f4f5f5"),
          (deposito[0], deposito[1] + 56, deposito[2]), (70, -20)),
        P("manguera_deposito", manguera(al_deposito, 6), al_deposito[8], (60, -20)),
        P("drenaje", perno((0, -110, 30), Y, 18, 7), (0, -110, 30), (-70, 30)),
        # Bomba de agua al final de la manguera de abajo: caracol con su tapa, el impulsor adentro y el eje que la mueve
        P("bomba_agua", cilindro((232, -200, -170), X, 26, 18, lado=LADO_MEDIO, cara="#eef0f0")
          + cilindro((244, -200, -170), X, 18, 4, lado=LADO_MEDIO, cara="#dfe3e4") + cilindro((214, -200, -170), X, 3.5, 34, lado=LADO_MEDIO)
          + cilindro((232, -176, -170), Y, 7, 22), (232, -200, -170), (60, 50)),
        P("abrazaderas", arandela(superior[2], Z, 14, 3) + arandela(inferior[2], Z, 14, 3) + arandela(hacia_bomba[-3], Z, 14, 3),
          inferior[2], (-60, 50)),
        P("empaques", oring((-30, 100, 30), Y, 12) + oring((-30, -110, 30), Y, 9), (-30, 100, 30), (-70, 30)),
        P(None, perno((140, 60, 0), (-1, 0, 0), 30, 6) + perno((140, -60, 0), (-1, 0, 0), 30, 6), (140, 60, 0), (70, 20), herraje="h_tornillo"),
    ]
    lineas = [linea((-150, 0, 0), (130, 0, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 9. Rueda
# ---------------------------------------------------------------------------
def _rueda(disco_derecha=False, x_tuerca=225):
    """Rueda. La delantera lleva el disco a la izquierda (-X). La trasera, como en la moto y en los planos: disco y sensor a
    la derecha (+X) y el arrastre a la izquierda; el eje entra por el lado de la cadena y la tuerca queda al otro lado."""
    xd, xr, xb, xh = (260, 225, 248, 110) if disco_derecha else (-345, -90, -333, -110)
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
        P("valvula", cilindro((10, 92, 30), Y, 6, 12, r2=4, cara=CAUCHO_CARA, lado=CAUCHO) + cilindro((10, 104, 30), Y, 3, 12, lado=LADO_MEDIO)
          + cilindro((10, 113, 30), Y, 3.6, 6, lado=OSCURO, cara="#59636a"), (10, 110, 30), (60, -60)),
        # Neumático (cámara) de las ruedas con cámara: un aro delgado de caucho que va dentro de la llanta, con su válvula
        P("neumatico", cilindro((95, 0, 0), X, 118, 26, ri=98, cara="#4a4f52", lado="#33383b", hueco_color="none")
          + cilindro((95, -104, 0), Y, 3, 14, lado=LADO_MEDIO), (95, 110, 0), (70, -60), orden=0),
        # Radios (rayos) de las ruedas de rayos: van cruzados de la manzana al rin, con su niple en el rin
        P("radios", [polilinea([(23, 26 * math.cos(a), 26 * math.sin(a)), (23, 104 * math.cos(a + 0.55), 104 * math.sin(a + 0.55))], 1.4, "#7f878a")
                     for a in [i * 2 * math.pi / 18 for i in range(18)]]
          + [polilinea([(23, 26 * math.cos(a), 26 * math.sin(a)), (23, 104 * math.cos(a - 0.55), 104 * math.sin(a - 0.55))], 1.4, "#9aa2a5")
             for a in [i * 2 * math.pi / 18 + 0.17 for i in range(18)]], (23, 60, 40), (70, 40), orden=2),
        P("eje", cilindro((-300, 0, 0), X, 7, 200) + prisma((-405, 0, 0), X, hexagono(11), 10, lado=LADO_MEDIO), (-380, 0, 0), (-60, -60)),
        P("buje", cilindro((-200, 0, 0), X, 13, 44, ri=8), (-200, 0, 0), (-50, 60)),
        P("retenedores", retenedor((-165, 0, 0), X, 25) + retenedor((165, 0, 0), X, 25), (-165, 0, 0), (-60, -65)),
        P("rodamientos", rodamiento((-140, 0, 0), X, 23, 10) + rodamiento((140, 0, 0), X, 23, 10), (-140, 0, 0), (-50, 70)),
        P("sensor_abs", cilindro((xr, 0, 0), X, 58, 3, ri=42) + puntos_en_cara((xr, 0, 0), X, 3, 50, 28, 2.6), (xr, -40, 40), (-70, 60)),
        # Sensor de velocidad (o ABS) con su cable: va frente al disco agujereado (rueda fónica)
        P("sensor_cable", caja((xr - 6, 78, 52), (16, 26, 16), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + manguera([(xr - 6, 92, 52), (xr - 6, 130, 60), (xr, 170, 90), (xr + 20, 200, 130)], 5, "#3c4447"),
          (xr - 6, 84, 52), (-55, -60), orden=2),
        # Kit de reparación de la maza (rodamientos, retenes y espaciador), dentro de su recuadro como en el plano
        P("kit", rodamiento((-150, -230, 160), X, 20, 10) + retenedor((-122, -230, 160), X, 21) + cilindro((-80, -230, 160), X, 9, 46, ri=5)
          + retenedor((-38, -230, 160), X, 21) + rodamiento((-10, -230, 160), X, 20, 10),
          (20, -200, 160), (60, 40), orden=3),
        # Disco de freno al lado izquierdo de la maza (solo aparece en las láminas que lo traen)
        P("disco", _disco_petalo((xd, 0, 0), 92, 5), (xd, 70, 40), (-60, -70), orden=0),
        P(None, perno((xb, 18, 18), X, 12, 5) + perno((xb, -18, -18), X, 12, 5), (xb, 18, 18), padre="disco", orden=1, herraje="h_tornillo"),
        P(None, perno((xh, 30, 30), X, 14, 5) + perno((xh, -30, -30), X, 14, 5), (xh, 30, 30), (-60, -45), herraje="h_tornillo"),
        P(None, arandela((x_tuerca - 30, 0, 0), X, 13, 3), (x_tuerca - 30, 0, 0), (60, -55), herraje="h_arandela"),
        P(None, tuerca((x_tuerca, 0, 0), X, 13), (x_tuerca, 0, 0), (60, 45), herraje="h_tuerca"),
    ]
    lineas = [linea((-430, 0, 0), (x_tuerca + 35, 0, 0))]
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
        # Dirección: dos juegos sobre la espiga. Abajo, sobre la tijera inferior: balinera y su taza (prensada en la columna);
        # arriba, bajo la tijera superior: taza y balinera. La columna del chasis va entre los dos (no se dibuja)
        P("rodamientos_direccion", rodamiento((-30, 278, -180), Y, 22, 9) + rodamiento((-30, 486, -180), Y, 20, 8),
          (-30, 486, -180), (-70, -30)),
        P("tazas", cilindro((-30, 296, -180), Y, 25, 5, ri=13) + cilindro((-30, 468, -180), Y, 23, 5, ri=12),
          (-30, 468, -180), (60, -40)),
        # Puente superior (tijera de arriba): aprieta la parte alta de las barras y la tuerca de la dirección
        P("tijera_superior", prisma((-30, 520, -180), Y, tijera, 16, lado=LADO_MEDIO, cara="#f4f5f5")
          + cilindro((-150, 520, -180), Y, 22, 17, ri=14, lado=LADO_MEDIO, cara="#f4f5f5")
          + cilindro((90, 520, -180), Y, 22, 17, ri=14, lado=LADO_MEDIO, cara="#f4f5f5")
          + cilindro((-30, 520, -180), Y, 13, 17.5, ri=8), (-110, 520, -180), (-70, -40)),
        # Bujes de deslizamiento de la barra (guía y del tubo) y el soporte de la farola en la barra
        P("bujes", cilindro((90, 172, 0), Y, 16, 6, ri=14, lado="#b98a52", cara="#dcb27c")
          + cilindro((90, 190, 0), Y, 16, 6, ri=14, lado="#b98a52", cara="#dcb27c"), (106, 181, 0), (70, 0)),
        P("soporte_farola", cilindro((90, 320, 0), Y, 20, 26, ri=15, lado=LADO_MEDIO, cara="#eef1f2")
          + caja((90, 320, 42), (14, 18, 50), colores=(LADO_MEDIO, "#eef1f2", LADO_CLARO))
          + cilindro((90, 320, 70), X, 8, 22, ri=3.5, cara=CAUCHO_CARA, lado=CAUCHO), (90, 320, 60), (70, -20)),
        P(None, perno((60, 420, -140), MENOS_Y, 30, 7) + perno((90, 420, -100), MENOS_Y, 30, 7), (75, 420, -120), (65, -30), herraje="h_tornillo"),
    ]
    lineas = [linea((90, -150, 0), (90, 390, 0)), linea((180, -60, 0), (180, 310, 0)), linea((-30, 230, -180), (-30, 550, -180))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 11. Basculante y amortiguadores
# ---------------------------------------------------------------------------
def _amortiguador(base, cima):
    """Amortiguador de resorte entre dos puntos (base abajo, cima arriba): ojo, cuerpo, vástago, resorte, ojo."""
    (x0, y0, z0), (x1, y1, z1) = base, cima
    eje = (x1 - x0, y1 - y0, z1 - z0)
    largo = math.sqrt(sum(c * c for c in eje))
    u = tuple(c / largo for c in eje)
    p = lambda t: (x0 + u[0] * t, y0 + u[1] * t, z0 + u[2] * t)
    return (cilindro(base, X, 11, 22, ri=5) + cilindro(p(largo * .22), u, 14, largo * .3, lado=OSCURO, cara=LADO_MEDIO)
            + cilindro(p(largo * .55), u, 7, largo * .45, lado="#f4f6f6") + resorte(p(largo * .5), u, 22, largo * .62, 9)
            + cilindro(p(largo * .86), u, 16, largo * .14, lado=OSCURO, cara=LADO_MEDIO) + cilindro(cima, X, 11, 22, ri=5))


def _templador(x, y, z_punta, lado=1, largo_ranura=60):
    """Templador de la cadena en la punta del brazo (eje del brazo = Z, hacia atrás = -Z), despiezado hacia atrás:
    taco en la ranura (con el agujero del eje), tornillo coaxial, platina de la punta y contratuerca afuera; marcas de
    alineación grabadas en la cara exterior del brazo junto a la ranura, con el índice en el taco."""
    gris = (LADO_MEDIO, "#eef1f2", LADO_CLARO)
    cara = x + lado * 10
    taco = caja((x, y, z_punta + 18), (16, 22, 22), colores=gris) + cilindro((x, y, z_punta + 18), X, 6.5, 17, cara=HUECO, grosor=1)
    platina = prisma((x, y, z_punta - 30), Z, redondeado(20, 26, 4), 5, lado=LADO_MEDIO, cara="#e3e6e7") + cilindro((x, y, z_punta - 27), Z, 3.5, 1, cara=HUECO, grosor=1)
    tornillo = perno((x, y, z_punta - 46), (0, 0, 1), 46, 6)
    contratuerca = prisma((x, y, z_punta - 52), Z, hexagono(9), 6, lado=LADO_MEDIO)
    marcas = [polilinea([(cara, y + 9, z_punta + 4 + k * 9), (cara, y + 16, z_punta + 4 + k * 9)], 1.4, "#5b6266") for k in range(5)]
    indice = [polilinea([(x + lado * 8.6, y + 11, z_punta + 18), (x + lado * 8.6, y + 17, z_punta + 18)], 2, ROJO)]
    return taco + tornillo + platina + contratuerca + marcas + indice


def _suspension_scooter(mono):
    """Scooter: el motor y la transmisión forman el brazo que sube y baja (conjunto oscilante). El brazo trasero, a la derecha,
    sostiene la otra punta del eje de la rueda. Los amortiguadores van del chasis a ese conjunto: uno a la izquierda (mono)
    o uno a cada lado. Sin templadores ni piezas de cadena."""
    y, zt = -140, -200
    gris = (LADO_MEDIO, "#eef1f2", LADO_CLARO)
    transmision = (prisma((-95, y + 10, -20), X, [(-190, 30), (-150, 60), (150, 50), (200, 10), (200, -40), (-170, -50)], 40, lado="#e6e0d2", cara="#f6f3eb")
                   + cilindro((-95, y + 10, zt), X, 30, 44, ri=12, lado="#e6e0d2", cara="#f6f3eb"))
    brazo = (prisma((95, y, -60), X, [(-150, 18), (150, 14), (160, -10), (-150, -18)], 22, lado=gris[0], cara=gris[1])
             + cilindro((95, y, zt), X, 22, 26, ri=10, lado=gris[0], cara=gris[1]) + cilindro((95, y, 90), X, 14, 26, ri=7, lado=gris[0], cara=gris[1]))
    if mono:
        amort = _amortiguador((-95, y + 40, zt + 30), (-95, 170, zt + 70))
    else:
        amort = _amortiguador((-95, y + 40, zt + 30), (-95, 170, zt + 70)) + _amortiguador((95, y + 22, zt + 30), (95, 170, zt + 70))
    piezas = [
        P("carcasa_transmision", transmision, (-95, y + 40, 60), (-70, -40), orden=0),
        P("amortiguador", amort, (-95, 40, zt + 50), (-80, -40), orden=1),
        P("basculante", brazo, (95, y + 14, -60), (60, 60), orden=1),
        P("bujes", cilindro((95, y, 90), X, 9, 30, cara=CAUCHO_CARA, lado=CAUCHO), (95, y, 90), (60, -40), orden=2),
        P(None, perno((-95, 170, zt + 70), X, 50, 8), (-95, 170, zt + 70), (-70, -40), herraje="h_tornillo"),
        P(None, tuerca((125, y, zt), X, 11), (125, y, zt), (60, 40), herraje="h_tuerca"),
    ]
    return piezas, [linea((-160, y + 10, zt), (160, y, zt))]


def _amortiguadores(perfil=None):
    """Basculante de dos brazos (pivote adelante, ranuras del eje atrás con sus templadores, travesaño) y la suspensión
    trasera según la moto: un monoamortiguador central sobre el travesaño o dos amortiguadores en las puntas de los brazos."""
    p = _perfil(perfil)
    mono = bool(p.get("m", 0))
    if p.get("s"):
        return _suspension_scooter(mono)
    y, zp, zt = -140, 200, -200                    # altura del basculante, pivote (adelante) y puntas (atrás)
    gris = (LADO_MEDIO, "#eef1f2", LADO_CLARO)
    brazos = []
    for x in (-95, 95):
        brazos += caja((x, y, (zp + zt) / 2 + 10), (18, 34, zp - zt - 40), colores=gris)                     # brazo (sección de caja)
        brazos += prisma((x, y, zt + 4), X, estadio(60, 34), 18, lado=LADO_MEDIO, cara="#eef1f2")             # punta con la ranura
        brazos += prisma((x + (10 if x > 0 else -10), y, zt + 4), X, estadio(44, 10), 1.2, lado=OSCURO, cara=HUECO, grosor=1.2)
    brazos += caja((0, y + 4, 70), (172, 30, 34), colores=gris)                                              # travesaño
    brazos += cilindro((0, y, zp), X, 18, 210, lado=LADO_MEDIO, cara="#eef1f2")                              # tubo del pivote
    if mono:
        brazos += prisma((0, y + 30, 70), X, [(-18, -12), (18, -12), (10, 20), (-10, 20)], 26, lado=LADO_MEDIO, cara="#eef1f2")
        amort = _amortiguador((0, y + 52, 70), (0, 150, 175))
        ancla_amort = (0, 60, 130)
    else:
        amort = _amortiguador((-95, y + 28, zt + 30), (-95, 160, zt + 60)) + _amortiguador((95, y + 28, zt + 30), (95, 160, zt + 60))
        ancla_amort = (-95, 40, zt + 45)
    templador = [f for x in (-95, 95) for f in _templador(x, y, zt - 6, 1 if x > 0 else -1)]
    piezas = [
        P("amortiguador", amort, ancla_amort, (-80, -40), orden=0),
        P("basculante", brazos, (95, y + 17, -40), (60, 60), orden=1),
        P("bujes", cilindro((-125, y, zp), X, 14, 18, cara=CAUCHO_CARA, lado=CAUCHO) + cilindro((125, y, zp), X, 14, 18, cara=CAUCHO_CARA, lado=CAUCHO),
          (125, y, zp), (60, -40), orden=2),
        P("retenedor", retenedor((-150, y, zp), X, 18, 6) + retenedor((150, y, zp), X, 18, 6), (150, y, zp), (60, 40), orden=2),
        P("tapones", cilindro((-175, y, zp), X, 19, 6, lado=OSCURO, cara=LADO_MEDIO) + cilindro((175, y, zp), X, 19, 6, lado=OSCURO, cara=LADO_MEDIO),
          (-175, y, zp), (-60, -40), orden=3),
        P("eje_basculante", cilindro((-30, y, zp), X, 7, 420) + prisma((-245, y, zp), X, hexagono(12), 10, lado=LADO_MEDIO),
          (-230, y, zp), (-60, -50), orden=3),
        P("tensores", templador, (95, y, zt - 40), (60, 40), orden=2),
        P("deslizador", prisma((-108, y + 22, zp - 70), X, [(-60, -6), (60, -6), (66, 6), (-66, 6)], 10, lado=OSCURO, cara="#4a5357"),
          (-108, y + 26, zp - 70), (-60, -50), orden=2),
        P("protector_cadena", prisma((-120, y + 44, 0), X, [(-150, 0), (130, 0), (120, 18), (-140, 18)], 4, lado="#3c4448", cara="#59636a"),
          (-122, y + 54, 0), (-70, -30), orden=2),
        # Cadena: corre por fuera del brazo izquierdo, del piñón de salida (adelante) a la corona (atrás)
        P("cadena", cadena_eslabones([(-140, y + 30, zp + 40), (-140, y + 20, zt - 10), (-140, y - 40, zt - 30), (-140, y - 50, zp + 10), (-140, y + 30, zp + 40)],
                              6), (-140, y + 20, zt + 60), (-70, 40), orden=3),
        # Barra de torque del freno de tambor: une el plato del freno con el brazo para que no gire al frenar
        P("barra_torque", caja((112, y - 30, -60), (8, 10, 240), colores=(LADO_MEDIO, "#eef1f2", LADO_CLARO))
          + cilindro((112, y - 30, 58), X, 7, 10, ri=3) + cilindro((112, y - 30, -178), X, 7, 10, ri=3), (112, y - 30, -60), (60, 50), orden=3),
        P(None, perno((0, 160, 205), X, 60, 8), (0, 160, 205), (-70, -40), herraje="h_tornillo"),
        P(None, tuerca((235, y, zp), X, 11), (235, y, zp), (60, 40), herraje="h_tuerca"),
    ]
    lineas = [linea((-260, y, zp), (260, y, zp))]
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
        P("llave", prisma((280, 0, 60), Z, redondeado(34, 40, 14), 8, lado=OSCURO, cara="#4a5357")
          + prisma((280, -38, 60), Z, [(-5, 18), (5, 18), (5, -14), (2, -18), (-5, -18), (-5, -6), (-2, -4), (-5, 0)], 3,
                   lado=LADO_MEDIO, cara="#dfe3e4"), (280, -20, 60), (60, 30)),
        P("sensor_pata", caja((-200, -110, 140), (26, 14, 18), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + cilindro((-200, -110, 155), Z, 3.5, 12, lado=LADO_MEDIO) + manguera([(-213, -110, 140), (-240, -120, 150), (-260, -110, 170)], 3, "#5d666a"),
          (-200, -110, 140), (-60, 40)),
        P("modulo", caja((80, -140, 200), (70, 20, 50), colores=(OSCURO, LADO_MEDIO, OSCURO))
          # Aletas de disipación del regulador / módulo
          + [f for i in range(-3, 4) for f in caja((80 + i * 9, -126, 200), (3, 8, 48), colores=(OSCURO, LADO_CLARO, LADO_MEDIO), grosor=1)],
          (80, -140, 200), (60, 40)),
        # Capuchón de la bujía con su cable (algunas marcas lo listan con la parte eléctrica)
        P("capuchon", cilindro((140, 120, 120), Y, 10, 30, r2=8, cara=CAUCHO_CARA, lado=CAUCHO)
          + cilindro((140, 138, 129), Z, 7.5, 22, r2=6, cara=CAUCHO_CARA, lado=CAUCHO)
          + manguera([(140, 138, 140), (150, 150, 175), (175, 150, 205)], 4, "#5d666a"), (140, 130, 120), (60, -50)),
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
        P("bujia", bujia_real((-60, 60, 120), Y, 1.6), (-60, 150, 120), (-60, -60), orden=2),
        P("capuchon", cilindro((-60, 206, 120), Y, 12, 34, r2=10, cara=CAUCHO_CARA, lado=CAUCHO)
          + cilindro((-60, 226, 131), Z, 9, 26, r2=7, cara=CAUCHO_CARA, lado=CAUCHO), (-60, 225, 120), (-60, -50), orden=3),
        # Antivibrante (caucho) del capuchón: el sello que entra sobre la bujía, separado en el despiece
        P("antivibrante", cilindro((-60, 182, 120), Y, 15, 12, ri=8, cara="#7b8385", lado=CAUCHO), (-60, 182, 135), (60, -10), orden=3),
        P("cables", manguera([(-60, 230, 120)] + cable, 6, "#5d666a"), cable[6], (-30, 60), orden=2),
        P("bobina", caja((150, 30, -20), (60, 40, 34), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + cilindro((150, 58, -20), Y, 9, 16, cara=CAUCHO_CARA, lado=CAUCHO)
          + caja((112, 30, -20), (16, 4, 20), colores=(LADO_MEDIO, "#dfe3e4", LADO_MEDIO))
          + caja((188, 30, -20), (16, 4, 20), colores=(LADO_MEDIO, "#dfe3e4", LADO_MEDIO)), (150, 50, -20), (60, -60), orden=2),
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
    """Caja de cambios: eje principal (arriba) y eje de salida (abajo) con sus pares de piñones, que engranan: la distancia
    entre ejes es la suma de los radios de cada par. Las horquillas salen del tambor selector (detrás de los ejes) y
    abrazan la ranura del piñón que mueven. Cada eje apoya en dos rodamientos; el de salida lleva retén y el piñón de cadena."""
    radios_p, radios_s = [24, 30, 36, 42, 48], [66, 60, 54, 48, 42]          # cada par suma 90
    yp, ys = 45, -45                                                           # ejes a 90 de distancia
    xs = [-110 + i * 58 for i in range(5)]

    def engrane(x, y, r):
        return prisma((x, y, 0), X, engranaje(r, max(12, int(r * .62))), 13, hueco=iso._circ2d(9), cara="#f6f6f4", lado=LADO_MEDIO)
    zt = 120                                                                   # tambor selector, detrás de los ejes
    tambor = cilindro((20, 0, zt), X, 17, 260) + [f for x in (xs[1], xs[2], xs[3]) for f in cilindro((x, 0, zt), X, 18, 4, cara=HUECO)]

    def horquilla(x, y):
        """Brazo del tambor al eje (en el plano y-z), con la pata en U que abraza la ranura del piñón y el pin en el tambor."""
        u0, v0, u1, v1 = 0.0, y, -zt + 17, 0.0                                  # (u, v) = (-z, y) con eje X
        largo = math.hypot(u1 - u0, v1 - v0)
        nu, nv = -(v1 - v0) / largo * 5, (u1 - u0) / largo * 5
        brazo = [(u0 + nu, v0 + nv), (u1 + nu, v1 + nv), (u1 - nu, v1 - nv), (u0 - nu, v0 - nv)]
        pata = [(math.cos(t) * 30, y + math.sin(t) * 30) for t in [math.pi * .5 + i * math.pi / 10 for i in range(11)]] + \
               [(math.cos(t) * 22, y + math.sin(t) * 22) for t in [math.pi * 1.5 - i * math.pi / 10 for i in range(11)]]
        return (prisma((x, 0, 0), X, brazo, 6, lado=LADO_MEDIO, cara="#f1f1ee") + prisma((x, 0, 0), X, pata, 6, lado=LADO_MEDIO, cara="#f1f1ee")
                + cilindro((x, v1 * .2, zt - 16), Z, 4, 10))
    cadena = _yz(ys, 0, 44, math.pi, 2 * math.pi, 12, x=330)
    cadena = [(330, cadena[-1][1], -230)] + cadena[::-1] + [(330, cadena[0][1], -230)]
    piezas = [
        P("eje_principal", cilindro((40, yp, 0), X, 8, 430), (-170, yp, 0), (-60, -55), orden=0),
        P("engranajes", [f for i, r in enumerate(radios_p) for f in engrane(xs[i], yp, r)], (xs[2], yp + radios_p[2], 0), (-20, -95), orden=1),
        P("eje_salida", cilindro((50, ys, 0), X, 9, 470), (-180, ys, 0), (-65, 55), orden=0),
        P("engranajes_salida", [f for i, r in enumerate(radios_s) for f in engrane(xs[i], ys, r)], (xs[3], ys - radios_s[3], 0), (40, 95), orden=1),
        P("horquillas", horquilla(xs[2], yp) + horquilla(xs[1], ys) + horquilla(xs[3], ys), (xs[2], yp / 2, zt / 2), (-60, -50), orden=2),
        P("tambor_selector", tambor, (150, 0, zt), (60, -50), orden=1),
        P("rodamientos", rodamiento((-200, yp, 0), X, 17, 10) + rodamiento((-215, ys, 0), X, 19, 10)
          + rodamiento((250, yp, 0), X, 17, 10) + rodamiento((265, ys, 0), X, 19, 10), (-200, yp, 0), (-60, 45), orden=2),
        P("reten", retenedor((285, ys, 0), X, 17), (285, ys, 0), (60, -55), orden=2),
        P("pinon", prisma((330, ys, 0), X, engranaje(38, 14, 7), 9, hueco=iso._circ2d(10), cara="#f6f6f4", lado=LADO_MEDIO),
          (330, ys + 38, 0), (70, -40), orden=3),
        P("cadena", cadena_eslabones(cadena, 8), cadena[-1], (60, 40), orden=2),
    ]
    lineas = [linea((-260, yp, 0), (300, yp, 0)), linea((-260, ys, 0), (380, ys, 0)), linea((-140, 0, zt), (180, 0, zt))]
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


def _tapon_varilla(c):
    """Tapón de llenado con varilla de nivel (eje Y hacia afuera): agarradera plana, rosca y varilla larga con sus dos marcas."""
    x, y, z = c
    agarre =[(-15, -4), (-13, -6), (13, -6), (15, -4), (15, 4), (13, 6), (-13, 6), (-15, 4)]
    formas = cilindro((x, y - 34, z), Y, 2.2, 60, lado=LADO_MEDIO)                     # varilla
    formas += cilindro((x, y - 52, z), Y, 2.8, 1.5, lado=OSCURO) + cilindro((x, y - 60, z), Y, 2.8, 1.5, lado=OSCURO)  # marcas
    formas += cilindro((x, y - 2, z), Y, 8, 10, lado=LADO_MEDIO)                       # rosca
    for k in range(4):
        formas += cilindro((x, y - 6 + k * 3, z), Y, 8.6, 0.8, lado=OSCURO)
    formas += cilindro((x, y + 4, z), Y, 11, 2.5, lado=OSCURO)                         # asiento del o-ring
    formas += prisma((x, y + 13, z), Y, agarre, 16, lado=OSCURO, cara=LADO_MEDIO)      # agarradera
    return formas


def _carcasa():
    piezas = [
        P("carcasa_izq", _media_carcasa(-170), (-170, 128, 30), (-70, -70), orden=0),
        P("empaques", prisma((-92, 0, 0), X, _CARTER, 2, hueco=[(u * .93, v * .93) for u, v in _CARTER], lado="#8d9391", cara="#a9aeac")
          + prisma((84, 10, 20), X, _TAPA_CLUTCH, 2, hueco=[(u * .9, v * .9) for u, v in _TAPA_CLUTCH], lado="#8d9391", cara="#a9aeac"),
          (-92, 110, -40), (-30, -85), orden=1),
        P("carcasa_der", _media_carcasa(0), (0, 128, -30), (40, -95), orden=2),
        P("rodamientos", rodamiento((-118, 8, 0), X, 30, 14) + rodamiento((-122, -40, -92), X, 18, 10) + rodamiento((-122, -84, -62), X, 14, 9), (-118, 8, 0), (-70, 50), orden=1),
        P("reten", retenedor((-230, 8, 0), X, 24), (-230, 8, 0), (-60, 40), orden=1),
        P("swiche", cilindro((-206, -80, 60), X, 6, 10, lado=LADO_MEDIO) + iso.roscas((-206, -80, 60), X, 6, 9, 2.5)
          + prisma((-216, -80, 60), X, hexagono(9), 7, lado=LADO_MEDIO, cara="#e6e9ea")
          + cilindro((-224, -80, 60), X, 6, 8, cara=CAUCHO_CARA, lado=CAUCHO) + cilindro((-232, -80, 60), X, 2, 8, lado="#b08d3c"),
          (-225, -80, 60), (-60, 55), orden=1),
        P("tapa_clutch", _tapa_clutch((110, 10, 20)), (110, 96, 0), (50, -80), orden=3),
        P("visor", cilindro((126, -52, 70), X, 12, 4, cara="#cfe6f1", lado="#9fbfcc"), (126, -52, 70), (70, 30), orden=4),
        P("tapon_llenado", _tapon_varilla((110, 150, -20)), (110, 176, -20), (60, -50), orden=4),
        P("filtro", cilindro((215, 30, -20), X, 26, 40, ri=10, cara="#f9f4e4", lado="#e6dcc0")
          + [polilinea([(196, 30 + math.sin(t) * 26, -20 + math.cos(t) * 26), (234, 30 + math.sin(t) * 26, -20 + math.cos(t) * 26)], 1)
             for t in [i * 0.5 for i in range(13)]], (215, 56, -20), (60, -55), orden=5),
        P("tapa_filtro", cilindro((270, 30, -20), X, 32, 10) + perno((285, 55, -40), X, 16, 5), (270, 30, -20), (60, 40), orden=6),
        P("bomba", cilindro((66, -60, 70), X, 24, 14, lado=LADO_MEDIO, cara="#eef0f0")
          + prisma((74, -60, 70), X, _rotor_interior(14, 4), 2, lado=LADO_MEDIO, cara="#cfd4d6")
          + cilindro((48, -60, 70), X, 3.5, 36, lado=LADO_MEDIO)
          + prisma((40, -60, 70), X, engranaje(16, 16), 5, hueco=iso._circ2d(4), cara="#f6f6f4", lado=LADO_MEDIO), (60, -60, 70), (50, 70), orden=3),
        P("malla", cilindro((0, -170, 20), Y, 14, 40, ri=10, cara="#e6e9ea", lado="#d4d9da")
          + [polilinea([(14.3 * math.cos(a), -190, 20 + 14.3 * math.sin(a)), (14.3 * math.cos(a), -150, 20 + 14.3 * math.sin(a))], 0.8, "#8f9799")
             for a in [i * math.pi / 9 for i in range(-1, 11)]]
          + [polilinea([(14.3 * math.cos(a), yy, 20 + 14.3 * math.sin(a)) for a in [i * math.pi / 12 for i in range(-2, 15)]], 0.8, "#8f9799")
             for yy in (-182, -174, -166, -158)],
          (0, -170, 20), (-70, 10), orden=1),
        P("tapon", tapon_perno((0, -228, 20), Y, 18, 12),
          (0, -225, 20), (-70, 20), orden=1),
    ]
    lineas = [("carcasa_der", linea((-260, 8, 0), (300, 8, 0))), ("malla", linea((0, -124, 20), (0, -255, 20))),
              ("filtro", linea((150, 30, -20), (300, 30, -20)))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 18. Rueda trasera con arrastre (corona, porta sprocket, cauchos, disco, tensores)
# ---------------------------------------------------------------------------
def _arrastre_trasero():
    """Corona, porta corona con sus cauchos y cadena, al lado izquierdo de la rueda trasera (-X), como en la moto."""
    cadena = _yz(0, 0, 106, 0.2, math.pi - 0.2, 14, x=-345)
    cadena = [(-345, cadena[0][1], 330)] + cadena + [(-345, cadena[-1][1], 330)]
    return [
        P("cauchos", [f for k in range(4) for f in caja((-90, math.sin(k * 1.57 + .8) * 46, math.cos(k * 1.57 + .8) * 46), (16, 20, 20),
                                                         colores=(CAUCHO, CAUCHO_CARA, CAUCHO))], (-90, -40, 40), (-40, 70), orden=2),
        P("porta_sprocket", cilindro((-250, 0, 0), X, 70, 26, ri=18, cara=LADO_CLARO, lado=LADO_MEDIO), (-250, 55, -40), (-40, -80), orden=1),
        P("corona", prisma((-290, 0, 0), X, engranaje(104, 42, 9), 6, hueco=iso._circ2d(24), cara="#f6f6f4", lado=LADO_MEDIO)
          + puntos_en_cara((-290, 0, 0), X, 6, 48, 4, 6), (-290, 90, -40), (-60, -60), orden=0),
        P("cadena", cadena_eslabones([(-290, y, z) for _, y, z in cadena], 8), (-290, cadena[-1][1], 330), (-50, 40), orden=0),
    ]


def _rueda_trasera():
    piezas, _ = _rueda(disco_derecha=True, x_tuerca=330)
    piezas += [
        P("tensores", _templador(-430, 0, -18, -1) + _templador(360, 0, -18, 1), (-430, 0, -50), (-50, 60), orden=0),
    ] + _arrastre_trasero()
    lineas = [linea((-480, 0, 0), (380, 0, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 19. Rueda trasera con freno de tambor y arrastre
# ---------------------------------------------------------------------------
def _rueda_tambor(perfil=None):
    """Rueda trasera con freno de tambor. En moto de cadena, con su kit de arrastre a la izquierda; en scooter, la rueda va
    montada directo en el eje de salida de la transmisión final (sin corona, porta corona, cadena ni templadores)."""
    scooter = bool(_perfil(perfil).get("s"))
    def zapata(lado, x, r=64, ri=50):
        arco = [(math.cos(t) * r, math.sin(t) * r * lado) for t in [i * 0.15 + 0.25 for i in range(19)]]
        return (prisma((x, 0, 0), X, arco + [(math.cos(t) * ri, math.sin(t) * ri * lado) for t in [i * 0.15 + 0.25 for i in range(18, -1, -1)]],
                       12, lado=LADO_MEDIO, cara="#f4f1e8")
                + prisma((x + 7, 0, 0), X, arco + [(math.cos(t) * (r - 6), math.sin(t) * (r - 6) * lado)
                                                   for t in [i * 0.15 + 0.25 for i in range(18, -1, -1)]], 2, lado=OSCURO, cara=FRICCION))
    piezas = [q for q in _rueda(disco_derecha=True, x_tuerca=440)[0] if q.puesto not in ("sensor_abs", "sensor_cable", "disco") and q.padre != "disco"]
    piezas += [
        # Freno de tambor al lado derecho (como en la moto): campana en la maza, bandas, leva, plato y palanca
        P("campana", cilindro((110, 0, 0), X, 80, 30, ri=70, cara="#f3f4f4", lado=LADO_MEDIO), (110, 72, 40), (50, -80), orden=2),
        P("bandas", zapata(1, 230) + zapata(-1, 230), (230, 0, 62), (40, -80), orden=3),
        P("resortes", resorte((236, 0, 48), Y, 5, 34, 6) + resorte((236, 0, -48), Y, 5, 34, 6), (236, 20, 48), (40, -70), orden=4),
        P("leva", cilindro((265, 0, 64), X, 9, 50), (265, 0, 64), (60, -40), orden=4),
        P("plato", cilindro((310, 0, 0), X, 76, 8, ri=12, cara="#f6f6f4", lado=LADO_MEDIO), (310, -55, -50), (50, 70), orden=5),
        P("palanca", prisma((335, 22, 64), X, [(-8, -9), (8, -9), (9, 80), (-9, 80)], 8, lado=OSCURO, cara=LADO_MEDIO),
          (335, 95, 64), (50, -50), orden=6),
        P("indicador", prisma((343, 0, 64), X, [(0, -14), (16, -3), (16, 3), (0, 14)], 3, lado="#c9a227", cara="#f0cd7c"),
          (343, -12, 70), (60, 30), orden=6),
        P("tensores", _templador(-430, 0, -18, -1) + _templador(470, 0, -18, 1), (-430, 0, -50), (-50, 60), orden=0),
    ] + _arrastre_trasero()
    if scooter:
        piezas = [q for q in piezas if q.puesto not in ("tensores", "corona", "porta_sprocket", "cadena", "cauchos", "eje")]
        # El eje de salida de la transmisión final entra por la izquierda y la rueda se aprieta con su tuerca
        estrias = [polilinea([(x, 11 * math.sin(t), 11 * math.cos(t)) for x in (-150, -110)], 1.1) for t in [i * math.pi / 6 for i in range(12)]]
        piezas.append(P("eje", cilindro((-200, 0, 0), X, 11, 200, lado=LADO_MEDIO, cara="#eef0f0") + estrias, (-260, 0, 0), (-60, -60), orden=0))
    return piezas, [linea((-550, 0, 0), (480, 0, 0))]


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
        P("guia_manguera", grapa_manguera(tubo[8])
          + grapa_manguera(tubo[20]), tubo[20], (60, -30), orden=3),
        # Soporte del depósito (en los frenos traseros el tanque va aparte, atornillado al chasis)
        P("soporte_deposito", prisma((-70, 40, -60), Z, [(-14, 40), (14, 40), (18, -30), (6, -60), (-10, -60), (-18, -30)], 6,
                                     hueco=iso._circ2d(5, 12), lado=LADO_MEDIO), (-70, 20, -60), (-70, -20), orden=1),
        # Pedal del freno trasero con su caucho, el resorte de retorno y el eje
        P("pedal", prisma((-240, -470, 140), Z, pedal, 12, hueco=iso._circ2d(9, 20), lado=LADO_MEDIO, cara="#f1f3f4")
          + cilindro((-240 + 172, -470 - 13, 140 + 14), Z, 11, 26, cara=CAUCHO_CARA, lado=CAUCHO)
          + resorte((-240 + 40, -470 + 30, 150), Y, 6, 46, 7) + cilindro((-240, -470, 120), Z, 8, 46), (-180, -480, 146), (-60, 50), orden=1),
        # Frenado combinado (CBS): el pedal trasero jala este cable, que también acciona la bomba delantera desde abajo
        P("cable_cbs", manguera(curva((-200, -440, 140), (-150, -200, 80), (-20, -30, -18)), 4, "#4a5357")
          + cilindro((-20, -24, -18), Y, 4, 14, lado=LADO_MEDIO), (-150, -200, 80), (-70, 40), orden=2),
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
    ("h_arandela", "Arandelas y platinas", ["ARANDELA", "ARAND", "WASHER", "PLATINA", "PLACA", "PLATE"]),
    ("h_tornillo", "Tornillos", ["TORNILLO", "TORN", "PERNO", "ESPARRAGO", "REMACHE", "CERROJO", "BOLT", "SCREW", "STUD", "RIVET"]),
    ("h_tuerca", "Tuercas", ["CONTRATUERCA", "TUERCA", "NUT"]),
    ("h_seguro", "Seguros", ["ANILLO", "PIN SEGURO", "PIN DE SEGURIDAD", "PIN SEGURIDAD", "SEGURO", "CIRCLIP", "SNAP"]),
    ("h_pin", "Pines", ["PIN", "PASADOR", "CHAVETA", "GUIA DE CENTRADO", "ESPIGA", "DOWEL", "COTTER", "KEY"]),
    ("h_empaque", "Empaques", ["EMPAQUETADURA", "EMPAQUE", "O-RING", "ORING", "JUNTA", "SELLO", "RETENEDOR", "RETEN", "GASKET", "SEAL"]),
    ("h_abrazadera", "Abrazaderas", ["ABRAZADERA", "GRAPA", "SUJETADOR", "BANDA", "CORREA", "CLAMP", "CLIP", "BAND"]),
    ("h_buje", "Bujes", ["BUJE", "CASQUILLO", "ESPACIADOR", "SEPARADOR", "DISTANCIADOR", "COLLAR", "SPACER", "BUSH"]),
    ("h_rodamiento", "Rodamientos", ["RODAMIENTO", "BALINERA", "COJINETE", "RODILLO", "BEARING"]),
    ("h_caucho", "Cauchos", ["CAUCHO", "ANTIVIBRANTE", "AMORTIGUADOR", "DAMPER", "GROMMET", "CUSHION", "RUBBER", "STOPPER", "BUMP", "ABSORBER"]),
    ("h_resorte", "Resortes", ["RESORTE", "SPRING"]),
    ("h_tapa", "Tapas y tapones", ["TAPA", "TAPON", "CUBIERTA", "CARCAZA", "CAP", "COVER", "PLUG", "KNOB"]),
    ("h_manguera", "Mangueras y tubos", ["MANGUERA", "TUBO", "CONDUCTO", "DUCTO", "MULTIPLE", "CONECTOR", "BOQUILLA",
                                         "INYECTOR", "HOSE", "PIPE", "TUBE", "JOINT"]),
    ("h_cable", "Cables", ["CABLE", "ARNES", "LEAD", "WIRE"]),
    ("h_electrico", "Eléctricos", ["SWICHE", "SWITCH", "SENSOR", "INTERRUPTOR", "PITO", "HORN", "BOBINA", "RELE", "RELAY",
                                   "DIODO", "DIODE", "FLASHER", "UNIDAD", "COIL", "ECU", "CONTROL UNIT", "BUZZER", "ARRANQUE", "SW"]),
    ("h_soporte", "Soportes", ["SOPORTE", "BRACKET", "BRKT", "STAY", "HOLDER", "GUIA", "GUIDE", "SOSTEN"]),
    ("h_etiqueta", "Calcomanías", ["CALCOMANIA", "ETIQUETA", "EMBLEMA", "LABEL", "EMBLEM", "STICKER", "GRAPHIC"]),
    ("h_eje", "Ejes", ["EJE", "VARILLA", "SHAFT", "ROD", "AXLE", "BALANCEADOR", "BALANCER"]),
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
ACOMPANANTES = {"sensor_cable": ("sensor_abs",), "tijera": ("eje_direccion",)}
# Dónde va un subconjunto al elegirlo (el kit de la maza: en los rodamientos, los retenes y el buje)
DESTINO_SUBCONJUNTO = {"kit": ("rodamientos", "retenedores", "buje")}

# Inferencia mecánica: dónde va normalmente cada tipo de pieza pequeña en cada sistema, cuando el catálogo no lo dice
# (p. ej. en las válvulas, la platina y las arandelas van en los ejes de los balancines, no en la válvula).
INFERENCIA = {
    "valvulas": {"h_arandela": "eje_balancin", "h_tornillo": "eje_balancin", "h_pin": "eje_balancin", "h_seguro": "cunas",
                 "h_resorte": "resortes", "h_empaque": "sello", "h_tuerca": "tornillo_calibracion"},
    "culata": {"h_tornillo": "culata", "h_arandela": "culata", "h_tuerca": "esparragos", "h_empaque": "empaque_culata",
               "h_pin": "guias", "h_seguro": "culata"},
    "freno_disco": {"h_tornillo": "caliper", "h_arandela": "caliper", "h_pin": "pasador", "h_seguro": "pasador",
                    "h_tuerca": "caliper", "h_buje": "caliper"},
    "bomba_freno": {"h_tornillo": "abrazadera", "h_arandela": "banjo", "h_seguro": "manigueta", "h_tuerca": "manigueta",
                    "h_buje": "manigueta", "h_pin": "manigueta"},
    "freno_completo": {"h_tornillo": "caliper", "h_arandela": "banjo", "h_seguro": "pedal", "h_tuerca": "pedal",
                       "h_buje": "pedal", "h_pin": "pedal"},
    "freno_trasero": {"h_tornillo": "bomba", "h_arandela": "banjo", "h_seguro": "varilla", "h_tuerca": "varilla",
                      "h_buje": "pedal", "h_pin": "varilla"},
    "bombas_abs": {"h_tornillo": "abrazadera", "h_arandela": "banjo", "h_tuerca": "manigueta", "h_seguro": "manigueta",
                   "h_buje": "manigueta", "h_pin": "manigueta"},
    "rueda": {"h_tornillo": "disco", "h_arandela": "eje", "h_tuerca": "eje", "h_seguro": "rodamientos", "h_buje": "buje"},
    "rueda_trasera": {"h_tornillo": "porta_sprocket", "h_arandela": "eje", "h_tuerca": "corona", "h_seguro": "rodamientos",
                      "h_buje": "buje"},
    "rueda_tambor": {"h_tornillo": "porta_sprocket", "h_arandela": "eje", "h_tuerca": "corona", "h_seguro": "rodamientos",
                     "h_buje": "buje", "h_pin": "palanca"},
    "suspension_delantera": {"h_tornillo": "tijera", "h_arandela": "tapon", "h_seguro": "retenedor", "h_tuerca": "eje_direccion",
                             "h_buje": "botella", "h_pin": "tijera", "h_caucho": "tijera", "h_soporte": "tijera"},
    "amortiguadores": {"h_tornillo": "amortiguador", "h_tuerca": "amortiguador", "h_arandela": "amortiguador",
                       "h_buje": "bujes", "h_pin": "basculante"},
    "transmision": {"h_arandela": "engranajes", "h_seguro": "engranajes", "h_buje": "eje_salida", "h_tornillo": "pinon",
                    "h_tuerca": "pinon"},
    "carcasa": {"h_tornillo": "carcasa_der", "h_pin": "carcasa_der", "h_arandela": "carcasa_der", "h_tuerca": "carcasa_der",
                "h_seguro": "rodamientos"},
    "aceite": {"h_tornillo": "bomba", "h_arandela": "tapon", "h_pin": "bomba"},
    "admision": {"h_tornillo": "caja", "h_arandela": "caja", "h_abrazadera": "ducto", "h_caucho": "caja"},
    "radiador": {"h_tornillo": "radiador", "h_arandela": "radiador", "h_caucho": "radiador", "h_buje": "radiador"},
    "electrico": {"h_tornillo": "bateria", "h_tuerca": "bateria", "h_arandela": "bateria", "h_caucho": "bateria"},
    "encendido": {"h_tornillo": "estator", "h_arandela": "estator", "h_tuerca": "regulador", "h_buje": "cdi", "h_caucho": "cdi"},
    "cvt": {"h_arandela": "polea_fija", "h_tornillo": "campana", "h_seguro": "clutch"},
    "freno_tambor": {"h_tuerca": "palanca", "h_tornillo": "palanca", "h_arandela": "leva", "h_seguro": "leva"},
}

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
    tipo = tipo_por_primera_palabra(descripcion)
    if tipo:
        return _HERRAJE_DE_TIPO[tipo]
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


# ---------------------------------------------------------------------------
# 21. Caja secundaria de las automáticas (transmisión final, la que lleva su propio aceite)
# ---------------------------------------------------------------------------
# Reductor de dos etapas (sin marchas). Vista lateral: y arriba, z hacia adelante; los ejes van a lo largo de X.
#   1.ª etapa: piñón primario (16 d., en el eje que sale del clutch) → engranaje grande (56 d.) del eje intermedio
#   2.ª etapa: piñón del eje intermedio (12 d., hecho en el mismo eje) → engranaje (35 d.) del eje de salida (rueda)
# Las distancias entre ejes salen de los radios, para que los dientes engranen.
_M = 2.5                                              # módulo del dibujo: radio = dientes × módulo / 2
_R16, _R56, _R12, _R35 = 16 * _M / 2, 56 * _M / 2, 12 * _M / 2, 35 * _M / 2
_YI = 20                                              # el intermedio un poco más alto; el primario de nuevo más abajo
_ZI = math.sqrt((_R12 + _R35) ** 2 - _YI ** 2)
_YP = _YI - 15
_ZP = _ZI + math.sqrt((_R16 + _R56) ** 2 - (_YP - _YI) ** 2)
_EJES_CAJA = {"primario": (_YP, _ZP), "intermedio": (_YI, _ZI), "salida": (0, 0)}
# Tapa de la caja: contorno que abraza los tres ejes (u, v) = (-z, y) con eje X
_CAJA_PERFIL = [(30, 60), (-60, 66), (-140, 62), (-200, 50), (-228, 14), (-210, -26), (-140, -40), (-40, -56), (40, -60),
                (78, -30), (80, 20), (64, 52)]


def _caja_secundaria():
    al_cara, al_lado = "#f4f2ec", "#dcd7cb"
    (yp, zp), (yi, zi), (ys, zs) = _EJES_CAJA["primario"], _EJES_CAJA["intermedio"], _EJES_CAJA["salida"]

    def rueda(x, y, z, r, dientes, largo=10, hueco=8):
        return prisma((x, y, z), X, engranaje(r, dientes, 3.2), largo, hueco=iso._circ2d(hueco), cara="#f6f6f4", lado=LADO_MEDIO)
    estrias = [polilinea([(x, ys + 11 * math.sin(t), zs + 11 * math.cos(t)) for x in (-190, -150)], 1.1)
               for t in [i * math.pi / 6 for i in range(12)]]
    # Carcasa (lado del motor) con los alojamientos de los rodamientos, tornillos del borde y los tapones del aceite
    carcasa = prisma((-90, 0, 0), X, _CAJA_PERFIL, 26, lado=al_lado, cara=al_cara)
    for (u, v) in _CAJA_PERFIL[::2]:
        carcasa += cilindro((-76, v * .88, -u * .88), X, 5, 3, ri=2, lado=LADO_MEDIO, cara="#e9e4d8", grosor=1.2)
    piezas = [
        P("carcasa_caja", carcasa, (-90, 70, 60), (-70, -70), orden=0),
        P("empaque", prisma((-72, 0, 0), X, _CAJA_PERFIL, 2, hueco=[(u * .93, v * .93) for u, v in _CAJA_PERFIL],
                            lado="#8d9391", cara="#a9aeac"), (-72, 62, 100), (-40, -80), orden=1),
        # Eje de salida: atraviesa la carcasa hacia la rueda trasera (estrías) y lleva el engranaje de 35 dientes
        P("eje_salida", cilindro((-60, ys, zs), X, 11, 250) + estrias, (-175, ys, zs), (-70, 40), orden=2),
        P("engranaje_salida", rueda(0, ys, zs, _R35, 35), (0, ys - _R35, zs), (40, 80), orden=4),
        P("seguro", arandela((10, ys, zs), X, 13, 1.5, color="#dfe3e4", lado=LADO_MEDIO), (10, ys + 13, zs), (60, 60), orden=5),
        # Eje intermedio: piñón de 12 dientes hecho en el eje (2.ª etapa) y engranaje grande de 56 (1.ª etapa)
        P("eje_intermedio", cilindro((10, yi, zi), X, 8, 120) + prisma((0, yi, zi), X, engranaje(_R12, 12, 3.2), 22,
                                                                      cara="#eeeeea", lado=LADO_MEDIO),
          (-40, yi, zi), (-60, -40), orden=3),
        P("engranaje_intermedio", rueda(36, yi, zi, _R56, 56), (36, yi + _R56, zi), (40, -90), orden=5),
        # Eje primario: sale del clutch (por la tapa, lado derecho) con el piñón de 16 dientes
        P("eje_primario", cilindro((70, yp, zp), X, 8, 150) + estrias_primario(yp, zp), (130, yp, zp), (60, -60), orden=4),
        P("pinon_primario", rueda(36, yp, zp, _R16, 16, 12, 6), (36, yp + _R16, zp), (-20, -90), orden=6),
        # Rodamientos: cada eje apoya en la carcasa (atrás) y en la tapa (adelante, del lado del clutch)
        P("rodamientos", rodamiento((-66, ys, zs), X, 20, 12) + rodamiento((-66, yi, zi), X, 15, 10) + rodamiento((-66, yp, zp), X, 14, 10)
          + rodamiento((80, yi, zi), X, 15, 10) + rodamiento((80, ys, zs), X, 18, 10) + rodamiento((80, yp, zp), X, 14, 10),
          (80, yi, zi), (70, 30), orden=6),
        # Retenes: donde un eje sale de la caja (al clutch y a la rueda), para que no se escape el aceite
        P("retenes", retenedor((-110, ys, zs), X, 17) + retenedor((112, yp, zp), X, 13), (-110, ys, zs), (-60, 60), orden=6),
        P("tapon_llenado", tapon_perno((-76, 56, 20), (-1, 0, 0), 14, 10),
          (-80, 56, 20), (-50, -60), orden=7),
        P("tapon_drenaje", tapon_perno((-76, -50, 60), (-1, 0, 0), 12, 8),
          (-80, -50, 60), (-60, 50), orden=7),
    ]
    lineas = [linea((-200, ys, zs), (130, ys, zs)), linea((-100, yi, zi), (120, yi, zi)), linea((-100, yp, zp), (170, yp, zp))]
    return piezas, lineas


def _clutch():
    """Clutch (embrague multidisco en baño de aceite), despiezado a lo largo del eje principal, del motor hacia afuera:
    arandela de empuje, canasta con el engranaje primario remachado, buje, centro estriado con su tuerca, discos
    alternados (fricción con orejas afuera / separadores de acero con dientes adentro), plato de presión, resortes con
    sus tornillos y el levantador (rodamiento de empuje y varilla)."""
    def con_orejas(r, r_oreja, orejas=8, ancho=.22):
        pts = []
        for i in range(orejas * 12):
            t = i * 2 * math.pi / (orejas * 12)
            fase = (t * orejas / (2 * math.pi)) % 1
            pts.append((math.cos(t) * (r_oreja if fase < ancho else r), math.sin(t) * (r_oreja if fase < ancho else r)))
        return pts

    # Canasta: copa abierta hacia afuera con ranuras (donde entran las orejas de los discos) y el engranaje primario detrás
    canasta = prisma((-118, 0, 0), X, engranaje(65, 72, 3.5), 8, hueco=iso._circ2d(18), cara="#f6f6f4", lado=LADO_MEDIO)
    canasta += cilindro((-96, 0, 0), X, 60, 36, ri=55, cara="#eceae4", lado="#d8d4ca")
    for k in range(8):                                                                    # ranuras de la canasta
        t = k * 2 * math.pi / 8
        canasta.append(polilinea([(x, 60.5 * math.sin(t), 60.5 * math.cos(t)) for x in (-112, -80)], 2.2, "#9a9f9f"))
    for k in range(6):                                                                    # amortiguadores (cauchos)
        t = k * 2 * math.pi / 6 + .3
        canasta += cilindro((-112.5, 36 * math.sin(t), 36 * math.cos(t)), X, 5, 3, cara=CAUCHO_CARA, lado=CAUCHO, grosor=1)
    centro = prisma((-10, 0, 0), X, engranaje(45, 24, 3), 30, hueco=iso._circ2d(13), cara="#f3f3f0", lado=LADO_MEDIO)
    for k in range(4):                                                                    # torres de los resortes
        t = k * math.pi / 2 + math.pi / 4
        centro += cilindro((8, 28 * math.sin(t), 28 * math.cos(t)), X, 6, 6, ri=2.5, cara="#e9e9e5", lado=LADO_MEDIO, grosor=1)
    friccion, separadores = [], []
    for i in range(9):
        x = 45 + i * 13
        if i % 2 == 0:
            friccion += prisma((x, 0, 0), X, con_orejas(52, 58), 3, hueco=iso._circ2d(44), cara=FRICCION, lado="#b39c7f")
        else:
            separadores += prisma((x, 0, 0), X, iso._circ2d(50, 48), 2, hueco=engranaje(45, 24, 3), cara="#e7ebec", lado="#c3c9cb")
    plato = cilindro((180, 0, 0), X, 50, 8, ri=10, cara="#f1f1ee", lado=LADO_MEDIO)
    for k in range(4):
        t = k * math.pi / 2 + math.pi / 4
        plato += cilindro((185, 28 * math.sin(t), 28 * math.cos(t)), X, 7, 3, ri=3, cara=HUECO, lado=LADO_MEDIO, grosor=1)
    resortes, pernos = [], []
    for k in range(4):
        t = k * math.pi / 2 + math.pi / 4
        y, z = 28 * math.sin(t), 28 * math.cos(t)
        resortes += resorte((215, y, z), X, 6, 26, vueltas=6, grosor_alambre=2.2)
        pernos += cilindro((248, y, z), X, 3, 14) + prisma((257, y, z), X, hexagono(5.5), 4, lado=LADO_MEDIO) \
            + arandela((254, y, z), X, 6.5, 1.2)
    piezas = [
        P("arandela_empuje", arandela((-165, 0, 0), X, 24, 2.5, lado=LADO_MEDIO), (-165, 24, 0), (-50, -70), orden=0),
        P("canasta", canasta, (-96, 60, 0), (-60, -90), orden=1),
        P("buje", cilindro((-55, 0, 0), X, 17, 22, ri=12, cara="#eeeae2", lado="#d6d0c4"), (-55, 17, 0), (-30, -80), orden=2),
        P("centro", centro, (-10, 45, 0), (-20, -100), orden=3),
        P("tuerca_centro", prisma((24, 0, 0), X, hexagono(15), 7, hueco=iso._circ2d(8), lado=LADO_MEDIO)
          + arandela((16, 0, 0), X, 16, 1.8), (24, 0, 15), (10, -110), orden=4),
        P("discos_friccion", friccion, (45, -58, 0), (-10, 90), orden=5),
        P("separadores", separadores, (58, 50, 0), (20, -110), orden=5),
        P("plato_presion", plato, (180, -50, 0), (40, 90), orden=6),
        P("resortes", resortes, (215, 28, 28), (40, -100), orden=7),
        P("tornillos_resorte", pernos, (256, -28, -28), (60, 80), orden=8),
        P("levantador", rodamiento((280, 0, 0), X, 11, 8) + cilindro((335, 0, 0), X, 3, 100), (320, 0, 3), (40, -60), orden=9),
    ]
    lineas = [linea((-185, 0, 0), (395, 0, 0))]
    return piezas, lineas


def estrias_primario(y, z):
    """Estrías del eje primario, donde encaja el clutch."""
    return [polilinea([(x, y + 8.4 * math.sin(t), z + 8.4 * math.cos(t)) for x in (120, 145)], 1)
            for t in [i * math.pi / 5 for i in range(10)]]


# ---------------------------------------------------------------------------
# 22. Cilindro y pistón (la "cabeza de fuerza"), biela y cigüeñal
# ---------------------------------------------------------------------------
def _biela(c, largo=120, r_pie=14, r_cabeza=28):
    x, y, z = c
    arriba = [(math.cos(t) * r_pie, largo / 2 + math.sin(t) * r_pie) for t in [i * math.pi / 12 for i in range(13)]]
    abajo = [(math.cos(t) * r_cabeza, -largo / 2 + math.sin(t) * r_cabeza) for t in [math.pi + i * math.pi / 12 for i in range(13)]]
    cuerpo = prisma(c, Z, arriba + abajo, 12, lado=LADO_MEDIO, cara="#efefeb")
    return (cuerpo + cilindro((x, y + largo / 2, z), Z, r_pie * .6, 13, cara=HUECO, grosor=1)
            + cilindro((x, y - largo / 2, z), Z, r_cabeza * .62, 13, cara=HUECO, grosor=1))


def _piston(c, r=36, alto=46):
    """Pistón: corona con dos rebajes de válvula, tres ranuras de anillos, alojamiento del pasador y falda recortada."""
    x, y, z = c
    f = cilindro((x, y - 6, z), Y, r, alto - 12, cara="#eeeeea", lado="#cfd3d4")                 # falda
    f += cilindro((x, y + alto / 2 - 9, z), Y, r, 18, cara="#f4f4f1", lado="#d9dcdc")           # zona de anillos
    for k in range(3):                                                                         # ranuras
        f.append(polilinea([(x + r * 1.01 * math.cos(t), y + alto / 2 - 4 - k * 5.5, z + r * 1.01 * math.sin(t))
                            for t in [i * math.pi / 16 for i in range(-5, 14)]], 1.4, "#7d8588"))
    f += cilindro((x - 11, y + alto / 2 + .6, z + 9), Y, 9, 1, cara="#dcdedd", lado="#cfd3d4", grosor=1)      # rebajes de válvula
    f += cilindro((x + 11, y + alto / 2 + .6, z - 9), Y, 10, 1, cara="#dcdedd", lado="#cfd3d4", grosor=1)
    f += cilindro((x, y - 4, z + r - 1), Z, 9, 4, ri=5, cara="#e6e8e8", lado="#cfd3d4")                       # alojamiento del pasador
    f += cilindro((x + r - 1, y - 14, z), X, 10, 2, cara="#e3e6e6", lado="#cfd3d4", grosor=1)                 # recorte de la falda
    return f


def _anillos(c, r=37):
    """Tres anillos abiertos (compresión, segundo y raspador de aceite), separados para verlos."""
    x, y, z = c
    f = []
    for k, (grosor, color) in enumerate(((1.6, "#9aa2a5"), (1.6, "#8a9295"), (3.2, "#b4babd"))):
        abierto = [(math.cos(t) * r, math.sin(t) * r) for t in [0.18 + i * (2 * math.pi - 0.36) / 40 for i in range(41)]]
        perfil = abierto + [(px * .9, py * .9) for px, py in abierto[::-1]]
        f += prisma((x, y + k * 9, z), Y, perfil, grosor, lado=color, cara="#dfe3e4", grosor=1.2)
    return f


def _cilindro_piston(perfil=None):
    p = _perfil(perfil)
    r, xs, ancho, fondo, esquinas = _bloque_motor(p)
    piezas = [
        P("empaque_culata", _plancha_empaque(318, ancho, fondo, r, xs, esquinas, _EMPAQUE_METAL), (ancho / 2 - 14, 319, 30), (-90, -20), orden=0),
        P("cilindro", _bloque_cilindro(255, 86, p, r, xs, ancho, fondo), (0, 255, 0), (-95, -20), orden=1),
        P("guias", [f for x, z in esquinas[:2] for f in cilindro((x, 205, z), Y, 5, 14, ri=2.5)], (esquinas[0][0], 205, esquinas[0][1]), (70, -20), orden=2),
        P("empaque_cilindro", _plancha_empaque(196, ancho, fondo, r + 2, xs, esquinas, _EMPAQUE_PAPEL), (ancho / 2 - 14, 196, 30), (-90, 10), orden=2),
        P("anillos", [f for xc in xs for f in _anillos((xc, 160, 0), r * .93)], (xs[0] + r, 169, 0), (70, -30), orden=3),
        P("piston", [f for xc in xs for f in _piston((xc, 120, 0), r * .9)], (xs[0], 130, 0), (-90, 20), orden=4),
        P("pasador", [f for xc in xs for f in cilindro((xc, 112, 100), Z, 9, 64, ri=5)], (xs[0], 112, 120), (70, 20), orden=5),
        P("seguros_piston", [f for xc in xs for f in seguro_pin((xc, 112, 148), Z, 9) + seguro_pin((xc, 112, 56), Z, 9)], (xs[0], 112, 148), (70, 40), orden=6),
        P("biela", [f for xc in xs for f in _biela((xc, -10, 0))], (xs[0], -10, 0), (-90, 30), orden=3),
        P("ciguenal", [f for xc in xs for f in cilindro((xc - 30, -80, 0), X, 62, 16, lado=LADO_MEDIO, cara="#ecece8")
                       + cilindro((xc + 30, -80, 0), X, 62, 16, lado=LADO_MEDIO, cara="#ecece8") + cilindro((xc, -80, 0), X, 12, 46)]
          + cilindro((xs[0] - r - 70, -80, 0), X, 14, 90) + cilindro((xs[-1] + r + 70, -80, 0), X, 12, 90),
          (xs[0] - r - 100, -80, 0), (-80, 40), orden=2),
        P("rodamientos_ciguenal", rodamiento((xs[0] - r - 40, -80, 0), X, 26, 14) + rodamiento((xs[-1] + r + 40, -80, 0), X, 26, 14),
          (xs[-1] + r + 40, -80, 0), (70, 50), orden=3),
    ]
    lineas = [linea((xc, -20, 0), (xc, 340, 0)) for xc in xs] + [linea((xs[0] - r - 130, -80, 0), (xs[-1] + r + 130, -80, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 23. Árbol de levas, cadenilla y balancines (distribución)
# ---------------------------------------------------------------------------
def _distribucion(perfil=None):
    """SOHC: un árbol de levas y balancines. DOHC (cuatro válvulas, dos árboles): admisión y escape, cada uno con su piñón,
    y taqués (vasos) debajo de las levas en lugar de balancines."""
    p = _perfil(perfil)
    dohc = bool(p.get("h"))
    levas = [(math.cos(t) * (16 + 10 * max(0, math.cos(t)) ** 3), math.sin(t) * (16 + 10 * max(0, math.cos(t)) ** 3))
             for t in [i * 2 * math.pi / 36 for i in range(36)]]
    guia = [(-6, -100), (6, -100), (10, 0), (8, 200), (-4, 214), (-10, 200), (-8, 0)]
    ejes = [(-48,), (48,)] if dohc else [(0,)]
    arbol, pinones, rodam = [], [], []
    for (x,) in ejes:
        arbol += cilindro((x, 260, -10), Z, 10, 200)
        if dohc:                                                       # dos lóbulos por cilindro en cada árbol
            for k in range(p["c"]):
                arbol += prisma((x, 260, -40 - k * 70), Z, levas, 14) + prisma((x, 260, -k * 70), Z, levas, 14)
        else:
            arbol += prisma((x, 260, -40), Z, levas, 16) + prisma((x, 260, 20), Z, levas, 16)
        pinones += prisma((x, 260, 122), Z, engranaje(40 if dohc else 48, 30 if dohc else 34, 5), 8, hueco=iso._circ2d(12),
                          cara="#f6f6f4", lado=LADO_MEDIO) + perno((x + 12, 260, 140), (0, 0, -1), 20, 6)
        rodam += rodamiento((x, 260, -100), Z, 20, 12) + rodamiento((x, 260, 80), Z, 20, 12)
    # Cadenilla: abraza los piñones de levas arriba y el del cigüeñal abajo
    rp = 40 if dohc else 50
    if dohc:
        arriba = [(48 + math.cos(t) * rp, 260 + math.sin(t) * rp) for t in [i * math.pi / 14 for i in range(8)]] \
            + [(-48 + math.cos(t) * rp, 260 + math.sin(t) * rp) for t in [math.pi / 2 + i * math.pi / 14 for i in range(8)]]
    else:
        arriba = [(math.cos(t) * rp, 260 + math.sin(t) * rp) for t in [i * math.pi / 14 for i in range(15)]]
    abajo = [(math.cos(t) * 22, -120 + math.sin(t) * 22) for t in [math.pi + i * math.pi / 10 for i in range(11)]]
    cadena = [(x, y, 130) for x, y in arriba + abajo + arriba[:1]]
    ancho_guia = 48 + rp if dohc else 62
    piezas = [
        P("arbol_levas", arbol, (ejes[0][0], 260, -110), (-70, -50), orden=1),
        P("rodamientos", rodam, (ejes[-1][0], 260, 80), (60, -70), orden=2),
        P("pinon_levas", pinones, (ejes[-1][0], 260 + rp, 122), (70, -40), orden=3),
        P("cadenilla", manguera(cadena, 6, "#7a8488"), cadena[len(arriba) + 2], (70, 20), orden=4),
        P("pinon_ciguenal", prisma((0, -120, 122), Z, engranaje(20, 14, 4), 8, hueco=iso._circ2d(8), cara="#f6f6f4", lado=LADO_MEDIO),
          (0, -120, 122), (60, 40), orden=3),
        P("guia_cadenilla", prisma((-ancho_guia, 80, 150), Z, guia, 10, lado="#3c4448", cara="#59636a"), (-ancho_guia, 80, 150), (-70, 20), orden=5),
        P("guia_tensor", prisma((ancho_guia, 80, 150), Z, [(-x, y) for x, y in guia], 10, lado="#3c4448", cara="#59636a"),
          (ancho_guia, 120, 150), (70, -10), orden=5),
        P("tensor", caja((ancho_guia + 78, 60, 150), (46, 24, 24)) + cilindro((ancho_guia + 43, 60, 150), X, 6, 34)
          + perno((ancho_guia + 108, 60, 150), X, 14, 7), (ancho_guia + 88, 60, 150), (70, 20), orden=6),
    ]
    if dohc:
        # Taqués (vasos) debajo de cada leva, con su laina de calibración
        vasos = [f for (x,) in ejes for k in range(p["c"]) for z in (-40 - k * 70, 0 - k * 70)
                 for f in cilindro((x, 222, z), Y, 13, 18, cara="#eef0f0", lado="#c3c9cc") + cilindro((x, 232, z), Y, 9, 2, cara="#d0d5d7")]
        piezas += [P("balancin", vasos, (ejes[0][0], 232, -40), (-60, -50), orden=3),
                   P("tornillo_calibracion", [f for (x,) in ejes for f in cilindro((x, 238, -40), Y, 9, 1.5, cara="#c9ced0")],
                     (ejes[-1][0], 240, -40), (70, -30), orden=5)]
    else:
        balancin = [(-58, 6), (-48, 16), (40, 12), (64, 4), (64, -6), (40, -12), (-48, -14), (-60, -4)]
        espejo = [(-x, y) for x, y in balancin[::-1]]
        piezas += [
            P("balancin", prisma((-70, 340, -40), Z, balancin, 14, hueco=iso._circ2d(7, 16)) + prisma((70, 340, 20), Z, espejo, 14, hueco=iso._circ2d(7, 16)),
              (-70, 352, -40), (-60, -50), orden=3),
            P("eje_balancin", cilindro((-70, 340, -40), Z, 6, 120) + cilindro((70, 340, 20), Z, 6, 120), (70, 340, 80), (60, -50), orden=4),
            P("tornillo_calibracion", perno((-128, 370, -40), MENOS_Y, 24, 6) + tuerca((-128, 356, -40), Y, 7)
              + perno((128, 370, 20), MENOS_Y, 24, 6) + tuerca((128, 356, 20), Y, 7), (128, 372, 20), (70, -30), orden=5),
        ]
    lineas = [linea((x, 260, -150), (x, 260, 160)) for (x,) in ejes]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 24. Carburador
# ---------------------------------------------------------------------------
def _carburador():
    caucho = dict(lado=CAUCHO, cara=CAUCHO_CARA)
    piezas = [
        P("ducto", cilindro((-150, 0, 0), X, 30, 50, r2=26, ri=20, **caucho), (-150, 0, 0), (-60, -60), orden=0),
        P("cuerpo", caja((0, 0, 0), (90, 76, 76)) + cilindro((0, 0, 0), X, 28, 140, ri=22) + cilindro((0, 52, 0), Y, 28, 30),
          (40, 20, 0), (-70, -70), orden=1),
        P("cortina", cilindro((0, 130, 0), Y, 20, 46, cara="#f3f3ef"), (0, 130, 0), (-70, -20), orden=2),
        P("aguja", cilindro((0, 190, 0), Y, 2, 70) + cilindro((0, 226, 0), Y, 5, 4), (0, 200, 0), (60, -20), orden=3),
        P("resorte", resorte((0, 270, 0), Y, 14, 52, 7), (0, 270, 0), (60, -10), orden=4),
        P("tapa", cilindro((0, 320, 0), Y, 30, 14) + cilindro((0, 340, 0), Y, 7, 24), (0, 320, 0), (-70, -30), orden=5),
        P("chicles", cilindro((0, -60, 18), Y, 4, 22) + prisma((0, -74, 18), Y, hexagono(6), 6, lado=LADO_MEDIO)
          + cilindro((0, -60, -18), Y, 3, 18), (0, -60, 18), (70, 10), orden=2),
        P("flotador", cilindro((-24, -110, 0), Z, 13, 46, cara="#f7f2df", lado="#e5dcc0") + cilindro((24, -110, 0), Z, 13, 46, cara="#f7f2df", lado="#e5dcc0")
          + caja((0, -100, -26), (60, 3, 10)), (24, -110, 0), (70, 20), orden=3),
        P("aguja_flotador", cilindro((0, -88, 40), Y, 3, 16, r2=1), (0, -88, 40), (-60, 30), orden=3),
        P("empaque", oring((0, -140, 0), Y, 40, 3), (40, -140, 0), (-70, 30), orden=4),
        P("taza", cilindro((0, -180, 0), Y, 44, 64, r2=40) + prisma((0, -218, 0), Y, hexagono(8), 8, lado=LADO_MEDIO), (0, -180, 0), (-70, 40), orden=5),
        P("tornillo_mezcla", perno((110, -20, 50), X, 26, 5) + resorte((95, -20, 50), X, 6, 16, 5), (115, -20, 50), (70, 30), orden=3),
        P("cebador", cilindro((0, 40, -70), Z, 9, 40) + caja((0, 40, -100), (30, 10, 6)), (0, 40, -100), (-60, -40), orden=2),
        P("manguera", manguera(curva((40, -40, -50), (90, -100, -90), (60, -200, -110)), 6), (60, -200, -110), (60, 50), orden=1),
    ]
    lineas = [linea((0, -230, 0), (0, 360, 0)), linea((-200, 0, 0), (100, 0, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 25. Cuerpo de aceleración e inyección
# ---------------------------------------------------------------------------
def _inyeccion():
    caucho = dict(lado=CAUCHO, cara=CAUCHO_CARA)
    tubo = curva((-70, 160, 0), (60, 220, -60), (200, 60, -40))
    piezas = [
        P("multiple", cilindro((-110, 0, 0), X, 30, 50, r2=26, ri=20, **caucho), (-110, 0, 0), (-60, -60), orden=0),
        P("cuerpo", caja((0, 0, 0), (80, 84, 84)) + cilindro((0, 0, 0), X, 30, 110, ri=24) + cilindro((56, 0, 0), X, 22, 2, cara="#d8dcdd", grosor=1),
          (20, 42, 0), (-60, -80), orden=1),
        P("polea", cilindro((0, 0, 64), Z, 24, 8) + caja((0, 26, 72), (6, 16, 6)), (0, 0, 68), (60, 40), orden=2),
        P("sensor_tps", prisma((0, 0, -60), Z, redondeado(34, 30, 10), 10, lado=OSCURO, cara="#4a5357")
          + caja((22, -6, -60), (12, 10, 9), colores=(CAUCHO,) * 3), (0, 0, -66), (-60, 40), orden=2),
        P("motor_ralenti", cilindro((10, 64, -24), Y, 13, 22, lado=OSCURO, cara=LADO_MEDIO) + caja((10, 80, -24), (12, 9, 14), colores=(CAUCHO,) * 3)
          + cilindro((10, 49, -24), Y, 4.5, 12, lado=LADO_MEDIO), (10, 64, -24), (60, -50), orden=2),
        P("inyector", cilindro((-70, 110, 0), Y, 7, 46, lado=OSCURO, cara=LADO_MEDIO) + caja((-60, 126, 0), (12, 11, 10), colores=(CAUCHO,) * 3)
          + oring((-70, 135, 0), Y, 8, 3) + oring((-70, 88, 0), Y, 8, 3) + cilindro((-70, 78, 0), Y, 3.5, 14, lado=LADO_MEDIO),
          (-70, 110, 0), (-60, -50), orden=3),
        P("empaque", oring((-70, 70, 0), Y, 6, 2) + oring((-110, 0, 0), X, 22, 2), (-70, 70, 0), (-70, 20), orden=2),
        P("riel", cilindro((-70, 160, 0), Y, 11, 26), (-70, 160, 0), (-60, -30), orden=4),
        P("sensor", caja((-40, 20, 60), (18, 22, 18), colores=(OSCURO, LADO_MEDIO, OSCURO)) + cilindro((-40, 0, 60), Y, 5, 12), (-40, 20, 60), (-60, 40), orden=2),
        P("manguera", manguera(tubo, 7), tubo[8], (60, -40), orden=1),
        P("bomba_gasolina", cilindro((200, -20, -40), Y, 26, 120, cara="#e9ecec") + cilindro((200, 46, -40), Y, 44, 8)
          + cilindro((200, 58, -40), Y, 9, 16, lado=OSCURO), (200, 0, -40), (70, 30), orden=2),
    ]
    lineas = [linea((-150, 0, 0), (80, 0, 0)), linea((-70, 60, 0), (-70, 180, 0))]
    return piezas, lineas


# ---------------------------------------------------------------------------
# 26. Escape: tubo (codo), silenciador (exosto) y protector
# ---------------------------------------------------------------------------
def _escape(perfil=None):
    """Escape: tubo (codo) desde la culata, empaques, catalizador y silenciador. Lateral (exosto largo al lado de la rueda)
    o bajo el motor (caja debajo del cárter, como en Pulsar NS/RS 200 y KTM 200), según la moto."""
    p = _perfil(perfil)
    piezas, lineas = _escape_bajo() if p.get("e") else _escape_lateral()
    if perfil and not p.get("i"):
        piezas = [q for q in piezas if q.puesto != "sensor_oxigeno"]            # sin inyección no hay sensor de oxígeno
    if p.get("u"):
        # Tubo y silenciador soldados, una sola pieza: no hay empaque de unión ni abrazadera; el tubo pasa a ser del silenciador
        sil = next(q for q in piezas if q.puesto == "silenciador")
        for q in [q for q in piezas if q.puesto in ("tubo", "catalizador")]:
            sil.agregar(*q.formas)
        if not p.get("e"):                                                        # tramo soldado entre el codo y el silenciador
            sil.agregar(*cilindro((0, -40, 52), Z, 31, 76, r2=30, cara="#e3e6e7", lado="#b9bfc2"))
        piezas = [q for q in piezas if q.puesto not in ("tubo", "catalizador", "empaque_silenciador", "abrazadera")]
    return piezas, lineas


def _escape_lateral():
    metal, metal_lado = "#e3e6e7", "#b9bfc2"
    cobre = ("#d2a273", "#a97d55")
    grafito = ("#6b7377", "#4a5154")
    tubo = curva((0, 160, 250), (0, -40, 260), (0, -40, 70), 22)
    ranuras = [f for k in range(4) for f in caja((63, -20, -150 + k * 42), (2, 34, 10), colores=(OSCURO, OSCURO, OSCURO), grosor=1)]
    piezas = [
        P("empaque", cilindro((0, 196, 250), Y, 18, 5, ri=11, cara=cobre[0], lado=cobre[1]), (18, 196, 250), (-70, -30), orden=0),
        P("brida", prisma((0, 176, 250), Y, estadio(92, 30), 6, hueco=iso._circ2d(16), lado=LADO_MEDIO, cara="#eef0f0")
          + cilindro((36, 179.5, 250), Y, 5, 1, cara=HUECO, grosor=1) + cilindro((-36, 179.5, 250), Y, 5, 1, cara=HUECO, grosor=1)
          + cilindro((0, 166, 250), Y, 15, 14, lado=metal_lado, cara=metal), (40, 176, 250), (60, -40), orden=1),
        P("sensor_oxigeno", cilindro((34, 110, 252), X, 7, 30, lado=OSCURO, cara=LADO_MEDIO) + prisma((52, 110, 252), X, hexagono(9), 6, lado=LADO_MEDIO)
          + manguera(curva((66, 110, 252), (110, 130, 252), (120, 180, 230)), 4, OSCURO), (56, 110, 252), (60, -10), orden=2),
        P("tubo", manguera(tubo, 26, "#d4d8da"), tubo[8], (-70, 20), orden=1),
        P("catalizador", cilindro((0, -40, 120), Z, 32, 70, r2=30, cara="#dfe2e3", lado=metal_lado), (0, -8, 120), (-70, 40), orden=2),
        P("empaque_silenciador", cilindro((0, -40, 58), Z, 27, 7, ri=19, cara=grafito[0], lado=grafito[1]), (0, -14, 58), (60, 60), orden=3),
        P("abrazadera", cilindro((0, -40, 36), Z, 33, 14, ri=29, lado=LADO_MEDIO, cara="#dfe3e4")
          + perno((0, -4, 36), X, 26, 5), (0, -6, 36), (60, 50), orden=4),
        P("valvula_ais", caja((-70, 200, 230), (34, 26, 26), colores=(OSCURO, LADO_MEDIO, OSCURO))
          + manguera(curva((-70, 187, 230), (-40, 160, 250), (-12, 150, 250)), 5), (-70, 200, 230), (-70, -40), orden=2),
        P("silenciador", cilindro((0, -40, 4), Z, 52, 30, r2=30, cara=metal, lado=metal_lado)                     # cono de entrada
          + cilindro((0, -40, -130), Z, 52, 240, cara=metal, lado=metal_lado)
          + [polilinea([(0, 12, -10), (0, 12, -250)], 1.2, "#aeb4b7")]                                              # costura
          + cilindro((0, -40, -254), Z, 48, 10, cara="#d7dbdc", lado=metal_lado)                                     # tapa final
          + cilindro((0, -40, -272), Z, 20, 30, ri=15, lado=LADO_MEDIO, cara="#c9ced0"),                            # punta
          (0, 12, -100), (-70, -50), orden=5),
        P("protector", prisma((60, -20, -110), X, redondeado(230, 70, 30), 4, lado="#3c4448", cara="#59636a") + ranuras,
          (62, -20, -110), (70, -40), orden=6),
        P("soporte", caja((0, 34, -170), (14, 50, 40), colores=(LADO_MEDIO, "#eef0f0", LADO_CLARO))
          + cilindro((0, 64, -170), X, 13, 18, ri=6, lado=CAUCHO, cara=CAUCHO_CARA), (0, 64, -170), (-60, -50), orden=6),
    ]
    lineas = [linea((0, 160, 250), (0, 240, 250)), linea((0, -40, -300), (0, -40, 80))]
    return piezas, lineas


def _escape_bajo():
    """Escape bajo el motor: el tubo baja de la culata y entra por delante a una caja silenciadora debajo del cárter."""
    metal, metal_lado = "#e3e6e7", "#b9bfc2"
    cobre = ("#d2a273", "#a97d55")
    tubo = curva((0, 160, 250), (0, -60, 260), (0, -110, 120), 20)
    caja_silenciador = (prisma((0, -150, -60), Y, redondeado(150, 230, 40), 110, lado=metal_lado, cara=metal)
                        + prisma((0, -94, -60), Y, redondeado(120, 200, 34), 1.5, lado="#c4c9cb", cara="#dde1e2", grosor=1.2)
                        + cilindro((50, -150, -190), Z, 18, 30, ri=13, lado=LADO_MEDIO, cara="#c9ced0"))                       # salida
    piezas = [
        P("empaque", cilindro((0, 196, 250), Y, 18, 5, ri=11, cara=cobre[0], lado=cobre[1]), (18, 196, 250), (-70, -30), orden=0),
        P("brida", prisma((0, 176, 250), Y, estadio(92, 30), 6, hueco=iso._circ2d(16), lado=LADO_MEDIO, cara="#eef0f0")
          + cilindro((0, 166, 250), Y, 15, 14, lado=metal_lado, cara=metal), (40, 176, 250), (60, -40), orden=1),
        P("sensor_oxigeno", cilindro((34, 100, 252), X, 7, 30, lado=OSCURO, cara=LADO_MEDIO) + prisma((52, 100, 252), X, hexagono(9), 6, lado=LADO_MEDIO),
          (56, 100, 252), (60, -10), orden=2),
        P("tubo", manguera(tubo, 26, "#d4d8da"), tubo[8], (-70, 20), orden=1),
        P("catalizador", cilindro((0, -112, 140), Z, 30, 50, r2=28, cara="#dfe2e3", lado=metal_lado), (0, -82, 140), (-70, 40), orden=2),
        P("empaque_silenciador", cilindro((0, -112, 98), Z, 27, 7, ri=19, cara="#6b7377", lado="#4a5154"), (0, -86, 98), (60, 60), orden=3),
        P("abrazadera", cilindro((0, -112, 80), Z, 33, 14, ri=29, lado=LADO_MEDIO, cara="#dfe3e4"), (0, -80, 80), (60, 50), orden=4),
        P("silenciador", caja_silenciador, (0, -95, -60), (-70, -50), orden=5),
        P("protector", prisma((80, -150, -40), X, redondeado(170, 90, 24), 4, lado="#3c4448", cara="#59636a"), (82, -150, -40), (70, -40), orden=6),
        P("soporte", caja((0, -80, -150), (60, 16, 20), colores=(LADO_MEDIO, "#eef0f0", LADO_CLARO))
          + cilindro((-26, -66, -150), Y, 10, 14, ri=4, lado=CAUCHO, cara=CAUCHO_CARA) + cilindro((26, -66, -150), Y, 10, 14, ri=4, lado=CAUCHO, cara=CAUCHO_CARA),
          (26, -60, -150), (-60, -50), orden=6),
    ]
    lineas = [linea((0, 160, 250), (0, 230, 250))]
    return piezas, lineas


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
    "freno_trasero": ("Freno trasero: bomba de pie, manguera y caliper", _freno_trasero),
    "bombas_abs": ("Bombas de freno, mangueras y ABS", _bombas_abs),
    "caja_secundaria": ("Transmisión final y piñonería", _caja_secundaria),
    "clutch": ("Clutch", _clutch),
    "cilindro_piston": ("Cilindro y pistón", _cilindro_piston),
    "distribucion": ("Árbol de levas, cadenilla y balancines", _distribucion),
    "carburador": ("Carburador", _carburador),
    "inyeccion": ("Cuerpo de aceleración e inyección", _inyeccion),
    "escape": ("Escape y silenciador", _escape),
}

# Dibujos que cambian según el motor de cada moto. Su clave puede llevar el perfil: "culata__l1c2d59v4b1".
PERFILABLES = {"culata", "cilindro_piston", "distribucion", "amortiguadores", "valvulas", "escape", "rueda_tambor"}


def _base(clave):
    return clave.split("__", 1)[0]


@lru_cache(maxsize=256)
def _construir_guardado(clave):
    base, _, perfil = clave.partition("__")
    funcion = DIAGRAMAS[base][1]
    piezas, lineas = funcion(perfil) if base in PERFILABLES and perfil else funcion()
    return tuple(piezas), tuple(lineas)


def _construir(clave):
    """Geometría del dibujo. Armarla es lo más lento del despiece y se pide una vez por cada pieza sola de la guía:
    se arma una vez por clave y se entregan copias de las piezas, porque componer() y dibujar_lamina() les ponen
    atributos (ancla_svg, contexto...). Las formas no se modifican y se comparten."""
    piezas, lineas = _construir_guardado(clave)
    return [copy.copy(q) for q in piezas], list(lineas)


def nombre_dibujo(clave):
    """Nombre del dibujo; en scooter (s1) la rueda trasera no lleva arrastre y la suspensión no tiene basculante de cadena."""
    base, _, perfil = clave.partition("__")
    p = _perfil(perfil) if perfil else {}
    if p.get("s") and base == "rueda_tambor":
        return "Rueda trasera y freno de tambor"
    if p.get("s") and base == "amortiguadores":
        return "Amortiguador trasero" if p.get("m") else "Amortiguadores traseros"
    return DIAGRAMAS[base][0]


def clave_dibujo(diagrama, perfil):
    """Clave del dibujo para una moto: con su perfil si el dibujo depende del motor."""
    return f"{diagrama}__{perfil}" if diagrama in PERFILABLES and perfil else diagrama


def perfil_motor(liquida, cilindros, cilindraje, dohc, bujias_por_cilindro, mono=False, valvulas=None, escape_bajo=False,
                 scooter=False, inyeccion=False):
    """Perfil en texto: diámetro estimado del cilindro (carrera ≈ diámetro) a partir del cilindraje por cilindro."""
    por_cilindro = max(49, cilindraje) / max(1, cilindros)
    diametro = round((4 * por_cilindro * 1000 / 3.1416) ** (1 / 3))
    valvulas = valvulas or (4 if dohc else 2)
    return f"l{int(bool(liquida))}c{cilindros}d{diametro}v{valvulas}b{bujias_por_cilindro}m{int(bool(mono))}h{int(bool(dohc))}e{int(bool(escape_bajo))}s{int(bool(scooter))}i{int(bool(inyeccion))}"


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
                ("CRANKCASE", "carcasa_der"), ("COVER", "tapa_clutch"), ("PLUG, OIL LEVEL", "tapon_llenado"), ("GAUGE", "tapon_llenado"), ("LENS", "visor"),
                ("WINDOW", "visor"), ("SIGHT", "visor"), ("LEVEL", "visor"),
                ("FILLER", "tapon_llenado"), ("ELEMENT", "filtro"), ("OIL CLEANER", "filtro"), ("STRAINER", "malla"),
                ("SCREEN", "malla"), ("PLUG", "tapon"), ("SWITCH", "swiche"), ("NEUTRAL", "swiche"), ("GASKET", "empaques"),
                ("OIL SEAL", "reten"), ("BEARING", "rodamientos"), ("PUMP", "bomba")],
}
REGLAS["rueda_trasera"] = [("SPROCKET", "corona"), ("CLUTCH HUB", "porta_sprocket"), ("HUB, CLUTCH", "porta_sprocket"),
                           ("DAMPER", "cauchos"), ("CHAIN", "cadena"), ("DISK", "disco"), ("DISC", "disco"), ("PULLER", "tensores"),
                           ("ADJUSTER", "tensores")] + REGLAS["rueda"]


# Lo mismo para los catálogos en español (Auteco: Bajaj, KTM, TVS). Sin tildes; se comparan sin tildes.
REGLAS_ES = {
    "cvt": [("RESORTE CONTRAPESO", "resortes_zapatas"), ("AMORT CONTRAPESO", "zapatas"), ("ZAPATA", "zapatas"),
            ("CONTRAPESO", "rodillos"), ("RODILLO", "rodillos"), ("CORREDERA", "deslizadores"), ("DESLIZADOR", "deslizadores"),
            ("ROLDANA PRIMARIA MOVIL", "polea_movil"), ("POLEA MOVIL", "polea_movil"), ("PISCO FIXADOR", "polea_fija"),
            ("POLEA FIJA", "polea_fija"), ("ROLDANA SECUNDARIA", "polea_trasera"), ("ASIENTO DE RESORTE SECUNDARIO", "resorte_torque"),
            ("RESORTE SECUNDARIO", "resorte_torque"), ("CAJA DE EMBRAGUE", "campana"), ("CAMPANA", "campana"),
            ("PORTADOR DE EMBRAGUE", "clutch"), ("CORREA", "correa"), ("LEVA", "rampa"), ("RAMPA", "rampa"),
            ("COLLAR", "buje"), ("CASQUILLO", "buje"), ("BUJE", "buje")],
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
    "transmision": [("EJE PINON SALIDA", "eje_salida"), ("EJE PIÑON SALIDA", "eje_salida"), ("EJE SALIDA", "eje_salida"),
                    ("EJE CLUTCH", "eje_principal"), ("ANILLO", None), ("ARANDELA", None), ("BUJE", None), ("PIN ", None), ("PINON SALIDA", "pinon"),
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
    "rueda": [("ROTOR DE SENSOR", "sensor_abs"), ("RUEDA FUNDIDA", "rin"), ("NEUMATICO", "llanta"), ("EJE DE LA RUEDA", "eje"),
              ("VALVULA", "valvula"), ("RODAMIENTO", "rodamientos"), ("COJINETE", "rodamientos"), ("BALINERA", "rodamientos"), ("RETEN", "retenedores")],
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
    "freno_completo": [("CABLE FRENO", "cable_cbs"), ("CABLE CBS", "cable_cbs"), ("MANGUERA TANQUE", "manguera"), ("KIT RETENES", "empaques"), ("KIT GUARDAPOLVO", "guardapolvo")],
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

# Sistemas agregados después (caja secundaria, cilindro y pistón, distribución, carburador, inyección y escape)
REGLAS.update({
    "caja_secundaria": [("MAIN AXLE", "eje_intermedio"), ("AXLE, DRIVE", "eje_salida"), ("DRIVE AXLE", "eje_salida"),
                        ("PRIMARY DRIVE", "pinon_primario"), ("PRIMARY", "eje_primario"), ("1ST WHEEL", "engranaje_salida"),
                        ("WHEEL", "engranaje_salida"), ("GEAR", "engranaje_intermedio"), ("CIRCLIP", "seguro"),
                        ("BEARING", "rodamientos"), ("OIL SEAL", "retenes"), ("DRAIN", "tapon_drenaje"),
                        ("FILLER", "tapon_llenado"), ("GASKET", "empaque"), ("CASE", "carcasa_caja"), ("COVER", "carcasa_caja")],
    "cilindro_piston": [("PISTON RING", "anillos"), ("RING SET", "anillos"), ("PIN, PISTON", "pasador"), ("PISTON PIN", "pasador"),
                        ("CLIP", "seguros_piston"), ("CIRCLIP", "seguros_piston"), ("PISTON", "piston"),
                        ("CONNECTING ROD", "biela"), ("ROD, CONNECTING", "biela"), ("CRANKSHAFT", "ciguenal"), ("CRANK", "ciguenal"),
                        ("BEARING", "rodamientos_ciguenal"), ("GASKET, CYLINDER HEAD", "empaque_culata"),
                        ("GASKET, CYLINDER", "empaque_cilindro"), ("GASKET", "empaque_cilindro"), ("DOWEL", "guias"),
                        ("CYLINDER", "cilindro")],
    "distribucion": [("TENSIONER", "tensor"), ("GUIDE, TENSION", "guia_tensor"), ("GUIDE, STOPPER 2", "guia_tensor"),
                     ("GUIDE 2", "guia_tensor"), ("GUIDE, STOPPER", "guia_cadenilla"), ("GUIDE", "guia_cadenilla"),
                     ("SPROCKET, DRIVE", "pinon_ciguenal"), ("SPROCKET", "pinon_levas"), ("DECOMPRESSION ASSY", "pinon_levas"),
                     ("BEARING", "rodamientos"), ("SHAFT, ROCKER", "eje_balancin"), ("ROCKER", "balancin"), ("LIFTER", "balancin"),
                     ("ADJUST", "tornillo_calibracion"), ("CHAIN", "cadenilla"), ("DECOMPRESS", "arbol_levas"),
                     ("CAMSHAFT", "arbol_levas")],
    "carburador": [("NOZZLE", "chicles"), ("DIAPHRAGM", "cortina"), ("CARBURETOR ASSY", "cuerpo"), ("FLOAT CHAMBER", "taza"), ("BOWL", "taza"), ("NEEDLE VALVE", "aguja_flotador"),
                   ("FLOAT", "flotador"), ("NEEDLE", "aguja"), ("JET", "chicles"), ("THROTTLE VALVE", "cortina"),
                   ("PISTON", "cortina"), ("SCREW, PILOT", "tornillo_mezcla"), ("SCREW, THROTTLE STOP", "tornillo_mezcla"),
                   ("SCREW, AIR", "tornillo_mezcla"), ("STARTER", "cebador"), ("CHOKE", "cebador"), ("SPRING", "resorte"),
                   ("CAP", "tapa"), ("TOP", "tapa"), ("GASKET", "empaque"), ("O-RING", "empaque"), ("JOINT", "ducto"),
                   ("MANIFOLD", "ducto"), ("HOSE", "manguera"), ("CARBURETOR", "cuerpo")],
    "inyeccion": [("THROTTLE BODY", "cuerpo"), ("THROTTLE POSITION", "sensor_tps"), ("TPS", "sensor_tps"), ("ISC", "motor_ralenti"),
                  ("IDLE", "motor_ralenti"), ("INJECTOR", "inyector"), ("FUEL PUMP", "bomba_gasolina"), ("DELIVERY", "riel"),
                  ("SENSOR", "sensor"), ("HOSE", "manguera"), ("JOINT", "multiple"), ("MANIFOLD", "multiple"),
                  ("O-RING", "empaque"), ("GASKET", "empaque"), ("PULLEY", "polea")],
    "escape": [("GASKET, MUFFLER", "empaque_silenciador"), ("GASKET, SILENCER", "empaque_silenciador"),
               ("GASKET", "empaque"), ("PROTECTOR", "protector"), ("COVER", "protector"), ("SHIELD", "protector"), ("MUFFLER", "silenciador"),
               ("SILENCER", "silenciador"), ("EXHAUST PIPE", "tubo"), ("PIPE", "tubo"), ("GASKET", "empaque"),
               ("FLANGE", "brida"), ("SENSOR", "sensor_oxigeno"), ("CATALY", "catalizador"), ("BRACKET", "soporte"),
               ("STAY", "soporte"), ("CLAMP", "abrazadera"), ("BAND", "abrazadera")],
})
# Caliper (Honda, Suzuki): juego de pastillas, sellos del pistón, guardapolvos y pines de las pastillas. Van primero
# porque "SEAL SET, PISTON" no es el pistón y "PAD SET" son las pastillas. Solo los puestos que tiene cada dibujo.
# Puestos de cada dibujo escritos a mano: sacarlos dibujando costaba medio segundo en cada arranque del servidor.
# PuestosFijosTests comprueba que sigan iguales a los del dibujo.
PUESTOS_FIJOS = {
    "freno_disco": {"caliper", "disco", "empaques", "guardapolvo", "lamina", "pasador", "pastillas", "piston", "purgador",
                    "resorte_pastillas", "soporte"},
    "freno_completo": {"abrazadera", "banjo", "bomba", "cable_cbs", "caliper", "deposito", "diafragma", "empaques", "guardapolvo",
                       "guia_manguera", "interruptor", "kit_reparacion", "lamina", "manguera", "manigueta", "pasador",
                       "pastillas", "pedal", "piston", "purgador", "resorte_pastillas", "soporte", "soporte_deposito", "tapa"},
    "freno_trasero": {"banjo", "bomba", "caliper", "deposito", "diafragma", "empaques", "guardapolvo", "guia_manguera",
                      "interruptor", "kit_reparacion", "lamina", "manguera", "manguera_deposito", "pasador", "pastillas",
                      "pedal", "piston", "purgador", "resorte_pastillas", "soporte", "soporte_deposito", "tapa", "varilla"},
    "bombas_abs": {"abrazadera", "abrazadera_trasera", "banjo", "banjo_trasera", "bomba", "bomba_trasera", "deposito",
                   "deposito_trasera", "diafragma", "diafragma_trasera", "guia_manguera", "interruptor",
                   "interruptor_trasera", "kit_reparacion", "kit_reparacion_trasera", "manguera", "manguera_trasera",
                   "manigueta", "manigueta_trasera", "soporte_abs", "tapa", "tapa_trasera", "tubos", "unidad_abs"},
}
for _clave in ("freno_disco", "freno_completo"):
    _puestos = PUESTOS_FIJOS[_clave]
    REGLAS[_clave] = [(t, p) for t, p in [
        ("PAD SET", "pastillas"), ("SHOE(PAD)", "pastillas"), ("PAD, BRAKE", "pastillas"), ("BRAKE PAD", "pastillas"),
        ("SEAL SET", "empaques"), ("SEAL, PISTON", "empaques"), ("PISTON SEAL", "empaques"), ("SEAL, DUST", "guardapolvo"),
        ("DUST SEAL", "guardapolvo"), ("DUST COVER", "guardapolvo"), ("BOOT", "guardapolvo"), ("INSULATOR", "piston"),
        ("PLUG, PIN", "pasador"), ("PIN, HANGER", "pasador"), ("HANGER PIN", "pasador"), ("PIN, PAD", "pasador"),
        ("STOPPER", "lamina"), ("SHIM", "lamina")] if p in _puestos] + REGLAS[_clave]
_PIE_EN = [("RESERVOIR HOSE", "manguera_deposito"), ("HOSE, RESERVOIR", "manguera_deposito"), ("RESERVOIR", "deposito"),
           ("TANK", "deposito"), ("PUSH ROD", "varilla"), ("ROD", "varilla"), ("JOINT", "varilla"), ("CLEVIS", "varilla"),
           ("BOOT", "guardapolvo"), ("SWITCH", "interruptor")]
_PIE_ES = [("MANGUERA TANQUE", "manguera_deposito"), ("MANGUERA DEPOSITO", "manguera_deposito"), ("TANQUE", "deposito"),
           ("DEPOSITO", "deposito"), ("VARILLA", "varilla"), ("HORQUILLA", "varilla"), ("YUGO", "varilla"),
           ("GUARDAPOLVO VARILLA", "guardapolvo"), ("SWICHE", "interruptor"), ("INTERRUPTOR", "interruptor")]
_p_tras = PUESTOS_FIJOS["freno_trasero"]
REGLAS["freno_trasero"] = _PIE_EN + [(t, p) for t, p in REGLAS["freno_completo"] if p in _p_tras]
REGLAS_ES["freno_trasero"] = _PIE_ES + [(t, p) for t, p in REGLAS_ES["freno_completo"] if p in _p_tras]
_p_abs = PUESTOS_FIJOS["bombas_abs"]
REGLAS["bombas_abs"] = [("HYDRAULIC UNIT", "unidad_abs"), ("HYDRAULIC", "unidad_abs"), ("ABS", "unidad_abs"), ("PIPE", "tubos"),
                        ("BRAKE PIPE", "tubos"), ("HOLDER, BRAKE HOSE", "guia_manguera"), ("CLAMP", "guia_manguera"),
                        ("STAY", "soporte_abs"), ("BRACKET, HYDRAULIC", "soporte_abs")] \
    + [(t, p) for t, p in REGLAS["bomba_freno"] if p in _p_abs]
REGLAS_ES["bombas_abs"] = [("ABS", "unidad_abs"), ("MODULADOR", "unidad_abs"), ("TUBO", "tubos")] \
    + [(t, p) for t, p in REGLAS_ES["bomba_freno"] if p in _p_abs]
REGLAS["amortiguadores"] = [("SEAL", "retenedor"), ("CAP", "tapones"), ("SHAFT, PIVOT", "eje_basculante"), ("PIVOT SHAFT", "eje_basculante"),
                            ("ADJUSTER", "tensores"), ("PULLER", "tensores"), ("CHAIN CASE", "protector_cadena"), ("CASE, CHAIN", "protector_cadena"),
                            ("COVER, CHAIN", "protector_cadena"), ("GUIDE, CHAIN", "deslizador"), ("SUPPORT, CHAIN", "deslizador"), ("SLIDER", "deslizador"),
                            ("BUSH", "bujes"), ("COLLAR", "bujes"), ("BEARING", "bujes"), ("CUSHION", "amortiguador"), ("SHOCK", "amortiguador"),
                            ("ARM", "basculante")] + REGLAS["amortiguadores"]
REGLAS_ES["amortiguadores"] = [("RETEN", "retenedor"), ("TAPON", "tapones"), ("PASADOR BRAZO", "eje_basculante"), ("EJE BRAZO", "eje_basculante"),
                               ("EJE BASCULANTE", "eje_basculante"), ("TENSOR CADENA", "tensores"), ("TEMPLADOR", "tensores"),
                               ("PROTECTOR CADENA", "protector_cadena"), ("GUARDACADENA", "protector_cadena"), ("GUIA CADENA", "deslizador"),
                               ("DESLIZADOR", "deslizador"), ("PATIN", "deslizador"), ("BUJE", "bujes"), ("RODAMIENTO", "bujes"),
                               ("AMORTIGUADOR", "amortiguador"), ("BRAZO", "basculante"), ("BASCULANTE", "basculante")] + REGLAS_ES["amortiguadores"]
# Suspensión delantera: puente superior, espiga (eje de dirección con la tijera de abajo), bujes de la barra,
# tapón de la barra y soporte de la farola, antes que las reglas generales
REGLAS["suspension_delantera"] = [("HANDLE CROWN", "tijera_superior"), ("CROWN, HANDLE", "tijera_superior"), ("BRACKET, UPPER", "tijera_superior"),
                                  ("UNDER BRACKET", "eje_direccion"), ("BRACKET, UNDER", "eje_direccion"), ("STEERING STEM", "eje_direccion"),
                                  ("SLIDE METAL", "bujes"), ("METAL, SLIDE", "bujes"), ("GUIDE BUSH", "bujes"), ("BUSH", "bujes"),
                                  ("CAP BOLT", "tapon"), ("BOLT, CAP", "tapon"), ("HEADLIGHT", "soporte_farola"), ("HEADLAMP", "soporte_farola")] \
    + REGLAS["suspension_delantera"]
REGLAS_ES["suspension_delantera"] = [("CABEZA ESPIGA", "tijera_superior"), ("TIJERA SUPERIOR", "tijera_superior"), ("PUENTE SUPERIOR", "tijera_superior"),
                                     ("ESPIGA", "tijera"), ("TIJERA INFERIOR", "tijera"), ("SOPORTE FAROLA", "soporte_farola"),
                                     ("CILINDRO", "cilindro_amortiguador"), ("BUJE GUIA", "bujes"), ("BUJE TUBO", "bujes"),
                                     ("TORNILLO TUBO", "tapon"), ("TAPON", "tapon")] + REGLAS_ES["suspension_delantera"]
REGLAS["radiador"] = [("CAP, RESERVOIR", "tapa_deposito"), ("RESERVOIR CAP", "tapa_deposito"), ("HOSE, RESERVOIR", "manguera_deposito"),
                      ("RESERVOIR HOSE", "manguera_deposito"), ("OVERFLOW", "manguera_deposito"), ("BREATHER", "manguera_deposito"),
                      ("RESERVOIR", "deposito"), ("TANK", "deposito"), ("JOINT", "tubo_t"), ("HOSE 2", "manguera_inferior"),
                      ("PIPE 2", "manguera_inferior"), ("PIPE 3", "manguera_inferior"), ("CAP, RADIATOR", "tapa")] + REGLAS["radiador"]
REGLAS_ES["radiador"] = [("TAPA TANQUE", "tapa_deposito"), ("TAPA DEPOSITO", "tapa_deposito"), ("MANGUERA TANQUE", "manguera_deposito"),
                         ("MANGUERA DEPOSITO", "manguera_deposito"), ("TANQUE", "deposito"), ("DEPOSITO", "deposito"), ("RESERVA", "deposito"),
                         ("TUBO T-BOMBA", "manguera_inferior"), ("RADIADOR-TUBO T", "manguera_inferior"), ("INFERIOR", "manguera_inferior"),
                         ("BOMBA", "manguera_inferior"), ("TUBO T", "tubo_t"), ("TERMOSTATO-RADIADOR", "manguera"), ("SUPERIOR", "manguera"),
                         ("TAPA RADIADOR", "tapa")] + REGLAS_ES["radiador"]
REGLAS["culata"] = [("PISTON RING", "anillos"), ("RING SET", "anillos"), ("PIN, PISTON", "pasador"), ("PISTON PIN", "pasador"),
                    ("CLIP, PISTON", "seguros_piston"), ("PISTON", "piston")] + REGLAS["culata"]
REGLAS_ES["culata"] = [("KIT ANILLOS", "anillos"), ("ANILLOS", "anillos"), ("PIN PISTON", "pasador"), ("PASADOR", "pasador"),
                       ("SEGURO PIN", "seguros_piston"), ("KIT PISTON", "piston"), ("PISTON", "piston")] + REGLAS_ES["culata"]
REGLAS["aceite"] = [("COVER, OIL ELEMENT", "tapa_filtro"), ("CAP, OIL FILTER", "tapa_filtro"), ("COVER, STRAINER", "malla"),
                    ("ELEMENT", "filtro"), ("OIL CLEANER", "filtro"), ("FILTER, ENGINE OIL", "filtro"), ("FILTER, ROTARY", "filtro"),
                    ("ROTOR, OIL FILTER", "filtro"), ("GEAR", "pinon_bomba"), ("SCREEN", "malla")] + REGLAS["aceite"]
REGLAS_ES["aceite"] = [("CUBIERTA FILTRO", "tapa_filtro"), ("TAPA FILTRO", "tapa_filtro"), ("KIT FILTRO", "filtro"),
                       ("FILTRO", "filtro"), ("PIÑON BOMBA", "pinon_bomba"), ("PINON BOMBA", "pinon_bomba")] + REGLAS_ES["aceite"]
REGLAS_ES.update({
    "caja_secundaria": [("EJE PRIMARIO", "eje_primario"), ("EJE INTERMEDIO", "eje_intermedio"), ("EJE PRINCIPAL", "eje_intermedio"),
                        ("EJE SALIDA", "eje_salida"), ("EJE TRASERO", "eje_salida"), ("PIÑON PRIMARIO", "pinon_primario"),
                        ("PINON PRIMARIO", "pinon_primario"), ("ENGRANAJE", "engranaje_intermedio"), ("PIÑON", "engranaje_salida"),
                        ("PINON", "engranaje_salida"), ("SEGURO", "seguro"), ("RODAMIENTO", "rodamientos"), ("BALINERA", "rodamientos"),
                        ("RETEN", "retenes"), ("DRENAJE", "tapon_drenaje"), ("LLENADO", "tapon_llenado"), ("EMPAQUE", "empaque"),
                        ("CARCASA", "carcasa_caja"), ("TAPA", "carcasa_caja")],
    "cilindro_piston": [("ANILLO", "anillos"), ("PASADOR", "pasador"), ("PIN PISTON", "pasador"), ("SEGURO", "seguros_piston"),
                        ("PISTON", "piston"), ("BIELA", "biela"), ("CIGUENAL", "ciguenal"), ("EMPAQUE CULATA", "empaque_culata"),
                        ("EMPAQUE", "empaque_cilindro"), ("GUIA", "guias"), ("BUJE GUIA", "guias"), ("RODAMIENTO", "rodamientos_ciguenal"),
                        ("BALINERA", "rodamientos_ciguenal"), ("CILINDRO", "cilindro")],
    "distribucion": [("EJE BALANCIN", "eje_balancin"), ("EJE DEL BALANCIN", "eje_balancin"), ("BALANCIN", "balancin"),
                     ("GUIA TENSOR", "guia_tensor"), ("PATIN TENSOR", "guia_tensor"), ("LADO TENSOR", "guia_tensor"),
                     ("TENSOR", "tensor"), ("GUIA", "guia_cadenilla"), ("PATIN", "guia_cadenilla"),
                     ("PIÑON CIGUEÑAL", "pinon_ciguenal"), ("PINON CIGUENAL", "pinon_ciguenal"), ("SPROCKET", "pinon_levas"),
                     ("PIÑON", "pinon_levas"), ("PINON", "pinon_levas"), ("RODAMIENTO", "rodamientos"), ("BALINERA", "rodamientos"),
                     ("BUJE EJE LEVAS", "rodamientos"), ("CADENILLA", "cadenilla"), ("CADENA", "cadenilla"), ("GUIA", "guia_cadenilla"),
                     ("PATIN", "guia_cadenilla"), ("CALIBRA", "tornillo_calibracion"), ("DESCOMPRES", "arbol_levas"),
                     ("EJE DE LEVAS", "arbol_levas"), ("EJE LEVAS", "arbol_levas"), ("ARBOL DE LEVAS", "arbol_levas"),
                     ("LEVAS", "arbol_levas")],
    "carburador": [("BOQUEREL", "chicles"), ("DIFUSOR", "chicles"), ("PULVERIZADOR", "chicles"), ("DIAFRAGMA", "cortina"),
                   ("AGUJA FLOTADOR", "aguja_flotador"), ("PUNZON", "aguja_flotador"), ("FLOTADOR", "flotador"), ("AGUJA", "aguja"),
                   ("CHICLER", "chicles"), ("CHICLE", "chicles"), ("SURTIDOR", "chicles"), ("TAZA", "taza"), ("CUBA", "taza"),
                   ("CORTINA", "cortina"), ("PISTON", "cortina"), ("TORNILLO MEZCLA", "tornillo_mezcla"), ("TORNILLO AIRE", "tornillo_mezcla"),
                   ("TORNILLO RALENTI", "tornillo_mezcla"), ("TORNILLO ALTA", "tornillo_mezcla"), ("CEBADOR", "cebador"),
                   ("CHOKE", "cebador"), ("CHOQUE", "cebador"), ("RESORTE", "resorte"), ("TAPA", "tapa"), ("EMPAQUE", "empaque"),
                   ("ORING", "empaque"), ("O-RING", "empaque"), ("MULTIPLE", "ducto"), ("ACOPLE", "ducto"), ("BOQUILLA", "ducto"),
                   ("CONECTOR", "ducto"), ("MANGUERA", "manguera"), ("CARBURADOR", "cuerpo")],
    "inyeccion": [("AJUSTE RPM", "motor_ralenti"), ("E.C.U", "sensor"), ("ECU", "sensor"), ("CUERPO", "cuerpo"), ("MARIPOSA", "cuerpo"), ("TPS", "sensor_tps"), ("SENSOR POSICION", "sensor_tps"),
                  ("SENSOR ACELERADOR", "sensor_tps"), ("RALENTI", "motor_ralenti"), ("ISC", "motor_ralenti"), ("IAC", "motor_ralenti"),
                  ("INYECTOR", "inyector"), ("BOMBA", "bomba_gasolina"), ("RIEL", "riel"), ("SENSOR", "sensor"),
                  ("MANGUERA", "manguera"), ("MULTIPLE", "multiple"), ("BOQUILLA", "multiple"), ("ACOPLE", "multiple"),
                  ("CONECTOR", "multiple"), ("EMPAQUE", "empaque"), ("ORING", "empaque"), ("O-RING", "empaque"), ("POLEA", "polea")],
    "escape": [("BUJE", "soporte"), ("CAUCHO", "soporte"), ("ANTIVIBRANTE", "soporte"), ("EMPAQUE SILENCIADOR", "empaque_silenciador"), ("EMPAQUE MOFLE", "empaque_silenciador"),
               ("EMPAQUE EXOSTO", "empaque_silenciador"), ("EMPAQUE", "empaque"), ("ANILLO", "empaque"),
               ("PROTECTOR", "protector"), ("CUBIERTA", "protector"), ("GUARDA", "protector"), ("SILENCIADOR", "silenciador"),
               ("EXOSTO", "silenciador"), ("MOFLE", "silenciador"), ("TUBO", "tubo"), ("CODO", "tubo"), ("COLECTOR", "tubo"),
               ("EMPAQUE", "empaque"), ("ANILLO", "empaque"), ("BRIDA", "brida"), ("PLATINA", "brida"), ("SENSOR", "sensor_oxigeno"),
               ("SONDA", "sensor_oxigeno"), ("CATALIZ", "catalizador"), ("SOPORTE", "soporte"), ("ABRAZADERA", "abrazadera")],
})


# Requerimiento 9: nombres de escape y basculante de AKT, Honda, Hero y Suzuki (al final: van antes que las demás)
REGLAS["amortiguadores"] = [("CASE, DRIVE CHAIN", "protector_cadena"), ("CASE, UPPER", "protector_cadena"), ("CASE, UNDER", "protector_cadena"),
                            ("CASE,CHAIN", "protector_cadena"), ("CASE, CHAIN", "protector_cadena"), ("ROLLER, CHAIN", "deslizador"),
                            ("SLIDER CHAIN", "deslizador"), ("JOINT, RJ", "cadena"), ("CHAIN", "cadena")] + REGLAS["amortiguadores"]
REGLAS_ES["amortiguadores"] = [("KIT BUJ", "bujes"), ("EJE TIJERA", "eje_basculante"), ("TIJERA", "basculante"), ("TORQUE", "barra_torque"),
                               ("KIT ARRAST", "cadena"), ("CADENA", "cadena")] + REGLAS_ES["amortiguadores"]
REGLAS["escape"] = [("AIR INDUCTION", "valvula_ais"), ("SEAT", "empaque")] + REGLAS.get("escape", [])
REGLAS_ES["escape"] = [("QUILLA", "protector")] + REGLAS_ES.get("escape", [])
REGLAS["escape"] = [("COVER, EXH", "protector"), ("PROTECTOR", "protector"), ("PACKING, PROTECTOR", "protector"), ("RUBBER, PROTECTOR", "protector"),
                    ("COVER, MUFFLER TAIL", "silenciador"), ("COLLAR COMP., EX", "brida"), ("JOINT, EX", "brida"), ("GASKET, EX", "empaque"),
                    ("RUBBER, MUFFLER", "soporte"), ("PIPE, EXHAUST", "tubo"), ("PIPE, EX", "tubo")] + REGLAS["escape"]
REGLAS_ES["escape"] = [("CURVA MOFLE", "tubo"), ("CURVA", "tubo"), ("PUNTERA", "silenciador"), ("MEDIA LUNA", "brida"),
                       ("ARAND ACOPLE", "brida"), ("ACOPLE", "brida"), ("SOPORTE MOFLE", "soporte"), ("EMPAQ", "empaque"),
                       ("MOFLE", "silenciador")] + REGLAS_ES["escape"]
REGLAS["amortiguadores"] = [("SHAFT, RR SWGARM PIVOT", "eje_basculante"), ("SHAFT,RR SWGARM PIVOT", "eje_basculante"), ("BOLT, PIVOT", "eje_basculante"),
                            ("SHAFT, PIVOT", "eje_basculante"), ("PIVOT", "bujes"), ("BUFFER,CHAIN", "deslizador"), ("BUFFER, CHAIN", "deslizador"),
                            ("SLIDER, CHAIN", "deslizador"), ("SWINGINGARM", "basculante"), ("SWING ARM", "basculante"), ("FORK, REAR", "basculante"),
                            ("ARM, REAR", "basculante"), ("DUST", "tapones")] + REGLAS["amortiguadores"]


# Clutch: la canasta trae remachado el engranaje primario; el embrague del arranque (starter clutch) NO va aquí
REGLAS["clutch"] = [("GUIDE, CLUTCH OUTER", "buje"), ("OUTER", "canasta"), ("PLATE,CLUTCH DRIVEN", "separadores"),
                    ("PLATE, CLUTCH DRIVEN", "separadores"), ("PLATE,CLUTCH DRIVE", "discos_friccion"), ("PLATE, CLUTCH DRIVE", "discos_friccion"),
                    ("RELEASE", "levantador"), ("PUSH LEVER", "levantador"), ("PLATE, PUSH", "levantador"), ("PRIMARY DRIVEN", "canasta"), ("HOUSING", "canasta"), ("GEAR, PRIMARY", "canasta"), ("DAMPER", "canasta"),
                    ("PLATE, FRICTION", "discos_friccion"), ("FRICTION", "discos_friccion"), ("PLATE, CLUTCH", "separadores"),
                    ("CLUTCH PLATE", "separadores"), ("BOSS", "centro"), ("CENTER", "centro"), ("HUB", "centro"),
                    ("PLATE, PRESSURE", "plato_presion"), ("PRESSURE", "plato_presion"), ("LIFTER", "plato_presion"),
                    ("SPRING", "resortes"), ("ROD, PUSH", "levantador"), ("PUSH ROD", "levantador"), ("ROD", "levantador"),
                    ("PUSH PIECE", "levantador"), ("BALL", "levantador"), ("BEARING", "levantador"),
                    ("SPACER", "buje"), ("BUSH", "buje"), ("COLLAR", "buje"), ("THRUST", "arandela_empuje"),
                    ("NUT", "tuerca_centro"), ("WASHER", "arandela_empuje"), ("BOLT", "tornillos_resorte")]
REGLAS_ES["clutch"] = [("CORONA INTERNA", "centro"), ("PIÑON CORONA", "canasta"), ("PINON CORONA", "canasta"), ("KIT CORONA", "canasta"),
                       ("CORONA", "canasta"), ("DISCO DE CLUTCH INTERNO", "separadores"), ("DISCO DE CLUTCH", "discos_friccion"),
                       ("METALICO", "separadores"), ("SEPARAD", "separadores"), ("PORTA RESORTE", "plato_presion"), ("PRENS", "plato_presion"),
                       ("PRESIONADOR", "plato_presion"), ("EMPUJADOR", "levantador"), ("IMPULSOR", "levantador"), ("LEVA INTERNA", "levantador"),
                       ("PORTABALINERA", "levantador"), ("PORTADISCOS", "centro"), ("MANZA", "centro"), ("MANZAN", "centro"), ("MANZ", "centro"), ("PRENSA", "plato_presion"), ("PRENSCLUSLICGR", "plato_presion"), ("ESPACIADOR", "buje"),
                       ("CAMPANA", "canasta"), ("CANASTA", "canasta"), ("CARCASA CLUTCH", "canasta"), ("ENGRANAJE PRIMARIO", "canasta"),
                       ("ENGRANAJE CONDUCIDO", "canasta"), ("DISCO DE FRICCION", "discos_friccion"), ("DISCO FRICCION", "discos_friccion"),
                       ("DISCOS CLUTCH", "discos_friccion"), ("DISCO CLUTCH", "discos_friccion"), ("FRICCION", "discos_friccion"),
                       ("SEPARADOR", "separadores"), ("DISCO METALICO", "separadores"), ("DISCO LISO", "separadores"),
                       ("PLATO PRESION", "plato_presion"), ("PLATO DE PRESION", "plato_presion"), ("PLATO", "plato_presion"),
                       ("LEVANTADOR", "levantador"), ("CENTRO", "centro"), ("MANZANA", "centro"), ("RESORTE", "resortes"),
                       ("VARILLA", "levantador"), ("BALINERA", "levantador"), ("RODAMIENTO", "levantador"), ("BOLA", "levantador"),
                       ("BUJE", "buje"), ("ARANDELA EMPUJE", "arandela_empuje"), ("TUERCA", "tuerca_centro"),
                       ("ARANDELA", "arandela_empuje"), ("TORNILLO", "tornillos_resorte")]


# Catálogo Yamaha Colombia en español (Aerox 155): palabras de su traducción para ubicar cada pieza en el dibujo.
# Van primero en sus listas porque "ROTOR DE SENSOR" no es el cable del sensor ni "TUBO EXTERIOR" el tubo interior.
_YAMAHA_CO = {
    "rueda": [("ROTOR DE SENSOR", "sensor_abs")],
    "rueda_tambor": [("JUEGO DE ZAPATA", "bandas"), ("ZAPATA", "bandas"), ("RUEDA FUNDIDA", "rin"), ("NEUMATICO", "llanta"),
                     ("PLACA INDICADOR", "indicador"), ("PALANCA DE ARBOL", "palanca"), ("ARBOL DE LEVAS", "leva"), ("RESORTE DE TENSION", "resortes")],
    "freno_disco": [("FUNDA", "guardapolvo"), ("JUEGO DE RETENES", "empaques"), ("COJIN DE FREN", "pastillas"),
                    ("SOPORTE DE PASTILLAS", "resorte_pastillas"), ("CALIBRE", "caliper"), ("TORNILLO DE PURGA", "purgador")],
    "bombas_abs": [("HIDRAULICA", "unidad_abs")],
    "bomba_freno": [("CLAMP,SENSOR", "h_electrico"), ("CLAMP, SENSOR", "h_electrico"), ("CLAMP (L", "h_electrico"),
                    ("HIDRAULICA", "unidad_abs"), ("HYDRAULIC", "unidad_abs"), ("HYDR UNIT", "unidad_abs"),
                    ("MASTER", "bomba"), ("CYLINDER ASSY", "bomba"), ("PISTON ASSY", "kit_reparacion")],
    "freno_completo": [("MANIFRE", "manigueta")],
    "suspension_delantera": [("TUBO EXTERIOR", "botella"), ("TUBO INTERIOR", "barra_cromada"), ("PLATINA INFERIOR", "eje_direccion"),
                             ("PISTA DE BOLAS", "tazas"), ("RETEN DE COJINETE", "rodamientos_direccion"), ("PERNO DE TAPA", "tapon"),
                             ("CILINDRO COMPL DE HORQ", "cilindro_amortiguador"), ("HORQUILLA DELANTERA", "barra_completa")],
    "radiador": [("BOMBA DE AGUA", "bomba_agua"), ("EJE IMPULSOR", "bomba_agua"), ("CUBIERTA DE CAJA", "bomba_agua"),
                 ("GRIFO DE DRENAJE", "drenaje"), ("CAJA VENTILADOR", "carcasa_ventilador"), ("TAPON, DEL RADIADOR", "tapa"),
                 ("TUBO", "manguera")],
    "carcasa": [("EQUILIBRIO", "h_caucho"), ("ELEMENTO", "filtro"), ("TAPON DEL NIVEL", "tapon_llenado")],
    "aceite": [("COLADOR", "malla")],
    "admision": [("CAJA DE ACELERADOR", "cuerpo_aceleracion"), ("UNION DEL FILTRO", "ducto"), ("TUBO DE ADMISION", "ducto")],
    "caja_secundaria": [("EJE SECUNDARIO", "eje_salida"), ("ENGRANAJE TRACC", "pinon_primario"), ("ENGRANAJE RUEDA", "engranaje_salida"),
                        ("SELLO ACEITE", "retenes")],
}
for _clave, _reglas in _YAMAHA_CO.items():
    REGLAS[_clave] = _reglas + REGLAS.get(_clave, [])
    REGLAS_ES[_clave] = _reglas + REGLAS_ES.get(_clave, [])
REGLAS["radiador"] = [("WATER PUMP", "bomba_agua"), ("IMPELLER", "bomba_agua")] + REGLAS["radiador"]
# Ruedas de rayos y con cámara: en Colombia "neumático" es la cámara (TUBE) y "llanta" la cubierta; los rayos con sus niples
_RUEDAS = [("VALVE", "valvula"), ("VALVULA", "valvula"), ("TUBE", "neumatico"), ("NEUMAT", "neumatico"), ("CAMARA", "neumatico"),
           ("SPOKE", "radios"), ("NIPPLE", "radios"), ("RADIO", "radios"), ("RAYO", "radios"), ("NIPLE", "radios")]
for _clave in ("rueda", "rueda_trasera", "rueda_tambor"):
    REGLAS[_clave] = _RUEDAS + REGLAS.get(_clave, [])
    REGLAS_ES[_clave] = _RUEDAS + REGLAS_ES.get(_clave, [])



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
CON_LUGAR_PROPIO = {"tijera_superior", "eje_direccion", "eje_basculante", "tapon", "pasador", "purgador", "banjo", "esparragos", "tornillo_calibracion", "cunas", "guias", "empate",
                    "seguros_piston", "seguro", "tornillo_mezcla", "chicles", "aguja_flotador", "anillos"}


# La rueda trasera y el kit de arrastre vienen en la misma lámina del catálogo; el visor los muestra por separado
CON_ARRASTRE = {"rueda_trasera", "rueda_tambor"}
ARRASTRE = {"corona", "cadena", "porta_sprocket", "cauchos", "tensores", "pinon"}
_PALABRAS_ARRASTRE = re.compile(r"\b(SPROCKET|CORONA|CADENA|CHAIN|PI[NÑ]ON|TENSOR|TEMPLADOR|CAUCHO|DAMPER|EMPATE|JOINT)")
_PALABRAS_RUEDA = re.compile(r"(BANDA|LEVA|FRENO|BRAKE|DISCO|DISC|CAMPANA|SENSOR|EJE RUEDA|AXLE|RIN\b|RIM\b|LLANTA|TIRE)")


def es_arrastre(clave, descripcion):
    """¿La pieza es del kit de arrastre (corona, cadena, porta sprocket, cauchos, tensores) y no de la rueda?"""
    kit = puestos_kit(clave, descripcion)
    if kit:
        return any(k in ARRASTRE for k in kit)
    texto = _sin_tildes((descripcion or "").upper())
    if _PALABRAS_ARRASTRE.search(texto):
        return True
    if _PALABRAS_RUEDA.search(texto):
        return False
    puesto = puesto_para(clave, descripcion)
    if puesto.startswith("h_"):
        puesto = INFERENCIA.get(clave, {}).get(puesto, puesto)
    return puesto in ARRASTRE


def puesto_para(clave, descripcion):
    """Toda pieza tiene puesto: la del dibujo del sistema o, si no está dibujada, la de la franja de tornillería."""
    herraje = herraje_para(descripcion)
    propio = puesto_en_dibujo(clave, descripcion)
    if herraje in SIEMPRE_EN_FRANJA and propio not in CON_LUGAR_PROPIO:
        return herraje
    return _por_primera_palabra(clave, descripcion, propio) or propio or herraje


# La primera palabra del catálogo dice qué es la pieza; lo que sigue, a qué pertenece: "O-RING, OIL PUMP" es un o-ring
# (de la bomba), no la bomba. Si la regla del dibujo la mandó a una pieza de otro tipo, va al puesto de su tipo en ese
# dibujo (el o-ring de la lámina del aceite) o, si el dibujo no tiene uno, a la franja de tornillería.
_TIPO_INICIO = [
    ("bujia", re.compile(r"^(PLUG,?\s*SPARK|SPARK PLUG|BUJIAS?)\b")),
    ("capuchon", re.compile(r"^(PLUG CAP|CAP,?\s*(SPARK\s*)?PLUG|CAPUCHON\s+(DE\s+(LA\s+)?)?BUJIA)\b")),
    ("empaque", re.compile(r"^(O-?\s?RING|ORING|GASKET|EMPAQ\w*|EMAPQ\w*|JUNTA|PACKING|ANILLO (EN )?O)\b")),
    ("reten", re.compile(r"^(OIL SEAL|DUST SEAL|SEAL,\s*(OIL|DUST)|RET[EÉ]N\w*|SELLO,? (DE )?ACEITE|SELLO PARA POLVO|GUARDAPOLVO)\b")),
    ("resorte", re.compile(r"^(SPRING|RESORTES?|MUELLES?)\b")),
    ("rodamiento", re.compile(r"^(BEARING|BALL BEARING|RODAMIENTOS?|BALINERAS?|COJINETES?)\b")),
    ("buje", re.compile(r"^(COLLAR|SPACER|BUSH|BUJES?|ESPACIADOR|CASQUILLO)\b(?! DE (DIAFRAGMA|EMBRAGUE))")),
    ("abrazadera", re.compile(r"^(CLAMPER|CLAMP|ABRAZADERA|ABRAZAD|GRAPA)\b")),
    ("etiqueta", re.compile(r"^(CALCOMANIA|EMBLEMA?|LABEL|STICKER|GRAPHIC|ETIQUETA)\b")),
    ("manguera", re.compile(r"^(HOSE|MANGUERA)\b")),
    ("tapa", re.compile(r"^(PLUG|CAP|TAPON|CAPUCHON)\b")),
]
_TIPO_PUESTO = {"empaque": re.compile(r"^(empaque|oring|junta)"), "reten": re.compile(r"^(reten|retenedor|guardapolvo|sello)"),
                "resorte": re.compile(r"^resorte"), "rodamiento": re.compile(r"^rodamiento"), "buje": re.compile(r"^buje"),
                "abrazadera": re.compile(r"^abrazadera"), "etiqueta": re.compile(r"^(etiqueta|calcomania|emblema)"),
                "bujia": re.compile(r"^bujia"), "capuchon": re.compile(r"^capuchon"), "manguera": re.compile(r"^manguera"),
                "tapa": re.compile(r"^tap")}
_HERRAJE_DE_TIPO = {"empaque": "h_empaque", "reten": "h_empaque", "resorte": "h_resorte", "rodamiento": "h_rodamiento",
                    "buje": "h_buje", "abrazadera": "h_abrazadera", "etiqueta": "h_etiqueta", "bujia": "h_electrico",
                    "capuchon": "h_electrico", "manguera": "h_manguera", "tapa": "h_tapa"}
# Un buje sí puede ser el rodamiento liso de un eje, la guía de centrado o parte del soporte de caucho donde está
_COMPATIBLES = {"buje": re.compile(r"^(rodamiento|guia|soporte)"), "tapa": re.compile(r"^(visor|deposito|purgador)")}
# Puestos que son un conjunto y traen esas piezas dentro (el levantador del clutch es varilla y rodamiento)
_CONJUNTOS = {"levantador", "kit_reparacion", "kit", "barra_completa", "amortiguador"}


@lru_cache(maxsize=None)
def _puestos_dibujo(base):
    """Puestos que tiene el dibujo, en su orden."""
    return tuple(dict.fromkeys(q.puesto for q in _construir_guardado(base)[0] if q.puesto)) if base in DIAGRAMAS else ()


def tipo_por_primera_palabra(descripcion):
    """Qué es la pieza según la primera palabra del catálogo (empaque, resorte, tapa...), o None."""
    texto = _sin_tildes((descripcion or "").upper()).strip(" .")
    return next((t for t, patron in _TIPO_INICIO if patron.match(texto)), None)


def _por_primera_palabra(clave, descripcion, propio):
    if propio in _CONJUNTOS or (propio or "").startswith("h_"):     # una regla que manda a la franja, se respeta
        return None
    texto = _sin_tildes(descripcion.upper()).strip(" .")
    tipo = tipo_por_primera_palabra(descripcion)
    if not tipo or (propio and (_TIPO_PUESTO[tipo].match(propio) or (tipo in _COMPATIBLES and _COMPATIBLES[tipo].match(propio)))):
        return None
    # Entre los puestos de ese tipo: el que nombra la descripción ("empaque_culata" para "Junta culata"); si ninguno,
    # uno genérico ("empaques", "resortes"); los de otra pieza ("resorte_pastillas" para el resorte del pedal), nunca.
    mejor, largo, generico = None, 0, None
    for q in _puestos_dibujo(_base(clave)):
        if not _TIPO_PUESTO[tipo].match(q):
            continue
        if "_" not in q:
            generico = generico or q
            continue
        sufijo = q.split("_", 1)[1]
        for frase in _SINONIMOS_SUFIJO.get(sufijo, [sufijo.upper().replace("_", " ")]):
            if len(frase) > largo and re.search(rf"\b{frase}\b", texto):
                mejor, largo = q, len(frase)
    return mejor or generico or _HERRAJE_DE_TIPO[tipo]


# Cómo nombra el catálogo la pieza a la que pertenece un empaque o resorte (la frase más larga que coincide gana)
_SINONIMOS_SUFIJO = {
    "culata": ["CYLINDER HEAD", "CULATA"],
    "cilindro": ["CYLINDER", "CILINDRO"],
    "tapa": ["CYLINDER HEAD COVER", "HEAD COVER", "CUBIERTA CULATA", "TAPA CULATA", "TAPA VALVULAS", "TAPA", "CUBIERTA", "COVER"],
    "pastillas": ["PASTILLAS?", "PASTAS?", "PADS?"],
    "llenado": ["LLENADO", "FILLER", "LEVEL", "NIVEL", "VARILLA", "MEDIDOR"],
    "drenaje": ["DRENAJE", "DRAIN"],
    "filtro": ["FILTRO", "FILTER", "STRAINER", "CEDAZO"],
    "valvulas": ["VALVULAS?", "TAPPET"],
    "deposito": ["DEPOSITO", "TANQUE", "RESERVOIR", "TANK"],
    "clutch": ["CLUTCH", "CRANKCASE", "CARTER"],
}


# Clutch: los discos ("PLATE"), su tuerca, su arandela y los tornillos de los resortes tienen lugar en el dibujo
CON_LUGAR_PROPIO |= {"discos_friccion", "separadores", "plato_presion", "tornillos_resorte", "tuerca_centro", "arandela_empuje", "levantador"}

# Piezas que no todas las motos tienen: si la lámina no las trae, no se dibujan (las demás quedan tenues, como contexto)
OPCIONALES = {"capuchon", "bomba_agua", "cable_cbs", "neumatico", "radios", "barra_torque", "cadena", "valvula_ais", "soporte_farola", "pedal", "kit", "unidad_abs", "soporte_abs", "tubos", "sensor_cable", "sensor_abs", "unidad_abs", "soporte_deposito", "guia_manguera", "manigueta",
              "filtro", "tapa_filtro",
              "ciguenal", "rodamientos_ciguenal", "biela", "piston", "anillos", "pasador", "seguros_piston", "empaque_culata", "bomba_gasolina", "catalizador", "sensor_oxigeno",
              }


def _queda(pieza, usadas):
    """Con `usadas` (puestos que trae la lámina) se dibujan solo esas piezas, como en el plano de la marca."""
    if usadas is None:
        return True
    if pieza.puesto is not None:
        return pieza.puesto in usadas
    return pieza.padre is None or pieza.padre in usadas


def _letra_rotulo(texto):
    """Tamaño de letra del rótulo: más pequeño cuanto más largo es el nombre (sistema · moto)."""
    n = len(texto)
    return 17 if n <= 34 else 15 if n <= 44 else 13 if n <= 56 else 12


def _texto_rotulo(texto, maximo=74):
    texto = texto.upper()
    return texto if len(texto) <= maximo else texto[:maximo - 1].rstrip(" ·") + "…"


@lru_cache(maxsize=512)

def _rotulo_columna(texto, cx, ancho):
    """Nombre de una columna de la franja de tornillería, que nunca se sale de su casilla ni pisa a la vecina:
    se achica la letra y, si aun así no cabe, se parte en dos líneas por el espacio más cercano a la mitad."""
    base, minima, util = (14 if ancho >= 100 else 12), 10.5, ancho - 16
    def tam(lineas):                      # Barlow semibold: ~0,53 del cuerpo por carácter
        return min(base, util / (0.53 * max(len(t) for t in lineas)))
    lineas = [texto]
    if tam(lineas) < minima and " " in texto:
        mitad = len(texto) / 2
        corte = min((i for i, c in enumerate(texto) if c == " "), key=lambda i: abs(i - mitad))
        lineas = [texto[:corte], texto[corte + 1:]]
    t = max(tam(lineas), 9)
    comun = f'text-anchor="middle" font-family="Barlow, Arial, sans-serif" font-size="{t:.1f}" font-weight="600" fill="#6f6857"'
    if len(lineas) == 1:
        return f'<text x="{cx:.1f}" y="928" {comun}>{escape(texto)}</text>'
    return (f'<text x="{cx:.1f}" y="{928 - t * .55:.1f}" {comun}>{escape(lineas[0])}'
            f'<tspan x="{cx:.1f}" dy="{t * 1.1:.1f}">{escape(lineas[1])}</tspan></text>')

def dibujar_lamina(clave, grupos=None, usadas=None, titulo=None):
    """Dibujo de una lámina con su franja de tornillería.

    grupos: (('h_arandela', 3), ...) = grupos de la franja y cuántos números lleva cada uno (None = todos, uno c/u).
    Devuelve dict con svg, puestos (punto de la etiqueta de cada pieza del dibujo), anclas (punto de la pieza),
    casillas ({grupo: [(x, y), ...]} un lugar por número en la franja) y alto (fin del área del dibujo). Todo en 0..1.
    """
    nombre = nombre_dibujo(clave)
    funcion = lambda: _construir(clave)
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
                         + _rotulo_columna(nombres[g], cx, ancho))
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
        f'<text x="62" y="972" font-family="Oswald, Barlow, Arial, sans-serif" font-size="{_letra_rotulo(titulo or nombre)}"'
        f' font-weight="700" letter-spacing="1" fill="#2b3134">{escape(_texto_rotulo(titulo or nombre))}</text>'
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
        formas = [q.formas for q in _construir(clave)[0] if q.puesto == puesto or (q.puesto is None and q.padre == puesto)]
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


# ---------------------------------------------------------------------------
# Kits: un repuesto que trae varias piezas del dibujo ("Kit resorte y arandela válvulas" = resortes, asientos, platillos
# y cuñas). (palabras, puestos que trae, débil): una palabra débil (el nombre del sistema: "válvulas") solo cuenta si
# ninguna otra dijo qué trae el kit. Puestos vacíos = no es un kit de piezas dibujadas (arandelas de ajuste).
# ---------------------------------------------------------------------------
_KIT_ARRASTRE = [(("AJUSTE", "REPARACION"), (), False), (("SPROCKET", "CORONA", "PINON"), ("corona", "pinon"), False),
                 (("CADENA",), ("cadena",), False), (("CAUCHO",), ("cauchos",), False),
                 (("BALINERA", "RODAMIENTO"), ("rodamientos",), False), (("RETEN",), ("retenedores", "reten"), False)]
KITS = {
    "valvulas": [(("AJUSTE",), (), False),
                 (("REPARACION",), ("valvula_admision", "valvula_escape", "sello", "resortes", "base_resorte", "platillo", "cunas"), False),
                 (("RESORTE",), ("resortes", "base_resorte", "platillo", "cunas"), False),
                 (("ARANDELA",), ("base_resorte", "platillo"), False), (("CUNA", "SEGURO"), ("cunas",), False),
                 (("RETEN", "SELLO", "GORRO"), ("sello",), False), (("VALVULA",), ("valvula_admision", "valvula_escape"), True)],
    "rueda_trasera": _KIT_ARRASTRE, "rueda_tambor": _KIT_ARRASTRE, "transmision": _KIT_ARRASTRE,
    "culata": [(("PISTON",), ("piston", "anillos", "pasador", "seguros_piston"), False), (("ANILLO", "RING"), ("anillos",), False)],
    "distribucion": [(("GUIA", "GUIAS", "GUIDE"), ("guia_cadenilla", "guia_tensor"), False)],
    "cilindro_piston": [(("PISTON",), ("piston", "anillos", "pasador", "seguros_piston"), False), (("ANILLO", "RING"), ("anillos",), False)],
    "suspension_delantera": [(("CUNA",), ("rodamientos_direccion", "tazas"), False), (("RETEN",), ("retenedor", "guardapolvo"), False)],
    "freno_disco": [(("PAD", "PASTILLA"), ("pastillas", "resorte_pastillas"), False), (("GUARDAPOLVO",), ("guardapolvo",), False),
                    (("SEAL", "RETEN", "EMPAQUE"), ("empaques",), False), (("PISTON",), ("piston",), False),
                    (("BLEED", "PURGA"), ("purgador",), False)],
    "freno_completo": [(("PAD", "PASTILLA"), ("pastillas",), False), (("GUARDAPOLVO",), ("guardapolvo",), False),
                       (("RETEN", "SEAL"), ("empaques",), False), (("PISTON",), ("piston", "embolo"), False)],
}
# Lo que se ve tenue junto al kit, para entender dónde va (los resortes y las cuñas van en la válvula)
KIT_CONTEXTO = {"valvulas": ("valvula_admision", "valvula_escape")}


def puestos_kit(clave, descripcion):
    """('valvulas', 'Kit Resorte y Arandela Válvulas') → ('base_resorte', 'cunas', 'platillo', 'resortes'); None si no es kit."""
    texto = _sin_tildes((descripcion or "").upper())
    reglas = KITS.get(_base(clave))
    if not reglas or not re.search(r"\bKIT\b", texto):
        return None
    existentes = dibujar_lamina(clave, ())["puestos"]
    fuertes, debiles, vacio = set(), set(), False
    for palabras, puestos, debil in reglas:
        if any(_palabra(p, texto) for p in palabras):
            if not puestos:
                vacio = True
            (debiles if debil else fuertes).update(p for p in puestos if p in existentes)
    elegidos = fuertes or debiles
    if vacio or not elegidos or (len(elegidos) == 1 and clave not in KIT_CONTEXTO):
        return None                          # una sola pieza: basta su propio dibujo
    return tuple(sorted(elegidos))


def clave_kit(clave, puestos):
    """Puestos del kit → texto para la dirección del dibujo: 'cunas-platillo-resortes--valvula_admision-valvula_escape'."""
    contexto = [p for p in KIT_CONTEXTO.get(_base(clave), ()) if p not in puestos]
    return "-".join(puestos) + ("--" + "-".join(contexto) if contexto else "")


def dibujar_kit(clave, texto):
    """Las piezas de un kit en su lugar del conjunto (lo de contexto, tenue), con el mismo encuadre de la guía."""
    propios, _, contexto = texto.partition("--")
    propios, contexto = set(propios.split("-")), set(filter(None, contexto.split("-")))
    piezas = []
    for q in _construir(clave)[0]:
        dueno = q.puesto or q.padre
        if dueno in propios or dueno in contexto:
            formas = [f for f in q.formas if f.anillos]
            if formas:
                sola = Pieza(None, None)            # sin puesto: sin números ni líneas guía
                sola.agregar(*formas)
                sola.contexto = dueno not in propios
                piezas.append(sola)
    if not any(not getattr(p, "contexto", False) for p in piezas):
        return None
    lado = 600
    cuerpo, _ = iso.componer(piezas, [], lado, margen=110, transparencia=False)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}" width="{lado}" height="{lado}">'
            '<defs><pattern id="cuadricula" width="30" height="30" patternUnits="userSpaceOnUse">'
            '<path d="M30 0H0V30" fill="none" stroke="#ece6d8" stroke-width="1"/></pattern></defs>'
            f'<rect width="{lado}" height="{lado}" fill="#fdfcf8"/><rect width="{lado}" height="{lado}" fill="url(#cuadricula)"/>'
            f'{cuerpo}</svg>')


def version_pieza(clave, puesto):
    """Huella del dibujo de una pieza sola (la guía): cambia la dirección cuando cambia el dibujo, así no se ve la vieja."""
    svg = dibujar_kit(clave, puesto) if "-" in puesto else dibujar_pieza(clave, puesto)
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
