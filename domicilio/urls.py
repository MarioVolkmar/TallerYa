from django.urls import path

from . import views, vista_descuentos as vd, vista_solicitudes as vs

app_name = "domicilio"

urlpatterns = [
    path("mecanicos/", views.listado, name="listado"),
    path("mecanicos/registro/", views.registro, name="registro"),
    path("mecanicos/mi-panel/", views.panel, name="panel"),
    path("mecanicos/mi-panel/precios/", views.alternar_precios, name="alternar_precios"),
    path("mecanicos/mi-panel/urgencias/", views.alternar_urgencias, name="alternar_urgencias"),
    path("mecanicos/mi-perfil/", views.mi_perfil, name="mi_perfil"),
    path("mecanicos/mi-perfil/fotos/<int:pk>/borrar/", views.borrar_trabajo, name="borrar_trabajo"),
    path("mecanicos/mi-perfil/precios/", views.mis_precios, name="mis_precios"),
    path("mecanicos/mi-perfil/resenas/<int:pk>/responder/", views.responder_resena, name="responder_resena"),
    path("mecanicos/mi-panel/resenas/", views.resenas, name="resenas"),
    path("mecanicos/mi-panel/descuentos/", vd.descuentos, name="descuentos"),
    path("mecanicos/mi-panel/descuentos/nuevo/", vd.descuento_form, name="descuento_nuevo"),
    path("mecanicos/mi-panel/descuentos/<int:pk>/", vd.descuento_form, name="descuento_editar"),
    path("mecanicos/mi-panel/descuentos/<int:pk>/pausar/", vd.descuento_pausar, name="descuento_pausar"),
    path("mecanicos/mi-perfil/solicitudes/", vs.solicitudes, name="solicitudes"),
    path("mecanicos/mi-perfil/solicitudes/<int:pk>/estado/", vs.solicitud_estado, name="solicitud_estado"),
    path("mecanicos/mi-perfil/solicitudes/<int:pk>/cotizar/", vs.solicitud_cotizar, name="solicitud_cotizar"),
    path("mecanicos/mi-perfil/solicitudes/<int:pk>/descuento/", vs.solicitud_descuento, name="solicitud_descuento"),
    path("mecanicos/visita/<str:token>/", vs.visita_publica, name="visita_publica"),
    path("mecanicos/mi-taller/", views.mi_taller, name="mi_taller"),
    path("mecanicos/mi-taller/alternar/", views.alternar_taller, name="alternar_taller"),
    path("mecanicos/<slug:slug>/", views.ficha, name="ficha"),
    path("mecanicos/<slug:slug>/visita/", views.visita, name="visita"),
    path("mecanicos/<slug:slug>/favorito/", views.favorito, name="favorito"),
]
