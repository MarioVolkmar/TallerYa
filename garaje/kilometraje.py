"""Kilometraje fácil: el motero casi nunca escribe el odómetro, así que se estima y se confirma con un toque.

- El perfil de uso (al registrar la moto) da un km/día inicial (plan._ritmo_perfil).
- Con dos o más lecturas el ritmo es el real (plan._ritmo_lecturas) y de ahí sale el km de hoy estimado.
- Cada cierto tiempo se le pregunta «¿vas por unos X km?»: Sí crea una LecturaKm.
- `registrar_lectura` es la única puerta para subir el km: la usan el motero, la confirmación y el taller (servicio_taller.aplicar)."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import LecturaKm
from .plan import RITMO_MAX, ritmo_km

# km por día típicos de cada perfil de uso (orientativos; se reemplazan por las lecturas reales)
KM_DIA_PERFIL = {"fines_semana": 9, "ciudad": 25, "trabajo": 70, "carretera": 45}
DIAS_ENTRE_PREGUNTAS = 30   # desde la última lectura
DIAS_POSPUESTA = 7          # tras «ahora no»
MIN_DIAS_ESTIMAR = 14       # menos que esto el ritmo no dice nada


def registrar_lectura(moto, km, fecha=None, estimada=False):
    """Guarda una lectura y, si el km sube, lo deja como km actual de la moto. Devuelve la lectura o None si el km
    no sube (una lectura menor no se guarda: la corrección del odómetro va por el formulario de km)."""
    fecha = fecha or timezone.localdate()
    if km <= moto.km_actual:
        return None
    with transaction.atomic():
        lectura = LecturaKm.objects.create(moto=moto, km=km, fecha=fecha, estimada=estimada)
        moto.km_actual = km
        moto.km_pregunta_pospuesta = None
        moto.save(update_fields=["km_actual", "km_pregunta_pospuesta"])
    return lectura


def km_estimado_hoy(moto, hoy=None):
    """Km que probablemente marca hoy el odómetro (redondeado a 100), o None si no hay con qué estimar."""
    hoy = hoy or timezone.localdate()
    ultima = moto.lecturas.order_by("-fecha", "-creado").first() if moto.pk else None
    fecha = ultima.fecha if ultima else (timezone.localdate(moto.creado) if moto.creado else hoy)
    dias = (hoy - fecha).days
    ritmo, _ = ritmo_km(moto, hoy)
    if not ritmo or dias < MIN_DIAS_ESTIMAR:
        return None
    km = round((moto.km_actual + ritmo * dias) / 100) * 100
    return km if km > moto.km_actual else None


def pregunta_km(moto, hoy=None):
    """{"km": estimado, "dias": desde la última lectura} si toca preguntar «¿vas por unos X km?», o None."""
    hoy = hoy or timezone.localdate()
    if moto.km_pregunta_pospuesta and (hoy - moto.km_pregunta_pospuesta).days < DIAS_POSPUESTA:
        return None
    ultima = moto.lecturas.order_by("-fecha", "-creado").first()
    if not ultima or (hoy - ultima.fecha).days < DIAS_ENTRE_PREGUNTAS:
        return None
    km = km_estimado_hoy(moto, hoy)
    return {"km": km, "dias": (hoy - ultima.fecha).days} if km else None


def km_valido(moto, km, hoy=None):
    """¿Es creíble que la moto tenga `km` hoy? (sube, y no más de lo que permite el ritmo máximo desde la última lectura)."""
    hoy = hoy or timezone.localdate()
    ultima = moto.lecturas.order_by("-fecha", "-creado").first()
    desde = ultima.fecha if ultima else hoy
    return moto.km_actual < km <= moto.km_actual + RITMO_MAX * max(1, (hoy - desde).days)
