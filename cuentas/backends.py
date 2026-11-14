"""Backend de ingreso: igual al de Django, pero carga en la misma consulta el taller, el perfil de motero
y el perfil de la cuenta. Así cada página (roles, menú, avisos) no hace tres consultas extra por visita."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class Backend(ModelBackend):
    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            usuario = UserModel._default_manager.select_related("taller", "motociclista", "perfil").get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return usuario if self.user_can_authenticate(usuario) else None
