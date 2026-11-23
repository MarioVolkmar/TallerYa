from urllib.parse import quote
from consola.ajustes import ajuste
from datetime import date, timedelta
import hashlib
import mimetypes
import re
import unicodedata
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import caches
from django.db import transaction
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from cupones.models import Cupon
from talleres.models import Servicio, Taller

from django.core.exceptions import ValidationError

from metricas.nucleo import registrar_evento

from . import hoja_vida, intervalos
from .gastos import resumen as resumen_gastos
from .forms import LecturaForm, MantenimientoForm, MotoForm, validar_documento
import json

from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.clickjacking import xframe_options_sameorigin

from . import diagramas, fallas, pico_placa
from .despiece_variantes import (quitar_modelo, datos_tecnicos, nombre_por_sistema, nombres_de_empaques, nombres_de_sellos,
                                 nombres_distintos,
                                 separar_nombre, texto_tecnico)
from .despiece_fichas import CATEGORIAS as _CATEGORIAS_FICHA, ficha_completa, tiene_guia_propia
_GUIA_GENERICA = _CATEGORIAS_FICHA["general"]["que_hace"]    # "Es una pieza del conjunto...": sin explicación propia
from .despiece_guia_mecanica import guia_mecanica
from .despiece_sistemas import ORDEN_SUBGRUPOS, sistema_de, sistemas_de
from .colores_fabrica import paleta_personalizar
from .models import (COLORES_SECUNDARIOS, DISENOS_CALCA, DOCUMENTOS, HEX, Despiece, LecturaKm,
                     AjusteTarea, LineaMoto, Mantenimiento, Moto, ParteDespiece, TareaMantenimiento)
from domiciliarios.intensivo import precargar_trabajo

from domicilio.models import TipoServicio
from .kilometraje import km_valido, pregunta_km, registrar_lectura
from .plan import GRAVEDAD, MARCA_SIN_IDEA, calcular_plan, es_sin_idea, fecha_de_nueva, fecha_en_km, km_en_fecha, km_es_estimado
from .intervalos import intervalo_para

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
    motos = list(request.motociclista.motos.select_related("linea", "linea__marca")
                 .prefetch_related("mantenimientos", "ajustes", "lecturas"))
    if len(motos) == 1 and not request.GET.get("lista"):
        return redirect(motos[0])
    tareas = list(TareaMantenimiento.objects.filter(activo=True).select_related("servicio"))  # una vez para todas
    Despiece.precargar(motos)
    precargar_trabajo(motos)  # TallerYa Ruta: qué moto es de trabajo, en una consulta
    planes = [(m, calcular_plan(m, tareas=tareas)) for m in motos]
    return render(request, "garaje/garaje.html", {"planes": planes, "puede_agregar": len(motos) < MAX_MOTOS})


@con_motociclista
def agregar(request):
    if request.motociclista.motos.count() >= MAX_MOTOS:
        messages.info(request, f"Puedes tener hasta {MAX_MOTOS} motos en tu garaje.")
        return redirect("garaje:garaje")
    form = MotoForm(request.POST or None, request.FILES or None)
    guia = bool(request.GET.get("guia"))  # guía de primer uso (garaje/vista_bienvenida.py): mismo formulario, 4 pasos
    filas, mostrar_paso2 = [], False
    if request.method == "POST" and form.is_valid():
        km_actual = form.cleaned_data["km_actual"]
        tareas = _tareas_principales(form.instance)
        form.instance.km_inicial = form.instance.km_actual = km_actual
        if request.POST.get("sin_datos"):  # atajo «No sé, agregar ya»: no registra nada, ignora lo marcado en la lista
            nuevos, errores = [], {}
        else:
            nuevos, errores = _leer_al_dia(request.POST, tareas, form.instance)
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
                for m in nuevos:  # uno a uno: cada mantenimiento también queda en la hoja de vida
                    m.save()
            registrar_evento(request, "moto_creada", guia=guia)
            if guia:  # primer uso: sigue al paso 3 (su plan y su moto en 3D)
                return redirect("garaje:bienvenida_plan", pk=moto.pk)
            messages.success(request, "¡Moto agregada! " + _mensaje_al_dia(len(nuevos)))
            return redirect(moto)
    return render(request, "garaje/form_moto.html", {
        "form": form, "nueva": True, "documentos_form": _documentos_form(form), "guia": guia,
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
@require_POST
def subir_documento(request, pk, clave):
    """Sube la foto o el PDF del SOAT o la técnico-mecánica desde la ficha, sin pasar por "Datos de la moto"."""
    if clave not in DOCUMENTOS:
        raise Http404
    moto = _moto_de(request, pk)
    archivo = request.FILES.get("archivo")
    if not archivo:
        messages.error(request, "Elige una foto o un PDF.")
        return redirect(f"{moto.get_absolute_url()}#documentos")
    try:
        validar_documento(archivo)
    except ValidationError as e:
        messages.error(request, e.messages[0])
        return redirect(f"{moto.get_absolute_url()}#documentos")
    campo = f"{clave}_archivo"
    anterior = getattr(moto, campo)
    if anterior:
        anterior.delete(save=False)   # el reemplazado no se queda en el disco
    setattr(moto, campo, archivo)
    moto.save(update_fields=[campo])
    messages.success(request, f"{DOCUMENTOS[clave]}: archivo guardado.")
    return redirect(f"{moto.get_absolute_url()}#documentos")


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
                        .select_related("barrio", "usuario__perfil").prefetch_related("servicios", "marcas")) if servicios else []
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
    for t in sorted(plan.tareas, key=lambda t: -GRAVEDAD[t.color]):
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


def _grupos_agenda(plan, ajustes=None):
    """Los cuatro grupos de la agenda (los mismos que cuenta la leyenda bajo el 3D), por el nivel de color de cada tarea:
    rojo = Requiere atención, amarillo = Próximos (incluye lo pospuesto), verde = Al día."""
    al_dia = sorted(plan.por_nivel("ok"),
                    key=lambda t: (t.fecha_estimada or date.max, t.km_restantes if t.km_restantes is not None else 10**9))
    return {
        "atencion": plan.urgentes,
        "proximos": plan.pronto,
        "sin_registro": plan.sin_registro,
        "al_dia": al_dia,
    }


def _conteos_agenda(moto, plan):
    grupos = _grupos_agenda(plan, {a.tarea_id: a for a in moto.ajustes.all()})
    return {clave: len(lista) for clave, lista in grupos.items()}


# "Qué necesitas" de la agenda: solo lo que se compra en ese mantenimiento. La pieza que la tarea marca en el despiece
# (la válvula en la calibración, el radiador en el refrigerante) explica el trabajo, pero no siempre se reemplaza.
_SE_COMPRA = {
    "valvulas": r"EMPAQ|GASKET|O-?\s?RING|ORING|ANILLO (EN )?O\b|JUNTA",           # el empaque de la tapa; las válvulas solo se ajustan
    "refrigerante": r"WASHER|ARANDELA|GASKET|EMPAQ|JUNTA",                            # el líquido; si acaso, la arandela del drenaje
    "liquido-frenos": r"WASHER|ARANDELA",                                             # el líquido; si acaso, arandelas de cobre del banjo
    "cadena-lubricar": r"$^",                                                         # solo lubricante: ningún repuesto
    "suspension-del": r"OIL SEAL|SEAL,\s*(OIL|DUST)|DUST SEAL|RET[EÉ]N|RETENEDOR|GUARDAP",  # retenes y guardapolvos (y el aceite)
    "bateria": r"BATTERY|BATER",
    "aceite-caja": r"WASHER|ARANDELA|GASKET|EMPAQ|O-?\s?RING|ORING|ANILLO (EN )?O\b|JUNTA",
}
_NO_SE_COMPRA = {"aceite": r"ROTOR|CENTRIFUG|EMPAQUE (CARCASA|CUBIERTA)|GASKET,? (CRANKCASE|CLUTCH COVER)",
                 "kit-arrastre": r"TOPE|CAUCHO|SLIDER|DESLIZ|BUFFER|STOPPER"}                                                   # el filtro centrífugo se limpia, no se compra


def _se_compra(clave, descripcion):
    texto = descripcion.upper()
    if clave in _SE_COMPRA and not re.search(_SE_COMPRA[clave], texto):
        return False
    if clave in _NO_SE_COMPRA and re.search(_NO_SE_COMPRA[clave], texto):
        return False
    if clave == "bateria" and re.match(r"(CAJA|CASE|BOX|HOLDER|SOPORTE|BANDA|BAND|CORREA|BASE)", texto):
        return False
    return True


def _url_domicilio(tarea, tipos):
    """Mecánicos a domicilio, filtrados por el servicio de la tarea si existe con el mismo nombre."""
    if not ajuste("mecanicos_activo"):
        return ""
    base = reverse("domicilio:listado")
    nombre = tarea.servicio.nombre if tarea.servicio_id else ""
    return f"{base}?servicio={tipos[nombre]}" if nombre in tipos else base


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
        for p in ParteDespiece.objects.filter(lamina__despiece=despiece, tarea__isnull=False).select_related("lamina", "tarea"):
            if not _se_compra(p.tarea.clave, p.descripcion):
                continue      # la pieza explica la tarea en el despiece, pero en ese mantenimiento no se cambia
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

    tipos_domicilio = dict(TipoServicio.objects.values_list("nombre", "pk"))
    for t in plan.tareas:
        t.ajuste = ajustes.get(t.tarea.pk)
        t.repuestos = repuestos.get(t.tarea.pk, [])
        t.por_que = POR_QUE.get(t.tarea.clave) or por_que.get(t.tarea.pk) or t.tarea.descripcion
        mejor = next((tl for tl in talleres if t.tarea.servicio_id in servicios_de[tl.pk]), None)
        t.url_domicilio = _url_domicilio(t.tarea, tipos_domicilio)
        t.taller_sugerido = mejor and {"taller": mejor, "cupon": cupones.get(mejor.pk),
                                       "whatsapp": _whatsapp_para(mejor, t.tarea, moto)}
        # Para el calendario: la fecha estimada, o en una semana si ya toca.
        t.fecha_calendario = t.fecha_estimada if t.fecha_estimada and t.fecha_estimada > hoy else hoy + timedelta(days=7)

    grupos = _grupos_agenda(plan, ajustes)
    atencion = grupos["atencion"]

    # ¿Un solo taller resuelve varias cosas de las pendientes (lo que toca ya y lo próximo)? Se sugiere una sola visita.
    visita = None
    por_hacer = atencion + grupos.get("proximos", [])
    for tl in talleres:
        cubre = [t for t in por_hacer if t.tarea.servicio_id in servicios_de[tl.pk]]
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
    return {"estado": t.color, "dato": dato, "detalle": detalle, "pct": round(uso * 100), "giro": round(-90 + uso * 180)}


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
        avisos.append({"clave": clave, "nombre": nombre, "estado": t.color, "dato": dato, "detalle": detalle,
                       "pct": round(uso * 100), "ancla": f"tarea-{clave}"})
    return avisos


def _tablero(moto, plan):
    """Datos para el odómetro y el indicador de aceite de la página de la moto."""
    texto = str(moto.km_actual).zfill(6)
    primero = len(texto) - len(texto.lstrip("0"))
    digitos = [{"valor": c, "relleno": i < primero and i < len(texto) - 1} for i, c in enumerate(texto)]
    return {"digitos_km": digitos, "aceite": _aceite(plan), "liquidos": _liquidos(plan)}


def resumen_plan(plan):
    """(todo_al_dia, lo_urgente) para el resumen de arriba de la agenda; también lo usa la guía de bienvenida."""
    # Resumen arriba de la agenda, con el mismo diseño en los dos casos: el estado por sistema y una lista con barras.
    # Todo al día → "Lo que viene" (las 3 más cercanas, con cuánto les falta). Con pendientes → "Lo urgente" (lo vencido
    # primero y luego lo próximo, hasta 5, con cuánto se pasó o cuánto falta).
    SISTEMAS = [("Motor", "engine", {"aceite", "motor", "filtro_aire", "bujia", "refrigeracion"}),
                ("Transmisión", "link", {"cadena", "correa"}), ("Frenos", "disc", {"freno_del", "freno_tras"}),
                ("Llantas", "circle", {"llanta_del", "llanta_tras"}),
                ("Suspensión", "spring", {"suspension_del", "suspension_tras"}), ("Eléctrico", "bolt", {"bateria"})]
    sistemas = []
    for nombre, icono, piezas in SISTEMAS:
        del_sistema = [t for t in plan.tareas if t.tarea.pieza in piezas]
        if del_sistema:
            ok = sum(t.estado == "ok" for t in del_sistema)
            niveles = {t.nivel or t.estado for t in del_sistema}
            sin_dato = sum(t.estado == "desconocido" for t in del_sistema)
            nivel = ("vencido" if niveles & {"vencido", "urgente"} else "pronto" if "pronto" in niveles
                     else "desconocido" if not ok else "ok")
            sistemas.append({"nombre": nombre, "icono": icono, "ok": ok, "total": len(del_sistema), "sin_dato": sin_dato,
                             "pct": round(ok * 100 / len(del_sistema)), "nivel": nivel})
    todo_al_dia = lo_urgente = None
    if not plan.urgentes and not plan.pronto and plan.tareas:
        viene = sorted((t for t in plan.tareas if t.progreso is not None), key=lambda t: -t.progreso)[:3]
        for t in viene:
            t.pct_vida = min(100, round(t.progreso * 100))
        todo_al_dia = {"viene": viene, "sistemas": sistemas}
    elif plan.urgentes or plan.pronto:
        pendientes_lista = sorted(plan.urgentes, key=lambda t: -(t.progreso or 0)) +             sorted(plan.pronto, key=lambda t: -(t.progreso or 0))
        from django.contrib.humanize.templatetags.humanize import intcomma
        for t in pendientes_lista:
            t.pct_vida = min(100, round((t.progreso or 0) * 100))
            km, dias = t.km_restantes, t.dias_restantes
            # Un texto corto y creíble: primero los km (es lo que manda en una moto); los días solo si no hay km
            # o si vencen antes. Sin registro no se dan cifras de vencido: solo "revísalo".
            if t.estimado and t.estado == "vencido":
                t.texto_lu = "Toca ya · estimado"
            elif t.estimado:
                t.texto_lu = f"≈ faltan {intcomma(km)} km · estimado" if km and km > 0 else f"≈ faltan {dias} días · estimado"
            elif t.supuesto:
                t.texto_lu = f"≈ faltan {intcomma(km)} km · estimado" if km and km > 0 else "Sin registro · revísalo"
            elif km is not None and km < 0:
                t.texto_lu = f"pasado {intcomma(-km)} km"
            elif dias is not None and dias < 0:
                t.texto_lu = f"vencido hace {-dias} día{'s' if dias != -1 else ''}"
            elif km == 0 or dias == 0:
                t.texto_lu = "Toca ya"
            elif km is not None and (dias is None or dias > 60):
                t.texto_lu = f"faltan {intcomma(km)} km"
            elif dias is not None:
                t.texto_lu = f"faltan {dias} día{'s' if dias != 1 else ''}"
            else:
                t.texto_lu = t.etiqueta
        lo_urgente = {"lista": pendientes_lista[:5], "total": len(pendientes_lista), "sistemas": sistemas}
    return todo_al_dia, lo_urgente


@con_motociclista
def detalle(request, pk):
    # ajustes: los usan el plan y la agenda (una consulta para los dos)
    moto = (Moto.objects.select_related("linea", "linea__marca").prefetch_related("ajustes")
            .filter(pk=pk, motociclista=request.motociclista).first())
    if not moto:
        # Puede ser de otra cuenta o haber sido eliminada; no decimos cuál para no revelar nada.
        messages.info(request, "Esa moto no está en tu garaje. Revisa con qué cuenta entraste.")
        return redirect(reverse("garaje:garaje") + "?lista=1")
    plan = calcular_plan(moto)
    registrar_evento(request, "plan_visto")

    # Talleres sugeridos para lo que toca ya o pronto, con sus cupones disponibles.
    pendientes = [t for t in plan.urgentes + plan.pronto if t.tarea.servicio_id]
    # Con todo al día la sección no desaparece: sugiere talleres para lo que viene más cerca (las 3 de más progreso)
    talleres_lo_que_viene = not pendientes
    if talleres_lo_que_viene:
        pendientes = sorted((t for t in plan.tareas if t.tarea.servicio_id and t.progreso is not None),
                            key=lambda t: -t.progreso)[:3]
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
        # Misma tarjeta de la pestaña Talleres: reseñas, favorito, iniciales y tono del avatar
        from talleres.views import _preparar_tarjetas
        talleres = _preparar_tarjetas(talleres[:3], request.user)

    todo_al_dia, lo_urgente = resumen_plan(plan)

    despiece = Despiece.para(moto)
    return render(request, "garaje/moto.html", {
        "todo_al_dia": todo_al_dia,
        "lo_urgente": lo_urgente,
        "moto": moto,
        "plan": plan,
        "datos_3d": {"specs": moto.specs(), "color": moto.color, "piezas": _acciones_piezas(moto, plan),
                     "linea": moto.nombre_completo, "placa": moto.placa,
                     "color_secundario": moto.color_secundario, "calcas": moto.calcas, "estilo": moto.estilo,
                     "calcas_personalizadas": settings.CALCAS_PERSONALIZADAS},
        "personalizacion": {"colores": paleta_personalizar(moto.nombre_completo), "secundarios": COLORES_SECUNDARIOS,
                            "disenos": DISENOS_CALCA,
                            "url": reverse("garaje:personalizar", args=[moto.pk]),
                            "calcas_personalizadas": settings.CALCAS_PERSONALIZADAS},
        "lectura_form": LecturaForm(moto=moto),
        "pregunta_km": pregunta_km(moto),
        "talleres_activos": Taller.objects.filter(activo=True).only("nombre"),
        "talleres": talleres,
        "talleres_lo_que_viene": talleres_lo_que_viene,
        "lecturas": (lecturas := _lecturas_con_diferencia(moto)),
        # Lo recorrido entre la primera y la última lectura de la lista (resumen al pie de la caja de kilometraje)
        "km_recorridos": {"km": lecturas[0].km - lecturas[-1].km, "desde": lecturas[-1].fecha}
                         if len(lecturas) > 1 and lecturas[0].km > lecturas[-1].km else None,
        **_tablero(moto, plan),
        # Historial: la hoja de vida (cada mantenimiento queda ahí) y los gastos del mes
        "registros_hv": list(moto.hoja_vida.select_related("taller", "mecanico")[:5]),
        "hv_resumen": moto.hoja_vida.aggregate(total=Count("id"), verificados=Count("id", filter=Q(verificado=True))),
        "gastos": resumen_gastos(moto),
        "agenda": _agenda(moto, plan, despiece),
        "leyenda": [("atencion", "Requiere atención", "Toca ya o le falta muy poco", "--vencido"),
                    ("proximos", "Próximos", "Le toca en las próximas semanas", "--pronto"),
                    ("al_dia", "Al día", "No necesita nada por ahora", "--ok"),
                    ("sin_registro", "Sin registro", "No sabemos cuándo se hizo", "--desconocido")],
        "pyp": pico_placa.resumen(moto),
        "otras_motos": request.motociclista.motos.exclude(pk=moto.pk),
        "despiece": despiece,
        # Las láminas pesan cientos de KB: el visor las pide aparte (despiece_json) para no frenar la página ni el 3D.
        "piezas_despiece": (piezas_despiece := sorted(set(despiece.laminas.values_list("pieza", flat=True))) if despiece else []),
        # Piloto «Tips y fallas frecuentes» (None con FALLAS_FRECUENTES_ACTIVO apagado)
        "fallas": fallas.para_moto(moto, plan, piezas_despiece, uso_severo=getattr(plan, "de_trabajo", False) or getattr(plan, "por_uso_trabajo", False)),
    })


@con_motociclista
def despiece_json(request, pk):
    """Láminas del despiece de la moto con el estado de cada pieza; el visor las pide después de cargar la ficha."""
    moto = _moto_de(request, pk)
    despiece = Despiece.para(moto)
    if not despiece:
        raise Http404("Esta moto no tiene despiece")
    datos = datos_despiece(despiece, calcular_plan(moto))
    # Las guías de las piezas son más de la mitad del peso (≈290 de 490 KB en la NMAX) y solo se leen al abrir la
    # guía de una pieza: van aparte (?guias=1) y el visor las pide después de pintar el esquema.
    if request.GET.get("guias"):
        respuesta = JsonResponse({"guias": {str(p["id"]): p["guia"] for l in datos["laminas"] for p in l["partes"] if p.get("guia")}})
    else:
        registrar_evento(request, "despiece_abierto")
        for lamina in datos["laminas"]:
            for parte in lamina["partes"]:
                if parte.get("guia"):
                    parte["guia"] = 1  # marca: la guía existe y llega con ?guias=1
        respuesta = JsonResponse(datos)
    # Caché del navegador con ETag: si nada cambió (estado de las piezas, código), responde 304 sin cuerpo
    respuesta["ETag"] = '"' + hashlib.md5(respuesta.content).hexdigest() + '"'
    respuesta["Cache-Control"] = "private, no-cache"
    # (GZipMiddleware vuelve débil el ETag al comprimir: el navegador lo devuelve como W/"…")
    if respuesta["ETag"] in request.headers.get("If-None-Match", "").replace("W/", ""):
        vacia = HttpResponse(status=304)
        vacia["ETag"], vacia["Cache-Control"] = respuesta["ETag"], respuesta["Cache-Control"]
        return vacia
    return respuesta


def _svg_guardado(request, generar):
    """El dibujo SVG desde la caché en disco (dibujarlo cuesta hasta medio segundo); si no está, se dibuja y se guarda."""
    clave = "svg:" + hashlib.md5(f"{request.get_full_path()}|{_version_codigo_despiece()}".encode()).hexdigest()
    svg = caches["despiece_svg"].get(clave)
    if svg is None:
        svg = generar()
        if svg is not None:
            caches["despiece_svg"].set(clave, svg, 60 * 60 * 24 * 7)
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
    """Texto del intervalo de una tarea (ya con el de su línea si viene del plan): un solo formateador."""
    return intervalos.texto(tarea.intervalo_km, tarea.intervalo_dias)


# Piezas que la moto tiene y que el plan revisa, pero que el catálogo de la marca no vende con su número (la batería,
# las llantas, la bujía, los amortiguadores...). Si ninguna pieza del despiece lleva esa tarea, se agrega en la lámina
# que dibuja la pieza, con la tarea y el aviso "No viene en el catálogo de esta moto": nunca se pone la tarea en un
# accesorio (la correa de la batería, un caucho). (tarea, diagramas, piezas de la lámina o None, descripción, nombre)
PIEZAS_DE_TAREA = [
    ("bateria", ("electrico",), None, "BATTERY", "Batería"),
    ("suspension-tras", ("amortiguadores",), None, "SHOCK ABSORBER, RR", "Amortiguadores traseros"),
    ("suspension-del", ("suspension_delantera",), None, "FORK, FR", "Barras de la suspensión delantera"),
    ("llanta-del", ("rueda",), ("llanta_del",), "TIRE, FR", "Llanta delantera"),
    ("llanta-tras", ("rueda_trasera", "rueda_tambor", "rueda"), ("llanta_tras", "cadena", "freno_tras"), "TIRE, RR", "Llanta trasera"),
    ("bujia", ("culata", "encendido"), None, "PLUG, SPARK", "Bujía"),
    ("bandas-tras", ("rueda_tambor", "freno_tambor"), ("llanta_tras", "freno_tras", "cadena"), "SHOE SET, BRAKE", "Bandas del freno trasero"),
]
FUERA_DE_CATALOGO = ("No aparece en los planos que usamos para este esquema: la dibujamos porque tu moto sí la tiene. "
                     "Se compra por su referencia (el tipo y la medida están en el manual o en la pieza actual).")


def _tareas_sin_pieza(despiece):
    """Tareas del plan que aplican a la línea y que ninguna pieza del despiece lleva: {clave: tarea}."""
    from .models import Moto
    specs = Moto(linea=despiece.linea).specs()
    enlazadas = set(ParteDespiece.objects.filter(lamina__despiece=despiece, tarea__isnull=False).values_list("tarea_id", flat=True))
    return {t.clave: t for t in TareaMantenimiento.objects.filter(activo=True) if t.aplica_a(specs) and t.pk not in enlazadas}


def _con_piezas_de_tarea(lamina, partes, faltan, usadas_ya):
    """Agrega a la lámina las piezas fuera del catálogo cuyas tareas faltan (una sola vez por despiece)."""
    from types import SimpleNamespace
    if not partes:
        return partes
    extra = []
    for clave, diags, piezas, descripcion, nombre in PIEZAS_DE_TAREA:
        tarea = faltan.get(clave)
        if not tarea or clave in usadas_ya or lamina.diagrama not in diags or (piezas and lamina.pieza not in piezas):
            continue
        usadas_ya.add(clave)
        extra.append(SimpleNamespace(pk=f"fuera-{lamina.pk}-{clave}", ref=max(p.ref for p in partes + extra) + 1, codigo="",
                                     descripcion=descripcion, nombre=nombre, nombre_es=nombre, cantidad=1, tarea_id=tarea.pk,
                                     ayuda="", x=None, y=None, virtual=True, contexto=FUERA_DE_CATALOGO))
    return list(partes) + extra


def _con_rueda_fonica(lamina, partes):
    """Si la rueda trae el sensor de velocidad pero el catálogo no lista el disco agujereado que lee (viene integrado),
    se agrega para que tenga su número y su guía en el dibujo."""
    if lamina.diagrama not in ("rueda", "rueda_trasera") or not partes:
        return partes
    puestos = {diagramas.puesto_para(lamina.diagrama, p.descripcion) for p in partes}
    if "sensor_cable" not in puestos or "sensor_abs" in puestos or any("ROTOR" in p.descripcion.upper() for p in partes):
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


# Tipo de filtro de aire por línea, según su manual (la marca solo es el respaldo)
_FILTRO_AIRE_POR_LINEA = {"NMAX 155": "viscoso", "Aerox 155": "viscoso", "FZ 25": "viscoso", "Crypton FI 115": "viscoso",
                          "CB 125F": "viscoso", "Pulsar NS 200": "viscoso", "Pulsar RS 200": "viscoso", "XTZ 125": "espuma",
                          "Boxer CT 100": "seco", "Eco Deluxe 100": "seco", "Apache RTR 160": "espuma",
                          # Su plan pide limpiarlo entre cambios: no es viscoso (el respaldo por marca diría que no se limpia)
                          "XTZ 150": "sin_confirmar",
                          # Confirmados en sus manuales (revisión mecánica, 15-nov-2026)
                          "Hunk 125R": "viscoso", "XR 190L": "viscoso", "FZ 2.0": "viscoso", "DR 150": "viscoso",
                          "Best 125": "seco"}
# Cuidado del filtro de aire según su tipo (Auditor mecánico): el consejo de uno daña a los otros
_CUIDADO_FILTRO_AIRE = {
    "seco": {"como_revisar": ["Míralo a contraluz: si casi no pasa luz o está negro, cámbialo.",
                              "Puedes soplarlo con aire suave desde adentro hacia afuera; nunca lo mojes."],
             "tips": ["Es de papel seco: no se lava ni se aceita", "Revisa que quede bien asentado: si entra aire sin filtrar, desgasta el motor"]},
    "viscoso": {"como_revisar": ["Mira que no esté roto ni lleno de barro; es normal que no deje pasar luz, ni nuevo."],
                "tips": ["Es de papel viscoso (con aceite): no se limpia, no se sopla y no se moja; se cambia cuando lo pide el plan",
                         "Revisa que quede bien asentado: si entra aire sin filtrar, desgasta el motor"]},
    "sin_confirmar": {"como_revisar": ["Mira de qué es tu filtro: papel seco, papel aceitoso o espuma."],
                      "tips": ["Si es de papel seco, puedes soplarlo con aire suave desde adentro. Si el papel se siente aceitoso o "
                               "pegajoso, es viscoso: no se limpia, se cambia. Si es de espuma, se lava, se seca y se aceita.",
                               "Revisa que quede bien asentado: si entra aire sin filtrar, desgasta el motor"]},
    "espuma": {"como_revisar": ["Sácalo y mira si la espuma está sucia, dura o rota."],
               "tips": ["Es de espuma: se lava con agua y jabón o desengrasante, se seca sin retorcerlo y se aceita con aceite para filtro de espuma",
                        "Si la espuma está rota o se desmorona, cámbialo"]},
}


# Respaldo cuando el archivo de intervalos de la línea no trae la especificación: nunca una cifra igual para todas las motos
_CONCEPTO_TAREA = [
    (r"FILTRO (DE |DEL )?AIRE|AIR (CLEANER|FILTER)|ELEMENT,? AIR|ELEMENTO (DEL )?FILTRO", "filtro-aire"),
    (r"^(DRIVE CHAIN|CHAIN|CADENA)\b(?!.*(GUIDE|GUIA|TENSOR|ADJUST|CASE|CAJA|DISTRIBU|CAM))", "cadena-lubricar"),
    (r"BATTERY|BATER", "bateria"),
]
_ESPECIFICACION_GENERICA = {
    "aceite": "Usa el aceite (viscosidad y norma) que indica el manual de tu moto.",
    "aceite-caja": "Usa el aceite de transmisión que indica el manual de tu moto.",
    "bujia": "Usa la referencia de bujía que indica el manual de tu moto.",
    "llanta-del": "Infla a la presión que indica el manual o la etiqueta de tu moto.",
    "llanta-tras": "Infla a la presión que indica el manual o la etiqueta de tu moto.",
    "liquido-frenos": "Usa el líquido que indica la tapa del depósito (no mezcles tipos).",
    "refrigerante": "Usa el refrigerante que indica el manual de tu moto.",
}


_TORNILLERIA = re.compile(r"(?i)^(kit )?(tornillos?|tuercas?|arandelas?|pernos?|seguros?|pines?|empaques?)\b")


def clave_base_despiece(despiece):
    """Clave de caché de lo pesado del despiece. Lo que cambie en los datos (también las cargas masivas del importador,
    que no avisan) o en el código del despiece cambia la clave."""
    huella = ParteDespiece.objects.filter(lamina__despiece=despiece).aggregate(n=Count("pk"), u=Max("pk"))
    return (f"despiece:{despiece.pk}:{_version_codigo_despiece()}:{caches['despiece'].get('generacion', 0)}:"
            f"{huella['n']}-{huella['u']}")


def _clave_parcial(clave, sistemas):
    return f"{clave}:sis:{hashlib.md5('|'.join(sorted(sistemas)).encode()).hexdigest()[:10]}"


def base_en_cache(despiece, sistemas=None):
    """¿Lo pesado del despiece (todo, o esos sistemas) ya está armado en la caché? Sin leerlo."""
    clave, cache = clave_base_despiece(despiece), caches["despiece"]
    return cache.has_key(clave) or bool(sistemas) and cache.has_key(_clave_parcial(clave, sistemas))


def base_despiece(despiece, sistemas=None):
    """Lo pesado del despiece (igual para todas las motos de esa línea), desde la caché o armado y guardado.

    Con `sistemas` (el diagnóstico, que solo muestra un sistema): si el despiece completo ya está en caché se filtra de
    ahí; si no, se arman y guardan solo las láminas de esos sistemas (los dibujos de todo el despiece tardan segundos)."""
    clave = clave_base_despiece(despiece)
    cache = caches["despiece"]
    base = cache.get(clave)
    if base is None and sistemas:
        clave_parcial = _clave_parcial(clave, sistemas)
        base = cache.get(clave_parcial)
        if base is None:
            base = _laminas_base(despiece, set(sistemas))
            cache.set(clave_parcial, base, 60 * 60 * 24 * 7)
        return base
    if base is None:
        base = _laminas_base(despiece)
        cache.set(clave, base, 60 * 60 * 24 * 7)
    if sistemas:
        base = {**base, "laminas": [l for l in base["laminas"] if l["sistema"] in sistemas]}
    return base


def km_guia(t):
    """Bloque "Kilometraje estimado" de la guía de una pieza: km desde el último cambio, cuánto falta, color (el mismo
    nivel de la agenda) y de dónde sale la cuenta. Todo sale del plan; sin cuenta por km, vacío."""
    if getattr(t, "km_desde", None) is None or not t.tarea.intervalo_km:
        return {"km": None}
    return {"km": {"desde": t.km_desde, "restantes": t.km_restantes, "intervalo": t.tarea.intervalo_km,
                   "porcentaje": min(100, round(100 * t.km_desde / t.tarea.intervalo_km)),
                   "nivel": t.nivel or t.estado, "origen": t.origen, "texto_origen": t.texto_origen}}


def datos_despiece(despiece, plan, sistemas=None):
    """Láminas con sus piezas marcadas y el estado de mantenimiento de cada una, para el visor.

    Lo pesado (dibujos, nombres, guías: igual para todas las motos de esa línea) se guarda en caché;
    aquí solo se pinta encima el estado de mantenimiento de esta moto. `sistemas`: solo las láminas de esos sistemas."""
    base = base_despiece(despiece, sistemas)
    por_tarea = {t.tarea.pk: t for t in plan.tareas}
    piezas = plan.piezas()
    laminas = base["laminas"]
    for lamina in laminas:
        peor = None
        for parte in lamina["partes"]:
            estado_tarea = por_tarea.get(parte.pop("_tarea", None))
            if not estado_tarea:
                continue
            parte["estado"] = estado_tarea.color  # mismo nivel que la agenda (urgente = rojo)
            parte["tarea"] = {
                "id": estado_tarea.tarea.pk,
                "nombre": estado_tarea.tarea.nombre, "etiqueta": estado_tarea.etiqueta,
                "detalle": estado_tarea.detalle,
                "servicio": estado_tarea.tarea.servicio_id,
                "porcentaje": estado_tarea.porcentaje if estado_tarea.progreso is not None else None,
                "intervalo": intervalo_texto(estado_tarea.tarea),
                "ancla": f"tarea-{estado_tarea.tarea.clave}",
                "hazlo_tu": estado_tarea.tarea.hazlo_tu,
                **km_guia(estado_tarea),
            }
            if peor is None or GRAVEDAD[estado_tarea.color] > GRAVEDAD[peor]:
                peor = estado_tarea.color
        # El estado del sistema sale solo de sus piezas con tarea: así siempre hay una pieza que lo explica, y el visor
        # abre en ella (vencida > pronto > la más avanzada en su intervalo > la de menor número). Sin piezas con tarea, sin estado.
        lamina["estado"] = peor
        motivo = [p for p in lamina["partes"] if p.get("estado") in ("vencido", "pronto", "desconocido")]
        # Con igual urgencia, la pieza principal antes que su tornillería ("Kit de arrastre" antes que "Kit tornillos")
        motivo.sort(key=lambda p: (-GRAVEDAD[p["estado"]], -((p["tarea"] or {}).get("porcentaje") or 0),
                                   bool(_TORNILLERIA.search(p.get("nombre", ""))), p["ref"]))
        lamina["inicial"] = motivo[0]["id"] if motivo else None
    laminas.sort(key=lambda l: -GRAVEDAD.get(l["estado"] or "ok", 0))
    moto = plan.moto
    registro = {
        "url": reverse("garaje:registrar_mantenimiento", args=[moto.pk]),
        "km": moto.km_actual, "hoy": timezone.localdate().isoformat(),
        "talleres": [[t.pk, t.nombre] for t in Taller.objects.filter(activo=True).only("nombre")],
        # Al elegir un taller de TallerYa se muestra ya el QR del código (reutiliza el vigente) para que lo verifique
        "codigo_url": reverse("garaje:codigo_taller", args=[moto.pk]),
    }
    return {"version": despiece.version, "anio": despiece.anio, "moto": moto.nombre_completo, "laminas": laminas,
            "sistemas": base["sistemas"], "orden_subgrupos": ORDEN_SUBGRUPOS, "registro": registro}


def _laminas_base(despiece, sistemas=None):
    """Láminas del despiece sin nada de una moto en particular (el estado se agrega en datos_despiece).
    `sistemas`: arma solo las vistas de esos sistemas (lo demás ni se dibuja)."""
    laminas = []
    perfil = _perfil_motor(despiece)
    faltan, usadas_ya = _tareas_sin_pieza(despiece), set()      # piezas que el plan revisa y los planos no traen
    tareas_por_pk = {t.pk: t for t in TareaMantenimiento.objects.all()}
    for lamina in despiece.laminas.prefetch_related("partes__tarea__servicio"):
        todas_lamina, alternos = _unir_variantes(list(lamina.partes.all()))
        todas_lamina = _con_rueda_fonica(lamina, todas_lamina)
        todas_lamina = _con_piezas_de_tarea(lamina, todas_lamina, faltan, usadas_ya)
        for vista_id, vista_nombre, todas in _vistas(lamina, todas_lamina):
            pieza_vista = ("cadena" if str(vista_id).endswith("-arrastre")
                           else "llanta_tras" if lamina.diagrama in diagramas.CON_ARRASTRE else lamina.pieza)
            sistema, subgrupo = sistema_de(lamina.diagrama, pieza_vista, vista_nombre, vista_id)
            if sistemas and sistema not in sistemas:
                continue
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
                # Sin ficha propia, o con una que no vale en este sistema ("CAM" es de la CVT; en el freno quedaba el
                # texto genérico): la guía de su papel mecánico en el dibujo o por su nombre de taller
                if not tiene_guia_propia(p.descripcion) or guia.get("que_hace") == _GUIA_GENERICA:
                    if con_dibujo and p.pk in posiciones:
                        kit = diagramas.puestos_kit(lamina.diagrama, p.descripcion)
                        mecanica = guia_mecanica(lamina.diagrama, posiciones[p.pk][2], kit, p.descripcion, (nombre_por_sistema(lamina.diagrama, p.descripcion) or getattr(p, "nombre", "")))
                    else:
                        mecanica = guia_mecanica(lamina.diagrama, diagramas.herraje_para(p.descripcion), None, p.descripcion,
                                                 (nombre_por_sistema(lamina.diagrama, p.descripcion) or getattr(p, "nombre", "")))
                    if mecanica:
                        guia.update(mecanica)
                # Tapa de la transmisión de una automática (fig. de la tapa de la CVT): no es la tapa del clutch de una moto de cambios
                if lamina.pieza == "correa" and lamina.diagrama == "carcasa" and re.match(r"(CUBIERTA DE CARTER|COVER, CRANKCASE)", p.descripcion.upper()):
                    guia["que_hace"] = ("Es la tapa de la transmisión: cubre el variador, la correa y el clutch, y trae la entrada de aire "
                                        "con su filtro para enfriar la correa.")
                    guia["cada_cuanto"] = "Se quita para revisar la correa y el variador; revisa que sus tornillos y su empaque cierren bien."
                # En una automática no hay piñón de salida ni palanca de cambios: el retén sella el cigüeñal o el eje de la rueda
                if lamina.despiece.linea.transmision == "cvt" and re.search(r"pi[ñn][oó]n de salida|palanca de cambios", guia.get("que_hace", ""), re.I):
                    guia["que_hace"] = ("Es un retén: sella donde un eje sale del cárter (el cigüeñal del lado del variador o del generador, "
                                        "o el eje de la rueda) para que no se escape el aceite.")
                if lamina.diagrama != "cvt" and lamina.pieza != "correa" and re.search(r"\bcorrea\b", guia.get("cada_cuanto", ""), re.I):
                    guia["cada_cuanto"] = "Se revisa si la moto patina o tiembla al arrancar, o cuando se abre el motor."
                # Filtro de aire: tres tipos con cuidados distintos (espuma se lava; papel viscoso no deja pasar luz ni se limpia)
                if lamina.pieza == "filtro_aire" and re.search(r"ELEMENT|FILTR|ESPUMA|SPONGE|FOAM", p.descripcion.upper()) \
                        and not re.search(r"CASE|CAJA|CAP\b|TAPA|COVER|CUBIERTA|JOINT|DUCT|CONDUCTO|HOLDER|SOPORTE", p.descripcion.upper()):
                    linea_nombre = lamina.despiece.linea.nombre
                    tipo = ("espuma" if re.search(r"ESPUMA|SPONGE|FOAM", p.descripcion.upper()) else
                            _FILTRO_AIRE_POR_LINEA.get(linea_nombre)
                            or ("viscoso" if lamina.despiece.linea.marca.nombre.lower() in ("yamaha", "honda") else "sin_confirmar"))
                    guia.update(_CUIDADO_FILTRO_AIRE[tipo])
                # Una sola fuente para los intervalos: si la pieza lleva una tarea del plan, el "cada cuánto" sale del intervalo de
                # esa tarea para esta línea (su manual, o el general), y la ficha no repite cifras que podrían contradecirlo
                # Filas sin tarea de una pieza del plan (otra variante del filtro de aire, la cadena, la batería): toman la
                # tarea por el concepto, solo para el texto, si su ficha trae cifras de ese mantenimiento
                clave_concepto = None
                if not p.tarea_id and re.search(r"\d[\d.]*\s*(km|mes|meses)\b", guia.get("cada_cuanto", ""), re.I):
                    clave_concepto = next((c for patron, c in _CONCEPTO_TAREA if re.search(patron, f"{p.descripcion} {p.nombre}".upper())), None)
                    if not clave_concepto and lamina.pieza == "filtro_aire" and re.search(r"\bfiltro\b", guia.get("cada_cuanto", "") + guia.get("que_hace", ""), re.I):
                        clave_concepto = "filtro-aire"        # "ELEMENT AIR/C", "GUARD, ELEMENT": piezas del filtro de aire
                    if not clave_concepto and lamina.pieza == "bateria" and re.search(r"^12\s*V|\bGEL\b", p.descripcion.upper()):
                        clave_concepto = "bateria"            # "12V (Gel)": la batería misma, nombrada por su tipo
                    # Accesorios de la batería (base, banda, caucho, caja): no tienen el intervalo de la batería
                    if clave_concepto == "bateria" and re.match(r"(BASE|BANDA|BAND|CAJA|CASE|BOX|HOLDER|SOPORTE|ANTIVIBRANTE|CAUCHO|CABLE|MANGUERA|"
                                                                r"HOSE|TERMINAL|TAPA|CAP|CORREA)", p.descripcion.upper()):
                        clave_concepto = None
                        guia["cada_cuanto"] = "No tiene cambio por kilometraje: revísalo cuando revises la batería y cámbialo si está roto."
                tarea_texto = (tareas_por_pk.get(p.tarea_id) if p.tarea_id else
                               next((t for t in tareas_por_pk.values() if t.clave == clave_concepto), None))
                if tarea_texto:
                    intervalo = intervalo_para(tarea_texto.clave, lamina.despiece.linea, anio=lamina.despiece.anio)
                    if intervalo and intervalo.get("texto"):
                        consejo = " ".join(f for f in re.split(r"(?<=[.;])\s+", guia.get("cada_cuanto", ""))
                                           if f and f[:1].isupper() and "plan de tu moto" not in f
                                           and not re.search(r"\d[\d.]*\s*(km|kil[oó]metros|mes|meses|años?|días?|semanas?)\b", f, re.I))
                        guia["cada_cuanto"] = f"{intervalo['texto']}, según el plan de tu moto." + (f" {consejo}" if consejo else "")
                    # La especificación (viscosidad y norma del aceite, referencia de bujía, presión de llantas) también es de
                    # cada moto: sale del mismo archivo; si no está, un consejo prudente en vez de una cifra para todas
                    clave_tarea = tarea_texto.clave
                    especificacion = (intervalo or {}).get("especificacion")
                    if especificacion:
                        guia["cada_cuanto"] += f" Especificación de tu moto: {especificacion}."
                    elif clave_tarea in _ESPECIFICACION_GENERICA:
                        guia["cada_cuanto"] += f" {_ESPECIFICACION_GENERICA[clave_tarea]}"
                if getattr(p, "contexto", None):
                    guia["contexto"] = p.contexto
                elif getattr(p, "virtual", False):
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
                    "_puesto": posiciones[p.pk][2] if con_dibujo and p.pk in posiciones else "",
                    # Pieza que la moto tiene pero los planos de la marca no traen (la dibujamos para su tarea)
                    "fuera_planos": bool(getattr(p, "contexto", None)),
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
            # Empaques: primero el del tapón (con su guía propia), después los demás sin dueño ("O ring" → "Empaque de la culata")
            sellos_tapon = nombres_de_sellos(partes)
            for i, nombre in nombres_de_empaques(partes, lamina.nombre).items():
                if i not in sellos_tapon:
                    partes[i]["nombre"] = nombre
            for parte in partes:
                parte.pop("_puesto", None)
            for i, nombre in sellos_tapon.items():
                partes[i]["nombre"] = nombre
                tapon = partes[i - 1]["nombre"][:1].lower() + partes[i - 1]["nombre"][1:]
                plan_texto = ""
                if partes[i].get("_tarea") in tareas_por_pk:
                    intervalo = intervalo_para(tareas_por_pk[partes[i]["_tarea"]].clave, despiece.linea, anio=despiece.anio)
                    plan_texto = f"{intervalo['texto']}, según el plan de tu moto. " if intervalo and intervalo.get("texto") else ""
                partes[i]["guia"] = {**(partes[i]["guia"] or {}),
                                     "que_hace": f"Es el empaque del {tapon}: sella el tapón para que no haya fugas ni "
                                                 "entre mugre. Es lo que se cambia; el tapón se vuelve a usar.",
                                     "cada_cuanto": plan_texto + "Revísalo cada vez que quites el tapón y cámbialo si está duro, "
                                                    "aplastado o rajado. Es barato: ante la duda, nuevo."}
            # Rótulo del dibujo: el sistema y la moto (como en el pie de un plano técnico)
            rotulo = f"{vista_nombre} · {despiece.linea}"[:90]
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
def confirmar_km(request, pk):
    """«¿Vas por unos X km?»: «Sí» guarda la estimación como lectura; «Ahora no» la pospone unos días."""
    moto = _moto_de(request, pk)
    if request.POST.get("accion") == "despues":
        moto.km_pregunta_pospuesta = timezone.localdate()
        moto.save(update_fields=["km_pregunta_pospuesta"])
        return redirect(moto)
    try:
        km = int(request.POST.get("km", ""))
    except ValueError:
        km = 0
    if km_valido(moto, km) and registrar_lectura(moto, km, estimada=True):
        messages.success(request, f"Kilometraje actualizado: {_miles(km)} km.")
    else:
        messages.error(request, "No pudimos confirmar ese kilometraje. Escríbelo abajo.")
    return redirect(moto)


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

    antes = {t.tarea.pk: t.color for t in calcular_plan(moto).tareas}
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
        "cambiaron": sorted(t.tarea.nombre for t in plan.tareas if antes.get(t.tarea.pk) != t.color),
    })


@con_motociclista
@require_POST
def registrar_mantenimiento(request, pk):
    moto = _moto_de(request, pk)
    sin_recargar = request.headers.get("X-Requested-With") == "fetch"
    datos, error_cuando = request.POST, None
    if request.POST.get("cuando"):
        # Diálogo "Registrar mantenimiento": las mismas opciones que "Poner al día" (Hace poco · A los … km · No sé)
        datos = request.POST.copy()
        tarea = TareaMantenimiento.objects.filter(pk=datos.get("tarea") or 0, activo=True).first()
        try:
            fecha = date.fromisoformat(datos.get("fecha", "")) if datos.get("fecha") else None
        except ValueError:
            fecha = None
        if fecha and fecha > timezone.localdate():
            fecha = None
        m, error_cuando = (leer_cuando(tarea, moto, datos["cuando"], datos.get("km", ""), datos.get("hace", ""), fecha, origen="")
                           if tarea else (None, None))
        if tarea and not m and not error_cuando:
            error_cuando = "Elige más o menos hace cuánto lo hiciste, o la fecha."
        if m:
            datos["km"], datos["fecha"] = str(m.km), m.fecha.isoformat()
            datos["notas"] = f"{(datos.get('notas') or '')[:200 - len(m.notas) - 1]} {m.notas}".strip()
    form = MantenimientoForm(datos, moto=moto)
    if not error_cuando and form.is_valid():
        registro = form.save(commit=False)
        registro.moto = moto
        registro.save()
        AjusteTarea.objects.filter(moto=moto, tarea=registro.tarea).delete()
        # Ya quedó en la hoja de vida (señal); el precio, si lo hizo un taller, va en ese mismo registro → Gastos lo suma una vez.
        # "Sin idea" no es un servicio hecho: no va a la hoja de vida.
        if not es_sin_idea(registro):
            hoja_vida.desde_mantenimiento(registro, costo=form.cleaned_data.get("precio"))
        url_hoja = reverse("garaje:hoja_vida", args=[moto.pk])
        mensaje = (f"Listo: {registro.tarea.nombre} cuenta desde que la moto era nueva (estimado)." if es_sin_idea(registro) else
                   f"Registrado: {registro.tarea.nombre} a los ≈ {_miles(registro.km)} km (estimados por la fecha)."
                   if km_es_estimado(registro) else f"Registrado: {registro.tarea.nombre} a los {_miles(registro.km)} km.")
        if sin_recargar:
            # Nuevo estado de esa tarea, para actualizar la ficha y los números del despiece sin recargar.
            t = next((t for t in calcular_plan(moto).tareas if t.tarea.pk == registro.tarea_id), None)
            return JsonResponse({"ok": True, "mensaje": mensaje, "hoja_vida": url_hoja, "tarea": t and {
                "id": t.tarea.pk, "estado": t.color, "etiqueta": t.etiqueta, "detalle": t.detalle,
                "porcentaje": t.porcentaje if t.progreso is not None else None, **km_guia(t),
            }})
        messages.success(request, f"{mensaje} Guardado también en tu hoja de vida.")
    else:
        errores = [e for lista in form.errors.values() for e in lista]
        error = error_cuando or " ".join(errores) or "Revisa los datos del mantenimiento."
        if sin_recargar:
            return JsonResponse({"ok": False, "error": error}, status=400)
        messages.error(request, error)
    return redirect(f"{moto.get_absolute_url()}#plan")



# ---------------- Poner al día el plan (al agregar una moto) ----------------
PIEZAS_PRINCIPALES = ["aceite", "filtro_aire", "bujia", "cadena", "correa", "freno_del", "freno_tras", "llanta_del", "llanta_tras",
                      "refrigeracion", "bateria"]
MESES_TENTATIVOS = {"1": "Hace 1 mes", "3": "Hace 3 meses", "6": "Hace 6 meses", "12": "Hace más de un año"}


def _tareas_principales(moto):
    specs = moto.specs()
    tareas = [intervalos.aplicar(t, moto.linea, anio=moto.modelo) if moto.linea_id else t  # con el intervalo del manual de la línea
              for t in TareaMantenimiento.objects.filter(activo=True, pieza__in=PIEZAS_PRINCIPALES) if t.aplica_a(specs)]
    return sorted(tareas, key=lambda t: (PIEZAS_PRINCIPALES.index(t.pieza), t.orden))


def leer_cuando(tarea, moto, eleccion, km_texto="", hace="", fecha=None, hoy=None, origen="Registrado al agregar la moto"):
    """Una respuesta de "¿cuándo se hizo?" (Hace poco · A los … km · No sé), la misma en "Poner al día" y en el diálogo
    "Registrar mantenimiento". Devuelve (Mantenimiento sin guardar, o None si no hay nada que registrar; error).
    Lo que no trae km o fecha se estima con las lecturas y el ritmo de la moto (plan.km_en_fecha / fecha_en_km)."""
    hoy = hoy or timezone.localdate()
    notas = lambda marca="": " ".join(p for p in (origen, marca) if p)
    if eleccion == "poco":
        return Mantenimiento(tarea=tarea, km=moto.km_actual, fecha=hoy, notas=notas()), None
    if eleccion == "km":
        texto = (km_texto or "").strip()
        if not texto.isdigit() or int(texto) > moto.km_actual:
            return None, f"Escribe un kilometraje entre 0 y {_miles(moto.km_actual)} km."
        km = int(texto)
        if fecha:
            return Mantenimiento(tarea=tarea, km=km, fecha=fecha, notas=notas()), None
        return Mantenimiento(tarea=tarea, km=km, fecha=fecha_en_km(moto, km, hoy), notas=notas("(fecha estimada)")), None
    if eleccion == "nose":
        if fecha:  # sabe la fecha pero no el kilometraje
            return Mantenimiento(tarea=tarea, km=km_en_fecha(moto, fecha, hoy), fecha=fecha,
                                 notas=notas("(km estimado por la fecha)")), None
        if hace == "sin_idea":  # no sabe si alguna vez se cambió: desde nueva (cuenta como supuesto en el plan)
            return Mantenimiento(tarea=tarea, km=0, fecha=fecha_de_nueva(moto, hoy), notas=notas(MARCA_SIN_IDEA)), None
        if hace in MESES_TENTATIVOS:  # "hace unos meses": el km de esa fecha sale de las lecturas o del ritmo de la moto
            fecha = hoy - timedelta(days=int(hace) * 30)
            return Mantenimiento(tarea=tarea, km=km_en_fecha(moto, fecha, hoy), fecha=fecha,
                                 notas=notas("(fecha y km estimados)")), None
    return None, None


def _leer_al_dia(datos, tareas, moto, previos=None):
    """Lee las respuestas de "último mantenimiento". Devuelve (mantenimientos sin moto, errores por tarea).
    `previos` = {tarea_id: km del último registro}: si la respuesta es ese mismo kilometraje, no se crea nada."""
    previos = previos or {}
    hoy = timezone.localdate()
    nuevos, errores = [], {}
    for t in tareas:
        eleccion = datos.get(f"estado_{t.pk}", "")
        if eleccion == "km" and (datos.get(f"km_{t.pk}") or "").strip() == str(previos.get(t.pk)):
            continue  # sin cambios: se conserva el registro que ya tenía
        m, error = leer_cuando(t, moto, eleccion, datos.get(f"km_{t.pk}", ""), datos.get(f"hace_{t.pk}", ""), hoy=hoy)
        if error:
            errores[t.pk] = error
        elif m:
            nuevos.append(m)
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
        tareas = sorted((t.tarea for t in plan.sin_registro + plan.estimados), key=lambda t: t.orden)  # sin ningún registro
    else:
        tareas = sorted((t.tarea for t in plan.tareas), key=lambda t: t.orden)
    ultimos = {}
    for m in moto.mantenimientos.order_by("fecha", "km"):
        ultimos[m.tarea_id] = m.km  # se queda con el más reciente
    previos = {t.pk: ultimos[t.pk] for t in tareas if t.pk in ultimos}
    errores = {}
    if request.method == "POST":
        nuevos, errores = _leer_al_dia(request.POST, tareas, moto, previos)
        if not errores:
            for m in nuevos:
                m.moto = moto
            for m in nuevos:  # uno a uno: cada mantenimiento también queda en la hoja de vida
                m.save()
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


@xframe_options_sameorigin
@con_motociclista
def vista_3d(request, pk):
    """Solo el modelo 3D de la moto, girando, para mostrarlo dentro de la portada del inicio."""
    moto = _moto_de(request, pk)
    return render(request, "garaje/vista_3d.html", {"datos_3d": {
        "specs": moto.specs(), "color": moto.color, "piezas": {}, "linea": moto.nombre_completo, "placa": moto.placa,
        "color_secundario": moto.color_secundario, "calcas": moto.calcas, "estilo": moto.estilo,
                     "calcas_personalizadas": settings.CALCAS_PERSONALIZADAS}})
