from django.contrib import admin

from .models import Articulo, FuenteNoticias


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "fuente", "fecha", "publicado")
    list_filter = ("categoria", "publicado", "origen")
    list_editable = ("publicado",)
    search_fields = ("titulo", "resumen", "cuerpo")
    prepopulated_fields = {"slug": ("titulo",)}


@admin.register(FuenteNoticias)
class FuenteNoticiasAdmin(admin.ModelAdmin):
    list_display = ("nombre", "url", "solo_motos", "internacional", "activa", "ultima_lectura", "ultimo_error")
    list_editable = ("activa",)
