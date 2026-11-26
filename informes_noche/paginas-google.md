# Que Google encuentre TallerYa (25-nov-2026)

Sin commit y sin desplegar: **tallerya.co todavía no tiene nada de esto**.

## Qué ya había
Portada, directorio de talleres (con barrios y servicios), foro, cupones, mecánicos, despiece por moto y por sistema,
`sitemap.xml` y `robots.txt`. Las fallas frecuentes y los intervalos solo se veían con sesión, dentro de la moto.

## Qué es nuevo
| Página | URL de ejemplo |
|---|---|
| Índice por moto | `/motos/` |
| Moto (fallas, mantenimientos, consejos) | `/motos/yamaha-nmax-155/` |
| Falla | `/motos/yamaha-nmax-155/fallas/cvt-tiembla/` |
| «¿Cada cuánto…?» | `/motos/yamaha-aerox-155/mantenimiento/correa-cvt/` |
| Pieza | `/despiece/yamaha-nmax-155/pieza/multiple-de-admision/` |

Cada una tiene título, descripción, canónica y H1 propios, datos estructurados (migas, artículo o pregunta y
respuesta) y enlaces entre moto, falla, mantenimiento, despiece y talleres. Hay un enlace nuevo en el pie del sitio.
`sitemap.xml` ahora sale de `django.contrib.sitemaps` (`config/sitemaps.py`).

**Privacidad:** las páginas salen del catálogo (archivos de fallas e intervalos y despiece); no leen las motos de los
usuarios. Sin códigos de repuesto. De la fuente de cada intervalo solo se publica el nombre del manual (el texto
completo trae notas internas como «copia entregada por el usuario»).

## Comprobado (en local)
- 36 pruebas focalizadas OK (páginas nuevas, despiece público, sitemap/robots, barrido de seguridad sin sesión). No se
  corrió la suite completa: hace falta antes de desplegar (se tocó `config/settings.py` y `templates/base.html`).
- Las páginas cargan sin sesión. Revisión de diseño a 1280 y 375 px: se corrigieron los enlaces sueltos; lo que queda
  (contraste de la campanita, alto de los enlaces del pie) ya estaba.
- Sitemap: 7.173 direcciones (6.112 de piezas, 389 de motos), sin repetidas ni privadas; 2,2 s con el despiece
  precalentado. Precalentar de cero: 5 min y medio.

## Lo que debes hacer
1. **Pedir el despliegue** (llevar los cambios a producción, `collectstatic`, reiniciar).
2. En producción, **correr una vez** (y tras cada despliegue). Sin esto, la primera lectura del sitemap arma todos los
   despieces y tarda varios minutos; Google se cansa de esperar:
   `venv\Scripts\python.exe manage.py precalentar_despiece --max-segundos 900`
3. Abrir https://tallerya.co/sitemap.xml y comprobar que carga en pocos segundos.
4. **Google Search Console** (gratis), https://search.google.com/search-console :
   1. «Agregar propiedad» → tipo **Dominio** → `tallerya.co`.
   2. Google da un registro **TXT**. En Cloudflare (o donde estén los DNS) → DNS → agregar TXT en `@` con ese valor.
   3. Esperar unos minutos y pulsar «Verificar».
   4. Menú «Sitemaps» → enviar `https://tallerya.co/sitemap.xml`.
   5. «Inspección de URLs» → pegar 5 o 10 páginas clave (NMAX, Aerox, NKD…) → «Solicitar indexación».
5. En Cloudflare, redirigir `www.tallerya.co` a `tallerya.co` (regla de redirección 301) para no duplicar páginas.
6. **Dejar el PC y el sitio prendidos.** Hoy producción corre en tu PC: si Google la visita apagada, no indexa y
   puede sacar páginas ya indexadas. Es el mayor riesgo de este trabajo.
7. A las 2-4 semanas, mirar en Search Console «Rendimiento» (qué buscan) y «Páginas» (qué no indexó y por qué).

Opcional: repetir el alta en Bing Webmaster Tools (importa desde Search Console).

## Límites y siguientes pasos
- Indexar toma semanas y no garantiza posiciones. Ayuda que talleres, grupos y redes enlacen las páginas.
- **No hay página «por qué se apaga la NMAX»**: ningún texto de la NMAX habla de eso (sí Boxer CT 100, Discover 125 y
  Duke 200). Agregarla es contenido mecánico nuevo (skills `fallas-modelo` y `mecanico`).
- Las páginas de pieza repiten la misma guía entre motos; Google puede indexar solo una parte. Se dejó fuera la
  tornillería y los empaques. Mejora: texto propio por moto en las piezas que más se buscan.
- Las páginas de mantenimiento solo existen donde hay dato del manual.
