from django.urls import path

from . import views

app_name = "domicilio"

urlpatterns = [
    path("mecanicos/", views.listado, name="listado"),
    path("mecanicos/registro/", views.registro, name="registro"),
    path("mecanicos/mi-perfil/", views.mi_perfil, name="mi_perfil"),
    path("mecanicos/<slug:slug>/", views.ficha, name="ficha"),
]
