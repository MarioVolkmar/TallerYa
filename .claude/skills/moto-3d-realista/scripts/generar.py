"""Arma el GLB de una moto a partir de su ficha JSON (motos/<id>.json).

Uso:  python -I generar.py motos/nmax155.json salida.glb
Tipos de pieza: panel (filos vivos), loft, barrido, torno, caja, llanta, rin (partes: todo|brazos), aro, disco, arco. "espejo": true duplica en -Z.
Imprime piezas, vértices, triángulos y peso.
"""
import sys
import json
import math
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import geom
import glb


def llanta(p):
    x, y = p["centro"]; R = p["R"]; r = p["rin_pulg"] * 0.0127; a = p["ancho"] / 2; h = R - r
    perfil = [(r - 0.004, -a * 0.72), (r + h * 0.2, -a), (r + h * 0.6, -a * 1.02), (R - h * 0.15, -a * 0.86),
              (R - h * 0.02, -a * 0.5), (R, 0), (R - h * 0.02, a * 0.5), (R - h * 0.15, a * 0.86),
              (r + h * 0.6, a * 1.02), (r + h * 0.2, a), (r - 0.004, a * 0.72)]
    return geom.torno(perfil, (x, y, p.get("z", 0)), nseg=p.get("nseg", 56), cerrado=True)


def rin(p):
    x, y = p["centro"]; z = p.get("z", 0); r = p["rin_pulg"] * 0.0127; a = p["ancho"] / 2
    aro = geom.torno([(r - 0.012, -a), (r + 0.006, -a), (r - 0.004, -a * 0.6), (r - 0.006, a * 0.6),
                      (r + 0.006, a), (r - 0.012, a), (r - 0.016, 0)], (x, y, z), nseg=p.get("nseg", 56), cerrado=True)
    cubo = geom.torno([(0.012, -a * 1.1), (0.045, -a * 0.9), (0.05, 0), (0.045, a * 0.9), (0.012, a * 1.1)],
                      (x, y, z), nseg=24)
    brazos = geom.radios((x, y), z + p.get("z_brazos", 0), 0.045, r - 0.01, p.get("brazos", 5),
                         p.get("ancho_brazo", 0.03), p.get("grueso_brazo", 0.022), en_y=p.get("en_y", True),
                         giro=p.get("giro", 90), abre=p.get("abre", 0.5), apertura=p.get("apertura", 0.16))
    # (partes: "brazos" = solo cubo y brazos, para que el aro vaya aparte con el tipo "aro" y quede visible cuando
    # Personalizar cambia el estilo de rin; "aro" = solo el aro)
    partes = p.get("partes", "todo")
    return aro if partes == "aro" else (cubo + brazos) if partes == "brazos" else aro + cubo + brazos


def disco(p):
    x, y = p["centro"]; z = p["z"]; r0, r1 = p["r0"], p["r1"]; e = p.get("grueso", 0.005) / 2
    return geom.torno([(r0, -e), (r1, -e), (r1, e), (r0, e)], (x, y, z), nseg=48, cerrado=True)


def arco(p):
    cx, cy = p["centro"]; r = p["r"]; z = p.get("z", 0)
    angs = np.radians(np.linspace(p["a0"], p["a1"], p.get("pasos", 14)))
    camino = [(cx + r * math.cos(a), cy + r * math.sin(a), z) for a in angs]
    return geom.barrido(camino, p["semiancho"], p["grueso"] / 2, n=p.get("n", 4), nseg=p.get("nseg", 16),
                        pasos_por_tramo=1, arriba=(0, 0, 1))


ficha_secciones = {}


def construir(p):
    t = p["tipo"]
    if t == "loft":
        return geom.loft(p["estaciones"], eje=p.get("eje", "x"), nseg=p.get("nseg", 28), pasos=p.get("pasos", 24))
    if t == "panel":
        sec = ficha_secciones.get(p["seccion"], p["seccion"]) if isinstance(p["seccion"], str) else p["seccion"]
        sec2 = p.get("seccion2"); sec2 = ficha_secciones.get(sec2, sec2) if isinstance(sec2, str) else sec2
        return geom.loft(p["estaciones"], eje=p.get("eje", "x"), pasos=p.get("pasos", 24), seccion=sec, seccion2=sec2)
    if t == "barrido":
        return geom.barrido(p["camino"], p["h"], p["w"], n=p.get("n", 2), nseg=p.get("nseg", 14),
                            pasos_por_tramo=p.get("pasos", 4), arriba=p.get("arriba", (0, 1, 0)), kt=p.get("kt", 1))
    if t == "torno":
        return geom.torno(p["perfil"], p["centro"], eje=p.get("eje", "z"), nseg=p.get("nseg", 40), cerrado=p.get("cerrado", False))
    if t == "caja":
        return geom.caja(p["c"], p["tam"], n=p.get("n", 6))
    if t == "aro":
        return rin({**p, "partes": "aro"})
    return {"llanta": llanta, "rin": rin, "disco": disco, "arco": arco}[t](p)


def main(argv):
    t0 = time.perf_counter()
    ficha = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    ficha_secciones.update(ficha.get("secciones", {}))
    piezas = []
    for p in ficha["piezas"]:
        m = construir(p)
        if p.get("girar"):
            eje, grados, centro = p["girar"]
            m = m.girar(eje, grados, centro)
        if p.get("espejo"):
            m = m + m.espejo_z()
        piezas.append({"nombre": p["nombre"], "material": p["material"], "malla": m, "extras": p.get("extras")})
    peso = glb.escribir(argv[1], piezas)
    nv = sum(len(p["malla"].v) for p in piezas); nf = sum(len(p["malla"].f) for p in piezas)
    print(f"{len(piezas)} piezas, {nv} vértices, {nf} triángulos, {peso / 1024:.0f} KB, {time.perf_counter() - t0:.2f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
