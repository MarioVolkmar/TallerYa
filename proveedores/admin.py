from django.contrib import admin

from .models import Categoria, EventoProveedor, Proveedor


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "icono", "inscripcion", "orden")
    list_editable = ("orden",)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "municipio", "estado", "verificado", "aliado", "origen_alta")
    list_filter = ("categoria", "estado", "verificado", "aliado", "origen_alta", "demo")
    search_fields = ("nombre", "whatsapp", "telefono", "responsable")
    readonly_fields = ("token_revision", "token_creado", "aprobado_por_proveedor", "aprobado_ip", "creado", "actualizado")


@admin.register(EventoProveedor)
class EventoProveedorAdmin(admin.ModelAdmin):
    list_display = ("proveedor", "fecha", "tipo", "cantidad")
    list_filter = ("tipo",)
