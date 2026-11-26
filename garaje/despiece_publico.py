"""Páginas públicas del despiece, para que Google las encuentre: /despiece/, /despiece/<moto>/,
/despiece/<moto>/<sistema>/ y /despiece/<moto>/pieza/<pieza>/.

Solo contenido propio de TallerYa: dibujos propios, nombres en español y guías de las piezas. Sin códigos
de repuesto de los catálogos de las marcas (decisión del usuario, 19-nov-2026) ni planos originales.
"""
from itertools import groupby
from types import SimpleNamespace

from django.core.cache import cache, caches
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import slugify

from .models import Despiece


def despieces():
    """El despiece activo más nuevo de cada línea, ordenado por marca y modelo, con su slug público."""
    por_linea = {}
    from . import diagramas
    con_dibujo = Despiece.objects.filter(activo=True, laminas__diagrama__in=list(diagramas.DIAGRAMAS)).distinct()
    for d in con_dibujo.select_related("linea__marca").order_by("-anio", "-pk"):
        por_linea.setdefault(d.linea_id, d)
    lista = sorted(por_linea.values(), key=lambda d: str(d.linea).lower())
    for d in lista:
        d.slug = slugify(str(d.linea))
        d.url_publica = reverse("garaje:despiece_moto", args=[d.slug])
    return lista


def _por_slug(slug):
    d = next((d for d in despieces() if d.slug == slug), None)
    if d is None:
        raise Http404("No hay despiece de esa moto")
    return d


def _publicable(laminas):
    """Las láminas con dibujo propio, sin códigos ni planos originales; las guías sin repetir por nombre."""
    salida, usados = [], set()
    for lam in laminas:
        if not lam.get("dibujo_propio"):
            continue
        slug = slugify(lam["nombre"]) or f"figura-{lam['figura']}"
        if slug in usados:
            slug = f"{slug}-{lam['figura']}"
        usados.add(slug)
        partes, guias, vistas = [], [], set()
        for p in lam["partes"]:
            partes.append({"ref": p["ref"], "nombre": p["nombre"], "ayuda": p.get("ayuda") or "",
                           "cantidad": p.get("cantidad") or 1})
            g = p.get("guia")
            if isinstance(g, dict) and g.get("que_hace") and p["nombre"].lower() not in vistas:
                vistas.add(p["nombre"].lower())
                guias.append({"nombre": p["nombre"], **g})
        salida.append({"slug": slug, "nombre": lam["nombre"], "sistema": lam.get("sistema") or "Otros",
                       "imagen": lam["imagen"], "partes": partes, "guias": guias})
    return salida


def laminas_de(d):
    """Láminas publicables del despiece (en caché: armarlas toma hasta un segundo)."""
    from .views import _version_codigo_despiece, datos_despiece
    clave = f"despiece_publico:{d.pk}:{_version_codigo_despiece()}"
    datos = cache.get(clave)
    if datos is None:
        sin_moto = SimpleNamespace(pk=0, km_actual=0, nombre_completo=str(d.linea))
        crudo = datos_despiece(d, SimpleNamespace(moto=sin_moto, tareas=[], piezas=lambda: {}))
        datos = _publicable(crudo["laminas"])
        cache.set(clave, datos, 60 * 60 * 24)
        indexar(d, datos)
    return datos


# Índice de direcciones públicas de cada despiece, para el sitemap: armar un despiece toma de 10 a 30 s, así que el
# sitemap nunca lo hace. Se guarda sin vencimiento y sin la versión del código (una dirección rara vez cambia); lo
# escriben `precalentar_despiece` y la primera visita a cada moto. El prefijo "zz_" lo deja de último en el
# descarte de la caché en base de datos, que borra por orden de clave.
def _clave_indice(pk):
    return f"zz_publico_indice:{pk}"


def indexar(d, laminas):
    caches["despiece"].set(_clave_indice(d.pk),
                           {"laminas": [lam["slug"] for lam in laminas], "piezas": list(piezas_de(laminas))}, None)


def indices(lista):
    """{pk: {"laminas": [slug], "piezas": [slug]}} de los despieces ya indexados, en una sola consulta."""
    claves = {_clave_indice(d.pk): d.pk for d in lista}
    return {claves[k]: v for k, v in caches["despiece"].get_many(claves).items()}


def piezas_de(laminas):
    """{slug: pieza} de las que tienen guía: una por nombre, con las láminas donde aparece. Sin la tornillería ni los
    empaques: su página no diría nada propio."""
    from .views import _TORNILLERIA
    salida = {}
    for lam in laminas:
        for g in lam["guias"]:
            slug = slugify(g["nombre"])
            if slug and not _TORNILLERIA.search(g["nombre"]):
                salida.setdefault(slug, {"slug": slug, "nombre": g["nombre"], "guia": g, "laminas": []})
    for lam in laminas:
        for slug in dict.fromkeys(slugify(p["nombre"]) for p in lam["partes"]):
            if slug in salida:
                salida[slug]["laminas"].append(lam)
    return salida


def indice(request):
    lista = despieces()
    marcas = [(marca, list(ds)) for marca, ds in groupby(lista, key=lambda d: d.linea.marca)]
    return render(request, "garaje/despiece_publico/indice.html", {
        "marcas": marcas, "total": len(lista),
        "seo_desc": f"Despiece de {len(lista)} motos populares en Colombia con dibujos propios: qué hace cada pieza, "
                    "señales de falla y cada cuánto revisarla.",
    })


def moto(request, moto):
    d = _por_slug(moto)
    laminas = laminas_de(d)
    if not laminas:
        raise Http404("Esta moto aún no tiene dibujos propios")
    sistemas = [(s, list(ls)) for s, ls in groupby(sorted(laminas, key=lambda l: l["sistema"]), key=lambda l: l["sistema"])]
    from .motos_publico import lineas
    return render(request, "garaje/despiece_publico/moto.html", {
        "ficha_moto": next((x for x in lineas() if x.pk == d.linea_id), None),
        "d": d, "moto": str(d.linea), "sistemas": sistemas, "n_laminas": len(laminas),
        "n_piezas": sum(len(l["partes"]) for l in laminas),
        "seo_desc": f"Despiece de la {d.linea}: {len(laminas)} dibujos por sistema (motor, frenos, suspensión, "
                    "eléctrico…) con qué hace cada pieza y cuándo revisarla.",
    })


def pieza(request, moto, pieza):
    from .motos_publico import json_ld, lineas, migas, resumir
    d = _por_slug(moto)
    todas = piezas_de(laminas_de(d))
    p = todas.get(pieza)
    if p is None:
        raise Http404("Esa pieza no está en el despiece")
    linea = str(d.linea)
    h1 = f"{p['nombre']} de la {linea}"
    desc = resumir(f"{h1}. {p['guia']['que_hace']}")
    url = request.build_absolute_uri(reverse("garaje:despiece_pieza", args=[d.slug, p["slug"]]))
    vecinas = {}
    for lam in p["laminas"]:
        for g in lam["guias"]:
            s = slugify(g["nombre"])
            if s != p["slug"] and s in todas:
                vecinas[s] = todas[s]
    return render(request, "garaje/despiece_publico/pieza.html", {
        "d": d, "moto": linea, "p": p, "g": p["guia"], "h1": h1, "vecinas": list(vecinas.values())[:10],
        "imagen": p["laminas"][0] if p["laminas"] else None,
        "ficha_moto": next((x for x in lineas() if x.pk == d.linea_id), None),
        "seo_titulo": f"{h1}: para qué sirve y cuándo revisarla · TallerYa", "seo_desc": desc,
        "ld": json_ld(
            migas(request, [("Despiece", reverse("garaje:despiece_indice")), (linea, d.url_publica), (p["nombre"], None)]),
            {"@type": "Article", "headline": h1[:110], "description": desc, "inLanguage": "es-CO", "url": url,
             "about": {"@type": "Vehicle", "name": linea, "brand": {"@type": "Brand", "name": d.linea.marca.nombre}},
             "publisher": {"@type": "Organization", "name": "TallerYa", "url": request.build_absolute_uri("/")}}),
    })


def sistema(request, moto, sistema):
    d = _por_slug(moto)
    laminas = laminas_de(d)
    i = next((i for i, l in enumerate(laminas) if l["slug"] == sistema), None)
    if i is None:
        raise Http404("Ese sistema no está en el despiece")
    lam = laminas[i]
    vecinas = [l for l in laminas if l["sistema"] == lam["sistema"] and l["slug"] != lam["slug"]][:6]
    con_pagina = piezas_de(laminas)
    return render(request, "garaje/despiece_publico/sistema.html", {
        "d": d, "moto": str(d.linea), "vecinas": vecinas,
        "lam": {**lam, "guias": [{**g, "slug": s if (s := slugify(g["nombre"])) in con_pagina else ""} for g in lam["guias"]]},
        "anterior": laminas[i - 1] if i > 0 else None, "siguiente": laminas[i + 1] if i + 1 < len(laminas) else None,
        "seo_desc": f"{lam['nombre']} de la {d.linea}: dibujo del despiece con sus {len(lam['partes'])} piezas, "
                    "qué hace cada una, señales de falla y cada cuánto revisarla.",
    })
