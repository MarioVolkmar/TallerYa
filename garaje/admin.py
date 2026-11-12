from django.contrib import admin

from .models import LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento


@admin.register(LineaMoto)
class LineaMotoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tipo", "cilindraje", "transmision", "refrigeracion", "freno_delantero",
                    "freno_trasero", "suspension_trasera", "rin_delantero", "rin_trasero", "activo")
    list_filter = ("marca", "tipo", "transmision", "refrigeracion", "activo")
    list_editable = ("activo",)
    search_fields = ("nombre", "marca__nombre")


@admin.register(TareaMantenimiento)
class TareaMantenimientoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "pieza", "aplica", "intervalo_km", "intervalo_dias", "servicio", "hazlo_tu", "orden", "activo")
    list_editable = ("intervalo_km", "intervalo_dias", "orden", "activo")
    list_filter = ("pieza", "aplica", "activo")
    prepopulated_fields = {"clave": ("nombre",)}


class LecturaInline(admin.TabularInline):
    model = LecturaKm
    extra = 0


class MantenimientoInline(admin.TabularInline):
    model = Mantenimiento
    extra = 0
    raw_id_fields = ("taller",)


@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "motociclista", "km_actual", "creado")
    list_filter = ("linea__marca", "linea__tipo")
    search_fields = ("linea__nombre", "marca_otra", "linea_otra", "motociclista__nombre", "motociclista__celular")
    raw_id_fields = ("motociclista",)
    inlines = [LecturaInline, MantenimientoInline]
