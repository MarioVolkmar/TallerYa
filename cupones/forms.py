from django import forms

from talleres.forms import EstiloMixin
from talleres.utils import normalizar_celular


class ObtenerCuponForm(EstiloMixin, forms.Form):
    nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    celular = forms.CharField(
        max_length=20, help_text="Con este número identificamos tus cupones.",
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "300 123 4567"}),
    )

    def clean_celular(self):
        return normalizar_celular(self.cleaned_data["celular"])


class CanjeForm(EstiloMixin, forms.Form):
    codigo = forms.CharField(
        label="Código del cupón", max_length=12,
        widget=forms.TextInput(attrs={"placeholder": "TY-XXXXXX", "autocapitalize": "characters", "autocomplete": "off"}),
    )
    pin = forms.CharField(
        label="PIN del taller", max_length=6, min_length=6,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "autocomplete": "off", "placeholder": "••••••"}),
    )
