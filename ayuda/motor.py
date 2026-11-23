"""Motor del chat de Chispa.

Hoy responde con las preguntas prehechas de faq.json y un buscador por palabras clave.
Para conectar un modelo de IA después, basta con cambiar `responder()` para que, cuando el
buscador no encuentre nada (o siempre), llame al modelo y devuelva un dict con la MISMA forma:

    {
      "fuente": "faq" | "ia" | "sin_respuesta",
      "id": "km-estimado" | None,
      "pregunta": "¿Cómo calcula TallerYa el kilometraje?",
      "respuesta": ["Párrafo 1.", "Párrafo 2."],
      "acciones": [{"texto": "Ver mi plan", "url": "/garaje/3/"}],
      "relacionadas": [{"id": "lo-urgente", "pregunta": "¿Qué es «Lo urgente»?"}],
    }
"""
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from django.urls import NoReverseMatch, reverse

RUTA_FAQ = Path(__file__).with_name("faq.json")

# Palabras que no ayudan a encontrar la pregunta.
VACIAS = {
    "a", "al", "algo", "como", "con", "cual", "cuando", "de", "del", "donde", "el", "en", "es", "esta", "este",
    "hay", "la", "las", "le", "lo", "los", "me", "mi", "mis", "o", "para", "por", "puedo", "que", "se", "si",
    "su", "sus", "te", "tengo", "un", "una", "uno", "y", "ya", "yo", "hacer", "hago", "quiero", "necesito",
    "chispa", "tallerya", "favor", "hola", "ayuda", "ayudame", "sirve", "funciona",
}


@lru_cache(maxsize=1)
def datos():
    return json.loads(RUTA_FAQ.read_text(encoding="utf-8"))


SALUDOS = {"hola", "holaa", "ola", "hey", "buenas", "buenos dias", "buenas tardes", "buenas noches", "buen dia", "que mas", "quiubo"}


def normalizar(texto):
    """Minúsculas, sin tildes ni signos: «¿Cuándo vence el SOAT?» → «cuando vence el soat»."""
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def _palabras(texto):
    return [p for p in normalizar(texto).split() if p not in VACIAS and len(p) > 1]


def _raiz(palabra):
    """Raíz muy simple para tolerar plurales y conjugaciones: «papeles» y «papel» comparten «pape»."""
    return palabra[:5] if len(palabra) > 5 else palabra


def preguntas():
    for tema in datos()["temas"]:
        for p in tema["preguntas"]:
            yield tema, p


def pregunta_por_id(pid):
    for _, p in preguntas():
        if p["id"] == pid:
            return p
    return None


@lru_cache(maxsize=1)
def _indice():
    """Por pregunta: frases clave normalizadas y bolsas de raíces con su peso."""
    indice = []
    for tema, p in preguntas():
        claves = [normalizar(c) for c in p.get("claves", [])]
        pesos = {}
        for texto, peso in ((" ".join(claves), 3), (p["pregunta"], 2), (tema["titulo"], 1), (" ".join(p["respuesta"]), 1)):
            for palabra in _palabras(texto):
                r = _raiz(palabra)
                pesos[r] = max(pesos.get(r, 0), peso)
        indice.append((p, claves, pesos))
    return indice


def buscar(texto, limite=3):
    """Preguntas que mejor coinciden con un texto libre, de mayor a menor puntaje."""
    normal = f" {normalizar(texto)} "
    raices = {_raiz(p) for p in _palabras(texto)}
    if not raices:
        return []
    resultados = []
    for p, claves, pesos in _indice():
        puntaje = sum(pesos.get(r, 0) for r in raices)
        puntaje += sum(4 for c in claves if c and f" {c} " in normal)
        if puntaje >= 3:
            resultados.append((puntaje, p))
    resultados.sort(key=lambda r: -r[0])
    return [p for _, p in resultados[:limite]]


def contexto_usuario(usuario):
    """Datos para personalizar: nombre, primera moto y su próxima tarea. Nunca falla."""
    ctx = {"nombre": "", "moto": None, "moto_nombre": "tu moto", "proxima": ""}
    if not getattr(usuario, "is_authenticated", False):
        return ctx
    ctx["nombre"] = (usuario.first_name or "").split(" ")[0]
    try:
        from garaje.models import Moto
        moto = Moto.objects.filter(motociclista__usuario=usuario).select_related("linea").order_by("id").first()
    except Exception:  # noqa: BLE001 - la ayuda nunca debe romper la página
        moto = None
    if moto:
        ctx["moto"] = moto
        ctx["moto_nombre"] = getattr(moto, "nombre_corto", None) or str(moto)
        ctx["proxima"] = proxima_tarea(moto)
    return ctx


def proxima_tarea(moto):
    """Nombre de la tarea de mantenimiento más cercana según el plan (la primera tras ordenar por gravedad)."""
    try:
        from garaje.plan import calcular_plan
        tareas = calcular_plan(moto).tareas
    except Exception:  # noqa: BLE001 - la ayuda nunca debe romper la página
        return ""
    return tareas[0].tarea.nombre if tareas else ""


def _url(accion, ctx):
    nombre = accion.get("url_nombre")
    if not nombre:
        return accion.get("url")
    args = []
    if accion.get("con_moto"):
        if not ctx["moto"]:
            nombre = accion.get("sin_moto", "garaje:bienvenida")
        else:
            args = [ctx["moto"].pk]
    try:
        url = reverse(nombre, args=args)
    except NoReverseMatch:
        return None
    return f"{url}#{accion['ancla']}" if accion.get("ancla") and args else url


def _rellenar(texto, ctx):
    return texto.replace("{moto}", ctx["moto_nombre"]).replace("{nombre}", ctx["nombre"] or "")


def _sin_precio_tipico(textos):
    """Apagado en la consola «Mostrar precio típico por servicio»: se quitan las frases que lo mencionan."""
    from consola.ajustes import ajuste
    return textos if ajuste("precio_tipico") else [t for t in textos if "precio típico" not in t.lower()]


def _forma(p, ctx, fuente="faq"):
    acciones = []
    for a in p.get("acciones", []):
        url = _url(a, ctx)
        if url:
            texto = a.get("texto_sin_moto") if a.get("con_moto") and not ctx["moto"] and a.get("texto_sin_moto") else a["texto"]
            acciones.append({"texto": texto, "url": url})
    relacionadas = []
    for rid in p.get("relacionadas", []):
        r = pregunta_por_id(rid)
        if r:
            relacionadas.append({"id": r["id"], "pregunta": r["pregunta"]})
    return {
        "fuente": fuente,
        "id": p.get("id"),
        "pregunta": p["pregunta"],
        "respuesta": [_rellenar(t, ctx) for t in _sin_precio_tipico(p["respuesta"])],
        "acciones": acciones,
        "relacionadas": relacionadas,
    }


def responder(texto="", pregunta_id="", usuario=None):
    """Punto único de respuesta: aquí se conectaría la IA."""
    ctx = contexto_usuario(usuario)
    if pregunta_id:
        p = pregunta_por_id(pregunta_id)
        if p:
            return _forma(p, ctx)
    if normalizar(texto) in SALUDOS:  # «hola» no es una pregunta sin respuesta: se contesta con el saludo
        sin = dict(datos()["sin_respuesta"], id=None, pregunta=texto)
        sin.update(respuesta=[catalogo(usuario)["saludo"], "Elige un tema o escríbeme tu duda."], acciones=[], relacionadas=[])
        return _forma(sin, ctx, fuente="saludo")
    encontradas = buscar(texto) if texto else []
    if encontradas:
        r = _forma(encontradas[0], ctx)
        r["relacionadas"] = [{"id": e["id"], "pregunta": e["pregunta"]} for e in encontradas[1:]] or r["relacionadas"]
        return r
    sin = dict(datos()["sin_respuesta"], id=None, pregunta=texto or "")
    return _forma(sin, ctx, fuente="sin_respuesta")


def catalogo(usuario=None):
    """Saludo y temas para el chat."""
    ctx = contexto_usuario(usuario)
    d = datos()
    saludo = _rellenar(d["saludos"]["con_nombre" if ctx["nombre"] else "anonimo"], ctx)
    return {
        "saludo": saludo,
        "temas": [{"id": t["id"], "titulo": t["titulo"], "preguntas": [{"id": p["id"], "pregunta": p["pregunta"]} for p in t["preguntas"]]} for t in d["temas"]],
    }
