"""Arma un HTML de un solo archivo (CSS, arte, biblioteca, visor 3D, datos y motor adentro) para probar una lámina en el
panel del navegador, que abre los archivos locales como data: y no carga rutas relativas.
La plantilla es freno.html; el título y la descripción salen del JSON de la lámina.
El motor es uno solo (esquema.js + esquema.css): un JSON con «v2» se ve con el modelo v2 y uno sin «v2» con el viejo.
Sale como prueba-<nombre del JSON>.html (un respaldo «-v1» usa el arte de su lámina, D["arte"]).

Uso: python armar_un_archivo.py datos/nmax-fig22.json     →   prueba-nmax-fig22.html (junto a este script)
     python armar_un_archivo.py datos/nmax-fig26-v1.json  →   prueba-nmax-fig26-v1.html
"""
import html, json, pathlib, re, sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # consola de Windows (cp1252)

AQUI = pathlib.Path(__file__).resolve().parent
datos_p = pathlib.Path(sys.argv[1]).resolve()
D = json.loads(datos_p.read_text(encoding="utf-8"))
leer = lambda p: p.read_text(encoding="utf-8")
pagina = leer(AQUI / "freno.html")
arte_p = datos_p.with_name(datos_p.stem + "-arte.js")
if not arte_p.exists():
    arte_p = datos_p.with_name(D["arte"] + "-arte.js")   # la v2 usa el arte de la lámina de origen
arte = leer(arte_p)
MOTOR = "esquema.js"
datos_js = json.dumps(D, ensure_ascii=False).replace("</", "<\\/")
lleva3d = any("forma3d" in F for F in D.get("fichas", {}).values()) or any("comun" in p for p in D["piezas"])


def script(codigo):
    return lambda _m: "<script>\n" + codigo + "</script>"


out = pagina.replace('<link rel="stylesheet" href="esquema.css">', "<style>\n" + leer(AQUI / "esquema.css") + "</style>")
out = re.sub(r'<script src="datos/[^"]+-arte\.js"></script>', script(arte), out)
out = re.sub(r'<script src="piezas-comunes\.js"></script>', script(leer(AQUI / "piezas-comunes.js")), out)
out = re.sub(r'<script src="esquema3d\.js"></script>', script(leer(AQUI / "esquema3d.js")) if lleva3d else "", out)
datos_tag = '<script type="application/json" id="esq-datos">' + datos_js + "</script>\n"
if lleva3d:
    # three.js como texto: el visor lo importa por Blob solo al abrir una ficha con modelo
    three = leer(AQUI.parents[2] / "garaje/static/garaje/vendor/three-0.160.0/build/three.module.min.js")
    assert "</script" not in three.lower() and "<!--" not in three
    datos_tag = '<script type="text/plain" id="esq-three">' + three + "</script>\n" + datos_tag
out = re.sub(r'<script src="' + re.escape(MOTOR) + r'"></script>', lambda _m: datos_tag + "<script>\n" + leer(AQUI / MOTOR) + "</script>", out)
# título y descripción de esta lámina (la plantilla es la del freno)
titulo = "Piloto " + re.sub(r"\s*·.*$", "", html.unescape(re.sub(r"<[^>]+>", "", D["visor"]["titulo"])))[:60]
out = re.sub(r"<title>.*?</title>", lambda _m: f"<title>{html.escape(titulo)}</title>", out, count=1)
desc = f"Esquema piloto de TallerYa: {D['visor']['titulo']} ({D['visor'].get('sub', '')}). Prototipo local."
out = re.sub(r'<meta name="description" content="[^"]*">', lambda _m: f'<meta name="description" content="{html.escape(desc)}">', out, count=1)
assert 'src="' not in out and "esquema.css" not in out.split("<style>")[0], "faltó reemplazar algún archivo"
destino = AQUI / f"prueba-{datos_p.stem}.html"
destino.write_text(out, encoding="utf-8")
print(destino.name, len(out), "bytes ·", titulo)
