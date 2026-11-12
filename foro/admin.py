from django.contrib import admin
from django.db.models import Count, Q

from .models import Pregunta, Reporte, Respuesta


class RespuestaInline(admin.TabularInline):
    model = Respuesta
    fields = ("autor", "cuerpo", "visible", "creado")
    readonly_fields = ("autor", "creado")
    extra = 0


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "marca", "num_respuestas", "reportes_pendientes", "visible", "creado")
    list_filter = ("visible", "marca")
    list_editable = ("visible",)
    search_fields = ("titulo", "cuerpo", "autor__email")
    raw_id_fields = ("autor", "mejor_respuesta")
    inlines = [RespuestaInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("autor", "marca").annotate(
            _respuestas=Count("respuestas", distinct=True),
            _reportes=Count("reportes", filter=Q(reportes__revisado=False), distinct=True),
        )

    @admin.display(description="Respuestas", ordering="_respuestas")
    def num_respuestas(self, obj):
        return obj._respuestas

    @admin.display(description="Reportes", ordering="_reportes")
    def reportes_pendientes(self, obj):
        return obj._reportes


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "autor", "visible", "creado")
    list_filter = ("visible",)
    list_editable = ("visible",)
    search_fields = ("cuerpo", "autor__email", "pregunta__titulo")
    raw_id_fields = ("autor", "pregunta")


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ("objetivo", "usuario", "motivo", "revisado", "creado")
    list_filter = ("revisado",)
    list_editable = ("revisado",)
    raw_id_fields = ("usuario", "pregunta", "respuesta")
    actions = ["ocultar_y_revisar", "restaurar_y_revisar"]

    @admin.action(description="Ocultar la publicación y marcar como revisado")
    def ocultar_y_revisar(self, request, queryset):
        for r in queryset:
            r.objetivo.visible = False
            r.objetivo.save(update_fields=["visible"])
        queryset.update(revisado=True)

    @admin.action(description="Volver a mostrar la publicación y marcar como revisado")
    def restaurar_y_revisar(self, request, queryset):
        for r in queryset:
            r.objetivo.visible = True
            r.objetivo.save(update_fields=["visible"])
        queryset.update(revisado=True)
