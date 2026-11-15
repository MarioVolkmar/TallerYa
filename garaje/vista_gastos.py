"""Vista de gastos y consumo de una moto."""
from django.contrib import messages
from django.shortcuts import redirect, render

from . import gastos
from .forms_gastos import GastoForm
from .views import _moto_de, con_motociclista


@con_motociclista
def gastos_moto(request, pk):
    moto = _moto_de(request, pk)
    # "Editar" desde el detalle de un movimiento: el mismo formulario, con ese gasto cargado
    editando = moto.gastos.filter(pk=request.POST.get("gasto") or request.GET.get("editar") or 0).first()
    form = GastoForm(instance=editando, moto=moto)
    if request.method == "POST":
        if request.POST.get("accion") == "eliminar":
            if moto.gastos.filter(pk=request.POST.get("gasto")).delete()[0]:
                messages.success(request, "Gasto eliminado.")
            return redirect("garaje:gastos", moto.pk)
        form = GastoForm(request.POST, instance=editando, moto=moto)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.moto = moto
            gasto.save()
            messages.success(request, "Gasto actualizado." if editando else "Gasto registrado.")
            return redirect("garaje:gastos", moto.pk)
    return render(request, "garaje/gastos.html", {"moto": moto, "form": form, "editando": editando,
                                                  **gastos.resumen(moto)})
