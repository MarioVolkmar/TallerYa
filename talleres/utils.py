import secrets

from django.core.exceptions import ValidationError

# Sin 0/O ni 1/I/L para que los códigos se puedan dictar sin confusión.
ALFABETO_CODIGOS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def normalizar_celular(valor):
    """Devuelve el celular colombiano como 57XXXXXXXXXX o lanza ValidationError."""
    num = "".join(c for c in str(valor) if c.isdigit())
    if len(num) == 10:
        num = "57" + num
    if len(num) != 12 or not num.startswith("57"):
        raise ValidationError("Número no válido. Usa 10 dígitos, ej: 3001234567")
    return num


def codigo_aleatorio(largo, alfabeto=ALFABETO_CODIGOS):
    return "".join(secrets.choice(alfabeto) for _ in range(largo))
