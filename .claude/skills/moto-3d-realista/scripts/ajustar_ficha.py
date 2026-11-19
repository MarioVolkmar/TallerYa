"""Ajuste automático de las estaciones de la ficha por IoU de silueta (descenso por coordenadas).

Uso:  python -I ajustar_ficha.py motos/<id>.json modelos_3d_local/<moto> v360_05 v360_23 ... [--piezas a,b,c]
      [--rondas 2] [--paso 0.012] [--tope 0.05] [--salida motos/<id>.json]
Necesita iou.json con el bloque "torno" (correr antes iou.py --torno): las poses de cámara quedan fijas.
Mueve ys / yt / w de cada estación (y x0/x1 en lofts verticales) de las piezas elegidas, como mucho 'tope'
metros desde el valor inicial, y solo acepta cambios que suben el IoU promedio. Escribe la ficha ajustada.
"""
import sys
import json
import copy
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import generar
import iou as I

DENSIDAD = 60000  # puntos por m² de superficie (≈ 100 k para una moto)


def puntos_pieza(p):
    m = generar.construir(p)
    if p.get("espejo"):
        m = m + m.espejo_z()
    a, b, c = m.v[m.f[:, 0]], m.v[m.f[:, 1]], m.v[m.f[:, 2]]
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    n = max(int(area.sum() * DENSIDAD), 200)
    rng = np.random.default_rng(len(p["nombre"]))
    k = rng.choice(len(area), n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
    return (1 - s)[:, None] * a[k] + (s * (1 - r2))[:, None] * b[k] + (s * r2)[:, None] * c[k]


def main(argv):
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    ruta, carpeta = Path(argv[0]), Path(argv[1])
    vistas = [a for a in argv[2:] if a.startswith("v") and not a.startswith("--")]
    ficha = json.loads(ruta.read_text(encoding="utf-8"))
    generar.ficha_secciones.update(ficha.get("secciones", {}))
    g = json.loads((carpeta / "iou.json").read_text())["torno"]
    refs = {v: I.preparar_ref(carpeta / v / "mascara.png")[:2] for v in vistas}
    elegidas = opt("--piezas", "")
    elegidas = set(elegidas.split(",")) if elegidas else {p["nombre"] for p in ficha["piezas"] if "estaciones" in p}
    paso0, tope, rondas = float(opt("--paso", 0.012)), float(opt("--tope", 0.05)), int(opt("--rondas", 2))
    t0 = time.perf_counter()
    cache = {p["nombre"]: puntos_pieza(p) for p in ficha["piezas"]}
    centro = np.concatenate(list(cache.values())).mean(0)
    # Rápido (v4): la normalización de la cámara (media y dispersión de la proyección) se congela con la moto inicial
    # y cada pieza guarda sus píxeles por vista; una prueba solo vuelve a proyectar la pieza que cambió y suma conteos.
    # (antes: 0,7 s por evaluación proyectando ~100 k puntos en 6 vistas; ahora ~0,05 s)
    P0 = I.poses_torno(g, vistas)
    todos = np.concatenate(list(cache.values())) - centro
    congel = {}
    for v in vistas:
        giro, cab, al, dist, dx, dy, ks = P0[v]
        R = I.rotacion(giro, cab, al); r = np.abs(todos).max(); q = todos @ R.T; z = q[:, 2] + dist * r
        u, w = q[:, 0] / z, -q[:, 1] / z
        cu, cv, esc = refs[v][1]
        congel[v] = (R, r, dist, u.mean(), w.mean(), esc / max(np.sqrt(u.var() + w.var()), 1e-12) * ks, cu + dx, cv + dy)
    def pixeles(pts, v):
        R, r, dist, um, wm, s, ox, oy = congel[v]
        q = (pts - centro) @ R.T; z = q[:, 2] + dist * r
        px = ((q[:, 0] / z - um) * s + ox).astype(int); py = ((-q[:, 1] / z - wm) * s + oy).astype(int)
        H, W = refs[v][0].shape; ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        return np.unique(py[ok] * W + px[ok])
    pix = {n: {v: pixeles(pts, v) for v in vistas} for n, pts in cache.items()}
    conteo = {v: np.zeros(refs[v][0].size, np.int32) for v in vistas}
    for n in pix:
        for v in vistas:
            np.add.at(conteo[v], pix[n][v], 1)
    def puntaje():
        vals = []
        for v in vistas:
            m = (conteo[v] > 0).reshape(refs[v][0].shape)
            vals.append(I.iou(I.cerrar(m, 1), refs[v][0]))
        return float(np.mean(vals))
    def cambiar(nombre, pts):
        for v in vistas:
            np.subtract.at(conteo[v], pix[nombre][v], 1)
        cache[nombre] = pts; pix[nombre] = {v: pixeles(pts, v) for v in vistas}
        for v in vistas:
            np.add.at(conteo[v], pix[nombre][v], 1)
    base = puntaje(); inicial = copy.deepcopy(ficha); evals = 0
    print(f"IoU inicial {base:.4f}")
    for ronda in range(rondas):
        paso = paso0 / (ronda + 1)
        for i, p in enumerate(ficha["piezas"]):
            if p["nombre"] not in elegidas or "estaciones" not in p:
                continue
            campos = ("ys", "yt", "w") if p.get("eje", "x") == "x" else ("x0", "x1", "w")
            for j, e in enumerate(p["estaciones"]):
                for c in campos:
                    if c not in e:
                        continue
                    v0 = inicial["piezas"][i]["estaciones"][j][c]
                    for sg in (1, -1):
                        nuevo = e[c] + sg * paso
                        if abs(nuevo - v0) > tope or (c == "w" and nuevo < 0.004):
                            continue
                        viejo = e[c]; e[c] = nuevo
                        guardado = cache[p["nombre"]]; cambiar(p["nombre"], puntos_pieza(p))
                        val = puntaje(); evals += 1
                        if val > base + 1e-4:
                            base = val
                            break
                        e[c] = viejo; cambiar(p["nombre"], guardado)
        print(f"ronda {ronda + 1}: IoU {base:.4f} ({evals} evaluaciones, {time.perf_counter() - t0:.0f} s)")
    for p in ficha["piezas"]:  # redondeo legible
        for e in p.get("estaciones", []):
            for c in ("ys", "yt", "w", "x0", "x1"):
                if c in e:
                    e[c] = round(e[c], 4)
    salida = Path(opt("--salida", str(ruta)))
    texto = json.dumps(ficha, indent=1, ensure_ascii=False)
    salida.write_text(texto, encoding="utf-8")
    print(f"ficha ajustada -> {salida}")


if __name__ == "__main__":
    main(sys.argv[1:])
