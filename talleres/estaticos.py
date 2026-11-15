"""Estáticos para producción: además de lo que hace WhiteNoise (nombre con hash, caché "para siempre" y
.gz/.br), el CSS se guarda sin comentarios ni espacios sobrantes al correr `collectstatic`.

El minificado es conservador a propósito: solo quita comentarios y espacios que nunca cambian el
significado (alrededor de `{ } ;` y saltos de línea). No toca el texto entre comillas, ni los espacios
dentro de valores como `calc(1px + 2px)`, ni los de los selectores (`a :hover` ≠ `a:hover`), así que el
navegador arma exactamente las mismas reglas. En local (DEBUG) no se usa: se sirve el archivo original.
"""
import re

from django.core.files.base import ContentFile
from whitenoise.storage import CompressedManifestStaticFilesStorage

_ESPACIOS = re.compile(r"\s+")
_ALREDEDOR = re.compile(r" ?([{};]) ?")


def _trozos(css):
    """Parte el CSS en (es_cadena, texto), saltándose los comentarios. Las cadenas se devuelven tal cual."""
    i, n, normal = 0, len(css), []
    while i < n:
        c = css[i]
        if c in "\"'":
            j = i + 1
            while j < n and css[j] != c:
                j += 2 if css[j] == "\\" else 1
            if normal:
                yield False, "".join(normal)
                normal = []
            yield True, css[i:j + 1]
            i = j + 1
        elif css.startswith("/*", i):
            fin = css.find("*/", i + 2)
            i = n if fin < 0 else fin + 2
            normal.append(" ")      # `a/**/b` no debe quedar como `ab`
        else:
            normal.append(c)
            i += 1
    if normal:
        yield False, "".join(normal)


def minificar_css(css):
    partes = []
    for es_cadena, texto in _trozos(css):
        if not es_cadena:
            texto = _ALREDEDOR.sub(r"\1", _ESPACIOS.sub(" ", texto)).replace(";}", "}")
        partes.append(texto)
    return "".join(partes).strip()


class EstaticosComprimidos(CompressedManifestStaticFilesStorage):
    """CompressedManifestStaticFilesStorage que además minifica el CSS propio (no el del admin ni los .min.css)."""

    def _save(self, name, content):
        if name.endswith(".css") and not name.endswith(".min.css") and not name.startswith("admin/"):
            content.seek(0)
            texto = content.read()
            if isinstance(texto, bytes):
                texto = texto.decode("utf-8")
            content = ContentFile(minificar_css(texto).encode("utf-8"))
        return super()._save(name, content)
