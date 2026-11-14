from django.urls import path

from . import views

app_name = "notificaciones"

urlpatterns = [
    path("notificaciones/", views.lista, name="lista"),
    path("notificaciones/panel/", views.panel, name="panel"),
    path("notificaciones/<int:pk>/ir/", views.ir, name="ir"),
    path("notificaciones/leidas/", views.marcar_todas, name="marcar_todas"),
]
