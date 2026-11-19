"""Runner de pruebas de TallerYa.

Igual al de Django, más:
- paralelo por defecto (hasta 6 procesos; `--parallel 1` lo apaga);
- tiempos por prueba (TEST_TIMING=archivo.json);
- plantilla de la base de pruebas: la primera vez se crea con las migraciones de siempre
  (incluidas las de datos que siembran catálogos) y se guarda una copia SQLite fuera del
  repo; las siguientes veces se copia esa plantilla en vez de migrar (~30 s menos).
  La plantilla se identifica con un hash de todos los archivos de migraciones de las apps
  instaladas (y de Django y los ajustes de bases), así que cambiar o agregar una migración
  la regenera sola. `PRUEBAS_SIN_PLANTILLA=1` obliga a migrar como antes.
"""
import hashlib
import json
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

import django
from django.apps import apps
from django.conf import settings
from django.db import connections
from django.core import management as gestion
from django.test.runner import DiscoverRunner

CARPETA_PLANTILLAS = Path(tempfile.gettempdir()) / "tallerya_pruebas"


class _Resultado(unittest.TextTestResult):
    def startTest(self, test):
        self._t0 = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self.tiempos = getattr(self, "tiempos", {})
        self.tiempos[test.id()] = time.perf_counter() - self._t0


def _clave_migraciones():
    """Hash de todo lo que define el esquema y los datos sembrados por migraciones."""
    h = hashlib.sha256()
    h.update(django.get_version().encode())
    h.update(json.dumps(getattr(settings, "MIGRATION_MODULES", {}), sort_keys=True, default=str).encode())
    for app in sorted(apps.get_app_configs(), key=lambda a: a.label):
        h.update(app.label.encode())
        carpeta = Path(app.path) / "migrations"
        archivos = sorted(carpeta.glob("*.py")) if carpeta.is_dir() else []
        if not archivos:
            # App sin migraciones: migrate la crea con syncdb a partir de los modelos.
            archivos = sorted(Path(app.path).glob("models*.py")) + sorted(Path(app.path).glob("models/*.py"))
        for archivo in archivos:
            h.update(archivo.name.encode())
            h.update(archivo.read_bytes())
    return h.hexdigest()[:20]


def _es_sqlite_en_memoria(alias):
    conexion = connections[alias]
    return conexion.vendor == "sqlite" and conexion.creation.is_in_memory_db(
        conexion.settings_dict["NAME"]
    )


def _copiar_plantilla(plantilla, destino):
    """Copia la plantilla a la base en memoria. False si no existe o no se pudo leer (entonces se migra)."""
    try:
        fuente = sqlite3.connect(f"{plantilla.as_uri()}?mode=ro", uri=True)
    except sqlite3.Error:
        return False
    try:
        fuente.backup(destino)
        try:
            os.utime(plantilla)  # marca de uso, para la limpieza semanal
        except OSError:
            pass
        return destino.execute("SELECT count(*) FROM django_migrations").fetchone()[0] > 0
    except sqlite3.Error:
        return False
    finally:
        fuente.close()


def _guardar_plantilla(plantilla, origen):
    """Guarda la base recién migrada. Escribe a un temporal y lo renombra (seguro con varias sesiones a la vez)."""
    try:
        CARPETA_PLANTILLAS.mkdir(parents=True, exist_ok=True)
        temporal = plantilla.with_suffix(f".{os.getpid()}.tmp")
        destino = sqlite3.connect(temporal)
        try:
            origen.backup(destino)
        finally:
            destino.close()
        os.replace(temporal, plantilla)
        # Limpieza: plantillas sin usar hace más de una semana (otras ramas o worktrees pueden usar otras claves).
        limite = time.time() - 7 * 24 * 3600
        for vieja in CARPETA_PLANTILLAS.glob("*.sqlite3"):
            if vieja != plantilla and vieja.stat().st_mtime < limite:
                vieja.unlink(missing_ok=True)
    except OSError:
        pass  # sin plantilla, la próxima vez simplemente vuelve a migrar


class TallerYaRunner(DiscoverRunner):
    def __init__(self, *args, parallel=0, **kwargs):
        # Paralelo por defecto (en Windows usa spawn); `--parallel 1` lo desactiva.
        if not parallel:
            # Un proceso por núcleo físico (cpu_count cuenta hilos): más procesos solo pelean por la CPU.
            parallel = max(1, min((os.cpu_count() or 2) // 2, 6))
        super().__init__(*args, parallel=parallel, **kwargs)

    def get_resultclass(self):
        base = super().get_resultclass()
        if not os.environ.get("TEST_TIMING"):
            return base
        return type("Resultado", (_Resultado, base), {}) if base else _Resultado

    def setup_databases(self, **kwargs):
        if os.environ.get("PRUEBAS_SIN_PLANTILLA"):
            return super().setup_databases(**kwargs)
        clave = _clave_migraciones()
        original = gestion.call_command
        verbosidad = self.verbosity

        def call_command(nombre, *args, **opciones):
            alias = opciones.get("database")
            if nombre != "migrate" or not alias or not _es_sqlite_en_memoria(alias):
                return original(nombre, *args, **opciones)
            plantilla = CARPETA_PLANTILLAS / f"{alias}-{clave}.sqlite3"
            conexion = connections[alias]
            conexion.ensure_connection()
            if _copiar_plantilla(plantilla, conexion.connection):
                if verbosidad >= 1:
                    print(f"Base de pruebas '{alias}' copiada de la plantilla {plantilla.name}.")
                return None
            resultado = original(nombre, *args, **opciones)
            _guardar_plantilla(plantilla, conexion.connection)
            return resultado

        gestion.call_command = call_command
        try:
            return super().setup_databases(**kwargs)
        finally:
            gestion.call_command = original

    def run_suite(self, suite, **kwargs):
        resultado = super().run_suite(suite, **kwargs)
        destino = os.environ.get("TEST_TIMING")
        if destino and hasattr(resultado, "tiempos"):
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(resultado.tiempos, f)
        return resultado
