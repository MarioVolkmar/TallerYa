from django.urls import path

from . import views

app_name = "talleres"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("taller/<slug:slug>/", views.detalle, name="detalle"),
    path("registra-tu-taller/", views.registro, name="registro"),
]
