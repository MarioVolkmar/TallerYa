"""Resumen de una lámina para las revisoras: revision/<lamina>.md (lo escribe «autocontrol.py <lamina> --informe»).
Trae en un solo archivo lo que hoy se busca navegando: desarme, grupos, fichas, «Cómo funciona», cadenas, «Cuándo»,
certezas, pendientes, el resultado del validador y de la última medición, y las capturas ya tomadas.
La revisión mira solo lo que la máquina no mide (guia-revision-rapida.md)."""
import json, pathlib, re, subprocess, sys

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]


def plano(t):
    t = re.sub(r"\[\[(\w+)\|([^\]]+)\]\]", r"\2 (\1)", str(t))
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


def escribir(lam):
    D = json.loads((AQUI / "datos" / f"{lam}.json").read_text(encoding="utf-8"))
    F = D.get("fichas", {}); V = D.get("v2", {})
    nom = {p["id"]: F.get(p["n"], {}).get("nombre", p["n"]) for p in D.get("piezas", [])}
    r = subprocess.run([sys.executable, str(AQUI / "validar_esquema.py"), str(AQUI / "datos" / f"{lam}.json")], cwd=RAIZ, capture_output=True)
    val = [l.strip() for l in r.stdout.decode("utf-8", "replace").splitlines() if "ERROR" in l or l.strip().startswith("aviso:")]
    med = AQUI / "revision" / f"{lam}-medicion.txt"
    mt = med.read_text(encoding="utf-8").splitlines() if med.exists() else []
    caps = sorted(p.name for p in AQUI.glob(f"*{lam}*.jpg"))
    o = [f"# Revisión rápida · {lam}", "",
         f"{D.get('cabeza', {}).get('titulo', '')} · catálogo {D.get('catalogo', '')} fig. {D.get('figura', '')} · página `motor/{lam}.html` · "
         f"{len(D.get('piezas', []))} piezas dibujadas · {len(F)} fichas · {len(D.get('pasos', []))} pasos · {len(D.get('funciona', {}).get('pasos', []))} pasos de «Cómo funciona»",
         "", "Guía: `informes_noche/piloto-esquema/guia-revision-rapida.md` (10 min por revisión; mecánica y UX en paralelo).", "",
         "## Lo que ya midió la máquina", f"- Validador: {len([v for v in val if 'ERROR' in v])} errores, {len([v for v in val if v.startswith('aviso')])} avisos."]
    o += [f"  - {v[:200]}" for v in val[:12]]
    if mt:
        o += [f"- Medición: {next((l for l in mt if l.startswith('Bloqueantes')), 'sin línea de bloqueantes')}",
              f"- {next((l for l in mt if l.startswith('Notas')), '')}"] + [f"  {l.strip()[:200]}" for l in mt if l.startswith("  - ")][:10]
    else:
        o.append("- Medición: todavía no hay (corre la medición final de autocontrol).")
    o += ["- Capturas: " + (", ".join(f"`motor/{c}`" for c in caps) or "ninguna"), ""]
    o += ["## Desarme (pasos)"] + [f"{i + 1}. {plano(p['t'])} · mueve: {', '.join(nom.get(k, k) for k in p['m'])}" for i, p in enumerate(D.get("pasos", []))]
    if D.get("sujeta"): o.append("- sujeta: " + "; ".join(f"{nom.get(k, k)} → {', '.join(nom.get(x, x) for x in v)}" for k, v in D["sujeta"].items()))
    o += ["", "## Grupos"] + [f"- **{g['nombre']}**: {', '.join(nom.get(i, i) for i in g['piezas'])}" + (" · tornillería: " + ", ".join(f"{t['nombre']} ×{t['cant']}" for t in g.get('torn', [])) if g.get("torn") else "")
                              for g in V.get("grupos", [])]
    if D.get("kits"): o.append("- kits (sin dibujo): " + "; ".join(f"ref. {k} trae {', '.join(v)}" for k, v in (D["kits"].items() if isinstance(D["kits"], dict) else [(k, []) for k in D["kits"]])))
    o += ["", "## Fichas"]
    for n, f in sorted(F.items(), key=lambda x: (len(x[0]), x[0])):
        cd = f.get("certezaDe", {}); ap = [k for k, v in cd.items() if v == "ap"]
        o.append(f"- **{n} · {f.get('nombre')}** · {f.get('decision', '')} · {f.get('dif', '')} · {plano(f.get('cat', ''))}")
        for c in ("que", "sirve", "porque", "cuando"):
            if f.get(c): o.append(f"  - {c}: {plano(f[c])}")
        if f.get("fallas"): o.append("  - fallas: " + "; ".join(f"{a}: {plano(b)}" for a, b in f["fallas"]))
        if f.get("sintomas"): o.append("  - síntomas: " + "; ".join(plano(x) for x in f["sintomas"]))
        if f.get("arrastra"): o.append("  - arrastra: " + "; ".join(plano(x) for x in f["arrastra"]))
        if ap: o.append(f"  - aprox.: {', '.join(ap)}")
    o += ["", "## Cómo funciona"] + [f"{i + 1}. {plano(p['t'])}" for i, p in enumerate(D.get("funciona", {}).get("pasos", []))]
    o += ["", "## Si falla (cadenas)"] + [f"- **{c['t']}**: " + " → ".join(f"{nom.get(n, F.get(n, {}).get('nombre', n))}: {plano(t)}" for n, t in c["p"]) for c in D.get("cadenas", [])]
    o += ["", "## Cuándo"] + [f"- {plano(c['que'])}: {plano(c['cuando'])} · {plano(c['fuente'])}" for c in D.get("cuando", [])]
    fu = D.get("fuentes", {})
    o += ["", "## Fuentes"] + [f"- Seguro: {plano(x)}" for x in fu.get("seguro", [])] + [f"- Aprox.: {plano(x)}" for x in fu.get("aproximado", [])]
    o += ["", "## Pendientes de la creadora"] + [f"- {plano(x)}" for x in D.get("pendientes", [])] + [""]
    (AQUI / "revision").mkdir(exist_ok=True)
    dest = AQUI / "revision" / f"{lam}.md"
    dest.write_text("\n".join(o), encoding="utf-8")
    return f"escrito {dest.relative_to(RAIZ)} ({len(o)} líneas)"


if __name__ == "__main__":
    print(escribir(sys.argv[1]))
