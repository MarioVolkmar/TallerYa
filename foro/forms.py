"""Formularios del foro para preguntar y responder, con el estilo común de TallerYa."""
from django import forms

from talleres.forms import EstiloMixin

from .models import Pregunta, Respuesta


class PreguntaForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ["titulo", "categoria", "marca", "linea", "cuerpo"]
        labels = {"titulo": "Tu pregunta", "cuerpo": "Detalles", "categoria": "Tema",
                  "marca": "Marca de tu moto (opcional)", "linea": "Línea (opcional)"}
        widgets = {"cuerpo": forms.Textarea(attrs={"rows": 6, "placeholder": "Cuenta el modelo, el año, qué síntomas tiene..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["linea"].queryset = self.fields["linea"].queryset.select_related("marca").order_by("marca__nombre", "nombre")
        self.fields["linea"].label_from_instance = lambda l: f"{l.marca} {l.nombre}"
        self.fields["categoria"].required = False  # si no elige tema, queda en "General"

    def clean_categoria(self):
        from .models import Categoria
        return self.cleaned_data.get("categoria") or Categoria.GENERAL

    def clean(self):
        datos = super().clean()
        linea, marca = datos.get("linea"), datos.get("marca")
        if linea and not marca:
            datos["marca"] = linea.marca  # si elige la línea, la marca sale de ahí
        elif linea and marca and linea.marca_id != marca.pk:
            self.add_error("linea", "Esa línea no es de la marca que elegiste.")
        return datos

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


# Señales de una dirección privada (casa, apto, nomenclatura con #). Las rodadas se citan en lugares públicos.
import re as _re

_DIRECCION_PRIVADA = _re.compile(
    r"#\s*\d|\b(apto|apartamento|apartaestudio|casa|interior|int\.|torre|piso|unidad|conjunto|urbanizaci[oó]n|mi\s+casa)\b"
    r"|\b(calle|cl|carrera|cra|kr|cr|diagonal|dg|transversal|tv|circular|cq)\.?\s*\d+\w?\s*(no\.?|n°|nro\.?|-)\s*\d",
    _re.IGNORECASE,
)


class RodadaForm(EstiloMixin, forms.Form):
    titulo = forms.CharField(label="Nombre de la rodada", max_length=150,
                             widget=forms.TextInput(attrs={"placeholder": "Ej: Rodada al Peñol para principiantes"}))
    fecha_hora = forms.DateTimeField(label="Fecha y hora", input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
                                     widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"))
    punto_encuentro = forms.CharField(label="Punto de encuentro (lugar público)", max_length=150,
                                      help_text="Estación del metro, parque, bomba de gasolina… Nunca una casa o apartamento.")
    destino = forms.CharField(label="Destino o ruta", max_length=200)
    nivel = forms.ChoiceField(label="Nivel")
    cupo = forms.IntegerField(label="Cupo (opcional)", required=False, min_value=2, max_value=500)
    cuerpo = forms.CharField(label="Detalles", max_length=3000, required=False,
                             widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Ritmo, paradas, qué llevar, si hay que tanquear antes…"}))

    def __init__(self, *args, **kwargs):
        from .models import Rodada
        super().__init__(*args, **kwargs)
        self.fields["nivel"].choices = Rodada.Nivel.choices

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"].strip()
        if len(titulo) < 8:
            raise forms.ValidationError("Ponle un nombre un poco más completo.")
        return titulo

    def clean_fecha_hora(self):
        from django.utils import timezone
        fecha = self.cleaned_data["fecha_hora"]
        if fecha < timezone.now():
            raise forms.ValidationError("La rodada tiene que ser en el futuro.")
        if fecha > timezone.now() + __import__("datetime").timedelta(days=180):
            raise forms.ValidationError("Publica rodadas de máximo seis meses en adelante.")
        return fecha

    def _sin_direccion_privada(self, campo):
        valor = self.cleaned_data[campo].strip()
        if _DIRECCION_PRIVADA.search(valor):
            raise forms.ValidationError("Parece una dirección privada. Usa un lugar público y conocido (ej: Estación Poblado, Parque de Envigado).")
        return valor

    def clean_punto_encuentro(self):
        return self._sin_direccion_privada("punto_encuentro")

    def clean_destino(self):
        return self._sin_direccion_privada("destino")
