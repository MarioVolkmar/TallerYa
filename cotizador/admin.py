from django.contrib import admin

from .models import Cotizacion


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ("consulta", "moto", "minimo", "tipico", "maximo", "fuente", "pedidos", "consultado_en")
    list_filter = ("fuente",)
    search_fields = ("consulta", "codigo", "nombre", "moto")
    readonly_fields = [f.name for f in Cotizacion._meta.fields]
