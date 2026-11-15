"""Correcciones del auditor mecánico: rines de la XTZ 125, edad de las llantas y nombres de revisión de frenos."""
from django.db import migrations

LLANTA_DESCRIPCION = ("Cámbiala si el labrado llega al testigo (1 mm en moto) o si el caucho está cuarteado, "
                      "aunque tenga pocos km.")
NOMBRES = {
    "pastillas-del": ("Pastillas de freno delanteras", "Revisión de pastillas delanteras"),
    "pastillas-tras": ("Pastillas de freno traseras", "Revisión de pastillas traseras"),
    "bandas-del": ("Bandas de freno delanteras", "Revisión de bandas delanteras"),
    "bandas-tras": ("Bandas de freno traseras", "Revisión de bandas traseras"),
}


def corregir(apps, schema_editor):
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    Tarea = apps.get_model("garaje", "TareaMantenimiento")
    # XTZ 125: 2.75-21 adelante y 4.10-18 atrás (manual del propietario Yamaha)
    LineaMoto.objects.filter(nombre="XTZ 125").update(rin_delantero=21, rin_trasero=18)
    # Llantas: también por edad (5 años): el caucho se cuartea aunque tenga labrado
    Tarea.objects.filter(clave__in=["llanta-del", "llanta-tras"]).update(intervalo_dias=1825,
                                                                         descripcion=LLANTA_DESCRIPCION)
    # Frenos: se cambian por desgaste, no por km fijo; el intervalo es de revisión
    for clave, (_, nuevo) in NOMBRES.items():
        Tarea.objects.filter(clave=clave).update(nombre=nuevo)


def revertir(apps, schema_editor):
    LineaMoto = apps.get_model("garaje", "LineaMoto")
    Tarea = apps.get_model("garaje", "TareaMantenimiento")
    LineaMoto.objects.filter(nombre="XTZ 125").update(rin_delantero=19, rin_trasero=17)
    Tarea.objects.filter(clave="llanta-del").update(
        intervalo_dias=None, descripcion="Revisa la profundidad del labrado y la presión cada semana.")
    Tarea.objects.filter(clave="llanta-tras").update(intervalo_dias=None,
                                                     descripcion="Se gasta más rápido que la delantera.")
    for clave, (viejo, _) in NOMBRES.items():
        Tarea.objects.filter(clave=clave).update(nombre=viejo)


class Migration(migrations.Migration):
    dependencies = [("garaje", "0022_linea_aerox_155")]
    operations = [migrations.RunPython(corregir, revertir)]
