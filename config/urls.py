from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "TallerYa · Administración"
admin.site.site_title = "TallerYa"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("cuentas.urls")),
    path("", include("foro.urls")),
    path("", include("cupones.urls")),
    path("", include("talleres.urls")),
    # Fotos subidas por los talleres. Suficiente para el MVP (en Render, con un Disk montado en
    # DJANGO_MEDIA_ROOT); con mucho tráfico conviene moverlas a un almacenamiento como S3 o Cloudinary.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
