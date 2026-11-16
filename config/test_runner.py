"""Runner de pruebas de TallerYa: igual al de Django, más tiempos por prueba (TEST_TIMING=archivo.json)."""
import json
import os
import time
import unittest

from django.test.runner import DiscoverRunner


class _Resultado(unittest.TextTestResult):
    def startTest(self, test):
        self._t0 = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self.tiempos = getattr(self, "tiempos", {})
        self.tiempos[test.id()] = time.perf_counter() - self._t0


class TallerYaRunner(DiscoverRunner):
    def __init__(self, *args, parallel=0, **kwargs):
        # Paralelo por defecto (en Windows usa spawn); `--parallel 1` lo desactiva.
        if not parallel:
            parallel = min(os.cpu_count() or 1, 6)
        super().__init__(*args, parallel=parallel, **kwargs)

    def get_resultclass(self):
        base = super().get_resultclass()
        if not os.environ.get("TEST_TIMING"):
            return base
        return type("Resultado", (_Resultado, base), {}) if base else _Resultado

    def run_suite(self, suite, **kwargs):
        resultado = super().run_suite(suite, **kwargs)
        destino = os.environ.get("TEST_TIMING")
        if destino and hasattr(resultado, "tiempos"):
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(resultado.tiempos, f)
        return resultado
