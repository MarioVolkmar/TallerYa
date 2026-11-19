"""Ilustraciones propias para los mecánicos de demostración: avatar con iniciales y dibujos de trabajos.

Se dibujan aquí con Pillow (formas simples, sin fotos de personas ni imágenes de internet) y se guardan como JPEG,
igual que las fotos que suben los mecánicos. Las usa domicilio/demo.py.
"""
import math
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

FONDO = (31, 39, 42)
REJILLA = (40, 50, 54)
CREMA = (238, 228, 210)
MOSTAZA = (227, 167, 47)
LAVA = (240, 104, 44)
GRIS = (120, 130, 134)
OSCURO = (22, 27, 29)


FUENTES = [  # con tildes y eñes: Windows (local) y Linux (servidor); si no hay ninguna, se quitan las tildes
    "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def _fuente(tam):
    for ruta in FUENTES:
        try:
            return ImageFont.truetype(ruta, tam)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=tam)
    except TypeError:  # Pillow viejo
        return ImageFont.load_default()


def _texto(f, texto):
    """La fuente por defecto de Pillow no trae tildes: en ese caso «Batería» se escribe «Bateria»."""
    if getattr(f, "path", "") in FUENTES:
        return texto
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _jpeg(img, nombre):
    salida = BytesIO()
    img.convert("RGB").save(salida, "JPEG", quality=86, optimize=True)
    return ContentFile(salida.getvalue(), name=nombre)


def avatar(iniciales, tono=0):
    """Círculo de color con iniciales y una llave inglesa pequeña (480×480)."""
    lado = 480
    colores = [(MOSTAZA, (196, 120, 24)), (LAVA, (176, 64, 26)), ((86, 160, 120), (46, 104, 76)), ((96, 140, 200), (52, 84, 140))]
    claro, oscuro = colores[tono % len(colores)]
    img = Image.new("RGB", (lado, lado), oscuro)
    d = ImageDraw.Draw(img)
    for i in range(lado):  # degradado diagonal
        t = i / lado
        color = tuple(int(claro[k] * (1 - t) + oscuro[k] * t) for k in range(3))
        d.line([(0, i), (i, 0)], fill=color, width=2)
        d.line([(i, lado), (lado, i)], fill=oscuro, width=2)
    d.ellipse([18, 18, lado - 18, lado - 18], outline=(255, 255, 255), width=6)
    texto = (iniciales or "M")[:2].upper()
    f = _fuente(190)
    caja = d.textbbox((0, 0), texto, font=f)
    d.text(((lado - (caja[2] - caja[0])) / 2 - caja[0], (lado - (caja[3] - caja[1])) / 2 - caja[1] - 30), texto,
           font=f, fill=OSCURO)
    _llave(d, lado / 2, lado * 0.78, 70, OSCURO, angulo=-35)
    return _jpeg(img, "avatar.jpg")


def _llave(d, cx, cy, largo, color, angulo=0, grosor=14):
    a = math.radians(angulo)
    dx, dy = math.cos(a) * largo, math.sin(a) * largo
    d.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=color, width=grosor)
    r = grosor * 1.3
    for sx, sy in ((cx - dx, cy - dy), (cx + dx, cy + dy)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=color)
        d.ellipse([sx - r * .45, sy - r * .45, sx + r * .45, sy + r * .45], fill=FONDO)


def _engrane(d, cx, cy, r, dientes, color):
    for i in range(dientes):
        a = 2 * math.pi * i / dientes
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        d.ellipse([x - r * .16, y - r * .16, x + r * .16, y + r * .16], fill=color)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.ellipse([cx - r * .35, cy - r * .35, cx + r * .35, cy + r * .35], fill=FONDO)


def _dibujo(d, tipo, cx, cy):
    if tipo == "aceite":
        d.polygon([(cx - 150, cy + 110), (cx - 150, cy - 30), (cx - 60, cy - 90), (cx + 90, cy - 90), (cx + 90, cy + 110)], fill=MOSTAZA)
        d.rectangle([cx + 90, cy - 50, cx + 170, cy - 20], fill=MOSTAZA)
        d.rectangle([cx - 40, cy - 125, cx + 20, cy - 90], fill=GRIS)
        d.rectangle([cx - 120, cy + 10, cx + 60, cy + 60], fill=OSCURO)
        d.text((cx - 105, cy + 18), "10W-40", font=_fuente(34), fill=MOSTAZA)
        d.polygon([(cx + 200, cy + 20), (cx + 225, cy + 70), (cx + 175, cy + 70)], fill=LAVA)
        d.ellipse([cx + 175, cy + 50, cx + 225, cy + 100], fill=LAVA)
    elif tipo == "frenos":
        d.ellipse([cx - 160, cy - 160, cx + 160, cy + 160], fill=GRIS)
        d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=FONDO)
        for i in range(12):
            a = 2 * math.pi * i / 12
            x, y = cx + math.cos(a) * 110, cy + math.sin(a) * 110
            d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=FONDO)
        d.rounded_rectangle([cx + 90, cy - 120, cx + 190, cy + 20], radius=26, fill=LAVA)
        d.text((cx + 104, cy - 70), "ABS", font=_fuente(34), fill=OSCURO)
    elif tipo == "bateria":
        d.rounded_rectangle([cx - 170, cy - 90, cx + 170, cy + 130], radius=18, fill=GRIS)
        d.rectangle([cx - 130, cy - 125, cx - 70, cy - 90], fill=LAVA)
        d.rectangle([cx + 70, cy - 125, cx + 130, cy - 90], fill=CREMA)
        f = _fuente(90)
        d.text((cx - 135, cy - 60), "+", font=f, fill=LAVA)
        d.rectangle([cx + 85, cy - 15, cx + 135, cy - 2], fill=CREMA)  # signo menos dibujado (no depende de la fuente)
        d.polygon([(cx + 10, cy - 40), (cx - 40, cy + 40), (cx, cy + 40), (cx - 20, cy + 110), (cx + 50, cy + 20), (cx + 10, cy + 20)], fill=MOSTAZA)
    elif tipo == "llanta":
        d.ellipse([cx - 170, cy - 170, cx + 170, cy + 170], fill=OSCURO, outline=GRIS, width=6)
        for i in range(24):
            a = 2 * math.pi * i / 24
            d.line([(cx + math.cos(a) * 150, cy + math.sin(a) * 150), (cx + math.cos(a) * 168, cy + math.sin(a) * 168)], fill=GRIS, width=10)
        d.ellipse([cx - 100, cy - 100, cx + 100, cy + 100], fill=GRIS)
        for i in range(5):
            a = 2 * math.pi * i / 5
            d.line([(cx, cy), (cx + math.cos(a) * 95, cy + math.sin(a) * 95)], fill=FONDO, width=14)
        d.ellipse([cx - 28, cy - 28, cx + 28, cy + 28], fill=MOSTAZA)
    elif tipo == "electrico":
        for y in (cy - 80, cy, cy + 80):
            d.line([(cx - 220, y), (cx - 80, y), (cx - 60, y - 20)], fill=REJILLA, width=8)
            d.line([(cx + 80, y), (cx + 220, y)], fill=REJILLA, width=8)
        d.polygon([(cx + 30, cy - 160), (cx - 90, cy + 20), (cx - 10, cy + 20), (cx - 40, cy + 160), (cx + 90, cy - 30), (cx + 10, cy - 30)], fill=MOSTAZA)
    elif tipo == "arrastre":
        _engrane(d, cx - 130, cy, 90, 14, GRIS)
        _engrane(d, cx + 150, cy, 55, 10, GRIS)
        for dy in (-92, 92):
            d.line([(cx - 130, cy + dy), (cx + 150, cy + dy * 0.62)], fill=LAVA, width=12)
    elif tipo == "diagnostico":
        d.rounded_rectangle([cx - 150, cy - 140, cx + 150, cy + 150], radius=26, fill=GRIS)
        d.rectangle([cx - 120, cy - 110, cx + 120, cy + 30], fill=OSCURO)
        puntos = [(cx - 110, cy - 30), (cx - 50, cy - 30), (cx - 30, cy - 90), (cx, cy + 10), (cx + 25, cy - 50), (cx + 50, cy - 30), (cx + 110, cy - 30)]
        d.line(puntos, fill=MOSTAZA, width=6)
        for i, color in enumerate((LAVA, MOSTAZA, CREMA)):
            d.ellipse([cx - 80 + i * 60, cy + 70, cx - 50 + i * 60, cy + 100], fill=color)
        d.line([(cx + 150, cy + 100), (cx + 230, cy + 160)], fill=CREMA, width=10)
    else:  # mantenimiento general
        _llave(d, cx, cy, 150, MOSTAZA, angulo=40, grosor=26)
        _llave(d, cx, cy, 150, CREMA, angulo=-40, grosor=26)


TIPOS = {  # servicio de domicilio → dibujo
    "Cambio de aceite": "aceite", "Frenos": "frenos", "Batería y arranque": "bateria", "Llantas y despinche": "llanta",
    "Sistema eléctrico": "electrico", "Inyección electrónica": "diagnostico", "Diagnóstico": "diagnostico",
    "Kit de arrastre": "arrastre", "Mantenimiento general": "general", "Carburación": "general",
    "Suspensión": "general", "Revisión antes de comprar moto usada": "diagnostico",
}


def trabajo(servicio):
    """Ilustración de un trabajo (960×720) con el nombre del servicio abajo."""
    ancho, alto = 960, 720
    img = Image.new("RGB", (ancho, alto), FONDO)
    d = ImageDraw.Draw(img)
    for x in range(0, ancho, 48):
        d.line([(x, 0), (x, alto)], fill=REJILLA, width=1)
    for y in range(0, alto, 48):
        d.line([(0, y), (ancho, y)], fill=REJILLA, width=1)
    _dibujo(d, TIPOS.get(servicio, "general"), ancho / 2, alto / 2 - 40)
    d.rectangle([0, alto - 110, ancho, alto], fill=OSCURO)
    f = _fuente(44)
    d.text((40, alto - 82), _texto(f, servicio), font=f, fill=CREMA)
    f = _fuente(26)
    d.text((ancho - 210, alto - 70), _texto(f, "Ilustración"), font=f, fill=GRIS)
    return _jpeg(img, "trabajo.jpg")
