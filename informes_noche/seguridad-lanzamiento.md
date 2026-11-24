# Seguridad y legal para anunciar tallerya.co (23-nov-2026)

Corrida: `revisar.py --sin-red` + revisión de `C:\dev\TallerYa-produccion` (solo lectura). Suite rápida: **1032 OK**.
Sin commit, sin push, producción intacta. Pendiente: `pip-audit` y `npm audit` (requieren red; no corrieron).

## Resultado
Sin hallazgos críticos ni altos reales. Autorización (IDOR, barrido anónimo, consola solo staff, frenos): 24 pruebas OK.
Las 95 «FALLAS» de secretos son falsos positivos (la palabra `clave` en JSON de fallas, `CACHE_CLAVE`, `registrar(clave=...)`,
y el propio regex del escáner en el historial). Se verificó con búsqueda de patrones reales (GOCSPX, AKIA, sk_live, claves
privadas): nada en el repo ni el historial. `.env`, `db.sqlite3`, `media/`, `privado/` no están en git.
Avisos revisados y aceptados: `proveedores.clic` csrf_exempt (solo suma un contador, con freno por IP y anti-bot);
IDOR de `proveedores/vistas_consola.py` (vistas de consola solo staff); `mark_safe` de metricas (valores escapados);
`|safe` de `_mis_precios_editor` (JSON de `json.dumps` con números).

## Arreglado en el código
1. Política de privacidad ampliada: cédula de mecánicos (huella + 4 dígitos), solicitudes de servicio, notificaciones push,
   foro/reseñas públicos, transferencia a proveedores fuera de Colombia (`templates/legal/privacidad.html`).
2. Pie de página: enlace «Reportar un problema» (mailto) cuando `CONTACTO_CORREO` está definido (`templates/base.html`).
3. Pruebas nuevas en `talleres/tests.py` (`PaginasLegalesTests`).

## Legal (Ley 1581/2012)
Ya existían y están enlazados en el pie y en ambos registros (`_terminos.html`): términos, privacidad, cupones y cookies.
Cubren autorización, finalidad, derechos, plazos (10/15 días hábiles), SIC y contacto. Siguen siendo borrador:
**revisar con abogado** (marca en `base_legal.html`). Faltan datos reales: razón social/NIT, correo de habeas data
(ver `.env`). Considerar registro de bases de datos en el RNBD de la SIC si aplica por tamaño.

## Cambios para el `.env` de producción (no aplicados)
| Prioridad | Cambio | Por qué |
|---|---|---|
| Alta | Rotar la contraseña de aplicación de Gmail (`EMAIL_HOST_PASSWORD`) | Se imprimió por error en la salida de esta sesión (queda en su transcripción). Generar una nueva y reemplazarla |
| Alta | Definir `CONTACTO_CORREO` (y `CONTACTO_WHATSAPP`) | Hoy el pie no muestra contacto ni «Reportar un problema» |
| Alta | Definir `LEGAL_CORREO`, `LEGAL_RAZON_SOCIAL`, `LEGAL_NIT` | Habeas data exige canal y responsable identificados; hoy la política dice «desde tu cuenta» |
| Media | `DJANGO_HSTS_SECONDS=31536000` cuando el dominio esté estable (antes 3600) | HSTS efectivo; luego `INCLUDE_SUBDOMAINS` solo si todo subdominio es https |
| Baja | Documentar en `.env.example` las variables `*_ACTIVO` nuevas | El escáner avisa que faltan |
| Baja | Actualizar `LEGAL_ACTUALIZADO` al publicar la versión revisada | Hoy dice 12-nov |
Ya correctos: `DJANGO_DEBUG=0`, SECRET_KEY propia (67 car.), ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS con tallerya.co y www,
`PROXIES_DE_CONFIANZA=1` (un salto: Cloudflare), cookies Secure (settings con DEBUG off), SSL redirect, nosniff,
`CARGAR_DEMO` no está en `.env` (no recarga demo). `SOAT_PAGO_SIMULADO` no está: queda apagado. Pendiente CSP con nonces (baja).

## Datos de demostración en producción
Base actual: 23 usuarios, 2 talleres, 5 reseñas, 2 cupones, 4 preguntas del foro con 8 respuestas, 5 proveedores,
7 mecánicos a domicilio.
- 18 usuarios `@demo.tallerya…` (ids 2-19), sin contraseña usable: no inician sesión, pero sus nombres salen como autores.
- Foro: las 4 preguntas y 8 respuestas parecen de esas cuentas. Reseñas (5) y mecánicos a domicilio (7) también
  probablemente demo: verificar autor antes de tocar.
- Proveedores (5: grúas y CDA) vienen de siembra: confirmar si son reales (teléfonos).
- Talleres 1 («Biela y Pistón») y 3 («Rin Diecisiete») no son los de `demo_talleres` (Doble Leva, Torque Sur): parecen del piloto real.
- Usuarios 20-23 son personas reales (gmail): no tocar.

**Cómo apagarlos sin borrar:** (1) listar con shell los objetos cuyo autor/usuario termina en `@demo.tallerya…` y revisar;
(2) desactivar en vez de borrar: `Taller.activo=False`, `MecanicoDomicilio`/`Proveedor` no publicados, y para foro y reseñas
ocultar por autor demo (campo de moderación si existe) o `is_active=False` en esos usuarios; (3) hacer copia de `db.sqlite3`
antes; (4) cuando haya contenido real, borrar definitivamente. Puedo escribir el comando `ocultar_demo` (con `--ejecutar`;
por defecto solo lista) si lo pides.

## Reportar problemas
- Foro: existe «Reportar» por mensaje (motivo, anónimo). No había canal general.
- Mínimo agregado: enlace en el pie con asunto prellenado (queda activo al definir `CONTACTO_CORREO`).
- Siguiente paso opcional: formulario `/ayuda/reportar/` que guarde el reporte en la consola (con frenos por IP).
