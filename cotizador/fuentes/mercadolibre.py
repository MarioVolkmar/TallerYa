"""Mercado Libre Colombia (sitio MCO) por su interfaz oficial (api.mercadolibre.com). Sin scraping de páginas.

Desde 2025 la búsqueda responde 403 sin token (probado el 18-nov-2026: /sites/MCO/search y /products/search
devuelven 403 a una llamada anónima). Hace falta una aplicación registrada en https://developers.mercadolibre.com.co
(ver cotizador/README.md). Configuración por variables de entorno:

- ML_APP_ID, ML_SECRET y ML_REFRESH_TOKEN: lo recomendado. El access token dura 6 h y se renueva solo; el refresh
  token es de un solo uso, así que el nuevo se guarda en la tabla TokenMercadoLibre.
- ML_ACCESS_TOKEN: atajo para probar (vence a las 6 h).

Privacidad: a Mercado Libre solo viaja el texto de la pieza y la moto (nada del usuario: ni IP, ni cookies, ni
correo). La llamada la hace el servidor; el navegador nunca habla con Mercado Libre (la CSP no cambia).
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

from django.utils import timezone

API = "https://api.mercadolibre.com"
SITIO = "MCO"
TIEMPO_MAX = 8  # segundos por llamada
AGENTE = "TallerYa-cotizador/0.1 (+piloto)"


class SinCredenciales(Exception):
    """No hay token configurado: el piloto muestra resultados de ejemplo con un aviso."""


class ErrorFuente(Exception):
    """Mercado Libre no respondió bien (caída, 403 con token, límite de uso…)."""


def configurada():
    e = os.environ
    return bool(e.get("ML_ACCESS_TOKEN") or (e.get("ML_APP_ID") and e.get("ML_SECRET") and e.get("ML_REFRESH_TOKEN")))


def _pedir(url, datos=None, token=None):
    """GET (o POST de formulario si hay `datos`). Devuelve (estado, json). Se reemplaza en las pruebas (mock)."""
    cabeceras = {"Accept": "application/json", "User-Agent": AGENTE}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    cuerpo = urllib.parse.urlencode(datos).encode() if datos else None
    if cuerpo:
        cabeceras["Content-Type"] = "application/x-www-form-urlencoded"
    peticion = urllib.request.Request(url, data=cuerpo, headers=cabeceras)
    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_MAX) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "null")
        except ValueError:
            return e.code, None
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise ErrorFuente(f"Sin respuesta de Mercado Libre: {e}") from e


def _token():
    """Access token vigente: el de la variable de entorno, el guardado o uno renovado con el refresh token."""
    from cotizador.models import TokenMercadoLibre

    if os.environ.get("ML_ACCESS_TOKEN"):
        return os.environ["ML_ACCESS_TOKEN"]
    if not configurada():
        raise SinCredenciales("Faltan ML_APP_ID, ML_SECRET y ML_REFRESH_TOKEN")
    guardado = TokenMercadoLibre.objects.first()
    if guardado and guardado.vence - timezone.now() > timedelta(minutes=5):
        return guardado.access_token
    refresh = (guardado.refresh_token if guardado and guardado.refresh_token else os.environ["ML_REFRESH_TOKEN"])
    estado, datos = _pedir(f"{API}/oauth/token", datos={
        "grant_type": "refresh_token", "client_id": os.environ["ML_APP_ID"],
        "client_secret": os.environ["ML_SECRET"], "refresh_token": refresh,
    })
    if estado != 200 or not datos or "access_token" not in datos:
        raise ErrorFuente(f"No se pudo renovar el token de Mercado Libre (HTTP {estado})")
    TokenMercadoLibre.objects.all().delete()
    TokenMercadoLibre.objects.create(
        access_token=datos["access_token"], refresh_token=datos.get("refresh_token", refresh),
        vence=timezone.now() + timedelta(seconds=int(datos.get("expires_in", 21600))),
    )
    return datos["access_token"]


def _ciudad(item):
    d = item.get("seller_address") or {}
    ciudad = (d.get("city") or {}).get("name") or (item.get("address") or {}).get("city_name") or ""
    depto = (d.get("state") or {}).get("name") or (item.get("address") or {}).get("state_name") or ""
    return ", ".join(x for x in (ciudad, depto) if x)


def _normalizar(item):
    precio = item.get("price")
    if not isinstance(precio, (int, float)) or precio <= 0:
        return None
    if item.get("currency_id", "COP") != "COP":
        return None
    enlace = item.get("permalink") or ""
    if not enlace.startswith("https://"):  # solo enlaces seguros de Mercado Libre
        iid = str(item.get("id") or item.get("item_id") or "")
        enlace = f"https://articulo.mercadolibre.com.co/{iid[:3]}-{iid[3:]}" if iid.startswith(SITIO) else ""
    return {
        "titulo": (item.get("title") or "")[:160],
        "precio": int(round(precio)),
        "enlace": enlace,
        "ciudad": _ciudad(item)[:80],
        "vendedor": ((item.get("seller") or {}).get("nickname") or "")[:60],
        "condicion": item.get("condition") or "",
    }


def buscar(texto, limite=50):
    """Publicaciones de Mercado Libre Colombia para `texto`, normalizadas. Lanza SinCredenciales o ErrorFuente."""
    token = _token()
    q = urllib.parse.quote(texto[:120])
    estado, datos = _pedir(f"{API}/sites/{SITIO}/search?q={q}&limit={limite}", token=token)
    if estado == 200 and datos:
        crudos = datos.get("results") or []
    elif estado in (403, 404):
        crudos = _buscar_catalogo(q, token)  # la búsqueda documentada hoy es la del catálogo de productos
    else:
        raise ErrorFuente(f"Búsqueda de Mercado Libre respondió HTTP {estado}")
    return [r for r in map(_normalizar, crudos) if r]


def _buscar_catalogo(q, token, productos=4):
    """Plan B: /products/search (catálogo, documentado con part number) y las publicaciones de cada producto."""
    estado, datos = _pedir(f"{API}/products/search?status=active&site_id={SITIO}&q={q}&limit={productos}", token=token)
    if estado != 200 or not datos:
        raise ErrorFuente(f"Catálogo de Mercado Libre respondió HTTP {estado}")
    items = []
    for producto in (datos.get("results") or [])[:productos]:
        pid = producto.get("id")
        if not pid:
            continue
        e2, d2 = _pedir(f"{API}/products/{urllib.parse.quote(pid)}/items?limit=10", token=token)
        if e2 == 200 and d2:
            for it in d2.get("results") or []:
                it.setdefault("title", producto.get("name", ""))
                items.append(it)
    return items
