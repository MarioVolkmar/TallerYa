from itertools import groupby

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from talleres.forms import EstiloMixin
from talleres.models import Taller

from .colores_fabrica import color_por_defecto
from .models import COLORES, LineaMoto, Mantenimiento, Moto, TareaMantenimiento

OTRA = "otra"
ANIO_MINIMO = 1980
MAX_KM = 999_999


EXTENSIONES_DOCUMENTO = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
MAX_DOCUMENTO = 5 * 1024 * 1024  # 5 MB


def validar_documento(archivo):
    from pathlib import Path
    if Path(archivo.name).suffix.lower() not in EXTENSIONES_DOCUMENTO:
        raise forms.ValidationError("Sube una foto (JPG, PNG o WEBP) o un PDF.")
    if archivo.size > MAX_DOCUMENTO:
        raise forms.ValidationError("El archivo pesa más de 5 MB. Prueba con un pantallazo.")
    inicio = archivo.read(8)
    archivo.seek(0)
    firmas = (b"\xff\xd8\xff", b"\x89PNG", b"%PDF", b"RIFF")
    if not inicio.startswith(firmas):
        raise forms.ValidationError("Ese archivo no parece una imagen o un PDF.")
    return archivo


class MotoForm(EstiloMixin, forms.ModelForm):
    linea_catalogo = forms.ChoiceField(label="Marca y línea")
    # Sin color preseleccionado: si no elige ninguno, queda el de fábrica más común de la línea (colores_fabrica.py)
    color = forms.ChoiceField(choices=COLORES, widget=forms.RadioSelect, required=False)
    km_actual = forms.IntegerField(
        label="Kilometraje actual", min_value=0, max_value=MAX_KM,
        error_messages={"min_value": "El kilometraje no puede ser negativo.",
                        "max_value": "Ese kilometraje es demasiado alto. Revisa el número."},
        widget=forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 12500", "min": 0, "max": MAX_KM,
                                        "step": 1, "data-validar-km": "1", "autocomplete": "off"}))

    class Meta:
        model = Moto
        fields = ["marca_otra", "linea_otra", "tipo_otra", "modelo", "color", "perfil_uso", "apodo", "placa",
                  "soat_vence", "soat_archivo", "tecno_vence", "tecno_archivo", "matricula"]
        widgets = {
            "modelo": forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 2021"}),
            "placa": forms.TextInput(attrs={"placeholder": "Ej: ABC12D", "autocomplete": "off", "maxlength": 8,
                                            "data-validar-placa": "1", "class": "campo uppercase"}),
            "soat_vence": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "tecno_vence": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "matricula": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "soat_archivo": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp,application/pdf"}),
            "tecno_archivo": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp,application/pdf"}),
        }

    quitar_soat = forms.BooleanField(required=False, label="Quitar el archivo del SOAT")
    quitar_tecno = forms.BooleanField(required=False, label="Quitar el archivo de la técnico-mecánica")

    def clean_soat_archivo(self):
        return self._documento("soat_archivo")

    def clean_tecno_archivo(self):
        return self._documento("tecno_archivo")

    def _documento(self, campo):
        # Solo se revisa lo que se acaba de subir; el archivo que ya estaba guardado se deja igual.
        archivo = self.cleaned_data.get(campo)
        return validar_documento(archivo) if isinstance(archivo, UploadedFile) else archivo

    def save(self, commit=True):
        # Borra del disco los archivos reemplazados o quitados.
        anteriores = {}
        if self.instance.pk:
            previa = Moto.objects.get(pk=self.instance.pk)
            anteriores = {c: getattr(previa, f"{c}_archivo") for c in ("soat", "tecno")}
        for clave in ("soat", "tecno"):
            if self.cleaned_data.get(f"quitar_{clave}") and f"{clave}_archivo" not in self.files:
                setattr(self.instance, f"{clave}_archivo", None)
        moto = super().save(commit=commit)
        if commit:
            for clave, viejo in anteriores.items():
                nuevo = getattr(moto, f"{clave}_archivo")
                if viejo and viejo.name != (nuevo.name if nuevo else None):
                    viejo.storage.delete(viejo.name)
        return moto

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uso = self.fields["perfil_uso"]  # Django no pone mayúscula tras «¿» y deja «---------» como opción vacía
        uso.label = "¿Cómo la usas?"
        uso.choices = [("", "Elige una opción")] + [c for c in uso.choices if c[0]]
        lineas = LineaMoto.objects.filter(activo=True).select_related("marca")
        opciones = [("", "Elige tu moto")]
        for marca, grupo in groupby(lineas, key=lambda l: l.marca.nombre):
            opciones.append((marca, [(str(l.pk), l.nombre) for l in grupo]))
        opciones.append((OTRA, "Mi moto no está en la lista"))
        self.fields["linea_catalogo"].choices = opciones
        self.fields["linea_catalogo"].widget.attrs["class"] = "campo"
        self.fields["tipo_otra"].choices = [("", "Elige el tipo")] + list(self.fields["tipo_otra"].choices)[1:]
        if self.instance.pk:
            self.fields["linea_catalogo"].initial = str(self.instance.linea_id) if self.instance.linea_id else OTRA
            self.fields.pop("km_actual")  # el kilometraje se actualiza aparte
            self.fields.pop("color")      # el color se cambia en "Personalizar", con vista previa en 3D
        # Año razonable: de 1980 al modelo del año siguiente (se valida también en el navegador).
        self.fields["modelo"].widget.attrs.update({
            "min": ANIO_MINIMO, "max": timezone.localdate().year + 1, "maxlength": 4,
            "data-validar-anio": "1", "autocomplete": "off",
        })

    def clean_matricula(self):
        fecha = self.cleaned_data.get("matricula")
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError("La fecha de matrícula no puede ser futura.")
        return fecha

    def clean_placa(self):
        # Solo letras y números, en mayúsculas (se aceptan otros formatos: motocarros, placas antiguas).
        placa = "".join(c for c in self.cleaned_data.get("placa", "").upper() if c.isalnum())
        if placa and not 5 <= len(placa) <= 7:
            raise forms.ValidationError("Revisa la placa: debería tener entre 5 y 7 letras y números (ej: ABC12D).")
        return placa

    def clean_modelo(self):
        anio = self.cleaned_data["modelo"]
        maximo = timezone.localdate().year + 1
        if not ANIO_MINIMO <= anio <= maximo:
            raise forms.ValidationError(f"El modelo debe estar entre {ANIO_MINIMO} y {maximo}.")
        return anio

    def clean(self):
        datos = super().clean()
        eleccion = datos.get("linea_catalogo")
        if eleccion == OTRA:
            for campo in ("marca_otra", "linea_otra", "tipo_otra"):
                if not datos.get(campo):
                    self.add_error(campo, "Completa este dato.")
            self.instance.linea = None
        elif eleccion:
            linea = LineaMoto.objects.filter(pk=eleccion, activo=True).first()
            if not linea:
                self.add_error("linea_catalogo", "Elige una línea de la lista.")
            self.instance.linea = linea
            datos["marca_otra"] = datos["linea_otra"] = datos["tipo_otra"] = ""
        if "color" in self.fields and not datos.get("color"):
            datos["color"] = color_por_defecto(str(self.instance.linea) if self.instance.linea else "")
        return datos


class LecturaForm(EstiloMixin, forms.Form):
    km = forms.IntegerField(label="Kilometraje de hoy", min_value=0, max_value=MAX_KM,
                            widget=forms.NumberInput(attrs={"inputmode": "numeric"}))

    def __init__(self, *args, moto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.moto = moto
        if moto:
            self.fields["km"].widget.attrs["placeholder"] = f"Último: {moto.km_actual}"
            self.fields["km"].widget.attrs["min"] = moto.km_actual

    def clean_km(self):
        km = self.cleaned_data["km"]
        if self.moto and km < self.moto.km_actual:
            raise forms.ValidationError(f"No puede ser menor que el último registro ({self.moto.km_actual} km).")
        if self.moto and km - self.moto.km_actual > 50_000:
            raise forms.ValidationError("Ese salto es muy grande. Revisa el número.")
        return km


MAX_COSTO = 50_000_000  # COP: más que esto es casi seguro un error de digitación


def leer_pesos(texto):
    """'85.000', '$ 85 000' o '85000' → 85000. None si está vacío. Error si es negativo, no es número o es enorme."""
    texto = (texto or "").strip()
    if not texto:
        return None
    if "-" in texto:
        raise forms.ValidationError("El precio no puede ser negativo.")
    digitos = "".join(c for c in texto.split(",")[0] if c.isdigit())
    if not digitos or any(c.isalpha() for c in texto):
        raise forms.ValidationError("Escribe el precio en pesos, solo números.")
    valor = int(digitos)
    if valor > MAX_COSTO:
        raise forms.ValidationError("Ese valor es demasiado alto. Revisa el número.")
    return valor


class MantenimientoForm(EstiloMixin, forms.ModelForm):
    # Precio (opcional, COP): solo si lo hizo un taller. Se guarda en el registro de la hoja de vida → Gastos lo suma una vez.
    precio = forms.CharField(label="Precio (opcional)", required=False, max_length=20,
                             widget=forms.TextInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 85.000"}))

    class Meta:
        model = Mantenimiento
        fields = ["tarea", "km", "fecha", "taller", "taller_otro", "notas"]
        labels = {"km": "Kilometraje cuando se hizo", "taller": "Taller (opcional)", "notas": "Notas (opcional)"}
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"}), "tarea": forms.HiddenInput,
                   "km": forms.NumberInput(attrs={"inputmode": "numeric"})}

    OTRO = "otro"  # valor del menú para "Otro taller (fuera de TallerYa)"

    def __init__(self, *args, **kwargs):
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        self.fields["fecha"].widget.attrs["max"] = timezone.localdate().isoformat()  # no se registra algo que aún no pasó

    def __init__(self, data=None, *args, moto=None, **kwargs):
        if data is not None and data.get("taller") == self.OTRO:
            data = data.copy()
            data["taller"] = ""
            data["taller_otro"] = (data.get("taller_otro") or "").strip() or "Otro taller"
        super().__init__(data, *args, **kwargs)
        self.moto = moto
        self.fields["taller"].queryset = Taller.objects.filter(activo=True)
        self.fields["tarea"].queryset = TareaMantenimiento.objects.filter(activo=True)
        # Con fecha pero sin kilometraje: lo estimamos con las lecturas de la moto (ver clean)
        self.fields["km"].required = False

    def clean_km(self):
        km = self.cleaned_data["km"]
        if km is not None and self.moto and km > self.moto.km_actual:
            raise forms.ValidationError(f"No puede ser mayor que el kilometraje actual ({self.moto.km_actual} km). "
                                        "Actualiza primero el kilometraje.")
        return km

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha > timezone.localdate():
            raise forms.ValidationError("La fecha no puede ser futura.")
        return fecha

    def clean_precio(self):
        return leer_pesos(self.cleaned_data.get("precio"))

    def clean(self):
        datos = super().clean()
        if datos.get("taller"):
            datos["taller_otro"] = ""  # si eligió un taller de TallerYa, el nombre libre sobra
        if not datos.get("taller") and not datos.get("taller_otro"):
            datos["precio"] = None  # "Lo hice yo": no se guarda precio
        if datos.get("km") is None and "km" not in self.errors:
            if not (self.moto and datos.get("fecha")):
                self.add_error("km", "Escribe el kilometraje, o al menos la fecha para estimarlo.")
            else:
                from .plan import MARCA_KM_ESTIMADO, km_en_fecha
                datos["km"] = km_en_fecha(self.moto, datos["fecha"])
                marca = f"({MARCA_KM_ESTIMADO}o por la fecha)"
                datos["notas"] = f"{(datos.get('notas') or '')[:200 - len(marca) - 1]} {marca}".strip()
        return datos
