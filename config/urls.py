from pathlib import PurePosixPath

from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_control
from django.views.static import serve

from cuentas.forms import EntrarAdminForm



@cache_control(public=True, max_age=7 * 24 * 3600)
def servir_media(request, path):
    """Solo imágenes y videos (talleres/subidas.EXTENSIONES_PUBLICAS). Un archivo con otra extensión (.html, .svg,
    .js…) responde 404 aunque exista, y la CSP `sandbox` impide que una respuesta de /media/ ejecute código."""
    from talleres.subidas import EXTENSIONES_PUBLICAS
    if PurePosixPath(path).suffix.lower() not in EXTENSIONES_PUBLICAS:
        raise Http404
    respuesta = serve(request, path, document_root=settings.MEDIA_ROOT)
    respuesta["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; media-src 'self'; sandbox"
    return respuesta


admin.site.site_header = "TallerYa · Administración"
admin.site.site_title = "TallerYa"
admin.site.login_form = EntrarAdminForm  # mismo límite de intentos que el login del sitio

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("consola.urls")),
    path("", include("metricas.urls")),
    path("", include("domiciliarios.urls")),  # 404 en todo mientras DOMICILIARIOS_ACTIVO esté apagado
    path("", include("cuentas.urls")),
    path("", include("foro.urls")),
    path("", include("garaje.urls")),
    path("", include("notificaciones.urls")),
    path("", include("noticias.urls")),
    path("", include("logros.urls")),
    path("", include("tramites.urls")),
    path("", include("ayuda.urls")),
    path("", include("cupones.urls")),
    path("", include("domicilio.urls")),
    path("", include("proveedores.urls")),
    path("cotizador/", include("cotizador.urls")),  # piloto; sus vistas responden 404 con COTIZADOR_ACTIVO=0
    path("", include("talleres.urls")),
    # Fotos subidas por los talleres. Suficiente para el MVP (en Render, con un Disk montado en
    # DJANGO_MEDIA_ROOT); con mucho tráfico conviene moverlas a un almacenamiento como S3 o Cloudinary.
    # Caché de 7 días: cada subida tiene nombre propio (uuid o sufijo de Django), una foto nueva nunca reusa el nombre.
    re_path(r"^media/(?P<path>.*)$", servir_media),
]
