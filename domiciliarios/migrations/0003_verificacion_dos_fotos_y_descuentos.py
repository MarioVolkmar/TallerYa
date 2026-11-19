"""Verificación con dos fotos obligatorias (pantallazo del perfil con la moto y foto de la moto con placa), sin niveles.
Talleres aliados: quedan solo como descuento para domiciliarios verificados (sin marca «Atiende domiciliarios»)."""
from django.db import migrations, models
import django.db.models.deletion
import domiciliarios.models


def sin_descuento_vacio(apps, schema_editor):
    # El descuento pasa a ser obligatorio: los aliados sin descuento no tienen sentido sin la marca del directorio
    apps.get_model("domiciliarios", "TallerAliado").objects.filter(descuento="").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("domiciliarios", "0002_verificacion"),
    ]

    operations = [
        migrations.RenameField("verificacion", "selfie", "foto_moto"),
        migrations.RemoveField("verificacion", "nivel"),
        migrations.RemoveField("talleraliado", "en_el_dia"),
        migrations.RemoveField("talleraliado", "horario_extendido"),
        migrations.RemoveField("talleraliado", "horario_texto"),
        migrations.RunPython(sin_descuento_vacio, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name='talleraliado',
            options={'ordering': ['orden', 'taller__nombre'], 'verbose_name': 'descuento de taller para domiciliarios', 'verbose_name_plural': 'descuentos de talleres para domiciliarios'},
        ),
        migrations.AlterField(
            model_name='talleraliado',
            name='descuento',
            field=models.CharField(help_text='Lo usan los domiciliarios verificados con Plus. Ej: 10% en mano de obra', max_length=120),
        ),
        migrations.AlterField(
            model_name='verificacion',
            name='captura',
            field=models.FileField(blank=True, storage=domiciliarios.models._almacen_privado, upload_to=domiciliarios.models.ruta_verificacion, verbose_name='pantallazo del perfil en la app'),
        ),
        migrations.AlterField(
            model_name='verificacion',
            name='foto_moto',
            field=models.FileField(blank=True, storage=domiciliarios.models._almacen_privado, upload_to=domiciliarios.models.ruta_verificacion, verbose_name='foto de la moto con la placa'),
        ),
        migrations.AlterField(
            model_name='verificacion',
            name='moto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='garaje.moto', verbose_name='moto del garaje que se verifica'),
        ),
    ]
