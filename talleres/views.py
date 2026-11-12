from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegistroTallerForm, ResenaForm, SolicitudCitaForm
from .models import Barrio, Marca, Servicio, Taller


def inicio(request):
    talleres = Taller.objects.filter(activo=True).select_related("barrio").prefetch_related("servicios")
    f = request.GET
    if q := f.get("q", "").strip():
        talleres = talleres.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if f.get("barrio", "").isdigit():
        talleres = talleres.filter(barrio_id=f["barrio"])
    if f.get("servicio", "").isdigit():
        talleres = talleres.filter(servicios__id=f["servicio"])
    if f.get("marca", "").isdigit():
        talleres = talleres.filter(marcas__id=f["marca"])
    return render(request, "talleres/inicio.html", {
        "talleres": talleres.distinct(),
        "barrios": Barrio.objects.all(),
        "servicios": Servicio.objects.all(),
        "marcas": Marca.objects.all(),
        "filtros": f,
    })


def detalle(request, slug):
    taller = get_object_or_404(Taller, slug=slug, activo=True)
    cita_form = SolicitudCitaForm(taller=taller)
    resena_form = ResenaForm()

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "cita":
            cita_form = SolicitudCitaForm(request.POST, taller=taller)
            form, msg = cita_form, "¡Solicitud enviada! El taller te contactará pronto."
        else:
            resena_form = ResenaForm(request.POST)
            form, msg = resena_form, "¡Gracias por tu reseña!"
        if form.is_valid():
            obj = form.save(commit=False)
            obj.taller = taller
            obj.save()
            messages.success(request, msg)
            return redirect(taller)

    return render(request, "talleres/detalle.html", {
        "taller": taller,
        "resenas": taller.resenas.filter(visible=True),
        "cita_form": cita_form,
        "resena_form": resena_form,
    })


def registro(request):
    form = RegistroTallerForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()  # queda inactivo hasta que el admin lo verifique
        messages.success(request, "¡Registro recibido! Revisaremos tu taller y lo publicaremos pronto.")
        return redirect("talleres:inicio")
    return render(request, "talleres/registro.html", {"form": form})
