from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm

from cupones.models import Motociclista
from cupones.servicios import normalizar_codigo
from talleres.forms import EstiloMixin
from talleres.utils import normalizar_celular

User = get_user_model()


class RegistroForm(EstiloMixin, forms.Form):
    domicilios = forms.BooleanField(label="Uso la moto para domicilios o mensajería", required=False)
    nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    email = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    celular = forms.CharField(
        max_length=20, help_text="Para tus cupones y los avisos de tu moto.",
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "300 123 4567"}),
    )
    codigo_existente = forms.CharField(
        label="Uno de tus códigos de cupón", required=False, max_length=12,
        help_text="Así comprobamos que el número es tuyo y pasamos tus cupones a la cuenta.",
        widget=forms.TextInput(attrs={"placeholder": "TY-XXXXXX", "autocomplete": "off"}),
    )
    password1 = forms.CharField(label="Contraseña", help_text="Mínimo 8 caracteres y que no sea solo números.",
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Repite la contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    acepto = forms.BooleanField(
        label="Acepto los términos y la política de privacidad",
        error_messages={"required": "Para crear la cuenta debes aceptar los términos y la política de privacidad."},
    )

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
    password1 = forms.CharField(label="Contraseña", help_text="Mínimo 8 caracteres y que no sea solo números.",
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Repite la contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    acepto = forms.BooleanField(
        label="Acepto los términos y la política de privacidad",
        error_messages={"required": "Para crear la cuenta debes aceptar los términos y la política de privacidad."},
    )

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


class FrenoIntentosMixin:
    """Freno contra adivinar contraseñas: por correo (10 fallos en 15 min) y por IP (30 fallos, muchas cuentas).
    Lo usan el login del sitio y el de /admin/ (config/urls.py), que antes no tenía límite."""

    MAX_FALLOS_CORREO, MAX_FALLOS_IP, VENTANA = 10, 30, 15 * 60

    def clean(self):
        from cuentas.limites import ip_cliente, limpiar, sumar, superado
        correo = (self.cleaned_data.get("username") or "").strip().lower()
        ip = ip_cliente(self.request) if self.request else "sin-ip"
        claves = (f"login-correo:{correo}", self.MAX_FALLOS_CORREO), (f"login-ip:{ip}", self.MAX_FALLOS_IP)
        if any(superado(c, m) for c, m in claves):
            raise forms.ValidationError("Demasiados intentos fallidos. Espera 15 minutos o recupera tu contraseña.",
                                        code="bloqueado")
        try:
            datos = super().clean()
        except forms.ValidationError:
            for c, _ in claves:
                sumar(c, self.VENTANA)
            raise
        limpiar(claves[0][0])
        return datos


class EntrarAdminForm(FrenoIntentosMixin, AdminAuthenticationForm):
    """Login de /admin/ con el mismo freno que el del sitio."""


class EntrarForm(FrenoIntentosMixin, EstiloMixin, AuthenticationForm):
    """Inicio de sesión con el correo (guardado como nombre de usuario)."""

    username = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "El correo o la contraseña no coinciden. Revisa que estén bien escritos o recupera tu contraseña.",
    }

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
        max_length=20, help_text="Para tus cupones y los avisos de tu moto.",
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


class RecuperarForm(EstiloMixin, PasswordResetForm):
    """Como el de Django, pero también sirve a quien entró con Google y aún no tiene contraseña (así la crea)."""

    def get_users(self, email):
        User = get_user_model()
        return (u for u in User._default_manager.filter(email__iexact=email, is_active=True))


class CambiarContrasenaForm(EstiloMixin, PasswordChangeForm):
    pass


class CrearContrasenaForm(EstiloMixin, SetPasswordForm):
    pass
