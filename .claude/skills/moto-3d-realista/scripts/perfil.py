"""Perfil lateral en metros desde la máscara de una vista lateral pura (convención del visor).

Uso:  python -I perfil.py <mascara.png> --entre-ejes 1.34 [--frente derecha|izquierda] [--paso 0.05]
Calibra con los puntos de apoyo de las llantas (los más bajos a cada lado = ejes) y la distancia entre ejes.
Imprime, cada 'paso' metros de x, los tramos ocupados en y (y0-y1), para dibujar las estaciones de la ficha.
Con --estaciones x0:x1:paso [--techo 1.0] además escribe en JSON estaciones de partida {x, ys, yt} del cuerpo: en cada x,
el tramo más alto bajo 'techo' (sin manubrio ni espejos) de al menos 4 cm; ys es el fondo de ese tramo. Son el punto de
partida de costados/frontal/asiento: el ojo solo decide dónde termina cada pieza (v4: antes se copiaban a mano).
"""
import json
import sys
import numpy as np
from PIL import Image


def calibrar(m, entre_ejes, frente="derecha"):
    ys, xs = np.nonzero(m)
    suelo = ys.max()
    banda = m[suelo - max(3, int(0.01 * m.shape[0])):suelo + 1].any(0)
    cols = np.nonzero(banda)[0]
    mitad = (cols.min() + cols.max()) / 2
    izq = cols[cols < mitad]; der = cols[cols >= mitad]
    xi, xd = izq.mean(), der.mean()                 # apoyo de cada llanta ~ bajo cada eje
    k = entre_ejes / (xd - xi)                      # metros por píxel
    signo = 1 if frente == "derecha" else -1
    cx = (xi + xd) / 2
    a_metros = lambda px, py: (signo * (px - cx) * k, (suelo - py) * k)
    return a_metros, k, cx, suelo, signo


def main(argv):
    m = np.asarray(Image.open(argv[0]).convert("L")) > 127
    wb = float(argv[argv.index("--entre-ejes") + 1]) if "--entre-ejes" in argv else 1.34
    frente = argv[argv.index("--frente") + 1] if "--frente" in argv else "derecha"
    paso = float(argv[argv.index("--paso") + 1]) if "--paso" in argv else 0.05
    _, k, cx, suelo, signo = calibrar(m, wb, frente)
    ys, xs = np.nonzero(m)
    x_m = signo * (xs - cx) * k
    print(f"escala {1 / k:.0f} px/m; largo {(x_m.max() - x_m.min()):.3f} m (x {x_m.min():.3f}..{x_m.max():.3f}); alto {(suelo - ys.min()) * k:.3f} m")
    tabla = {}
    for x in np.arange(np.floor(x_m.min() / paso) * paso, x_m.max() + paso, paso):
        px = int(round(cx + signo * x / k))
        if not (0 <= px < m.shape[1]):
            continue
        col = m[:, px]
        tramos, dentro = [], False
        for py in range(len(col)):
            if col[py] and not dentro:
                ini, dentro = py, True
            elif not col[py] and dentro:
                tramos.append(((suelo - py) * k, (suelo - ini) * k)); dentro = False
        if dentro:
            tramos.append(((suelo - len(col)) * k, (suelo - ini) * k))
        tramos = [(a, b) for a, b in tramos if b - a > 0.008][::-1]
        print(f"x={x:+.2f}: " + "  ".join(f"{a:.2f}-{b:.2f}" for a, b in tramos))
        tabla[round(float(x), 3)] = tramos
    if "--estaciones" in argv:
        x0, x1, p = map(float, argv[argv.index("--estaciones") + 1].split(":"))
        techo = float(argv[argv.index("--techo") + 1]) if "--techo" in argv else 1.0
        est = []
        for x in np.arange(x0, x1 + p / 2, p):
            clave = min(tabla, key=lambda c: abs(c - x))
            cuerpo = [(a, min(b, techo)) for a, b in tabla[clave] if a < techo and min(b, techo) - a >= 0.04]
            if cuerpo:
                a, b = max(cuerpo, key=lambda t: t[1])
                est.append({"x": round(float(x), 3), "ys": round(a, 3), "yt": round(b, 3)})
        print(json.dumps(est))


if __name__ == "__main__":
    main(sys.argv[1:])
