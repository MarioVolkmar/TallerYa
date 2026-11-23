"""Alta asistida: el equipo carga un taller con los datos que dio el taller y se genera el enlace de revisión (sin cuenta)."""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from cuentas.limites import ip_cliente
from talleres.forms import RegistroTallerForm
from talleres.forms_alta import AltaAsistidaForm
from talleres.models import Taller

from .. import secciones
from ..acciones import registrar
from ..permisos import pagina_de_consola


@pagina_de_consola
def alta(request):
    form = AltaAsistidaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        taller = form.save(commit=False)
        taller.activo = False
        taller.origen_alta = Taller.Alta.ASISTIDO
        taller.generar_token()
        taller.save()
        form.save_m2m()
        registrar(actor=request.user, clave="talleres.alta_asistida", frase=f"Dio de alta (asistida) al taller #{taller.pk} ({taller.nombre})",
                  obj_tipo="taller", obj_id=taller.pk, obj_repr=taller, cambios=[], ip=ip_cliente(request))
        enlace = request.build_absolute_uri(reverse("talleres:revisar_ficha", args=[taller.token_revision]))
        messages.success(request, f"Taller creado sin publicar. Envíale este enlace para que revise y apruebe: {enlace}")
        return redirect(reverse("consola:inicio") + "?seccion=talleres&estado=por_aprobar")
    filas, total = secciones.con_pendientes()
    filas = [(s, n) for s, n in filas if s.en_menu and s.lista]  # mismo menú que consola.views
    return render(request, "consola/consola.html", {
        "seccion": secciones.POR_CLAVE["talleres"], "secciones": filas, "total_pendientes": total,
        "plantilla": "consola/alta_taller.html", "pendientes_seccion": 0, "form": form,
        "barrios_por_ciudad": RegistroTallerForm.barrios_por_ciudad()})
