"""Formulario de gastos (tanqueo, servicio, repuesto, SOAT, técnico-mecánica u otro)."""
from django import forms
from django.utils import timezone

from talleres.forms import EstiloMixin

from .forms import MAX_KM
from .forms_hoja_vida import MAX_COSTO, _fecha_no_futura
from .models import Gasto


class GastoForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ["tipo", "fecha", "valor", "galones", "km", "tanque_lleno", "notas"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "valor": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0, "placeholder": "Ej: 25000"}),
            "galones": forms.NumberInput(attrs={"inputmode": "decimal", "min": 0, "step": "0.01", "placeholder": "Ej: 1.8"}),
            "km": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0, "max": MAX_KM}),
            "notas": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }
        help_texts = {"km": "Lo que marca el odómetro. Con km y galones calculamos el rendimiento."}

    def __init__(self, *args, moto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].widget.attrs["max"] = timezone.localdate().isoformat()
        if moto and not self.is_bound:
            self.fields["km"].initial = moto.km_actual

    def clean_fecha(self):
        return _fecha_no_futura(self.cleaned_data.get("fecha"))

    def clean_valor(self):
        valor = self.cleaned_data.get("valor")
        if valor is not None and valor > MAX_COSTO:
            raise forms.ValidationError("Ese valor es demasiado alto. Revisa el número.")
        return valor

    def clean(self):
        datos = super().clean()
        if datos.get("tipo") != Gasto.Tipo.TANQUEO:
            datos["galones"], datos["tanque_lleno"] = None, False
        elif datos.get("galones") is not None and not 0 < datos["galones"] <= 30:
            self.add_error("galones", "Escribe los galones del tanqueo (una moto rara vez pasa de 5).")
        if datos.get("km") is not None and datos["km"] > MAX_KM:
            self.add_error("km", "Ese kilometraje es demasiado alto.")
        return datos
