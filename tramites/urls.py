from django.urls import path

from . import views

app_name = "tramites"

urlpatterns = [
    path("soat/", views.soat, name="soat"),
    path("soat/<int:pk>/pedir/", views.pedir_soat, name="pedir_soat"),
    path("soat/pedido/<int:pk>/pago-de-prueba/", views.pago_prueba, name="pago_prueba"),
    path("soat/pedido/<int:pk>/poliza/", views.poliza, name="poliza"),
    path("soat/pedido/<int:pk>/tarjeta/", views.tarjeta, name="tarjeta"),
    path("tecnomecanica/", views.tecnomecanica, name="tecnomecanica"),
]
