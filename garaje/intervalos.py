"""Intervalos de mantenimiento propios de cada línea (del manual del fabricante), en archivos del repo.

garaje/intervalos/<marca>_<linea>.json   (ej.: yamaha_nmax_155.json; slug = marca + nombre de la línea)
{
  "linea": "Yamaha NMAX 155",
  "tareas": {
    "aceite": {"km": 3000, "dias": 180, "fuente": "Manual del propietario, p. 7-12", "aproximado": false,
               "especificacion": "SAE 10W-40 JASO MB, 0,9 L", "notas": "..."},
    ...
  }
}
- Claves de tarea = TareaMantenimiento.clave. En "km" y "dias": ausente o null = usar el general en esa dimensión;
  0 = sin límite en esa dimensión (el manual no lo da y no aplica). Una tarea que no esté usa el intervalo general.
- Versiones por año del modelo (opcional): "versiones": [{"nombre": "FI ABS", "desde": 2020, "hasta": null,
  "tareas": {...}}]. Para una moto de ese rango de años, cada tarea de la versión reemplaza la de la línea
  (desde/hasta inclusivos; hasta null = sin tope). Los rangos no deben cruzarse.
- Los archivos que empiezan por "_" (como _ejemplo.json) no se leen.
- Un solo lugar de lectura, cacheado por proceso; el plan aplica estos valores y de ahí salen colores, avisos y textos.
"""
import copy
import json
from functools import lru_cache
from pathlib import Path

from django.utils.text import slugify

CARPETA = Path(__file__).resolve().parent / "intervalos"
CAMPOS = {"km", "dias", "fuente", "aproximado", "especificacion", "notas"}


class IntervaloInvalido(ValueError):
    pass


def slug_linea(linea):
    if not linea:
        return ""
    marca = getattr(getattr(linea, "marca", None), "nombre", "")
    return slugify(f"{marca} {linea.nombre}").replace("-", "_")


def validar(datos, nombre="archivo"):
    """Revisa el formato; lanza IntervaloInvalido con un mensaje claro para quien llena el archivo."""
    if not isinstance(datos, dict) or not isinstance(datos.get("tareas"), dict):
        raise IntervaloInvalido(f"{nombre}: falta el objeto \"tareas\".")
    _validar_tareas(datos["tareas"], nombre)
    versiones = datos.get("versiones", [])
    if not isinstance(versiones, list):
        raise IntervaloInvalido(f"{nombre}: \"versiones\" debe ser una lista.")
    rangos = []
    for i, v in enumerate(versiones, 1):
        etiqueta = f"{nombre}: versión {v.get('nombre') or i}" if isinstance(v, dict) else f"{nombre}: versión {i}"
        if not isinstance(v, dict) or not isinstance(v.get("tareas"), dict):
            raise IntervaloInvalido(f"{etiqueta}: necesita su objeto \"tareas\".")
        sobran = set(v) - {"nombre", "desde", "hasta", "tareas"}
        if sobran:
            raise IntervaloInvalido(f"{etiqueta}: campos desconocidos: {', '.join(sorted(sobran))}.")
        desde, hasta = v.get("desde"), v.get("hasta")
        if not isinstance(desde, int) or (hasta is not None and (not isinstance(hasta, int) or hasta < desde)):
            raise IntervaloInvalido(f"{etiqueta}: \"desde\" es un año y \"hasta\" un año ≥ desde, o null.")
        for d, h in rangos:
            if desde <= (h if h is not None else 9999) and d <= (hasta if hasta is not None else 9999):
                raise IntervaloInvalido(f"{etiqueta}: su rango de años se cruza con otra versión.")
        rangos.append((desde, hasta))
        _validar_tareas(v["tareas"], etiqueta)
    return datos


def _validar_tareas(tareas, nombre):
    for clave, valores in tareas.items():
        if not isinstance(valores, dict):
            raise IntervaloInvalido(f"{nombre}: \"{clave}\" debe ser un objeto.")
        sobran = set(valores) - CAMPOS
        if sobran:
            raise IntervaloInvalido(f"{nombre}: \"{clave}\" tiene campos desconocidos: {', '.join(sorted(sobran))}.")
        for campo in ("km", "dias"):
            v = valores.get(campo)
            if v is not None and (not isinstance(v, int) or isinstance(v, bool) or v < 0):
                raise IntervaloInvalido(f"{nombre}: \"{clave}.{campo}\" debe ser un entero ≥ 0 (0 = sin límite) o null.")
        if valores.get("km") == 0 and valores.get("dias") == 0:
            raise IntervaloInvalido(f"{nombre}: \"{clave}\" no puede quedar sin límite en km y en días a la vez.")
        if not str(valores.get("fuente") or "").strip():
            raise IntervaloInvalido(f"{nombre}: \"{clave}\" necesita \"fuente\" (manual y página, o URL).")
        if not isinstance(valores.get("aproximado", False), bool):
            raise IntervaloInvalido(f"{nombre}: \"{clave}.aproximado\" debe ser true o false.")


@lru_cache(maxsize=256)
def _leer(slug):
    ruta = CARPETA / f"{slug}.json"
    if not slug or not ruta.is_file():
        return {}
    with ruta.open(encoding="utf-8") as f:
        return validar(json.load(f), ruta.name)


def de_linea(linea, anio=None):
    """{clave_tarea: {...}} de esa línea (y de la versión de ese año del modelo, que gana), o {} si no tiene archivo."""
    datos = _leer(slug_linea(linea))
    if not datos:
        return {}
    tareas = dict(datos["tareas"])
    if anio:
        for v in datos.get("versiones", []):
            if v["desde"] <= anio and (v.get("hasta") is None or anio <= v["hasta"]):
                tareas.update(v["tareas"])
    return tareas


def aplicar(tarea, linea, propios=None, anio=None):
    """Copia de la tarea con el intervalo de la línea (nunca se guarda). Sin dato propio, la misma tarea."""
    propios = de_linea(linea, anio) if propios is None else propios
    dato = propios.get(tarea.clave)
    if not dato:
        return tarea
    t = copy.copy(tarea)
    # null/ausente → el general en esa dimensión; 0 → sin límite
    for campo, atributo in (("km", "intervalo_km"), ("dias", "intervalo_dias")):
        valor = dato.get(campo)
        if valor is not None:
            setattr(t, atributo, valor or None)
    t.fuente_intervalo = dato["fuente"]
    t.intervalo_aproximado = dato.get("aproximado", False)
    t.especificacion = dato.get("especificacion", "")
    t.notas_intervalo = dato.get("notas", "")
    return t


def texto(km=None, dias=None):
    """ "Cada 10.000 km o 12 meses": el único formateador de intervalos (plan, despiece, guía, poner al día)."""
    partes = []
    if km:
        partes.append(f"cada {km:,} km".replace(",", "."))
    if dias:
        if dias < 45:
            partes.append(f"cada {dias} días")
        elif dias < 700:
            meses = round(dias / 30)
            partes.append(f"cada {meses} mes{'es' if meses != 1 else ''}")
        else:
            partes.append(f"cada {round(dias / 365)} años")
    return (" o ".join(partes)).capitalize() if partes else ""


def intervalo_para(clave_tarea, linea=None, anio=None):
    """API estable para la guía/visor: el intervalo de esa tarea para esa línea (archivo del manual) o el general.
    → {"km", "dias", "texto", "fuente", "aproximado", "especificacion", "notas", "propio"} o None si la tarea no existe."""
    from .models import TareaMantenimiento
    tarea = TareaMantenimiento.objects.filter(clave=clave_tarea).first()
    if not tarea:
        return None
    t = aplicar(tarea, linea, anio=anio) if linea else tarea
    return {"km": t.intervalo_km, "dias": t.intervalo_dias, "texto": texto(t.intervalo_km, t.intervalo_dias),
            "fuente": getattr(t, "fuente_intervalo", ""), "aproximado": getattr(t, "intervalo_aproximado", False),
            "especificacion": getattr(t, "especificacion", ""), "notas": getattr(t, "notas_intervalo", ""),
            "propio": t is not tarea}


def limpiar_cache():
    _leer.cache_clear()
