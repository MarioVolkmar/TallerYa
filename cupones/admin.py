from django.contrib import admin
from django.db.models import Count, Q

from .models import CodigoCupon, Cupon, Motociclista


@admin.register(Cupon)
class CuponAdmin(admin.ModelAdmin):
    list_display = ("titulo", "donde", "valido_hasta", "cupo", "emitidos", "canjeados", "activo", "publico", "solo_plus", "regalo_mensual", "premio_referido")
    list_filter = ("activo", "publico", "solo_plus", "regalo_mensual", "premio_referido", "taller")
    list_editable = ("activo",)
    search_fields = ("titulo", "taller__nombre")
    autocomplete_fields = ("taller",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("taller").annotate(
            _emitidos=Count("codigos"),
            _canjeados=Count("codigos", filter=Q(codigos__canjeado_en__isnull=False)),
        )

    @admin.display(description="Taller")
    def donde(self, obj):
        return obj.taller or "Todos los talleres"

    @admin.display(description="Entregados", ordering="_emitidos")
    def emitidos(self, obj):
        return obj._emitidos

    @admin.display(description="Canjeados", ordering="_canjeados")
    def canjeados(self, obj):
        return obj._canjeados


@admin.register(CodigoCupon)
class CodigoCuponAdmin(admin.ModelAdmin):
    list_display = ("codigo", "cupon", "motociclista", "origen", "creado", "canjeado_en", "canjeado_taller")
    list_filter = ("origen", ("canjeado_en", admin.EmptyFieldListFilter), "cupon")
    search_fields = ("codigo", "motociclista__celular", "motociclista__nombre")
    readonly_fields = ("codigo", "creado")
    raw_id_fields = ("motociclista", "referido")
    list_select_related = ("cupon", "cupon__taller", "motociclista", "canjeado_taller")


class ReferidoInline(admin.TabularInline):
    model = Motociclista
    fk_name = "referido_por"
    fields = ("nombre", "celular", "premio_otorgado", "creado")
    readonly_fields = fields
    extra = 0
    can_delete = False
    verbose_name_plural = "Amigos que invitó"


@admin.register(Motociclista)
class MotociclistaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "celular", "usuario", "codigo_referido", "referido_por", "num_referidos", "creado")
    search_fields = ("nombre", "celular", "codigo_referido", "usuario__email")
    readonly_fields = ("codigo_referido", "creado")
    raw_id_fields = ("referido_por", "usuario")
    inlines = [ReferidoInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("referido_por").annotate(_referidos=Count("referidos"))

    @admin.display(description="Referidos", ordering="_referidos")
    def num_referidos(self, obj):
        return obj._referidos
