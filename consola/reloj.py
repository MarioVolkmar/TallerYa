"""Reloj central de la consola: todo lo que necesite "ahora" o "hoy" lo pide aquí.

En pruebas se fija la fecha con `with reloj.fijar(datetime(...)):` en vez de parchear timezone en cada módulo.
"""
from contextlib import contextmanager

from django.utils import timezone

_fijo = None


def ahora():
    return _fijo or timezone.now()


def hoy():
    return timezone.localdate(ahora())


@contextmanager
def fijar(momento):
    """Congela el reloj en `momento` (datetime; si no trae zona, se toma la de settings)."""
    global _fijo
    if timezone.is_naive(momento):
        momento = timezone.make_aware(momento)
    anterior, _fijo = _fijo, momento
    try:
        yield momento
    finally:
        _fijo = anterior
