from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm

from cupones.models import Motociclista
from cupones.servicios import normalizar_codigo
from talleres.forms import EstiloMixin
from talleres.utils import normalizar_celular

User = get_user_model()


class RegistroForm(EstiloMixin, forms.Form):
    nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    email = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    celular = forms.CharField(
        max_length=20, help_text="Si ya tienes cupones con este número, los verás en tu cuenta.",
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "300 123 4567"}),
    )
    codigo_existente = forms.CharField(
        label="Uno de tus códigos de cupón", required=False, max_length=12,
        help_text="Solo si ya tienes cupones con este celular. Así comprobamos que el número es tuyo.",
        widget=forms.TextInput(attrs={"placeholder": "TY-XXXXXX", "autocomplete": "off"}),
    )
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Repite la contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo. ¿Quieres entrar?")
        return email

    def clean_celular(self):
        return normalizar_celular(self.cleaned_data["celular"])

    def clean(self):
        datos = super().clean()
        celular = datos.get("celular")
        if celular:
            moto = Motociclista.objects.filter(celular=celular).first()
            if moto and moto.usuario_id:
                self.add_error("celular", "Este celular ya está asociado a otra cuenta.")
            elif moto and moto.codigos.exists():
                codigo = datos.get("codigo_existente", "")
                if not codigo or not moto.codigos.filter(codigo=normalizar_codigo(codigo)).exists():
                    self.add_error(
                        "codigo_existente",
                        "Este celular ya tiene cupones. Escribe uno de sus códigos para enlazarlos a tu cuenta.",
                    )
            self.motociclista_existente = moto

        p1, p2 = datos.get("password1"), datos.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        elif p1:
            usuario_temporal = User(username=datos.get("email", ""), email=datos.get("email", ""),
                                    first_name=datos.get("nombre", ""))
            try:
                password_validation.validate_password(p1, usuario_temporal)
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return datos


class CuentaTallerForm(EstiloMixin, forms.Form):
    """Correo y contraseña de la cuenta del taller (los datos del negocio van en RegistroTallerForm)."""

    email = forms.EmailField(label="Correo de la cuenta", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Repite la contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo. ¿Quieres entrar?")
        return email

    def clean(self):
        datos = super().clean()
        p1, p2 = datos.get("password1"), datos.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        elif p1:
            try:
                password_validation.validate_password(p1, User(username=datos.get("email", ""), email=datos.get("email", "")))
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return datos


class EntrarForm(EstiloMixin, AuthenticationForm):
    """Inicio de sesión con el correo (guardado como nombre de usuario)."""

    username = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()



MAX_FOTO = 4 * 1024 * 1024  # 4 MB antes de recortar


class AvatarForm(forms.Form):
    """Elegir avatar: la inicial, un prediseñado, la foto ya subida o una foto nueva."""

    eleccion = forms.CharField(required=False)
    foto = forms.ImageField(required=False)

    def clean_eleccion(self):
        from .avatares import PREDISENADOS
        valor = self.cleaned_data.get("eleccion", "")
        if valor not in ("", "foto", *PREDISENADOS):
            raise forms.ValidationError("Elige uno de los avatares.")
        return valor

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and foto.size > MAX_FOTO:
            raise forms.ValidationError("La foto pesa más de 4 MB. Prueba con una más liviana.")
        return foto


def foto_cuadrada(archivo, lado=256):
    """Recorta al centro, la deja de 256x256 y la guarda como JPEG nuevo (sin datos EXIF como la ubicación)."""
    from io import BytesIO

    from django.core.files.base import ContentFile
    from PIL import Image, ImageOps

    imagen = ImageOps.exif_transpose(Image.open(archivo)).convert("RGB")
    imagen = ImageOps.fit(imagen, (lado, lado), Image.LANCZOS)
    salida = BytesIO()
    imagen.save(salida, "JPEG", quality=86, optimize=True)
    return ContentFile(salida.getvalue(), name="avatar.jpg")



class CelularForm(EstiloMixin, forms.Form):
    """Completar el perfil de motero de una cuenta creada con Google: solo falta el celular."""

    celular = forms.CharField(
        max_length=20, help_text="Si ya tienes cupones con este número, los verás en tu cuenta.",
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "300 123 4567"}),
    )
    codigo_existente = forms.CharField(
        label="Uno de tus códigos de cupón", required=False, max_length=12,
        help_text="Solo si ya tienes cupones con este celular.",
        widget=forms.TextInput(attrs={"placeholder": "TY-XXXXXX", "autocomplete": "off"}),
    )

    def clean_celular(self):
        return normalizar_celular(self.cleaned_data["celular"])

    def clean(self):
        datos = super().clean()
        celular = datos.get("celular")
        self.motociclista_existente = None
        if celular:
            moto = Motociclista.objects.filter(celular=celular).first()
            if moto and moto.usuario_id:
                self.add_error("celular", "Este celular ya está asociado a otra cuenta.")
            elif moto and moto.codigos.exists():
                codigo = datos.get("codigo_existente", "")
                if not codigo or not moto.codigos.filter(codigo=normalizar_codigo(codigo)).exists():
                    self.add_error("codigo_existente",
                                   "Este celular ya tiene cupones. Escribe uno de sus códigos para enlazarlos a tu cuenta.")
            self.motociclista_existente = moto
        return datos
