from pathlib import Path

from django import forms

from .models import PedidoSoat

MAX_ARCHIVO = 5 * 1024 * 1024
TIPOS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".heic"}


class PedidoSoatForm(forms.ModelForm):
    acepta_datos = forms.BooleanField(
        label="Autorizo a TallerYa a tratar mis datos personales para gestionar mi SOAT (Ley 1581 de 2012).",
        error_messages={"required": "Para emitir tu SOAT necesitamos tu autorización de datos."})
    # Se aceptan espacios y guiones al escribir; clean_celular deja los 10 dígitos
    celular = forms.CharField(max_length=20, widget=forms.TextInput(
        attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "3001234567"}))

    class Meta:
        model = PedidoSoat
        fields = ["tipo_documento", "numero_documento", "nombre_completo", "chasis_motor", "tarjeta_propiedad",
                  "correo", "direccion", "celular"]
        widgets = {
            "tipo_documento": forms.Select(attrs={"class": "campo"}),
            "numero_documento": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
            "nombre_completo": forms.TextInput(attrs={"autocomplete": "name"}),
            "chasis_motor": forms.TextInput(attrs={"autocapitalize": "characters",
                                                   "placeholder": "Está en la tarjeta de propiedad"}),
            "tarjeta_propiedad": forms.FileInput(attrs={"accept": "image/*,application/pdf"}),
            "correo": forms.EmailInput(attrs={"autocomplete": "email"}),
            "direccion": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "celular": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "3001234567"}),
        }

    def clean_numero_documento(self):
        valor = "".join(c for c in self.cleaned_data["numero_documento"] if c.isalnum()).upper()
        if len(valor) < 5:
            raise forms.ValidationError("Revisa el número de documento.")
        return valor

    def clean_chasis_motor(self):
        return "".join(c for c in self.cleaned_data.get("chasis_motor", "") if c.isalnum()).upper()

    def clean_celular(self):
        valor = "".join(c for c in self.cleaned_data["celular"] if c.isdigit())[-10:]
        if len(valor) != 10 or not valor.startswith("3"):
            raise forms.ValidationError("Escribe un celular colombiano de 10 dígitos.")
        return valor

    def clean_tarjeta_propiedad(self):
        archivo = self.cleaned_data.get("tarjeta_propiedad")
        if archivo and hasattr(archivo, "size"):
            if archivo.size > MAX_ARCHIVO:
                raise forms.ValidationError("El archivo pesa más de 5 MB.")
            if Path(archivo.name).suffix.lower() not in TIPOS:
                raise forms.ValidationError("Sube una foto (JPG o PNG) o un PDF.")
            # El contenido debe ser de verdad una imagen o un PDF (no basta con la extensión). HEIC: "ftyp" en el byte 4.
            inicio = archivo.read(12)
            archivo.seek(0)
            if not (inicio.startswith((b"\xff\xd8\xff", b"\x89PNG", b"%PDF", b"RIFF")) or inicio[4:8] == b"ftyp"):
                raise forms.ValidationError("Ese archivo no parece una foto o un PDF.")
        return archivo

    def clean(self):
        datos = super().clean()
        if not datos.get("chasis_motor") and not datos.get("tarjeta_propiedad"):
            self.add_error("chasis_motor",
                           "Escribe el número de chasis o de motor, o sube la foto de la tarjeta de propiedad.")
        return datos
