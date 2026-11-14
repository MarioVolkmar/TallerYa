from django.urls import path

from . import views

app_name = "garaje"

urlpatterns = [
    path("garaje/", views.garaje, name="garaje"),
    path("garaje/agregar/", views.agregar, name="agregar"),
    path("garaje/<int:pk>/", views.detalle, name="moto"),
    path("garaje/<int:pk>/editar/", views.editar, name="editar"),
    path("garaje/<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path("garaje/<int:pk>/documento/<slug:clave>/", views.documento, name="documento"),
    path("garaje/<int:pk>/km/", views.registrar_km, name="registrar_km"),
    path("garaje/<int:pk>/al-dia/", views.poner_al_dia, name="poner_al_dia"),
    path("garaje/agregar/mantenimientos/", views.tareas_alta, name="tareas_alta"),
    path("garaje/<int:pk>/ajustar/", views.ajustar_tarea, name="ajustar_tarea"),
    path("garaje/<int:pk>/soat/", views.cotizar_soat, name="cotizar_soat"),
    path("garaje/<int:pk>/personalizar/", views.personalizar, name="personalizar"),
    path("garaje/<int:pk>/vista-3d/", views.vista_3d, name="vista_3d"),
    path("garaje/<int:pk>/mantenimiento/", views.registrar_mantenimiento, name="registrar_mantenimiento"),
    path("garaje/diagrama/<slug:clave>.svg", views.diagrama_svg, name="diagrama"),
    path("garaje/diagrama/<slug:clave>/<slug:puesto>.svg", views.pieza_svg, name="pieza_svg"),
]
