from django import forms

from .models import PLATAFORMAS, PerfilDomiciliario


class PerfilForm(forms.ModelForm):
    plataformas = forms.MultipleChoiceField(choices=PLATAFORMAS, required=False, widget=forms.CheckboxSelectMultiple,
                                            label="¿Con qué plataformas trabajas?")

    class Meta:
        model = PerfilDomiciliario
        fields = ["moto", "plataformas", "km_semana", "dias_semana"]
        widgets = {
            "moto": forms.Select(attrs={"class": "campo mt-1"}),
            "km_semana": forms.NumberInput(attrs={"class": "campo mt-1", "inputmode": "numeric", "min": 50, "max": 5000,
                                                  "placeholder": "Ej: 1200"}),
            "dias_semana": forms.NumberInput(attrs={"class": "campo mt-1", "inputmode": "numeric", "min": 1, "max": 7}),
        }
        help_texts = {"km_semana": "Más o menos. Si no sabes: unos 200 km por cada día que trabajas."}

    def __init__(self, *args, motociclista, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo sus motos: elegir la de otro no pasa la validación (sin IDOR)
        self.fields["moto"].queryset = motociclista.motos.select_related("linea", "linea__marca")
        self.fields["moto"].required = True
        self.fields["moto"].empty_label = None


class JornadaForm(forms.Form):
    ingreso = forms.IntegerField(label="¿Cuánto ganaste hoy?", min_value=0, max_value=3_000_000,
                                 widget=forms.NumberInput(attrs={"class": "campo mt-1", "inputmode": "numeric",
                                                                 "placeholder": "Ej: 95000"}))
    km = forms.IntegerField(label="Km del tablero al terminar", required=False, min_value=0,
                            widget=forms.NumberInput(attrs={"class": "campo mt-1", "inputmode": "numeric"}))
    gasolina = forms.IntegerField(label="Gasolina que tanqueaste hoy", required=False, min_value=0, max_value=500_000,
                                  widget=forms.NumberInput(attrs={"class": "campo mt-1", "inputmode": "numeric",
                                                                  "placeholder": "Ej: 15000"}))

    def __init__(self, *args, moto, **kwargs):
        super().__init__(*args, **kwargs)
        self.moto = moto
        self.fields["km"].widget.attrs["placeholder"] = f"Último: {moto.km_actual}"

    def clean_km(self):
        km = self.cleaned_data.get("km")
        if km is None:
            return None
        if km < self.moto.km_actual:
            raise forms.ValidationError(f"Es menor que el último registrado ({self.moto.km_actual} km).")
        if km > self.moto.km_actual + 2000:
            raise forms.ValidationError("Son más de 2.000 km en un día: revisa el número.")
        return km
