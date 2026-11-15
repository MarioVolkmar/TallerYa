"""Menciones del foro (@alias), hilo de respuestas y notificaciones de respuestas y menciones.

Alias público: nombre visible convertido a minúsculas sin espacios + "-" + id (ej. "@camila-12"). Nunca se usa el correo.
El autocompletado inserta el alias; al mostrar el texto se cambia por "@Camila" (enlace al taller si es una cuenta de taller).
"""
import re

from django.contrib.auth import get_user_model
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from notificaciones.models import Notificacion
from notificaciones.servicios import notificar

NIVEL_MAXIMO = 2  # niveles visuales de anidación bajo una respuesta; más abajo se muestra "en respuesta a @usuario"
MAX_MENCIONES = 10  # por mensaje: freno contra menciones masivas
RE_MENCION = re.compile(r"(?<![\w@])@([a-z0-9]+)-(\d+)\b")


def nombre_publico(usuario):
    taller = getattr(usuario, "taller", None)
    return (getattr(taller, "nombre", "") or usuario.first_name or "Motociclista").strip()


def alias(usuario):
    base = slugify(nombre_publico(usuario)).replace("-", "")[:20] or "motociclista"
    return f"{base}-{usuario.pk}"


def ids_mencionados(texto):
    """Ids de usuario mencionados en el texto, en orden y sin repetir (máximo MAX_MENCIONES)."""
    ids = []
    for m in RE_MENCION.finditer(texto or ""):
        pk = int(m.group(2))
        if pk not in ids:
            ids.append(pk)
    return ids[:MAX_MENCIONES]


def usuarios_por_id(ids):
    User = get_user_model()
    return {u.pk: u for u in User.objects.filter(pk__in=ids, is_active=True).select_related("taller")}


def mencionados(texto):
    """Usuarios mencionados que existen y cuyo alias coincide con lo escrito (evita ids al azar)."""
    escritos = {(m.group(1), int(m.group(2))) for m in RE_MENCION.finditer(texto or "")}
    usuarios = usuarios_por_id(ids_mencionados(texto))
    return [u for pk, u in usuarios.items() if (alias(u).rsplit("-", 1)[0], pk) in escritos]


def texto_plano(texto, usuarios):
    """Texto con "@camila-2" cambiado por "@Camila" (para extractos sin enlaces)."""
    def cambiar(m):
        u = usuarios.get(int(m.group(2)))
        return f"@{nombre_publico(u)}" if u and alias(u).rsplit("-", 1)[0] == m.group(1) else m.group(0)
    return RE_MENCION.sub(cambiar, texto or "")


def enlace_mencion(usuario):
    """La mención lleva a la página pública de actividad de esa persona en el foro."""
    from django.urls import reverse
    return format_html('<a href="{}" class="fo-mencion">@{}</a>', reverse("foro:integrante", args=[usuario.pk]),
                       nombre_publico(usuario))


def renderizar(texto, usuarios):
    """Texto escapado con las menciones válidas convertidas en enlace o nombre resaltado."""
    partes, ultimo = [], 0
    for m in RE_MENCION.finditer(texto or ""):
        u = usuarios.get(int(m.group(2)))
        if not u or alias(u).rsplit("-", 1)[0] != m.group(1):
            continue
        partes.append(escape(texto[ultimo:m.start()]))
        partes.append(enlace_mencion(u))
        ultimo = m.end()
    partes.append(escape((texto or "")[ultimo:]))
    return mark_safe("".join(str(p) for p in partes))


def armar_hilo(pregunta, respuestas, padres_de):
    """Ordena las respuestas visibles en árbol.

    respuestas: lista ya ordenada de las de primer nivel (mejor, más votadas…). padres_de: {id: padre_id} de todas,
    incluidas las ocultas, para colgar una respuesta del antepasado visible más cercano si su padre se ocultó.
    Devuelve las de primer nivel; cada una lleva .en_hilo (lista), .nivel (0-2) y .responde_a (autor, solo si no
    se ve anidada justo debajo).
    """
    visibles = {r.pk: r for r in respuestas}

    def padre_visible(r):
        p = padres_de.get(r.pk)
        while p and p not in visibles:
            p = padres_de.get(p)
        return p

    hijas = {}
    for r in respuestas:
        r.en_hilo, r.planas, r.responde_a, r.padre_real = [], [], "", visibles.get(r.padre_id)
        r.autor_nombre = nombre_publico(r.autor)
        p = padre_visible(r)
        hijas.setdefault(p, []).append(r)
    raiz = hijas.get(None, [])
    orden_raiz = {r.pk: i for i, r in enumerate(respuestas)}
    raiz.sort(key=lambda r: orden_raiz[r.pk])

    def bajar(nodo, nivel):
        nodo.nivel = nivel
        directas = sorted(hijas.get(nodo.pk, []), key=lambda r: r.creado)
        if nivel < NIVEL_MAXIMO:
            nodo.en_hilo = directas
            for h in directas:
                bajar(h, nivel + 1)
        else:  # último nivel visual: todo lo de abajo va plano, en orden, con "en respuesta a @usuario"
            planas = []
            pendientes = list(directas)
            while pendientes:
                h = pendientes.pop(0)
                planas.append(h)
                pendientes.extend(hijas.get(h.pk, []))
            for h in planas:
                h.nivel, h.en_hilo = nivel, []
                h.responde_a = h.padre_real.autor_nombre if h.padre_real else ""
            planas.sort(key=lambda r: r.creado)
            nodo.planas = planas

    def contar(nodo):
        nodo.total_hilo = len(nodo.planas) + sum(1 + contar(h) for h in nodo.en_hilo)
        return nodo.total_hilo

    for r in raiz:
        bajar(r, 0)
        contar(r)
    return raiz


def aplanar(raiz):
    """Todas las respuestas del árbol (para contar o calcular el HTML del cuerpo)."""
    todas = []
    for r in raiz:
        todas.append(r)
        todas.extend(aplanar(r.en_hilo))
        todas.extend(r.planas)
    return todas


def _quien(usuario):
    return nombre_publico(usuario) if getattr(usuario, "taller", None) else (usuario.first_name or "Alguien")


def notificar_publicacion(objeto, pregunta, autor, en_rodada=False):
    """Avisos de una respuesta nueva (o de una pregunta con menciones), sin avisar dos veces a la misma persona.

    Orden de prioridad: respuesta directa a tu mensaje > respuesta a tu pregunta > mención. Nadie se avisa a sí mismo.
    """
    from .models import Respuesta

    avisados = {autor.pk}
    quien = _quien(autor)
    url = objeto.get_absolute_url()
    es_respuesta = isinstance(objeto, Respuesta)
    if es_respuesta and objeto.padre_id:
        destino = objeto.padre.autor
        if destino.pk not in avisados:
            notificar(destino, f"foro-hilo:{objeto.pk}", f"{quien} respondió tu mensaje", pregunta.titulo, url,
                      Notificacion.Tipo.FORO)
            avisados.add(destino.pk)
    if es_respuesta and not objeto.padre_id and pregunta.autor_id not in avisados:
        titulo = f"{quien} comentó tu rodada" if en_rodada else f"{quien} respondió tu pregunta"
        notificar(pregunta.autor, f"foro-respuesta:{objeto.pk}", titulo, pregunta.titulo, url, Notificacion.Tipo.FORO)
        avisados.add(pregunta.autor_id)
    tipo = "r" if es_respuesta else "p"
    for u in mencionados(objeto.cuerpo):
        if u.pk in avisados:
            continue
        notificar(u, f"foro-mencion:{tipo}{objeto.pk}", f"{quien} te mencionó en {pregunta.titulo}"[:120],
                  objeto.cuerpo[:140], url, Notificacion.Tipo.FORO)
        avisados.add(u.pk)
