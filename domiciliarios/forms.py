from django import forms

from talleres import subidas

from .models import PLATAFORMAS, PerfilDomiciliario, Verificacion

MAX_FOTO = 5 * 1024 * 1024  # menos de 5 MB


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
                                 widget=forms.NumberInput(attrs={"class": "campo", "inputmode": "numeric",
                                                                 "placeholder": "95000", "enterkeyhint": "done"}))
    km = forms.IntegerField(label="Km del tablero", required=False, min_value=0,
                            widget=forms.NumberInput(attrs={"class": "campo", "inputmode": "numeric"}))
    gasolina = forms.IntegerField(label="¿Cuánto tanqueaste?", required=False, min_value=0, max_value=500_000,
                                  widget=forms.NumberInput(attrs={"class": "campo", "inputmode": "numeric",
                                                                  "placeholder": "15000"}))

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


LADO_MAX = 1600  # px: de sobra para leer una placa


def _imagen(archivo):
    """Solo imágenes reales (JPG, PNG o WebP por el contenido, no por el nombre) de menos de 5 MB. Se vuelve a codificar
    como JPEG: sin EXIF (ubicación GPS, modelo del celular, fecha) y con nombre aleatorio."""
    if not archivo:
        return archivo
    if archivo.size >= MAX_FOTO:
        raise forms.ValidationError("La foto debe pesar menos de 5 MB.")
    if not subidas.tipo_real(archivo, subidas.IMAGENES):
        raise forms.ValidationError("Sube una foto (JPG, PNG o WebP).")
    import io
    import uuid

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image, ImageOps
    try:
        with Image.open(archivo) as img:
            img = ImageOps.exif_transpose(img)  # respeta la rotación del celular antes de botar el EXIF
            img = img.convert("RGB")
            img.thumbnail((LADO_MAX, LADO_MAX))
            salida = io.BytesIO()
            img.save(salida, "JPEG", quality=85, optimize=True)  # sin exif=: no se copia ningún metadato
    except Exception:
        raise forms.ValidationError("No pudimos leer esa foto. Prueba con otra.")
    return SimpleUploadedFile(f"{uuid.uuid4().hex}.jpg", salida.getvalue(), content_type="image/jpeg")


class VerificacionForm(forms.ModelForm):
    """Dos fotos, las dos obligatorias. Nunca se piden contraseñas de las apps."""
    autorizo = forms.BooleanField(
        required=True, label="Autorizo a TallerYa a usar estas 2 fotos solo para verificarme",
        error_messages={"required": "Marca la autorización para poder enviar las fotos."})

    class Meta:
        model = Verificacion
        fields = ["plataforma", "moto", "captura", "foto_moto"]
        labels = {"plataforma": "¿En qué app trabajas?", "moto": "¿Con qué moto trabajas?",
                  "captura": "Pantallazo de tu perfil en la app", "foto_moto": "Foto de tu moto con la placa"}
        widgets = {
            "plataforma": forms.Select(attrs={"class": "campo"}),
            "moto": forms.Select(attrs={"class": "campo"}),
            "captura": forms.FileInput(attrs={"accept": "image/*", "class": "dm-archivo"}),
            "foto_moto": forms.FileInput(attrs={"accept": "image/*", "capture": "environment", "class": "dm-archivo"}),
        }

    def __init__(self, *args, motociclista, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo sus motos con placa: la placa de las fotos tiene que ser de una moto de su garaje (sin IDOR)
        self.fields["moto"].queryset = motociclista.motos.exclude(placa="").select_related("linea", "linea__marca")
        self.fields["moto"].empty_label = None
        self.fields["moto"].label_from_instance = lambda m: f"{m.nombre_corto} · placa {m.placa}"
        for nombre in ("moto", "captura", "foto_moto"):
            self.fields[nombre].required = True
        self.fields["moto"].error_messages["required"] = "Agrega la placa de tu moto en el garaje y vuelve."
        self.fields["captura"].error_messages["required"] = "Falta el pantallazo de tu perfil."
        self.fields["foto_moto"].error_messages["required"] = "Falta la foto de tu moto con la placa."

    def clean_captura(self):
        return _imagen(self.cleaned_data.get("captura"))

    def clean_foto_moto(self):
        return _imagen(self.cleaned_data.get("foto_moto"))
