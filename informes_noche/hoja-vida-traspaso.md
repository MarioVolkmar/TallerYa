# Hoja de vida: traspaso al vender y certificado imprimible

Fecha: 19 nov 2026 · Sin commit.

## Qué quedó

### 1. Traspaso al vender
- En la hoja de vida hay una tarjeta nueva, **«¿Vendiste la moto?»**. Dice qué pasa al comprador y qué no, y tiene el botón «Traspasar a quien la compró» (pide confirmar).
- Ese botón genera un **enlace de un solo uso con QR** (`/garaje/traspaso/<token>/`) que **vence a los 7 días**. Si se genera otro, el anterior queda anulado. También se puede cancelar.
- Quien compra abre el enlace con su sesión iniciada (sin sesión lo manda a entrar), ve la moto, la placa enmascarada y los servicios sin costos, y toca **«Aceptar la moto»**.
- Al aceptar, la moto (el mismo registro) pasa a su garaje y el vendedor deja de verla. Se revocan los enlaces públicos y los códigos de taller vigentes, y se avisa a los dos por `notificaciones`.
- Casos que se bloquean con su mensaje:
  - enlace vencido, usado o cancelado (410);
  - el vendedor abre su propio enlace (ve «Este es tu enlace»);
  - cuenta sin perfil de motociclista;
  - garaje lleno (5 motos);
  - **pedido de SOAT en curso**: no deja generar ni aceptar el traspaso.
- La aceptación es atómica, con `select_for_update` y un update condicional: dos envíos a la vez no gastan el enlace dos veces.

### 2. Certificado imprimible y PDF
- Ruta `/hoja-de-vida/<token>/certificado/`, del mismo enlace público (si el dueño lo desactiva, el certificado deja de abrir). Lo enlazan la página pública y la tarjeta «Compartir» del dueño.
- Muestra:
  - la marca TallerYa;
  - la moto: marca, moto, año, **placa enmascarada** y km;
  - una tabla de servicios con fecha, km, servicio, taller y estado (**Verificado / Propio / Pendiente**);
  - un **QR al enlace público** para comprobar que es auténtico, la URL y la fecha y hora de emisión.
- Va con `@media print` y un botón **«Imprimir / Guardar PDF»** (`window.print()`). **Sin dependencias nuevas**: el «Guardar como PDF» del navegador da un PDF vectorial, sin pesar el servidor. En pantalla se ve como una hoja clara. Al imprimir se ocultan la cabecera, el pie, la barra inferior, Chispa y los mensajes.
- `noindex` y `Referrer-Policy: no-referrer`, como la página pública.

## Qué viaja y qué no (decisión de privacidad)
| Viaja (es de la moto) | No viaja (es del dueño) |
|---|---|
| Servicios de la hoja de vida (verificados, propios y pendientes), con taller, fecha, km y notas | **Gastos**: se borran. Son las finanzas personales del vendedor |
| Plan de mantenimiento (mantenimientos hechos) y lecturas de km | **Lo que pagó** en cada servicio (`costo` de los registros y de `ServicioTaller`): queda vacío |
| Servicios del panel de talleres, con su foto | **Fotos o PDF del SOAT y la tecnomecánica** (en `privado/`): se borran del disco. Llevan nombre y cédula del tomador |
| Placa y matrícula | **SOAT y tecnomecánica completos, también las fechas de vencimiento** (cambio del 19 nov, a pedido del usuario: son datos privados del dueño) · apodo, ajustes del plan (posponer o recordar) y recordatorio de pico y placa por WhatsApp |
| Aspecto del 3D (colores, calcas) | **Pedidos de SOAT** del vendedor (cédula, dirección, póliza): quedan para el equipo, pero el comprador no los ve (abajo) |

Por qué:
- La hoja de vida vale como garantía porque es **de la moto**: el comprador necesita fechas, km y quién hizo qué.
- Cuánto pagó el vendedor, sus gastos y los documentos con sus datos son **de la persona**. Pasarlos sería exponer datos personales a un tercero (Ley 1581).
- SOAT y tecnomecánica no viajan, ni siquiera las fechas (pedido del usuario): el comprador carga los suyos en «Datos de la moto». Excepción: si la moto tiene menos de 2 años, la primera tecnomecánica se sigue estimando desde la matrícula, que sí viaja.
- La tarjeta y el aviso de confirmación le dicen al vendedor que sus gastos y documentos se borran.

## Cambios en el código
- `garaje/models.py`: modelo `TraspasoMoto`; campo `Moto.dueno_desde` (desde cuándo la tiene el dueño actual); método `Moto.pedidos_soat_del_dueno()`. Migración `0036_traspaso_moto` (ya aplicada a la `db.sqlite3` local).
- `garaje/traspaso.py` (nuevo): crear, cancelar, buscar y aceptar; limpieza de lo personal y avisos.
- `garaje/vista_hoja_vida.py`: acciones `vender` y `cancelar_traspaso`; vistas `traspaso` y `hoja_vida_certificado`.
- `garaje/urls.py`: 2 rutas nuevas. **No se tocaron `config/urls.py` ni `talleres/seo.py`.**
- Plantillas: `traspaso.html` y `hoja_vida_certificado.html` (nuevas); `hoja_vida.html` y `hoja_vida_publica.html` (tarjeta y enlaces).
- CSS: `secciones/garaje.css` (`.hv-vender*`, `.hv-viaja*`, `.cert*`, `@media print`). No hacen falta clases de Tailwind nuevas.
- **Fuera de garaje** (aviso a quien trabaje en trámites): `tramites/views.py` y `tramites/templatetags/tramites.py` usan `pedidos_soat_del_dueno()`. Además `_pedido_de` excluye los pedidos anteriores al traspaso, así el comprador no puede abrir por URL la póliza del dueño anterior (IDOR).
- Los perfiles y verificaciones de domiciliario del vendedor dejan de apuntar a la moto.
- `revisar-ux/anexo-guia.md`: componente «Documento para imprimir» (y su respaldo).

## Verificación
- `garaje/tests_traspaso.py`: 13 pruebas nuevas.
  - Traspaso: solo el dueño genera el enlace; traspaso completo (qué viaja y qué no, archivo borrado del disco, enlaces y códigos revocados, avisos); el vendedor ya no accede y el comprador sí; un solo uso; vencido y cancelado; generar otro anula el anterior; pide sesión; el vendedor no se la acepta a sí mismo; comprador sin perfil y garaje lleno; SOAT en curso bloquea y la póliza vieja da 404.
  - Certificado: placa enmascarada y nada privado (placa completa, costos, apodo, nombre, correo, celular); enlace revocado da 404; las páginas lo enlazan.
- **Suite rápida en verde: 793 pruebas OK** (`--exclude-tag=lenta`).
- **revisar-ux a 1280 y 375 px**: hoja de vida, certificado y página de traspaso. Sin scroll horizontal y sin hallazgos propios.
  - Corregido durante la revisión: grises del certificado llevados a la paleta (`#354044`, `#111517`, papel `#fbf8f1`) y la marca en lava a 24 px por contraste; fecha «26 de Noviembre … p.m..» pasada a «26 Nov 2026».
  - Lo que queda es ruido previo del sitio (enlaces del pie, contador de la campanita, «¿Te varaste?»).

## Ronda 2 (19 nov, pedido del usuario)
- **Precio fuera de la hoja de vida**: el valor cobrado ya no aparece en la vista del dueño, en la pública ni en el certificado (la pública y el certificado ya no lo mostraban). El campo «Costo» del formulario sigue, con la etiqueta «solo va a tus gastos»: el valor queda guardado en privado y alimenta los gastos.
- **Tecnomecánica privada en la hoja de vida del dueño**: tarjeta con el vencimiento y el estado (vigente, vence pronto o vencida), usando los mismos componentes `doc-*` de la ficha. Tiene «Agendar» (CDA), «Ver archivo» o «Agregar fecha» según el caso. En `tramites` no hay registros de tecnomecánica (solo CDA), así que la fuente es `Moto.tecno_vence` o la estimada desde la matrícula. No sale en la página pública, el certificado ni el traspaso.
- Pruebas: 2 nuevas y ajustes (15 en `tests_traspaso`). **Suite rápida: 808 OK.** Revisión a 375 px de la tarjeta nueva sin hallazgos propios.

## Pendiente o para decidir
- Si la hoja de vida está vacía, la página del comprador repite el texto de vacío del dueño («Registra el próximo servicio…»). Viene de `_hoja_vida_lista.html`, compartido con la página pública. Detalle menor.
- `SolicitudSoat` (cotizaciones viejas, solo admin) sigue colgada de la moto con el celular del vendedor. El comprador no la ve, pero el equipo la verá asociada al nuevo dueño.
- Revisión: el servidor `tallerya` del puerto 8001 era de otra sesión con otra copia del código. Revisé en un servidor propio en el 8003, con una configuración temporal que ya quité de `launch.json`.

## Ronda 3 (19 nov): mecánicos a domicilio en la hoja de vida
- **Modelo**: `RegistroServicio.mecanico` y `ServicioTaller.mecanico` (FK a `domicilio.MecanicoDomicilio`) y `ServicioTaller.solicitud` (FK a `SolicitudVisita`); `ServicioTaller.taller` pasa a opcional. Restricciones: un registro no puede tener taller y mecánico a la vez; un servicio tiene exactamente uno de los dos. Origen nuevo `visita`. Migración `0037_servicio_mecanico_domicilio` (aplicada a la base local).
- **Reglas** (`garaje/servicio_taller.py`): `crear(None, moto, mecanico=..., solicitud=...)` aplica igual que un taller: hoja de vida verificada, plan al día (en el plan queda «A domicilio: <nombre>»), solicitud a «atendida» y aviso al dueño. Confirmar o rechazar avisan a quien lo registró (`prestador`).
- **Flujo** (`garaje/vista_servicio_mecanico.py`, rutas `garaje:servicio_visita` y `garaje:servicio_mecanico`): en la bandeja, botón «Registrar servicio» en las solicitudes confirmadas o atendidas. Con la moto del motero si tiene cuenta; si no, pide el código/QR y deja la visita ligada. Además, «Registrar servicio con el código del dueño» sin solicitud. Solo mecánicos **aprobados**; sin búsqueda por placa. Mismo freno a códigos fallidos que los talleres. Reutiliza las plantillas `talleres/servicio_hecho.html` y `servicio_buscar.html`, con variables opcionales (`volver_url`, `etiqueta`, `sin_placa`, `visita`, `accion_buscar`). Para los talleres no cambia nada.
- **Hoja de vida**: «Mecánico a domicilio: <nombre> · verificado» en la vista del dueño, la pública, el certificado (`donde`), la ficha de la moto y el detalle del servicio. Sin precio.
- Pruebas: `garaje/tests_servicio_mecanico.py` (7): con solicitud y cuenta; solicitudes ajenas o pendientes dan 404; mecánico sin aprobar y motero no registran; código de un solo uso sin solicitud; solicitud sin cuenta pide código y queda ligada; aparece en las tres vistas sin precio; restricciones de la base. **Suite rápida: 819 OK.**
- No corrí `revisar-ux` en esta ronda: llegué al tope de contexto de la sesión. Los cambios visuales son chicos (botón en la bandeja y textos con componentes que ya existen), pero conviene revisarlos a 375 px en una sesión nueva.

## Ronda 4 (19 nov): papeles al día en lo compartido
- La hoja de vida pública muestra chips «SOAT vigente hasta <fecha>» y «Técnico-mecánica vigente hasta / vencido desde <fecha>». El certificado los suma a sus datos. La fuente es solo lo registrado (`soat_vence`, `tecno_vence`, sin la estimación por matrícula). Sin fecha no hay línea. Los archivos y los pedidos de SOAT siguen privados.
- La tarjeta de técnico-mecánica del dueño ahora dice que el documento es privado y que solo la vigencia sale en lo compartido.
- Tras un traspaso las fechas se borran (ronda 2), así que el comprador empieza sin líneas hasta que cargue las suyas.
- Pruebas: 2 nuevas (vigente y vencido; sin fecha no hay línea ni enlaces a documentos). **Suite rápida en verde.** Sin `revisar-ux` (tope de contexto): los chips usan los colores de estado existentes.
