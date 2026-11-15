"""Rutas de notificaciones: lista, panel desplegable, abrir una y marcar todas como leídas; PWA y push."""
from django.urls import path

from . import views

app_name = "notificaciones"

urlpatterns = [
    path("notificaciones/", views.lista, name="lista"),
    path("notificaciones/panel/", views.panel, name="panel"),
    path("notificaciones/<int:pk>/ir/", views.ir, name="ir"),
    path("notificaciones/leidas/", views.marcar_todas, name="marcar_todas"),
    path("manifest.webmanifest", views.manifiesto, name="manifiesto"),
    path("sw.js", views.service_worker, name="sw"),
    path("sin-conexion/", views.sin_conexion, name="sin_conexion"),
    path("push/estado/", views.push_estado, name="push_estado"),
    path("push/suscribir/", views.push_suscribir, name="push_suscribir"),
    path("push/desactivar/", views.push_desactivar, name="push_desactivar"),
]
