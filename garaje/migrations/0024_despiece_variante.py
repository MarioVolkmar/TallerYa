"""Variante del despiece (Carburador, FI ABS...): distingue versiones de una misma línea en el diagnóstico."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("garaje", "0023_correcciones_auditor_mecanico")]
    operations = [
        migrations.AddField(
            model_name="despiece", name="variante",
            field=models.CharField(blank=True, max_length=40,
                                   help_text="Cómo se distingue de otra versión de la misma línea (ej: Carburador, FI ABS)"),
        ),
    ]
