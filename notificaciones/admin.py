from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "usuario", "tipo", "leida", "creada")
    list_filter = ("tipo", "leida")
    search_fields = ("titulo", "usuario__email")
    raw_id_fields = ("usuario",)
