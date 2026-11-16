"""Autocontrol en un solo comando: validador (con mas_controles) + medir_lamina + informe de métricas, con salida corta.

Uso (desde la raíz del proyecto):
  python informes_noche/piloto-esquema/motor/autocontrol.py <lamina> [--pagina <pagina>.html] [--captura <lamina>-1280.jpg] [--rapido] [--previa] [--ojo a,b,c,d,e,f] [--separar]

- <lamina>: nombre del JSON en datos/ (sin .json).
- --pagina y --captura, mismo formato: nombre solo = en M (motor/); con carpeta = desde la raíz; o absoluta. --pagina por omisión <lamina>.html.
- --captura: una sola captura del armado (1280, escala 0,5) en la misma medición, para juzgar el dibujo. Úsala solo en la medición final.
- --separar: corre antes separar_numeros.py --escribir (solo si el validador da errores de toque en el despiece).
- --final: medición completa corta (≈ la mitad): no repite «Cómo funciona» ni el solape del desarme, que ya revisó --previa (chequeo_rapido.py). Úsala después de una --previa sin problemas.
- --rapido: solo el validador (segundos); sin --rapido mide además con medir_lamina (≈ 40 s, 6 anchos, Chrome sin ventana).
- --previa: validador + captura a 1280 + chequeo_rapido.py (etiquetas montadas, pasos sin cambio, textos largos, marcas,
  solape del desarme): lo que antes salía recién en la medición completa. Así la medición completa se corre UNA vez.
- --informe: escribe revision/<lamina>.md (textos para revisar, certezas, pendientes, última medición y capturas) para
  que las revisoras trabajen sobre el resumen y no naveguen la lámina desde cero (guia-revision-rapida.md).
- -v: detalle (todos los errores y avisos); sin -v, resumen corto (hasta 8 errores y los avisos agrupados).
- Sale con código 1 si hay errores del validador o bloqueantes de medir_lamina: «Terminado» exige 0 y 0.
"""
import argparse, pathlib, re, subprocess, sys
from collections import Counter

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
PY = sys.executable


def correr(args, timeout=400):
    r = subprocess.run([PY, *args], cwd=RAIZ, capture_output=True, timeout=timeout, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    return (r.stdout + r.stderr).decode("utf-8", "replace"), r.returncode


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("lamina"); ap.add_argument("--pagina"); ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--ojo"); ap.add_argument("--separar", action="store_true"); ap.add_argument("--captura")
    ap.add_argument("--final", action="store_true", help="medición final corta (medir_lamina --final): sin «Cómo funciona» ni solape, que ya revisó chequeo_rapido.py en --previa")
    ap.add_argument("--antes", action="store_true", help="guarda datos/<lamina>.antes.json (la versión antes de corregir) y sale; el validador avisa después si se pierde una palabra de seguridad o de procedimiento")
    ap.add_argument("-v", action="store_true", help="detalle: todos los errores y avisos")
    ap.add_argument("--informe", action="store_true", help="escribe revision/<lamina>.md para las revisoras y sale")
    ap.add_argument("--previa", action="store_true", help="validador + captura a 1280 + etiquetas montadas de «Cómo funciona» (~35 s): mírala y luego corre la medición completa con --ojo")
    a = ap.parse_args()
    if a.antes:
        import shutil; src = AQUI / "datos" / f"{a.lamina}.json"; shutil.copyfile(src, src.with_suffix(".antes.json"))
        print(f"guardada {src.with_suffix('.antes.json').name}: corrige y corre --rapido"); sys.exit(0)
    js = AQUI / f"datos/{a.lamina}.json"
    if a.informe:
        import informe_revision; print(informe_revision.escribir(a.lamina)); sys.exit(0)
    rel = lambda p: str(p.relative_to(RAIZ)).replace("\\", "/")
    if a.separar:
        out, _ = correr([rel(AQUI / "separar_numeros.py"), rel(js), "--escribir"]); print("separar_numeros:", out.strip().splitlines()[-1] if out.strip() else "-")
    out, _ = correr([rel(AQUI / "validar_esquema.py"), rel(js)] + (["--previa"] if a.previa else []))
    errores = [l.strip() for l in out.splitlines() if "ERROR" in l]
    avisos = [l.strip()[7:] for l in out.splitlines() if l.strip().startswith("aviso:")]
    print(f"VALIDADOR: {len(errores)} errores · {len(avisos)} avisos")
    tope = 40 if a.v else 8
    for e in errores[:tope]: print("  " + e)
    if len(errores) > tope: print(f"  … y {len(errores) - tope} más (-v para verlos)")
    tipos = Counter(re.sub(r"\d+[a-z]?", "N", x)[:60] for x in avisos)
    if a.v or len(avisos) <= 4:
        for x in avisos[:40]: print("  aviso: " + x[:170])
    else:
        for t, n in tipos.most_common(4): print(f"  aviso ({n}×): {t}")
        if len(tipos) > 4: print(f"  … {len(tipos) - 4} tipos más de aviso (-v)")
    bloq = []
    if not a.rapido and not errores:
        res = lambda p: pathlib.Path(p) if pathlib.Path(p).is_absolute() else (RAIZ / p if ("/" in p or "\\" in p) else AQUI / p)
        pag = res(a.pagina or f"{a.lamina}.html").resolve()
        if not pag.exists():
            print(f"MEDIR: no está {pag.name} (pasa --pagina)")
        else:
            args = [rel(AQUI / "medir_lamina.py"), rel(pag)] + (["--ojo", a.ojo] if a.ojo else []) + (["--captura", str(res(a.captura).resolve())] if a.captura else [])
            if a.previa:
                out, _ = correr(args + ["--solo-captura"] + ([] if a.captura else ["--captura", str((AQUI / f"{a.lamina}-1280.jpg").resolve())]))
                print("MEDIR (previa): " + (out.strip().splitlines() or [""])[-1])
                fo, fc = correr([rel(AQUI / "chequeo_rapido.py"), rel(pag)] + (["-v"] if a.v else []))   # lo que la medición completa bloquearía
                for l in fo.strip().splitlines(): print(l[:300])
                sys.exit(1 if errores or fc else 0)
            out, _ = correr(args + (["--final"] if a.final else []))
            (AQUI / "revision").mkdir(exist_ok=True); (AQUI / "revision" / f"{a.lamina}-medicion.txt").write_text(out, encoding="utf-8")   # para --informe
            ls = out.splitlines()
            nota = next((l for l in ls if l.startswith("Notas")), "")
            bl = next((l for l in ls if l.startswith("Bloqueantes")), "")
            print("MEDIR: " + bl); print("  " + nota)
            for l in ls:
                if l.startswith("  - ") and "área tocable ≥" not in l: print("  " + l.strip()[:220])
            if bl and "ninguno" not in bl: bloq.append(bl)
    elif errores and not a.rapido:
        print("MEDIR: no se mide con errores del validador (corrígelos primero)")
    out, _ = correr([rel(AQUI / "metricas.py"), "informe", a.lamina])
    ls = [l for l in out.splitlines() if l.strip()]
    if ls and "no hay" not in out.lower():
        print("MÉTRICAS: " + " · ".join(l.strip() for l in ls if re.search(r"TOTAL|reloj|POR DEBAJO|más de lo esperado|⚠", l))[:400])
    sys.exit(1 if errores or bloq else 0)


if __name__ == "__main__":
    main()
