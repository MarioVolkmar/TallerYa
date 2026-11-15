from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import citas, views
from .forms import EntrarForm, RecuperarForm

app_name = "cuentas"

urlpatterns = [
    path("cuenta/registro/", views.registro, name="registro"),
    path("cuenta/entrar/", views.EntrarView.as_view(authentication_form=EntrarForm), name="entrar"),
    path("cuenta/salir/", auth_views.LogoutView.as_view(), name="salir"),
    path("cuenta/", views.mi_cuenta, name="mi_cuenta"),
    path("cuenta/citas/<int:pk>/", citas.detalle, name="cita"),
    path("cuenta/citas/<int:pk>/cancelar/", citas.cancelar, name="cita_cancelar"),
    path("cuenta/citas/<int:pk>/calendario.ics", citas.ics, name="cita_ics"),
    path("cuenta/avatar/", views.cambiar_avatar, name="avatar"),
    path("cuenta/calificar/<int:pk>/", views.calificar_taller, name="calificar_taller"),
    path("cuenta/google/", views.google_entrar, name="google"),
    path("cuenta/google/volver/", views.google_volver, name="google_volver"),
    path("cuenta/completar/", views.completar_perfil, name="completar"),
    path("cuenta/verificar/<uidb64>/<token>/", views.verificar_correo, name="verificar"),
    path("cuenta/verificar/reenviar/", views.reenviar_verificacion, name="reenviar_verificacion"),
    path("cuenta/contrasena/", views.contrasena, name="contrasena"),
    path("cuenta/administracion/", views.administracion, name="administracion"),
    path("cuenta/administracion/taller/<int:pk>/aprobar/", views.aprobar_taller, name="aprobar_taller"),
    path("cuenta/regalo/", views.reclamar_regalo, name="reclamar_regalo"),
    path("plus/", views.plus, name="plus"),
    path("plus/solicitar/", views.solicitar_plus, name="solicitar_plus"),

    # Recuperar contraseña por correo
    path("cuenta/recuperar/", views.RecuperarView.as_view(), name="recuperar"),
    path("cuenta/recuperar/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="cuentas/recuperar_enviado.html",
    ), name="recuperar_enviado"),
    path("cuenta/recuperar/<uidb64>/<token>/", views.RecuperarConfirmar.as_view(
        success_url=reverse_lazy("cuentas:recuperar_listo"),
    ), name="recuperar_confirmar"),
    path("cuenta/recuperar/listo/", auth_views.PasswordResetCompleteView.as_view(
        template_name="cuentas/recuperar_listo.html",
    ), name="recuperar_listo"),
]
