# Tecnica v2: parte la malla en piezas "material.parte" recortando por campos implicitos (bordes lisos, no dentados).
# Cada regla es un campo por vertice (positivo = adentro) hecho de: regiones analiticas (radios, planos), plantillas
# (poligonos proyectados de frente o de atras para las luces) y color suavizado de la textura.
# Coordenadas de la moto: x adelante, y arriba, z hacia el lado del escape (se espeja al exportar).
import sys
sys.path.insert(0, sys.argv[1])
import rend, comp, malla, numpy as np, json
d = sys.argv[2]
P, N, C, I = rend.cargar(d)
I = I.astype(np.int64)
x, y, z = P.T.astype(np.float64)
az = np.abs(z)
nx, ny = N[:, 0].astype(np.float64), N[:, 1].astype(np.float64)
Cs = malla.suavizar(C, I, 5)
r_, g_, b_ = Cs.T
lum = Cs.mean(1)
sat = Cs.max(1) - Cs.min(1)
lum4 = malla.suavizar(C.mean(1), I, 6)

Y = np.minimum.reduce
O = np.maximum.reduce


def banda(v, a, b):
    return np.minimum(v - a, b - v)


claro = Y([lum - 0.50, 0.16 - sat])
claro = malla.suavizar(malla.abrir(malla.cerrar(claro, I, 4), I, 3), I, 2, 0.5)
oscuro = -claro

# --- medidas tomadas de la malla
cf_cara = comp.componentes(len(P), I)
ids, cnt = np.unique(cf_cara, return_counts=True)
en_guarda = np.zeros(len(P), bool)
en_guarda[np.unique(I[cf_cara == ids[np.argsort(-cnt)[1]]])] = True


def circulo(cx, cy):
    m = (az < 0.02) & (y < cy) & (np.abs(np.hypot(x - cx, y - cy) - 0.26) < 0.03)
    A = np.c_[2 * x[m], 2 * y[m], np.ones(m.sum())]
    s = np.linalg.lstsq(A, x[m] ** 2 + y[m] ** 2, rcond=None)[0]
    return float(s[0]), float(s[1]), float(np.sqrt(s[2] + s[0] ** 2 + s[1] ** 2))


xd, yd, Rd = circulo(0.67, 0.26)
xt, yt, Rt = circulo(-0.67, 0.26)
rd = np.hypot(x - xd, y - yd)
rt = np.hypot(x - xt, y - yt)


def medir_disco(r, zmin):
    m = (r < 0.15) & (claro > 0) & (z > zmin) & (z < 0.12) & ~en_guarda
    zc = float(np.median(z[m]))
    m &= np.abs(z - zc) < 0.006
    return zc, float(np.percentile(r[m], 99))


ZR = 0.047
zdd, Rdd = medir_disco(rd, ZR)
zdt, Rdt = medir_disco(rt, ZR)
print(f"ruedas del ({xd:.3f},{yd:.3f}) R={Rd:.3f}  tras ({xt:.3f},{yt:.3f}) R={Rt:.3f}")
print(f"discos del z={zdd:.3f} R={Rdd:.3f}  tras z={zdt:.3f} R={Rdt:.3f}")
punta = (y > 0.975) & (x < 0.30) & (az > 0.39) & (y < 1.07)
xp, yp = float(x[punta].mean()), float(y[punta].mean())
extremo = float(az[punta].max())
m = (az < 0.07) & (y > 0.44) & (y < 0.57) & (x < -0.85) & (nx < -0.5) & (claro < 0)
pb, pa = np.polyfit(y[m], x[m], 1)
placa = {"c": [round(float(pa + pb * 0.505) - 0.006, 3), 0.505, 0], "incl": round(float(-np.arctan(pb)), 3), "tam": [0.235, 0.105]}
print("placa", placa, "manubrio", round(xp, 3), round(yp, 3), round(extremo, 3))

# --- plantillas (mitad en (|z|, y); se reflejan)
FARO = malla.espejo([(0, 0.722), (0.05, 0.705), (0.10, 0.695), (0.145, 0.715), (0.185, 0.75), (0.193, 0.785), (0.175, 0.812), (0.12, 0.817), (0.06, 0.80), (0, 0.782)])
OJO = np.array([(0.03, 0.755), (0.08, 0.737), (0.15, 0.75), (0.17, 0.785), (0.15, 0.80), (0.08, 0.79), (0.035, 0.775)])
DIR_DEL = np.array([(0.19, 0.512), (0.262, 0.518), (0.268, 0.45), (0.24, 0.418), (0.2, 0.425)])
STOP = malla.espejo([(0, 0.713), (0.118, 0.713), (0.13, 0.722), (0.13, 0.752), (0.085, 0.768), (0.085, 0.79), (0.058, 0.795), (0.05, 0.84), (0, 0.845)])
DIR_TRAS = np.array([(0.092, 0.797), (0.092, 0.772), (0.135, 0.756), (0.18, 0.775), (0.172, 0.79)])
PLANT = {k: v for k, v in (("faro", FARO), ("ojo", OJO), ("dir", DIR_DEL), ("stop", STOP), ("dirt", DIR_TRAS))}
for k, v in PLANT.items():
    if f"--{k}" in sys.argv:
        PLANT[k] = np.array(json.loads(sys.argv[sys.argv.index(f"--{k}") + 1]))

# (el recuadro claro y plano que el modelo trae encima del cubre-manubrio: ahi va la pantalla, mirando hacia arriba)
m = (C.mean(1) > 0.45) & (az < 0.09) & (y > 1.05) & (ny > 0.8) & (x > 0.1) & (x < 0.3)
nt = N[m].astype(np.float64).mean(0)
nt[2] = 0
nt /= np.linalg.norm(nt)
ct = np.array([(x[m].min() + x[m].max()) / 2, float(np.percentile(y[m], 90)), 0.0]) + nt * 0.002
pantalla = {"c": [round(float(v), 4) for v in ct], "n": [round(float(v), 4) for v in nt],
            "tam": [round(min(float(2 * az[m].max()) + 0.006, 0.13), 3), round(min(float(x[m].max() - x[m].min()) + 0.006, 0.084), 3)]}
print("pantalla", pantalla, "vertices", int(m.sum()))
REGLAS = []


def regla(nombre, campo, **extras):
    REGLAS.append((nombre, extras, np.asarray(campo, np.float64)))


# --- Ruedas y discos
regla("pintura.guardabarros_del", np.where(en_guarda, 1.0, -1.0), zonas=["guardabarros"])
regla("_quitar", O([Y([Rdd + 0.008 - rd, rd - 0.052, 0.007 - np.abs(z - zdd)]), Y([Rdt + 0.008 - rt, rt - 0.047, 0.007 - np.abs(z - zdt)])]))
regla("caucho.llanta_del", Y([rd - 0.172, Rd + 0.012 - rd, 0.068 - az]), pieza="llanta_del", eje=[xd, yd])
regla("rin.rin_del", Y([0.172 - rd, ZR - az]), pieza="llanta_del", rin=True, eje=[xd, yd])
regla("caucho.llanta_tras", Y([rt - 0.172, Rt + 0.012 - rt, 0.078 - az]), pieza="llanta_tras", eje=[xt, yt])
regla("rin.rin_tras", Y([0.172 - rt, ZR - az]), pieza="llanta_tras", rin=True, eje=[xt, yt])
# --- Luces y colores especiales
regla("dorado.deposito_amortiguador", Y([malla.cerrar(Y([sat - 0.1, r_ - b_ - 0.08]), I, 4), banda(x, -0.72, -0.62), banda(y, 0.51, 0.63), az - 0.14]), pieza="suspension_tras")
lum1 = malla.suavizar(C.mean(1), I, 1)


def pliegue(dist, valido, banda=0.012):
    return malla.a_pliegues(P, I, N, lum1, dist, valido, banda)


# Cola (medida en vista lateral, de arriba y de atras): la luz de stop es la tapa trasera y ENVUELVE la esquina hasta
# una arista inclinada; delante de esa arista, sobre el costado, va el triangulo largo de la direccional.
STOP_LADO = np.array([(-1.0, 0.70), (-0.865, 0.706), (-0.822, 0.713), (-0.826, 0.734), (-0.88, 0.798), (-0.862, 0.818), (-0.853, 0.85), (-1.0, 0.85)])
DIRT_LADO = np.array([(-0.882, 0.802), (-0.738, 0.770), (-0.824, 0.731)])
# La arista inclinada que separa el stop (atras) de las micas laterales (adelante) es UN solo campo para los dos:
# asi comparten borde y no se montan; entre ambos queda un filete de carroceria de ~7 mm que los deja bien definidos.
A_, B_ = np.array([-0.88, 0.798]), np.array([-0.826, 0.734])
n_ar = np.array([-(B_ - A_)[1], (B_ - A_)[0]]) / np.linalg.norm(B_ - A_)
n_ar = n_ar if n_ar[0] > 0 else -n_ar                      # (positivo = hacia adelante, lado de la mica)
arista = pliegue((x - A_[0]) * n_ar[0] + (y - A_[1]) * n_ar[1], (az < 0.2) & (x < -0.74) & (y > 0.69), 0.008)
SEP = 0.0035
ala = Y([pliegue(malla.dist_poligono(x, y, DIRT_LADO), (az > 0.06) & (x < -0.7), 0.008), az - 0.06, arista - SEP])
regla("mica_dir.direccional_tras_a", Y([ala, z]), lampara={"tipo": "direccional"})
regla("mica_dir.direccional_tras_b", ala, lampara={"tipo": "direccional"})
regla("stop.stop", Y([pliegue(malla.dist_poligono(x, y, STOP_LADO), (az < 0.16) & (x < -0.8), 0.008), 0.16 - az, O([-arista - SEP, 0.058 - az])]), lampara={"tipo": "stop"})
ovalo = Y([pliegue((1 - np.hypot((x + 0.787) / 0.031, (y - 0.645) / 0.02)) * 0.02, (az > 0.085) & (x < -0.7) & (y < 0.7), 0.006), az - 0.085])
regla("reflector.reflector_lateral", ovalo)
regla("luz.luz_placa", Y([banda(y, 0.632, 0.678), 0.092 - az, -0.85 - x, lum - 0.42]))
regla("stop.reflector", O([Y([banda(y, 0.596, 0.626), 0.05 - az, -0.88 - x, lum - 0.3]), Y([banda(y, 0.383, 0.417), 0.04 - az, -0.9 - x, lum - 0.33])]))
lente = Y([pliegue(malla.dist_poligono(z, y, PLANT["faro"]), x > 0.55), x - 0.55])
ojo = Y([lente, malla.dist_poligono(az, y, PLANT["ojo"])])
regla("luz.faro_a", Y([ojo, z]), lampara={"tipo": "faro"})
regla("luz.faro_b", ojo, lampara={"tipo": "faro"})
regla("faro.lente", lente)
DIR_LADO = np.array([(0.529, 0.510), (0.578, 0.513), (0.582, 0.505), (0.523, 0.414), (0.495, 0.427), (0.483, 0.455), (0.493, 0.475)])
intermitente = Y([pliegue(malla.dist_poligono(x, y, DIR_LADO), az > 0.185, 0.008), az - 0.185])
regla("mica_dir.direccional_del_a", Y([intermitente, z]), lampara={"tipo": "direccional"})
# (NMAX real: mica transparente con bombillo ambar, igual que atras)
regla("mica_dir.direccional_del_b", intermitente, lampara={"tipo": "direccional"})
regla("ambar.reflectores", Y([banda(x, 0.47, 0.6), banda(y, 0.46, 0.6), banda(az, 0.05, 0.2), lum - 0.4]))
# --- Horquilla y mordaza
eje = np.array([0.50 - xd, 0.66 - yd])
eje /= np.linalg.norm(eje)
dl = np.abs((x - xd) * eje[1] - (y - yd) * eje[0])
regla("oscuro.mordaza_del", Y([0.2 - rd, banda(az, ZR, 0.12), xd - 0.035 - x, y - (yd - 0.02), oscuro, dl - 0.03]), pieza="freno_del")
regla("oscuro.horquilla", O([Y([0.14 - az, 0.64 - y, x - 0.47, 0.075 - dl, oscuro]), Y([0.2 - rd, banda(az, ZR, 0.14)])]), pieza="suspension_del")
# --- Escape, amortiguadores, motor
tope = 0.55 - (x + 0.98) * 0.30
regla("oscuro.escape_silenciador", Y([z - 0.115, banda(x, -1.0, -0.43), tope - y, y - 0.15, -Y([banda(x, -0.73, -0.57), 0.205 - z, y - 0.33])]), padre="escapeFabrica")
regla("oscuro.amortiguadores", Y([banda(x, -0.76, -0.55), banda(y, 0.30, 0.66), banda(az, 0.12, 0.24), oscuro]), pieza="suspension_tras")
bajo = O([Y([0.41 - y, banda(x, -0.66, -0.24)]), Y([0.2 - y, banda(x, -0.24, -0.06)]), Y([0.2 - rt, az - ZR])])
regla("metal.posapies", Y([claro, banda(x, -0.37, -0.23), banda(y, 0.36, 0.48), az - 0.19]))
regla("plastico.caja_cvt", Y([bajo, -0.06 - z, oscuro]), pieza="correa")
regla("chasis.bloque_motor", Y([bajo, oscuro]), pieza="motor")
# --- Manubrio y espejos
arriba = Y([y - 0.975, 0.30 - x])
regla("espejo.luna", Y([arriba, y - 1.10, az - 0.24, -0.5 - nx, lum - 0.33]), padre="espejos.fabrica")
regla("oscuro.espejos", Y([arriba, y - 1.085, az - 0.2]), padre="espejos.fabrica")
regla("caucho.punos", Y([arriba, az - 0.295, 0.03 - np.hypot(x - xp - (extremo - az) * 0.12, y - yp)]))
regla("oscuro.manubrio", arriba, manubrio={"x": round(xp, 3), "y": round(yp, 3), "extremo": round(extremo, 3)}, pantalla=pantalla,
      # (opciones de Personalizar que este modelo no ofrece: las piezas genericas desentonan con el modelo realista)
      sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"])
# --- Visor, cola, asiento
regla("negro_brillo.visor", Y([oscuro, x - 0.33, y - 0.83, y - (0.83 + (0.72 - x) * 0.25), nx + 0.2]), rol="visor_fijo",
      acomodar=[{"grupo": "accesorios.parabrisas", "ref": "abajo_frente", "a": [0.6, 0.93, None]}])
regla("plastico.portaplaca", Y([-0.80 - x, 0.66 - y, 0.17 - az, oscuro]), placa=placa,
      acomodar=[{"grupo": "accesorios.baul", "ref": "abajo", "a": [-0.95, 0.872, 0]}])
regla("oscuro.agarradera", Y([oscuro, -0.52 - x, az - 0.158, y - 0.76, y - (0.79 - (x + 0.9) * 0.3)]))
base_asiento = np.interp(x, [-0.88, -0.5, -0.3, -0.02], [0.83, 0.71, 0.63, 0.59])
regla("asiento.asiento", Y([oscuro, banda(x, -0.88, -0.01), y - base_asiento, ny + 0.3]))
# --- Carroceria
regla("titanio.boomerang", Y([oscuro, lum4 - 0.125, banda(x, -0.48, 0.45), banda(y, 0.30, 0.63), az - 0.1, 0.6 - ny]))
# Calcas de fabrica de este modelo, ubicadas sobre el (en: [x, y] de la moto) segun fotos de la NMAX real:
# nombre con su linea de acento en la tapa trasera, cilindrada en el costado del frontal y ABS en el guardabarros
CALCAS = [
    {"id": "nombre", "nombre": "Nombre NMAX", "tipo": "texto", "texto": "NMAX", "zona": ["lateral"], "cara": "lado", "en": [-0.675, 0.757], "ancho": 0.135, "giro": 0, "color": "letra"},
    {"id": "acento", "nombre": "Línea de acento", "tipo": "franja", "forma": "filete", "zona": ["lateral"], "cara": "lado", "en": [-0.66, 0.732], "ancho": 0.15, "giro": 0, "color": "vivo:#2f5fd0", "color2": "gris"},
    {"id": "cilindrada", "nombre": "Cilindrada 155", "tipo": "numero", "texto": "155", "zona": ["frontal"], "cara": "lado", "en": [0.5, 0.875], "ancho": 0.1, "giro": 0, "color": "vivo:#2f5fd0", "color2": "contorno"},
    {"id": "abs", "nombre": "ABS", "tipo": "texto", "texto": "ABS", "zona": ["guardabarros"], "cara": "lado", "en": [0.745, 0.43], "ancho": 0.042, "giro": 0, "color": "gris"},
]
regla("pintura2.costados", Y([claro, -0.05 - x, y - 0.5]), zonas=["lateral", "cola"], calcas_fabrica=CALCAS)
regla("pintura.frontal", Y([claro, x - 0.1, y - 0.4]), zonas=["frontal", "escudo"])
regla("pintura.quilla", claro, zonas=["quilla"])
regla("plastico.escudo", x - 0.02)
REGLAS.append(("plastico.bajo_trasero", {}, None))

nombres = [r[0] for r in REGLAS]
V = np.column_stack([P, N, C] + [r[2] for r in REGLAS[:-1]])
rec = malla.Recortador(V, I)
for k in range(len(REGLAS) - 1):
    rec.cortar(9 + k, k)
V, F, L = rec.resultado(len(REGLAS) - 1)
rig = [k for k, n in enumerate(nombres) if n.split(".")[-1].startswith(("llanta", "rin", "guardabarros_del", "_quitar")) or n == "_quitar"]
L = malla.quitar_islas(F, L, 60, rig)
pint = [k for k, n in enumerate(nombres) if n.startswith("pintura") and "guardabarros" not in n]
L = malla.quitar_islas(F, L, 260, [k for k in range(len(nombres)) if k not in pint])
quitar = L == nombres.index("_quitar")
F, L = F[~quitar], L[~quitar]
print("caras", len(I), "->", len(F), "vertices", len(P), "->", len(V))

# --- discos nuevos: corona plana con dos filas de agujeros (los del modelo eran pintura, no geometria)


def disco(cx, cy, zc, R, pieza):
    ri = R * 0.50
    nr, na = 5, 96
    rr = np.linspace(ri, R, nr)
    aa = np.linspace(0, 2 * np.pi, na, endpoint=False)
    gr, ga = np.meshgrid(rr, aa, indexing="ij")
    px, py = (gr * np.cos(ga)).ravel(), (gr * np.sin(ga)).ravel()
    i0 = (np.arange(nr - 1)[:, None] * na + np.arange(na)[None, :]).ravel()
    i1 = (np.arange(nr - 1)[:, None] * na + (np.arange(na)[None, :] + 1) % na).ravel()
    caras = np.concatenate([np.stack([i0, i0 + na, i1 + na], 1), np.stack([i0, i1 + na, i1], 1)])
    campo = np.full(len(px), -1.0)
    for fila, (rf, n, rh) in enumerate(((0.66, 14, 0.0052), (0.86, 20, 0.0048))):
        for k in range(n):
            a = 2 * np.pi * (k + 0.5 * fila) / n
            campo = np.maximum(campo, rh - np.hypot(px - R * rf * np.cos(a), py - R * rf * np.sin(a)))
    rc = malla.Recortador(np.column_stack([px, py, campo]), caras)
    rc.cortar(2, 0)
    Vd, Fd, Ld = rc.resultado(1)
    Fd = Fd[Ld == 1]
    usados, inv = np.unique(Fd, return_inverse=True)
    Fd = inv.reshape(-1, 3)
    Vd = Vd[usados]
    n = len(Vd)
    e = 0.0022
    pos = np.concatenate([np.column_stack([cx + Vd[:, 0], cy + Vd[:, 1], np.full(n, zc + e)]), np.column_stack([cx + Vd[:, 0], cy + Vd[:, 1], np.full(n, zc - e)])])
    nor = np.concatenate([np.tile([0, 0, 1.0], (n, 1)), np.tile([0, 0, -1.0], (n, 1))])
    return pos, nor, np.concatenate([Fd, Fd[:, [0, 2, 1]] + n])


extra = {}
for nombre, (cx, cy, zc, R, pieza) in {"disco.disco_del": (xd, yd, zdd, Rdd, "freno_del"), "disco.disco_tras": (xt, yt, zdt, Rdt, "freno_tras")}.items():
    pos, nor, car = disco(cx, cy, zc, R, pieza)
    extra[nombre] = (pos, nor, car)
    REGLAS.append((nombre, {"pieza": pieza}, None))
    print(nombre, "triangulos", len(car))
np.savez(f"{d}/c_extra.npz", **{f"{n}|{k}": a for n, (p_, n_, c_) in extra.items() for k, a in (("pos", p_), ("nor", n_), ("idx", c_))})

usados, inv = np.unique(F, return_inverse=True)
F = inv.reshape(-1, 3)
V = V[usados]
V[:, :3].astype(np.float32).tofile(f"{d}/c_pos.bin")
nn = V[:, 3:6] / np.maximum(np.linalg.norm(V[:, 3:6], axis=1, keepdims=True), 1e-9)
nn.astype(np.float32).tofile(f"{d}/c_nor.bin")
V[:, 6:9].astype(np.float32).tofile(f"{d}/c_col.bin")
F.astype(np.uint32).tofile(f"{d}/c_idx.bin")
L.astype(np.int32).tofile(f"{d}/c_lab.bin")
json.dump({"partes": [{"nombre": n, "extras": e} for n, e, _ in REGLAS], "medidas": {"eje_del": [xd, yd], "eje_tras": [xt, yt], "R_del": Rd, "R_tras": Rt}}, open(f"{d}/c_partes.json", "w"))
cen = V[F][:, :, :3].mean(1)
for k, (n, e, _) in enumerate(REGLAS):
    m = L == k
    if m.any():
        print(f"{n:30s} {m.sum():6d}  x[{cen[m, 0].min():.2f},{cen[m, 0].max():.2f}] y[{cen[m, 1].min():.2f},{cen[m, 1].max():.2f}] z[{cen[m, 2].min():.2f},{cen[m, 2].max():.2f}]")
if "--ver" in sys.argv:
    rng = np.random.default_rng(7)
    MAT = {"pintura": (.85, .85, .9), "pintura2": (.55, .7, .95), "caucho": (.25, .25, .25), "rin": (.5, .3, .7), "metal": (.6, .9, .9),
           "dorado": (1, .85, .2), "ambar": (1, .55, 0), "oscuro": (.2, .45, .3), "plastico": (.35, .3, .28), "chasis": (.6, .2, .2),
           "espejo": (.3, 1, 1), "negro_brillo": (.1, .1, .5), "luz": (1, 1, .5), "stop": (1, 0, 0), "asiento": (.6, .4, .2), "titanio": (.5, .5, .35),
           "faro": (.2, .6, 1), "mica": (.3, 1, .6), "mica_dir": (.3, 1, .6), "reflector": (1, .55, 0), "_quitar": (1, 0, 1), "disco": (.6, .9, .9)}
    pal = np.array([np.clip(np.array(MAT[n.split(".")[0]]) + rng.uniform(-.1, .1, 3), 0, 1) for n, _, _ in REGLAS])
    i = sys.argv.index("--ver")
    Pv, Nv = V[:, :3].astype(np.float32), nn.astype(np.float32)
    ims = []
    for esp in sys.argv[i + 1].split("+"):
        v, esc, caja = esp.split(";")
        caja = eval(caja)
        sel = np.all((cen >= np.array(caja[0]) - 0.02) & (cen <= np.array(caja[1]) + 0.02), axis=1) if caja else np.ones(len(F), bool)
        ims.append(rend.vista(Pv, Nv, F[sel], pal[L[sel]], v, float(esc), caja))
    rend.lamina(ims, f"{d}/corte.png", cols=2)
