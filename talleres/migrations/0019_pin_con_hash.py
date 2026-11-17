"""PIN de canje: de texto en claro (único entre talleres, buscado por su valor) a hash por taller.

Los PIN existentes se conservan: se guarda su hash, así cada taller sigue usando el mismo PIN. Después se borra la
columna en claro. No hay vuelta atrás (el hash no se puede deshacer): al revertir, los talleres quedan sin PIN y lo
generan de nuevo en Mi taller.
"""
from django.contrib.auth.hashers import make_password
from django.db import migrations, models


def hashear(apps, schema_editor):
    Taller = apps.get_model("talleres", "Taller")
    for taller in Taller.objects.exclude(pin_canje__isnull=True).exclude(pin_canje="").only("pk", "pin_canje"):
        Taller.objects.filter(pk=taller.pk).update(pin_hash=make_password(taller.pin_canje))


class Migration(migrations.Migration):
    dependencies = [("talleres", "0018_perfil_estandarizado")]

    operations = [
        migrations.AddField(
            model_name="taller",
            name="pin_hash",
            field=models.CharField(blank=True, editable=False, max_length=128, verbose_name="PIN de canje (hash)"),
        ),
        migrations.RunPython(hashear, migrations.RunPython.noop),
        migrations.RemoveField(model_name="taller", name="pin_canje"),
    ]
