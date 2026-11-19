# Guía: entrar con Google y enviar correos (para no técnicos)

TallerYa ya trae todo el código. Solo faltan **dos cuentas gratis** y copiar unos datos. Nunca compartas las claves por chat ni las subas al repositorio.

## 1. Entrar con Google (Google Cloud)

1. Entra a <https://console.cloud.google.com> con tu cuenta de Google.
2. Arriba, en el selector de proyectos → **Proyecto nuevo** → nombre `TallerYa` → **Crear**.
3. Menú ☰ → **APIs y servicios** → **Pantalla de consentimiento de OAuth** (a veces se llama "Google Auth Platform").
   - Tipo de usuario: **Externo**. Nombre de la app: `TallerYa`. Correo de asistencia: el tuyo.
   - Dominio de la app: pon la dirección de tu sitio cuando exista (ej. `https://tallerya.co`) y los enlaces a *Términos* y *Privacidad* del sitio (`/terminos/`, `/privacidad/` si existen).
   - Permisos (scopes): solo `openid`, `email` y `profile` (son los básicos; no pide revisión de Google).
   - Mientras pruebas, queda en **Pruebas** y solo entran los correos que agregues en "Usuarios de prueba".
4. Menú → **Credenciales** → **Crear credenciales** → **ID de cliente de OAuth** → tipo **Aplicación web**, nombre `TallerYa web`.
   - **URIs de redireccionamiento autorizados** (deben ser exactos, con la barra final):
     - `http://localhost:8001/cuenta/google/volver/` (para probar en tu computador)
     - `http://127.0.0.1:8001/cuenta/google/volver/` (el sitio local se abre con 127.0.0.1)
     - `https://TU-DOMINIO/cuenta/google/volver/` (producción; si usas Render sin dominio propio: `https://tallerya.onrender.com/cuenta/google/volver/` con tu nombre real)
   - **Crear**. Copia el **ID de cliente** y el **Secreto del cliente**.
5. Cuando el sitio esté desplegado y listo: en la pantalla de consentimiento pulsa **Publicar aplicación** (pasa de "Pruebas" a "En producción") para que entre cualquier persona. Con solo los permisos básicos no exige verificación larga.

**Dónde poner los datos**
- Local: archivo `.env` en la carpeta del proyecto:
  ```
  GOOGLE_CLIENT_ID=el-id-que-copiaste
  GOOGLE_CLIENT_SECRET=el-secreto-que-copiaste
  ```
- Render: panel del servicio → **Environment** → agrega las mismas dos variables.
Reinicia el servidor. El botón "Continuar con Google" funciona solo cuando ambas existen.

## 2. Enviar correos (Brevo, gratis hasta 300 al día)

1. Crea cuenta en <https://www.brevo.com> y confirma tu correo.
2. **Remitente**: menú (tu nombre) → **Senders, Domains & Dedicated IPs** → **Senders** → agrega `no-responder@tu-dominio.com` (o el correo que uses) y confirma el mensaje que te llega.
3. **Dominio (muy importante para que no caiga en spam)**: en **Domains** → **Add a domain** → escribe tu dominio. Brevo te muestra unos registros **DNS** (TXT/CNAME): uno de verificación (Brevo code), **DKIM** y **DMARC**. Entra al lugar donde compraste el dominio (GoDaddy, Namecheap, Cloudflare…), sección DNS, y crea cada registro tal como Brevo lo muestra. Para **SPF**: si no tienes un registro TXT que empiece por `v=spf1`, crea uno con `v=spf1 include:spf.brevo.com ~all`; si ya existe, agrega `include:spf.brevo.com` dentro del mismo. Vuelve a Brevo y pulsa **Authenticate/Verify**. Puede tardar de minutos a unas horas.
4. **Clave SMTP**: menú → **SMTP & API** → pestaña **SMTP** → **Generate a new SMTP key**. Copia el servidor, el puerto, tu *login* y la clave.
5. Variables (en `.env` local y en Render → Environment):
   ```
   EMAIL_HOST=smtp-relay.brevo.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=el-login-SMTP-de-Brevo
   EMAIL_HOST_PASSWORD=la-clave-SMTP-generada
   EMAIL_USE_TLS=1
   DEFAULT_FROM_EMAIL=TallerYa <no-responder@tu-dominio.com>
   SITIO_URL=https://tu-dominio.com
   ```
   `SITIO_URL` es la dirección pública del sitio (sin barra final): los botones de los correos la usan. En local usa `http://localhost:8001`.
   Sin `EMAIL_HOST` los correos solo salen escritos en la consola del servidor (útil para probar).

## 3. Probar
- Regístrate con un correo tuyo → debe llegar "Confirma tu correo".
- "¿Olvidaste tu contraseña?" → debe llegar el enlace (máximo 3 por hora por correo).
- Si no llega: mira la carpeta Spam y los registros DNS del paso 2.3.
