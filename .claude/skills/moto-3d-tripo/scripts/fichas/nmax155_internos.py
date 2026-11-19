# Piezas internas de mantenimiento de la NMAX con forma real (en vez de las cajas de la moto generica): bateria, carter
# y aceite, bujia, filtro de aire, radiador, y lo que se ve en Rayos X dentro del motor y de la transmision.
# Coordenadas de la moto antes de espejar: x adelante, y arriba, z hacia el escape (la correa va en -z).
import sys
sys.path.insert(0, sys.argv[1])
import formas as F, numpy as np, json
d = sys.argv[2]
med = json.load(open(f"{d}/c_partes.json"))["medidas"]
xt, yt = med["eje_tras"]
PIEZAS = []


def pon(nombre, pieza, *fs, pliegue=38):
    PIEZAS.append((nombre, pieza, F.con_normales(F.unir(*fs), pliegue)))


def cil(r, largo, base, eje, n=12, canto=0.0):
    perfil = [(0, 0), (r - canto, 0), (r, canto), (r, largo - canto), (r - canto, largo), (0, largo)] if canto else [(0, 0), (r, 0), (r, largo), (0, largo)]
    return F.revolucion(perfil, base, eje, n)


# ---------- Bateria (12 V sellada: caja, tapa con 6 tapones, bornes y capuchon rojo del positivo)
B = np.array([0.22, 0.462, 0.0])
pon("bateria.bat_cuerpo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.07, 0.105, 0.007), -0.0565, 0.0565, 0.004), B))
tapa = [F.mover(F.extrusion(F.rect_redondo(0.075, 0.016, 0.004), -0.059, 0.059, 0.003), B + [0, 0.058, 0])]
tapa += [cil(0.0065, 0.005, B + [-0.014, 0.065, zz], (0, 1, 0), 10) for zz in np.linspace(-0.032, 0.032, 6)]
pon("oscuro.bat_tapa", "bateria", *tapa)
pon("metal.bat_bornes", "bateria", *[cil(0.008, 0.014, B + [0.02, 0.064, zz], (0, 1, 0), 10, 0.002) for zz in (-0.044, 0.044)])
pon("rojo.bat_positivo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.026, 0.02, 0.005), -0.013, 0.013, 0.003), B + [0.02, 0.078, 0.044]))

# ---------- Motor: ciguenal, biela, piston y cilindro (lo que deja ver Rayos X dentro del bloque)
C = np.array([-0.30, 0.265, 0.0])                      # eje del ciguenal
a = np.radians(12)
dc = np.array([np.cos(a), np.sin(a), 0.0])              # el cilindro va casi acostado hacia adelante
perfil_cig = [(0, -0.055), (0.012, -0.055), (0.012, -0.024), (0.05, -0.024), (0.05, -0.008), (0.014, -0.008),
              (0.014, 0.008), (0.05, 0.008), (0.05, 0.024), (0.012, 0.024), (0.012, 0.055), (0, 0.055)]
pon("metal.motor_ciguenal", "motor", F.revolucion(perfil_cig, C, (0, 0, 1), 20), F.tubo([C + dc * 0.034, C + dc * 0.138], 0.008, 8))
pon("motor.motor_cilindro", "motor", F.revolucion([(0.034, 0.078), (0.045, 0.078), (0.045, 0.185), (0.052, 0.188), (0.052, 0.232), (0.038, 0.248), (0, 0.248)], C, dc, 20))
pon("cromo.motor_piston", "motor", F.revolucion([(0, 0.128), (0.029, 0.128), (0.029, 0.134), (0.0275, 0.136), (0.029, 0.138), (0.029, 0.168), (0, 0.17)], C, dc, 20))

# ---------- Bujia: rosca, hexagono, aislador con nervios y terminal, mas el capuchon con su cable
a2 = np.radians(42)
db = np.array([np.cos(a2), np.sin(a2), 0.0])
bb = C + dc * 0.222 + np.array([0, 0.028, 0.0])
pon("metal.bujia_rosca", "bujia", F.revolucion([(0, -0.002), (0.0035, -0.002), (0.0035, 0.002), (0.0062, 0.002), (0.0062, 0.020)], bb, db, 10),
    F.revolucion([(0.0062, 0.020), (0.0105, 0.020), (0.0105, 0.029), (0.0062, 0.029)], bb, db, 6),
    F.revolucion([(0.0, 0.066), (0.0038, 0.066), (0.0038, 0.074), (0, 0.074)], bb, db, 8))
nerv = [(0.0062, 0.029), (0.0082, 0.031)]
for k in range(5):
    t0 = 0.034 + k * 0.006
    nerv += [(0.0082, t0), (0.0066, t0 + 0.0015), (0.0066, t0 + 0.0035), (0.0082, t0 + 0.005)]
nerv += [(0.0060, 0.066), (0, 0.066)]
pon("bujia.bujia_aislador", "bujia", F.revolucion(nerv, bb, db, 12))
punta = bb + db * 0.058
cable = [punta + db * 0.045, punta + db * 0.07 + [0, 0.012, 0.01], punta + db * 0.08 + [-0.03, 0.04, 0.03], punta + [-0.02, 0.085, 0.05], punta + [-0.07, 0.10, 0.06]]
pon("oscuro.bujia_capuchon", "bujia", F.revolucion([(0, 0), (0.0115, 0), (0.0125, 0.004), (0.0125, 0.034), (0.008, 0.046), (0, 0.046)], punta, db, 12), F.tubo(cable, 0.0045, 6))

# ---------- Aceite: carter con su forma, nivel de aceite, tapon de drenaje y tapa de llenado con varilla
carter = F.suave([(-0.13, -0.02), (-0.12, -0.10), (-0.05, -0.125), (0.06, -0.12), (0.11, -0.08), (0.12, -0.02), (0.09, 0.03), (-0.09, 0.03)], 2)
pon("carter.aceite_carter", "aceite", F.mover(F.extrusion(carter, -0.075, 0.075, 0.014), C))
nivel = F.suave([(-0.112, -0.062), (-0.108, -0.095), (-0.05, -0.114), (0.055, -0.109), (0.098, -0.076), (0.104, -0.062)], 1)
pon("aceiteVisible.aceite_nivel", "aceite", F.mover(F.extrusion(nivel, -0.06, 0.06, 0.004), C))
pon("metal.aceite_tapon", "aceite", F.revolucion([(0, 0), (0.011, 0), (0.011, 0.008), (0.0075, 0.008), (0.0075, 0.016), (0, 0.016)], C + [-0.03, -0.122, 0], (0, -1, 0), 6))
et = np.array([0, 0.45, 1.0])
et /= np.linalg.norm(et)
bt = C + [0.075, -0.005, 0.072]
pon("oscuro.aceite_tapa", "aceite", F.revolucion([(0, 0), (0.017, 0), (0.017, 0.009), (0.012, 0.011), (0.012, 0.02), (0.0, 0.02)], bt, et, 12),
    F.tubo([bt, bt - et * 0.07], 0.0025, 6))

# ---------- Correa CVT: variador (adelante), polea conducida con campana del embrague (atras) y la correa
zc = -0.13
A, Bp = np.array([C[0], C[1], zc]), np.array([xt, yt, zc])


def polea(r, centro):
    return F.revolucion([(0, -0.022), (0.014, -0.022), (r, -0.013), (r, -0.010), (0.02, -0.001), (0.02, 0.001), (r, 0.010), (r, 0.013), (0.014, 0.022), (0, 0.022)], centro, (0, 0, 1), 24)


campana = F.revolucion([(0, -0.03), (0.082, -0.03), (0.086, -0.026), (0.086, -0.058), (0.08, -0.058), (0.08, -0.034), (0, -0.034)], Bp, (0, 0, 1), 24)
pon("metal.cvt_poleas", "correa", polea(0.062, A), polea(0.08, Bp), campana, F.tubo([A + [0, 0, -0.03], A + [0, 0, 0.1]], 0.009, 8), F.tubo([Bp + [0, 0, -0.06], Bp + [0, 0, 0.05]], 0.009, 8))
rA, rB = 0.048, 0.07
dv = (Bp - A)[:2]
fi = np.arctan2(dv[1], dv[0])
al = np.arccos((rA - rB) / np.linalg.norm(dv))
arcoA = [A + [rA * np.cos(t), rA * np.sin(t), 0] for t in np.linspace(fi + al, fi - al + 2 * np.pi, 14)]
arcoB = [Bp + [rB * np.cos(t), rB * np.sin(t), 0] for t in np.linspace(fi - al, fi + al, 14)]
pon("caucho.cvt_correa", "correa", F.tubo(arcoA + arcoB, 0.0075, 6, cerrado=True))

# ---------- Filtro de aire: caja con tapa atornillada, toma, ducto al motor y elemento plisado
caja = F.suave([(-0.63, 0.37), (-0.60, 0.345), (-0.43, 0.345), (-0.38, 0.375), (-0.375, 0.44), (-0.42, 0.475), (-0.60, 0.475), (-0.635, 0.445)], 2)
pon("oscuro.filtro_caja", "filtro_aire", F.extrusion(caja, -0.205, -0.115, 0.012))
torn = [cil(0.006, 0.006, (px, py, -0.203), (0, 0, -1), 6) for px, py in ((-0.60, 0.37), (-0.42, 0.365), (-0.40, 0.44), (-0.51, 0.462), (-0.61, 0.445))]
pon("metal.filtro_tornillos", "filtro_aire", *torn)
pon("caucho.filtro_ductos", "filtro_aire",
    F.tubo([(-0.60, 0.455, -0.16), (-0.655, 0.49, -0.15), (-0.70, 0.505, -0.125), (-0.73, 0.50, -0.10)], 0.017, 8),
    F.tubo([(-0.40, 0.40, -0.14), (-0.34, 0.395, -0.09), (-0.28, 0.375, -0.04), (-0.225, 0.352, -0.005)], 0.019, 8),
    F.revolucion([(0.021, 0), (0.0225, 0), (0.0225, 0.008), (0.021, 0.008)], (-0.345, 0.396, -0.094), (0.72, -0.05, 0.69), 10))
x0, x1, n = -0.60, -0.415, 12
xs = np.linspace(x0, x1, 2 * n + 1)
zs = np.where(np.arange(2 * n + 1) % 2 == 0, -0.19, -0.135)
Pp = np.concatenate([np.column_stack([xs, np.full_like(xs, 0.372), zs]), np.column_stack([xs, np.full_like(xs, 0.452), zs])])
k = np.arange(2 * n)
m = 2 * n + 1
una = np.concatenate([np.stack([k, k + 1, k + 1 + m], 1), np.stack([k, k + 1 + m, k + m], 1)])
pon("bujia.filtro_elemento", "filtro_aire", (Pp, una), (Pp, una[:, [0, 2, 1]]), pliegue=10)

# ---------- Refrigeracion: radiador (panal con aletas y tanques), tapa, mangueras y deposito de reserva
Rc = C + [0.0, 0.012, 0.0]
panal = [F.mover(F.extrusion(F.rect_redondo(0.15, 0.15, 0.008), 0.108, 0.132, 0.003), Rc)]
panal += [F.mover(F.extrusion(F.rect_redondo(0.14, 0.0045, 0.001, 1), 0.132, 0.1365), Rc + [0, yy, 0]) for yy in np.linspace(-0.06, 0.06, 9)]
pon("radiador.radiador_panal", "refrigeracion", *panal)
tanques = [F.mover(F.extrusion(F.rect_redondo(0.162, 0.024, 0.009), 0.103, 0.138, 0.004), Rc + [0, yy, 0]) for yy in (-0.086, 0.086)]
pon("oscuro.radiador_tanques", "refrigeracion", *tanques, cil(0.014, 0.012, Rc + [-0.055, 0.098, 0.12], (0, 1, 0), 12, 0.002))
cab = C + dc * 0.2
pon("caucho.radiador_mangueras", "refrigeracion",
    F.tubo([Rc + [0.06, 0.098, 0.12], Rc + [0.11, 0.115, 0.11], Rc + [0.16, 0.105, 0.075], cab + [0, 0.05, 0.03]], 0.011, 8),
    F.tubo([Rc + [0.055, -0.098, 0.12], Rc + [0.10, -0.10, 0.10], Rc + [0.135, -0.07, 0.065], C + dc * 0.12 + [0, -0.04, 0.035]], 0.011, 8))
bot = F.suave([(-0.035, -0.045), (0.035, -0.045), (0.04, 0.02), (0.02, 0.05), (-0.02, 0.05), (-0.04, 0.02)], 2)
pon("bujia.refrigerante_deposito", "refrigeracion", F.mover(F.extrusion(bot, -0.018, 0.018, 0.006), (-0.03, 0.235, 0.115)),
    cil(0.011, 0.012, (-0.03, 0.283, 0.115), (0, 1, 0), 10, 0.002),
    F.tubo([(-0.045, 0.2, 0.115), (-0.12, 0.19, 0.12), (-0.2, 0.2, 0.125), Rc + [0.07, -0.08, 0.125]], 0.004, 6))

datos, extras, tot = {}, {}, 0
for nombre, pieza, (P, N, I) in PIEZAS:
    datos[f"{nombre}|pos"], datos[f"{nombre}|nor"], datos[f"{nombre}|idx"] = P, N, I
    extras[nombre] = {"pieza": pieza, "interno": True}
    tot += len(I)
np.savez(f"{d}/i_extra.npz", **datos)
json.dump(extras, open(f"{d}/i_extras.json", "w"))
print("piezas internas", len(PIEZAS), "triangulos", tot)
if "--ver" in sys.argv:
    import rend
    Pt = np.concatenate([p for _, _, (p, _, _) in PIEZAS]).astype(np.float32)
    Nt = np.concatenate([n for _, _, (_, n, _) in PIEZAS]).astype(np.float32)
    off = np.cumsum([0] + [len(p) for _, _, (p, _, _) in PIEZAS])
    It = np.concatenate([i + off[k] for k, (_, _, (_, _, i)) in enumerate(PIEZAS)])
    rng = np.random.default_rng(3)
    col = np.concatenate([np.tile(rng.uniform(0.25, 0.95, 3), (len(i), 1)) for _, _, (_, _, i) in PIEZAS])
    rend.lamina([rend.vista(Pt, Nt, It, col, v, 1100) for v in ("der", "izq", "arriba")], f"{d}/internos.png", cols=1)
