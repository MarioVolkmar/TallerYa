from django.urls import path

from . import views

app_name = "consola"
urlpatterns = [
    path("consola/", views.consola, name="inicio"),
    path("consola/accion/<str:clave>/<int:pk>/", views.ejecutar, name="accion"),
]
