"""Motor mínimo de dibujo isométrico para diagramas de despiece estilo manual técnico.

Cada pieza se describe como un sólido 3D sencillo (cilindro, prisma, caja, resorte...). El motor
proyecta en isométrico, calcula la silueta (envolvente convexa), dibuja la cara visible y ordena las
piezas por profundidad. Todo se emite como SVG de línea (contorno negro, rellenos claros).

Ejes del mundo: x hacia abajo-derecha, z hacia abajo-izquierda, y hacia arriba (vertical en pantalla).
"""
import math

COS30 = math.cos(math.radians(30))
VISTA = (1 / math.sqrt(3),) * 3  # dirección hacia el observador

# Estilo
TINTA = "#1d2427"
BLANCO = "#ffffff"
LADO_CLARO = "#eef0f0"
LADO_MEDIO = "#dfe3e4"
OSCURO = "#9aa3a7"
CAUCHO = "#4a5154"
CAUCHO_CARA = "#626a6d"
HUECO = "#e3ddd0"
ROJO = "#e7a08f"
FRICCION = "#cdb79a"
RESORTE = "#f2d18a"


# ---------------------------------------------------------------------------
# Álgebra básica
# ---------------------------------------------------------------------------
def _sum(*vs):
    return tuple(sum(c) for c in zip(*vs))


def _mul(v, k):
    return tuple(c * k for c in v)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    n = math.sqrt(_dot(v, v)) or 1
    return tuple(c / n for c in v)


def proyectar(p):
    x, y, z = p
    return ((x - z) * COS30, -y + (x + z) * 0.5)


def base(eje):
    """Base ortonormal (u, v) perpendicular al eje; v apunta lo más "arriba" posible."""
    a = _norm(eje)
    if abs(a[1]) > 0.95:
        u, v = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    else:
        v = _norm(_sum((0, 1, 0), _mul(a, -a[1])))
        u = _norm(_cross(v, a))
    return a, u, v


def envolvente(puntos):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in puntos))
    if len(pts) < 3:
        return pts

    def cruz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    inf, sup = [], []
    for p in pts:
        while len(inf) >= 2 and cruz(inf[-2], inf[-1], p) <= 0:
            inf.pop()
        inf.append(p)
    for p in reversed(pts):
        while len(sup) >= 2 and cruz(sup[-2], sup[-1], p) <= 0:
            sup.pop()
        sup.append(p)
    return inf[:-1] + sup[:-1]


# ---------------------------------------------------------------------------
# Formas 2D intermedias (se transforman al final al lienzo)
# ---------------------------------------------------------------------------
class Forma:
    __slots__ = ("anillos", "relleno", "grosor", "trazo", "guiones", "abierta", "clase")

    def __init__(self, anillos, relleno=BLANCO, grosor=2.0, trazo=TINTA, guiones=None, abierta=False, clase=""):
        self.anillos = anillos  # lista de listas de puntos 2D (varios = con huecos, evenodd)
        self.relleno, self.grosor, self.trazo = relleno, grosor, trazo
        self.guiones, self.abierta, self.clase = guiones, abierta, clase


class Pieza:
    """Conjunto de formas con una profundidad (para ordenar) y un ancla para su número."""

    def __init__(self, puesto=None, ancla=None, etiqueta=None, orden=None, padre=None):
        self.formas, self.puesto, self.ancla3d, self.etiqueta = [], puesto, ancla, etiqueta
        self.padre = padre  # pieza sin número que pertenece a otra (p. ej. los tornillos del disco): se va con ella
        self.orden = orden  # fuerza el orden de dibujo (mayor = más adelante)
        self.profundidad = 0.0

    def agregar(self, *formas):
        self.formas.extend(formas)
        return self


def _circulo(c, u, v, r, n=48, giro=0.0):
    return [_sum(c, _mul(u, math.cos(giro + t * 2 * math.pi / n) * r), _mul(v, math.sin(giro + t * 2 * math.pi / n) * r))
            for t in range(n)]


def _contorno(c, u, v, puntos2d):
    return [_sum(c, _mul(u, x), _mul(v, y)) for x, y in puntos2d]


def _p2(puntos3d):
    return [proyectar(p) for p in puntos3d]


# ---------------------------------------------------------------------------
# Sólidos
# ---------------------------------------------------------------------------
def prisma(centro, eje, contorno, largo, hueco=None, lado=LADO_CLARO, cara=BLANCO, hueco_color=HUECO, grosor=2.0):
    """Extrusión de un contorno 2D (en el plano u,v) a lo largo del eje. `hueco` = contorno interior opcional."""
    a, u, v = base(eje)
    e0, e1 = _sum(centro, _mul(a, -largo / 2)), _sum(centro, _mul(a, largo / 2))
    frente, atras = (e1, e0) if _dot(a, VISTA) >= 0 else (e0, e1)
    c_frente, c_atras = _contorno(frente, u, v, contorno), _contorno(atras, u, v, contorno)
    formas = [Forma([envolvente(_p2(c_frente + c_atras))], lado, grosor)]
    anillos = [_p2(c_frente)]
    if hueco:
        anillos.append(_p2(_contorno(frente, u, v, hueco)))
    formas.append(Forma(anillos, cara, grosor))
    if hueco:
        formas.append(Forma([_p2(_contorno(frente, u, v, hueco))], hueco_color, grosor * 0.6))
    return formas


def _mezcla(c1, c2, t):
    """Color entre c1 y c2 (#rrggbb), t = 0..1."""
    a, b = int(c1[1:], 16), int(c2[1:], 16)
    canal = lambda x, y: round(x + (y - x) * t)
    return "#%02x%02x%02x" % tuple(canal((a >> s) & 255, (b >> s) & 255) for s in (16, 8, 0))


LUZ = _norm((-0.35, 0.85, 0.4))  # luz de estudio: arriba y un poco a la izquierda


def _brillo_lateral(e0, e1, u, v, r0, r1, a, lado):
    """Franja de brillo y franja de sombra sobre el costado de un cilindro: lo hace ver metálico y redondo."""
    if not lado.startswith("#") or len(lado) != 7:
        return []
    visibles = []
    for i in range(96):
        t = i * 2 * math.pi / 96
        normal = _sum(_mul(u, math.cos(t)), _mul(v, math.sin(t)))
        if _dot(normal, VISTA) > 0.08:
            visibles.append((t, _dot(normal, LUZ)))
    if len(visibles) < 8:
        return []

    def franja(t0, t1, color):
        angulos = [t0 + (t1 - t0) * k / 6 for k in range(7)]
        frente = [_sum(e1, _mul(u, math.cos(t) * r1), _mul(v, math.sin(t) * r1)) for t in angulos]
        atras = [_sum(e0, _mul(u, math.cos(t) * r0), _mul(v, math.sin(t) * r0)) for t in reversed(angulos)]
        return Forma([_p2(frente + atras)], color, 0, "none")

    claro = max(visibles, key=lambda x: x[1])[0]
    oscuro = min(visibles, key=lambda x: x[1])[0]
    return [franja(claro - 0.22, claro + 0.12, _mezcla(lado, "#ffffff", .75)),
            franja(oscuro - 0.25, oscuro + 0.25, _mezcla(lado, "#7d878b", .35))]


def cilindro(centro, eje, r, largo, ri=0.0, r2=None, n=48, giro=0.0, lado=LADO_CLARO, cara=BLANCO, hueco_color=HUECO, grosor=2.0):
    """Cilindro (o tronco de cono si r2) con agujero opcional ri."""
    a, u, v = base(eje)
    r_atras, r_frente = r, (r2 if r2 is not None else r)
    e0, e1 = _sum(centro, _mul(a, -largo / 2)), _sum(centro, _mul(a, largo / 2))
    if _dot(a, VISTA) < 0:
        e0, e1 = e1, e0
        r_atras, r_frente = r_frente, r_atras
    c_atras, c_frente = _circulo(e0, u, v, r_atras, n, giro), _circulo(e1, u, v, r_frente, n, giro)
    formas = [Forma([envolvente(_p2(c_frente + c_atras))], lado, grosor)]
    # Brillo y sombra en el costado, solo si el costado se ve lo suficiente
    if min(r_atras, r_frente) >= 5 and largo >= 4:
        formas += _brillo_lateral(e0, e1, u, v, r_atras, r_frente, a, lado)
    anillos = [_p2(c_frente)]
    if ri:
        anillos.append(_p2(_circulo(e1, u, v, ri, n)))
    formas.append(Forma(anillos, cara, grosor))
    # Chaflán en la cara: un aro fino junto al borde, como una pieza mecanizada
    if r_frente >= 16 and cara.startswith("#") and len(cara) == 7:
        formas.append(Forma([_p2(_circulo(e1, u, v, r_frente * 0.9, n))], "none", 1.0, _mezcla(cara, "#7d878b", .35)))
    if ri:
        formas.append(Forma([_p2(_circulo(e1, u, v, ri, n))], hueco_color, grosor * 0.6))
    return formas


def caja(centro, dims, ejes=((1, 0, 0), (0, 1, 0), (0, 0, 1)), colores=(LADO_MEDIO, BLANCO, LADO_CLARO), grosor=2.0):
    """Caja orientada: dims = (dx, dy, dz) a lo largo de los tres ejes dados. Dibuja las tres caras visibles."""
    ex, ey, ez = (_norm(e) for e in ejes)
    hx, hy, hz = (d / 2 for d in dims)
    formas = []
    caras = [(ex, hx, ey, hy, ez, hz, colores[0]), (ey, hy, ex, hx, ez, hz, colores[1]), (ez, hz, ex, hx, ey, hy, colores[2])]
    for n, hn, p, hp, q, hq, color in caras:
        signo = 1 if _dot(n, VISTA) >= 0 else -1
        c = _sum(centro, _mul(n, signo * hn))
        esquinas = [_sum(c, _mul(p, sp * hp), _mul(q, sq * hq)) for sp, sq in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        formas.append(Forma([_p2(esquinas)], color, grosor))
    return formas


def resorte(centro, eje, r, largo, vueltas=8, grosor_alambre=4.0, color=RESORTE):
    a, u, v = base(eje)
    inicio = _sum(centro, _mul(a, -largo / 2))
    pts = []
    n = vueltas * 24
    for i in range(n + 1):
        t = i / n
        ang = t * vueltas * 2 * math.pi
        pts.append(_sum(inicio, _mul(a, t * largo), _mul(u, math.cos(ang) * r), _mul(v, math.sin(ang) * r)))
    linea = _p2(pts)
    return [Forma([linea], "none", grosor_alambre + 2.5, TINTA, abierta=True),
            Forma([linea], "none", grosor_alambre, color, abierta=True)]


def linea(p1, p2, guiones="14 6 3 6", grosor=1.4, color="#8f9597"):
    """Línea de eje de montaje (trazo y punto, como en los manuales)."""
    return Forma([_p2([p1, p2])], "none", grosor, color, guiones=guiones, abierta=True)


def polilinea(puntos3d, grosor=2.0, color=TINTA, guiones=None):
    return Forma([_p2(puntos3d)], "none", grosor, color, guiones=guiones, abierta=True)


def roscas(centro, eje, r, largo, paso=6.0):
    """Rayitas de rosca sobre un vástago."""
    a, u, v = base(eje)
    formas = []
    inicio = _sum(centro, _mul(a, -largo / 2))
    pasos = int(largo / paso)
    for i in range(1, pasos):
        c = _sum(inicio, _mul(a, i * paso))
        p1, p2 = _sum(c, _mul(v, r)), _sum(c, _mul(a, paso * 0.6), _mul(v, -r))
        formas.append(Forma([_p2([p1, p2])], "none", 1.1, TINTA, abierta=True))
    return formas


def puntos_en_cara(centro, eje, largo, radio_anillo, cantidad, r, color=HUECO):
    """Agujeros o bolitas repartidos en la cara visible de un disco."""
    a, u, v = base(eje)
    frente = _sum(centro, _mul(a, (largo / 2) * (1 if _dot(a, VISTA) >= 0 else -1)))
    formas = []
    for i in range(cantidad):
        ang = i * 2 * math.pi / cantidad
        c = _sum(frente, _mul(u, math.cos(ang) * radio_anillo), _mul(v, math.sin(ang) * radio_anillo))
        formas.append(Forma([_p2(_circulo(c, u, v, r, 16))], color, 1.2))
    return formas


# ---------------------------------------------------------------------------
# Piezas compuestas frecuentes
# ---------------------------------------------------------------------------
def hexagono(r):
    return [(math.cos(i * math.pi / 3) * r, math.sin(i * math.pi / 3) * r) for i in range(6)]


def perno(base_cabeza, eje, largo, d=8.0, cabeza=None, color_cabeza=LADO_MEDIO):
    """Tornillo: cabeza hexagonal en `base_cabeza` y vástago roscado hacia +eje."""
    a = _norm(eje)
    cab = cabeza or d * 1.6
    alto_cab = d * 0.75
    c_cab = _sum(base_cabeza, _mul(a, -alto_cab / 2))
    c_vas = _sum(base_cabeza, _mul(a, largo / 2))
    formas_vas = cilindro(c_vas, a, d / 2, largo, n=24) + roscas(c_vas, a, d / 2, largo * 0.8)
    formas_cab = prisma(c_cab, a, hexagono(cab / 2), alto_cab, lado=color_cabeza)
    # La cabeza tapa el vástago si mira hacia el observador
    return (formas_vas + formas_cab) if _dot(a, VISTA) < 0 else (formas_cab + formas_vas)


def tuerca(centro, eje, d=10.0):
    return prisma(centro, eje, hexagono(d), d * 0.8, hueco=_circ2d(d * 0.5, 24), lado=LADO_MEDIO)


def arandela(centro, eje, r, grosor=2.0, color=BLANCO, lado=LADO_CLARO):
    return cilindro(centro, eje, r, grosor, ri=r * 0.55, cara=color, lado=lado, grosor=1.6)


def oring(centro, eje, r, grosor=3.0):
    return cilindro(centro, eje, r, grosor, ri=r * 0.82, cara=CAUCHO_CARA, lado=CAUCHO, grosor=1.6)


def retenedor(centro, eje, r, ancho=7.0):
    return cilindro(centro, eje, r, ancho, ri=r * 0.62, cara=CAUCHO_CARA, lado=CAUCHO)


def rodamiento(centro, eje, r, ancho=10.0):
    formas = cilindro(centro, eje, r, ancho, ri=r * 0.45, cara=BLANCO)
    formas += puntos_en_cara(centro, eje, ancho, r * 0.72, 9, r * 0.12, color=LADO_MEDIO)
    return formas


def _circ2d(r, n=32):
    return [(math.cos(i * 2 * math.pi / n) * r, math.sin(i * 2 * math.pi / n) * r) for i in range(n)]


def redondeado(ancho, alto, radio, n=6):
    """Contorno de rectángulo con esquinas redondeadas."""
    radio = min(radio, ancho / 2, alto / 2)
    pts = []
    for cx, cy, a0 in ((ancho / 2 - radio, alto / 2 - radio, 0), (-ancho / 2 + radio, alto / 2 - radio, 90),
                       (-ancho / 2 + radio, -alto / 2 + radio, 180), (ancho / 2 - radio, -alto / 2 + radio, 270)):
        for i in range(n + 1):
            ang = math.radians(a0 + i * 90 / n)
            pts.append((cx + math.cos(ang) * radio, cy + math.sin(ang) * radio))
    return pts


def estadio(ancho, alto, n=16):
    r = alto / 2
    pts = []
    for i in range(n + 1):
        ang = -math.pi / 2 + i * math.pi / n
        pts.append((ancho / 2 - r + math.cos(ang) * r, math.sin(ang) * r))
    for i in range(n + 1):
        ang = math.pi / 2 + i * math.pi / n
        pts.append((-ancho / 2 + r + math.cos(ang) * r, math.sin(ang) * r))
    return pts


def engranaje(r, dientes=24, alto_diente=None):
    alto_diente = alto_diente or r * 0.12
    pts = []
    for i in range(dientes * 2):
        ang = i * math.pi / dientes
        rr = r if i % 2 == 0 else r - alto_diente
        pts.append((math.cos(ang) * rr, math.sin(ang) * rr))
    return pts


# ---------------------------------------------------------------------------
# Composición final
# ---------------------------------------------------------------------------
OPACIDAD_ENCIMA = 0.8   # pieza que tapa a otra: se ve un poco transparente para que se note la de abajo


def _caja2d(pieza):
    pts = [q for f in pieza.formas for anillo in f.anillos for q in anillo]
    if not pts:
        return None
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _tapa_a_otra(caja, detras):
    """¿La pieza (caja) tapa una parte importante de alguna de las de atrás? No cuenta si queda casi toda dentro de
    ella (el rin dentro de la llanta, el pistón en su cilindro): ahí no oculta nada que haga falta ver."""
    if caja is None:
        return False
    area = max((caja[2] - caja[0]) * (caja[3] - caja[1]), 1e-6)
    for otra in detras:
        if otra is None:
            continue
        ancho = min(caja[2], otra[2]) - max(caja[0], otra[0])
        alto = min(caja[3], otra[3]) - max(caja[1], otra[1])
        if ancho <= 0 or alto <= 0:
            continue
        cruce = ancho * alto
        area_otra = max((otra[2] - otra[0]) * (otra[3] - otra[1]), 1e-6)
        if cruce / area_otra > 0.08 and cruce / area < 0.85:
            return True
    return False


def componer(piezas, lineas, lado=1000, margen=95, marco=None, transparencia=True, guias_fijas=True):
    """Ajusta todo al lienzo (o al rectángulo `marco` = (x, y, ancho, alto)) y devuelve (svg_cuerpo, puestos_relativos).

    Cada pieza queda con `ancla_svg` (punto de su línea guía en el lienzo). Con `transparencia`, la pieza que tapa
    a otra que está detrás se dibuja algo transparente (como un solo bloque) para que se vea la de abajo."""
    mx, my, mw, mh = marco or (0, 0, lado, lado)
    for p in piezas:
        if p.ancla3d is None:
            pts = [q for f in p.formas for anillo in f.anillos for q in anillo]
            p.ancla2d = (sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)) if pts else (0, 0)
        else:
            p.ancla2d = proyectar(p.ancla3d)
        p.profundidad = p.orden if p.orden is not None else (_dot(p.ancla3d, VISTA) if p.ancla3d else 0)
    todos = [q for p in piezas for f in p.formas for anillo in f.anillos for q in anillo]
    todos += [q for f in lineas for anillo in f.anillos for q in anillo]
    xs, ys = [x for x, _ in todos], [y for _, y in todos]
    ancho, alto = max(xs) - min(xs), max(ys) - min(ys)
    escala = min((mw - 2 * margen) / max(ancho, 1e-6), (mh - 2 * margen) / max(alto, 1e-6))
    ox = mx + (mw - ancho * escala) / 2 - min(xs) * escala
    oy = my + (mh - alto * escala) / 2 - min(ys) * escala

    def t(pt):
        return (pt[0] * escala + ox, pt[1] * escala + oy)

    def svg_forma(f):
        if f.abierta:
            d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in map(t, f.anillos[0]))
        else:
            d = "".join("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in map(t, anillo)) + "Z" for anillo in f.anillos if anillo)
        extra = f' stroke-dasharray="{f.guiones}"' if f.guiones else ""
        regla = ' fill-rule="evenodd"' if len(f.anillos) > 1 else ""
        return (f'<path d="{d}" fill="{f.relleno}" stroke="{f.trazo}" stroke-width="{f.grosor}"'
                f' stroke-linejoin="round" stroke-linecap="round"{regla}{extra}/>')

    cuerpo = ['<g class="ejes">' + "".join(svg_forma(f) for f in lineas) + "</g>"]
    guias, puestos = [], {}
    for p in piezas:
        p.ancla_svg = t(p.ancla2d)
        caja = _caja2d(p)
        p.caja_svg = (t(caja[:2]) + t(caja[2:])) if caja else None
    detras = []
    for p in sorted(piezas, key=lambda q: q.profundidad):
        caja = _caja2d(p)
        encima = transparencia and _tapa_a_otra(caja, detras)
        opacidad = f' opacity="{OPACIDAD_ENCIMA}"' if encima else ""
        if getattr(p, "contexto", False):           # pieza sin número en esta lámina: se ve tenue, como referencia
            opacidad = ' opacity="0.42"'
        cuerpo.append(f'<g class="pieza" data-puesto="{p.puesto or ""}"{opacidad}>' + "".join(svg_forma(f) for f in p.formas) + "</g>")
        detras.append(caja)
    for p in piezas:
        if not p.puesto:
            continue
        ax, ay = t(p.ancla2d)
        p.ancla_svg = (ax, ay)
        dx, dy = p.etiqueta if p.etiqueta else (60, -55)
        lx, ly = min(lado - 30, max(30, ax + dx)), min(lado - 30, max(30, ay + dy))
        if guias_fijas:
            guias.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="{TINTA}" stroke-width="1.2"/>'
                         f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="2.6" fill="{TINTA}"/>')
        puestos[p.puesto] = (round(lx / lado, 4), round(ly / lado, 4))
    cuerpo.append('<g class="guias">' + "".join(guias) + "</g>")
    return "".join(cuerpo), puestos
