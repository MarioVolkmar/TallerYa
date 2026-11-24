"""Bandeja «Por aprobar»: mecánicos, talleres, proveedores y domiciliarios en una sola lista, la más antigua primero.

Aprobar y rechazar usan las mismas acciones de cada sección (consola.acciones: permiso, POST y bitácora).
Domiciliarios: solo «Revisar», porque aprobar exige comparar las fotos y las placas en su ficha."""
from django.urls import reverse
from django.utils import timezone

TIPOS = [("mecanicos", "Mecánicos"), ("talleres", "Talleres"), ("proveedores", "Proveedores"), ("domiciliarios", "Domiciliarios")]
MAXIMO = 100  # por tipo; los pendientes reales son pocos


def _accion(clave, pk):
    return reverse("consola:accion", args=[clave, pk])


VALOR_APROBAR = {"mecanicos": "aprobado", "talleres": "1", "proveedores": "publicado"}


def _item(tipo, obj, nombre, detalle, creado, ver, aprobar=None, rechazar=None, nota=""):
    dias = max((timezone.now() - creado).days, 0)
    return {"tipo": tipo, "pk": obj.pk, "nombre": nombre, "detalle": detalle, "creado": creado, "dias": dias, "ver": ver,
            "aprobar": aprobar, "valor": VALOR_APROBAR.get(tipo, ""), "rechazar": rechazar, "nota": nota}


def pendientes_por_tipo():
    """{tipo: [items]} de lo que espera una decisión."""
    from domicilio.consola import con_algo_por_revisar
    from domicilio.models import MecanicoDomicilio
    from proveedores.models import Proveedor
    from talleres.models import Taller
    datos = {}
    datos["mecanicos"] = []
    for m in con_algo_por_revisar().select_related("usuario", "identidad").order_by("creado")[:MAXIMO]:
        base = f"{m.whatsapp}" + (f" · {m.usuario.email}" if m.usuario_id else " · sin cuenta")
        ver = f"?seccion=aprobaciones&revisar=mecanicos-{m.pk}"
        ident = getattr(m, "identidad", None)
        con_cedula = bool(ident and ident.estado == "enviada")
        if m.estado == MecanicoDomicilio.Estado.PENDIENTE:
            item = _item("mecanicos", m, m.nombre, base + (" · cédula por revisar" if con_cedula else ""), m.creado, ver,
                         _accion("mecanicos.estado", m.pk), _accion("mecanicos.rechazar", m.pk))
        else:  # perfil ya publicado o pausado: solo falta revisar su cédula
            item = _item("mecanicos", m, m.nombre, base + " · verificación de identidad", ident.enviado or m.creado, ver, None,
                         _accion("mecanicos.identidad_rechazar", m.pk), "Revisa la foto de su cédula en la ficha.")
            item["solo_identidad"] = True
        datos["mecanicos"].append(item)
    datos["talleres"] = [
        _item("talleres", t, t.nombre, f"{t.barrio}" + (f" · {t.usuario.email}" if t.usuario_id else " · sin cuenta"), t.creado,
              f"?seccion=aprobaciones&revisar=talleres-{t.pk}", None if t.falta_aprobacion else _accion("talleres.publicar", t.pk),
              _accion("talleres.rechazar", t.pk), "Espera que el taller apruebe su ficha." if t.falta_aprobacion else "")
        for t in Taller.objects.filter(activo=False, motivo_rechazo="").select_related("barrio", "usuario").order_by("creado")[:MAXIMO]]
    datos["proveedores"] = [
        _item("proveedores", p, p.nombre, f"{p.categoria.singular}" + (f" · {p.municipio}" if p.municipio else ""), p.creado,
              f"?seccion=aprobaciones&revisar=proveedores-{p.pk}", None if p.falta_aprobacion else _accion("proveedores.estado", p.pk),
              _accion("proveedores.rechazar", p.pk), "Espera que el proveedor apruebe su ficha." if p.falta_aprobacion else "")
        for p in Proveedor.objects.filter(estado=Proveedor.Estado.POR_REVISAR).select_related("categoria").order_by("creado")[:MAXIMO]]
    datos["domiciliarios"] = []
    from domiciliarios.bandera import activo
    if activo():
        from domiciliarios.models import Verificacion
        datos["domiciliarios"] = [
            _item("domiciliarios", v, v.perfil.motociclista.usuario.get_full_name() or v.perfil.motociclista.usuario.email,
                  f"Verificación en {v.get_plataforma_display()}", v.creado,
                  f"?seccion=usuarios&id={v.perfil.motociclista.usuario_id}", None, _accion("ruta.rechazar", v.pk),
                  "Compara las 3 placas en su ficha antes de aprobar.")
            for v in Verificacion.objects.filter(estado=Verificacion.Estado.PENDIENTE)
            .select_related("perfil__motociclista__usuario").order_by("creado")[:MAXIMO]]
    return datos


def seccion(request):
    if request.GET.get("revisar"):
        from .aprobacion_ficha import revision
        return revision(request.GET["revisar"])
    datos = pendientes_por_tipo()
    tipo = request.GET.get("tipo", "")
    if tipo not in datos:
        tipo = ""
    items = sorted((i for t, lista in datos.items() if not tipo or t == tipo for i in lista), key=lambda i: i["creado"])
    return "consola/aprobaciones.html", {
        "items": items, "tipo": tipo, "etiquetas": dict(TIPOS),
        "pestanas": [(clave, nombre, len(datos[clave])) for clave, nombre in TIPOS], "total_bandeja": sum(len(v) for v in datos.values()),
    }
