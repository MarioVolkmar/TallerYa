"""Vista del diagnóstico guiado (datos en diagnostico.py). Aparte de views.py para no cruzarse con otras sesiones."""
from types import SimpleNamespace
from urllib.parse import urlencode

from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from talleres.models import Servicio, Taller

from . import diagnostico as dx
from .models import Despiece
from .plan import calcular_plan
from .views import base_en_cache, datos_despiece

CLAVES_FIJAS = ("moto", "t", "s")


def _motos_del_usuario(request):
    perfil = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    return list(perfil.motos.select_related("linea", "linea__marca")) if perfil else []


def _url(base, **params):
    params = {k: v for k, v in params.items() if v not in (None, "")}
    return f"{base}?{urlencode(params)}" if params else base


def _catalogo():
    """Motos con despiece, para diagnosticar una que no está en el garaje. Hay un despiece por moto, así que se nombran
    sin año ("Honda CB 125F"); si dos quedan con el mismo nombre, se desempata con la versión del catálogo."""
    catalogo = list(Despiece.objects.filter(activo=True).select_related("linea", "linea__marca")
                    .order_by("linea__marca__nombre", "linea__nombre", "-anio"))
    nombres = [f"{d.linea.marca.nombre} {d.linea.nombre}" for d in catalogo]
    for d, nombre in zip(catalogo, nombres):
        if nombres.count(nombre) == 1:
            d.etiqueta = nombre
            continue
        # Varias versiones de la misma línea (Gixxer 150 de carburador y FI ABS): su variante y los años que cubre cada una
        anios = sorted(o.anio for o in catalogo if o.linea_id == d.linea_id)
        siguiente = next((a for a in anios if a > d.anio), None)
        rango = f"{d.anio}–{siguiente - 1}" if siguiente else f"{d.anio} en adelante"
        d.etiqueta = f"{nombre} {d.variante} ({rango})" if d.variante else f"{nombre} ({d.version}, {rango})"
        d.modelo = d.etiqueta[len(d.linea.marca.nombre) + 1:]
    return catalogo


def _laminas_de(despiece, moto=None, sistemas=None):
    """Láminas del despiece como las ve el visor; sin moto (moto del catálogo), sin estado de mantenimiento.
    `sistemas`: solo las del resultado (armar todo el despiece en frío tarda segundos)."""
    if moto:
        return datos_despiece(despiece, calcular_plan(moto), sistemas)["laminas"]
    sin_moto = SimpleNamespace(pk=0, km_actual=0, nombre_completo=str(despiece.linea))
    plan = SimpleNamespace(moto=sin_moto, tareas=[], piezas=lambda: {})
    return datos_despiece(despiece, plan, sistemas)["laminas"]


def despiece_publico(request, pk):
    """Láminas de un despiece del catálogo (sin datos de ninguna moto), para la guía de pieza del diagnóstico."""
    despiece = get_object_or_404(Despiece, pk=pk, activo=True)
    sin_moto = SimpleNamespace(pk=0, km_actual=0, nombre_completo=str(despiece.linea))
    datos = datos_despiece(despiece, SimpleNamespace(moto=sin_moto, tareas=[], piezas=lambda: {}))
    datos.pop("registro", None)   # registrar mantenimiento no aplica sin moto del garaje
    return JsonResponse(datos)


def _tarjetas_diagnostico(talleres, moto, usuario):
    """Datos de la tarjeta de taller (los mismos del directorio) y si trabaja la marca de la moto."""
    from talleres.views import _preparar_tarjetas
    talleres = _preparar_tarjetas(list(talleres), usuario)
    marca = moto.linea.marca_id if moto and moto.linea_id else None
    for t in talleres:
        t.tu_marca = bool(marca) and any(m.pk == marca for m in t.marcas.all())
    return talleres


def diagnostico(request):
    base = reverse("garaje:diagnostico")
    motos = _motos_del_usuario(request)
    moto = None
    if request.GET.get("moto", "").isdigit():
        moto = next((m for m in motos if m.pk == int(request.GET["moto"])), None)
    elif len(motos) == 1 and request.GET.get("moto") != "otra" and not request.GET.get("despiece"):
        moto = motos[0]
    # Moto del catálogo (no está en el garaje): se usa su despiece
    catalogo = _catalogo()
    del_catalogo = None
    if not moto and request.GET.get("despiece", "").isdigit():
        del_catalogo = next((d for d in catalogo if d.pk == int(request.GET["despiece"])), None)

    if del_catalogo and getattr(del_catalogo, "linea_id", None):  # si esa línea ya es una moto suya, se usa la suya (?moto=)
        suya = next((m for m in motos if m.linea_id == del_catalogo.linea_id), None)
        if suya:
            moto, del_catalogo = suya, None
    linea = getattr(moto, "linea", None) or getattr(del_catalogo, "linea", None)
    t = getattr(linea, "transmision", "") or request.GET.get("t", "")
    t = t if t in ("cadena", "cvt") else ""
    r = getattr(linea, "refrigeracion", "") if linea else ""
    fijos = {"moto": moto.pk if moto else ("otra" if request.GET.get("moto") == "otra" else None),
             "despiece": del_catalogo.pk if del_catalogo else None,
             "t": None if linea and linea.transmision else t}
    ctx = {"motos": motos, "moto": moto, "t": t, "base": base, "aviso": True,
           "cambiar_moto": _url(base) if motos else None,
           "catalogo": catalogo, "del_catalogo": del_catalogo}

    # 1) Tipo de moto (si no la sabemos por su línea)
    if not t:
        ctx["paso"] = "tipo"
        ctx["tipos"] = [(_url(base, **{**fijos, "t": v}), nombre, ayuda) for v, nombre, ayuda in (
            ("cadena", "De cambios", "Con clutch en la manigueta o semiautomática, y cadena"),
            ("cvt", "Automática", "Scooter: sin cambios, con correa (CVT)"))]
        return render(request, "garaje/diagnostico.html", ctx)

    sintomas = dict(dx.sintomas_para(t))
    s = request.GET.get("s", "")
    # 2) Síntoma
    if s not in sintomas:
        ctx["paso"] = "sintoma"
        ctx["sintomas"] = [(_url(base, **fijos, s=clave), datos["nombre"], datos["icono"]) for clave, datos in sintomas.items()]
        # Sin moto del garaje: interruptor para pasar de "de cambios" a "automática" sin volver atrás
        if fijos["t"]:
            ctx["tipo_toggle"] = [(_url(base, **{**fijos, "t": v}), nombre, v == t)
                                  for v, nombre in (("cadena", "De cambios"), ("cvt", "Automática"))]
        return render(request, "garaje/diagnostico.html", ctx)

    preguntas_todas = {p["clave"] for p in dx.SINTOMAS[s]["preguntas"]}
    respuestas = {k: v for k, v in request.GET.items() if k in preguntas_todas}
    contexto = {**respuestas, "t": t, "r": r}
    ctx["sintoma"] = sintomas[s]["nombre"]
    ctx["reiniciar"] = _url(base, **fijos)

    # Respuestas dadas, cada una con un enlace para cambiarla (vuelve a esa pregunta)
    visibles = dx.preguntas_visibles(s, contexto)
    dadas, previas = [], {}
    for p in visibles:
        valor = contexto.get(p["clave"])
        texto = dict(p["opciones"]).get(valor)
        if not texto:
            break
        dadas.append({"pregunta": p["texto"], "respuesta": texto, "cambiar": _url(base, **fijos, s=s, **previas)})
        previas[p["clave"]] = valor
    ctx["dadas"] = dadas

    clave = dx.resultado(s, contexto)
    # 3) Siguiente pregunta
    if not clave:
        pregunta = next(p for p in visibles if dict(p["opciones"]).get(contexto.get(p["clave"])) is None)
        ctx["paso"] = "pregunta"
        ctx["pregunta"] = {"texto": pregunta["texto"], "opciones": [
            (_url(base, **fijos, s=s, **previas, **{pregunta["clave"]: v}), texto) for v, texto in pregunta["opciones"]]}
        ctx["numero"] = len(dadas) + 1
        return render(request, "garaje/diagnostico.html", ctx)

    # 4) Resultado
    res = dx.RESULTADOS[clave]
    subgrupo = res.get("subgrupo") or (dx.subgrupo_freno(contexto) if res["sistema"] == "Frenos" else "")
    nombre_servicio = dx.servicio_de(clave)
    servicio = Servicio.objects.filter(nombre=nombre_servicio).first()
    from talleres.views import _base_talleres
    talleres = _base_talleres()
    if servicio:
        talleres = talleres.filter(servicios=servicio)
    piezas, esquemas, sin_despiece, esquema_diferido, aviso = [], [], False, None, None
    despiece = Despiece.para(moto) if moto else del_catalogo
    if despiece:
        sistemas_res = dx.sistemas_a_armar(res)
        solo_esquema = request.GET.get("parte") == "esquema"
        esquema_url = _url(base, **fijos, s=s, **respuestas, parte="esquema")
        # El esquema necesita los dibujos de las láminas del sistema: si no están en caché tardan segundos en armarse,
        # así que la página sale ya y el esquema llega aparte (?parte=esquema) con un "cargando" visible.
        if solo_esquema or base_en_cache(despiece, sistemas_res):
            laminas = _laminas_de(despiece, moto, sistemas_res)
            # Una pestaña por lámina con candidatas (varias causas en sistemas distintos): hasta 4
            piezas = dx.piezas_candidatas(clave, laminas, subgrupo, limite=16)
            esquemas = dx.esquemas(piezas, laminas, maximo=4)
            aviso = None if esquemas else (res["sistema"] + (f" · {subgrupo}" if subgrupo else ""))
            if solo_esquema:
                lamina = request.GET.get("lamina")
                if lamina:  # una pestaña que se abre después
                    e = next((e for e in esquemas if str(e["id"]) == lamina), None)
                    return render(request, "garaje/_diag_esquema_fig.html", {"e": e}) if e else HttpResponse("")
                return render(request, "garaje/_diag_esquema.html",
                              {"esquemas": esquemas, "esquema_url": esquema_url, "aviso_sistema": aviso})
        else:
            esquema_diferido = esquema_url
    elif moto:
        sin_despiece = True
    # Se anota en la sesión para poder citarlo en el foro (solo lo de esta persona)
    recordar_diagnostico(request, sintomas[s]["nombre"], res["causa"],
                         moto.nombre_completo if moto else getattr(del_catalogo, "etiqueta", ""))
    ctx.update({
        "enviar_url": _url(reverse("garaje:diagnostico_enviar"), **fijos, s=s, **respuestas),
        "compartir_url": _url(reverse("foro:preguntar"), diagnostico=request.session["diagnosticos"][0]["consulta"]),
        "paso": "resultado", "clave": clave, "res": res, "subgrupo": subgrupo,
        "urgencia": res["urgencia"], "urgencia_info": dx.URGENCIAS[res["urgencia"]],
        "piezas": piezas, "sin_despiece": sin_despiece, "esquemas": esquemas, "esquema_diferido": esquema_diferido,
        "esquema_url": esquema_url if despiece else None,
        "aviso_sistema": aviso if despiece and not esquema_diferido else None,
        "datos_url": (reverse("garaje:despiece_json", args=[moto.pk]) if moto and despiece
                      else reverse("garaje:diagnostico_despiece", args=[despiece.pk]) if despiece else None),
        "servicio": servicio, "nombre_servicio": nombre_servicio,
        "talleres": _tarjetas_diagnostico(talleres.order_by("-destacado", "-verificado", "nombre")[:3], moto, request.user),
        "directorio": _url(reverse("talleres:directorio"), servicio=servicio.pk if servicio else None),
    })
    return render(request, "garaje/diagnostico.html", ctx)


# ---------- Compartir en el foro ----------
# Los diagnósticos no se guardan: son una URL con las respuestas. Para citarlos en el foro, cada resultado que alguien ve
# se anota en SU sesión (solo la consulta) y, al publicar, el servidor vuelve a calcular el resumen desde esa consulta
# con las motos de quien publica. Así nadie puede adjuntar el diagnóstico de otro (una moto ajena no resuelve) y el
# resumen guardado es inmutable y no depende de texto enviado por el navegador.

MAX_RECIENTES = 6


def recordar_diagnostico(request, sintoma, causa, moto_nombre):
    """Anota la consulta del resultado en la sesión (los últimos MAX_RECIENTES, sin repetir)."""
    consulta = request.GET.copy()
    consulta.pop("parte", None)
    consulta.pop("lamina", None)
    consulta = consulta.urlencode()
    recientes = [d for d in request.session.get("diagnosticos", []) if d.get("consulta") != consulta]
    recientes.insert(0, {"consulta": consulta, "sintoma": sintoma, "causa": causa, "moto": moto_nombre})
    request.session["diagnosticos"] = recientes[:MAX_RECIENTES]


def diagnosticos_recientes(request):
    """Los diagnósticos que esta persona vio (de su sesión), para adjuntar en el foro."""
    return [d for d in request.session.get("diagnosticos", []) if isinstance(d, dict) and d.get("consulta")]


def resumen_diagnostico(consulta, usuario, con_piezas=True):
    """Resumen público del diagnóstico de esa consulta, o None si no llega a un resultado o la moto no es de `usuario`.

    Solo datos públicos: marca, modelo y año de la moto (nunca placa, apodo ni dueño), síntoma, causa, sistema y las
    piezas candidatas. `enlace` abre el mismo diagnóstico para cualquiera (con el despiece de esa línea, no la moto)."""
    from django.http import QueryDict
    q = QueryDict(consulta or "")
    perfil = getattr(usuario, "motociclista", None) if usuario and usuario.is_authenticated else None
    moto, despiece = None, None
    if q.get("moto", "").isdigit():
        if not perfil:
            return None
        moto = perfil.motos.select_related("linea", "linea__marca").filter(pk=int(q["moto"])).first()
        if moto is None:  # moto ajena o borrada: no se puede citar
            return None
    elif q.get("despiece", "").isdigit():
        despiece = Despiece.objects.filter(pk=int(q["despiece"]), activo=True).select_related("linea", "linea__marca").first()
    linea = getattr(moto, "linea", None) or getattr(despiece, "linea", None)
    t = getattr(linea, "transmision", "") or q.get("t", "")
    if t not in ("cadena", "cvt"):
        return None
    s = q.get("s", "")
    sintomas = dict(dx.sintomas_para(t))
    if s not in sintomas:
        return None
    respuestas = {p["clave"]: q[p["clave"]] for p in dx.SINTOMAS[s]["preguntas"] if q.get(p["clave"])}
    contexto = {**respuestas, "t": t, "r": getattr(linea, "refrigeracion", "") if linea else ""}
    clave = dx.resultado(s, contexto)
    if not clave:
        return None
    res = dx.RESULTADOS[clave]
    subgrupo = res.get("subgrupo") or (dx.subgrupo_freno(contexto) if res["sistema"] == "Frenos" else "")
    if moto:
        despiece = Despiece.para(moto)
        marca = moto.linea.marca.nombre if moto.linea_id else moto.marca_otra
        modelo, anio = (moto.linea.nombre if moto.linea_id else moto.linea_otra), moto.modelo
    elif despiece:
        marca, modelo, anio = despiece.linea.marca.nombre, despiece.linea.nombre, None
    else:
        marca, modelo, anio = "", "", None
    piezas = []
    if despiece and con_piezas:
        sistemas_res = dx.sistemas_a_armar(res)
        laminas = _laminas_de(despiece, None, sistemas_res)  # sin moto: no hace falta su estado de mantenimiento
        piezas = [p["nombre"] for p in dx.piezas_candidatas(clave, laminas, subgrupo, limite=6)]
    enlace = _url(reverse("garaje:diagnostico"), despiece=despiece.pk if despiece else None,
                  t=None if despiece and linea and linea.transmision else t, s=s, **respuestas)
    return {"clave": clave, "sintoma_clave": s, "sintoma": sintomas[s]["nombre"], "marca": marca[:60], "modelo": modelo[:80],
            "anio": anio, "causa": res["causa"], "sistema": res["sistema"], "subgrupo": subgrupo or "",
            "urgencia": res["urgencia"], "revisa": res.get("revisa", ""), "piezas": piezas, "enlace": enlace,
            "linea_id": linea.pk if linea else None, "marca_id": linea.marca_id if linea else None}
