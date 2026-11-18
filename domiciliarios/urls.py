from django.urls import path

from . import views

app_name = "domiciliarios"

urlpatterns = [
    path("domiciliarios/", views.presentacion, name="inicio"),
    path("domiciliarios/activar/", views.activar, name="activar"),
    path("domiciliarios/salir/", views.salir, name="salir"),
    path("domiciliarios/mi-ruta/", views.panel, name="panel"),
    path("domiciliarios/jornada/", views.jornada, name="jornada"),
    path("domiciliarios/plus/", views.solicitar_plus, name="plus"),
    path("domiciliarios/comprobante/anular/", views.anular_comprobante, name="anular_comprobante"),
    path("domiciliarios/c/<str:token>/", views.comprobante_publico, name="comprobante"),
]
