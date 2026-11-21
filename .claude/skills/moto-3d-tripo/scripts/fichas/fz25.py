# Ficha de la Yamaha FZ25 (249 cc, monocilindrica) para ciclo.py. Modelo de Tripo SIN textura (62 mil triangulos, a lo
# largo de z con el manubrio en +z: preparar.py T 1.36 90). La escala de preparar.py deja las llantas a su medida
# (R 0,29 y 0,31: 100/80-17 y 140/70-17) y el largo en 1,99 m (ficha 2,015 m).
# Coordenadas: x adelante, y arriba, z hacia el escape (lado derecho de la moto).
# Pintura segun la foto lateral del fabricante (azul): tanque y la parte alta de las aletas, los costados de la mascara,
# la franja bajo el asiento y el guardabarros delantero. La parte baja de las aletas y el bastidor van en gris (plastico).
# Luces al estilo de la Eco Deluxe: faro con mica curva de Tripo, reflector, aro y bombillo (extras), ojos LED de
# posicion, direccionales en mica ambar + carcasa + vastago, stop LED en la punta del colin.
import numpy as np

import formas
from motor import O, Y, banda

EJES = 1.36
MEZCLA = 0.6
SITIOS = {}
CONSERVAR = []
ISLAS = {"isla": 24, "isla_pintura": 200, "rigidas": ("llanta", "rin", "_quitar", "direccional")}
ALISAR = {"pintura.tanque": 8, "asiento.asiento": 4, "pintura.farola": 3}
SUAVE = 3

# Faro: lente bajo los ojos, trapecio en (z, y) ancho arriba
FARO = [(-0.050, 0.772), (0.050, 0.772), (0.066, 0.800), (0.068, 0.828), (-0.068, 0.828), (-0.066, 0.800)]
X_LENTE = 0.60   # tope de x: solo la cara de adelante de la mascara


def cortar(m):
    x, y, z, az = m.x, m.y, m.z, m.az
    xd, yd, Rd, rd = m.rueda(0.684, 0.292, 0.29)
    xt, yt, Rt, rt = m.rueda(-0.674, 0.309, 0.309)
    m.medidas.update(eje_del=[xd, yd], eje_tras=[xt, yt], R_del=Rd, R_tras=Rt)
    print(f"ruedas del ({xd:.3f},{yd:.3f}) R={Rd:.3f}  tras ({xt:.3f},{yt:.3f}) R={Rt:.3f}  entre ejes {xd - xt:.3f}")

    def lado(pol, valido=None, ancho=0.01):
        d = m.poligono(x, y, pol)
        return m.pliegue(d, np.ones(len(x), bool) if valido is None else valido, ancho)

    # --- Ruedas de aleacion 17": llanta y rin (aro y rayos colados). Aro medido: talon a r 0,232-0,235 en las dos.
    RIN = 0.233
    m.regla("oscuro.mordaza_del", Y([banda(x, xd - 0.20, xd - 0.03), banda(y, yd - 0.02, yd + 0.18), banda(z, 0.07, 0.125), banda(rd, 0.09, 0.19)]), pieza="freno_del")
    m.regla("_quitar", Y([rd - 0.075, 0.15 - rd, banda(az, 0.05, 0.075)]))
    m.disco("disco.disco_del", xd, yd, 0.064, 0.141, "freno_del", interior=0.6,
            filas=((0.70, 14, 0.0055), (0.84, 14, 0.0055)))
    m.disco("disco.disco_tras", xt, yt, 0.072, 0.110, "freno_tras", interior=0.55)
    angd = np.degrees(np.arctan2(y - yd, x - xd))
    m.regla("caucho.llanta_del", Y([rd - RIN, O([Rd + 0.006 - rd, Y([Rd + 0.02 - rd, O([12 - angd, angd - 176])])]), 0.058 - az]), pieza="llanta_del", eje=[xd, yd])
    m.regla("caucho.llanta_tras", Y([rt - RIN, Rt + 0.02 - rt, 0.08 - az]), pieza="llanta_tras", eje=[xt, yt])
    m.regla("rin.rin_del", Y([RIN - rd, O([0.045 - az, Y([0.06 - rd, 0.06 - az])])]), pieza="llanta_del", rin=True, eje=[xd, yd])
    m.regla("rin.rin_tras", Y([RIN - rt, O([0.055 - az, Y([0.07 - rt, 0.065 - az])])]), pieza="llanta_tras", rin=True, eje=[xt, yt])
    m.regla("metal.corona", Y([0.125 - rt, banda(-z, 0.065, 0.11)]), pieza="cadena")

    # --- Guardabarros delantero (el de Tripo, pintado) y horquilla convencional
    ang = np.degrees(np.arctan2(y - yd, x - xd))
    df = m.recta(x, y, (xd, yd), (0.36, 0.985))
    m.regla("oscuro.horquilla", Y([0.03 - df, banda(az, 0.045, 0.11), banda(y, yd - 0.03, 0.97)]), pieza="suspension_del")
    m.regla("pintura.guardabarros_del", Y([O([rd - (Rd + 0.004), Y([az - 0.058, rd - (Rd - 0.03)])]), Rd + 0.10 - rd, banda(ang, 12, 150), 0.118 - az]), zonas=["guardabarros"])

    # --- Luces
    # Faro: mica = la superficie curva de Tripo dentro del trapecio (transparente); detras van reflector y bombillo
    m.regla("vidrio.mica_faro", Y([m.poligono(z, y, FARO), x - X_LENTE]), doble=True)
    # Ojos LED de posicion (las cejas inclinadas de la mascara)
    OJO = [(0.018, 0.836), (0.080, 0.852), (0.084, 0.872), (0.022, 0.850)]
    for lz, l in ((1, "a"), (-1, "b")):
        m.regla(f"luz.posicion_{l}", Y([m.poligono(lz * z, y, OJO), x - 0.58]), lampara={"tipo": "faro", "cono": False})
    # Direccionales delanteras: capsula en tallo a cada lado detras de la mascara
    caja = Y([banda(x, 0.44, 0.575), banda(y, 0.878, 0.937)])
    sel = (x > 0.44) & (x < 0.575) & (y > 0.878) & (y < 0.937) & (az > 0.15) & (az < 0.22)
    xc = float(np.median(x[sel])) if sel.any() else 0.51
    for lz, l in ((1, "a"), (-1, "b")):
        s = lz * z
        m.regla(f"ambar.direccional_del_{l}", Y([caja, banda(s, 0.155, 0.225), x - xc]), lampara={"tipo": "direccional"})
        m.regla(f"negro_brillo.carcasa_del_{l}", Y([caja, banda(s, 0.155, 0.225)]))
        m.regla(f"oscuro.vastago_del_{l}", Y([caja, banda(s, 0.10, 0.16)]))
    # Stop LED: la cara de atras de la punta del colin
    STOP = [(-0.072, 0.874), (0.072, 0.874), (0.085, 0.900), (0.075, 0.928), (-0.075, 0.928), (-0.085, 0.900)]
    m.regla("stop.stop", Y([m.poligono(z, y, STOP), -0.84 - x, -0.4 - m.nx]), lampara={"tipo": "stop"})
    # Direccionales traseras en la barra del portaplaca (mica = mitad de atras)
    ct = Y([banda(x, -1.07, -0.88), banda(y, 0.775, 0.835)])
    sel = (x > -1.07) & (x < -0.88) & (y > 0.775) & (y < 0.835) & (az > 0.14) & (az < 0.205)
    xct = float(np.median(x[sel])) if sel.any() else -0.98
    for lz, l in ((1, "a"), (-1, "b")):
        s = lz * z
        m.regla(f"ambar.direccional_tras_{l}", Y([ct, banda(s, 0.145, 0.205), xct - x]), lampara={"tipo": "direccional"})
        m.regla(f"negro_brillo.carcasa_tras_{l}", Y([ct, banda(s, 0.145, 0.205)]))
    m.regla("oscuro.vastago_tras", Y([banda(x, -1.07, -0.78), banda(y, 0.775, 0.845), 0.15 - az]))

    # --- Manubrio, espejos y mascara
    arriba = Y([y - 0.965, 0.47 - x, x - 0.18])
    m.regla("espejo.luna", Y([y - 1.15, az - 0.22, -0.3 - m.nx]), padre="espejos.fabrica")
    m.regla("oscuro.espejos", Y([y - 1.07, az - 0.19]), padre="espejos.fabrica")
    m.regla("caucho.punos", Y([arriba, az - 0.30]))
    m.regla("oscuro.manubrio", arriba, manubrio={"x": 0.31, "y": 1.0, "extremo": 0.40},
            sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"])
    m.regla("negro_brillo.faro_marco", Y([banda(z, -0.09, 0.09), banda(y, 0.755, 0.885), x - 0.585]))
    m.regla("pintura.farola", Y([x - 0.50, banda(y, 0.74, 0.99), 0.12 - az]), rol="visor_fijo", zonas=["farola"])

    # --- Tanque (azul arriba), aletas bajas grises, asiento, colin y portaplaca
    TANQUE = [(-0.24, 0.80), (-0.05, 0.92), (0.15, 0.985), (0.35, 0.93), (0.52, 0.81), (0.58, 0.67), (0.50, 0.63),
              (0.30, 0.71), (0.05, 0.765), (-0.24, 0.765)]
    m.regla("asiento.asiento", Y([banda(x, -0.80, -0.20), 0.15 - az, m.ny - 0.45, y - 0.80]))
    m.regla("pintura.tanque", Y([lado(TANQUE, az < 0.27), 0.27 - az, O([0.33 - x, az - 0.12])]), zonas=["tanque"])
    m.regla("plastico.aletas", Y([banda(x, 0.0, 0.62), banda(y, 0.45, 0.80), banda(az, 0.09, 0.27)]))
    COLIN = [(-0.97, 0.87), (-0.70, 0.865), (-0.32, 0.80), (-0.26, 0.745), (-0.42, 0.725), (-0.97, 0.835)]
    m.regla("pintura.colin", Y([lado(COLIN, az > 0.05), az - 0.06, 0.2 - az]), zonas=["lateral"])
    m.regla("plastico.colin", Y([banda(x, -1.0, -0.25), banda(y, 0.66, 0.96), 0.2 - az]))
    placa = {"c": [-1.005, 0.70, 0], "incl": -0.1, "tam": [0.17, 0.09]}
    m.regla("plastico.portaplaca", Y([-0.86 - x, 0.86 - y, y - 0.55, 0.13 - az]), placa=placa,
            acomodar=[{"grupo": "accesorios.baul", "ref": "abajo", "a": [-0.82, 0.95, 0]}])

    # --- Mecanica a la vista
    ESCAPE = [(-0.80, 0.30), (-0.78, 0.50), (-0.36, 0.48), (-0.20, 0.30), (0.05, 0.25), (0.26, 0.30), (0.31, 0.19), (-0.05, 0.16), (-0.40, 0.27), (-0.80, 0.27)]
    m.regla("cromo.escape", Y([m.poligono(x, y, ESCAPE), z - 0.05]), padre="escapeFabrica")
    db = m.recta(x, y, (-0.17, 0.43), (xt, yt))
    m.regla("oscuro.basculante", Y([0.045 - db, banda(x, xt - 0.03, -0.15), banda(az, 0.03, 0.12)]), pieza="suspension_tras")
    MOTOR = [(-0.18, 0.20), (-0.20, 0.55), (0.0, 0.64), (0.28, 0.62), (0.34, 0.40), (0.27, 0.17), (-0.10, 0.16)]
    m.regla("motor.bloque", Y([m.poligono(x, y, MOTOR), 0.16 - az]), pieza="motor")
    m.regla("_quitar", Y([rt - (Rt - 0.06), Rt + 0.045 - rt, 0.10 - az, 0.6 - y]))
    m.resto("chasis.chasis")

    faro_extras(m)


def _x_cara(m, zz, yy, r=0.006):
    """x de la cara de adelante de la mascara en (z, y): maximo de los vertices cercanos."""
    d = (m.z - zz) ** 2 + (m.y - yy) ** 2
    cerca = d < r * r
    if not cerca.any():
        cerca = d <= np.partition(d, 5)[5]
    return float(m.x[cerca].max())


def faro_extras(m):
    """Como la Eco Deluxe: aro que sigue el borde de la mica, reflector detras y bombillo LED en el foco."""
    # Borde del trapecio remuestreado y llevado a la cara de la mascara
    pol = np.array(FARO + [FARO[0]])
    pts = []
    for a, b in zip(pol[:-1], pol[1:]):
        for t in np.linspace(0, 1, 6, endpoint=False):
            pts.append(a + (b - a) * t)
    borde = np.array([[_x_cara(m, zz, yy) - 0.002, yy, zz] for zz, yy in pts])
    P, N, I = formas.con_normales(formas.tubo(borde, 0.0035, 8, cerrado=True), 60)
    m.extra["cromo.aro_faro"] = (P, N, I, {})
    # Reflector: copa eliptica (revolucion alrededor de x, aplastada en y) que tapa el hueco detras de la mica
    xf = float(np.min(borde[:, 0]))
    yc, hz, hy = 0.800, 0.070, 0.030
    perfil = [(0.0, -0.045), (0.35, -0.040), (0.6, -0.030), (0.8, -0.017), (0.95, -0.006), (1.02, 0.0)]
    Pr, Ir = formas.revolucion(perfil, (xf, yc, 0.0), (1, 0, 0), 32)
    Pr = Pr.copy()
    Pr[:, 1] = yc + (Pr[:, 1] - yc) * hy
    Pr[:, 2] = Pr[:, 2] * hz
    P, N, I = formas.con_normales((Pr, Ir), 80)
    m.extra["cromo.reflector_faro"] = (P, N, I, {"doble": True})
    # Bombillo: tira LED (dos medias esferas) en el foco, mirando hacia adelante
    fs = []
    for zz in (-0.022, 0.022):
        fs.append(formas.revolucion([(0.0, 0.0), (0.012, 0.0), (0.011, 0.004), (0.008, 0.008), (0.0, 0.0105)],
                                    (xf - 0.030, yc, zz), (1, 0, 0), 16))
    P, N, I = formas.con_normales(formas.unir(*fs), 50)
    m.extra["luz.faro"] = (P, N, I, {"lampara": {"tipo": "faro"}})
