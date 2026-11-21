# Ficha de la Yamaha Aerox 155 (scooter, 155 cc VVA, agua) para ciclo.py. Modelo de Tripo SIN textura (61 mil
# triangulos, a lo largo de z con el manubrio en +z: preparar.py T 1.35 90). Entre ejes 1,35 m (ficha Yamaha Aerox 155).
# Coordenadas: x adelante, y arriba, z hacia el escape (lado derecho de la moto).
# Fotos (manual_despiece/yamaha_aerox155/fotos, 4 de Wikimedia + faro): escudo frontal y tapas laterales traseras del
# color de la moto; piso, tunel, asiento, guardabarros, cubre manubrio y parte baja en negro. Disco delantero y escape a
# la derecha (+z); caja del CVT a la izquierda. Faros LED dobles en el escudo, bajo la ceja pintada.
import numpy as np

import formas
from motor import O, Y, banda

EJES = 1.35
MEZCLA = 0.6
CONSERVAR = []
ISLAS = {"isla": 24, "isla_pintura": 200, "rigidas": ("llanta", "rin", "_quitar", "direccional")}
ALISAR = {"pintura.escudo": 6, "pintura.laterales": 6, "asiento.asiento": 4}
SUAVE = 3
ZC = 0.03   # centro de la cola de Tripo (corrida 3 cm a la derecha): placa, stop y direccionales traseras
# Calcas de fabrica en puntos fijos del panel lateral (las de la linea, por posicion relativa, flotaban; usuario 20-nov)
CALCAS = [
    {"id": "nombre", "nombre": "Nombre aerox", "tipo": "texto", "texto": "aerox", "fuente": "yamaha_script", "zona": ["lateral"], "cara": "lado", "en": [-0.48, 0.74], "ancho": 0.22, "giro": 10, "color": "vivo:#35c4ef"},
    {"id": "rayas", "nombre": "Rayas traseras", "tipo": "franja", "forma": "rayas", "zona": ["lateral"], "cara": "lado", "en": [-0.74, 0.80], "ancho": 0.08, "giro": 0, "color": "vivo:#35c4ef", "color2": "letra"},
]


def cortar(m):
    x, y, z, az = m.x, m.y, m.z, m.az
    xd, yd, Rd, rd = m.rueda(0.673, 0.264, 0.263)
    xt, yt, Rt, rt = m.rueda(-0.674, 0.278, 0.26)
    m.medidas.update(eje_del=[xd, yd], eje_tras=[xt, yt], R_del=Rd, R_tras=Rt)
    print(f"ruedas del ({xd:.3f},{yd:.3f}) R={Rd:.3f}  tras ({xt:.3f},{yt:.3f}) R={Rt:.3f}  entre ejes {xd - xt:.3f}")

    # --- Ruedas de aleacion 14" (110/80 y 140/70): llanta y rin colado
    m.regla("oscuro.mordaza_del", Y([banda(x, xd - 0.17, xd - 0.02), banda(y, yd - 0.01, yd + 0.15), banda(z, 0.058, 0.105), banda(rd, 0.07, 0.15)]), pieza="freno_del")
    m.regla("_quitar", Y([rd - 0.06, 0.13 - rd, banda(az, 0.040, 0.064)]))   # disco de Tripo (pintado y plano)
    m.disco("disco.disco_del", xd, yd, 0.052, 0.115, "freno_del", interior=0.62,
            filas=((0.70, 12, 0.0050), (0.84, 12, 0.0050), (0.93, 24, 0.0036)))   # 230 mm
    portador(m, xd, yd, 0.052, 0.115 * 0.62 + 0.004, "freno_del")
    # Llantas ajustadas al ancho real de la malla (+-4,8 y +-6,2 cm) y sin el asiento del aro: caras de mas a un lado
    # (disco, buje, guardabarros) hacian que el torneado del visor sacara un «disco» o una «dona» al lado (usuario 20-nov).
    # Hasta R - 0,003 (el visor le suma 3 mm de holgura): asi la llanta torneada cabe bajo el guardabarros de Tripo.
    m.regla("caucho.llanta_del", Y([rd - (Rd - 0.072), Rd - 0.018 - rd, 0.048 - az]), pieza="llanta_del", eje=[xd, yd], torno="redondo")
    m.regla("caucho.llanta_tras", Y([rt - (Rt - 0.075), O([Rt + 0.004 - rt, Y([Rt + 0.022 - rt, yt - y])]), banda(z, -0.05, 0.062), yt + 0.17 - y]), pieza="llanta_tras", eje=[xt, yt], torno="redondo")   # (la de Tripo va corrida 1 cm a la derecha)
    m.regla("rin.rin_del", Y([Rd - 0.072 - rd, O([0.036 - az, Y([0.05 - rd, 0.05 - az])])]), pieza="llanta_del", rin=True, eje=[xd, yd])
    m.regla("rin.rin_tras", Y([Rt - 0.075 - rt, O([0.045 - az, Y([0.05 - rt, 0.06 - az])])]), pieza="llanta_tras", rin=True, eje=[xt, yt])

    # --- Guardabarros delantero (negro en las fotos) y horquilla telescopica
    ang = np.degrees(np.arctan2(y - yd, x - xd))
    m.regla("oscuro.horquilla", Y([banda(x, xd - 0.25, xd + 0.03), banda(az, 0.06, 0.11), banda(y, yd - 0.03, 0.66), banda(rd, 0.0, 0.42)]), pieza="suspension_del")
    # Guardabarros de Tripo (negro en las fotos; el usuario lo prefiere al propio)
    # (la cara interior del guardabarros de Tripo va pegada a la banda, a r 0,254-0,27: se conserva y la llanta se achica 1,5 cm)
    m.regla("plastico.guardabarros_del", Y([O([rd - (Rd + 0.006), Y([rd - (Rd - 0.015), banda(ang, 22, 162)])]), Rd + 0.12 - rd, banda(ang, -10, 175), 0.085 - az]))

    # --- Luces: faros LED dobles en el escudo (franja inclinada bajo la ceja), direccionales en la punta de afuera
    # Faro grande (fotos 2021-2025 y _faro_aerox.jpg): cuña bajo la ceja pintada, angosta adentro y alta afuera
    FARO = [(0.058, 0.745), (0.19, 0.828), (0.205, 0.79), (0.206, 0.726), (0.11, 0.684), (0.056, 0.70)]   # todo el hueco
    # Direccionales delanteras: lente chico en la esquina de adelante del panel lateral bajo, sobre el guardabarros
    # (fotos 2021 y 2022: debajo del faro, junto a la horquilla), no junto al faro
    DIR = [(0.108, 0.565), (0.178, 0.575), (0.185, 0.512), (0.112, 0.498)]
    frente = x - 0.50
    for s, l in ((1, "a"), (-1, "b")):
        m.regla(f"luz.faro_{l}", Y([m.pliegue(m.poligono(s * z, y, FARO), s * z > 0, 0.014), frente, m.nx - 0.35]), lampara={"tipo": "faro"})
    for s, l in ((1, "a"), (-1, "b")):
        m.regla(f"ambar.direccional_del_{l}", Y([m.poligono(s * z, y, DIR), x - 0.52, m.nx + 0.05]), lampara={"tipo": "direccional"})
    # Stop LED en la punta del colin, mirando atras; direccionales traseras en la barra del portaplaca
    STOP = [(-0.075, 0.81), (0.075, 0.81), (0.088, 0.878), (-0.088, 0.878)]
    m.regla("stop.stop", Y([m.poligono(z - ZC, y, STOP), -0.70 - x, -0.45 - m.nx]), lampara={"tipo": "stop"})
    tras = Y([-0.74 - x, banda(y, 0.705, 0.80)])
    # (ambar solo el lente de la punta; el tallo que sale del portaplaca va oscuro)
    m.regla("_quitar", Y([tras, z - 0.10]))   # tallo derecho de Tripo (va el propio)
    m.regla("_quitar", Y([tras, -z - 0.06]))   # la izquierda de Tripo (a medias, quedaba doble)
    tallos(m)   # direccionales propias, cortas (las de Tripo sobresalian 5 cm de la cola vista desde arriba)

    # --- Manubrio, espejos, visor y tablero
    m.regla("espejo.luna", Y([y - 1.12, az - 0.24, -0.3 - m.nx]), padre="espejos.fabrica")
    m.regla("oscuro.espejos", Y([y - 1.06, az - 0.2]), padre="espejos.fabrica")
    m.regla("caucho.punos", Y([y - 0.93, banda(x, 0.15, 0.40), az - 0.30]))
    m.regla("vidrio_oscuro.visor", Y([x - 0.34, y - 0.985, 0.12 - az]), rol="visor_fijo")   # entero (antes medio visor quedaba como hueco)
    nt = np.array([-0.55, 0.835, 0.0])
    tablero = [{"c": [0.315, 1.035, 0.0], "n": [round(float(v), 4) for v in nt / np.linalg.norm(nt)], "tam": [0.12, 0.055], "dibujo": "tacometro"}]
    m.regla("oscuro.manubrio", Y([y - 0.93, banda(x, 0.12, 0.48)]), manubrio={"x": 0.27, "y": 0.99, "extremo": 0.38}, pantalla=tablero,
            sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"])

    # --- Carroceria: escudo frontal y tapas laterales traseras pintados; lo demas plastico negro
    NARIZ = [(0, 0.67), (0.04, 0.69), (0.08, 0.726), (0.11, 0.846), (0.115, 0.96), (0, 0.96)]
    m.regla("plastico.nariz", Y([m.pliegue(m.poligono(az, y, NARIZ), x > 0.45, 0.012), x - 0.42]))
    m.regla("pintura.escudo", Y([x - 0.33, banda(y, 0.40, 0.93), O([y - 0.62, az - 0.09])]), zonas=["frente"])
    ASIENTO = [(-0.80, 0.85), (-0.70, 0.935), (-0.40, 0.935), (-0.15, 0.88), (-0.06, 0.85), (-0.08, 0.79), (-0.40, 0.795), (-0.80, 0.815)]
    m.regla("asiento.asiento", Y([m.pliegue(m.poligono(x, y, ASIENTO), az < 0.2, 0.01), 0.19 - az, m.ny + 0.3]))
    LAT = [(-0.92, 0.84), (-0.55, 0.92), (-0.12, 0.80), (0.05, 0.66), (-0.05, 0.56), (-0.45, 0.60), (-0.85, 0.72)]
    m.regla("pintura.laterales", Y([m.poligono(x, y, LAT), az - 0.09]), zonas=["lateral"], calcas_fabrica=CALCAS)
    placa = {"c": [-0.862, 0.655, -ZC],   # (la placa no se espeja al exportar; la malla si)
    "incl": -0.42, "tam": [0.15, 0.08]}
    m.regla("plastico.portaplaca", Y([-0.86 - x, 0.75 - y, y - 0.38, 0.10 - az]), placa=placa,
            acomodar=[{"grupo": "accesorios.baul", "ref": "abajo", "a": [-0.78, 0.93, 0]}])

    # --- Mecanica: escape a la derecha, caja del CVT a la izquierda, amortiguadores y bloque
    m.regla("oscuro.escape", Y([banda(x, -1.05, -0.30), banda(y, 0.15, 0.60), z - 0.13]), padre="escapeFabrica")
    m.regla("metal.amortiguadores", Y([banda(x, -0.80, -0.58), banda(y, 0.40, 0.74), banda(az, 0.07, 0.135)]), pieza="suspension_tras")
    CVT = [(-0.76, 0.20), (-0.76, 0.40), (-0.45, 0.48), (-0.08, 0.44), (0.02, 0.30), (-0.05, 0.17), (-0.40, 0.15)]
    m.regla("motor.cvt", Y([m.poligono(x, y, CVT), -z - 0.075]), pieza="correa")
    MOTOR = [(-0.25, 0.14), (-0.25, 0.45), (0.10, 0.48), (0.22, 0.38), (0.15, 0.14)]
    m.regla("motor.bloque", Y([m.poligono(x, y, MOTOR), 0.16 - az]), pieza="motor")
    # Restos de las llantas de Tripo a los lados (el torneado los dejaba como un segundo circulo, usuario 20-nov)
    m.regla("_quitar", Y([rd - (Rd - 0.085), O([Rd + 0.014 - rd, Y([Rd + 0.022 - rd, yd - y])]), 0.085 - az]))
    m.regla("_quitar", Y([rt - (Rt - 0.085), O([Rt + 0.014 - rt, Y([Rt + 0.03 - rt, yt - y])]), 0.095 - az]))
    # «Dona» de Tripo al lado derecho de la rueda trasera (anillo a z 0,022-0,125: la llanta real de Tripo va de -0,035 a 0,02, r 0,16-0,275; no es pieza real)
    m.regla("_quitar", Y([rt - 0.16, 0.278 - rt, banda(z, 0.07, 0.126)]))
    # Casco suelto de Tripo delante de la rueda trasera (quedaba flotando al limpiar la llanta)
    m.regla("_quitar", Y([banda(x, -0.49, -0.33), banda(y, 0.26, 0.43), banda(z, 0.015, 0.09), banda(rt, 0.24, 0.30)]))
    # El resto de la carroceria (piso, tunel, bajos) plastico negro
    m.resto("plastico.carroceria")


def _mt03():
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("ficha_mt03", os.path.join(os.path.dirname(os.path.abspath(__file__)), "mt03.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tallos(m):
    """Tallos de las direccionales traseras: tubo del soporte central a cada lente (antes, el de Tripo espejado quedaba doble)."""
    fs = [formas.tubo([(-0.772, 0.758, ZC + s * 0.03), (-0.772, 0.758, ZC + s * 0.104)], 0.0095, 10) for s in (1, -1)]
    P, N, I = formas.con_normales(formas.unir(*fs), 40)
    m.extra["oscuro.direccional_tras_tallos"] = (P, N, I, {})
    lente = [(0, 0), (0.011, 0), (0.0145, 0.006), (0.0155, 0.028), (0.012, 0.040), (0, 0.044)]
    for s, l in ((1, "a"), (-1, "b")):
        P, I = formas.revolucion(lente, (-0.772, 0.758, ZC + s * 0.10), (0, 0, s), 20)
        P, N, I = formas.con_normales((np.asarray(P), np.asarray(I)), 40)
        m.extra[f"ambar.direccional_tras_{l}"] = (P, N, I, {"lampara": {"tipo": "direccional"}})


def arco_guardabarros(m, xd, yd, R, a0=12, a1=128, n=36):
    """Guardabarros delantero: casco curvo 1,4 cm por encima de la llanta torneada, de 12 a 128 grados (0 = adelante)."""
    w, ri, e = 0.056, R + 0.013, 0.006
    zs = np.linspace(-w, w, 9)
    caida = 0.012 * (zs / w) ** 2
    lazo = [(ri + e - c, zz) for zz, c in zip(zs, caida)] + [(ri - c, zz) for zz, c in zip(zs[::-1], caida[::-1])]
    k = len(lazo)
    P, I = [], []
    for a in np.radians(np.linspace(a0, a1, n)):
        P += [(xd + r * np.cos(a), yd + r * np.sin(a), zz) for r, zz in lazo]
    for j in range(n - 1):
        for i in range(k):
            a, b, c, d = j * k + i, j * k + (i + 1) % k, (j + 1) * k + (i + 1) % k, (j + 1) * k + i
            I += [(a, b, c), (a, c, d)]
    for j, sg in ((0, 1), (n - 1, -1)):
        ctr = len(P)
        P.append(tuple(np.mean(P[j * k:(j + 1) * k], axis=0)))
        for i in range(k):
            a, b = j * k + i, j * k + (i + 1) % k
            I.append((ctr, b, a) if sg > 0 else (ctr, a, b))
    P, N, I = formas.con_normales((np.array(P), np.array(I)), 40)
    m.extra["plastico.guardabarros_arco"] = (P, N, I, {})


def portador(m, xd, yd, zc, r_ext, pieza, brazos=5):
    """Portador del disco: aro central y brazos con un remache en cada punta."""
    eje, base = (0, 0, 1), (xd, yd, zc)
    fs = [formas.revolucion([(0.030, -0.003), (0.044, -0.003), (0.044, 0.003), (0.030, 0.003), (0.030, -0.003)], base, eje, 32)]
    for k in range(brazos):
        a = 2 * np.pi * k / brazos
        ca, sa = np.cos(a), np.sin(a)
        rect = [(0.040, -0.008), (r_ext, -0.006), (r_ext, 0.006), (0.040, 0.008)]
        pol = [(xd + r * ca - t * sa, yd + r * sa + t * ca) for r, t in rect]
        fs.append(formas.extrusion(pol, zc - 0.0028, zc + 0.0028))
        c = (xd + (r_ext - 0.004) * ca, yd + (r_ext - 0.004) * sa, zc)
        fs.append(formas.revolucion([(0, -0.004), (0.004, -0.004), (0.004, 0.004), (0, 0.004)], c, eje, 10))
    P, N, I = formas.con_normales(formas.unir(*fs), 40)
    m.extra["titanio.disco_portador_del"] = (P, N, I, {"pieza": pieza})


def internos(k):
    """Rayos X: monocilindrico de agua casi horizontal (ciguenal, piston, cilindro), bujia, aceite, CVT (poleas y
    correa), bateria y filtro. Antes de espejar: +z es el lado del escape; el CVT va a -z."""
    F, pon, cil = k.F, k.pon, k.cil
    C = np.array([-0.12, 0.30, 0.0])
    dc = np.array([0.94, 0.34, 0.0])
    dc /= np.linalg.norm(dc)
    cig = [(0, -0.06), (0.011, -0.06), (0.011, -0.022), (0.044, -0.022), (0.044, -0.007), (0.013, -0.007),
           (0.013, 0.007), (0.044, 0.007), (0.044, 0.022), (0.011, 0.022), (0.011, 0.06), (0, 0.06)]
    pon("metal.motor_ciguenal", "motor", F.revolucion(cig, C, (0, 0, 1), 20), F.tubo([C + dc * 0.03, C + dc * 0.14], 0.0075, 8))
    pon("motor.motor_cilindro", "motor", F.revolucion([(0.030, 0.08), (0.040, 0.08), (0.040, 0.20), (0.045, 0.205), (0.045, 0.25), (0.032, 0.265), (0, 0.265)], C, dc, 20))
    pon("cromo.motor_piston", "motor", F.revolucion([(0, 0.14), (0.0290, 0.14), (0.0290, 0.146), (0.027, 0.148), (0.029, 0.15), (0.029, 0.178), (0, 0.18)], C, dc, 20))
    bb = C + dc * 0.265
    pon("metal.bujia_rosca", "bujia", F.revolucion([(0, -0.02), (0.005, -0.02), (0.005, 0.01), (0.0085, 0.01), (0.0085, 0.018), (0.005, 0.018)], bb, dc, 8))
    pon("bujia.bujia_aislador", "bujia", F.revolucion([(0.005, 0.018), (0.0065, 0.02), (0.0065, 0.05), (0, 0.052)], bb, dc, 10))
    pon("oscuro.bujia_capuchon", "bujia", F.revolucion([(0, 0.03), (0.011, 0.03), (0.011, 0.08), (0, 0.085)], bb, dc, 10))
    carter = F.suave([(-0.12, -0.02), (-0.11, -0.08), (-0.04, -0.10), (0.06, -0.09), (0.09, -0.05), (0.09, 0.0), (0.05, 0.03), (-0.10, 0.03)], 2)
    pon("carter.aceite_carter", "aceite", F.mover(F.extrusion(carter, -0.06, 0.06, 0.012), C))
    nivel = F.suave([(-0.10, -0.055), (-0.095, -0.075), (-0.04, -0.09), (0.05, -0.082), (0.075, -0.06), (0.08, -0.055)], 1)
    pon("aceiteVisible.aceite_nivel", "aceite", F.mover(F.extrusion(nivel, -0.05, 0.05, 0.004), C))
    pon("metal.aceite_tapon", "aceite", F.revolucion([(0, 0), (0.011, 0), (0.011, 0.008), (0.0075, 0.008), (0.0075, 0.016), (0, 0.016)], C + [-0.03, -0.10, 0], (0, -1, 0), 6))
    # CVT del lado izquierdo (-z): polea motriz en el ciguenal, polea conducida junto al eje trasero, correa entre ellas
    zc = -0.10
    p1, p2 = C + [0, 0, zc], np.array([-0.56, 0.29, zc])
    pon("metal.cvt_polea_motriz", "correa", F.revolucion([(0, -0.012), (0.055, -0.004), (0.055, 0.004), (0, 0.012)], p1, (0, 0, 1), 24))
    pon("metal.cvt_polea_conducida", "correa", F.revolucion([(0, -0.012), (0.07, -0.004), (0.07, 0.004), (0, 0.012)], p2, (0, 0, 1), 24))
    d = p2 - p1
    d /= np.linalg.norm(d)
    nn = np.array([-d[1], d[0], 0.0])
    pon("caucho.cvt_correa", "correa", F.tubo([p1 + nn * 0.05, p2 + nn * 0.064], 0.008, 6), F.tubo([p1 - nn * 0.05, p2 - nn * 0.064], 0.008, 6))
    # Bateria bajo el asiento (frente del baul); caja del filtro sobre el CVT
    B = np.array([-0.22, 0.62, 0.0])
    pon("bateria.bat_cuerpo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.12, 0.08, 0.006), -0.035, 0.035, 0.004), B))
    pon("metal.bat_bornes", "bateria", *[cil(0.007, 0.012, B + [xx, 0.046, 0.012], (0, 1, 0), 10, 0.002) for xx in (-0.045, 0.045)])
    caja = F.suave([(-0.55, 0.42), (-0.50, 0.38), (-0.30, 0.38), (-0.26, 0.42), (-0.26, 0.50), (-0.30, 0.53), (-0.50, 0.53), (-0.55, 0.50)], 2)
    pon("oscuro.filtro_caja", "filtro_aire", F.extrusion(caja, -0.17, -0.07, 0.012))
