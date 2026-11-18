"""Sección «Métricas» de la consola: (plantilla, contexto). Días cerrados desde ResumenDiario; hoy, al vuelo."""
from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe

from . import nucleo
from .agregacion import agregar_pendientes, lunes, resumir
from .models import ActividadSemanal, Evento, ResumenDiario

PERIODOS = (7, 30, 90)
DISPOSITIVOS = {"c": "Celular", "e": "Escritorio", "t": "Tableta"}
REFERENTES = {"directo": "Directo", "google": "Google", "buscadores": "Otros buscadores", "whatsapp": "WhatsApp",
              "redes": "Redes sociales", "otros": "Otros sitios", "": "Sin dato"}
def periodo_de(request):
    try:
        dias = int(request.GET.get("periodo", 30))
    except ValueError:
        dias = 30
    return dias if dias in PERIODOS else 30


def paginas_conocidas(hoy, dias=365):
    """Páginas que alguien vio en el último año: las que hoy tienen 0 visitas salen como «candidatas a sobrar».
    (Se toman del historial y no de las URL: así no aparecen acciones POST ni respuestas JSON.)"""
    return set(ResumenDiario.objects.filter(clave="vista", dia__gte=hoy - timedelta(days=dias))
               .values_list("valor", flat=True).distinct())


def _filas(desde, hoy):
    agregar_pendientes(hoy)
    filas = list(ResumenDiario.objects.filter(dia__gte=desde, dia__lt=hoy).exclude(clave="_hecho"))
    return filas + resumir(hoy)


def _suma(filas, clave, campo="total"):
    cuenta = defaultdict(int)
    for f in filas:
        if f.clave == clave:
            cuenta[f.valor] += getattr(f, campo)
    return cuenta


def _barras(cuenta, nombres=None, limite=None, inverso=False):
    filas = sorted(cuenta.items(), key=lambda kv: (kv[1], kv[0]) if inverso else (-kv[1], kv[0]))
    if limite:
        filas = filas[:limite]
    total = sum(cuenta.values()) or 1
    maximo = max([n for _, n in filas] or [1]) or 1
    return [{"clave": k, "nombre": (nombres or {}).get(k, k), "n": n, "pct": round(100 * n / total),
             "ancho": max(2, round(100 * n / maximo)) if n else 0} for k, n in filas]


def _paso(nombre, n, anterior, primero):
    return {"nombre": nombre, "n": n, "del_anterior": round(100 * n / anterior) if anterior else 0,
            "del_total": round(100 * n / primero) if primero else 0, "ancho": max(2, round(100 * n / primero)) if primero and n else 0}


def _usuarios_con(nombre, desde):
    return set(Evento.objects.filter(dia__gte=desde, nombre=nombre, usuario_id__isnull=False)
               .values_list("usuario_id", flat=True))


def _visitas_dia_con(nombre, desde):
    return Evento.objects.filter(dia__gte=desde, nombre=nombre).values("visitante", "dia").distinct().count()


def embudos(desde, visitantes):
    registrados = _usuarios_con("registro", desde)
    con_moto = registrados & _usuarios_con("moto_creada", desde)
    con_plan = con_moto & _usuarios_con("plan_visto", desde)
    motero = [visitantes, len(registrados), len(con_moto), len(con_plan)]
    vieron, contactaron = _visitas_dia_con("taller_visto", desde), _visitas_dia_con("contacto", desde)
    canjes = Evento.objects.filter(dia__gte=desde, nombre="cupon_canjeado").count()
    taller = [vieron, contactaron, canjes]

    def armar(nombres, ns):
        return [_paso(nombre, n, ns[i - 1] if i else n, ns[0]) for i, (nombre, n) in enumerate(zip(nombres, ns))]
    return [
        {"titulo": "Motero", "pasos": armar(["Visitantes (por día)", "Se registraron", "Crearon una moto",
                                              "Vieron su plan"], motero)},
        {"titulo": "Talleres", "pasos": armar(["Vieron un taller (visitante-día)", "Lo contactaron",
                                                "Cupones canjeados"], taller)},
    ]


def retencion(hoy, semanas=8):
    """Por cohorte de registro (semana): % de esas cuentas activas en la semana 0, 1, 2... después."""
    inicio = lunes(hoy) - timedelta(weeks=semanas - 1)
    usuarios = get_user_model().objects.filter(date_joined__date__gte=inicio, is_staff=False).values_list("pk", "date_joined")
    cohortes = defaultdict(set)
    for pk, alta in usuarios:
        cohortes[lunes(timezone.localtime(alta).date())].add(pk)
    activos = defaultdict(set)
    for u, semana in ActividadSemanal.objects.filter(semana__gte=inicio).values_list("usuario_id", "semana"):
        activos[semana].add(u)
    activos[lunes(hoy)] |= set(Evento.objects.filter(dia__gte=lunes(hoy), usuario_id__isnull=False)
                               .values_list("usuario_id", flat=True))
    filas = []
    for k in range(semanas):
        semana = inicio + timedelta(weeks=k)
        gente = cohortes.get(semana, set())
        celdas = []
        for j in range(semanas - k):
            if not gente:
                celdas.append(None)
                continue
            pct = round(100 * len(gente & activos.get(semana + timedelta(weeks=j), set())) / len(gente))
            celdas.append(pct)
        filas.append({"semana": semana, "n": len(gente), "celdas": celdas})
    return filas, list(range(semanas))


def grafico(serie):
    """SVG propio (sin librerías): barras = páginas vistas, línea = visitantes, línea punteada = usuarios con cuenta."""
    an, al, iz, ab, ar = 640, 230, 36, 28, 14
    n = len(serie)
    maximo = max([max(d["vistas"], d["visitantes"]) for d in serie] + [1])
    paso = (an - iz - 8) / max(n, 1)
    y = lambda v: ar + (al - ar - ab) * (1 - v / maximo)  # noqa: E731
    x = lambda i: iz + paso * i + paso / 2  # noqa: E731
    partes = [f'<svg viewBox="0 0 {an} {al}" class="mt-grafico" role="img" aria-labelledby="mt-graf-t">'
              f'<title id="mt-graf-t">Páginas vistas, visitantes y usuarios activos por día</title>']
    for frac in (0, .5, 1):
        v = round(maximo * frac)
        partes.append(f'<line x1="{iz}" x2="{an - 4}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="mt-guia"/>'
                      f'<text x="{iz - 6}" y="{y(v) + 4:.1f}" text-anchor="end" class="mt-eje">{v}</text>')
    ancho_barra = max(1.5, paso * .7)
    for i, d in enumerate(serie):
        alto = (al - ar - ab) * d["vistas"] / maximo
        partes.append(f'<rect x="{x(i) - ancho_barra / 2:.1f}" y="{al - ab - alto:.1f}" width="{ancho_barra:.1f}" '
                      f'height="{alto:.1f}" class="mt-barra"><title>{d["dia"]:%d %b}: {d["vistas"]} páginas, '
                      f'{d["visitantes"]} visitantes, {d["usuarios"]} usuarios</title></rect>')
    for campo, clase in (("visitantes", "mt-linea"), ("usuarios", "mt-linea mt-linea-2")):
        puntos = " ".join(f"{x(i):.1f},{y(d[campo]):.1f}" for i, d in enumerate(serie))
        partes.append(f'<polyline points="{puntos}" class="{clase}"/>')
    for i in sorted({0, n // 2, n - 1}):
        if 0 <= i < n:
            partes.append(f'<text x="{x(i):.1f}" y="{al - 8}" text-anchor="middle" class="mt-eje">'
                          f'{escape(serie[i]["dia"].strftime("%d/%m"))}</text>')
    partes.append("</svg>")
    return mark_safe("".join(partes))


def seccion(request):
    dias = periodo_de(request)
    hoy = timezone.localdate()
    desde = hoy - timedelta(days=dias - 1)
    filas = _filas(desde, hoy)

    por_dia = defaultdict(lambda: {"vistas": 0, "visitantes": 0, "usuarios": 0})
    for f in filas:
        if f.clave == "vista":
            por_dia[f.dia]["vistas"] += f.total
        elif f.clave == "activos" and f.valor == "visitantes":
            por_dia[f.dia]["visitantes"] = f.unicos
        elif f.clave == "activos" and f.valor == "dia":
            por_dia[f.dia]["usuarios"] = f.unicos
    serie = [{"dia": desde + timedelta(days=i), **por_dia[desde + timedelta(days=i)]} for i in range(dias)]

    vistas, eventos = _suma(filas, "vista"), _suma(filas, "evento")
    visitantes_dia = sum(d["visitantes"] for d in serie)
    activos = {f.valor: f.unicos for f in filas if f.clave == "activos" and f.dia == hoy}
    usuarios_periodo = (Evento.objects.filter(dia__gte=desde, usuario_id__isnull=False)
                        .values("usuario_id").distinct().count())

    paginas_todas = dict(vistas)
    for nombre in paginas_conocidas(hoy):
        paginas_todas.setdefault(nombre, 0)
    eventos_todos = {k: eventos.get(k, 0) for k in nucleo.EVENTOS} | dict(eventos)

    return "metricas/panel.html", {
        "periodos": PERIODOS, "dias": dias, "desde": desde, "hoy": hoy,
        "activas": nucleo.activas(),
        "tarjetas": [
            ("Páginas vistas", sum(vistas.values())),
            ("Visitantes (suma diaria)", visitantes_dia),
            ("Usuarios con cuenta activos", usuarios_periodo),
            ("Registros", eventos.get("registro", 0)),
            ("Motos creadas", eventos.get("moto_creada", 0)),
            ("Contactos a talleres", eventos.get("contacto", 0)),
        ],
        "activos": [("Hoy (DAU)", activos.get("dia", 0)), ("7 días (WAU)", activos.get("7d", 0)),
                    ("30 días (MAU)", activos.get("30d", 0))],
        "grafico": grafico(serie),
        "top_paginas": _barras(vistas, limite=10),
        "top_eventos": _barras(eventos, nucleo.EVENTOS, limite=10),
        "menos_paginas": _barras(paginas_todas, limite=10, inverso=True),
        "menos_eventos": _barras(eventos_todos, nucleo.EVENTOS, limite=8, inverso=True),
        "dispositivos": _barras(_suma(filas, "dispositivo", "unicos"), DISPOSITIVOS),
        "referentes": _barras(_suma(filas, "referente", "unicos"), REFERENTES),
        "busquedas": _barras(_suma(filas, "busqueda"), limite=10),
        "embudos": embudos(desde, visitantes_dia),
        "retencion": retencion(hoy),
    }
