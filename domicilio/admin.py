from django.contrib import admin, messages

from .estados import cambiar_estado
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .models import FotoTrabajo, MecanicoDomicilio, PrecioMecanico, ResenaMecanico, TallerDomicilio, TipoServicio, Zona


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
    fields = ("nombre", "estrellas", "comentario", "respuesta", "visible", "creado")
    readonly_fields = ("nombre", "estrellas", "comentario", "creado")


class FotoTrabajoInline(admin.TabularInline):
    model = FotoTrabajo
    extra = 0
    fields = ("vista", "imagen", "creado")
    readonly_fields = ("vista", "creado")

    @admin.display(description="Foto")
    def vista(self, obj):
        return format_html('<img src="{}" width="120" style="border-radius:6px">', obj.imagen.url) if obj.imagen else ""


class PrecioInline(admin.TabularInline):
    model = PrecioMecanico
    extra = 0


@admin.register(MecanicoDomicilio)
class MecanicoDomicilioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "whatsapp", "estado", "verificado", "urgencias", "anios_experiencia", "creado")
    list_filter = ("estado", "verificado", "urgencias", "zonas", "servicios")
    list_editable = ("verificado",)
    search_fields = ("nombre", "whatsapp", "usuario__email", "descripcion")
    filter_horizontal = ("zonas", "servicios", "marcas")
    readonly_fields = ("slug", "creado", "actualizado", "cedula", "verificacion")
    raw_id_fields = ("usuario",)
    inlines = [FotoTrabajoInline, PrecioInline, ResenaInline]
    actions = ["aprobar", "suspender", "volver_a_pendiente"]
    fieldsets = (
        ("Moderación", {"fields": ("estado", "verificado", "nota_al_mecanico", "notas_admin")}),
        ("Verificación", {"fields": ("cedula", "referencias", "verificacion"),
                          "description": "La cédula no se guarda completa: pide al mecánico que la muestre (video o en "
                                         "persona) y coteja los 4 últimos dígitos."}),
        ("Perfil", {"fields": ("usuario", "nombre", "slug", "foto", "whatsapp", "descripcion", "anios_experiencia",
                               "horario", "urgencias", "tarifa_visita")}),
        ("Dónde y qué", {"fields": ("zonas", "servicios", "marcas")}),
        ("Fechas", {"fields": ("creado", "actualizado")}),
    )

    @admin.display(description="Cédula")
    def cedula(self, obj):
        if not obj.cedula_huella:
            return "No la ha registrado"
        otros = MecanicoDomicilio.objects.filter(cedula_huella=obj.cedula_huella).exclude(pk=obj.pk)
        aviso = f" ⚠ La misma cédula está en otro perfil: {', '.join(m.nombre for m in otros[:3])}" if otros else ""
        return f"Termina en {obj.cedula_ultimos}{aviso}"

    @admin.display(description="Lista del perfil")
    def verificacion(self, obj):
        return format_html_join(mark_safe("<br>"), "{} {}",
                                (("✔" if hecho else "✗", texto) for texto, hecho, _ in obj.pasos()))

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


@admin.register(TallerDomicilio)
class TallerDomicilioAdmin(admin.ModelAdmin):
    """Servicio a domicilio de los talleres. Se publica si está activo y el taller está aprobado (Taller.activo)."""
    list_display = ("taller", "activo", "urgencias", "tarifa_visita", "actualizado")
    list_filter = ("activo", "urgencias", "zonas")
    list_editable = ("activo",)
    search_fields = ("taller__nombre",)
    raw_id_fields = ("taller",)
    filter_horizontal = ("zonas", "servicios")


@admin.register(ResenaMecanico)
class ResenaMecanicoAdmin(admin.ModelAdmin):
    list_display = ("mecanico", "nombre", "estrellas", "visible", "creado")
    list_filter = ("visible", "estrellas")
    list_editable = ("visible",)
    search_fields = ("mecanico__nombre", "nombre", "comentario")
    raw_id_fields = ("mecanico", "usuario")
