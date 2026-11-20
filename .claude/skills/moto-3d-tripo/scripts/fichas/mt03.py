# Ficha de la Yamaha MT-03 (321 cc, bicilindrica) para ciclo.py. Modelo de Tripo SIN textura (62 mil triangulos,
# a lo largo de z con el manubrio en +z: preparar.py T 1.38 90). Entre ejes 1,38 m (ficha Yamaha MT-03 B5W).
# Coordenadas: x adelante, y arriba, z hacia el escape (lado derecho de la moto).
# Pintura segun 5 fotos oficiales de Incolmotos Yamaha (gris 2025-2026 y azul): van del color de la moto el tanque con
# sus aletas, la mascara de la farola y el guardabarros delantero; asiento, colin, portaplaca y tapas en negro.
# Disco delantero (298 mm), disco trasero (220 mm) y escape del mismo lado (derecho, +z); corona a la izquierda.
import numpy as np

from motor import O, Y, banda

EJES = 1.38
MEZCLA = 0.6
ISLAS = {"isla": 24, "isla_pintura": 200, "rigidas": ("llanta", "rin", "_quitar")}
ALISAR = {"pintura.tanque": 8, "pintura.guardabarros_del": 4, "asiento.asiento": 4, "pintura.farola": 3, "plastico.colin": 3}
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
    m.regla("_quitar", Y([rd - 0.075, 0.15 - rd, banda(-z, 0.045, 0.064)]))     # copia del disco del lado de la corona
    m.disco("disco.disco_del", xd, yd, 0.052, 0.144, "freno_del", interior=0.62)  # 298 mm
    m.disco("disco.disco_tras", xt, yt, 0.062, 0.107, "freno_tras", interior=0.55)  # 220 mm
    m.regla("caucho.llanta_del", Y([rd - (Rd - 0.068), O([Rd + 0.006 - rd, Y([Rd + 0.025 - rd, 22 - np.degrees(np.arctan2(y - yd, x - xd))])]), 0.062 - az]), pieza="llanta_del", eje=[xd, yd])
    m.regla("caucho.llanta_tras", Y([rt - (Rt - 0.09), Rt + 0.02 - rt, 0.082 - az]), pieza="llanta_tras", eje=[xt, yt])
    m.regla("rin.rin_del", Y([Rd - 0.068 - rd, O([0.037 - az, Y([0.06 - rd, 0.05 - az])])]), pieza="llanta_del", rin=True, eje=[xd, yd])
    m.regla("rin.rin_tras", Y([Rt - 0.09 - rt, O([0.05 - az, Y([0.07 - rt, 0.06 - az])])]), pieza="llanta_tras", rin=True, eje=[xt, yt])
    m.regla("oscuro.mordaza_del", Y([banda(x, xd - 0.19, xd - 0.04), banda(y, yd - 0.02, yd + 0.17), banda(z, 0.056, 0.11), banda(rd, 0.09, 0.185)]), pieza="freno_del")
    m.regla("metal.corona", Y([0.125 - rt, banda(-z, 0.05, 0.09)]), pieza="cadena")

    # --- Guardabarros delantero (corto, pintado) y horquilla invertida
    ang = np.degrees(np.arctan2(y - yd, x - xd))
    df = m.recta(x, y, (xd, yd), (0.43, 1.0))
    m.regla("pintura.guardabarros_del", Y([rd - (Rd + 0.004), Rd + 0.075 - rd, 0.075 - az, banda(ang, 20, 170)]), zonas=["guardabarros"])
    m.regla("oscuro.horquilla", Y([0.04 - df, banda(az, 0.05, 0.125), banda(y, yd - 0.03, 0.97)]), pieza="suspension_del")

    # --- Luces: mascara con proyector LED central abajo y dos ojos LED arriba; stop LED bajo la punta del colin y
    # direccionales traseras en tallo
    # (GLB de la ronda 2: mascara de x 0,40 a 0,63; proyector central abajo y dos ojos LED inclinados arriba)
    FARO = [(-0.06, 0.755), (0.06, 0.755), (0.065, 0.80), (0.05, 0.825), (-0.05, 0.825), (-0.065, 0.80)]
    m.regla("luz.faro", Y([m.poligono(z, y, FARO), x - 0.54]), lampara={"tipo": "faro"})
    OJO = [(0.025, 0.88), (0.10, 0.905), (0.11, 0.95), (0.03, 0.925)]
    for lado_z, letra in ((1, "a"), (-1, "b")):
        m.regla(f"luz.posicion_{letra}", Y([m.poligono(lado_z * z, y, OJO), x - 0.52]), lampara={"tipo": "faro"})
    # Direccionales delanteras: en la punta baja de las aletas del tanque, junto a la horquilla (foto gris oficial)
    for lado_z, letra in ((1, "a"), (-1, "b")):
        m.regla(f"ambar.direccional_del_{letra}", Y([x - 0.435, banda(y, 0.60, 0.685), banda(lado_z * z, 0.14, 0.23)]), lampara={"tipo": "direccional"})
    # Stop LED: cuna roja en lo alto de la punta del colin, mirando hacia atras (foto trasera 360 de Yamaha USA y 3/4 de
    # Incolmotos). Solo la cara casi vertical (y 0,903-0,945, normal atras): debajo, de y 0,86 a 0,90, la punta tiene una
    # cara inclinada hacia abajo que es colin; con ella la normal de la lampara apuntaba 38 grados al piso y la luz roja
    # y el halo caian sobre el portaplaca. La placa y su luz van en el portaplaca, debajo de las direccionales.
    STOP = [(-0.034, 0.903), (0.034, 0.903), (0.068, 0.946), (-0.068, 0.946)]   # trapecio en (z, y), ancho arriba
    m.regla("stop.stop", Y([m.poligono(z, y, STOP), -0.87 - x, -0.4 - m.nx, 0.7 - np.abs(m.ny)]), lampara={"tipo": "stop"})
    tras = Y([banda(x, -1.01, -0.90), banda(y, 0.72, 0.77), az - 0.15])
    m.regla("ambar.direccional_tras_a", Y([tras, z]), lampara={"tipo": "direccional"})
    m.regla("ambar.direccional_tras_b", tras, lampara={"tipo": "direccional"})
    m.regla("oscuro.direccional_tallos", Y([banda(x, -1.01, -0.86), banda(y, 0.715, 0.775), az - 0.07]))

    # --- Manubrio, espejos, tablero y farola
    arriba = Y([y - 0.975, 0.52 - x, x - 0.18])
    m.regla("espejo.luna", Y([y - 1.15, az - 0.24, -0.3 - m.nx]), padre="espejos.fabrica")
    m.regla("oscuro.espejos", Y([y - 1.07, az - 0.2]), padre="espejos.fabrica")
    m.regla("caucho.punos", Y([arriba, az - 0.33]))
    m.regla("oscuro.manubrio", arriba, manubrio={"x": 0.3, "y": 1.01, "extremo": 0.44},
            sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"])
    m.regla("pintura.farola", Y([x - 0.49, banda(y, 0.76, 1.05), 0.115 - az]), rol="visor_fijo")

    # --- Tanque con aletas (pintado), asiento, colin y portaplaca
    TANQUE = [(-0.16, 0.80), (-0.05, 0.93), (0.10, 0.995), (0.28, 0.965), (0.38, 0.93), (0.47, 0.76), (0.46, 0.64),
              (0.22, 0.635), (0.05, 0.71), (-0.16, 0.76)]
    m.regla("asiento.asiento", Y([banda(x, -0.745, -0.12), 0.14 - az, m.ny - 0.5, y - 0.76]))
    m.regla("pintura.tanque", Y([lado(TANQUE, az < 0.25), 0.25 - az]), zonas=["tanque"])
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
