"""«Mi día»: herramientas del día a día del taller y del mecánico a domicilio (una sola página para los dos).

La lógica vive en talleres/herramientas.py; aquí solo formularios, permisos y redirecciones. Rutas bajo /mi-negocio/
(el middleware de config/piloto.py las apaga con el módulo «herramientas_activo»).
"""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import herramientas as h
from .utils import normalizar_celular


class AnotarCitaForm(forms.Form):
    nombre = forms.CharField(label="Cliente", max_length=80)
    telefono = forms.CharField(label="Celular", max_length=15)
    moto = forms.CharField(label="Moto", max_length=60, widget=forms.TextInput(attrs={"placeholder": "Ej: Yamaha NMAX"}))
    servicio = forms.ChoiceField(label="Servicio", required=False)
    fecha = forms.DateField(label="Día", widget=forms.DateInput(attrs={"type": "date"}))
    hora = forms.TimeField(label="Hora", required=False, widget=forms.TimeInput(attrs={"type": "time"}))
    detalle = forms.CharField(label="Nota", max_length=200, required=False)

    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.opciones = {str(s.pk): s for s in h.servicios_del_negocio(negocio)}
        self.fields["servicio"].choices = [("", "Por definir")] + [(k, str(s)) for k, s in self.opciones.items()]

    def clean_telefono(self):
        return normalizar_celular(self.cleaned_data["telefono"])[2:]

    def clean_fecha(self):
        f = self.cleaned_data["fecha"]
        if f < timezone.localdate():
            raise forms.ValidationError("Elige hoy o un día que venga.")
        return f

    def clean_servicio(self):
        return self.opciones.get(self.cleaned_data.get("servicio") or "")


class RecibirMotoForm(forms.Form):
    nombre = forms.CharField(label="Cliente", max_length=120)
    telefono = forms.CharField(label="Celular", max_length=15, required=False)
    moto = forms.CharField(label="Moto", max_length=80, widget=forms.TextInput(attrs={"placeholder": "Ej: Honda CB 125F"}))
    que = forms.CharField(label="Qué se le hace", max_length=160, required=False,
                          widget=forms.TextInput(attrs={"placeholder": "Ej: cambio de aceite y frenos"}))

    def clean_telefono(self):
        t = self.cleaned_data["telefono"]
        return normalizar_celular(t)[2:] if t else ""


def _negocio(request):
    n = h.negocio_de(request.user)
    if not n:
        raise Http404
    return n


def _volver(ancla):
    return redirect(reverse("talleres:mi_dia") + ancla)


@login_required
def mi_dia(request):
    negocio = _negocio(request)
    hoy = timezone.localdate()
    ag = h.agenda(negocio, hoy)
    tab = h.tablero(negocio)
    clientes = h.clientes_que_les_toca(negocio, hoy)
    por_avisar = sum(1 for c in clientes if not c["avisado"])
    taller = h.es_taller(negocio)
    return render(request, "talleres/negocio/mi_dia.html", {
        "negocio": negocio, "es_taller": taller, "hoy": hoy, "agenda": ag, "tablero": tab,
        "clientes": clientes, "por_avisar": por_avisar,
        "form_cita": AnotarCitaForm(negocio=negocio, initial={"fecha": hoy}), "form_recibir": RecibirMotoForm(),
        "url_panel": reverse("talleres:panel") if taller else reverse("domicilio:panel"),
        "palabra": "cita" if taller else "visita",
        "dato_agenda": f"{ag['dias'][0]['n']} hoy · {ag['total']} en la semana",
        "dato_tablero": f"{tab['abiertos']} en curso" + (f" · {tab['listas']} lista{'s' if tab['listas'] != 1 else ''}" if tab["listas"] else ""),
        "dato_clientes": f"{por_avisar} por avisar" if por_avisar else (f"{len(clientes)} avisado{'s' if len(clientes) != 1 else ''}" if clientes else "Nadie por ahora"),
    })


@login_required
@require_POST
def anotar_cita(request):
    negocio = _negocio(request)
    form = AnotarCitaForm(request.POST, negocio=negocio)
    if not form.is_valid():
        errores = "; ".join(f"{form.fields[c].label}: {e[0]}" if c in form.fields else e[0] for c, e in form.errors.items())
        messages.error(request, f"No pudimos anotar la cita. {errores}")
        return _volver("#agenda")
    h.anotar_cita(negocio, form.cleaned_data)
    d = form.cleaned_data
    messages.success(request, f"Anotamos la {'cita' if h.es_taller(negocio) else 'visita'} de {d['nombre']} el {d['fecha']:%d/%m}.")
    return _volver("#agenda")


@login_required
@require_POST
def recibir_moto(request):
    negocio = _negocio(request)
    cita = visita = None
    if pk := request.POST.get("cita"):
        if not h.es_taller(negocio):
            raise Http404
        cita = get_object_or_404(negocio.solicitudes, pk=pk)
    elif pk := request.POST.get("visita"):
        if h.es_taller(negocio):
            raise Http404
        visita = get_object_or_404(negocio.solicitudes, pk=pk)
    if cita or visita:
        t = h.recibir(negocio, cita=cita, visita=visita)
    else:
        form = RecibirMotoForm(request.POST)
        if not form.is_valid():
            errores = "; ".join(f"{form.fields[c].label}: {e[0]}" for c, e in form.errors.items() if c in form.fields)
            messages.error(request, f"No pudimos recibir la moto. {errores}")
            return _volver("#motos")
        t = h.recibir(negocio, datos=form.cleaned_data)
    messages.success(request, f"Recibiste la {t.moto} de {t.nombre}.")
    return _volver("#motos")


@login_required
@require_POST
def trabajo_estado(request, pk):
    negocio = _negocio(request)
    t = get_object_or_404(h.trabajos(negocio), pk=pk)
    estado = request.POST.get("estado", "")
    nota = request.POST.get("nota")
    canales = h.cambiar_estado(t, estado, nota.strip() if nota is not None else None)
    if t.estado == "lista":
        msg = f"La {t.moto} quedó lista." + (" Le avisamos al cliente en la app." if canales else
                                             " El cliente no tiene cuenta: avísale por WhatsApp." if not t.usuario_id else "")
        messages.success(request, msg)
    elif t.estado == "entregada":
        messages.success(request, f"Entregaste la {t.moto}. Registra el servicio para que quede en su hoja de vida.")
        return redirect(h.url_registrar(t))
    return _volver("#motos")


@login_required
@require_POST
def recordar(request, moto_id):
    negocio = _negocio(request)
    cliente = next((c for c in h.clientes_que_les_toca(negocio) if c["moto"].pk == int(moto_id)), None)
    if not cliente:
        raise Http404
    if cliente["avisado"]:
        messages.info(request, f"A {cliente['nombre']} ya le llegó este recordatorio.")
    elif h.recordar(negocio, cliente):
        messages.success(request, f"Le recordamos a {cliente['nombre']} el mantenimiento de su {cliente['moto']}.")
    return _volver("#recordatorios")


@login_required
@require_POST
def recordar_todos(request):
    negocio = _negocio(request)
    n = h.recordar_todos(negocio)
    messages.success(request, f"Enviamos {n} recordatorio{'s' if n != 1 else ''}." if n else "No había recordatorios por enviar.")
    return _volver("#recordatorios")
