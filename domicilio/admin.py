from django.contrib import admin, messages

from .estados import cambiar_estado
from .models import MecanicoDomicilio, ResenaMecanico, TipoServicio, Zona


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciudad", "orden")
    list_editable = ("orden",)


@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "orden")
    list_editable = ("orden",)


class ResenaInline(admin.TabularInline):
    model = ResenaMecanico
    extra = 0
    fields = ("nombre", "estrellas", "comentario", "visible", "creado")
    readonly_fields = ("nombre", "estrellas", "comentario", "creado")


@admin.register(MecanicoDomicilio)
class MecanicoDomicilioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "whatsapp", "estado", "verificado", "urgencias", "anios_experiencia", "creado")
    list_filter = ("estado", "verificado", "urgencias", "zonas", "servicios")
    list_editable = ("verificado",)
    search_fields = ("nombre", "whatsapp", "usuario__email", "descripcion")
    filter_horizontal = ("zonas", "servicios", "marcas")
    readonly_fields = ("slug", "creado", "actualizado")
    raw_id_fields = ("usuario",)
    inlines = [ResenaInline]
    actions = ["aprobar", "suspender", "volver_a_pendiente"]
    fieldsets = (
        ("Moderación", {"fields": ("estado", "verificado", "notas_admin")}),
        ("Perfil", {"fields": ("usuario", "nombre", "slug", "foto", "whatsapp", "descripcion", "anios_experiencia",
                               "horario", "urgencias", "tarifa_visita")}),
        ("Dónde y qué", {"fields": ("zonas", "servicios", "marcas")}),
        ("Fechas", {"fields": ("creado", "actualizado")}),
    )

    def save_model(self, request, obj, form, change):
        # Si el estado cambió desde el formulario, se guarda igual pero pasando por cambiar_estado (avisa al mecánico)
        nuevo = obj.estado
        if change and "estado" in form.changed_data:
            obj.estado = form.initial.get("estado")
            super().save_model(request, obj, form, change)
            cambiar_estado(obj, nuevo)
        else:
            super().save_model(request, obj, form, change)

    def _cambiar(self, request, queryset, estado, texto):
        n = sum(cambiar_estado(m, estado) for m in queryset)
        self.message_user(request, f"{n} perfil{'es' if n != 1 else ''} {texto}.", messages.SUCCESS)

    @admin.action(description="Aprobar (publicar en el listado)")
    def aprobar(self, request, queryset):
        self._cambiar(request, queryset, MecanicoDomicilio.Estado.APROBADO, "aprobado(s)")

    @admin.action(description="Suspender (sacar del listado)")
    def suspender(self, request, queryset):
        self._cambiar(request, queryset, MecanicoDomicilio.Estado.SUSPENDIDO, "suspendido(s)")

    @admin.action(description="Volver a pendiente de revisión")
    def volver_a_pendiente(self, request, queryset):
        self._cambiar(request, queryset, MecanicoDomicilio.Estado.PENDIENTE, "pendiente(s)")


@admin.register(ResenaMecanico)
class ResenaMecanicoAdmin(admin.ModelAdmin):
    list_display = ("mecanico", "nombre", "estrellas", "visible", "creado")
    list_filter = ("visible", "estrellas")
    list_editable = ("visible",)
    search_fields = ("mecanico__nombre", "nombre", "comentario")
    raw_id_fields = ("mecanico", "usuario")
