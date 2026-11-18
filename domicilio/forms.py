from django import forms

from talleres.forms import EstiloMixin
from talleres.subidas import IMAGENES, tipo_real
from talleres.utils import normalizar_celular

from .models import MecanicoDomicilio, ResenaMecanico

MAX_FOTO = 5 * 1024 * 1024  # antes de recortar; se guarda un JPEG de 480x480


class PerfilMecanicoForm(EstiloMixin, forms.ModelForm):
    """Lo que el mecánico llena al registrarse y puede cambiar después. Estado y «verificado» solo los toca el equipo."""
    # Más largo que el campo del modelo: acepta «+57 300 123 4567» y clean_whatsapp lo deja en 573001234567
    whatsapp = forms.CharField(
        label="WhatsApp o celular", max_length=20,
        help_text="10 dígitos, ej: 3001234567. Los motociclistas te escriben a este número.",
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "3001234567"}))

    class Meta:
        model = MecanicoDomicilio
        fields = ["nombre", "foto", "whatsapp", "zonas", "servicios", "marcas", "anios_experiencia", "horario",
                  "urgencias", "tarifa_visita", "descripcion"]
        labels = {"nombre": "Nombre visible", "foto": "Foto (tu cara o tú trabajando)",
                  "zonas": "¿Dónde atiendes?", "servicios": "¿Qué trabajos haces a domicilio?",
                  "marcas": "Marcas que mejor conoces (opcional)", "tarifa_visita": "Tarifa de visita orientativa"}
        help_texts = {"whatsapp": "10 dígitos, ej: 3001234567. Los motociclistas te escriben a este número.",
                      "tarifa_visita": "En pesos, sin puntos. Es una referencia: el precio final lo acuerdas con el cliente."}
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Jhon Fredy · Mecánico a domicilio"}),
            "foto": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "whatsapp": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "3001234567"}),
            "zonas": forms.CheckboxSelectMultiple,
            "servicios": forms.CheckboxSelectMultiple,
            "marcas": forms.CheckboxSelectMultiple,
            "anios_experiencia": forms.NumberInput(attrs={"min": 0, "max": 60}),
            "horario": forms.TextInput(attrs={"placeholder": "Ej: Lun-Sáb 7am-6pm"}),
            "tarifa_visita": forms.NumberInput(attrs={"min": 0, "step": 1000, "placeholder": "25000"}),
            "descripcion": forms.Textarea(attrs={"rows": 4, "maxlength": 600,
                                                 "placeholder": "Ej: 12 años en motos de trabajo y scooters. Llevo herramienta "
                                                                "y escáner. Si el daño es grande, te recomiendo taller."}),
        }

    def clean_whatsapp(self):
        return normalizar_celular(self.cleaned_data["whatsapp"])

    def clean_foto(self):
        """Mismo criterio que las demás subidas: se mira el contenido real (no el nombre ni el Content-Type), y la
        foto se vuelve a codificar como JPEG cuadrado (sin EXIF, sin lo que traiga escondido el archivo original)."""
        foto = self.cleaned_data.get("foto")
        if not foto or foto == getattr(self.instance, "foto", None):
            return foto  # sin cambios
        if foto.size > MAX_FOTO:
            raise forms.ValidationError("La foto debe pesar máximo 5 MB.")
        if not tipo_real(foto, IMAGENES):
            raise forms.ValidationError("Sube una foto JPG, PNG o WEBP.")
        from cuentas.forms import foto_cuadrada
        return foto_cuadrada(foto, lado=480)


class ResenaMecanicoForm(EstiloMixin, forms.ModelForm):
    estrellas = forms.TypedChoiceField(choices=[(i, "★" * i) for i in range(5, 0, -1)], coerce=int)

    class Meta:
        model = ResenaMecanico
        fields = ["estrellas", "comentario"]
        labels = {"comentario": "¿Cómo te fue?"}
        widgets = {"comentario": forms.Textarea(attrs={"rows": 3, "maxlength": 600})}
