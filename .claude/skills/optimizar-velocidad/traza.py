"""Traza del hilo principal (CDP Tracing) en el celular de referencia sin freno de red: las 6 tareas más largas y qué las llena.
Uso: venv/Scripts/python.exe .claude/skills/optimizar-velocidad/traza.py http://127.0.0.1:8024/garaje/3/ [segundos=9] [correo]
Lectura: «Layout/UpdateLayoutTree» = CSS o DOM; «FunctionCall archivo.js» = ese JS; «EventDispatch» = un evento (p. ej.
moto3d-listo); «GPUTask» = la GPU compilando shaders (espera de GPU); «MajorGC/MinorGC» = basura de JS (armado del 3D).
"""
import os, sys, json, time, collections
sys.path.insert(0, __import__("os").path.dirname(os.path.abspath(__file__)))
import medir_chrome as m
url = sys.argv[1]
sys.stdout.reconfigure(encoding="utf-8")
espera = float(sys.argv[2]) if len(sys.argv) > 2 else 9
cookie = m.sesion(sys.argv[3]) if len(sys.argv) > 3 else None
p, puerto, perfil = m.abrir("real")
try:
    t = m.pestaña(puerto)
    t("Page.enable"); t("Network.enable")
    if cookie: t("Network.setCookie", name=cookie[0], value=cookie[1], url=url)
    t("Emulation.setDeviceMetricsOverride", width=375, height=812, deviceScaleFactor=2, mobile=True)
    t("Emulation.setCPUThrottlingRate", rate=4)
    t("Tracing.start", categories="devtools.timeline,disabled-by-default-devtools.timeline", transferMode="ReportEvents")
    t("Page.navigate", url=url); time.sleep(espera)
    t.n += 1
    import json as J
    c = J.dumps({"id": t.n, "method": "Tracing.end", "params": {}}).encode(); mk = os.urandom(4); L = len(c)
    t.s.sendall(bytes([0x81, 0x80 | L]) + mk + bytes(b ^ mk[i % 4] for i, b in enumerate(c)))
    ev = []
    while True:
        r = t._recibir()
        if r.get("method") == "Tracing.dataCollected": ev += r["params"]["value"]
        if r.get("method") == "Tracing.tracingComplete": break
    largas = [e for e in ev if e.get("name") == "RunTask" and e.get("dur", 0) > 300000]
    for L_ in sorted(largas, key=lambda e: -e["dur"])[:6]:
        hijos = collections.Counter()
        for e in ev:
            if e.get("tid") == L_["tid"] and e.get("ph") == "X" and e is not L_ and L_["ts"] <= e["ts"] <= L_["ts"] + L_["dur"]:
                d = e.get("args", {}).get("data", {})
                hijos[e["name"] + (" " + (d.get("url") or "")[-40:] if d.get("url") else "")] += e.get("dur", 0)
        print(f"tarea {L_['dur']/1000:.0f} ms:", "; ".join(f"{k} {v/1000:.0f}" for k, v in hijos.most_common(6)))
finally:
    m.cerrar(p, puerto, perfil)
