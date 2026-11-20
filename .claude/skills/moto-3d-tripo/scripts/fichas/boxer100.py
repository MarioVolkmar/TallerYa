# Ficha de la Bajaj Boxer CT 100 para ciclo.py. Modelo de Tripo SIN textura (49 mil triangulos, solo forma), como la
# NKD: todo por regiones y plantillas con el borde llevado al pliegue. Distancia entre ejes: 1,285 m (Bajaj CT100).
# Coordenadas: x adelante, y arriba, z hacia el escape (lado derecho de la moto).
import numpy as np

from motor import O, Y, banda

EJES = 1.285
MEZCLA = 0.6
ISLAS = {"isla": 24, "isla_pintura": 200, "rigidas": ("llanta", "rin", "aro", "rayos", "_quitar")}
ALISAR = {"pintura.tanque": 10, "plastico.tapa_lateral": 4, "plastico.guardabarros_del": 4, "asiento.asiento": 4, "plastico.colin": 4, "pintura.farola": 3}
# Pintura segun 8 fotos de Galgo (turquesa, negra, negra y morada, Boxer Racing; 19-nov-2026): del color de la moto solo van
# el TANQUE y la FAROLA; tapa lateral (con calca), colin, guardabarros, parrilla y guardacadena son plastico o chasis negro.
SUAVE = 3
PERFIL = False
# Tripo hizo la rueda delantera 10 % mas grande que la trasera (R 0,330 contra 0,299); en la CT 100 las dos son de 17".
# Se escala alrededor de su eje y despues se nivela la moto (giro de ~1,5 grados alrededor del eje trasero) para que las dos
# toquen el piso; exportar.py gira tambien ejes, placa, pantalla y demas extras.
ESCALAR = [{"piezas": ["llanta_del", "aro_del", "rayos_del", "tambor_del"], "eje": "eje_del", "factor": 0.906}]
NIVELAR = True       # (True: imprime el perfil radial de cada rueda para ajustar llanta, aro y rayos)


def cortar(m):
    x, y, z, az = m.x, m.y, m.z, m.az
    xd, yd, Rd, rd = m.rueda(0.61, 0.325, 0.32)
    xt, yt, Rt, rt = m.rueda(-0.655, 0.31, 0.30)
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

    ESCAPE = [(-0.885, 0.44), (-0.85, 0.475), (-0.33, 0.435), (-0.15, 0.33), (0.0, 0.335), (0.06, 0.27), (-0.05, 0.235), (-0.3, 0.265), (-0.87, 0.325)]
    esc = m.poligono(x, y, ESCAPE)

    # --- Ruedas de rayos (rin 17) con freno de tambor adelante y atras
    angd = np.degrees(np.arctan2(y - yd, x - xd))
    m.regla("caucho.llanta_del", Y([rd - (Rd - 0.055), O([Rd + 0.008 - rd, Y([Rd + 0.03 - rd, 20 - angd])]), 0.05 - az]), pieza="llanta_del", eje=[xd, yd])
    m.regla("metal.aro_del", Y([banda(rd, Rd - 0.09, Rd - 0.055), 0.037 - az]), pieza="llanta_del", aro=True, eje=[xd, yd])
    m.regla("metal.tambor_del", Y([0.085 - rd, banda(az, 0.0, 0.075)]), pieza="freno_del")
    m.regla("cromo.rayos_del", Y([Rd - 0.09 - rd, 0.04 - az]), pieza="llanta_del", rin=True, eje=[xd, yd])
    m.regla("caucho.llanta_tras", Y([rt - (Rt - 0.055), Rt + 0.025 - rt, 0.06 - az]), pieza="llanta_tras", eje=[xt, yt])
    m.regla("metal.aro_tras", Y([banda(rt, Rt - 0.09, Rt - 0.055), 0.044 - az]), pieza="llanta_tras", aro=True, eje=[xt, yt])
    m.regla("metal.tambor_tras", Y([0.10 - rt, banda(-z, 0.03, 0.09)]), pieza="freno_tras")
    m.regla("metal.corona", Y([0.12 - rt, banda(z, 0.03, 0.09)]), pieza="cadena")
    m.regla("cromo.rayos_tras", Y([Rt - 0.09 - rt, 0.044 - az]), pieza="llanta_tras", rin=True, eje=[xt, yt])

    # --- Luces. Boxer CT100: farola con faro rectangular bajo un visor corto, direccionales redondas sobre tallo y
    # stop en la punta del colin, sobre el guardafango con la placa.
    FARO = [(0.135, 1.028), (-0.135, 1.028), (-0.125, 0.89), (0.125, 0.89)]
    m.regla("luz.faro", Y([m.pliegue(m.poligono(z, y, FARO), x > 0.45, 0.006), x - 0.47]), lampara={"tipo": "faro"})
    STOP = [(-0.058, 0.865), (0.06, 0.865), (0.07, 0.742), (-0.068, 0.742)]
    m.regla("stop.stop", Y([m.pliegue(m.poligono(z, y, STOP), x < -0.94, 0.006), -0.955 - x]), lampara={"tipo": "stop"})

    def gotas(nombre, cuerpo, hacia):
        xc = float(np.median(x[cuerpo > 0]))
        print(f"{nombre}: x[{x[cuerpo > 0].min():.3f},{x[cuerpo > 0].max():.3f}] centro {xc:.3f} y[{y[cuerpo > 0].min():.3f},{y[cuerpo > 0].max():.3f}] z[{az[cuerpo > 0].min():.3f},{az[cuerpo > 0].max():.3f}]")
        mica = Y([cuerpo, (x - xc) * hacia + 0.004])
        m.regla(f"ambar.{nombre}_a", Y([mica, z]), lampara={"tipo": "direccional"})
        m.regla(f"ambar.{nombre}_b", mica, lampara={"tipo": "direccional"})
        m.regla(f"oscuro.{nombre}_base", cuerpo)

    gotas("direccional_del", Y([banda(x, 0.27, 0.36), banda(y, 0.96, 1.045), banda(az, 0.135, 0.235)]), 1)
    gotas("direccional_tras", Y([banda(x, -0.925, -0.86), banda(y, 0.67, 0.75), banda(az, 0.10, 0.18)]), -1)

    # --- Tren delantero. Guardabarros: cubre arriba y atras de la rueda (de 45 a -150 grados)
    df = m.recta(x, y, (xd, yd), (0.37, 0.98))
    m.regla("cromo.barras", Y([0.03 - df, banda(az, 0.04, 0.12), banda(y, 0.62, 0.86)]), pieza="suspension_del")
    m.regla("metal.horquilla", Y([0.04 - df, banda(az, 0.04, 0.13), 0.62 - y, x - 0.45]), pieza="suspension_del")
    m.regla("plastico.guardabarros_del", Y([Rd + 0.09 - rd, rd - (Rd - 0.08), 0.075 - az, O([angd - 45, -150 - angd]), O([df - 0.042, 0.062 - az]),
                                           # (Tripo pego el guardabarros a la llanta: se separa por el ancho, la llanta no pasa de |z| 0,037, y por la cara
                                           # de adentro, que mira hacia el eje)
                                           O([rd - (Rd + 0.008), az - 0.042, -0.3 - (m.nx * (x - xd) + m.ny * (y - yd)) / np.maximum(rd, 1e-6)])]), zonas=["guardabarros"])

    # --- Manubrio, espejos y farola
    m.regla("espejo.luna", Y([y - 1.27, az - 0.40, -0.35 - m.nx]), padre="espejos.fabrica")
    m.regla("oscuro.espejos", Y([y - 1.15, az - 0.24, 0.45 - x]), padre="espejos.fabrica")
    m.regla("caucho.punos", Y([y - 1.07, 1.21 - y, az - 0.36, 0.45 - x]))
    # Reloj analogo redondo (velocimetro) en el hueco de atras de la farola, bajo el visor: el modelo trae ahi un piso
    # plano (y 1,08, x 0,35-0,48) que mira atras y arriba. Carcasa propia y pantalla asentada encima.
    import formas
    nr = np.array([-0.6, 0.8, 0.0])
    base = np.array([0.425, 1.083, 0.0]) + nr * 0.014
    carcasa = formas.revolucion([(0, -0.03), (0.047, -0.03), (0.047, -0.002), (0.045, 0.0), (0, 0.0)], base, nr, 32)
    Pc, Nc, Ic = formas.con_normales(formas.unir(carcasa), 38)
    m.extra["negro_brillo.reloj"] = (Pc, Nc, Ic, {})
    reloj = [{"c": [round(float(v), 4) for v in base + nr * 0.0012], "n": [round(float(v), 4) for v in nr], "tam": [0.084, 0.084], "redonda": True, "dibujo": "velocimetro"}]
    # (visor ahumado arriba de la farola, como en las fotos; la farola va del color de la moto)
    m.regla("vidrio_oscuro.visor", Y([banda(x, 0.36, 0.60), banda(y, 1.13, 1.24), 0.185 - az]))
    m.regla("pintura.farola", Y([banda(x, 0.36, 0.60), banda(y, 0.86, 1.24), 0.185 - az]), rol="visor_fijo", pantalla=reloj)
    m.regla("oscuro.manubrio", Y([y - 1.04, 0.37 - x]), manubrio={"x": 0.20, "y": 1.10, "extremo": 0.50},
            sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"])

    # --- Carroceria pintada, asiento y cola
    TANQUE = [(-0.235, 0.76), (-0.225, 0.86), (-0.19, 0.905), (-0.05, 0.935), (0.05, 0.968), (0.2, 0.968), (0.27, 0.94), (0.29, 0.87), (0.285, 0.77), (0.26, 0.732), (0.0, 0.744), (-0.2, 0.752)]
    ASIENTO = [(-1.01, 0.885), (-0.85, 0.895), (-0.6, 0.89), (-0.4, 0.878), (-0.26, 0.865), (-0.215, 0.905), (-0.21, 0.80), (-0.24, 0.775), (-0.45, 0.80), (-0.7, 0.815), (-0.9, 0.835), (-1.012, 0.85)]
    TAPA = [(-0.57, 0.725), (-0.46, 0.625), (-0.41, 0.565), (-0.33, 0.555), (-0.215, 0.62), (-0.205, 0.755), (-0.42, 0.79)]
    m.regla("asiento.asiento", Y([lado(ASIENTO, az < 0.2), 0.2 - az]))
    CALCAS = [
        {"id": "franja", "nombre": "Franja del tanque", "tipo": "franja", "forma": "barra", "angosto": 0.6, "zona": ["tanque"], "cara": "lado",
         "en": [0.05, 0.85], "ancho": 0.2, "grueso": 3.0, "giro": 0, "color": "gris"},
        {"id": "nombre", "nombre": "Nombre Boxer", "tipo": "texto", "texto": "BOXER", "zona": ["lateral"], "cara": "lado",
         "en": [-0.36, 0.68], "ancho": 0.11, "giro": 0, "color": "gris"},
    ]
    m.regla("pintura.tanque", Y([lado(TANQUE, az < 0.2), 0.2 - az]), zonas=["tanque"], calcas_fabrica=CALCAS)
    m.regla("plastico.tapa_lateral", Y([lado(TAPA, az > 0.06), az - 0.06]), zonas=["lateral"])
    m.regla("plastico.colin", Y([banda(x, -1.02, -0.55), banda(y, 0.72, 0.89), 0.2 - az, O([0.1 - az, 0.86 - y])]))
    placa = {"c": [-0.975, 0.585, 0], "incl": -0.75, "tam": [0.19, 0.095]}
    m.regla("plastico.guardabarros_tras", Y([-0.90 - x, 0.74 - y, 0.07 - az]), placa=placa,
            acomodar=[{"grupo": "accesorios.baul", "ref": "abajo", "a": [-0.88, 0.96, 0]}])
    m.regla("oscuro.parrilla", Y([-0.78 - x, y - 0.89]))

    # --- Mecanica a la vista
    m.regla("oscuro.escape", Y([esc, z - 0.085]), padre="escapeFabrica")
    AMORT = [(-0.545, 0.735), (-0.48, 0.735), (-0.53, 0.42), (-0.625, 0.42)]
    m.regla("metal.amortiguadores", Y([m.poligono(x, y, AMORT), banda(az, 0.09, 0.20)]), pieza="suspension_tras")
    m.regla("oscuro.guardacadena", Y([banda(x, -0.62, -0.17), banda(y, 0.27, 0.45), -z - 0.06]), pieza="cadena")
    MOTOR = [(-0.20, 0.24), (-0.22, 0.50), (-0.12, 0.60), (-0.05, 0.705), (0.15, 0.705), (0.15, 0.55), (0.09, 0.42), (0.06, 0.24)]
    m.regla("motor.bloque", Y([m.poligono(x, y, MOTOR), 0.18 - az]), pieza="motor")
    m.resto("chasis.chasis")
    # Laminas abiertas de Tripo (llantas, aros, guardabarros): se dibujan por las dos caras; por dentro se veian huecas
    for nombre, extras, _ in m.reglas:
        if any(s in nombre for s in ("llanta", "aro_", "guardabarros", "colin", "tapa_lateral")):
            extras["doble"] = True


def internos(k):
    """Rayos X: motor monocilindrico de aire (ciguenal, biela, piston, cilindro), bujia, aceite, bateria y filtro de aire.
    La cadena y el tambor ya vienen a la vista en el modelo. Antes de espejar: +z es el lado del escape."""
    F, pon, cil = k.F, k.pon, k.cil
    C = np.array([-0.10, 0.42, 0.0])                       # eje del ciguenal
    dc = np.array([0.6, 0.8, 0.0])
    dc /= np.linalg.norm(dc)                              # cilindro casi parado, inclinado hacia adelante
    perfil_cig = [(0, -0.05), (0.011, -0.05), (0.011, -0.022), (0.046, -0.022), (0.046, -0.007), (0.013, -0.007),
                  (0.013, 0.007), (0.046, 0.007), (0.046, 0.022), (0.011, 0.022), (0.011, 0.05), (0, 0.05)]
    pon("metal.motor_ciguenal", "motor", F.revolucion(perfil_cig, C, (0, 0, 1), 20), F.tubo([C + dc * 0.03, C + dc * 0.15], 0.0075, 8))
    pon("motor.motor_cilindro", "motor", F.revolucion([(0.031, 0.085), (0.041, 0.085), (0.041, 0.21), (0.047, 0.213), (0.047, 0.262), (0.034, 0.278), (0, 0.278)], C, dc, 20))
    pon("cromo.motor_piston", "motor", F.revolucion([(0, 0.145), (0.0265, 0.145), (0.0265, 0.151), (0.025, 0.153), (0.0265, 0.155), (0.0265, 0.185), (0, 0.187)], C, dc, 20))

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
    pon("metal.aceite_tapon", "aceite", F.revolucion([(0, 0), (0.011, 0), (0.011, 0.008), (0.0075, 0.008), (0.0075, 0.016), (0, 0.016)], C + [-0.04, -0.112, 0], (0, -1, 0), 6))
    et = np.array([0, 0.45, 1.0])
    et /= np.linalg.norm(et)
    bt = C + [-0.06, 0.0, 0.068]
    pon("oscuro.aceite_tapa", "aceite", F.revolucion([(0, 0), (0.017, 0), (0.017, 0.009), (0.012, 0.011), (0.012, 0.02), (0.0, 0.02)], bt, et, 12),
        F.tubo([bt, bt - et * 0.07], 0.0025, 6))

    # Bateria: bajo la tapa lateral izquierda (12 V sellada chica)
    B = np.array([-0.34, 0.64, -0.075])
    pon("bateria.bat_cuerpo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.115, 0.085, 0.006), -0.03, 0.03, 0.004), B))
    tapa = [F.mover(F.extrusion(F.rect_redondo(0.119, 0.014, 0.004), -0.032, 0.032, 0.003), B + [0, 0.048, 0])]
    pon("oscuro.bat_tapa", "bateria", *tapa)
    pon("metal.bat_bornes", "bateria", *[cil(0.007, 0.012, B + [xx, 0.054, 0.012], (0, 1, 0), 10, 0.002) for xx in (-0.042, 0.042)])
    pon("rojo.bat_positivo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.024, 0.018, 0.005), -0.012, 0.012, 0.003), B + [0.042, 0.066, 0.012]))

    # Filtro de aire: caja bajo la tapa lateral derecha, con ducto de caucho al carburador y elemento plisado
    caja = F.suave([(-0.40, 0.60), (-0.37, 0.58), (-0.24, 0.58), (-0.21, 0.605), (-0.21, 0.695), (-0.24, 0.72), (-0.37, 0.72), (-0.40, 0.695)], 2)
    pon("oscuro.filtro_caja", "filtro_aire", F.extrusion(caja, 0.03, 0.10, 0.010))
    pon("metal.filtro_tornillos", "filtro_aire", *[cil(0.005, 0.005, (px, py, 0.099), (0, 0, 1), 6) for px, py in ((-0.385, 0.605), (-0.225, 0.605), (-0.225, 0.695), (-0.385, 0.695))])
    pon("caucho.filtro_ductos", "filtro_aire", F.tubo([(-0.215, 0.65, 0.06), (-0.17, 0.65, 0.04), (-0.12, 0.62, 0.02), (-0.085, 0.58, 0.0)], 0.02, 8))
    # Carburador entre el ducto del filtro y la culata (revision de la skill mecanico: faltaba; cotas estimadas, 18-20 mm)
    pon("metal.carburador", "filtro_aire", F.tubo([(-0.085, 0.58, 0), (-0.03, 0.60, 0)], 0.02, 10), F.tubo([(-0.03, 0.60, 0), (0.01, 0.64, 0)], 0.016, 8))
    n = 9
    xs = np.linspace(-0.385, -0.225, 2 * n + 1)
    zs = np.where(np.arange(2 * n + 1) % 2 == 0, 0.04, 0.085)
    Pp = np.concatenate([np.column_stack([xs, np.full_like(xs, 0.60), zs]), np.column_stack([xs, np.full_like(xs, 0.70), zs])])
    i = np.arange(2 * n)
    mm = 2 * n + 1
    una = np.concatenate([np.stack([i, i + 1, i + 1 + mm], 1), np.stack([i, i + 1 + mm, i + mm], 1)])
    pon("bujia.filtro_elemento", "filtro_aire", (Pp, una), (Pp, una[:, [0, 2, 1]]), pliegue=10)
