from django.db import migrations

# Fuentes con RSS público verificado. Los medios generales se filtran: solo entra lo que hable de motos, tránsito o trámites.
FUENTES = [
    ("El Colombiano · Medellín", "https://www.elcolombiano.com/rss/medellin.xml", "https://www.elcolombiano.com", True, False),
    ("El Colombiano · Colombia", "https://www.elcolombiano.com/rss/colombia.xml", "https://www.elcolombiano.com", True, False),
    ("La República", "https://www.larepublica.co/rss/", "https://www.larepublica.co", True, False),
    ("Motorpasión Moto", "https://www.motorpasionmoto.com/index.xml", "https://www.motorpasionmoto.com", True, True),
]


def cargar(apps, schema_editor):
    Fuente = apps.get_model("noticias", "FuenteNoticias")
    for nombre, url, sitio, solo_motos, internacional in FUENTES:
        Fuente.objects.get_or_create(url=url, defaults=dict(nombre=nombre, sitio=sitio, solo_motos=solo_motos, internacional=internacional))
    apps.get_model("noticias", "Articulo").objects.filter(categoria="noticia").update(categoria="actualidad")
    # Los textos propios iniciales son consejos, no noticias.
    apps.get_model("noticias", "Articulo").objects.filter(slug="ten-tus-documentos-al-dia").update(categoria="consejo")


def quitar(apps, schema_editor):
    apps.get_model("noticias", "FuenteNoticias").objects.filter(url__in=[f[1] for f in FUENTES]).delete()


class Migration(migrations.Migration):
    dependencies = [("noticias", "0003_noticiero")]
    operations = [migrations.RunPython(cargar, quitar)]
