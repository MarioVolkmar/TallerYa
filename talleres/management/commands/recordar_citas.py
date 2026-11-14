"""Recordatorio de citas el día antes (para cron, p. ej. todos los días a las 6 p. m.).

Es idempotente: cada cita se marca con `recordatorio_enviado` y cada aviso lleva una clave única,
así que correrlo dos veces no repite nada. El aviso sale por la app `notificaciones`; WhatsApp
sigue como alternativa manual desde el panel del taller.

    python manage.py recordar_citas
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from talleres.models import SolicitudCita
from talleres.utils import normalizar_celular


def _hora(h):
    return f" a las {h.hour % 12 or 12}:{h.minute:02d} {'a. m.' if h.hour < 12 else 'p. m.'}" if h else ""


class Command(BaseCommand):
    help = "Avisa a moteros y talleres de las citas de mañana (no repite avisos)."

    def handle(self, *args, **opciones):
        from cupones.models import Motociclista
        from notificaciones.models import Notificacion
        from notificaciones.servicios import notificar

        manana = timezone.localdate() + timedelta(days=1)
        citas = list(SolicitudCita.objects.select_related("taller", "taller__usuario", "usuario", "servicio")
                     .filter(fecha_preferida=manana, recordatorio_enviado__isnull=True,
                             estado__in=[SolicitudCita.Estado.PENDIENTE, SolicitudCita.Estado.CONFIRMADA])
                     .order_by("taller_id", "hora"))
        if not citas:
            self.stdout.write("Sin citas para recordar.")
            return
        # Moteros sin cuenta enlazada a la cita: se buscan por celular en una sola consulta
        celulares = {}
        for c in citas:
            if not c.usuario_id:
                try:
                    celulares[c.pk] = normalizar_celular(c.telefono)
                except Exception:
                    pass
        por_celular = {m.celular: m.usuario for m in Motociclista.objects.filter(
            celular__in=set(celulares.values()), usuario__isnull=False).select_related("usuario")}
        enviados, por_taller = 0, {}
        for c in citas:
            usuario = c.usuario or por_celular.get(celulares.get(c.pk))
            servicio = f" ({c.servicio.nombre.lower()})" if c.servicio else ""
            if usuario and notificar(
                    usuario, f"cita-recordatorio:{c.pk}:{manana}", f"Mañana tienes cita en {c.taller.nombre}",
                    f"{manana:%d/%m}{_hora(c.hora)}{servicio}. Si no puedes ir, escríbele al taller por WhatsApp.",
                    c.taller.get_absolute_url(), Notificacion.Tipo.TALLER):
                enviados += 1
            por_taller.setdefault(c.taller, []).append(c)
        for taller, lista in por_taller.items():
            n = len(lista)
            notificar(taller.usuario, f"agenda-manana:{taller.pk}:{manana}", f"Mañana tienes {n} cita{'s' if n != 1 else ''}",
                      ", ".join(f"{c.nombre}{_hora(c.hora)}" for c in lista[:4]) + (f" y {n - 4} más" if n > 4 else ""),
                      reverse("talleres:panel") + "#citas", Notificacion.Tipo.TALLER)
        SolicitudCita.objects.filter(pk__in=[c.pk for c in citas]).update(recordatorio_enviado=timezone.now())
        self.stdout.write(self.style.SUCCESS(f"{len(citas)} cita(s) de mañana; {enviados} recordatorio(s) a moteros."))
