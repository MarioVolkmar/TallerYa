# Arma el GLB del visor («modelo completo») desde un Tripo DESPIEZADO y las etiquetas del usuario (página /garaje/etiquetar-3d/).
# No cambia la geometría de Tripo: solo la gira y escala (parejo), la reparte en nodos «material.pieza» según las etiquetas,
# separa luces (por zona y por la cara que mira afuera), marca ruedas y pone la placa. Corre igual en Python o en Blender:
#   python -I armar.py ficha.json            (o)  blender -b --factory-startup --python armar.py -- ficha.json
# La ficha (fichas/<moto>.json) dice entrada, etiquetas, ruedas, luces, placa y los «forzar» de etiquetas ambiguas.
import sys, os, json, re, unicodedata, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import glbio

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))  # carpeta del proyecto
F = json.load(open(args[0], encoding="utf-8"))
def ruta(p): return p if os.path.isabs(p) else os.path.join(RAIZ, p)
SALIDA = ruta(args[1]) if len(args) > 1 else ruta(F["salida"])

# ---------- Etiquetas: texto libre -> (pieza, acabado). Misma deducción que la página, con «color principal» primero.
sys.path.insert(0, os.path.join(RAIZ, "garaje"))
from deduccion_3d import deducir, normalizar
def deduce(texto, guardado):
    t = normalizar(texto or "")
    if not t: return guardado.get("pieza"), guardado.get("acabado")
    d = deducir(texto)
    pieza = d["pieza"] or guardado.get("pieza") or "otra"; acabado = d["acabado"] or guardado.get("acabado")
    if re.search(r"\bsecundari", t): acabado = "pintura_secundaria"
    elif re.search(r"\b(color principal|principal|color moto|pintura princ)", t) and pieza not in ("faro", "stop", "direccional"): acabado = "pintura"
    return pieza, acabado

# Acabado -> material del visor (prefijo del nodo). Un material por acabado: tonos parejos.
def material(pieza, acabado):
    if acabado == "oculta" or pieza == "basura": return None
    if pieza in ("llanta_del", "llanta_tras"): return "caucho"
    if pieza in ("rin_del", "rin_tras"): return "rin"
    if acabado and acabado.startswith("@"): return acabado[1:]  # material del visor puesto a mano en la ficha
    return {"mica_ambar": "ambar", "mica_roja": "stop", "mica_faro": "luz" if pieza == "faro" else "vidrio_oscuro",
            "pintura": "pintura", "pintura_secundaria": "blanco", "plastico_mate": "chasis" if pieza in ("basculante", "chasis", "pata") else "plastico",
            "plastico_brillo": "negro_brillo", "caucho": "caucho", "vinilo": "asiento", "cromo": "cromo",
            "aluminio": "carter" if pieza in ("motor", "cvt") else "metal", "motor": "motor", "chasis": "chasis"}.get(acabado, "plastico")
ACABADO = {  # PBR propio por material (igual para todos los nodos del material)
    "rin": {"roughness": 0.3, "metalness": 0.7, "clearcoat": 0.5}, "metal": {"roughness": 0.35, "metalness": 0.85},
    "cromo": {"roughness": 0.15, "metalness": 1.0}, "carter": {"roughness": 0.5, "metalness": 0.4},
    "asiento": {"roughness": 0.62, "sheen": 0.35, "sheenRoughness": 0.5, "clearcoat": 0.12, "clearcoatRoughness": 0.6},
    "caucho": {"roughness": 0.95, "metalness": 0}}
PADRE = {"escape": "escapeFabrica", "espejo": "espejos.fabrica"}
PIEZA_VISOR = {"horquilla": "suspension_del", "amortiguador": "suspension_tras", "motor": "motor"}

# ---------- Tripo -> ejes del visor (x adelante, y arriba, escape en -z). Reflexión: se invierte el orden de los vértices.
g, b, base = glbio.leer(ruta(F["entrada"]))
P = {}
for n in g["nodes"]:
    if "mesh" not in n: continue
    pr = g["meshes"][n["mesh"]]["primitives"][0]
    k = int(n["name"].rsplit("_", 1)[1])
    P[k] = (glbio.atributo(g, b, base, pr["attributes"]["POSITION"]) + np.array(n.get("translation", [0, 0, 0])),
            glbio.atributo(g, b, base, pr["attributes"]["NORMAL"]), glbio.atributo(g, b, base, pr["indices"]).astype(np.int64).reshape(-1, 3))
R = F["ruedas"]
def caja(ids): p = np.vstack([P[i][0] for i in ids]); return (p.min(0) + p.max(0)) / 2, p.min(0)
ct, mt = caja(R["tras"]["llanta"]); cd, md = caja(R["del"]["llanta"])
S = F["distancia_ejes"] / (cd[2] - ct[2]); Y0 = min(mt[1], md[1]); ZM = (cd[2] + ct[2]) / 2
def T(p): return np.stack([(p[:, 2] - ZM) * S, (p[:, 1] - Y0) * S, p[:, 0] * S], 1)
M = {k: {"pos": T(p), "nor": np.stack([nn[:, 2], nn[:, 1], nn[:, 0]], 1), "idx": i[:, [0, 2, 1]]} for k, (p, nn, i) in P.items()}

def compacta(m, sel):
    idx = m["idx"][sel]; u = np.unique(idx); mapa = -np.ones(len(m["pos"]), np.int64); mapa[u] = np.arange(len(u))
    return {"pos": m["pos"][u], "nor": m["nor"][u], "idx": mapa[idx]}
def unir(ms):
    pos, nor, idx, o = [], [], [], 0
    for m in ms: pos.append(m["pos"]); nor.append(m["nor"]); idx.append(m["idx"] + o); o += len(m["pos"])
    return {"pos": np.vstack(pos), "nor": np.vstack(nor), "idx": np.vstack(idx)}
def radio(m, e): return np.hypot(m["pos"][:, 0] - e[0], m["pos"][:, 1] - e[1])
def normal_tri(m):
    n = m["nor"][m["idx"]].mean(1); return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)

# ---------- Bordes limpios entre zonas: la pertenencia de cada vértice a cada zona se suaviza (Laplaciano por aristas) y
# los triángulos se parten por la isolínea 0,5 (vértices nuevos sobre las aristas: no se mueve ningún vértice de Tripo).
# Así el borde de una mica o de una franja pintada sale como una curva, no como los dientes de los triángulos.
def cortar_por(m, s, attr):
    """Parte cada triángulo que cruza s = 0. Devuelve malla nueva, atributo por vértice interpolado y máscara s > 0 por triángulo."""
    idx = m["idx"]; sg = s[idx] > 0; n = sg.sum(1); cruza = (n == 1) | (n == 2)
    pos = [m["pos"]]; nor = [m["nor"]]; at = [attr]; nv = len(m["pos"]); cache = {}; extra = []
    def corte(a, c):
        nonlocal nv
        kk = (min(a, c), max(a, c))
        if kk not in cache:
            t = s[a] / (s[a] - s[c])
            pos.append((m["pos"][a] + t * (m["pos"][c] - m["pos"][a]))[None]); nor.append((m["nor"][a] + t * (m["nor"][c] - m["nor"][a]))[None])
            at.append((attr[a] + t * (attr[c] - attr[a]))[None]); cache[kk] = nv; nv += 1
        return cache[kk]
    tris, lado = [idx[~cruza]], [sg[~cruza, 0]]
    for tri, g3 in zip(idx[cruza], sg[cruza]):
        solo = np.where(g3 != (g3.sum() >= 2))[0][0]; a, b1, c1 = tri[solo], tri[(solo + 1) % 3], tri[(solo + 2) % 3]
        p, q = corte(a, b1), corte(a, c1); extra += [([a, p, q], g3[solo]), ([p, b1, c1], not g3[solo]), ([p, c1, q], not g3[solo])]
    if extra:
        tris.append(np.array([e[0] for e in extra], np.int64)); lado.append(np.array([e[1] for e in extra], bool))
    return {"pos": np.vstack(pos), "nor": np.vstack(nor), "idx": np.vstack(tris)}, np.vstack(at), np.concatenate(lado)

def suavizar(m, val, iteraciones):
    """Promedia un valor por vértice sobre las aristas (vértices repetidos en la misma posición cuentan como uno)."""
    _, sold = np.unique(np.round(m["pos"], 6), axis=0, return_inverse=True); sold = sold.ravel(); ns = sold.max() + 1
    e = sold[np.vstack([m["idx"][:, [0, 1]], m["idx"][:, [1, 2]], m["idx"][:, [2, 0]]])]
    v = np.bincount(sold, val, ns) / np.maximum(np.bincount(sold, minlength=ns), 1); grado = np.bincount(e.ravel(), minlength=ns)
    for _ in range(iteraciones):
        suma = np.bincount(e[:, 0], v[e[:, 1]], ns) + np.bincount(e[:, 1], v[e[:, 0]], ns); v = 0.5 * v + 0.5 * suma / np.maximum(grado, 1)
    return v[sold]

def normales_suaves(m, pasadas=6):
    """Sombreado suave (mica del faro): normal por vértice = promedio por área de las caras que lo tocan (en vértices soldados,
    orientadas como las normales de Tripo) y luego promediada sobre la malla; borra las facetas y rayas que dejan los cortes."""
    if not len(m["idx"]): return m
    t = m["pos"][m["idx"]]; fn = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    # (la mica mira al frente: los triángulos de Tripo con el orden al revés se voltean; si no, el visor los descarta
    # y quedan puntitos oscuros)
    atras = fn[:, 0] < 0; m = dict(m, idx=np.where(atras[:, None], m["idx"][:, [0, 2, 1]], m["idx"])); fn[atras] *= -1
    acc = np.zeros_like(m["pos"]); [np.add.at(acc, m["idx"][:, j], fn) for j in range(3)]
    _, sold = np.unique(np.round(m["pos"], 5), axis=0, return_inverse=True); sold = sold.ravel()
    tot = np.zeros((sold.max() + 1, 3)); np.add.at(tot, sold, acc); n = tot[sold]
    n = np.stack([suavizar(m, n[:, j], pasadas) for j in range(3)], 1)
    return dict(m, nor=n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9))

def bordes_limpios(m, gv, iteraciones=4):
    grupos = [g for g in np.unique(gv) if g]
    if not grupos: return m, np.zeros(len(m["idx"]), np.int64)
    nv = len(m["pos"]); I = np.stack([(gv == g) for g in [0] + grupos], 1).astype(float)
    # (vértices repetidos de Tripo en la misma posición cuentan como uno: se suaviza sobre las aristas soldadas)
    _, sold = np.unique(np.round(m["pos"], 6), axis=0, return_inverse=True); sold = sold.ravel()
    e = np.vstack([m["idx"][:, [0, 1]], m["idx"][:, [1, 2]], m["idx"][:, [2, 0]]]); e = sold[e]; ns = sold.max() + 1
    Is = np.zeros((ns, I.shape[1])); np.add.at(Is, sold, I); cnt = np.bincount(sold, minlength=ns)[:, None]; Is /= np.maximum(cnt, 1)
    grado = np.bincount(e.ravel(), minlength=ns)[:, None]
    for _ in range(iteraciones):
        suma = np.zeros_like(Is); np.add.at(suma, e[:, 0], Is[e[:, 1]]); np.add.at(suma, e[:, 1], Is[e[:, 0]])
        Is = 0.5 * Is + 0.5 * suma / np.maximum(grado, 1)
    A = Is[sold]; zona = np.zeros(len(m["idx"]), np.int64); hecho = np.zeros(len(m["idx"]), bool)
    for j, g in enumerate(grupos, 1):  # cada zona pintada se corta por donde su pertenencia pasa de 0,5
        otros = np.delete(A, j, axis=1).max(1); s = A[:, j] - np.maximum(otros, 0.5) + 1e-7
        m2, A, dentro = cortar_por(m, s, A); n_viejo = len(zona)
        # (los triángulos partidos heredan lo ya decidido del que venían; los nuevos van al final en el mismo orden de cortar_por)
        sg = s[m["idx"]] > 0; nn = sg.sum(1); cruza = (nn == 1) | (nn == 2)
        zona = np.concatenate([zona[~cruza], np.repeat(zona[cruza], 3)]); hecho = np.concatenate([hecho[~cruza], np.repeat(hecho[cruza], 3)])
        nuevo = dentro & ~hecho; zona[nuevo] = g; hecho |= nuevo; m = m2
    return m, zona

# ---------- Zona de cada triángulo (borde suavizado; lo sin pintar = zona 0)
ET = {p["parte"]: p for p in json.load(open(ruta(F["etiquetas"]), encoding="utf-8"))["partes"]}
FORZAR = F.get("forzar", {})
tri_zona, decision = {}, []
for k, m in M.items():
    e = ET.get(f"tripo_part_{k}", {"texto": "", "zonas": []}); nv = len(m["pos"]); gv = np.zeros(nv, np.int64)
    zonas = {0: e.get("texto", "")}; guard = {0: e}
    for z in e.get("zonas", []):
        for a, c in z["vertices"]: gv[a:c + 1] = z["grupo"]
        if z["grupo"] == 0 and z.get("texto"): zonas[0] = z["texto"] if not e.get("texto") else e["texto"] + ". " + z["texto"]
        elif z["grupo"]: zonas[z["grupo"]] = z.get("texto", ""); guard[z["grupo"]] = z
    if F.get("bordes_limpios", True): M[k], tz = bordes_limpios(m, gv); m = M[k]
    else:
        tv = gv[m["idx"]]; tz = np.where((tv[:, 0] == tv[:, 1]) | (tv[:, 0] == tv[:, 2]), tv[:, 0], np.where(tv[:, 1] == tv[:, 2], tv[:, 1], tv.max(1)))
    # forzar_cara: lo de una zona que mira hacia `cara` (p. ej. el interior del frente, que mira atrás) pasa a otro acabado;
    # se corta por la isolínea de la normal (borde curvo, sin mover vértices). Zona nueva = 100 + zona.
    extra_f = {}
    for zs, regla in F.get("forzar_cara", {}).get(str(k), {}).items():
        zg0 = int(zs); dv = np.asarray(regla["cara"], float); dv /= np.linalg.norm(dv)
        nv_ = m["nor"] / np.maximum(np.linalg.norm(m["nor"], axis=1, keepdims=True), 1e-9); sc = suavizar(m, nv_ @ dv, regla.get("suavizar", 20)) - regla.get("umbral", 0.2)
        en_zona = np.zeros(len(m["pos"]), bool); en_zona[m["idx"][tz == zg0].ravel()] = True; sc = np.where(en_zona, sc, -1.0)
        m2, _, lado = cortar_por(m, sc + 1e-7, np.zeros((len(m["pos"]), 1)))
        sg = (sc + 1e-7)[m["idx"]] > 0; nn = sg.sum(1); cruza = (nn == 1) | (nn == 2)
        tz = np.concatenate([tz[~cruza], np.repeat(tz[cruza], 3)]); tz[(tz == zg0) & lado] = 100 + zg0
        M[k] = m = m2; zonas[100 + zg0] = regla.get("nota", "forzar_cara"); extra_f[100 + zg0] = regla["como"]
    tri_zona[k] = tz
    for zg in sorted(set(tz.tolist())):
        f = FORZAR.get(str(k), {}).get(str(zg)) or extra_f.get(zg)
        pieza, acab = f.split("/") if f else deduce(zonas.get(zg, ""), guard.get(zg, e) if zg else e)
        if zg and not zonas.get(zg) and not f: pieza, acab = deduce(zonas[0], e)
        mat = material(pieza, acab)
        # Pantalla del tablero (enciende con las luces, M.pantalla en el visor): la zona propia del tablero en plástico
        # brillante, mica o vidrio (la que el usuario marcó como «tacómetro»/«pantalla»); ficha.pantalla [[parte, zona]] la fuerza
        if [k, zg] in F.get("pantalla", []) or (pieza == "tablero" and zg and acab in ("plastico_brillo", "mica_faro", "vidrio") and "pantalla" not in F):
            mat = "pantalla"
        decision.append((k, zg, int((tz == zg).sum()), zonas.get(zg, "")[:50], pieza, acab, mat))

# ---------- Reparto: ruedas, luces, placa y el resto por (material, pieza)
asignado = {k: np.zeros(len(M[k]["idx"]), bool) for k in M}
nodos = []
def tomar(k, zg=None):
    sel = ~asignado[k] if zg is None else (~asignado[k]) & (tri_zona[k] == zg)
    asignado[k] |= sel; return compacta(M[k], sel)
def nodo(nombre, m, **ex):
    if len(m["idx"]): nodos.append({"name": nombre, "pos": m["pos"], "nor": m["nor"], "idx": m["idx"], "extras": ex})

def centro_rueda(m, aprox, nsec=72):
    """Centro y radio del borde exterior de la llanta: el punto más lejano por sector, ajuste de círculo y fuera los
    sectores que no cuadran (restos pegados, p. ej. un pedazo de guardabarros, corrían el centro 9 mm). Devuelve (eje, R)."""
    p = m["pos"]; e = np.asarray(aprox, float)
    for _ in range(5):
        r = radio(m, e); a = np.arctan2(p[:, 1] - e[1], p[:, 0] - e[0]); s = ((a + np.pi) / (2 * np.pi) * nsec).astype(int) % nsec
        q = np.array([p[s == k][np.argmax(r[s == k])] for k in range(nsec) if (s == k).any()])
        ok = np.ones(len(q), bool)
        for _ in range(3):
            A = np.c_[2 * q[ok, 0], 2 * q[ok, 1], np.ones(ok.sum())]; c = np.linalg.lstsq(A, (q[ok, :2] ** 2).sum(1), rcond=None)[0]
            Rr = np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2); res = np.abs(np.hypot(q[:, 0] - c[0], q[:, 1] - c[1]) - Rr)
            ok = res < max(0.003, 2.5 * np.median(res))
        e = c[:2]
    return [round(float(e[0]), 4), round(float(e[1]), 4)], float(Rr)
def cortar_cilindro(m, eje, r0):
    """Parte la malla por el cilindro r = r0 alrededor del eje, partiendo los triángulos del borde (no mueve vértices)."""
    s = radio(m, eje) - r0; pos = list(m["pos"]); nor = list(m["nor"]); fuera, dentro, cache = [], [], {}
    def corte(a, c):
        kk = (min(a, c), max(a, c))
        if kk not in cache:
            t = s[a] / (s[a] - s[c]); pos.append(m["pos"][a] + t * (m["pos"][c] - m["pos"][a])); nor.append(m["nor"][a] + t * (m["nor"][c] - m["nor"][a])); cache[kk] = len(pos) - 1
        return cache[kk]
    for tri in m["idx"]:
        sg = s[tri] > 0
        if sg.all(): fuera.append(tri); continue
        if not sg.any(): dentro.append(tri); continue
        solo = np.where(sg != (sg.sum() >= 2))[0][0]; a, b1, c1 = tri[solo], tri[(solo + 1) % 3], tri[(solo + 2) % 3]
        p, q = corte(a, b1), corte(a, c1)
        (fuera if sg[solo] else dentro).append([a, p, q])
        for t in ([p, b1, c1], [p, c1, q]): (dentro if sg[solo] else fuera).append(t)
    full = {"pos": np.array(pos), "nor": np.array(nor)}
    mk = lambda L: compacta(dict(full, idx=np.array(L, np.int64).reshape(-1, 3)), np.ones(len(L), bool))
    return mk(fuera), mk(dentro)

REVOLUCION_MIN = 0.5
def de_revolucion(m, e, nsec=24):
    """¿La pieza es de revolución alrededor del eje? Área por sector (24) en la banda exterior (60-99 % del radio), mínimo
    sobre la mediana: llanta y rin sanos dan 0,7-1 (los rayos no cuentan: la banda exterior es el aro); un disco al que le
    falta un pedazo da ~0. Lo que gira con < REVOLUCION_MIN muestra el hueco o el bulto dando vueltas."""
    t = m["pos"][m["idx"]]; c = t.mean(1); area = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
    r = np.hypot(c[:, 0] - e[0], c[:, 1] - e[1]); rmax = np.percentile(r, 99); banda = (r > 0.6 * rmax) & (r < rmax)
    s = ((np.arctan2(c[:, 1] - e[1], c[:, 0] - e[0]) + np.pi) / (2 * np.pi) * nsec).astype(int) % nsec
    h = np.bincount(s[banda], area[banda], nsec); return float(h.min() / max(np.median(h), 1e-12))

ejes = {}
for lado, cc in (("tras", ct), ("del", cd)):
    r = R[lado]; llanta = unir([tomar(k) for k in r["llanta"]])
    eje, Rll = centro_rueda(llanta, np.array([(cc[2] - ZM) * S, (cc[1] - Y0) * S])); ejes[lado] = eje
    rin = [tomar(k) for k in r.get("rin", [])]
    if r.get("rin_corte_r"):  # llanta y rin en una sola parte de Tripo: se separan por radio
        llanta, adentro = cortar_cilindro(llanta, eje, r["rin_corte_r"] * S); rin.append(adentro)
    # El nodo que gira lleva solo la rueda: lo que sobresale del borde de la llanta (restos de Tripo de otra pieza, p. ej.
    # guardabarros) sale del nodo; queda fijo o se quita según ficha.ruedas.<lado>.restos ("fijo" por defecto | "quitar")
    restos = []
    def sin_restos(m):
        fuera = (radio(m, eje)[m["idx"]] > Rll + 0.004).any(1)
        if fuera.any(): restos.append(compacta(m, fuera))
        return compacta(m, ~fuera)
    llanta = sin_restos(llanta); rin = [sin_restos(x) for x in rin]
    base = dict(rueda=lado, pieza="llanta_" + lado, eje=eje)
    nodo(f"caucho.llanta_{lado}", llanta, **base, acabado=ACABADO["caucho"])
    if rin: nodo(f"rin.rin_{lado}", unir(rin), **base, rin=True, acabado=ACABADO["rin"])
    if r.get("disco"):
        # Un disco de Tripo incompleto (le falta el pedazo que tapaba la mordaza) dejaba ver el hueco dando vueltas: si no es
        # de revolución queda FIJO, como vino de Tripo (el hueco sigue detrás de la mordaza). ruedas.<lado>.disco_gira lo fuerza.
        disco = sin_restos(unir([tomar(k) for k in r["disco"]])); q = de_revolucion(disco, eje)
        gira = r.get("disco_gira", q >= REVOLUCION_MIN)
        print(f"rueda {lado}: disco de revolución {q:.2f} -> {'gira' if gira else 'FIJO (incompleto)'}")
        if gira: nodo(f"metal.disco_{lado}", disco, **base, acabado=ACABADO["metal"])
        else: nodo(f"metal.disco_{lado}", disco, pieza="disco_" + lado, acabado=ACABADO["metal"])
    if restos and r.get("restos", "fijo") == "fijo": nodo(f"plastico.restos_rueda_{lado}", unir(restos))
    print(f"rueda {lado}: eje {eje} R {Rll:.3f}  restos fuera del nodo que gira: {sum(len(x['idx']) for x in restos)} tri ({r.get('restos', 'fijo')})")

MAT_LUZ = {"faro": "luz", "stop": "stop", "direccional": "ambar"}

def dist_poligono(q, poli):
    """Distancia con signo de los puntos q (n×2) al polígono (k×2): + adentro, − afuera."""
    a = poli; b = np.roll(poli, -1, 0); d = np.full(len(q), np.inf); dentro = np.zeros(len(q), bool)
    for p0, p1 in zip(a, b):
        e = p1 - p0; t = np.clip(((q - p0) @ e) / max(e @ e, 1e-12), 0, 1); d = np.minimum(d, np.linalg.norm(q - (p0 + t[:, None] * e), axis=1))
        cruza = (p0[1] > q[:, 1]) != (p1[1] > q[:, 1]); xc = p0[0] + (q[:, 1] - p0[1]) * e[0] / (e[1] if abs(e[1]) > 1e-12 else 1e-12)
        dentro ^= cruza & (q[:, 0] < xc)
    return np.where(dentro, d, -d)

def recorte_mica(m, contra, tira, contorno=None, tapar_a_mica=False):
    """Mica del faro con la forma de la foto y bordes limpios.
    - Borde de arriba: recta y = a·z + b ajustada al borde visible del carenado (vista de frente).
    - `contorno` (opcional): polígono [[u, v], ...] tomado de la foto de frente, en la caja de la mica vista de frente
      (u: 0 = lado de afuera, 1 = centro de la moto; v: 0 = arriba, 1 = abajo). Da el borde de abajo y el de afuera.
    Región de la mica = debajo de la recta ∩ dentro del contorno. Mica y carenado se parten por ese borde (sin mover vértices):
    lo del carenado que tapa la mica adentro se quita; lo del carenado adentro sin mica detrás (dientes de Tripo) pasa a mica;
    la mica que sobra afuera pasa al plástico vecino (pintura arriba de la recta, plástico mate abajo), nunca a carcasa negra.
    Devuelve (tira LED de ancho `tira` bajo la recta, sobra arriba, sobra afuera, resto de la mica = reflector)."""
    c = m["pos"][m["idx"]].mean(1); h = 0.004
    z0, y0 = c[:, 2].min(), c[:, 1].min(); nz, ny = int((c[:, 2].max() - z0) / h) + 2, int((c[:, 1].max() - y0) / h) + 2
    celda = lambda p: (np.clip(((p[:, 2] - z0) / h).astype(int), 0, nz - 1), np.clip(((p[:, 1] - y0) / h).astype(int), 0, ny - 1))
    dentro = lambda p: (p[:, 2] >= z0) & (p[:, 2] < z0 + nz * h) & (p[:, 1] >= y0) & (p[:, 1] < y0 + ny * h)
    frente_mica = np.full((nz, ny), -9.0); iz, iy = celda(c); np.maximum.at(frente_mica, (iz, iy), c[:, 0])
    frente_otro = np.full((nz, ny), -9.0)
    for k2 in contra:
        c2 = M[k2]["pos"][M[k2]["idx"]].mean(1); d2 = dentro(c2) & ~asignado[k2]; jz, jy = celda(c2[d2]); np.maximum.at(frente_otro, (jz, jy), c2[d2, 0])
    vis = (frente_mica > -9) & (frente_mica >= frente_otro - 0.002)
    zs, ys = [], []
    for a in range(nz):
        col = np.where(vis[a])[0]
        if len(col) > 2: zs.append(z0 + (a + 0.5) * h); ys.append(y0 + (col.max() + 0.5) * h)
    zs, ys = np.array(zs), np.array(ys); ok = np.ones(len(zs), bool)
    for _ in range(3):  # ajuste robusto: fuera los puntos lejos de la recta
        A, B = np.polyfit(zs[ok], ys[ok], 1); r = ys - (A * zs + B); mad = np.median(np.abs(r[ok])) + 1e-4; ok = np.abs(r) < 2.5 * mad
    B += float(np.quantile(r, 0.9))  # (la recta se sube al borde alto del carenado)
    p = m["pos"]; zo, zi = (p[:, 2].max(), p[:, 2].min()) if p[:, 2].mean() > 0 else (p[:, 2].min(), p[:, 2].max())
    yt, yb = p[:, 1].max(), p[:, 1].min()
    poli = None if not contorno else np.array([[zo + u * (zi - zo), yt - v * (yt - yb)] for u, v in contorno])
    if poli is not None and poli[:, 0].mean() < 0: poli = poli[::-1]
    def adentro(q):  # + dentro de la mica (debajo de la recta y dentro del contorno)
        s = -(q[:, 1] - (A * q[:, 2] + B)) / np.sqrt(1 + A * A)
        return s if poli is None else np.minimum(s, dist_poligono(q[:, [2, 1]], poli))
    def partir(mm, s):
        m3, _, pos_ = cortar_por(mm, s, np.zeros((len(mm["pos"]), 1))); sg = s[mm["idx"]] > 0; nn = sg.sum(1)
        return m3, pos_, (nn == 1) | (nn == 2)
    xmin = p[:, 0].min() - 0.01; extra = []
    for k2 in contra:  # carenado: se parte por el borde de la mica; adentro, lo que tapa se quita y lo que no tiene mica detrás pasa a mica
        m2 = M[k2]; m3, ins, cruza = partir(m2, adentro(m2["pos"]) + 1e-7)
        tri_zona[k2] = np.concatenate([tri_zona[k2][~cruza], np.repeat(tri_zona[k2][cruza], 3)])
        asignado[k2] = np.concatenate([asignado[k2][~cruza], np.repeat(asignado[k2][cruza], 3)]); M[k2] = m3
        t3 = m3["pos"][m3["idx"]]; c3 = t3.mean(1); jz, jy = celda(c3); fm = frente_mica[jz, jy]; fo = frente_otro[jz, jy]
        cubierto = fm > -9  # (la mica cubre el triángulo entero: sus 3 vértices caen en celdas con mica)
        for v in range(3): vz, vy = celda(t3[:, v]); cubierto &= frente_mica[vz, vy] > -9
        sel = ins & dentro(c3) & ~asignado[k2] & (c3[:, 0] > xmin)
        tapa = sel & cubierto & (c3[:, 0] > fm - 0.015)
        hueco = sel & ~cubierto & (c3[:, 0] >= fo - 0.01)
        if tapar_a_mica: hueco |= tapa; tapa = tapa & False  # (lo que tapa también pasa a mica: sin huecos que se vean en perspectiva)
        if hueco.any(): extra.append(compacta(m3, hueco))
        asignado[k2] |= tapa | hueco  # (asignado sin nodo = se quita)
    m1, ins, _ = partir(m, adentro(m["pos"]) + 1e-7)
    mica = unir([compacta(m1, ins)] + extra); fuera = compacta(m1, ~ins)
    cf = fuera["pos"][fuera["idx"]].mean(1); arriba = cf[:, 1] > A * cf[:, 2] + B - 0.003
    s2 = -(mica["pos"][:, 1] - (A * mica["pos"][:, 2] + B)) / np.sqrt(1 + A * A) - tira
    m4, _, en_tira = cortar_por(mica, -s2, np.zeros((len(mica["pos"]), 1)))
    print(f"  recorte mica: y = {A:.3f}·z + {B:.3f} ({ok.sum()}/{len(ok)} columnas); contorno {'sí' if poli is not None else 'no'}; huecos a mica {sum(len(e['idx']) for e in extra)} tri")
    return compacta(m4, en_tira), compacta(fuera, arriba), compacta(fuera, ~arriba), compacta(m4, ~en_tira)

cuenta = {}
for L in F["luces"]:
    k, zg = L["de"]; m = tomar(k, zg); tipo = L["tipo"]; i = cuenta[tipo] = cuenta.get(tipo, 0) + 1
    R_ = L.get("recorte") or {}
    if L.get("cara") and not R_.get("contorno"):  # la lente es lo que mira hacia afuera; lo demás es la carcasa
        sel = normal_tri(m) @ np.asarray(L["cara"], float) > L.get("umbral", 0.3)
        nodo(f"negro_brillo.carcasa_{tipo}_{i}", compacta(m, ~sel)); m = compacta(m, sel)
    if R_:  # faro: contorno de la foto y borde recto contra el carenado; tira LED (luz) arriba y reflector cromado debajo
        m, sobra_arriba, sobra_fuera, refl = recorte_mica(m, R_["contra"], R_.get("tira", 0.02), R_.get("contorno"))
        nodo(f"pintura.borde_{tipo}_{i}", sobra_arriba); nodo(f"plastico.borde_{tipo}_{i}", sobra_fuera)
        if R_.get("suave", True): m, refl = normales_suaves(m, R_.get("pasadas", 6)), normales_suaves(refl, R_.get("pasadas", 6))
        nodo(f"luz_reflector.reflector_{tipo}_{i}", refl, lampara={"tipo": tipo})
    nodo(f"{MAT_LUZ[tipo]}.{tipo}_{i}", m, lampara={"tipo": tipo, **({"cono": False} if L.get("recorte") else {})})

# Placa colombiana al 78 %: 18,3 × 10,5 cm (ancho × alto); la ficha puede cambiarla con placa.tam
PLACA_CO = [0.183, 0.105]  # (placa colombiana 23,5 × 13,5 cm al 78 %: pedido del usuario, 21-nov-2026)
# Placa: en la cara que mira atrás del soporte que dice la ficha; centro por área e inclinación por la normal media
if F.get("placa"):
    pk = F["placa"]["parte"]; pl = M[pk]; t = pl["pos"][pl["idx"]]; nt = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); ar = np.linalg.norm(nt, axis=1)
    nt = nt / np.maximum(ar[:, None], 1e-12); c3 = t.mean(1); atras = nt[:, 0] < -0.5
    if ar[atras].sum() < 1e-4: atras = nt[:, 0] > 0.5; nt = -nt
    w = ar[atras]; cp = (c3[atras] * w[:, None]).sum(0) / w.sum(); nm = (nt[atras] * w[:, None]).sum(0); nm /= np.linalg.norm(nm)
    sal = float(((pl["pos"] - cp) @ nm).max())  # (pegada por delante de lo más saliente del soporte: pestañas que no la atraviesen)
    cpl = cp + nm * (max(sal, 0) + 0.004); incl = -float(np.arcsin(np.clip(nm[1], -1, 1)))
    mats = {d[6] for d in decision if d[0] == pk}
    nodo(f"{sorted(mats)[0]}.soporte_placa", tomar(pk), placa={"c": [round(float(cpl[0]), 4), round(float(cpl[1]), 4), 0.0], "incl": round(incl, 3), "tam": F["placa"].get("tam", PLACA_CO)})

grupos = {}
for (k, zg, n, txt, pieza, acab, mat) in decision:
    if mat is None: asignado[k][tri_zona[k] == zg] = True; continue
    sel = (~asignado[k]) & (tri_zona[k] == zg)
    if sel.any(): grupos.setdefault((mat, pieza), []).append(compacta(M[k], sel)); asignado[k] |= sel
def partir(m, nombre, ex):
    if len(m["pos"]) < 60000: nodo(nombre, m, **ex); return
    c = m["pos"][m["idx"]].mean(1)[:, 0]; med = np.median(c)
    partir(compacta(m, c < med), nombre + "_a", ex); partir(compacta(m, c >= med), nombre + "_b", ex)
for (mat, pieza), ms in sorted(grupos.items()):
    ex = {}
    if mat in ACABADO: ex["acabado"] = ACABADO[mat]
    if pieza in PADRE: ex["padre"] = PADRE[pieza]
    if pieza in PIEZA_VISOR: ex["pieza"] = PIEZA_VISOR[pieza]
    if mat == "pintura" and pieza in ("tapa_lateral", "carenado"): ex["zonas"] = ["lateral"]
    if mat == "pintura" and pieza in ("guardabarros_del",): ex["zonas"] = ["guardabarros"]
    partir(unir(ms), f"{mat}.{'piezas' if pieza == 'otra' else pieza}", ex)

# Ruedas: la traslación del nodo es el centro del eje (pivote del giro en el visor)
for nd in nodos:
    if nd["extras"].get("rueda"):
        e = nd["extras"]["eje"]; z = nd["pos"][:, 2]; nd["centro"] = [e[0], e[1], float((z.min() + z.max()) / 2)]
# Rayos X: internos de un GLB anterior de la misma moto (mismas coordenadas)
if F.get("internos_de"):
    _, viejos = glbio.mallas(ruta(F["internos_de"])); nodos += [m for m in viejos if m["extras"].get("interno")]

# Calcas de fábrica (ficha.calcas_fabrica): la lista va en extras.calcas_fabrica del primer nodo pintado y el visor las
# dibuja como capa fina aparte (decal proyectado sobre la pieza, con desfase de profundidad: sin tocar la geometría ni
# z-fighting), cada una con su interruptor en Personalizar. ficha.calcas_zonas {nodo: [zona]} marca las piezas no pintadas
# donde también van (p. ej. el panel negro del costado); el visor busca la pieza por esa zona y el punto «en: [x, y]».
for nd in nodos:
    if nd["name"] in F.get("calcas_zonas", {}): nd["extras"]["zonas"] = sorted(set(nd["extras"].get("zonas", [])) | set(F["calcas_zonas"][nd["name"]]))
if F.get("calcas_fabrica"):
    next(nd for nd in nodos if nd["name"].startswith("pintura."))["extras"]["calcas_fabrica"] = F["calcas_fabrica"]
ESCENA = dict({"modelo_completo": True}, **({"calcas": True} if F.get("calcas_fabrica") else {}))
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
GEN = f"TallerYa: {F['moto']} desde Tripo despiezado y etiquetas del usuario (skill moto-3d-blender)"
glbio.escribir(SALIDA, nodos, GEN, ESCENA)
# Peso: soldar y simplificar con gltf-transform (meshoptimizer, error acotado: la silueta no cambia a la vista) y volver
# a escribir en el formato cuantizado del visor, con los mismos nombres, extras y pivotes de rueda. ficha.simplificar:
# {"ratio": 0.25, "error": 0.0015} por defecto (meta ≤ 1,5 MB, la revisa revisar.py); false lo apaga.
SIMP = F.get("simplificar", {"ratio": 0.25, "error": 0.0015})
if SIMP:
    import subprocess, tempfile
    tmp = tempfile.mkdtemp(); w, s_ = os.path.join(tmp, "w.glb"), os.path.join(tmp, "s.glb")
    def simplificado(error, nombre):
        sal = os.path.join(tmp, nombre)
        subprocess.run(f'npx gltf-transform simplify "{w}" "{sal}" --ratio {SIMP["ratio"]} --error {error} --lock-border {str(SIMP.get("bordes_fijos", True)).lower()}',
                       shell=True, check=True, cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {m["name"]: m for m in glbio.mallas(sal)[1]}
    subprocess.run(f'npx gltf-transform weld "{SALIDA}" "{w}"', shell=True, check=True, cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # (las ruedas con error más fino: con el del resto el rin se metía hasta 7 mm en la llanta)
    cuerpo, ruedas = simplificado(SIMP["error"], "s.glb"), simplificado(SIMP.get("error_ruedas", 0.0007), "r.glb")
    for nd in nodos:  # (los nodos que meshoptimizer dejó vacíos se quedan como estaban)
        m = (ruedas if nd["extras"].get("rueda") else cuerpo).get(nd["name"])
        if m is not None and len(m["idx"]): nd.update(pos=m["pos"], nor=m["nor"], idx=m["idx"])
    glbio.escribir(SALIDA, nodos, GEN, ESCENA)
inf = {"escala": S, "ejes": ejes, "decision": [dict(zip(("parte", "zona", "tri", "texto", "pieza", "acabado", "material"), d)) for d in decision],
       "nodos": [{"name": n["name"], "tri": len(n["idx"])} for n in nodos]}
json.dump(inf, open(os.path.splitext(os.path.abspath(args[0]))[0] + ".armado.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"escala {S:.4f} ejes {ejes} nodos {len(nodos)}")
