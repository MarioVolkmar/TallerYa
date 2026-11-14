from django.db import migrations

# Zonas de partida por municipio. En Medellín: sus 16 comunas y 5 corregimientos. En los demás municipios, sectores
# conocidos. Se pueden agregar más desde el admin (Barrios).
ZONAS = {
    "Medellín": ["Popular", "Santa Cruz", "Manrique", "Aranjuez", "Castilla", "Doce de Octubre", "Robledo", "Villa Hermosa",
                 "Buenos Aires", "Centro", "Laureles", "La América", "San Javier", "El Poblado", "Guayabal", "Belén",
                 "San Antonio de Prado", "San Cristóbal", "Altavista", "Santa Elena", "Palmitas"],
    "Bello": ["Centro", "Niquía", "París", "Zamora", "Cabañas", "La Madera", "Fontidueño", "Santa Ana", "Pachelly"],
    "Itagüí": ["Centro", "Santa María", "San Pío X", "Ditaires", "Suramérica", "Simón Bolívar", "Calatrava"],
    "Envigado": ["Centro", "Zúñiga", "La Magnolia", "Alcalá", "El Portal", "San Marcos", "Las Antillas", "Obrero"],
    "Sabaneta": ["Centro", "Calle Larga", "Aliadas del Sur", "Holanda", "Prados de Sabaneta", "María Auxiliadora"],
    "La Estrella": ["Centro", "La Tablaza", "Pueblo Viejo"],
    "Caldas": ["Centro"],
    "Copacabana": ["Centro"],
    "Girardota": ["Centro"],
    "Barbosa": ["Centro"],
}
# Antes había "barrios" que en realidad eran municipios: pasan a ser el Centro de ese municipio.
MUNICIPIOS_COMO_BARRIO = ["Bello", "Envigado", "Itagüí"]


def cargar(apps, schema_editor):
    Barrio = apps.get_model("talleres", "Barrio")
    for municipio in MUNICIPIOS_COMO_BARRIO:
        viejo = Barrio.objects.filter(nombre=municipio, ciudad="Medellín").first()
        if viejo:
            destino = Barrio.objects.filter(nombre="Centro", ciudad=municipio).first()
            if destino:
                viejo.talleres.update(barrio=destino)
                viejo.delete()
            else:
                viejo.nombre, viejo.ciudad = "Centro", municipio
                viejo.save()
    for ciudad, zonas in ZONAS.items():
        for nombre in zonas:
            Barrio.objects.get_or_create(nombre=nombre, ciudad=ciudad)


class Migration(migrations.Migration):
    dependencies = [("talleres", "0007_barrios_por_ciudad")]
    operations = [migrations.RunPython(cargar, migrations.RunPython.noop)]
