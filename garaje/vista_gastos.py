"""Vista de gastos y consumo de una moto."""
from django.contrib import messages
from django.shortcuts import redirect, render

from . import gastos
from .forms_gastos import GastoForm
from .models import LecturaKm
from .views import _moto_de, con_motociclista


@con_motociclista
def gastos_moto(request, pk):
    moto = _moto_de(request, pk)
    form = GastoForm(moto=moto)
    if request.method == "POST":
        if request.POST.get("accion") == "eliminar":
            if moto.gastos.filter(pk=request.POST.get("gasto")).delete()[0]:
                messages.success(request, "Gasto eliminado.")
            return redirect("garaje:gastos", moto.pk)
        form = GastoForm(request.POST, moto=moto)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.moto = moto
            gasto.save()
            if gasto.km and gasto.km > moto.km_actual:  # el odómetro del tanqueo también actualiza el kilometraje
                LecturaKm.objects.create(moto=moto, km=gasto.km, fecha=gasto.fecha)
                moto.km_actual = gasto.km
                moto.save(update_fields=["km_actual"])
            messages.success(request, "Gasto registrado.")
            return redirect("garaje:gastos", moto.pk)
    return render(request, "garaje/gastos.html", {"moto": moto, "form": form, **gastos.resumen(moto)})
