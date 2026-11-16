# Genera informes_noche/piloto-esquema/integrado.html a partir de una versión del piloto (por defecto v8.html, sin editarla) y de la plantilla.
# Uso: venv/Scripts/python.exe informes_noche/piloto-esquema/integracion/armar_integrado.py [v8.html]
import re, pathlib, sys

base = pathlib.Path(__file__).resolve().parent.parent
raiz = base.parent.parent
fuente = sys.argv[1] if len(sys.argv) > 1 else "v8.html"
src = (base / fuente).read_text(encoding="utf-8")
plantilla = (base / "integracion" / "plantilla_integrado.html").read_text(encoding="utf-8")


def corte(ini, fin):
    i = src.index(ini)
    return src[i:src.index(fin, i)]

# CSS del piloto desde el escenario (sin las reglas genéricas de su página: body, h1, .envoltura, section…)
css = corte("/* ---------- escenario del despiece", "</style>")
# Su regla «button {…}» es para toda la página del piloto: aquí se limita al esquema para no pisar los botones del sitio
css = re.sub(r"(?m)^button", ":is(.escenario,.hoja) button", css)
# «.visor» en el sitio es la caja del 3D (alto fijo y overflow oculto): el visor del esquema pasa a «.esq-visor»
css = css.replace(".visor{padding:12px}", ".esq-visor{padding:12px}")
# Cuerpo: escenario (visor + ficha) y las fuentes plegadas; la barra fija del celular
cuerpo = corte('<div class="escenario" id="despiece">', "<footer>").rstrip()
cuerpo = cuerpo.replace('class="papel visor"', 'class="papel esq-visor"')
# Lo mismo con «.interruptor» (en el sitio es el switch de 2,6 rem)
css = css.replace(".interruptor", ".esq-interruptor")
cuerpo = cuerpo.replace('class="interruptor"', 'class="esq-interruptor"')
# Y con «.paso» (en el sitio es un circulito de 1,2 rem) y «.leyenda» (en el sitio, una fila flex de colores)
for viejo, nuevo in (("paso", "esq-pasotxt"), ("leyenda", "esq-leyenda")):
    css = re.sub(r"\." + viejo + r"(?=[{ ])", "." + nuevo, css)
    cuerpo = cuerpo.replace(f'class="{viejo}"', f'class="{nuevo}"')
js_cambios = [('class="leyenda"', 'class="esq-leyenda"')]
assert 'esq-visor' in cuerpo and '.esq-visor{' in css
hoja = corte('<div class="hoja" id="hoja"', "<script>")
hoja = hoja[:hoja.index("</div>", hoja.index('id="hojaVer"')) + 6]
js = re.search(r"<script>(.*)</script>", src, re.S).group(1)
for viejo, nuevo in js_cambios:
    js = js.replace(viejo, nuevo)

# Logo del sitio (parciales/logo.html sin etiquetas de plantilla)
logo = (raiz / "templates" / "parciales" / "logo.html").read_text(encoding="utf-8")
logo = re.sub(r"\{#.*?#\}", "", logo, flags=re.S)
logo = re.sub(r"\{% if lema %\}.*?\{% else %\}(.*?)\{% endif %\}", r"\1", logo, flags=re.S)
logo = re.sub(r"\{% if lema %\}.*?\{% endif %\}", "", logo, flags=re.S)
logo = logo.replace("{{ clase }}", "h-10 w-auto").strip()
assert "{%" not in logo and "{{" not in logo, logo[:300]

out = (plantilla.replace("/*CSS_PILOTO*/", css).replace("<!--CUERPO-->", cuerpo)
       .replace("<!--HOJA-->", hoja).replace("/*JS_PILOTO*/", js).replace("<!--LOGO-->", logo))
assert "<!--" + "CUERPO" not in out
(base / "integrado.html").write_text(out, encoding="utf-8")
print("ok", len(out))
