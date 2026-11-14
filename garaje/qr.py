"""Código QR en SVG sin librerías (modo byte, corrección M, versiones 1 a 10: hasta 213 bytes).

Sigue la norma ISO/IEC 18004. Alcanza para los enlaces de TallerYa (hoja de vida, código de servicio).
"""
# Versión: (códigos de corrección por bloque, [(cantidad de bloques, datos por bloque), ...]) para el nivel M.
_NIVEL_M = {
    1: (10, [(1, 16)]), 2: (16, [(1, 28)]), 3: (26, [(1, 44)]), 4: (18, [(2, 32)]), 5: (24, [(2, 43)]),
    6: (16, [(4, 27)]), 7: (18, [(4, 31)]), 8: (22, [(2, 38), (2, 39)]), 9: (22, [(3, 36), (2, 37)]),
    10: (26, [(4, 43), (1, 44)]),
}
_ALINEACION = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34], 7: [6, 22, 38],
               8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}
_BITS_NIVEL_M = 0  # en la información de formato: L=1, M=0, Q=3, H=2

# Aritmética en GF(256) con el polinomio 0x11D
_EXP, _LOG = [0] * 512, [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i], _LOG[_x] = _x, _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _mul(a, b):
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]


def _divisor(grado):
    res = [0] * (grado - 1) + [1]
    raiz = 1
    for _ in range(grado):
        for j in range(grado):
            res[j] = _mul(res[j], raiz)
            if j + 1 < grado:
                res[j] ^= res[j + 1]
        raiz = _mul(raiz, 2)
    return res


def _resto(datos, divisor):
    res = [0] * len(divisor)
    for b in datos:
        factor = b ^ res.pop(0)
        res.append(0)
        for i, coef in enumerate(divisor):
            res[i] ^= _mul(coef, factor)
    return res


def _codewords(datos):
    """Elige la versión, arma los bits y entrega los códigos ya intercalados con su corrección."""
    for version, (ec, grupos) in _NIVEL_M.items():
        capacidad = sum(n * d for n, d in grupos)
        bits_cuenta = 8 if version < 10 else 16
        if 4 + bits_cuenta + 8 * len(datos) <= capacidad * 8:
            break
    else:
        raise ValueError("Texto demasiado largo para el QR (máximo 213 bytes).")
    bits = [0, 1, 0, 0] + [(len(datos) >> i) & 1 for i in range(bits_cuenta - 1, -1, -1)]
    for b in datos:
        bits += [(b >> i) & 1 for i in range(7, -1, -1)]
    bits += [0] * min(4, capacidad * 8 - len(bits))
    bits += [0] * (-len(bits) % 8)
    cw = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    relleno = 0
    while len(cw) < capacidad:
        cw.append((0xEC, 0x11)[relleno % 2])
        relleno += 1
    bloques, pos, div = [], 0, _divisor(ec)
    for n, d in grupos:
        for _ in range(n):
            bloque = cw[pos:pos + d]
            pos += d
            bloques.append((bloque, _resto(bloque, div)))
    salida = []
    for i in range(max(len(b) for b, _ in bloques)):
        salida += [b[i] for b, _ in bloques if i < len(b)]
    for i in range(ec):
        salida += [e[i] for _, e in bloques]
    return version, salida


_MASCARAS = [
    lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0, lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: x * y % 2 + x * y % 3 == 0, lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
]


class _Matriz:
    def __init__(self, version):
        self.version = version
        self.n = n = version * 4 + 17
        self.m = [[False] * n for _ in range(n)]
        self.fijo = [[False] * n for _ in range(n)]
        for i in range(n):
            self.poner(6, i, i % 2 == 0)
            self.poner(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < n and 0 <= y < n:
                        self.poner(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        pos = _ALINEACION[version]
        ult = len(pos) - 1
        for i, ax in enumerate(pos):
            for j, ay in enumerate(pos):
                if (i, j) in ((0, 0), (0, ult), (ult, 0)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.poner(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)
        self.formato(0)
        if version >= 7:
            resto = version
            for _ in range(12):
                resto = (resto << 1) ^ ((resto >> 11) * 0x1F25)
            bits = version << 12 | resto
            for i in range(18):
                bit = (bits >> i) & 1 == 1
                a, b = n - 11 + i % 3, i // 3
                self.poner(a, b, bit)
                self.poner(b, a, bit)

    def poner(self, x, y, oscuro):
        self.m[y][x] = oscuro
        self.fijo[y][x] = True

    def formato(self, mascara):
        datos = _BITS_NIVEL_M << 3 | mascara
        resto = datos
        for _ in range(10):
            resto = (resto << 1) ^ ((resto >> 9) * 0x537)
        bits = (datos << 10 | resto) ^ 0x5412
        bit = lambda i: (bits >> i) & 1 == 1  # noqa: E731
        n = self.n
        for i in range(6):
            self.poner(8, i, bit(i))
        self.poner(8, 7, bit(6))
        self.poner(8, 8, bit(7))
        self.poner(7, 8, bit(8))
        for i in range(9, 15):
            self.poner(14 - i, 8, bit(i))
        for i in range(8):
            self.poner(n - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.poner(8, n - 15 + i, bit(i))
        self.poner(8, n - 8, True)

    def colocar(self, cw):
        n, i, derecha = self.n, 0, self.n - 1
        while derecha >= 1:
            if derecha == 6:
                derecha = 5
            for vert in range(n):
                for j in range(2):
                    x = derecha - j
                    y = n - 1 - vert if ((derecha + 1) & 2) == 0 else vert
                    if not self.fijo[y][x] and i < len(cw) * 8:
                        self.m[y][x] = (cw[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            derecha -= 2

    def enmascarar(self, mascara):
        f = _MASCARAS[mascara]
        for y in range(self.n):
            for x in range(self.n):
                if not self.fijo[y][x] and f(x, y):
                    self.m[y][x] = not self.m[y][x]

    def castigo(self):
        n, m, total = self.n, self.m, 0
        lineas = [m[y] for y in range(n)] + [[m[y][x] for y in range(n)] for x in range(n)]
        patron_a, patron_b = "00001011101", "10111010000"
        for linea in lineas:
            corrida, previo = 0, None
            for v in linea:
                corrida = corrida + 1 if v == previo else 1
                previo = v
                if corrida == 5:
                    total += 3
                elif corrida > 5:
                    total += 1
            texto = "".join("1" if v else "0" for v in linea)
            total += 40 * (texto.count(patron_a) + texto.count(patron_b))
        for y in range(n - 1):
            for x in range(n - 1):
                if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                    total += 3
        oscuros = sum(sum(fila) for fila in m)
        total += 10 * (abs(oscuros * 20 - n * n * 10) // (n * n))
        return total


def matriz(texto):
    """Matriz de módulos (lista de filas con True = oscuro) para el texto dado."""
    version, cw = _codewords(texto.encode("utf-8"))
    mejor = None
    for mascara in range(8):
        qr = _Matriz(version)
        qr.colocar(cw)
        qr.enmascarar(mascara)
        qr.formato(mascara)
        puntos = qr.castigo()
        if mejor is None or puntos < mejor[0]:
            mejor = (puntos, qr.m)
    return mejor[1]


def svg(texto, titulo="Código QR"):
    """SVG del QR con margen de 4 módulos; se escala con CSS (ancho al 100 %)."""
    m = matriz(texto)
    n = len(m) + 8
    trazos = "".join(f"M{x + 4} {y + 4}h1v1h-1z" for y, fila in enumerate(m) for x, v in enumerate(fila) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" role="img" aria-label="{titulo}" '
            f'shape-rendering="crispEdges"><rect width="{n}" height="{n}" fill="#fff"/>'
            f'<path d="{trazos}" fill="#000"/></svg>')
