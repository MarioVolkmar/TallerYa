# Pendientes: correo, Google y seguridad (sesión de pendientes-correo)

## Qué cambió
- **Preconnect**: `moto.html` ya tenía `preconnect` a cdn.jsdelivr.net; se añadió `dns-prefetch`.
- **DEBUG** ahora es False por defecto (`config/settings.py`); `SECRET_KEY` de desarrollo solo si DEBUG o `manage.py test`. Creé `.env` local (ignorado por git) con `DJANGO_DEBUG=1` y `SITIO_URL`; documentado en `.env.example`.
- **Recuperar contraseña con freno**: `cuentas.views.RecuperarView` (5/hora por IP, 3/hora por correo, usa `cuentas/limites.py`; al pasarse responde igual sin enviar).
- **`PROXIES_DE_CONFIANZA=1`** puesto en `render.yaml` y documentado; gunicorn con `--timeout 60`.
- **Botón día/noche** (`.portada-noche`) 40 px mínimo en celular (<768 px).
- **Correos**: ya existían verificación al registrarse, recuperar contraseña y "contraseña cambiada" (HTML+texto, marca, `SITIO_URL`). Nuevo: aviso de SOAT/técnico-mecánica por correo (`templates/correos/aviso.*`, `cuentas.correos.enviar_aviso`), enviado solo la primera vez de cada umbral y solo a correos verificados. Citas siguen por WhatsApp/notificación (no se añadió correo).
- **Google**: flujo revisado (PKCE, state, correo verificado); funciona con solo definir `GOOGLE_CLIENT_ID/SECRET`; la URL de retorno usa el esquema correcto tras el proxy de Render.
- Guía para no técnicos: `informes_noche/guia-google-y-correo.md`.

## Lo que debe hacer el usuario
1. Seguir la guía (Google Cloud + Brevo) y poner las variables en `.env` y en Render.
2. En Render poner `SITIO_URL` y `DJANGO_ALLOWED_HOSTS`/dominio. Sin `.env` con `DJANGO_DEBUG=1`, el servidor local no arranca (falta SECRET_KEY): ya existe el archivo.
3. Pendiente menor: correo para citas, si se desea.
