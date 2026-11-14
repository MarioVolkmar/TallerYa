from django.urls import path

from . import views

app_name = "talleres"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("talleres/", views.directorio, name="directorio"),
    path("taller/<slug:slug>/", views.detalle, name="detalle"),
    path("taller/<slug:slug>/favorito/", views.favorito, name="favorito"),
    path("taller/<slug:slug>/whatsapp/", views.ir, {"canal": "whatsapp"}, name="ir_whatsapp"),
    path("taller/<slug:slug>/llamar/", views.ir, {"canal": "llamar"}, name="ir_llamar"),
    path("mi-taller/registrar-servicio/", views.registrar_servicio, name="registrar_servicio"),
    path("taller/<slug:slug>/franjas/", views.franjas, name="franjas"),
    path("mi-taller/precios/", views.precios_taller, name="precios"),
    path("mi-taller/agenda/", views.agenda_taller, name="agenda"),
    path("mi-taller/estadisticas/", views.estadisticas_taller, name="estadisticas"),
    path("mi-taller/", views.panel, name="panel"),
    path("mi-taller/citas/", views.citas_taller, name="citas_taller"),
    path("mi-taller/resenas/", views.resenas_taller, name="resenas_taller"),
    path("mi-taller/cita/<int:pk>/estado/", views.cambiar_estado_cita, name="cita_estado"),
    path("mi-taller/cita/<int:pk>/reprogramar/", views.reprogramar_cita, name="cita_reprogramar"),
    path("cita/<str:token>/", views.cita_publica, name="cita_publica"),
    path("mi-taller/resena/<int:pk>/responder/", views.responder_resena, name="responder_resena"),
    path("mi-taller/cupones/nuevo/", views.cupon_taller, name="cupon_nuevo"),
    path("mi-taller/cupones/<int:pk>/", views.cupon_taller, name="cupon_editar"),
    path("mi-taller/cupones/<int:pk>/pausar/", views.pausar_cupon, name="cupon_pausar"),
    path("mi-taller/perfil/", views.editar_perfil, name="editar_perfil"),
    path("mi-taller/foto/<int:pk>/eliminar/", views.eliminar_foto, name="eliminar_foto"),
    path("emergencias/", views.emergencias, name="emergencias"),
    path("registra-tu-taller/", views.registro, name="registro"),
    path("legal/<slug:pagina>/", views.legal, name="legal"),
]
