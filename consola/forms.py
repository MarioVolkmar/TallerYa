from django import forms
from django.contrib.auth import get_user_model

from .limites import LIMITES

User = get_user_model()


def _texto(campo, etiqueta, requerido=True):
    l = LIMITES[campo]
    return forms.CharField(label=etiqueta, required=requerido, min_length=l["min"] or None, max_length=l["max"],
                           strip=True)


class UsuarioForm(forms.ModelForm):
    """Editar nombre y correo. El correo es también el usuario con que entra (username = email)."""

    first_name = _texto("nombre", "Nombre")
    last_name = _texto("apellido", "Apellido", requerido=False)
    email = forms.EmailField(label="Correo", min_length=LIMITES["correo"]["min"], max_length=LIMITES["correo"]["max"])

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def clean_email(self):
        correo = self.cleaned_data["email"].strip().lower()
        otros = User.objects.exclude(pk=self.instance.pk)
        if otros.filter(email__iexact=correo).exists() or otros.filter(username__iexact=correo).exists():
            raise forms.ValidationError("Ya hay otra cuenta con ese correo.")
        return correo

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = usuario.email
        if commit:
            usuario.save()
        return usuario


class FiltroUsuarios(forms.Form):
    q = _texto("busqueda", "Buscar", requerido=False)
    rol = forms.ChoiceField(required=False, choices=[("", "Todos los roles"), ("admin", "Administrador"),
                                                     ("taller", "Taller"), ("motero", "Motero"),
                                                     ("sin_perfil", "Registro incompleto")],
                            widget=forms.Select(attrs={"class": "cs-campo campo"}))
    estado = forms.ChoiceField(required=False, choices=[("", "Activas e inactivas"), ("activa", "Activas"),
                                                        ("inactiva", "Inactivas")],
                               widget=forms.Select(attrs={"class": "cs-campo campo"}))


class FiltroBitacora(forms.Form):
    q = _texto("busqueda", "Buscar", requerido=False)
    accion = forms.CharField(required=False, max_length=60)
    actor = forms.IntegerField(required=False, min_value=1)
    objeto = forms.RegexField(required=False, regex=r"^[a-z_]+:\d+$", max_length=80)
    desde = forms.DateField(required=False)
    hasta = forms.DateField(required=False)


def _opciones(*pares):
    return forms.ChoiceField(required=False, choices=pares, widget=forms.Select(attrs={"class": "cs-campo campo"}))


class FiltroTalleres(forms.Form):
    q = _texto("busqueda", "Buscar", requerido=False)
    estado = _opciones(("", "Todos"), ("por_aprobar", "Por aprobar"), ("publicados", "Publicados"),
                       ("verificados", "Verificados"))


class FiltroCupones(forms.Form):
    q = _texto("busqueda", "Buscar", requerido=False)
    estado = _opciones(("", "Todos"), ("vigentes", "Vigentes"), ("vencidos", "Vencidos"),
                       ("desactivados", "Desactivados"))


class FiltroCitas(forms.Form):
    q = _texto("busqueda", "Buscar", requerido=False)
    estado = forms.CharField(required=False, max_length=12)
    desde = forms.DateField(required=False)
    hasta = forms.DateField(required=False)


class FiltroModeracion(forms.Form):
    q = _texto("busqueda", "Buscar", requerido=False)
    tipo = _opciones(("reportes", "Reportes pendientes"), ("preguntas", "Preguntas del foro"),
                     ("respuestas", "Respuestas del foro"), ("resenas", "Reseñas de talleres"))
    estado = _opciones(("", "Visibles y ocultas"), ("visibles", "Visibles"), ("ocultas", "Ocultas"))
