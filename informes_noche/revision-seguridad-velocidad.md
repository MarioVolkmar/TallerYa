# Revisión de seguridad y velocidad — 17-nov-2026

Criterios: OWASP Top 10 (2021), ASVS 4 nivel 2 (autenticación, sesiones, control de acceso, validación, archivos,
configuración) y el checklist de despliegue de Django. Todo en local: test client de Django con la configuración de
producción, navegador del panel contra `localhost:8001`. Ningún escaneo ni prueba contra servicios externos.

Continúa la revisión del 15-nov (`informes_noche/seguridad-velocidad.md`), cuyos arreglos siguen en pie (frenos de login,
recuperar contraseña y reseñas, IP real tras el proxy, documentos privados, N+1 de garaje y foro).

**Skill nueva:** `.claude/skills/revisar-seguridad/` (`SKILL.md`, `revisar.py`, `permitidos.txt`). Correrla antes de cada
despliegue: `venv/Scripts/python.exe .claude/skills/revisar-seguridad/revisar.py --sin-red` (~1 min). Resultado final:
**0 fallas · 9 avisos (pip-audit sin instalar, npm de compilación y bajos propuestos abajo) · 30 OK**.

## Resumen

| Severidad | Encontrados | Arreglados | Propuestos (decisión del usuario) |
|---|---|---|---|
| Crítica | 0 | — | — |
| Alta | 3 | 3 | — |
| Media | 7 | 7 | — |
| Baja | 9 | 3 | 6 |

Pruebas: rápida **572 OK**, completa **615 OK** (en paralelo y con `--parallel 1`). Pruebas nuevas en
`config/tests_seguridad.py` (IDOR de 41 rutas × 3 intrusos × GET/POST, barrido anónimo de todas las URL, consola, y una
prueba por cada arreglo) y `cuentas/tests_velocidad.py`.

## 1. Hallazgos arreglados

| Sev. | Hallazgo | Dónde | Cómo se explota | Arreglo (prueba) |
|---|---|---|---|---|
| **Alta** | **XSS almacenado por la galería del taller** | `talleres/views.py` (editar perfil), `config/urls.py` (`/media/`) | La galería solo miraba el `Content-Type` que manda el navegador. Una cuenta de taller (cualquiera puede registrarse) subía `x.html` declarado como `image/png`; quedaba en `/media/talleres/galeria/x.html` y Django lo servía como `text/html` en el mismo dominio. Un admin que abriera el enlace ejecutaba el script con su sesión (acciones de consola con su token CSRF). | `talleres/subidas.py`: contenido real (firma + `Pillow.verify()`), nombre aleatorio con la extensión del contenido; video por firma MP4/WEBM. `/media/` ahora solo entrega `.jpg .jpeg .png .webp .gif .mp4 .webm` (otra extensión → 404) y con CSP `sandbox`. (`test_galeria_rechaza_html_disfrazado_de_imagen`, `test_media_solo_entrega_imagenes_y_videos`) |
| **Alta** | **SOAT "pagado" sin pagar en producción** | `tramites/pagos.py`, `config/settings.py` | `SOAT_PAGO_SIMULADO` valía `True` por defecto también en producción: cualquiera con un pedido "listo para pagar" abría `/soat/pedido/<id>/pago-de-prueba/` y lo marcaba **pagado**; el equipo podía emitir la póliza sin cobro (solo un check "pago simulado" en el admin lo delataba). | Por defecto solo en local y pruebas (`DEBUG`); en producción hay que activarlo a propósito (`SOAT_PAGO_SIMULADO=1`). Si está apagado, la página avisa "el pago en línea todavía no está disponible". (`test_pago_de_prueba_del_soat_apagado_en_produccion`) |
| **Alta** | **Login de `/admin/` sin límite de intentos** | `config/urls.py`, `cuentas/forms.py` | El freno de 10/30 intentos solo estaba en `/cuenta/entrar/`; `/admin/login/` (cuentas de staff, las más valiosas) aceptaba fuerza bruta ilimitada. | `FrenoIntentosMixin` compartido por el login del sitio y `admin.site.login_form = EntrarAdminForm`. (`test_login_del_admin_con_freno`) |
| Media | **Sin Content-Security-Policy ni Permissions-Policy** | `config/cabeceras.py` (nuevo), `settings.MIDDLEWARE` | Sin CSP, un XSS puede cargar scripts de cualquier dominio, enviar formularios fuera o meter la página en un iframe; sin Permissions-Policy cualquier iframe pide cámara/ubicación. | CSP aplicada: scripts solo propios + jsDelivr, `object-src 'none'`, `base-uri 'self'`, `form-action 'self' accounts.google.com`, `frame-ancestors 'none'`, `frame-src` solo Google Maps, `upgrade-insecure-requests` en producción. Permissions-Policy: cámara y ubicación solo propias. Verificado en el navegador sin bloqueos en portada, ficha de taller, rodada (mapa), canje (jsQR), emergencias, diagnóstico y noticias; control: un script externo inyectado sí se bloquea. (`test_cabeceras_csp_y_permisos`) |
| Media | **Registro sin freno: enumeración de correos y celulares** | `cuentas/views.py: registro` | El formulario responde "Ya existe una cuenta con este correo" y "Este celular ya está asociado a otra cuenta": sin límite, un script averiguaba quién está registrado y probaba códigos de cupón para adueñarse del perfil de un celular. | Máximo 20 envíos por IP y hora (uno normal usa 1-3). El texto no cambia (eso es UX: ver propuestas). (`test_registro_con_freno_por_ip`) |
| Media | **Vista previa del canje sin freno** + **error 500** | `cupones/views.py: canjear_cupon` | `GET /canjear/?codigo=TY-XXXXXX` mostraba nombre y celular enmascarado del dueño de cualquier código válido, sin límite (adivinar códigos). Además, con un código inválido la página daba **error 500** (`add_error` sobre un formulario sin enviar). | La vista previa usa el mismo freno que el canje (8 fallos / 15 min por IP) y el 500 quedó corregido. (`test_vista_previa_del_canje_con_freno`) |
| Media | Códigos de servicio del motero probados al azar por un taller | `talleres/vista_servicios.py: registrar_servicio` | Un taller podía probar códigos de 6 caracteres sin límite; cada acierto abre la moto y la hoja de vida de otra persona. | Máximo 20 códigos fallidos por taller y hora. |
| Media (velocidad) | **Mi cuenta: N+1 por moto** | `cuentas/views.py: mi_cuenta` | ~5 consultas por moto (ajustes, mantenimientos, despiece, lecturas, tareas) + barrio por cada taller del historial: 51 consultas con 5 motos. | Mismo precargado que Mi garaje (`_motos_con_plan`) y `select_related("taller__barrio")`: **51 → 25** y ya no crece con las motos. (`cuentas/tests_velocidad.py`) |
| Media | **Scripts de jsDelivr sin SRI** (jsQR y qrcode-generator, 4 plantillas) | canje y cupones | Si jsDelivr o el paquete se comprometían, ese JS corría en canje y cupones con la sesión del taller. | Instalados con npm (`--save-exact`; el lockfile guarda el `integrity` sha512, que coincide con el publicado en el registro), minificados con terser y servidos desde `cupones/static/cupones/vendor/`; jsDelivr salió de la CSP (`script-src 'self' 'unsafe-inline'`). Verificado en el navegador: generar un QR con qrcode-generator y leerlo con jsQR funciona con la CSP. |
| Media | **Citas ajenas en Mi cuenta por coincidencia de celular** | `cuentas/views.py: historial_servicios` | Las citas anónimas se ligaban por el celular del perfil, que no se verifica: quien registrara el número de otra persona (sin cuenta) veía sus citas (taller, servicio, fecha). | Solo se muestran las citas pedidas con la sesión abierta (`SolicitudCita.usuario`). (`test_citas_anonimas_con_mi_celular_no_salen_en_mi_cuenta`; la prueba vieja de notificaciones se ajustó al nuevo criterio) |
| Baja | `.env.example` sin 6 variables | `.env.example` | `CHISPA_EN_VACIOS`, `CONTACTO_CIUDAD`, `DJANGO_SSL_REDIRECT`, `LEGAL_ACTUALIZADO`, `LEGAL_CIUDAD`, `WHATSAPP_PLANTILLA_CONFIRMAR` (+ `SOAT_PAGO_SIMULADO`). | Documentadas. |
| Baja | Login del admin distinguía mayúsculas en el contador por correo | `cuentas/forms.py` | `Admin@x.co` y `admin@x.co` contaban aparte. | El contador normaliza a minúsculas. |
| Baja | Pruebas de frenos podían contaminarse entre sí | `config/tests_seguridad.py` | Los contadores viven en la caché del proceso de pruebas. | `cache.clear()` antes y después de cada prueba del archivo. |

## 2. Revisado sin problemas (con evidencia)

- **Autorización / IDOR** (A01): `config/tests_seguridad.py` prueba 41 rutas con `<pk>` (garaje, citas, notificaciones,
  SOAT, foro, panel del taller, consola, aprobar talleres) como otro motero, otro taller y anónimo, por GET y POST: nunca
  200 y la base no cambia; el dueño legítimo sí entra (control). El barrido anónimo de todas las URL sin parámetros solo
  deja 23 públicas a propósito (`PUBLICAS`). La consola exige `is_staff` en cada vista y acción, bitácora en transacción,
  y un admin no puede tocar a un superusuario.
- **XSS** (A03): sin `autoescape off`; los 8 `mark_safe` son SVG/QR propios, JSON-LD con `</` escapado o menciones con
  `escape()`+`format_html`; 60 usos de `innerHTML` revisados uno a uno: solo constantes, SVG propios, HTML del servidor
  o números (el texto de usuarios va con `textContent`). Aceptados en `permitidos.txt`.
- **SQL crudo**: ninguno (`.raw`, `.extra`, `cursor`). **Deserialización/`eval`/`shell=True`**: ninguno.
- **Redirecciones abiertas**: todos los `next`/`volver` pasan por `url_has_allowed_host_and_scheme`.
- **CSRF**: middleware en todo; la única exenta es `/tareas/<nombre>/` (Bearer ≥20 caracteres, `compare_digest`, lista
  cerrada). Los `fetch` POST mandan `X-CSRFToken`.
- **Google OAuth**: `state` aleatorio + PKCE, comparación en tiempo constante, exige `email_verified`; `redirect_uri` se arma
  con el host validado por `ALLOWED_HOSTS`.
- **Sesiones**: Django rota la llave al iniciar sesión; cookies `Secure`, `HttpOnly` (sesión), `SameSite=Lax`; duración 2
  semanas; salir solo por POST.
- **Contraseñas**: 4 validadores (incluido parecido a datos propios); hash PBKDF2 en producción (MD5 solo en pruebas).
- **Tokens públicos**: cita (`token_urlsafe(16)`), hoja de vida (`token_urlsafe(24)`, revocable), nombres de archivo `uuid4`.
- **Configuración** (A05): `check --deploy` sin avisos salvo HSTS (decisión de dominio); DEBUG apagado por defecto;
  SECRET_KEY obligatoria fuera de local; HTTP→HTTPS; X-Frame `DENY`, nosniff, Referrer-Policy `same-origin`, COOP.
- **Secretos**: ninguno en archivos rastreados ni en el historial completo de git (3 falsos positivos aceptados:
  una URL de Google, un texto "Clave:" y la clave de la cuenta demo, que solo se crea con DEBUG). `despiece_local/`,
  `manual_despiece/`, `planos_a_generar/`, `privado/`, `media/`, `db.sqlite3` y `.env` ignorados y fuera de git.
- **Estáticos**: WhiteNoise con manifest + `.gz/.br` y CSS minificado en producción; GZip del HTML; `tw.css` purgado (16 KB);
  three.js y el despiece solo se cargan en sus páginas, no desde `base.html`.

## 3. Propuesto, sin aplicar (pide decisión)

| Sev. | Propuesta | Por qué no se aplicó |
|---|---|---|
| Baja | **CSP con nonces** (quitar `'unsafe-inline'` de `script-src`). | ~40 plantillas con `<script>` en línea y algunos `onload=`: hay que moverlos o ponerles nonce; es trabajo de varias plantillas que otras sesiones están tocando. |
| Baja | **HSTS de 1 año + `includeSubDomains`** (`DJANGO_HSTS_SECONDS=31536000` y `SECURE_HSTS_INCLUDE_SUBDOMAINS`). | Solo cuando el dominio propio sea definitivo: con HSTS largo no hay vuelta atrás si algo queda en http. |
| Baja | Mensajes de registro neutros ("Si el correo no está registrado…") para cerrar la enumeración del todo. | Rompe el flujo: el aviso "Ya existe una cuenta… ¿Quieres entrar?" es la salida de quien olvidó que tenía cuenta, y un mensaje neutro exigiría mandar correo en vez de mostrar el error. Queda con el freno de 20 envíos por IP y hora. |
| Baja | **`npm audit`: 10 altas**, todas por `picomatch` (ReDoS con extglobs, GHSA-fc5q-39xc-vjpf) en la cadena de `tailwindcss` 3. | `npm audit fix` (sin `--force`) no encuentra arreglo: **no existe versión parcheada** (afecta ≤4.0.7 y la última publicada es 4.0.7) y `--force` llevaría a Tailwind 4 (cambio mayor). No es explotable aquí: solo corre al compilar y los patrones vienen de `tailwind/tailwind.config.js`, no de usuarios. `npm run css` y `npm run js` dan exactamente el mismo resultado (comparado byte a byte). Revisar cuando salga picomatch ≥4.0.8 o al migrar a Tailwind 4. |
| Media | **`pip-audit`** no se pudo correr: instalarlo en el venv fue rechazado por el control de permisos de esta sesión y no lo reintenté. Versiones actuales: Django 5.2.19, Pillow 13.0.0, whitenoise 6.12, gunicorn 27, psycopg 3.3.9, cryptography 50.0.2, requests 2.34.2. | Instalarlo una vez: `venv/Scripts/pip install pip-audit` (ya está en `requirements-dev.txt`) y correr la skill sin `--sin-red`. |
| Baja | PIN de canje global de 6 dígitos (cualquier PIN de cualquier taller sirve): con N talleres, cada intento acierta con prob. N/10⁶; el freno es 8 por IP cada 15 min. | Con IPs distribuidas sería abusable a gran escala; pasar a PIN por taller + código del cupón cambia el flujo del canje. |
| Baja | `render.yaml` trae `CARGAR_DEMO=1`: en producción real carga talleres, cupones y foro de ejemplo (la cuenta demo no, porque exige DEBUG). | Útil para la demo de Ruta N; ponerlo en 0 al abrir al público (aviso añadido en `render.yaml`). |

Pendiente de verificar a mano: abrir con sesión el garaje, una ficha de moto, la vista 3D, el despiece y la consola y mirar
la consola del navegador ("Content Security Policy"). Esas páginas piden sesión; iniciarla por mi cuenta (leer las cuentas
de prueba o crear una sesión en la base) fue rechazado por el control de permisos, así que no lo hice. Por análisis no deberían
romperse (importmap en línea permitido, módulos y `.glb` propios, texturas `blob:`/`data:` permitidas, sin workers ni `eval`).

## 4. Velocidad (local, `db.sqlite3`, mejor de 3, test client)

| Página | Consultas antes | Después | ms antes | ms después |
|---|---|---|---|---|
| Portada (anónimo) | 13 | 13 | 36 | 27 |
| Talleres | 11 | 11 | 31 | 28 |
| Foro | 5 | 5 | 38 | 31 |
| Rodadas | 3 | 3 | 13 | 10 |
| Cupones | 1 | 1 | 12 | 13 |
| Emergencias | 4 | 4 | 15 | 11 |
| Ficha de taller | 10 | 10 | 29 | 25 |
| Pregunta (31 respuestas) | — | 8 | — | 60 |
| Portada (con sesión) | 19 | 19 | 39 | 29 |
| Mi garaje (5 motos) | 10 | 10 | 21 | 17 |
| Ficha de moto | 30 | 30 | 78 | 67 |
| **Mi cuenta (5 motos)** | **51** | **25** | **74** | **52** |
| Mi taller | 26 | 26 | 36 | 27 |
| Citas del taller | 7 | 7 | 18 | 17 |

Los ms varían ±30 % entre corridas (otras sesiones usan la máquina); las consultas son exactas. La medición "antes" de
la pregunta del foro medía una redirección 301 (la URL sin slug); ya se mide la página real. Todas las páginas quedan
por debajo de 100 ms y 35 consultas.

Pesos que conviene vigilar (no son urgentes): `three.module.min.js` 654 KB (solo en las páginas 3D, comprimido ~160 KB),
`tallerya.css` 456 KB sin minificar en el repo (en producción sale minificado y en `.br`), `moto3d/construir.js` 165 KB
(minificado por `npm run js` en el build). Partir `tallerya.css` por sección sería la mejora siguiente para la primera visita.

## 5. Archivos tocados

Nuevos: `.claude/skills/revisar-seguridad/{SKILL.md,revisar.py,permitidos.txt}`, `config/cabeceras.py`,
`config/tests_seguridad.py`, `talleres/subidas.py`, `cuentas/tests_velocidad.py`, `cupones/static/cupones/vendor/`
(jsQR 1.4.0 y qrcode-generator 1.4.4 minificados + licencia de jsQR), este informe.
Cambiados: `config/settings.py` (middleware de cabeceras, `SOAT_PAGO_SIMULADO`), `config/urls.py` (`servir_media`, login
del admin), `cuentas/forms.py` (`FrenoIntentosMixin`, `EntrarAdminForm`), `cuentas/views.py` (freno de registro, Mi cuenta
sin N+1), `cupones/views.py` (freno de la vista previa, 500), `talleres/views.py` (galería y video), `talleres/vista_servicios.py`
(freno de códigos), `tramites/views.py` (aviso sin pago simulado), 4 plantillas de cupones (scripts locales),
`notificaciones/tests.py` (citas solo con sesión), `package.json`/`package-lock.json` (jsqr y qrcode-generator como
devDependencies exactas), `render.yaml` (aviso de `CARGAR_DEMO`), `.env.example`, `.gitignore`, `requirements-dev.txt`.
