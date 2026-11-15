"""Emergencias: qué talleres están abiertos ahora según su horario (HorarioTaller) o porque abren 24 h."""
from django.utils import timezone


def abierto_ahora(taller, ahora=None, turnos=None):
    """True / False según el horario; None si el taller no ha registrado horario (no se sabe).
    `turnos` evita otra consulta cuando los horarios vienen precargados (prefetch_related("horarios"))."""
    if taller.abierto_24h:
        return True
    ahora = ahora or timezone.localtime()
    turnos = list(taller.horarios.all()) if turnos is None else turnos
    if not turnos:
        return None
    dia, hora = ahora.weekday(), ahora.time()
    return any(t.dia == dia and t.abre <= hora < t.cierra for t in turnos)


def ordenar_por_barrio(talleres, barrio):
    """Sin ubicación del navegador: primero los del barrio elegido, luego los de su ciudad y después el resto."""
    if not barrio:
        return talleres
    return sorted(talleres, key=lambda t: (t.barrio_id != barrio.pk, t.barrio.ciudad != barrio.ciudad))


# Flujo "¿Te varaste?" (los íconos están en _icono_emergencia.html): cada opción filtra los talleres de emergencias por lo que atienden
OPCIONES = {
    "grua": ("Necesito grúa", {"grua": True}),
    "pinchazo": ("Pinchazo", {"despinche_domicilio": True}),
    "no_prende": ("No prende o se apagó", {}),
    "gasolina": ("Me quedé sin gasolina", {"gasolina_domicilio": True}),
    "accidente": ("Accidente", {"grua": True}),
}
CON_GRUAS = {None, "grua", "accidente"}


def grua_abierta(grua, ahora=None):
    """True / False según su horario diario (admite cierre después de medianoche); None si no lo registró."""
    if grua.abierto_24h:
        return True
    if not (grua.abre and grua.cierra):
        return None
    hora = (ahora or timezone.localtime()).time()
    if grua.abre < grua.cierra:
        return grua.abre <= hora < grua.cierra
    return hora >= grua.abre or hora < grua.cierra


def ordenar_gruas(gruas, municipio=None, ahora=None):
    """Abiertas ahora primero (luego sin horario y cerradas); dentro de cada grupo, las que cubren el municipio."""
    orden = {True: 0, None: 1, False: 2}
    for g in gruas:
        g.abierto = grua_abierta(g, ahora)
    return sorted(gruas, key=lambda g: (orden[g.abierto], bool(municipio) and municipio not in g.municipios))


def mensaje_grua(moto=None):
    """Texto base del WhatsApp; la ubicación la agrega el navegador solo si el motero la compartió."""
    return f"Necesito grúa para mi moto {moto}" if moto else "Necesito grúa para mi moto"
