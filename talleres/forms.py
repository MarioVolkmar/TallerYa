from django import forms

from . import perfil
from .models import CIUDADES, Barrio, PrecioServicio, Resena, Servicio, SolicitudCita, Taller
from .utils import normalizar_celular

INPUT = "campo"


def hora_texto(h):
    return f"{h.hour % 12 or 12}:{h.minute:02d} {'a. m.' if h.hour < 12 else 'p. m.'}" if h else ""  # estilos en talleres/static/talleres/css/tallerya.css


class EstiloMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            if not isinstance(f.widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                f.widget.attrs.setdefault("class", INPUT)


class SolicitudCitaForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = SolicitudCita
        fields = ["nombre", "telefono", "moto", "servicio", "fecha_preferida", "detalle"]
        widgets = {
            "fecha_preferida": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),  # <input type=date> exige ISO
            "detalle": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, taller=None, **kwargs):
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        self.fields["fecha_preferida"].widget.attrs["min"] = timezone.localdate().isoformat()
        self.taller = taller
        if taller:
            self.fields["servicio"].queryset = taller.servicios.all()
        if taller and taller.agenda_activa:
            # Reserva por franjas: la hora es obligatoria y debe estar libre (el JS cambia la lista al cambiar el día)
            from .agenda import franjas_libres, proxima_fecha_libre
            self.fields["fecha_preferida"].label = "Día"
            fecha = self._fecha_elegida()
            if fecha is None and not self.is_bound:
                fecha = proxima_fecha_libre(taller)
                if fecha:
                    self.initial.setdefault("fecha_preferida", fecha)
            opciones = [(h.strftime("%H:%M"), hora_texto(h)) for h, _ in franjas_libres(taller, fecha)] if fecha else []
            self.fields["hora"] = forms.ChoiceField(label="Hora", choices=[("", "Elige la hora")] + opciones,
                                                    widget=forms.Select(attrs={"class": INPUT, "data-franjas": "1"}))
            self.order_fields(["nombre", "telefono", "moto", "servicio", "fecha_preferida", "hora", "detalle"])

    def _fecha_elegida(self):
        from datetime import date
        valor = self.data.get("fecha_preferida") if self.is_bound else self.initial.get("fecha_preferida")
        if isinstance(valor, date):
            return valor
        try:
            return date.fromisoformat(valor or "")
        except ValueError:
            return None

    def clean(self):
        datos = super().clean()
        if self.taller and self.taller.agenda_activa and datos.get("fecha_preferida") and datos.get("hora"):
            # Se acepta cualquier hora de la agenda; el cupo se verifica al reservar (con candado)
            from datetime import time
            from .agenda import horas_del_dia
            hora = time.fromisoformat(datos["hora"])
            if hora not in horas_del_dia(self.taller, datos["fecha_preferida"]):
                self.add_error("hora", "Ese horario no está disponible. Elige otro.")
            datos["hora"] = hora
        return datos

    def save(self, commit=True):
        cita = super().save(commit=False)
        if "hora" in self.cleaned_data and self.cleaned_data["hora"]:
            cita.hora = self.cleaned_data["hora"]
        if commit:
            cita.save()
        return cita

    def clean_fecha_preferida(self):
        from django.utils import timezone
        fecha = self.cleaned_data["fecha_preferida"]
        if fecha < timezone.localdate():
            raise forms.ValidationError("Elige una fecha de hoy en adelante.")
        return fecha


class ResenaForm(EstiloMixin, forms.ModelForm):
    estrellas = forms.TypedChoiceField(choices=[(i, "★" * i) for i in range(5, 0, -1)], coerce=int)

    class Meta:
        model = Resena
        fields = ["nombre", "estrellas", "comentario"]
        widgets = {"comentario": forms.Textarea(attrs={"rows": 3})}


class RegistroTallerForm(EstiloMixin, forms.ModelForm):
    ciudad = forms.ChoiceField(choices=[(c, c) for c in CIUDADES], initial="Medellín")

    class Meta:
        model = Taller
        fields = ["nombre", "responsable", "whatsapp", "direccion", "barrio", "horario",
                  "descripcion", "servicios", "marcas", "foto"]
        widgets = {
            "servicios": forms.CheckboxSelectMultiple,
            "marcas": forms.CheckboxSelectMultiple,
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["barrio"].empty_label = "Elige el barrio"
        self.fields["barrio"].label = "Barrio"
        self.fields["ciudad"].widget.attrs["class"] = "campo"
        if self.instance.pk and self.instance.barrio_id:
            self.fields["ciudad"].initial = self.instance.barrio.ciudad
        # El orden de los campos: la ciudad antes del barrio
        orden = ["nombre", "responsable", "whatsapp", "ciudad", "barrio", "direccion", "horario", "descripcion", "servicios", "marcas", "foto"]
        self.order_fields(orden)
        if "horario" in self.fields:
            self.fields["horario"].widget.attrs.setdefault("placeholder", "Lun-Sáb 8am-6pm")
        self.fields["direccion"].widget.attrs.setdefault("placeholder", "Calle 00 # 00-00")

    def clean_whatsapp(self):
        return normalizar_celular(self.cleaned_data["whatsapp"])

    def clean(self):
        datos = super().clean()
        barrio, ciudad = datos.get("barrio"), datos.get("ciudad")
        if barrio and ciudad and barrio.ciudad != ciudad:
            self.add_error("barrio", f"Ese barrio no es de {ciudad}. Elige uno de la lista.")
        return datos

    @staticmethod
    def barrios_por_ciudad():
        """{ciudad: [[id, nombre], ...]} para que el formulario cambie la lista de barrios al elegir la ciudad."""
        datos = {c: [] for c in CIUDADES}
        for b in Barrio.objects.all():
            datos.setdefault(b.ciudad, []).append([b.pk, b.nombre])
        for lista in datos.values():
            lista.sort(key=lambda x: (x[1] != "Centro", x[1]))
        return datos


class PerfilTallerForm(EstiloMixin, forms.ModelForm):
    """Lo que el taller puede cambiar de su perfil público."""
    especialidades = forms.MultipleChoiceField(choices=perfil.ESPECIALIDADES, required=False,
                                               widget=forms.CheckboxSelectMultiple, label="Especialidades")
    compromisos = forms.MultipleChoiceField(choices=[(c, t) for c, t, _ in perfil.COMPROMISOS], required=False,
                                            widget=forms.CheckboxSelectMultiple, label="Cómo trabajan")
    garantia_meses = forms.TypedChoiceField(
        label="Garantía en mano de obra", required=False, coerce=int, empty_value=None,
        choices=[("", "Sin garantía publicada")] + [(n, f"{n} {'mes' if n == 1 else 'meses'}") for n in (1, 2, 3, 6, 12)])

    class Meta:
        model = Taller
        fields = ["descripcion", "nivel_precio", "servicios", "marcas", "foto", "especialidades",
                  "garantia_meses", "compromisos", "multimarca", "latitud", "longitud"]
        labels = {"descripcion": "Descripción corta", "foto": "Foto de portada", "multimarca": "Multimarca"}
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3, "maxlength": perfil.MAXIMO_DESCRIPCION,
                                                 "placeholder": "Ej: Taller familiar en Belén desde 2012. Motos de trabajo y scooters hasta 200 cc."}),
            "servicios": forms.CheckboxSelectMultiple,
            "marcas": forms.CheckboxSelectMultiple,
            "foto": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "latitud": forms.HiddenInput, "longitud": forms.HiddenInput,
        }

    def clean(self):
        datos = super().clean()
        for campo in ("latitud", "longitud"):  # si el formulario no los trae, no se borran las coordenadas
            if campo not in self.data:
                datos[campo] = getattr(self.instance, campo)
        _validar_ubicacion(self, datos)
        return datos

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and getattr(foto, "size", 0) > 5 * 1024 * 1024:
            raise forms.ValidationError("La foto debe pesar máximo 5 MB.")
        return foto


class MecanicoForm(EstiloMixin, forms.Form):
    """Una persona del equipo («Quiénes te atienden»). Rol de una lista corta y especialidad del catálogo de servicios
    (o «Otra» con un texto corto). Una fila vacía se ignora."""
    nombre = forms.CharField(max_length=60, required=False, widget=forms.TextInput(attrs={"placeholder": "Ej: Jhon Fredy"}))
    rol = forms.ChoiceField(required=False, choices=[("", "Elige el rol")] + [(r, r) for r in perfil.ROLES])
    anios = forms.IntegerField(label="Años de experiencia", min_value=0, max_value=60, required=False)
    especialidad = forms.ChoiceField(required=False, label="Especialidad")
    especialidad_otra = forms.CharField(max_length=40, required=False, widget=forms.TextInput(attrs={"placeholder": "¿En qué es bueno?"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicios = {str(s.pk): s.nombre for s in Servicio.objects.all()}
        self.fields["especialidad"].choices = ([("", "Elige la especialidad")] + list(self.servicios.items())
                                               + [(perfil.OTRA, "Otra…")])

    def clean(self):
        datos = super().clean()
        if not datos.get("nombre", "").strip() and any(datos.get(c) for c in ("rol", "anios", "especialidad")):
            self.add_error("nombre", "Escribe el nombre o borra la fila.")
        if datos.get("especialidad") == perfil.OTRA and not datos.get("especialidad_otra", "").strip():
            self.add_error("especialidad_otra", "Escribe la especialidad o elige una de la lista.")
        return datos


def equipo_formset(taller, data=None):
    """Formset del equipo: las personas guardadas más filas vacías (mínimo 3 filas, máximo perfil.MAXIMO_EQUIPO)."""
    inicial = []
    for m in perfil.equipo_limpio(taller.equipo):
        m = dict(m, rol=m["rol"] if m["rol"] in perfil.ROLES else perfil.rol_cercano(m["rol"]))
        if m["servicio"]:
            m["especialidad"] = str(m["servicio"])
        elif m["especialidad"]:
            m["especialidad_otra"], m["especialidad"] = m["especialidad"], perfil.OTRA
        inicial.append(m)
    # Se dibujan todas las filas posibles; la plantilla esconde las vacías de más y el botón «+» las muestra
    extra = max(perfil.MAXIMO_EQUIPO - len(inicial), 0)
    Formset = forms.formset_factory(MecanicoForm, extra=extra, max_num=perfil.MAXIMO_EQUIPO, validate_max=True)
    fs = Formset(data, initial=inicial, prefix="equipo")
    fs.visibles = min(max(3, len(inicial) + 1), perfil.MAXIMO_EQUIPO)
    return fs


def equipo_de(formset):
    """Lista para Taller.equipo a partir de un formset válido (sin filas vacías)."""
    salida = []
    for f in formset.forms:
        d = f.cleaned_data
        if not d.get("nombre", "").strip():
            continue
        esp, servicio = d.get("especialidad", ""), None
        if esp == perfil.OTRA:
            texto = d["especialidad_otra"].strip()
        elif esp in f.servicios:
            texto, servicio = f.servicios[esp], int(esp)
        else:
            texto = ""
        salida.append({"nombre": d["nombre"].strip(), "rol": d.get("rol", ""), "anios": d.get("anios") or None,
                       "especialidad": texto, "servicio": servicio})
    return salida


class AgendaForm(EstiloMixin, forms.ModelForm):
    """Agenda y emergencias. Los turnos por día se leen aparte (ver leer_turnos)."""
    CASILLAS = ["agenda_activa", "atiende_emergencias", "abierto_24h", "grua", "despinche_domicilio", "gasolina_domicilio"]

    class Meta:
        model = Taller
        fields = ["agenda_activa", "duracion_franja", "cupo_franja",
                  "atiende_emergencias", "abierto_24h", "grua", "despinche_domicilio", "gasolina_domicilio"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for c in self.CASILLAS:
            self.fields[c].widget.attrs["class"] = ""


def _validar_ubicacion(form, datos):
    """Solo el Valle de Aburrá (aprox.): evita ubicaciones erradas."""
    lat, lng = datos.get("latitud"), datos.get("longitud")
    if lat is not None and lng is not None and not (5.9 <= lat <= 6.6 and -75.8 <= lng <= -75.2):
        form.add_error(None, "La ubicación no parece del Valle de Aburrá. Vuelve a tomarla desde el taller.")


def leer_turnos(datos):
    """Lee los turnos (hasta dos por día). Vienen de `turnos_json` (filas con días y horas: la pantalla de agenda)
    o de los campos d<dia>_<n>_abre / _cierra. Devuelve (turnos, errores)."""
    import json
    from datetime import time
    from .models import DIAS_SEMANA
    crudos = {dia: [] for dia, _ in DIAS_SEMANA}
    errores = []
    if "turnos_json" in datos:
        try:
            filas = json.loads(datos.get("turnos_json") or "[]")
            for f in filas:
                for d in f["dias"]:
                    crudos[int(d)].append((str(f["abre"]), str(f["cierra"])))
        except (ValueError, KeyError, TypeError):
            return [], ["No pudimos leer tu horario. Vuelve a elegirlo."]
    else:
        for dia, _ in DIAS_SEMANA:
            for n in (1, 2):
                abre, cierra = datos.get(f"d{dia}_{n}_abre", ""), datos.get(f"d{dia}_{n}_cierra", "")
                if abre or cierra:
                    crudos[dia].append((abre, cierra))
    turnos = []
    for dia, nombre in DIAS_SEMANA:
        previos = []
        if len(crudos[dia]) > 2:
            errores.append(f"{nombre}: máximo dos turnos.")
            continue
        for abre, cierra in crudos[dia]:
            try:
                a, c = time.fromisoformat(abre), time.fromisoformat(cierra)
            except ValueError:
                errores.append(f"{nombre}: escribe la hora de abrir y la de cerrar.")
                continue
            if c <= a:
                errores.append(f"{nombre}: la hora de cierre debe ser después de la de apertura.")
            elif any(a < pc and pa < c for pa, pc in previos):
                errores.append(f"{nombre}: los dos turnos se cruzan.")
            else:
                previos.append((a, c))
                turnos.append((dia, a, c))
    return turnos, errores


class PrecioServicioForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = PrecioServicio
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


class _PreciosBase(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        vistos = set()
        for f in self.forms:
            if not hasattr(f, "cleaned_data") or not f.cleaned_data or f.cleaned_data.get("DELETE"):
                continue
            clave = (f.cleaned_data.get("servicio"), f.cleaned_data.get("cilindraje"))
            if clave in vistos:
                raise forms.ValidationError("Repetiste un servicio con el mismo cilindraje.")
            vistos.add(clave)


def precios_formset(taller):
    class Form(PrecioServicioForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["servicio"].queryset = taller.servicios.all()
            self.fields["servicio"].empty_label = "Elige el servicio"

    return forms.inlineformset_factory(Taller, PrecioServicio, form=Form, formset=_PreciosBase, extra=0,
                                       can_delete=True, max_num=60)
