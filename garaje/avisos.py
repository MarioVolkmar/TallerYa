"""Avisos de pico y placa y de vencimientos (SOAT y técnico-mecánica) de una moto.

Aquí vive la escala única de color de los documentos (nivel_documento) y el enlace a la página que resuelve
cada aviso (url_solucion). Los avisos llegan a la campana con las mismas claves desde dos lados, sin repetirse:
las notificaciones que se generan al navegar (notificaciones.servicios) y el comando `avisar_vencimientos`.
"""
import re
from datetime import date

from django.urls import reverse
from django.utils import timezone

from .pico_placa import tiene_pico_placa

UMBRALES = (30, 15, 3)  # días antes del vencimiento en que se avisa
_CLAVE_VENCE = re.compile(r"^doc:\d+:(?:soat|tecno):\w+:(\d{4}-\d{2}-\d{2})$")
_CLAVE_DOC = re.compile(r"^doc:\d+:(soat|tecno):")


# Escala única de color para SOAT y técnico-mecánica (fichas, chips de Mi garaje, notificaciones y campana).
DIAS_PRONTO = 30   # de 8 a 30 días: amarillo
DIAS_URGENTE = 7   # de 0 a 7 días: rojo


def nivel_documento(dias):
    """ok (verde, > 30 días) · pronto (amarillo, 8–30) · urgente (rojo, 0–7) · vencido (rojo fuerte) · desconocido."""
    if dias is None:
        return "desconocido"
    if dias < 0:
        return "vencido"
    if dias <= DIAS_URGENTE:
        return "urgente"
    return "pronto" if dias <= DIAS_PRONTO else "ok"


def texto_vence(dias):
    """"Vence hoy", "Vence mañana", "Vence en 4 días", "Venció ayer", "Vencido hace 3 días"."""
    if dias is None:
        return "Sin fecha"
    if dias < 0:
        return "Venció ayer" if dias == -1 else f"Vencido hace {-dias} días"
    return "Vence hoy" if dias == 0 else "Vence mañana" if dias == 1 else f"Vence en {dias} días"


def accion_de_clave(clave):
    """Texto del botón según el aviso: el SOAT se pide (tarifa única), la técnico-mecánica va a un CDA."""
    if m := _CLAVE_DOC.match(clave or ""):
        return "Pedir SOAT" if m.group(1) == "soat" else "Ver CDA"
    if (clave or "").startswith(("plan:", "recordar:")):
        return "Buscar taller"
    return "Ver" if (clave or "").startswith("pyp:") else ""


def es_urgente(clave, hoy=None):
    """Documento urgente o vencido según la escala (por la fecha guardada en la clave), o pico y placa de hoy."""
    clave = clave or ""
    hoy = hoy or timezone.localdate()
    if m := _CLAVE_VENCE.match(clave):
        return nivel_documento((date.fromisoformat(m.group(1)) - hoy).days) in ("urgente", "vencido")
    if clave.startswith("plan:") and ":vencido:" in clave:
        return True  # mantenimiento en rojo ("Toca ya"): mismo criterio que la agenda
    return clave.startswith("pyp:") and clave.endswith(f":{hoy}")


def url_talleres(servicio_ids, moto):
    """Directorio de talleres filtrado por el servicio, si es uno solo; si no, el plan de mantenimiento de la moto."""
    ids = {i for i in servicio_ids if i}
    if len(ids) == 1:
        return f"{reverse('talleres:inicio')}?servicio={ids.pop()}"
    return f"{moto.get_absolute_url()}#plan"


def url_solucion(clave):
    """Página que resuelve el aviso, deducida de su clave. Sirve también para las notificaciones ya guardadas
    con el enlace viejo. None: usar el enlace guardado (p. ej. pico y placa va a la ficha de la moto)."""
    partes = (clave or "").split(":")
    if len(partes) < 3 or not partes[1].isdigit():
        return None
    tipo, moto_id = partes[0], int(partes[1])
    if tipo == "doc" and partes[2] in ("soat", "tecno"):
        return f"{reverse('tramites:soat' if partes[2] == 'soat' else 'tramites:tecnomecanica')}?moto={moto_id}"
    if tipo not in ("plan", "recordar"):
        return None
    from .models import Moto, TareaMantenimiento
    moto = Moto.objects.filter(pk=moto_id).first()
    if not moto:
        return None
    if tipo == "recordar":
        servicio = TareaMantenimiento.objects.filter(pk=partes[2]).values_list("servicio_id", flat=True).first()             if partes[2].isdigit() else None
        return url_talleres([servicio], moto)
    from .plan import calcular_plan
    return url_talleres([t.tarea.servicio_id for t in calcular_plan(moto).tareas if t.estado == partes[2]], moto)


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
            nivel = "alerta" if nivel_documento(dias) == "urgente" else "aviso"
        texto = f"{moto} · {'venció' if dias < 0 else 'vence'} el {doc['vence']:%d/%m/%Y}"
        if doc["estimado"]:
            texto += " (calculado con la fecha de matrícula)"
        avisos.append({
            "clave": f"doc:{moto.pk}:{doc['clave']}:{etapa}:{doc['vence']}", "titulo": titulo, "texto": texto,
            # Lleva a la solución: cotizar el SOAT o elegir un CDA para la técnico-mecánica
            "url": reverse("tramites:soat" if doc["clave"] == "soat" else "tramites:tecnomecanica") + f"?moto={moto.pk}",
            "accion": accion_de_clave(f"doc:{moto.pk}:{doc['clave']}:"),
            "tipo": "documento", "nivel": nivel, "dias": dias,
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
            "url": f"{moto.get_absolute_url()}#pico-placa", "accion": "Ver", "tipo": "general", "nivel": "alerta", "dias": 0}


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


def notificar_todas(hoy=None, ahora=None):
    """Avisos de todas las motos (lo usan el comando para cron y el endpoint de tareas). Idempotente."""
    from .models import Moto

    ahora = timezone.localtime(ahora) if ahora else timezone.localtime()
    hoy = hoy or ahora.date()
    # El de pico y placa es del mismo día: después de las 8 p. m. ya no sirve.
    pico_placa = hoy != ahora.date() or ahora.hour < 20
    motos = Moto.objects.filter(motociclista__usuario__isnull=False).select_related(
        "motociclista__usuario", "linea", "linea__marca")
    return sum(notificar_moto(m, hoy, pico_placa) for m in motos.iterator())
