"""Paso 3 (Blender, sin ventana): corta la malla por los contornos lisos de los paneles (bisect con planos verticales
por cada tramo de ~1 cm) y reetiqueta: los bordes entre tapa lateral, aletas, colín y lo negro siguen la curva, no
los triángulos de Tripo.
Uso: blender -b --factory-startup --python cortar.py -- DIR   (lee DIR/grueso.npz y DIR/contornos.json, escribe DIR/despiece.npz)"""
import json
import sys
from pathlib import Path

import bmesh
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

d = Path(sys.argv[sys.argv.index("--") + 1])
g = np.load(d / "grueso.npz")
W, F, lab0 = g["W"], g["F"], g["lab"]
polis = {k: np.array(v) for k, v in json.load(open(d / "contornos.json")).items()}
PANELES = ("tapa_lateral", "aletas", "colin")
CAMBIABLES = {"aletas", "tapa_lateral", "colin", "chasis", "cubierta_trasera", "escape"}  # (escape: su regla gruesa tapaba la tapa lateral derecha)

C0 = W[F].mean(1)
kd = KDTree(len(C0))
for i, c in enumerate(C0):
    kd.insert(c, i)
kd.balance()

bm = bmesh.new()
vs = [bm.verts.new(p) for p in W]
for f in F:
    try:
        bm.faces.new([vs[i] for i in f])
    except ValueError:
        pass
bm.normal_update()
cortes = 0
for nombre, P in polis.items():
    for i in range(len(P)):
        p, q = P[i], P[(i + 1) % len(P)]
        lo, hi = np.minimum(p, q) - 0.02, np.maximum(p, q) + 0.02
        caras = [f for f in bm.faces if abs(f.calc_center_median().z) > 0.04 and
                 lo[0] < f.calc_center_median().x < hi[0] and lo[1] < f.calc_center_median().y < hi[1]]
        if not caras:
            continue
        geom = list({v for f in caras for v in f.verts}) + list({e for f in caras for e in f.edges}) + caras
        t = q - p
        n = Vector((-t[1], t[0], 0.0)).normalized()
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector((p[0], p[1], 0.0)), plane_no=n, dist=1e-6)
        cortes += 1
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.verts.index_update()
V2 = np.array([v.co[:] for v in bm.verts])
F2 = np.array([[v.index for v in f.verts] for f in bm.faces])
C2 = V2[F2].mean(1)
lab = np.array([lab0[kd.find(c)[1]] for c in C2], dtype=object)


def dentro(P, pts):
    x, y = pts[:, 0], pts[:, 1]
    ins = np.zeros(len(pts), bool)
    xa, ya = P[:, 0], P[:, 1]
    xb, yb = np.roll(xa, -1), np.roll(ya, -1)
    for i in range(len(P)):
        cruza = ((ya[i] > y) != (yb[i] > y)) & (x < (xb[i] - xa[i]) * (y - ya[i]) / (yb[i] - ya[i] + 1e-12) + xa[i])
        ins ^= cruza
    return ins


n = np.cross(V2[F2[:, 1]] - V2[F2[:, 0]], V2[F2[:, 2]] - V2[F2[:, 0]])
nz = np.abs(n[:, 2]) / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
cand = np.isin(lab, list(CAMBIABLES)) & (np.abs(C2[:, 2]) > 0.06) & (nz > 0.25)
asignado = np.zeros(len(C2), bool)
for p in PANELES:
    m = cand & ~asignado & dentro(polis[p], C2)
    lab[m] = p
    asignado |= m
# (lo que era panel y quedó fuera de toda curva vuelve a lo negro de su zona)
fuera = cand & ~asignado & np.isin(lab, PANELES)
lab[fuera & (C2[:, 0] > -0.35)] = "chasis"
lab[fuera & (C2[:, 0] <= -0.35)] = "cubierta_trasera"
np.savez_compressed(d / "despiece.npz", W=V2, F=F2, lab=lab.astype(str))
u, c = np.unique(lab.astype(str), return_counts=True)
print("CORTES", cortes, "caras", len(F), "->", len(F2), dict(zip(u, c.tolist())))
