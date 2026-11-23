"""Equipo del taller: rol de la lista corta y especialidad ligada al catálogo de servicios (texto libre → servicio
más cercano; sin coincidencia clara, queda como «Otra» con su texto)."""
from django.db import migrations

from talleres import perfil


def migrar(apps, schema_editor):
    Taller = apps.get_model("talleres", "Taller")
    Servicio = apps.get_model("talleres", "Servicio")
    servicios = list(Servicio.objects.values_list("id", "nombre"))
    nombres = dict(servicios)
    for t in Taller.objects.exclude(equipo=[]):
        nuevo = []
        for m in perfil.equipo_limpio(t.equipo):
            if m["rol"] not in perfil.ROLES:
                m["rol"] = perfil.rol_cercano(m["rol"])
            if m["especialidad"] and not m["servicio"]:
                sid = perfil.servicio_cercano(m["especialidad"], servicios)
                if sid:
                    m["servicio"], m["especialidad"] = sid, nombres[sid]
            nuevo.append(m)
        if nuevo != t.equipo:
            t.equipo = nuevo
            t.save(update_fields=["equipo"])


class Migration(migrations.Migration):
    dependencies = [("talleres", "0025_multimarca")]
    operations = [migrations.RunPython(migrar, migrations.RunPython.noop)]
