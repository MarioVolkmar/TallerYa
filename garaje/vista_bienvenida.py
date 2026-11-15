"""Guía de bienvenida (primer uso): 1 Tu moto · 2 Último mantenimiento · 3 Tu plan · 4 Qué más.

Los pasos 1 y 2 son el mismo formulario de «Agregar moto» (views.agregar con ?guia=1). Aquí van el arranque, los pasos
3 y 4 y «Saltar». Quién la ve y cuándo deja de salir se decide en cuentas/guia.py."""
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from cuentas import guia

from .plan import calcular_plan
from .views import _moto_de, con_motociclista, resumen_plan


@con_motociclista
def bienvenida(request):
    """Arranque: sin motos, al formulario en modo guía; con motos (volvió a entrar a medias), a ver su plan."""
    primera = request.motociclista.motos.order_by("pk").first()
    if primera:
        return redirect("garaje:bienvenida_plan", pk=primera.pk)
    return redirect(reverse("garaje:agregar") + "?guia=1")


@con_motociclista
def bienvenida_plan(request, pk):
    """Paso 3: su moto en 3D y «Lo urgente» (o «Lo que viene» si todo está al día)."""
    moto = _moto_de(request, pk)
    plan = calcular_plan(moto)
    todo_al_dia, lo_urgente = resumen_plan(plan)
    return render(request, "garaje/bienvenida.html", {
        "paso": 3, "moto": moto, "plan": plan, "todo_al_dia": todo_al_dia, "lo_urgente": lo_urgente,
        "sin_registro": len(plan.sin_registro)})


@con_motociclista
def bienvenida_listo(request, pk):
    """Paso 4: qué más puede hacer. Llegar aquí ya cuenta como guía terminada."""
    moto = _moto_de(request, pk)
    guia.marcar_vista(request.user)
    return render(request, "garaje/bienvenida.html", {"paso": 4, "moto": moto})


@require_POST
@con_motociclista
def bienvenida_saltar(request):
    guia.marcar_vista(request.user)
    primera = request.motociclista.motos.order_by("pk").first()
    return redirect(primera or "talleres:inicio")
