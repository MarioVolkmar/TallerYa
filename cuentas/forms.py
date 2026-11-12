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


class EntrarForm(EstiloMixin, AuthenticationForm):
    """Inicio de sesión con el correo (guardado como nombre de usuario)."""

    username = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()

