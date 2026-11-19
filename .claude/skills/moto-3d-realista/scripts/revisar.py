"""Revisión estricta del GLB contra las fotos, más allá de la silueta: bordes internos, rasgos y hoja comparativa.

Uso:  python -I revisar.py modelo.glb <carpeta_moto> v360_05 v360_32 ... [--salida dir] [--ancho 600]
Requiere haber corrido antes iou.py --torno (lee las poses de <carpeta_moto>/iou.json).

Por cada vista:
1. Renderiza el GLB con la misma cámara que el IoU (pintor por triángulo, PIL) y saca sus líneas:
   silueta, filos (ángulo entre caras > 35°) y juntas entre piezas (cambio de nodo del GLB).
2. Saca los bordes de la foto (Sobel, el 15 % más fuerte dentro de la silueta).
3. Mide solo los bordes INTERNOS (lejos de la silueta, que ya mide el IoU):
   - precisión: de las líneas del modelo, cuántas tienen un borde de la foto a ≤ tol px (¿lo que dibujo existe?);
   - cobertura: de los bordes fuertes de la foto, cuántos tienen una línea del modelo cerca (¿falta algo?).
4. Rasgos (si existe <carpeta_moto>/rasgos.json y la ficha trae "rasgos"): proyecta cada punto 3D de la ficha y
   mide la distancia en cm a donde está marcado en la foto. Un rasgo «calza» en una vista si el error es ≤ 3 cm
   en vistas ortogonales (laterales, frontal, trasera). Las 3/4 se reportan como informativas: aun calibrando giro,
   cabeceo, escala y corrimiento con anclas validadas, su cámara erra 6-15 cm (medido con el eje delantero);
   está CUMPLIDO solo si calza en al menos 2 vistas. Si la vista trae marcados los dos ejes, la cámara se calibra
   con ellos (escala y corrimiento) antes de medir: los ejes son anclas, no rasgos a cumplir.
Escribe <salida>/revision.json y <salida>/hoja_revision.jpg (por vista: foto | render | foto con líneas del
modelo en rojo y bordes de la foto en verde; amarillo = coinciden).
"""
import sys
import json
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import glb
import iou as I

COLOR = {k: v[:3] for k, v in glb.COLORES.items()}


def camara(modelo, pose, info, F):
    """Devuelve proy(X) -> (px, py, z) en la caja de la foto (escala F respecto de los 200 px del IoU)."""
    pts_c = I.puntos_superficie(modelo)  # (centrados; mismo muestreo determinista que iou.py)
    medio = _medio(modelo)
    giro, cab, al, dist, dx, dy, ks = pose
    R = I.rotacion(giro, cab, al); r = np.abs(pts_c).max()
    q = pts_c @ R.T; z = q[:, 2] + dist * r; u, v = q[:, 0] / z, -q[:, 1] / z
    um, vm = u.mean(), v.mean(); su = math.sqrt(max(u.var() + v.var(), 1e-12))
    cu, cv, esc = info; s = esc / su * ks

    def proy(X):
        q = (np.asarray(X, float) - medio) @ R.T; z = q[..., 2] + dist * r
        return ((q[..., 0] / z - um) * s + cu + dx) * F, ((-q[..., 1] / z - vm) * s + cv + dy) * F, z
    return proy


_cache = {}
def _medio(modelo):
    if modelo not in _cache:  # media del muestreo sin centrar (puntos_superficie la resta)
        P, A = [], []
        for _, v, f, _ in glb.leer(modelo):
            a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
            P.append((a, b, c)); A.append(np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2)
        a = np.concatenate([p[0] for p in P]); b = np.concatenate([p[1] for p in P]); c = np.concatenate([p[2] for p in P])
        area = np.concatenate(A); rng = np.random.default_rng(0); n = 120000
        k = rng.choice(len(area), n, p=area / area.sum())
        r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
        pts = (1 - s)[:, None] * a[k] + (s * (1 - r2))[:, None] * b[k] + (s * r2)[:, None] * c[k]
        _cache[modelo] = pts.mean(0)
    return _cache[modelo]


def render(modelo, proy, forma):
    """Pintor por triángulo: imagen de color sombreado, id de triángulo, nodo y normal por triángulo."""
    H, W = forma
    T, N, C, NODO = [], [], [], []
    for k, (nombre, v, f, _) in enumerate(glb.leer(modelo)):
        a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        T.append(np.stack([a, b, c], 1)); N.append(n); NODO.append(np.full(len(f), k))
        C.append(np.tile(COLOR.get(nombre.split(".")[0], (0.5, 0.5, 0.5)), (len(f), 1)))
    T = np.concatenate(T); N = np.concatenate(N); C = np.concatenate(C); NODO = np.concatenate(NODO)
    px, py, z = proy(T)
    orden = np.argsort(-z.mean(1))  # de lejos a cerca
    ids = Image.new("I", (W, H), 0); col = Image.new("RGB", (W, H), (235, 238, 240))
    di, dc = ImageDraw.Draw(ids), ImageDraw.Draw(col)
    luz = np.array([0.35, 0.55, 0.75]); luz /= np.linalg.norm(luz)
    # (la luz va en coordenadas de la moto, de arriba y adelante-izquierda; abs: las caras no tienen lado)
    sombra = 0.3 + 0.7 * np.abs(N @ luz)
    rgb = np.clip(C * sombra[:, None] * 255 * 1.1, 0, 255).astype(int)
    for t in orden:
        poly = list(zip(px[t], py[t]))
        di.polygon(poly, fill=int(t) + 1)
        dc.polygon(poly, fill=tuple(rgb[t]))
    return np.asarray(col), np.asarray(ids, np.int64) - 1, N, NODO


def lineas_modelo(ids, N, NODO, angulo=35):
    e = np.zeros(ids.shape, bool); cosmax = math.cos(math.radians(angulo))
    for a, b in ((ids[:, :-1], ids[:, 1:]), (ids[:-1, :], ids[1:, :])):
        dif = a != b
        fondo = (a < 0) | (b < 0)
        aa, bb = np.where(a < 0, 0, a), np.where(b < 0, 0, b)
        filo = np.abs(np.sum(N[aa] * N[bb], -1)) < cosmax
        junta = NODO[aa] != NODO[bb]
        m = dif & (fondo | filo | junta)
        if a.shape[1] < ids.shape[1]: e[:, :-1] |= m
        else: e[:-1, :] |= m
    sil = (ids >= 0)
    return e, sil


def bordes_foto(foto, mascara, pct=85):
    g = np.asarray(foto.convert("L").filter(ImageFilter.GaussianBlur(1.2)), float)
    gx = np.zeros_like(g); gy = np.zeros_like(g)
    gx[:, 1:-1] = g[:, 2:] - g[:, :-2]; gy[1:-1, :] = g[2:, :] - g[:-2, :]
    mag = np.hypot(gx, gy)
    dentro = mascara
    u = np.percentile(mag[dentro], pct) if dentro.any() else 1e9
    e = (mag >= u) & dentro
    # adelgazar: quedarse con máximos locales en x o en y
    mx = (mag >= np.roll(mag, 1, 1)) & (mag >= np.roll(mag, -1, 1))
    my = (mag >= np.roll(mag, 1, 0)) & (mag >= np.roll(mag, -1, 0))
    return e & (mx | my)


def dil(m, k):
    for _ in range(k):
        y = m.copy(); y[1:] |= m[:-1]; y[:-1] |= m[1:]; y[:, 1:] |= m[:, :-1]; y[:, :-1] |= m[:, 1:]; m = y
    return m


def contorno(m):
    return m & ~(~dil(~m, 1))  # borde de una máscara (m menos su erosión)


def revisar_vista(modelo, carpeta, vista, pose, F, rasgos_ficha, rasgos_foto, tol):
    ref, info, caja = I.preparar_ref(carpeta / vista / "mascara.png")
    H, W = ref.shape[0] * F, ref.shape[1] * F
    foto = Image.open(carpeta / vista / "foto.jpg").convert("RGB").crop(caja).resize((W, H), Image.BILINEAR)
    masc = np.asarray(Image.open(carpeta / vista / "mascara.png").convert("L").crop(caja).resize((W, H))) > 127
    proy = camara(modelo, pose, info, F)
    col, ids, N, NODO = render(modelo, proy, (H, W))
    lm, sil = lineas_modelo(ids, N, NODO)
    lf = bordes_foto(foto, masc)
    lejos = ~dil(contorno(masc) | contorno(sil), 4 * F // 3 + 2)  # internos: lejos de ambas siluetas
    lm_i, lf_i = lm & lejos & masc, lf & lejos & sil
    cerca_f, cerca_m = dil(lf, tol), dil(lm, tol)
    prec = float((lm_i & cerca_f).sum() / max(lm_i.sum(), 1))
    cob = float((lf_i & cerca_m).sum() / max(lf_i.sum(), 1))
    # superposición
    g = np.asarray(foto.convert("L"), float)[..., None] * np.array([1, 1, 1]) * 0.55 + 100
    sup = g.astype(np.uint8).copy()
    sup[lf] = (60, 200, 60); sup[lm] = (230, 40, 40); sup[lm & cerca_f & lf] = (240, 220, 30)
    # rasgos
    res_r, crudos = {}, {}
    caja_w = caja[2] - caja[0]; k_full = caja_w / W  # px de la foto completa por px de la hoja
    # Calibración con anclas: si la vista trae los dos ejes marcados (su posición la fija la distancia entre ejes de
    # la ficha técnica), se corrige escala y corrimiento de la cámara del IoU, que iguala por área y se corre unos cm
    marcas_v = (rasgos_foto or {}).get(vista, {})
    anclas = [k for k in ("eje_del", "eje_tras") if k in marcas_v and k in (rasgos_ficha or {})]
    lateral = abs(math.sin(math.radians(pose[0]))) < 0.2  # (en 3/4 la similitud con 2 puntos no basta)
    if len(anclas) == 2 and lateral:
        U = np.array([proy(np.array(rasgos_ficha[k]))[:2] for k in anclas])
        Mk = np.array([[(marcas_v[k][0] - caja[0]) / k_full, (marcas_v[k][1] - caja[1]) / k_full] for k in anclas])
        cu, cm_ = U.mean(0), Mk.mean(0)
        esc = np.linalg.norm(Mk[1] - Mk[0]) / max(np.linalg.norm(U[1] - U[0]), 1e-6)
        base = proy
        def proy(X, base=base, esc=esc, cu=cu, cm_=cm_):
            u, v, z = base(X)
            return (u - cu[0]) * esc + cm_[0], (v - cu[1]) * esc + cm_[1], z
    for nombre, X in (rasgos_ficha or {}).items():
        marca = (rasgos_foto or {}).get(vista, {}).get(nombre)
        if marca is None:
            continue
        u, v, _ = proy(np.array(X))
        mu, mv = (marca[0] - caja[0]) / k_full, (marca[1] - caja[1]) / k_full
        res_r[nombre] = (math.hypot(u - mu, v - mv), mu - u, mv - v)  # (error y hacia dónde habría que mover el rasgo)
        crudos[nombre] = (float(u), float(v), float(mu), float(mv))
        d = ImageDraw.Draw(im := Image.fromarray(sup)); d.ellipse([mu - 4, mv - 4, mu + 4, mv + 4], outline=(0, 120, 255), width=2)
        d.line([mu, mv, u, v], fill=(0, 120, 255), width=2); sup = np.asarray(im).copy()
    return {"precision_bordes": round(prec, 3), "cobertura_bordes": round(cob, 3), "px": res_r, "crudos": crudos, "anclada": len(anclas) == 2 and lateral,
            "imagenes": (np.asarray(foto), col, sup), "info": info, "proy": proy, "W": W}


def puntos_rasgos(modelo, spec):
    """Rasgo = [x, y, z] fijo (anclas) o {"nodo", "lado": -1|0|1, "punto": centro|min_x|max_x|min_y|max_y|min_z|max_z,
    "en_x": x (opcional: solo los vértices a ±2 cm de ese x)} calculado de los vértices del GLB, para que el control
    mida la geometría y no un número escrito a mano."""
    nodos = {n.split(".", 1)[1]: v for n, v, _, _ in glb.leer(modelo)}
    out = {}
    for k, r in (spec or {}).items():
        if isinstance(r, list):
            out[k] = r; continue
        v = nodos.get(r["nodo"])
        if v is None:
            continue
        if r.get("lado"):
            v = v[np.sign(v[:, 2]) == r["lado"]]
        for i, e in enumerate(("en_x", "en_y", "en_z")):
            if e in r:
                v = v[np.abs(v[:, i] - r[e]) < 0.02]
        p = r.get("punto", "centro")
        if p == "centro":
            out[k] = ((v.min(0) + v.max(0)) / 2).tolist()
        else:
            eje = "xyz".index(p[-1]); i = v[:, eje].argmin() if p.startswith("min") else v[:, eje].argmax()
            out[k] = v[i].tolist()
    return out


def calibrar_oblicua(modelo, pose, rasgos_ficha, crudos, ok_orto, px_previo):
    """3/4: busca giro (±12°) y cabeceo (±6°) y ajusta escala y corrimiento con las anclas (eje delantero y rasgos ya
    validados en vistas ortogonales), dejando afuera el rasgo que se mide. Con menos de 3 anclas deja el error previo."""
    medio = _medio(modelo); r0 = np.abs(I.puntos_superficie(modelo)).max()
    nombres = list(crudos); X = np.array([rasgos_ficha[k] for k in nombres], float) - medio
    Mk = np.array([crudos[k][2:] for k in nombres])
    cand = []
    for dg in range(-12, 13, 2):
        for dc in range(-6, 7, 2):
            R = I.rotacion(pose[0] + dg, pose[1] + dc, 0); q = X @ R.T; z = q[:, 2] + pose[3] * r0
            cand.append(np.stack([q[:, 0] / z, -q[:, 1] / z], 1))
    out = {}
    for i, k in enumerate(nombres):
        A = [j for j, x in enumerate(nombres) if x in ok_orto and x != k]
        if len(A) < 3:
            out[k] = px_previo[k]; continue
        mejor = None
        for U in cand:
            um, mm = U[A].mean(0), Mk[A].mean(0); d = U[A] - um
            esc = float((d * (Mk[A] - mm)).sum() / max((d * d).sum(), 1e-12))
            res = float(np.linalg.norm((d * esc + mm) - Mk[A], axis=1).mean())
            if mejor is None or res < mejor[0]:
                p = (U[i] - um) * esc + mm
                mejor = (res, p)
        p = mejor[1]; mu, mv = Mk[i]
        out[k] = (math.hypot(p[0] - mu, p[1] - mv), mu - p[0], mv - p[1])
    return out


def escala_cm(proy):
    """cm por px de la hoja cerca del centro de la moto (proyecta 1 m en x y en y)."""
    a = np.array([[0, 0.5, 0], [1, 0.5, 0], [0, 1.5, 0]], float)
    u, v, _ = proy(a)
    return 100 / max(math.hypot(u[1] - u[0], v[1] - v[0]), math.hypot(u[2] - u[0], v[2] - v[0]), 1e-6)


def main(argv):
    salida = Path(argv[argv.index("--salida") + 1]) if "--salida" in argv else None
    F = int(argv[argv.index("--ancho") + 1]) // 200 if "--ancho" in argv else 3
    ficha_ruta = argv[argv.index("--ficha") + 1] if "--ficha" in argv else None
    opc = {"--salida", "--ancho", "--ficha"}
    pos = [a for i, a in enumerate(argv) if a not in opc and (i == 0 or argv[i - 1] not in opc)]
    modelo, carpeta, vistas = pos[0], Path(pos[1]), pos[2:]
    salida = salida or carpeta / "revision"; salida.mkdir(parents=True, exist_ok=True)
    poses = {k: v["pose"] for k, v in json.loads((carpeta / "iou.json").read_text()).get("vistas", {}).items()}
    rasgos_ficha = puntos_rasgos(modelo, json.loads(Path(ficha_ruta).read_text(encoding="utf-8")).get("rasgos")) if ficha_ruta else None
    rasgos_foto = json.loads((carpeta / "rasgos.json").read_text()) if (carpeta / "rasgos.json").exists() else None
    tol = 2 * F  # ≈ 2 cm a la escala de la lateral
    res, filas, calza = {}, [], {}
    oblicua = lambda v: min(abs(math.sin(math.radians(poses[v][0]))), abs(math.cos(math.radians(poses[v][0])))) >= 0.2
    # Primero las vistas ortogonales (lateral, frontal, trasera): sus rasgos validados calibran después las 3/4
    orden = sorted(vistas, key=oblicua)
    validos = {}
    for vista in orden:
        r = revisar_vista(modelo, carpeta, vista, poses[vista], F, rasgos_ficha, rasgos_foto, tol)
        cm = escala_cm(r["proy"])
        if oblicua(vista) and r["crudos"]:
            # 3/4: la cámara del IoU erra ±5-8 cm. Se corrige escala y corrimiento con el eje delantero y los rasgos
            # que ya calzaron en vistas ortogonales, dejando afuera el rasgo que se mide (así no se valida a sí mismo)
            ok_orto = {k for k, n in validos.items() if n >= 1} | {"eje_del", "eje_tras"}
            r["px"] = calibrar_oblicua(modelo, poses[vista], rasgos_ficha, r["crudos"], ok_orto, r["px"])
        err = {k: round(v[0] * cm, 1) for k, v in r["px"].items()}
        mover = {k: [round(v[1] * cm, 1), round(v[2] * cm, 1)] for k, v in r["px"].items()}
        if not oblicua(vista):
            for k, e in err.items():
                if e <= 3.0: validos[k] = validos.get(k, 0) + 1
        g = math.radians(poses[vista][0])
        tol_cm = 3.0 if min(abs(math.sin(g)), abs(math.cos(g))) < 0.2 else 6.0  # (3/4: la cámara erra ±5 cm, medido con los ejes)
        for k, e in err.items():
            if oblicua(vista):
                continue  # (3/4: informativas; su cámara erra 6-15 cm, medido con el eje delantero)
            if k in ("eje_del", "eje_tras"):
                continue  # (anclas: con la vista anclada calzan por construcción; si no, miden el error de la cámara)
            calza.setdefault(k, []).append((vista, e, tol_cm))
        ejes = [e for k, e in err.items() if k in ("eje_del", "eje_tras")]
        res[vista] = {"error_camara_cm": round(float(np.mean(ejes)), 1) if ejes and not r["anclada"] else None, "precision_bordes": r["precision_bordes"], "cobertura_bordes": r["cobertura_bordes"], "rasgos_cm": err, "mover_cm_derecha_abajo": mover, "anclada": r["anclada"]}
        filas.append((vista, r["imagenes"]))
        print(f"{vista}: bordes precisión {r['precision_bordes']:.2f} cobertura {r['cobertura_bordes']:.2f}"
              + ("  rasgos(cm) " + " ".join(f"{k}={v}" for k, v in err.items()) if err else ""))
    rasgos = {k: {"vistas": {v: e for v, e, _ in l}, "calza_en": sum(e <= tl for _, e, tl in l), "cumplido": sum(e <= tl for _, e, tl in l) >= 2}
              for k, l in calza.items()}
    prec = float(np.mean([r["precision_bordes"] for r in res.values()])); cob = float(np.mean([r["cobertura_bordes"] for r in res.values()]))
    resumen = {"modelo": modelo, "precision_bordes": round(prec, 3), "cobertura_bordes": round(cob, 3),
               "rasgos_cumplidos": f"{sum(x['cumplido'] for x in rasgos.values())}/{len(rasgos)}", "vistas": res, "rasgos": rasgos}
    (salida / "revision.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False))
    print(f"PROMEDIO bordes internos: precisión {prec:.2f}, cobertura {cob:.2f}; rasgos cumplidos {resumen['rasgos_cumplidos']}")
    for k, x in rasgos.items():
        if not x["cumplido"]:
            print(f"  NO cumple {k}: {x['vistas']}")
    # hoja: una fila por vista, tres columnas, alto común 260 px
    alto = 260; filas_im = []
    filas = [im for v in vistas for (w, im) in filas if w == v]
    for trio in filas:
        ims = [Image.fromarray(np.asarray(t).astype(np.uint8)) for t in trio]
        ims = [i.resize((int(i.size[0] * alto / i.size[1]), alto)) for i in ims]
        fila = Image.new("RGB", (sum(i.size[0] for i in ims) + 20, alto), "white"); x = 0
        for i in ims:
            fila.paste(i, (x, 0)); x += i.size[0] + 10
        filas_im.append(fila)
    Wt = max(f.size[0] for f in filas_im); hoja = Image.new("RGB", (Wt, (alto + 8) * len(filas_im)), "white")
    for j, f in enumerate(filas_im):
        hoja.paste(f, (0, j * (alto + 8)))
    hoja.save(salida / "hoja_revision.jpg", quality=85)


if __name__ == "__main__":
    main(sys.argv[1:])
