from django.urls import path

from . import views

app_name = "talleres"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("taller/<slug:slug>/", views.detalle, name="detalle"),
    path("mi-taller/perfil/", views.editar_perfil, name="editar_perfil"),
    path("mi-taller/foto/<int:pk>/eliminar/", views.eliminar_foto, name="eliminar_foto"),
    path("registra-tu-taller/", views.registro, name="registro"),
    path("legal/<slug:pagina>/", views.legal, name="legal"),
]
