from django import forms

from .models import Resena, SolicitudCita, Taller
from .utils import normalizar_celular

INPUT = "campo"  # estilos en talleres/static/talleres/css/tallerya.css


class EstiloMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            if not isinstance(f.widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                f.widget.attrs.setdefault("class", INPUT)


class SolicitudCitaForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = SolicitudCita
        fields = ["nombre", "telefono", "moto", "servicio", "fecha_preferida", "detalle"]
        widgets = {
            "fecha_preferida": forms.DateInput(attrs={"type": "date"}),
            "detalle": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, taller=None, **kwargs):
        super().__init__(*args, **kwargs)
        if taller:
            self.fields["servicio"].queryset = taller.servicios.all()


class ResenaForm(EstiloMixin, forms.ModelForm):
    estrellas = forms.TypedChoiceField(choices=[(i, "★" * i) for i in range(5, 0, -1)], coerce=int)

    class Meta:
        model = Resena
        fields = ["nombre", "estrellas", "comentario"]
        widgets = {"comentario": forms.Textarea(attrs={"rows": 3})}


class RegistroTallerForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Taller
        fields = ["nombre", "responsable", "whatsapp", "direccion", "barrio", "horario",
                  "descripcion", "servicios", "marcas", "foto"]
        widgets = {
            "servicios": forms.CheckboxSelectMultiple,
            "marcas": forms.CheckboxSelectMultiple,
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_whatsapp(self):
        return normalizar_celular(self.cleaned_data["whatsapp"])



class PerfilTallerForm(EstiloMixin, forms.ModelForm):
    """Lo que el taller puede cambiar de su perfil público."""
    class Meta:
        model = Taller
        fields = ["descripcion", "horario", "servicios", "marcas", "foto"]
        labels = {"descripcion": "Sobre el taller", "foto": "Foto de portada"}
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 5, "maxlength": 1200,
                                                 "placeholder": "Cuéntale a los moteros quiénes son, desde cuándo trabajan y en qué son buenos."}),
            "horario": forms.TextInput(attrs={"placeholder": "Ej: Lun-Sáb 8am-6pm"}),
            "servicios": forms.CheckboxSelectMultiple,
            "marcas": forms.CheckboxSelectMultiple,
            "foto": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and getattr(foto, "size", 0) > 5 * 1024 * 1024:
            raise forms.ValidationError("La foto debe pesar máximo 5 MB.")
        return foto
