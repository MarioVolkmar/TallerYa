"""Especificaciones propias de una versión del despiece (ej. freno trasero de tambor en la Gixxer 150 2015)."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("garaje", "0024_despiece_variante")]
    operations = [
        migrations.AddField(
            model_name="despiece", name="especificaciones",
            field=models.JSONField(blank=True, default=dict,
                                   help_text='Lo que esta versión cambia de la ficha de la línea, ej: {"freno_trasero": "tambor"}'),
        ),
    ]
