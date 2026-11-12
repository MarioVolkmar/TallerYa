from django.urls import path

from . import views

app_name = "cupones"

urlpatterns = [
    path("cupones/", views.lista, name="lista"),
    path("cupones/<int:pk>/", views.obtener, name="obtener"),
    path("cupon/<str:codigo>/", views.mi_cupon, name="mi_cupon"),
    path("r/<str:codigo>/", views.referido, name="referido"),
    path("canjear/", views.canjear_cupon, name="canjear"),
]
