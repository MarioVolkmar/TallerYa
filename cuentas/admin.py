from django.conf import settings
from django.contrib import admin

from .models import Suscripcion


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ("motociclista", "estado", "inicia", "vence", "referencia_pago", "creado")
    list_filter = ("estado",)
    search_fields = ("motociclista__nombre", "motociclista__celular", "motociclista__usuario__email", "referencia_pago")
    raw_id_fields = ("motociclista",)
    readonly_fields = ("creado", "actualizado")
    actions = ["activar_un_mes", "cancelar"]

    @admin.action(description=f"Activar / renovar Plus por {settings.PLUS_DIAS} días")
    def activar_un_mes(self, request, queryset):
        for s in queryset.select_related("motociclista"):
            s.activar()
        self.message_user(request, f"{queryset.count()} suscripción(es) activadas.")

    @admin.action(description="Cancelar suscripción")
    def cancelar(self, request, queryset):
        n = queryset.update(estado=Suscripcion.Estado.CANCELADA)
        self.message_user(request, f"{n} suscripción(es) canceladas.")
