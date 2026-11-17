"""Aplica los hallazgos de una revisora y los guarda en el registro de aprendizaje.

  python aplicar_hallazgos.py <lamina> <revisora> <hallazgos.json> [--probar]
  python aplicar_hallazgos.py --candidatas
  python aplicar_hallazgos.py --reaplicar <lamina>     vuelve a aplicar datos/<lamina>.hallazgos.json tras regenerar con el script de armado

<hallazgos.json>: {"nota": {"mecanica":4.5,"ux":4.6}, "hallazgos":[…]} (la nota va a metricas.py) o solo la lista;
  como máximo 15 hallazgos, los graves primero, cada uno
  {"gravedad":"grave|menor", "lado":"mecanica|ux", "categoria":"…", "campo":"fichas.11.que", "reemplazar":"texto exacto", "por":"texto nuevo", "texto":"qué está mal"}
- «campo» (obligatorio si hay «reemplazar») es la ruta dentro del JSON (puntos; números para listas: «pasos.3.t», «cadenas.0.p.2.1»).
  Si el texto cambió desde la revisión, reintenta sin mirar espacios, mayúsculas ni etiquetas; si no lo encuentra, avisa y va a mano.
- Sin «reemplazar» (dibujo, orden, layout): no se toca, se lista para corregirlo a mano.
- Antes de escribir guarda datos/<lamina>.antes.json (como `autocontrol.py --antes`), así `--rapido` avisa de regresiones.
- Cada hallazgo va a revision/hallazgos.jsonl (lámina, revisora, gravedad, categoría, texto, aplicado).
- Varios hallazgos sobre el mismo campo se aplican juntos sobre el texto original; si se enciman, el aviso dice con cuál.
- Un reemplazo que deja un paso (pasos.N.t o funciona.pasos.N.t) en más de 250 caracteres visibles no se aplica: va a mano.
- --probar: no escribe la lámina ni el registro; dice qué haría.
- --candidatas: categorías que se repiten en 2 o más láminas y todavía no tienen control automático.

Categorías (usar estas para que el conteo sirva): cantidad, rastro-hermana, jerga, sinonimo, relleno-plantilla, genero-numero,
cadena-no-causal, desarme-orden, catalogo-en-prosa, seguridad, dato-sin-fuente, dato-tecnico, toque, etiqueta, dibujo, claridad, otro.
"""
import datetime, json, pathlib, re, shutil, subprocess, sys
from collections import defaultdict

AQUI = pathlib.Path(__file__).resolve().parent
REGISTRO = AQUI / "revision" / "hallazgos.jsonl"
MAXIMO = 15   # una sola revisora (mecánica + UX): como máximo 15, graves primero
# categoría → control de mas_controles.py que ya la atrapa (las demás son candidatas si se repiten)
CUBIERTAS = {"cantidad": "revisar_cantidad_texto", "rastro-hermana": "revisar_rastros", "jerga": "revisar_jerga",
             "relleno-plantilla": "revisar_jerga («(Escribe…)»)", "sinonimo": "revisar_dos_nombres",
             "catalogo-en-prosa": "revisar_estilo_v2 (solo nombres en inglés)", "seguridad": "revisar_seguridad_v2 + regresión"}


TOPE = 250   # pasos del desarme y de «Cómo funciona»: un reemplazo que los deja más largos no se aplica (va a mano, acortando)
LARGO = re.compile(r"^(pasos|funciona\.pasos)\.\d+\.t$")


def largo_visible(t):
    return len(re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", re.sub(r"<[^>]+>", "", t)))


def ir(D, ruta):
    """(contenedor, clave) del campo «a.b.3.c»."""
    partes = ruta.split(".")
    x = D
    for p in partes[:-1]:
        x = x[int(p)] if isinstance(x, list) else x[p]
    u = partes[-1]
    return x, (int(u) if isinstance(x, list) else u)


def textos(x, ruta=""):
    if isinstance(x, str): yield ruta, x
    elif isinstance(x, dict):
        for k, v in x.items(): yield from textos(v, f"{ruta}.{k}" if ruta else k)
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from textos(v, f"{ruta}.{i}" if ruta else str(i))


def en_cadena(D, H):
    """Ronda 7: varios hallazgos sobre el mismo campo se ubican en el texto original y se aplican juntos (de atrás hacia
    adelante). Si dos se enciman, el segundo va a mano diciendo con cuál; si juntos pasan el tope de 250, van a mano."""
    from collections import Counter
    mult = [c for c, n in Counter(h.get("campo") for h in H if h.get("reemplazar") and h.get("campo")).items() if n > 1]
    for campo in mult:
        hs = [h for h in H if h.get("campo") == campo and h.get("reemplazar")]
        try:
            c, k = ir(D, campo); t0 = c[k]
            if not isinstance(t0, str): continue
        except (KeyError, IndexError, ValueError):
            continue
        spans = []
        for h in hs:
            if t0.count(h["reemplazar"]) == 1:
                i = t0.index(h["reemplazar"]); spans.append((i, i + len(h["reemplazar"]), h)); continue
            ms = list(re.finditer(r"(?:<[^>]+>)?\s*".join(re.escape(w) for w in h["reemplazar"].split()), t0, re.I))
            if len(ms) == 1: spans.append((ms[0].start(), ms[0].end(), h))
            else: h["_razon"] = f"{campo}: «{h['reemplazar'][:50]}» no está una sola vez ({len(ms)}); corrígelo a mano"
        spans.sort(key=lambda x: x[0]); keep = []
        for sp in spans:
            if keep and sp[0] < keep[-1][1]:
                sp[2]["_razon"] = f"{campo}: se encima con otro hallazgo del mismo campo («{keep[-1][2]['reemplazar'][:40]}»): combínalos a mano"
            else: keep.append(sp)
        t = t0
        for i, j, h in reversed(keep): t = t[:i] + h.get("por", "") + t[j:]
        if LARGO.match(campo) and largo_visible(t) > max(TOPE, largo_visible(t0)):
            for _i, _j, h in keep: h["_razon"] = f"{campo}: juntos lo dejan en {largo_visible(t)} caracteres (> {TOPE}); ponlos a mano acortando el resto"
            continue
        c[k] = t
        for i, j, h in keep: h["_cadena"] = True; h["reemplazar"] = t0[i:j]
        if len(keep) > 1: print(f"  en cadena: {len(keep)} hallazgos sobre {campo}, aplicados juntos")


def aplicar(lam, revisora, archivo, probar):
    js = AQUI / "datos" / f"{lam}.json"
    D = json.loads(js.read_text(encoding="utf-8"))
    X = json.loads(pathlib.Path(archivo).read_text(encoding="utf-8"))
    # dos formatos: la lista de hallazgos, o {"nota": 4.5 | {"mecanica":4,"ux":4.5}, "hallazgos": [...]}
    nota, H = (X.get("nota"), X.get("hallazgos", [])) if isinstance(X, dict) else (None, X)
    if len(H) > MAXIMO: print(f"aviso: {len(H)} hallazgos; la revisora debía devolver como máximo {MAXIMO}")
    hechos, a_mano, fallidos, avisos = [], [], [], []
    en_cadena(D, H)
    for h in H:
        h["aplicado"] = False
        if h.pop("_cadena", False): h["aplicado"] = True; hechos.append(h); continue
        if h.get("_razon"): avisos.append(h.pop("_razon")); a_mano.append(h); continue
        if not h.get("reemplazar"):
            a_mano.append(h); continue
        if not h.get("campo"):
            h["error"] = "falta «campo» (ruta del texto, p. ej. fichas.11.que): sin campo no se aplica"; fallidos.append(h); continue
        try:
            c, k = ir(D, h["campo"]); t = c[k]
            if not isinstance(t, str): raise ValueError(f"{h['campo']} no es un texto")
            n = t.count(h["reemplazar"])
            if n == 1 and LARGO.match(h["campo"]) and largo_visible(t.replace(h["reemplazar"], h.get("por", ""))) > max(TOPE, largo_visible(t)):
                nuevo = largo_visible(t.replace(h["reemplazar"], h.get("por", "")))
                avisos.append(f"{h['campo']}: quedaría en {nuevo} caracteres (> {TOPE}); no se aplicó: ponlo a mano acortando el resto (sin quitar avisos ni cierres)")
                a_mano.append(h); continue
            if n == 1:
                c[k] = t.replace(h["reemplazar"], h.get("por", ""))
            elif h.get("por") and h["por"] in t:
                avisos.append(f"{h['campo']}: ya decía «{h['por'][:50]}» (¿aplicado antes?); no se tocó"); a_mano.append(h); continue
            else:
                # el texto cambió desde la revisión (otra corrección, el script de armado): se reintenta sin mirar espacios,
                # mayúsculas ni etiquetas; si no aparece una sola vez, se avisa y va a mano (no falla)
                pat = r"(?:<[^>]+>)?\s*".join(re.escape(w) for w in h["reemplazar"].split())
                ms = list(re.finditer(pat, t, re.I))
                if len(ms) != 1:
                    avisos.append(f"{h['campo']}: «{h['reemplazar'][:50]}» ya no está tal cual ({len(ms)} parecidos); corrígelo a mano"); a_mano.append(h); continue
                c[k] = t[:ms[0].start()] + h.get("por", "") + t[ms[0].end():]; h["reemplazar"] = ms[0].group(0)   # se guarda el texto real, para --reaplicar
                avisos.append(f"{h['campo']}: el texto había cambiado; se aplicó sobre el parecido «{ms[0].group(0)[:50]}»")
            h["aplicado"] = True; hechos.append(h)
        except (KeyError, IndexError, ValueError) as e:
            h["error"] = str(e); fallidos.append(h)
    print(f"{lam} · {revisora}: {len(hechos)} aplicados · {len(a_mano)} a mano · {len(fallidos)} no se pudieron aplicar" + (f" · nota {json.dumps(nota)}" if nota is not None else ""))
    for x in avisos: print(f"  aviso: {x}")
    for h in a_mano: print(f"  a mano [{h.get('gravedad')}] {h.get('categoria', '')}: {h.get('texto', '')[:140]}")
    for h in fallidos: print(f"  falló [{h.get('gravedad')}] {h.get('campo', '-')}: {h['error']}")
    if probar: print("(--probar: no se escribió nada)"); return
    if nota is not None:
        notas = nota if isinstance(nota, dict) else {revisora: nota}
        r = subprocess.run([sys.executable, str(AQUI / "metricas.py"), "dato", lam, "notas_revision", json.dumps(notas)], capture_output=True)
        print(f"nota anotada en metricas.py: {json.dumps(notas)}" if r.returncode == 0 else f"aviso: metricas.py no anotó la nota ({r.stderr.decode('utf-8', 'replace')[-120:]})")
    if hechos:
        shutil.copyfile(js, js.with_suffix(".antes.json"))
        js.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
    REGISTRO.parent.mkdir(exist_ok=True)
    hoy = datetime.date.today().isoformat()
    with REGISTRO.open("a", encoding="utf-8") as f:
        for h in H:
            f.write(json.dumps({"fecha": hoy, "lamina": lam, "revisora": revisora, "gravedad": h.get("gravedad"), "categoria": h.get("categoria", "otro"),
                                "texto": h.get("texto", "")[:300], "aplicado": h["aplicado"]}, ensure_ascii=False) + "\n")
    print(f"registrados {len(H)} en {REGISTRO.relative_to(AQUI.parents[2])}; ahora: autocontrol.py {lam} --rapido")
    if hechos:   # ronda 4: los reemplazos quedan en datos/<lamina>.hallazgos.json, para que regenerar con el script de armado no los pierda
        guardados = AQUI / "datos" / f"{lam}.hallazgos.json"
        G = json.loads(guardados.read_text(encoding="utf-8")) if guardados.exists() else []
        G += [{"campo": h["campo"], "reemplazar": h["reemplazar"], "por": h.get("por", "")} for h in hechos]
        guardados.write_text(json.dumps(G, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"guardados en datos/{guardados.name} ({len(G)} en total). Al final del script de armado, después de guardar el JSON:\n"
              f"    subprocess.run([sys.executable, r\"{AQUI / 'aplicar_hallazgos.py'}\", \"--reaplicar\", \"{lam}\"])")


def reaplicar(lam):
    """Vuelve a aplicar datos/<lamina>.hallazgos.json sobre el JSON (después de regenerarlo). Los que ya están puestos se saltan."""
    guardados = AQUI / "datos" / f"{lam}.hallazgos.json"
    if not guardados.exists(): print("no hay reemplazos guardados para", lam); return
    js = AQUI / "datos" / f"{lam}.json"; D = json.loads(js.read_text(encoding="utf-8"))
    n = ya = mal = 0
    for h in json.loads(guardados.read_text(encoding="utf-8")):
        try:
            c, k = ir(D, h["campo"]); t = c[k]
            if h["por"] and h["por"] in t: ya += 1; continue   # ya puesto (aunque lo nuevo contenga lo viejo)
            if t.count(h["reemplazar"]) == 1: c[k] = t.replace(h["reemplazar"], h["por"]); n += 1
            else: mal += 1; print(f"  aviso: {h['campo']}: «{h['reemplazar'][:50]}» no está una sola vez; revísalo a mano")
        except (KeyError, IndexError, TypeError):
            mal += 1; print(f"  aviso: {h['campo']} ya no existe en la lámina")
    if n: js.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"reaplicados {n} · ya estaban {ya} · a mano {mal}")


def candidatas():
    if not REGISTRO.exists(): print("sin registro todavía"); return
    por = defaultdict(lambda: {"laminas": set(), "graves": 0, "n": 0, "ej": ""})
    for l in REGISTRO.read_text(encoding="utf-8").splitlines():
        if not l.strip(): continue
        h = json.loads(l); c = por[h.get("categoria") or "otro"]
        c["laminas"].add(h["lamina"]); c["n"] += 1; c["graves"] += h.get("gravedad") == "grave"; c["ej"] = c["ej"] or h.get("texto", "")
    print("| categoría | láminas | hallazgos (graves) | control | ejemplo |\n|---|---|---|---|---|")
    for cat, c in sorted(por.items(), key=lambda x: (-len(x[1]["laminas"]), -x[1]["graves"])):
        ctl = CUBIERTAS.get(cat, "**candidata a control automático**" if len(c["laminas"]) >= 2 and cat not in ("otro", "claridad", "dibujo") else "-")
        print(f"| {cat} | {len(c['laminas'])} | {c['n']} ({c['graves']}) | {ctl} | {c['ej'][:70]} |")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--candidatas" in sys.argv: candidatas()
    elif "--reaplicar" in sys.argv: reaplicar(sys.argv[sys.argv.index("--reaplicar") + 1])
    elif len(sys.argv) >= 4: aplicar(sys.argv[1], sys.argv[2], sys.argv[3], "--probar" in sys.argv)
    else: print(__doc__)
