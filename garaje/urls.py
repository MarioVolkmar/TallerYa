from django.urls import path

from . import despiece_publico as dp, views
from .vista_diagnostico import despiece_publico, diagnostico
from .vista_bienvenida import bienvenida, bienvenida_listo, bienvenida_plan, bienvenida_saltar
from .vista_gastos import gastos_moto
from . import vista_etiquetar_3d as et3d
from .vista_ficha_diagnostico import enviar as diagnostico_enviar, ficha as ficha_diagnostico
from .vista_tareas import tarea
from .vista_servicio_taller import servicio_taller
from .vista_servicio_mecanico import servicio_mecanico, servicio_visita
from .vista_hoja_vida import (codigo_taller, hoja_vida_certificado, hoja_vida_moto, hoja_vida_publica, servicio_codigo,
                              traspaso)

app_name = "garaje"

urlpatterns = [
    path("garaje/", views.garaje, name="garaje"),
    path("garaje/agregar/", views.agregar, name="agregar"),
    path("garaje/etiquetar-3d/", et3d.indice, name="etiquetar_3d_indice"),  # solo staff
    path("garaje/etiquetar-3d/<str:modelo>/", et3d.pagina, name="etiquetar_3d"),
    path("garaje/etiquetar-3d/<str:modelo>/modelo.glb", et3d.glb, name="etiquetar_3d_glb"),
    path("garaje/etiquetar-3d/<str:modelo>/guardar/", et3d.guardar, name="etiquetar_3d_guardar"),
    path("bienvenida/", bienvenida, name="bienvenida"),
    path("bienvenida/saltar/", bienvenida_saltar, name="bienvenida_saltar"),
    path("bienvenida/<int:pk>/", bienvenida_plan, name="bienvenida_plan"),
    path("bienvenida/<int:pk>/listo/", bienvenida_listo, name="bienvenida_listo"),
    path("diagnostico/", diagnostico, name="diagnostico"),
    path("diagnostico/enviar/", diagnostico_enviar, name="diagnostico_enviar"),
    path("diagnostico/ficha/<str:token>/", ficha_diagnostico, name="ficha_diagnostico"),
    path("diagnostico/despiece/<int:pk>.json", despiece_publico, name="diagnostico_despiece"),
    path("garaje/<int:pk>/", views.detalle, name="moto"),
    path("garaje/<int:pk>/editar/", views.editar, name="editar"),
    path("garaje/<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path("garaje/<int:pk>/documento/<slug:clave>/", views.documento, name="documento"),
    path("garaje/<int:pk>/documento/<slug:clave>/subir/", views.subir_documento, name="subir_documento"),
    path("garaje/<int:pk>/km/", views.registrar_km, name="registrar_km"),
    path("garaje/<int:pk>/km/confirmar/", views.confirmar_km, name="confirmar_km"),
    path("garaje/<int:pk>/al-dia/", views.poner_al_dia, name="poner_al_dia"),
    path("garaje/agregar/mantenimientos/", views.tareas_alta, name="tareas_alta"),
    path("garaje/<int:pk>/ajustar/", views.ajustar_tarea, name="ajustar_tarea"),
    path("garaje/<int:pk>/personalizar/", views.personalizar, name="personalizar"),
    path("garaje/<int:pk>/pico-y-placa/", views.avisos_pico_placa, name="pico_placa"),
    path("garaje/<int:pk>/vista-3d/", views.vista_3d, name="vista_3d"),
    path("garaje/<int:pk>/despiece.json", views.despiece_json, name="despiece_json"),
    path("garaje/<int:pk>/mantenimiento/", views.registrar_mantenimiento, name="registrar_mantenimiento"),
    path("garaje/<int:pk>/hoja-de-vida/", hoja_vida_moto, name="hoja_vida"),
    path("garaje/<int:pk>/codigo-taller/", codigo_taller, name="codigo_taller"),
    path("garaje/<int:pk>/gastos/", gastos_moto, name="gastos"),
    path("garaje/servicio-taller/<int:pk>/", servicio_taller, name="servicio_taller"),
    path("garaje/servicio/<str:codigo>/", servicio_codigo, name="servicio_codigo"),
    path("mecanicos/registrar-servicio/", servicio_mecanico, name="servicio_mecanico"),
    path("mecanicos/visita-atendida/<int:pk>/servicio/", servicio_visita, name="servicio_visita"),
    path("tareas/<slug:nombre>/", tarea, name="tarea"),  # solo las de la lista fija vista_tareas.TAREAS
    path("hoja-de-vida/<str:token>/", hoja_vida_publica, name="hoja_vida_publica"),
    path("hoja-de-vida/<str:token>/certificado/", hoja_vida_certificado, name="hoja_vida_certificado"),
    path("garaje/traspaso/<str:token>/", traspaso, name="traspaso"),
    path("despiece/", dp.indice, name="despiece_indice"),  # públicas, para Google (despiece_publico.py)
    path("despiece/<slug:moto>/", dp.moto, name="despiece_moto"),
    path("despiece/<slug:moto>/<slug:sistema>/", dp.sistema, name="despiece_sistema"),
    path("garaje/diagrama/<slug:clave>.svg", views.diagrama_svg, name="diagrama"),
    path("garaje/diagrama/<slug:clave>/<slug:puesto>.svg", views.pieza_svg, name="pieza_svg"),
]
