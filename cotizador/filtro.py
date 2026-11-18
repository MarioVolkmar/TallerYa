"""Quita de los resultados lo que no es la pieza: accesorios y basura, otra pieza, otra moto y precios atípicos.

Reglas (en este orden):
1. Palabras prohibidas en el título (llavero, calcomanía, juguete, lote, «para carro»…).
2. La primera palabra con sentido del nombre de la pieza (o un sinónimo) debe estar en el título, salvo que el
   título traiga el código de repuesto exacto. «Pastillas de freno» exige «pastilla»; «Filtro de aceite», «filtro».
3. Si el título nombra otra línea de moto y no la nuestra (ni el código), se descarta.
4. Precios atípicos: fuera de [mediana × 0,35, mediana × 2,8] y, con 5 o más precios, fuera de las vallas de Tukey.
Lo que trae el código o la línea de la moto sube al principio de la lista.
"""
import re
import statistics
import unicodedata

PROHIBIDAS = [
    "llavero", "calcomania", "sticker", "adhesivo", "juguete", "miniatura", "a escala", "manual de", "libro",
    "camiseta", "gorra", "lote", "mayorista", "x10", "x20", "x50", "para carro", "para auto", "camioneta",
    "automovil", "bicicleta", "patineta", "scooter electrico", "cuatrimoto", "dibujo", "poster", "afiche",
]
VACIAS = {"de", "del", "la", "el", "los", "las", "para", "con", "y", "o", "en", "a", "juego", "conjunto", "set",
          "kit", "par", "completo", "completa", "nuevo", "nueva", "original", "moto", "comp", "assy"}
SINONIMOS = {
    "pastill": ["pastill", "pasta"], "zapata": ["zapat", "banda"], "correa": ["correa", "banda"],
    "arrast": ["arrast", "cadena", "pinon", "sproc"], "bujia": ["bujia"], "empaqu": ["empaq", "junta", "sello"],
    "rodami": ["rodami", "balin", "balinera"], "llanta": ["llanta", "neumat"],
}


def normal(texto):
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ\- ]", " ", t)).strip()


def _sin_guiones(texto):
    return re.sub(r"[\s\-]", "", normal(texto))


def raiz(palabra):
    return palabra[:6] if len(palabra) > 6 else palabra


def palabra_clave(nombre):
    """Raíz de la primera palabra con sentido del nombre («Kit de arrastre» → «arrast»)."""
    for p in normal(nombre).split():
        if p not in VACIAS and len(p) >= 4 and not p.isdigit():
            return raiz(p)
    return ""


def _contiene_palabra(titulo, palabra):
    return re.search(rf"\b{re.escape(palabra)}", titulo) is not None


def filtrar(resultados, nombre="", codigo="", linea="", otras_lineas=()):
    """Devuelve (aceptados, descartes); cada descarte es (resultado, motivo)."""
    clave = palabra_clave(nombre)
    variantes = SINONIMOS.get(clave, [clave]) if clave else []
    cod = _sin_guiones(codigo) if len(_sin_guiones(codigo)) >= 6 else ""
    linea_n = normal(linea)
    tokens_linea = [t for t in linea_n.split() if len(t) >= 3 and not t.isdigit()] or linea_n.split()
    otras = [normal(o) for o in otras_lineas if normal(o) and normal(o) != linea_n]

    aceptados, descartes = [], []
    for r in resultados:
        t = normal(r.get("titulo"))
        trae_codigo = bool(cod) and cod in _sin_guiones(r.get("titulo"))
        nuestra = trae_codigo or any(_contiene_palabra(t, x) for x in tokens_linea)
        prohibida = next((p for p in PROHIBIDAS if p in t), None)
        if prohibida:
            descartes.append((r, f"no es un repuesto («{prohibida}»)"))
        elif variantes and not trae_codigo and not any(_contiene_palabra(t, v) for v in variantes):
            descartes.append((r, "es otra pieza"))
        elif not nuestra and any(_contiene_palabra(t, o.split()[0]) for o in otras if o.split()):
            descartes.append((r, "es de otra moto"))
        else:
            aceptados.append(dict(r, compatible=nuestra))

    aceptados, atipicos = _sin_atipicos(aceptados)
    descartes += [(r, "precio atípico") for r in atipicos]
    aceptados.sort(key=lambda r: (not r["compatible"], r["precio"]))
    return aceptados, descartes


def _sin_atipicos(resultados):
    if len(resultados) < 3:
        return resultados, []
    precios = sorted(r["precio"] for r in resultados)
    m = statistics.median(precios)
    bajo, alto = m * 0.35, m * 2.8
    if len(precios) >= 5:
        q1, _, q3 = statistics.quantiles(precios, n=4)
        rango = q3 - q1
        if rango > 0:  # con casi todos los precios iguales, las vallas quitarían precios normales
            bajo, alto = max(bajo, q1 - 1.5 * rango), min(alto, q3 + 1.5 * rango)
    buenos = [r for r in resultados if bajo <= r["precio"] <= alto]
    return buenos, [r for r in resultados if not bajo <= r["precio"] <= alto]


def resumen(aceptados):
    """Mínimo, típico (mediana) y máximo."""
    if not aceptados:
        return None, None, None
    precios = [r["precio"] for r in aceptados]
    return min(precios), int(statistics.median(precios)), max(precios)
