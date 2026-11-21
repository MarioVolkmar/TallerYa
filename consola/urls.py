from django.urls import path

from . import views
from .vistas import alta_taller

app_name = "consola"
urlpatterns = [
    path("consola/", views.consola, name="inicio"),
    path("consola/alta-taller/", alta_taller.alta, name="alta_taller"),
    path("consola/accion/<str:clave>/<int:pk>/", views.ejecutar, name="accion"),
]
