"""SOAT (precio de ley y pedido dentro de TallerYa) y CDA para la técnico-mecánica (a donde llevan los avisos)."""
import mimetypes
from pathlib import Path
from urllib.parse import quote

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from garaje.models import Moto
from talleres.models import CIUDADES, Taller

from . import pagos
from .forms import PedidoSoatForm
from .models import CentroCDA, PedidoSoat, TarifaSoat


def _motos(request):
    motero = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    return motero, (list(motero.motos.select_related("linea", "linea__marca")) if motero else [])


def _elegida(request, motos):
    pk = request.GET.get("moto")
    return next((m for m in motos if str(m.pk) == pk), motos[0] if motos else None)


def _documento(moto, clave):
    return next((d for d in moto.documentos() if d["clave"] == clave), None) if moto else None


def soat(request):
    """Precio de ley según el cilindraje y, con sesión, el pedido del SOAT y su estado."""
    motero, motos = _motos(request)
    moto = _elegida(request, motos)
    cilindraje = None
    if moto:
        cilindraje = moto.specs().get("cilindraje")
    elif request.GET.get("cc", "").isdigit():
        cilindraje = int(request.GET["cc"])
    categoria = TarifaSoat.categoria_para(cilindraje)
    if not moto and not categoria and request.GET.get("cat") in TarifaSoat.Categoria.values:
        categoria = request.GET["cat"]                     # visitante: eligió la categoría sin escribir el cc
    anio = timezone.localdate().year
    tarifa = TarifaSoat.objects.filter(anio=anio, categoria=categoria).first() if categoria else None
    pedido = moto.pedidos_soat.exclude(estado=PedidoSoat.Estado.CANCELADA).first() if moto else None
    # Si el pedido anterior no pasó la validación, se vuelve a mostrar con sus datos y errores
    previo = request.session.pop("soat_form", None) if moto else None
    inicial = {}
    if motero:
        inicial = {"celular": motero.celular[-10:], "correo": request.user.email,
                   "nombre_completo": request.user.get_full_name()}
    form = PedidoSoatForm(previo, initial=inicial) if previo else PedidoSoatForm(initial=inicial)
    if previo:
        form.is_valid()
    return render(request, "tramites/soat.html", {
        "motero": motero, "motos": motos, "moto": moto, "cilindraje": cilindraje, "anio": anio,
        "categoria": TarifaSoat.Categoria(categoria).label if categoria else None,
        "categoria_clave": categoria,
        "tarifa": tarifa, "documento": _documento(moto, "soat"),
        "pedido": pedido, "url_pago": pagos.url_pago(pedido) if pedido else None, "simulado": pagos.simulado(),
        "form": form, "placa_form": (previo or {}).get("placa", moto.placa if moto else ""),
        # Un pedido nuevo solo si no hay uno en curso (o el último se emitió y ya toca renovar)
        "puede_pedir": bool(moto) and not (pedido and (pedido.activo or (
            pedido.estado == PedidoSoat.Estado.EMITIDA and _documento(moto, "soat")["estado"] == "ok"))),
    })


def _pedido_de(request, pk):
    motero = getattr(request.user, "motociclista", None)
    return get_object_or_404(PedidoSoat.objects.select_related("moto"), pk=pk, moto__motociclista=motero)


@login_required
@require_POST
def pedir_soat(request, pk):
    """Crea el pedido: datos de la moto desde el garaje + los del tomador. El precio es la tarifa de ley."""
    motero = getattr(request.user, "motociclista", None)
    moto = get_object_or_404(Moto.objects.select_related("linea"), pk=pk, motociclista=motero) if motero else None
    if not moto:
        return redirect("tramites:soat")
    volver = f"{reverse('tramites:soat')}?moto={moto.pk}"
    if moto.pedidos_soat.filter(estado__in=PedidoSoat.ACTIVOS).exists():
        messages.info(request, "Ya tienes un pedido de SOAT en curso para esta moto.")
        return redirect(volver)
    form = PedidoSoatForm(request.POST, request.FILES)
    placa = "".join(c for c in request.POST.get("placa", "").upper() if c.isalnum())[:8] or moto.placa
    valido = form.is_valid()
    if not placa:
        form.add_error(None, "Escribe la placa de tu moto.")
        valido = False
    if not valido:
        datos = request.POST.dict()
        datos.pop("csrfmiddlewaretoken", None)
        request.session["soat_form"] = datos
        messages.error(request, "Revisa los datos marcados." + (" Vuelve a adjuntar la foto." if request.FILES else ""))
        return redirect(volver + "#pedir")
    cilindraje = moto.specs().get("cilindraje")
    categoria = TarifaSoat.categoria_para(cilindraje)
    tarifa = TarifaSoat.objects.filter(anio=timezone.localdate().year, categoria=categoria).first()
    pedido = form.save(commit=False)
    pedido.moto, pedido.placa, pedido.linea = moto, placa, moto.nombre_completo
    pedido.cilindraje, pedido.categoria = cilindraje, categoria
    pedido.valor = tarifa.valor if tarifa else None
    pedido.acepta_datos_en = timezone.now()
    pedido.save()
    if not moto.placa:
        moto.placa = placa
        moto.save(update_fields=["placa"])
    from django.contrib.auth import get_user_model
    from notificaciones.models import Notificacion
    from notificaciones.servicios import notificar
    for admin_ in get_user_model().objects.filter(is_staff=True, is_active=True):
        notificar(admin_, f"pedido-soat:{pedido.pk}:nuevo", "Nuevo pedido de SOAT", f"{pedido.linea} · {placa}",
                  reverse("admin:tramites_pedidosoat_change", args=[pedido.pk]), Notificacion.Tipo.GENERAL)
    messages.success(request, "¡Pedido recibido! Te avisamos cuando tu póliza esté lista para pagar.")
    return redirect(volver)


@login_required
def pago_prueba(request, pk):
    """PAGO DE PRUEBA (simulación): no cobra ni pide tarjeta. Ver tramites/pagos.py para conectar el aliado."""
    pedido = _pedido_de(request, pk)
    volver = f"{reverse('tramites:soat')}?moto={pedido.moto_id}"
    if not pagos.simulado() or pedido.estado != PedidoSoat.Estado.LISTA_PAGAR:
        return redirect(volver)
    if request.method == "POST":
        pagos.confirmar_pago(pedido)
        messages.success(request, "Pago de prueba registrado. Te avisamos cuando tu póliza quede emitida.")
        return redirect(volver)
    return render(request, "tramites/pago_prueba.html", {"pedido": pedido, "volver": volver})


def _entregar(archivo, nombre):
    tipo = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
    respuesta = FileResponse(archivo.open("rb"), content_type=tipo)
    respuesta["Content-Disposition"] = f'inline; filename="{nombre}{Path(archivo.name).suffix}"'
    respuesta["Cache-Control"] = "private, no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta


@login_required
def poliza(request, pk):
    """PDF de la póliza: solo el dueño o el equipo."""
    pedido = get_object_or_404(PedidoSoat, pk=pk) if request.user.is_staff else _pedido_de(request, pk)
    if not pedido.poliza:
        raise Http404
    return _entregar(pedido.poliza, f"soat-{pedido.placa}")


@staff_member_required
def tarjeta(request, pk):
    """Foto de la tarjeta de propiedad: solo el equipo, para emitir la póliza."""
    pedido = get_object_or_404(PedidoSoat, pk=pk)
    if not pedido.tarjeta_propiedad:
        raise Http404
    return _entregar(pedido.tarjeta_propiedad, f"tarjeta-{pedido.placa}")


def tecnomecanica(request):
    """CDA (aliados primero) con precio y WhatsApp, y los talleres que llevan la moto a la revisión."""
    motero, motos = _motos(request)
    moto = _elegida(request, motos)
    municipio = request.GET.get("municipio", "")
    cdas = CentroCDA.objects.filter(activo=True)
    from django.db.models import Count
    por_municipio = dict(cdas.values_list("municipio").annotate(n=Count("pk")))
    if municipio in CIUDADES:
        cdas = cdas.filter(municipio=municipio)
    else:
        municipio = ""
    cdas = list(cdas)
    mensaje = "Hola, vengo de TallerYa. Quiero hacer la revisión técnico-mecánica de mi moto"
    if moto:
        mensaje += f" {moto}" + (f", placa {moto.placa}" if moto.placa else "")
    for c in cdas:
        numero = "".join(ch for ch in c.whatsapp if ch.isdigit())
        c.whatsapp_url = f"https://wa.me/{numero}?text={quote(mensaje + '.')}" if numero else ""
        lugar = quote(f"{c.nombre}, {c.direccion}, {c.municipio}, Antioquia, Colombia")
        c.mapa_url = f"https://www.google.com/maps?q={lugar}&output=embed"   # sin clave de API
        c.como_llegar = f"https://www.google.com/maps/dir/?api=1&destination={lugar}"
        palabras = [w for w in c.nombre.split() if w.upper() != "CDA"] or c.nombre.split()
        c.iniciales = "".join(w[0] for w in palabras[:2]).upper()
        c.tono = (c.pk * 47) % 360                                          # mismo tono que las tarjetas de taller
    talleres = _talleres_que_ayudan()
    return render(request, "tramites/tecnomecanica.html", {
        "motero": motero, "motos": motos, "moto": moto, "documento": _documento(moto, "tecno"),
        "cdas": cdas, "municipio": municipio, "talleres": talleres,
        "ciudades_con_cda": [(c, por_municipio.get(c, 0)) for c in CIUDADES],
    })


def _talleres_que_ayudan():
    """Talleres con el servicio de revisión técnico-mecánica: calificación anotada, horario y precio precargados."""
    from django.db.models import Avg, Count, Prefetch, Q

    from talleres.emergencias import abierto_ahora
    from talleres.models import PrecioServicio, Servicio
    servicio = Servicio.objects.filter(nombre__icontains="técnico").first()
    if not servicio:
        return []
    visibles = Q(resenas__visible=True)
    talleres = list(
        Taller.objects.filter(activo=True, servicios=servicio)
        .select_related("barrio", "usuario__perfil")
        .prefetch_related("horarios", Prefetch("precios", queryset=PrecioServicio.objects.filter(servicio=servicio),
                                               to_attr="precios_revision"))
        .annotate(prom=Avg("resenas__estrellas", filter=visibles), n_resenas=Count("resenas", filter=visibles, distinct=True))
        .order_by("-destacado", "-verificado", "nombre")[:6]
    )
    for t in talleres:
        palabras = [w for w in t.nombre.split() if len(w) > 2] or t.nombre.split()
        t.iniciales = "".join(w[0] for w in palabras[:2]).upper()
        t.tono = (t.pk * 47) % 360
        etiquetas = []
        if abierto_ahora(t, turnos=list(t.horarios.all())):
            etiquetas.append(("abierto", "Abierto ahora"))
        if t.grua:
            etiquetas.append(("recoge", "Recoge tu moto"))
        if t.precios_revision:
            etiquetas.append(("precio", f"Revisión desde ${min(p.desde for p in t.precios_revision):,}".replace(",", ".")))
        t.etiquetas = etiquetas[:2]
    return talleres

