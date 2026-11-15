# App instalable (PWA) y avisos push

## Qué se hizo
- **Manifest** `/manifest.webmanifest` (vista en `notificaciones/views.py`): nombre, colores de la marca (#111517), íconos 192/512 y maskable generados con Pillow en `talleres/static/talleres/img/pwa/` (rueda crema sobre fondo oscuro, como el favicon). Enlazado en `templates/base.html` junto con apple-touch-icon.
- **Service worker** `/sw.js` (desde la raíz; plantilla `notificaciones/templates/notificaciones/sw.js`): caché de `/static/`, páginas siempre de la red y, sin conexión, la página `/sin-conexion/`. También maneja `push` y `notificationclick`.
- **Instalar**: barra discreta "Instala TallerYa" (`static/talleres/js/pwa.js`, estilos al final de `tallerya.css`). Android/Chrome usa `beforeinstallprompt`; iPhone muestra "Compartir → Agregar a inicio". Se puede cerrar (se recuerda).
- **Push**: modelo `SuscripcionPush` (migración `notificaciones/0002_suscripcion_push`), `notificaciones/push.py` (pywebpush + VAPID). Un `post_save` de `Notificacion` envía el push cada vez que se crea un aviso nuevo, así salen con los mismos avisos de siempre (SOAT, técnico-mecánica, pico y placa, citas, mantenimiento, foro…), sin duplicados (la clave única ya evita repetirlos). Suscripciones muertas (404/410) se borran solas. El botón "Activar avisos en este celular" está al pie del panel de la campana. Preferencia = activar/desactivar por dispositivo (no existía otro modelo de preferencias).
- **Sin claves VAPID**: el botón no aparece y no se envía nada; el resto funciona igual (hay prueba).
- Comando `manage.py generar_vapid` imprime un par de claves nuevo.
- **requirements.txt**: se agregó `pywebpush>=2.0` (ya instalado en el venv local).
- Pruebas: `notificaciones/tests_push.py` (7). Suite completa corrida al final.

## Cómo probarlo
Push y service worker exigen **HTTPS** (o localhost en el mismo equipo). En el celular, con el servidor local, no sirve `http://IP:8001`; usa un túnel HTTPS (p. ej. `cloudflared tunnel --url http://localhost:8001`, o ngrok) y añade ese host a `DJANGO_CSRF_TRUSTED_ORIGINS`/`ALLOWED_HOSTS`. Más simple: probar en Chrome de escritorio en `http://localhost:8001`.
1. Entra con una cuenta, abre la campana → "Activar avisos en este celular" → permitir.
2. Provoca un aviso: `venv/Scripts/python.exe manage.py shell -c "from notificaciones.servicios import notificar; from django.contrib.auth import get_user_model as g; notificar(g().objects.first(),'prueba:1','Prueba','Hola','/garaje/')"` (usa un usuario que activó push).
3. Android/Chrome: menú ⋮ → "Instalar app" o la barra. iPhone (iOS 16.4+): Safari → Compartir → Agregar a inicio; los push solo funcionan ya instalada.

## Qué debe configurar el usuario
- Local: ya hay claves de prueba en `.env` (ignorado por git).
- Producción (Render): generar claves con `python manage.py generar_vapid` y poner `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` y `VAPID_SUBJECT` (`mailto:tu-correo`) en el panel (en `render.yaml` están con `sync: false`). Con las mismas claves siempre; si se cambian, las suscripciones existentes dejan de servir.
- El cron diario de avisos (`/tareas/avisos/`) ya crea las `Notificacion`, por lo que también dispara push.
- Si el envío síncrono molesta con muchos usuarios, mover a cola/hilo (hoy: timeout 5 s por dispositivo, solo si hay suscripciones).
