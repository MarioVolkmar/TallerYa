from django.urls import path

from . import views

app_name = "logros"

urlpatterns = [
    path("insignias/", views.mis_insignias, name="mis_insignias"),
    path("insignias/canjear/<int:pk>/", views.canjear, name="canjear"),
]
