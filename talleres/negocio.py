"""Negocio de servicio: el taller y el mecánico a domicilio como un solo negocio con dos variantes.

Los modelos y las tablas siguen separados (talleres.SolicitudCita y domicilio.SolicitudVisita); aquí se traducen
a una sola forma que consumen las plantillas compartidas (talleres/_solicitud.html), sin `if rol` en ellas.

Diferencias reales, como opciones de la variante:
- dónde se atiende: local con mapa (taller) o zona (mecánico);
- flujo: cita con fecha que se puede reprogramar (taller) o visita que se cotiza y confirma (mecánico);
- verificación, horario y tarifa de visita viven en sus perfiles (talleres/perfil.py, domicilio/identidad.py).
"""
from urllib.parse import quote

from django.urls import reverse
from django.utils import timezone

# Vocabulario único de estados en la interfaz (los valores guardados no cambian).
PENDIENTE, COTIZADA, ESPERANDO, CONFIRMADA, ATENDIDA, CANCELADA = (
    "Pendiente", "Cotizada", "Esperando al motero", "Confirmada", "Atendida", "Cancelada")
ABIERTOS = ("pendiente", "cotizada", "reprogramada", "confirmada")


def estado_texto(solicitud):
    """Nombre del estado para la interfaz. «reprogramada» del taller es «Cotizada» si lleva precio y
    «Esperando al motero» si solo propone otra fecha; «cotizada» del mecánico es «Cotizada»."""
    e = solicitud.estado
    if e == "reprogramada":
        return COTIZADA if solicitud.cotizacion_hasta else ESPERANDO
    return {"pendiente": PENDIENTE, "cotizada": COTIZADA, "confirmada": CONFIRMADA,
            "atendida": ATENDIDA, "cancelada": CANCELADA}.get(e, solicitud.get_estado_display())


def estado_clase(solicitud):
    """Clase del chip: la misma para el mismo nombre en las dos variantes."""
    return "cotizada" if solicitud.estado == "reprogramada" and solicitud.cotizacion_hasta else solicitud.estado


def _pesos(n):
    return "$" + f"{n:,}".replace(",", ".")


def precio_texto(s):
    if not s.cotizacion_hasta:
        return ""
    d, h = s.cotizacion_desde, s.cotizacion_hasta
    return _pesos(h) if d == h else f"{_pesos(d)} a {_pesos(h)}"


def _boton_cotizar(s, url, que, fecha, hora, texto=None, menu=False):
    return {"tipo": "cotizar", "url": url, "texto": texto or ("Cambiar cotización" if s.estado in ("cotizada", "reprogramada") else "Cotizar"),
            "nombre": s.nombre, "que": que, "fecha": fecha, "hora": hora, "menu": menu}


def _cancelar(s, url, fecha):
    return {"tipo": "cancelar", "url": url, "nombre": s.nombre, "fecha": fecha, "confirmada": s.estado == "confirmada"}


class Variante:
    """Lo que cambia entre taller y mecánico. Las subclases dicen cómo leer su solicitud y qué acciones permite."""
    clave = ""
    sustantivo = ""        # «cita» / «visita»
    ancla = ""             # prefijo del id en la lista (#cita-12, #visita-12)
    con_detalle = False    # la tarjeta abre la ventana de detalle al tocarla

    def preparar(self, lista, negocio, request=None):
        """Datos por lote (una consulta para todas) antes de armar las tarjetas."""
        return {}

    def tarjeta(self, s, extra, request=None):
        raise NotImplementedError

    def base(self, s, fecha, que, lugar=""):
        return {
            "obj": s, "pk": s.pk, "id": f"{self.ancla}-{s.pk}", "variante": self.clave, "sustantivo": self.sustantivo,
            "estado": s.estado, "estado_texto": estado_texto(s), "chip": estado_clase(s), "fecha": fecha, "nombre": s.nombre, "moto": s.moto,
            "que": que, "lugar": lugar, "creado": s.creado, "detalle": s.detalle, "con_detalle": self.con_detalle,
            "precio": precio_texto(s) if s.estado != "cancelada" else "", "incluye": s.cotizacion_incluye,
            "precio_vencio": s.estado in ("cotizada", "reprogramada") and s.cotizacion_vencida,
            "propuesta": None, "rechazo": "", "motivo": "", "vencida": False, "cupon": None, "registrado": False,
            "botones": [], "menu": [], "reabrir": False,
        }


class Taller(Variante):
    clave, sustantivo, ancla, con_detalle = "taller", "cita", "cita", True

    def preparar(self, lista, taller, request=None):
        from garaje.models import ServicioTaller
        ids = [c.pk for c in lista]
        con = set(ServicioTaller.objects.filter(cita_id__in=ids).values_list("cita_id", flat=True)) if ids else set()
        from .views import _whatsapp_cita
        return {"taller": taller, "con_servicio": con, "request": request, "wa": lambda c: _whatsapp_cita(c, taller, request)}

    def tarjeta(self, c, x, request=None):
        hoy = timezone.localdate()
        que = str(c.servicio) if c.servicio else "Servicio por definir"
        t = self.base(c, c.fecha_preferida, que)
        t["whatsapp_url"] = x["wa"](c)
        t["vencida"] = c.estado == "pendiente" and c.fecha_preferida < hoy
        t["registrado"] = c.pk in x["con_servicio"]
        t["motivo"] = c.motivo_cancelacion if c.estado == "cancelada" else ""
        if c.estado == "reprogramada":
            t["propuesta"] = {"fecha": c.fecha_propuesta, "hora": c.hora_propuesta}
        if c.propuesta_rechazada and c.estado == "pendiente":
            t["rechazo"] = "No pudo en la fecha que propusiste: escríbele para acordar otra."
        url_estado = reverse("talleres:cita_estado", args=[c.pk])
        t["form"] = url_estado
        fecha_prop = c.fecha_propuesta or c.fecha_preferida
        cotizar = _boton_cotizar(c, reverse("talleres:cita_cotizar", args=[c.pk]), str(c.servicio) if c.servicio else c.moto,
                                 fecha_prop, c.hora_propuesta or c.hora)
        registrar = {"tipo": "enlace", "url": reverse("talleres:servicio_cita", args=[c.pk]), "texto": "Registrar servicio", "clase": "ok"}
        if c.estado == "pendiente" or (c.estado == "reprogramada" and c.cotizacion_hasta):
            t["botones"].append(cotizar)
        if c.estado == "pendiente":
            t["botones"].append({"tipo": "estado", "valor": "confirmada", "texto": "Confirmar", "clase": "ok"})
        elif c.estado == "confirmada" or (c.estado == "atendida" and not t["registrado"]):
            t["botones"].append(registrar)
        if c.estado in ("pendiente", "confirmada", "reprogramada"):
            t["menu"] = [{"tipo": "reprogramar", "url": reverse("talleres:cita_reprogramar", args=[c.pk]), "nombre": c.nombre,
                          "fecha": fecha_prop, "texto": "Cambiar propuesta" if c.estado == "reprogramada" else "Reprogramar"},
                         _cancelar(c, url_estado, c.fecha_preferida)]
        else:
            t["reabrir"] = True
        return t


class Mecanico(Variante):
    clave, sustantivo, ancla = "mecanico", "visita", "visita"

    def preparar(self, lista, mecanico, request=None):
        con = set(mecanico.servicios_hechos.exclude(estado="rechazado").filter(solicitud__isnull=False)
                  .values_list("solicitud_id", flat=True))
        from domicilio.views import CUANDO
        return {"con_servicio": con, "puede_registrar": mecanico.estado == mecanico.Estado.APROBADO, "cuando": dict(CUANDO), "quien": mecanico.nombre}

    def tarjeta(self, s, x, request=None):
        que = str(s.servicio) if s.servicio else "Diagnóstico"
        lugar = " · ".join(p for p in (str(s.zona) if s.zona else "", x["cuando"].get(s.cuando, "")) if p)
        t = self.base(s, s.fecha_propuesta or s.creado, que, lugar)
        t["whatsapp_url"] = f"https://wa.me/{s.telefono}?text={quote(f"Hola {s.nombre}, te escribe {x['quien']} por tu solicitud de visita en TallerYa.")}"
        t["registrado"] = s.pk in x["con_servicio"]
        if s.fecha_propuesta and s.estado in ("cotizada", "confirmada"):
            t["fecha_hora"] = {"fecha": s.fecha_propuesta, "hora": s.hora_propuesta}
        if s.rechazada and s.estado == "pendiente":
            t["rechazo"] = "No aceptó tu cotización: escríbele para acordar otra opción."
        abierta = s.estado in ("pendiente", "cotizada", "confirmada")
        if s.codigo_cupon_id:
            t["cupon"] = {"titulo": s.codigo_cupon.cupon.titulo, "codigo": s.codigo_cupon.codigo, "usado": s.codigo_cupon.canjeado}
        elif abierta:
            t["cupon_anotar"] = reverse("domicilio:solicitud_descuento", args=[s.pk])
        url_estado = reverse("domicilio:solicitud_estado", args=[s.pk])
        t["form"] = url_estado
        hoy = timezone.localdate()
        url_cot = reverse("domicilio:solicitud_cotizar", args=[s.pk])
        cotizar = _boton_cotizar(s, url_cot, que, s.fecha_propuesta or hoy, s.hora_propuesta)
        puede = x["puede_registrar"]
        registrar = {"tipo": "enlace", "url": reverse("garaje:servicio_visita", args=[s.pk]), "texto": "Registrar servicio", "clase": "ok"}
        atendida = {"tipo": "estado", "valor": "atendida", "texto": "Marcar atendida", "clase": "ok"}
        if s.estado in ("pendiente", "cotizada"):
            t["botones"].append(cotizar)
        if s.estado == "pendiente":
            t["botones"].append({"tipo": "estado", "valor": "confirmada", "texto": "Confirmar", "clase": "ok"})
        elif s.estado == "confirmada":
            t["botones"].append(registrar if puede and not t["registrado"] else atendida)
        elif s.estado == "atendida" and puede and not t["registrado"]:
            t["botones"].append(registrar)
        if abierta:
            if s.estado == "confirmada":
                t["menu"].append(_boton_cotizar(s, url_cot, que, s.fecha_propuesta or hoy, s.hora_propuesta, texto="Reprogramar", menu=True))
                if puede and not t["registrado"]:
                    t["menu"].append(dict(atendida, menu=True))
            t["menu"].append(_cancelar(s, url_estado, s.fecha_propuesta or s.creado))
        return t


# ---- Reseñas: la misma nota y la misma selección para el panel en las dos variantes ----
RESENAS_PANEL = 4


def nota(resenas):
    from django.db.models import Avg, Count
    n = resenas.aggregate(prom=Avg("estrellas"), n=Count("id"))
    n["pct"] = round((n["prom"] or 0) * 20)
    return n


def resenas_panel(resenas):
    """Primero las que faltan por responder; el resto está en la página de reseñas."""
    return sorted(resenas.order_by("-creado")[:20], key=lambda r: bool(r.respuesta))[:RESENAS_PANEL]


def contexto_resenas(request, todas):
    """Página «Mis reseñas» (las dos variantes): filtro sin responder, por estrellas, reparto y páginas de 10."""
    from django.core.paginator import Paginator
    from django.db.models import Count
    filtro = request.GET.get("ver", "todas")
    lista = todas.filter(respuesta="") if filtro == "sin_responder" else todas
    estrellas = request.GET.get("estrellas", "")
    if estrellas in {"1", "2", "3", "4", "5"}:
        lista = lista.filter(estrellas=int(estrellas))
    reparto = {r["estrellas"]: r["n"] for r in todas.values("estrellas").annotate(n=Count("id"))}
    n = nota(todas)
    return {"pagina": Paginator(lista.order_by("-creado"), 10).get_page(request.GET.get("pagina")),
            "filtro": filtro, "estrellas": estrellas, "nota": n, "sin_responder": todas.filter(respuesta="").count(),
            "reparto": [(e, reparto.get(e, 0), round(reparto.get(e, 0) * 100 / n["n"]) if n["n"] else 0) for e in (5, 4, 3, 2, 1)]}


# ---- «Por hacer» del panel: una lista de datos; cada variante suma sus tareas propias ----
def tarea(texto, url, boton, urgente=False):
    return {"texto": texto, "url": url, "boton": boton, "urgente": urgente}


def _cuantas(n, singular, plural):
    from django.utils.html import format_html
    return format_html("<strong>{} {}</strong>", n, singular if n == 1 else plural)


def tareas_comunes(*, por_responder=0, palabra=("cita", "citas"), que="por confirmar", url_solicitudes="", boton="Responder",
                   precios_por_confirmar=False, url_precios="", sin_responder=0, url_resenas=""):
    """Tareas que tienen el taller y el mecánico (solicitudes por responder, precios viejos, reseñas sin responder)."""
    from django.utils.html import format_html
    t = []
    if por_responder:
        t.append(tarea(format_html("{} {}", _cuantas(por_responder, *palabra), que), url_solicitudes, boton, True))
    if precios_por_confirmar:
        t.append(tarea("Tus precios de mano de obra llevan más de 2 meses sin confirmarse", url_precios, "Confirmar", True))
    if sin_responder:
        t.append(tarea(format_html("{} sin responder", _cuantas(sin_responder, "reseña", "reseñas")), url_resenas, "Responder"))
    return t


def cupones_con_cifras(cupones):
    """Cupones del negocio con entregados y canjeados (taller y mecánico usan el mismo cupones.Cupon)."""
    from django.db.models import Count, F, Q
    return (cupones.annotate(entregados=Count("codigos", distinct=True),
                             canjeados=Count("codigos", filter=Q(codigos__canjeado_en__isnull=False), distinct=True),
                             num_emitidos=F("entregados"))  # Cupon.restantes lo reutiliza sin consultar
            .order_by("-activo", "-creado"))


VARIANTES = {"taller": Taller(), "mecanico": Mecanico()}


def variante_de(negocio):
    from domicilio.models import MecanicoDomicilio
    return VARIANTES["mecanico" if isinstance(negocio, MecanicoDomicilio) else "taller"]


def tarjetas(lista, negocio, request=None):
    """Lista de solicitudes (citas o visitas) → tarjetas para talleres/_solicitud.html."""
    v = variante_de(negocio)
    lista = list(lista)
    extra = v.preparar(lista, negocio, request)
    return [v.tarjeta(s, extra, request) for s in lista]


def datos_tarjeta(solicitud, request=None):
    """Una sola tarjeta (atajo para pruebas y vistas de detalle)."""
    negocio = getattr(solicitud, "taller", None) or solicitud.mecanico
    return tarjetas([solicitud], negocio, request)[0]


def acciones(solicitud, request=None):
    """Acciones que el flujo de la variante permite en el estado actual: {"botones": [...], "menu": [...]}."""
    t = datos_tarjeta(solicitud, request)
    return {"botones": t["botones"], "menu": t["menu"], "reabrir": t["reabrir"]}


def _plural(n, uno, varios):
    return f"{n} {uno if n == 1 else varios}"


def dato_resenas(promedio, cuantas):
    """Dato corto para el resumen de la sección plegable «Reseñas»: «4,5 ★ · 12 reseñas»."""
    if not cuantas:
        return "Sin reseñas aún"
    nota = f"{promedio:.1f}".replace(".", ",") if promedio else "–"
    return f"{nota} ★ · {_plural(cuantas, 'reseña', 'reseñas')}"


def dato_cantidad(n, uno, varios):
    return _plural(n, uno, varios)
