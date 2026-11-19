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
    path("domiciliarios/verificacion/", views.verificacion, name="verificacion"),
    path("domiciliarios/verificacion/retirar/", views.cancelar_verificacion, name="cancelar_verificacion"),
    path("domiciliarios/verificacion/<int:pk>/<str:campo>/", views.verificacion_foto, name="verificacion_foto"),
    path("domiciliarios/moto/<int:pk>/trabajo/", views.moto_trabajo, name="moto_trabajo"),
    path("domiciliarios/c/<str:token>/", views.comprobante_publico, name="comprobante"),
]
