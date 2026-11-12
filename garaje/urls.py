from django.urls import path

from . import views

app_name = "garaje"

urlpatterns = [
    path("garaje/", views.garaje, name="garaje"),
    path("garaje/agregar/", views.agregar, name="agregar"),
    path("garaje/<int:pk>/", views.detalle, name="moto"),
    path("garaje/<int:pk>/editar/", views.editar, name="editar"),
    path("garaje/<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path("garaje/<int:pk>/km/", views.registrar_km, name="registrar_km"),
    path("garaje/<int:pk>/mantenimiento/", views.registrar_mantenimiento, name="registrar_mantenimiento"),
]
