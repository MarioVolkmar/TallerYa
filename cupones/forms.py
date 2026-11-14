from django import forms

from talleres.forms import EstiloMixin
from talleres.utils import normalizar_celular

from .models import Cupon


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
        label="PIN del taller", max_length=6, min_length=6, required=False,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "autocomplete": "off", "placeholder": "••••••"}),
    )


class CuponTallerForm(EstiloMixin, forms.ModelForm):
    """Lo que el taller llena para publicar un cupón propio."""

    class Meta:
        model = Cupon
        fields = ["titulo", "condiciones", "valido_hasta", "cupo", "solo_plus"]
        labels = {"titulo": "¿Qué ofreces?", "valido_hasta": "Válido hasta", "cupo": "Cantidad de cupones"}
        help_texts = {"titulo": "", "condiciones": "", "valido_hasta": "", "cupo": "", "solo_plus": ""}
        widgets = {
            "titulo": forms.TextInput(attrs={"placeholder": "15% de descuento en cambio de aceite"}),
            "condiciones": forms.Textarea(attrs={"rows": 3, "placeholder": "No acumulable. Válido de lunes a viernes."}),
            "valido_hasta": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "cupo": forms.NumberInput(attrs={"min": 1, "placeholder": "Sin límite"}),
        }

    def __init__(self, *args, **kwargs):
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        self.fields["valido_hasta"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean_valido_hasta(self):
        from django.utils import timezone
        fecha = self.cleaned_data.get("valido_hasta")
        if fecha and fecha < timezone.localdate():
            raise forms.ValidationError("La fecha ya pasó. Elige una fecha de hoy en adelante.")
        return fecha
