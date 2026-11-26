"""Recordatorios de mantenimiento de cada negocio a sus clientes (para cron, p. ej. todos los días a las 8 a. m.).

A cada moto cuyo último servicio verificado lo hizo un taller o un mecánico a domicilio, cuando su plan dice que le
toca mantenimiento, le llega un aviso para agendar con ese negocio (talleres/herramientas.py). Idempotente: la clave
del aviso lleva la lista de tareas, así que solo vuelve a avisar si cambia. No hace nada con el módulo
«herramientas_activo» apagado.

    python manage.py recordar_clientes
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Avisa a los clientes de cada taller y mecánico cuando a su moto le toca mantenimiento (no repite avisos)."

    def handle(self, *args, **opciones):
        from consola.ajustes import ajuste
        from domicilio.models import MecanicoDomicilio
        from garaje.models import ServicioTaller
        from talleres import herramientas as h
        from talleres.models import Taller

        if not ajuste("herramientas_activo"):
            self.stdout.write("Herramientas del negocio apagadas: no se envía nada.")
            return
        verificados = ServicioTaller.objects.filter(estado=ServicioTaller.Estado.VERIFICADO)
        negocios = (list(Taller.objects.filter(activo=True, pk__in=verificados.values("taller_id")))
                    + list(MecanicoDomicilio.objects.filter(estado=MecanicoDomicilio.Estado.APROBADO,
                                                            pk__in=verificados.values("mecanico_id"))))
        total = 0
        for n in negocios:
            enviados = h.recordar_todos(n)
            total += enviados
            if enviados:
                self.stdout.write(f"{n.nombre}: {enviados}")
        self.stdout.write(self.style.SUCCESS(f"Recordatorios enviados: {total}"))
