from django.urls import path

from . import views

app_name = "ayuda"

urlpatterns = [
    path("ayuda/catalogo.json", views.catalogo_json, name="catalogo"),
    path("ayuda/preguntar/", views.preguntar, name="preguntar"),
]
