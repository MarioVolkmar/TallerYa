"""Límites de validación compartidos: los usan los formularios (servidor) y las plantillas (atributos del <input>).

Así el navegador avisa antes de enviar y el servidor rechaza lo mismo si alguien se salta el formulario.
"""
LIMITES = {
    "nombre": {"min": 2, "max": 150},       # first_name de Django: 150
    "apellido": {"min": 0, "max": 150},
    "correo": {"min": 6, "max": 254},
    "busqueda": {"min": 0, "max": 80},
    "contrasena_temporal": {"min": 12, "max": 12},
    "motivo": {"min": 5, "max": 200},          # = SolicitudCita.motivo_cancelacion
}
POR_PAGINA = {"usuarios": 10, "bitacora": 15, "talleres": 10, "cupones": 10, "citas": 10, "moderacion": 10}      # tamaño por defecto de cada listado
OPCIONES_POR_PAGINA = (10, 25, 50)                  # lo que puede elegir el administrador (?por=)


def maximo(campo):
    return LIMITES[campo]["max"]


def minimo(campo):
    return LIMITES[campo]["min"]
