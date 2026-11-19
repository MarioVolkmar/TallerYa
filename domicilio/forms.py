from django import forms

from talleres import perfil as perfil_taller
from talleres.forms import EstiloMixin
from talleres.subidas import IMAGENES, tipo_real
from talleres.utils import normalizar_celular

from .models import FotoTrabajo, MecanicoDomicilio, PrecioMecanico, ResenaMecanico, TallerDomicilio

MAX_FOTO = 5 * 1024 * 1024  # antes de recortar; se guarda un JPEG de 480x480

# Pasos del alta (registro.html los muestra uno a uno en el celular). El paso «cuenta» solo si no hay sesión.
PASO_TRABAJO = ["nombre", "whatsapp", "zonas", "servicios", "anios_experiencia", "urgencias", "tarifa_visita"]
PASO_VERIFICACION = ["cedula", "foto", "descripcion", "referencias", "horario", "marcas"]


def foto_trabajo(archivo):
    """Foto de un trabajo: se valida el contenido real y se guarda como JPEG nuevo de máx. 1200 px (sin EXIF)."""
    from io import BytesIO

    from django.core.files.base import ContentFile
    from PIL import Image, ImageOps

    if archivo.size > MAX_FOTO or not tipo_real(archivo, IMAGENES):
        return None
    imagen = ImageOps.exif_transpose(Image.open(archivo)).convert("RGB")
    imagen.thumbnail((1200, 1200), Image.LANCZOS)
    salida = BytesIO()
    imagen.save(salida, "JPEG", quality=84, optimize=True)
    return ContentFile(salida.getvalue(), name="trabajo.jpg")


class PerfilMecanicoForm(EstiloMixin, forms.ModelForm):
    """Lo que el mecánico llena al registrarse y puede cambiar después. Estado y «verificado» solo los toca el equipo."""
    # Más largo que el campo del modelo: acepta «+57 300 123 4567» y clean_whatsapp lo deja en 573001234567
    whatsapp = forms.CharField(
        label="WhatsApp o celular", max_length=20,
        help_text="10 dígitos, ej: 3001234567. Los motociclistas te escriben a este número.",
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "3001234567"}))
    # No es campo del modelo: se guarda solo su huella HMAC y los 4 últimos dígitos (MecanicoDomicilio.poner_cedula)
    cedula = forms.CharField(
        label="Número de cédula", max_length=15, required=True,
        help_text="Solo para verificar tu identidad: no se publica ni se guarda completo (solo los 4 últimos dígitos).",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off", "placeholder": "1020304050"}))

    class Meta:
        model = MecanicoDomicilio
        fields = ["nombre", "whatsapp", "zonas", "servicios", "anios_experiencia", "urgencias", "tarifa_visita",
                  "cedula", "foto", "descripcion", "referencias", "horario", "marcas"]
        labels = {"nombre": "Nombre visible", "foto": "Foto (tu cara o tú trabajando)",
                  "zonas": "¿Dónde atiendes?", "servicios": "¿Qué trabajos haces a domicilio?",
                  "marcas": "Marcas que mejor conoces (opcional)", "tarifa_visita": "Tarifa de visita orientativa",
                  "horario": "Horario (opcional)", "descripcion": "Cuéntale a los moteros tu experiencia",
                  "referencias": "Referencias (opcional, ayudan a verificarte)"}
        help_texts = {"whatsapp": "10 dígitos, ej: 3001234567. Los motociclistas te escriben a este número.",
                      "tarifa_visita": "En pesos, sin puntos. Es una referencia: el precio final lo acuerdas con el cliente."}
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Jhon Fredy · Mecánico a domicilio"}),
            "foto": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "whatsapp": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "3001234567"}),
            "zonas": forms.CheckboxSelectMultiple,
            "servicios": forms.CheckboxSelectMultiple,
            "marcas": forms.CheckboxSelectMultiple,
            "anios_experiencia": forms.NumberInput(attrs={"min": 0, "max": 60}),
            "horario": forms.TextInput(attrs={"placeholder": "Ej: Lun-Sáb 7am-6pm"}),
            "tarifa_visita": forms.NumberInput(attrs={"min": 0, "step": 1000, "placeholder": "25000"}),
            "referencias": forms.Textarea(attrs={"rows": 2, "maxlength": 400,
                                                 "placeholder": "Ej: Carlos Pérez, cliente, 3001112233 · Taller La 80, 3004445566"}),
            "descripcion": forms.Textarea(attrs={"rows": 4, "maxlength": 600,
                                                 "placeholder": "Ej: 12 años en motos de trabajo y scooters. Llevo herramienta "
                                                                "y escáner. Si el daño es grande, te recomiendo taller."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.cedula_ultimos:  # editar: la cédula ya está; solo se cambia si escribe otra
            self.fields["cedula"].required = False
            self.fields["cedula"].help_text = (f"Registrada (termina en {self.instance.cedula_ultimos}). "
                                               "Déjalo vacío para conservarla.")

    def clean_whatsapp(self):
        return normalizar_celular(self.cleaned_data["whatsapp"])

    def clean_cedula(self):
        valor = self.cleaned_data.get("cedula", "")
        digitos = "".join(c for c in valor if c.isdigit())
        if not valor.strip():
            return ""
        if not 5 <= len(digitos) <= 11 or any(c not in "0123456789 .-" for c in valor):
            raise forms.ValidationError("Escribe solo el número de la cédula (entre 5 y 11 dígitos).")
        return digitos

    def save(self, commit=True):
        mecanico = super().save(commit=False)
        if self.cleaned_data.get("cedula"):
            mecanico.poner_cedula(self.cleaned_data["cedula"])
        if commit:
            mecanico.save()
            self.save_m2m()
        return mecanico

    def campos(self, nombres):
        return [self[n] for n in nombres]

    def clean_foto(self):
        """Mismo criterio que las demás subidas: se mira el contenido real (no el nombre ni el Content-Type), y la
        foto se vuelve a codificar como JPEG cuadrado (sin EXIF, sin lo que traiga escondido el archivo original)."""
        foto = self.cleaned_data.get("foto")
        if not foto or foto == getattr(self.instance, "foto", None):
            return foto  # sin cambios
        if foto.size > MAX_FOTO:
            raise forms.ValidationError("La foto debe pesar máximo 5 MB.")
        if not tipo_real(foto, IMAGENES):
            raise forms.ValidationError("Sube una foto JPG, PNG o WEBP.")
        from cuentas.forms import foto_cuadrada
        return foto_cuadrada(foto, lado=480)


class EdicionMecanicoForm(PerfilMecanicoForm):
    """Mi perfil: lo del alta más lo que completa la ficha (las mismas listas cerradas que el perfil del taller).
    No va en el alta para que esta siga corta."""
    especialidades = forms.MultipleChoiceField(choices=perfil_taller.ESPECIALIDADES, required=False,
                                               widget=forms.CheckboxSelectMultiple, label="¿En qué eres bueno?")
    compromisos = forms.MultipleChoiceField(choices=[(c, t) for c, t, _ in perfil_taller.COMPROMISOS], required=False,
                                            widget=forms.CheckboxSelectMultiple, label="¿Cómo trabajas?")
    garantia_meses = forms.TypedChoiceField(
        label="Garantía en mano de obra", required=False, coerce=int, empty_value=None,
        choices=[("", "Sin garantía fija"), (1, "1 mes"), (2, "2 meses"), (3, "3 meses"), (6, "6 meses")])

    class Meta(PerfilMecanicoForm.Meta):
        fields = PerfilMecanicoForm.Meta.fields + ["especialidades", "herramientas", "garantia_meses", "compromisos"]
        widgets = {**PerfilMecanicoForm.Meta.widgets,
                   "herramientas": forms.TextInput(attrs={"placeholder": "Ej: escáner, multímetro, compresor, gato de moto"})}

    def clean_herramientas(self):
        """«escáner, multímetro» → «Escáner, Multímetro» (mayúscula inicial, sin repetidos ni vacíos)."""
        vistos, lista = set(), []
        for h in self.cleaned_data.get("herramientas", "").split(","):
            h = " ".join(h.split())
            if h and h.lower() not in vistos:
                vistos.add(h.lower())
                lista.append(h[:1].upper() + h[1:])
        return ", ".join(lista)[:200]


class PrecioMecanicoForm(EstiloMixin, forms.ModelForm):
    """Igual que talleres.forms.PrecioServicioForm, con los servicios a domicilio del mecánico."""
    class Meta:
        model = PrecioMecanico
        fields = ["servicio", "cilindraje", "desde", "hasta"]
        widgets = {"desde": forms.NumberInput(attrs={"min": 0, "step": 1000, "placeholder": "50000"}),
                   "hasta": forms.NumberInput(attrs={"min": 0, "step": 1000, "placeholder": "100000"})}

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde is not None and hasta is not None and hasta < desde:
            self.add_error("hasta", "El 'hasta' debe ser mayor o igual al 'desde'.")
        if hasta and hasta > 20_000_000:
            self.add_error("hasta", "Revisa la cifra: parece demasiado alta.")
        return datos


def precios_formset(mecanico):
    from talleres.forms import _PreciosBase  # misma validación: sin servicio+cilindraje repetidos

    class Form(PrecioMecanicoForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["servicio"].queryset = mecanico.servicios.all()
            self.fields["servicio"].empty_label = "Elige el servicio"

    return forms.inlineformset_factory(MecanicoDomicilio, PrecioMecanico, form=Form, formset=_PreciosBase, extra=3,
                                       can_delete=True, max_num=40)


class ResenaMecanicoForm(EstiloMixin, forms.ModelForm):
    estrellas = forms.TypedChoiceField(choices=[(i, "★" * i) for i in range(5, 0, -1)], coerce=int)

    class Meta:
        model = ResenaMecanico
        fields = ["estrellas", "comentario"]
        labels = {"comentario": "¿Cómo te fue?"}
        widgets = {"comentario": forms.Textarea(attrs={"rows": 3, "maxlength": 600})}


class TallerDomicilioForm(EstiloMixin, forms.ModelForm):
    """Lo que el taller llena para salir también en Mecánicos a domicilio."""

    class Meta:
        model = TallerDomicilio
        fields = ["activo", "zonas", "servicios", "urgencias", "tarifa_visita"]
        labels = {"activo": "También atiendo a domicilio", "zonas": "¿A qué zonas vas?",
                  "servicios": "¿Qué trabajos haces a domicilio?", "tarifa_visita": "Tarifa de visita orientativa"}
        help_texts = {"tarifa_visita": "En pesos, sin puntos. Es una referencia: el precio final lo acuerdas con el cliente."}
        widgets = {
            "zonas": forms.CheckboxSelectMultiple, "servicios": forms.CheckboxSelectMultiple,
            "tarifa_visita": forms.NumberInput(attrs={"min": 0, "step": 1000, "placeholder": "25000"}),
        }

    def clean(self):
        datos = super().clean()
        if datos.get("activo"):
            if not datos.get("zonas"):
                self.add_error("zonas", "Elige al menos una zona para salir en el listado.")
            if not datos.get("servicios"):
                self.add_error("servicios", "Elige al menos un servicio.")
        return datos
