"""Ayudas para pruebas de cualquier app."""
import tempfile
from pathlib import Path
from unittest import mock


def usar_intervalos_generales(prueba):
    """Para pruebas que cuentan con los intervalos generales de la base (aceite cada 2.500 km, etc.): ignora los
    archivos del manual por línea (garaje/intervalos/*.json), que el equipo va llenando y cambiarían las cifras.
    Uso: en setUp, usar_intervalos_generales(self)."""
    from . import intervalos
    parche = mock.patch.object(intervalos, "CARPETA", Path(tempfile.mkdtemp()))
    parche.start()
    intervalos.limpiar_cache()
    prueba.addCleanup(parche.stop)
    prueba.addCleanup(intervalos.limpiar_cache)
