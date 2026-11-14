"""Avisos de pico y placa y de vencimientos (SOAT y técnico-mecánica) de una moto.

Los usan tres lugares, con las mismas claves para no repetir nada:
- la franja de avisos de Mi garaje y de la ficha de la moto;
- las notificaciones que se generan al navegar (notificaciones.servicios);
- el comando `avisar_vencimientos`, pensado para cron.
"""
from django.utils import timezone

from .pico_placa import tiene_pico_placa

UMBRALES = (30, 15, 3)  # días antes del vencimiento en que se avisa


def _cuando(dias):
    if dias == 0:
        return "hoy"
    if dias == 1:
        return "mañana"
    return f"en {dias} días"


def umbral(dias):
    """Umbral que corresponde a los días que faltan (30, 15 o 3), o None si aún falta más."""
    return min((u for u in UMBRALES if dias <= u), default=None)


def avisos_documentos(moto, hoy=None):
    """Un aviso por documento vencido o por vencer en 30 días o menos."""
    hoy = hoy or timezone.localdate()
    avisos = []
    for doc in moto.documentos(hoy):
        dias = doc["dias"]
        if dias is None or (dias >= 0 and umbral(dias) is None):
            continue
        if dias < 0:
            etapa = "vencido"
            titulo = f"Tu {doc['nombre'].lower() if doc['clave'] == 'tecno' else doc['nombre']} está vencid{'o' if doc['clave'] == 'soat' else 'a'}"
            nivel = "alerta"
        else:
            etapa = f"{umbral(dias)}d"
            titulo = f"Tu {doc['nombre'].lower() if doc['clave'] == 'tecno' else doc['nombre']} vence {_cuando(dias)}"
            nivel = "alerta" if dias <= 3 else "aviso"
        texto = f"{moto} · {'venció' if dias < 0 else 'vence'} el {doc['vence']:%d/%m/%Y}"
        if doc["estimado"]:
            texto += " (calculado con la fecha de matrícula)"
        avisos.append({
            "clave": f"doc:{moto.pk}:{doc['clave']}:{etapa}:{doc['vence']}", "titulo": titulo, "texto": texto,
            "url": f"{moto.get_absolute_url()}#documentos", "tipo": "documento", "nivel": nivel, "dias": dias,
        })
    return avisos


def aviso_pico_placa(moto, hoy=None):
    """Aviso del mismo día si la moto tiene pico y placa hoy, o None."""
    hoy = hoy or timezone.localdate()
    if not moto.placa:
        return None
    aplica, regla = tiene_pico_placa(moto, hoy)
    if not aplica:
        return None
    return {"clave": f"pyp:{moto.pk}:{hoy}", "titulo": "Hoy tienes pico y placa",
            "texto": f"{moto} · placa {moto.placa} · {regla.horario}",
            "url": f"{moto.get_absolute_url()}#pico-placa", "tipo": "general", "nivel": "alerta", "dias": 0}


def avisos_moto(moto, hoy=None):
    """Todos los avisos de hoy para la franja de la página (pico y placa primero, luego lo que vence antes)."""
    hoy = hoy or timezone.localdate()
    pyp = aviso_pico_placa(moto, hoy)
    return ([pyp] if pyp else []) + sorted(avisos_documentos(moto, hoy), key=lambda a: a["dias"])


def notificar_moto(moto, hoy=None, pico_placa=True):
    """Crea las notificaciones que falten para esta moto. Devuelve cuántas creó (las repetidas no cuentan)."""
    from notificaciones.servicios import notificar

    usuario = moto.motociclista.usuario
    if not usuario:
        return 0
    avisos = avisos_documentos(moto, hoy)
    if pico_placa and moto.aviso_pico_placa and (pyp := aviso_pico_placa(moto, hoy)):
        avisos.append(pyp)
    return sum(1 for a in avisos if notificar(usuario, a["clave"], a["titulo"], a["texto"], a["url"], a["tipo"]))
