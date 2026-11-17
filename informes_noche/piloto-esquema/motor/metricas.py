"""Cronómetro y métricas de cada lámina (lo usa la skill «hacer-lamina»). Guarda todo en metricas.json, junto a este script.

  python metricas.py nueva <lamina>                         crea el registro (fecha de hoy)
  python metricas.py inicio <lamina> <fase>                 anota la hora de inicio de la fase
  python metricas.py fin <lamina> <fase>                    anota la hora de fin (avisa si la fase no tiene inicio; --hora HH:MM corrige una marca olvidada)
  python metricas.py dato <lamina> <clave> '<json>'         p. ej. rondas_revision 2 · contexto_creadora '{"inicio":"12%","fin":"48%"}'
                                                             · notas_mecanica '{"fidelidad":5,...,"promedio":4.9}'
  python metricas.py informe <lamina>                        compara con la línea base (CVT) y con el promedio de las demás
  python metricas.py dato <lamina> tokens '{"inicio":N,"fin":N}'   tokens de la sesión (get_usage) o contexto en %: el informe los muestra
Meta (meta_fases en metricas.json): 10 min para todo, creación + revisión integrada. Al cerrar una fase: ⚠ si pasó su presupuesto (una línea en «explicacion»);
✋ CORTE si pasó del doble: se para ahí, la causa va a «pendientes» del JSON y se sigue con la siguiente fase.

Fases: catalogo, dibujo_contenido (alias dibujo+contenido; o dibujo2d, contenido y 3d por separado: cuentan contra el mismo
presupuesto), validacion, mediciones, revision (revisoras subagente + correcciones; o revision_mecanica, revision_ux y correcciones).
Auditoría externa: a la 5.ª lámina sin auditoría escribe ../auditoria-pendiente.md y avisa. La sesión auditora la registra con
  python metricas.py auditoria <lamina> <sigue|ajustar|parar>      (reinicia el contador; guía en ../guia-auditoria-externa.md)
Notas de la revisión integrada: dato <lamina> notas_revision '{"mecanica":4.0,"ux":4.2}'. Fases aparte, fuera del total: mejora_skill y revision_espera (la revisora corre en paralelo con --final; «revision» cuenta solo las correcciones).
Si dos fases corren a la vez (p. ej. el esqueleto en paralelo con el dibujo), el informe muestra el solapamiento y el tiempo de reloj.
Datos: pct_seguro = % de números, nombres y cantidades que cuadran con el catálogo (como en la CVT);
pct_certeza_total = % de todas las marcas de certeza («Seguro» sobre el total); uso_plan lo anota Auxiliares.
«Terminado» = cada nota ≥ la de la línea base; si alguna baja, el informe lo marca y hay que explicarlo en «explicacion».
"""
import datetime as dt, json, pathlib, sys

AQUI = pathlib.Path(__file__).resolve().parent
ARCH = AQUI / "metricas.json"
FASES = ["catalogo", "dibujo_contenido", "dibujo2d", "contenido", "3d", "validacion", "mediciones", "revision", "revision_mecanica", "revision_ux", "correcciones"]
GRUPO = {"dibujo2d": "dibujo_contenido", "contenido": "dibujo_contenido", "3d": "dibujo_contenido", "validacion": "verificacion", "mediciones": "verificacion",
         "revision_mecanica": "revision", "revision_ux": "revision", "correcciones": "revision"}   # fase → presupuesto de meta_fases
ALIAS = {"dibujo+contenido": "dibujo_contenido"}
CADA_AUDITORIA = 5
PENDIENTE = AQUI.parent / "auditoria-pendiente.md"
FASES_EXTRA = ["mejora_skill", "rediseno", "adopcion_v2", "revision_espera"]   # revision_espera: la revisora corre en paralelo con --final; solo las correcciones son «revision»   # se cronometran, pero no suman al total de la lámina
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


def sin_auditoria(M):
    """Láminas desde la última auditoría externa (de la más nueva hacia atrás)."""
    L = []
    for k, r in reversed(list(M["laminas"].items())):
        if r.get("auditoria") or r.get("revision_externa"):
            break
        L.append(k)
    return L[::-1]


def aviso_auditoria(M):
    L = sin_auditoria(M)
    if len(L) < CADA_AUDITORIA:
        return
    filas = []
    for k in L:
        r = M["laminas"][k]
        t = sum(x for x in (minutos(f) for f in r["fases"].values()) if x)
        pend = r.get("pendientes")
        filas.append(f"| {k} | {r['fecha']} | {t:.0f} | {r.get('notas_revision') or '-'} | {r.get('notas_ux', {}).get('promedio', '-')} | "
                     f"{r.get('notas_mecanica', {}).get('promedio', '-')} | {len(pend) if isinstance(pend, list) else pend} |")
    PENDIENTE.write_text(
        f"# Auditoría externa pendiente ({dt.date.today().isoformat()})\n\n{len(L)} láminas desde la última auditoría.\n\n"
        "| lámina | fecha | min (creación + revisión) | revisión integrada | nota UX | nota mecánica | pendientes |\n|---|---|---|---|---|---|---|\n"
        + "\n".join(filas)
        + "\n\n## Brief para la sesión auditora (pegar tal cual)\n"
        "Eres la auditora externa del esquema pedagógico de TallerYa (C:\\dev\\TallerYa). Sigue `informes_noche/piloto-esquema/guia-auditoria-externa.md` "
        f"con estas láminas: {', '.join(L)}. Sortea 2, revísalas a fondo (mecánica y UX) contra el manual y la CVT (fig. 12), compara con las notas "
        "de la revisión integrada (tabla de arriba), mira la tendencia y entrega una página con veredicto sigue / ajustar / parar. Registra con "
        f"`venv/Scripts/python.exe informes_noche/piloto-esquema/motor/metricas.py auditoria {L[-1]} <veredicto>`. Los PDF solo se leen; sin commit.\n",
        encoding="utf-8")
    print(f"  ⚑ hay una auditoría externa pendiente ({len(L)} láminas): pídesela a Auxiliares · {PENDIENTE.name}")


def gastado(R, presupuesto):
    v = [minutos(R["fases"].get(x, {})) for x in [presupuesto] + [f for f, g in GRUPO.items() if g == presupuesto]]
    v = [x for x in v if x is not None]
    return sum(v) if v else None


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
    if meta:   # todo = del catálogo hasta revisada y corregida (revisión integrada incluida)
        CREA = FASES
        tc = [t for t in tramos if t[0] in CREA]
        if tc:
            rc = (max(t[2] for t in tc) - min(t[1] for t in tc)).total_seconds() / 60
            dif = rc - meta
            print(f"  TOTAL (creación + revisión): {rc:.0f} min de reloj · meta {meta}{' sin paralelo' if M.get('sin_paralelo') else ''} → " + (f"sobró {-dif:.0f} min" if dif <= 0 else f"faltó {dif:.0f} min (pasó la meta)"))
            mf = M.get("meta_fases", {})
            fila = []
            for f, mm in mf.items():
                v = gastado(R, f)
                if v is not None: fila.append(f"{f} {v:.1f}/{mm} ({v - mm:+.1f})")
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
    aviso_auditoria(M)


def main(a):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    M = cargar()
    if len(a) < 2:
        print(__doc__); return 1
    orden, lam = a[0], a[1]
    if orden in ("inicio", "fin") and len(a) > 2:
        a[2] = ALIAS.get(a[2], a[2])
    if orden == "auditoria":
        if len(a) < 3 or a[2] not in ("sigue", "ajustar", "parar"):
            print("uso: metricas.py auditoria <lamina> <sigue|ajustar|parar>"); return 1
        registro(M, lam)["auditoria"] = {"fecha": ahora(), "veredicto": a[2]}
        if PENDIENTE.exists(): PENDIENTE.unlink()
        guardar(M); print("auditoría registrada:", lam, a[2], "· contador en 0"); return 0
    if orden == "nueva" or (orden == "inicio" and lam not in M["laminas"]):
        registro(M, lam)
        aviso_auditoria(M)
    if orden in ("inicio", "fin") and len(a) > 2:   # ronda 4: el primer «inicio» de una lámina nueva también anota su fase (antes se perdía)
        if a[2] not in FASES + FASES_EXTRA:
            print("fase desconocida:", a[2], "· fases:", ", ".join(FASES + FASES_EXTRA)); return 1
        hora = ahora()
        if "--hora" in a:   # p. ej. --hora 19:33: corrige una marca olvidada (mismo día)
            hora = ahora()[:11] + a[a.index("--hora") + 1]
        F = registro(M, lam)["fases"].setdefault(a[2], {})
        if orden == "fin" and "inicio" not in F:
            otras = sorted(x["fin"] for k, x in M["laminas"][lam]["fases"].items() if k != a[2] and x.get("fin"))
            sug = otras[-1][11:] if otras else "HH:MM"
            print(f"⚠ «{a[2]}» no tiene inicio: probablemente empezó cuando terminó la fase anterior ({sug}). "
                  f"Corrígelo con: metricas.py inicio {lam} {a[2]} --hora {sug}")
        F[orden] = hora
        if orden == "fin" and a[2] in FASES:   # tope por fase: si pasa del 125 % del promedio, se anota por qué y se sigue
            pres = GRUPO.get(a[2], a[2])
            m = gastado(M["laminas"][lam], pres) if pres in M.get("meta_fases", {}) else minutos(M["laminas"][lam]["fases"][a[2]])
            refs = [x for x in (minutos(r["fases"].get(a[2], {})) for k, r in M["laminas"].items() if k != lam) if x]
            mm = M.get("meta_fases", {}).get(pres)
            if m is not None and mm is not None:
                print(f"{a[2]}{' (' + pres + ')' if pres != a[2] else ''}: {m:.1f} min · meta {mm}" + (f"  ✋ CORTE: pasó del doble. No pulas más esta fase: anota la causa en «pendientes» del JSON y sigue" if m > 2 * mm
                      else f"  ⚠ pasó la meta: anota por qué en una línea (dato {lam} explicacion) y sigue" if m > mm else "  ✓"))
            elif m is not None and refs:
                esp = sum(refs) / len(refs)
                print(f"{a[2]}: {m:.0f} min (promedio {esp:.0f})" + (f"  ⚠ pasó del 125 %: anota por qué con «dato {lam} explicacion …» y sigue" if m > esp * TOLERANCIA else ""))
        if orden == "fin" and a[2] in ("revision_mecanica", "revision_ux", "revision"):
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
    elif orden != "nueva":
        print(__doc__); return 1
    guardar(M)
    print(orden, lam, *a[2:3], "→", (ahora()[:11] + a[a.index("--hora") + 1]) if "--hora" in a else ahora())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
