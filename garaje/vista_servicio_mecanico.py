"""Lado del mecánico a domicilio: registrar el servicio hecho en la hoja de vida de la moto, igual que un taller.

- Desde una solicitud de visita confirmada o atendida: con la moto del motero (si la pidió con su cuenta) queda
  verificado de una vez, como la cita de un taller; si no tiene cuenta, se pide el código/QR de su hoja de vida.
- Sin solicitud: con el código/QR que muestra el dueño (de un solo uso).
No hay búsqueda por placa: el mecánico no tiene un local donde la moto «llega sola».
Mismas plantillas y reglas que los talleres (talleres/vista_servicios.py, garaje/servicio_taller.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from . import hoja_vida, servicio_taller as st
from .forms_servicio_taller import ServicioHechoForm
from .models import ServicioTaller

CODIGOS_FALLIDOS_HORA = 20


def _mecanico_de(request):
    """Perfil de mecánico aprobado de la cuenta (solo los publicados dejan servicios verificados)."""
    from domicilio.models import MecanicoDomicilio
    return MecanicoDomicilio.objects.filter(usuario=request.user, estado=MecanicoDomicilio.Estado.APROBADO).first()


def _solicitud_de(mecanico, pk):
    from domicilio.models import SolicitudVisita
    if not pk:
        return None
    return get_object_or_404(SolicitudVisita, pk=pk, mecanico=mecanico,
                             estado__in=[SolicitudVisita.Estado.CONFIRMADA, SolicitudVisita.Estado.ATENDIDA])


def _contexto_base(mecanico, solicitud):
    return {"taller": mecanico, "origenes": ServicioTaller.Origen, "sin_placa": True, "visita": solicitud,
            "volver_url": reverse("domicilio:solicitudes"), "volver_texto": "Mis solicitudes",
            "etiqueta": (f"Visita de {solicitud.nombre}" if solicitud else "Visita sin solicitud"),
            "accion_buscar": reverse("garaje:servicio_mecanico")}


def _formulario(request, mecanico, moto, origen, *, solicitud=None, motos=(), codigo=""):
    from talleres.vista_servicios import _gastar_codigo
    tareas = st.tareas_de(moto)
    inicial = {}
    if solicitud is not None:
        if solicitud.fecha_propuesta:
            inicial["fecha"] = min(solicitud.fecha_propuesta, timezone.localdate())
        if solicitud.cotizacion_hasta and solicitud.cotizacion_desde == solicitud.cotizacion_hasta:
            inicial["costo"] = f"{solicitud.cotizacion_hasta:,}".replace(",", ".")
    form = ServicioHechoForm(request.POST if request.POST.get("guardar") else None, request.FILES or None,
                             moto=moto, tareas=tareas, initial=inicial)
    if request.method == "POST" and request.POST.get("guardar") and form.is_valid():
        with transaction.atomic():
            if origen == ServicioTaller.Origen.CODIGO and not _gastar_codigo(codigo, moto):
                form.add_error(None, "El código ya caducó o se usó. Pídele al motero uno nuevo.")
            else:
                from cuentas.limites import ip_cliente
                st.crear(None, moto, origen=origen, mecanico=mecanico, solicitud=solicitud,
                         registrado_por=request.user, ip=ip_cliente(request), **form.datos())
        if not form.errors:
            messages.success(request, "Registrado y verificado en la hoja de vida de la moto. "
                                      "Le avisamos al dueño y lo invitamos a calificarte.")
            return redirect("domicilio:solicitudes")
    return render(request, "talleres/servicio_hecho.html", {
        **_contexto_base(mecanico, solicitud), "moto": moto, "form": form, "origen": origen, "motos": motos,
        "codigo": codigo, "plan_vacio": not tareas,
    })


@login_required
def servicio_visita(request, pk):
    """«Registrar servicio» de una solicitud confirmada o atendida de la bandeja del mecánico."""
    mecanico = _mecanico_de(request)
    if not mecanico:
        return redirect("domicilio:registro")
    solicitud = _solicitud_de(mecanico, pk)
    if solicitud.servicios_hechos.exclude(estado=ServicioTaller.Estado.RECHAZADO).exists():
        messages.info(request, "Ya registraste el servicio de esa visita.")
        return redirect("domicilio:solicitudes")
    motos = st.motos_de_cita(solicitud)
    if not motos:  # el motero no tiene cuenta (o no tiene motos): su código/QR
        return render(request, "talleres/servicio_buscar.html", {**_contexto_base(mecanico, solicitud),
                                                                 "error": "", "codigo": ""})
    elegida = request.POST.get("moto") or request.GET.get("moto")
    moto = next((m for m in motos if str(m.pk) == elegida), None)
    if not moto:
        texto = solicitud.moto.lower()
        moto = next((m for m in motos if m.linea and m.linea.nombre.lower() in texto), motos[0])
    return _formulario(request, mecanico, moto, ServicioTaller.Origen.VISITA, solicitud=solicitud, motos=motos)


@login_required
def servicio_mecanico(request):
    """Con el código/QR del dueño (con o sin solicitud): queda verificado de una vez."""
    from cuentas import limites
    mecanico = _mecanico_de(request)
    if not mecanico:
        return redirect("domicilio:registro")
    datos = request.POST if request.method == "POST" else request.GET
    solicitud = _solicitud_de(mecanico, datos.get("visita"))
    codigo = hoja_vida.normalizar(datos.get("codigo", ""))[:12]
    error = ""
    if codigo:
        # Freno a probar códigos al azar (cada acierto abre la moto de alguien): por mecánico y por IP
        clave_m, clave_ip = f"codigo-mecanico:{mecanico.pk}", f"codigo-ip:{limites.ip_cliente(request)}"
        if limites.superado(clave_m, CODIGOS_FALLIDOS_HORA) or limites.superado(clave_ip, CODIGOS_FALLIDOS_HORA):
            error = "Demasiados códigos no válidos en la última hora. Intenta más tarde."
        elif obj := hoja_vida.buscar_codigo(codigo):
            return _formulario(request, mecanico, obj.moto, ServicioTaller.Origen.CODIGO, solicitud=solicitud,
                               codigo=codigo)
        else:
            limites.sumar(clave_m, 3600)
            limites.sumar(clave_ip, 3600)
            error = "El código no es válido o ya caducó. Pídele al motero uno nuevo."
    return render(request, "talleres/servicio_buscar.html", {**_contexto_base(mecanico, solicitud),
                                                             "error": error, "codigo": codigo})
