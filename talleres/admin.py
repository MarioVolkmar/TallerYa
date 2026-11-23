from django import forms
from django.contrib import admin

from .models import Barrio, FotoTaller, HorarioTaller, Marca, Resena, Servicio, SolicitudCita, Taller

admin.site.register([Barrio, Servicio, Marca])


class HorarioTallerInline(admin.TabularInline):
    model = HorarioTaller
    extra = 0


class FotoTallerInline(admin.TabularInline):
    model = FotoTaller
    extra = 0
    fields = ("imagen", "video", "descripcion", "orden")


class TallerAdminForm(forms.ModelForm):
    class Meta:
        model = Taller
        fields = "__all__"

    def clean_activo(self):
        activo = self.cleaned_data.get("activo")
        if activo and self.instance.pk and self.instance.falta_aprobacion:
            raise forms.ValidationError("El taller aún no aprobó su ficha (Ley 1581): no se puede publicar.")
        return activo


@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    form = TallerAdminForm
    inlines = [HorarioTallerInline, FotoTallerInline]
    list_display = ("nombre", "barrio", "nivel_precio", "verificado", "activo", "destacado", "creado")
    list_filter = ("verificado", "activo", "destacado", "barrio")
    list_editable = ("verificado", "activo", "destacado")
    search_fields = ("nombre", "responsable", "direccion")
    filter_horizontal = ("servicios", "marcas")
    readonly_fields = ("slug", "tiene_pin")
    raw_id_fields = ("usuario",)
    actions = ["regenerar_pin"]

    @admin.display(boolean=True, description="Tiene PIN de canje")
    def tiene_pin(self, obj):
        return obj.tiene_pin

    @admin.action(description="Generar nuevo PIN de canje (se muestra una sola vez)")
    def regenerar_pin(self, request, queryset):
        """Solo se guarda el hash: el PIN en claro se ve aquí una vez para dárselo al taller. El taller también
        puede generarlo él mismo en Mi taller."""
        nuevos = [f"{t.nombre}: {t.nuevo_pin()}" for t in queryset]
        self.message_user(request, "PIN nuevos (anótalos ahora, no se vuelven a mostrar): " + " · ".join(nuevos))


@admin.register(SolicitudCita)
class SolicitudCitaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "taller", "moto", "fecha_preferida", "hora", "estado", "creado")
    raw_id_fields = ("usuario",)
    list_filter = ("estado", "taller")
    list_editable = ("estado",)


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ("taller", "nombre", "estrellas", "visible", "creado")
    list_filter = ("visible", "estrellas")
    list_editable = ("visible",)


from .models import EventoDiario  # noqa: E402


@admin.register(EventoDiario)
class EventoDiarioAdmin(admin.ModelAdmin):
    list_display = ("taller", "fecha", "tipo", "cantidad")
    list_filter = ("tipo",)
    date_hierarchy = "fecha"
    raw_id_fields = ("taller",)
