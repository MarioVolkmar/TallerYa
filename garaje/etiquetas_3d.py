"""Etiquetas de las partes de los modelos 3D de Tripo (página /garaje/etiquetar-3d/, solo staff).

El usuario dice qué pieza es cada parte de un GLB despiezado y su acabado. Cada moto etiquetada queda en
garaje/etiquetas_3d/<modelo>.json y alimenta el glosario (garaje/etiquetas_3d/glosario.json), del que salen las
sugerencias de la siguiente moto: por nombre de la parte y por su posición y forma dentro de la moto.
"""
import json
import re
from pathlib import Path

from django.conf import settings

from .deduccion_3d import deducir, normalizar

CARPETA = Path(__file__).resolve().parent / "etiquetas_3d"
MODELOS_STATIC = Path(__file__).resolve().parent / "static" / "garaje" / "modelos"
# GLB de Tripo sin convertir: solo en local (privado/ nunca va al repo ni a producción)
TRIPO_LOCAL = Path(settings.BASE_DIR) / "privado" / "tripo"

ACABADOS = [
    ("pintura", "Pintura principal"),
    ("pintura_secundaria", "Pintura secundaria"),
    ("plastico_mate", "Plástico negro mate"),
    ("plastico_brillo", "Plástico negro brillante"),
    ("cromo", "Cromo"),
    ("aluminio", "Aluminio"),
    ("caucho", "Caucho"),
    ("vinilo", "Vinilo (asiento)"),
    ("mica_faro", "Mica de faro"),
    ("mica_ambar", "Mica ámbar"),
    ("mica_roja", "Mica roja"),
    ("motor", "Motor"),
    ("chasis", "Chasis"),
    ("oculta", "Oculta"),
]

PIEZAS = [
    ("llanta_del", "Llanta delantera"), ("llanta_tras", "Llanta trasera"),
    ("rin_del", "Rin delantero"), ("rin_tras", "Rin trasero"),
    ("disco_del", "Disco de freno delantero"), ("freno_tras", "Freno trasero (disco o tambor)"),
    ("guardabarros_del", "Guardabarros delantero"), ("guardabarros_tras", "Guardabarros trasero"),
    ("tanque", "Tanque"), ("asiento", "Asiento"), ("colin", "Colín"), ("tapa_lateral", "Tapa lateral"),
    ("carenado", "Carenado"), ("frente", "Frente o farola"), ("visor", "Visor o parabrisas"),
    ("escudo", "Escudo (scooter)"), ("pisadera", "Pisadera"), ("bajos", "Bajos o quilla"),
    ("faro", "Faro"), ("stop", "Stop"), ("direccional", "Direccional"), ("tablero", "Tablero"),
    ("manubrio", "Manubrio"), ("puno", "Puño"), ("manigueta", "Manigueta"), ("espejo", "Espejo"),
    ("horquilla", "Horquilla"), ("amortiguador", "Amortiguador"), ("basculante", "Basculante"),
    ("motor", "Motor"), ("cvt", "Tapa de la CVT"), ("escape", "Escape"), ("protector_escape", "Protector del escape"),
    ("chasis", "Chasis"), ("guardacadena", "Guardacadena"), ("cadena", "Cadena y piñones"),
    ("posapies", "Posapiés"), ("pata", "Pata lateral o central"), ("portaplaca", "Portaplaca"),
    ("parrilla", "Parrilla"), ("radiador", "Radiador"), ("otra", "Otra"), ("basura", "Resto suelto (quitar)"),
]

CLAVES_PIEZA = {k for k, _ in PIEZAS}
CLAVES_ACABADO = {k for k, _ in ACABADOS}
NOMBRE_VALIDO = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,80}$")


def modelos():
    """{modelo: ruta del GLB}: los del visor (static) y, en local, los de Tripo sin convertir."""
    rutas = {p.stem: p for p in sorted(MODELOS_STATIC.glob("*.glb"))}
    if TRIPO_LOCAL.is_dir():
        for p in sorted(TRIPO_LOCAL.glob("**/*.glb")):
            rutas.setdefault(p.stem.lower(), p)
    return {k: v for k, v in rutas.items() if NOMBRE_VALIDO.match(k)}


def ruta_etiquetas(modelo):
    return CARPETA / f"{modelo}.json"


def leer_json(ruta, vacio):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return vacio


def etiquetas(modelo):
    return leer_json(ruta_etiquetas(modelo), {"modelo": modelo, "partes": []})


def glosario():
    return leer_json(CARPETA / "glosario.json", {"entradas": []})


def limpiar_zonas(zonas, frases=None):
    """Zonas pintadas sobre una parte: [{grupo 1-4, texto, vertices [[a, b], ...]}] + lo deducido del texto de cada una."""
    if not zonas:
        return []
    if not isinstance(zonas, list) or len(zonas) > 9:
        raise ValueError("zonas inválidas")
    limpias = []
    for z in zonas:
        grupo = z.get("grupo") if isinstance(z, dict) else None
        rangos = z.get("vertices") if isinstance(z, dict) else None
        if grupo not in range(0, 9) or not isinstance(rangos, list) or len(rangos) > 20000:
            raise ValueError("zona inválida")
        r = []
        for par in rangos:
            if not (isinstance(par, list) and len(par) == 2 and all(isinstance(x, int) and 0 <= x < 10**7 for x in par) and par[0] <= par[1]):
                raise ValueError("rango de vértices inválido")
            r.append(par)
        texto = str(z.get("texto", "")).strip()[:200]
        d = deducir(texto, frases) if texto else {"pieza": None, "acabado": None, "por_revisar": True}
        limpias.append({"grupo": grupo, "texto": texto, "vertices": r, "pieza": d["pieza"] or "otra",
                        "acabado": d["acabado"] or "plastico_mate", "por_revisar": d["por_revisar"]})
    return limpias


def limpiar_partes(partes, frases=None):
    """Valida lo que manda la página: lista de {parte, pieza, acabado, pos[3], tam[3]} con valores conocidos."""
    if not isinstance(partes, list) or len(partes) > 2000:
        raise ValueError("lista de partes inválida")
    limpias = []
    for p in partes:
        if not isinstance(p, dict):
            raise ValueError("parte inválida")
        nombre = str(p.get("parte", ""))[:120]
        texto = str(p.get("texto", "")).strip()[:200]
        pieza, acabado = p.get("pieza"), p.get("acabado")
        por_revisar = False
        if texto and p.get("editado"):
            # el usuario escribió con sus palabras: se deduce; lo que no se entiende queda «por revisar», sin inventar
            d = deducir(texto, frases)
            por_revisar = d["por_revisar"]
            pieza = d["pieza"] or "otra"
            acabado = d["acabado"] or (acabado if acabado in CLAVES_ACABADO else "plastico_mate")
        if pieza not in CLAVES_PIEZA or acabado not in CLAVES_ACABADO or not nombre:
            raise ValueError(f"pieza o acabado desconocido en {nombre!r}")
        vec = lambda v: [round(float(x), 3) for x in v][:3] if isinstance(v, list) and len(v) == 3 else None
        zonas = limpiar_zonas(p.get("zonas"), frases)
        limpias.append({"parte": nombre, "texto": texto, "zonas": zonas, "mezclada": len(zonas) > 1, "por_revisar": por_revisar, "pieza": pieza, "acabado": acabado, "pos": vec(p.get("pos")), "tam": vec(p.get("tam")),
                        "confirmada": bool(p.get("confirmada"))})
    return limpias


def guardar(modelo, partes):
    """Escribe las etiquetas de la moto y rehace el glosario con todas las motos etiquetadas."""
    CARPETA.mkdir(exist_ok=True)
    frases = {f["texto"]: f for f in glosario().get("frases", [])}
    datos = {"modelo": modelo, "partes": limpiar_partes(partes, frases)}
    ruta_etiquetas(modelo).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    entradas, frases = [], {}
    for archivo in sorted(CARPETA.glob("*.json")):
        if archivo.name == "glosario.json":
            continue
        d = leer_json(archivo, {})
        for p in d.get("partes", []):
            t = normalizar(p.get("texto", ""))
            if p.get("confirmada") and t and not p.get("por_revisar"):
                frases[t] = {"texto": t, "pieza": p["pieza"], "acabado": p["acabado"]}  # el glosario aprende la frase
            for z in p.get("zonas", []):
                tz = normalizar(z.get("texto", ""))
                if p.get("confirmada") and tz and not z.get("por_revisar"):
                    frases[tz] = {"texto": tz, "pieza": z["pieza"], "acabado": z["acabado"]}
            if p.get("confirmada") and p.get("pos") and p.get("tam"):
                entradas.append({"modelo": d.get("modelo", archivo.stem), "parte": p["parte"], "pieza": p["pieza"],
                                 "acabado": p["acabado"], "pos": p["pos"], "tam": p["tam"]})
    (CARPETA / "glosario.json").write_text(json.dumps({"entradas": entradas, "frases": list(frases.values())}, ensure_ascii=False, indent=1), encoding="utf-8")
    return datos, len(entradas)
