from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from cupones.models import Cupon
from talleres.models import Taller

from .forms import LecturaForm, MantenimientoForm, MotoForm
from .models import Despiece, LecturaKm, Moto
from .plan import GRAVEDAD, calcular_plan

MAX_MOTOS = 5


def con_motociclista(vista):
    """Exige sesión y un perfil de motociclista (las cuentas sin celular no tienen garaje)."""
    @login_required
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        moto_perfil = getattr(request.user, "motociclista", None)
        if not moto_perfil:
            messages.info(request, "Tu cuenta necesita un celular de motociclista para usar el garaje.")
            return redirect("cuentas:mi_cuenta")
        request.motociclista = moto_perfil
        return vista(request, *args, **kwargs)
    return envoltura


def _moto_de(request, pk):
    return get_object_or_404(Moto.objects.select_related("linea", "linea__marca"), pk=pk,
                             motociclista=request.motociclista)


@con_motociclista
def garaje(request):
    motos = list(request.motociclista.motos.select_related("linea", "linea__marca"))
    planes = [(m, calcular_plan(m)) for m in motos]
    if len(motos) == 1 and not request.GET.get("lista"):
        return redirect(motos[0])
    return render(request, "garaje/garaje.html", {"planes": planes, "puede_agregar": len(motos) < MAX_MOTOS})


@con_motociclista
def agregar(request):
    if request.motociclista.motos.count() >= MAX_MOTOS:
        messages.info(request, f"Puedes tener hasta {MAX_MOTOS} motos en tu garaje.")
        return redirect("garaje:garaje")
    form = MotoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            moto = form.save(commit=False)
            moto.motociclista = request.motociclista
            moto.km_inicial = moto.km_actual = form.cleaned_data["km_actual"]
            moto.save()
            LecturaKm.objects.create(moto=moto, km=moto.km_actual)
        messages.success(request, "¡Moto agregada! Registra lo que le hayas hecho hace poco para afinar las sugerencias.")
        return redirect(moto)
    return render(request, "garaje/form_moto.html", {"form": form, "nueva": True})


@con_motociclista
def editar(request, pk):
    moto = _moto_de(request, pk)
    form = MotoForm(request.POST or None, instance=moto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Datos actualizados.")
        return redirect(moto)
    return render(request, "garaje/form_moto.html", {"form": form, "moto": moto})


@con_motociclista
@require_POST
def eliminar(request, pk):
    moto = _moto_de(request, pk)
    moto.delete()
    messages.success(request, "Moto eliminada de tu garaje.")
    return redirect(reverse("garaje:garaje") + "?lista=1")


@con_motociclista
def detalle(request, pk):
    moto = _moto_de(request, pk)
    plan = calcular_plan(moto)

    # Talleres sugeridos para lo que toca ya o pronto, con sus cupones disponibles.
    servicios = {t.tarea.servicio_id for t in plan.urgentes + plan.pronto if t.tarea.servicio_id}
    talleres = []
    if servicios:
        talleres = list(
            Taller.objects.filter(activo=True, servicios__in=servicios).distinct()
            .select_related("barrio").prefetch_related("servicios")[:3]
        )
        cupones = Cupon.objects.disponibles().filter(taller__in=talleres)
        por_taller = {}
        for c in cupones:
            por_taller.setdefault(c.taller_id, []).append(c)
        for t in talleres:
            t.cupones_sugeridos = por_taller.get(t.pk, [])
            t.servicios_que_tocan = [s for s in t.servicios.all() if s.pk in servicios]

    despiece = Despiece.para(moto)
    return render(request, "garaje/moto.html", {
        "moto": moto,
        "plan": plan,
        "datos_3d": {"specs": moto.specs(), "color": moto.color, "piezas": plan.piezas()},
        "lectura_form": LecturaForm(moto=moto),
        "talleres_activos": Taller.objects.filter(activo=True).only("nombre"),
        "talleres": talleres,
        "lecturas": moto.lecturas.all()[:8],
        "historial": moto.mantenimientos.select_related("tarea", "taller")[:15],
        "otras_motos": request.motociclista.motos.exclude(pk=moto.pk),
        "despiece": despiece,
        "datos_despiece": datos_despiece(despiece, plan) if despiece else None,
    })


def datos_despiece(despiece, plan):
    """Láminas con sus piezas marcadas y el estado de mantenimiento de cada una, para el visor."""
    por_tarea = {t.tarea.pk: t for t in plan.tareas}
    piezas = plan.piezas()
    laminas = []
    for lamina in despiece.laminas.prefetch_related("partes__tarea__servicio"):
        partes, peor = [], None
        for p in lamina.partes.all():
            if not p.marcada:
                continue
            estado_tarea = por_tarea.get(p.tarea_id)
            parte = {
                "id": p.pk, "ref": p.ref, "codigo": p.codigo, "nombre": p.nombre, "descripcion": p.descripcion,
                "cantidad": p.cantidad, "x": p.x, "y": p.y, "estado": None, "tarea": None,
            }
            if estado_tarea:
                parte["estado"] = estado_tarea.estado
                parte["tarea"] = {
                    "nombre": estado_tarea.tarea.nombre, "etiqueta": estado_tarea.etiqueta,
                    "detalle": estado_tarea.detalle,
                    "servicio": estado_tarea.tarea.servicio_id,
                }
                if peor is None or GRAVEDAD[estado_tarea.estado] > GRAVEDAD[peor]:
                    peor = estado_tarea.estado
            partes.append(parte)
        if not partes:
            continue
        laminas.append({
            "id": lamina.pk, "figura": lamina.figura, "nombre": lamina.nombre, "pieza": lamina.pieza,
            "imagen": lamina.imagen.url, "ancho": lamina.ancho, "alto": lamina.alto,
            "estado": peor or piezas.get(lamina.pieza, {}).get("estado"), "partes": partes,
        })
    laminas.sort(key=lambda l: -GRAVEDAD.get(l["estado"] or "ok", 0))
    return {"version": despiece.version, "anio": despiece.anio, "laminas": laminas}


@con_motociclista
@require_POST
def registrar_km(request, pk):
    moto = _moto_de(request, pk)
    form = LecturaForm(request.POST, moto=moto)
    if form.is_valid():
        with transaction.atomic():
            moto.km_actual = form.cleaned_data["km"]
            moto.save(update_fields=["km_actual"])
            LecturaKm.objects.create(moto=moto, km=moto.km_actual)
        urgentes = len(calcular_plan(moto).urgentes)
        messages.success(request, f"Kilometraje actualizado: {moto.km_actual:,} km.".replace(",", ".")
                         + (f" Tienes {urgentes} pendiente{'s' if urgentes != 1 else ''} por hacer." if urgentes else ""))
    else:
        messages.error(request, " ".join(form.errors.get("km", ["Revisa el número."])))
    return redirect(moto)


@con_motociclista
@require_POST
def registrar_mantenimiento(request, pk):
    moto = _moto_de(request, pk)
    form = MantenimientoForm(request.POST, moto=moto)
    if form.is_valid():
        registro = form.save(commit=False)
        registro.moto = moto
        registro.save()
        messages.success(request, f"Registrado: {registro.tarea.nombre} a los {registro.km:,} km.".replace(",", "."))
    else:
        errores = [e for lista in form.errors.values() for e in lista]
        messages.error(request, " ".join(errores) or "Revisa los datos del mantenimiento.")
    return redirect(f"{moto.get_absolute_url()}#plan")
