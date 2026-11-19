"""Esqueleto de garaje/fallas_frecuentes/<slug>.json desde la línea (BD) y su archivo de intervalos (manual).

Genera solo lo honesto sin investigar: fallas de alcance «tipo» según cómo es la moto (cadena o CVT, frenos de
tambor o disco, refrigeración líquida, enduro) con los valores del manual, y tips desde las notas de intervalos.
Las fallas propias del modelo (alcance «modelo») se agregan a mano, con su fuente (skill fallas-modelo).

  manage.py esqueleto_fallas yamaha_aerox_155            # muestra el resumen (no escribe)
  manage.py esqueleto_fallas --faltantes --escribir      # crea los que falten (nunca sobrescribe sin --forzar)
"""
import json
import re

from django.core.management.base import BaseCommand, CommandError

from garaje import fallas, intervalos
from garaje.models import LineaMoto

HOY = "2026-11-18"
DX = {"nombre": "Diagnóstico guiado de TallerYa (garaje/diagnostico.py): causas usuales por síntoma", "url": ""}
TITULOS_TIP = {
    "aceite": "El aceite que pide", "correa-cvt": "La correa", "valvulas": "Válvulas", "filtro-aire": "Filtro de aire",
    "refrigerante": "Refrigerante", "bujia": "Bujía", "aceite-caja": "Aceite de la transmisión final",
    "liquido-frenos": "Líquido de frenos", "cadena-lubricar": "La cadena", "suspension-del": "Suspensión delantera",
}
TIPO_GENERAL = {"semi": "calle", "sport": "calle"}


def _km(n):
    return f"{n:,}".replace(",", ".")


def _cada(t):
    partes = []
    if t.get("km"):
        partes.append(f"cada {_km(t['km'])} km")
    if t.get("dias"):
        meses = round(t["dias"] / 30)
        partes.append(f"cada {meses} meses" if meses < 24 else f"cada {round(meses / 12)} años")
    return " o ".join(partes)


def _frase(texto):
    texto = (texto or "").strip()
    return texto if not texto or texto.endswith(".") else texto + "."


INTERNO = re.compile(r"Usamos|plan general|cuadro|cat[aá]logo|anotaci[oó]n|verificar|tabla|Manual:|mismo manual|copia|bloque", re.I)


def _limpiar(texto):
    """Quita de las notas de intervalos lo que es interno (de dónde salió el dato, decisiones nuestras)."""
    texto = re.sub(r"\s*\([^)]*(manual|p\.\s*\d|cat[aá]logo|bloque|secci[oó]n)[^)]*\)", "", texto or "", flags=re.I)
    frases = re.split(r"(?<=\.)\s+(?=[A-ZÁÉÍÓÚÑ¿«])", texto.strip())
    return " ".join(f for f in frases if f and not INTERNO.search(f)).strip()


def construir(linea):
    slug = intervalos.slug_linea(linea)
    datos_int = {}
    ruta = intervalos.CARPETA / f"{slug}.json"
    if ruta.exists():
        datos_int = json.loads(ruta.read_text(encoding="utf-8"))
    tareas = datos_int.get("tareas", {})
    nombre = f"{linea.marca.nombre} {linea.nombre}"
    fuente_manual = (tareas.get("aceite", {}).get("fuente") or f"Manual del propietario {nombre}")
    fuente_manual = re.split(r"[;(,]", fuente_manual)[0].strip().rstrip(",")
    fuentes = {"manual": {"nombre": f"{fuente_manual} (datos en garaje/intervalos/{slug}.json)", "url": ""},
               "diagnostico": DX}
    enduro, cvt = linea.tipo == "enduro", linea.transmision == "cvt"
    fs = []

    if cvt:
        correa = tareas.get("correa-cvt", {})
        fs.append({"clave": "cvt-tiembla", "titulo": "Tiembla al arrancar desde parado",
                   "sintoma": "Al salir del semáforo la moto vibra unos segundos antes de coger impulso, más en subida o con parrillero.",
                   "causa": "Polvo de la correa y de las zapatas acumulado en la campana del clutch, o zapatas vidriadas.",
                   "gravedad": "molestia",
                   "que_hacer": "Pide una limpieza del CVT y que revisen zapatas y campana. Si la campana está marcada o azulada, se cambia.",
                   "tareas": ["correa-cvt"], "pieza": "correa", "diagnostico": {"s": "cvt", "que": "tiembla"},
                   "taller": "Mantenimiento general", "domicilio": "Diagnóstico"})
        cambio = f" El manual la cambia {_cada(correa)}." if _cada(correa) else ""
        fs.append({"clave": "correa-gastada", "titulo": "Acelera pero no avanza como antes",
                   "sintoma": "El motor sube de vueltas y la moto se queda, sobre todo en lomas; a veces chilla la tapa del CVT.",
                   "causa": "Correa gastada o rodillos del variador aplanados. Una correa vieja puede reventarse.",
                   "gravedad": "cuidado",
                   "que_hacer": f"Revisa cuánto lleva la correa.{cambio} Si ya pasó, cambia correa y revisa rodillos en el mismo servicio.",
                   "tareas": ["correa-cvt"], "pieza": "correa", "diagnostico": {"s": "cvt", "que": "lenta"},
                   "taller": "Mantenimiento general", "domicilio": "Diagnóstico"})
    else:
        esp = tareas.get("cadena-lubricar", {}).get("especificacion", "")
        holgura = re.search(r"(\d+\s*[–-]\s*\d+)\s*mm", esp)
        juego = f" Deja el juego de la cadena en {holgura.group(1).replace('-', '–').replace(' ', '')} mm, como pide el manual." if holgura else ""
        if enduro:
            fs.append({"clave": "arrastre-trocha", "titulo": "La cadena se gasta rápido",
                       "sintoma": "La cadena se afloja seguido, suena o la corona tiene los dientes en punta.",
                       "causa": "Barro y polvo pegados al lubricante forman una pasta que lija cadena, piñón y corona.",
                       "gravedad": "cuidado",
                       "que_hacer": f"Después de trocha, lava, seca y lubrica la cadena.{juego} Si el kit está gastado, cámbialo completo.",
                       "tareas": ["cadena-lubricar", "kit-arrastre"], "pieza": "cadena",
                       "diagnostico": {"s": "ruido", "donde": "arrastre"}, "taller": "Kit de arrastre", "domicilio": "Kit de arrastre"})
        else:
            fs.append({"clave": "arrastre-gastado", "titulo": "Traqueteo de la cadena o tirones al acelerar",
                       "sintoma": "La cadena suena, cuelga o da golpecitos al soltar y dar acelerador.",
                       "causa": "Kit de arrastre gastado por falta de lubricar y tensar; con lluvia, parrillero y lomas se gasta más rápido.",
                       "gravedad": "cuidado",
                       "que_hacer": f"Lubrica y tensa ya.{juego} Si la corona tiene los dientes en punta, cambia el kit completo.",
                       "tareas": ["cadena-lubricar", "kit-arrastre"], "pieza": "cadena",
                       "diagnostico": {"s": "ruido", "donde": "arrastre"}, "taller": "Kit de arrastre", "domicilio": "Kit de arrastre"})

    tambor = linea.freno_trasero == "tambor"
    fs.append({"clave": "freno-tras", "titulo": "El freno de atrás cada vez frena menos",
               "sintoma": "Tienes que pisar o apretar más para que frene, o chilla al frenar.",
               "causa": ("Bandas gastadas o freno desajustado." if tambor else "Pastillas gastadas o líquido de frenos viejo.")
               + " En las bajadas de Medellín se gastan rápido.",
               "gravedad": "peligro",
               "que_hacer": ("Ajusta el freno y revisa el indicador de desgaste; si las bandas llegaron al límite, cámbialas ya."
                             if tambor else "Revisa el grosor de las pastillas y el nivel del líquido; si están al límite, cámbialas ya."),
               "tareas": ["bandas-tras"] if tambor else ["pastillas-tras", "liquido-frenos"], "pieza": "freno_tras",
               "diagnostico": {"s": "frena_mal", "cual": "tras", "como": "poco"}, "taller": "Frenos", "domicilio": "Frenos"})

    if "valvulas" in tareas:
        cada = _cada(tareas["valvulas"])
        fs.append({"clave": "valvulas-tic", "titulo": "Un «tic tic» metálico arriba del motor",
                   "sintoma": "Con el motor caliente oyes un golpeteo rápido y parejo que sube con las revoluciones.",
                   "causa": "Válvulas descalibradas: se abren con el uso normal y hay que ajustarlas.",
                   "gravedad": "molestia",
                   "que_hacer": f"Pide calibración de válvulas en frío{' ' + cada if cada else ''}, como pide el manual.",
                   "tareas": ["valvulas"], "pieza": "motor", "diagnostico": {"s": "ruido", "donde": "motor", "tipo": "tic"},
                   "taller": "Mantenimiento general", "domicilio": "Mantenimiento general"})

    if linea.refrigeracion == "liquido":
        fs.append({"clave": "recalienta", "titulo": "Se calienta en el trancón",
                   "sintoma": "El ventilador no para, la temperatura sube en el tablero o el depósito del refrigerante baja.",
                   "causa": "Poco refrigerante, una fuga en mangueras o radiador, o el ventilador que no prende. Que el ventilador prenda en el trancón es normal.",
                   "gravedad": "peligro",
                   "que_hacer": "Si la temperatura sigue subiendo, para y apaga. Revisa el nivel en frío y pide revisar ventilador, mangueras y radiador.",
                   "tareas": ["refrigerante"], "pieza": "refrigeracion",
                   "diagnostico": {"s": "se_apaga", "cuando": "caliente", "radiador": "si"},
                   "taller": "Mantenimiento general", "domicilio": "Diagnóstico"})
    elif enduro:
        fs.append({"clave": "filtro-polvo", "titulo": "Pierde fuerza después de andar en polvo",
                   "sintoma": "La moto se siente perezosa, acelera lento y gasta más gasolina.",
                   "causa": "Filtro de aire tapado de polvo o mojado.",
                   "gravedad": "molestia",
                   "que_hacer": "Revisa el filtro de aire: con polvo o lluvia toca atenderlo antes de lo que dice el plan.",
                   "tareas": ["filtro-aire"], "pieza": "filtro_aire", "diagnostico": {"s": "sin_fuerza", "como": "lenta"},
                   "taller": "Mantenimiento general", "domicilio": "Mantenimiento general"})

    if len(fs) < 3:
        cada = _cada(tareas.get("filtro-aire", {}))
        fs.append({"clave": "filtro-sucio", "titulo": "Se siente sin fuerza y gasta más",
                   "sintoma": "Acelera lento, le cuesta subir lomas y rinde menos el galón.",
                   "causa": "Filtro de aire sucio o bujía gastada: con el polvo y la lluvia de la ciudad se ensucia antes.",
                   "gravedad": "molestia",
                   "que_hacer": f"Revisa filtro de aire y bujía{' (el manual pide el filtro ' + cada + ')' if cada else ''}; si siguen bien, pide revisar la carburación o la inyección.",
                   "tareas": ["filtro-aire", "bujia"], "pieza": "filtro_aire", "diagnostico": {"s": "sin_fuerza", "como": "lenta"},
                   "taller": "Sincronización", "domicilio": "Diagnóstico"})
    for f in fs:
        f.update({"alcance": "tipo", "fuentes": ["manual", "diagnostico"] if any(
            k in f["que_hacer"] for k in ("manual", "Deja el juego")) else ["diagnostico"]})
    fs = fs[:6]

    tips = []
    for clave in TITULOS_TIP:
        t = tareas.get(clave)
        if not t or len(tips) >= 4:
            continue
        notas = _limpiar(t.get("notas"))
        partes = [_frase(_limpiar(t.get("especificacion"))), _frase(_cada(t).capitalize()) if _cada(t) else "", _frase(notas)]
        texto = " ".join(p for p in partes if p)
        if len(texto) >= 25:
            tips.append({"titulo": TITULOS_TIP[clave], "texto": texto, "fuentes": ["manual"]})
    if len(tips) < 3:
        general = fallas._generales().get(TIPO_GENERAL.get(linea.tipo, linea.tipo), {})
        for t in general.get("tips", [])[: 3 - len(tips)]:
            tips.append({**t, "fuentes": ["diagnostico"]})

    return slug, {"linea": nombre, "tipo": linea.tipo, "revisado": HOY,
                  "nota": "Generado con manage.py esqueleto_fallas: alcance «tipo» con los datos del manual. "
                          "Agregar fallas propias del modelo solo con fuente (skill fallas-modelo).",
                  "fuentes": fuentes, "fallas": fs, "tips": tips}


class Command(BaseCommand):
    help = "Crea el esqueleto de garaje/fallas_frecuentes/<slug>.json desde la línea y sus intervalos."

    def add_arguments(self, parser):
        parser.add_argument("slugs", nargs="*")
        parser.add_argument("--faltantes", action="store_true", help="Todas las líneas sin archivo de fallas")
        parser.add_argument("--escribir", action="store_true")
        parser.add_argument("--forzar", action="store_true", help="Sobrescribe archivos existentes")

    def handle(self, *args, **o):
        lineas = {intervalos.slug_linea(l): l for l in LineaMoto.objects.select_related("marca")}
        if o["faltantes"]:
            pedidos = [s for s in sorted(lineas) if not (fallas.CARPETA / f"{s}.json").exists()]
        else:
            pedidos = o["slugs"]
        if not pedidos:
            raise CommandError("Nada que hacer: pasa slugs o --faltantes.")
        for s in pedidos:
            if s not in lineas:
                raise CommandError(f"No hay línea con slug {s}. Opciones: {', '.join(sorted(lineas))}")
            slug, datos = construir(lineas[s])
            fallas.validar(datos, f"{slug}.json")
            ruta = fallas.CARPETA / f"{slug}.json"
            estado = "solo resumen"
            if o["escribir"]:
                if ruta.exists() and not o["forzar"]:
                    estado = "ya existe (usa --forzar)"
                else:
                    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    estado = "escrito"
            self.stdout.write(f"{slug}: {len(datos['fallas'])} fallas, {len(datos['tips'])} tips · {estado}")
