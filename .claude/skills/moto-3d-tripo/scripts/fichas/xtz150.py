# Ficha de la Yamaha XTZ 150 para ciclo.py. Modelo de Tripo SIN textura (48 mil triangulos, solo forma) entregado a lo
# largo de z: preparar.py con giro 90. Distancia entre ejes 1,36 m (aprox., no verificada en el manual local).
# Doble proposito: rin 21 adelante y 18 atras, guardabarros delantero alto (pico bajo la farola), disco adelante.
# Coordenadas: x adelante, y arriba, z hacia el escape (lado derecho de la moto).
import numpy as np

from motor import O, Y, banda

EJES = 1.36
MEZCLA = 0.6
ISLAS = {"isla": 24, "isla_pintura": 200, "rigidas": ("llanta", "rin", "aro", "rayos", "_quitar")}
ALISAR = {"pintura.tanque": 10, "pintura2.tapa_lateral": 4, "pintura.guardabarros_del": 4, "asiento.asiento": 4, "pintura.farola": 3}
SUAVE = 3
PERFIL = False        # (True: imprime el perfil radial de cada rueda para ajustar llanta, aro y rayos)


def cortar(m):
    x, y, z, az = m.x, m.y, m.z, m.az
    xd, yd, Rd, rd = m.rueda(0.68, 0.33, 0.325)
    xt, yt, Rt, rt = m.rueda(-0.673, 0.315, 0.31)
    m.medidas.update(eje_del=[xd, yd], eje_tras=[xt, yt], R_del=Rd, R_tras=Rt)
    print(f"ruedas del ({xd:.3f},{yd:.3f}) R={Rd:.3f}  tras ({xt:.3f},{yt:.3f}) R={Rt:.3f}  entre ejes {xd - xt:.3f}")
    if PERFIL:
        for nom, r, yc in (("del", rd, yd), ("tras", rt, yt)):
            bajo = y < yc - 0.05
            fila = []
            for a in np.arange(0.12, 0.36, 0.01):
                k = bajo & (r > a) & (r < a + 0.01)
                fila.append((round(float(a), 2), round(float(np.percentile(az[k], 90)), 3) if k.sum() > 5 else "-"))
            print(nom, fila)

    def lado(pol, valido=None, ancho=0.01):
        d = m.poligono(x, y, pol)
        return m.pliegue(d, np.ones(len(x), bool) if valido is None else valido, ancho)

    # --- Ruedas de rayos con disco adelante y atras, los dos a la derecha (+z, foto oficial), corona a la izquierda (-z)
    AD, AT = 0.226, 0.207          # radio del rin medido en el perfil (Tripo hizo las dos ruedas de R 0,306: la del 21 sale chica)
    m.regla("_quitar", Y([0.128 - rd, rd - 0.052, banda(-z, 0.02, 0.065)]))   # disco del modelo, del lado equivocado
    m.disco("disco.disco_del", xd, yd, 0.045, 0.1225, "freno_del", interior=0.55)   # 245 mm
    m.disco("disco.disco_tras", xt, yt, 0.07, 0.1015, "freno_tras", interior=0.55)  # 203 mm
    m.regla("caucho.llanta_del", Y([rd - AD, Rd + 0.03 - rd, 0.055 - az]), pieza="llanta_del", eje=[xd, yd])
    m.regla("metal.aro_del", Y([banda(rd, AD - 0.025, AD), 0.037 - az]), pieza="llanta_del", aro=True, eje=[xd, yd])
    m.regla("cromo.rayos_del", Y([AD - 0.025 - rd, 0.045 - az]), pieza="llanta_del", rin=True, eje=[xd, yd])
    m.regla("caucho.llanta_tras", Y([rt - AT, Rt + 0.03 - rt, 0.07 - az]), pieza="llanta_tras", eje=[xt, yt])
    m.regla("metal.aro_tras", Y([banda(rt, AT - 0.025, AT), 0.045 - az]), pieza="llanta_tras", aro=True, eje=[xt, yt])
    m.regla("metal.manzana_tras", Y([0.10 - rt, banda(z, 0.03, 0.09)]), pieza="freno_tras")
    m.regla("metal.corona", Y([0.12 - rt, banda(-z, 0.03, 0.09)]), pieza="cadena")
    m.regla("cromo.rayos_tras", Y([AT - 0.025 - rt, 0.05 - az]), pieza="llanta_tras", rin=True, eje=[xt, yt])

    # --- Luces: faro bajo la farola con visera, direccionales chicas a los lados de la farola y en tallos atras,
    # stop en la punta del colin
    FARO = [(0.072, 0.985), (-0.072, 0.985), (-0.07, 0.85), (0.07, 0.85)]
    m.regla("luz.faro", Y([m.pliegue(m.poligono(z, y, FARO), x > 0.5, 0.006), x - 0.525]), lampara={"tipo": "faro"})
    m.regla("stop.stop", Y([-0.985 - x, banda(y, 0.945, 1.012), 0.05 - az]), lampara={"tipo": "stop"})

    def gotas(nombre, cuerpo, hacia):
        xc = float(np.median(x[cuerpo > 0]))
        print(f"{nombre}: x[{x[cuerpo > 0].min():.3f},{x[cuerpo > 0].max():.3f}] centro {xc:.3f} y[{y[cuerpo > 0].min():.3f},{y[cuerpo > 0].max():.3f}] z[{az[cuerpo > 0].min():.3f},{az[cuerpo > 0].max():.3f}]")
        mica = Y([cuerpo, (x - xc) * hacia + 0.004])
        m.regla(f"ambar.{nombre}_a", Y([mica, z]), lampara={"tipo": "direccional"})
        m.regla(f"ambar.{nombre}_b", mica, lampara={"tipo": "direccional"})
        m.regla(f"oscuro.{nombre}_base", cuerpo)

    gotas("direccional_del", Y([banda(x, 0.39, 0.47), banda(y, 0.905, 0.99), banda(az, 0.145, 0.19)]), 1)
    gotas("direccional_tras", Y([banda(x, -0.935, -0.855), banda(y, 0.895, 0.955), banda(az, 0.12, 0.195)]), -1)

    # --- Tren delantero: horquilla convencional (barras cromadas arriba, botellas abajo) y guardabarros alto
    df = m.recta(x, y, (xd, yd), (0.44, 1.0))
    m.regla("cromo.barras", Y([0.03 - df, banda(az, 0.045, 0.12), banda(y, 0.56, 0.86)]), pieza="suspension_del")
    m.regla("metal.horquilla", Y([0.04 - df, banda(az, 0.045, 0.13), 0.56 - y, y - 0.25]), pieza="suspension_del")
    PICO = [(0.48, 0.81), (0.62, 0.81), (0.76, 0.755), (1.0, 0.615), (0.86, 0.615), (0.70, 0.64), (0.56, 0.655), (0.47, 0.70)]
    m.regla("pintura.guardabarros_del", Y([lado(PICO, az < 0.13), 0.13 - az]), zonas=["guardabarros"])
    m.regla("pintura.farola", Y([banda(x, 0.44, 0.63), banda(y, 0.80, 1.06), 0.13 - az]), rol="visor_fijo")

    # --- Manubrio y espejos
    m.regla("espejo.luna", Y([y - 1.19, az - 0.40, -0.35 - m.nx]), padre="espejos.fabrica")
    m.regla("oscuro.espejos", Y([y - 1.07, az - 0.20, 0.45 - x, x - 0.12]), padre="espejos.fabrica")
    m.regla("caucho.punos", Y([y - 0.98, 1.07 - y, az - 0.25, 0.42 - x, x - 0.12]))
    m.regla("oscuro.manubrio", Y([y - 0.985, 0.44 - x, x - 0.12]), manubrio={"x": 0.27, "y": 1.02, "extremo": 0.32},
            sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"])

    # --- Carroceria pintada, asiento y cola
    TANQUE = [(-0.22, 0.93), (-0.1, 0.99), (0.1, 1.0), (0.25, 0.975), (0.36, 0.93), (0.43, 0.85), (0.46, 0.75), (0.41, 0.665),
              (0.30, 0.62), (0.15, 0.63), (0.05, 0.66), (-0.1, 0.70), (-0.22, 0.78)]
    ASIENTO = [(-0.92, 0.935), (-0.7, 0.955), (-0.5, 0.905), (-0.35, 0.875), (-0.24, 0.905), (-0.16, 0.965), (-0.15, 0.86),
               (-0.3, 0.81), (-0.5, 0.83), (-0.7, 0.865), (-0.92, 0.885)]
    TAPA = [(-0.64, 0.84), (-0.26, 0.81), (-0.19, 0.73), (-0.24, 0.62), (-0.40, 0.55), (-0.64, 0.665)]
    # escape alto (silenciador con protector) bajo el asiento, lado derecho; Tripo lo repitio en el izquierdo (no existe): se quita
    SIL = Y([banda(x, -0.90, -0.58), banda(y, 0.50, 0.90), az - 0.105])
    m.regla("oscuro.escape", Y([SIL, z]), padre="escapeFabrica")
    m.regla("_quitar", Y([SIL, -z]))
    m.regla("asiento.asiento", Y([lado(ASIENTO, az < 0.2), 0.2 - az]))
    CALCAS = [
        {"id": "nombre", "nombre": "Nombre XTZ", "tipo": "texto", "texto": "XTZ150", "zona": ["tanque"], "cara": "lado",
         "en": [0.20, 0.90], "ancho": 0.24, "giro": -9, "color": "gris"},
    ]
    # calca: «XTZ150» en la aleta del tanque (foto oficial); el «YAMAHA» de la tapa no se pone (es la marca)
    m.regla("pintura.tanque", Y([lado(TANQUE, az < 0.22), 0.22 - az]), zonas=["tanque"], calcas_fabrica=CALCAS)
    m.regla("pintura2.tapa_lateral", Y([lado(TAPA, az > 0.05), az - 0.05]), zonas=["lateral"])
    m.regla("plastico.colin", Y([banda(x, -1.05, -0.62), banda(y, 0.84, 1.02), 0.2 - az]))
    placa = {"c": [-0.995, 0.69, 0], "incl": -0.58, "tam": [0.19, 0.095]}
    m.regla("plastico.guardabarros_tras", Y([-0.86 - x, 0.89 - y, 0.07 - az]), placa=placa,
            acomodar=[{"grupo": "accesorios.baul", "ref": "abajo", "a": [-0.8, 1.0, 0]}])

    # --- Mecanica a la vista
    MOTOR = [(-0.22, 0.25), (-0.25, 0.45), (-0.12, 0.53), (-0.05, 0.68), (0.12, 0.68), (0.14, 0.55), (0.2, 0.45), (0.15, 0.25)]
    m.regla("motor.bloque", Y([m.poligono(x, y, MOTOR), 0.16 - az]), pieza="motor")
    m.resto("chasis.chasis")

    # --- Rin delantero de 21": Tripo hizo las dos ruedas iguales (rin a 0,74 del radio exterior; el 21 real va a 0,81
    # y el 18 de atras a 0,69, que ya cuadra). El diametro exterior real es casi igual adelante y atras (llanta delgada
    # adelante, gruesa atras): se estira solo lo de adentro, alrededor del eje, sin mover ejes ni apoyo en el piso.
    RT, D = Rd + 0.03, 0.81 * Rd - AD

    def rin21(P):
        dx, dy = P[:, 0] - xd, P[:, 1] - yd
        r = np.hypot(dx, dy)
        d = np.where(r < 0.06, 0, np.where(r < AD, (r - 0.06) / (AD - 0.06) * D, np.clip((RT - r) / (RT - AD), 0, 1) * D))
        d = d * (np.abs(P[:, 2]) < 0.075)
        f = (r + d) / np.maximum(r, 1e-9)
        P[:, 0], P[:, 1] = xd + dx * f, yd + dy * f
        return P

    m.deformaciones.append(rin21)

    # --- Monoshock (no se ve en la foto: va tras la tapa lateral): barra del bieleta al bastidor bajo el asiento
    import formas
    a0, a1 = np.array([-0.30, 0.44, 0.0]), np.array([-0.24, 0.80, 0.0])
    e = (a1 - a0) / np.linalg.norm(a1 - a0)
    L = float(np.linalg.norm(a1 - a0))
    cuerpo = formas.revolucion([(0, 0), (0.014, 0), (0.014, 0.02), (0.022, 0.03), (0.022, L * 0.55), (0.009, L * 0.58), (0.009, L - 0.03),
                                (0.016, L - 0.02), (0.016, L), (0, L)], a0, e, 18)
    Pc, Nc, Ic = formas.con_normales(formas.unir(cuerpo), 40)
    m.extra["metal.monoshock"] = (Pc, Nc, Ic, {"pieza": "suspension_tras"})
    u = np.cross(e, [0, 0, 1.0]); u /= np.linalg.norm(u); w = np.cross(e, u)
    t = np.linspace(0, 1, 160)
    hel = [a0 + e * (L * (0.10 + 0.78 * tt)) + (u * np.cos(tt * 2 * np.pi * 9) + w * np.sin(tt * 2 * np.pi * 9)) * 0.028 for tt in t]
    Pr, Nr, Ir = formas.con_normales(formas.unir(formas.tubo(hel, 0.0045, 6)), 60)
    m.extra["rojo.resorte_tras"] = (Pr, Nr, Ir, {"pieza": "suspension_tras"})


def internos(k):
    """Rayos X: motor monocilindrico de aire (ciguenal, biela, piston, cilindro), bujia, aceite, bateria y filtro de aire.
    La cadena y el tambor ya vienen a la vista en el modelo. Antes de espejar: +z es el lado del escape."""
    F, pon, cil = k.F, k.pon, k.cil
    C = np.array([-0.05, 0.38, 0.0])                       # eje del ciguenal
    dc = np.array([0.3, 0.95, 0.0])
    dc /= np.linalg.norm(dc)                              # cilindro casi parado, inclinado hacia adelante
    perfil_cig = [(0, -0.05), (0.011, -0.05), (0.011, -0.022), (0.046, -0.022), (0.046, -0.007), (0.013, -0.007),
                  (0.013, 0.007), (0.046, 0.007), (0.046, 0.022), (0.011, 0.022), (0.011, 0.05), (0, 0.05)]
    pon("metal.motor_ciguenal", "motor", F.revolucion(perfil_cig, C, (0, 0, 1), 20), F.tubo([C + dc * 0.03, C + dc * 0.15], 0.0075, 8))
    pon("motor.motor_cilindro", "motor", F.revolucion([(0.029, 0.085), (0.041, 0.085), (0.041, 0.095), (0.052, 0.097), (0.052, 0.101), (0.041, 0.103), (0.041, 0.125), (0.052, 0.127), (0.052, 0.131), (0.041, 0.133), (0.041, 0.155), (0.052, 0.157), (0.052, 0.161), (0.041, 0.163), (0.041, 0.185), (0.052, 0.187), (0.052, 0.191), (0.041, 0.193), (0.041, 0.215), (0.052, 0.217), (0.052, 0.221), (0.041, 0.223), (0.041, 0.24), (0.047, 0.243), (0.047, 0.262), (0.034, 0.278), (0, 0.278)], C, dc, 20))  # aletas: enfriado por aire
    pon("cromo.motor_piston", "motor", F.revolucion([(0, 0.145), (0.0285, 0.145), (0.0285, 0.151), (0.027, 0.153), (0.0285, 0.155), (0.0285, 0.185), (0, 0.187)], C, dc, 20))  # 57,3 mm (aprox.)

    # Bujia: sale de la culata hacia el lado izquierdo y arriba
    db = np.array([0.1, 0.55, -0.83])
    db /= np.linalg.norm(db)
    bb = C + dc * 0.262 + db * 0.012
    pon("metal.bujia_rosca", "bujia", F.revolucion([(0, -0.002), (0.0035, -0.002), (0.0035, 0.002), (0.0062, 0.002), (0.0062, 0.020)], bb, db, 10),
        F.revolucion([(0.0062, 0.020), (0.0105, 0.020), (0.0105, 0.029), (0.0062, 0.029)], bb, db, 6),
        F.revolucion([(0.0, 0.066), (0.0038, 0.066), (0.0038, 0.074), (0, 0.074)], bb, db, 8))
    nerv = [(0.0062, 0.029), (0.0082, 0.031)]
    for i in range(5):
        t0 = 0.034 + i * 0.006
        nerv += [(0.0082, t0), (0.0066, t0 + 0.0015), (0.0066, t0 + 0.0035), (0.0082, t0 + 0.005)]
    nerv += [(0.0060, 0.066), (0, 0.066)]
    pon("bujia.bujia_aislador", "bujia", F.revolucion(nerv, bb, db, 12))
    punta = bb + db * 0.058
    cable = [punta + db * 0.045, punta + db * 0.07 + [-0.01, 0.012, 0], punta + db * 0.08 + [-0.05, 0.03, 0.02], punta + [-0.11, 0.07, 0.05], punta + [-0.17, 0.06, 0.06]]
    pon("oscuro.bujia_capuchon", "bujia", F.revolucion([(0, 0), (0.0115, 0), (0.0125, 0.004), (0.0125, 0.034), (0.008, 0.046), (0, 0.046)], punta, db, 12), F.tubo(cable, 0.0045, 6))

    # Aceite: carter, nivel, tapon de drenaje abajo y tapa de llenado con varilla en la tapa derecha
    carter = F.suave([(-0.15, -0.02), (-0.14, -0.09), (-0.06, -0.115), (0.05, -0.11), (0.09, -0.07), (0.10, -0.02), (0.07, 0.03), (-0.11, 0.03)], 2)
    pon("carter.aceite_carter", "aceite", F.mover(F.extrusion(carter, -0.07, 0.07, 0.014), C))
    nivel = F.suave([(-0.13, -0.058), (-0.125, -0.086), (-0.06, -0.104), (0.045, -0.099), (0.078, -0.07), (0.084, -0.058)], 1)
    pon("aceiteVisible.aceite_nivel", "aceite", F.mover(F.extrusion(nivel, -0.056, 0.056, 0.004), C))
    pon("metal.aceite_tapon", "aceite", F.revolucion([(0, 0), (0.011, 0), (0.011, 0.008), (0.0075, 0.008), (0.0075, 0.016), (0, 0.016)], C + [-0.04, -0.123, 0], (0, 1, 0), 6))  # cabeza abajo, rosca hacia el carter
    pon("metal.aceite_arandela", "aceite", F.revolucion([(0.0078, 0), (0.0125, 0), (0.0125, 0.002), (0.0078, 0.002)], C + [-0.04, -0.115, 0], (0, 1, 0), 12))
    et = np.array([0, 0.45, 1.0])
    et /= np.linalg.norm(et)
    bt = C + [-0.06, 0.0, 0.068]
    pon("oscuro.aceite_tapa", "aceite", F.revolucion([(0, 0), (0.017, 0), (0.017, 0.009), (0.012, 0.011), (0.012, 0.02), (0.0, 0.02)], bt, et, 12),
        F.tubo([bt, bt - et * 0.07], 0.0025, 6))

    # Bateria: bajo la tapa lateral izquierda (12 V sellada chica)
    B = np.array([-0.36, 0.66, -0.075])
    pon("bateria.bat_cuerpo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.115, 0.085, 0.006), -0.03, 0.03, 0.004), B))
    tapa = [F.mover(F.extrusion(F.rect_redondo(0.119, 0.014, 0.004), -0.032, 0.032, 0.003), B + [0, 0.048, 0])]
    pon("oscuro.bat_tapa", "bateria", *tapa)
    pon("metal.bat_bornes", "bateria", *[cil(0.007, 0.012, B + [xx, 0.054, 0.012], (0, 1, 0), 10, 0.002) for xx in (-0.042, 0.042)])
    pon("rojo.bat_positivo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.024, 0.018, 0.005), -0.012, 0.012, 0.003), B + [0.042, 0.066, 0.012]))

    # Filtro de aire: caja bajo la tapa lateral derecha, con ducto de caucho al cuerpo de aceleracion (inyeccion) o carburador; lejos del monoshock y elemento plisado
    caja = F.suave([(-0.40, 0.60), (-0.37, 0.58), (-0.26, 0.58), (-0.235, 0.605), (-0.235, 0.695), (-0.26, 0.72), (-0.37, 0.72), (-0.40, 0.695)], 2)
    pon("oscuro.filtro_caja", "filtro_aire", F.extrusion(caja, 0.05, 0.12, 0.010))
    pon("metal.filtro_tornillos", "filtro_aire", *[cil(0.005, 0.005, (px, py, 0.119), (0, 0, 1), 6) for px, py in ((-0.385, 0.605), (-0.25, 0.605), (-0.25, 0.695), (-0.385, 0.695))])
    pon("caucho.filtro_ductos", "filtro_aire", F.tubo([(-0.24, 0.65, 0.08), (-0.18, 0.65, 0.05), (-0.12, 0.62, 0.02), (-0.085, 0.58, 0.0)], 0.02, 8))
    pon("oscuro.cuerpo_aceleracion", "filtro_aire", F.tubo([(-0.085, 0.58, 0), (-0.035, 0.60, 0)], 0.017, 10))
    pon("caucho.admision", "filtro_aire", F.tubo([(-0.035, 0.60, 0), (-0.005, 0.61, 0)], 0.015, 8))
    n = 9
    xs = np.linspace(-0.385, -0.25, 2 * n + 1)
    zs = np.where(np.arange(2 * n + 1) % 2 == 0, 0.06, 0.105)
    Pp = np.concatenate([np.column_stack([xs, np.full_like(xs, 0.60), zs]), np.column_stack([xs, np.full_like(xs, 0.70), zs])])
    i = np.arange(2 * n)
    mm = 2 * n + 1
    una = np.concatenate([np.stack([i, i + 1, i + 1 + mm], 1), np.stack([i, i + 1 + mm, i + mm], 1)])
    pon("bujia.filtro_elemento", "filtro_aire", (Pp, una), (Pp, una[:, [0, 2, 1]]), pliegue=10)
