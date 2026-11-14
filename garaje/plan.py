"""Calcula el estado de mantenimiento de una moto a partir de su kilometraje y su historial."""
from dataclasses import dataclass, field
from datetime import date, timedelta

from django.utils import timezone

from .models import TareaMantenimiento

UMBRAL_PRONTO = 0.8  # desde el 80 % del intervalo avisamos que se acerca

# Orden de gravedad para resumir varias tareas en una sola pieza del modelo 3D.
GRAVEDAD = {"ok": 0, "desconocido": 1, "pronto": 2, "vencido": 3}

ETIQUETAS = {
    "ok": "Al día",
    "pronto": "Pronto",
    "vencido": "Toca ya",
    "desconocido": "Sin registro",
}


@dataclass
class EstadoTarea:
    tarea: TareaMantenimiento
    estado: str
    progreso: float | None = None  # 0..1+ (1 = toca hoy)
    km_restantes: int | None = None
    dias_restantes: int | None = None
    fecha_estimada: date | None = None
    ultimo_km: int | None = None
    ultima_fecha: date | None = None
    supuesto: bool = False  # sin registro, asumimos que se hizo de fábrica

    @property
    def etiqueta(self):
        return ETIQUETAS[self.estado]

    @property
    def porcentaje(self):
        return min(100, round((self.progreso or 0) * 100))

    @property
    def detalle(self):
        if self.estado == "desconocido":
            return "No sabemos cuándo se hizo por última vez. Regístralo para empezar a contar."
        partes = []
        if self.km_restantes is not None:
            if self.km_restantes > 0:
                partes.append(f"faltan {self.km_restantes:,} km".replace(",", "."))
            elif self.km_restantes == 0:
                partes.append("toca justo ahora")
            else:
                partes.append(f"pasado por {-self.km_restantes:,} km".replace(",", "."))
        if self.dias_restantes is not None and (self.km_restantes is None or self.dias_restantes < 30):
            partes.append(f"faltan {self.dias_restantes} días" if self.dias_restantes > 0
                          else f"vencido hace {-self.dias_restantes} días")
        return ", ".join(partes).capitalize() + "."


@dataclass
class PlanMoto:
    moto: object
    tareas: list = field(default_factory=list)
    km_por_dia: float | None = None
    ritmo_estimado: bool = False

    def por_estado(self, estado):
        return [t for t in self.tareas if t.estado == estado]

    @property
    def urgentes(self):
        return self.por_estado("vencido")

    @property
    def pronto(self):
        return self.por_estado("pronto")

    @property
    def al_dia(self):
        return self.por_estado("ok")

    @property
    def sin_registro(self):
        return self.por_estado("desconocido")

    @property
    def peor_estado(self):
        return max((t.estado for t in self.tareas), key=GRAVEDAD.get, default="ok")

    def piezas(self):
        """Estado por pieza, para colorear el modelo 3D."""
        resultado = {}
        for t in self.tareas:
            p = resultado.setdefault(t.tarea.pieza, {
                "nombre": t.tarea.get_pieza_display(), "estado": "ok", "tareas": [],
            })
            if GRAVEDAD[t.estado] > GRAVEDAD[p["estado"]]:
                p["estado"] = t.estado
            p["tareas"].append({"nombre": t.tarea.nombre, "estado": t.estado,
                                "etiqueta": t.etiqueta, "detalle": t.detalle})
        return resultado


RITMO_MIN, RITMO_MAX = 0.5, 400  # km/día creíbles; fuera de eso el dato no sirve para estimar


def _ritmo_lecturas(moto):
    """Pendiente (recta de mejor ajuste) de las lecturas, sin contar correcciones del odómetro.

    Un salto imposible (más de RITMO_MAX por día, o grande el mismo día) es una corrección, no kilómetros rodados.
    Exige al menos una semana entre la primera y la última lectura."""
    lecturas = list(moto.lecturas.order_by("fecha", "creado").values_list("fecha", "km"))
    if len(lecturas) < 2:
        return None
    rodado = {lecturas[0][0]: 0}
    acumulado = 0
    for (f0, k0), (f1, k1) in zip(lecturas, lecturas[1:]):
        subida = k1 - k0
        if 0 < subida <= RITMO_MAX * max(1, (f1 - f0).days):
            acumulado += subida
        rodado[f1] = acumulado
    fechas = sorted(rodado)
    if len(fechas) < 2 or (fechas[-1] - fechas[0]).days < 7:
        return None
    xs = [(f - fechas[0]).days for f in fechas]
    ys = [rodado[f] for f in fechas]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    pendiente = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return pendiente if RITMO_MIN <= pendiente <= RITMO_MAX else None


def _ritmo_estimado(moto, hoy):
    """Sin historial suficiente: desde que se registró en TallerYa, o si no, por el año del modelo."""
    if moto.creado and moto.km_actual > moto.km_inicial:
        dias = (hoy - timezone.localdate(moto.creado)).days
        if dias >= 14:
            ritmo = (moto.km_actual - moto.km_inicial) / dias
            if RITMO_MIN <= ritmo <= RITMO_MAX:
                return ritmo
    if moto.km_actual and moto.modelo:
        # Se supone que la moto salió a mitad del año anterior a su modelo (las de modelo X se venden desde mediados de X-1).
        dias = (hoy - date(moto.modelo - 1, 7, 1)).days
        if dias >= 90:
            ritmo = moto.km_actual / dias
            if RITMO_MIN <= ritmo <= RITMO_MAX:
                return ritmo
    return None


def ritmo_km(moto, hoy=None):
    """(km por día, estimado). estimado=True cuando no sale de las lecturas sino de una aproximación."""
    if (ritmo := _ritmo_lecturas(moto)) is not None:
        return ritmo, False
    ritmo = _ritmo_estimado(moto, hoy or timezone.localdate())
    return ritmo, ritmo is not None


def km_por_dia(moto):
    """Ritmo de uso (de las lecturas o estimado)."""
    return ritmo_km(moto)[0]


def calcular_plan(moto, hoy=None):
    hoy = hoy or timezone.localdate()
    specs = moto.specs()
    ritmo, estimado = ritmo_km(moto, hoy)
    ultimos = {}
    for m in moto.mantenimientos.order_by("fecha", "km"):
        ultimos[m.tarea_id] = m  # se queda con el más reciente

    plan = PlanMoto(moto=moto, km_por_dia=ritmo, ritmo_estimado=estimado)
    for tarea in TareaMantenimiento.objects.filter(activo=True).select_related("servicio"):
        if not tarea.aplica_a(specs):
            continue
        plan.tareas.append(_estado_tarea(tarea, moto, ultimos.get(tarea.pk), ritmo, hoy))

    plan.tareas.sort(key=lambda t: (-GRAVEDAD[t.estado], -(t.progreso or 0), t.tarea.orden))
    return plan


def _estado_tarea(tarea, moto, ultimo, ritmo, hoy):
    supuesto = False
    if ultimo:
        base_km, base_fecha = ultimo.km, ultimo.fecha
    elif tarea.intervalo_km and moto.km_inicial <= tarea.intervalo_km:
        # Se registró casi nueva: asumimos que la pieza viene de fábrica.
        base_km, base_fecha, supuesto = 0, moto.creado.date(), True
    else:
        return EstadoTarea(tarea=tarea, estado="desconocido")

    progresos, km_rest, dias_rest = [], None, None
    if tarea.intervalo_km:
        recorrido = max(0, moto.km_actual - base_km)
        km_rest = tarea.intervalo_km - recorrido
        progresos.append(recorrido / tarea.intervalo_km)
    if tarea.intervalo_dias:
        transcurridos = (hoy - base_fecha).days
        dias_rest = tarea.intervalo_dias - transcurridos
        progresos.append(transcurridos / tarea.intervalo_dias)

    progreso = max(progresos) if progresos else 0
    estado = "vencido" if progreso >= 1 else "pronto" if progreso >= UMBRAL_PRONTO else "ok"

    fechas = []
    if km_rest is not None and ritmo:
        fechas.append(hoy + timedelta(days=max(0, round(km_rest / ritmo))))
    if dias_rest is not None:
        fechas.append(hoy + timedelta(days=max(0, dias_rest)))

    return EstadoTarea(
        tarea=tarea, estado=estado, progreso=progreso, km_restantes=km_rest, dias_restantes=dias_rest,
        fecha_estimada=min(fechas) if fechas else None,
        ultimo_km=None if supuesto else base_km, ultima_fecha=None if supuesto else base_fecha, supuesto=supuesto,
    )
