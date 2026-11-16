"""Cronómetro y métricas de cada lámina (lo usa la skill «hacer-lamina»). Guarda todo en metricas.json, junto a este script.

  python metricas.py nueva <lamina>                         crea el registro (fecha de hoy)
  python metricas.py inicio <lamina> <fase>                 anota la hora de inicio de la fase
  python metricas.py fin <lamina> <fase>                    anota la hora de fin
  python metricas.py dato <lamina> <clave> '<json>'         p. ej. rondas_revision 2 · contexto_creadora '{"inicio":"12%","fin":"48%"}'
                                                             · notas_mecanica '{"fidelidad":5,...,"promedio":4.9}'
  python metricas.py informe <lamina>                        compara con la línea base (CVT) y con el promedio de las demás
  python metricas.py dato <lamina> tokens '{"inicio":N,"fin":N}'   tokens de la sesión (get_usage) o contexto en %: el informe los muestra
Meta (meta_fases en metricas.json): creación 10 min. Al cerrar una fase: ⚠ si pasó su presupuesto (una línea en «explicacion»);
✋ CORTE si pasó del doble: se para ahí, la causa va a «pendientes» del JSON y se sigue con la siguiente fase.

Fases: catalogo, dibujo2d, contenido, 3d, validacion, mediciones, revision_mecanica, revision_ux, correcciones.
Las revisoras cronometran revision_mecanica y revision_ux con este mismo script. Fase aparte, fuera del total: mejora_skill.
Si dos fases corren a la vez (p. ej. el esqueleto en paralelo con el dibujo), el informe muestra el solapamiento y el tiempo de reloj.
Datos: pct_seguro = % de números, nombres y cantidades que cuadran con el catálogo (como en la CVT);
pct_certeza_total = % de todas las marcas de certeza («Seguro» sobre el total); uso_plan lo anota Auxiliares.
«Terminado» = cada nota ≥ la de la línea base; si alguna baja, el informe lo marca y hay que explicarlo en «explicacion».
"""
import datetime as dt, json, pathlib, sys

AQUI = pathlib.Path(__file__).resolve().parent
ARCH = AQUI / "metricas.json"
FASES = ["catalogo", "dibujo2d", "contenido", "3d", "validacion", "mediciones", "revision_mecanica", "revision_ux", "correcciones"]
FASES_EXTRA = ["mejora_skill", "rediseno", "adopcion_v2"]   # se cronometran, pero no suman al total de la lámina
BASE = "nmax-fig12"
TOLERANCIA = 1.25   # una fase «tardó más de lo esperado» si pasa del 125 % de lo esperado


def cargar():
    return json.loads(ARCH.read_text(encoding="utf-8")) if ARCH.exists() else {"base": BASE, "laminas": {}}


def guardar(M):
    ARCH.write_text(json.dumps(M, ensure_ascii=False, indent=1), encoding="utf-8")


def ahora():
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M")


def minutos(f):
    try:
        a, b = (dt.datetime.fromisoformat(f[k]) for k in ("inicio", "fin"))
        return (b - a).total_seconds() / 60
    except (KeyError, TypeError, ValueError):
        return None


def registro(M, lam):
    if lam not in M["laminas"]:
        M["laminas"][lam] = {"lamina": lam, "fecha": dt.date.today().isoformat(), "fases": {},
                             "rondas_revision": 0, "rondas_correccion": 0, "errores_revisoras": {},
                             "piezas_3d": [], "contexto_creadora": {}, "uso_plan": {}, "notas_mecanica": {},
                             "notas_ux": {}, "pct_seguro": None, "pct_certeza_total": None, "pendientes": [], "explicacion": ""}
    return M["laminas"][lam]


def informe(M, lam):
    R, B = M["laminas"][lam], M["laminas"].get(M.get("base", BASE))
    otras = [r for k, r in M["laminas"].items() if k != lam]
    print(f"Informe de {lam} ({R['fecha']})")
    total = 0
    for fase in FASES:
        m = minutos(R["fases"].get(fase, {}))
        if m is None:
            continue
        total += m
        refs = [minutos(r["fases"].get(fase, {})) for r in otras]
        refs = [x for x in refs if x]
        esperado = sum(refs) / len(refs) if refs else None
        base = minutos(B["fases"].get(fase, {})) if B and B is not R else None
        marca = "  ← TARDÓ MÁS DE LO ESPERADO" if esperado and m > esperado * TOLERANCIA else ""
        print(f"  {fase:18} {m:6.0f} min   base {base and round(base) or '-':>4}   promedio {esperado and round(esperado) or '-':>4}{marca}")
    print(f"  {'TOTAL':18} {total:6.0f} min")
    tramos = []
    for fase in FASES:
        F = R["fases"].get(fase, {})
        try: tramos.append((fase, dt.datetime.fromisoformat(F["inicio"]), dt.datetime.fromisoformat(F["fin"])))
        except (KeyError, TypeError, ValueError): pass
    solapes = []
    for i in range(len(tramos)):
        for j in range(i + 1, len(tramos)):
            a, b = tramos[i], tramos[j]
            m = (min(a[2], b[2]) - max(a[1], b[1])).total_seconds() / 60
            if m > 0: solapes.append(f"{a[0]} y {b[0]} {m:.0f} min")
    if solapes:
        reloj = (max(t[2] for t in tramos) - min(t[1] for t in tramos)).total_seconds() / 60
        print(f"  solapamiento: {'; '.join(solapes)} · tiempo de reloj {reloj:.0f} min")
    meta = M.get("creacion_meta_min")
    if meta:   # creación = del catálogo hasta lista para revisión (las revisiones van aparte)
        CREA = ["catalogo", "dibujo2d", "contenido", "3d", "validacion", "mediciones"]
        tc = [t for t in tramos if t[0] in CREA]
        if tc:
            rc = (max(t[2] for t in tc) - min(t[1] for t in tc)).total_seconds() / 60
            dif = rc - meta
            print(f"  CREACIÓN: {rc:.0f} min de reloj · meta {meta}{' sin paralelo' if M.get('sin_paralelo') else ''} → " + (f"sobró {-dif:.0f} min" if dif <= 0 else f"faltó {dif:.0f} min (pasó la meta)"))
            mf = M.get("meta_fases", {})
            fila = []
            for f, mm in mf.items():
                fs = ["validacion", "mediciones"] if f == "verificacion" else [f]
                v = [minutos(R["fases"].get(x, {})) for x in fs]
                v = [x for x in v if x is not None]
                if v: fila.append(f"{f} {sum(v):.0f}/{mm} ({sum(v) - mm:+.0f})")
            if fila: print("  por fase (real/meta): " + " · ".join(fila))
    if R.get("tokens"): print(f"  tokens: {R['tokens']}" + (f" · base {B['tokens']}" if B and B is not R and B.get("tokens") else ""))
    for fase in FASES_EXTRA:
        m = minutos(R["fases"].get(fase, {}))
        if m is not None: print(f"  {fase:18} {m:6.0f} min   (aparte, no suma)")
    if B and B is not R:
        for k in ("rondas_revision", "rondas_correccion"):
            print(f"  {k}: {R[k]} (base {B[k]}){'  ← más que la base' if R[k] > B[k] else ''}")
        bajas = []
        for k in ("notas_mecanica", "notas_ux"):
            for crit, v in R[k].items():
                b = B[k].get(crit)
                if isinstance(v, (int, float)) and isinstance(b, (int, float)) and v < b:
                    bajas.append(f"{k}.{crit} {v} < {b}")
        if R.get("pct_seguro") is not None and B.get("pct_seguro") is not None and R["pct_seguro"] < B["pct_seguro"]:
            bajas.append(f"pct_seguro {R['pct_seguro']} < {B['pct_seguro']}")
        if bajas:
            print("  NOTAS POR DEBAJO DE LA BASE:", "; ".join(bajas))
            print("  " + ("Explicación: " + R["explicacion"] if R.get("explicacion") else "FALTA la explicación: no está terminada."))
        else:
            print("  Notas: todas ≥ la línea base.")


def main(a):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    M = cargar()
    if len(a) < 2:
        print(__doc__); return 1
    orden, lam = a[0], a[1]
    if orden == "nueva":
        registro(M, lam)
    elif orden in ("inicio", "fin"):
        if a[2] not in FASES + FASES_EXTRA:
            print("fase desconocida:", a[2], "· fases:", ", ".join(FASES + FASES_EXTRA)); return 1
        registro(M, lam)["fases"].setdefault(a[2], {})[orden] = ahora()
        if orden == "fin" and a[2] in FASES:   # tope por fase: si pasa del 125 % del promedio, se anota por qué y se sigue
            m = minutos(M["laminas"][lam]["fases"][a[2]])
            refs = [x for x in (minutos(r["fases"].get(a[2], {})) for k, r in M["laminas"].items() if k != lam) if x]
            mm = M.get("meta_fases", {}).get("verificacion" if a[2] in ("validacion", "mediciones") else a[2])
            if m is not None and mm is not None:
                print(f"{a[2]}: {m:.0f} min · meta {mm}" + (f"  ✋ CORTE: pasó del doble. No pulas más esta fase: anota la causa en «pendientes» del JSON y sigue" if m > 2 * mm
                      else f"  ⚠ pasó la meta: anota por qué en una línea (dato {lam} explicacion) y sigue" if m > mm else "  ✓"))
            elif m is not None and refs:
                esp = sum(refs) / len(refs)
                print(f"{a[2]}: {m:.0f} min (promedio {esp:.0f})" + (f"  ⚠ pasó del 125 %: anota por qué con «dato {lam} explicacion …» y sigue" if m > esp * TOLERANCIA else ""))
        if orden == "fin" and a[2] in ("revision_mecanica", "revision_ux"):
            M["laminas"][lam]["rondas_revision"] += 1
        if orden == "fin" and a[2] == "correcciones":
            M["laminas"][lam]["rondas_correccion"] += 1
    elif orden == "dato":
        try:
            v = json.loads(a[3])
        except json.JSONDecodeError:
            v = a[3]
        registro(M, lam)[a[2]] = v
    elif orden == "informe":
        informe(M, lam); return 0
    else:
        print(__doc__); return 1
    guardar(M)
    print(orden, lam, *a[2:3], "→", ahora())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
