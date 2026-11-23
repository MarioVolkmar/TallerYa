"""Calcula el estado de mantenimiento de una moto a partir de su kilometraje y su historial."""
from dataclasses import dataclass, field
from datetime import date, timedelta

from django.utils import timezone

from . import intervalos
from .models import TareaMantenimiento

UMBRAL_PRONTO = 0.8  # desde el 80 % del intervalo avisamos que se acerca
# Rojo ("urgente") antes de vencer: el último 10 % del intervalo, con tope de 500 km (≈ 3 semanas a 25 km/día, el margen
# para conseguir cita y repuesto sin rodar con la pieza gastada), o 7 días o menos (como los documentos).
FRACCION_URGENTE = 0.10
KM_URGENTE_MAX = 500
DIAS_URGENTE = 7

# Orden de gravedad para resumir varias tareas en una sola pieza del modelo 3D.
GRAVEDAD = {"ok": 0, "desconocido": 1, "pronto": 2, "vencido": 3}

ETIQUETAS = {
    "ok": "Al día",
    "pronto": "Pronto",
    "vencido": "Toca ya",
    "urgente": "Muy pronto",
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
    # De dónde sale la cuenta: "exacto" (registro con km), "aproximado" (km estimado por la fecha o "hace unos meses")
    # o "supuesto" (no sabemos: contamos desde que la moto era nueva). None si no hay cuenta.
    origen: str | None = None
    km_desde: int | None = None  # km estimados desde el último cambio o revisión
    # Color y grupo (un solo criterio para agenda, Mi garaje y campana): vencido · urgente (rojo) · pronto (amarillo)
    # · ok (verde) · desconocido. Lo pospuesto por el dueño se muestra como "pronto".
    nivel: str = ""
    pospuesta: bool = False
    # Sin ningún registro: estado estimado desde que la moto era nueva (ver _estimar_sin_registro). ritmo = km/día usados.
    estimado: bool = False
    ritmo: float | None = None
    edad_dias: int | None = None   # edad estimada de la moto (solo en lo estimado)
    km_moto: int | None = None
    manda: str | None = None       # "km" o "tiempo": cuál de los dos intervalos va más adelantado

    @property
    def intervalo(self):
        """«Cada 2.500 km o 4 meses, lo que pase primero» · «Cada 12 meses» · «Cada 6.000 km»."""
        texto = intervalos.texto(self.tarea.intervalo_km, self.tarea.intervalo_dias)
        return f"{texto}, lo que pase primero" if self.tarea.intervalo_km and self.tarea.intervalo_dias else texto

    @property
    def ritmo_usado(self):
        """Los km/día solo cuentan cuando manda el kilometraje y todavía falta (para la fecha aproximada)."""
        return bool(self.ritmo and self.manda == "km" and self.estado != "vencido")

    @property
    def texto_estimado(self):
        """«estimado con tus ~38 km/día» si los km/día se usaron; si no, solo «estimado»."""
        return f"estimado con tus ~{round(self.ritmo)} km/día" if self.ritmo_usado else "estimado"

    @property
    def explicacion_estimada(self):
        """Por qué sale así, sin registro: por la edad (manda el tiempo) o por los km (manda el kilometraje)."""
        intervalo = self.intervalo[:1].lower() + self.intervalo[1:]
        if self.manda == "tiempo":
            base = f"Tu moto tiene {_edad(self.edad_dias)} y esto toca {intervalo}"
        else:
            base = f"Tu moto tiene {_miles(self.km_moto)} km y esto toca {intervalo}"
        if self.tarea.intervalo_km and self.tarea.intervalo_dias:
            base += "; aquí manda " + ("el tiempo" if self.manda == "tiempo" else "el kilometraje")
        return base

    @property
    def etiqueta(self):
        texto = ETIQUETAS[self.nivel or self.estado]
        # Lo supuesto (no sabemos; contamos desde nueva) siempre dice que es una estimación
        if self.estimado and (self.nivel or self.estado) != "ok":
            return f"{texto} (estimado)"
        return f"{texto} (estimado)" if self.supuesto and (self.nivel or self.estado) not in ("ok", "desconocido") else texto

    @property
    def color(self):
        """El estado que entienden el 3D y el despiece (ok · pronto · vencido · desconocido), sacado del MISMO nivel que
        la agenda: "urgente" se pinta rojo como vencido; lo pospuesto, amarillo."""
        nivel = self.nivel or self.estado
        return "vencido" if nivel == "urgente" else nivel

    @property
    def porcentaje(self):
        return min(100, round((self.progreso or 0) * 100))

    @property
    def texto_origen(self):
        """Una línea que dice de dónde sale la estimación (se muestra siempre junto a los km)."""
        if self.origen == "exacto":
            return f"Según tu registro del {self.ultima_fecha:%d/%m/%Y} a los {_miles(self.ultimo_km)} km."
        if self.origen == "aproximado":
            return (f"Estimado: la fecha ({self.ultima_fecha:%d/%m/%Y}) no trae kilometraje exacto; lo calculamos "
                    f"con tu ritmo de uso (≈ {_miles(self.ultimo_km)} km).")
        if self.origen == "supuesto":
            return "Estimado: no sabemos cuándo se hizo, así que contamos desde que la moto era nueva."
        if self.origen == "estimado":
            return f"{self.texto_estimado.capitalize()}: no hay registro, así que contamos desde que la moto era nueva."
        return ""

    @property
    def detalle(self):
        if self.estado == "desconocido":
            return "No sabemos cuándo se hizo por última vez. Regístralo para empezar a contar."
        if self.estimado:
            if self.estado == "vencido":
                return f"{self.explicacion_estimada}: lo prudente es hacerlo ya ({self.texto_estimado})."
            if self.manda == "km":
                falta = f"faltan {_miles(self.km_restantes)} km"
            else:
                falta = (f"faltan ~{round(self.dias_restantes / 30)} meses" if self.dias_restantes > 60
                         else f"faltan {self.dias_restantes} días")
            return f"{self.explicacion_estimada}: {falta} ({self.texto_estimado})."
        if self.supuesto and (self.progreso or 0) > 1:
            return "No hay registro y desde nueva ya pasó el intervalo: revísalo pronto."
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

    def por_nivel(self, *niveles):
        return [t for t in self.tareas if t.nivel in niveles]

    @property
    def urgentes(self):
        """Requieren atención (rojo): vencidas o urgentes, sin las pospuestas."""
        return self.por_nivel("vencido", "urgente")

    @property
    def pronto(self):
        """Próximas (amarillo)."""
        return self.por_nivel("pronto")

    @property
    def al_dia(self):
        return self.por_estado("ok")

    @property
    def sin_registro(self):
        return self.por_estado("desconocido")

    @property
    def estimados(self):
        """Sin ningún registro, con el estado estimado desde nueva."""
        return [t for t in self.tareas if t.estimado]

    @property
    def peor_estado(self):
        return max((t.color for t in self.tareas), key=GRAVEDAD.get, default="ok")

    def piezas(self):
        """Estado por pieza, para colorear el modelo 3D."""
        resultado = {}
        for t in self.tareas:
            p = resultado.setdefault(t.tarea.pieza, {
                "nombre": t.tarea.get_pieza_display(), "estado": "ok", "tareas": [],
            })
            if GRAVEDAD[t.color] > GRAVEDAD[p["estado"]]:
                p["estado"] = t.color
            p["tareas"].append({"nombre": t.tarea.nombre, "estado": t.color,
                                "etiqueta": t.etiqueta, "detalle": t.detalle})
        return resultado


def _miles(n):
    return f"{n:,}".replace(",", ".")


def _edad(dias):
    """«~7 meses», «~1 año y 5 meses», «~3 años»."""
    meses = round((dias or 0) / 30.44)
    if meses < 1:
        return "menos de un mes"
    if meses < 12:
        return f"~{meses} mes{'es' if meses != 1 else ''}"
    anos, resto = divmod(meses, 12)
    texto = f"~{anos} año{'s' if anos != 1 else ''}"
    return f"{texto} y {resto} mes{'es' if resto != 1 else ''}" if resto else texto


RITMO_MIN, RITMO_MAX = 0.5, 400  # km/día creíbles; fuera de eso el dato no sirve para estimar


def _ritmo_lecturas(moto):
    """Pendiente (recta de mejor ajuste) de las lecturas, sin contar correcciones del odómetro.

    Un salto imposible (más de RITMO_MAX por día, o grande el mismo día) es una corrección, no kilómetros rodados.
    Exige al menos una semana entre la primera y la última lectura."""
    if "lecturas" in getattr(moto, "_prefetched_objects_cache", {}):  # Mi garaje las precarga para todas las motos
        lecturas = [(lec.fecha, lec.km) for lec in sorted(moto.lecturas.all(), key=lambda lec: (lec.fecha, lec.creado))]
    else:
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
    """Sin historial suficiente: desde que se registró en TallerYa; si no, desde la fecha de matrícula; si no, por el año
    del modelo."""
    for calcular in (_ritmo_registro, _ritmo_matricula, _ritmo_perfil, _ritmo_modelo):
        if (ritmo := calcular(moto, hoy)) is not None:
            return ritmo
    return None


def _ritmo_matricula(moto, hoy):
    """Todos los km de la moto desde que se matriculó (salió nueva a la calle)."""
    if moto.km_actual and getattr(moto, "matricula", None):
        dias = (hoy - moto.matricula).days
        if dias >= 90:
            ritmo = moto.km_actual / dias
            if RITMO_MIN <= ritmo <= RITMO_MAX:
                return ritmo
    return None


def fecha_de_nueva(moto, hoy=None):
    """Cuándo salió nueva: la fecha de matrícula; si no, mitad del año anterior a su modelo (como el ritmo por modelo)."""
    if getattr(moto, "matricula", None):
        return moto.matricula
    if moto.modelo:
        return min(hoy or timezone.localdate(), date(moto.modelo - 1, 7, 1))
    return timezone.localdate(moto.creado) if moto.creado else (hoy or timezone.localdate())


def _ritmo_registro(moto, hoy):
    if moto.creado and moto.km_actual > moto.km_inicial:
        dias = (hoy - timezone.localdate(moto.creado)).days
        if dias >= 14:
            ritmo = (moto.km_actual - moto.km_inicial) / dias
            if RITMO_MIN <= ritmo <= RITMO_MAX:
                return ritmo
    return None


def _ritmo_perfil(moto, hoy):
    """Lo que el motero dijo al registrar la moto (ciudad a diario, fines de semana…): primer km/día, antes de tener lecturas."""
    from .kilometraje import KM_DIA_PERFIL
    return KM_DIA_PERFIL.get(getattr(moto, "perfil_uso", ""))


def _ritmo_modelo(moto, hoy):
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
    if moto.pk and (ritmo := _ritmo_lecturas(moto)) is not None:
        return ritmo, False
    ritmo = _ritmo_estimado(moto, hoy or timezone.localdate())
    return ritmo, ritmo is not None


def km_por_dia(moto):
    """Ritmo de uso (de las lecturas o estimado)."""
    return ritmo_km(moto)[0]


# ---------------- Registros sin kilometraje exacto ----------------
# Criterio (más en docs/funciones.md, "Estimación del kilometraje"):
# - Fecha sin km: km de hoy menos lo rodado desde esa fecha. Lo rodado se interpola entre las lecturas sin contar las
#   correcciones del odómetro; antes de la primera lectura se cuenta con el ritmo de la moto (lecturas, desde el registro
#   o por el año del modelo) y, sin ritmo, un uso típico de 25 km/día. Nunca menos de 0 ni más que hoy.
# - "Hace unos meses": la fecha es hoy menos esos meses, y el km sale igual que arriba.
# - "No sé" en una moto que llegó con menos km que el intervalo, o "Sin idea" al registrar: contamos desde 0 km (lo peor
#   razonable: que nunca se haya cambiado) y, en "Sin idea", el tiempo desde la matrícula o el año del modelo. Como la
#   única evidencia es la edad de la moto, lo más alto que marcamos es "Pronto (estimado)", nunca "Toca ya".
# Los registros estimados llevan "km estimado" en las notas y la interfaz siempre dice que es una estimación.
KM_DIA_TIPICO = 25
MARCA_KM_ESTIMADO = "km estimad"   # "(fecha y km estimados)", "(km estimado por la fecha)"
# "Sin idea": no se sabe si alguna vez se cambió; se guarda desde nueva (0 km, matrícula o año del modelo) y cuenta como
# supuesto: "Pronto (estimado)" como mucho, nunca "Toca ya".
MARCA_SIN_IDEA = "(sin idea: contamos desde nueva)"


def km_es_estimado(mantenimiento):
    return MARCA_KM_ESTIMADO in (mantenimiento.notas or "")


def es_sin_idea(mantenimiento):
    return MARCA_SIN_IDEA in (mantenimiento.notas or "")


def _ritmo_o_tipico(moto, hoy):
    return ritmo_km(moto, hoy)[0] or KM_DIA_TIPICO


def _serie_rodado(moto, hoy):
    """[(fecha, km rodados acumulados)] desde la primera lectura hasta hoy, sin contar las correcciones del odómetro
    (la misma regla que el ritmo). Vacía si no hay lecturas."""
    lecturas = list(moto.lecturas.filter(fecha__lte=hoy).order_by("fecha", "creado").values_list("fecha", "km")) if moto.pk else []
    if not lecturas:
        return []
    lecturas.append((hoy, moto.km_actual))
    serie, acumulado = {lecturas[0][0]: 0}, 0
    for (f0, k0), (f1, k1) in zip(lecturas, lecturas[1:]):
        subida = k1 - k0
        if 0 < subida <= RITMO_MAX * max(1, (f1 - f0).days):
            acumulado += subida
        serie[f1] = acumulado
    return sorted(serie.items())


def km_en_fecha(moto, fecha, hoy=None):
    """Kilometraje estimado de la moto en `fecha`, en la escala del odómetro de hoy: km de hoy menos lo rodado desde
    esa fecha. Lo rodado se interpola entre las lecturas sin las correcciones del odómetro; antes de la primera lectura
    (o sin lecturas) se cuenta hacia atrás con el ritmo."""
    hoy = hoy or timezone.localdate()
    serie = _serie_rodado(moto, hoy)
    rodado_hoy = serie[-1][1] if serie else 0
    rodado = None
    for (f0, r0), (f1, r1) in zip(serie, serie[1:]):
        if f0 <= fecha <= f1:
            dias = (f1 - f0).days
            rodado = r0 + (r1 - r0) * (fecha - f0).days / dias if dias else r1
            break
    if rodado is None:
        inicio = serie[0][0] if serie else hoy
        rodado = -_ritmo_o_tipico(moto, hoy) * max(0, (inicio - fecha).days) if fecha < inicio else rodado_hoy
    return max(0, min(moto.km_actual, round(moto.km_actual - (rodado_hoy - rodado))))


def fecha_en_km(moto, km, hoy=None):
    """Fecha estimada en que la moto tenía `km` (registro con km pero sin fecha). Como mucho, dos años atrás."""
    hoy = hoy or timezone.localdate()
    dias = min(730, round(max(0, moto.km_actual - km) / _ritmo_o_tipico(moto, hoy)))
    return hoy - timedelta(days=dias)


def calcular_plan(moto, hoy=None, tareas=None, intensivo=True):
    """tareas: las TareaMantenimiento activas ya cargadas (Mi garaje las pasa una vez para todas las motos).

    Moto marcada «La uso para trabajar» (TallerYa Ruta, con DOMICILIARIOS_ACTIVO): plan de uso intensivo con sus km/día
    reales (domiciliarios/intensivo.py). intensivo=False fuerza el plan normal."""
    if intensivo:
        from domiciliarios.intensivo import perfil_de_trabajo, plan_intensivo
        if perfil := perfil_de_trabajo(moto):
            return plan_intensivo(moto, perfil.km_semana, hoy, tareas)
        # «Trabajo o domicilios» en la moto: plan intensivo con el ritmo del perfil (o las lecturas reales), sin
        # necesidad de ser domiciliario inscrito ni de que el módulo esté prendido (solo invita a Ruta)
        if getattr(moto, "perfil_uso", "") == "trabajo":
            from .kilometraje import KM_DIA_PERFIL
            plan = plan_intensivo(moto, KM_DIA_PERFIL["trabajo"] * 7, hoy, tareas)
            plan.de_trabajo = False  # no es de Ruta: sin franja de jornada ni chapa
            plan.por_uso_trabajo = True
            return plan
    hoy = hoy or timezone.localdate()
    specs = moto.specs()
    ritmo, estimado = ritmo_km(moto, hoy)
    ultimos = {}
    # .all() + orden en Python: aprovecha prefetch_related("mantenimientos") si la vista lo hizo
    for m in sorted(moto.mantenimientos.all(), key=lambda m: (m.fecha, m.km)):
        ultimos[m.tarea_id] = m  # se queda con el más reciente

    pospuestas = {a.tarea_id for a in moto.ajustes.all() if a.pospuesta}
    # Intervalos del manual de esta línea (garaje/intervalos/*.json); sin archivo, los generales de la base.
    propios = intervalos.de_linea(moto.linea, moto.modelo) if moto.linea_id else {}
    plan = PlanMoto(moto=moto, km_por_dia=ritmo, ritmo_estimado=estimado)
    # Ritmo de datos reales (lecturas o km desde el registro), para la edad de lo que no tiene registro
    ritmo_medido = ritmo if not estimado else _ritmo_registro(moto, hoy)
    if tareas is None:
        tareas = TareaMantenimiento.objects.filter(activo=True).select_related("servicio")
    for tarea in tareas:
        if not tarea.aplica_a(specs):
            continue
        tarea = intervalos.aplicar(tarea, moto.linea, propios) if propios else tarea
        t = _estado_tarea(tarea, moto, ultimos.get(tarea.pk), ritmo, hoy, ritmo_medido)
        t.pospuesta = tarea.pk in pospuestas
        # Supuesto ya pasado (no sabemos; contamos desde nueva): "Pronto", como lo pospuesto; nunca "Toca ya"
        t.nivel = nivel_tarea(t.estado, t.km_restantes, t.dias_restantes, tarea.intervalo_km,
                              t.pospuesta or (t.supuesto and (t.progreso or 0) >= 1))
        plan.tareas.append(t)

    plan.tareas.sort(key=lambda t: (-GRAVEDAD[t.estado], -(t.progreso or 0), t.tarea.orden))
    return plan


def nivel_tarea(estado, km_restantes=None, dias_restantes=None, intervalo_km=None, pospuesta=False):
    """Nivel de color de una tarea (la misma idea que la escala de documentos)."""
    if estado in ("ok", "desconocido"):
        return estado
    if pospuesta:
        return "pronto"
    if estado == "vencido":
        return "vencido"
    tope_km = min(KM_URGENTE_MAX, round(intervalo_km * FRACCION_URGENTE)) if intervalo_km else None
    if (tope_km is not None and km_restantes is not None and km_restantes <= tope_km) or             (dias_restantes is not None and dias_restantes <= DIAS_URGENTE):
        return "urgente"
    return "pronto"


def _estado_tarea(tarea, moto, ultimo, ritmo, hoy, ritmo_medido=None):
    supuesto = False
    if ultimo and es_sin_idea(ultimo):
        base_km, base_fecha, supuesto, origen = ultimo.km, ultimo.fecha, True, "supuesto"
    elif ultimo:
        base_km, base_fecha = ultimo.km, ultimo.fecha
        origen = "aproximado" if km_es_estimado(ultimo) else "exacto"
    elif tarea.intervalo_km and moto.km_inicial <= tarea.intervalo_km:
        # Se registró casi nueva: asumimos que la pieza viene de fábrica. El km cuenta desde 0 (lo peor razonable); el tiempo,
        # desde que se registró: correrlo hacia atrás con un ritmo débil (el del año del modelo) alarmaría sin evidencia.
        creado = timezone.localdate(moto.creado) if moto.creado else hoy
        base_km, base_fecha, supuesto, origen = 0, creado, True, "supuesto"
    else:
        return _estimar_sin_registro(tarea, moto, ritmo, hoy, ritmo_medido)

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
    if supuesto and estado == "vencido":
        estado = "pronto"  # sin registro: "revisar pronto", no "toca ya" (ver el criterio arriba)

    fechas = []
    if km_rest is not None and ritmo:
        fechas.append(hoy + timedelta(days=max(0, round(km_rest / ritmo))))
    if dias_rest is not None:
        fechas.append(hoy + timedelta(days=max(0, dias_rest)))

    return EstadoTarea(
        tarea=tarea, estado=estado, progreso=progreso, km_restantes=km_rest, dias_restantes=dias_rest,
        fecha_estimada=min(fechas) if fechas else None,
        ultimo_km=None if supuesto else base_km, ultima_fecha=None if supuesto else base_fecha, supuesto=supuesto,
        origen=origen, km_desde=max(0, moto.km_actual - base_km),
    )


# ---------------- Tareas sin ningún registro ----------------
# Criterio (18-nov-2026, pedido del fundador): una tarea que nunca se registró (la moto llegó con más km que el intervalo,
# o la tarea va solo por tiempo) ya no queda "Sin registro": se estima desde que la moto era nueva (0 km y la fecha de
# matrícula; si no, la más reciente entre el 1 de enero del año del modelo y los km contados hacia atrás con un ritmo
# medido, o 25 km/día; ver _fecha_nueva_estimada).
# - Si desde nueva todavía no se cumple el intervalo (ni por km ni por tiempo), esa cuenta es el peor caso posible y es
#   honesta: "Al día" o "Pronto", con la fecha aproximada que dan los km por día.
# - Si desde nueva ya se cumplió (ej.: aceite cada 3.000 km y la moto tiene 12.000 sin registro), no hay forma de saber
#   cuándo se hizo; lo prudente es asumir el peor caso razonable: que toca ya → "Toca ya (estimado)", sin cifras de cuánto
#   se pasó (serían inventadas). La interfaz solo dice, discreto, que es estimado (sin invitar a registrar: el dueño
#   ya dijo que no sabe); el día que registre el mantenimiento con el flujo normal, la cuenta pasa a ser exacta sola.
# Lo de "No sé" en una moto que llegó casi nueva y "Sin idea" siguen el criterio de arriba (tope "Pronto").
ANOS_MAX_HACIA_ATRAS = 15


def _fecha_nueva_estimada(moto, ritmo_medido, hoy):
    """Cuándo salió nueva, para las tareas por tiempo sin registro (edad de la moto):
    - con fecha de matrícula, esa (es el único dato real de compra que guarda la moto);
    - sin ella, la más reciente (la edad más corta) entre:
      · el 1 de enero del año del modelo (una moto modelo X se vende sobre todo durante X; nunca después de hoy), y
      · los km de hoy contados hacia atrás con un ritmo MEDIDO (lecturas del tablero o km desde que se registró en
        TallerYa) o, si no lo hay, con el uso típico de 25 km/día.
    El ritmo que solo sale del año del modelo no se usa aquí: es el mismo supuesto en círculo y daba edades imposibles
    (una XR 190L modelo 2026 con 1.600 km salía con ~1 año y 5 meses y la batería vencida)."""
    if getattr(moto, "matricula", None):
        return moto.matricula
    por_km = hoy - timedelta(days=min(365 * ANOS_MAX_HACIA_ATRAS,
                                      round(moto.km_actual / (ritmo_medido or KM_DIA_TIPICO))))
    return max(por_km, min(hoy, date(moto.modelo, 1, 1))) if moto.modelo else por_km


def _estimar_sin_registro(tarea, moto, ritmo, hoy, ritmo_medido=None):
    if not tarea.intervalo_km and not tarea.intervalo_dias:
        return EstadoTarea(tarea=tarea, estado="desconocido")
    nueva = _fecha_nueva_estimada(moto, ritmo_medido, hoy)
    progresos, km_rest, dias_rest = [], None, None
    if tarea.intervalo_km:
        km_rest = tarea.intervalo_km - moto.km_actual
        progresos.append(moto.km_actual / tarea.intervalo_km)
    if tarea.intervalo_dias:
        dias_rest = tarea.intervalo_dias - max(0, (hoy - nueva).days)
        progresos.append(max(0, (hoy - nueva).days) / tarea.intervalo_dias)
    progreso = max(progresos)
    prog_km = moto.km_actual / tarea.intervalo_km if tarea.intervalo_km else -1
    prog_tiempo = max(0, (hoy - nueva).days) / tarea.intervalo_dias if tarea.intervalo_dias else -1
    comunes = dict(tarea=tarea, estimado=True, ritmo=ritmo, origen="estimado", edad_dias=max(0, (hoy - nueva).days),
                   km_moto=moto.km_actual, manda="km" if prog_km >= prog_tiempo else "tiempo")
    if progreso >= 1:
        return EstadoTarea(estado="vencido", progreso=1.0, fecha_estimada=hoy,
                           km_restantes=0 if tarea.intervalo_km else None,
                           dias_restantes=0 if tarea.intervalo_dias else None, **comunes)
    fechas = []
    if km_rest is not None and ritmo:
        fechas.append(hoy + timedelta(days=round(km_rest / ritmo)))
    if dias_rest is not None:
        fechas.append(hoy + timedelta(days=dias_rest))
    return EstadoTarea(estado="pronto" if progreso >= UMBRAL_PRONTO else "ok", progreso=progreso,
                       km_restantes=km_rest, dias_restantes=dias_rest, fecha_estimada=min(fechas) if fechas else None,
                       km_desde=moto.km_actual if tarea.intervalo_km else None, **comunes)
