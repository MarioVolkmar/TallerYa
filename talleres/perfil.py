"""Información estandarizada del perfil del taller: listas cerradas (especialidades, compromisos), el equipo y el
estado «abierto ahora». Todo lo usa el detalle, el formulario del panel y el JSON-LD."""
from django.utils import timezone

# Especialidades: lista cerrada para que se puedan comparar y filtrar talleres (clave, texto)
ESPECIALIDADES = [
    ("inyeccion", "Inyección electrónica"),
    ("carburacion", "Carburación"),
    ("scooters", "Scooters y CVT"),
    ("trabajo", "Motos de trabajo"),
    ("alta", "Alta cilindrada"),
    ("trail", "Trail y doble propósito"),
    ("electrico", "Sistema eléctrico y escáner"),
    ("suspension", "Suspensiones"),
    ("frenos", "Frenos y ABS"),
    ("arrastre", "Kit de arrastre"),
    ("motor", "Reparación de motor"),
    ("electricas", "Motos eléctricas"),
    ("pintura", "Latonería y pintura"),
    ("tecnomecanica", "Preparación técnico-mecánica"),
]
ESPECIALIDADES_DICT = dict(ESPECIALIDADES)

# Compromisos de «Cómo trabajamos» (clave, texto, ícono). La garantía va aparte (garantia_meses).
COMPROMISOS = [
    ("fotos", "Te mandamos fotos por WhatsApp", "📸"),
    ("presupuesto", "Presupuesto antes de empezar", "📝"),
    ("piezas", "Te devolvemos las piezas cambiadas", "🔩"),
    ("avisamos", "Te avisamos antes de cambiar algo no cotizado", "📞"),
    ("factura", "Repuestos con factura", "🧾"),
]
COMPROMISOS_DICT = {c: (t, i) for c, t, i in COMPROMISOS}

MAXIMO_EQUIPO = 6
ROLES = ["Jefe de taller", "Técnico", "Ayudante", "Otro"]
OTRA = "otra"  # valor del select de especialidad cuando no está en el catálogo de servicios

# Texto libre antiguo → servicio más cercano (palabra clave sin tildes → inicio del nombre del servicio)
_CLAVES_SERVICIO = [
    ("aceite", "cambio de aceite"), ("freno", "frenos"), ("suspens", "suspension"), ("horquilla", "suspension"),
    ("amortigua", "suspension"), ("llanta", "llantas"), ("neumatic", "llantas"), ("electric", "sistema electrico"),
    ("escaner", "sistema electrico"), ("latoner", "latoneria"), ("pintura", "latoneria"), ("tecnico-mec", "revision"),
    ("tecnomec", "revision"), ("tecnico mec", "revision"), ("arrastre", "kit de arrastre"), ("sincroniz", "sincroniz"),
    ("inyeccion", "sincroniz"), ("carburacion", "sincroniz"), ("afinacion", "sincroniz"), ("mantenimiento", "mantenimiento"),
]


def _sin_tildes(t):
    import unicodedata
    return unicodedata.normalize("NFKD", str(t).lower()).encode("ascii", "ignore").decode()


def servicio_cercano(texto, servicios):
    """id del servicio que mejor describe un texto libre, o None si no hay coincidencia clara.
    `servicios`: iterable de (id, nombre). Si el texto nombra varias cosas, gana la primera que aparezca."""
    t = _sin_tildes(texto)
    nombres = [(i, _sin_tildes(n)) for i, n in servicios]
    for n in nombres:  # nombre exacto
        if t.strip() == n[1]:
            return n[0]
    hallazgos = sorted((t.find(c), prefijo) for c, prefijo in _CLAVES_SERVICIO if c in t)
    for _, prefijo in hallazgos:
        for i, n in nombres:
            if n.startswith(prefijo):
                return i
    return None


def rol_cercano(texto):
    """Rol de la lista corta más parecido a un texto libre (si no se reconoce, «Otro»)."""
    t = _sin_tildes(texto)
    if not t.strip():
        return ""
    if any(k in t for k in ("jefe", "duen", "propiet", "gerente", "administr")):
        return "Jefe de taller"
    if any(k in t for k in ("ayudante", "aprendiz", "auxiliar")):
        return "Ayudante"
    if any(k in t for k in ("tecnic", "mecanic", "sena")):
        return "Técnico"
    return "Otro"
MAXIMO_DESCRIPCION = 300


def equipo_limpio(equipo):
    """Lista de mecánicos válida (ignora entradas mal formadas o sin nombre)."""
    salida = []
    for m in equipo or []:
        if isinstance(m, dict) and str(m.get("nombre", "")).strip():
            anios = m.get("anios")
            salida.append({"nombre": str(m["nombre"]).strip(), "rol": str(m.get("rol", "")).strip(),
                           "anios": anios if isinstance(anios, int) and anios > 0 else None,
                           "especialidad": str(m.get("especialidad", "")).strip(),
                           "servicio": m["servicio"] if isinstance(m.get("servicio"), int) else None})
    return salida[:MAXIMO_EQUIPO]


def especialidades_texto(claves):
    return [ESPECIALIDADES_DICT[c] for c in claves or [] if c in ESPECIALIDADES_DICT]


def compromisos_lista(taller):
    """[(ícono, texto)] para «Cómo trabajamos», con la garantía primero si la hay."""
    lista = []
    if taller.garantia_meses:
        n = taller.garantia_meses
        lista.append(("🛡️", f"Garantía de {n} {'mes' if n == 1 else 'meses'} en mano de obra"))
    lista += [(COMPROMISOS_DICT[c][1], COMPROMISOS_DICT[c][0]) for c in taller.compromisos or [] if c in COMPROMISOS_DICT]
    return lista


def _hora(h):
    return f"{h.hour % 12 or 12}:{h.minute:02d} {'a. m.' if h.hour < 12 else 'p. m.'}"


_DIAS = ["el lunes", "el martes", "el miércoles", "el jueves", "el viernes", "el sábado", "el domingo"]


def estado_horario(taller, turnos, ahora=None):
    """{"abierto": bool, "texto": "..."} según los turnos de la agenda; None si no hay turnos (se muestra el texto libre)."""
    if taller.abierto_24h:
        return {"abierto": True, "texto": "Abierto 24 horas"}
    if not turnos:
        return None
    ahora = ahora or timezone.localtime()
    dia, hora = ahora.weekday(), ahora.time()
    for t in sorted(turnos, key=lambda t: t.abre):
        if t.dia == dia and t.abre <= hora < t.cierra:
            return {"abierto": True, "texto": f"Abierto ahora · cierra a las {_hora(t.cierra)}"}
    for n in range(8):  # el próximo turno: hoy más tarde, mañana o en los días siguientes
        d = (dia + n) % 7
        proximos = sorted(t.abre for t in turnos if t.dia == d and (n or t.abre > hora))
        if proximos:
            cuando = "hoy" if n == 0 else "mañana" if n == 1 else _DIAS[d]
            return {"abierto": False, "texto": f"Cerrado · abre {cuando} a las {_hora(proximos[0])}"}
    return {"abierto": False, "texto": "Cerrado"}
