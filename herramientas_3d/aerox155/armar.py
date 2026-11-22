# Aerox 155: arma el GLB del visor desde el Tripo YA DESPIEZADO (75 partes, una por isla), con el método de la Eco Deluxe.
# Uso: python -I armar.py tripo.glb salida.glb
# Ejes: Tripo trae z adelante, y arriba y -x del lado del escape; el visor quiere x adelante y el escape en -z
# (reflexión: se invierte el orden de los vértices). Escala uniforme por la distancia entre ejes de la ficha (1,35 m).
import sys, json, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ecodeluxe100", "blender"))
import glbio

ENTRADA, SALIDA = sys.argv[1], sys.argv[2]
EJES = 1.35
g, b, base = glbio.leer(ENTRADA)
P = {}
for i, n in enumerate(g["nodes"]):
    if "mesh" not in n: continue
    pr = g["meshes"][n["mesh"]]["primitives"][0]
    pos = glbio.atributo(g, b, base, pr["attributes"]["POSITION"]) + np.array(n.get("translation", [0, 0, 0]))
    nor = glbio.atributo(g, b, base, pr["attributes"]["NORMAL"])
    idx = glbio.atributo(g, b, base, pr["indices"]).astype(np.int64).reshape(-1, 3)
    P[i] = (pos, nor, idx)

# --- Escala y origen: centros de rueda por la caja de cada llanta de Tripo
def caja(i): p = P[i][0]; return p.min(0), p.max(0)
mt, Mt = caja(1); md, Md = caja(23)
ct, cd = (mt + Mt) / 2, (md + Md) / 2
S = EJES / (cd[2] - ct[2])
Y0 = min(mt[1], md[1])
ZM = (cd[2] + ct[2]) / 2
def T(p): return np.stack([(p[:, 2] - ZM) * S, (p[:, 1] - Y0) * S, p[:, 0] * S], 1)
def TN(nn): return np.stack([nn[:, 2], nn[:, 1], nn[:, 0]], 1)
M = {}  # i -> malla en coordenadas del visor
for i, (pos, nor, idx) in P.items():
    M[i] = {"pos": T(pos), "nor": TN(nor), "idx": idx[:, [0, 2, 1]]}
EJE_T = [round(float((ct[2] - ZM) * S), 4), round(float((ct[1] - Y0) * S), 4)]
EJE_D = [round(float((cd[2] - ZM) * S), 4), round(float((cd[1] - Y0) * S), 4)]
print(f"escala {S:.4f}  eje tras {EJE_T}  eje del {EJE_D}  largo {(max(m['pos'][:,0].max() for k,m in M.items() if k) - min(m['pos'][:,0].min() for k,m in M.items() if k)):.3f}")

def unir(*ms):
    pos, nor, idx, o = [], [], [], 0
    for m in ms:
        pos.append(m["pos"]); nor.append(m["nor"]); idx.append(m["idx"] + o); o += len(m["pos"])
    return {"pos": np.vstack(pos), "nor": np.vstack(nor), "idx": np.vstack(idx)}
def compacta(m, sel):
    idx = m["idx"][sel]; usados = np.unique(idx); mapa = -np.ones(len(m["pos"]), np.int64); mapa[usados] = np.arange(len(usados))
    return {"pos": m["pos"][usados], "nor": m["nor"][usados], "idx": mapa[idx]}
def por_tri(m, f):
    c = m["pos"][m["idx"]].mean(1); s = f(c); return compacta(m, s), compacta(m, ~s)
def reflejar_z(m):
    return {"pos": m["pos"] * [1, 1, -1], "nor": m["nor"] * [1, 1, -1], "idx": m["idx"][:, [0, 2, 1]]}
def cortar(m, n, d, s=None):
    """Parte la malla por el plano n·p = d partiendo los triángulos del borde (sin dientes). Devuelve (n·p>d, n·p<d).
    Con s (un valor por vértice) corta por la superficie s = 0, p. ej. un cilindro alrededor del eje."""
    pos = list(m["pos"]); nor = list(m["nor"]); s = m["pos"] @ np.asarray(n, float) - d if s is None else s
    arriba, abajo, cache = [], [], {}
    def corte(a, b_):
        k = (min(a, b_), max(a, b_))
        if k not in cache:
            t = s[a] / (s[a] - s[b_]); pos.append(m["pos"][a] + t * (m["pos"][b_] - m["pos"][a]))
            nor.append(m["nor"][a] + t * (m["nor"][b_] - m["nor"][a])); cache[k] = len(pos) - 1
        return cache[k]
    for tri in m["idx"]:
        sg = s[tri] > 0
        if sg.all(): arriba.append(tri); continue
        if not sg.any(): abajo.append(tri); continue
        solo = np.where(sg != (sg.sum() >= 2))[0][0]  # el vértice que queda solo de su lado
        a, b1, c1 = tri[solo], tri[(solo + 1) % 3], tri[(solo + 2) % 3]
        p, q = corte(a, b1), corte(a, c1)
        uno, dos = ([a, p, q], [[p, b1, c1], [p, c1, q]])
        (arriba if sg[solo] else abajo).append(uno)
        for t in dos: (abajo if sg[solo] else arriba).append(t)
    full = {"pos": np.array(pos), "nor": np.array(nor), "idx": np.zeros((0, 3), np.int64)}
    A = dict(full, idx=np.array(arriba, np.int64).reshape(-1, 3)); B = dict(full, idx=np.array(abajo, np.int64).reshape(-1, 3))
    return compacta(A, np.ones(len(A["idx"]), bool)), compacta(B, np.ones(len(B["idx"]), bool))
def radio(m, eje): return np.hypot(m["pos"][:, 0] - eje[0], m["pos"][:, 1] - eje[1])

piezas = []  # (nombre, malla, extras)
def pieza(nombre, m, **ex): piezas.append((nombre, m, ex))
usados = {0}
def G(*ids):
    usados.update(ids); return unir(*[M[i] for i in ids])

# --- Ruedas: llanta, rin y freno. La delantera de Tripo trae llanta y rin juntos: se separan por radio
RIN = {"roughness": 0.3, "metalness": 0.7, "clearcoat": 0.5}
llanta_t = G(1); rin_t = G(20, 38)
del_m = G(23)
def centro_rueda(m, eje):
    """Centro del eje por ajuste de círculo (mínimos cuadrados) a la banda de rodadura en el plano xy: la caja de Tripo
    no es exacta y una rueda descentrada cabecea al girar."""
    p = m["pos"]; r = radio(m, eje); q = p[r > np.quantile(r, 0.85)]
    A = np.c_[2 * q[:, 0], 2 * q[:, 1], np.ones(len(q))]; sol = np.linalg.lstsq(A, (q[:, :2] ** 2).sum(1), rcond=None)[0]
    return [round(float(sol[0]), 4), round(float(sol[1]), 4)]
EJE_T = centro_rueda(llanta_t, np.array(EJE_T)); EJE_D = centro_rueda(del_m, np.array(EJE_D))
print("ejes ajustados", EJE_T, EJE_D)
# La delantera trae llanta y rin en una sola parte: se separan por el cilindro r = 0,098 (en unidades de Tripo) partiendo
# los triángulos del borde, sin dientes
llanta_d, rin_d = cortar(del_m, None, None, s=radio(del_m, np.array(EJE_D)) - 0.098 * S)
def ajustar_rin(rin, llanta, eje, nombre):
    """Rin integrado: la pestaña del aro cubre el talón de la llanta (radio 3 % de la llanta + 4 mm), escalado parejo."""
    r_ll = np.quantile(radio(llanta, eje), 0.03); r_rin = np.quantile(radio(rin, eje), 0.995)
    f = (r_ll + 0.004) / r_rin
    if f > 1:
        rin["pos"][:, :2] = (rin["pos"][:, :2] - eje) * f + eje
    print(f"{nombre}: talón llanta r={r_ll:.3f}  pestaña rin r={r_rin:.3f}  factor rin {f:.3f}  llanta R={radio(llanta, eje).max():.3f}")
ajustar_rin(rin_t, llanta_t, np.array(EJE_T), "tras"); ajustar_rin(rin_d, llanta_d, np.array(EJE_D), "del")
# Ruedas de Tripo que giran tal cual (extras.rueda): el visor no tornea la llanta; el nodo va con su traslación en el eje
# (final.py) y eso hace de pivote. Todo lo que gira con la rueda lleva la misma marca; el freno y la horquilla, no.
pieza("caucho.llanta_tras", llanta_t, rueda="tras", pieza="llanta_tras", eje=EJE_T)
pieza("caucho.llanta_del", llanta_d, rueda="del", pieza="llanta_del", eje=EJE_D)
pieza("rin.rin_tras", rin_t, rueda="tras", pieza="llanta_tras", rin=True, eje=EJE_T, acabado=RIN)
pieza("rin.rin_del", rin_d, rueda="del", pieza="llanta_del", rin=True, eje=EJE_D, acabado=RIN)
pieza("metal.disco_del", G(25), rueda="del", pieza="llanta_del", eje=EJE_D, acabado={"roughness": 0.35, "metalness": 0.9})
pieza("metal.freno_tras", G(22), rueda="tras", pieza="llanta_tras", eje=EJE_T, acabado={"roughness": 0.4, "metalness": 0.85})

# --- Luces (como la Eco): faros = mica curva de Tripo + reflector detrás + bombillo; direccionales y stop cortados por planos
def normal_media(m):
    t = m["pos"][m["idx"]]; n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]).sum(0); return n / np.linalg.norm(n)
for lado, i in (("a", 52), ("b", 43)):   # a = derecha (-z), b = izquierda (+z)
    mica = G(i); c = mica["pos"].mean(0); n = normal_media(mica)
    if n[0] < 0: n = -n
    refl = {"pos": c + (mica["pos"] - c) * 0.97 - n * 0.004, "nor": mica["nor"].copy(), "idx": mica["idx"].copy()}
    bomb = {"pos": c + (mica["pos"] - c) * 0.8 - n * 0.002, "nor": mica["nor"].copy(), "idx": mica["idx"].copy()}
    pieza(f"vidrio.mica_faro_{lado}", mica, doble=True)
    pieza(f"cromo.reflector_faro_{lado}", refl, doble=True, acabado={"roughness": 0.15, "metalness": 1.0})
    pieza(f"luz.faro_{lado}", bomb, lampara={"tipo": "faro"})
# Direccional delantera derecha de Tripo (71); la izquierda no vino: se refleja. Mica = mitad de adelante.
dd = G(71); cx = dd["pos"][:, 0].mean()
mica_d, carc_d = cortar(dd, [1, 0, 0], cx - 0.004)
pieza("ambar.direccional_del_a", mica_d, lampara={"tipo": "direccional"})
pieza("ambar.direccional_del_b", reflejar_z(mica_d), lampara={"tipo": "direccional"})
pieza("negro_brillo.carcasa_direccionales_del", unir(carc_d, reflejar_z(carc_d)))
# Traseras (55 izq, 58 der): vástago hacia adentro, mica en la punta de afuera
vast, micas = [], {}
for lado, i in (("b", 55), ("a", 58)):
    m = G(i); z = m["pos"][:, 2]; zc = z.min() + 0.55 * (z.max() - z.min()) if z.mean() > 0 else z.max() - 0.55 * (z.max() - z.min())
    afuera, adentro = cortar(m, [0, 0, np.sign(z.mean())], abs(zc))
    pieza(f"ambar.direccional_tras_{lado}", afuera, lampara={"tipo": "direccional"}); vast.append(adentro)
pieza("oscuro.vastago_direccionales", unir(*vast))
# Stop: la cara de atrás de la pieza roja bajo el colín (7); el resto es carcasa negra
st = G(7); xs = st["pos"][:, 0]
stop, carc_s = cortar(st, [-1, 0, 0], -(xs.min() + 0.05))
pieza("stop.stop", stop, lampara={"tipo": "stop"})
pieza("negro_brillo.carcasa_stop", carc_s, doble=True)
pieza("negro_brillo.luz_placa", G(41))

# --- Carrocería (Personalizar pinta "pintura"), plásticos y negro
# Según las fotos, la pintura va en el frente, el escudo de afuera, el túnel, las tapas laterales, el colín y el
# guardabarros. Bajos y pisaderas (parte 12 bajo y = 0,45 m), la franja de la pisadera (32), la tapa del túnel (42) y el
# escudo de adentro (37, 40) son plástico negro texturizado.
PLAST = {"roughness": 0.86, "metalness": 0}
c12 = G(12); tunel, bajos = cortar(c12, [0, 1, 0], 0.45)
pieza("pintura.carenado", tunel, doble=True, zonas=["lateral"])
pieza("plastico.bajos", unir(bajos, G(32)), doble=True)
pieza("plastico.tapa_tunel", G(42), doble=True)
pieza("pintura.frente", G(34, 8), doble=True, rol="visor_fijo")
pieza("pintura.escudo", G(45), doble=True)
pieza("plastico.escudo_interior", G(37, 40), doble=True)
pieza("pintura.tapa_lateral_izq", G(74), doble=True, zonas=["lateral"])
pieza("pintura.tapa_lateral_der", G(16), doble=True, zonas=["lateral"])
pieza("pintura.colin", G(27, 19), doble=True)
pieza("pintura.guardabarros_del", G(14), doble=True, zonas=["guardabarros"])
pieza("plastico.interior", G(21, 26, 31, 50), doble=True)
# Placa: sobre el soporte que Tripo modeló con el tamaño de la placa (parte 62, antes «reflector»), en su cara que mira atrás (triángulos con normal hacia -x), con su plano medido: centro
# ponderado por área e inclinación por la normal media (incl negativa = arriba hacia adelante). Placa de moto: 17 × 12 cm.
pl = G(62); pa = unir(G(2), pl); t = pl["pos"][pl["idx"]]; nt = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); ar = np.linalg.norm(nt, axis=1)
nt = nt / np.maximum(ar[:, None], 1e-12); ct3 = t.mean(1)
atras = nt[:, 0] < -0.5
if (ar[atras].sum() if atras.any() else 0) < 1e-4:
    atras = nt[:, 0] > 0.5; nt = -nt
w = ar[atras]; cp = (ct3[atras] * w[:, None]).sum(0) / w.sum(); nm = (nt[atras] * w[:, None]).sum(0); nm /= np.linalg.norm(nm)
incl = -float(np.arcsin(np.clip(nm[1], -1, 1)))
cpl = cp + nm * 0.006
print(f"placa c={np.round(cpl, 3)} normal={np.round(nm, 2)} incl={incl:.3f} área={w.sum():.4f}")
pieza("plastico.portaplaca", pa, doble=True,
      placa={"c": [round(float(cpl[0]), 4), round(float(cpl[1]), 4), 0.0], "incl": round(incl, 3), "tam": [0.17, 0.12]})
# Visor ahumado translúcido (lo único translúcido junto con las micas)
pieza("vidrio_oscuro.visor", G(30), doble=True)
pieza("asiento.asiento", G(18), acabado={"roughness": 0.62, "sheen": 0.35, "sheenRoughness": 0.5, "clearcoat": 0.12, "clearcoatRoughness": 0.6})
pieza("oscuro.frente_centro", G(44, 51, 59), doble=True)
pieza("oscuro.agarradera", G(70))

# --- Manubrio, espejos, palancas
mb = G(56); zx = float(mb["pos"][:, 0].mean())
# Tablero: en la cara de atrás de la caja del instrumento (la capota negra de la parte 56, bajo el visor), mirando al
# piloto. Triángulos del centro (|z| < 6 cm) con normal hacia atrás y arriba, de la mitad alta: centro por área y normal media.
t = mb["pos"][mb["idx"]]; nt = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); ar = np.linalg.norm(nt, axis=1)
nt = nt / np.maximum(ar[:, None], 1e-12); c3 = t.mean(1)
sel = (np.abs(c3[:, 2]) < 0.06) & (nt[:, 0] < -0.3) & (nt[:, 1] > 0.2) & (np.abs(nt[:, 2]) < 0.5)
sel &= c3[:, 1] > np.quantile(c3[sel, 1], 0.4)
w = ar[sel]; cc = (c3[sel] * w[:, None]).sum(0) / w.sum(); nn = (nt[sel] * w[:, None]).sum(0); nn[2] = 0; nn /= np.linalg.norm(nn)
ct_ = [float(cc[0] + nn[0] * 0.004), float(cc[1] + nn[1] * 0.004)]; nt_ = nn[:2]
print(f"tablero c={np.round(ct_, 3)} n={np.round(nt_, 2)} área={w.sum():.4f}")
pieza("oscuro.manubrio", mb, manubrio={"x": round(zx, 4), "y": round(float(np.quantile(mb["pos"][:, 1], 0.6)), 4), "extremo": round(float(np.abs(mb["pos"][:, 2]).max()), 4)},
      sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"],
      pantalla=[{"c": [round(ct_[0], 4), round(ct_[1], 4), 0.0], "n": [round(float(nt_[0]), 3), round(float(nt_[1]), 3), 0.0], "tam": [0.12, 0.055], "dibujo": "tacometro"}])
pieza("oscuro.espejos", G(4), padre="espejos.fabrica", acabado={"roughness": 0.35, "metalness": 0.1, "clearcoat": 0.6})
pieza("caucho.punos", G(48), acabado={"roughness": 0.95, "metalness": 0})
pieza("metal.palancas", G(49, 65))

# --- Suspensión, chasis, motor, escape
pieza("metal.horquilla", G(33, 67, 57, 60), pieza="suspension_del", acabado={"roughness": 0.28, "metalness": 0.9})
pieza("oscuro.horquilla_baja", G(6, 10, 36), pieza="suspension_del")
pieza("metal.amortiguadores", G(5, 15), pieza="suspension_tras")
pieza("chasis.caballete", G(9))
pieza("chasis.pata", G(72, 64))
pieza("motor.bloque", G(73, 28), pieza="motor")
pieza("carter.tapa_cvt", G(17), acabado={"roughness": 0.55, "metalness": 0.3})
pieza("oscuro.escape", G(11, 29, 24, 46), padre="escapeFabrica", acabado={"roughness": 0.5, "metalness": 0.45})
pieza("negro_brillo.protector_escape", G(3), padre="escapeFabrica")
resto = [i for i in M if i not in usados]
print("resto ->", resto)
pieza("oscuro.piezas", G(*resto))

json.dump({"eje_tras": EJE_T, "eje_del": EJE_D, "escala": S}, open(SALIDA + ".json", "w"))
glbio.escribir(SALIDA, [{"name": n, "pos": m["pos"], "nor": m["nor"], "idx": m["idx"], "extras": ex} for n, m, ex in piezas],
               "TallerYa: Aerox 155 desde Tripo despiezado, método Eco Deluxe")
