"""Categorías iniciales (Grúas, CDA, SOAT) y copia de las grúas (talleres.Grua) y los CDA (tramites.CentroCDA)
al modelo Proveedor, sin perder nada de lo que veía el motero. Después talleres y tramites borran sus modelos viejos."""
from django.db import migrations

CATEGORIAS = (
    ("grua", dict(nombre="Grúas", singular="Grúa", icono="🚚", orden=1, campos=["vehiculo"],
                  etiqueta_precio="Tarifa base desde", descripcion="Grúas y planchones que recogen motos varadas")),
    ("cda", dict(nombre="CDA (técnico-mecánica)", singular="CDA", icono="🔧", orden=2, campos=["agenda"],
                 etiqueta_precio="Revisión de moto desde", descripcion="Centros de diagnóstico automotor")),
    ("soat", dict(nombre="SOAT", singular="Punto de SOAT", icono="🛡️", orden=3, campos=[],
                  etiqueta_precio="Precio de referencia desde", descripcion="Agencias y puntos de venta del SOAT")),
)


def copiar(apps, schema_editor):
    Categoria = apps.get_model("proveedores", "Categoria")
    Proveedor = apps.get_model("proveedores", "Proveedor")
    Grua = apps.get_model("talleres", "Grua")
    CentroCDA = apps.get_model("tramites", "CentroCDA")
    cats = {}
    for slug, datos in CATEGORIAS:
        cats[slug], _ = Categoria.objects.get_or_create(slug=slug, defaults=datos)
    for g in Grua.objects.all():
        Proveedor.objects.create(
            categoria=cats["grua"], nombre=g.nombre, telefono=g.telefono, whatsapp=g.whatsapp, zonas=g.municipios or [],
            abierto_24h=g.abierto_24h, abre=g.abre, cierra=g.cierra, precio_desde=g.tarifa_desde,
            extras={"vehiculo": g.vehiculo}, latitud=g.latitud, longitud=g.longitud, demo=g.demo,
            estado="publicado" if g.activo else "pausado", origen_alta="equipo")
    for c in CentroCDA.objects.all():
        Proveedor.objects.create(
            categoria=cats["cda"], nombre=c.nombre, municipio=c.municipio, zonas=[c.municipio] if c.municipio else [],
            direccion=c.direccion, telefono=c.telefono, whatsapp=c.whatsapp, sitio_web=c.sitio_web, horario=c.horario,
            precio_desde=c.precio_moto, precio_fuente=c.precio_fuente, aliado=c.aliado, beneficio=c.beneficio,
            estado="publicado" if c.activo else "pausado", origen_alta="equipo")


class Migration(migrations.Migration):
    dependencies = [
        ("proveedores", "0001_initial"),
        ("talleres", "0023_token_vence_y_aviso_precios"),
        ("tramites", "0003_pedido_soat"),
    ]
    operations = [migrations.RunPython(copiar, migrations.RunPython.noop)]
