# Cuenta de mecánico a domicilio y talleres que van a domicilio (18-nov-2026)

Todo en local, **sin commit**. Migración nueva: `domicilio/0003_cuenta_verificacion_y_talleres` (ya aplicada en tu `db.sqlite3`).

## A. La cuenta del mecánico a domicilio

### Cómo estaba
- `/cuenta/registro/` iba directo al formulario de motero, con pestañas «Soy motero / Tengo un taller». La pantalla de elección de rol (`registro_elegir.html`) solo la ven las cuentas de Google sin rol. El mecánico aparecía solo como una línea de texto al pie.
- `/mecanicos/registro/` era un formulario largo de una sola página (cuenta + 11 campos), sin datos de verificación. En «Mi perfil» había una línea de estado y nada sobre lo que faltaba.

### Opciones
| Opción | A favor | En contra |
|---|---|---|
| (a) Tipo de cuenta propio en la elección de rol | Se descubre al registrarse, igual que motero y taller | Sola no resuelve nada: sigue faltando un buen formulario |
| (b) Alta especial por pasos (perfil + verificación en el mismo registro) | Una sola vez, sale con todo lo que necesita la moderación; en el celular cada paso cabe en una pantalla | Un formulario más largo si se muestra entero |
| (c) «Soy mecánico a domicilio» desde cualquier cuenta | Sirve al motero que también trabaja | No se descubre; el perfil queda a medias si no hay pasos guiados |

### Recomendada: (a) + (b), con (c) como camino secundario
La puerta de entrada es visible (a), el alta es guiada (b) y quien ya tiene cuenta usa el mismo formulario sin el paso de cuenta (c). No hace falta otro tipo de usuario: el rol se sigue deduciendo de tener un `MecanicoDomicilio` (`cuentas/roles.py`).

### Lo hecho
- **Entrada:** tercera tarjeta «Soy mecánico a domicilio» en `registro_elegir.html` y tercera pestaña «Mecánico a domicilio» en el registro (`_registro_tipo.html`). `?tipo=mecanico` en `/cuenta/registro/` y `/cuenta/completar/` (Google) lleva al alta.
- **Alta por pasos** (`/mecanicos/registro/`): 1 Tu cuenta (si no hay sesión), 2 Tu trabajo (nombre, WhatsApp, zonas, servicios, años, urgencias, tarifa), 3 Verificación (cédula, foto, descripción, referencias, fotos de trabajos). Se ve un paso a la vez, con barra de pasos (`static/domicilio/js/pasos.js`). «Siguiente» revisa los obligatorios del paso, incluida «al menos una zona o servicio». Si el servidor devuelve errores, se abre el primer paso que los tiene. Sin JS se ven los pasos seguidos y funciona igual.
- **Verificación sin datos sensibles en claro:**
  - **Cédula:** obligatoria. Se guarda solo una huella HMAC-SHA256 (con `SECRET_KEY`) y los 4 últimos dígitos. El admin avisa si la misma cédula está en otro perfil, y el equipo coteja los 4 dígitos cuando el mecánico la muestra por video o en persona.
  - **Referencias:** texto que solo ve el equipo.
  - **Fotos de trabajos:** hasta 4 (modelo `FotoTrabajo`), públicas en la ficha. Se valida el contenido real, se vuelven a codificar como JPEG de máx. 1200 px sin EXIF y se guardan con nombre aleatorio.
  - No se suben fotos de documentos.
- **Lo que ve el mecánico** (`/mecanicos/mi-perfil/`):
  - Una caja de estado: ⏳ En revisión (con lo obligatorio que falta), ✔ Publicado / Verificado, o ⛔ Suspendido.
  - Un **«Mensaje del equipo»**: campo nuevo `nota_al_mecanico` que se edita en el admin.
  - Una lista «Tu perfil al N %» con ✔ y · : datos básicos, cédula, correo confirmado, foto, descripción, fotos de trabajos y referencias.
  - La galería de trabajos, con botón para borrar (solo POST, y solo las fotos propias).
- **Moderación:**
  - Admin de Django: secciones «Verificación» (cédula …1234 y aviso de repetida, referencias, lista del perfil) y la galería de trabajos como inline.
  - `/consola/`: cada fila muestra cédula …1234, el número de fotos y si tiene referencias.
  - Los estados y avisos no cambian (`estados.py`).

## B. Talleres que también van a domicilio

### Decisión de modelo
**Modelo ligero aparte `domicilio.TallerDomicilio`, uno a uno con el taller.** Descarté dos opciones:
- **Perfil genérico de domicilio** (de un mecánico o de un taller): duplicaría lo que el taller ya tiene (nombre, foto, WhatsApp, reseñas, verificación) y su moderación.
- **Campos en `Taller`:** acoplaría `talleres` a `domicilio` en las migraciones (hoy `domicilio` depende de `talleres` y no al revés).

Así, `TallerDomicilio` solo guarda `activo`, `zonas`, `servicios`, `tarifa_visita` y `urgencias`, y reutiliza las mismas `Zona` y `TipoServicio` de los mecánicos.
- **Publicación:** sale si está activo **y** el taller está aprobado (`Taller.activo`). Es la misma moderación de siempre; el admin además puede apagarlo (`TallerDomicilioAdmin`).

### Lo hecho
- **Activación:** `/mecanicos/mi-taller/`. La URL no lleva id: se toma el taller de la propia cuenta. Si está activo, pide al menos una zona y un servicio.
  - Se llega desde el panel del taller (botón «¿Vas a domicilio?» / «🛵 A domicilio: activo») y desde «Editar perfil» (una línea).
  - Muestra el estado: activo, activo pero con el taller en revisión, o apagado.
- **Distintivo:**
  - Chapa «Va a domicilio» en la tarjeta del directorio (una consulta para todas las tarjetas, en `_preparar_tarjetas`).
  - En la ficha del taller: insignia «🛵 Va a domicilio» y la línea «También va a domicilio: zonas · visita desde $X · atiende urgencias».
- **Listado mixto en `/mecanicos/`:**
  - Talleres e independientes salen juntos y en el mismo orden: verificados primero, luego nota y número de reseñas.
  - Los mismos filtros (zona, servicio, búsqueda, urgencias, verificados) más uno nuevo, «Quién va»: todos, mecánicos independientes o talleres.
  - La tarjeta del taller lleva la chapa «Taller», «Taller en {barrio} · va a…», y su WhatsApp pasa por `talleres:ir_whatsapp`, así cuenta en las estadísticas del taller.
  - En las cifras de arriba, «Verificados» cambió por «Talleres».
- **Demo:** «MotoServicio El Paisa» y «Clínica de Motos Bello» con domicilio (`demo.cargar_talleres()`, dentro de `cargar_demo` y de `cargar_demo_domicilio`). El mecánico pendiente de demo trae un mensaje del equipo.

## Seguridad
- **Sin IDOR:** mi-perfil, mi-taller y borrar foto buscan por `request.user` (probado: 404 con una foto ajena; otra cuenta de taller no toca el taller ajeno).
- **CSRF** en todos los formularios (probado 403 en mi-taller sin token).
- **CSP:** sin dominios nuevos. El JS de pasos es un archivo estático; sin `|safe` ni `innerHTML`.
- **Subidas:** firma real, 5 MB y re-codificación. Estado, verificado y huella de la cédula no se pueden mandar desde el formulario.

## Pruebas
- 17 pruebas nuevas en `domicilio/tests.py` (`AltaYVerificacionTests`, `TallerDomicilioTests`, incluida una de consultas constantes en el listado mixto). `domicilio cuentas talleres`: **219 OK**.
- Suite completa: ver el resultado al final de este informe.
- **Navegador** (celular 375 px, servidor de :8001):
  - Pasos del alta: bloquea sin nombre y sin zona, avanza y envía; Mi perfil muestra «En revisión» y la lista al 43 %.
  - Chapa en el directorio, insignia y línea en la ficha, listado mixto filtrado por Bello. Sin scroll horizontal.
  - El perfil de prueba que creé en la cuenta demo del garaje lo borré.
  - La activación del taller la probé con la cuenta de un taller demo (cliente de Django con `force_login` contra tu base local, sin contraseñas): formulario → listado → ficha → panel. Después dejé la base como estaba.

## Archivos tocados
- `domicilio/`: `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `consola.py`, `demo.py`, `tests.py`, `migrations/0003_cuenta_verificacion_y_talleres.py`, `static/domicilio/js/pasos.js` (nuevo), `static/domicilio/css/domicilio.css`, plantillas `registro.html`, `mi_perfil.html`, `mi_taller.html` (nueva), `_tarjeta_taller.html` (nueva), `_campos.html`, `listado.html`, `ficha.html`, `consola_mecanicos.html`
- `cuentas/`: `views.py` (2 redirecciones `?tipo=mecanico`), `templates/cuentas/registro_elegir.html`, `templates/cuentas/_registro_tipo.html`
- `talleres/`: `views.py` (`va_domicilio` en `_preparar_tarjetas`), plantillas `_tarjeta_taller.html`, `detalle.html`, `panel.html`, `editar_perfil.html`; `static/talleres/css/tallerya.css` (7 líneas al final: chapa e insignia, y la pestaña triple del registro)

## Para decidir
- **¿Verificado exige cédula cotejada + fotos de trabajos o referencias?** Hoy es una casilla manual. Sugerencia: no marcarla sin esas dos cosas.
- **¿Editar un perfil aprobado debe volver a revisión?** Hoy no. Con fotos públicas, quizá convenga solo si cambian nombre o fotos.
- **Pestaña del registro:** pasó de 2 a 3 (en celular el texto va debajo del ícono). Ese archivo lo comparte la sesión de portada/entrar: avisar.
- **Huella de la cédula:** depende de `SECRET_KEY`. Si se rota la clave, las huellas viejas ya no detectan repetidos (los 4 dígitos siguen sirviendo).

## Resultado de la suite completa
`manage.py test --parallel 1 -v 1` → **744 pruebas, 743 OK y 1 falla ajena**: `garaje.tests.DespieceTests.test_datos_del_visor_solo_partes_marcadas_y_con_estado` (espera «desconocido» y da «vencido»). Es de la sesión de estado-por-km, que está cambiando `garaje/plan.py` en este momento; no toca nada de domicilio, cuentas ni talleres. Con paralelo, el runner se corta en esa falla (no hay `tblib`), por eso la corrí sin paralelo.


---

# Ronda 2: ficha del mecánico como el detalle del taller (18-nov-2026)

La ficha `/mecanicos/<slug>/` ahora tiene la misma estructura, clases y orden que `talleres/detalle.html` (Clínica de Motos Bello). **No hay CSS nuevo para el diseño**: se reutilizan `perfil-*`, `papel`, `insignia`, `visor-fotos`, `dialogo-*` y `fav` de `tallerya.css`. En `domicilio.css` solo agregué la lista de verificaciones (6 líneas).

| Parte del taller | En el mecánico |
|---|---|
| Encabezado: avatar, nombre grande, nota y reseñas, barrio, horario | Igual. «📍 Va a {3 zonas} y N más» (lleva a la cobertura), horario, línea «Visita desde $X (orientativa) · N años de experiencia», insignias Mecánico a domicilio / Verificado / Atiende urgencias |
| Descripción corta | `perfil-lema` con la descripción |
| Botones Pedir cita, WhatsApp, Llamar, Guardar | **📅 Solicitar visita**, WhatsApp, Llamar, **Guardar** (favoritos) y Editar mi perfil si es el dueño |
| Precios / servicios como chips | «Servicios a domicilio» como chips; cada chip abre la visita con ese servicio elegido. Debajo, el aviso «TallerYa solo los promociona» |
| Fotos del taller (franja + visor) | «Trabajos de {nombre}»: las fotos de trabajos en la misma franja y el mismo visor |
| En qué es bueno y cómo trabaja | Experiencia (años), especialidades, marcas que mejor conoce, cómo trabaja (con garantía) y herramientas y equipo que lleva |
| — | **Nuevo: «Lo que revisó TallerYa»**: perfil aprobado, identidad verificada, cédula registrada (no se publica), dio referencias, N fotos de trabajos. Sin mostrar datos personales |
| Reseñas con calificar | Igual: puntaje, reparto y lista. «★ Escribir reseña» abre una ventana (estrellas como las del taller); sigue siendo solo con cuenta y una por cuenta |
| Ubicación con mapa | **Zona de cobertura**: comunas de Medellín y municipios como chips, horario y urgencias. Sin mapa: el mecánico no tiene local y las zonas no tienen coordenadas |

## Decisiones
- **«Solicitar visita»**: no hay un flujo de citas para mecánicos, así que no inventé uno. La ventana pide servicio, zona, moto, cuándo y qué le pasa.
  - Al enviar, abre WhatsApp con el mensaje armado (`/mecanicos/<slug>/visita/`, GET, redirige a wa.me).
  - TallerYa no guarda nada. Solo acepta servicios y zonas que ofrece ese mecánico, recorta los textos y usa solo perfiles publicados.
  - «Ahora mismo (estoy varado)» solo sale si el mecánico atiende urgencias.
  - Si más adelante quieren solicitudes con seguimiento (como `SolicitudCita`), este es el punto para cambiarlo.
- **Favoritos**: modelo nuevo `MecanicoFavorito` (como `TallerFavorito`), una vista `favorito` que copia el comportamiento del taller (JSON para el corazón, `next` validado, solo POST, solo publicados) y el mismo `favoritos.js`. El modelo del taller no se tocó.
  - **Pendiente:** no hay todavía una lista de «mis favoritos». El taller tampoco tiene una página así (solo el corazón).
- **Datos nuevos del mecánico** (migración `0004_ficha_completa`):
  - `especialidades` y `compromisos`, con las mismas listas cerradas del taller (`talleres/perfil.py`), así se comparan igual.
  - `garantia_meses`.
  - `herramientas` (texto separado por comas, se muestra como chips).
  - Horario y marcas ya existían.
  - Se editan en **Mi perfil** (`EdicionMecanicoForm`), no en el alta, para que el registro siga corto. La lista «Tu perfil al N %» suma «En qué eres bueno y cómo trabajas».
- **Demo**: los 6 mecánicos demo traen especialidades, cómo trabaja, garantía y herramientas. También se rellenan en perfiles demo ya creados si esos campos están vacíos, así tu base local ya se ve completa. Sin fotos de trabajos de demo: no hay fotos reales y unas inventadas se verían falsas.
- **JS**: `static/domicilio/js/ficha.js` (ventanas y visor). Es la misma lógica que el script del detalle del taller, en archivo aparte para no tocar esa plantilla.

## Pruebas
- 7 pruebas nuevas en `FichaCompletaTests`: secciones y datos; especialidades inventadas no salen; la cédula nunca sale; sin visita ni favorito en perfiles no publicados; la visita arma el WhatsApp e ignora servicios o zonas ajenos; favoritos (con cuenta, POST, `next` externo ignorado, 404 si no está publicado); reseña desde la ventana; Mi perfil guarda lo nuevo; la demo rellena la ficha.
- `domicilio`: 46 OK. **Suite completa (`--parallel 1`): 810 pruebas OK** (la falla de garaje de la ronda anterior ya no está).
- **Navegador** (servidor de :8001):
  - Computador: encabezado, botones y servicios; el chip «Sistema eléctrico» abre la visita con ese servicio elegido.
  - 375 px: sin scroll horizontal; botones en dos filas; secciones numeradas 01–04.
  - Capturas enviadas.
  - El hueco entre los botones y la primera tarjeta en el celular es el mismo del detalle del taller (258 px allá y 272 px aquí): lo deja la portada del encabezado.

## Archivos tocados (ronda 2)
- `domicilio/models.py` (4 campos, `herramientas_lista`, `MecanicoFavorito`, un punto más en `pasos()`), `forms.py` (`EdicionMecanicoForm`), `views.py` (contexto de la ficha, `visita`, `favorito`, Mi perfil usa la edición), `urls.py` (2 rutas), `demo.py` (`FICHA`), `tests.py`, `migrations/0004_ficha_completa.py`
- `domicilio/templates/domicilio/ficha.html` (rehecha), `_favorito.html` (nueva), `_campos.html` (herramientas a lo ancho)
- `domicilio/static/domicilio/js/ficha.js` (nuevo), `static/domicilio/css/domicilio.css` (verificaciones)
- **Coordinación:** otra sesión agregó `alternar_taller` en `domicilio/views.py` y `urls.py`, y `talleres/tests_filtro_domicilio.py`, mientras yo trabajaba. Sus cambios siguen intactos: edité con reemplazos puntuales. No toqué `templates/base.html` ni la app `domiciliarios`.


---

# Ronda 3: ajustes de la ficha tras la revisión del fundador (18-nov-2026)

1. **Aviso legal discreto.** La caja amarilla de «Servicios» desapareció.
   - Bajo los botones de contacto queda una línea gris pequeña: «TallerYa conecta; el acuerdo y el pago son con el mecánico. Más info». Es un `<details>`: al tocarla se ve el texto completo.
   - El texto completo también está dentro de «Solicitar visita», antes del botón «Abrir WhatsApp».
   - El texto vive en un solo lugar: `_aviso_texto.html`.
   - El listado `/mecanicos/` conserva la caja grande; si también se quiere discreta allí, es una línea.
2. **Chips de servicio:** quité «Toca uno para pedir la visita». Ahora llevan una flecha pequeña «›» que se mueve al pasar el mouse, cursor de botón y un `title` «Solicitar visita: frenos».
3. **Sello «Verificado por TallerYa»** junto al nombre, en lugar de la sección «02 Lo que revisó TallerYa» (las demás secciones se renumeraron: 01 En qué es bueno, 02 Reseñas, 03 Zona de cobertura).
   - Al tocarlo flota un desplegable con lo verificado, en lenguaje simple: «Identidad confirmada» (si hay cédula), «Experiencia revisada» (si hay años o fotos de trabajos) y «Referencias comprobadas» (si dio referencias).
   - No lista lo que falta. Sin «verificado» no hay sello.
   - La frase va dentro del desplegable: «Revisamos cada perfil antes de publicarlo. Sus datos privados no se muestran».
   - **Ojo moderación:** el sello depende de la casilla «verificado» del admin y la consola. Solo debe marcarse después de cotejar la cédula, revisar la experiencia y llamar a las referencias. Si más adelante quieren marcar cada cosa por separado, harían falta 3 casillas (con migración).
4. **Fotos:** el mecánico ya podía subir su foto y hasta 4 fotos de trabajos desde Mi perfil (ronda 1): solo JPG, PNG o WEBP de menos de 5 MB, validadas por contenido, recodificadas sin EXIF y con nombre aleatorio. Salen en la tarjeta del listado (avatar) y en la ficha (avatar, más la franja de trabajos con su visor). No hay una moderación aparte para las fotos (los talleres tampoco la tienen): el equipo puede suspender el perfil.
   - **Demo:** ilustraciones propias dibujadas con Pillow en `domicilio/ilustraciones.py`, sin fotos de personas ni imágenes de internet:
     - avatar de 480 px con degradado, iniciales y una llave;
     - 3 ilustraciones de trabajos por mecánico, según sus servicios: aceite, frenos, batería, llanta, eléctrico, kit de arrastre, diagnóstico o mantenimiento general, con el nombre del servicio y la marca «Ilustración».
   - Solo se crean si el perfil demo no tiene. La fuente sale de Windows o de DejaVu en Linux; si no hay ninguna, el texto va sin tildes.
   - Los demo verificados reciben una cédula ficticia (solo huella y 4 dígitos) y referencias de ejemplo, para que el sello muestre las tres líneas.
5. **Mayúscula inicial:**
   - Herramientas: se guardan normalizadas («escáner básico,  multímetro , escáner básico» → «Escáner básico, Multímetro») y `herramientas_lista` también corrige los datos viejos.
   - Servicios y marcas usan `capfirst` en la ficha.

**Sin migraciones en esta ronda.**
- `domicilio`: 51 pruebas OK (5 nuevas en `FichaAjustesTests`: aviso discreto, sin sello si no está verificado, el sello lista solo lo verificado y nunca las referencias, mayúsculas al guardar y al mostrar, ilustraciones demo idempotentes y visibles en listado y ficha). Las pruebas que cargan la demo escriben en una carpeta temporal.
- Suite completa: ver abajo.
- **Navegador:** computador (sello abierto, flotando encima de la descripción y los botones) y 375 px (sello abierto, sin salirse de la pantalla; aviso bajo los botones). Capturas enviadas.

**Archivos (ronda 3):**
- `domicilio/templates/domicilio/ficha.html`, `_aviso_texto.html` (nuevo)
- `domicilio/views.py` (`_verificaciones`), `forms.py` (`clean_herramientas`), `models.py` (`herramientas_lista` con mayúscula)
- `domicilio/demo.py` (`imagenes()` y cédula y referencias demo), `ilustraciones.py` (nuevo)
- `domicilio/static/domicilio/css/domicilio.css`, `tests.py`

**Suite completa (ronda 3, `--parallel 1`): 815 pruebas OK.** La corrí antes de los últimos retoques: cédula y referencias demo, y CSS del desplegable. Después volví a pasar `DemoTests` y `FichaAjustesTests`: OK.


---

# Ronda 4: los mismos ítems que el detalle del taller (19-nov-2026)

## Inventario: detalle del taller frente a la ficha del mecánico
| Sección del taller | En la ficha del mecánico |
|---|---|
| Encabezado (avatar, nombre, nota, barrio, horario o «abierto ahora», insignias) | ✔ Igual. Barrio → «Va a {zonas}». El horario es texto libre (el mecánico no tiene la agenda por franjas del taller). Sello «Verificado por TallerYa» |
| Descripción y botones Pedir cita, WhatsApp, Llamar, Guardar, Editar | ✔ Solicitar visita, WhatsApp, Llamar, Guardar y Editar mi perfil, más el aviso legal discreto |
| **Precios desde** (servicio × cilindraje, «orientativos, no son una cotización», «También hace:») | ✔ **Nuevo:** la misma tabla y los mismos estilos. Arriba va una fila «🛵 Visita a domicilio desde $X · se suma al servicio; sin repuestos». Tocar un servicio abre la visita con ese servicio elegido |
| **Fotos del taller** (franja + «Ver las N fotos» + visor) | ✔ «Fotos de sus trabajos»: misma franja, mismo botón y mismo visor (en el demo, ilustraciones propias) |
| Quiénes te atienden | ✗ No aplica: quien atiende es el propio mecánico (sus años y especialidades ya están en el encabezado y en la sección siguiente) |
| En qué es bueno y cómo trabaja (especialidades, marcas, compromisos, garantía) | ✔ Igual, más experiencia y herramientas |
| Cupones disponibles | ✗ Por ahora no. Los cupones (`cupones.Cupon`) pertenecen a un taller y viven en otra app; darle cupones al mecánico es cambiar ese modelo. Queda anotado como posible siguiente paso |
| **Reseñas** (puntaje, reparto, escribir reseña, **respuesta del taller**) | ✔ Igual. **Nuevo: «Respuesta de {mecánico}»**: el mecánico responde desde Mi perfil |
| Ubicación (dirección, horario, mapa) | ↔ Reemplazada por **Zona de cobertura** (comunas, municipios, horario, urgencias). No tiene local ni mapa |
| Preguntas frecuentes | — El detalle del taller no las tiene |

## Lo hecho
- **Modelo `PrecioMecanico`**: mismos campos y nombres que `talleres.PrecioServicio` (servicio, cilindraje, desde, hasta y las mismas restricciones). Así la ficha usa **la misma función `_tabla_precios` del taller**, sin duplicarla.
- **«Mis precios» del mecánico** (`/mecanicos/mi-perfil/precios/`): la misma pantalla que la del taller (formset, `taller-funciones.css`, misma validación sin repetidos). Solo deja elegir servicios que el mecánico ofrece. Se enlaza desde Mi perfil, y la lista «Tu perfil al N %» suma «Precios de referencia».
- **Respuesta a reseñas**: campos `respuesta` y `respondida_en`, y `responder_resena` (solo POST, solo reseñas del propio perfil: 404 si no; con el texto vacío se borra la respuesta). Mi perfil tiene una sección «Mis reseñas» con un campo para responder.
- **Admin**: los precios aparecen dentro del perfil del mecánico, y la respuesta se ve en las reseñas.
- **Demo**: 18 precios repartidos en 5 mecánicos y una respuesta de Wilson a su reseña. Solo se crean si faltan.
- Migración `0005_precios_y_respuestas`.

## Pruebas
- `domicilio`: **56 OK** (5 nuevas en `PreciosYRespuestasTests`: tabla con columnas usadas y visita, «Servicios a domicilio» sin precios, Mis precios con login, solo sus servicios y «hasta» validado, responder solo las propias, enlaces en Mi perfil).
- Suite completa: ver abajo.
- **Navegador:**
  - Computador: tabla «Precios desde» con la fila de la visita, «También hace:», franja de fotos y respuesta en las reseñas.
  - 375 px: la página no se desborda (ancho 375) y la tabla se desplaza hacia el lado dentro de su caja, igual que la del taller.
  - **La captura de 375 px salió recortada por la derecha** porque el panel del navegador estaba oculto durante la verificación (las medidas sí son de 375 px).

## Archivos (ronda 4)
- `domicilio/models.py` (`PrecioMecanico`, respuesta en `ResenaMecanico`, un punto más en `pasos()`), `forms.py` (`PrecioMecanicoForm`, `precios_formset`), `views.py` (tabla de precios en la ficha, `mis_precios`, `responder_resena`), `urls.py`, `admin.py`, `demo.py`, `tests.py`, `migrations/0005_precios_y_respuestas.py`
- `domicilio/templates/domicilio/ficha.html`, `mi_perfil.html`, `mis_precios.html` (nueva); `static/domicilio/css/domicilio.css` (fila de la visita)

**Suite completa (ronda 4, `--parallel 1`): 821 pruebas, OK.**
