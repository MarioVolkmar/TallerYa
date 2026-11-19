"""IoU de silueta del GLB contra las fotos de referencia (con ajuste de cámara a cada foto).

Uso:  python -I iou.py modelo.glb <carpeta_moto> vista1 vista2 ... [--umbral 0.80] [--hoja salida.png]
Cada vista es una subcarpeta con foto.jpg y mascara.png (siluetas.py). Como las fotos libres casi nunca son
ortogonales, se busca la pose de cámara (giro, cabeceo, alabeo, distancia) que mejor calza y se reporta el IoU
en esa pose; la escala y el centro se igualan por área y centroide (la foto no trae escala).
Escribe <carpeta_moto>/iou.json y una hoja de comparación (rojo = solo foto, cian = solo modelo, gris = ambos).
"""
import sys
import json
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
import glb

ANCHO = 200  # resolución de trabajo (lado mayor de la caja de la foto)


def puntos_superficie(ruta, n=120000, excluir=()):
    P, A = [], []
    for nombre, v, f, _ in glb.leer(ruta):
        if nombre.split(".")[0] in excluir:  # (el vidrio casi no se ve en la máscara de la foto)
            continue
        a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        P.append((a, b, c)); A.append(np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2)
    a = np.concatenate([p[0] for p in P]); b = np.concatenate([p[1] for p in P]); c = np.concatenate([p[2] for p in P])
    area = np.concatenate(A); rng = np.random.default_rng(0)
    k = rng.choice(len(area), n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
    pts = (1 - s)[:, None] * a[k] + (s * (1 - r2))[:, None] * b[k] + (s * r2)[:, None] * c[k]
    return pts - pts.mean(0)


def rotacion(giro, cabeceo, alabeo):
    g, c, a = map(math.radians, (giro, cabeceo, alabeo))
    Ry = np.array([[math.cos(g), 0, math.sin(g)], [0, 1, 0], [-math.sin(g), 0, math.cos(g)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(c), -math.sin(c)], [0, math.sin(c), math.cos(c)]])
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def cerrar(m, k=1):
    def dil(x):
        y = x.copy(); y[1:] |= x[:-1]; y[:-1] |= x[1:]; y[:, 1:] |= x[:, :-1]; y[:, :-1] |= x[:, 1:]; return y
    def ero(x):
        return ~dil(~x)
    for _ in range(k): m = dil(m)
    for _ in range(k): m = ero(m)
    return m


def silueta(pts, pose, ref_info, forma):
    giro, cabeceo, alabeo, dist, dx, dy, ks = pose
    q = pts @ rotacion(giro, cabeceo, alabeo).T
    r = np.abs(pts).max()
    z = q[:, 2] + dist * r
    u, v = q[:, 0] / z, -q[:, 1] / z
    # igualar área (aprox. por la dispersión) y centroide con la foto
    cu, cv, escala_ref = ref_info
    su = math.sqrt(max(u.var() + v.var(), 1e-12))
    s = escala_ref / su * ks
    px = ((u - u.mean()) * s + cu + dx).astype(int); py = ((v - v.mean()) * s + cv + dy).astype(int)
    H, W = forma; ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
    m = np.zeros(forma, bool); m[py[ok], px[ok]] = True
    return cerrar(m, 1)


def preparar_ref(ruta_mascara):
    m = np.asarray(Image.open(ruta_mascara).convert("L")) > 127
    ys, xs = np.nonzero(m); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    pad = int(0.08 * max(x1 - x0, y1 - y0))
    caja = (max(x0 - pad, 0), max(y0 - pad, 0), min(x1 + pad, m.shape[1]), min(y1 + pad, m.shape[0]))
    sub = Image.fromarray(m[caja[1]:caja[3], caja[0]:caja[2]].astype(np.uint8) * 255)
    k = ANCHO / max(sub.size); sub = sub.resize((max(int(sub.size[0] * k), 1), max(int(sub.size[1] * k), 1)), Image.BILINEAR)
    r = np.asarray(sub) > 127
    ys, xs = np.nonzero(r)
    return r, (xs.mean(), ys.mean(), math.sqrt(xs.var() + ys.var())), caja


def iou(a, b):
    return (a & b).sum() / max((a | b).sum(), 1)


def ajustar(pts, ref, info, pista=None):
    forma = ref.shape
    f = lambda p: iou(silueta(pts, p, info, forma), ref)
    mejor, mejor_v = None, -1
    giros = range(0, 360, 15) if pista is None else range(pista - 40, pista + 41, 10)
    for g in giros:
        for c in (-12, 0, 12, 24):  # (sin el cabeceo negativo, la foto frontal calzaba en espejo: 0,69 en vez de 0,82)
            p = (g, c, 0, 4.0, 0, 0, 1.0); val = f(p)
            if val > mejor_v: mejor, mejor_v = p, val
    pasos = [6, 6, 3, 1.2, 4, 4, 0.05]
    for _ in range(5):
        for i in range(7):
            for sg in (-1, 1):
                p = list(mejor); p[i] += sg * pasos[i]
                if i == 3: p[3] = max(p[3], 1.6)
                val = f(tuple(p))
                if val > mejor_v: mejor, mejor_v = tuple(p), val
        pasos = [x * 0.6 for x in pasos]
    return mejor, mejor_v


def puntos_de_mallas(mallas, n=120000, centro=None):
    """Igual que puntos_superficie pero desde mallas en memoria [(v, f)] (para el ajuste automático)."""
    a = np.concatenate([v[f[:, 0]] for v, f in mallas]); b = np.concatenate([v[f[:, 1]] for v, f in mallas])
    c = np.concatenate([v[f[:, 2]] for v, f in mallas])
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2; rng = np.random.default_rng(0)
    k = rng.choice(len(area), n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
    pts = (1 - s)[:, None] * a[k] + (s * (1 - r2))[:, None] * b[k] + (s * r2)[:, None] * c[k]
    return pts - (pts.mean(0) if centro is None else centro)


def cuadro_de(vista):
    """'v360_14' -> 14 (cuadro del visor 360°)."""
    return int(vista.split("_")[-1])


def poses_torno(g, vistas):
    """g = {g0, paso, cabeceo, dist, aj: {vista: [dx, dy, ks]}} -> pose por vista."""
    return {v: (g["g0"] + g["paso"] * cuadro_de(v), g["cabeceo"], 0.0, g["dist"], *g["aj"].get(v, [0, 0, 1]))
            for v in vistas}


def evaluar_torno(pts, refs, g):
    P = poses_torno(g, refs.keys())
    return {v: iou(silueta(pts, P[v], refs[v][1], refs[v][0].shape), refs[v][0]) for v in refs}


def ajustar_torno(pts, refs, g=None):
    """Ajusta g0, cabeceo y distancia comunes a todas las vistas de un visor 360°, y un corrimiento por vista."""
    g = g or {"g0": 45.0, "paso": -10.0, "cabeceo": 8.0, "dist": 6.0, "aj": {}}
    media = lambda gg: float(np.mean(list(evaluar_torno(pts, refs, gg).values())))
    if "fijo" not in g:  # búsqueda gruesa del giro inicial (una vuelta)
        mejor = max(range(0, 360, 10), key=lambda g0: media({**g, "g0": g0}))
        g["g0"] = float(mejor)
    pasos = {"g0": 4, "cabeceo": 4, "dist": 1.0}
    val = media(g)
    for _ in range(4):
        for k in pasos:
            for sg in (-1, 1):
                h = dict(g); h[k] = g[k] + sg * pasos[k]
                if k == "dist": h[k] = max(h[k], 2.0)
                vv = media(h)
                if vv > val: g, val = h, vv
        for v in refs:  # corrimiento fino por vista
            aj = list(g["aj"].get(v, [0, 0, 1])); pv = [3, 3, 0.03]
            for _ in range(2):
                for i in range(3):
                    for sg in (-1, 1):
                        a2 = list(aj); a2[i] += sg * pv[i]
                        h = {**g, "aj": {**g["aj"], v: a2}}
                        vv = media(h)
                        if vv > val: g, val, aj = h, vv, a2
                pv = [x * 0.5 for x in pv]
        pasos = {k: x * 0.6 for k, x in pasos.items()}
    g["fijo"] = True
    return g


def main(argv):
    umbral = float(argv[argv.index("--umbral") + 1]) if "--umbral" in argv else 0.80
    hoja = argv[argv.index("--hoja") + 1] if "--hoja" in argv else None
    torno = "--torno" in argv
    argv = [a for a in argv if a != "--torno"]
    opciones = {"--umbral", "--hoja"}
    posicionales = [a for i, a in enumerate(argv) if a not in opciones and (i == 0 or argv[i - 1] not in opciones)]
    modelo, carpeta, vistas = posicionales[0], Path(posicionales[1]), posicionales[2:]
    pts = puntos_superficie(modelo)
    pistas = {}
    previo = carpeta / "iou.json"
    if previo.exists():
        pistas = {k: int(v["pose"][0]) for k, v in json.loads(previo.read_text()).get("vistas", {}).items()}
    res, imgs = {}, []
    g = None
    if torno:
        refs = {v: preparar_ref(carpeta / v / "mascara.png")[:2] for v in vistas}
        anterior = json.loads(previo.read_text()).get("torno") if previo.exists() else None
        g = ajustar_torno(pts, refs, anterior)
        P = poses_torno(g, vistas)
        print(f"torno: g0={g['g0']:.1f} cabeceo={g['cabeceo']:.1f} dist={g['dist']:.1f}")
    for vista in vistas:
        ref, info, _ = preparar_ref(carpeta / vista / "mascara.png")
        if torno:
            pose = P[vista]; val = iou(silueta(pts, pose, info, ref.shape), ref)
        else:
            pose, val = ajustar(pts, ref, info, pistas.get(vista))
        res[vista] = {"iou": round(float(val), 3), "pose": [round(float(x), 2) for x in pose]}
        mod = silueta(pts, pose, info, ref.shape)
        rgb = np.full(ref.shape + (3,), 255, np.uint8)
        rgb[ref & ~mod] = (220, 60, 50); rgb[mod & ~ref] = (40, 180, 200); rgb[ref & mod] = (150, 150, 150)
        imgs.append((vista, val, Image.fromarray(rgb)))
        print(f"{vista}: IoU {val:.3f}  pose giro={pose[0]:.0f} cabeceo={pose[1]:.0f} alabeo={pose[2]:.1f} dist={pose[3]:.1f}")
    prom = float(np.mean([r["iou"] for r in res.values()]))
    salida = {"modelo": str(modelo), "umbral": umbral, "iou_promedio": round(prom, 3),
              "aprobado": all(r["iou"] >= umbral for r in res.values()), "vistas": res}
    if g:
        salida["torno"] = g
    previo.write_text(json.dumps(salida, indent=1, ensure_ascii=False))
    print(f"promedio {prom:.3f}  ({'APROBADO' if salida['aprobado'] else 'NO aprobado'} con umbral {umbral})")
    if hoja and imgs:
        W = sum(i.size[0] for _, _, i in imgs) + 10 * len(imgs); H = max(i.size[1] for _, _, i in imgs)
        out = Image.new("RGB", (W, H), "white"); x = 0
        for _, _, i in imgs:
            out.paste(i, (x, 0)); x += i.size[0] + 10
        out.save(hoja)


if __name__ == "__main__":
    main(sys.argv[1:])
