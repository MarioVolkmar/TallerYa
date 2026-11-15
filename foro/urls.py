"""Rutas del foro: lista, preguntar, ver pregunta, marcar mejor respuesta, reportar y votar."""
from django.urls import path

from . import rodadas, views

app_name = "foro"

urlpatterns = [
    path("foro/", views.lista, name="lista"),
    path("foro/preguntar/", views.preguntar, name="preguntar"),
    path("foro/<int:pk>/", views.pregunta, name="pregunta_corta"),
    path("foro/<int:pk>/<slug:slug>/", views.pregunta, name="pregunta"),
    path("foro/respuesta/<int:pk>/mejor/", views.marcar_mejor, name="marcar_mejor"),
    path("foro/reportar/<str:tipo>/<int:pk>/", views.reportar, name="reportar"),
    path("foro/rodadas/", rodadas.lista, name="rodadas"),
    path("foro/rodadas/nueva/", rodadas.crear, name="rodada_crear"),
    path("foro/rodadas/<int:pk>/", rodadas.detalle, name="rodada"),
    path("foro/rodadas/<int:pk>/voy/", rodadas.voy, name="rodada_voy"),
    path("foro/reaccionar/<str:tipo>/<int:pk>/", views.reaccionar, name="reaccionar"),
    path("foro/editar/<str:tipo>/<int:pk>/", views.editar, name="editar"),
    path("foro/eliminar/<str:tipo>/<int:pk>/", views.eliminar, name="eliminar"),
    path("foro/integrante/<int:pk>/", views.integrante, name="integrante"),
    path("foro/usuarios/", views.sugerir_usuarios, name="sugerir_usuarios"),
    path("foro/votar/<str:tipo>/<int:pk>/", views.votar, name="votar"),
]
