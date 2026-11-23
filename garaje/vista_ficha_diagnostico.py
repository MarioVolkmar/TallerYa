"""Piloto, paso 4 (fase 1): enviar un diagnóstico a un taller o a un mecánico a domicilio por WhatsApp.

El motero elige a quién, opcionalmente corrige el km y sube 1-3 fotos; se guarda una FichaDiagnostico (foto fija,
sin datos personales) y se abre WhatsApp con el mensaje armado y el enlace a la ficha pública (token, sin cuenta, 30 días)."""
import re
from urllib.parse import quote, urlencode

from django.db.models import F
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.html import strip_tags

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
MAX_NOTA = 500
NOTA_WHATSAPP = 160
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


# Sistema del diagnóstico → claves de especialidad del perfil (talleres.perfil.ESPECIALIDADES)
ESPECIALIDAD_POR_SISTEMA = {
    "Frenos": {"frenos"}, "Eléctrico": {"electrico"}, "Suspensión": {"suspension"}, "Motor": {"motor"},
    "Transmisión": {"arrastre", "scooters"}, "Inyección": {"inyeccion"}, "Combustible": {"inyeccion", "carburacion"},
}
MAX_DESTACADOS = 2  # «destacado» (plan pro) sube como máximo 2 y va marcado
PRIOR_N, PRIOR_NOTA = 3, 4.0  # nota «bayesiana»: pocas reseñas pesan menos que muchas


def _puntaje(prom, n):
    return ((prom or 0) * n + PRIOR_NOTA * PRIOR_N) / (n + PRIOR_N) if n else 0


def ordenar(candidatos, sistema, destacables):
    """Ordena objetos con .especialidades, .verificado, .prom, .n_resenas, .nombre: quien atiende el sistema, verificado,
    nota (suavizada por nº de reseñas), nº de reseñas y nombre. Marca .atiende y .es_destacado (máx. MAX_DESTACADOS)."""
    claves = ESPECIALIDAD_POR_SISTEMA.get(sistema, set())
    for c in candidatos:
        c.atiende = bool(claves & set(c.especialidades or []))
    llave = lambda c: (-c.atiende, -bool(c.verificado), -_puntaje(c.prom, c.n_resenas), -c.n_resenas, c.nombre.lower())
    ordenados = sorted(candidatos, key=llave)
    destacados = [c for c in ordenados if c.pk in destacables][:MAX_DESTACADOS]
    for c in ordenados:
        c.es_destacado = c in destacados
    return destacados + [c for c in ordenados if not c.es_destacado]


def _opciones(clave, sistema=""):
    from django.db.models import Avg, Count
    from domicilio.models import ResenaMecanico
    from talleres.views import _base_talleres, _preparar_tarjetas
    servicio = Servicio.objects.filter(nombre=dx.servicio_de(clave)).first()
    talleres = _base_talleres().exclude(whatsapp="")
    if servicio:
        talleres = talleres.filter(servicios=servicio)
    talleres = _preparar_tarjetas(list(talleres[:60]))
    destacables = {t.pk for t in talleres if t.destacado}
    talleres = ordenar(talleres, sistema, destacables)[:OPCIONES]
    for t in talleres:
        t.valor_enviar, t.sub_enviar = f"t:{t.pk}", t.barrio.nombre or "Taller"
        t.chips_enviar = [x.nombre for x in t.servicios_vista]
    mecanicos = list(MecanicoDomicilio.objects.publicados().exclude(whatsapp="").prefetch_related("servicios")[:60])
    notas = {r["mecanico"]: r for r in ResenaMecanico.objects.filter(visible=True, mecanico__in=[m.pk for m in mecanicos])
             .values("mecanico").annotate(prom=Avg("estrellas"), n=Count("id"))}
    for m in mecanicos:
        r = notas.get(m.pk)
        m.prom, m.n_resenas = (r["prom"], r["n"]) if r else (None, 0)
        m.estrellas_pct = round((m.prom or 0) * 20)
    mecanicos = ordenar(mecanicos, sistema, set())[:OPCIONES]
    for m in mecanicos:
        m.valor_enviar = f"m:{m.pk}"
        m.sub_enviar = ("Atiende urgencias" if m.urgencias else "A domicilio") + (f" · visita desde {m.tarifa_texto}" if m.tarifa_visita else "")
        m.chips_enviar = [x.nombre for x in list(m.servicios.all())[:3]]
    return talleres, mecanicos


def _km(texto):
    texto = "".join(c for c in (texto or "") if c.isdigit())
    return int(texto) if texto and int(texto) <= MAX_KM else None


def _nota(texto):
    """Texto plano: sin etiquetas, espacios y saltos compactados, con tope."""
    texto = strip_tags(texto or "").replace("\r", "")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
    return texto[:MAX_NOTA]


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
    if ficha.nota:
        nota = " ".join(ficha.nota.split())
        if len(nota) > NOTA_WHATSAPP:
            nota = nota[:NOTA_WHATSAPP - 1].rstrip() + "…"
        lineas.append(f"Nota del motero: {nota}")
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
    talleres, mecanicos = _opciones(res["clave"], res["sistema"])
    ctx = {"res": res, "moto": moto, "km": sugerido, "talleres": talleres, "mecanicos": mecanicos,
           "volver": res["enlace"] if not moto else f"{reverse('garaje:diagnostico')}?{consulta}", "max_fotos": MAX_FOTOS, "max_nota": MAX_NOTA}

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
    ctx["nota"] = _nota(request.POST.get("nota"))
    fotos, error = _fotos_validas(request.FILES.getlist("fotos"))
    if error:
        ctx["error"] = error
        return render(request, "garaje/diagnostico_enviar.html", ctx, status=400)

    km = _km(request.POST.get("km"))
    nombre_moto = " ".join(x for x in (res["marca"], res["modelo"], str(res["anio"] or "")) if x)
    ficha = FichaDiagnostico.objects.create(
        consulta=consulta[:300], moto=nombre_moto, km=km, km_estimado=bool(km and moto and km == km_estimado_hoy(moto)),
        sintoma=res["sintoma"][:80], causa=res["causa"][:200], sistema=res["sistema"][:80], urgencia=res["urgencia"],
        revisa=res["revisa"][:300], piezas=res["piezas"][:6], enlace=res["enlace"][:300], nota=_nota(request.POST.get("nota")),
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
