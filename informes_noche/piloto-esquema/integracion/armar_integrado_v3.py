# Genera informes_noche/piloto-esquema/integrado.html a partir de index.html (sin editar index.html).
import re, pathlib, sys

base = pathlib.Path(r"C:\dev\TallerYa\informes_noche\piloto-esquema")
src = (base / "index.html").read_text(encoding="utf-8")
L = src.splitlines()
plantilla = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")


def entre(ini, fin, incluir_fin=True):
    i = next(n for n, l in enumerate(L) if ini in l)
    j = next(n for n in range(i + 1, len(L)) if fin in L[n])
    return "\n".join(L[i:j + 1] if incluir_fin else L[i:j])

# CSS del dibujo, la ficha, el funcionamiento y las cadenas (sin reglas genéricas de la página)
css = entre("/* piezas del SVG */", "table{width", incluir_fin=False)
# El SVG de la lámina
lamina = entre('<svg id="lamina"', "</svg>")
# Cómo funciona: el SVG y su texto (los botones los pone la plantilla)
fn = entre('<div class="desliza" id="fnDesliza">', "</svg>") + "\n      </div>"
# Tabla de intervalos
tabla = entre("<table>", "</table>")
# Fuentes: listas de seguro / aproximado / fuentes
m = re.search(r'<section id="fuentes">.*?<div class="dos">(.*)</section>', src, re.S)
fuentes = m.group(1)
fuentes = fuentes.replace('class="tarjeta" style="padding:12px 18px;margin-top:14px"', 'class="esq-fuente"') \
                 .replace('class="tarjeta" style="padding:12px 18px"', 'class="esq-fuente"')
# Logo del sitio (parciales/logo.html sin etiquetas de plantilla)
logo = pathlib.Path(r"C:\dev\TallerYa\templates\parciales\logo.html").read_text(encoding="utf-8")
logo = re.sub(r"\{#.*?#\}", "", logo, flags=re.S)
logo = re.sub(r"\{% if lema %\}.*?\{% else %\}(.*?)\{% endif %\}", r"\1", logo, flags=re.S)
logo = re.sub(r"\{% if lema %\}.*?\{% endif %\}", "", logo, flags=re.S)
logo = logo.replace("{{ clase }}", "h-10 w-auto").strip()
assert "{%" not in logo and "{{" not in logo, logo[:300]
# El script completo del piloto
js = re.search(r"<script>(.*)</script>", src, re.S).group(1)

out = (plantilla.replace("/*CSS_PILOTO*/", css).replace("<!--LAMINA-->", lamina)
       .replace("<!--FN-->", fn).replace("<!--TABLA-->", tabla)
       .replace("<!--FUENTES-->", fuentes).replace("/*JS_PILOTO*/", js).replace("<!--LOGO-->", logo))
(base / "integrado.html").write_text(out, encoding="utf-8")
print("ok", len(out))
