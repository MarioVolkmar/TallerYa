from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from cuentas.models import Suscripcion
from garaje import pico_placa
from garaje.models import Gasto, LecturaKm

from . import comprobante as comp
from .balance import balance
from .bandera import requiere_bandera
from . import verificacion as verif
from .forms import JornadaForm, PerfilForm, VerificacionForm
from .intensivo import FACTORES, al_dia, km_semana_sugerido, plan_intensivo
from .models import Jornada, PerfilDomiciliario, TallerAliado, Verificacion, verificacion_vigente

NOTA_PLUS = "Plan domiciliario"


def _motociclista(request):
    return getattr(request.user, "motociclista", None) if request.user.is_authenticated else None


def _perfil(motociclista):
    if not motociclista:
        return None
    return PerfilDomiciliario.objects.filter(motociclista=motociclista).select_related("moto", "moto__linea").first()


def _aliados():
    return (TallerAliado.objects.filter(activo=True, taller__activo=True)
            .select_related("taller", "taller__barrio"))


def _ejemplo_intensivo():
    """Para la presentación: cuánto se adelanta cada pieza (intervalos generales de la base)."""
    from garaje.models import TareaMantenimiento
    filas = []
    for t in TareaMantenimiento.objects.filter(activo=True, pieza__in=list(FACTORES), intervalo_km__isnull=False):
        filas.append({"nombre": t.nombre, "normal": t.intervalo_km, "intensivo": round(t.intervalo_km * FACTORES[t.pieza] / 100) * 100})
    return filas[:6]


@requiere_bandera
def presentacion(request):
    motociclista = _motociclista(request)
    return render(request, "domiciliarios/presentacion.html", {
        "perfil": _perfil(motociclista), "motociclista": motociclista,
        "precio": settings.DOMICILIARIOS_PRECIO_PLUS, "precio_plus": settings.PLUS_PRECIO_MENSUAL,
        "aliados": _aliados()[:4], "ejemplo": _ejemplo_intensivo(),
    })


@requiere_bandera
@login_required
def activar(request):
    motociclista = _motociclista(request)
    if not motociclista:
        messages.info(request, "Primero completa tu perfil de motero.")
        return redirect("cuentas:mi_cuenta")
    if not motociclista.motos.exists():
        messages.info(request, "Agrega tu moto al garaje y vuelve: el plan se calcula con ella.")
        return redirect("garaje:agregar")
    perfil = _perfil(motociclista)
    form = PerfilForm(request.POST or None, instance=perfil, motociclista=motociclista,
                      initial=None if perfil else {"km_semana": 1200, "dias_semana": 6})
    if request.method == "POST" and form.is_valid():
        nuevo = form.save(commit=False)
        nuevo.motociclista = motociclista
        nuevo.save()
        messages.success(request, "Listo: ya tienes tu plan de uso intensivo." if not perfil else "Datos actualizados.")
        return redirect("domiciliarios:panel")
    return render(request, "domiciliarios/activar.html", {"form": form, "perfil": perfil})


@requiere_bandera
@login_required
@require_POST
def salir(request):
    perfil = _perfil(_motociclista(request))
    if perfil:
        perfil.delete()  # las jornadas se van con él; los gastos y km quedan en el garaje (son de la moto)
        messages.success(request, "Ya no estás marcado como domiciliario. Tu garaje sigue igual.")
    return redirect("domiciliarios:inicio")


def _montos_rapidos(jornadas):
    """4 montos de un toque para el cierre de jornada, alrededor de lo que suele ganar (redondeado a $10.000)."""
    ingresos = [j.ingreso for j in jornadas if j.ingreso]
    centro = round(sum(ingresos) / len(ingresos) / 10_000) * 10_000 if ingresos else 80_000
    centro = max(40_000, centro)
    return [centro - 20_000, centro, centro + 20_000, centro + 40_000]


@requiere_bandera
@login_required
def panel(request):
    motociclista = _motociclista(request)
    perfil = _perfil(motociclista)
    if not perfil:
        return redirect("domiciliarios:activar")
    moto = perfil.moto
    if not moto:
        messages.info(request, "Elige otra vez la moto con la que trabajas.")
        return redirect("domiciliarios:activar")
    hoy = timezone.localdate()
    plan = plan_intensivo(moto, perfil.km_semana, hoy)
    es_plus = motociclista.es_plus
    vigente = verificacion_vigente(perfil, hoy)
    jornada_hoy = perfil.jornadas.filter(fecha=hoy).first()
    contexto = {
        "perfil": perfil, "moto": moto, "plan": plan, "proximas": [t for t in plan.tareas if t.nivel != "desconocido"][:5],
        "al_dia": al_dia(plan), "documentos": moto.documentos(hoy), "pyp": pico_placa.resumen(moto, hoy),
        "manana_pyp": pico_placa.tiene_pico_placa(moto, hoy + timedelta(days=1))[0] if moto.placa else False,
        "balance": balance(perfil, hoy), "jornada_hoy": jornada_hoy, "jornadas": (jornadas := list(perfil.jornadas.all()[:7])),
        "montos": _montos_rapidos(jornadas),
        "form": JornadaForm(moto=moto), "aliados": _aliados(), "es_plus": es_plus,
        # Lo de Plus (descuentos y comprobante) exige además la verificación vigente; lo gratis no
        "verificado": vigente, "beneficios": es_plus and vigente is not None, "verif_pendiente": verif.pendiente(perfil),
        "precio": settings.DOMICILIARIOS_PRECIO_PLUS,
        "whatsapp_pago": request.session.pop("dm_whatsapp", None),
        "solicitud": motociclista.suscripciones.filter(estado=Suscripcion.Estado.SOLICITADA).first(),
    }
    if es_plus and vigente:
        enlace = request.build_absolute_uri(reverse("domiciliarios:comprobante", args=[comp.token(perfil)]))
        contexto["enlace_comprobante"] = enlace
        contexto["whatsapp_comprobante"] = "https://wa.me/?text=" + quote(f"Comprobante de mantenimiento de mi moto (TallerYa): {enlace}")
    return render(request, "domiciliarios/panel.html", contexto)


@requiere_bandera
@login_required
@require_POST
def jornada(request):
    perfil = _perfil(_motociclista(request))
    if not perfil or not perfil.moto:
        return redirect("domiciliarios:activar")
    moto = perfil.moto
    form = JornadaForm(request.POST, moto=moto)
    if not form.is_valid():
        for errores in form.errors.values():
            messages.error(request, " ".join(errores))
        return redirect(reverse("domiciliarios:panel") + "#jornada")
    hoy = timezone.localdate()
    datos = form.cleaned_data
    with transaction.atomic():
        if datos["km"] is not None and datos["km"] > moto.km_actual:
            moto.km_actual = datos["km"]
            moto.save(update_fields=["km_actual"])
            LecturaKm.objects.create(moto=moto, km=moto.km_actual, fecha=hoy)
        if datos["gasolina"]:
            Gasto.objects.create(moto=moto, fecha=hoy, tipo=Gasto.Tipo.GASOLINA, valor=datos["gasolina"],
                                 notas="Cierre de jornada")
        Jornada.objects.update_or_create(perfil=perfil, fecha=hoy,
                                         defaults={"ingreso": datos["ingreso"], "km_fin": datos["km"]})
    messages.success(request, "Jornada guardada. ¡Buen trabajo!")
    return redirect(reverse("domiciliarios:panel") + "#balance")


@requiere_bandera
@login_required
@require_POST
def solicitar_plus(request):
    motociclista = _motociclista(request)
    if not _perfil(motociclista):
        return redirect("domiciliarios:activar")
    solicitud = motociclista.suscripciones.filter(estado=Suscripcion.Estado.SOLICITADA).first()
    nota = f"{NOTA_PLUS} · ${settings.DOMICILIARIOS_PRECIO_PLUS:,}/mes".replace(",", ".")
    if solicitud:
        if NOTA_PLUS not in solicitud.notas:
            solicitud.notas = f"{solicitud.notas}\n{nota}".strip()
            solicitud.save(update_fields=["notas", "actualizado"])
    else:
        Suscripcion.objects.create(motociclista=motociclista, notas=nota)
    texto = (f"Hola TallerYa, quiero activar Plus domiciliario (${settings.DOMICILIARIOS_PRECIO_PLUS}). "
             f"Mi correo es {request.user.email}. Adjunto el comprobante de pago.")
    messages.success(request, f"¡Solicitud recibida! Paga ${settings.DOMICILIARIOS_PRECIO_PLUS:,} por Nequi al "
                              f"{settings.PLUS_NEQUI} y envía el comprobante por WhatsApp.".replace(",", "."))
    request.session["dm_whatsapp"] = f"https://wa.me/{settings.TALLERYA_WHATSAPP}?text={quote(texto)}"
    return redirect(reverse("domiciliarios:panel") + "#plus")


@requiere_bandera
@login_required
@require_POST
def anular_comprobante(request):
    perfil = _perfil(_motociclista(request))
    if perfil:
        PerfilDomiciliario.objects.filter(pk=perfil.pk).update(version_comprobante=F("version_comprobante") + 1)
        messages.success(request, "Listo: los enlaces que habías compartido ya no abren. Aquí tienes uno nuevo.")
    return redirect(reverse("domiciliarios:panel") + "#comprobante")


@requiere_bandera
def comprobante_publico(request, token):
    leido = comp.leer(token)
    if not leido:
        raise Http404
    perfil = (PerfilDomiciliario.objects.filter(pk=leido[0], version_comprobante=leido[1])
              .select_related("moto", "moto__linea", "moto__linea__marca", "motociclista").first())
    # Solo con Plus y verificación vigentes: si alguno vence, el comprobante deja de abrir
    if not perfil or not perfil.moto or not perfil.motociclista.es_plus or not verif.es_verificado(perfil):
        raise Http404
    hoy = timezone.localdate()
    plan = plan_intensivo(perfil.moto, perfil.km_semana, hoy)
    respuesta = render(request, "domiciliarios/comprobante.html", {
        "perfil": perfil, "moto": perfil.moto, "placa": comp.placa_oculta(perfil.moto.placa), "al_dia": al_dia(plan),
        "tareas": [t for t in plan.tareas if t.tarea.pieza in FACTORES and t.nivel != "desconocido"],
        "documentos": perfil.moto.documentos(hoy), "hoy": hoy,
        "nombre": perfil.motociclista.nombre.split(" ")[0] if perfil.motociclista.nombre else "",
    })
    respuesta["X-Robots-Tag"] = "noindex"
    respuesta["Referrer-Policy"] = "no-referrer"  # el token no se filtra a otros sitios
    respuesta["Cache-Control"] = "private, no-store"
    return respuesta


@requiere_bandera
@login_required
def verificacion(request):
    """Subir las 2 fotos (pantallazo del perfil con la moto y foto de la moto con placa). Nunca se piden contraseñas."""
    motociclista = _motociclista(request)
    perfil = _perfil(motociclista)
    if not perfil:
        messages.info(request, "Primero activa TallerYa Ruta (es gratis).")
        return redirect("domiciliarios:activar")
    vigente = verificacion_vigente(perfil)
    pendiente = verif.pendiente(perfil)
    ultima = perfil.verificaciones.exclude(estado=Verificacion.Estado.PENDIENTE).first()
    form = None
    if not vigente and not pendiente:
        form = VerificacionForm(request.POST or None, request.FILES or None, motociclista=motociclista,
                                initial={"plataforma": (perfil.plataformas or [""])[0], "moto": perfil.moto_id})
        if request.method == "POST" and form.is_valid():
            nueva = form.save(commit=False)
            nueva.perfil = perfil
            nueva.autorizacion = timezone.now()
            nueva.save()
            messages.success(request, "Recibimos tus fotos. Una persona del equipo las revisa y te avisamos aquí.")
            return redirect("domiciliarios:verificacion")
    elif request.method == "POST":
        return redirect("domiciliarios:verificacion")
    return render(request, "domiciliarios/verificacion.html", {
        "perfil": perfil, "vigente": vigente, "pendiente": pendiente, "ultima": ultima, "form": form,
    })


@requiere_bandera
@login_required
@require_POST
def cancelar_verificacion(request):
    """El dueño retira su solicitud: se borran las fotos y la solicitud."""
    perfil = _perfil(_motociclista(request))
    pendiente = verif.pendiente(perfil)
    if pendiente:
        pendiente.borrar_fotos()
        pendiente.delete()
        messages.success(request, "Listo: retiramos tu solicitud y borramos las fotos.")
    return redirect("domiciliarios:verificacion")


TIPOS_FOTO = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


@requiere_bandera
@login_required
def verificacion_foto(request, pk, campo):
    """Entrega la foto solo a su dueño o al staff; nunca por /media/. Mismo 404 si no existe o no es suya."""
    if campo not in ("captura", "foto_moto"):
        raise Http404
    v = Verificacion.objects.filter(pk=pk).select_related("perfil__motociclista").first()
    es_staff = request.user.is_staff and request.user.is_active
    if not v or not (es_staff or v.perfil.motociclista.usuario_id == request.user.pk):
        raise Http404
    archivo = getattr(v, campo)
    tipo = TIPOS_FOTO.get(archivo.name.rsplit(".", 1)[-1].lower()) if archivo else None
    if not tipo:
        raise Http404
    respuesta = FileResponse(archivo.open("rb"), content_type=tipo)
    respuesta["Content-Disposition"] = f'inline; filename="verificacion-{v.pk}-{campo}"'
    respuesta["Cache-Control"] = "private, no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"
    respuesta["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return respuesta


@requiere_bandera
@login_required
@require_POST
def moto_trabajo(request, pk):
    """Interruptor «La uso para trabajar» de la página de la moto. Prendido: esa moto lleva el plan intensivo y la
    tarjeta Mi ruta (crea el perfil si no existe). Apagado: vuelve al plan normal; el perfil y las jornadas quedan."""
    motociclista = _motociclista(request)
    moto = motociclista.motos.filter(pk=pk).first() if motociclista else None  # solo sus motos (sin IDOR)
    if not moto:
        raise Http404
    perfil = _perfil(motociclista)
    if request.POST.get("valor") == "1":
        if not perfil:
            perfil = PerfilDomiciliario(motociclista=motociclista, km_semana=km_semana_sugerido(moto))
        perfil.moto = moto
        perfil.save()
        messages.success(request, "Listo: esta moto lleva el plan de uso intensivo y su tarjeta Mi ruta.")
    elif perfil and perfil.moto_id == moto.pk:
        perfil.moto = None
        perfil.save(update_fields=["moto", "actualizado"])
        messages.success(request, "Esta moto vuelve al plan normal. Tus jornadas quedan guardadas.")
    if request.POST.get("volver") == "garaje":  # desde el modo «Editar» de Mi garaje (valor fijo, sin redirección abierta)
        return redirect(reverse("garaje:garaje") + "?lista=1")
    return redirect(moto.get_absolute_url())
