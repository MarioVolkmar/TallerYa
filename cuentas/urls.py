from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import EntrarForm

app_name = "cuentas"

urlpatterns = [
    path("cuenta/registro/", views.registro, name="registro"),
    path("cuenta/entrar/", auth_views.LoginView.as_view(
        template_name="cuentas/entrar.html", authentication_form=EntrarForm,
    ), name="entrar"),
    path("cuenta/salir/", auth_views.LogoutView.as_view(), name="salir"),
    path("cuenta/", views.mi_cuenta, name="mi_cuenta"),
    path("cuenta/regalo/", views.reclamar_regalo, name="reclamar_regalo"),
    path("plus/", views.plus, name="plus"),
    path("plus/solicitar/", views.solicitar_plus, name="solicitar_plus"),

    # Recuperar contraseña por correo
    path("cuenta/recuperar/", auth_views.PasswordResetView.as_view(
        template_name="cuentas/recuperar.html",
        email_template_name="cuentas/correo_recuperar.txt",
        subject_template_name="cuentas/asunto_recuperar.txt",
        success_url=reverse_lazy("cuentas:recuperar_enviado"),
    ), name="recuperar"),
    path("cuenta/recuperar/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="cuentas/recuperar_enviado.html",
    ), name="recuperar_enviado"),
    path("cuenta/recuperar/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="cuentas/recuperar_nueva.html",
        success_url=reverse_lazy("cuentas:recuperar_listo"),
    ), name="recuperar_confirmar"),
    path("cuenta/recuperar/listo/", auth_views.PasswordResetCompleteView.as_view(
        template_name="cuentas/recuperar_listo.html",
    ), name="recuperar_listo"),
]
