# Cotizador de repuestos (piloto)

Precio aproximado y dónde venden cada repuesto del despiece, consultando Mercado Libre Colombia por su interfaz
oficial desde el servidor. Apagado por defecto.

## Encender / apagar
- `COTIZADOR_ACTIVO=1` en el entorno lo enciende. Sin la variable (o con `0`), los ganchos no pintan nada y
  `/cotizador/…` responde 404: la página queda igual que sin la app.

## Credenciales de Mercado Libre (obligatorias para precios reales)
Desde 2025 la búsqueda de Mercado Libre responde 403 sin token. Sin credenciales, el piloto muestra **precios de
ejemplo** con un aviso amarillo.

1. Entrar a https://developers.mercadolibre.com.co con una cuenta de Mercado Libre y crear una aplicación
   (DevCenter → «Crear aplicación»). Redirect URI: la del sitio, p. ej. `https://tallerya.onrender.com/`.
   Permisos: solo lectura.
2. Autorizar la app con esa cuenta: abrir
   `https://auth.mercadolibre.com.co/authorization?response_type=code&client_id=APP_ID&redirect_uri=REDIRECT_URI`
   y copiar el `code` que vuelve en la URL.
3. Cambiar el `code` por tokens (una sola vez, desde una terminal):
   ```
   curl -X POST https://api.mercadolibre.com/oauth/token \
     -d grant_type=authorization_code -d client_id=APP_ID -d client_secret=SECRET \
     -d code=CODE -d redirect_uri=REDIRECT_URI
   ```
4. En Render (Environment) poner `ML_APP_ID`, `ML_SECRET` y `ML_REFRESH_TOKEN` (el `refresh_token` de la
   respuesta). El access token dura 6 h y se renueva solo; el refresh token es de un solo uso, por eso el nuevo
   se guarda en la tabla `cotizador_tokenmercadolibre`.
   Para una prueba rápida basta `ML_ACCESS_TOKEN` (vence a las 6 h).

## Refresco nocturno (cron) — documentado, no activado
`python manage.py refrescar_cotizaciones --max 60` vuelve a consultar las 60 cotizaciones más pedidas con más de
20 h. Para activarlo en Render, agregar a `render.yaml` (los cron jobs de Render se cobran aparte; ver el informe):

```yaml
  - type: cron
    name: tallerya-cotizaciones
    runtime: python
    schedule: "0 8 * * *"   # 3:00 a. m. en Colombia (UTC-5)
    buildCommand: pip install -r requirements.txt
    startCommand: python manage.py refrescar_cotizaciones --max 60
    envVars:
      - key: DATABASE_URL
        fromDatabase: {name: tallerya-db, property: connectionString}
      - key: DJANGO_SECRET_KEY
        sync: false
      - key: COTIZADOR_ACTIVO
        value: "1"
      - {key: ML_APP_ID, sync: false}
      - {key: ML_SECRET, sync: false}
      - {key: ML_REFRESH_TOKEN, sync: false}
```

## Piezas
- `fuentes/mercadolibre.py`: consulta y token. `fuentes/ejemplo.py`: precios de ejemplo sin credenciales.
- `filtro.py`: quita basura, otra pieza, otra moto y precios atípicos. `servicio.py`: consulta, caché de 24 h.
- `views.py` + `templates/cotizador/_recuadro.html`: el recuadro. `static/cotizador/js/cotizar.js`: botón
  «Cotizar» en la ficha del despiece y en «Qué necesitas» del plan.
- Frenos: 40 cotizaciones/hora por persona, 80 por IP (`cuentas/limites.py`) y 300 consultas nuevas/hora en total.

## Quitarla del todo
1. `COTIZADOR_ACTIVO=0` (o borrar la variable).
2. `python manage.py migrate cotizador zero` (borra sus 2 tablas).
3. Borrar la carpeta `cotizador/`, su línea en `INSTALLED_APPS` y `COTIZADOR_ACTIVO` en `config/settings.py`,
   su `include` en `config/urls.py`, y los ganchos: `cotizador` en el `{% load %}` y `{% cotizador_script %}` de
   `garaje/templates/garaje/moto.html`, y `cotizador` en el `{% load %}` y `{% cotizador_boton r.codigo %}` de
   `garaje/templates/garaje/_tarea.html`. (Si se unió con un solo commit: `git revert <commit>`.)
