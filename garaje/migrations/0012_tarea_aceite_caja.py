"""Recordatorio del aceite de la caja (transmisión final) para las motos automáticas con CVT."""
from django.db import migrations


def crear(apps, schema_editor):
    Tarea = apps.get_model("garaje", "TareaMantenimiento")
    Servicio = apps.get_model("talleres", "Servicio")
    correa = Tarea.objects.filter(clave="correa-cvt").first()
    Tarea.objects.get_or_create(clave="aceite-caja", defaults=dict(
        nombre="Cambio de aceite de la caja",
        descripcion="Aceite de la transmisión final de la scooter (no es el del motor). Es poco, pero se quema y se contamina.",
        pieza="correa", aplica="cvt", intervalo_km=8000, intervalo_dias=365,
        servicio=Servicio.objects.filter(nombre="Cambio de aceite").first(),
        hazlo_tu=False, orden=(correa.orden + 1) if correa else 0,
    ))


def quitar(apps, schema_editor):
    apps.get_model("garaje", "TareaMantenimiento").objects.filter(clave="aceite-caja").delete()


class Migration(migrations.Migration):
    dependencies = [("garaje", "0011_moto_placa"), ("talleres", "0001_initial")]
    operations = [migrations.RunPython(crear, quitar)]
