# Ficha de la Yamaha MT-03 (321 cc, bicilindrica) para ciclo.py. Modelo de Tripo SIN textura (62 mil triangulos,
# a lo largo de z con el manubrio en +z: preparar.py T 1.38 90). Entre ejes 1,38 m (ficha Yamaha MT-03 B5W).
# Coordenadas: x adelante, y arriba, z hacia el escape (lado derecho de la moto).
# Pintura segun 5 fotos oficiales de Incolmotos Yamaha (gris 2025-2026 y azul): van del color de la moto el tanque con
# sus aletas, la mascara de la farola y el guardabarros delantero; asiento, colin, portaplaca y tapas en negro.
# Disco delantero (298 mm), disco trasero (220 mm) y escape del mismo lado (derecho, +z); corona a la izquierda.
import numpy as np

import formas
from motor import O, Y, banda

EJES = 1.38
MEZCLA = 0.6
# Zonas aprobadas para revisar.py --ficha (metros de la pagina): direccionales delanteras ARRIBA junto a la farola
SITIOS = {"direccional delantera": (0.25, 0.50, 0.85, 1.05)}
CONSERVAR = []   # regex de piezas que la limpieza automatica de sobrantes no debe quitar (ninguna por ahora)
ISLAS = {"isla": 24, "isla_pintura": 200, "rigidas": ("llanta", "rin", "_quitar", "direccional")}
ALISAR = {"pintura.tanque": 8, "asiento.asiento": 4, "pintura.farola": 3, "plastico.colin": 3}
SUAVE = 3


def cortar(m):
    x, y, z, az = m.x, m.y, m.z, m.az
    xd, yd, Rd, rd = m.rueda(0.696, 0.287, 0.287)
    xt, yt, Rt, rt = m.rueda(-0.689, 0.303, 0.302)
    m.medidas.update(eje_del=[xd, yd], eje_tras=[xt, yt], R_del=Rd, R_tras=Rt)
    print(f"ruedas del ({xd:.3f},{yd:.3f}) R={Rd:.3f}  tras ({xt:.3f},{yt:.3f}) R={Rt:.3f}  entre ejes {xd - xt:.3f}")

    def lado(pol, valido=None, ancho=0.01):
        d = m.poligono(x, y, pol)
        return m.pliegue(d, np.ones(len(x), bool) if valido is None else valido, ancho)

    # --- Ruedas de aleacion (rin 17, 110/70 y 140/70): llanta y rin colado (rayos y aro en una pieza, rin=True)
    m.regla("oscuro.mordaza_del", Y([banda(x, xd - 0.19, xd - 0.04), banda(y, yd - 0.02, yd + 0.17), banda(z, 0.056, 0.11), banda(rd, 0.09, 0.185)]), pieza="freno_del")
    # Disco de Tripo de los dos lados a _quitar (el del lado del escape quedaba como chasis oscuro encima del disco nuevo
    # y lo hacia ver negro; el del lado de la corona es una copia falsa)
    m.regla("_quitar", Y([rd - 0.075, 0.15 - rd, banda(az, 0.04, 0.066)]))
    m.disco("disco.disco_del", xd, yd, 0.052, 0.144, "freno_del", interior=0.62)  # 298 mm
    m.disco("disco.disco_tras", xt, yt, 0.062, 0.107, "freno_tras", interior=0.55)  # 220 mm
    m.regla("caucho.llanta_del", Y([rd - (Rd - 0.068), O([Rd + 0.006 - rd, Y([Rd + 0.025 - rd, 22 - np.degrees(np.arctan2(y - yd, x - xd))])]), 0.062 - az]), pieza="llanta_del", eje=[xd, yd])
    m.regla("caucho.llanta_tras", Y([rt - (Rt - 0.09), Rt + 0.02 - rt, 0.082 - az]), pieza="llanta_tras", eje=[xt, yt])
    m.regla("rin.rin_del", Y([Rd - 0.068 - rd, O([0.037 - az, Y([0.06 - rd, 0.05 - az])])]), pieza="llanta_del", rin=True, eje=[xd, yd])
    m.regla("rin.rin_tras", Y([Rt - 0.09 - rt, O([0.05 - az, Y([0.07 - rt, 0.06 - az])])]), pieza="llanta_tras", rin=True, eje=[xt, yt])
    m.regla("metal.corona", Y([0.125 - rt, banda(-z, 0.05, 0.09)]), pieza="cadena")

    # --- Guardabarros delantero (corto, pintado) y horquilla invertida
    ang = np.degrees(np.arctan2(y - yd, x - xd))
    df = m.recta(x, y, (xd, yd), (0.43, 1.0))
    # El de Tripo era una lamina mas angosta que la llanta (+-5 cm contra +-6,2) y suelta detras de la horquilla: de lado
    # parecia flotar. Se quita (sin tocar la horquilla, que pasa por la misma zona a |z| > 5,4 cm) y se pone uno propio
    # como en las fotos (Incolmotos lateral y 3/4): casco en U de +-7 cm que cubre la llanta de 32 a 135 grados con
    # 2,2 cm de holgura arriba, faldones a cada lado que bajan hasta la barra de la horquilla (alli va atornillado) y el
    # reflector ambar del faldon, delante de la barra.
    m.regla("_quitar", Y([rd - (Rd + 0.004), Rd + 0.075 - rd, banda(ang, 20, 170), O([0.054 - az, Y([0.075 - az, df - 0.04])])]))
    guardabarros(m, xd, yd)
    m.regla("oscuro.horquilla", Y([0.04 - df, banda(az, 0.05, 0.125), banda(y, yd - 0.03, 0.97)]), pieza="suspension_del")

    # --- Luces: mascara con proyector LED central abajo y dos ojos LED arriba; stop LED bajo la punta del colin y
    # direccionales traseras en tallo
    # (GLB de la ronda 2: mascara de x 0,40 a 0,63; proyector central abajo y dos ojos LED inclinados arriba)
    # Faro (revisado 19-nov con 3 fotos: Yamaha EU 2027 de frente, Incolmotos 3/4 y lateral): proyector LED compacto
    # en el centro bajo la V de la mascara, cuadro de esquinas redondas de ~7 x 5 cm, un poco mas ancho arriba, con
    # lente redondo. Tripo trae un bloque plano de 10 x 5,5 cm (x 0,60): la lente es solo el cuadro central y lo que
    # sobra del bloque queda como carcasa negra (no pintada).
    # (cuadro redondeado: superelipse de exponente 4, 7,6 cm de ancho arriba y 6,4 abajo, 5,1 de alto)
    t = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    cs, sn = np.cos(t), np.sin(t)
    ex_, ey_ = np.sign(cs) * np.abs(cs) ** 0.5, np.sign(sn) * np.abs(sn) ** 0.5
    FARO = [(float(u * (0.035 + 0.003 * v)), float(0.7755 + 0.0255 * v)) for u, v in zip(ex_, ey_)]
    m.regla("luz.faro", Y([m.poligono(z, y, FARO), x - 0.585]), lampara={"tipo": "faro"})
    m.regla("oscuro.faro_carcasa", Y([banda(z, -0.058, 0.058), banda(y, 0.738, 0.806), x - 0.56]))
    OJO = [(0.025, 0.88), (0.10, 0.905), (0.11, 0.95), (0.03, 0.925)]
    # Carcasa negra brillante alrededor de cada ojo (en las fotos el LED va hundido en un marco oscuro; con la moto
    # blanca el ojo pintado no se distinguia). "cono": False: halo al encender, pero el haz sale del faro.
    co = np.mean(OJO, 0)
    OJO_C = [(max(0.012, float(co[0] + (u - co[0]) * 1.45)), float(co[1] + (v - co[1]) * 1.6)) for u, v in OJO]
    for lado_z, letra in ((1, "a"), (-1, "b")):
        m.regla(f"luz.posicion_{letra}", Y([m.poligono(lado_z * z, y, OJO), x - 0.52]), lampara={"tipo": "faro", "cono": False})
    for lado_z, letra in ((1, "a"), (-1, "b")):
        m.regla(f"negro_brillo.ojo_carcasa_{letra}", Y([m.poligono(lado_z * z, y, OJO_C), x - 0.50]))
    # Direccionales delanteras (decision FINAL del usuario, 19-nov ultima hora): ARRIBA, a la altura del manubrio, a los
    # lados de la farola junto a la punta de las aletas. La malla trae el cuerpo solo a la DERECHA del piloto (+z): bloque
    # de x 0,33-0,40, y 0,92-0,96, z 0,13-0,235 (mapa de x maximo por celda; del lado -z no hay nada). Se corta y la
    # IZQUIERDA es su copia espejada en z = 0. Las de abajo junto a la horquilla NO van (vuelven a la tapa del radiador).
    # Como en la foto de frente (Yamaha EU 2027): tallo fino negro que sale de la mascara y lente en la punta de afuera.
    caja_dir = Y([banda(x, 0.325, 0.405), banda(y, 0.915, 0.963)])
    # (solo el lente, de x 0,36 en adelante: detras pasa el cable del manubrio, que con la caja entera salia ambar y
    # espejado al otro lado; el cable queda oscuro con el tallo)
    m.regla("ambar.direccional_del_a", Y([caja_dir, banda(z, 0.188, 0.242), x - 0.36]), lampara={"tipo": "direccional"})
    m.regla("oscuro.direccional_del_tallo_a", Y([caja_dir, banda(z, 0.125, 0.242)]))
    m.espejar("ambar.direccional_del_a", "ambar.direccional_del_b")
    m.espejar("oscuro.direccional_del_tallo_a", "oscuro.direccional_del_tallo_b")
    # Stop LED: cuna roja en lo alto de la punta del colin, mirando hacia atras (foto trasera 360 de Yamaha USA y 3/4 de
    # Incolmotos). Solo la cara casi vertical (y 0,903-0,945, normal atras): debajo, de y 0,86 a 0,90, la punta tiene una
    # cara inclinada hacia abajo que es colin; con ella la normal de la lampara apuntaba 38 grados al piso y la luz roja
    # y el halo caian sobre el portaplaca. La placa y su luz van en el portaplaca, debajo de las direccionales.
    STOP = [(-0.034, 0.903), (0.034, 0.903), (0.068, 0.946), (-0.068, 0.946)]   # trapecio en (z, y), ancho arriba
    m.regla("stop.stop", Y([m.poligono(z, y, STOP), -0.87 - x, -0.4 - m.nx, 0.7 - np.abs(m.ny)]), lampara={"tipo": "stop"})
    tras = Y([banda(x, -1.01, -0.90), banda(y, 0.72, 0.77), az - 0.15])
    m.regla("ambar.direccional_tras_a", Y([tras, z]), lampara={"tipo": "direccional"})
    m.regla("ambar.direccional_tras_b", Y([tras, -z]), lampara={"tipo": "direccional"})
    m.regla("oscuro.direccional_tallos", Y([banda(x, -1.01, -0.86), banda(y, 0.715, 0.775), az - 0.07]))

    # --- Manubrio, espejos, tablero y farola
    arriba = Y([y - 0.975, 0.52 - x, x - 0.18])
    m.regla("espejo.luna", Y([y - 1.15, az - 0.24, -0.3 - m.nx]), padre="espejos.fabrica")
    m.regla("oscuro.espejos", Y([y - 1.07, az - 0.2]), padre="espejos.fabrica")
    m.regla("caucho.punos", Y([arriba, az - 0.33]))
    # Tablero: pantalla LCD de ~11 x 5,5 cm sobre la cara inclinada de la caja negra tras la mascara (medida en la
    # malla: x 0,42-0,47, y 0,93-0,99, normal (-0,73, 0,68)); enciende con «Encender» como en las otras motos
    nt = np.array([-0.733, 0.681, 0.0])
    tablero = [{"c": [round(float(v), 4) for v in np.array([0.447, 0.971, 0.0]) + nt * 0.006], "n": [round(float(v), 4) for v in nt],
                "tam": [0.11, 0.055], "dibujo": "tacometro"}]
    m.regla("oscuro.manubrio", arriba, manubrio={"x": 0.3, "y": 1.01, "extremo": 0.44}, pantalla=tablero,
            sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"])
    m.regla("pintura.farola", Y([x - 0.49, banda(y, 0.76, 1.05), 0.115 - az]), rol="visor_fijo")

    # --- Tanque con aletas (pintado), asiento, colin y portaplaca
    TANQUE = [(-0.16, 0.80), (-0.05, 0.93), (0.10, 0.995), (0.28, 0.965), (0.38, 0.93), (0.47, 0.76), (0.46, 0.64),
              (0.22, 0.635), (0.05, 0.71), (-0.16, 0.76)]
    m.regla("asiento.asiento", Y([banda(x, -0.745, -0.12), 0.14 - az, m.ny - 0.5, y - 0.76]))
    # (sin la zona de la pipa de la direccion, x > 0,30 y |z| < 0,13: alli pasan cables y mangueras que se pintaban)
    m.regla("pintura.tanque", Y([lado(TANQUE, az < 0.25), 0.25 - az, O([0.30 - x, az - 0.13])]), zonas=["tanque"])
    # Tapa del radiador (debajo de la aleta pintada, punta junto a la horquilla): plastico negro en todas las fotos
    m.regla("plastico.tapa_radiador", Y([x - 0.38, banda(y, 0.56, 0.66), banda(az, 0.125, 0.25)]))
    m.regla("plastico.colin", Y([banda(x, -0.95, -0.30), banda(y, 0.66, 0.95), 0.17 - az]), zonas=["lateral"])
    placa = {"c": [-1.046, 0.63, 0], "incl": -0.1, "tam": [0.17, 0.09]}   # (cara plana del portaplaca, y 0,56-0,70)
    m.regla("plastico.portaplaca", Y([-0.78 - x, 0.86 - y, y - 0.40, 0.11 - az]), placa=placa,
            acomodar=[{"grupo": "accesorios.baul", "ref": "abajo", "a": [-0.82, 0.95, 0]}])

    # --- Mecanica a la vista
    ESCAPE = [(-0.86, 0.33), (-0.84, 0.45), (-0.45, 0.43), (-0.05, 0.27), (0.20, 0.25), (0.20, 0.14), (-0.10, 0.14), (-0.86, 0.25)]
    m.regla("oscuro.escape", Y([m.poligono(x, y, ESCAPE), z - 0.045]), padre="escapeFabrica")
    db = m.recta(x, y, (-0.20, 0.43), (xt, yt))
    m.regla("oscuro.basculante", Y([0.045 - db, banda(x, xt - 0.03, -0.18), banda(az, 0.03, 0.12)]), pieza="suspension_tras")
    MOTOR = [(-0.25, 0.22), (-0.25, 0.55), (-0.05, 0.63), (0.25, 0.63), (0.33, 0.45), (0.27, 0.18), (-0.15, 0.17)]
    m.regla("motor.bloque", Y([m.poligono(x, y, MOTOR), 0.17 - az]), pieza="motor")
    m.resto("chasis.chasis")


def _lamina(G1, G0):
    """Solido delgado entre dos rejillas (na, nb, 3) de la misma forma: caras de las dos, cantos y orientacion hacia afuera."""
    na, nb = G1.shape[:2]
    n = na * nb
    k = lambda i, j: i * nb + j
    I = []
    for i in range(na - 1):
        for j in range(nb - 1):
            a, b, c, d = k(i, j), k(i + 1, j), k(i + 1, j + 1), k(i, j + 1)
            I += [(a, b, c), (a, c, d), (n + a, n + c, n + b), (n + a, n + d, n + c)]
    for i in range(na - 1):
        a, b = k(i, 0), k(i + 1, 0)
        I += [(n + a, n + b, b), (n + a, b, a)]
        a, b = k(i, nb - 1), k(i + 1, nb - 1)
        I += [(n + a, b, n + b), (n + a, a, b)]
    for j in range(nb - 1):
        a, b = k(0, j), k(0, j + 1)
        I += [(n + a, a, b), (n + a, b, n + b)]
        a, b = k(na - 1, j), k(na - 1, j + 1)
        I += [(n + a, b, a), (n + a, n + b, b)]
    P, I = np.concatenate([G1.reshape(-1, 3), G0.reshape(-1, 3)]), np.array(I)
    if np.einsum("ij,ij->i", P[I[:, 0]], np.cross(P[I[:, 1]], P[I[:, 2]])).sum() < 0:
        I = I[:, [0, 2, 1]]
    return P, I


def _espejo_z(forma):
    P, I = forma
    return P * [1, 1, -1], I[:, [0, 2, 1]]


def guardabarros(m, xd, yd, R0=0.312, W=0.070, caida=0.024, grueso=0.003):
    """Guardabarros delantero propio (pintado) con faldones hasta la horquilla y reflectores ambar."""
    th = np.radians(np.linspace(32, 135, 40))
    u = np.linspace(-1, 1, 15)
    r = R0 - caida * np.abs(u) ** 2.5
    # (la punta delantera y la de atras bajan 6 mm, como el labio del guardabarros real)
    r = r[None, :] - 0.006 * np.clip(1 - (np.degrees(th)[:, None] - 32) / 12, 0, 1)
    def casco(dr):
        rr = r + dr
        return np.stack([xd + rr * np.cos(th)[:, None], yd + rr * np.sin(th)[:, None], np.broadcast_to(u * W, rr.shape)], -1)
    formas_ = [_lamina(casco(grueso / 2), casco(-grueso / 2))]
    # Faldon: de 76 a 128 grados, del borde del casco hacia abajo hasta r 0,215 junto a la barra (cruza la barra: atornillado)
    tf = np.radians(np.linspace(76, 128, 16))
    s_ = np.linspace(0, 1, 6)
    r_lo = 0.215 + 0.075 * np.clip((100 - np.degrees(tf)) / 24, 0, 1)
    r_hi = R0 - caida - 0.004
    rr = r_lo[:, None] + (r_hi - r_lo[:, None]) * s_[None, :]
    zc = W - 0.0035
    def faldon(zz):
        return np.stack([xd + rr * np.cos(tf)[:, None], yd + rr * np.sin(tf)[:, None], np.full(rr.shape, zz)], -1)
    f = _lamina(faldon(zc - grueso / 2), faldon(zc + grueso / 2))
    formas_ += [f, _espejo_z(f)]
    P, N, I = formas.con_normales(formas.unir(*formas_), 50)
    m.extra["pintura.guardabarros_del"] = (P, N, I, {"zonas": ["guardabarros"]})
    # Reflector ambar redondo en la cara de afuera de cada faldon, delante de la barra de la horquilla
    a = np.radians(93)
    t = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    cx, cy = xd + 0.258 * np.cos(a), yd + 0.258 * np.sin(a)
    ref = formas.extrusion(np.column_stack([cx + 0.011 * np.cos(t), cy + 0.011 * np.sin(t)]), zc + grueso / 2 - 0.0005, zc + grueso / 2 + 0.0025, 0.0008)
    for nombre, forma in (("reflector.reflector_del_a", ref), ("reflector.reflector_del_b", _espejo_z(ref))):
        P, N, I = formas.con_normales(forma, 50)
        m.extra[nombre] = (P, N, I, {})


def internos(k):
    """Rayos X: bicilindrico en linea de agua (ciguenal, dos pistones, bloque), dos bujias, aceite, bateria y filtro.
    Antes de espejar: +z es el lado del escape."""
    F, pon, cil = k.F, k.pon, k.cil
    C = np.array([0.02, 0.33, 0.0])
    dc = np.array([0.42, 0.91, 0.0])
    dc /= np.linalg.norm(dc)
    cig = [(0, -0.09), (0.011, -0.09), (0.011, -0.06), (0.042, -0.06), (0.042, -0.045), (0.013, -0.045), (0.013, -0.024),
           (0.042, -0.024), (0.042, -0.009), (0.013, -0.009), (0.013, 0.009), (0.042, 0.009), (0.042, 0.024), (0.013, 0.024),
           (0.013, 0.045), (0.042, 0.045), (0.042, 0.06), (0.011, 0.06), (0.011, 0.09), (0, 0.09)]
    pon("metal.motor_ciguenal", "motor", F.revolucion(cig, C, (0, 0, 1), 20),
        *[F.tubo([C + [0, 0, s * 0.034] + dc * 0.03, C + [0, 0, s * 0.034] + dc * 0.14], 0.0075, 8) for s in (-1, 1)])
    for s, l in ((-1, "a"), (1, "b")):
        Ci = C + np.array([0, 0, s * 0.034])
        pon(f"motor.motor_cilindro_{l}", "motor", F.revolucion([(0.034, 0.08), (0.042, 0.08), (0.042, 0.215), (0.044, 0.25), (0.03, 0.262), (0, 0.262)], Ci, dc, 20))
        pon(f"cromo.motor_piston_{l}", "motor", F.revolucion([(0, 0.14), (0.034, 0.14), (0.034, 0.146), (0.032, 0.148), (0.034, 0.15), (0.034, 0.18), (0, 0.182)], Ci, dc, 20))
        bb = Ci + dc * 0.262
        pon(f"metal.bujia_rosca_{l}", "bujia", F.revolucion([(0, -0.02), (0.005, -0.02), (0.005, 0.01), (0.0085, 0.01), (0.0085, 0.018), (0.005, 0.018)], bb, dc, 8))
        pon(f"bujia.bujia_aislador_{l}", "bujia", F.revolucion([(0.005, 0.018), (0.0065, 0.02), (0.0065, 0.05), (0, 0.052)], bb, dc, 10))
        pon(f"oscuro.bujia_capuchon_{l}", "bujia", F.revolucion([(0, 0.03), (0.011, 0.03), (0.011, 0.08), (0, 0.085)], bb, dc, 10))
    carter = F.suave([(-0.18, -0.03), (-0.16, -0.12), (-0.06, -0.15), (0.08, -0.14), (0.13, -0.08), (0.13, -0.02), (0.08, 0.03), (-0.14, 0.03)], 2)
    pon("carter.aceite_carter", "aceite", F.mover(F.extrusion(carter, -0.10, 0.10, 0.014), C))
    nivel = F.suave([(-0.15, -0.075), (-0.145, -0.11), (-0.06, -0.135), (0.07, -0.128), (0.11, -0.09), (0.115, -0.075)], 1)
    pon("aceiteVisible.aceite_nivel", "aceite", F.mover(F.extrusion(nivel, -0.085, 0.085, 0.004), C))
    pon("metal.aceite_tapon", "aceite", F.revolucion([(0, 0), (0.011, 0), (0.011, 0.008), (0.0075, 0.008), (0.0075, 0.016), (0, 0.016)], C + [-0.04, -0.148, 0], (0, -1, 0), 6))
    # Bateria bajo el asiento del piloto; caja del filtro bajo el tanque
    B = np.array([-0.30, 0.70, 0.0])
    pon("bateria.bat_cuerpo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.13, 0.09, 0.006), -0.04, 0.04, 0.004), B))
    pon("oscuro.bat_tapa", "bateria", F.mover(F.extrusion(F.rect_redondo(0.134, 0.014, 0.004), -0.042, 0.042, 0.003), B + [0, 0.05, 0]))
    pon("metal.bat_bornes", "bateria", *[cil(0.007, 0.012, B + [xx, 0.056, 0.015], (0, 1, 0), 10, 0.002) for xx in (-0.048, 0.048)])
    caja = F.suave([(-0.10, 0.66), (-0.06, 0.63), (0.12, 0.63), (0.16, 0.66), (0.16, 0.76), (0.12, 0.79), (-0.06, 0.79), (-0.10, 0.76)], 2)
    pon("oscuro.filtro_caja", "filtro_aire", F.extrusion(caja, -0.09, 0.09, 0.012))
