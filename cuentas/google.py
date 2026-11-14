"""Ingreso con Google (OAuth 2.0 / OpenID Connect) sin librerías externas.

Flujo de "código de autorización" con PKCE y `state` contra suplantación:
1. /cuenta/google/        -> redirige a Google con state + code_challenge guardados en la sesión.
2. /cuenta/google/volver/ -> comprueba el state, cambia el código por un token (servidor a servidor)
                             y pide los datos de la cuenta (correo verificado, nombre, id).

Se activa con las variables de entorno GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET.
"""
import base64
import hashlib
import json
import secrets
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

AUTORIZAR = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
DATOS = "https://openidconnect.googleapis.com/v1/userinfo"


class ErrorGoogle(Exception):
    pass


def configurado():
    return bool(getattr(settings, "GOOGLE_CLIENT_ID", "") and getattr(settings, "GOOGLE_CLIENT_SECRET", ""))


def url_autorizacion(redirect_uri, sesion):
    """Arma la URL de Google y guarda en la sesión lo necesario para verificar la vuelta."""
    state = secrets.token_urlsafe(32)
    verificador = secrets.token_urlsafe(64)
    reto = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).rstrip(b"=").decode()
    sesion["google_oauth"] = {"state": state, "verificador": verificador}
    return AUTORIZAR + "?" + urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": "openid email profile", "state": state, "code_challenge": reto,
        "code_challenge_method": "S256", "prompt": "select_account",
    })


def _pedir(url, datos=None, token=None):
    """Petición HTTPS a Google. Aparte para poder simularla en las pruebas."""
    cuerpo = urlencode(datos).encode() if datos else None
    req = Request(url, data=cuerpo, headers={"Accept": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=10) as respuesta:  # noqa: S310 (solo URLs fijas de Google)
        return json.loads(respuesta.read().decode())


def datos_de_la_cuenta(parametros, redirect_uri, sesion):
    """Valida la vuelta de Google y devuelve {sub, email, nombre}. Lanza ErrorGoogle si algo no cuadra."""
    guardado = sesion.pop("google_oauth", None)
    if parametros.get("error"):
        raise ErrorGoogle("Cancelaste el ingreso con Google.")
    if not guardado or not secrets.compare_digest(parametros.get("state", ""), guardado["state"]):
        raise ErrorGoogle("La sesión de ingreso venció. Intenta de nuevo.")
    codigo = parametros.get("code")
    if not codigo:
        raise ErrorGoogle("Google no devolvió el código de ingreso.")
    try:
        token = _pedir(TOKEN, {
            "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": codigo, "code_verifier": guardado["verificador"], "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        })
        datos = _pedir(DATOS, token=token["access_token"])
    except Exception as error:  # red, JSON o token inválido
        raise ErrorGoogle("No pudimos comunicarnos con Google. Intenta de nuevo.") from error
    if not datos.get("sub") or not datos.get("email") or not datos.get("email_verified"):
        raise ErrorGoogle("Tu cuenta de Google no tiene un correo verificado.")
    return {"sub": str(datos["sub"]), "email": datos["email"].strip().lower(),
            "nombre": (datos.get("given_name") or datos.get("name") or "").strip()[:150]}
