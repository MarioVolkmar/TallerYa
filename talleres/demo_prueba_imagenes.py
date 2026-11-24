"""Ilustraciones propias (Pillow) para el juego de cuentas de prueba: fachada de taller e interior con moto en elevador.

Todo se dibuja aquí (formas simples, colores de marca): sin fotos de personas ni descargas de terceros.
Las usa talleres/demo_prueba.py (comando preparar_demo_prueba).
"""
from domicilio.ilustraciones import CREMA, FONDO, GRIS, LAVA, MOSTAZA, OSCURO, _fuente, _jpeg, _llave, _texto
from PIL import Image, ImageDraw

PALETAS = [  # (cielo arriba, cielo abajo, muro, toldo)
    ((250, 214, 160), (240, 150, 96), (70, 82, 88), LAVA),
    ((176, 214, 240), (230, 240, 250), (92, 70, 62), MOSTAZA),
    ((196, 186, 232), (244, 206, 190), (58, 84, 78), (86, 160, 120)),
]


def _degradado(img, arriba, abajo, hasta):
    d = ImageDraw.Draw(img)
    for y in range(hasta):
        t = y / max(1, hasta)
        d.line([(0, y), (img.width, y)], fill=tuple(int(arriba[k] * (1 - t) + abajo[k] * t) for k in range(3)))


def _moto(d, cx, cy, e, color):
    """Moto de perfil: dos ruedas, chasis, tanque, asiento, manubrio y farola."""
    r = int(62 * e)
    for x in (cx - int(135 * e), cx + int(135 * e)):
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=OSCURO)
        d.ellipse([x - int(r * 0.62), cy - int(r * 0.62), x + int(r * 0.62), cy + int(r * 0.62)], outline=GRIS, width=max(2, int(5 * e)))
        d.ellipse([x - int(8 * e), cy - int(8 * e), x + int(8 * e), cy + int(8 * e)], fill=GRIS)
    g = max(3, int(10 * e))
    d.line([(cx - int(135 * e), cy), (cx - int(20 * e), cy - int(60 * e)), (cx + int(70 * e), cy - int(48 * e))], fill=color, width=g)
    d.line([(cx + int(70 * e), cy - int(48 * e)), (cx + int(135 * e), cy)], fill=GRIS, width=g)
    d.polygon([(cx - int(10 * e), cy - int(70 * e)), (cx + int(70 * e), cy - int(76 * e)), (cx + int(80 * e), cy - int(48 * e)),
               (cx, cy - int(44 * e))], fill=color)
    d.rounded_rectangle([cx - int(100 * e), cy - int(76 * e), cx - int(20 * e), cy - int(60 * e)], radius=int(6 * e), fill=OSCURO)
    d.line([(cx + int(78 * e), cy - int(52 * e)), (cx + int(92 * e), cy - int(96 * e)), (cx + int(70 * e), cy - int(100 * e))], fill=GRIS, width=g)
    d.ellipse([cx + int(94 * e), cy - int(80 * e), cx + int(114 * e), cy - int(62 * e)], fill=MOSTAZA)


def fachada(nombre, tono=0):
    """Fachada del taller con letrero, toldo, persiana y una moto al frente (1280×800)."""
    cielo1, cielo2, muro, toldo = PALETAS[tono % len(PALETAS)]
    ancho, alto = 1280, 800
    img = Image.new("RGB", (ancho, alto), cielo1)
    _degradado(img, cielo1, cielo2, 520)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 600, ancho, alto], fill=(58, 62, 64))
    d.rectangle([0, 590, ancho, 610], fill=(150, 150, 146))
    d.rectangle([150, 150, 1130, 600], fill=muro)
    d.rectangle([150, 130, 1130, 160], fill=OSCURO)
    d.rounded_rectangle([260, 170, 1020, 270], radius=14, fill=OSCURO, outline=toldo, width=6)
    f = _fuente(58 if len(nombre) < 22 else 44)
    caja = d.textbbox((0, 0), _texto(f, nombre), font=f)
    d.text(((ancho - (caja[2] - caja[0])) / 2 - caja[0], 220 - (caja[3] - caja[1]) / 2 - caja[1]), _texto(f, nombre), font=f, fill=CREMA)
    for i, x in enumerate(range(200, 1080, 80)):  # toldo a rayas
        d.polygon([(x, 290), (x + 80, 290), (x + 96, 350), (x - 16, 350)], fill=toldo if i % 2 == 0 else CREMA)
    d.rectangle([200, 360, 760, 590], fill=(30, 36, 38))  # persiana
    for y in range(366, 590, 16):
        d.line([(200, y), (760, y)], fill=(44, 52, 55), width=3)
    d.rectangle([800, 380, 1080, 590], fill=(236, 226, 206))  # vitrina y puerta
    d.rectangle([815, 395, 940, 520], fill=(130, 190, 210))
    d.rectangle([955, 395, 1065, 590], fill=(34, 40, 42))
    d.ellipse([1048, 490, 1060, 502], fill=MOSTAZA)
    _moto(d, 560, 690, 1.15, toldo)
    return _jpeg(img, "fachada.jpg")


def interior(tono=0):
    """Interior: panel de herramientas en la pared y una moto sobre el elevador (1280×800)."""
    _, _, muro, toldo = PALETAS[tono % len(PALETAS)]
    ancho, alto = 1280, 800
    img = Image.new("RGB", (ancho, alto), FONDO)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, ancho, 560], fill=muro)
    for x in range(0, ancho, 64):
        d.line([(x, 0), (x, 560)], fill=tuple(max(0, c - 14) for c in muro), width=2)
    d.rectangle([0, 560, ancho, alto], fill=(52, 56, 58))
    d.rectangle([90, 70, 640, 330], fill=(40, 46, 48), outline=OSCURO, width=8)  # panel de herramientas
    for i in range(7):
        _llave(d, 140 + i * 72, 200, 150, CREMA if i % 2 else MOSTAZA, angulo=90, grosor=12)
    d.rectangle([700, 90, 1180, 280], fill=(36, 42, 44))  # estante con aceites
    for i in range(6):
        d.rounded_rectangle([722 + i * 74, 150, 772 + i * 74, 262], radius=8, fill=toldo if i % 2 == 0 else CREMA)
    d.rectangle([330, 560, 1000, 590], fill=(120, 126, 130))  # elevador
    d.rectangle([380, 590, 400, 700], fill=(120, 126, 130))
    d.rectangle([930, 590, 950, 700], fill=(120, 126, 130))
    _moto(d, 660, 500, 1.3, toldo)
    return _jpeg(img, "interior.jpg")
