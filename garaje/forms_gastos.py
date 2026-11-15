"""Formulario de gastos: categoría, valor, fecha y notas opcionales."""
from django import forms
from django.utils import timezone

from talleres.forms import EstiloMixin

from .forms_hoja_vida import MAX_COSTO, _fecha_no_futura
from .models import Gasto


class GastoForm(EstiloMixin, forms.ModelForm):
    """Solo lo que importa: categoría, valor y fecha (las notas son opcionales). Los km salen de las lecturas."""

    class Meta:
        model = Gasto
        fields = ["tipo", "valor", "fecha", "notas"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "valor": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0, "placeholder": "Ej: 25000"}),
            "notas": forms.TextInput(attrs={"placeholder": "Opcional. Ej: Terpel de la 80"}),
        }

    def __init__(self, *args, moto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].widget.attrs["max"] = timezone.localdate().isoformat()

    def clean_fecha(self):
        return _fecha_no_futura(self.cleaned_data.get("fecha"))

    def clean_valor(self):
        valor = self.cleaned_data.get("valor")
        if valor is not None and valor > MAX_COSTO:
            raise forms.ValidationError("Ese valor es demasiado alto. Revisa el número.")
        return valor
