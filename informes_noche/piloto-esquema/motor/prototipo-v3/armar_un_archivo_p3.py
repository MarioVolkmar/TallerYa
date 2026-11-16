"""Arma el prototipo UX v3 en un solo HTML (para abrirlo en el celular o en el panel del navegador, que no carga rutas relativas).
Mismo método que ../armar_un_archivo.py, pero parte de prototipo-v3/fig26.html y suma prototipo.css y prototipo.js.
No toca los archivos de piloto-esquema. Sale como prototipo-v3/prueba-p3-fig26.html.

Uso (desde la raíz del proyecto): venv/Scripts/python.exe informes_noche/piloto-esquema/motor/prototipo-v3/armar_un_archivo_p3.py
"""
import json, pathlib, re

AQUI = pathlib.Path(__file__).resolve().parent
MOTOR = AQUI.parent
leer = lambda p: p.read_text(encoding="utf-8")
pagina = leer(AQUI / "fig26.html")
D = json.loads(leer(MOTOR / "datos/nmax-fig26.json"))
datos_js = json.dumps(D, ensure_ascii=False).replace("</", "<\\/")
script = lambda codigo: (lambda _m: "<script>\n" + codigo + "</script>")
estilo = lambda codigo: (lambda _m: "<style>\n" + codigo + "</style>")

out = re.sub(r'<link rel="stylesheet" href="\.\./esquema\.css">', estilo(leer(MOTOR / "esquema.css")), pagina)
out = re.sub(r'<link rel="stylesheet" href="prototipo\.css">', estilo(leer(AQUI / "prototipo.css")), out)
out = re.sub(r'<script src="\.\./datos/[^"]+-arte\.js"></script>', script(leer(MOTOR / "datos/nmax-fig26-arte.js")), out)
out = re.sub(r'<script src="\.\./piezas-comunes\.js"></script>', script(leer(MOTOR / "piezas-comunes.js")), out)
out = re.sub(r'<script src="\.\./esquema3d\.js"></script>', script(leer(MOTOR / "esquema3d.js")), out)
three = leer(MOTOR.parents[2] / "garaje/static/garaje/vendor/three-0.160.0/build/three.module.min.js")
assert "</script" not in three.lower() and "<!--" not in three
datos_tag = '<script type="text/plain" id="esq-three">' + three + '</script>\n<script type="application/json" id="esq-datos">' + datos_js + "</script>\n"
out = re.sub(r'<script src="\.\./esquema\.js"></script>', lambda _m: datos_tag + "<script>\n" + leer(MOTOR / "esquema.js") + "</script>", out)
out = re.sub(r'<script src="prototipo\.js"></script>', script(leer(AQUI / "prototipo.js")), out)
assert 'src="' not in out and 'href="../' not in out and 'href="prototipo' not in out, "faltó reemplazar algún archivo"
destino = AQUI / "prueba-p3-fig26.html"
destino.write_text(out, encoding="utf-8")
print(destino, len(out), "bytes")
