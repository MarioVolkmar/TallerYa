"""Franja compacta de cifras de los paneles de aliados (taller y mecánico a domicilio).

Cada cifra: (etiqueta, valor, anterior, nota, url, color, consejo). Las que valen 0 y no tienen
nada con qué compararse no se muestran: pasan a ser un consejo (solo el primero).
"""
import calendar
from datetime import date

MAXIMO = 4


def mes_anterior(hoy: date):
    """Rango del mes pasado hasta el mismo día de hoy (comparación justa con el mes en curso)."""
    ano, mes = (hoy.year - 1, 12) if hoy.month == 1 else (hoy.year, hoy.month - 1)
    dia = min(hoy.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, 1), date(ano, mes, dia)


def tendencia(valor, anterior, contra):
    """«+2 vs semana pasada»; None si no hay con qué comparar o ambos son 0."""
    if anterior is None or (valor == 0 and anterior == 0):
        return None
    dif = valor - anterior
    if dif == 0:
        return {"texto": f"igual que {contra}", "sentido": "igual"}
    return {"texto": f"{dif:+d} vs {contra}".replace("-", "−"), "sentido": "sube" if dif > 0 else "baja"}


def franja(cifras):
    """Devuelve {"items": [...], "consejo": str}. Cifras sin valor útil se esconden."""
    items, consejo = [], ""
    for etiqueta, valor, anterior, contra, nota, url, color, tip in cifras:
        vacio = valor in (0, None, "") and not anterior
        if vacio:
            consejo = consejo or tip
            continue
        if len(items) < MAXIMO:
            items.append({"etiqueta": etiqueta, "valor": valor, "tend": tendencia(valor, anterior, contra) if isinstance(valor, int) else None,
                          "nota": nota, "url": url, "color": color})
    return {"items": items, "consejo": consejo}


CORTOS = {
    "cédula registrada": "cédula", "correo confirmado": "correo", "foto tuya o trabajando": "foto",
    "datos básicos, zonas y servicios": "datos y zonas", "descripción de tu experiencia": "descripción",
    "fotos de trabajos que hayas hecho": "fotos de trabajos", "en qué eres bueno y cómo trabajas": "especialidades",
    "precios de referencia por servicio": "precios", "una o dos referencias": "referencias",
    "garantía o cómo trabajan": "garantía", "marcas que atiendes": "marcas", "quiénes atienden": "equipo",
    "precios por servicio": "precios", "rango de precios": "rango de precios",
}


def faltan_cortos(faltan, maximo=3):
    """«cédula, correo, foto +2» a partir de los textos largos de lo que le falta al perfil."""
    cortos = []
    for t in faltan:
        t = t.split(" (")[0].strip().lower()
        cortos.append(CORTOS.get(t, t))
    texto = ", ".join(cortos[:maximo])
    return texto + (f" +{len(cortos) - maximo}" if len(cortos) > maximo else "")
