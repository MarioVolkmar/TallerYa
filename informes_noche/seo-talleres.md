# SEO de TallerYa (talleres)

## Qué se hizo
- `templates/base.html`: `{% block seo %}{% seo %}{% endblock %}` en el `<head>`. Por defecto da descripción, canonical, Open Graph (og:title/description/image/url, locale es_CO) y Twitter card. Cada página lo sobreescribe con su título y descripción.
- `talleres/templatetags/seo.py`: etiquetas `seo` y `json_ld_taller`. Plantilla `talleres/_seo.html`.
- Imagen para compartir: `talleres/static/talleres/img/og.png` (1200×630, provisional; conviene reemplazarla por una con la marca real).
- Páginas con meta propia: portada (por defecto), directorio, detalle de taller, foro, pregunta, rodadas, rodada, cupones, emergencias.
- Detalle de taller: JSON-LD `AutoRepair` (nombre, dirección, teléfono, descripción, foto, geo, horarios por turno, `aggregateRating` si hay reseñas).
- Páginas por barrio y servicio, que reutilizan `directorio()` con filtros fijos (sin duplicar lógica):
  - `/talleres/en/<barrio>/`  ·  `/talleres/servicio/<servicio>/`  ·  `/talleres/servicio/<servicio>/<barrio>/`
  - Slugs calculados al vuelo con `slugify` (sin migración). Solo existen si hay talleres activos; una combinación vacía da 404.
  - Texto propio (h1, intro, título, descripción) en `talleres/seo.py`.
- `/sitemap.xml` y `/robots.txt` en `talleres/seo.py`. El sitemap es XML propio, porque `django.contrib.sitemaps` exige tocar `INSTALLED_APPS` (settings no se tocó). Incluye talleres activos, barrios, servicios, combinaciones, preguntas visibles y rodadas.
- `robots.txt` excluye admin, cuenta, garaje, mi-taller, tareas, hoja-de-vida, notificaciones, cupón/canje, media y otras rutas privadas.
- Indexación: lista blanca de rutas públicas en `talleres/seo.py::es_indexable`. Todo lo demás sale con `noindex,follow`. Cualquier URL con parámetros GET (`?q`, `?pagina`, filtros) también sale `noindex`, con canonical a la página limpia.

## Pruebas
`talleres/tests_seo.py` (10 pruebas): robots, sitemap, páginas de barrio y servicio, 404s, JSON-LD, meta en páginas públicas y noindex en privadas. Suite completa corrida al final (ver respuesta a Auxiliares).

## Pendiente / recomendaciones al desplegar
- Registrar el dominio en Google Search Console y enviar `/sitemap.xml`.
- `request.build_absolute_uri` usa el host real; en Render confirmar `SECURE_PROXY_SSL_HEADER`/`USE_X_FORWARDED_HOST` para que los canonical salgan con `https` (esto está en settings, lo toca otra sesión).
- Reemplazar `og.png` por una imagen de marca.
- Opcional: enlaces internos a barrios y servicios desde el directorio o el pie, para que Google los descubra además del sitemap.
- Noticias: solo se indexa el listado/artículos por la regla de rutas; no están en el sitemap.
