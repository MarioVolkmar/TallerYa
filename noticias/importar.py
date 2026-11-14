"""Trae titulares de las fuentes RSS/Atom: filtra lo motero, clasifica y guarda solo titular, resumen corto y enlace."""
import html
import logging
import re
import urllib.request
from datetime import timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Articulo, FuenteNoticias

log = logging.getLogger(__name__)
ATOM = "{http://www.w3.org/2005/Atom}"
MAX_BYTES = 3_000_000
DIAS_RECIENTES = 30
DIAS_CONSERVAR = 90

# Para medios generales: la nota debe hablar de motos, tránsito o trámites del vehículo.
MOTERO = re.compile(
    r"\b(motos?|motocicletas?|motociclistas?|moteros?|motorizad[oa]s?|parrilleros?|pico y placa|tr[aá]nsito|movilidad|"
    r"fotomultas?|comparendos?|soat|runt|licencias? de conducci[oó]n|traspasos?|t[eé]cnico.?mec[aá]nica|tecnomec[aá]nica|"
    r"scooters?|ciclomotor(?:es)?|motociclismo)\b", re.I)
REGLAS = [
    ("tramites", re.compile(r"\b(traspasos?|soat|runt|licencias? de conducci[oó]n|pase de conducci[oó]n|t[eé]cnico.?mec[aá]nica|"
                            r"tecnomec[aá]nica|matr[ií]cula|impuesto vehicular|(?<!pico y )placas?)\b", re.I)),
    ("transito", re.compile(r"\b(pico y placa|tr[aá]nsito|movilidad|fotomultas?|comparendos?|multas?|v[ií]as?|siniestr\w*|"
                            r"accidentes?|velocidad|parrilleros?|cierres? viales?|peajes?)\b", re.I)),
    ("lanzamiento", re.compile(r"\b(lanza(?:miento|mientos|r|n|do|da)?|estren\w*|eicma|modelo 20\d\d|ficha t[eé]cnica|prueba de manejo|"
                               r"nuev[oa]s? (?:moto|motos|modelo|versi[oó]n|generaci[oó]n|scooter|naked|trail)|"
                               r"llega(?:r[aá]|n)? a colombia|precios? en colombia|\d+ (?:cc|cv)|\d+ cilindros|tres cilindros|dos cilindros)\b", re.I)),
]


def clasificar(texto, internacional=False):
    for categoria, regla in REGLAS:
        if regla.search(texto):
            # El tránsito y los trámites de otro país no aplican aquí: van a actualidad.
            if internacional and categoria in ("tramites", "transito"):
                return "actualidad"
            return categoria
    return "actualidad"


def limpiar(texto, maximo):
    texto = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", texto or ""))).strip()
    if len(texto) <= maximo:
        return texto
    return texto[:maximo].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def _fecha(texto):
    if texto:
        try:
            fecha = parsedate_to_datetime(texto)
        except (TypeError, ValueError):
            fecha = parse_datetime(texto.strip())
        if fecha:
            return fecha if timezone.is_aware(fecha) else timezone.make_aware(fecha)
    return timezone.now()


def _texto(nodo, *etiquetas):
    for etiqueta in etiquetas:
        e = nodo.find(etiqueta)
        if e is not None:
            valor = (e.text or e.get("href") or "").strip()
            if valor:
                return valor
    return ""


def leer_feed(datos):
    """[(titulo, enlace, resumen, fecha)] de un RSS 2.0 o Atom."""
    raiz = ET.fromstring(datos)
    items = raiz.findall("./channel/item") or raiz.findall(f"{ATOM}entry")
    salida = []
    for it in items:
        salida.append((_texto(it, "title", f"{ATOM}title"), _texto(it, "link", f"{ATOM}link"),
                       _texto(it, "description", f"{ATOM}summary", f"{ATOM}content"),
                       _fecha(_texto(it, "pubDate", f"{ATOM}published", f"{ATOM}updated"))))
    return salida


def descargar(url, timeout=12):
    peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; TallerYa lector de noticias)"})
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return respuesta.read(MAX_BYTES)


def importar(fuente):
    """Guarda las notas nuevas de una fuente. Devuelve cuántas se agregaron."""
    nuevos, desde = 0, timezone.now() - timedelta(days=DIAS_RECIENTES)
    try:
        for titulo, enlace, resumen, fecha in leer_feed(descargar(fuente.url)):
            titulo, resumen = limpiar(titulo, 160), limpiar(resumen, 240)
            if not titulo or not enlace.startswith("http") or fecha < desde:
                continue
            texto = f"{titulo} {resumen}"
            if fuente.solo_motos and not MOTERO.search(texto):
                continue
            if Articulo.objects.filter(fuente_url=enlace[:500]).exists():
                continue
            Articulo.objects.create(titulo=titulo, resumen=resumen or titulo, fuente=fuente.nombre, fuente_url=enlace[:500],
                                    origen=fuente, internacional=fuente.internacional, fecha=min(fecha, timezone.now()),
                                    categoria=clasificar(texto, fuente.internacional))
            nuevos += 1
        fuente.ultimo_error = ""
    except Exception as error:  # una fuente caída no detiene a las demás
        log.warning("No se pudo leer %s: %s", fuente.url, error)
        fuente.ultimo_error = str(error)[:200]
    fuente.ultima_lectura = timezone.now()
    fuente.save(update_fields=["ultima_lectura", "ultimo_error"])
    return nuevos


def importar_todas():
    total = sum(importar(f) for f in FuenteNoticias.objects.filter(activa=True))
    # Las importadas viejas se borran; las propias (con cuerpo) se quedan.
    Articulo.objects.filter(origen__isnull=False, fecha__lt=timezone.now() - timedelta(days=DIAS_CONSERVAR)).delete()
    return total
