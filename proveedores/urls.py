from django.urls import path

from . import views, vistas_consola

app_name = "proveedores"
urlpatterns = [
    path("proveedores/unete/", views.autoregistro, name="unete"),
    path("proveedores/enviada/<str:token>/", views.enviada, name="enviada"),
    path("proveedores/ficha/<str:token>/", views.revisar, name="revisar"),
    path("proveedores/clic/<int:pk>/<str:canal>/", views.clic, name="clic"),
    # Consola (solo administradores)
    path("consola/proveedores/nuevo/", vistas_consola.editar, name="nuevo"),
    path("consola/proveedores/<int:pk>/editar/", vistas_consola.editar, name="editar"),
    path("consola/proveedores/<int:pk>/enlace/", vistas_consola.enlace, name="enlace"),
    path("consola/proveedores/categoria/nueva/", vistas_consola.categoria, name="categoria_nueva"),
    path("consola/proveedores/categoria/<int:pk>/", vistas_consola.categoria, name="categoria"),
]
