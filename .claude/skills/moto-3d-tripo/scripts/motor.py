# Motor generico del corte (no sabe nada de ninguna moto): carga la malla preparada, ofrece las herramientas para
# armar campos (regiones, plantillas, pliegues, color si lo hay), reparte en piezas y guarda. Las reglas de cada moto
# viven en su ficha (fichas/<moto>.py), que recibe un objeto Corte. Lo lento (suavizados, pliegues, componentes) se
# guarda en T/cache con la huella de sus datos: una vuelta que solo cambia una regla no recalcula lo demas.
# Coordenadas de la moto: x adelante, y arriba, z hacia el lado del escape (se espeja al exportar).
import hashlib
import json
import os
import re
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
        self.reglas, self.extra, self.medidas, self.espejos = [], {}, {}, []
        self.deformaciones = []   # funciones P -> P aplicadas tras cortar (p. ej. agrandar un rin alrededor de su eje)
        self.desplazamientos = []   # (pieza, funcion P -> P) que mueven solo esa pieza (ver desplazar)
        self.conservar = []   # regex de piezas que sobrantes() no toca (CONSERVAR de la ficha)
        self.limpiar = True   # SOBRANTES = False en la ficha lo apaga
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

    def espejar(self, origen, nuevo, despegar=0.0015, **extras):
        """Pieza par que falta de un lado (Tripo dejo solo una direccional, espejo o reposapies): tras repartir, copia las
        caras de la regla `origen` reflejadas en z = 0 como pieza nueva `nuevo` (mismos extras salvo los que se pasen),
        despegada `despegar` m por su normal para que no pelee con la superficie que haya debajo."""
        self.espejos.append((origen, nuevo, despegar, extras))

    def desplazar(self, nombre, fn):
        """Mueve solo las caras de la regla `nombre` tras repartir (p. ej. despegar un guardabarros que Tripo pego a la
        llanta). Los vertices que comparte con otras piezas se duplican: las vecinas no se estiran."""
        self.desplazamientos.append((nombre, fn))

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
    def cortar(self, isla=60, isla_pintura=260, rigidas=("llanta", "rin", "aro", "rayos", "_quitar", "direccional")):
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
        q = np.isin(L, [k for k, n in enumerate(nombres) if n == "_quitar"])   # todas, no solo la primera
        if self.limpiar:
            q |= self.sobrantes(V, F, L, R)
        F, L = F[~q], L[~q]
        partes = [{"nombre": n, "extras": e} for n, e, _ in R]
        for origen, nuevo, despegar, ex in self.espejos:
            k = nombres.index(origen)
            Fo = F[L == k]
            if not len(Fo):
                raise RuntimeError(f"espejar: la regla {origen} quedo vacia")
            u, inv = np.unique(Fo, return_inverse=True)
            pos, nor = V[u, :3].copy(), V[u, 3:6].copy()
            nor /= np.maximum(np.linalg.norm(nor, axis=1, keepdims=True), 1e-9)
            pos += nor * despegar
            pos[:, 2] *= -1
            nor[:, 2] *= -1
            self.extra[nuevo] = (pos, nor, inv.reshape(-1, 3)[:, [0, 2, 1]], {**R[k][1], **ex})
            print(f"espejada {origen} -> {nuevo} ({len(Fo)} caras)")
        if self.extra:
            np.savez(f"{self.T}/c_extra.npz", **{f"{n}|{k}": a for n, (p_, n_, c_, _) in self.extra.items() for k, a in (("pos", p_), ("nor", n_), ("idx", c_))})
            partes += [{"nombre": n, "extras": e} for n, (_, _, _, e) in self.extra.items()]
        elif os.path.exists(f"{self.T}/c_extra.npz"):
            os.remove(f"{self.T}/c_extra.npz")
        for nombre, fn in self.desplazamientos:
            sel = L == nombres.index(nombre)
            comun = np.intersect1d(np.unique(F[sel]), np.unique(F[~sel]))
            mapa = np.arange(len(V) + len(comun))
            mapa[comun] = np.arange(len(V), len(V) + len(comun))
            V = np.vstack([V, V[comun]])
            F = F.copy()
            F[sel] = mapa[F[sel]]
            u = np.unique(F[sel])
            V[u, :3] = fn(V[u, :3].copy())
            print(f"desplazada {nombre} ({sel.sum()} caras)")
        usados, inv = np.unique(F, return_inverse=True)
        F, V = inv.reshape(-1, 3), V[usados]
        for fn in self.deformaciones:
            V[:, :3] = fn(V[:, :3].copy())
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

    # Piezas que nunca se quitan solas: luces, direccionales, tornilleria, placa y espejos (chicas y a veces sueltas)
    NO_QUITAR = r"direccional|luz\.|stop|ambar|tornill|perno|placa|espejo|lente|reflector"
    UN_LADO = r"escape|silenciador|mofle|corona|cadena|pinon|cvt"

    def sobrantes(self, V, F, L, R, cajamax=0.08, carasmax=400, lejos=0.015):
        """Sobrantes de Tripo que se quitan solos al construir (pedido del usuario, 19-nov). Devuelve la mascara de caras
        y deja la lista en T/quitados.json para la hoja de revisar.py:
        - isla suelta: componente conectado chico (caja < 8 cm y < 400 caras) a mas de 1,5 cm de todo lo demas;
        - copia del otro lado: en piezas de un solo lado, los pedazos sueltos de esa pieza en el lado contrario al suyo
          (escape a +z; corona, cadena, pinon y CVT a -z): Tripo hace la moto simetrica (segundo escape de la XTZ).
        Nunca toca NO_QUITAR ni lo que case con CONSERVAR (regex sobre el nombre) de la ficha."""
        nombres = [r[0] for r in R]
        prot = [k for k, n in enumerate(nombres) if n == "_quitar" or re.search(self.NO_QUITAR, n) or "lampara" in R[k][1]
                or any(re.search(c, n) for c in self.conservar)]
        P = V[:, :3]
        _, w = np.unique(np.round(P / 2e-4).astype(np.int64), axis=0, return_inverse=True)
        w = w.ravel()
        cf = comp.componentes(w.max() + 1, w[F])
        ids, inv, cnt = np.unique(cf, return_inverse=True, return_counts=True)
        q = np.zeros(len(F), bool)
        lista = []
        cen = P[F].mean(1)
        # rejilla de 1,5 cm con el componente de cada vertice para medir "lejos de todo"
        vc = np.full(len(P), -1)
        vc[F.ravel()] = np.repeat(inv, 3)
        celda = np.floor(P / lejos).astype(np.int64)
        clave = (celda[:, 0] * 73856093) ^ (celda[:, 1] * 19349663) ^ (celda[:, 2] * 83492791)
        orden = np.argsort(clave)
        ck, cc = clave[orden], vc[orden]

        def vecinos(c):
            u = np.unique(F[inv == c])
            cel = celda[u]
            otros = set()
            for d in np.array(np.meshgrid([-1, 0, 1], [-1, 0, 1], [-1, 0, 1])).T.reshape(-1, 3):
                cl = ((cel[:, 0] + d[0]) * 73856093) ^ ((cel[:, 1] + d[1]) * 19349663) ^ ((cel[:, 2] + d[2]) * 83492791)
                a, b = np.searchsorted(ck, cl), np.searchsorted(ck, cl, "right")
                for i, j in zip(a, b):
                    if j > i:
                        otros.update(cc[i:j].tolist())
                        if len(otros - {c, -1}):
                            return True
            return False

        for c in np.where(cnt < carasmax)[0]:
            m = inv == c
            labs = np.unique(L[m])
            if np.isin(labs, prot).any():
                continue
            Q = cen[m]
            if np.linalg.norm(Q.max(0) - Q.min(0)) > cajamax or vecinos(c):
                continue
            q |= m
            lista.append({"motivo": "isla suelta", "pieza": nombres[np.bincount(L[m]).argmax()], "caras": int(m.sum()),
                          "centro": [round(float(v), 3) for v in Q.mean(0)]})
        for k, n in enumerate(nombres):
            if k in prot or not re.search(self.UN_LADO, n.split(".")[-1]):
                continue
            mk = (L == k) & ~q
            if not mk.any():
                continue
            idx = np.where(mk)[0]   # componentes de esta pieza sola (la malla de Tripo viene fundida en una)
            cl = np.zeros(len(F), np.int64) - 1
            cl[idx] = comp.componentes(w.max() + 1, w[F[idx]])
            cs = np.unique(cl[idx])
            lado = 1 if re.search(r"escape|silenciador|mofle", n) else -1   # fichas: +z = escape; corona, cadena y CVT a -z
            for c in cs:
                m = cl == c
                zc = cen[m, 2].mean()
                if np.sign(zc) != lado and abs(zc) > 0.07:
                    q |= m
                    lista.append({"motivo": "copia del otro lado", "pieza": n, "caras": int(m.sum()),
                                  "centro": [round(float(v), 3) for v in cen[m].mean(0)]})
        json.dump(lista, open(f"{self.T}/quitados.json", "w"), ensure_ascii=False, indent=0)
        for e in lista:
            print(f"quitado solo: {e['motivo']} de {e['pieza']} ({e['caras']} caras) en {e['centro']}")
        return q

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
