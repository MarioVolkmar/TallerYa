"""Mecanismo central de las acciones de la consola.

Cada acción se declara con `@accion(...)` y una regla: qué modelo toca, qué campos vigilar y qué frase escribir.
La vista única `ejecutar` (consola/views.py) se encarga del resto, igual para todas:
  1. verifica que sea administrador y que llegue por POST;
  2. toma una foto de los campos vigilados (antes);
  3. corre la acción dentro de una transacción;
  4. si sale bien, toma la foto de después y escribe la Bitácora con la frase y el detalle campo por campo;
  5. si la acción lanza ErrorAccion, no se registra nada y se responde el error.
Así ninguna acción puede olvidar la bitácora ni el permiso.
"""
from dataclasses import dataclass, field
from typing import Callable

from django.db import transaction

from .models import Bitacora

ACCIONES = {}
VACIO = "—"


class ErrorAccion(Exception):
    """La acción no se pudo hacer (validación, regla de negocio). El mensaje se muestra tal cual."""


@dataclass
class Regla:
    clave: str
    modelo: type
    frase: str              # str.format con obj, a (antes), d (después) y lo que devuelva la acción en "ctx"
    campos: dict            # {"campo": ("Etiqueta", funcion(obj) -> valor legible)}
    funcion: Callable = None
    exito: str = "Listo."   # mensaje para el aviso; mismo formato que la frase
    extras: dict = field(default_factory=dict)
    nombre: str = ""        # para el filtro de la bitácora: "Cambiar rol"


def accion(clave, *, modelo, frase, campos, exito="Listo.", nombre=""):
    def decorador(funcion):
        ACCIONES[clave] = Regla(clave, modelo, frase, campos, funcion, exito, nombre=nombre or clave)
        return funcion
    return decorador


def legible(valor):
    if valor is None or valor == "":
        return VACIO
    if valor is True:
        return "Sí"
    if valor is False:
        return "No"
    return str(valor)


def foto(obj, campos):
    return {nombre: legible(fn(obj)) for nombre, (_etiqueta, fn) in campos.items()}


def diferencias(regla, antes, despues):
    return [{"campo": c, "etiqueta": regla.campos[c][0], "antes": antes.get(c, VACIO), "despues": despues.get(c, VACIO)}
            for c in regla.campos if antes.get(c, VACIO) != despues.get(c, VACIO)]


def registrar(*, actor, clave, frase, obj_tipo, obj_id, obj_repr, cambios, ip=None):
    return Bitacora.objects.create(actor=actor, actor_nombre=(actor.get_full_name() or actor.email or actor.username)[:200],
                                   accion=clave, frase=frase[:300], objeto_tipo=obj_tipo, objeto_id=obj_id,
                                   objeto_repr=str(obj_repr)[:200], cambios=cambios, ip=ip)


def correr(regla, request, obj, ip=None):
    """Corre la acción y escribe la bitácora. Devuelve (mensaje, extra). Lanza ErrorAccion si no se pudo."""
    with transaction.atomic():
        # Bloquea la fila (en PostgreSQL) para que dos clics seguidos no lean el mismo "antes"
        obj = type(obj)._default_manager.select_for_update().get(pk=obj.pk)
        antes = foto(obj, regla.campos)
        pk, tipo, repr_ = obj.pk, obj._meta.model_name, str(obj)
        resultado = regla.funcion(request, obj) or {}
        if resultado.get("eliminado"):
            despues = {c: "(eliminado)" for c in regla.campos}
        else:
            obj.refresh_from_db()
            despues = foto(obj, regla.campos)
        cambios = resultado.get("cambios_extra", []) + diferencias(regla, antes, despues)
        if not cambios and not resultado.get("registrar_sin_cambios"):
            raise ErrorAccion("No había nada que cambiar.")
        datos = {"obj": obj, "pk": pk, "a": antes, "d": despues, **resultado.get("ctx", {})}
        registrar(actor=request.user, clave=regla.clave, frase=regla.frase.format(**datos), obj_tipo=tipo,
                  obj_id=pk, obj_repr=repr_, cambios=cambios, ip=ip)
    return regla.exito.format(**datos), resultado.get("extra", {})


# ---------- Fábricas para los casos repetidos (una línea por acción en cada sección) ----------
def interruptor(clave, *, modelo, campo, etiqueta, nombre, si, no, describe, antes_de=None, despues_de=None):
    """Acción que prende o apaga un campo booleano (POST valor=1/0).
    si/no: verbos para la frase ("Publicó"/"Despublicó"); describe: "el taller #{pk} ({obj.nombre})"."""
    @accion(clave, modelo=modelo, nombre=nombre, campos={campo: (etiqueta, lambda o: getattr(o, campo))},
            frase="{verbo} " + describe, exito="{verbo} " + describe + ".")
    def _interruptor(request, obj):
        valor = request.POST.get("valor") == "1"
        if antes_de:
            antes_de(request, obj, valor)
        setattr(obj, campo, valor)
        obj.save(update_fields=[campo])
        if despues_de:
            despues_de(request, obj, valor)
        return {"ctx": {"verbo": si if valor else no}}
    return _interruptor


def eliminador(clave, *, modelo, reglas, describe, nombre="Eliminar", extra=None):
    """Acción de eliminación segura: revisa las reglas (consola.eliminacion) y solo borra si nada lo impide."""
    from .eliminacion import analizar

    @accion(clave, modelo=modelo, nombre=nombre, campos={"registro": ("Registro", str)},
            frase="Eliminó " + describe, exito="Eliminado.")
    def _eliminar(request, obj):
        analisis = analizar(obj, reglas, extra(obj) if extra else ())
        if not analisis.se_puede:
            raise ErrorAccion("No se puede eliminar. " + " ".join(analisis.bloqueos))
        obj.delete()
        return {"eliminado": True}
    return _eliminar
