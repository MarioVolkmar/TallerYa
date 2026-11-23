"""Vistas públicas de proveedores: «Soy proveedor» (autoregistro, apagable), revisión de la ficha por enlace con token
(sin cuenta ni contraseña) y el contador de clics a WhatsApp / llamar.

Una ficha dada de alta por el proveedor o por el equipo con sus datos queda «Por revisar» hasta que él la apruebe
(autorizando sus datos, Ley 1581) y el equipo la publique desde la consola."""
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from consola.ajustes import ajuste
from cuentas import limites
from cuentas.limites import ip_cliente
from talleres.estadisticas import es_bot

from .forms import AutoregistroForm, RevisionForm
from .models import Categoria, EventoProveedor, Proveedor

ALTAS_HORA_IP = 5
CLICS_HORA_IP = 60


def _sin_indexar(respuesta):
    respuesta["X-Robots-Tag"] = "noindex, nofollow"
    return respuesta


def _campos_por_categoria():
    """{pk: [campos propios]} para que la plantilla muestre solo los de la categoría elegida."""
    return {str(c.pk): {"campos": c.campos, "precio": c.etiqueta_precio} for c in Categoria.objects.all()}


def autoregistro(request):
    """«Soy proveedor»: el negocio llena su ficha desde el celular; queda «Por revisar» hasta que el equipo la publique."""
    if not ajuste("proveedores_registro"):
        raise Http404
    ip = ip_cliente(request)
    form = AutoregistroForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if limites.superado(f"alta-proveedor:{ip}", ALTAS_HORA_IP):
            form.add_error(None, "Se enviaron muchos registros desde esta conexión. Intenta en una hora.")
        elif form.is_valid():
            obj = form.save(commit=False)
            obj.estado = Proveedor.Estado.POR_REVISAR
            obj.origen_alta = Proveedor.Alta.AUTOREGISTRO
            obj.autoriza_datos = True
            obj.aprobado_por_proveedor, obj.aprobado_ip = timezone.now(), ip
            obj.generar_token()
            obj.save()
            limites.sumar(f"alta-proveedor:{ip}", 3600)
            return redirect("proveedores:enviada", token=obj.token_revision)
    return _sin_indexar(render(request, "proveedores/autoregistro.html", {
        "form": form, "campos_por_categoria": _campos_por_categoria()}))


def enviada(request, token):
    obj = get_object_or_404(Proveedor.objects.exclude(origen_alta=Proveedor.Alta.EQUIPO), token_revision=token)
    return _sin_indexar(render(request, "proveedores/enviada.html", {"proveedor": obj}))


def revisar(request, token):
    """Enlace sin cuenta: el proveedor ve su ficha, corrige y aprueba. Después de aprobar queda de solo lectura."""
    obj = get_object_or_404(Proveedor.objects.select_related("categoria").exclude(origen_alta=Proveedor.Alta.EQUIPO),
                            token_revision=token)
    if obj.aprobado_por_proveedor:
        return _sin_indexar(render(request, "proveedores/revisar.html", {"proveedor": obj, "aprobada": True}))
    if obj.enlace_vencido:
        return _sin_indexar(render(request, "proveedores/revisar.html", {"proveedor": obj, "vencida": True}, status=410))
    form = RevisionForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        nuevo = form.save(commit=False)
        if form.cleaned_data["autoriza"]:
            nuevo.autoriza_datos = True
            nuevo.aprobado_por_proveedor, nuevo.aprobado_ip = timezone.now(), ip_cliente(request)
        nuevo.save()
        if form.cleaned_data["autoriza"]:
            messages.success(request, "¡Listo! Aprobaste tu ficha. El equipo de TallerYa la publica en breve.")
        else:
            messages.info(request, "Guardamos tus correcciones. Para publicar, marca la autorización y aprueba.")
        return redirect("proveedores:revisar", token=token)
    return _sin_indexar(render(request, "proveedores/revisar.html", {"proveedor": obj, "form": form, "aprobada": False}))


@csrf_exempt  # solo suma 1 a un contador agregado; no cambia nada del usuario ni lee datos suyos
@require_POST
def clic(request, pk, canal):
    tipos = {"whatsapp": EventoProveedor.Tipo.WHATSAPP, "llamada": EventoProveedor.Tipo.LLAMADA}
    if canal not in tipos:
        raise Http404
    ip = ip_cliente(request)
    if es_bot(request) or limites.superado(f"clic-proveedor:{ip}", CLICS_HORA_IP):
        return HttpResponse(status=204)
    if not Proveedor.objects.publicados().filter(pk=pk).exists():
        raise Http404
    limites.sumar(f"clic-proveedor:{ip}", 3600)
    hoy, tipo = timezone.localdate(), tipos[canal]
    n = EventoProveedor.objects.filter(proveedor_id=pk, fecha=hoy, tipo=tipo).update(cantidad=F("cantidad") + 1)
    if not n:
        try:
            with transaction.atomic():
                EventoProveedor.objects.create(proveedor_id=pk, fecha=hoy, tipo=tipo, cantidad=1)
        except IntegrityError:  # otro clic creó la fila al mismo tiempo
            EventoProveedor.objects.filter(proveedor_id=pk, fecha=hoy, tipo=tipo).update(cantidad=F("cantidad") + 1)
    return HttpResponse(status=204)
