"""Revisión automática de seguridad y velocidad de TallerYa (skill revisar-seguridad).

Uso (desde la raíz del proyecto):
    venv/Scripts/python.exe .claude/skills/revisar-seguridad/revisar.py            # todo
    venv/Scripts/python.exe .claude/skills/revisar-seguridad/revisar.py --solo config,cabeceras,codigo
    ... --sin-red        # salta pip-audit y npm audit (son las únicas que consultan internet: bases de vulnerabilidades)
    ... --json salida.json

Secciones: config, cabeceras, codigo, secretos, dependencias, autorizacion, velocidad, estaticos.
Salida: una tabla corta (estado, severidad, sección, hallazgo, dónde). Código de salida 1 si hay alguna FALLA.
Nunca imprime secretos: solo archivo y línea (o commit y archivo).
Lo revisado a mano y aceptado va en permitidos.txt (ruta|patrón|motivo) para que no vuelva a salir.
"""
import argparse
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
AQUI = Path(__file__).resolve().parent
PY = sys.executable
SECCIONES = ["config", "cabeceras", "codigo", "secretos", "dependencias", "autorizacion", "velocidad", "estaticos"]
SEV_ORDEN = {"crítica": 0, "alta": 1, "media": 2, "baja": 3, "-": 4}
# Carpetas que nunca se revisan como código propio
FUERA = ("venv/", ".venv/", "node_modules/", "staticfiles/", "build_js/", "informes_noche/", ".claude/", "docs/",
         "despiece_local/", "manual_despiece/", "planos_a_generar/", "trabajo_emprendimiento/", "privado/", "media/")
LOCALES = ["despiece_local", "manual_despiece", "planos_a_generar", "media", "privado", "db.sqlite3", ".env",
           "trabajo_emprendimiento"]

hallazgos = []


def anotar(estado, sev, seccion, texto, donde=""):
    hallazgos.append({"estado": estado, "sev": sev if estado != "OK" else "-", "seccion": seccion,
                      "texto": texto, "donde": donde})


def correr(cmd, env_extra=None, timeout=600, entrada=None):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "NOTICIAS_AUTO": "0", **(env_extra or {})}
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, timeout=timeout, input=entrada, shell=isinstance(cmd, str))
    return r.returncode, r.stdout, r.stderr


def env_produccion():
    return {"DJANGO_DEBUG": "0", "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
            "DJANGO_ALLOWED_HOSTS": "tallerya.co,testserver", "DJANGO_CSRF_TRUSTED_ORIGINS": "https://tallerya.co"}


def archivos_git():
    _, out, _ = correr(["git", "ls-files"])
    return [a for a in out.splitlines() if not a.startswith(FUERA)]


def permitidos():
    reglas = []
    archivo = AQUI / "permitidos.txt"
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            partes = re.split(r"(?<!\\)\|", linea, maxsplit=2)  # un \| dentro del patrón no separa
            if linea.strip() and not linea.startswith("#") and len(partes) == 3:
                ruta, patron, _ = partes
                reglas.append((ruta.strip(), patron.strip()))
    return reglas


# ----------------------------------------------------------------------------------------------------- config
def rev_config():
    cod, out, err = correr([PY, "manage.py", "check", "--deploy"], env_produccion())
    avisos = re.findall(r"\((security\.\w+)\) ([^\n]+)", out + err)
    leves = {"security.W005", "security.W021"}  # HSTS includeSubDomains / preload: decisión de dominio
    for codigo, texto in avisos:
        anotar("AVISO", "baja" if codigo in leves else "media", "config", f"check --deploy {codigo}: {texto[:90]}")
    if cod != 0 and not avisos:
        anotar("FALLA", "alta", "config", "check --deploy no corrió", (err or out).strip().splitlines()[-1][:120])
    elif not avisos:
        anotar("OK", "-", "config", "check --deploy sin avisos")
    # Valores leídos con la configuración de producción
    codigo = r"""
import json, django; django.setup()
from django.conf import settings as s
print(json.dumps({k: str(getattr(s, k, None)) for k in [
 "DEBUG","SESSION_COOKIE_SECURE","SESSION_COOKIE_HTTPONLY","SESSION_COOKIE_SAMESITE","SESSION_COOKIE_AGE",
 "CSRF_COOKIE_SECURE","CSRF_COOKIE_HTTPONLY","SECURE_HSTS_SECONDS","SECURE_SSL_REDIRECT","SECURE_PROXY_SSL_HEADER",
 "X_FRAME_OPTIONS","SECURE_REFERRER_POLICY","SECURE_CROSS_ORIGIN_OPENER_POLICY","DATA_UPLOAD_MAX_MEMORY_SIZE",
 "FILE_UPLOAD_MAX_MEMORY_SIZE","DATA_UPLOAD_MAX_NUMBER_FIELDS","PASSWORD_HASHERS","SESSION_EXPIRE_AT_BROWSER_CLOSE"]}))
"""
    cod, out, err = correr([PY, "-c", codigo], {**env_produccion(), "DJANGO_SETTINGS_MODULE": "config.settings"})
    if cod:
        anotar("FALLA", "alta", "config", "No arranca con settings de producción", err.strip().splitlines()[-1][:120])
        return
    v = json.loads(out.strip().splitlines()[-1])
    esperado = {"DEBUG": "False", "SESSION_COOKIE_SECURE": "True", "SESSION_COOKIE_HTTPONLY": "True",
                "CSRF_COOKIE_SECURE": "True", "SECURE_SSL_REDIRECT": "True", "X_FRAME_OPTIONS": "DENY"}
    for k, bueno in esperado.items():
        if v[k] != bueno:
            anotar("FALLA" if k == "DEBUG" else "AVISO", "crítica" if k == "DEBUG" else "media", "config",
                   f"{k} = {v[k]} (se espera {bueno})", "config/settings.py")
    if v["SESSION_COOKIE_SAMESITE"] not in ("Lax", "Strict"):
        anotar("AVISO", "media", "config", f"SESSION_COOKIE_SAMESITE = {v['SESSION_COOKIE_SAMESITE']}")
    if int(v["SESSION_COOKIE_AGE"]) > 60 * 60 * 24 * 30:
        anotar("AVISO", "baja", "config", f"Sesión dura {int(v['SESSION_COOKIE_AGE']) // 86400} días (máx. sugerido 30)")
    if int(v["SECURE_HSTS_SECONDS"] or 0) < 31536000:
        anotar("AVISO", "baja", "config", f"HSTS de {v['SECURE_HSTS_SECONDS']} s: subir a 1 año con el dominio estable")
    if "MD5" in v["PASSWORD_HASHERS"]:
        anotar("FALLA", "crítica", "config", "Hash MD5 de contraseñas fuera de las pruebas", "config/settings.py")
    # Secretos fuera del código y .env.example completo
    texto = (RAIZ / "config/settings.py").read_text(encoding="utf-8")
    usadas = set(re.findall(r"os\.environ(?:\.get)?[\[(]\"([A-Z_]+)\"", texto)) | set(re.findall(r"env_(?:bool|lista)\(\"([A-Z_]+)\"", texto))
    ejemplo = (RAIZ / ".env.example").read_text(encoding="utf-8") if (RAIZ / ".env.example").exists() else ""
    faltan = sorted(n for n in usadas if n not in ejemplo and n not in ("RENDER", "RENDER_EXTERNAL_HOSTNAME"))
    if faltan:
        anotar("AVISO", "baja", "config", f".env.example no documenta: {', '.join(faltan)}", ".env.example")
    else:
        anotar("OK", "-", "config", f".env.example documenta las {len(usadas)} variables de settings")
    if re.search(r"SECRET_KEY\s*=\s*['\"][^'\"]{20,}['\"]", texto):
        anotar("FALLA", "crítica", "config", "SECRET_KEY escrita en el código", "config/settings.py")


# -------------------------------------------------------------------------------------------------- cabeceras
def rev_cabeceras():
    """Pide páginas con la configuración de producción (sin servidor ni red) y mira cabeceras y cookies."""
    codigo = r"""
import json, django; django.setup()
from django.test.utils import setup_test_environment, override_settings
setup_test_environment()
from django.test import Client
from django.db import transaction
sal = {}
with override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                                 "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}):
    c = Client(HTTP_HOST="tallerya.co")
    with transaction.atomic():
        for url in ["/", "/cuenta/entrar/", "/foro/"]:
            r = c.get(url, secure=True)
            sal[url] = {"status": r.status_code, "h": {k: v for k, v in r.headers.items()},
                        "cookies": {n: {"secure": bool(m["secure"]), "httponly": bool(m["httponly"]), "samesite": m["samesite"]}
                                    for n, m in r.cookies.items()}}
        r = c.get("/cuenta/entrar/")  # http: debe redirigir a https
        sal["http"] = {"status": r.status_code, "loc": r.headers.get("Location", "")}
        transaction.set_rollback(True)
print("JSON" + json.dumps(sal))
"""
    cod, out, err = correr([PY, "-c", codigo], {**env_produccion(), "DJANGO_SETTINGS_MODULE": "config.settings"})
    linea = next((l for l in out.splitlines() if l.startswith("JSON")), None)
    if not linea:
        anotar("FALLA", "alta", "cabeceras", "No se pudieron pedir páginas en modo producción",
               (err or out).strip().splitlines()[-1][:120] if (err or out).strip() else "")
        return
    datos = json.loads(linea[4:])
    h = {k.lower(): v for k, v in datos["/"]["h"].items()}
    reglas = [
        ("strict-transport-security", "alta", "HSTS"),
        ("x-frame-options", "media", "X-Frame-Options"),
        ("x-content-type-options", "media", "nosniff"),
        ("referrer-policy", "baja", "Referrer-Policy"),
        ("cross-origin-opener-policy", "baja", "COOP"),
        ("permissions-policy", "baja", "Permissions-Policy"),
    ]
    for cab, sev, nombre in reglas:
        if cab in h:
            anotar("OK", "-", "cabeceras", f"{nombre}: {h[cab][:70]}")
        else:
            anotar("AVISO", sev, "cabeceras", f"Falta la cabecera {nombre}")
    csp = h.get("content-security-policy") or ""
    csp_ro = h.get("content-security-policy-report-only") or ""
    if not csp and not csp_ro:
        anotar("AVISO", "media", "cabeceras", "Sin Content-Security-Policy")
    elif csp:
        debiles = [d for d in ("'unsafe-eval'", "*") if re.search(rf"script-src[^;]*{re.escape(d)}", csp)]
        nota = " con 'unsafe-inline' en script-src (falta nonce)" if re.search(r"script-src[^;]*'unsafe-inline'", csp) else ""
        anotar("AVISO" if (debiles or nota) else "OK", "baja" if nota and not debiles else "media", "cabeceras",
               f"CSP aplicada{nota}{' y ' + ', '.join(debiles) if debiles else ''}")
        for falta in ("object-src", "base-uri", "frame-ancestors"):
            if falta not in csp:
                anotar("AVISO", "baja", "cabeceras", f"CSP sin {falta}")
    else:
        anotar("AVISO", "baja", "cabeceras", "CSP solo en modo Report-Only")
    if "server" in h and re.search(r"\d", h["server"]):
        anotar("AVISO", "baja", "cabeceras", f"Server revela versión: {h['server'][:40]}")
    for url, d in datos.items():
        if url == "http":
            continue
        for nombre, m in d.get("cookies", {}).items():
            if not m["secure"] or (nombre == "sessionid" and not m["httponly"]) or not m["samesite"]:
                anotar("AVISO", "media", "cabeceras", f"Cookie {nombre} sin Secure/HttpOnly/SameSite", url)
    if datos["http"]["status"] not in (301, 302) or not datos["http"]["loc"].startswith("https://"):
        anotar("AVISO", "alta", "cabeceras", "HTTP no redirige a HTTPS")
    else:
        anotar("OK", "-", "cabeceras", "HTTP → HTTPS y cookies con Secure/SameSite")


# ----------------------------------------------------------------------------------------------------- codigo
PATRONES = [  # (regex, extensiones, severidad, texto)
    (r"\|\s*safe\b", (".html",), "media", "Filtro |safe (posible XSS)"),
    (r"\bmark_safe\(", (".py",), "media", "mark_safe (posible XSS)"),
    (r"autoescape\s+off", (".html",), "alta", "autoescape off"),
    (r"\.(innerHTML|outerHTML)\s*\+?=|insertAdjacentHTML\(", (".js", ".html"), "baja", "innerHTML/insertAdjacentHTML: ¿dato escapado?"),
    (r"\bcsrf_exempt\b", (".py",), "alta", "Vista sin CSRF"),
    (r"\.raw\(|\.extra\(|cursor\(\)|RawSQL\(", (".py",), "alta", "SQL crudo"),
    (r"\beval\(|new Function\(", (".js", ".html", ".py"), "alta", "eval / new Function"),
    (r"pickle\.loads?\(|yaml\.load\((?!.*SafeLoader)", (".py",), "alta", "Deserialización insegura"),
    (r"shell\s*=\s*True", (".py",), "alta", "subprocess con shell=True"),
    (r"redirect\(\s*request\.(GET|POST)", (".py",), "alta", "Redirección abierta (next sin validar)"),
    (r"HttpResponse\(\s*request\.(GET|POST)", (".py",), "alta", "Eco de entrada sin escapar"),
    (r"<script[^>]+src=\"https?://(?![^\"]*integrity)", (".html",), "media", "Script de CDN sin integrity (SRI)"),
    (r"FileField\(|ImageField\(", (".py",), "baja", "Campo de archivo: ¿valida tipo, tamaño y nombre?"),
    (r"\.objects\.get\(\s*pk\s*=\s*pk\s*\)|get_object_or_404\(\s*\w+\s*,\s*pk\s*=\s*pk\s*\)", (".py",), "media",
     "Objeto por pk sin filtrar por dueño (¿IDOR?)"),
]


def rev_codigo():
    reglas = permitidos()
    contador = {}
    for ruta in archivos_git():
        if "/tests" in ruta or ruta.split("/")[-1].startswith("tests") or "/migrations/" in ruta or "/admin" in ruta:
            continue
        ext = Path(ruta).suffix
        if ext not in (".py", ".html", ".js") or ruta.endswith(".min.js") or "/vendor/" in ruta:
            continue
        try:
            lineas = (RAIZ / ruta).read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for regex, exts, sev, texto in PATRONES:
            if ext not in exts:
                continue
            for n, linea in enumerate(lineas, 1):
                if re.search(regex, linea) and not linea.lstrip().startswith(("#", "//")):
                    if any(ruta.startswith(r) and re.search(p, linea) for r, p in reglas):
                        contador["permitidos"] = contador.get("permitidos", 0) + 1
                        continue
                    anotar("AVISO", sev, "codigo", texto, f"{ruta}:{n}")
    # fetch() que manda POST sin token CSRF en el mismo archivo
    for ruta in archivos_git():
        if Path(ruta).suffix in (".js", ".html") and "/tests" not in ruta:
            try:
                t = (RAIZ / ruta).read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError):
                continue
            if re.search(r"fetch\([^)]*\{[^}]*method:\s*[\"']POST", t, re.S) and not re.search(r"X-CSRFToken|csrfmiddlewaretoken|FormData\(", t):
                anotar("AVISO", "media", "codigo", "fetch POST sin X-CSRFToken visible", ruta)
    anotar("OK", "-", "codigo", f"Patrones revisados; {contador.get('permitidos', 0)} casos ya aceptados en permitidos.txt")


# --------------------------------------------------------------------------------------------------- secretos
SECRETO = re.compile(
    r"(AKIA[0-9A-Z]{16}|sk_live_[0-9a-zA-Z]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[0-9A-Za-z]{30,}|"
    r"xox[abp]-[0-9A-Za-z-]{20,}|AIza[0-9A-Za-z_-]{35}|GOCSPX-[0-9A-Za-z_-]{20,}|"
    r"(?i:(secret|password|passwd|token|api_key|clave)[\"']?\s*[:=]\s*[\"'][^\"'\s{}<>%]{12,}[\"']))")
IGNORAR_SECRETO = re.compile(r"(?i)ejemplo|example|dummy|insegura|cambiar|xxxx|placeholder|test|prueba|<|\{\{|os\.environ")


def _aceptado(reglas, ruta, linea):
    return any(ruta.startswith(r) and re.search(p, linea) for r, p in reglas)


def rev_secretos():
    reglas = permitidos()
    encontrados = 0
    for ruta in archivos_git():
        if Path(ruta).suffix in (".png", ".jpg", ".jpeg", ".webp", ".glb", ".pdf", ".ico", ".woff2", ".svg"):
            continue
        try:
            for n, linea in enumerate((RAIZ / ruta).read_text(encoding="utf-8").splitlines(), 1):
                if SECRETO.search(linea) and not IGNORAR_SECRETO.search(linea) and "tests" not in ruta                         and not _aceptado(reglas, ruta, linea):
                    anotar("FALLA", "crítica", "secretos", "Posible secreto en el repositorio (valor no mostrado)", f"{ruta}:{n}")
                    encontrados += 1
        except (UnicodeDecodeError, FileNotFoundError, OSError):
            continue
    # Historial: solo líneas añadidas que parezcan secretos; se informa commit y archivo
    cod, out, _ = correr("git log --all -p --no-color -U0 --diff-filter=AM -- . "
                         "\":(exclude)*.svg\" \":(exclude)*.json\" \":(exclude)*.glb\" \":(exclude)informes_noche\"",
                         timeout=300)
    commit, archivo, vistos = "", "", set()
    for linea in out.splitlines():
        if linea.startswith("commit "):
            commit = linea[7:15]
        elif linea.startswith("+++ b/"):
            archivo = linea[6:]
        elif linea.startswith("+") and SECRETO.search(linea) and not IGNORAR_SECRETO.search(linea)                 and "tests" not in archivo and not _aceptado(reglas, archivo, linea[1:]):
            if (commit, archivo) not in vistos:
                vistos.add((commit, archivo))
                anotar("FALLA", "alta", "secretos", "Posible secreto en el historial de git (valor no mostrado)",
                       f"commit {commit} · {archivo}")
    # Lo que debe quedarse en local
    for carpeta in LOCALES:
        _, rastreados, _ = correr(["git", "ls-files", carpeta])
        if rastreados.strip():
            anotar("FALLA", "alta", "secretos", f"{carpeta} está en el repositorio ({len(rastreados.splitlines())} archivos)")
        cod, _, _ = correr(["git", "check-ignore", "-q", carpeta])
        if cod != 0 and (RAIZ / carpeta).exists():
            anotar("AVISO", "media", "secretos", f"{carpeta} no está en .gitignore", ".gitignore")
    if not encontrados and not vistos:
        anotar("OK", "-", "secretos", "Sin secretos en archivos ni en el historial; lo local está ignorado")


# ----------------------------------------------------------------------------------------------- dependencias
def rev_dependencias(sin_red):
    if sin_red:
        anotar("AVISO", "-", "dependencias", "Saltado (--sin-red)")
        return
    cod, out, err = correr([PY, "-m", "pip_audit", "-r", "requirements.txt", "-f", "json", "--progress-spinner", "off"], timeout=600)
    if "No module named pip_audit" in err:
        anotar("AVISO", "media", "dependencias", "pip-audit no está instalado: venv/Scripts/pip install pip-audit")
    else:
        try:
            datos = json.loads(out[out.index("{"):])
            vulns = [(d["name"], d["version"], v["id"]) for d in datos.get("dependencies", []) for v in d.get("vulns", [])]
            for nombre, version, vid in vulns:
                anotar("FALLA", "alta", "dependencias", f"{nombre} {version}: {vid}", "requirements.txt")
            if not vulns:
                anotar("OK", "-", "dependencias", f"pip-audit: {len(datos.get('dependencies', []))} paquetes sin vulnerabilidades conocidas")
        except (ValueError, KeyError):
            anotar("AVISO", "media", "dependencias", "pip-audit no devolvió JSON", (err or out).strip()[-120:])
    cod, out, err = correr("npm audit --json", timeout=300)
    try:
        meta = json.loads(out)["metadata"]["vulnerabilities"]
        graves = meta.get("critical", 0) + meta.get("high", 0)
        total = sum(meta.values()) - meta.get("total", 0) if "total" in meta else sum(meta.values())
        if graves:
            anotar("AVISO", "media", "dependencias", f"npm audit: {graves} altas/críticas (solo compilan CSS/JS; no van al servidor)", "package.json")
        elif total:
            anotar("AVISO", "baja", "dependencias", f"npm audit: {total} leves/moderadas (herramientas de compilación)", "package.json")
        else:
            anotar("OK", "-", "dependencias", "npm audit sin vulnerabilidades")
    except (ValueError, KeyError):
        anotar("AVISO", "baja", "dependencias", "npm audit no corrió", (err or out).strip()[-100:])


# ----------------------------------------------------------------------------------------------- autorizacion
def rev_autorizacion():
    cod, out, err = correr([PY, "manage.py", "test", "config.tests_seguridad", "cuentas.tests_seguridad", "-v", "1"], timeout=600)
    res = (err + out).strip().splitlines()
    resumen = next((l for l in reversed(res) if l.startswith(("OK", "FAILED"))), "sin resultado")
    corridas = next((l for l in reversed(res) if l.startswith("Ran ")), "")
    if cod == 0:
        anotar("OK", "-", "autorizacion", f"IDOR, barrido anónimo, panel y límites: {corridas}")
    else:
        fallos = [l for l in res if l.startswith(("FAIL:", "ERROR:"))]
        for f in fallos[:10]:
            anotar("FALLA", "alta", "autorizacion", f[:110], "config/tests_seguridad.py")
        if not fallos:
            anotar("FALLA", "alta", "autorizacion", resumen)


# -------------------------------------------------------------------------------------------------- velocidad
def rev_velocidad():
    """Consultas y ms de las páginas principales sobre db.sqlite3 (en una transacción que se deshace)."""
    codigo = r"""
import json, time, django; django.setup()
from django.test.utils import setup_test_environment, CaptureQueriesContext
setup_test_environment()
from django.db import connection, transaction
from django.test import Client
from django.contrib.auth import get_user_model
from django.db.models import Count
sal = []
with transaction.atomic():
    c = Client()
    from talleres.models import Taller
    from foro.models import Pregunta
    t = Taller.objects.filter(activo=True).first()
    p = Pregunta.objects.filter(visible=True).annotate(n=Count("respuestas")).order_by("-n").first()
    paginas = [("Portada", "/"), ("Talleres", "/talleres/"), ("Foro", "/foro/"), ("Rodadas", "/foro/rodadas/"),
               ("Cupones", "/cupones/"), ("Emergencias", "/emergencias/")]
    if t: paginas.append(("Ficha de taller", t.get_absolute_url()))
    if p: paginas.append((f"Pregunta ({p.n} resp.)", p.get_absolute_url()))
    def medir(nombre, url, cliente):
        mejor, n, tam, status = 1e9, 0, 0, 0
        for _ in range(3):
            with CaptureQueriesContext(connection) as q:
                t0 = time.perf_counter(); r = cliente.get(url, HTTP_ACCEPT_ENCODING="gzip"); dt = time.perf_counter() - t0
            mejor, n, tam, status = min(mejor, dt), len(q), len(r.content), r.status_code
        sal.append({"pagina": nombre, "url": url, "ms": round(mejor * 1000), "consultas": n, "kb": round(tam / 1024, 1), "status": status})
    for nombre, url in paginas:
        medir(nombre, url, c)
    U = get_user_model()
    u = U.objects.filter(motociclista__motos__isnull=False).annotate(n=Count("motociclista__motos")).order_by("-n").first()
    if u:
        c2 = Client(); c2.force_login(u)
        medir("Portada (con sesión)", "/", c2)
        medir(f"Mi garaje ({u.n} motos)", "/garaje/", c2)
        m = u.motociclista.motos.first()
        medir("Ficha de moto", f"/garaje/{m.pk}/", c2)
        medir("Vista 3D", f"/garaje/{m.pk}/vista-3d/", c2)
        medir("Mi cuenta", "/cuenta/", c2)
    tu = U.objects.filter(taller__activo=True).first()
    if tu:
        c3 = Client(); c3.force_login(tu)
        medir("Mi taller", "/mi-taller/", c3)
        medir("Citas del taller", "/mi-taller/citas/", c3)
    transaction.set_rollback(True)
print("JSON" + json.dumps(sal))
"""
    cod, out, err = correr([PY, "-c", codigo], {"DJANGO_DEBUG": "1", "DJANGO_SETTINGS_MODULE": "config.settings"})
    linea = next((l for l in out.splitlines() if l.startswith("JSON")), None)
    if not linea:
        anotar("FALLA", "media", "velocidad", "No se pudo medir", (err or out).strip().splitlines()[-1][:120] if (err or out).strip() else "")
        return
    filas = json.loads(linea[4:])
    (AQUI / "ultima_velocidad.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in filas:
        lento = f["ms"] > 300 or f["consultas"] > 35 or f["status"] >= 400
        sev = "media" if (f["ms"] > 600 or f["consultas"] > 60) else "baja"
        anotar("AVISO" if lento else "OK", sev, "velocidad",
               f"{f['pagina']}: {f['ms']} ms, {f['consultas']} consultas, {f['kb']} KB (HTTP {f['status']})", f["url"])


# -------------------------------------------------------------------------------------------------- estaticos
def rev_estaticos():
    texto = (RAIZ / "config/settings.py").read_text(encoding="utf-8")
    est = (RAIZ / "talleres/estaticos.py")
    if "CompressedManifestStaticFilesStorage" in (est.read_text(encoding="utf-8") if est.exists() else "") or "CompressedManifest" in texto:
        anotar("OK", "-", "estaticos", "WhiteNoise con manifest y compresión en producción")
    else:
        anotar("AVISO", "media", "estaticos", "Estáticos sin WhiteNoise manifest (caché larga + .br/.gz)")
    if "GZipMiddleware" not in texto:
        anotar("AVISO", "baja", "estaticos", "HTML sin compresión (GZipMiddleware)")
    tw = RAIZ / "talleres/static/talleres/css/tw.css"
    if tw.exists():
        kb = tw.stat().st_size / 1024
        anotar("OK" if kb < 80 else "AVISO", "baja", "estaticos", f"tw.css {kb:.0f} KB ({'purgado' if kb < 80 else 'sin purgar?'})")
    pesados = []
    for ruta in archivos_git():
        p = RAIZ / ruta
        if "/static/" in ruta and p.suffix in (".css", ".js") and p.exists() and p.stat().st_size > 150 * 1024:
            pesados.append((ruta, p.stat().st_size // 1024))
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif") and p.exists() and p.stat().st_size > 300 * 1024 and "/static/" in ruta:
            pesados.append((ruta, p.stat().st_size // 1024))
        if p.suffix.lower() == ".glb" and p.exists() and p.stat().st_size > 2 * 1024 * 1024:
            pesados.append((ruta, p.stat().st_size // 1024))
    for ruta, kb in sorted(pesados, key=lambda x: -x[1])[:12]:
        anotar("AVISO", "baja", "estaticos", f"Archivo estático pesado: {kb} KB", ruta)
    # El 3D y el despiece solo deben cargarse en sus páginas, nunca desde base.html
    base = (RAIZ / "templates/base.html").read_text(encoding="utf-8")
    for js in ("three", "moto3d", "despiece.js"):
        if js in base:
            anotar("AVISO", "media", "estaticos", f"base.html carga {js} en todas las páginas", "templates/base.html")
    imgs_sin_lazy = 0
    for ruta in archivos_git():
        if ruta.endswith(".html"):
            t = (RAIZ / ruta).read_text(encoding="utf-8", errors="ignore")
            imgs_sin_lazy += len(re.findall(r"<img(?![^>]*loading=)[^>]*>", t))
    anotar("AVISO" if imgs_sin_lazy > 15 else "OK", "baja", "estaticos", f"{imgs_sin_lazy} <img> sin loading=\"lazy\"/\"eager\" explícito")
    media = RAIZ / "media"
    if media.exists():
        grandes = [f for f in media.rglob("*") if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp") and f.stat().st_size > 800 * 1024]
        anotar("AVISO" if grandes else "OK", "baja", "estaticos", f"{len(grandes)} fotos subidas de más de 800 KB en media/ (¿se reducen al subir?)")


# ------------------------------------------------------------------------------------------------------ main
def tabla():
    hallazgos.sort(key=lambda h: ({"FALLA": 0, "AVISO": 1, "OK": 2}[h["estado"]], SEV_ORDEN.get(h["sev"], 9), h["seccion"]))
    filas = [("Estado", "Sev.", "Sección", "Hallazgo", "Dónde")] + [
        (h["estado"], h["sev"], h["seccion"], h["texto"], h["donde"]) for h in hallazgos]
    anchos = [max(len(str(f[i])) for f in filas) for i in range(4)]
    for i, f in enumerate(filas):
        print("  ".join(str(c).ljust(min(anchos[j], 95)) for j, c in enumerate(f[:4])) + (f"  {f[4]}" if f[4] else ""))
        if i == 0:
            print("-" * min(sum(anchos) + 8, 140))
    n = {e: sum(1 for h in hallazgos if h["estado"] == e) for e in ("FALLA", "AVISO", "OK")}
    print(f"\nTotal: {n['FALLA']} fallas · {n['AVISO']} avisos · {n['OK']} OK")


def main():
    for flujo in (sys.stdout, sys.stderr):  # tildes bien aunque la consola de Windows sea cp1252
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", default="", help="secciones separadas por coma")
    ap.add_argument("--sin-red", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    elegidas = [s for s in (a.solo.split(",") if a.solo else SECCIONES) if s in SECCIONES]
    for s in elegidas:
        print(f"· {s}…", file=sys.stderr, flush=True)
        try:
            (rev_dependencias(a.sin_red) if s == "dependencias" else globals()[f"rev_{s}"]())
        except Exception as e:  # una sección rota no tumba las demás
            anotar("FALLA", "media", s, f"La comprobación falló: {e.__class__.__name__}: {str(e)[:90]}")
    tabla()
    if a.json:
        Path(a.json).write_text(json.dumps(hallazgos, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if any(h["estado"] == "FALLA" for h in hallazgos) else 0)


if __name__ == "__main__":
    main()
