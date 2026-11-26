"""Cifras por semana (lunes a domingo) para el panel: qué partes se usan. Solo conteos, ningún dato personal.

Las visitas y los planos/3D salen de la medición (ResumenDiario); lo demás, de lo que ya está en la base, así que
también cuenta las semanas anteriores a la medición. No se cuenta al equipo administrador."""
from collections import Counter
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef
from django.db.models.functions import TruncWeek
from django.utils import timezone

from cupones.models import CodigoCupon, Motociclista
from domicilio.models import MecanicoDomicilio
from domiciliarios.models import PerfilDomiciliario
from foro.models import Asistencia, Pregunta, Respuesta
from garaje.models import FichaDiagnostico, Gasto, LecturaKm, Moto, RegistroServicio
from talleres.models import Taller
from tramites.models import PedidoSoat

from .agregacion import lunes

SEMANAS = 6

# Sección del sitio según la app de la ruta ("garaje:moto" → Garaje). Las primeras cinco salen siempre.
SECCIONES = {
    "talleres": "Talleres y portada", "garaje": "Garaje", "foro": "Foro", "cupones": "Cupones", "tramites": "Trámites",
    "domicilio": "Mecánicos a domicilio", "domiciliarios": "TallerYa Ruta", "proveedores": "Proveedores",
    "cuentas": "Cuenta y registro", "cotizador": "Cotizador", "noticias": "Noticias", "logros": "Insignias",
    "ayuda": "Ayuda", "notificaciones": "Avisos",
}
FIJAS = ("talleres", "garaje", "foro", "cupones", "tramites")
OTRAS = "Otras páginas"


def _por_semana(qs, campo):
    """{lunes: filas} de las fechas `campo`, en hora local; una sola consulta."""
    filas = qs.annotate(s=TruncWeek(campo)).values("s").annotate(n=Count("pk")).order_by()
    return {f["s"].date(): f["n"] for f in filas if f["s"]}


def _visitas(filas, semanas):
    cuenta = {clave: Counter() for clave in [*SECCIONES, ""]}
    for f in filas:
        if f.clave == "vista":
            app = f.valor.split(":")[0] if ":" in f.valor else ""
            cuenta[app if app in SECCIONES else ""][lunes(f.dia)] += f.total
    return [(SECCIONES.get(app, OTRAS), c) for app, c in cuenta.items()
            if app in FIJAS or any(c[s] for s in semanas)]


def _usuarios_nuevos(desde):
    """Cuentas nuevas por rol, con la misma prioridad de la consola: taller, motero (o domiciliario), mecánico."""
    filas = (get_user_model().objects.filter(date_joined__gte=desde, is_staff=False)
             .annotate(taller_=Exists(Taller.objects.filter(usuario=OuterRef("pk"))),
                       motero_=Exists(Motociclista.objects.filter(usuario=OuterRef("pk"))),
                       ruta_=Exists(PerfilDomiciliario.objects.filter(motociclista__usuario=OuterRef("pk"))),
                       mecanico_=Exists(MecanicoDomicilio.objects.filter(usuario=OuterRef("pk"))))
             .values_list("date_joined", "taller_", "motero_", "ruta_", "mecanico_"))
    cuenta = {n: Counter() for n in ("Moteros", "Domiciliarios", "Talleres", "Mecánicos", "Sin terminar el registro")}
    for alta, taller, motero, ruta, mecanico in filas:
        rol = ("Talleres" if taller else "Domiciliarios" if ruta else "Moteros" if motero
               else "Mecánicos" if mecanico else "Sin terminar el registro")
        cuenta[rol][lunes(timezone.localtime(alta).date())] += 1
    return list(cuenta.items())


def grupos(filas, hoy):
    """`filas`: ResumenDiario que cubran las semanas mostradas (incluido hoy). La semana actual va primero."""
    semanas = [lunes(hoy) - timedelta(weeks=i) for i in range(SEMANAS)]
    desde = timezone.make_aware(datetime.combine(semanas[-1], time.min))

    def base(modelo, campo="creado", dueno=None):
        qs = modelo.objects.filter(**{f"{campo}__gte": desde})
        return _por_semana(qs.exclude(**{f"{dueno}__is_staff": True}) if dueno else qs, campo)

    def evento(nombre):
        c = Counter()
        for f in filas:
            if f.clave == "evento" and f.valor == nombre:
                c[lunes(f.dia)] += f.total
        return c

    de_moto = "moto__motociclista__usuario"
    crudo = [
        ("Visitas por sección", _visitas(filas, semanas)),
        ("Usuarios nuevos por rol", _usuarios_nuevos(desde)),
        ("Garaje", [
            ("Motos agregadas", base(Moto, dueno="motociclista__usuario")),
            ("Servicios anotados", base(RegistroServicio, dueno=de_moto)),
            ("Lecturas de kilometraje", base(LecturaKm, dueno=de_moto)),
            ("Gastos anotados", base(Gasto, dueno=de_moto)),
            ("Fichas de diagnóstico", base(FichaDiagnostico)),
            ("Planes vistos", evento("plan_visto")),
            ("Despieces abiertos", evento("despiece_abierto")),
            ("3D abierto", evento("visor_3d")),
        ]),
        ("Foro", [
            ("Preguntas", base(Pregunta, dueno="autor")),
            ("Respuestas", base(Respuesta, dueno="autor")),
            ("Inscripciones a rodadas", base(Asistencia, dueno="usuario")),
        ]),
        ("Cupones", [
            ("Códigos entregados", base(CodigoCupon, dueno="motociclista__usuario")),
            ("Códigos canjeados", base(CodigoCupon, "canjeado_en", "motociclista__usuario")),
        ]),
        ("Trámites", [
            ("Pedidos de SOAT", base(PedidoSoat, dueno=de_moto)),
            ("SOAT pagados", base(PedidoSoat, "pagado_en", de_moto)),
            ("Pólizas emitidas", base(PedidoSoat, "emitido_en", de_moto)),
        ]),
    ]
    return {
        "semanas": semanas,
        "grupos": [(titulo, [(nombre, [por.get(s, 0) for s in semanas]) for nombre, por in renglones])
                   for titulo, renglones in crudo],
    }
