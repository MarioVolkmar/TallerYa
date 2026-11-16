from django.contrib.auth.password_validation import UserAttributeSimilarityValidator
from django.core.exceptions import ValidationError


class ClaveParecidaValidator(UserAttributeSimilarityValidator):
    """Igual al de Django, pero el aviso habla de tu correo o nombre (aquí nadie tiene «nombre de usuario»)."""

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            raise ValidationError("La contraseña se parece demasiado a tu correo o a tu nombre. Elige otra.",
                                  code="password_too_similar")

    def get_help_text(self):
        return "Tu contraseña no puede parecerse a tu correo ni a tu nombre."
