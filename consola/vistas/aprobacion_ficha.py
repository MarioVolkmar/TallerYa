"""Ficha de revisión de «Por aprobar»: todo lo que cargó el solicitante, qué revisar y Aprobar/Rechazar al final.

La cédula del mecánico: solo se guardan los últimos dígitos y una huella (Ley 1581); la foto va a privado/ y se borra al decidir.
Las fotos de verificación de domiciliarios se revisan en su ficha de usuario (enlace protegido)."""
from django.http import Http404
from django.shortcuts import get_object_or_404

CHECKLIST = {
    "talleres": ["Nombre real del negocio y de la persona responsable", "Foto clara del taller o del logo",
                 "Dirección y barrio en el Valle de Aburrá; ubicación marcada en el mapa",
                 "WhatsApp válido (escríbele si hay duda)", "Servicios y horario coherentes con lo que ofrece"],
    "mecanicos": ["Nombre real y foto de su cara o de su trabajo", "Cédula: coinciden los últimos dígitos y el nombre",
                  "Foto de la cédula: nítida, el nombre y el número coinciden, y la selfie (si hay) es la misma persona",
                  "Zonas de atención dentro del Valle de Aburrá", "WhatsApp válido",
                  "Fotos de trabajos y referencias que se vean reales"],
    "proveedores": ["Nombre real del negocio y persona de contacto", "Contacto válido (WhatsApp o teléfono)",
                    "Municipio o zonas en el Valle de Aburrá", "Horario y servicios coherentes", "Aprobó su ficha (Ley 1581)"],
}
ETIQUETAS = {"talleres": "Taller", "mecanicos": "Mecánico a domicilio", "proveedores": "Proveedor"}


def _fotos(*campos):
    return [f.url for f in campos if f]


def _cop(n):
    return f"${n:,.0f}".replace(",", ".")


def _ficha(tipo, pk):
    """(obj, nombre, [(etiqueta, valor o vacío)], [urls de fotos])."""
    from domicilio.models import MecanicoDomicilio
    from proveedores.models import Proveedor
    from talleres.models import Taller
    if tipo == "talleres":
        t = get_object_or_404(Taller.objects.select_related("barrio", "usuario").prefetch_related(
            "servicios", "marcas", "precios__servicio", "fotos"), pk=pk)
        precios = [f"{p.servicio.nombre}: {_cop(p.desde)} a {_cop(p.hasta)}" for p in t.precios.all()]
        ubic = ""
        if t.latitud and t.longitud:
            ubic = ("Exacta" if t.ubicacion_exacta else "Aproximada") + f" ({t.latitud}, {t.longitud})"
        datos = [("Nombre", t.nombre), ("Responsable", t.responsable), ("WhatsApp", t.whatsapp),
                 ("Cuenta", t.usuario.email if t.usuario_id else "Sin cuenta (alta asistida)"),
                 ("Dirección", f"{t.direccion}, {t.barrio}" if t.direccion else ""), ("Ubicación", ubic),
                 ("Horario", t.horario), ("24 horas", "Sí" if t.abierto_24h else ""),
                 ("Servicios", ", ".join(s.nombre for s in t.servicios.all())),
                 ("Marcas", "Multimarca" if t.multimarca else ", ".join(m.nombre for m in t.marcas.all())),
                 ("Descripción", t.descripcion), ("Rango de precios", t.get_nivel_precio_display() if t.nivel_precio else ""),
                 ("Precios cargados", "; ".join(precios)), ("Origen del alta", t.get_origen_alta_display()),
                 ("Aprobó su ficha", f"{t.aprobado_por_taller:%d/%m/%Y %H:%M}" if t.aprobado_por_taller else "")]
        return t, t.nombre, datos, _fotos(t.foto, *[f.imagen for f in t.fotos.all()])
    if tipo == "mecanicos":
        m = get_object_or_404(MecanicoDomicilio.objects.select_related("usuario").prefetch_related(
            "zonas", "servicios", "marcas", "precios__servicio", "fotos_trabajo"), pk=pk)
        precios = [f"{p.servicio.nombre}: {_cop(p.desde)} a {_cop(p.hasta)}" for p in m.precios.all()]
        datos = [("Nombre", m.nombre), ("WhatsApp", m.whatsapp), ("Cuenta", m.usuario.email if m.usuario_id else "Sin cuenta"),
                 ("Cédula", f"…{m.cedula_ultimos} (solo se guardan los últimos dígitos y una huella; la foto, si la envió, está abajo)"
                  if m.cedula_ultimos else ""),
                 ("Zonas", ", ".join(z.nombre for z in m.zonas.all())),
                 ("Servicios", ", ".join(s.nombre for s in m.servicios.all())),
                 ("Marcas", "Multimarca" if m.multimarca else ", ".join(x.nombre for x in m.marcas.all())),
                 ("Experiencia", f"{m.anios_experiencia} años" if m.anios_experiencia is not None else ""),
                 ("Horario", m.horario), ("Tarifa de visita", _cop(m.tarifa_visita) if m.tarifa_visita else ""),
                 ("Urgencias", "Sí" if m.urgencias else ""), ("Herramientas", m.herramientas),
                 ("Descripción", m.descripcion), ("Referencias", m.referencias), ("Precios cargados", "; ".join(precios))]
        return m, m.nombre, datos, _fotos(m.foto, *[f.imagen for f in m.fotos_trabajo.all()])
    p = get_object_or_404(Proveedor.objects.select_related("categoria"), pk=pk)
    datos = [("Nombre", p.nombre), ("Categoría", p.categoria.singular), ("Contacto", p.responsable),
             ("WhatsApp", p.whatsapp), ("Teléfono", p.telefono),
             ("Dirección", f"{p.direccion}, {p.municipio}" if p.direccion else p.municipio),
             ("Zonas que atiende", ", ".join(p.zonas or [])),
             ("Ubicación", f"({p.latitud}, {p.longitud})" if p.latitud and p.longitud else ""),
             ("Horario", "24 horas" if p.abierto_24h else p.horario), ("Sitio web", p.sitio_web),
             ("Descripción", p.descripcion), ("Precio desde", _cop(p.precio_desde) if p.precio_desde else ""),
             ("Origen del alta", p.get_origen_alta_display()),
             ("Aprobó su ficha", f"{p.aprobado_por_proveedor:%d/%m/%Y %H:%M}" if p.aprobado_por_proveedor else "")]
    return p, p.nombre, datos, _fotos(p.foto)


def _identidad(m):
    """Fotos de la cédula (enlaces protegidos, solo admins) y acciones, si el mecánico las envió y están por revisar."""
    from django.urls import reverse
    ident = getattr(m, "identidad", None)
    if not ident or ident.estado != "enviada":
        return None
    nombres = {"frente": "Cédula, frente", "respaldo": "Cédula, respaldo", "selfie": "Selfie con la cédula"}
    return {"fotos": [(nombres[c], reverse("domicilio:identidad_foto", args=[ident.pk, c]))
                      for c in ident.CAMPOS_FOTO if getattr(ident, c)],
            "numero": f"…{m.cedula_ultimos}" if m.cedula_ultimos else "",
            "aprobar": reverse("consola:accion", args=["mecanicos.identidad_aprobar", m.pk]),
            "rechazar": reverse("consola:accion", args=["mecanicos.identidad_rechazar", m.pk])}


def revision(clave):
    from .aprobaciones import pendientes_por_tipo
    tipo, _, pk = clave.partition("-")
    if tipo not in CHECKLIST or not pk.isdigit():
        raise Http404("Solicitud desconocida.")
    obj, nombre, datos, fotos = _ficha(tipo, int(pk))
    item = next((i for i in pendientes_por_tipo()[tipo] if i["pk"] == obj.pk), None)
    identidad = _identidad(obj) if tipo == "mecanicos" else None
    return "consola/aprobacion_ficha.html", {
        "identidad": identidad, "obj": obj, "nombre": nombre, "tipo": tipo, "etiqueta": ETIQUETAS[tipo], "datos": datos, "fotos": fotos,
        "faltan": sum(1 for _, v in datos if not v), "checklist": CHECKLIST[tipo], "item": item,
    }
