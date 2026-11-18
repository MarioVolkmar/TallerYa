from django.contrib import admin

from .models import Jornada, PerfilDomiciliario, TallerAliado


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
    list_display = ("taller", "en_el_dia", "horario_extendido", "descuento", "activo", "orden")
    list_editable = ("activo", "orden")
    raw_id_fields = ("taller",)
