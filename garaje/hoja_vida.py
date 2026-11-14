"""Hoja de vida verificada: códigos de un solo uso para el taller y enlaces públicos revocables.

Privacidad: un taller nunca busca motos por placa; solo ve una moto cuando el dueño le muestra un código vigente.
"""
import re
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import CodigoServicio, EnlaceHojaVida, LecturaKm, RegistroServicio

ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin 0/O, 1/I/L para dictarlo sin errores
LARGO_CODIGO = 6
MINUTOS_CODIGO = 30


class CodigoInvalido(Exception):
    """El código no existe, ya se usó o caducó."""


def normalizar(texto):
    return re.sub(r"[^A-Z0-9]", "", (texto or "").upper())


def generar_codigo(moto):
    """Código nuevo para esta moto; anula los anteriores sin usar (solo hay uno vivo a la vez)."""
    ahora = timezone.now()
    moto.codigos_servicio.filter(usado__isnull=True, vence__gt=ahora).update(vence=ahora)
    while True:
        codigo = "".join(secrets.choice(ALFABETO) for _ in range(LARGO_CODIGO))
        if not CodigoServicio.objects.filter(codigo=codigo).exists():
            return CodigoServicio.objects.create(moto=moto, codigo=codigo, vence=ahora + timedelta(minutes=MINUTOS_CODIGO))


def codigo_vigente(moto):
    return moto.codigos_servicio.filter(usado__isnull=True, vence__gt=timezone.now()).order_by("-creado").first()


def buscar_codigo(texto):
    """CodigoServicio vigente para ese texto, o None."""
    codigo = normalizar(texto)
    if len(codigo) != LARGO_CODIGO:
        return None
    return (CodigoServicio.objects.select_related("moto", "moto__linea", "moto__linea__marca")
            .filter(codigo=codigo, usado__isnull=True, vence__gt=timezone.now()).first())


def registrar_verificado(taller, codigo, *, fecha, km, servicios, notas="", costo=None):
    """Crea un registro verificado con el código del dueño y lo gasta. Lanza CodigoInvalido si no sirve."""
    with transaction.atomic():
        obj = CodigoServicio.objects.select_for_update().filter(
            codigo=normalizar(codigo), usado__isnull=True, vence__gt=timezone.now()).first()
        if not obj or not taller:
            raise CodigoInvalido("El código no es válido o ya caducó. Pídele al motero uno nuevo.")
        obj.usado = timezone.now()
        obj.save(update_fields=["usado"])
        registro = RegistroServicio(moto=obj.moto, fecha=fecha, km=km, servicios=servicios, notas=notas,
                                    costo=costo, taller=taller)
        registro.verificado = True
        registro.save()
        moto = obj.moto
        if km > moto.km_actual:  # el taller vio el odómetro: también cuenta como lectura de kilometraje
            LecturaKm.objects.create(moto=moto, km=km, fecha=fecha)
            moto.km_actual = km
            moto.save(update_fields=["km_actual"])
    return registro


def enlace_activo(moto):
    return moto.enlaces_hoja_vida.filter(revocado__isnull=True).order_by("-creado").first()


def crear_enlace(moto):
    return enlace_activo(moto) or EnlaceHojaVida.objects.create(moto=moto)


def revocar_enlaces(moto):
    return moto.enlaces_hoja_vida.filter(revocado__isnull=True).update(revocado=timezone.now())


def placa_enmascarada(placa):
    """ABC12D → A••••D: sirve para reconocerla sin exponerla."""
    placa = (placa or "").strip().upper()
    if len(placa) < 3:
        return "Sin placa"
    return placa[0] + "•" * (len(placa) - 2) + placa[-1]


def resumen(registros):
    verificados = [r for r in registros if r.verificado]
    return {"total": len(registros), "verificados": len(verificados),
            "talleres": sorted({r.taller.nombre for r in verificados if r.taller})}
