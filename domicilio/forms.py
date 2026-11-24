from django import forms

from talleres import perfil as perfil_taller
from talleres.forms import EstiloMixin
from talleres.subidas import IMAGENES, tipo_real
from talleres.utils import normalizar_celular

from .models import FotoTrabajo, MecanicoDomicilio, PrecioMecanico, ResenaMecanico, TallerDomicilio

MAX_FOTO = 5 * 1024 * 1024  # antes de recortar; se guarda un JPEG de 480x480

# Pasos del alta (registro.html los muestra uno a uno en el celular). El paso «cuenta» solo si no hay sesión.
# Lo mínimo para publicar va a la vista; lo opcional, en el bloque plegado «Completa tu perfil».
PASO_TRABAJO = ["nombre", "whatsapp", "zona_modo", "zonas", "servicios", "tarifa_visita", "anios_experiencia", "urgencias"]
PASO_VERIFICACION = ["cedula"]
PASO_OPCIONAL = ["foto", "descripcion", "marcas", "horario", "referencias"]

# Atajos del selector de zonas: «Toda Medellín» = las zonas con ciudad Medellín; «Todo el Valle» = todas.
ZONA_MEDELLIN, ZONA_VALLE, ZONA_ELEGIR = "medellin", "valle", "elegir"


class PesosField(forms.IntegerField):
    """Entero en pesos que acepta «$ 25.000» o «25,000» (el JS pone los puntos de miles al escribir)."""
    def to_python(self, value):
        if isinstance(value, str):
            value = "".join(c for c in value if c.isdigit())
        return super().to_python(value)


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


class ZonasAtajoMixin(forms.Form):
    """Selector de zonas del alta del mecánico y del servicio a domicilio del taller: tres atajos («Toda Medellín»,
    «Todo el Valle», «Elegir zonas») más las casillas reales de `zonas` (se usan con «Elegir» o sin JS).
    También trae la tarifa con «$» y puntos de miles."""
    zona_modo = forms.ChoiceField(
        label="¿Dónde atiendes?", required=False, widget=forms.RadioSelect,
        choices=[(ZONA_MEDELLIN, "Toda Medellín"), (ZONA_VALLE, "Todo el Valle"), (ZONA_ELEGIR, "Elegir zonas")])
    tarifa_visita = PesosField(
        label="Tarifa de visita", required=False, min_value=0, max_value=2_000_000,
        help_text="Orientativa: el precio final lo acuerdas con el cliente.",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off", "placeholder": "25.000"}))

    def iniciar_zonas(self):
        if "zona_modo" in self.fields:
            self.fields["zonas"].required = False  # se exige en limpiar_zonas(), según el atajo elegido
            if self.instance.pk and not self.is_bound:
                self.initial.setdefault("zona_modo", self.modo_de(set(self.instance.zonas.values_list("pk", flat=True))))

    @staticmethod
    def zonas_del_modo(modo):
        from .models import Zona
        if modo == ZONA_MEDELLIN:
            return Zona.objects.filter(ciudad="Medellín")
        return Zona.objects.all() if modo == ZONA_VALLE else None

    @classmethod
    def modo_de(cls, pks):
        """El atajo que corresponde a unas zonas guardadas (para mostrarlo al editar)."""
        for modo in (ZONA_MEDELLIN, ZONA_VALLE):
            if pks and pks == set(cls.zonas_del_modo(modo).values_list("pk", flat=True)):
                return modo
        return ZONA_ELEGIR if pks else ""

    def limpiar_zonas(self, datos, exigir=True):
        if "zona_modo" not in self.fields:
            return
        atajo = self.zonas_del_modo(datos.get("zona_modo"))
        if atajo is not None:
            datos["zonas"] = atajo
        elif exigir and not datos.get("zonas") and "zonas" not in self.errors:
            self.add_error("zonas", "Elige dónde atiendes.")


class PerfilMecanicoForm(ZonasAtajoMixin, EstiloMixin, forms.ModelForm):
    """Lo que el mecánico llena al registrarse y puede cambiar después. Estado y «verificado» solo los toca el equipo."""
    # Más largo que el campo del modelo: acepta «+57 300 123 4567» y clean_whatsapp lo deja en 573001234567
    whatsapp = forms.CharField(
        label="WhatsApp o celular", max_length=20,
        help_text="Aquí te escriben los motociclistas.",
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "300 123 4567"}))
    # No es campo del modelo: se guarda solo su huella HMAC y los 4 últimos dígitos (MecanicoDomicilio.poner_cedula)
    cedula = forms.CharField(
        label="Número de cédula", max_length=15, required=True,
        help_text="No se publica ni se guarda completa (solo los 4 últimos dígitos).",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off", "placeholder": "1020304050"}))


    class Meta:
        model = MecanicoDomicilio
        fields = ["nombre", "whatsapp", "zonas", "servicios", "anios_experiencia", "urgencias", "tarifa_visita",
                  "cedula", "foto", "descripcion", "referencias", "horario", "marcas", "multimarca"]
        labels = {"nombre": "Nombre visible", "foto": "Foto (tu cara o tú trabajando)",
                  "zonas": "¿Dónde atiendes?", "servicios": "¿Qué trabajos haces a domicilio?",
                  "marcas": "Marcas que mejor conoces", "tarifa_visita": "Tarifa de visita orientativa",
                  "horario": "Horario", "descripcion": "Cuéntale a los moteros tu experiencia",
                  "referencias": "Referencias"}
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
        self.fields["anios_experiencia"].required = False
        self.iniciar_zonas()
        if self.instance.pk and self.instance.cedula_ultimos:  # editar: la cédula ya está; solo se cambia si escribe otra
            self.fields["cedula"].required = False
            self.fields["cedula"].help_text = (f"Registrada (termina en {self.instance.cedula_ultimos}). "
                                               "Déjalo vacío para conservarla.")

    def clean_anios_experiencia(self):
        return self.cleaned_data.get("anios_experiencia") or 0  # opcional en el alta: vacío = 0

    def clean_whatsapp(self):
        return normalizar_celular(self.cleaned_data["whatsapp"])

    def clean(self):
        datos = super().clean()
        self.limpiar_zonas(datos)
        return datos

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
        widgets = {"desde": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off", "placeholder": "50.000"}),
                   "hasta": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off", "placeholder": "100.000"})}

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

    return forms.inlineformset_factory(MecanicoDomicilio, PrecioMecanico, form=Form, formset=_PreciosBase, extra=0,
                                       can_delete=True, max_num=40)


class ResenaMecanicoForm(EstiloMixin, forms.ModelForm):
    estrellas = forms.TypedChoiceField(choices=[(i, "★" * i) for i in range(5, 0, -1)], coerce=int)

    class Meta:
        model = ResenaMecanico
        fields = ["estrellas", "comentario"]
        labels = {"comentario": "¿Cómo te fue?"}
        widgets = {"comentario": forms.Textarea(attrs={"rows": 3, "maxlength": 600})}


class TallerDomicilioForm(ZonasAtajoMixin, EstiloMixin, forms.ModelForm):
    """Lo que el taller llena para salir también en Mecánicos a domicilio."""

    class Meta:
        model = TallerDomicilio
        fields = ["activo", "zonas", "servicios", "urgencias", "tarifa_visita"]  # + zona_modo (ZonasAtajoMixin)
        labels = {"activo": "También atiendo a domicilio", "zonas": "¿A qué zonas vas?",
                  "servicios": "¿Qué trabajos haces a domicilio?", "tarifa_visita": "Tarifa de visita orientativa"}
        help_texts = {"tarifa_visita": "En pesos, sin puntos. Es una referencia: el precio final lo acuerdas con el cliente."}
        widgets = {
            "zonas": forms.CheckboxSelectMultiple, "servicios": forms.CheckboxSelectMultiple,
            "tarifa_visita": forms.NumberInput(attrs={"min": 0, "step": 1000, "placeholder": "25000"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iniciar_zonas()

    def clean(self):
        datos = super().clean()
        self.limpiar_zonas(datos, exigir=False)
        if datos.get("activo"):
            if not datos.get("zonas"):
                self.add_error("zonas", "Elige al menos una zona para salir en el listado.")
            if not datos.get("servicios"):
                self.add_error("servicios", "Elige al menos un servicio.")
        return datos


class IdentidadForm(forms.Form):
    """Fotos de la cédula: frente y respaldo obligatorios, selfie con la cédula opcional. Imagen real, menos de 5 MB,
    re-codificada sin metadatos y reducida (mismo tratamiento que las fotos de verificación de domiciliarios)."""
    frente = forms.FileField(label="Cédula, frente", widget=forms.FileInput(attrs={"accept": "image/*", "class": "campo"}),
                             error_messages={"required": "Falta la foto del frente de tu cédula."})
    respaldo = forms.FileField(label="Cédula, respaldo", widget=forms.FileInput(attrs={"accept": "image/*", "class": "campo"}),
                               error_messages={"required": "Falta la foto del respaldo de tu cédula."})
    selfie = forms.FileField(label="Selfie con la cédula (opcional)", required=False,
                             widget=forms.FileInput(attrs={"accept": "image/*", "capture": "user", "class": "campo"}))
    autorizo = forms.BooleanField(
        label="Autorizo a TallerYa a usar estas fotos solo para verificar mi identidad",
        error_messages={"required": "Marca la autorización para poder enviar las fotos."})

    def _foto(self, campo):
        from domiciliarios.forms import _imagen
        return _imagen(self.cleaned_data.get(campo))

    def clean_frente(self):
        return self._foto("frente")

    def clean_respaldo(self):
        return self._foto("respaldo")

    def clean_selfie(self):
        return self._foto("selfie")
