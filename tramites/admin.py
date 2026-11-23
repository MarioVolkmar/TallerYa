from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .models import PedidoSoat, TarifaSoat


@admin.register(TarifaSoat)
class TarifaSoatAdmin(admin.ModelAdmin):
    list_display = ("anio", "categoria", "valor", "fuente")
    list_filter = ("anio", "categoria")


def _accion(estado):
    def accion(modeladmin, request, queryset):
        n = 0
        for pedido in queryset.exclude(estado=estado):
            if estado == PedidoSoat.Estado.LISTA_PAGAR and not pedido.valor:
                continue
            pedido.cambiar_estado(estado)
            n += 1
        modeladmin.message_user(request, f"{n} pedido(s) pasaron a «{PedidoSoat.Estado(estado).label}».", messages.SUCCESS)
    accion.__name__ = f"pasar_a_{estado}"
    accion.short_description = f"Pasar a «{PedidoSoat.Estado(estado).label}»"
    return accion


@admin.register(PedidoSoat)
class PedidoSoatAdmin(admin.ModelAdmin):
    """Cola del equipo: se pega el enlace de pago, se sube la póliza y se cambia el estado (con avisos al motero)."""
    list_display = ("creado", "placa", "linea", "nombre_completo", "valor", "estado")
    list_filter = ("estado",)
    search_fields = ("placa", "numero_documento", "nombre_completo", "correo")
    date_hierarchy = "creado"
    actions = [_accion(e) for e in (PedidoSoat.Estado.EN_PROCESO, PedidoSoat.Estado.LISTA_PAGAR,
                                    PedidoSoat.Estado.EMITIDA, PedidoSoat.Estado.CANCELADA)]
    readonly_fields = ("moto", "placa", "linea", "cilindraje", "categoria", "valor", "acepta_datos_en",
                       "ver_tarjeta", "ver_poliza", "pago_simulado", "creado", "pagado_en", "emitido_en")
    exclude = ("tarjeta_propiedad",)
    fieldsets = (
        ("Estado", {"fields": ("estado", "notas_internas")}),
        ("Moto", {"fields": ("moto", "placa", "linea", "cilindraje", "categoria", "valor")}),
        ("Tomador", {"fields": ("tipo_documento", "numero_documento", "nombre_completo", "chasis_motor",
                                "ver_tarjeta", "correo", "direccion", "celular", "acepta_datos_en")}),
        ("Póliza y pago", {"fields": ("enlace_pago", "poliza", "ver_poliza", "numero_poliza", "inicio_vigencia",
                                      "pago_simulado", "pagado_en", "emitido_en")}),
        ("Fechas", {"fields": ("creado",)}),
    )

    @admin.display(description="tarjeta de propiedad")
    def ver_tarjeta(self, obj):
        if not obj.tarjeta_propiedad:
            return "—"
        return format_html('<a href="{}" target="_blank" rel="noopener">Ver archivo</a>', reverse("tramites:tarjeta", args=[obj.pk]))

    @admin.display(description="póliza actual")
    def ver_poliza(self, obj):
        if not obj.poliza:
            return "—"
        return format_html('<a href="{}" target="_blank" rel="noopener">Ver PDF</a>', reverse("tramites:poliza", args=[obj.pk]))

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # El almacén privado no tiene URL pública: subir sin el enlace "Actualmente" (se ve con "Ver PDF")
        if db_field.name == "poliza":
            from django import forms
            kwargs["widget"] = forms.FileInput(attrs={"accept": "application/pdf"})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # El cambio de estado pasa por cambiar_estado para que salgan los avisos y la fecha del SOAT
        if change and "estado" in form.changed_data:
            nuevo = obj.estado
            obj.estado = form.initial["estado"]
            super().save_model(request, obj, form, change)
            obj.cambiar_estado(nuevo)
        else:
            super().save_model(request, obj, form, change)
