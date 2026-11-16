"""Separa los números del despiece para que cada uno tenga su área de toque (≥ radioToqueMin px a 360).
Corre el final de cada pieza: suma un pequeño desplazamiento en el ÚLTIMO paso en que se mueve. No toca el armado
(anc y et quedan igual), así que los números del armado no cambian.

  python separar_numeros.py datos/<lamina>.json              muestra cuánto movería, sin escribir
  python separar_numeros.py datos/<lamina>.json --escribir   escribe el JSON (indent=1, sin ASCII forzado)

Calcula la distancia necesaria como validar_esquema.py: encuadre del despiece estimado (±34 alrededor de los números,
proporción 900:700) y un ancho de dibujo de 301 px a 360. Después, correr validar_esquema.py y medir_lamina.py:
este script no sabe qué arte pintado encima tapa un número (eso lo dice medir_lamina con «→rect»).
"""
import argparse, json, math, pathlib, sys

ASPECTO = 900 / 700


def finales(D):
    suma = {}
    for st in D["pasos"]:
        for pid, (dx, dy) in st.get("m", {}).items():
            s = suma.setdefault(pid, [0, 0]); s[0] += dx; s[1] += dy
    return {p["id"]: [p["anc"][0] + p["et"][0] + suma.get(p["id"], [0, 0])[0], p["anc"][1] + p["et"][1] + suma.get(p["id"], [0, 0])[1]] for p in D["piezas"]}


def necesaria(fin, ancho_px, radio, margen=1.08):
    xs = [x for x, _ in fin.values()]; ys = [y for _, y in fin.values()]
    ew, eh = max(xs) - min(xs) + 68, max(ys) - min(ys) + 68
    if ew / eh < ASPECTO: ew = eh * ASPECTO
    return 2 * radio * margen * ew / ancho_px


def separar(D, ancho_px=301, vueltas=600):
    radio = D.get("radioToqueMin", 9)
    ult = {}
    for i, st in enumerate(D["pasos"]):
        for pid in st.get("m", {}): ult[pid] = i
    sin_paso = [p["id"] for p in D["piezas"] if p["id"] not in ult]
    movido = {}
    for _ in range(vueltas):
        fin = finales(D); obj = necesaria(fin, ancho_px, radio); ids = [i for i in fin if i in ult]; mov = False
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                A, B = fin[ids[a]], fin[ids[b]]; dx, dy = B[0] - A[0], B[1] - A[1]; d = math.hypot(dx, dy)
                if d >= obj: continue
                if d < 1e-6: dx, dy, d = 1.0, 0.0, 1.0
                e = (obj - d) / 2 + 0.5; ux, uy = dx / d * e, dy / d * e
                for pid, sg in ((ids[a], -1), (ids[b], 1)):
                    m = D["pasos"][ult[pid]]["m"][pid]; m[0] += sg * ux; m[1] += sg * uy
                    movido[pid] = movido.get(pid, 0) + e
                    fin[pid][0] += sg * ux; fin[pid][1] += sg * uy
                mov = True
        if not mov: break
    for st in D["pasos"]:
        for pid in st.get("m", {}): st["m"][pid] = [round(st["m"][pid][0]), round(st["m"][pid][1])]
    return movido, sin_paso, round(necesaria(finales(D), ancho_px, radio))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("json"); ap.add_argument("--escribir", action="store_true")
    ap.add_argument("--ancho", type=float, default=301, help="ancho del dibujo a 360, en px")
    a = ap.parse_args(); ruta = pathlib.Path(a.json)
    D = json.loads(ruta.read_text(encoding="utf-8"))
    movido, sin_paso, obj = separar(D, a.ancho)
    print(f"{len(movido)} piezas corridas en el despiece (distancia mínima entre números: {obj} unidades)")
    for pid, e in sorted(movido.items(), key=lambda x: -x[1])[:10]: print(f"  {pid}: {e:.0f} unidades")
    if sin_paso: print("  aviso: sin paso que las mueva (no se pueden separar):", ", ".join(sin_paso))
    if a.escribir:
        ruta.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8"); print("escrito:", ruta)
    else:
        print("(sin escribir; agrega --escribir)")


if __name__ == "__main__":
    main()
