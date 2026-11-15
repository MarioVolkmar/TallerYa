"""Revisa que en cada despiece activo cada tarea del plan tenga una pieza, y que el visor abra en ella.

Para cada despiece y cada tarea que aplica a la línea, simula una moto con esa tarea vencida (las demás al día) y
comprueba que los sistemas en "Toca ya" abren en una pieza de esa tarea. Uso: manage.py auditar_tareas_despiece
"""
from types import SimpleNamespace

from django.core.management.base import BaseCommand

from garaje.models import Despiece, Moto, TareaMantenimiento
from garaje.views import _laminas_base, datos_despiece


def _plan_simulado(moto, tareas, vencida):
    estados = [SimpleNamespace(tarea=t, estado="vencido" if t.pk == vencida.pk else "ok",
                               color="vencido" if t.pk == vencida.pk else "ok", etiqueta="", detalle="",
                               progreso=100 if t.pk == vencida.pk else 10, porcentaje=100 if t.pk == vencida.pk else 10)
               for t in tareas]
    return SimpleNamespace(tareas=estados, moto=moto, piezas=lambda: {})


def auditar():
    """Lista de problemas: (moto, tarea, explicación). Vacía si todo está bien."""
    problemas, sin_pieza = [], []
    for despiece in Despiece.objects.filter(activo=True).select_related("linea"):
        moto = Moto(pk=0, linea=despiece.linea, km_actual=0, modelo=despiece.anio)   # specs de esa versión
        tareas = [t for t in TareaMantenimiento.objects.filter(activo=True) if t.aplica_a(moto.specs())]
        # Lo que ve el visor: piezas del catálogo y las agregadas por no venir en los planos
        enlazadas = {q.get("_tarea") for lam in _laminas_base(despiece)["laminas"] for q in lam["partes"]} - {None}
        for tarea in tareas:
            if tarea.pk not in enlazadas:
                sin_pieza.append((despiece.linea.nombre, tarea.clave))
                continue
            datos = datos_despiece(despiece, _plan_simulado(moto, tareas, tarea))
            for lamina in datos["laminas"]:
                if lamina["estado"] != "vencido":
                    continue
                inicial = next((p for p in lamina["partes"] if p["id"] == lamina["inicial"]), None)
                if not inicial or not inicial.get("tarea") or inicial["tarea"]["id"] != tarea.pk:
                    problemas.append((despiece.linea.nombre, tarea.clave, f"{lamina['nombre']} abre en otra pieza"))
    return problemas, sin_pieza


class Command(BaseCommand):
    help = "Revisa que cada tarea del plan tenga pieza en cada despiece y que el visor abra en ella."

    def handle(self, **opts):
        problemas, sin_pieza = auditar()
        for moto, tarea, texto in problemas:
            self.stdout.write(self.style.ERROR(f"{moto}: {tarea}: {texto}"))
        for moto, tarea in sin_pieza:
            self.stdout.write(f"{moto}: {tarea} sin pieza en el catálogo (el sistema no se muestra con estado)")
        self.stdout.write(self.style.SUCCESS(f"Sistemas que abren en otra pieza: {len(problemas)} · tareas sin pieza: {len(sin_pieza)}"))
