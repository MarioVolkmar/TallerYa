from django.urls import path

from . import views

app_name = "metricas"
urlpatterns = [
    path("metricas/evento/", views.evento, name="evento"),
    path("metricas/exportar.csv", views.exportar, name="exportar"),
]
