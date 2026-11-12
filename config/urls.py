from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "TallerYa · Administración"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("cupones.urls")),
    path("", include("talleres.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
