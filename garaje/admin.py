import json

from django.contrib import admin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path

from .models import (Despiece, Lamina, LecturaKm, LineaMoto, Mantenimiento, Moto, ParteDespiece,
                     TareaMantenimiento)


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


# ---------------------------------------------------------------------------
# Despiece y herramienta de marcado
# ---------------------------------------------------------------------------
@admin.register(Despiece)
class DespieceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "anio", "num_laminas", "activo")
    list_editable = ("activo",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_laminas=Count("laminas"))

    @admin.display(description="Láminas", ordering="_laminas")
    def num_laminas(self, obj):
        return obj._laminas


class ParteInline(admin.TabularInline):
    model = ParteDespiece
    fields = ("ref", "codigo", "descripcion", "nombre_es", "cantidad", "tarea", "marcada")
    readonly_fields = ("marcada",)  # x/y se editan solo con la herramienta, así el formulario no las pisa
    extra = 0

    @admin.display(boolean=True, description="Marcada")
    def marcada(self, obj):
        return obj.marcada


@admin.register(Lamina)
class LaminaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "despiece", "pieza", "num_partes", "num_marcadas", "orden")
    list_filter = ("despiece", "pieza")
    list_editable = ("orden",)
    fields = ("despiece", "figura", "titulo", "titulo_es", "pieza", "orden", "imagen")
    inlines = [ParteInline]
    change_form_template = "admin/garaje/lamina/marcar.html"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _partes=Count("partes"), _marcadas=Count("partes", filter=Q(partes__x__isnull=False)),
        )

    @admin.display(description="Partes", ordering="_partes")
    def num_partes(self, obj):
        return obj._partes

    @admin.display(description="Marcadas", ordering="_marcadas")
    def num_marcadas(self, obj):
        return f"{obj._marcadas} de {obj._partes}"

    def get_urls(self):
        return [
            path("<int:pk>/marcar/", self.admin_site.admin_view(self.marcar), name="garaje_lamina_marcar"),
        ] + super().get_urls()

    def change_view(self, request, object_id, form_url="", extra_context=None):
        lamina = self.get_object(request, object_id)
        extra_context = extra_context or {}
        if lamina:
            extra_context["partes_json"] = json.dumps([
                {"id": p.pk, "ref": p.ref, "codigo": p.codigo, "nombre": p.nombre, "x": p.x, "y": p.y,
                 "tarea": p.tarea.nombre if p.tarea else ""}
                for p in lamina.partes.select_related("tarea")
            ])
        return super().change_view(request, object_id, form_url, extra_context)

    def marcar(self, request, pk):
        """Guarda (o quita) la posición de una parte en el dibujo. Recibe JSON {parte, x, y} o {parte, quitar}."""
        if request.method != "POST":
            return JsonResponse({"error": "Método no permitido"}, status=405)
        lamina = get_object_or_404(Lamina, pk=pk)
        if not self.has_change_permission(request, lamina):
            return JsonResponse({"error": "Sin permiso"}, status=403)
        try:
            datos = json.loads(request.body)
            parte = lamina.partes.get(pk=int(datos["parte"]))
            if datos.get("quitar"):
                parte.x = parte.y = None
            else:
                parte.x = min(1.0, max(0.0, float(datos["x"])))
                parte.y = min(1.0, max(0.0, float(datos["y"])))
        except (ValueError, KeyError, TypeError, ParteDespiece.DoesNotExist):
            return JsonResponse({"error": "Datos inválidos"}, status=400)
        parte.save(update_fields=["x", "y"])
        return JsonResponse({"ok": True, "parte": parte.pk, "x": parte.x, "y": parte.y})

