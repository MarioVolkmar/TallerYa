"""Páginas públicas por moto, para que Google las encuentre: /motos/, /motos/<moto>/, sus fallas frecuentes y
cada cuánto se le hace cada mantenimiento.

Solo sale contenido del catálogo (garaje/fallas_frecuentes/ y garaje/intervalos/): nada de las motos, placas ni
historiales de los usuarios. Estas vistas no leen el modelo Moto.
"""
import json
import re
from itertools import groupby

from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import Truncator, slugify

from consola.ajustes import ajuste

from . import despiece_publico as dp
from . import fallas, intervalos
from .models import LineaMoto, TareaMantenimiento

# Cómo lo pregunta la gente en Google: verbo y objeto de cada tarea del plan
_PREGUNTAS = {
    "aceite": ("cambiar", "el aceite"),
    "aceite-caja": ("cambiar", "el aceite de la transmisión"),
    "cadena-lubricar": ("limpiar y lubricar", "la cadena"),
    "kit-arrastre": ("cambiar", "el kit de arrastre"),
    "correa-cvt": ("cambiar", "la correa CVT"),
    "filtro-aire": ("limpiar o cambiar", "el filtro de aire"),
    "bujia": ("revisar o cambiar", "la bujía"),
    "valvulas": ("calibrar", "las válvulas"),
    "pastillas-del": ("revisar", "las pastillas de adelante"),
    "pastillas-tras": ("revisar", "las pastillas de atrás"),
    "bandas-del": ("revisar", "las bandas de adelante"),
    "bandas-tras": ("revisar", "las bandas de atrás"),
    "liquido-frenos": ("cambiar", "el líquido de frenos"),
    "llanta-del": ("revisar o cambiar", "la llanta delantera"),
    "llanta-tras": ("revisar o cambiar", "la llanta trasera"),
    "suspension-del": ("revisar", "la suspensión delantera"),
    "suspension-tras": ("revisar", "los amortiguadores"),
    "refrigerante": ("cambiar", "el refrigerante"),
    "bateria": ("revisar", "la batería"),
}


def json_ld(*bloques):
    """<script> de datos estructurados; «<» va escapado para que ningún texto cierre la etiqueta."""
    return mark_safe("".join(
        '<script type="application/ld+json">%s</script>'
        % json.dumps({"@context": "https://schema.org", **b}, ensure_ascii=False).replace("<", "\\u003c")
        for b in bloques))


def migas(request, pasos):
    """BreadcrumbList; pasos = [(nombre, ruta o None para la página actual)]."""
    items = []
    for i, (nombre, ruta) in enumerate(pasos, 1):
        item = {"@type": "ListItem", "position": i, "name": nombre}
        if ruta:
            item["item"] = request.build_absolute_uri(ruta)
        items.append(item)
    return {"@type": "BreadcrumbList", "itemListElement": items}


def resumir(texto, largo=158):
    return Truncator(" ".join(texto.split())).chars(largo)


def fuente_publica(texto):
    """Del texto de la fuente solo el nombre del manual: lo demás son notas internas de dónde salió la copia."""
    return re.split(r"[(,;]", texto or "")[0].strip()


def tareas_de(linea, tareas=None):
    """Mantenimientos de la línea que tienen dato del fabricante (sin él, la página no aportaría nada propio)."""
    propios = intervalos.de_linea(linea)
    if not propios:
        return []
    if tareas is None:
        tareas = TareaMantenimiento.objects.filter(activo=True).order_by("orden", "pk")
    specs, salida = linea.specs(), []
    for base in tareas:
        dato = propios.get(base.clave)
        if not dato or base.clave not in _PREGUNTAS or not base.aplica_a(specs):
            continue
        t = intervalos.aplicar(base, linea, propios)
        verbo, objeto = _PREGUNTAS[base.clave]
        if t.notas_intervalo.startswith("Es revisión"):
            verbo = "revisar"
        # Si el manual no da una de las dos medidas, la que se muestra es la del plan general: hay que decirlo
        generales = [nombre for campo, atributo, nombre in (("km", "intervalo_km", "el kilometraje"),
                                                             ("dias", "intervalo_dias", "el tiempo"))
                     if dato.get(campo) is None and getattr(t, atributo)]
        texto = intervalos.texto(t.intervalo_km, t.intervalo_dias)
        if not texto:
            continue
        versiones = []
        for v in intervalos._leer(intervalos.slug_linea(linea)).get("versiones", []):
            if base.clave in v["tareas"]:
                tv = intervalos.aplicar(base, linea, {base.clave: v["tareas"][base.clave]})
                versiones.append({"nombre": v.get("nombre") or "", "desde": v["desde"], "hasta": v.get("hasta"),
                                  "texto": intervalos.texto(tv.intervalo_km, tv.intervalo_dias)})
        salida.append({
            "clave": base.clave, "nombre": base.nombre, "descripcion": base.descripcion, "verbo": verbo,
            "objeto": objeto, "texto": texto, "generales": " y ".join(generales),
            "especificacion": t.especificacion, "notas": t.notas_intervalo, "aproximado": t.intervalo_aproximado,
            "fuente": fuente_publica(t.fuente_intervalo), "versiones": versiones,
            "url": reverse("garaje:moto_mantenimiento", args=[slugify(str(linea)), base.clave]),
        })
    return salida


def fallas_de(linea):
    """Fallas propias de la línea (con su URL), o [] si no tiene archivo o la sección está apagada."""
    datos = fallas.de_linea(linea) if ajuste("fallas_activo") else None
    if not datos:
        return []
    slug = slugify(str(linea))
    return [{**f, "gravedad_texto": fallas.GRAVEDADES[f["gravedad"]],
             "url": reverse("garaje:moto_falla", args=[slug, f["clave"]])} for f in datos["fallas"]]


def lineas():
    """Líneas del catálogo con algo propio que contar, con slug y URL."""
    salida = []
    for linea in LineaMoto.objects.filter(activo=True).select_related("marca"):
        if not (intervalos.de_linea(linea) or (ajuste("fallas_activo") and fallas.de_linea(linea))):
            continue
        linea.slug = slugify(str(linea))
        linea.url_publica = reverse("garaje:moto_publica", args=[linea.slug])
        salida.append(linea)
    return salida


def _linea(slug):
    linea = next((x for x in lineas() if x.slug == slug), None)
    if linea is None:
        raise Http404("No tenemos esa moto")
    return linea


def _despiece(linea):
    return next((d for d in dp.despieces() if d.linea_id == linea.pk), None)


def indice(request):
    lista = lineas()
    marcas = [(marca, list(ls)) for marca, ls in groupby(lista, key=lambda x: x.marca)]
    ruta = reverse("garaje:motos_publicas")
    return render(request, "garaje/motos_publico/indice.html", {
        "marcas": marcas, "total": len(lista),
        "seo_titulo": "Fallas y mantenimiento por moto · TallerYa",
        "seo_desc": f"Fallas más comunes y cada cuánto hacer cada mantenimiento en {len(lista)} motos populares en "
                    "Colombia: aceite, correa, cadena, frenos, válvulas y más.",
        "ld": json_ld(migas(request, [("Inicio", "/"), ("Motos", None)]), {
            "@type": "CollectionPage", "name": "Fallas y mantenimiento por moto",
            "url": request.build_absolute_uri(ruta)}),
    })


def moto(request, moto):
    linea = _linea(moto)
    nombre = str(linea)
    lista_fallas, tareas = fallas_de(linea), tareas_de(linea)
    datos = fallas.de_linea(linea) if ajuste("fallas_activo") else None
    return render(request, "garaje/motos_publico/moto.html", {
        "linea": linea, "moto": nombre, "fallas": lista_fallas, "tareas": tareas,
        "tips": datos["tips"] if datos else [], "revisado": datos.get("revisado", "") if datos else "",
        "despiece": _despiece(linea),
        "seo_titulo": f"{nombre}: fallas comunes y mantenimiento · TallerYa",
        "seo_desc": resumir(f"{nombre}: " + (f"{len(lista_fallas)} fallas que más reportan sus dueños, " if lista_fallas else "")
                            + "cada cuánto cambiar el aceite y hacerle cada mantenimiento según el manual."),
        "ld": json_ld(migas(request, [("Inicio", "/"), ("Motos", reverse("garaje:motos_publicas")), (nombre, None)]),
                      {"@type": "ItemList", "name": f"Fallas y mantenimientos de la {nombre}", "itemListElement": [
                          {"@type": "ListItem", "position": i, "url": request.build_absolute_uri(x["url"])}
                          for i, x in enumerate(lista_fallas + tareas, 1)]}),
    })


def falla(request, moto, clave):
    linea = _linea(moto)
    lista = fallas_de(linea)
    f = next((x for x in lista if x["clave"] == clave), None)
    if f is None:
        raise Http404("Esa falla no está registrada para esta moto")
    nombre, datos = str(linea), fallas.de_linea(linea)
    h1 = f"{f['titulo']}: {nombre}"
    desc = resumir(f"{nombre}. {f['sintoma']} Causas probables y qué hacer.")
    fuentes = [datos.get("fuentes", {})[c] for c in f.get("fuentes", []) if c in datos.get("fuentes", {})]
    relacionadas = [t for t in tareas_de(linea) if t["clave"] in f.get("tareas", [])]
    from urllib.parse import urlencode
    despiece, dx = _despiece(linea), f.get("diagnostico")
    consulta = {**({"despiece": despiece.pk} if despiece else {}), **(dx or {})}
    url = request.build_absolute_uri(f["url"])
    articulo = {"@type": "Article", "headline": h1[:110], "description": desc, "inLanguage": "es-CO", "url": url,
                "mainEntityOfPage": url, "about": {"@type": "Vehicle", "name": nombre,
                                                   "brand": {"@type": "Brand", "name": linea.marca.nombre}},
                "publisher": {"@type": "Organization", "name": "TallerYa", "url": request.build_absolute_uri("/")}}
    if datos.get("revisado"):
        articulo["dateModified"] = datos["revisado"]
    return render(request, "garaje/motos_publico/falla.html", {
        "linea": linea, "moto": nombre, "f": f, "h1": h1, "fuentes": fuentes, "tareas": relacionadas,
        "otras": [x for x in lista if x["clave"] != clave], "despiece": despiece,
        "url_diagnostico": f"{reverse('garaje:diagnostico')}?{urlencode(consulta)}" if dx else "",
        "revisado": datos.get("revisado", ""),
        "seo_titulo": f"{h1} · TallerYa", "seo_desc": desc,
        "ld": json_ld(migas(request, [("Motos", reverse("garaje:motos_publicas")), (nombre, linea.url_publica),
                                      (f["titulo"], None)]), articulo),
    })


def mantenimiento(request, moto, clave):
    linea = _linea(moto)
    tareas = tareas_de(linea)
    t = next((x for x in tareas if x["clave"] == clave), None)
    if t is None:
        raise Http404("No tenemos ese dato para esta moto")
    nombre = str(linea)
    pregunta = f"¿Cada cuánto {t['verbo']} {t['objeto']} de la {nombre}?"
    respuesta = f"{t['texto']}, lo que se cumpla primero." if " o " in t["texto"] else f"{t['texto']}."
    if t["aproximado"]:
        respuesta += " Es un valor aproximado."
    return render(request, "garaje/motos_publico/mantenimiento.html", {
        "linea": linea, "moto": nombre, "t": t, "pregunta": pregunta, "respuesta": respuesta,
        "otras": [x for x in tareas if x["clave"] != clave],
        "fallas": [f for f in fallas_de(linea) if clave in f.get("tareas", [])], "despiece": _despiece(linea),
        "seo_titulo": f"Cada cuánto {t['verbo']} {t['objeto']}: {nombre} · TallerYa",
        "seo_desc": resumir(f"{nombre}: {t['verbo']} {t['objeto']} {t['texto'][0].lower()}{t['texto'][1:]}. "
                            f"{t['especificacion'] or t['notas']}"),
        "ld": json_ld(migas(request, [("Motos", reverse("garaje:motos_publicas")), (nombre, linea.url_publica),
                                      (t["nombre"], None)]),
                      {"@type": "FAQPage", "mainEntity": [{
                          "@type": "Question", "name": pregunta, "acceptedAnswer": {"@type": "Answer", "text": " ".join(
                              x for x in (respuesta, t["especificacion"], t["notas"]) if x)}}]}),
    })
