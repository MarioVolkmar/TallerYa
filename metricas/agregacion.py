"""Agregación por día (idempotente) y purga de lo crudo. La usa `manage.py agregar_metricas` y el panel.

Un día cerrado se resume una sola vez (marca `_hecho`); hoy se resume al vuelo sin guardar."""
from collections import Counter
from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from .models import ActividadSemanal, Evento, ResumenDiario, SalDiaria

DIAS_CRUDOS = 90


def lunes(dia):
    return dia - timedelta(days=dia.weekday())


def _usuarios_entre(desde, hasta):
    return (Evento.objects.filter(dia__gte=desde, dia__lte=hasta, usuario_id__isnull=False)
            .values("usuario_id").distinct().count())


def resumir(dia):
    """Filas de ResumenDiario (sin guardar) para un día."""
    filas = []
    del_dia = Evento.objects.filter(dia=dia)
    vistas = del_dia.filter(tipo=Evento.VISTA)

    def agrupar(qs, campo, clave):
        for r in qs.values(campo).annotate(total=Count("id"), unicos=Count("visitante", distinct=True)):
            filas.append(ResumenDiario(dia=dia, clave=clave, valor=(r[campo] or "")[:80], total=r["total"],
                                       unicos=r["unicos"]))

    agrupar(vistas, "nombre", "vista")
    agrupar(del_dia.filter(tipo=Evento.FUNCION), "nombre", "evento")
    agrupar(vistas, "dispositivo", "dispositivo")
    agrupar(vistas.exclude(referente="interno"), "referente", "referente")

    terminos = Counter(d.get("q") for d in del_dia.filter(nombre="busqueda_talleres").values_list("datos", flat=True)
                       if isinstance(d, dict) and d.get("q"))
    filas += [ResumenDiario(dia=dia, clave="busqueda", valor=t[:80], total=n, unicos=n) for t, n in terminos.items()]

    totales = del_dia.aggregate(visitantes=Count("visitante", distinct=True),
                                usuarios=Count("usuario_id", distinct=True), eventos=Count("id"))
    filas += [
        ResumenDiario(dia=dia, clave="activos", valor="visitantes", total=totales["eventos"], unicos=totales["visitantes"]),
        ResumenDiario(dia=dia, clave="activos", valor="dia", total=totales["usuarios"], unicos=totales["usuarios"]),
        ResumenDiario(dia=dia, clave="activos", valor="7d", unicos=_usuarios_entre(dia - timedelta(days=6), dia)),
        ResumenDiario(dia=dia, clave="activos", valor="30d", unicos=_usuarios_entre(dia - timedelta(days=29), dia)),
    ]
    return filas


@transaction.atomic
def agregar_dia(dia):
    ResumenDiario.objects.filter(dia=dia).delete()
    filas = resumir(dia) + [ResumenDiario(dia=dia, clave="_hecho")]
    ResumenDiario.objects.bulk_create(filas)
    semana = lunes(dia)
    ids = Evento.objects.filter(dia=dia, usuario_id__isnull=False).values_list("usuario_id", flat=True).distinct()
    ActividadSemanal.objects.bulk_create([ActividadSemanal(usuario_id=u, semana=semana) for u in ids],
                                         ignore_conflicts=True)
    return len(filas) - 1


def agregar_pendientes(hoy=None):
    """Resume los días cerrados que tienen crudos y aún no tienen resumen. Devuelve cuántos días resumió."""
    hoy = hoy or timezone.localdate()
    con_crudos = set(Evento.objects.filter(dia__lt=hoy).values_list("dia", flat=True).distinct())
    hechos = set(ResumenDiario.objects.filter(clave="_hecho", dia__in=con_crudos).values_list("dia", flat=True))
    for dia in sorted(con_crudos - hechos):
        agregar_dia(dia)
    return len(con_crudos - hechos)


def purgar(hoy=None, dias=DIAS_CRUDOS):
    """Borra los eventos crudos de más de `dias` días (ya resumidos) y las sales viejas."""
    hoy = hoy or timezone.localdate()
    agregar_pendientes(hoy)
    borrados, _ = Evento.objects.filter(dia__lt=hoy - timedelta(days=dias)).delete()
    SalDiaria.objects.filter(dia__lt=hoy).delete()
    return borrados
