from django import forms

from talleres.forms import EstiloMixin

from .models import Pregunta, Respuesta


class PreguntaForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ["titulo", "marca", "cuerpo"]
        labels = {"titulo": "Tu pregunta", "cuerpo": "Detalles", "marca": "Marca de tu moto (opcional)"}
        widgets = {"cuerpo": forms.Textarea(attrs={"rows": 6, "placeholder": "Cuenta el modelo, el año, qué síntomas tiene..."})}

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"].strip()
        if len(titulo) < 10:
            raise forms.ValidationError("Escribe una pregunta un poco más completa.")
        return titulo


class RespuestaForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Respuesta
        fields = ["cuerpo"]
        labels = {"cuerpo": "Tu respuesta"}
        widgets = {"cuerpo": forms.Textarea(attrs={"rows": 4})}
