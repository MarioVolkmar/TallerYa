"""Formularios de proveedores: consola (alta asistida y edición), autoregistro «Soy proveedor», revisión por enlace
y categorías. Los campos propios de cada categoría (CAMPOS_EXTRA) se agregan como «extra_<clave>» y se guardan en
Proveedor.extras solo si la categoría los usa."""
from django import forms

from talleres.forms import INPUT, EstiloMixin
from talleres.models import CIUDADES

from .models import CAMPOS_EXTRA, CAMPOS_EXTRA_OPCIONES, Categoria, Proveedor

AVISO_FOTOS = "Solo fotos o logos propios. Nunca imágenes copiadas de Google, Facebook u otras páginas."
TEXTO_AUTORIZO = ("Autorizo a TallerYa a tratar los datos de mi negocio (nombre, teléfono, dirección, fotos) para mostrarlos "
                  "a los moteros, según la política de tratamiento de datos (Ley 1581 de 2012).")
MAX_FOTO = 5 * 1024 * 1024

CAMPOS_CONSOLA = ["categoria", "nombre", "responsable", "whatsapp", "telefono", "municipio", "zonas", "barrios",
                  "direccion", "sitio_web", "abierto_24h", "abre", "cierra", "horario", "descripcion", "precio_desde",
                  "precio_fuente", "aliado", "beneficio", "foto", "latitud", "longitud"]
CAMPOS_REVISION = ["nombre", "responsable", "whatsapp", "telefono", "municipio", "zonas", "barrios", "direccion",
                   "sitio_web", "abierto_24h", "abre", "cierra", "horario", "descripcion", "precio_desde", "foto"]
CAMPOS_AUTOREGISTRO = ["categoria", "nombre", "responsable", "whatsapp", "municipio", "zonas", "direccion",
                       "abierto_24h", "horario", "descripcion", "precio_desde", "foto"]


def _digitos(valor):
    return "".join(ch for ch in (valor or "") if ch.isdigit())


class ProveedorForm(EstiloMixin, forms.ModelForm):
    zonas = forms.MultipleChoiceField(choices=[(c, c) for c in CIUDADES], required=False,
                                      widget=forms.CheckboxSelectMultiple, label="Municipios que atiende")

    class Meta:
        model = Proveedor
        fields = CAMPOS_CONSOLA
        widgets = {
            "abre": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "cierra": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "descripcion": forms.Textarea(attrs={"rows": 3, "maxlength": 600}),
            "foto": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "whatsapp": forms.TextInput(attrs={"inputmode": "tel", "placeholder": "3001234567"}),
            "telefono": forms.TextInput(attrs={"inputmode": "tel"}),
            "precio_desde": forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "Opcional"}),
        }

    def __init__(self, *args, categoria=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.categoria_fija = categoria or (self.instance.categoria if self.instance.categoria_id else None)
        for f in self.fields.values():
            if isinstance(f.widget, forms.CheckboxInput):
                f.widget.attrs.pop("class", None)
        if "foto" in self.fields:
            self.fields["foto"].help_text = AVISO_FOTOS
        if "horario" in self.fields:
            self.fields["horario"].widget.attrs.setdefault("placeholder", "Lun a sáb 7 a. m. a 6 p. m.")
        if "categoria" in self.fields:
            self.fields["categoria"].empty_label = "Elige la categoría"
        for clave, (etiqueta, tipo, opciones) in CAMPOS_EXTRA.items():
            if tipo == "opcion":
                campo = forms.ChoiceField(label=etiqueta, required=False, choices=[("", "Sin indicar")] + list(opciones))
            else:
                campo = forms.BooleanField(label=etiqueta, required=False)
            campo.widget.attrs["data-extra"] = clave
            if tipo == "opcion":
                campo.widget.attrs["class"] = INPUT
            campo.initial = self.instance.extras.get(clave) if self.instance.pk else None
            self.fields[f"extra_{clave}"] = campo
        # Solo se muestran los propios de la categoría (si ya se sabe); el JS de la plantilla los muestra al elegirla
        if self.categoria_fija:
            for clave in CAMPOS_EXTRA:
                if clave not in self.categoria_fija.campos:
                    del self.fields[f"extra_{clave}"]
            if "precio_desde" in self.fields:
                self.fields["precio_desde"].label = f"{self.categoria_fija.etiqueta_precio} (COP)"

    def clean_whatsapp(self):
        numero = _digitos(self.cleaned_data.get("whatsapp"))
        if numero and len(numero) not in (10, 12):
            raise forms.ValidationError("Escribe el celular de 10 dígitos (ej. 3001234567).")
        return numero

    def clean_telefono(self):
        return _digitos(self.cleaned_data.get("telefono"))

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and getattr(foto, "size", 0) > MAX_FOTO:
            raise forms.ValidationError("La foto debe pesar máximo 5 MB.")
        return foto

    def clean(self):
        datos = super().clean()
        if "whatsapp" in self.fields and not datos.get("whatsapp") and not datos.get("telefono"):
            self.add_error("whatsapp", "Pon al menos un WhatsApp o un teléfono para que los moteros te contacten.")
        if "abre" in self.fields and not datos.get("abierto_24h") and bool(datos.get("abre")) != bool(datos.get("cierra")):
            self.add_error("cierra", "Pon la hora de apertura y la de cierre, o marca 24 horas.")
        return datos

    def save(self, commit=True):
        obj = super().save(commit=False)
        categoria = self.cleaned_data.get("categoria") or self.categoria_fija
        extras = dict(obj.extras or {})
        for clave in CAMPOS_EXTRA:
            nombre = f"extra_{clave}"
            if nombre not in self.cleaned_data:
                continue
            if categoria and clave in categoria.campos and self.cleaned_data[nombre] not in ("", None, False):
                extras[clave] = self.cleaned_data[nombre]
            else:
                extras.pop(clave, None)
        obj.extras = extras
        if commit:
            obj.save()
        return obj


class AutoregistroForm(ProveedorForm):
    """«Soy proveedor»: pocos campos, pensado para el celular. La autorización de datos es obligatoria."""
    autoriza = forms.BooleanField(label=TEXTO_AUTORIZO,
                                  error_messages={"required": "Necesitamos tu autorización para publicar tu negocio."})

    class Meta(ProveedorForm.Meta):
        fields = CAMPOS_AUTOREGISTRO

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = Categoria.objects.filter(inscripcion=True)
        self.fields["categoria"].label = "¿Qué servicio ofreces?"
        self.fields["nombre"].label = "Nombre del negocio"


class RevisionForm(ProveedorForm):
    """El proveedor revisa lo que cargamos: corrige y, si marca la autorización, aprueba."""
    autoriza = forms.BooleanField(label=TEXTO_AUTORIZO, required=False)

    class Meta(ProveedorForm.Meta):
        fields = CAMPOS_REVISION


class CategoriaForm(EstiloMixin, forms.ModelForm):
    campos = forms.MultipleChoiceField(choices=CAMPOS_EXTRA_OPCIONES, required=False, widget=forms.CheckboxSelectMultiple,
                                       label="Campos propios", help_text="Solo si hacen falta; los comunes ya están.")

    class Meta:
        model = Categoria
        fields = ["nombre", "singular", "icono", "descripcion", "etiqueta_precio", "campos", "inscripcion", "orden"]
