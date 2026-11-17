from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_control
from django.views.static import serve

admin.site.site_header = "TallerYa · Administración"
admin.site.site_title = "TallerYa"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("consola.urls")),
    path("", include("cuentas.urls")),
    path("", include("foro.urls")),
    path("", include("garaje.urls")),
    path("", include("notificaciones.urls")),
    path("", include("noticias.urls")),
    path("", include("logros.urls")),
    path("", include("tramites.urls")),
    path("", include("ayuda.urls")),
    path("", include("cupones.urls")),
    path("", include("talleres.urls")),
    # Fotos subidas por los talleres. Suficiente para el MVP (en Render, con un Disk montado en
    # DJANGO_MEDIA_ROOT); con mucho tráfico conviene moverlas a un almacenamiento como S3 o Cloudinary.
    # Caché de 7 días: cada subida tiene nombre propio (uuid o sufijo de Django), una foto nueva nunca reusa el nombre.
    re_path(r"^media/(?P<path>.*)$", cache_control(public=True, max_age=7 * 24 * 3600)(serve),
            {"document_root": settings.MEDIA_ROOT}),
]
