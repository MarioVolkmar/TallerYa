from django.urls import path

from . import views

app_name = "cotizador"
urlpatterns = [
    path("parte/<int:pk>/", views.cotizar_parte, name="parte"),
    path("codigo/", views.cotizar_codigo, name="codigo"),
]
