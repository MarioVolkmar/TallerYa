"""Formularios de la hoja de vida: el registro propio del motero y el del taller con código."""
from django import forms
from django.utils import timezone

from talleres.forms import EstiloMixin
from talleres.models import Taller

from .forms import MAX_COSTO, MAX_KM, leer_pesos
from .hoja_vida import CodigoInvalido, buscar_codigo, registrar_verificado
from .models import RegistroServicio


def _fecha_no_futura(fecha):
    if fecha and fecha > timezone.localdate():
        raise forms.ValidationError("La fecha no puede ser futura.")
    return fecha


class RegistroPropioForm(EstiloMixin, forms.ModelForm):
    """Lo registra el dueño: queda como no verificado. Si elige qué mantenimiento del plan cubre, el plan se pone al día."""

    tarea = forms.ModelChoiceField(queryset=None, required=False, label="¿Qué mantenimiento del plan cubre? (opcional)",
                                   empty_label="Ninguno (solo anotarlo aquí)")
    costo = forms.CharField(label="Costo (opcional)", required=False, max_length=20,
                            widget=forms.TextInput(attrs={"inputmode": "numeric", "placeholder": "Ej: 85.000"}))

    class Meta:
        model = RegistroServicio
        fields = ["tarea", "fecha", "km", "servicios", "costo", "taller", "taller_otro", "notas"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "km": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0, "max": MAX_KM}),
            "servicios": forms.TextInput(attrs={"placeholder": "Ej: cambio de aceite y filtro, ajuste de cadena"}),
            "taller_otro": forms.TextInput(attrs={"placeholder": "Si no está en la lista"}),
            "notas": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }

    def __init__(self, *args, moto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["taller"].queryset = Taller.objects.filter(activo=True).only("nombre")
        self.fields["taller"].empty_label = "Lo hice yo / otro taller"
        self.fields["fecha"].widget.attrs["max"] = timezone.localdate().isoformat()
        if moto and not self.is_bound:
            self.fields["km"].initial = moto.km_actual
        self.moto = moto
        self.fields["servicios"].required = False  # basta con elegir el mantenimiento del plan
        from .models import TareaMantenimiento
        from .plan import calcular_plan
        ids = [t.tarea.pk for t in calcular_plan(moto).tareas] if moto else []
        self.fields["tarea"].queryset = TareaMantenimiento.objects.filter(pk__in=ids).order_by("orden", "nombre")

    def clean_fecha(self):
        return _fecha_no_futura(self.cleaned_data.get("fecha"))

    def clean_km(self):
        km = self.cleaned_data.get("km")
        if km is not None and km > MAX_KM:
            raise forms.ValidationError("Ese kilometraje es demasiado alto.")
        return km

    def clean_costo(self):
        return leer_pesos(self.cleaned_data.get("costo"))

    def clean(self):
        datos = super().clean()
        tarea = datos.get("tarea")
        if not datos.get("servicios"):
            if not tarea:
                self.add_error("servicios", "Escribe qué se le hizo o elige el mantenimiento del plan.")
            else:
                datos["servicios"] = self.instance.servicios = tarea.nombre[:300]
        if not datos.get("taller") and not datos.get("taller_otro"):
            datos["costo"] = self.instance.costo = None  # lo hizo el mismo motero: sin costo (los repuestos van en Gastos)
        km = datos.get("km")
        if tarea and self.moto and km is not None and km > self.moto.km_actual:
            self.add_error("km", f"Para poner al día el plan, no puede ser mayor que el kilometraje actual "
                                 f"({self.moto.km_actual:,} km). Actualiza primero el kilometraje.".replace(",", "."))
        return datos


class ServicioTallerForm(EstiloMixin, forms.Form):
    """Para el panel del taller: registra un servicio verificado con el código que le muestra el motero."""
    codigo = forms.CharField(label="Código del motero", max_length=12,
                             widget=forms.TextInput(attrs={"autocomplete": "off", "class": "campo uppercase",
                                                           "placeholder": "Ej: K7P2QM"}))
    fecha = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    km = forms.IntegerField(label="Kilometraje", min_value=0, max_value=MAX_KM,
                            widget=forms.NumberInput(attrs={"inputmode": "numeric"}))
    servicios = forms.CharField(label="Qué se le hizo", max_length=300)
    costo = forms.IntegerField(label="Costo (COP)", min_value=0, max_value=MAX_COSTO, required=False,
                               widget=forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "Opcional"}))
    notas = forms.CharField(max_length=300, required=False)

    def __init__(self, *args, taller=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.taller = taller
        self.codigo_obj = None

    def clean_codigo(self):
        self.codigo_obj = buscar_codigo(self.cleaned_data["codigo"])
        if not self.codigo_obj:
            raise forms.ValidationError("El código no es válido o ya caducó. Pídele al motero uno nuevo.")
        return self.cleaned_data["codigo"]

    def clean_fecha(self):
        return _fecha_no_futura(self.cleaned_data.get("fecha"))

    def guardar(self):
        datos = self.cleaned_data
        try:
            return registrar_verificado(self.taller, datos["codigo"], fecha=datos["fecha"], km=datos["km"],
                                        servicios=datos["servicios"], notas=datos["notas"], costo=datos["costo"])
        except CodigoInvalido as e:
            self.add_error("codigo", str(e))
            return None
