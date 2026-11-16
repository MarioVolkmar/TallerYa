# Arma la v2 de una lámina (fig. 22 o 12) desde su v1 (datos/<lamina>-v1.json) y los textos v2 (v2-textos-<lamina>.json).
# Uso: python armar_v2.py nmax-fig22   →   datos/nmax-fig22.json (la v1 queda como respaldo nmax-fig22-v1.json)
# Los grupos, la tornillería y el 3D se definen abajo; los textos vienen del JSON de textos (revisados a mano).
import json, pathlib, shutil, sys

AQUI = pathlib.Path(__file__).resolve().parent
M = AQUI.parent / "motor"
LAM = sys.argv[1]
v1p, out = M / f"datos/{LAM}-v1.json", M / f"datos/{LAM}.json"
if not v1p.exists():
    shutil.copy(out, v1p)
D = json.loads(v1p.read_text(encoding="utf-8"))
T = json.loads((AQUI / f"v2-textos-{LAM}.json").read_text(encoding="utf-8"))
CAT = {p["ref"]: p for p in json.loads((M / f"catalogo/{D['catalogo']}.json").read_text(encoding="utf-8"))["figuras"][str(D["figura"])]["partes"]}

def tn(nombre, corto, ids, cant): return {"nombre": nombre, "corto": corto, "ids": ids, "cant": cant}

GRUPOS = {
 "nmax-fig22": [
  {"id": "disco", "nombre": "Disco", "piezas": ["1"], "torn": [tn("Tornillos del disco", "Tornillos", ["2"], 3)], "pasos": [12, 13], "marca": [650, 500]},
  {"id": "caliper", "nombre": "Cáliper", "piezas": ["3", "4", "5a", "5b", "6", "7", "8", "13"],
   "torn": [tn("Tornillos del soporte", "Tornillos", ["15"], 2)], "pasos": [0, 1, 7, 8, 9, 10, 11], "marca": [450, 290]},
  {"id": "pastillas", "nombre": "Pastillas", "piezas": ["9a", "9b", "14", "11", "12", "10a", "10b"], "torn": [], "pasos": [1, 2, 3, 4, 5, 6], "marca": [370, 440]},
 ],
 "nmax-fig12": [
  {"id": "tapa", "nombre": "Tapa", "piezas": ["30", "31", "32"], "torn": [], "pasos": [0], "marca": [470, 560]},
  {"id": "variador", "nombre": "Variador", "piezas": ["6", "33", "1", "2", "3", "4", "5", "26"],
   "torn": [tn("Tuerca y arandela del variador", "Tuerca", ["28", "27"], 2)], "pasos": [1, 2, 6, 7, 8, 9, 10]},
  {"id": "correa", "nombre": "Correa", "piezas": ["25"], "torn": [], "pasos": [4, 5]},
  {"id": "campana", "nombre": "Campana", "piezas": ["24"], "torn": [tn("Tuerca de la campana", "Tuerca", ["29"], 1)], "pasos": [3], "marca": [690, 470]},
  {"id": "clutch", "nombre": "Clutch y polea trasera", "corto": "Clutch",
   "piezas": ["7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "21", "22", "23"],
   "torn": [tn("Tuerca del portazapatas", "Tuerca", ["20"], 1)], "pasos": [4, 11, 12, 13, 14], "marca": [620, 345]},
 ],
}
TOQUE = {"nmax-fig22": ["10a", "12"], "nmax-fig12": []}   # piezas chicas: círculo de toque invisible
CON3D = {"nmax-fig22": [], "nmax-fig12": ["13", "23", "24", "25"]}
INICIO = {"nmax-fig22": "Piezas del freno delantero", "nmax-fig12": "Piezas de la CVT"}

CAMPOS = ["que", "sirve", "sintomas", "fallas", "decision", "porque", "dif", "cuando", "arrastra", "certezaDe"]
for k, F in D["fichas"].items():
    t = T["fichas"][k]
    for c in CAMPOS:
        if c in t: F[c] = t[c]
    if t.get("nombre"):
        F["nombre"] = t["nombre"]
        if k in D.get("nombres", {}): D["nombres"][k] = t["nombre"]
    for c in ("efectos", "compra"):
        F.pop(c, None)
    if k in CAT and CAT[k].get("codigo") and not F.get("ctx"):
        F["codigo"] = CAT[k]["codigo"]
for i, p in enumerate(D["pasos"]):
    p["t"] = T["pasos"][str(i)]
D["textoArmado"] = T.get("textoArmado", D["textoArmado"])
D["cadenas"] = T["cadenas"]
for i, t in T.get("funciona", {}).items():   # «Cómo funciona» sin «(N)»
    D["funciona"]["pasos"][int(i)]["t"] = t
for c in T["cuando"]:
    D["cuando"][c["i"]].update(que=c["que"], cuando=c["cuando"])
if LAM == "nmax-fig22":   # el pasador va después de las grapas: su círculo de toque no queda tapado por el de la grapa
    pz = D["piezas"]; i12 = next(i for i, p in enumerate(pz) if p["id"] == "12"); p12 = pz.pop(i12)
    pz.insert(next(i for i, p in enumerate(pz) if p["id"] == "10b") + 1, p12)
D["v2"] = {"deriva": f"{LAM}-v1.json", "grupos": GRUPOS[LAM], "con3d": CON3D[LAM], "inicio": INICIO[LAM], "toqueExtra": TOQUE[LAM]}
out.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
print(out.name, len(D["fichas"]), "fichas")
