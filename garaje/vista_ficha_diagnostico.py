"""Piloto, paso 4 (fase 1): enviar un diagnóstico a un taller o a un mecánico a domicilio por WhatsApp.

El motero elige a quién, opcionalmente corrige el km y sube 1-3 fotos; se guarda una FichaDiagnostico (foto fija,
sin datos personales) y se abre WhatsApp con el mensaje armado y el enlace a la ficha pública (token, sin cuenta, 30 días)."""
from urllib.parse import quote, urlencode

from django.db.models import F
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from domicilio.forms import foto_trabajo
from domicilio.models import MecanicoDomicilio
from metricas.nucleo import registrar_evento
from talleres import estadisticas
from talleres.models import EventoDiario, Servicio, Taller

from . import diagnostico as dx
from .kilometraje import km_estimado_hoy
from .models import FichaDiagnostico, FotoFichaDiagnostico
from .vista_diagnostico import resumen_diagnostico

MAX_FOTOS = 3
MAX_KM = 999_999
OPCIONES = 6  # talleres y mecánicos que se ofrecen


class _RedireccionWhatsApp(HttpResponseRedirect):
    allowed_schemes = ["https"]


def _consulta(request):
    """Solo las claves del diagnóstico (moto, despiece, t, s y las preguntas del síntoma): nada más viaja a la ficha."""
    s = request.GET.get("s", "")
    permitidas = {"moto", "despiece", "t", "s"} | ({p["clave"] for p in dx.SINTOMAS[s]["preguntas"]} if s in dx.SINTOMAS else set())
    return urlencode([(k, v) for k, v in request.GET.items() if k in permitidas])


def _moto_del_usuario(request, consulta):
    from django.http import QueryDict
    pk = QueryDict(consulta).get("moto", "")
    perfil = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    if not (pk.isdigit() and perfil):
        return None
    return perfil.motos.select_related("linea", "linea__marca").filter(pk=int(pk)).first()


def _opciones(clave):
    from talleres.views import _base_talleres
    servicio = Servicio.objects.filter(nombre=dx.servicio_de(clave)).first()
    talleres = _base_talleres().exclude(whatsapp="")
    if servicio:
        talleres = talleres.filter(servicios=servicio)
    talleres = list(talleres.order_by("-destacado", "-verificado", "nombre")[:OPCIONES])
    mecanicos = list(MecanicoDomicilio.objects.publicados().exclude(whatsapp="").order_by("-urgencias", "-verificado", "nombre")[:OPCIONES])
    return talleres, mecanicos


def _km(texto):
    texto = "".join(c for c in (texto or "") if c.isdigit())
    return int(texto) if texto and int(texto) <= MAX_KM else None


def _fotos_validas(archivos):
    """(contenidos, error): cada foto se valida por su contenido real y se regraba como JPEG sin EXIF."""
    if len(archivos) > MAX_FOTOS:
        return [], f"Máximo {MAX_FOTOS} fotos."
    fotos = []
    for a in archivos:
        f = foto_trabajo(a)
        if f is None:
            return [], f"«{a.name[:40]}» no es una foto válida (JPG, PNG o WebP de hasta 5 MB)."
        fotos.append(f)
    return fotos, ""


def mensaje(ficha, destinatario, url):
    domicilio = ficha.destino == ficha.Destino.DOMICILIO
    lineas = [f"Hola {destinatario}, te encontré en TallerYa" + (" y quiero pedir una visita a domicilio." if domicilio else ".")]
    moto = ficha.moto
    if moto and ficha.km:
        moto += f" (~{ficha.km:,} km{', estimado' if ficha.km_estimado else ''})".replace(",", ".")
    for etiqueta, valor in (("Moto", moto), ("Síntoma", ficha.sintoma), ("Posible causa", ficha.causa)):
        if valor:
            lineas.append(f"{etiqueta}: {valor}")
    fotos = ficha.fotos.count()
    lineas.append(f"Ficha con los detalles{' y ' + str(fotos) + ' foto' + ('s' if fotos != 1 else '') if fotos else ''}: {url}")
    return "\n".join(lineas)


def enviar(request):
    consulta = _consulta(request)
    res = resumen_diagnostico(consulta, request.user)
    if not res:
        raise Http404
    moto = _moto_del_usuario(request, consulta)
    sugerido = km_estimado_hoy(moto) if moto else None
    if not sugerido and moto and moto.km_actual:
        sugerido = moto.km_actual
    talleres, mecanicos = _opciones(res["clave"])
    ctx = {"res": res, "moto": moto, "km": sugerido, "talleres": talleres, "mecanicos": mecanicos,
           "volver": res["enlace"] if not moto else f"{reverse('garaje:diagnostico')}?{consulta}", "max_fotos": MAX_FOTOS}

    if request.method != "POST":
        return render(request, "garaje/diagnostico_enviar.html", ctx)

    destino = request.POST.get("destino", "")
    taller = mecanico = None
    if destino.startswith("t:") and destino[2:].isdigit():
        taller = next((t for t in talleres if t.pk == int(destino[2:])), None)
    elif destino.startswith("m:") and destino[2:].isdigit():
        mecanico = next((m for m in mecanicos if m.pk == int(destino[2:])), None)
    if not (taller or mecanico):
        ctx["error"] = "Elige a quién enviarlo."
        return render(request, "garaje/diagnostico_enviar.html", ctx, status=400)
    fotos, error = _fotos_validas(request.FILES.getlist("fotos"))
    if error:
        ctx["error"] = error
        return render(request, "garaje/diagnostico_enviar.html", ctx, status=400)

    km = _km(request.POST.get("km"))
    nombre_moto = " ".join(x for x in (res["marca"], res["modelo"], str(res["anio"] or "")) if x)
    ficha = FichaDiagnostico.objects.create(
        consulta=consulta[:300], moto=nombre_moto, km=km, km_estimado=bool(km and moto and km == km_estimado_hoy(moto)),
        sintoma=res["sintoma"][:80], causa=res["causa"][:200], sistema=res["sistema"][:80], urgencia=res["urgencia"],
        revisa=res["revisa"][:300], piezas=res["piezas"][:6], enlace=res["enlace"][:300],
        destino=FichaDiagnostico.Destino.TALLER if taller else FichaDiagnostico.Destino.DOMICILIO,
        taller=taller, mecanico=mecanico)
    for i, f in enumerate(fotos):
        FotoFichaDiagnostico.objects.create(ficha=ficha, imagen=f, orden=i)
    destinatario = taller or mecanico
    if taller:  # se mide como el WhatsApp del directorio (paso 1)
        registrar_evento(request, "contacto", canal="whatsapp", taller=taller.pk, origen="diagnostico")
        estadisticas.registrar(request, taller, EventoDiario.Tipo.WHATSAPP)
    else:
        registrar_evento(request, "contacto", canal="whatsapp", mecanico=mecanico.pk, origen="diagnostico")
    url = request.build_absolute_uri(ficha.get_absolute_url())
    texto = mensaje(ficha, destinatario.nombre, url)
    return _RedireccionWhatsApp(f"https://wa.me/{destinatario.whatsapp}?text={quote(texto)}")


def ficha(request, token):
    """Ficha pública: la abre quien reciba el enlace, sin cuenta. No se indexa; vencida responde 410."""
    f = get_object_or_404(FichaDiagnostico.objects.select_related("taller", "mecanico").prefetch_related("fotos"), token=token)
    if f.vencida:
        r = render(request, "garaje/ficha_diagnostico.html", {"vencida": True}, status=410)
    else:
        FichaDiagnostico.objects.filter(pk=f.pk).update(vistas=F("vistas") + 1)
        info = dx.URGENCIAS.get(f.urgencia)
        r = render(request, "garaje/ficha_diagnostico.html", {"f": f, "urgencia_info": info})
    r["X-Robots-Tag"] = "noindex, nofollow"
    r["Cache-Control"] = "private, no-store"
    return r
