# Revisión automática del GLB del visor: falla (código 1) si algo no cumple las reglas del usuario.
# Uso: python -I revisar.py modelo.glb [--sin-validar]
# Revisa: piezas flotando, transparencias fuera de micas o visor, la misma pintura con tonos distintos, llanta fuera del rin,
# placa, luces con emisivo (faro, stop y 4 direccionales), modo «modelo completo», nombres únicos y gltf-transform validate.
import sys, os, json, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio

ruta = sys.argv[1]; g, ms = glbio.mallas(ruta)
fallas, avisos = [], []
def falla(t): fallas.append(t)
vis = [m for m in ms if not m["extras"].get("interno")]
pref = lambda m: m["name"].split(".")[0]

# 1. Modo modelo completo y nombres
if not g["scenes"][g.get("scene", 0)].get("extras", {}).get("modelo_completo"): falla("la escena no lleva extras.modelo_completo")
nombres = [m["name"] for m in ms]; rep = {n for n in nombres if nombres.count(n) > 1}
if rep: falla(f"nombres repetidos: {sorted(rep)}")

# 2. Piezas flotando: ningún vértice de la pieza a menos de 2 cm de otra pieza (rejilla de 2 cm, vecinos incluidos)
CEL = 0.02
celdas = [set(map(tuple, np.floor(m["pos"] / CEL).astype(np.int64))) for m in vis]
dueno = {}
for i, cs in enumerate(celdas):
    for c in cs: dueno.setdefault(c, set()).add(i)
vec = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)]
for i, cs in enumerate(celdas):
    toca = any(len(dueno.get((c[0] + a, c[1] + b, c[2] + d), ())) > (1 if (c[0] + a, c[1] + b, c[2] + d) in cs else 0)
               for c in cs for a, b, d in vec)
    if not toca: falla(f"pieza flotando: {vis[i]['name']}")

# 3. Transparencias solo en micas y visor
TRANSL = {"vidrio", "vidrio_oscuro", "mica_dir"}; PERMITIDAS = ("visor", "faro", "mica", "parabrisas", "tablero")
for m in vis:
    if pref(m) in TRANSL and not any(p in m["name"] for p in PERMITIDAS): falla(f"translúcida fuera de micas o visor: {m['name']}")

# 4. Un material = un tono: mismos tono, acabado, luz y emisivo en todos los nodos de un material
for p in sorted({pref(m) for m in vis}):
    vistos = {json.dumps({k: m["extras"].get(k) for k in ("tono", "acabado", "luz", "emisivo")}, sort_keys=True) for m in vis if pref(m) == p}
    if len(vistos) > 1: falla(f"material «{p}» con tonos o acabados distintos: {len(vistos)} variantes")

# 5. Ruedas: llanta y rin del mismo eje; el rin llega al talón de la llanta y está centrado
def radio(m, e): return np.hypot(m["pos"][:, 0] - e[0], m["pos"][:, 1] - e[1])
for lado in ("del", "tras"):
    ll = [m for m in vis if m["extras"].get("rueda") == lado and pref(m) == "caucho"]
    rn = [m for m in vis if m["extras"].get("rueda") == lado and m["extras"].get("rin")]
    if not ll or not rn: falla(f"rueda {lado}: falta llanta o rin marcados con extras.rueda"); continue
    e = ll[0]["extras"]["eje"]; L, Rn = ll[0], rn[0]
    if Rn["extras"].get("eje") != e: falla(f"rueda {lado}: rin y llanta con ejes distintos")
    talon, pest = np.quantile(radio(L, e), 0.03), np.quantile(radio(Rn, e), 0.995)
    q = Rn["pos"][radio(Rn, e) > np.quantile(radio(Rn, e), 0.9)]
    A = np.c_[2 * q[:, 0], 2 * q[:, 1], np.ones(len(q))]; s = np.linalg.lstsq(A, (q[:, :2] ** 2).sum(1), rcond=None)[0]
    desc = float(np.hypot(s[0] - e[0], s[1] - e[1])); hueco = float(talon - pest)
    zL, zR = (L["pos"][:, 2].min(), L["pos"][:, 2].max()), Rn["pos"][:, 2].mean()
    print(f"rueda {lado}: talón llanta r={talon:.3f}  pestaña rin r={pest:.3f}  hueco {hueco*1000:+.0f} mm  rin descentrado {desc*1000:.1f} mm")
    if hueco > 0.012: falla(f"rueda {lado}: la llanta queda fuera del rin (hueco de {hueco*1000:.0f} mm)")
    if desc > 0.006: falla(f"rueda {lado}: el rin no está centrado en el eje ({desc*1000:.1f} mm)")
    if not zL[0] < zR < zL[1]: falla(f"rueda {lado}: el rin está fuera del ancho de la llanta")
    # El nodo que gira tiene solo la rueda y gira sobre su centro: borde exterior de la llanta redondo alrededor del pivote
    # (un pedazo de guardabarros pegado a la llanta corría el centro 9 mm y giraba con ella: Aerox, 21-nov-2026)
    p_ = L["pos"]; a_ = np.arctan2(p_[:, 1] - e[1], p_[:, 0] - e[0]); s_ = ((a_ + np.pi) / (2 * np.pi) * 36).astype(int) % 36
    rr = radio(L, e); rb = np.array([rr[s_ == k].max() for k in range(36) if (s_ == k).any()])
    redondez = float(rb.max() - rb.min()); Rmed = float(np.median(rb))
    sobra = sum(int((radio(m, e) > Rmed + 0.006).sum()) for m in vis if m["extras"].get("rueda") == lado)
    print(f"rueda {lado}: borde de la llanta {rb.min():.3f}-{rb.max():.3f} (redondez {redondez*1000:.1f} mm)  vértices fuera del radio {sobra}")
    if redondez > 0.008: falla(f"rueda {lado}: la llanta no es redonda alrededor del pivote ({redondez*1000:.0f} mm): pivote descentrado o restos pegados")
    if sobra: falla(f"rueda {lado}: {sobra} vértices del nodo que gira por fuera de la llanta (restos de otra pieza)")
    # Eje real: normal del plano de la llanta (PCA). El visor gira sobre z: inclinado, la rueda cabecea al girar.
    c0 = p_ - p_.mean(0); n_ = np.linalg.svd(c0, full_matrices=False)[2][2]; incl = float(np.degrees(np.arccos(min(1, abs(n_[2])))))
    print(f"rueda {lado}: eje real inclinado {incl:.2f}° respecto a z")
    if incl > 1.5: falla(f"rueda {lado}: el eje real de la llanta está inclinado {incl:.1f}° (el visor gira sobre z: cabecea)")
    # Todo lo que gira debe ser de revolución (un hueco o un bulto da vueltas a la vista): llanta, rin y disco
    for m in vis:
        if m["extras"].get("rueda") != lado: continue
        t = m["pos"][m["idx"]]; c = t.mean(1); ar = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
        r_ = np.hypot(c[:, 0] - e[0], c[:, 1] - e[1]); rmax = np.percentile(r_, 99); bd = (r_ > 0.6 * rmax) & (r_ < rmax)
        sc = ((np.arctan2(c[:, 1] - e[1], c[:, 0] - e[0]) + np.pi) / (2 * np.pi) * 24).astype(int) % 24
        h = np.bincount(sc[bd], ar[bd], 24); q_ = float(h.min() / max(np.median(h), 1e-12))
        print(f"rueda {lado}: {m['name']} de revolución {q_:.2f}")
        if q_ < 0.5: falla(f"rueda {lado}: {m['name']} gira pero no es de revolución ({q_:.2f}): hueco o bulto que da vueltas; dejarlo fijo")

# 6. Placa
if not any("placa" in m["extras"] for m in vis): falla("falta la placa (extras.placa)")

# 7. Luces con emisivo: faro, stop y 4 direccionales, en materiales que encienden
EMIS = {"faro": {"luz", "luz_reflector"}, "stop": {"stop"}, "direccional": {"ambar", "mica_dir"}}
cuenta = {}
for m in vis:
    la = m["extras"].get("lampara")
    if not la: continue
    cuenta[la["tipo"]] = cuenta.get(la["tipo"], 0) + 1
    if pref(m) not in EMIS.get(la["tipo"], set()): falla(f"luz sin emisivo: {m['name']} ({la['tipo']})")
for t, n in (("faro", 1), ("stop", 1), ("direccional", 4)):
    if cuenta.get(t, 0) < n: falla(f"faltan luces «{t}»: {cuenta.get(t, 0)} de {n}")
dirs = [m for m in vis if m["extras"].get("lampara", {}).get("tipo") == "direccional"]
lados = {("d" if m["pos"].mean(0)[0] > 0 else "t") + ("i" if m["pos"].mean(0)[2] > 0 else "d") for m in dirs}
if len(lados) < 4: falla(f"direccionales: deben quedar adelante y atrás en los dos lados; hay {sorted(lados)}")

# 8. Validador oficial
if "--sin-validar" not in sys.argv:
    r = subprocess.run(f'npx gltf-transform validate "{ruta}"', shell=True, capture_output=True, text=True)
    sal = r.stdout + r.stderr
    if r.returncode != 0 or "No errors found" not in sal: falla("gltf-transform validate con errores:\n" + sal[:800])
    else: print("gltf-transform validate: sin errores")

tri = sum(len(m["idx"]) for m in ms)
# 9. Peso ≤ 1,5 MB (celular con 4G): si no da, bajar simplificar.ratio en la ficha
if os.path.getsize(ruta) > 1.5e6: falla(f"pesa {os.path.getsize(ruta)/1e6:.2f} MB (meta: hasta 1,5 MB): bajar simplificar.ratio en la ficha")
print(f"{os.path.basename(ruta)}: {os.path.getsize(ruta)/1e6:.2f} MB, {tri} triángulos, {len(ms)} nodos, luces {cuenta}")
for f in fallas: print("FALLA:", f)
print("REVISIÓN OK" if not fallas else f"REVISIÓN CON {len(fallas)} FALLAS")
sys.exit(1 if fallas else 0)
