"""Servicios que registra el taller desde su panel: crean la hoja de vida verificada y ponen al día el plan.

- Con cita (el motero la pidió con su cuenta) o con el código/QR que muestra el dueño: queda verificado de una vez.
- Por placa (moto que llega sin cita): queda "esperando al dueño" hasta que lo confirme desde su aviso.
El dueño siempre puede decir "no reconozco este servicio": se quita de la hoja de vida y del plan.
"""
import re
from datetime import timedelta

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .hoja_vida import desde_mantenimiento
from .kilometraje import registrar_lectura
from .models import AjusteTarea, LecturaKm, Mantenimiento, Moto, RegistroServicio, ServicioTaller

DIAS_EMPATE = 10  # un "ya lo hice" del dueño con la misma tarea dentro de ±10 días es el mismo servicio


def normalizar_placa(texto):
    return re.sub(r"[^A-Z0-9]", "", (texto or "").upper())[:8]


def buscar_por_placa(placa):
    """Motos con esa placa cuyo dueño tiene cuenta (si no, no hay a quién pedirle el visto bueno)."""
    placa = normalizar_placa(placa)
    if len(placa) < 5:
        return []
    return list(Moto.objects.select_related("linea", "linea__marca", "motociclista__usuario")
                .filter(placa__iexact=placa, motociclista__usuario__isnull=False)[:3])


def motos_de_cita(cita):
    """Motos del motero que pidió la cita (solo si la pidió con su cuenta)."""
    if not cita.usuario_id:
        return []
    return list(Moto.objects.select_related("linea", "linea__marca")
                .filter(motociclista__usuario_id=cita.usuario_id).order_by("-pk"))


def tareas_de(moto):
    """Tareas del plan de esa moto, en el orden del plan."""
    from .plan import calcular_plan
    return [t.tarea for t in calcular_plan(moto).tareas]


def _avisar(usuario, clave, titulo, texto, url):
    from notificaciones.servicios import notificar  # crea el aviso; el push sale solo (notificaciones.apps)
    notificar(usuario, clave, titulo, texto, url)


def crear(taller, moto, *, origen, fecha, km, tareas, otros="", costo=None, notas="", foto=None, cita=None,
          registrado_por=None, ip=None, mecanico=None, solicitud=None):
    """Guarda el servicio, lo aplica si ya hay consentimiento (cita, visita o código) y le avisa al dueño.
    Lo hace un taller o un mecánico a domicilio (taller=None y mecanico=...; la visita es su «cita»).
    Queda la bitácora: quién, cuenta que lo registró, IP y fecha; el dueño lo ve y puede rechazarlo (rechazar)."""
    with transaction.atomic():
        s = ServicioTaller.objects.create(taller=taller, mecanico=mecanico, solicitud=solicitud, moto=moto, cita=cita,
                                          fecha=fecha, km=km, otros=otros,
                                          costo=costo, notas=notas, foto=foto or "", origen=origen, ip=ip,
                                          registrado_por=registrado_por if getattr(registrado_por, "pk", None) else None)
        s.tareas.set(tareas)
        if origen != ServicioTaller.Origen.PLACA:
            aplicar(s)
        for pedido in (cita, solicitud):
            if pedido is not None:
                pedido.estado = pedido.Estado.ATENDIDA
                pedido.save(update_fields=["estado"])
                # La moto sale del tablero de «Mi día» si el servicio se registró sin pasar por «Entregada»
                pedido.trabajos.exclude(estado="entregada").update(estado="entregada", entregada_en=timezone.now())
    que = s.resumen()
    quien = s.prestador.nombre
    if s.estado == ServicioTaller.Estado.VERIFICADO:
        califica = "Califica al taller." if taller else "Califica al mecánico."
        _avisar(s.dueno, f"servicio-taller:{s.pk}", f"{quien} registró el servicio de tu moto",
                f"{que[:120]}. Ya está en tu hoja de vida y tu plan. ¿Cómo te fue? {califica}", s.get_absolute_url())
    else:
        _avisar(s.dueno, f"servicio-taller:{s.pk}", f"{quien} quiere anotar un servicio en tu moto",
                f"{que[:120]}. Confírmalo para que quede verificado en tu hoja de vida.", s.get_absolute_url())
    return s


def aplicar(s):
    """Hoja de vida verificada + plan al día (igual que "ya lo hice"). Una entrada por tarea del plan, más una
    para los otros trabajos; el valor va en la primera para no sumarlo dos veces en los gastos."""
    moto, taller, mecanico = s.moto, s.taller, s.mecanico
    # En el plan (Mantenimiento) el mecánico a domicilio queda como "otro taller" con su nombre
    taller_otro = "" if taller else f"A domicilio: {mecanico.nombre}"[:80]
    registros = []
    with transaction.atomic():
        for tarea in s.tareas.all():
            # Si el dueño ya lo había anotado (con este taller o sin taller) cerca de esa fecha, se verifica ese.
            previo = (RegistroServicio.objects.select_for_update()
                      .filter(moto=moto, verificado=False, mantenimiento__tarea=tarea,
                              fecha__range=(s.fecha - timedelta(days=DIAS_EMPATE), s.fecha + timedelta(days=DIAS_EMPATE)))
                      .filter(taller=taller, mecanico=mecanico).first()
                      or RegistroServicio.objects.select_for_update()
                      .filter(moto=moto, verificado=False, mantenimiento__tarea=tarea, taller__isnull=True,
                              mecanico__isnull=True, taller_otro="", fecha__range=(s.fecha - timedelta(days=DIAS_EMPATE), s.fecha + timedelta(days=DIAS_EMPATE)))
                      .first())
            if previo:
                m = previo.mantenimiento
                m.km, m.fecha, m.taller, m.taller_otro = s.km, s.fecha, taller, taller_otro
                m.save(update_fields=["km", "fecha", "taller", "taller_otro"])
                registro = previo
            else:
                m = Mantenimiento.objects.create(moto=moto, tarea=tarea, km=s.km, fecha=s.fecha, taller=taller,
                                                 taller_otro=taller_otro, notas=s.notas[:200])
                registro = desde_mantenimiento(m)  # normalmente ya lo creó la señal de garaje.apps
            AjusteTarea.objects.filter(moto=moto, tarea=tarea).delete()
            registros.append(registro)
        if s.otros:
            registros.append(RegistroServicio(moto=moto, servicios=s.otros[:300]))
        for i, r in enumerate(registros):
            r.fecha, r.km, r.taller, r.mecanico, r.taller_otro = s.fecha, s.km, taller, mecanico, ""
            r.notas = s.notas[:300] or r.notas
            r.costo = s.costo if i == 0 else None
            r.verificado, r.servicio_taller = True, s
            r.save()
        registrar_lectura(moto, s.km, s.fecha)  # el taller vio el odómetro: cuenta como lectura y recalibra el ritmo
        s.estado = ServicioTaller.Estado.VERIFICADO
        s.save(update_fields=["estado"])
    return registros


def _panel(s):
    return reverse("talleres:servicios_taller") if s.taller_id else reverse("domicilio:solicitudes")


def confirmar(s):
    """El dueño acepta un servicio registrado por placa."""
    if s.estado != ServicioTaller.Estado.POR_CONFIRMAR:
        return False
    aplicar(s)
    s.respondido = timezone.now()
    s.save(update_fields=["respondido"])
    _avisar(s.prestador.usuario, f"servicio-confirmado:{s.pk}", f"El dueño de la {s.moto} confirmó el servicio",
            "Quedó verificado en su hoja de vida con tu sello.", _panel(s))
    return True


def rechazar(s):
    """El dueño no reconoce el servicio: sale de la hoja de vida y del plan, y el taller se entera."""
    if s.estado == ServicioTaller.Estado.RECHAZADO:
        return False
    with transaction.atomic():
        for r in s.registros.select_related("mantenimiento"):
            m = r.mantenimiento
            r.delete()
            if m:
                m.delete()
        s.estado, s.respondido = ServicioTaller.Estado.RECHAZADO, timezone.now()
        s.save(update_fields=["estado", "respondido"])
    _avisar(s.prestador.usuario, f"servicio-rechazado:{s.pk}", f"El dueño de la {s.moto} no reconoce un servicio",
            f"El del {s.fecha:%d/%m} no quedó en su hoja de vida. Escríbele si fue un error.", _panel(s))
    return True


def resumen_taller(taller, hoy=None):
    """Cifras del panel: citas de la semana, servicios registrados y calificación."""
    from django.db.models import Avg, Count
    hoy = hoy or timezone.localdate()
    lunes = hoy - timedelta(days=hoy.weekday())
    nota = taller.resenas.filter(visible=True).aggregate(prom=Avg("estrellas"), n=Count("id"))
    servicios = taller.servicios_taller.exclude(estado=ServicioTaller.Estado.RECHAZADO)
    from talleres.panel_cifras import mes_anterior
    ini_ant, fin_ant = mes_anterior(hoy)
    return {
        "citas_semana": taller.solicitudes.filter(fecha_preferida__range=(lunes, lunes + timedelta(days=6)))
                              .exclude(estado="cancelada").count(),
        "citas_semana_ant": taller.solicitudes.filter(fecha_preferida__range=(lunes - timedelta(days=7), lunes - timedelta(days=1)))
                                  .exclude(estado="cancelada").count(),
        "servicios_mes_ant": servicios.filter(fecha__range=(ini_ant, fin_ant)).count(),
        "servicios_mes": servicios.filter(fecha__gte=hoy.replace(day=1)).count(),
        "servicios_total": servicios.count(),
        "por_confirmar": servicios.filter(estado=ServicioTaller.Estado.POR_CONFIRMAR).count(),
        "nota": nota,
    }
