# Ficha de la AKT NKD 125 para ciclo.py. Modelo de Tripo SIN textura (47 mil triangulos, solo forma): todas las
# reglas son regiones y plantillas, con el borde llevado al pliegue del modelo. Distancia entre ejes: 1,27 m.
# Coordenadas: x adelante, y arriba, z hacia el escape (lado derecho de la moto).
import numpy as np

from motor import O, Y, banda

EJES = 1.27          # (para preparar.py)
MEZCLA = 0.6
ISLAS = {"isla": 24, "isla_pintura": 200, "rigidas": ("llanta", "rin", "aro", "rayos", "_quitar")}
ALISAR = {"pintura.tanque": 10, "pintura2.tapa_lateral": 4, "pintura.guardabarros_del": 4, "asiento.asiento": 4}
SUAVE = 3            # (vueltas de alisado de normales en pintura y lentes: el tanque llega con grano y facetas)


def cortar(m):
    x, y, z, az = m.x, m.y, m.z, m.az
    xd, yd, Rd, rd = m.rueda(0.635, 0.30)
    xt, yt, Rt, rt = m.rueda(-0.645, 0.31)
    m.medidas.update(eje_del=[xd, yd], eje_tras=[xt, yt], R_del=Rd, R_tras=Rt)
    print(f"ruedas del ({xd:.3f},{yd:.3f}) R={Rd:.3f}  tras ({xt:.3f},{yt:.3f}) R={Rt:.3f}")

    def lado(pol, valido=None, ancho=0.01):
        """Plantilla dibujada en la vista lateral (x, y), con el borde llevado al pliegue."""
        d = m.poligono(x, y, pol)
        return m.pliegue(d, np.ones(len(x), bool) if valido is None else valido, ancho)

    # --- Ruedas de rayos (rin 18): llanta, aro y rayos con su manzana; disco adelante (lado +z) y tambor atras
    m.regla("_quitar", Y([0.128 - rd, rd - 0.052, banda(z, 0.034, 0.057)]))
    m.disco("disco.disco_del", xd, yd, 0.045, 0.122, "freno_del", interior=0.55)
    # La rueda del modelo no es un circulo perfecto: arriba la banda de rodadura llega a R + 0,02 y con el tope en
    # R + 0,008 ese pedazo caia en el guardabarros (se pintaba con la moto). Fuera del guardabarros (por delante de
    # su punta, angulo < 50 grados) el tope es holgado; debajo de el, la llanta es la corona (|z| < 0,037) que mira hacia afuera del eje;
    # el guardabarros por dentro mira hacia el eje y sus faldas quedan mas afuera en z.
    ang = np.degrees(np.arctan2(y - yd, x - xd))
    afuera = (m.nx * (x - xd) + m.ny * (y - yd)) / np.maximum(rd, 1e-6)
    tope = O([Rd + 0.008 - rd, Y([Rd + 0.03 - rd, 50 - ang]), Y([Rd + 0.027 - rd, afuera - 0.5, 0.037 - az, 135 - ang])])
    m.regla("caucho.llanta_del", Y([rd - 0.247, tope, 0.05 - az]), pieza="llanta_del", eje=[xd, yd])
    # (aro aparte de rayos y manzana: como en la moto generica, el color de rines de Personalizar pinta solo el aro
    # y los rayos siguen cromados; con todo junto en "rin" el color se regaba por toda la rueda)
    m.regla("metal.aro_del", Y([banda(rd, 0.213, 0.247), 0.037 - az]), pieza="llanta_del", aro=True, eje=[xd, yd])
    m.regla("cromo.rayos_del", Y([0.213 - rd, 0.037 - az]), pieza="llanta_del", rin=True, eje=[xd, yd])
    m.regla("caucho.llanta_tras", Y([rt - 0.252, Rt + 0.025 - rt, 0.056 - az]), pieza="llanta_tras", eje=[xt, yt])
    m.regla("metal.aro_tras", Y([banda(rt, 0.205, 0.252), 0.044 - az]), pieza="llanta_tras", aro=True, eje=[xt, yt])
    m.regla("cromo.rayos_tras", Y([0.205 - rt, 0.044 - az]), pieza="llanta_tras", rin=True, eje=[xt, yt])
    m.regla("oscuro.mordaza_del", Y([banda(x, 0.48, 0.60), banda(y, 0.29, 0.41), banda(z, 0.03, 0.12), 0.21 - rd]), pieza="freno_del")
    m.regla("metal.tambor_tras", Y([0.14 - rt, banda(z, 0.044, 0.085)]), pieza="freno_tras")
    m.regla("metal.corona", Y([0.14 - rt, banda(-z, 0.044, 0.085)]), pieza="cadena")

    # --- Luces. NKD real (fotos AKT y manual): farola redonda con aro, stop rectangular bajo la cola y cuatro
    # direccionales de gota con mica ambar sobre tallo negro. La mica es la mitad que mira hacia afuera del eje de la moto.
    FARO_C = (0.0, 0.885)
    # (sin pliegue: el lente trae relieve por dentro y el borde se iba a una de esas aristas)
    lente = Y([m.circulo_plantilla(z, y, FARO_C, 0.084), x - 0.50])
    m.regla("luz.faro", lente, lampara={"tipo": "faro"})
    m.regla("cromo.aro_faro", Y([m.circulo_plantilla(z, y, FARO_C, 0.099), x - 0.515]))
    STOP = [(-0.066, 0.762), (0.066, 0.762), (0.064, 0.83), (0.05, 0.842), (-0.05, 0.842), (-0.064, 0.83)]
    m.regla("stop.stop", Y([m.pliegue(m.poligono(z, y, STOP), x < -0.86, 0.006), -0.9 - x, x + 0.975]), lampara={"tipo": "stop"})

    def gotas(nombre, cuerpo, hacia):
        """Direccional de gota: la mitad del cuerpo que mira hacia `hacia` (+1 adelante, -1 atras) es la mica."""
        xc = float(np.median(x[cuerpo > 0]))
        print(f"{nombre}: x[{x[cuerpo > 0].min():.3f},{x[cuerpo > 0].max():.3f}] centro {xc:.3f} y[{y[cuerpo > 0].min():.3f},{y[cuerpo > 0].max():.3f}]")
        mica = Y([cuerpo, (x - xc) * hacia + 0.004])
        m.regla(f"ambar.{nombre}_a", Y([mica, z]), lampara={"tipo": "direccional"})
        m.regla(f"ambar.{nombre}_b", mica, lampara={"tipo": "direccional"})
        m.regla(f"oscuro.{nombre}_base", cuerpo)

    gotas("direccional_del", Y([banda(x, 0.30, 0.50), banda(y, 0.825, 0.912), az - 0.15]), 1)
    gotas("direccional_tras", Y([banda(x, -0.87, -0.76), banda(y, 0.68, 0.76), az - 0.10]), -1)
    m.regla("reflector.reflector_del", Y([banda(x, 0.40, 0.53), banda(y, 0.75, 0.83), banda(az, 0.125, 0.21)]))

    # --- Tren delantero
    df = m.recta(x, y, (xd, yd), (0.435, 0.92))
    m.regla("metal.horquilla", Y([0.04 - df, banda(az, 0.08, 0.14), 0.60 - y, x - 0.5]), pieza="suspension_del")
    m.regla("cromo.barras", Y([0.03 - df, banda(az, 0.07, 0.14), banda(y, 0.60, 0.78)]), pieza="suspension_del")
    m.regla("pintura.guardabarros_del", Y([O([rd - (Rd + 0.008), Y([rd - 0.2, az - 0.05])]), Rd + 0.08 - rd, 0.088 - az, y - 0.27, ang - 48, O([df - 0.042, 0.062 - az]),
                                           # (la manguera del freno baja por fuera de la falda trasera, a |z| > 0,06: no es guardabarros)
                                           O([0.06 - az, y - 0.60, x - 0.52])]), zonas=["guardabarros"])

    # --- Manubrio, espejos, relojes y farola
    arriba = Y([y - 0.955, 0.42 - x])
    m.regla("espejo.luna", Y([y - 1.13, az - 0.24, -0.35 - m.nx]), padre="espejos.fabrica")
    m.regla("oscuro.espejos", Y([y - 1.085, az - 0.2]), padre="espejos.fabrica")
    m.regla("caucho.punos", Y([arriba, az - 0.40, 1.07 - y]))
    m.regla("oscuro.manubrio", arriba, manubrio={"x": 0.25, "y": 1.0, "extremo": 0.52},
            sin=["accesorios.parabrisas", "accesorios.cubremanos", "espejos.redondos", "espejos.puntas"])
    # Dos relojes redondos digitales (foto AKT): velocimetro a la izquierda del piloto (-z antes de espejar) y
    # tacometro a la derecha. Cara medida en la malla: centro (0.416, 1.047, +-0.055), normal (-0.43, 0.90, 0).
    nr = np.array([-0.43, 0.90, 0.0]) / np.hypot(0.43, 0.90)
    # La cara que trae el modelo es un domo irregular de 2 cm: una pantalla plana encima quedaba en el aire. Cada reloj
    # lleva su carcasa cilindrica (pieza nueva) que sale del domo, y la pantalla va asentada sobre ella.
    import formas
    ALTO = 0.022
    relojes = []
    for zz, dib, letra in ((-0.055, "velocimetro", "a"), (0.055, "tacometro", "b")):
        base = np.array([0.416, 1.047, zz]) + nr * ALTO
        carcasa = formas.revolucion([(0, -0.045), (0.0415, -0.045), (0.0415, -0.002), (0.0395, 0.0), (0, 0.0)], base, nr, 28)
        Pc, Nc, Ic = formas.con_normales(formas.unir(carcasa), 38)
        m.extra[f"negro_brillo.reloj_{letra}"] = (Pc, Nc, Ic, {})
        relojes.append({"c": [round(float(v), 4) for v in base + nr * 0.0012], "n": [round(float(v), 4) for v in nr],
                        "tam": [0.074, 0.074], "redonda": True, "dibujo": dib})
    m.regla("oscuro.relojes", Y([banda(x, 0.36, 0.60), y - 0.985, 0.14 - az]), pantalla=relojes)
    # (rol visor_fijo: sin el, queda a la vista el visor transparente de la moto generica atravesando la farola)
    m.regla("oscuro.farola", Y([banda(x, 0.44, 0.62), banda(y, 0.79, 1.0), 0.13 - az]), rol="visor_fijo")

    # --- Carroceria pintada, asiento y cola
    TANQUE = [(-0.225, 0.715), (-0.215, 0.82), (-0.13, 0.885), (0.05, 0.905), (0.28, 0.90), (0.355, 0.865), (0.38, 0.80), (0.34, 0.72), (0.28, 0.688), (0.0, 0.688), (-0.2, 0.70)]
    ASIENTO = [(-0.875, 0.905), (-0.85, 0.80), (-0.60, 0.742), (-0.25, 0.703), (-0.213, 0.71), (-0.208, 0.80), (-0.24, 0.835), (-0.55, 0.885), (-0.80, 0.905)]
    TAPA = [(-0.50, 0.705), (-0.415, 0.565), (-0.30, 0.51), (-0.19, 0.50), (-0.11, 0.625), (-0.05, 0.70)]
    m.regla("asiento.asiento", Y([lado(ASIENTO, az < 0.22), 0.22 - az]))
    # Calcas de fabrica ubicadas sobre este modelo (en: [x, y]): con la posicion relativa de la linea generica, la
    # flecha se salia por la punta del tanque y quedaba en el aire. Foto AKT: bloque oscuro en punta con barra lima
    # en el costado alto del tanque; barra lima y "NKD" chico en la tapa lateral.
    CALCAS = [
        {"id": "flecha", "nombre": "Flecha del tanque", "tipo": "franja", "forma": "flecha", "angosto": 0.4, "zona": ["tanque"], "cara": "lado",
         "en": [0.07, 0.845], "ancho": 0.13, "giro": 0, "color": "vivo:#c6e23a", "color2": "#1b1e20"},
        {"id": "barra", "nombre": "Barra lateral", "tipo": "franja", "forma": "barra", "angosto": 0.6, "zona": ["lateral"], "cara": "lado",
         "en": [-0.25, 0.65], "ancho": 0.15, "grueso": 3.5, "giro": 0, "color": "vivo:#c6e23a"},
        {"id": "nombre", "nombre": "Nombre NKD", "tipo": "texto", "texto": "NKD", "zona": ["lateral"], "cara": "lado",
         "en": [-0.26, 0.59], "ancho": 0.085, "giro": 0, "color": "gris"},
    ]
    m.regla("pintura.tanque", Y([lado(TANQUE, az < 0.22), 0.22 - az]), zonas=["tanque"], calcas_fabrica=CALCAS)
    m.regla("pintura2.tapa_lateral", Y([lado(TAPA, az > 0.07), az - 0.07]), zonas=["lateral"])
    placa = {"c": [-0.978, 0.68, 0], "incl": -0.75, "tam": [0.19, 0.095]}
    m.regla("plastico.guardabarros_tras", Y([-0.86 - x, 0.775 - y, 0.13 - az]), placa=placa,
            acomodar=[{"grupo": "accesorios.baul", "ref": "abajo", "a": [-0.9, 0.9, 0]}])
    m.regla("oscuro.agarradera", Y([-0.72 - x, y - 0.74, az - 0.10]))

    # --- Mecanica a la vista
    ESCAPE = [(-0.93, 0.36), (-0.90, 0.45), (-0.30, 0.375), (-0.05, 0.315), (0.02, 0.30), (0.02, 0.22), (-0.3, 0.26), (-0.9, 0.325)]
    m.regla("oscuro.escape", Y([m.poligono(x, y, ESCAPE), z - 0.09]), padre="escapeFabrica")
    AMORT = [(-0.565, 0.725), (-0.47, 0.725), (-0.49, 0.58), (-0.53, 0.43), (-0.61, 0.43), (-0.585, 0.58)]
    m.regla("metal.amortiguadores", Y([m.poligono(x, y, AMORT), banda(az, 0.095, 0.21)]), pieza="suspension_tras")
    m.regla("oscuro.guardacadena", Y([banda(x, -0.66, -0.17), banda(y, 0.27, 0.47), -z - 0.06]), pieza="cadena")
    MOTOR = [(-0.205, 0.30), (-0.205, 0.56), (-0.09, 0.60), (-0.07, 0.688), (0.21, 0.688), (0.21, 0.56), (0.125, 0.44), (0.085, 0.30), (0.05, 0.255), (-0.12, 0.255)]
    m.regla("motor.bloque", Y([m.poligono(x, y, MOTOR), 0.19 - az]), pieza="motor")
    m.resto("chasis.chasis")


def internos(k):
    """Rayos X: motor monocilindrico de aire (ciguenal, biela, piston, cilindro), bujia, aceite, bateria y filtro de aire.
    La cadena y el tambor ya vienen a la vista en el modelo. Antes de espejar: +z es el lado del escape."""
    F, pon, cil = k.F, k.pon, k.cil
    C = np.array([0.0, 0.385, 0.0])                       # eje del ciguenal
    dc = np.array([0.37, 0.93, 0.0])
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
    B = np.array([-0.30, 0.585, -0.075])
    pon("bateria.bat_cuerpo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.115, 0.085, 0.006), -0.03, 0.03, 0.004), B))
    tapa = [F.mover(F.extrusion(F.rect_redondo(0.119, 0.014, 0.004), -0.032, 0.032, 0.003), B + [0, 0.048, 0])]
    pon("oscuro.bat_tapa", "bateria", *tapa)
    pon("metal.bat_bornes", "bateria", *[cil(0.007, 0.012, B + [xx, 0.054, 0.012], (0, 1, 0), 10, 0.002) for xx in (-0.042, 0.042)])
    pon("rojo.bat_positivo", "bateria", F.mover(F.extrusion(F.rect_redondo(0.024, 0.018, 0.005), -0.012, 0.012, 0.003), B + [0.042, 0.066, 0.012]))

    # Filtro de aire: caja bajo la tapa lateral derecha, con ducto de caucho al carburador y elemento plisado
    caja = F.suave([(-0.40, 0.54), (-0.37, 0.52), (-0.24, 0.52), (-0.21, 0.545), (-0.21, 0.635), (-0.24, 0.66), (-0.37, 0.66), (-0.40, 0.635)], 2)
    pon("oscuro.filtro_caja", "filtro_aire", F.extrusion(caja, 0.03, 0.10, 0.010))
    pon("metal.filtro_tornillos", "filtro_aire", *[cil(0.005, 0.005, (px, py, 0.099), (0, 0, 1), 6) for px, py in ((-0.385, 0.545), (-0.225, 0.545), (-0.225, 0.635), (-0.385, 0.635))])
    pon("caucho.filtro_ductos", "filtro_aire", F.tubo([(-0.215, 0.59, 0.06), (-0.17, 0.59, 0.04), (-0.12, 0.585, 0.02), (-0.085, 0.58, 0.0)], 0.02, 8))
    n = 9
    xs = np.linspace(-0.385, -0.225, 2 * n + 1)
    zs = np.where(np.arange(2 * n + 1) % 2 == 0, 0.04, 0.085)
    Pp = np.concatenate([np.column_stack([xs, np.full_like(xs, 0.54), zs]), np.column_stack([xs, np.full_like(xs, 0.64), zs])])
    i = np.arange(2 * n)
    mm = 2 * n + 1
    una = np.concatenate([np.stack([i, i + 1, i + 1 + mm], 1), np.stack([i, i + 1 + mm, i + mm], 1)])
    pon("bujia.filtro_elemento", "filtro_aire", (Pp, una), (Pp, una[:, [0, 2, 1]]), pliegue=10)
