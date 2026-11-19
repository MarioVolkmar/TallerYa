from django.urls import path

from . import views, vista_solicitudes as vs

app_name = "domicilio"

urlpatterns = [
    path("mecanicos/", views.listado, name="listado"),
    path("mecanicos/registro/", views.registro, name="registro"),
    path("mecanicos/mi-perfil/", views.mi_perfil, name="mi_perfil"),
    path("mecanicos/mi-perfil/fotos/<int:pk>/borrar/", views.borrar_trabajo, name="borrar_trabajo"),
    path("mecanicos/mi-perfil/precios/", views.mis_precios, name="mis_precios"),
    path("mecanicos/mi-perfil/resenas/<int:pk>/responder/", views.responder_resena, name="responder_resena"),
    path("mecanicos/mi-perfil/solicitudes/", vs.solicitudes, name="solicitudes"),
    path("mecanicos/mi-perfil/solicitudes/<int:pk>/estado/", vs.solicitud_estado, name="solicitud_estado"),
    path("mecanicos/mi-perfil/solicitudes/<int:pk>/cotizar/", vs.solicitud_cotizar, name="solicitud_cotizar"),
    path("mecanicos/visita/<str:token>/", vs.visita_publica, name="visita_publica"),
    path("mecanicos/mi-taller/", views.mi_taller, name="mi_taller"),
    path("mecanicos/mi-taller/alternar/", views.alternar_taller, name="alternar_taller"),
    path("mecanicos/<slug:slug>/", views.ficha, name="ficha"),
    path("mecanicos/<slug:slug>/visita/", views.visita, name="visita"),
    path("mecanicos/<slug:slug>/favorito/", views.favorito, name="favorito"),
]
