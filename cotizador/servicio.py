"""Cotizar una pieza del despiece: arma la consulta, usa la caché de 24 h y, si no hay dato fresco, pregunta a la
fuente (Mercado Libre; sin credenciales, resultados de ejemplo) y guarda el resumen."""
import logging

from django.core.cache import cache
from django.db.models import F
from django.utils import timezone

from cuentas import limites

from . import filtro
from .fuentes import ejemplo, mercadolibre
from .models import Cotizacion

log = logging.getLogger(__name__)
MAX_VENDEDORES = 5
MAX_FUENTE_POR_HORA = 300   # tope global de cotizaciones nuevas por hora (cuida la cuota de Mercado Libre)
MIN_PARA_NO_REINTENTAR = 3  # si la consulta por código deja menos de esto, se intenta por nombre


class SinDatos(Exception):
    """La fuente falló y no hay nada guardado que mostrar."""


def datos_parte(parte):
    """Lo único que sale hacia la fuente: código, nombre de la pieza, marca y línea (catálogo, nada del usuario)."""
    linea = parte.lamina.despiece.linea
    return {"parte_id": parte.pk, "codigo": parte.codigo.strip(), "nombre": parte.nombre,
            "marca": linea.marca.nombre, "linea": linea.nombre}


def consultas(d):
    """Primero la referencia del despiece con la moto; de respaldo, el nombre de la pieza con la moto."""
    moto = f"{d['marca']} {d['linea']}".strip()
    salida = []
    if d["codigo"]:
        salida.append(f"{d['codigo']} {d['linea']}".strip())
    if d["nombre"]:
        salida.append(f"{d['nombre']} {moto}".strip())
    return salida


def clave(d):
    return filtro.normal(f"{d['codigo'] or d['nombre']}|{d['marca']} {d['linea']}")[:200]


def _otras_lineas():
    nombres = cache.get("cotizador:lineas")
    if nombres is None:
        from garaje.models import LineaMoto
        nombres = sorted({n.split()[0] for n in LineaMoto.objects.values_list("nombre", flat=True) if n.split()})
        cache.set("cotizador:lineas", nombres, 3600)
    return nombres


def _buscar(texto, pista=""):
    """(resultados, fuente). Sin credenciales, ejemplo; un fallo de red sube como ErrorFuente."""
    try:
        return mercadolibre.buscar(texto), Cotizacion.Fuente.MERCADOLIBRE
    except mercadolibre.SinCredenciales:
        return ejemplo.buscar(texto, pista=pista), Cotizacion.Fuente.EJEMPLO


def consultar_fuente(d):
    """Hace hasta 2 consultas y devuelve el resumen filtrado (sin guardar)."""
    vistos, todos, aceptados, descartes, fuente, usadas = set(), [], [], [], None, []
    for texto in consultas(d):
        resultados, fuente = _buscar(texto, pista=d["nombre"])
        usadas.append(texto)
        for r in resultados:
            if (r["enlace"], r["titulo"], r["precio"]) not in vistos:
                vistos.add((r["enlace"], r["titulo"], r["precio"]))
                todos.append(r)
        aceptados, descartes = filtro.filtrar(todos, nombre=d["nombre"], codigo=d["codigo"], linea=d["linea"],
                                              otras_lineas=_otras_lineas())
        if len(aceptados) >= MIN_PARA_NO_REINTENTAR:
            break
    encontrados, usada = len(todos), " · ".join(usadas)
    minimo, tipico, maximo = filtro.resumen(aceptados)
    vendedores = [{k: r[k] for k in ("titulo", "precio", "enlace", "ciudad", "vendedor")}
                  for r in aceptados[:MAX_VENDEDORES]]
    return {"consulta": usada[:200], "minimo": minimo, "tipico": tipico, "maximo": maximo, "vendedores": vendedores,
            "encontrados": min(encontrados, 32000), "descartados": min(len(descartes), 32000), "fuente": fuente,
            "descartes": descartes}


def cotizar(d, forzar=False, contar=True, tope_global=True):
    """Cotización de la caché si tiene menos de 24 h; si no, consulta la fuente y la guarda."""
    k = clave(d)
    actual = Cotizacion.objects.filter(clave=k).first()
    if contar and actual:
        Cotizacion.objects.filter(pk=actual.pk).update(pedidos=F("pedidos") + 1)
    if actual and actual.vigente and not forzar and not (actual.es_ejemplo and mercadolibre.configurada()):
        return actual
    if tope_global:
        if limites.superado("cotizador:fuente", MAX_FUENTE_POR_HORA):
            if actual:
                return actual
            raise SinDatos("tope global de consultas por hora")
        limites.sumar("cotizador:fuente", 3600)
    try:
        nuevo = consultar_fuente(d)
    except mercadolibre.ErrorFuente as e:
        log.warning("cotizador: %s", e)
        if actual:
            return actual  # dato viejo antes que nada; la interfaz muestra la fecha
        raise SinDatos(str(e)) from e
    nuevo.pop("descartes")
    campos = dict(nuevo, parte_id=d.get("parte_id"), codigo=d["codigo"][:30], nombre=d["nombre"][:120],
                  moto=f"{d['marca']} {d['linea']}"[:120], consultado_en=timezone.now())
    obj, _ = Cotizacion.objects.update_or_create(clave=k, defaults=campos)
    if contar and not actual:
        Cotizacion.objects.filter(pk=obj.pk).update(pedidos=F("pedidos") + 1)
        obj.refresh_from_db(fields=["pedidos"])
    return obj
