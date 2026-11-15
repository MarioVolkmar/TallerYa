# Lado del taller — informe (15-nov-2026)

Objetivo: que al taller le sirva estar en TallerYa y que su registro alimente solo la hoja de vida y el plan de la moto.

## Qué ya existía
Panel `mi-taller` (citas, reseñas, cupones, cifras), confirmar/reprogramar/cancelar citas (reprogramar y cancelar ya avisaban al motero), códigos de 6 caracteres + QR de la hoja de vida (`/garaje/servicio/<código>/` → registrar servicio verificado), `RegistroServicio` con estados propio/pendiente/verificado.

## Qué se hizo
1. **Citas**
   - Al **confirmar**, ahora también se avisa al motero (aviso en TallerYa; el push sale solo desde `notificaciones`; WhatsApp con la plantilla nueva `WHATSAPP_PLANTILLA_CONFIRMAR`, por defecto `cita_confirmada`: hay que crearla en Meta igual que las otras).
   - El aviso va primero a `cita.usuario` (si pidió la cita con su cuenta) y si no, al motero con ese celular.
   - `Mis citas` tiene pestañas **Hoy · Próximas · Pasadas** (abre en «Hoy» si hay citas hoy) además de las de estado.
2. **Registrar el servicio al terminar una cita** (`/mi-taller/cita/<id>/servicio/`, botón «Registrar servicio» en citas confirmadas o atendidas sin registro):
   - Elige la moto del motero (si tiene varias), marca tareas del **plan de esa moto** (casillas grandes), otros trabajos, km, fecha, valor, nota y foto opcional (abre la cámara en el celular).
   - Crea un `Mantenimiento` por tarea (igual que «ya lo hice»: el plan se pone al día y se borra el ajuste de esa tarea) y su entrada en la hoja de vida **verificada** con el taller; los otros trabajos van en una entrada aparte. El valor queda solo en la primera entrada (no se duplica en Gastos). Si el dueño ya lo había anotado (misma tarea, ±10 días, con ese taller o sin taller) se verifica ese registro en vez de duplicarlo. Si los km son mayores, cuentan como lectura.
   - La cita pasa a atendida. El dueño recibe aviso con enlace al detalle (`/garaje/servicio-taller/<id>/`): ve tareas, km, valor, nota y foto, **«Calificar a <taller>»** (abre la ventana de reseña en la página del taller con `?calificar=1`) y «No reconozco este servicio» (lo quita de la hoja y del plan y avisa al taller).
   - Si la cita no tiene moto de TallerYa: botón para buscar la moto o solo marcar atendida.
3. **Moto sin cita** (`/mi-taller/registrar-servicio/`): por **código/QR** (verificado de una vez, el código se gasta) o por **placa** (solo motos con dueño con cuenta; el taller ve marca/línea, no datos del dueño; máximo 30 búsquedas por hora por taller). Por placa queda **«Esperando al dueño»**: nada entra a la hoja de vida hasta que el dueño toca «Sí, confirmar» desde su aviso («No es mío» lo descarta). El taller recibe aviso de la respuesta.
   - Se cambió el texto de la hoja de vida que decía «nadie puede buscar tu moto por la placa».
4. **Resumen en el panel**: cifras «Citas esta semana» (con cuántas por confirmar) y «Servicios registrados» (este mes y por confirmar), junto a la calificación. Página nueva `/mi-taller/servicios/` con la lista y su estado.

## Archivos
- Nuevos: `garaje/servicio_taller.py` (reglas), `garaje/forms_servicio_taller.py`, `garaje/vista_servicio_taller.py`, `garaje/templates/garaje/servicio_taller.html`, `talleres/vista_servicios.py`, plantillas `talleres/servicio_hecho.html`, `servicio_buscar.html`, `servicios_taller.html`, `garaje/tests_servicio_taller.py` (10 pruebas).
- Modelo nuevo `ServicioTaller` + campo `RegistroServicio.servicio_taller` → migración `garaje/0031_servicio_taller.py` (aplicada en la base local).
- Tocados: `talleres/views.py` (confirmar avisa, filtros de citas, resumen del panel, `?calificar=1`; se quitó el `registrar_servicio` viejo, ahora en `vista_servicios`), `talleres/urls.py`, `garaje/urls.py`, `config/settings.py` (1 línea), `_cita_item.html`, `panel.html`, `garaje/_hoja_vida_lista.html` (enlace «Ver detalle y foto»), `hoja_vida.html` (texto), `hoja_vida.py` (docstring), `taller-funciones.css` (bloque `sv-`), `talleres/tests.py` (prueba de registrar servicio al formulario nuevo).
- `ServicioTallerForm` / `registrar_verificado` de `garaje/forms_hoja_vida.py` / `hoja_vida.py` ya no los usa ninguna vista (siguen con sus pruebas); se pueden borrar más adelante.

## Pruebas
Suite completa: 503 pruebas, 1 falla ajena a este trabajo (`garaje.tests_avisos.ArchivosIntervalosTests`: falta la línea `honda_xr_190l` para su archivo de intervalos, de la sesión que amplía motos). Las 10 nuevas y las de talleres pasan.

## Pendiente / a decidir
- No se tomó captura en el navegador: crear una sesión de taller en la base local fue denegado. Verificado con el cliente de pruebas; falta mirar `/mi-taller/servicios/` y el formulario a 360 px con una cuenta de taller real.
- Plantilla de WhatsApp `cita_confirmada` por crear en Meta (sin ella, en producción el envío falla en silencio y solo queda el aviso en TallerYa).
- Caso borde: si el dueño anotó un registro pendiente **sin tarea del plan** y el taller lo registra con código, quedan dos entradas (la del dueño y la verificada). Antes `registrar_verificado` lo fusionaba; ahora solo se fusiona por tarea.
- Las fotos van a `media/servicios/` (públicas por URL aleatoria, como las del taller). Si se quieren privadas, usar `AlmacenPrivado` como los documentos.
