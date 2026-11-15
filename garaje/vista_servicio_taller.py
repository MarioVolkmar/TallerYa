"""Lado del dueño: ver el servicio que registró un taller, confirmarlo (si llegó por placa) o decir que no es suyo."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from . import servicio_taller as st
from .models import ServicioTaller


@login_required
def servicio_taller(request, pk):
    s = get_object_or_404(ServicioTaller.objects.select_related("taller", "taller__barrio", "moto", "moto__linea",
                                                                "moto__linea__marca")
                          .prefetch_related("tareas"), pk=pk, moto__motociclista__usuario=request.user)
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "confirmar" and st.confirmar(s):
            messages.success(request, "¡Listo! Quedó verificado en tu hoja de vida y tu plan se puso al día.")
        elif accion == "rechazar" and st.rechazar(s):
            messages.info(request, "Lo quitamos de tu hoja de vida y le avisamos al taller.")
        return redirect(s)
    return render(request, "garaje/servicio_taller.html", {
        "s": s, "estados": ServicioTaller.Estado,
        "ya_califico": s.taller.resenas.filter(usuario=request.user).exists(),
    })
