"""Tarifas oficiales del SOAT 2026 para motos y los primeros CDA (datos públicos de sus sitios, nov. 2026)."""
from django.db import migrations

FUENTE_SOAT = "https://www.fasecolda.com/wp-content/uploads/Tarifas-SOAT-2026-referencia.pdf"
NOTA_SOAT = ("Tarifa máxima 2026 (Circular 022 de 2025 de la Superfinanciera); "
             "incluye la contribución a la ADRES y la tasa RUNT")
TARIFAS = (("moto_100", 256200), ("moto_100_200", 343300), ("moto_200", 761400))
FUENTE_CDA = "Desde · según su sitio web (nov. 2026); varía con el modelo"
CDAS = (
    ("CDA Glorieta Guayabal", dict(
        municipio="Medellín", direccion="Carrera 52 (Av. Guayabal) #9A-25", telefono="3013176894",
        sitio_web="https://cdaglorietaguayabal.com.co/",
        horario="Lun a sáb 6:00 a. m. a 8:00 p. m. · Dom y festivos 7:00 a. m. a 2:00 p. m.",
        precio_moto=240817, precio_fuente=FUENTE_CDA)),
    ("CDA Servisuper Medellín", dict(
        municipio="Medellín", direccion="Calle 80 #51C-35, Aranjuez (cerca al Jardín Botánico)",
        telefono="3007049580", whatsapp="573007049580", sitio_web="https://cdaservisuper.com/",
        precio_moto=242200, precio_fuente=FUENTE_CDA)),
)


def cargar(apps, schema_editor):
    TarifaSoat = apps.get_model("tramites", "TarifaSoat")
    CentroCDA = apps.get_model("tramites", "CentroCDA")
    for categoria, valor in TARIFAS:
        TarifaSoat.objects.update_or_create(anio=2026, categoria=categoria,
                                            defaults={"valor": valor, "fuente": FUENTE_SOAT, "nota": NOTA_SOAT})
    for nombre, datos in CDAS:
        CentroCDA.objects.get_or_create(nombre=nombre, defaults=datos)


class Migration(migrations.Migration):
    dependencies = [("tramites", "0001_initial")]
    operations = [migrations.RunPython(cargar, migrations.RunPython.noop)]
