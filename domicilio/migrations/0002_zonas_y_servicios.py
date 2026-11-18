"""Listas fijas de zonas (16 comunas de Medellín, sus corregimientos y los otros 9 municipios del Valle de Aburrá)
y de servicios que se pueden hacer donde está la moto. Se pueden ajustar luego desde el admin."""
from django.db import migrations

COMUNAS = ["Popular", "Santa Cruz", "Manrique", "Aranjuez", "Castilla", "Doce de Octubre", "Robledo", "Villa Hermosa",
           "Buenos Aires", "La Candelaria (Centro)", "Laureles-Estadio", "La América", "San Javier", "El Poblado",
           "Guayabal", "Belén", "Corregimientos de Medellín"]
MUNICIPIOS = ["Bello", "Itagüí", "Envigado", "Sabaneta", "La Estrella", "Caldas", "Copacabana", "Girardota", "Barbosa"]
SERVICIOS = ["Mantenimiento general", "Cambio de aceite", "Frenos", "Sistema eléctrico", "Batería y arranque",
             "Llantas y despinche", "Diagnóstico", "Carburación", "Inyección electrónica", "Kit de arrastre",
             "Suspensión", "Revisión antes de comprar moto usada"]


def sembrar(apps, schema_editor):
    Zona = apps.get_model("domicilio", "Zona")
    TipoServicio = apps.get_model("domicilio", "TipoServicio")
    for i, nombre in enumerate(COMUNAS):
        Zona.objects.get_or_create(nombre=nombre, ciudad="Medellín", defaults={"orden": i})
    for i, ciudad in enumerate(MUNICIPIOS, start=len(COMUNAS)):
        Zona.objects.get_or_create(nombre=ciudad, ciudad=ciudad, defaults={"orden": i})
    for i, nombre in enumerate(SERVICIOS):
        TipoServicio.objects.get_or_create(nombre=nombre, defaults={"orden": i})


class Migration(migrations.Migration):
    dependencies = [("domicilio", "0001_initial")]
    operations = [migrations.RunPython(sembrar, migrations.RunPython.noop)]
