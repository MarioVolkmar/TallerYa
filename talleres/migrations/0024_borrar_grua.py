"""Las grúas pasaron a proveedores.Proveedor (categoría «grua»); los datos se copiaron en proveedores 0002."""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("talleres", "0023_token_vence_y_aviso_precios"), ("proveedores", "0002_datos_desde_grua_y_cda")]
    operations = [migrations.DeleteModel(name="Grua")]
