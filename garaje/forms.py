from itertools import groupby

from django import forms
from django.utils import timezone

from talleres.forms import EstiloMixin
from talleres.models import Taller

from .models import COLORES, LineaMoto, Mantenimiento, Moto, TareaMantenimiento

OTRA = "otra"
MAX_KM = 999_999


class MotoForm(EstiloMixin, forms.ModelForm):
    linea_catalogo = forms.ChoiceField(label="Marca y línea")
    color = forms.ChoiceField(choices=COLORES, widget=forms.RadioSelect)
    km_actual = forms.IntegerField(label="Kilometraje actual", min_value=0, max_value=MAX_KM,
                                   widget=forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 12500"}))

    class Meta:
        model = Moto
        fields = ["marca_otra", "linea_otra", "tipo_otra", "modelo", "color", "apodo"]
        widgets = {"modelo": forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 2021"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lineas = LineaMoto.objects.filter(activo=True).select_related("marca")
        opciones = [("", "Elige tu moto")]
        for marca, grupo in groupby(lineas, key=lambda l: l.marca.nombre):
            opciones.append((marca, [(str(l.pk), l.nombre) for l in grupo]))
        opciones.append((OTRA, "Mi moto no está en la lista"))
        self.fields["linea_catalogo"].choices = opciones
        self.fields["linea_catalogo"].widget.attrs["class"] = "campo"
        self.fields["tipo_otra"].choices = [("", "Elige el tipo")] + list(self.fields["tipo_otra"].choices)[1:]
        if self.instance.pk:
            self.fields["linea_catalogo"].initial = str(self.instance.linea_id) if self.instance.linea_id else OTRA
            self.fields.pop("km_actual")  # el kilometraje se actualiza aparte

    def clean_modelo(self):
        anio = self.cleaned_data["modelo"]
        if not 1980 <= anio <= timezone.localdate().year + 1:
            raise forms.ValidationError("Escribe un año válido.")
        return anio

    def clean(self):
        datos = super().clean()
        eleccion = datos.get("linea_catalogo")
        if eleccion == OTRA:
            for campo in ("marca_otra", "linea_otra", "tipo_otra"):
                if not datos.get(campo):
                    self.add_error(campo, "Completa este dato.")
            self.instance.linea = None
        elif eleccion:
            linea = LineaMoto.objects.filter(pk=eleccion, activo=True).first()
            if not linea:
                self.add_error("linea_catalogo", "Elige una línea de la lista.")
            self.instance.linea = linea
            datos["marca_otra"] = datos["linea_otra"] = datos["tipo_otra"] = ""
        return datos


class LecturaForm(EstiloMixin, forms.Form):
    km = forms.IntegerField(label="Kilometraje de hoy", min_value=0, max_value=MAX_KM,
                            widget=forms.NumberInput(attrs={"inputmode": "numeric"}))

    def __init__(self, *args, moto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.moto = moto
        if moto:
            self.fields["km"].widget.attrs["placeholder"] = f"Último: {moto.km_actual}"

    def clean_km(self):
        km = self.cleaned_data["km"]
        if self.moto and km < self.moto.km_actual:
            raise forms.ValidationError(f"No puede ser menor que el último registro ({self.moto.km_actual} km).")
        if self.moto and km - self.moto.km_actual > 50_000:
            raise forms.ValidationError("Ese salto es muy grande. Revisa el número.")
        return km


class MantenimientoForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Mantenimiento
        fields = ["tarea", "km", "fecha", "taller", "notas"]
        labels = {"km": "Kilometraje cuando se hizo", "taller": "Taller (opcional)", "notas": "Notas (opcional)"}
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"}), "tarea": forms.HiddenInput,
                   "km": forms.NumberInput(attrs={"inputmode": "numeric"})}

    def __init__(self, *args, moto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.moto = moto
        self.fields["taller"].queryset = Taller.objects.filter(activo=True)
        self.fields["tarea"].queryset = TareaMantenimiento.objects.filter(activo=True)

    def clean_km(self):
        km = self.cleaned_data["km"]
        if self.moto and km > self.moto.km_actual:
            raise forms.ValidationError(f"No puede ser mayor que el kilometraje actual ({self.moto.km_actual} km). "
                                        "Actualiza primero el kilometraje.")
        return km

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha > timezone.localdate():
            raise forms.ValidationError("La fecha no puede ser futura.")
        return fecha
