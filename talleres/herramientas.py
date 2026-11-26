"""Herramientas del día a día del negocio (taller o mecánico a domicilio), una sola implementación para los dos.

Módulo apagable «herramientas_activo» (consola › Configuración; rutas /mi-negocio/). Tres piezas:
- Agenda: las citas (talleres.SolicitudCita) y visitas (domicilio.SolicitudVisita) que ya existen, por día. El negocio
  también puede anotar una cita que le llegó por teléfono: se guarda en esos mismos modelos, ya confirmada.
- Motos en el taller: garaje.TrabajoEnCurso, recibida → en reparación → lista → entregada. «Lista» avisa al dueño
  (notificaciones: push y, sin push, correo de respaldo). «Entregada» lleva a registrar el servicio (flujo existente).
- Recordatorios: a los clientes cuyo último servicio verificado lo hizo este negocio, cuando su plan de mantenimiento
  dice que toca, les llega un aviso para agendar con él (comando recordar_clientes y botón manual).
"""
import hashlib
import secrets
from datetime import timedelta
from urllib.parse import quote

from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from . import negocio as neg

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
DIAS_LARGOS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
DIAS_AGENDA = 7
MAX_CLIENTES = 60  # motos revisadas por página de recordatorios


# ---------- quién es el negocio ----------
def negocio_de(usuario):
    """El taller o el mecánico a domicilio de esta cuenta (o None)."""
    if not getattr(usuario, "is_authenticated", False):
        return None
    return getattr(usuario, "taller", None) or getattr(usuario, "mecanico_domicilio", None)


def es_taller(negocio):
    return neg.variante_de(negocio).clave == "taller"


def filtro_negocio(negocio):
    """{"taller": x} o {"mecanico": x}: el mismo par de campos en TrabajoEnCurso y ServicioTaller."""
    return {"taller": negocio} if es_taller(negocio) else {"mecanico": negocio}


def url_ficha(negocio):
    return negocio.get_absolute_url() if negocio.slug else ""


def url_agendar(negocio, servicio_id=None):
    """Donde el cliente pide cita o visita con este negocio (la ficha, con el formulario abierto si es taller)."""
    url = url_ficha(negocio)
    if not url:
        return ""
    if es_taller(negocio):
        url += "?agendar=1" + (f"&servicio={servicio_id}" if servicio_id else "")
    return url


def whatsapp(telefono, texto):
    num = "".join(c for c in (telefono or "") if c.isdigit())
    if len(num) == 10:
        num = "57" + num
    return f"https://wa.me/{num}?text={quote(texto)}" if num else ""


def usuario_por_celular(telefono):
    """Cuenta del motero con ese celular (para avisarle), o None."""
    from cupones.models import Motociclista
    from .utils import normalizar_celular
    try:
        cel = normalizar_celular(telefono)
    except Exception:
        return None
    m = Motociclista.objects.filter(celular=cel, usuario__isnull=False).select_related("usuario").first()
    return m.usuario if m else None


def servicios_del_negocio(negocio):
    """Opciones del campo «servicio» al anotar una cita: los servicios que ofrece."""
    return list(negocio.servicios.order_by("nombre")) if es_taller(negocio) else list(negocio.servicios.all())


# ---------- agenda ----------
def _hora(h):
    return f"{h.hour % 12 or 12}:{h.minute:02d} {'a. m.' if h.hour < 12 else 'p. m.'}" if h else ""


def _items_taller(taller, desde, hasta):
    ab = ("pendiente", "confirmada", "reprogramada")
    citas = (taller.solicitudes.select_related("servicio").filter(estado__in=ab)
             .filter(Q(fecha_preferida__range=(desde, hasta)) | Q(estado="reprogramada", fecha_propuesta__range=(desde, hasta))))
    for c in citas:
        fecha, hora = (c.fecha_propuesta, c.hora_propuesta) if c.estado == "reprogramada" else (c.fecha_preferida, c.hora)
        yield {"origen": "cita", "obj": c, "pk": c.pk, "fecha": fecha, "hora": hora, "nombre": c.nombre, "telefono": c.telefono,
               "moto": c.moto, "que": str(c.servicio) if c.servicio else "Servicio por definir", "detalle": c.detalle,
               "confirmada": c.estado == "confirmada", "url": reverse("talleres:citas_taller") + f"?q={quote(c.nombre)}"}


def _items_mecanico(mecanico, desde, hasta):
    visitas = (mecanico.solicitudes.select_related("servicio", "zona").filter(estado__in=("pendiente", "cotizada", "confirmada"))
               .filter(Q(fecha_propuesta__range=(desde, hasta)) | Q(fecha_propuesta__isnull=True, estado="pendiente")))
    for v in visitas:
        yield {"origen": "visita", "obj": v, "pk": v.pk, "fecha": v.fecha_propuesta, "hora": v.hora_propuesta, "nombre": v.nombre,
               "telefono": v.telefono, "moto": v.moto or "Moto sin indicar", "que": str(v.servicio) if v.servicio else "Diagnóstico",
               "detalle": " · ".join(p for p in (str(v.zona) if v.zona else "", v.detalle) if p),
               "confirmada": v.estado == "confirmada", "url": reverse("domicilio:solicitudes") + f"#visita-{v.pk}"}


def agenda(negocio, hoy=None):
    """Días de la agenda (hoy y los 6 siguientes) con sus citas o visitas, y las que no tienen fecha aún."""
    hoy = hoy or timezone.localdate()
    hasta = hoy + timedelta(days=DIAS_AGENDA - 1)
    items = list((_items_taller if es_taller(negocio) else _items_mecanico)(negocio, hoy, hasta))
    recibidas = trabajos_por_origen(negocio, items)
    quien = negocio.nombre
    for it in items:
        it["estado_texto"], it["chip"] = neg.estado_texto(it["obj"]), neg.estado_clase(it["obj"])
        it["hora_texto"] = _hora(it["hora"])
        it["trabajo"] = recibidas.get((it["origen"], it["pk"]))
        it["whatsapp"] = whatsapp(it["telefono"], f"Hola {it['nombre']}, te escribe {quien} por tu {'cita' if it['origen'] == 'cita' else 'visita'} en TallerYa.")
    dias = []
    for n in range(DIAS_AGENDA):
        f = hoy + timedelta(days=n)
        del_dia = sorted((i for i in items if i["fecha"] == f), key=lambda i: (i["hora"] is None, i["hora"] or 0))
        titulo = "Hoy" if n == 0 else "Mañana" if n == 1 else DIAS_LARGOS[f.weekday()]
        dias.append({"fecha": f, "titulo": titulo, "corto": DIAS[f.weekday()], "items": del_dia, "n": len(del_dia), "hoy": n == 0})
    sin_fecha = [i for i in items if i["fecha"] is None]
    return {"dias": dias, "sin_fecha": sin_fecha, "total": len(items)}


def anotar_cita(negocio, datos):
    """Cita (o visita) que el negocio anota él mismo: queda confirmada y, si el celular es de un motero con cuenta,
    enlazada a él y avisada. `datos`: nombre, telefono, moto, servicio (obj o None), fecha, hora, detalle."""
    from notificaciones.models import Notificacion
    from notificaciones.servicios import notificar
    usuario = usuario_por_celular(datos["telefono"])
    comun = {"nombre": datos["nombre"], "telefono": datos["telefono"], "moto": datos["moto"], "servicio": datos.get("servicio"),
             "usuario": usuario, "estado": "confirmada"}
    if es_taller(negocio):
        from .models import SolicitudCita
        s = SolicitudCita(taller=negocio, fecha_preferida=datos["fecha"], hora=datos.get("hora"), detalle=datos.get("detalle", ""), **comun)
        s.token = secrets.token_urlsafe(16)  # página pública de la cita, como cuando el taller la cotiza
        s.save()
        url = reverse("talleres:cita_publica", args=[s.token])
        palabra = "cita"
    else:
        from domicilio.models import SolicitudVisita
        s = SolicitudVisita.objects.create(mecanico=negocio, fecha_propuesta=datos["fecha"], hora_propuesta=datos.get("hora"),
                                           detalle=(datos.get("detalle") or "")[:300], **comun)
        url = reverse("domicilio:visita_publica", args=[s.token])
        palabra = "visita"
    if usuario:
        cuando = f"{datos['fecha']:%d/%m}" + (f" a las {_hora(datos.get('hora'))}" if datos.get("hora") else "")
        notificar(usuario, f"{palabra}-agendada:{s.pk}", f"{negocio.nombre} te agendó una {palabra}",
                  f"El {cuando} · {datos['moto']}.", url, Notificacion.Tipo.TALLER)
    return s


# ---------- motos en el taller ----------
def trabajos(negocio):
    from garaje.models import TrabajoEnCurso
    return TrabajoEnCurso.objects.filter(**filtro_negocio(negocio))


def trabajos_por_origen(negocio, items):
    """{("cita", pk) | ("visita", pk): trabajo} de las citas/visitas de la agenda que ya se recibieron."""
    citas = [i["pk"] for i in items if i["origen"] == "cita"]
    visitas = [i["pk"] for i in items if i["origen"] == "visita"]
    if not (citas or visitas):
        return {}
    out = {}
    for t in trabajos(negocio).filter(Q(cita_id__in=citas) | Q(visita_id__in=visitas)):
        if t.cita_id:
            out[("cita", t.cita_id)] = t
        if t.visita_id:
            out[("visita", t.visita_id)] = t
    return out


def recibir(negocio, *, cita=None, visita=None, datos=None):
    """Abre un trabajo: desde una cita/visita (copia sus datos) o con los datos del formulario (cliente sin cita)."""
    from garaje.models import TrabajoEnCurso
    origen = cita or visita
    if origen:
        existente = trabajos(negocio).filter(cita=cita) if cita else trabajos(negocio).filter(visita=visita)
        if t := existente.exclude(estado=TrabajoEnCurso.Estado.ENTREGADA).first():
            return t
        d = {"nombre": origen.nombre, "telefono": origen.telefono, "moto": origen.moto or "Moto",
             "que": str(origen.servicio) if origen.servicio else "", "usuario": origen.usuario}
    else:
        d = {k: datos.get(k, "") for k in ("nombre", "telefono", "moto", "que", "nota")}
        d["usuario"] = usuario_por_celular(d["telefono"])
    return TrabajoEnCurso.objects.create(cita=cita, visita=visita, **filtro_negocio(negocio), **d)


SIGUIENTE = {"recibida": "reparacion", "reparacion": "lista", "lista": "entregada"}
BOTON_SIGUIENTE = {"recibida": "Empezar reparación", "reparacion": "Marcar lista", "lista": "Entregada"}


def cambiar_estado(trabajo, estado, nota=None):
    """Mueve el trabajo; al pasar a «lista» avisa al dueño (una vez). Devuelve los canales del aviso ([] si no hubo)."""
    from garaje.models import TrabajoEnCurso
    if estado not in TrabajoEnCurso.Estado.values or estado == trabajo.estado:
        return []
    ahora = timezone.now()
    trabajo.estado = estado
    campos = ["estado"]
    if nota is not None:
        trabajo.nota = nota[:200]
        campos.append("nota")
    if estado == "lista" and not trabajo.lista_en:
        trabajo.lista_en = ahora
        campos.append("lista_en")
    if estado == "entregada":
        trabajo.entregada_en = ahora
        campos.append("entregada_en")
    trabajo.save(update_fields=campos)
    return avisar_lista(trabajo) if estado == "lista" else []


def url_cliente(trabajo):
    """A dónde lleva el aviso: la página de la cita o visita, o la ficha del negocio."""
    from .ciclo import url_pedido  # con cuenta, el detalle en «Mis citas» (pasos y siguiente botón)
    pedido = trabajo.cita or trabajo.visita
    return url_pedido(pedido) if pedido else url_ficha(trabajo.negocio)


def avisar_lista(trabajo):
    """Aviso «tu moto está lista» al dueño con cuenta (push; sin push, correo de respaldo: prefijo urgente en
    notificaciones/correo.py). Sin cuenta, el negocio tiene el botón de WhatsApp con el mensaje listo."""
    from notificaciones.models import Notificacion
    from notificaciones.servicios import notificar
    if trabajo.avisado_en or not trabajo.usuario_id:
        return []
    n = trabajo.negocio
    donde = "en el taller" if trabajo.taller_id else "con tu mecánico"
    texto = f"{n.nombre} terminó{': ' + trabajo.que.lower() if trabajo.que else ''}. Ya puedes recogerla {donde}."
    if trabajo.nota:
        texto += f" Nota: {trabajo.nota}"
    notif = notificar(trabajo.usuario, f"trabajo-listo:{trabajo.pk}", f"Tu {trabajo.moto} está lista", texto,
                      url_cliente(trabajo), Notificacion.Tipo.TALLER)
    trabajo.avisado_en = timezone.now()
    trabajo.save(update_fields=["avisado_en"])
    return ["la app"] if notif else []


def mensaje_lista(trabajo):
    n = trabajo.negocio
    return f"Hola {trabajo.nombre}, tu {trabajo.moto} ya está lista para recoger en {n.nombre}." + (f" {trabajo.nota}" if trabajo.nota else "")


def url_registrar(trabajo):
    """Registrar el servicio al entregar (flujos existentes: desde la cita, desde la visita o suelto)."""
    if trabajo.taller_id:
        return reverse("talleres:servicio_cita", args=[trabajo.cita_id]) if trabajo.cita_id else reverse("talleres:registrar_servicio")
    return reverse("garaje:servicio_visita", args=[trabajo.visita_id]) if trabajo.visita_id else reverse("garaje:servicio_mecanico")


def tablero(negocio):
    """Trabajos abiertos por columna y los entregados de los últimos 7 días."""
    from garaje.models import TrabajoEnCurso
    E = TrabajoEnCurso.Estado
    hace = timezone.now() - timedelta(days=7)
    lista = list(trabajos(negocio).select_related("cita", "visita").filter(Q(estado__in=[E.RECIBIDA, E.EN_REPARACION, E.LISTA]) | Q(entregada_en__gte=hace)))
    for t in lista:
        t.siguiente, t.boton = SIGUIENTE.get(t.estado), BOTON_SIGUIENTE.get(t.estado)
        t.wa_lista = whatsapp(t.telefono, mensaje_lista(t)) if t.estado == E.LISTA else whatsapp(t.telefono, f"Hola {t.nombre}, te escribe {negocio.nombre} por tu {t.moto}.")
    columnas = [{"clave": e.value, "titulo": e.label, "trabajos": [t for t in lista if t.estado == e.value]} for e in E]
    return {"columnas": columnas, "abiertos": sum(len(c["trabajos"]) for c in columnas[:3]),
            "listas": len(columnas[2]["trabajos"])}


# ---------- recordatorios ----------
def _ultimo_negocio_por_moto(negocio):
    """Motos cuyo ÚLTIMO servicio verificado lo hizo este negocio (así dos negocios no le escriben a la misma moto)."""
    from garaje.models import ServicioTaller
    verificados = ServicioTaller.objects.filter(estado=ServicioTaller.Estado.VERIFICADO)
    mias = set(verificados.filter(**filtro_negocio(negocio)).values_list("moto_id", flat=True))
    if not mias:
        return []
    ultimo = {}
    for moto_id, taller_id, mecanico_id in (verificados.filter(moto_id__in=mias).order_by("moto_id", "fecha", "creado")
                                           .values_list("moto_id", "taller_id", "mecanico_id")):
        ultimo[moto_id] = (taller_id, mecanico_id)
    clave = (negocio.pk, None) if es_taller(negocio) else (None, negocio.pk)
    return [m for m, quien in ultimo.items() if quien == clave]


def _firma(tareas):
    return hashlib.sha1("|".join(f"{t.tarea.pk}:{t.ultimo_km}" for t in tareas).encode()).hexdigest()[:12]


def clave_recordatorio(negocio, moto, tareas):
    return f"negocio-recordatorio:{neg.variante_de(negocio).clave}{negocio.pk}:{moto.pk}:{_firma(tareas)}"


def clientes_que_les_toca(negocio, hoy=None):
    """[{moto, usuario, tareas, urgente, clave, avisado}] de los clientes de este negocio a los que su plan dice que toca."""
    from garaje.models import Moto
    from garaje.plan import calcular_plan
    from notificaciones.models import Notificacion
    ids = _ultimo_negocio_por_moto(negocio)[:MAX_CLIENTES]
    motos = list(Moto.objects.filter(pk__in=ids, motociclista__usuario__isnull=False)
                 .select_related("linea", "linea__marca", "motociclista", "motociclista__usuario").prefetch_related("ajustes"))
    out = []
    for moto in motos:
        plan = calcular_plan(moto, hoy=hoy)
        pospuestas = {a.tarea_id for a in moto.ajustes.all() if a.pospuesta}
        urgentes = [t for t in plan.urgentes if t.tarea.pk not in pospuestas]
        tareas = urgentes + [t for t in plan.pronto if t.tarea.pk not in pospuestas]
        if not tareas:
            continue
        out.append({"moto": moto, "usuario": moto.motociclista.usuario, "nombre": moto.motociclista.nombre, "tareas": tareas,
                    "urgente": bool(urgentes), "clave": clave_recordatorio(negocio, moto, tareas)})
    avisados = dict(Notificacion.objects.filter(clave__in=[c["clave"] for c in out]).values_list("clave", "creada"))
    for c in out:
        c["avisado"] = avisados.get(c["clave"])
    out.sort(key=lambda c: (c["avisado"] is not None, not c["urgente"]))
    return out


def recordar(negocio, cliente):
    """Envía el recordatorio (una vez por lista de tareas). Devuelve la notificación nueva o None."""
    from notificaciones.models import Notificacion
    from notificaciones.servicios import notificar
    tareas = cliente["tareas"]
    servicios = {t.tarea.servicio_id for t in tareas if t.tarea.servicio_id}
    nombres = [t.tarea.nombre for t in tareas]
    texto = ", ".join(nombres[:3]) + (f" y {len(nombres) - 3} más" if len(nombres) > 3 else "")
    url = url_agendar(negocio, servicios.pop() if len(servicios) == 1 else None) or cliente["moto"].get_absolute_url() + "#plan"
    palabra = "Agenda tu cita" if es_taller(negocio) else "Pide tu visita"
    return notificar(cliente["usuario"], cliente["clave"],
                     f"{'Toca ya' if cliente['urgente'] else 'Se acerca'}: mantenimiento de tu {cliente['moto']}",
                     f"{texto}. {palabra} con {negocio.nombre}, que la atendió la última vez.", url, Notificacion.Tipo.MANTENIMIENTO)


def recordar_todos(negocio, hoy=None):
    return sum(1 for c in clientes_que_les_toca(negocio, hoy) if not c["avisado"] and recordar(negocio, c))


# ---------- «Por hacer» del panel ----------
def tareas_panel(negocio):
    """Tareas de «Mi día» para el «Por hacer» del panel (taller y mecánico). Vacío con el módulo apagado."""
    from consola.ajustes import ajuste
    from django.utils.html import format_html
    if not ajuste("herramientas_activo"):
        return []
    from garaje.models import TrabajoEnCurso
    E = TrabajoEnCurso.Estado
    url = reverse("talleres:mi_dia")
    abiertos = dict(trabajos(negocio).filter(estado__in=[E.RECIBIDA, E.EN_REPARACION, E.LISTA]).order_by().values("estado")
                    .annotate(n=Count("pk")).values_list("estado", "n"))
    t = []
    if listas := abiertos.get(E.LISTA, 0):
        t.append(neg.tarea(format_html("<strong>{} moto{}</strong> lista{} para entregar", listas, "s" if listas != 1 else "",
                                       "s" if listas != 1 else ""), url + "#motos", "Ver", True))
    en_curso = sum(abiertos.values()) - listas
    if en_curso:
        t.append(neg.tarea(format_html("<strong>{} moto{}</strong> en {}", en_curso, "s" if en_curso != 1 else "",
                                       "el taller" if es_taller(negocio) else "curso"), url + "#motos", "Ver"))
    return t
