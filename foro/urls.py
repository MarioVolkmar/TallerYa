from django.urls import path

from . import views

app_name = "foro"

urlpatterns = [
    path("foro/", views.lista, name="lista"),
    path("foro/preguntar/", views.preguntar, name="preguntar"),
    path("foro/<int:pk>/", views.pregunta, name="pregunta_corta"),
    path("foro/<int:pk>/<slug:slug>/", views.pregunta, name="pregunta"),
    path("foro/respuesta/<int:pk>/mejor/", views.marcar_mejor, name="marcar_mejor"),
    path("foro/reportar/<str:tipo>/<int:pk>/", views.reportar, name="reportar"),
]
