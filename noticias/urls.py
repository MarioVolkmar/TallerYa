from django.urls import path

from . import views

app_name = "noticias"
urlpatterns = [
    path("noticias/", views.lista, name="lista"),
    path("noticias/<slug:slug>/", views.articulo, name="articulo"),
]
