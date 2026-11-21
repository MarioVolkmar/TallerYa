# Piloto · Paso 3: facilitarle la vida al taller

Hecho A–E. Pruebas: `talleres/tests_paso3.py` (18, OK) y suite rápida 867 OK. `revisar-ux` en 1280 y 375 px: sin bloqueantes propios (inputs de 43 px son el `.campo` existente; arreglé un enlace suelto y un botón de 39 px).

## Qué hay
- **A · Alta asistida**: `/consola/alta-taller/` (botón «+ Alta asistida» en Talleres). Crea el taller sin publicar (`origen_alta=asistido`) con token; la consola muestra el enlace `/ficha/<token>/`. El taller revisa, corrige y aprueba marcando la autorización (Ley 1581); se guarda fecha/hora/IP. La consola no deja publicar hasta que el taller apruebe. Aviso de fotos propias en el formulario. Tras aprobar, la ficha queda de solo lectura. Páginas con `noindex`.
- **B · Autoregistro**: `/unete/` (sin cuenta, pocos campos, autorización obligatoria, 5 envíos/hora por IP). Queda «pendiente de revisión»; recibe su enlace de ficha. Se publica desde la consola.
- **C · Precios**: «precio de referencia, confirmado el dd/mm» en el perfil (solo si `mostrar_precios`). Recordatorio a los 75 días: aviso en el panel del taller, botón «Siguen vigentes» en Mis precios y marca en la fila de Talleres de la consola. Usa `PrecioServicio.actualizado`, sin campo nuevo.
- **D · Servicio en 30 s**: `/mi-taller/servicio-rapido/` (placa, km, qué se hizo, precio) con botón en el panel. Usa `st.crear` por placa: queda «esperando al dueño» y entra a la hoja de vida cuando lo confirma.
- **E · Reseñas**: siguen abiertas; sello «✓ Verificada» si el autor tiene un servicio verificado de ese taller sin reseñar (uno por servicio). Visible en el perfil y en el panel.

## Archivos
Nuevos: `talleres/forms_alta.py`, `talleres/vista_alta.py`, `talleres/tests_paso3.py`, migración `talleres/0022`, plantillas `autoregistro/alta_enviada/revisar_ficha/_ficha_campos/servicio_rapido`, `consola/vistas/alta_taller.py`, `consola/templates/consola/alta_taller.html`.
Editados: `talleres/{models,views,urls,precios,forms,vista_servicios}.py`, plantillas `detalle/panel/precios/_resena_item`, `talleres/css/secciones/talleres.css`, `consola/{urls.py,vistas/talleres.py,templates/consola/talleres.html}`, `config/tests_seguridad.py` (`unete/` pública).
No toqué 3D, `garaje/urls.py` ni `garaje.css`. Capturas en esta carpeta (≤900 px).

## Decisiones abiertas
1. `/registra-tu-taller/` sigue redirigiendo al registro con cuenta (hay una prueba que lo exige). ¿Apuntar el CTA de portada/pie a `/unete/`?
2. Servicio rápido por placa exige confirmación del dueño (consistente con el paso 2); la reseña verificada espera esa confirmación.
3. El enlace de ficha no caduca (solo se cierra al aprobar). ¿Vencimiento a 30 días?
4. Publicar desde el admin de Django (Talleres por aprobar) no pasa por el bloqueo de aprobación; solo lo exige la consola.
5. Aviso de precios vencidos solo en panel y consola; falta notificación push/correo si se quiere.

## Ronda 2 (decisiones del coordinador)
1. Portada, pie y FAQ → `/unete/`; `/registra-tu-taller/` redirige a `/unete/` (prueba ajustada en `talleres/tests.py`).
3. Enlace de ficha vence a los 30 días (410 con aviso); acción de consola «Renovar enlace» (genera uno nuevo, el anterior deja de servir). Campo `token_creado`.
4. Sin aprobación del taller tampoco se publica desde el admin de Django (`TallerAdminForm`, incluye la edición en lista) ni desde `cuentas/administracion` (`Taller.falta_aprobacion`).
5. `manage.py avisar_precios_vencidos` (cron diario): un correo por taller con precios sin confirmar +75 días; idempotente con `precios_aviso_enviado`. Migración `talleres/0023` (aplicada).
Pickle en paralelo: no reproducible; ese error sale cuando una prueba falla en paralelo (el traceback no se serializa). Las fallas de mis pruebas en la 1.ª ronda lo causaron; suite rápida en paralelo: 872 OK.
Archivos nuevos: `talleres/management/commands/avisar_precios_vencidos.py`, migración 0023. Editados: `talleres/{models,admin,views,vista_alta,tests,tests_paso3}.py`, `cuentas/views.py`, `consola/vistas/talleres.py`, plantilla de Talleres, `revisar_ficha.html`, `inicio.html`, `base.html`, `ayuda/faq.json`.
