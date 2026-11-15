"""La tarea del filtro de aire se llama «Revisión y cambio de filtro de aire».

En varias motos (Best 125, GN 125 y otras) el manual pide limpiarlo o revisarlo a ese kilometraje y cambiarlo según
su estado: «Cambio» a secas prometía un repuesto que no siempre toca. Solo cambia el nombre (misma clave y misma fila),
así que el historial, los ajustes y los registros de «ya lo hice» siguen apuntando a la misma tarea.
"""
from django.db import migrations

NUEVO = "Revisión y cambio de filtro de aire"
VIEJO = "Cambio de filtro de aire"


def renombrar(apps, schema_editor):
    apps.get_model("garaje", "TareaMantenimiento").objects.filter(clave="filtro-aire").update(nombre=NUEVO)


def revertir(apps, schema_editor):
    apps.get_model("garaje", "TareaMantenimiento").objects.filter(clave="filtro-aire").update(nombre=VIEJO)


class Migration(migrations.Migration):
    dependencies = [("garaje", "0033_hunk_150")]
    operations = [migrations.RunPython(renombrar, revertir)]
