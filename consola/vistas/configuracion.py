"""Sección Configuración: interruptores de módulos (solo superusuario). Cada cambio queda en la bitácora con antes y después."""
from django.urls import reverse

from .. import ajustes
from ..acciones import accion
from ..models import Ajuste


def _estado(ajuste):
    return "Prendido" if ajuste.valor else "Apagado"


@accion("ajustes.cambiar", modelo=Ajuste, nombre="Prender o apagar ajuste", superusuario=True,
        campos={"valor": ("Estado", _estado)},
        frase="{verbo} «{obj}»", exito="{verbo} «{obj}».")
def _cambiar(request, obj):
    obj.valor = request.POST.get("valor") == "1"
    obj.save(update_fields=["valor"])
    return {"ctx": {"verbo": "Prendió" if obj.valor else "Apagó"}}


def seccion(request):
    filas = [(m, ajustes.ajuste(m.clave), reverse("consola:ajuste", args=[m.clave])) for m in ajustes.MODULOS]
    pres = [(m, ajustes.ajuste(m.clave), reverse("consola:ajuste", args=[m.clave])) for m in ajustes.PRESENTACION]
    return "consola/configuracion.html", {"modulos": filas, "presentacion": pres}
