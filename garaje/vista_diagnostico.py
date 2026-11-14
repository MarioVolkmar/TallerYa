"""Vista del diagnóstico guiado (datos en diagnostico.py). Aparte de views.py para no cruzarse con otras sesiones."""
from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse

from talleres.models import Servicio, Taller

from . import diagnostico as dx
from .models import Despiece
from .plan import calcular_plan
from .views import datos_despiece

CLAVES_FIJAS = ("moto", "t", "s")


def _motos_del_usuario(request):
    perfil = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    return list(perfil.motos.select_related("linea", "linea__marca")) if perfil else []


def _url(base, **params):
    params = {k: v for k, v in params.items() if v not in (None, "")}
    return f"{base}?{urlencode(params)}" if params else base


def diagnostico(request):
    base = reverse("garaje:diagnostico")
    motos = _motos_del_usuario(request)
    moto = None
    if request.GET.get("moto", "").isdigit():
        moto = next((m for m in motos if m.pk == int(request.GET["moto"])), None)
    elif len(motos) == 1 and request.GET.get("moto") != "otra":
        moto = motos[0]

    linea = getattr(moto, "linea", None)
    t = getattr(linea, "transmision", "") or request.GET.get("t", "")
    t = t if t in ("cadena", "cvt") else ""
    r = getattr(linea, "refrigeracion", "") if linea else ""
    fijos = {"moto": moto.pk if moto else ("otra" if request.GET.get("moto") == "otra" else None),
             "t": None if linea and linea.transmision else t}
    ctx = {"motos": motos, "moto": moto, "t": t, "base": base, "aviso": True,
           "cambiar_moto": _url(base) if motos else None}

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
    talleres = Taller.objects.filter(activo=True).select_related("barrio")
    if servicio:
        talleres = talleres.filter(servicios=servicio)
    piezas, sin_despiece = [], False
    if moto:
        despiece = Despiece.para(moto)
        if despiece:
            laminas = datos_despiece(despiece, calcular_plan(moto))["laminas"]
            piezas = dx.piezas_candidatas(clave, laminas, subgrupo)
            for p in piezas:
                p["url"] = f"{moto.get_absolute_url()}?pieza={p['id']}#despiece"
        else:
            sin_despiece = True
    ctx.update({
        "paso": "resultado", "clave": clave, "res": res, "subgrupo": subgrupo,
        "urgencia": res["urgencia"], "urgencia_info": dx.URGENCIAS[res["urgencia"]],
        "piezas": piezas, "sin_despiece": sin_despiece,
        "servicio": servicio, "nombre_servicio": nombre_servicio,
        "talleres": talleres.order_by("-destacado", "-verificado", "nombre")[:3],
        "directorio": _url(reverse("talleres:directorio"), servicio=servicio.pk if servicio else None),
    })
    return render(request, "garaje/diagnostico.html", ctx)
