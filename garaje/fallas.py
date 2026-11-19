"""Piloto «Tips y fallas frecuentes» por modelo de moto (apagado con FALLAS_FRECUENTES_ACTIVO=0).

garaje/fallas_frecuentes/<marca>_<linea>.json   (mismo slug que garaje/intervalos/: intervalos.slug_linea)
{
  "linea": "Yamaha NMAX 155", "tipo": "scooter", "revisado": "2026-11-18",
  "fuentes": {"manual": {"nombre": "...", "url": "..."}, ...},
  "fallas": [{
      "clave": "cvt-tiembla", "titulo": "...", "sintoma": "...", "causa": "...",
      "gravedad": "molestia" | "cuidado" | "peligro", "que_hacer": "...", "costo": "..." (opcional),
      "alcance": "modelo" (reportado por dueños de este modelo) | "tipo" (pasa en muchas motos de este tipo),
      "tareas": ["correa-cvt"],            # TareaMantenimiento.clave: se resalta si está vencida o próxima
      "pieza": "correa",                   # TareaMantenimiento.Pieza: enlace al despiece si la moto lo tiene
      "diagnostico": {"s": "cvt", "que": "tiembla"},   # garaje/diagnostico.py: síntoma y respuestas
      "taller": "Mantenimiento general",  # talleres.Servicio.nombre (directorio filtrado)
      "domicilio": "Diagnóstico",         # domicilio.TipoServicio.nombre (mecánicos a domicilio)
      "fuentes": ["manual", "motoryk"]}],
  "tips": [{"titulo": "...", "texto": "...", "fuentes": ["manual"]}]
}
generales.json: {"scooter": {"tips": [...]}, "calle": {...}, "enduro": {...}} para las motos sin archivo propio.
Los archivos que empiezan por "_" no se leen. Lectura cacheada por proceso, como intervalos.py.
"""
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse

from .intervalos import slug_linea

CARPETA = Path(__file__).resolve().parent / "fallas_frecuentes"
GRAVEDADES = {"molestia": "Molestia", "cuidado": "Cuidado", "peligro": "Peligro"}
ALCANCES = {"modelo", "tipo"}


class FallasInvalidas(ValueError):
    pass


def validar(datos, nombre="archivo"):
    if not isinstance(datos, dict) or not isinstance(datos.get("fallas"), list) or not isinstance(datos.get("tips"), list):
        raise FallasInvalidas(f"{nombre}: necesita las listas \"fallas\" y \"tips\".")
    fuentes = datos.get("fuentes", {})
    for i, f in enumerate(datos["fallas"], 1):
        for campo in ("clave", "titulo", "sintoma", "causa", "gravedad", "que_hacer", "alcance", "fuentes"):
            if not f.get(campo):
                raise FallasInvalidas(f"{nombre}: la falla {f.get('clave') or i} no tiene \"{campo}\".")
        if f["gravedad"] not in GRAVEDADES:
            raise FallasInvalidas(f"{nombre}: {f['clave']}: gravedad debe ser molestia, cuidado o peligro.")
        if f["alcance"] not in ALCANCES:
            raise FallasInvalidas(f"{nombre}: {f['clave']}: alcance debe ser modelo o tipo.")
        _validar_fuentes(f, fuentes, nombre)
    for i, t in enumerate(datos["tips"], 1):
        if not t.get("titulo") or not t.get("texto"):
            raise FallasInvalidas(f"{nombre}: el tip {i} necesita \"titulo\" y \"texto\".")
        _validar_fuentes(t, fuentes, nombre)


def _validar_fuentes(item, fuentes, nombre):
    faltan = [f for f in item.get("fuentes", []) if f not in fuentes]
    if faltan:
        raise FallasInvalidas(f"{nombre}: {item.get('clave') or item.get('titulo')}: fuentes sin definir: {', '.join(faltan)}.")


@lru_cache(maxsize=None)
def _cargar(slug):
    ruta = CARPETA / f"{slug}.json"
    if not slug or slug.startswith("_") or not ruta.exists():
        return None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    validar(datos, ruta.name)
    return datos


@lru_cache(maxsize=None)
def _generales():
    ruta = CARPETA / "generales.json"
    datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    for tipo, d in datos.items():
        validar({"fallas": [], **d}, f"generales.json ({tipo})")
    return datos


def limpiar_cache():
    _cargar.cache_clear()
    _generales.cache_clear()


def de_linea(linea):
    return _cargar(slug_linea(linea)) if linea else None


def _nombres_a_pk(modelo, nombres):
    return dict(modelo.objects.filter(nombre__in=nombres).values_list("nombre", "pk")) if nombres else {}


# Moto de trabajo (TallerYa Ruta): lo que más sufre con el uso severo (pare y arranque, carga, lluvia) va primero
PIEZAS_SEVERAS = {"cadena", "correa", "freno_del", "freno_tras", "llanta_del", "llanta_tras"}
PALABRAS_SEVERAS = ("cadena", "freno", "pastilla", "llanta", "clutch", "embrague")


def es_uso_severo(falla):
    texto = f"{falla.get('clave', '')} {falla.get('titulo', '')}".lower()
    return falla.get("pieza") in PIEZAS_SEVERAS or any(p in texto for p in PALABRAS_SEVERAS)


def para_moto(moto, plan, piezas_despiece=(), uso_severo=False):
    """Contexto de la sección para la página de la moto, o None (bandera apagada o sin nada que mostrar).
    uso_severo: la moto es «La uso para trabajar»; se marcan y ordenan primero cadena, frenos, llantas y clutch."""
    if not settings.FALLAS_FRECUENTES_ACTIVO:
        return None
    datos = de_linea(moto.linea)
    tipo = getattr(moto.linea, "tipo", "") or "calle"
    if not datos:
        general = _generales().get(tipo) or _generales().get("calle")
        if not general:
            return None
        return {"general": True, "tipo": tipo, "fallas": [], "tips": general["tips"],
                "fuentes": list(general.get("fuentes", {}).values())}

    from domicilio.models import TipoServicio
    from talleres.models import Servicio

    # Lo del plan que se relaciona: urgentes (rojo) resaltan la tarjeta; lo próximo solo se menciona
    pendientes = {t.tarea.clave: (t, False) for t in plan.pronto}
    pendientes.update({t.tarea.clave: (t, True) for t in plan.urgentes})
    talleres = _nombres_a_pk(Servicio, {f["taller"] for f in datos["fallas"] if f.get("taller")})
    domicilio = _nombres_a_pk(TipoServicio, {f["domicilio"] for f in datos["fallas"] if f.get("domicilio")})
    fallas = []
    for f in datos["fallas"]:
        alertas = [{"nombre": t.tarea.nombre, "urgente": urgente}
                   for t, urgente in (pendientes[c] for c in f.get("tareas", []) if c in pendientes)]
        dx = f.get("diagnostico")
        fallas.append({
            **f,
            "gravedad_texto": GRAVEDADES[f["gravedad"]],
            "alertas": alertas,
            "toca": any(a["urgente"] for a in alertas),
            "severo": uso_severo and es_uso_severo(f),
            "en_despiece": f.get("pieza") in set(piezas_despiece),
            "url_diagnostico": f"{reverse('garaje:diagnostico')}?{urlencode({'moto': moto.pk, **dx})}" if dx else "",
            "url_taller": f"{reverse('talleres:directorio')}?servicio={talleres[f['taller']]}" if f.get("taller") in talleres else "",
            "url_domicilio": (f"{reverse('domicilio:listado')}?servicio={domicilio[f['domicilio']]}"
                              if f.get("domicilio") in domicilio else ""),
        })
    # Primero lo que ya requiere atención en el plan, luego lo más grave
    orden = {"peligro": 0, "cuidado": 1, "molestia": 2}
    fallas.sort(key=lambda f: (not f["toca"], not f["severo"], orden[f["gravedad"]]))
    usadas = {c for f in datos["fallas"] + datos["tips"] for c in f.get("fuentes", [])}
    return {"general": False, "tipo": tipo, "modelo": datos.get("linea") or str(moto.linea), "fallas": fallas,
            "uso_severo": uso_severo,
            "tips": datos["tips"], "revisado": datos.get("revisado", ""),
            "fuentes": [v for k, v in datos.get("fuentes", {}).items() if k in usadas]}
