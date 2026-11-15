"""Genera un par de claves VAPID para los avisos push (se imprimen; no se guardan en ningún archivo)."""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


def _b64(datos):
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


class Command(BaseCommand):
    help = "Genera claves VAPID (VAPID_PUBLIC_KEY y VAPID_PRIVATE_KEY) para Web Push."

    def handle(self, *args, **opciones):
        k = ec.generate_private_key(ec.SECP256R1())
        privada = _b64(k.private_numbers().private_value.to_bytes(32, "big"))
        publica = _b64(k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
        self.stdout.write(f"VAPID_PUBLIC_KEY={publica}\nVAPID_PRIVATE_KEY={privada}")
