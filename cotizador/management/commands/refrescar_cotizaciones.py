"""Refresco nocturno: vuelve a consultar las cotizaciones más pedidas que ya tienen más de ~20 h, con un tope de
consultas por corrida para no gastar la cuota de Mercado Libre. Pensado para un cron (ver cotizador/README.md).

    python manage.py refrescar_cotizaciones --max 60
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cotizador import servicio
from cotizador.models import Cotizacion


class Command(BaseCommand):
    help = "Refresca las cotizaciones más pedidas (tope de consultas por corrida)."

    def add_arguments(self, parser):
        parser.add_argument("--max", type=int, default=60, help="Máximo de piezas por corrida (cada una gasta 1-2 consultas)")
        parser.add_argument("--horas", type=int, default=20, help="Solo las consultadas hace más de estas horas")

    def handle(self, *args, **opciones):
        from garaje.models import ParteDespiece

        limite = timezone.now() - timedelta(hours=opciones["horas"])
        viejas = (Cotizacion.objects.filter(consultado_en__lt=limite, parte_id__isnull=False, pedidos__gt=0)
                  .order_by("-pedidos")[: max(0, opciones["max"])])
        hechas = fallidas = 0
        for cot in viejas:
            parte = (ParteDespiece.objects.select_related("lamina__despiece__linea__marca")
                     .filter(pk=cot.parte_id).first())
            if not parte:
                continue
            try:
                servicio.cotizar(servicio.datos_parte(parte), forzar=True, contar=False, tope_global=False)
                hechas += 1
            except servicio.SinDatos as e:
                fallidas += 1
                self.stderr.write(f"{cot.consulta}: {e}")
        self.stdout.write(f"Cotizaciones refrescadas: {hechas} · fallidas: {fallidas}")
