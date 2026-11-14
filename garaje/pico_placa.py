"""Pico y placa: festivos de Colombia, regla vigente y estado de una moto."""
import re
from datetime import date, timedelta
from functools import lru_cache

from django.utils import timezone

DIAS_CORTOS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
DIAS_LARGOS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _pascua(anio):
    """Domingo de Pascua (algoritmo gregoriano anónimo)."""
    a, b, c = anio % 19, anio // 100, anio % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def _al_lunes(d):
    return d + timedelta(days=(7 - d.weekday()) % 7)


@lru_cache(maxsize=8)
def festivos(anio):
    """Festivos de Colombia (Ley 51 de 1983: varios se corren al lunes siguiente)."""
    fijos = {date(anio, m, d) for m, d in ((1, 1), (5, 1), (7, 20), (8, 7), (12, 8), (12, 25))}
    corridos = {_al_lunes(date(anio, m, d)) for m, d in ((1, 6), (3, 19), (6, 29), (8, 15), (10, 12), (11, 1), (11, 11))}
    p = _pascua(anio)
    pascua = {p - timedelta(days=3), p - timedelta(days=2),  # jueves y viernes santo
              p + timedelta(days=43), p + timedelta(days=64), p + timedelta(days=71)}  # Ascensión, Corpus, Sagrado Corazón
    return frozenset(fijos | corridos | pascua)


def es_festivo(d):
    return d in festivos(d.year)


def regla_vigente(d, ciudad="Medellín"):
    from .models import ReglaPicoPlaca
    return (ReglaPicoPlaca.objects.filter(ciudad=ciudad, vigente_desde__lte=d)
            .exclude(vigente_hasta__lt=d).order_by("-vigente_desde").first())


def digito_placa(placa, cual="primero"):
    numeros = re.findall(r"\d", placa or "")
    if not numeros:
        return None
    return numeros[0] if cual == "primero" else numeros[-1]


def restringido(regla, digito, d):
    """True si ese día aplica la medida para ese dígito (no aplica fines de semana ni festivos)."""
    return bool(regla and digito is not None and not es_festivo(d) and digito in regla.digitos(d.weekday()))


def tiene_pico_placa(moto, d):
    regla = regla_vigente(d)
    return restringido(regla, digito_placa(moto.placa, regla.digito if regla else "primero"), d), regla


def resumen(moto, hoy=None):
    """Datos para la tarjeta de la moto."""
    hoy = hoy or timezone.localdate()
    datos = {"placa": moto.placa, "regla": None}
    regla = regla_vigente(hoy)
    if not moto.placa or not regla:
        datos["regla"] = regla
        return datos
    digito = digito_placa(moto.placa, regla.digito)
    # Semana a mostrar: la actual de lunes a viernes; el fin de semana, la siguiente.
    lunes = hoy - timedelta(days=hoy.weekday()) + (timedelta(days=7) if hoy.weekday() > 4 else timedelta())
    semana = []
    for i in range(5):
        d = lunes + timedelta(days=i)
        semana.append({"fecha": d, "dia": DIAS_CORTOS[i], "digitos": " · ".join(regla.digitos(i)),
                       "mio": digito in regla.digitos(i), "festivo": es_festivo(d), "hoy": d == hoy,
                       "pasado": d < hoy})
    proximo = next((hoy + timedelta(days=n) for n in range(1, 30) if restringido(regla, digito, hoy + timedelta(days=n))), None)
    datos.update({
        "regla": regla, "digito": digito, "semana": semana, "hoy": restringido(regla, digito, hoy),
        "festivo_hoy": es_festivo(hoy), "fin_de_semana": hoy.weekday() > 4,
        "proximo": proximo, "proximo_dia": DIAS_LARGOS[proximo.weekday()] if proximo else "",
        "es_manana": proximo == hoy + timedelta(days=1),
        "dias_mios": [DIAS_LARGOS[i] for i in range(5) if digito in regla.digitos(i)],
    })
    return datos


def aviso_pendiente(moto, ahora=None):
    """Aviso dentro de TallerYa: el mismo día (antes de las 8 p. m.) o la tarde anterior. Una sola vez por día."""
    if not moto.placa or not moto.aviso_pico_placa:
        return None
    ahora = timezone.localtime(ahora) if ahora else timezone.localtime()
    hoy = ahora.date()
    for d, desde, hasta, titulo in ((hoy, 0, 20, "Hoy tienes pico y placa"),
                                    (hoy + timedelta(days=1), 15, 24, "Mañana tienes pico y placa")):
        aplica, regla = tiene_pico_placa(moto, d)
        if aplica and desde <= ahora.hour < hasta:
            return f"pyp:{moto.pk}:{d}", titulo, f"{moto} · placa {moto.placa} · {regla.horario}"
    return None
