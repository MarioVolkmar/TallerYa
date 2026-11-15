"""Formulario del taller para registrar el servicio hecho a una moto (desde la cita, con código/QR o por placa)."""
from django import forms
from django.utils import timezone

from talleres.forms import EstiloMixin

from .forms import MAX_KM, leer_pesos
from .forms_hoja_vida import _fecha_no_futura
from .models import TareaMantenimiento

MAX_FOTO = 6 * 1024 * 1024


class ServicioHechoForm(EstiloMixin, forms.Form):
    tareas = forms.ModelMultipleChoiceField(queryset=TareaMantenimiento.objects.none(), required=False,
                                            widget=forms.CheckboxSelectMultiple, label="Qué se le hizo")
    otros = forms.CharField(label="Otros trabajos", max_length=200, required=False,
                            widget=forms.TextInput(attrs={"placeholder": "Ej: ajuste de clutch, cambio de bombillo"}))
    km = forms.IntegerField(label="Kilometraje de la moto", min_value=0, max_value=MAX_KM,
                            widget=forms.NumberInput(attrs={"inputmode": "numeric"}))
    fecha = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    costo = forms.CharField(label="Valor cobrado (opcional)", required=False, max_length=20,
                            widget=forms.TextInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 85.000"}))
    notas = forms.CharField(label="Nota para el dueño (opcional)", max_length=300, required=False,
                            widget=forms.TextInput(attrs={"placeholder": "Ej: las pastillas traseras van a la mitad"}))
    foto = forms.ImageField(label="Foto (opcional)", required=False,
                            widget=forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"}))

    def __init__(self, *args, moto=None, tareas=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.moto = moto
        self.fields["tareas"].queryset = TareaMantenimiento.objects.filter(pk__in=[t.pk for t in tareas])
        orden = {t.pk: i for i, t in enumerate(tareas)}
        self.fields["tareas"].choices = sorted(self.fields["tareas"].choices, key=lambda c: orden.get(int(str(c[0])), 0))
        self.fields["fecha"].widget.attrs["max"] = timezone.localdate().isoformat()
        if moto and not self.is_bound:
            self.fields["km"].initial = moto.km_actual

    def clean_fecha(self):
        return _fecha_no_futura(self.cleaned_data.get("fecha"))

    def clean_costo(self):
        return leer_pesos(self.cleaned_data.get("costo"))

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and foto.size > MAX_FOTO:
            raise forms.ValidationError("La foto pesa más de 6 MB.")
        return foto

    def clean(self):
        datos = super().clean()
        if not datos.get("tareas") and not (datos.get("otros") or "").strip():
            raise forms.ValidationError("Marca al menos un trabajo del plan o escribe qué se le hizo.")
        return datos

    def datos(self):
        d = self.cleaned_data
        return {"fecha": d["fecha"], "km": d["km"], "tareas": list(d["tareas"]), "otros": d["otros"].strip(),
                "costo": d["costo"], "notas": d["notas"].strip(), "foto": d.get("foto") or None}
