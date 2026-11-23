"""Aviso de contexto grande (hook UserPromptSubmit/PostToolUse). Solo avisa; nunca bloquea.
Uso: python -I .claude/herramientas/aviso_contexto.py   (JSON del hook por stdin)
Umbrales: 250 mil (tope de tareas livianas) y 300 mil (tope de las pesadas y techo duro de todas); una vez por umbral y sesión (marca en %TEMP%)."""
import json, os, sys, tempfile

U1, U2 = 250_000, 300_000
TXT1 = ("Pasaste ~250 mil tokens de contexto: es el tope de las tareas LIVIANAS (vistas, plantillas, CSS, pruebas, "
        "informes, coordinación). Si la tuya es liviana: TERMINA el encargo en curso (y los ajustes cortos de ese mismo "
        "encargo), pero no aceptes encargos nuevos; al terminar, escribe una nota de relevo en la memoria (qué hiciste, "
        "qué falta, archivos, estado de las pruebas) y avisa para seguir en una sesión nueva. Si es PESADA (3D, láminas "
        "del despiece, skills grandes, funciones nuevas que piden diseño), sigue hasta ~300 mil.")
TXT2 = ("Pasaste ~300 mil tokens de contexto: es el techo de TODAS las tareas, también las pesadas. "
        "Termina SOLO el paso en curso, no empieces nada más, escribe YA la nota de relevo en la memoria "
        "(qué hiciste, qué falta, archivos, estado de las pruebas) y pide al usuario seguir en una sesión nueva.")


def contexto(ruta):
    """Contexto del último mensaje del asistente, leyendo solo el final del archivo."""
    with open(ruta, "rb") as f:
        f.seek(0, 2)
        fin = f.tell()
        for tam in (200_000, 2_000_000):
            ini = max(0, fin - tam)
            f.seek(ini)
            datos = f.read(fin - ini)
            lineas = datos.split(b"\n")
            if ini:
                lineas = lineas[1:]
            for ln in reversed(lineas):
                if b'"usage"' not in ln or b'"assistant"' not in ln:
                    continue
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if d.get("isSidechain"):
                    continue
                u = (d.get("message") or {}).get("usage")
                if u:
                    return (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                            + u.get("cache_creation_input_tokens", 0))
            if ini == 0:
                break
    return 0


def main():
    try:
        h = json.load(sys.stdin)
        ruta, sid = h.get("transcript_path"), str(h.get("session_id", ""))
        if not ruta or not sid or not os.path.isfile(ruta):
            return
        n = contexto(ruta)
        nivel = 2 if n >= U2 else 1 if n >= U1 else 0
        if not nivel:
            return
        d = os.path.join(tempfile.gettempdir(), "tallerya_aviso_contexto")
        os.makedirs(d, exist_ok=True)
        marca = os.path.join(d, "".join(c for c in sid if c.isalnum() or c in "-_"))
        previo = 0
        if os.path.isfile(marca):
            previo = int(open(marca).read().strip() or 0)
        if previo >= nivel:
            return
        open(marca, "w").write(str(nivel))
        evento = h.get("hook_event_name") or "UserPromptSubmit"
        texto = (TXT2 if nivel == 2 else TXT1) + f" (contexto actual: ~{n // 1000} mil)"
        print(json.dumps({"hookSpecificOutput": {"hookEventName": evento, "additionalContext": texto}},
                         ensure_ascii=False))
    except Exception:
        pass


main()
