from datetime import timedelta

from django.db import migrations
from django.utils import timezone

CONSEJOS = [
    ("Revisa la presión de las llantas cada semana", "consejo",
     "Una llanta baja frena peor, se calienta, gasta más gasolina y se desgasta por los bordes.",
     "La presión correcta está en el manual o en una calcomanía en el basculante o la cadena de tu moto. "
     "Mídela con las llantas frías, antes de rodar, y ajústala si vas con parrillero o con carga.\n\n"
     "Revisa también que no tengan cortes, objetos clavados ni la banda gastada: el labrado debe verse parejo en toda la llanta."),
    ("Antes de salir: la revisión de un minuto", "consejo",
     "Luces, frenos, llantas y cadena. Un vistazo rápido antes de rodar evita muchos sustos.",
     "Prende la moto y revisa luz alta, baja, stop y direccionales. Aprieta las dos manijas de freno: deben sentirse firmes, "
     "no esponjosas.\n\nMira la cadena (que no esté seca ni muy suelta) y el estado de las llantas. Si algo no se ve bien, "
     "mejor llevarla al taller antes de que el problema crezca."),
    ("Ten tus documentos al día", "transito",
     "El SOAT y la revisión técnico-mecánica son obligatorios para circular en Colombia. En Mi garaje puedes registrar sus fechas y te avisamos.",
     "Circular sin SOAT o sin la revisión técnico-mecánica vigente (cuando aplica) puede traer multa e inmovilización de la moto. "
     "Además, el SOAT es el que cubre la atención médica en caso de accidente.\n\n"
     "Registra las fechas de vencimiento en Mi garaje y TallerYa te recuerda con tiempo, para que no te coja la tarde."),
]


def cargar(apps, schema_editor):
    Articulo = apps.get_model("noticias", "Articulo")
    ahora = timezone.now()
    for i, (titulo, categoria, resumen, cuerpo) in enumerate(CONSEJOS):
        from django.utils.text import slugify
        Articulo.objects.get_or_create(slug=slugify(titulo), defaults=dict(
            titulo=titulo, categoria=categoria, resumen=resumen, cuerpo=cuerpo, fecha=ahora - timedelta(days=i)))


def quitar(apps, schema_editor):
    from django.utils.text import slugify
    apps.get_model("noticias", "Articulo").objects.filter(slug__in=[slugify(c[0]) for c in CONSEJOS]).delete()


class Migration(migrations.Migration):
    dependencies = [("noticias", "0001_initial")]
    operations = [migrations.RunPython(cargar, quitar)]
