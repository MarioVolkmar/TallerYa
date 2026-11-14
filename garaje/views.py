from urllib.parse import quote
from datetime import date, timedelta
import hashlib
import mimetypes
import re
import unicodedata
from functools import wraps
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import caches
from django.db import transaction
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from cupones.models import Cupon
from talleres.models import Servicio, Taller

from .forms import LecturaForm, MantenimientoForm, MotoForm
import json

from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.clickjacking import xframe_options_sameorigin

from . import diagramas, pico_placa
from .avisos import avisos_moto
from .despiece_variantes import quitar_modelo, datos_tecnicos, nombre_por_sistema, nombres_distintos, separar_nombre, texto_tecnico
from .despiece_fichas import ficha_completa, tiene_guia_propia
from .despiece_guia_mecanica import guia_mecanica
from .despiece_sistemas import ORDEN_SUBGRUPOS, sistema_de, sistemas_de
from .models import (COLORES, COLORES_EXTRA, COLORES_SECUNDARIOS, DISENOS_CALCA, DOCUMENTOS, HEX, Despiece, LecturaKm,
                     AjusteTarea, LineaMoto, Mantenimiento, Moto, ParteDespiece, SolicitudSoat, TareaMantenimiento)
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
    if len(motos) == 1 and not request.GET.get("lista"):
        return redirect(motos[0])
    planes = [(m, calcular_plan(m)) for m in motos]
    avisos = [{**a, "moto": m} for m in motos for a in avisos_moto(m)]
    return render(request, "garaje/garaje.html", {"planes": planes, "puede_agregar": len(motos) < MAX_MOTOS,
                                                  "avisos": avisos})


@con_motociclista
def agregar(request):
    if request.motociclista.motos.count() >= MAX_MOTOS:
        messages.info(request, f"Puedes tener hasta {MAX_MOTOS} motos en tu garaje.")
        return redirect("garaje:garaje")
    form = MotoForm(request.POST or None, request.FILES or None)
    filas, mostrar_paso2 = [], False
    if request.method == "POST" and form.is_valid():
        km_actual = form.cleaned_data["km_actual"]
        tareas = _tareas_principales(form.instance)
        nuevos, errores = _leer_al_dia(request.POST, tareas, km_actual)
        if errores:
            filas, mostrar_paso2 = _filas_al_dia(tareas, request.POST, errores), True
        else:
            # Todo junto y solo ahora: si la persona abandona el formulario, no queda una moto a medias.
            with transaction.atomic():
                moto = form.save(commit=False)
                moto.motociclista = request.motociclista
                moto.km_inicial = moto.km_actual = km_actual
                moto.save()
                LecturaKm.objects.create(moto=moto, km=moto.km_actual)
                for m in nuevos:
                    m.moto = moto
                Mantenimiento.objects.bulk_create(nuevos)
            messages.success(request, "¡Moto agregada! " + _mensaje_al_dia(len(nuevos)))
            return redirect(moto)
    return render(request, "garaje/form_moto.html", {
        "form": form, "nueva": True, "documentos_form": _documentos_form(form),
        "filas": filas, "mostrar_paso2": mostrar_paso2, "tentativos": MESES_TENTATIVOS.items(),
        "km_actual": request.POST.get("km_actual", "") if request.method == "POST" else ""})


def _documentos_form(form, moto=None):
    """Agrupa los campos de SOAT y técnico-mecánica para pintarlos como tarjetas en el formulario."""
    ayudas = {"soat": "Dura 1 año desde que empieza la cobertura.",
              "tecno": "Las motos nuevas la hacen por primera vez a los 2 años de la matrícula; luego, cada año."}
    lista = []
    for clave, nombre in DOCUMENTOS.items():
        actual = bool(moto and getattr(moto, f"{clave}_archivo"))
        lista.append({
            "nombre": nombre, "fecha": form[f"{clave}_vence"], "archivo": form[f"{clave}_archivo"],
            "quitar": form[f"quitar_{clave}"], "actual": actual, "ayuda": ayudas[clave],
            "extra": form["matricula"] if clave == "tecno" and "matricula" in form.fields else None,
            "url_ver": reverse("garaje:documento", args=[moto.pk, clave]) if actual else "",
        })
    return lista


@con_motociclista
def editar(request, pk):
    moto = _moto_de(request, pk)
    form = MotoForm(request.POST or None, request.FILES or None, instance=moto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Datos actualizados.")
        return redirect(moto)
    return render(request, "garaje/form_moto.html", {"form": form, "moto": moto, "documentos_form": _documentos_form(form, moto)})


@con_motociclista
def documento(request, pk, clave):
    """Entrega el SOAT o la técnico-mecánica solo al dueño de la moto; nunca por una URL pública."""
    if clave not in DOCUMENTOS:
        raise Http404
    moto = _moto_de(request, pk)
    archivo = getattr(moto, f"{clave}_archivo")
    if not archivo:
        raise Http404
    tipo = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
    respuesta = FileResponse(archivo.open("rb"), content_type=tipo)
    respuesta["Content-Disposition"] = f'inline; filename="{clave}-{moto.pk}{Path(archivo.name).suffix}"'
    respuesta["Cache-Control"] = "private, no-store"
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta


@con_motociclista
@require_POST
def eliminar(request, pk):
    moto = _moto_de(request, pk)
    moto.delete()
    messages.success(request, "Moto eliminada de tu garaje.")
    return redirect(reverse("garaje:garaje") + "?lista=1")


LIMITE_HISTORIAL = 50  # registros que se envían a la página; allí se muestran de a 6 con "Ver más"


def _lecturas_con_diferencia(moto):
    """Últimas lecturas (más reciente primero) con cuántos km subió desde la anterior."""
    lecturas = list(moto.lecturas.all()[:LIMITE_HISTORIAL + 1])
    for actual, anterior in zip(lecturas, lecturas[1:] + [None]):
        actual.diferencia = actual.km - anterior.km if anterior else None
    return lecturas[:LIMITE_HISTORIAL]


# Por qué importa cada mantenimiento (consecuencias generales de no hacerlo a tiempo).
POR_QUE = {
    "aceite": "El aceite viejo pierde su capacidad de lubricar: el motor se desgasta más rápido, se calienta y consume más.",
    "cadena-lubricar": "Una cadena seca se estira y desgasta el piñón y la corona; además puede saltarse o romperse andando.",
    "kit-arrastre": "Una cadena estirada o dientes gastados hacen que la transmisión patine o se suelte en marcha.",
    "correa-cvt": "Una correa gastada patina y resta fuerza; si se revienta, la moto se queda sin tracción de inmediato.",
    "filtro-aire": "Un filtro tapado ahoga el motor: pierde potencia, consume más combustible y entra polvo que lo desgasta.",
    "bujia": "Una bujía gastada causa mal encendido, tirones y más consumo, y puede dejarte varado.",
    "valvulas": "Con las válvulas descalibradas el motor pierde potencia, suena más y puede dañarse la culata.",
    "pastillas-del": "Unas pastillas gastadas frenan menos y, al llegar al metal, rayan el disco y encarecen la reparación.",
    "bandas-del": "Bandas gastadas o desajustadas alargan la distancia de frenado y pueden rayar la campana.",
    "pastillas-tras": "Unas pastillas gastadas frenan menos y, al llegar al metal, rayan el disco y encarecen la reparación.",
    "bandas-tras": "Bandas gastadas o desajustadas alargan la distancia de frenado y pueden rayar la campana.",
    "liquido-frenos": "El líquido viejo absorbe humedad: el freno se siente esponjoso y puede fallar al calentarse.",
    "llanta-del": "Una llanta lisa pierde agarre, sobre todo con lluvia, y aumenta el riesgo de caída al frenar o girar.",
    "llanta-tras": "Una llanta lisa pierde agarre y tracción, sobre todo con lluvia, y se pincha con más facilidad.",
    "suspension-del": "Con el aceite de las barras gastado la moto rebota, frena peor y los retenedores empiezan a botar aceite.",
    "suspension-tras": "Amortiguadores vencidos hacen la moto inestable, rebotan en los huecos y cansan más al manejar.",
    "refrigerante": "El refrigerante viejo protege menos: el motor puede recalentarse y el radiador oxidarse por dentro.",
    "bateria": "Una batería débil deja la moto sin arrancar y puede afectar las luces y el sistema eléctrico.",
}


def _talleres_del_plan(plan):
    """Talleres activos que hacen algún servicio del plan, con sus cupones disponibles ({taller_id: [cupones]}).
    La ficha de la moto los usa en tres bloques (sugeridos, piezas del 3D y agenda): se cargan una sola vez
    por visita y se guardan en el plan."""
    if not hasattr(plan, "_talleres"):
        servicios = {t.tarea.servicio_id for t in plan.tareas if t.tarea.servicio_id}
        talleres = list(Taller.objects.filter(activo=True, servicios__in=servicios).distinct()
                        .select_related("barrio").prefetch_related("servicios", "marcas")) if servicios else []
        cupones = {}
        for c in Cupon.objects.disponibles().filter(taller__in=talleres):
            cupones.setdefault(c.taller_id, []).append(c)
        plan._talleres = (talleres, cupones)
    return plan._talleres


def _talleres_que_hacen(plan, servicios):
    """Del listado del plan, los talleres que hacen alguno de esos servicios (mismo orden) y su primer cupón."""
    todos, cupones = _talleres_del_plan(plan)
    talleres = [tl for tl in todos if servicios & {s.pk for s in tl.servicios.all()}]
    return talleres, {pk: lista[0] for pk, lista in cupones.items()}


def _acciones_piezas(moto, plan):
    """Para cada pieza del modelo 3D: el mejor taller que hace su servicio (con su cupón, si tiene) y el directorio
    filtrado por ese servicio. Así, al tocar una pieza en el 3D se puede ir directo a resolverla."""
    piezas = plan.piezas()
    servicio_de = {}
    for t in sorted(plan.tareas, key=lambda t: -GRAVEDAD[t.estado]):
        if t.tarea.servicio_id:
            servicio_de.setdefault(t.tarea.pieza, t.tarea)
    if not servicio_de:
        return piezas
    marca = moto.linea.marca_id if moto.linea_id else None
    talleres, cupones = _talleres_que_hacen(plan, {t.servicio_id for t in servicio_de.values()})
    talleres.sort(key=lambda tl: (tl.pk not in cupones, not (marca and any(m.pk == marca for m in tl.marcas.all())),
                                  not tl.destacado, not tl.verificado, tl.nombre))
    servicios_de = {tl.pk: {s.pk for s in tl.servicios.all()} for tl in talleres}
    directorio = reverse("talleres:directorio")
    for clave, tarea in servicio_de.items():
        if clave not in piezas:
            continue
        acciones = {"talleres": f"{directorio}?servicio={tarea.servicio_id}"}
        mejor = next((tl for tl in talleres if tarea.servicio_id in servicios_de[tl.pk]), None)
        if mejor:
            acciones["taller"] = {"nombre": mejor.nombre, "url": mejor.get_absolute_url(),
                                  "whatsapp": _whatsapp_para(mejor, tarea, moto) if mejor.whatsapp else ""}
            cupon = cupones.get(mejor.pk)
            if cupon:
                acciones["cupon"] = {"titulo": cupon.titulo, "url": reverse("cupones:obtener", args=[cupon.pk])}
        piezas[clave]["acciones"] = acciones
    return piezas


def _whatsapp_para(taller, tarea, moto):
    texto = (f"Hola {taller.nombre}, te escribo desde TallerYa. Necesito {tarea.nombre.lower()} para mi {moto}. "
             "¿Tienen disponibilidad?")
    return f"https://wa.me/{taller.whatsapp}?text={quote(texto)}"


def _grupos_agenda(plan, ajustes):
    """Los cuatro grupos de la agenda (los mismos que cuenta la leyenda bajo el 3D)."""
    def pospuesta(t):
        a = ajustes.get(t.tarea.pk)
        return bool(a and a.pospuesta)
    def cerca(t):
        return ((t.km_restantes is not None and t.km_restantes <= 3000) or
                (t.dias_restantes is not None and t.dias_restantes <= 60))
    pendientes = [t for t in plan.tareas if t.estado in ("vencido", "pronto")]
    al_dia = sorted(plan.al_dia, key=lambda t: (t.fecha_estimada or date.max, t.km_restantes if t.km_restantes is not None else 10**9))
    return {
        "atencion": [t for t in pendientes if not pospuesta(t)],
        "proximos": [t for t in pendientes if pospuesta(t)] + [t for t in al_dia if cerca(t)],
        "sin_registro": plan.sin_registro,
        "al_dia": [t for t in al_dia if not cerca(t)],
    }


def _conteos_agenda(moto, plan):
    grupos = _grupos_agenda(plan, {a.tarea_id: a for a in moto.ajustes.all()})
    return {clave: len(lista) for clave, lista in grupos.items()}


def _agenda(moto, plan, despiece=None):
    """La "Agenda de mantenimiento": próximo servicio, grupos por estado y una ficha de acción por tarea."""
    hoy = timezone.localdate()
    ajustes = {a.tarea_id: a for a in moto.ajustes.all()}
    activas = [t for t in plan.tareas if t.estado in ("ok", "pronto")]
    proximo = min(activas, key=lambda t: (t.fecha_estimada or date.max, t.km_restantes if t.km_restantes is not None else 10**9),
                  default=None)

    # Repuestos de cada tarea (si la moto tiene despiece) y por qué importa (de la guía de la pieza).
    repuestos, por_que = {}, {}
    if despiece:
        for p in ParteDespiece.objects.filter(lamina__despiece=despiece, tarea__isnull=False).select_related("lamina"):
            lista = repuestos.setdefault(p.tarea_id, [])
            if all(r["codigo"] != p.codigo for r in lista):
                lista.append({"nombre": p.nombre, "codigo": p.codigo, "cantidad": p.cantidad})
            if p.tarea_id not in por_que:
                consecuencia = ficha_completa(p.descripcion, p.lamina.pieza).get("si_no")
                if consecuencia:
                    por_que[p.tarea_id] = consecuencia if isinstance(consecuencia, str) else " ".join(consecuencia)

    # El mejor taller para cada servicio: con cupón, que trabaje tu marca, destacado, verificado.
    servicios = {t.tarea.servicio_id for t in plan.tareas if t.tarea.servicio_id}
    marca = moto.linea.marca_id if moto.linea_id else None
    talleres, cupones = _talleres_que_hacen(plan, servicios)
    def puntaje(tl):
        return (tl.pk not in cupones, not (marca and any(m.pk == marca for m in tl.marcas.all())), not tl.destacado,
                not tl.verificado, tl.nombre)
    talleres.sort(key=puntaje)
    servicios_de = {tl.pk: {s_.pk for s_ in tl.servicios.all()} for tl in talleres}

    for t in plan.tareas:
        t.ajuste = ajustes.get(t.tarea.pk)
        t.repuestos = repuestos.get(t.tarea.pk, [])
        t.por_que = POR_QUE.get(t.tarea.clave) or por_que.get(t.tarea.pk) or t.tarea.descripcion
        mejor = next((tl for tl in talleres if t.tarea.servicio_id in servicios_de[tl.pk]), None)
        t.taller_sugerido = mejor and {"taller": mejor, "cupon": cupones.get(mejor.pk),
                                       "whatsapp": _whatsapp_para(mejor, t.tarea, moto)}
        # Para el calendario: la fecha estimada, o en una semana si ya toca.
        t.fecha_calendario = t.fecha_estimada if t.fecha_estimada and t.fecha_estimada > hoy else hoy + timedelta(days=7)

    grupos = _grupos_agenda(plan, ajustes)
    atencion = grupos["atencion"]

    # ¿Un solo taller resuelve varias cosas de las que tocan? Se sugiere una sola visita.
    visita = None
    for tl in talleres:
        cubre = [t for t in atencion if t.tarea.servicio_id in servicios_de[tl.pk]]
        if len(cubre) >= 2 and (not visita or len(cubre) > len(visita["tareas"])):
            visita = {"taller": tl, "tareas": cubre, "cupon": cupones.get(tl.pk),
                      "whatsapp": f"https://wa.me/{tl.whatsapp}?text=" + quote(
                          f"Hola {tl.nombre}, te escribo desde TallerYa. Para mi {moto} necesito: "
                          + ", ".join(t.tarea.nombre.lower() for t in cubre) + ". ¿Me puedes dar cita?")}

    para_agendar = next((t for t in atencion + ([proximo] if proximo else []) if t.tarea.servicio_id), None)
    return {
        "proximo": proximo,
        "servicio_agendar": para_agendar.tarea.servicio_id if para_agendar else None,
        "visita": visita,
        **grupos,
    }


@con_motociclista
@require_POST
def ajustar_tarea(request, pk):
    """Posponer un mantenimiento, pedir un recordatorio o quitar lo que se había ajustado."""
    moto = _moto_de(request, pk)
    tarea = get_object_or_404(TareaMantenimiento, pk=request.POST.get("tarea") or 0)
    accion = request.POST.get("accion")
    hoy = timezone.localdate()
    ajuste, _ = AjusteTarea.objects.get_or_create(moto=moto, tarea=tarea)
    if accion == "posponer":
        dias = int(request.POST.get("dias", "7")) if request.POST.get("dias", "7").isdigit() else 7
        ajuste.pospuesto_hasta = hoy + timedelta(days=min(max(dias, 1), 90))
        mensaje = f"Pospusimos «{tarea.nombre}» hasta el {ajuste.pospuesto_hasta:%d/%m/%Y}."
    elif accion == "recordar":
        try:
            fecha = date.fromisoformat(request.POST.get("fecha", ""))
        except ValueError:
            fecha = None
        if not fecha or fecha < hoy:
            messages.error(request, "Elige una fecha de hoy en adelante para el recordatorio.")
            return redirect(reverse("garaje:moto", args=[moto.pk]) + "#plan")
        ajuste.recordar_el, ajuste.recordado = fecha, False
        mensaje = f"Te recordaremos «{tarea.nombre}» el {fecha:%d/%m/%Y}."
    else:
        ajuste.delete()
        messages.success(request, f"Quitamos el ajuste de «{tarea.nombre}».")
        return redirect(reverse("garaje:moto", args=[moto.pk]) + "#plan")
    ajuste.save()
    messages.success(request, mensaje)
    return redirect(reverse("garaje:moto", args=[moto.pk]) + "#plan")


def _miles(n):
    return f"{n:,}".replace(",", ".")


def _aceite(plan):
    """Estado del cambio de aceite listo para el indicador tipo tacómetro (o None si no aplica)."""
    t = next((t for t in plan.tareas if t.tarea.pieza == "aceite" and t.tarea.intervalo_km), None)
    if not t:
        return None
    if t.estado == "desconocido":
        dato = "Sin registro"
    elif t.km_restantes is not None and t.km_restantes > 0:
        dato = f"Faltan {_miles(t.km_restantes)} km"
    elif t.km_restantes is not None:
        dato = f"Pasado por {_miles(-t.km_restantes)} km"
    else:
        dato = t.etiqueta
    if t.ultimo_km is not None:
        detalle = f"Último cambio a los {_miles(t.ultimo_km)} km"
    elif t.estado == "desconocido":
        detalle = "Regístralo en el plan"
    else:
        detalle = "Contamos desde que la moto era nueva"
    detalle += f" · cada {_miles(t.tarea.intervalo_km)} km"
    uso = min(1.0, t.progreso or 0) if t.estado != "desconocido" else 0
    return {"estado": t.estado, "dato": dato, "detalle": detalle, "pct": round(uso * 100), "giro": round(-90 + uso * 180)}


LIQUIDOS = [("aceite-caja", "Aceite de la caja"), ("refrigerante", "Refrigerante"), ("liquido-frenos", "Líquido de frenos")]


def _plazo(dias):
    """'40 días', '5 meses', '1 año y 2 meses'…"""
    if dias < 60:
        return f"{dias} día{'s' if dias != 1 else ''}"
    meses = round(dias / 30)
    if meses < 12:
        return f"{meses} meses"
    anios, resto = divmod(meses, 12)
    return f"{anios} año{'s' if anios != 1 else ''}" + (f" y {resto} mes{'es' if resto != 1 else ''}" if resto else "")


def _liquidos(plan):
    """Avisos de refrigerante (solo motos con radiador) y líquido de frenos (solo con freno de disco).

    El plan ya trae solo las tareas que aplican a la moto. Como cada cambio vence por km o por tiempo, el aviso
    muestra lo que llegue primero (los km se pasan a días con el ritmo de uso de la moto)."""
    avisos = []
    for clave, nombre in LIQUIDOS:
        t = next((t for t in plan.tareas if t.tarea.clave == clave), None)
        if not t:
            continue
        km, dias = t.km_restantes, t.dias_restantes
        if t.estado == "desconocido":
            dato = "Sin registro"
        else:
            # ¿Qué llega primero? Con el ritmo de uso, los km restantes equivalen a cierta cantidad de días.
            dias_por_km = round(km / plan.km_por_dia) if km is not None and plan.km_por_dia else None
            por_tiempo = dias is not None and (km is None or dias_por_km is None or dias < dias_por_km)
            if por_tiempo:
                dato = f"Faltan {_plazo(dias)}" if dias > 0 else ("Toca hoy" if dias == 0 else f"Vencido hace {_plazo(-dias)}")
            elif km is not None:
                dato = f"Faltan {_miles(km)} km" if km > 0 else ("Toca ya" if km == 0 else f"Pasado por {_miles(-km)} km")
            else:
                dato = t.etiqueta
        cada = []
        if t.tarea.intervalo_km:
            cada.append(f"{_miles(t.tarea.intervalo_km)} km")
        if t.tarea.intervalo_dias:
            cada.append(_plazo(t.tarea.intervalo_dias).replace("24 meses", "2 años"))
        if t.ultimo_km is not None:
            detalle = f"Último cambio a los {_miles(t.ultimo_km)} km"
        elif t.estado == "desconocido":
            detalle = "Regístralo en el plan"
        else:
            detalle = "Contamos desde que la moto era nueva"
        if cada:
            detalle += " · cada " + " o ".join(cada)
        uso = min(1.0, t.progreso or 0) if t.estado != "desconocido" else 0
        avisos.append({"clave": clave, "nombre": nombre, "estado": t.estado, "dato": dato, "detalle": detalle,
                       "pct": round(uso * 100), "ancla": f"tarea-{clave}"})
    return avisos


def _tablero(moto, plan):
    """Datos para el odómetro y el indicador de aceite de la página de la moto."""
    texto = str(moto.km_actual).zfill(6)
    primero = len(texto) - len(texto.lstrip("0"))
    digitos = [{"valor": c, "relleno": i < primero and i < len(texto) - 1} for i, c in enumerate(texto)]
    return {"digitos_km": digitos, "aceite": _aceite(plan), "liquidos": _liquidos(plan)}


@con_motociclista
def detalle(request, pk):
    moto = Moto.objects.select_related("linea", "linea__marca").filter(pk=pk, motociclista=request.motociclista).first()
    if not moto:
        # Puede ser de otra cuenta o haber sido eliminada; no decimos cuál para no revelar nada.
        messages.info(request, "Esa moto no está en tu garaje. Revisa con qué cuenta entraste.")
        return redirect(reverse("garaje:garaje") + "?lista=1")
    plan = calcular_plan(moto)

    # Talleres sugeridos para lo que toca ya o pronto, con sus cupones disponibles.
    pendientes = [t for t in plan.urgentes + plan.pronto if t.tarea.servicio_id]
    servicios = {t.tarea.servicio_id for t in pendientes}
    talleres = []
    if servicios:
        marca = moto.linea.marca_id if moto.linea_id else None
        todos, por_taller = _talleres_del_plan(plan)
        talleres = [tl for tl in todos if servicios & {s.pk for s in tl.servicios.all()}]
        for t in talleres:
            ids = {s.pk for s in t.servicios.all()}
            t.cupones_sugeridos = por_taller.get(t.pk, [])
            # Qué de lo pendiente resuelve este taller (con su estado), y si trabaja la marca de la moto.
            t.tareas_que_cubre = [p for p in pendientes if p.tarea.servicio_id in ids]
            t.cubre_todo = len({p.tarea.servicio_id for p in t.tareas_que_cubre}) == len(servicios)
            t.tu_marca = bool(marca) and any(m.pk == marca for m in t.marcas.all())
        # Primero los que resuelven más cosas, luego los de tu marca, los destacados y los que tienen cupón.
        talleres.sort(key=lambda t: (-len(t.tareas_que_cubre), not t.tu_marca, not t.destacado, not t.cupones_sugeridos, t.nombre))
        talleres = talleres[:3]

    despiece = Despiece.para(moto)
    return render(request, "garaje/moto.html", {
        "moto": moto,
        "plan": plan,
        "datos_3d": {"specs": moto.specs(), "color": moto.color, "piezas": _acciones_piezas(moto, plan),
                     "linea": moto.nombre_completo, "placa": moto.placa,
                     "color_secundario": moto.color_secundario, "calcas": moto.calcas, "estilo": moto.estilo},
        "personalizacion": {"colores": COLORES + COLORES_EXTRA, "secundarios": COLORES_SECUNDARIOS,
                            "disenos": DISENOS_CALCA,
                            "url": reverse("garaje:personalizar", args=[moto.pk])},
        "lectura_form": LecturaForm(moto=moto),
        "talleres_activos": Taller.objects.filter(activo=True).only("nombre"),
        "talleres": talleres,
        "lecturas": _lecturas_con_diferencia(moto),
        **_tablero(moto, plan),
        "historial": moto.mantenimientos.select_related("tarea", "taller")[:LIMITE_HISTORIAL],
        "agenda": _agenda(moto, plan, despiece),
        "leyenda": [("atencion", "Requiere atención", "Toca ya o le falta muy poco", "--vencido"),
                    ("proximos", "Próximos", "Le toca en las próximas semanas", "--pronto"),
                    ("al_dia", "Al día", "No necesita nada por ahora", "--ok"),
                    ("sin_registro", "Sin registro", "No sabemos cuándo se hizo", "--desconocido")],
        "soat_en_curso": moto.solicitudes_soat.exclude(estado=SolicitudSoat.Estado.CERRADA).first(),
        "pyp": pico_placa.resumen(moto),
        "avisos": avisos_moto(moto),
        # Para el botón "Agendar" de la técnico-mecánica cuando está por vencer.
        "servicio_tecno": Servicio.objects.filter(nombre__icontains="técnico").values_list("pk", flat=True).first(),
        "otras_motos": request.motociclista.motos.exclude(pk=moto.pk),
        "despiece": despiece,
        # Las láminas pesan cientos de KB: el visor las pide aparte (despiece_json) para no frenar la página ni el 3D.
        "piezas_despiece": sorted(set(despiece.laminas.values_list("pieza", flat=True))) if despiece else [],
    })


@con_motociclista
def despiece_json(request, pk):
    """Láminas del despiece de la moto con el estado de cada pieza; el visor las pide después de cargar la ficha."""
    moto = _moto_de(request, pk)
    despiece = Despiece.para(moto)
    if not despiece:
        raise Http404("Esta moto no tiene despiece")
    return JsonResponse(datos_despiece(despiece, calcular_plan(moto)))


def _svg_guardado(request, generar):
    """El dibujo SVG desde la caché en disco (dibujarlo cuesta hasta medio segundo); si no está, se dibuja y se guarda."""
    clave = "svg:" + hashlib.md5(f"{request.get_full_path()}|{_version_codigo_despiece()}".encode()).hexdigest()
    svg = caches["despiece"].get(clave)
    if svg is None:
        svg = generar()
        if svg is not None:
            caches["despiece"].set(clave, svg, 60 * 60 * 24 * 7)
    return svg


@cache_control(max_age=86400, public=True)
def diagrama_svg(request, clave):
    """Diagrama de despiece propio de TallerYa (dibujo original, se puede publicar)."""
    if diagramas._base(clave) not in diagramas.DIAGRAMAS:
        raise Http404("Diagrama no encontrado")
    grupos = diagramas.grupos_desde_texto(request.GET.get("h")) if "h" in request.GET else None
    usadas = diagramas.usadas_desde_texto(clave, request.GET.get("p")) if "p" in request.GET else None
    titulo = (request.GET.get("t") or "")[:90] or None
    svg = _svg_guardado(request, lambda: diagramas.dibujar_lamina(clave, grupos, usadas, titulo)["svg"])
    return HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")


_SIN_DESCRIPCION = re.compile(r"[\s\-–—.]*")
_SOLO_MODELO = re.compile(r"(?i)^x?\s*(desde|hasta)\s+modelo\b")


def _anio_modelo(cantidad):
    """Algunos catálogos ponen el año del modelo en la columna de cantidad (2014, 2015...)."""
    return cantidad if cantidad and cantidad >= 1900 else None


@cache_control(max_age=86400, public=True)
def pieza_svg(request, clave, puesto):
    """Una pieza sola, con el dibujo propio de TallerYa, para la guía de la pieza."""
    if diagramas._base(clave) not in diagramas.DIAGRAMAS:
        raise Http404("Diagrama no encontrado")
    def generar():
        try:
            return diagramas.dibujar_kit(clave, puesto) if "-" in puesto else diagramas.dibujar_pieza(clave, puesto)
        except (KeyError, ValueError):
            return None
    svg = _svg_guardado(request, generar)
    if svg is None:
        raise Http404("Pieza no encontrada")
    return HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")


def _base_sobremedida(descripcion):
    """'Kit Piston 0.50 125CGR' → 'kit piston 125cgr' (sin la medida: estándar o sobremedida, ni el año de modelo)."""
    sin_modelo = re.sub(r"(?i)\s*\((hasta|desde) modelo[^)]*\)", " ", descripcion or "")
    return re.sub(r"\s+", " ", re.sub(r"(?i)\b(std|standard|est[aá]ndar|\d[.,]\d{2})\b", " ", sin_modelo)).strip().lower()


def _unir_variantes(partes):
    """Une las filas que no son una pieza aparte, sino otra referencia de la anterior con el mismo número.

    Son las filas sin descripción ("- -", códigos de otras versiones de la moto) y las que solo dicen
    "x Desde Modelo". Devuelve (piezas, {pk: [{"codigo", "nota"}]}).
    """
    piezas, alternos = [], {}
    for p in partes:
        desc = (p.descripcion or "").strip()
        previa = piezas[-1] if piezas else None
        if previa is not None and previa.ref == p.ref and _base_sobremedida(previa.descripcion) == _base_sobremedida(desc) \
                and _base_sobremedida(desc) != desc.lower():
            # Misma pieza en otra sobremedida ("Kit Piston 0.25" después de "Kit Piston Std"): otra referencia
            medida = re.search(r"\d[.,]\d{2}", desc)
            modelo = re.search(r"(?i)\((hasta|desde) modelo[^)]*\)", desc)
            nota = (modelo.group(0).strip("()") if modelo else
                    f"otra medida ({medida.group(0).replace('.', ',')})" if medida else "medida estándar")
            alternos.setdefault(previa.pk, []).append({"codigo": p.codigo, "nota": nota})
            continue
        if previa is not None and previa.ref == p.ref and (_SIN_DESCRIPCION.fullmatch(desc) or _SOLO_MODELO.match(desc)):
            anio = _anio_modelo(p.cantidad)
            nota = re.sub(r"(?i)^x\s*", "", desc) if _SOLO_MODELO.match(desc) else "otra versión"
            alternos.setdefault(previa.pk, []).append({"codigo": p.codigo, "nota": f"{nota} {anio}" if anio else nota})
            continue
        piezas.append(p)
    return piezas, alternos


# Motos de dos cilindros (el catálogo no lo dice de forma fiable: los pistones vienen como kits y variantes)
# Escape debajo del motor (caja silenciadora bajo el cárter)
_ESCAPE_BAJO = {"Pulsar NS 200", "Pulsar RS 200", "Pulsar NS 160", "Duke 200", "RC 200", "Duke 390", "RC 390", "Duke 250"}
_BICILINDRICAS = {"MT-03", "YZF-R3", "R3", "Ninja 300", "Ninja 400", "Z400", "CB 500F", "CBR 500R", "CB 190R Twin"}
_DOS_ARBOLES = re.compile(r"((EJE (DE )?LEVAS|CAMSHAFT).*(ADMISI|ESCAPE|INTAKE|EXHAUST)|CAMSHAFT( ASSY)? 2\b|CAMSHAFT, (INTAKE|EXHAUST))", re.I)


def _valvulas_por_cilindro(descripciones, cilindros):
    """Cuatro válvulas si el catálogo trae dos (o más) válvulas de admisión por cilindro; si no, dos."""
    sin_tildes = [("".join(ch for ch in unicodedata.normalize("NFD", d) if unicodedata.category(ch) != "Mn"), c) for d, c in descripciones]
    cantidades = [int(c) for d, c in sin_tildes if re.search(r"VALVE, IN|INTAKE VALVE|VALVULA (DE )?ADMISI|VALVULA ADM", d) and c and int(c) < 10]
    return 4 if cantidades and max(cantidades) >= 2 * cilindros else None


def _perfil_motor(despiece):
    """Perfil del motor de la moto para los dibujos (culata, cilindro, distribución): refrigeración y cilindraje de su
    ficha; dos árboles de levas (DOHC) y triple chispa según lo que trae su catálogo."""
    linea = despiece.linea
    filas = list(ParteDespiece.objects.filter(lamina__despiece=despiece).values_list("descripcion", "cantidad"))
    descripciones = [d.upper() for d, _ in filas]
    dohc = any(_DOS_ARBOLES.search(d) for d in descripciones)
    triple = any(d.startswith("BUJ") and "CENTRAL" in d for d in descripciones)   # bujía central + 2 laterales
    inyeccion = any(re.search(r"THROTTLE BODY|BODY ASSY, THROTTLE|INJECTOR|CUERPO (DE )?ACELERACI|INYECTOR|INYECCI", d) for d in descripciones)
    cilindros = 2 if linea.nombre in _BICILINDRICAS else 1
    return diagramas.perfil_motor(linea.refrigeracion == "liquido", cilindros, linea.cilindraje, dohc, 3 if triple else 1,
                                  mono=linea.suspension_trasera == "mono",
                                  valvulas=_valvulas_por_cilindro([(d.upper(), c) for d, c in filas], cilindros),
                                  escape_bajo=linea.nombre in _ESCAPE_BAJO, scooter=linea.transmision == "cvt", inyeccion=inyeccion)


def _posiciones_en_diagrama(lamina, partes, dibujo=None):
    """Ubica cada parte en el dibujo (o en la franja de tornillería) sin que los números se monten.

    Las variantes con el mismo número en el mismo puesto comparten lugar. Devuelve ({pk: (x, y, puesto)}, grupos).
    """
    puesto_de, numero_de, asignaciones = {}, {}, []
    for p in partes:
        puesto = diagramas.puesto_para(lamina.diagrama, p.descripcion)
        clave = (puesto, p.ref)
        puesto_de[p.pk], numero_de[p.pk] = puesto, clave
        if clave not in asignaciones:
            asignaciones.append(clave)
    if lamina.diagrama == "transmision":
        # La caja: el catálogo lista primero el eje del clutch (principal) y, desde el eje de salida, el secundario con sus piñones
        salida = min((p.ref for p in partes if puesto_de[p.pk] == "eje_salida"), default=None)
        if salida is not None:
            asignaciones = []
            for p in partes:
                if p.ref > salida and puesto_de[p.pk] == "engranajes":
                    puesto_de[p.pk] = "engranajes_salida"
                numero_de[p.pk] = (puesto_de[p.pk], p.ref)
                if numero_de[p.pk] not in asignaciones:
                    asignaciones.append(numero_de[p.pk])
    if lamina.diagrama == "bombas_abs":
        # Dos bombas en la misma lámina: desde la bomba trasera ("RR. MASTER CYLINDER"), lo que se repite es de la trasera
        trasera = min((p.ref for p in partes if re.search(r"\b(RR|REAR)\b.*MASTER|TRASER", p.descripcion.upper())), default=None)
        if trasera is not None:
            existentes = diagramas.dibujar_lamina(dibujo or lamina.diagrama, ())["puestos"]
            asignaciones = []
            for p in partes:
                puesto = puesto_de[p.pk]
                if p.ref >= trasera and puesto + "_trasera" in existentes:
                    puesto_de[p.pk] = puesto = puesto + "_trasera"
                numero_de[p.pk] = (puesto, p.ref)
                if numero_de[p.pk] not in asignaciones:
                    asignaciones.append(numero_de[p.pk])
    asignaciones.sort(key=lambda c: (c[1] is None, c[1] or 0))
    con_cantidad = frozenset(numero_de[p.pk] for p in partes if p.cantidad and 1 < p.cantidad < 1900)
    lugares, grupos, usadas = diagramas.ubicar_numeros(dibujo or lamina.diagrama, [(c, c[0]) for c in asignaciones], con_cantidad)
    return {pk: (*lugares[numero_de[pk]], puesto_de[pk]) for pk in puesto_de}, grupos, usadas


def intervalo_texto(tarea):
    partes = []
    if tarea.intervalo_km:
        partes.append(f"cada {tarea.intervalo_km:,} km".replace(",", "."))
    if tarea.intervalo_dias:
        dias = tarea.intervalo_dias
        if dias < 45:
            partes.append(f"cada {dias} días")
        elif dias < 700:
            meses = round(dias / 30)
            partes.append(f"cada {meses} mes{'es' if meses != 1 else ''}")
        else:
            partes.append(f"cada {round(dias / 365)} años")
    return (" o ".join(partes)).capitalize() if partes else ""


def _con_rueda_fonica(lamina, partes):
    """Si la rueda trae el sensor de velocidad pero el catálogo no lista el disco agujereado que lee (viene integrado),
    se agrega para que tenga su número y su guía en el dibujo."""
    if lamina.diagrama not in ("rueda", "rueda_trasera") or not partes:
        return partes
    puestos = {diagramas.puesto_para(lamina.diagrama, p.descripcion) for p in partes}
    if "sensor_cable" not in puestos or "sensor_abs" in puestos:
        return partes
    from types import SimpleNamespace
    disco = SimpleNamespace(pk=f"fonica-{lamina.pk}", ref=max(p.ref for p in partes) + 1, codigo="", descripcion="ROTOR, SENSOR",
                            nombre="Disco del sensor (rueda fónica)", nombre_es="Disco del sensor (rueda fónica)", cantidad=1,
                            tarea_id=None, ayuda="", x=None, y=None, virtual=True)
    return list(partes) + [disco]


def _vistas(lamina, todas):
    """La lámina tal cual, o dos vistas si mezcla la rueda trasera con el kit de arrastre: cada una numera solo sus
    piezas y deja la otra tenue, como contexto. Devuelve [(id, nombre, partes)]."""
    # En las automáticas no hay kit de arrastre: la rueda trasera va entera
    if lamina.diagrama not in diagramas.CON_ARRASTRE or lamina.despiece.linea.transmision == "cvt":
        return [(lamina.pk, lamina.nombre, todas)]
    arrastre = [p for p in todas if diagramas.es_arrastre(lamina.diagrama, p.descripcion)]
    rueda = [p for p in todas if p not in arrastre]
    if not arrastre or not rueda:
        return [(lamina.pk, lamina.nombre, todas)]
    nombre_rueda = "Rueda trasera y freno de tambor" if lamina.diagrama == "rueda_tambor" else "Rueda trasera"
    return [(lamina.pk, nombre_rueda, rueda), (f"{lamina.pk}-arrastre", "Kit de arrastre", arrastre)]


_ARCHIVOS_DESPIECE = ("views.py", "diagramas.py", "isometrico.py", "models.py")


def _version_codigo_despiece():
    """Huella del código que arma el despiece: si alguien cambia un dibujo o un texto, la caché se renueva sola."""
    base = Path(__file__).resolve().parent
    huella = []
    rutas = [base / n for n in _ARCHIVOS_DESPIECE] + sorted(base.glob("despiece_*.py"))
    for ruta in rutas + sorted((base / "despiece_mapas").glob("*.json")):
        try:
            huella.append(f"{ruta.name}:{ruta.stat().st_mtime_ns}")
        except OSError:
            pass
    return hashlib.md5("|".join(huella).encode()).hexdigest()[:12]


def datos_despiece(despiece, plan):
    """Láminas con sus piezas marcadas y el estado de mantenimiento de cada una, para el visor.

    Lo pesado (dibujos, nombres, guías: igual para todas las motos de esa línea) se guarda en caché;
    aquí solo se pinta encima el estado de mantenimiento de esta moto."""
    # Lo que cambie en los datos (también cargas masivas del importador, que no avisan) cambia la clave
    huella = ParteDespiece.objects.filter(lamina__despiece=despiece).aggregate(n=Count("pk"), u=Max("pk"))
    clave = (f"despiece:{despiece.pk}:{_version_codigo_despiece()}:{caches['despiece'].get('generacion', 0)}:"
             f"{huella['n']}-{huella['u']}")
    base = caches["despiece"].get(clave)
    if base is None:
        base = _laminas_base(despiece)
        caches["despiece"].set(clave, base, 60 * 60 * 24 * 7)
    por_tarea = {t.tarea.pk: t for t in plan.tareas}
    piezas = plan.piezas()
    laminas = base["laminas"]
    for lamina in laminas:
        peor = None
        for parte in lamina["partes"]:
            estado_tarea = por_tarea.get(parte.pop("_tarea", None))
            if not estado_tarea:
                continue
            parte["estado"] = estado_tarea.estado
            parte["tarea"] = {
                "id": estado_tarea.tarea.pk,
                "nombre": estado_tarea.tarea.nombre, "etiqueta": estado_tarea.etiqueta,
                "detalle": estado_tarea.detalle,
                "servicio": estado_tarea.tarea.servicio_id,
                "porcentaje": estado_tarea.porcentaje if estado_tarea.progreso is not None else None,
                "intervalo": intervalo_texto(estado_tarea.tarea),
                "ancla": f"tarea-{estado_tarea.tarea.clave}",
                "hazlo_tu": estado_tarea.tarea.hazlo_tu,
            }
            if peor is None or GRAVEDAD[estado_tarea.estado] > GRAVEDAD[peor]:
                peor = estado_tarea.estado
        lamina["estado"] = peor or piezas.get(lamina["pieza"], {}).get("estado")
    laminas.sort(key=lambda l: -GRAVEDAD.get(l["estado"] or "ok", 0))
    moto = plan.moto
    registro = {
        "url": reverse("garaje:registrar_mantenimiento", args=[moto.pk]),
        "km": moto.km_actual, "hoy": timezone.localdate().isoformat(),
        "talleres": [[t.pk, t.nombre] for t in Taller.objects.filter(activo=True).only("nombre")],
    }
    return {"version": despiece.version, "anio": despiece.anio, "moto": moto.nombre_completo, "laminas": laminas,
            "sistemas": base["sistemas"], "orden_subgrupos": ORDEN_SUBGRUPOS, "registro": registro}


def _laminas_base(despiece):
    """Láminas del despiece sin nada de una moto en particular (el estado se agrega en datos_despiece)."""
    laminas = []
    perfil = _perfil_motor(despiece)
    for lamina in despiece.laminas.prefetch_related("partes__tarea__servicio"):
        todas_lamina, alternos = _unir_variantes(list(lamina.partes.all()))
        todas_lamina = _con_rueda_fonica(lamina, todas_lamina)
        for vista_id, vista_nombre, todas in _vistas(lamina, todas_lamina):
            # Se muestra el dibujo propio de TallerYa; el plano del catálogo (solo existe en local, no se publica)
            # va como pestaña aparte, o solo si la lámina aún no tiene dibujo propio.
            con_dibujo = lamina.diagrama in diagramas.DIAGRAMAS
            hay_original = bool(lamina.imagen) and lamina.imagen.storage.exists(lamina.imagen.name)
            if not con_dibujo and not hay_original:
                continue
            clave = diagramas.clave_dibujo(lamina.diagrama, perfil)          # el dibujo según el motor de esta moto
            if lamina.diagrama == "escape" and not any(diagramas.puesto_para("escape", q.descripcion) == "tubo" for q in todas):
                clave += "u1"                                                  # tubo y silenciador de una pieza: sin unión
            posiciones, grupos, usadas = _posiciones_en_diagrama(lamina, todas, clave) if con_dibujo else ({}, (), None)
            # Piezas que solo tienen número en la franja (tornillería): dónde van en el dibujo, si el catálogo lo dice
            # ("Tornillo Caliper" va al caliper). Es el punto de la pieza dibujada a la que pertenecen.
            dibujo_lamina = diagramas.dibujar_lamina(clave, grupos, usadas) if con_dibujo else {}
            anclas, herrajes = dibujo_lamina.get("anclas", {}), dibujo_lamina.get("herrajes", {})

            cuenta_puestos = {}
            for q in todas:
                if q.pk in posiciones and not posiciones[q.pk][2].startswith("h_"):
                    cuenta_puestos[posiciones[q.pk][2]] = cuenta_puestos.get(posiciones[q.pk][2], 0) + 1
            principal = max(cuenta_puestos, key=cuenta_puestos.get) if cuenta_puestos else None

            def guia_de(p):
                """Guía de la pieza: la propia si existe; si no, la de su papel mecánico en el sistema (su puesto)."""
                guia = ficha_completa(p.descripcion, lamina.pieza)
                guia["contexto"] = ""                 # "En tu moto hace parte de..." no aporta: se quita
                if not tiene_guia_propia(p.descripcion):
                    if con_dibujo and p.pk in posiciones:
                        kit = diagramas.puestos_kit(lamina.diagrama, p.descripcion)
                        mecanica = guia_mecanica(lamina.diagrama, posiciones[p.pk][2], kit, p.descripcion)
                    else:
                        mecanica = guia_mecanica(lamina.diagrama, diagramas.herraje_para(p.descripcion), None, p.descripcion)
                    if mecanica:
                        guia.update(mecanica)
                if getattr(p, "virtual", False):
                    guia["contexto"] = ("En esta moto no se vende aparte: viene con la manzana o con el disco de freno. "
                                        "Igual vale la pena revisarlo, porque de él depende la lectura de velocidad.")
                return guia

            def dibujo_guia(p):
                """Dibujo de la pieza sola para la guía; si no tiene uno propio ("Otras piezas"), el del conjunto donde va."""
                if not (con_dibujo and p.pk in posiciones):
                    return None
                kit = diagramas.puestos_kit(lamina.diagrama, p.descripcion)
                if kit:                                  # un kit: sus piezas juntas, en su lugar del conjunto
                    texto = diagramas.clave_kit(lamina.diagrama, kit)
                    return (reverse("garaje:pieza_svg", args=[clave, texto])
                            + f"?v={diagramas.version_pieza(clave, texto)}")
                for puesto in (posiciones[p.pk][2], principal):
                    if puesto and diagramas.dibujar_pieza(clave, puesto):
                        return (reverse("garaje:pieza_svg", args=[clave, puesto])
                                + f"?v={diagramas.version_pieza(clave, puesto)}")
                return None

            def destino(p):
                """Dónde va en el dibujo una pieza de la franja: su pieza, si el catálogo lo dice ("Tornillo Disco"),
                o la tornillería de su mismo tipo que está dibujada (tornillos, tuercas, arandelas). Lista de puntos."""
                if not (con_dibujo and p.pk in posiciones):
                    return None
                kit = diagramas.puestos_kit(lamina.diagrama, p.descripcion)
                if kit and len(kit) > 1:                 # un kit: dónde va cada pieza que trae
                    return [anclas[q] for q in kit if q in anclas] or None
                # Subconjunto (el kit de la maza): se marca dónde van sus piezas en la moto
                if posiciones[p.pk][2] in diagramas.DESTINO_SUBCONJUNTO:
                    return [anclas[q] for q in diagramas.DESTINO_SUBCONJUNTO[posiciones[p.pk][2]] if q in anclas] or None
                if not posiciones[p.pk][2].startswith("h_"):
                    return None
                propio = anclas.get(diagramas.puesto_en_dibujo(lamina.diagrama, p.descripcion))
                if propio:
                    return [propio]
                tipo = posiciones[p.pk][2]
                if herrajes.get(tipo):
                    return herrajes[tipo][:3]
                # Inferencia mecánica por sistema (la platina de las válvulas va en los ejes de los balancines)
                inferido = diagramas.INFERENCIA.get(lamina.diagrama, {}).get(tipo)
                if inferido in anclas:
                    return [anclas[inferido]]
                # Sin tornillería de ese tipo dibujada: la pieza que sujeta o sella (el seguro, en los rodamientos...)
                por_tipo = next(([anclas[q]] for q in diagramas.DESTINO_POR_TIPO.get(tipo, []) if q in anclas), None)
                return por_tipo
            partes = []
            for p in todas:
                x, y = posiciones.get(p.pk, (None, None, None))[:2] if con_dibujo else (p.x, p.y)
                # Nombre corto y claro; las medidas, dientes, referencias y modelos van a la guía ("Detalles técnicos")
                propio = nombre_por_sistema(lamina.diagrama, p.descripcion)
                nombre_corto, _ = separar_nombre(propio or p.nombre or p.descripcion)
                nombre_corto = quitar_modelo(nombre_corto, despiece.linea.nombre, p.descripcion, lamina.pieza, lamina.nombre)
                # Piñones de la caja: en qué eje van, según su lugar en el catálogo
                if con_dibujo and p.pk in posiciones and nombre_corto.startswith("Piñón") and " del eje " not in nombre_corto:
                    eje = {"engranajes": " del eje principal", "engranajes_salida": " del eje secundario"}.get(posiciones[p.pk][2], "")
                    nombre_corto += eje
                datos = datos_tecnicos(p.nombre, p.descripcion, p.codigo)
                tecnico = texto_tecnico(datos)
                nombre_corto = nombre_corto or f"Pieza {p.ref}"
                parte = {
                    "id": p.pk, "ref": p.ref, "codigo": p.codigo, "nombre": nombre_corto, "tecnico": tecnico, "datos": datos, "descripcion": p.descripcion,
                    "cantidad": 1 if _anio_modelo(p.cantidad) else p.cantidad, "alternos": alternos.get(p.pk, []), "x": x, "y": y, "estado": None, "tarea": None, "ayuda": p.ayuda,
                    "guia": guia_de(p),
                    "destino": destino(p),
                    # Punto de la pieza en el dibujo: el visor une el número con él por una línea fina
                    "ancla": (anclas.get(posiciones[p.pk][2]) if con_dibujo and p.pk in posiciones else None),
                    "dibujo": dibujo_guia(p),
                    "xo": p.x if hay_original else None, "yo": p.y if hay_original else None,
                    "_tarea": p.tarea_id,
                }
                partes.append(parte)
            if not partes:
                continue
            # Piezas que el catálogo llama igual: se distinguen por lo que son (revisado con el plano) o por la pieza con
            # la que van ("Abrazadera · para conducto filtro aire"); el código queda en la ficha para pedirla
            distintos, va_con = nombres_distintos(despiece.linea.nombre, lamina.figura, partes)
            for i, nombre in distintos.items():
                partes[i]["nombre"] = nombre
            for i, pieza in va_con.items():
                partes[i]["va_con"] = pieza
            # Rótulo del dibujo: el sistema y la moto (como en el pie de un plano técnico)
            rotulo = f"{vista_nombre} · {despiece.linea}"[:90]
            pieza_vista = ("cadena" if str(vista_id).endswith("-arrastre")
                           else "llanta_tras" if lamina.diagrama in diagramas.CON_ARRASTRE else lamina.pieza)
            sistema, subgrupo = sistema_de(lamina.diagrama, pieza_vista, vista_nombre, vista_id)
            laminas.append({
                "id": vista_id, "figura": lamina.figura, "nombre": vista_nombre, "pieza": pieza_vista, "diagrama": lamina.diagrama, "moto": str(despiece.linea),
                "sistema": sistema, "subgrupo": subgrupo,
                "imagen": (f'{reverse("garaje:diagrama", args=[clave])}?h={diagramas.grupos_a_texto(grupos)}'
                           f'&v={diagramas.version(clave, grupos, usadas, rotulo)}&p={diagramas.usadas_a_texto(usadas)}'
                           f'&t={quote(rotulo)}'
                           if con_dibujo else lamina.imagen.url),
                "ancho": diagramas.LADO if con_dibujo else lamina.ancho,
                "alto": diagramas.LADO if con_dibujo else lamina.alto,
                "dibujo_propio": con_dibujo,
                "original": lamina.imagen.url if (con_dibujo and hay_original) else None,
                "ancho_original": lamina.ancho, "alto_original": lamina.alto,
                "estado": None, "partes": partes,
            })
    # Todos los sistemas de la moto, aunque alguno no tenga láminas (se muestra con aviso); lo que no encaja va al final
    sistemas = sistemas_de(despiece.linea)
    sistemas += [s for s in dict.fromkeys(l["sistema"] for l in laminas) if s not in sistemas]
    return {"laminas": laminas, "sistemas": sistemas}


@con_motociclista
@require_POST
def avisos_pico_placa(request, pk):
    """Activa o desactiva los avisos de pico y placa (en TallerYa y por WhatsApp)."""
    moto = _moto_de(request, pk)
    moto.aviso_pico_placa = bool(request.POST.get("aviso"))
    moto.pico_placa_whatsapp = bool(request.POST.get("whatsapp"))
    moto.save(update_fields=["aviso_pico_placa", "pico_placa_whatsapp"])
    if moto.pico_placa_whatsapp:
        messages.success(request, "Listo: te escribiremos por WhatsApp la tarde antes de tu pico y placa.")
    return redirect(f"{moto.get_absolute_url()}#pico-placa")


@con_motociclista
@require_POST
def personalizar(request, pk):
    """Guarda color, color de detalles, calcas y estilo (acabado, rines, accesorios) del modelo 3D (JSON desde el panel de personalización)."""
    moto = _moto_de(request, pk)
    try:
        datos = json.loads(request.body)
        color = str(datos.get("color", moto.color))
        secundario = str(datos.get("color_secundario", moto.color_secundario))
        HEX(color)
        HEX(secundario)
        calcas = Moto.limpiar_calcas(datos.get("calcas", []))
        estilo = Moto.limpiar_estilo(datos.get("estilo", moto.estilo))
    except (ValueError, ValidationError, TypeError, AttributeError) as e:
        mensaje = e.messages[0] if isinstance(e, ValidationError) else (str(e) or "Datos inválidos.")
        return JsonResponse({"ok": False, "error": mensaje}, status=400)
    moto.color, moto.color_secundario, moto.calcas, moto.estilo = color, secundario, calcas, estilo
    moto.save(update_fields=["color", "color_secundario", "calcas", "estilo"])
    return JsonResponse({"ok": True})


@con_motociclista
@require_POST
def registrar_km(request, pk):
    moto = _moto_de(request, pk)
    form = LecturaForm(request.POST, moto=moto)
    sin_recargar = request.headers.get("X-Requested-With") == "fetch"
    if not form.is_valid():
        error = " ".join(form.errors.get("km", ["Revisa el número."]))
        if sin_recargar:
            return JsonResponse({"ok": False, "error": error}, status=400)
        messages.error(request, error)
        return redirect(moto)

    antes = {t.tarea.pk: t.estado for t in calcular_plan(moto).tareas}
    with transaction.atomic():
        moto.km_actual = form.cleaned_data["km"]
        moto.save(update_fields=["km_actual"])
        LecturaKm.objects.create(moto=moto, km=moto.km_actual)
    plan = calcular_plan(moto)
    urgentes = len(plan.urgentes)
    mensaje = f"Kilometraje actualizado: {_miles(moto.km_actual)} km." + (
        f" Tienes {urgentes} pendiente{'s' if urgentes != 1 else ''} por hacer." if urgentes else "")
    if not sin_recargar:
        messages.success(request, mensaje)
        return redirect(moto)
    return JsonResponse({
        "ok": True, "km": moto.km_actual, "mensaje": mensaje,
        "km_por_dia": round(plan.km_por_dia) if plan.km_por_dia else None,
        "ritmo_estimado": plan.ritmo_estimado,
        "aceite": _aceite(plan),
        "liquidos": _liquidos(plan),
        "conteos": _conteos_agenda(moto, plan),
        # Si algún sistema cambió de estado, el modelo 3D y el plan de abajo quedan desactualizados.
        "cambiaron": sorted(t.tarea.nombre for t in plan.tareas if antes.get(t.tarea.pk) != t.estado),
    })


@con_motociclista
@require_POST
def registrar_mantenimiento(request, pk):
    moto = _moto_de(request, pk)
    form = MantenimientoForm(request.POST, moto=moto)
    sin_recargar = request.headers.get("X-Requested-With") == "fetch"
    if form.is_valid():
        registro = form.save(commit=False)
        registro.moto = moto
        registro.save()
        AjusteTarea.objects.filter(moto=moto, tarea=registro.tarea).delete()
        mensaje = f"Registrado: {registro.tarea.nombre} a los {_miles(registro.km)} km."
        if sin_recargar:
            # Nuevo estado de esa tarea, para actualizar la ficha y los números del despiece sin recargar.
            t = next((t for t in calcular_plan(moto).tareas if t.tarea.pk == registro.tarea_id), None)
            return JsonResponse({"ok": True, "mensaje": mensaje, "tarea": t and {
                "id": t.tarea.pk, "estado": t.estado, "etiqueta": t.etiqueta, "detalle": t.detalle,
                "porcentaje": t.porcentaje if t.progreso is not None else None,
            }})
        messages.success(request, mensaje)
    else:
        errores = [e for lista in form.errors.values() for e in lista]
        error = " ".join(errores) or "Revisa los datos del mantenimiento."
        if sin_recargar:
            return JsonResponse({"ok": False, "error": error}, status=400)
        messages.error(request, error)
    return redirect(f"{moto.get_absolute_url()}#plan")



# ---------------- Poner al día el plan (al agregar una moto) ----------------
PIEZAS_PRINCIPALES = ["aceite", "filtro_aire", "bujia", "cadena", "correa", "freno_del", "freno_tras", "llanta_del", "llanta_tras",
                      "refrigeracion", "bateria"]
KM_POR_DIA_SUPUESTO = 25  # para estimar la fecha de un mantenimiento del que solo se sabe el kilometraje
MESES_TENTATIVOS = {"1": "Hace 1 mes", "3": "Hace 3 meses", "6": "Hace 6 meses", "12": "Hace más de un año"}


def _tareas_principales(moto):
    specs = moto.specs()
    tareas = [t for t in TareaMantenimiento.objects.filter(activo=True, pieza__in=PIEZAS_PRINCIPALES) if t.aplica_a(specs)]
    return sorted(tareas, key=lambda t: (PIEZAS_PRINCIPALES.index(t.pieza), t.orden))


def _leer_al_dia(datos, tareas, km_actual, previos=None):
    """Lee las respuestas de "último mantenimiento". Devuelve (mantenimientos sin moto, errores por tarea).
    `previos` = {tarea_id: km del último registro}: si la respuesta es ese mismo kilometraje, no se crea nada."""
    previos = previos or {}
    hoy = timezone.localdate()
    nuevos, errores = [], {}
    for t in tareas:
        eleccion = datos.get(f"estado_{t.pk}", "")
        if eleccion == "nose":
            # Fecha tentativa: estimamos fecha y kilometraje con un uso típico de 25 km al día.
            meses = datos.get(f"hace_{t.pk}", "")
            if meses in MESES_TENTATIVOS:
                dias = int(meses) * 30
                nuevos.append(Mantenimiento(tarea=t, km=max(0, km_actual - dias * KM_POR_DIA_SUPUESTO),
                                            fecha=hoy - timedelta(days=dias),
                                            notas="Registrado al agregar la moto (fecha y km estimados)"))
        elif eleccion == "poco":
            nuevos.append(Mantenimiento(tarea=t, km=km_actual, fecha=hoy, notas="Registrado al agregar la moto"))
        elif eleccion == "km":
            texto = datos.get(f"km_{t.pk}", "").strip()
            if not texto.isdigit() or int(texto) > km_actual:
                errores[t.pk] = f"Escribe un kilometraje entre 0 y {_miles(km_actual)} km."
                continue
            km = int(texto)
            if previos.get(t.pk) == km:
                continue  # sin cambios: se conserva el registro que ya tenía
            dias = min(730, round((km_actual - km) / KM_POR_DIA_SUPUESTO))
            nuevos.append(Mantenimiento(tarea=t, km=km, fecha=hoy - timedelta(days=dias),
                                        notas="Registrado al agregar la moto (fecha estimada)"))
    return nuevos, errores


def _filas_al_dia(tareas, datos=None, errores=None, registradas=None):
    datos, errores = datos or {}, errores or {}
    return [{"tarea": t, "intervalo": intervalo_texto(t), "registrada": (registradas or {}).get(t.pk),  # km del último registro, o None
             "eleccion": datos.get(f"estado_{t.pk}", ""), "km": datos.get(f"km_{t.pk}", ""),
             "hace": datos.get(f"hace_{t.pk}", ""), "error": errores.get(t.pk)} for t in tareas]


def _mensaje_al_dia(n):
    return (f"Registramos {n} mantenimiento{'s' if n != 1 else ''}. Tu plan ya está al día." if n
            else "Cuando sepas cuándo se hizo algo, regístralo en el plan.")


@con_motociclista
def tareas_alta(request):
    """Filas del paso 2 al agregar una moto (todavía sin guardar): dependen de la línea o del tipo y del kilometraje."""
    moto = Moto(linea=LineaMoto.objects.filter(pk=request.GET.get("linea") or 0, activo=True).first(),
                tipo_otra=request.GET.get("tipo", ""))
    if not moto.linea and moto.tipo_otra not in dict(Moto._meta.get_field("tipo_otra").choices):
        moto.tipo_otra = ""
    km = request.GET.get("km", "")
    km_actual = int(km) if km.isdigit() else 0
    return render(request, "garaje/_al_dia_filas.html", {
        "filas": _filas_al_dia(_tareas_principales(moto)), "km_actual": km_actual, "tentativos": MESES_TENTATIVOS.items()})


@con_motociclista
def poner_al_dia(request, pk):
    """Para motos ya creadas. ?solo=pendientes muestra solo los sistemas sin registro;
    sin eso, muestra todos con el kilometraje de su último registro y solo guarda lo que cambie."""
    moto = _moto_de(request, pk)
    pendientes = request.GET.get("solo") == "pendientes"
    plan = calcular_plan(moto)
    if pendientes:
        tareas = sorted((t.tarea for t in plan.sin_registro), key=lambda t: t.orden)
    else:
        tareas = sorted((t.tarea for t in plan.tareas), key=lambda t: t.orden)
    ultimos = {}
    for m in moto.mantenimientos.order_by("fecha", "km"):
        ultimos[m.tarea_id] = m.km  # se queda con el más reciente
    previos = {t.pk: ultimos[t.pk] for t in tareas if t.pk in ultimos}
    errores = {}
    if request.method == "POST":
        nuevos, errores = _leer_al_dia(request.POST, tareas, moto.km_actual, previos)
        if not errores:
            for m in nuevos:
                m.moto = moto
            Mantenimiento.objects.bulk_create(nuevos)
            AjusteTarea.objects.filter(moto=moto, tarea__in=[m.tarea for m in nuevos]).delete()
            messages.success(request, ("¡Listo! " if nuevos else "Listo. ") + _mensaje_al_dia(len(nuevos)))
            return redirect(reverse("garaje:moto", args=[moto.pk]) + "#plan")
        datos = request.POST
    else:
        # El formulario arranca con lo que ya se sabía de cada sistema.
        datos = {}
        for tid, km in previos.items():
            datos[f"estado_{tid}"], datos[f"km_{tid}"] = "km", str(km)
    return render(request, "garaje/poner_al_dia.html", {
        "moto": moto, "filas": _filas_al_dia(tareas, datos, errores, previos), "pendientes": pendientes,
        "nueva": False, "tentativos": MESES_TENTATIVOS.items()})



@con_motociclista
@require_POST
def cotizar_soat(request, pk):
    """Guarda el pedido de cotización de SOAT y avisa al equipo de TallerYa."""
    moto = _moto_de(request, pk)
    destino = reverse("garaje:moto", args=[moto.pk])
    if moto.solicitudes_soat.exclude(estado=SolicitudSoat.Estado.CERRADA).exists():
        messages.info(request, "Ya tienes una cotización de SOAT en curso para esta moto. Te contactaremos pronto.")
        return redirect(destino)
    placa = "".join(c for c in request.POST.get("placa", "").upper() if c.isalnum())[:8]
    celular = "".join(c for c in request.POST.get("celular", "") if c.isdigit())[:15]
    if len(celular) < 10:
        messages.error(request, "Escribe un celular válido para que podamos contactarte.")
        return redirect(destino)
    if placa and not moto.placa:
        moto.placa = placa
        moto.save(update_fields=["placa"])
    solicitud = SolicitudSoat.objects.create(moto=moto, placa=placa, celular=celular,
                                             comentario=request.POST.get("comentario", "").strip()[:300])
    from django.contrib.auth import get_user_model
    from notificaciones.models import Notificacion
    from notificaciones.servicios import notificar
    for admin_ in get_user_model().objects.filter(is_staff=True, is_active=True):
        notificar(admin_, f"soat:{solicitud.pk}", "Nueva cotización de SOAT", f"{moto} · {placa or 'sin placa'}",
                  reverse("admin:garaje_solicitudsoat_change", args=[solicitud.pk]), Notificacion.Tipo.GENERAL)
    messages.success(request, "¡Listo! Recibimos tu solicitud de SOAT. Te contactaremos por WhatsApp con opciones.")
    return redirect(destino)



@xframe_options_sameorigin
@con_motociclista
def vista_3d(request, pk):
    """Solo el modelo 3D de la moto, girando, para mostrarlo dentro de la portada del inicio."""
    moto = _moto_de(request, pk)
    return render(request, "garaje/vista_3d.html", {"datos_3d": {
        "specs": moto.specs(), "color": moto.color, "piezas": {}, "linea": moto.nombre_completo, "placa": moto.placa,
        "color_secundario": moto.color_secundario, "calcas": moto.calcas, "estilo": moto.estilo}})
