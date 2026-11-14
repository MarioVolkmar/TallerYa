from django.contrib import admin

from .models import Barrio, FotoTaller, Marca, Resena, Servicio, SolicitudCita, Taller

admin.site.register([Barrio, Servicio, Marca])


class FotoTallerInline(admin.TabularInline):
    model = FotoTaller
    extra = 0
    fields = ("imagen", "descripcion", "orden")


@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    inlines = [FotoTallerInline]
    list_display = ("nombre", "barrio", "verificado", "activo", "destacado", "creado")
    list_filter = ("verificado", "activo", "destacado", "barrio")
    list_editable = ("verificado", "activo", "destacado")
    search_fields = ("nombre", "responsable", "direccion")
    filter_horizontal = ("servicios", "marcas")
    readonly_fields = ("slug", "pin_canje")
    raw_id_fields = ("usuario",)
    actions = ["regenerar_pin"]

    @admin.action(description="Generar nuevo PIN de canje")
    def regenerar_pin(self, request, queryset):
        for taller in queryset:
            taller.pin_canje = Taller.generar_pin()
            taller.save(update_fields=["pin_canje"])
        self.message_user(request, f"PIN regenerado para {queryset.count()} taller(es).")


@admin.register(SolicitudCita)
class SolicitudCitaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "taller", "moto", "fecha_preferida", "estado", "creado")
    list_filter = ("estado", "taller")
    list_editable = ("estado",)


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ("taller", "nombre", "estrellas", "visible", "creado")
    list_filter = ("visible", "estrellas")
    list_editable = ("visible",)
