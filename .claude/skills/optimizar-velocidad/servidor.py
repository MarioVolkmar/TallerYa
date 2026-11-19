"""Tiempo y consultas SQL por URL, en el servidor (test client de Django, base local, solo GET).

Uso:
  venv/Scripts/python.exe .claude/skills/optimizar-velocidad/servidor.py / /talleres/ /mecanicos/ \
      --usuario correo@x.com /garaje/3/ /garaje/3/despiece.json
- Las URL antes de --usuario van anónimas; las de después, con sesión de ese usuario (force_login: sin contraseña).
- Mejor de 3 corridas (la 1.ª calienta cachés). Todo dentro de una transacción que se deshace: no cambia la base.
- --json archivo.json guarda el resultado para comparar antes/después. --top N muestra las N consultas más repetidas.
Salida: una línea por URL (ms, consultas, repetidas, KB, KB gzip).
"""
import argparse, gzip, json, logging, os, sys, time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()
from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.db import connection, transaction  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import CaptureQueriesContext  # noqa: E402

if "testserver" not in settings.ALLOWED_HOSTS and "*" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = [*settings.ALLOWED_HOSTS, "testserver"]


def limpiar(url):
    # Git Bash convierte "/talleres/" en "C:/Program Files/Git/talleres/": se deshace aquí
    i = url.find("/Git/")
    return url[i + 4:] if ":" in url[:3] and i >= 0 else url


def medir(cliente, url, top):
    mejor = None
    for _ in range(3):
        with CaptureQueriesContext(connection) as q:
            t = time.perf_counter()
            r = cliente.get(url, HTTP_ACCEPT_ENCODING="identity")
            ms = (time.perf_counter() - t) * 1000
        cuerpo = b"".join(r.streaming_content) if r.streaming else r.content
        if mejor is None or ms < mejor["ms"]:
            sql = [x["sql"] for x in q.captured_queries]
            rep = Counter(sql)
            mejor = {"url": url, "estado": r.status_code, "ms": round(ms), "consultas": len(sql),
                     "repetidas": sum(c - 1 for c in rep.values() if c > 1),
                     "kb": round(len(cuerpo) / 1024, 1), "kb_gzip": round(len(gzip.compress(cuerpo)) / 1024, 1),
                     "top": [f"{c}× {s[:110]}" for s, c in rep.most_common(top) if c > 1]}
    return mejor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--usuario", nargs="+", metavar=("CORREO", "URL"))
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=0)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    logging.getLogger("django.request").setLevel(logging.ERROR)
    a.urls = [limpiar(u) for u in a.urls]
    if a.usuario:
        a.usuario = [a.usuario[0], *map(limpiar, a.usuario[1:])]
    grupos = [(None, a.urls)]
    if a.usuario:
        grupos.append((a.usuario[0], a.usuario[1:]))
    res = []
    with transaction.atomic():
        for correo, urls in grupos:
            c = Client()
            if correo:
                u = get_user_model().objects.filter(email__iexact=correo).first()
                if not u:
                    sys.exit(f"No existe el usuario {correo}")
                c.force_login(u)
            for url in urls:
                m = medir(c, url, a.top)
                m["quien"] = "sesión" if correo else "anónimo"
                res.append(m)
                print(f"{url:32} {m['quien']:8} {m['estado']} {m['ms']:5} ms {m['consultas']:3} consultas "
                      f"({m['repetidas']} repetidas)  {m['kb']} KB / {m['kb_gzip']} KB gzip")
                for linea in m["top"]:
                    print("    ", linea)
        transaction.set_rollback(True)
    if a.json:
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
