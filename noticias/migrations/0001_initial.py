import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Articulo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=140)),
                ("slug", models.SlugField(blank=True, max_length=160, unique=True)),
                ("categoria", models.CharField(choices=[("consejo", "Consejo"), ("transito", "Tránsito"), ("noticia", "Noticia")], default="consejo", max_length=10)),
                ("resumen", models.CharField(help_text="Una o dos frases: se ven en la tarjeta del inicio", max_length=220)),
                ("cuerpo", models.TextField(help_text="Texto completo. Separa los párrafos con una línea en blanco.")),
                ("imagen", models.ImageField(blank=True, upload_to="noticias/")),
                ("fuente", models.CharField(blank=True, help_text="Ej: Secretaría de Movilidad de Medellín", max_length=120)),
                ("fuente_url", models.URLField(blank=True)),
                ("lectura_min", models.PositiveSmallIntegerField(default=2, verbose_name="minutos de lectura")),
                ("publicado", models.BooleanField(default=True)),
                ("fecha", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"verbose_name": "artículo", "verbose_name_plural": "artículos", "ordering": ["-fecha"]},
        ),
    ]
