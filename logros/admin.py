from django.contrib import admin

from .models import Canje, Logro


@admin.register(Logro)
class LogroAdmin(admin.ModelAdmin):
    list_display = ("usuario", "clave", "referencia", "puntos", "creado")
    list_filter = ("clave",)
    search_fields = ("usuario__email",)
    raw_id_fields = ("usuario",)


@admin.register(Canje)
class CanjeAdmin(admin.ModelAdmin):
    list_display = ("usuario", "codigo", "puntos", "creado")
    search_fields = ("usuario__email", "codigo__codigo")
    raw_id_fields = ("usuario", "codigo")
