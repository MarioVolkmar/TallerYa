"""El camino del motero en un solo lugar: pedido → confirmado → en el taller → lista → hoja de vida → reseña.

Une lo que ya existe (SolicitudCita / SolicitudVisita, TrabajoEnCurso de «Mi día», ServicioTaller y las reseñas)
para pintar los pasos y el siguiente botón en «Mis citas», la página de la cita o visita y el garaje.
Solo lee: no cambia estados (eso sigue en talleres/views, domicilio/vista_solicitudes y talleres/herramientas).
"""
from django.urls import reverse

from garaje.models import ServicioTaller, TrabajoEnCurso
from talleres.models import SolicitudCita, Taller

ESPERANDO = ("reprogramada", "cotizada")  # el negocio respondió y falta el sí del motero


def es_cita(pedido):
    return isinstance(pedido, SolicitudCita)


def prestador_de(pedido):
    return pedido.taller if es_cita(pedido) else pedido.mecanico


def url_pedido(pedido):
    """La página del pedido para el motero: con cuenta, el detalle de «Mis citas»; si no, la página pública."""
    if es_cita(pedido):
        if pedido.usuario_id:
            return reverse("cuentas:cita", args=[pedido.pk])
        return reverse("talleres:cita_publica", args=[pedido.token]) if pedido.token else pedido.taller.get_absolute_url()
    return pedido.get_absolute_url() if pedido.token else pedido.mecanico.get_absolute_url()


def url_responder(pedido):
    """Donde se acepta o rechaza la cotización o la nueva fecha (páginas públicas con token)."""
    if not pedido.token:
        return ""
    return reverse("talleres:cita_publica", args=[pedido.token]) if es_cita(pedido) else pedido.get_absolute_url()


def url_calificar(pedido):
    return prestador_de(pedido).get_absolute_url() + "?calificar=1"


def _cuando(pedido, taller):
    fecha = pedido.fecha_preferida if taller else pedido.fecha_propuesta
    if not fecha:
        return "Por acordar fecha"
    return f"Llévala el {fecha:%d/%m}" if taller else f"Visita el {fecha:%d/%m}"


def _ya_califico(prestador, usuario, desde=None):
    """¿Calificó esta vez? Al taller se le deja una reseña por visita (cuenta la hecha después del pedido); al
    mecánico, una por cuenta que se edita (cuenta cualquiera)."""
    if not (usuario and getattr(usuario, "pk", None)):
        return False
    resenas = prestador.resenas.filter(usuario=usuario)
    if desde is not None and isinstance(prestador, Taller):
        resenas = resenas.filter(creado__gte=desde)
    return resenas.exists()


def estado(pedido, usuario=None):
    """Pasos y siguiente acción del pedido. usuario: quien mira (para saber si ya calificó)."""
    prestador = prestador_de(pedido)
    taller = es_cita(pedido)
    if pedido.estado == "cancelada":
        return {"cancelada": True, "pasos": [], "siguiente": None, "prestador": prestador}
    trabajo = pedido.trabajos.order_by("-recibida").first()
    servicio = (pedido.servicios_hechos.exclude(estado=ServicioTaller.Estado.RECHAZADO).order_by("-pk").first())
    usuario = usuario or pedido.usuario
    califico = _ya_califico(prestador, usuario, pedido.creado)
    t = trabajo.estado if trabajo else ""
    E = TrabajoEnCurso.Estado
    atendida = pedido.estado == "atendida" or t == E.ENTREGADA or servicio is not None
    verificado = servicio is not None and servicio.estado == ServicioTaller.Estado.VERIFICADO
    confirmada = pedido.estado in ("confirmada", "atendida") or bool(trabajo) or servicio is not None

    def paso(clave, titulo, hecho, detalle=""):
        return {"clave": clave, "titulo": titulo, "hecho": hecho, "detalle": detalle}

    trabajando = "En el taller" if taller else "Trabajando"
    pasos = [
        paso("pedida", "Pedida", True),
        paso("confirmada", "Confirmada", confirmada,
             "Falta tu respuesta" if pedido.estado in ESPERANDO else "Esperando respuesta"),
        paso("taller", trabajando, t in (E.LISTA, E.ENTREGADA) or atendida,
             "En reparación" if t == E.EN_REPARACION else "Recibida" if t else _cuando(pedido, taller)),
        paso("lista", "Lista", t == E.ENTREGADA or atendida, "Pasa a recogerla" if taller else "Terminó"),
        paso("hoja", "En tu hoja de vida", verificado, "Confírmalo" if servicio else "Lo registra el negocio"),
        paso("resena", "Calificada", califico and atendida, "Falta tu reseña"),
    ]
    # El paso actual es el primero sin hacer; solo ese muestra su detalle
    actual = next((p for p in pasos if not p["hecho"]), None)
    for p in pasos:
        p["actual"] = p is actual

    siguiente = None
    if pedido.estado in ESPERANDO:
        siguiente = {"texto": "Responder", "url": url_responder(pedido),
                     "nota": "Te enviaron una cotización o una fecha: acéptala o recházala."}
    elif t == E.LISTA:
        siguiente = {"texto": "", "url": "", "nota": "Tu moto está lista." +
                     (" Pasa a recogerla." if taller else "") + (f" Nota: {trabajo.nota}" if trabajo.nota else "")}
    elif servicio is not None and not verificado:
        siguiente = {"texto": "Confirmar el servicio", "url": servicio.get_absolute_url(),
                     "nota": "Confírmalo para que quede verificado en tu hoja de vida."}
    elif atendida and not califico:
        siguiente = {"texto": f"★ Calificar a {prestador.nombre}", "url": url_calificar(pedido),
                     "nota": "¿Cómo te fue? Tu reseña ayuda a otros moteros."}
    hoja = reverse("garaje:hoja_vida", args=[servicio.moto_id]) if verificado else ""
    return {"cancelada": False, "pasos": pasos, "siguiente": siguiente, "prestador": prestador, "trabajo": trabajo,
            "servicio": servicio, "url_hoja": hoja, "califico": califico, "es_taller": taller}


def en_curso(usuario):
    """Motos del motero que un negocio tiene entre manos ahora (para el garaje y Mi cuenta)."""
    if not getattr(usuario, "pk", None):
        return []
    lista = list(TrabajoEnCurso.objects.filter(usuario=usuario).exclude(estado=TrabajoEnCurso.Estado.ENTREGADA)
                 .select_related("taller", "mecanico", "cita", "visita").order_by("-recibida")[:3])
    for t in lista:
        pedido = t.cita or t.visita
        t.url = url_pedido(pedido) if pedido else t.negocio.get_absolute_url()
    return lista
