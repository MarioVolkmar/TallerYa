"""Eliminación segura: antes de borrar se miran las dependencias con reglas declarativas.

Cada Dependencia cuenta cuántos registros dependen del objeto y dice qué pasa con ellos:
  - bloquea=True: no se puede borrar mientras exista (se explica por qué y se ofrece desactivar);
  - efecto: lo que les pasa si se borra ("se borran", "quedan anónimas").
Además se consulta el Collector de Django: si algún on_delete=PROTECT lo impide, también bloquea.
"""
from dataclasses import dataclass
from typing import Callable

from django.db import router
from django.db.models.deletion import Collector, ProtectedError, RestrictedError


@dataclass
class Dependencia:
    etiqueta: str            # en plural: "citas"
    singular: str            # "cita"
    contar: Callable         # funcion(obj) -> int
    bloquea: bool = False
    motivo: str = ""         # por qué bloquea
    efecto: str = ""         # qué pasa si se borra


@dataclass
class Analisis:
    filas: list
    bloqueos: list

    @property
    def se_puede(self):
        return not self.bloqueos

    @property
    def resumen(self):
        """Para el texto de confirmación: «Tiene 3 respuestas: se borran.»"""
        return "".join(f"{f['texto'].capitalize()}: {f['detalle']} " for f in self.filas)


def analizar(obj, reglas, extra_bloqueos=()):
    filas, bloqueos = [], list(extra_bloqueos)
    for dep in reglas:
        n = dep.contar(obj)
        if not n:
            continue
        nombre = dep.singular if n == 1 else dep.etiqueta
        fila = {"texto": f"tiene {n} {nombre}", "cantidad": n, "bloquea": dep.bloquea,
                "detalle": dep.motivo if dep.bloquea else dep.efecto}
        filas.append(fila)
        if dep.bloquea:
            bloqueos.append(f"Tiene {n} {nombre}: {dep.motivo}")
    try:
        Collector(using=router.db_for_write(type(obj))).collect([obj])
    except (ProtectedError, RestrictedError) as e:
        modelos = sorted({o._meta.verbose_name_plural for o in e.protected_objects}) if hasattr(e, "protected_objects") else []
        bloqueos.append("Hay registros protegidos que dependen de esta cuenta" + (f" ({', '.join(modelos)})." if modelos else "."))
    return Analisis(filas, bloqueos)
