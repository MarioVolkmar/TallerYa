# Motor generico del corte (no sabe nada de ninguna moto): carga la malla preparada, ofrece las herramientas para
# armar campos (regiones, plantillas, pliegues, color si lo hay), reparte en piezas y guarda. Las reglas de cada moto
# viven en su ficha (fichas/<moto>.py), que recibe un objeto Corte. Lo lento (suavizados, pliegues, componentes) se
# guarda en T/cache con la huella de sus datos: una vuelta que solo cambia una regla no recalcula lo demas.
# Coordenadas de la moto: x adelante, y arriba, z hacia el lado del escape (se espeja al exportar).
import hashlib
import json
import os
import time

import numpy as np

import comp
import malla
import rend

Y = np.minimum.reduce      # interseccion de campos
O = np.maximum.reduce      # union de campos


def banda(v, a, b):
    """Positivo cuando a < v < b."""
    return np.minimum(v - a, b - v)


class Corte:
    def __init__(self, T, pref="s"):
        self.T = T
        self.P, self.N, self.C, I = rend.cargar(T, pref)
        self.I = I.astype(np.int64)
        self.x, self.y, self.z = self.P.T.astype(np.float64)
        self.az = np.abs(self.z)
        self.nx, self.ny, self.nz = self.N.T.astype(np.float64)
        w = json.load(open(f"{T}/w.json")) if os.path.exists(f"{T}/w.json") else {}
        self.con_color = bool(w.get("con_color", True))
        self.reglas, self.extra, self.medidas = [], {}, {}
        self._lum1 = None
        os.makedirs(f"{T}/cache", exist_ok=True)
        self.aciertos = self.fallos = 0

    # ---------- memoria en disco
    def memo(self, nombre, calcular, *datos):
        h = hashlib.sha1(nombre.encode())
        for d in datos:
            h.update(np.ascontiguousarray(d).tobytes() if isinstance(d, np.ndarray) else repr(d).encode())
        ruta = f"{self.T}/cache/{nombre}_{h.hexdigest()[:16]}.npy"
        if os.path.exists(ruta):
            self.aciertos += 1
            return np.load(ruta)
        self.fallos += 1
        v = calcular()
        np.save(ruta, v)
        return v

    # ---------- campos
    def suavizar(self, v, vueltas=2, peso=0.6):
        return self.memo("suav", lambda: malla.suavizar(v, self.I, vueltas, peso), v, vueltas, peso)

    def cerrar(self, campo, anillos=3):
        return self.memo("cerrar", lambda: malla.cerrar(campo, self.I, anillos), campo, anillos)

    def abrir(self, campo, anillos=2):
        return self.memo("abrir", lambda: malla.abrir(campo, self.I, anillos), campo, anillos)

    def poligono(self, u, v, pol):
        """Distancia con signo (positiva adentro) a una plantilla dibujada en el plano (u, v)."""
        return malla.dist_poligono(u, v, np.asarray(pol, np.float64))

    def circulo_plantilla(self, u, v, c, r):
        return r - np.hypot(u - c[0], v - c[1])

    def recta(self, u, v, a, b):
        """Distancia a la recta a->b en el plano (u, v)."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        e = (b - a) / np.linalg.norm(b - a)
        return np.abs((u - a[0]) * e[1] - (v - a[1]) * e[0])

    def pliegue(self, dist, valido, ancho=0.012):
        """Lleva el borde de una plantilla al pliegue mas cercano del modelo (y al cambio de tono, si hay color)."""
        if self._lum1 is None:
            self._lum1 = malla.suavizar(self.C.mean(1), self.I, 1) if self.con_color else np.zeros(len(self.P))
        return self.memo("pliegue", lambda: malla.a_pliegues(self.P, self.I, self.N, self._lum1, dist, valido, ancho), dist, valido, ancho)

    def color(self):
        """(lum, sat, Cs) suavizados; solo si el modelo trae textura."""
        if not self.con_color:
            raise RuntimeError("el modelo no trae textura: las reglas van solo por forma")
        Cs = self.suavizar(self.C, 5)
        return Cs.mean(1), Cs.max(1) - Cs.min(1), Cs

    def componentes(self):
        """Etiqueta de componente suelto por cara y lista de ids de mayor a menor."""
        cf = self.memo("comp", lambda: comp.componentes(len(self.P), self.I), self.I)
        ids, cnt = np.unique(cf, return_counts=True)
        return cf, ids[np.argsort(-cnt)]

    # ---------- medidas
    def rueda(self, cx, cy, R=0.30, margen=0.04):
        """Ajusta el circulo de la banda de rodadura (mitad de abajo, plano medio). Devuelve (x, y, R, radio por vertice)."""
        x, y = self.x, self.y
        m = (self.az < 0.02) & (y < cy) & (np.abs(np.hypot(x - cx, y - cy) - R) < margen)
        A = np.c_[2 * x[m], 2 * y[m], np.ones(m.sum())]
        s = np.linalg.lstsq(A, x[m] ** 2 + y[m] ** 2, rcond=None)[0]
        cx, cy, R = float(s[0]), float(s[1]), float(np.sqrt(s[2] + s[0] ** 2 + s[1] ** 2))
        return cx, cy, R, np.hypot(x - cx, y - cy)

    # ---------- reglas
    def regla(self, nombre, campo, **extras):
        self.reglas.append((nombre, extras, np.asarray(campo, np.float64)))

    def resto(self, nombre, **extras):
        self.reglas.append((nombre, extras, None))

    def disco(self, nombre, cx, cy, zc, R, pieza, interior=0.5, filas=((0.66, 14, 0.0052), (0.86, 20, 0.0048)), grueso=0.0022):
        """Disco de freno nuevo: corona plana con agujeros reales (los del modelo son pintura o relieve)."""
        ri = R * interior
        nr, na = 5, 96
        gr, ga = np.meshgrid(np.linspace(ri, R, nr), np.linspace(0, 2 * np.pi, na, endpoint=False), indexing="ij")
        px, py = (gr * np.cos(ga)).ravel(), (gr * np.sin(ga)).ravel()
        i0 = (np.arange(nr - 1)[:, None] * na + np.arange(na)[None, :]).ravel()
        i1 = (np.arange(nr - 1)[:, None] * na + (np.arange(na)[None, :] + 1) % na).ravel()
        caras = np.concatenate([np.stack([i0, i0 + na, i1 + na], 1), np.stack([i0, i1 + na, i1], 1)])
        campo = np.full(len(px), -1.0)
        for fila, (rf, n, rh) in enumerate(filas):
            for k in range(n):
                a = 2 * np.pi * (k + 0.5 * fila) / n
                campo = np.maximum(campo, rh - np.hypot(px - R * rf * np.cos(a), py - R * rf * np.sin(a)))
        rc = malla.Recortador(np.column_stack([px, py, campo]), caras)
        rc.cortar(2, 0)
        Vd, Fd, Ld = rc.resultado(1)
        Fd = Fd[Ld == 1]
        usados, inv = np.unique(Fd, return_inverse=True)
        Fd, Vd = inv.reshape(-1, 3), Vd[usados]
        n = len(Vd)
        pos = np.concatenate([np.column_stack([cx + Vd[:, 0], cy + Vd[:, 1], np.full(n, zc + s * grueso)]) for s in (1, -1)])
        nor = np.concatenate([np.tile([0, 0, 1.0], (n, 1)), np.tile([0, 0, -1.0], (n, 1))])
        self.extra[nombre] = (pos, nor, np.concatenate([Fd, Fd[:, [0, 2, 1]] + n]), {"pieza": pieza})

    # ---------- reparto
    def cortar(self, isla=60, isla_pintura=260, rigidas=("llanta", "rin", "aro", "rayos", "_quitar")):
        if self.reglas[-1][2] is not None:
            raise RuntimeError("la ultima regla debe ser m.resto(...)")
        R = self.reglas
        nombres = [r[0] for r in R]
        V = np.column_stack([self.P, self.N, self.C] + [r[2] for r in R[:-1]])
        rec = malla.Recortador(V, self.I)
        for k in range(len(R) - 1):
            rec.cortar(9 + k, k)
        V, F, L = rec.resultado(len(R) - 1)
        rig = [k for k, n in enumerate(nombres) if n == "_quitar" or n.split(".")[-1].startswith(rigidas)]
        L = malla.quitar_islas(F, L, isla, rig)
        pint = [k for k, n in enumerate(nombres) if n.startswith("pintura")]
        if pint and isla_pintura:
            L = malla.quitar_islas(F, L, isla_pintura, [k for k in range(len(nombres)) if k not in pint])
        if "_quitar" in nombres:
            q = L == nombres.index("_quitar")
            F, L = F[~q], L[~q]
        partes = [{"nombre": n, "extras": e} for n, e, _ in R]
        if self.extra:
            np.savez(f"{self.T}/c_extra.npz", **{f"{n}|{k}": a for n, (p_, n_, c_, _) in self.extra.items() for k, a in (("pos", p_), ("nor", n_), ("idx", c_))})
            partes += [{"nombre": n, "extras": e} for n, (_, _, _, e) in self.extra.items()]
        elif os.path.exists(f"{self.T}/c_extra.npz"):
            os.remove(f"{self.T}/c_extra.npz")
        usados, inv = np.unique(F, return_inverse=True)
        F, V = inv.reshape(-1, 3), V[usados]
        nn = V[:, 3:6] / np.maximum(np.linalg.norm(V[:, 3:6], axis=1, keepdims=True), 1e-9)
        T = self.T
        V[:, :3].astype(np.float32).tofile(f"{T}/c_pos.bin")
        nn.astype(np.float32).tofile(f"{T}/c_nor.bin")
        V[:, 6:9].astype(np.float32).tofile(f"{T}/c_col.bin")
        F.astype(np.uint32).tofile(f"{T}/c_idx.bin")
        L.astype(np.int32).tofile(f"{T}/c_lab.bin")
        json.dump({"partes": partes, "medidas": self.medidas}, open(f"{T}/c_partes.json", "w"))
        self.V, self.F, self.L, self.nn, self.nombres = V, F, L, nn, nombres
        return V, F, L

    def resumen(self):
        cen = self.V[self.F][:, :, :3].mean(1)
        for k, n in enumerate(self.nombres):
            m = self.L == k
            if m.any():
                print(f"{n:32s} {m.sum():6d}  x[{cen[m, 0].min():.2f},{cen[m, 0].max():.2f}] y[{cen[m, 1].min():.2f},{cen[m, 1].max():.2f}] z[{cen[m, 2].min():.2f},{cen[m, 2].max():.2f}]")
            else:
                print(f"{n:32s}      0  (vacia)")
        print(f"cache: {self.aciertos} reutilizados, {self.fallos} calculados")

    MAT = {"pintura": (.9, .25, .2), "pintura2": (.95, .55, .5), "caucho": (.25, .25, .25), "rin": (.5, .3, .7), "metal": (.6, .9, .9),
           "dorado": (1, .85, .2), "ambar": (1, .55, 0), "oscuro": (.2, .45, .3), "plastico": (.35, .3, .28), "chasis": (.45, .45, .7),
           "espejo": (.3, 1, 1), "negro_brillo": (.1, .1, .5), "luz": (1, 1, .4), "stop": (1, 0, 0), "asiento": (.6, .4, .2), "titanio": (.5, .5, .35),
           "faro": (.2, .6, 1), "mica_dir": (.3, 1, .6), "reflector": (1, .55, 0), "_quitar": (1, 0, 1), "disco": (.6, .9, .9), "cromo": (.8, .8, .85),
           "motor": (.7, .6, .3), "resorte": (.9, .3, .9)}

    def ver(self, espec, salida, solo=None):
        """espec: "vista;px por metro;caja o None" separadas por +. Pinta cada pieza de un color (por material)."""
        rng = np.random.default_rng(7)
        pal = np.array([np.clip(np.array(self.MAT.get(n.split(".")[0], (.5, .5, .5))) + rng.uniform(-.1, .1, 3), 0, 1) for n in self.nombres])
        if solo:
            for k, n in enumerate(self.nombres):
                if not any(s in n for s in solo):
                    pal[k] = (.82, .82, .82)
        cen = self.V[self.F][:, :, :3].mean(1)
        Pv, Nv = self.V[:, :3].astype(np.float32), self.nn.astype(np.float32)
        ims = []
        for esp in espec.split("+"):
            v, esc, caja = esp.split(";")
            caja = eval(caja)
            sel = np.all((cen >= np.array(caja[0]) - 0.02) & (cen <= np.array(caja[1]) + 0.02), axis=1) if caja else np.ones(len(self.F), bool)
            ims.append(rend.vista(Pv, Nv, self.F[sel], pal[self.L[sel]], v, float(esc), caja))
        rend.lamina(ims, salida, cols=2)


class Internos:
    """Piezas internas (Rayos X) hechas con formas.py. La ficha llama a pon(...) y el ciclo guarda."""

    def __init__(self, T):
        import formas
        self.F = formas
        self.T = T
        self.medidas = json.load(open(f"{T}/c_partes.json"))["medidas"]
        self.piezas = []

    def pon(self, nombre, pieza, *fs, pliegue=38):
        self.piezas.append((nombre, pieza, self.F.con_normales(self.F.unir(*fs), pliegue)))

    def cil(self, r, largo, base, eje, n=12, canto=0.0):
        perfil = [(0, 0), (r - canto, 0), (r, canto), (r, largo - canto), (r - canto, largo), (0, largo)] if canto else [(0, 0), (r, 0), (r, largo), (0, largo)]
        return self.F.revolucion(perfil, base, eje, n)

    def guardar(self):
        datos, extras, tot = {}, {}, 0
        for nombre, pieza, (P, N, I) in self.piezas:
            datos[f"{nombre}|pos"], datos[f"{nombre}|nor"], datos[f"{nombre}|idx"] = P, N, I
            extras[nombre] = {"pieza": pieza, "interno": True}
            tot += len(I)
        np.savez(f"{self.T}/i_extra.npz", **datos)
        json.dump(extras, open(f"{self.T}/i_extras.json", "w"))
        return len(self.piezas), tot


class Reloj:
    """Cronometro por paso; cada vuelta se agrega a T/tiempos.jsonl (de ahi sale la tabla de tiempos de la moto)."""

    def __init__(self, T):
        self.T, self.t0, self.pasos = T, time.time(), {}

    def paso(self, nombre):
        ahora = time.time()
        self.pasos[nombre] = round(ahora - self.t0, 2)
        self.t0 = ahora

    def cerrar(self, **datos):
        with open(f"{self.T}/tiempos.jsonl", "a") as f:
            f.write(json.dumps({"hora": time.strftime("%H:%M:%S"), **self.pasos, **datos}) + "\n")
        n = sum(1 for _ in open(f"{self.T}/tiempos.jsonl"))
        print(f"vuelta {n}: " + "  ".join(f"{k} {v}s" for k, v in self.pasos.items()) + f"  total {sum(self.pasos.values()):.1f}s")
