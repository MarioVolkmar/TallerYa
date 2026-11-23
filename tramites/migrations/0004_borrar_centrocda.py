"""Los CDA pasaron a proveedores.Proveedor (categoría «cda»); los datos se copiaron en proveedores 0002."""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("tramites", "0003_pedido_soat"), ("proveedores", "0002_datos_desde_grua_y_cda")]
    operations = [migrations.DeleteModel(name="CentroCDA")]
