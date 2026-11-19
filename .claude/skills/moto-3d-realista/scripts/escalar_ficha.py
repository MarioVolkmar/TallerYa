"""Arranca la ficha de una moto nueva escalando una plantilla de su familia (motos/plantillas/<familia>.json).

Uso:  python -I escalar_ficha.py motos/plantillas/scooter.json motos/<id>.json --entre-ejes 1.30 --asiento 0.79
      --ancho 0.72 [--rin-del 13 --rin-tras 13 --r-del 0.24 --r-tras 0.25] [--moto "Marca Modelo"]
Escala x por la distancia entre ejes, y por la altura del asiento y z por el ancho total, contra las medidas de la
plantilla ("base"). Las ruedas no se estiran: van con su radio (o el nuevo) y su eje queda en x = ±entre_ejes/2.
Deja la ficha lista para medir el perfil (perfil.py), generar, IoU y revisión (revisar.py).
"""
import sys
import json
from pathlib import Path

RUEDAS = {"llanta", "rin", "aro", "disco", "arco"}


def escalar(ficha, sx, sy, sz, ruedas):
    def xyz(p):
        return [p[0] * sx, p[1] * sy] + ([p[2] * sz] if len(p) > 2 else [])
    for p in ficha["piezas"]:
        t = p["tipo"]
        if t in RUEDAS:
            delante = p["centro"][0] > 0
            R = ruedas["del" if delante else "tras"]
            x = ficha["base"]["entre_ejes"] * sx / 2 * (1 if delante else -1)
            p["centro"] = [x, R.get("r", p["centro"][1])] + p["centro"][2:]
            if t == "llanta" and "r" in R:
                p["R"] = R["r"]
            if "rin" in R and "rin_pulg" in p:
                p["rin_pulg"] = R["rin"]
            if "z" in p:
                p["z"] *= sz
            continue
        for e in p.get("estaciones", []):
            if p.get("eje", "x") == "x":
                e["x"] *= sx; e["ys"] *= sy; e["yt"] *= sy
            else:
                e["y"] *= sy; e["x0"] *= sx; e["x1"] *= sx
            e["w"] = e.get("w", 0.1) * sz
            if "zc" in e:
                e["zc"] *= sz
        if "camino" in p:
            p["camino"] = [xyz(q) for q in p["camino"]]
            if not isinstance(p.get("w"), list):
                p["w"] = p.get("w", 0.01) * sz
        if "c" in p:
            p["c"] = xyz(p["c"]); p["tam"] = [p["tam"][0] * sx, p["tam"][1] * sy, p["tam"][2] * sz]
        if t == "torno":
            p["centro"] = xyz(p["centro"])
        ex = p.get("extras") or {}
        if "placa" in ex:
            ex["placa"]["c"] = xyz(ex["placa"]["c"])
        if "manubrio" in ex:
            m = ex["manubrio"]; m.update(x=m["x"] * sx, y=m["y"] * sy, extremo=m["extremo"] * sz)
        for a in ex.get("acomodar", []):
            a["a"] = [None if v is None else v * k for v, k in zip(a["a"], (sx, sy, sz))]
    for k, r in list(ficha.get("rasgos", {}).items()):
        if isinstance(r, list):
            ficha["rasgos"][k] = xyz(r)
        elif "en_x" in r:
            r["en_x"] *= sx
    return ficha


def main(argv):
    opt = lambda k, d=None: float(argv[argv.index(k) + 1]) if k in argv else d
    plantilla, salida = Path(argv[0]), Path(argv[1])
    f = json.loads(plantilla.read_text(encoding="utf-8"))
    b = f["base"]
    sx = opt("--entre-ejes", b["entre_ejes"]) / b["entre_ejes"]
    sy = opt("--asiento", b["asiento"]) / b["asiento"]
    sz = opt("--ancho", b["ancho"]) / b["ancho"]
    ruedas = {"del": {k: v for k, v in (("r", opt("--r-del")), ("rin", opt("--rin-del"))) if v},
              "tras": {k: v for k, v in (("r", opt("--r-tras")), ("rin", opt("--rin-tras"))) if v}}
    f = escalar(f, sx, sy, sz, ruedas)
    f["base"] = {"entre_ejes": b["entre_ejes"] * sx, "asiento": b["asiento"] * sy, "ancho": b["ancho"] * sz,
                 "desde": str(plantilla.name)}
    if "--moto" in argv:
        f["moto"] = argv[argv.index("--moto") + 1]
    f["medidas"] = {"nota": "Escalada desde la plantilla: reemplazar por las medidas de la ficha técnica, con su fuente."}
    salida.write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{salida}: escala x {sx:.3f}, y {sy:.3f}, z {sz:.3f}; {len(f['piezas'])} piezas")


if __name__ == "__main__":
    main(sys.argv[1:])
