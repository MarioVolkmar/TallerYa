"""Resultados de EJEMPLO para cuando no hay token de Mercado Libre: el piloto se puede ver y probar igual, y la
interfaz lo dice claramente («Precios de ejemplo»). Son deterministas (mismo texto → mismos precios) e incluyen
basura a propósito (accesorios, otra moto, un precio absurdo) para que se vea el filtro trabajando."""
import hashlib
import urllib.parse

# Rango de referencia por tipo de pieza (COP, aproximado, solo para la demostración).
RANGOS = [
    (("pastilla", "pad"), (22_000, 65_000)),
    (("kit de arrastre", "kit arrastre", "cadena", "piñón", "pinon", "sprocket"), (110_000, 260_000)),
    (("filtro de aceite", "filtro aceite", "oil filter"), (12_000, 32_000)),
    (("filtro de aire", "filtro aire", "air filter", "elemento"), (25_000, 70_000)),
    (("bujía", "bujia", "spark plug"), (15_000, 45_000)),
    (("correa", "belt"), (90_000, 220_000)),
    (("llanta", "tire"), (150_000, 380_000)),
]
CIUDADES = ["Medellín, Antioquia", "Itagüí, Antioquia", "Bogotá D.C.", "Envigado, Antioquia", "Cali, Valle del Cauca",
            "Bello, Antioquia", "Barranquilla, Atlántico"]


def _rango(texto):
    t = texto.lower()
    for claves, rango in RANGOS:
        if any(c in t for c in claves):
            return rango
    return (30_000, 120_000)


def buscar(texto, limite=50, pista=""):
    """`pista`: nombre de la pieza, para el rango de precios y el título (la consulta puede ser solo el código)."""
    semilla = int(hashlib.md5(texto.encode()).hexdigest(), 16)
    bajo, alto = _rango(f"{pista} {texto}")
    nombre = f"{pista} {texto}" if pista and pista.lower() not in texto.lower() else texto
    enlace = "https://listado.mercadolibre.com.co/" + urllib.parse.quote(texto.lower().replace(" ", "-"))
    salida = []
    for i in range(9):
        paso = (semilla >> (i * 7)) % 1000 / 1000
        salida.append({
            "titulo": f"{nombre} {'original' if i % 3 == 0 else 'alta calidad' if i % 3 == 1 else 'genérico'}",
            "precio": int(round((bajo + (alto - bajo) * paso) / 100) * 100),
            "enlace": enlace, "ciudad": CIUDADES[i % len(CIUDADES)], "vendedor": f"Vendedor de ejemplo {i + 1}",
            "condicion": "new",
        })
    salida += [  # basura que el filtro debe quitar
        {"titulo": f"Llavero metálico {nombre}", "precio": 9_900, "enlace": enlace, "ciudad": CIUDADES[0],
         "vendedor": "Accesorios", "condicion": "new"},
        {"titulo": f"Calcomanía sticker {nombre}", "precio": 7_500, "enlace": enlace, "ciudad": CIUDADES[2],
         "vendedor": "Stickers", "condicion": "new"},
        {"titulo": f"{nombre} lote x20 mayorista", "precio": alto * 12, "enlace": enlace, "ciudad": CIUDADES[4],
         "vendedor": "Mayorista", "condicion": "new"},
    ]
    return salida[:limite]
