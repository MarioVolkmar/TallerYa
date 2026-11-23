from django.contrib import admin

from .models import Jornada, PerfilDomiciliario, TallerAliado, Verificacion


@admin.register(PerfilDomiciliario)
class PerfilDomiciliarioAdmin(admin.ModelAdmin):
    list_display = ("motociclista", "km_semana", "dias_semana", "creado")
    search_fields = ("motociclista__nombre", "motociclista__usuario__email")
    raw_id_fields = ("motociclista", "moto")


@admin.register(Jornada)
class JornadaAdmin(admin.ModelAdmin):
    list_display = ("perfil", "fecha", "ingreso", "km_fin")
    date_hierarchy = "fecha"
    raw_id_fields = ("perfil",)


@admin.register(TallerAliado)
class TallerAliadoAdmin(admin.ModelAdmin):
    list_display = ("taller", "descuento", "activo", "orden")
    list_editable = ("activo", "orden")
    raw_id_fields = ("taller",)


@admin.register(Verificacion)
class VerificacionAdmin(admin.ModelAdmin):
    """Solo lectura del resultado: las fotos se revisan y deciden en la ficha del usuario en /consola/ (las borra al decidir)."""
    list_display = ("perfil", "plataforma", "estado", "vence", "renovaciones", "revisado_por", "creado")
    list_filter = ("estado", "plataforma")
    search_fields = ("perfil__motociclista__nombre", "perfil__motociclista__usuario__email")
    exclude = ("captura", "foto_moto")
    readonly_fields = ("perfil", "moto", "autorizacion", "revisado_por", "revisado_en", "creado")

    def has_add_permission(self, request):
        return False
