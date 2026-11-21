"""Lado del taller: registrar el servicio hecho (al cerrar una cita, con el código/QR del dueño o por placa)
y la lista de servicios registrados. Las reglas (hoja de vida, plan, avisos) viven en garaje.servicio_taller."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import SolicitudCita

BUSQUEDAS_PLACA_HORA = 30  # por taller: buscar por placa no debe servir para rastrear motos


def _taller_de(request):
    return getattr(request.user, "taller", None)


def _gastar_codigo(codigo, moto):
    """Marca como usado el código del dueño (que siga vigente y sea de esa moto). False si ya no sirve."""
    from garaje.hoja_vida import normalizar
    from garaje.models import CodigoServicio
    # Actualización condicional: dos envíos a la vez (doble clic, dos pestañas) no gastan el mismo código dos veces
    return CodigoServicio.objects.filter(codigo=normalizar(codigo), moto=moto, usado__isnull=True,
                                         vence__gt=timezone.now()).update(usado=timezone.now()) == 1


def _formulario(request, taller, moto, origen, *, cita=None, motos=(), codigo="", placa=""):
    from garaje import servicio_taller as st
    from garaje.forms_servicio_taller import ServicioHechoForm
    from garaje.models import ServicioTaller
    tareas = st.tareas_de(moto)
    inicial = {"fecha": min(cita.fecha_preferida, timezone.localdate())} if cita else {}
    desde, hasta = (cita.cotizacion_desde, cita.cotizacion_hasta) if cita else (None, None)
    if hasta and desde == hasta:  # precio fijo cotizado y aceptado: ya viene puesto (el taller lo puede cambiar)
        inicial["costo"] = f"{hasta:,}".replace(",", ".")
    form = ServicioHechoForm(request.POST or None, request.FILES or None, moto=moto, tareas=tareas, initial=inicial)
    if hasta and desde != hasta:
        form.fields["costo"].widget.attrs["placeholder"] = f"Cotizaste ${desde:,} a ${hasta:,}".replace(",", ".")
    if request.method == "POST" and request.POST.get("guardar") and form.is_valid():
        with transaction.atomic():
            if origen == ServicioTaller.Origen.CODIGO and not _gastar_codigo(codigo, moto):
                form.add_error(None, "El código ya caducó o se usó. Pídele al motero uno nuevo.")
            else:
                from cuentas.limites import ip_cliente
                s = st.crear(taller, moto, origen=origen, cita=cita, registrado_por=request.user,
                             ip=ip_cliente(request), **form.datos())
        if not form.errors:
            if s.estado == ServicioTaller.Estado.VERIFICADO:
                messages.success(request, f"Registrado y verificado en la hoja de vida de la moto. "
                                          f"Le avisamos al dueño y lo invitamos a calificarte.")
            else:
                messages.success(request, "Listo. Le pedimos al dueño que lo confirme; cuando lo haga queda "
                                          "verificado en su hoja de vida.")
            return redirect("talleres:servicios_taller")
    return render(request, "talleres/servicio_hecho.html", {
        "taller": taller, "moto": moto, "form": form, "origen": origen, "cita": cita, "motos": motos,
        "codigo": codigo, "placa": placa, "origenes": ServicioTaller.Origen,
        "plan_vacio": not tareas,
    })


@login_required
def servicio_cita(request, pk):
    """Al terminar una cita: el servicio de una de las motos del motero que la pidió."""
    from garaje import servicio_taller as st
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    cita = get_object_or_404(SolicitudCita.objects.select_related("servicio"), pk=pk, taller=taller)
    if cita.servicios_hechos.exclude(estado="rechazado").exists():
        messages.info(request, "Ya registraste el servicio de esa cita.")
        return redirect("talleres:servicios_taller")
    if request.method == "POST" and request.POST.get("solo_atendida"):
        cita.estado = SolicitudCita.Estado.ATENDIDA
        cita.save(update_fields=["estado"])
        messages.success(request, f"Cita de {cita.nombre}: atendida.")
        return redirect(reverse("talleres:citas_taller") + "?estado=pasadas")
    motos = st.motos_de_cita(cita)
    if not motos:
        return render(request, "talleres/servicio_hecho.html", {"taller": taller, "cita": cita, "sin_moto": True})
    elegida = request.POST.get("moto") or request.GET.get("moto")
    moto = next((m for m in motos if str(m.pk) == elegida), None)
    if not moto:  # la que escribió en la cita (p. ej. "Yamaha NMAX") o la más reciente
        texto = cita.moto.lower()
        moto = next((m for m in motos if (m.linea and m.linea.nombre.lower() in texto)), motos[0])
    from garaje.models import ServicioTaller
    return _formulario(request, taller, moto, ServicioTaller.Origen.CITA, cita=cita, motos=motos)


CODIGOS_FALLIDOS_HORA = 20


@login_required
def registrar_servicio(request):
    """Moto que llega sin cita: se busca con el código/QR del dueño (queda verificado de una vez) o por placa
    (el dueño lo confirma desde su aviso)."""
    from cuentas import limites
    from garaje import hoja_vida, servicio_taller as st
    from garaje.models import ServicioTaller
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    datos = request.POST if request.method == "POST" else request.GET
    codigo = hoja_vida.normalizar(datos.get("codigo", ""))[:12]
    placa = st.normalizar_placa(datos.get("placa", ""))
    error = ""
    if codigo:
        # Freno a probar códigos al azar (cada acierto abre la moto de alguien): por taller y por IP
        clave_cod, clave_ip = f"codigo-taller:{taller.pk}", f"codigo-ip:{limites.ip_cliente(request)}"
        if limites.superado(clave_cod, CODIGOS_FALLIDOS_HORA) or limites.superado(clave_ip, CODIGOS_FALLIDOS_HORA):
            error = "Demasiados códigos no válidos en la última hora. Intenta más tarde o busca la moto por placa."
        elif obj := hoja_vida.buscar_codigo(codigo):
            return _formulario(request, taller, obj.moto, ServicioTaller.Origen.CODIGO, codigo=codigo)
        else:
            limites.sumar(clave_cod, 3600)
            limites.sumar(clave_ip, 3600)
            error = "El código no es válido o ya caducó. Pídele al motero uno nuevo."
    elif placa:
        clave = f"placa-taller:{taller.pk}"
        nueva = request.method == "GET"
        if nueva and limites.superado(clave, BUSQUEDAS_PLACA_HORA):
            error = "Hiciste muchas búsquedas por placa. Intenta en un rato o pídele al motero el código de su moto."
        else:
            if nueva:
                limites.sumar(clave, 3600)
            motos = st.buscar_por_placa(placa)
            elegida = datos.get("moto")
            moto = next((m for m in motos if str(m.pk) == elegida), motos[0] if motos else None)
            if moto:
                return _formulario(request, taller, moto, ServicioTaller.Origen.PLACA, placa=placa)
            error = (f"No encontramos una moto con placa {placa} en TallerYa. Pídele al motero que la registre en su "
                     "garaje (es gratis) o que te muestre el código de su hoja de vida.")
    return render(request, "talleres/servicio_buscar.html", {"taller": taller, "error": error,
                                                             "codigo": codigo, "placa": placa})


@login_required
def servicios_taller(request):
    """Servicios que el taller ha registrado, con su estado (verificado, esperando al dueño, no reconocido)."""
    from garaje import servicio_taller as st
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    servicios = (taller.servicios_taller.select_related("moto", "moto__linea", "moto__linea__marca", "cita")
                 .prefetch_related("tareas"))
    pagina = Paginator(servicios, 15).get_page(request.GET.get("pagina"))
    return render(request, "talleres/servicios_taller.html", {
        "taller": taller, "pagina": pagina, "resumen": st.resumen_taller(taller)})


def _form_rapido():
    from django import forms

    from garaje.forms import MAX_KM, leer_pesos
    from .forms import EstiloMixin

    class ServicioRapidoForm(EstiloMixin, forms.Form):
        placa = forms.CharField(label="Placa", max_length=8, widget=forms.TextInput(
            attrs={"autocapitalize": "characters", "autocomplete": "off", "placeholder": "ABC12D", "autofocus": True}))
        km = forms.IntegerField(label="Kilometraje", min_value=0, max_value=MAX_KM,
                                widget=forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 12500"}))
        que = forms.CharField(label="Qué se hizo", max_length=200,
                              widget=forms.TextInput(attrs={"placeholder": "Ej: cambio de aceite y filtro"}))
        costo = forms.CharField(label="Precio cobrado (opcional)", required=False, max_length=20,
                                widget=forms.TextInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 85.000"}))

        def clean_placa(self):
            from garaje import servicio_taller as st
            return st.normalizar_placa(self.cleaned_data["placa"])

        def clean_costo(self):
            return leer_pesos(self.cleaned_data.get("costo"))

    return ServicioRapidoForm


@login_required
def servicio_rapido(request):
    """Servicio en 30 segundos desde el celular: placa, km, qué se hizo y precio. Va a la hoja de vida del motero
    (cuando él lo confirma) y le abre una reseña verificada."""
    from cuentas import limites
    from cuentas.limites import ip_cliente
    from garaje import servicio_taller as st
    from garaje.models import ServicioTaller
    taller = _taller_de(request)
    if not taller:
        return redirect("cuentas:mi_cuenta")
    form = _form_rapido()(request.POST or None)
    if request.method == "POST":
        clave = f"placa-taller:{taller.pk}"
        if limites.superado(clave, BUSQUEDAS_PLACA_HORA):
            form.add_error(None, "Hiciste muchas búsquedas por placa. Intenta en un rato.")
        elif form.is_valid():
            limites.sumar(clave, 3600)
            d = form.cleaned_data
            motos = st.buscar_por_placa(d["placa"])
            if not motos:
                form.add_error("placa", "No hay una moto con esa placa en TallerYa. Pídele al motero que la registre en su garaje (es gratis).")
            elif d["km"] < motos[0].km_actual:
                form.add_error("km", f"Es menor que el kilometraje actual ({motos[0].km_actual:,} km). Revísalo.".replace(",", "."))
            else:
                s = st.crear(taller, motos[0], origen=ServicioTaller.Origen.PLACA, fecha=timezone.localdate(), km=d["km"],
                             tareas=[], otros=d["que"], costo=d["costo"], registrado_por=request.user, ip=ip_cliente(request))
                messages.success(request, f"Listo: {motos[0]} ({d['placa']}). Le pedimos al dueño que lo confirme; "
                                          "al confirmarlo queda en su hoja de vida y puede dejarte una reseña verificada.")
                return redirect("talleres:servicio_rapido")
    return render(request, "talleres/servicio_rapido.html", {"taller": taller, "form": form})
