"""Mide el consumo de tokens de las sesiones de Claude Code de TallerYa.

Uso:  python -I .claude/herramientas/uso_tokens.py [--desde AAAA-MM-DD] [--hasta AAAA-MM-DD] [--sesiones N]

Lee las transcripciones locales (~/.claude/projects/C--dev-TallerYa*/*.jsonl) y muestra:
contexto releído por turno (media y mediana), % de turnos sobre 150 mil, gasto por día y por modelo,
y las sesiones más caras. Línea base (16 al 19-nov-2026): 231 mil por turno, 76 % de turnos > 150 mil.
No manda nada a ningún lado.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import statistics as st

LINEA_BASE = {"contexto_medio_k": 231, "pct_mayor_150k": 76}

ap = argparse.ArgumentParser()
ap.add_argument("--desde", default=None)
ap.add_argument("--hasta", default=None)
ap.add_argument("--sesiones", type=int, default=8)
a = ap.parse_args()
desde = a.desde or (dt.date.today() - dt.timedelta(days=7)).isoformat()
hasta = a.hasta or "9999"

turnos, por_dia, por_modelo, sesiones = [], collections.Counter(), collections.Counter(), []
for d in glob.glob(os.path.expanduser("~/.claude/projects/C--dev-TallerYa*")):
    for f in glob.glob(d + "/*.jsonl"):
        tot = n = 0
        mayor = 0
        for linea in open(f, encoding="utf-8", errors="ignore"):
            try:
                j = json.loads(linea)
            except ValueError:
                continue
            if j.get("type") != "assistant":
                continue
            dia = (j.get("timestamp") or "")[:10]
            if not (desde <= dia <= hasta):
                continue
            m = j.get("message") or {}
            u = m.get("usage") or {}
            ctx = u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("input_tokens", 0)
            if not ctx:
                continue
            g = ctx + u.get("output_tokens", 0)
            turnos.append(ctx)
            por_dia[dia] += g
            por_modelo[m.get("model", "?")] += g
            tot += g
            n += 1
            mayor = max(mayor, ctx)
        if n:
            sesiones.append((tot, n, mayor, os.path.basename(f)[:8]))

if not turnos:
    raise SystemExit(f"Sin turnos entre {desde} y {hasta}.")
T = sum(por_dia.values())
medio = st.mean(turnos) / 1000
pct = 100 * sum(t > 150_000 for t in turnos) / len(turnos)
print(f"Periodo {desde} a {hasta}: {len(turnos)} turnos, {len(sesiones)} sesiones, {T / 1e6:.0f} M tokens")
print(f"Contexto por turno: media {medio:.0f} mil (base {LINEA_BASE['contexto_medio_k']}), "
      f"mediana {st.median(turnos) / 1000:.0f} mil")
print(f"Turnos > 150 mil: {pct:.0f} % (base {LINEA_BASE['pct_mayor_150k']} %, meta < 20 %)")
print("Por día (M):", ", ".join(f"{k[5:]} {v / 1e6:.0f}" for k, v in sorted(por_dia.items())))
print("Por modelo:", ", ".join(f"{k.replace('claude-', '')} {100 * v / T:.0f} %" for k, v in por_modelo.most_common()))
print("Sesiones más caras (M, turnos, contexto máx.):")
for tot, n, mayor, nombre in sorted(sesiones, reverse=True)[: a.sesiones]:
    print(f"  {nombre}  {tot / 1e6:.0f} M  {n} turnos  máx {mayor // 1000} mil")
