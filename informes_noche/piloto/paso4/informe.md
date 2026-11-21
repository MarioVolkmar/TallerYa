# Paso 4 (fase 1): enviar el diagnóstico a un taller o mecánico a domicilio

**Hecho, sin commit.** Pruebas: 17 nuevas (`garaje.tests_ficha_diagnostico`) y suite rápida 889 OK. Migración `0039_ficha_diagnostico` aplicada con `migrate`.

## Qué hace
- Resultado del diagnóstico → botón «Enviar a un taller o a un mecánico a domicilio» → `/diagnostico/enviar/?<respuestas>`: km opcional (estimado de `kilometraje.py` si hay moto, editable), 1-3 fotos opcionales, y lista de hasta 6 talleres (con WhatsApp, del servicio del resultado) y 6 mecánicos a domicilio publicados.
- Al elegir uno (POST): crea `FichaDiagnostico` y redirige a `wa.me` con mensaje armado + enlace a la ficha. Talleres se miden como en el paso 1 (`EventoDiario` WHATSAPP + evento «contacto»); mecánicos: evento «contacto» y la propia ficha (`destino`, `mecanico`, `vistas`).
- Ficha pública `/diagnostico/ficha/<token>/`: token `secrets.token_urlsafe(24)`, sin cuenta, vence a 30 días (vencida: 410), `noindex` en meta y `X-Robots-Tag`, `no-store`. Muestra moto (marca, modelo, año), km, síntoma, causa, sistema, urgencia, qué revisar, piezas y fotos. Nunca placa, nombre, celular ni correo (hay prueba).
- Fotos: validadas por contenido real (`tipo_real`), ≤5 MB, máx. 3, regrabadas como JPEG ≤1200 px sin EXIF, en `media/diagnosticos/<uuid>.jpg` (media no va al repo). Se borran con la foto (señal `post_delete`).
- Seguridad: la consulta solo conserva claves del diagnóstico; moto ajena → 404; destinos fuera de la lista ofrecida → 400.

## Archivos
Nuevos: `garaje/vista_ficha_diagnostico.py`, `garaje/templates/garaje/diagnostico_enviar.html`, `ficha_diagnostico.html`, `garaje/tests_ficha_diagnostico.py`, `garaje/migrations/0039_ficha_diagnostico.py`, `informes_noche/piloto/paso4/*`.
Editados: `garaje/models.py` (final: `FichaDiagnostico`, `FotoFichaDiagnostico`; import `timedelta`), `garaje/urls.py` (2 rutas y 1 import, fuera del bloque etiquetar-3d), `garaje/vista_diagnostico.py` (`enviar_url`), `garaje/templates/garaje/diagnostico.html` (botón), `talleres/static/talleres/css/secciones/garaje.css` (bloque «Enviar diagnóstico y ficha pública» al final).

## revisar-ux (CDP, Chrome sin ventana, 375 y 1280)
Sin scroll horizontal ni bloqueantes propios; lo que reporta el script es del chrome del sitio (cabecera, pie, nav inferior, «Emergencia», banner «Instala»). Se quitó el borde punteado de `.diag-revisa` en la ficha. Capturas: `enviar_375/1280.png`, `ficha_375/1280.png`, `resultado_375.png` (muestra el botón). Se usó una copia de la base en el scratchpad; `db.sqlite3` intacta.

## Decisiones abiertas
1. **Mecánicos sin filtro por servicio/zona** (solo urgencias y verificados primero). ¿Filtrar por zona cuando se tenga?
2. **«Cercano»**: los talleres se ordenan por destacado/verificado, no por distancia (no hay geolocalización del motero).
3. **Retención**: fichas vencidas y sus fotos siguen en base y disco. Falta un comando de limpieza (cron) y una vista en la consola; propongo hacerlo con el paso del cron del plan.
4. Las vistas de la ficha cuentan también al propio motero y a la vista previa de WhatsApp: «abierta por el taller» es aproximada.
5. Fase 2 (chat): `diseno-chat.md`, no construido.
