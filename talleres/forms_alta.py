"""Formularios de alta de talleres sin cuenta: asistida (la carga el equipo), autoregistro y revisión por enlace."""
from django import forms

from .forms import RegistroTallerForm

AVISO_FOTOS = "Solo fotos del propio taller o que él autorizó. Nunca fotos copiadas de Google, Facebook u otras páginas."
TEXTO_AUTORIZO = ("Autorizo a TallerYa a tratar los datos de mi taller (nombre, teléfono, dirección, fotos) para mostrarlos "
                  "en el directorio, según la política de tratamiento de datos (Ley 1581 de 2012).")


class _FichaBase(RegistroTallerForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["foto"].help_text = AVISO_FOTOS
        self.fields["foto"].required = False


class AltaAsistidaForm(_FichaBase):
    """Lo llena el equipo en la consola con lo que dijo el taller."""
    class Meta(RegistroTallerForm.Meta):
        fields = ["nombre", "responsable", "whatsapp", "direccion", "barrio", "horario",
                  "descripcion", "servicios", "marcas", "foto"]


class AutoregistroForm(_FichaBase):
    """Pocos campos, pensado para el celular. La autorización de datos es obligatoria."""
    autoriza = forms.BooleanField(label=TEXTO_AUTORIZO, error_messages={"required": "Necesitamos tu autorización para publicar tu taller."})

    class Meta(RegistroTallerForm.Meta):
        fields = ["nombre", "responsable", "whatsapp", "direccion", "barrio", "servicios", "foto"]


class RevisionForm(_FichaBase):
    """El taller revisa lo que cargamos: corrige y, si marca la autorización, aprueba."""
    autoriza = forms.BooleanField(label=TEXTO_AUTORIZO, required=False)

    class Meta(RegistroTallerForm.Meta):
        fields = ["nombre", "responsable", "whatsapp", "direccion", "barrio", "horario",
                  "descripcion", "servicios", "marcas", "foto"]
