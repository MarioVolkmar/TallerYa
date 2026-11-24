"""«Mis descuentos» del mecánico a domicilio: crear, editar y pausar sus descuentos (por dentro son cupones de
cupones.Cupon con `mecanico`), validar el código que le muestra un motero y ver los canjes. Se entra desde el bloque
de precios del panel (la fila de accesos se queda en 6)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from cupones.forms import DescuentoMecanicoForm, ValidarCodigoForm
from cupones.models import CodigoCupon, Cupon
from cupones.servicios import ErrorCanje, canjear_con_mecanico


def _mecanico(request):
    from .views import _perfil_de
    return _perfil_de(request.user)


def _ip(request):
    return request.META.get("REMOTE_ADDR")


@login_required
def descuentos(request):
    mecanico = _mecanico(request)
    if not mecanico:
        return redirect("domicilio:registro")
    form = ValidarCodigoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            codigo = canjear_con_mecanico(form.cleaned_data["codigo"], mecanico, via="codigo",
                                          usuario=request.user, ip=_ip(request))
        except ErrorCanje as e:
            form.add_error("codigo", str(e))
        else:
            from metricas.nucleo import registrar_evento
            registrar_evento(request, "cupon_canjeado", con_sesion=True, mecanico=True)
            messages.success(request, f"Cupón validado: {codigo.cupon.titulo} para {codigo.motociclista.nombre}.")
            return redirect("domicilio:descuentos")
    inicio_mes = timezone.localdate().replace(day=1)
    lista = (mecanico.cupones.annotate(entregados=Count("codigos", distinct=True),
                                       canjeados=Count("codigos", filter=Q(codigos__canjeado_en__isnull=False), distinct=True),
                                       num_emitidos=F("entregados"))
             .order_by("-activo", "-creado"))
    canjes = mecanico.canjes.select_related("cupon", "motociclista").order_by("-canjeado_en")
    return render(request, "domicilio/descuentos.html", {
        "m": mecanico, "form": form, "cupones": lista, "canjes": canjes[:8],
        "canjes_mes": canjes.filter(canjeado_en__date__gte=inicio_mes).count(),
        "publicado": mecanico.estado == mecanico.Estado.APROBADO,
    })


@login_required
def descuento_form(request, pk=None):
    mecanico = _mecanico(request)
    if not mecanico:
        return redirect("domicilio:registro")
    cupon = get_object_or_404(Cupon, pk=pk, mecanico=mecanico) if pk else None
    form = DescuentoMecanicoForm(request.POST or None, instance=cupon)
    if request.method == "POST" and form.is_valid():
        nuevo = form.save(commit=False)
        nuevo.mecanico, nuevo.taller = mecanico, None
        if not cupon:
            nuevo.publico, nuevo.premio_referido, nuevo.regalo_mensual, nuevo.solo_plus = True, False, False, False
        nuevo.save()
        if cupon:
            messages.success(request, "Cupón actualizado.")
        elif mecanico.estado == mecanico.Estado.APROBADO:
            messages.success(request, "Cupón publicado: ya aparece en tu ficha y en la página de cupones.")
        else:
            messages.success(request, "Cupón guardado: se verá en tu ficha cuando aprobemos tu perfil.")
        return redirect("domicilio:descuentos")
    return render(request, "talleres/cupon_form.html", {"form": form, "cupon": cupon, "m": mecanico, "descuento": True})


@login_required
@require_POST
def descuento_pausar(request, pk):
    mecanico = _mecanico(request)
    cupon = get_object_or_404(Cupon, pk=pk, mecanico=mecanico) if mecanico else None
    if cupon is None:
        return redirect("domicilio:registro")
    cupon.activo = not cupon.activo
    cupon.save(update_fields=["activo"])
    messages.success(request, "Cupón activado." if cupon.activo
                     else "Cupón pausado: ya no se entrega (los que ya tienen los moteros siguen sirviendo hasta su fecha).")
    return redirect("domicilio:descuentos")


def codigo_disponible(usuario, mecanico):
    """Descuento sin usar que el motero (con cuenta) ya tomó de este mecánico, para anotarlo en la solicitud."""
    moto = getattr(usuario, "motociclista", None) if usuario and usuario.is_authenticated else None
    if not moto:
        return None
    hoy = timezone.localdate()
    return (CodigoCupon.objects.filter(motociclista=moto, cupon__mecanico=mecanico, canjeado_en__isnull=True,
                                       cupon__activo=True, visitas__isnull=True)
            .filter(Q(cupon__valido_hasta__isnull=True) | Q(cupon__valido_hasta__gte=hoy))
            .select_related("cupon").order_by("-creado").first())
