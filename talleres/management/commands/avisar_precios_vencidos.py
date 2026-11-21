"""Correo simple a los talleres cuyos precios de mano de obra llevan más de 75 días sin confirmarse (para cron, a diario).

Idempotente: cada taller guarda `precios_aviso_enviado` y no recibe otro correo hasta pasados 75 días. Usa el backend de
correo configurado (en local imprime en consola).

    python manage.py avisar_precios_vencidos
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from talleres import precios
from talleres.models import Taller


class Command(BaseCommand):
    help = "Avisa por correo a los talleres con precios sin confirmar hace más de 75 días (no repite)."

    def handle(self, *args, **opciones):
        ahora = timezone.now()
        limite = precios.limite_vencimiento(ahora)
        talleres = (Taller.objects.filter(activo=True, usuario__isnull=False, precios__actualizado__lt=limite)
                    .filter(Q(precios_aviso_enviado__isnull=True) | Q(precios_aviso_enviado__lt=limite))
                    .exclude(usuario__email="").select_related("usuario").distinct())
        enviados = 0
        for t in talleres:
            enlace = (settings.SITIO_URL or "").rstrip("/") + reverse("talleres:precios")
            send_mail(
                "Confirma tus precios en TallerYa",
                f"Hola {t.nombre},\n\nTus precios de mano de obra llevan más de 2 meses sin confirmarse. "
                f"Entra y toca «Siguen vigentes» o actualízalos:\n{enlace}\n\nTallerYa",
                None, [t.usuario.email])
            Taller.objects.filter(pk=t.pk).update(precios_aviso_enviado=ahora)
            enviados += 1
        self.stdout.write(f"Correos enviados: {enviados}.")
