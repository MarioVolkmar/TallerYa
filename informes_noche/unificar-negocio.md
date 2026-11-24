# Unificar taller ↔ mecánico a domicilio como un solo «negocio de servicio»

Modelos y tablas intactos (sin migraciones). El adaptador es `talleres/negocio.py` (variantes `Taller` y `Mecanico`:
`tarjetas(lista, negocio, request)`, `datos_tarjeta(s)`, `acciones(s)`, `estado_texto(s)`) y los filtros de
`talleres/templatetags/negocio.py` (`estado_ui`, `estado_chip`, `url_responder`, `url_cupon`). Las plantillas no llevan `if rol`.

## Compartido (un solo parcial + su lógica)
| Pieza | Antes | Ahora |
|---|---|---|
| Tarjeta de solicitud | `_cita_item.html` (fila completa) y `domicilio/_solicitud_item.html` + lista propia en `solicitudes.html` (solo «Ver»/«Cotizar») | `talleres/_solicitud.html`: fecha, cliente y moto, servicio, «hace X», estado, cotización, Confirmar · Cotizar · WhatsApp (ícono) · ⋯ (Reprogramar, Cancelar) en panel, citas y solicitudes |
| Estados | etiquetas distintas por modelo | Pendiente, Cotizada, Esperando al motero, Confirmada, Atendida, Cancelada (mapeo de presentación; mismo color de chip) |
| Panel · Por hacer | dos listas de `if` en plantilla | `_por_hacer.html` con `tareas` (datos); comunes en `negocio.tareas_comunes`; fila de precios única (`pt-fila`) |
| Panel · Solicitudes / Reseñas / Cupones | cajas copiadas; mecánico sin caja de cupones | `_panel_solicitudes.html`, `_panel_resenas.html`, `_panel_cupones.html` (el mecánico ahora tiene «Mis cupones» en su panel) |
| Reseñas | 2 ítems, 2 páginas, 2 vistas con la misma lógica | `_resena_item.html`, `resenas_negocio.html`, `negocio.contexto_resenas` (el mecánico gana páginas de 10) y `negocio.nota`/`resenas_panel` (4, primero sin responder) |
| Cupones | ítem copiado en panel del taller y en «Mis cupones» del mecánico | `_lista_cupones.html` + `_cupon_detalle.html` (QR y detalle también para el mecánico), `negocio.cupones_con_cifras` |
| Diálogo cancelar | solo citas | `_dialogo_cancelar.html with sustantivo="visita"`; el motivo le llega al motero en el aviso |
| Ya compartidos antes | franja de cifras, fila de cupones, `_servicios_cabecera`, `_resenas_resumen`, editor de precios | sin cambio |

## Distinto, como opción de la variante (y por qué)
- **Dónde**: local con mapa (taller) / zona y «cuándo» en la tarjeta (mecánico).
- **Flujo**: cita con fecha preferida que se reprograma (diálogo reprogramar) / visita que se cotiza y confirma; en el
  mecánico «Reprogramar» del ⋯ abre la cotización con otra fecha (su único camino de cambiar fecha). Sin «Reabrir» en
  el mecánico (su vista no lo admite). «Marcar atendida» queda en el mecánico: canjea el cupón anotado.
- **Cupón en la tarjeta**: solo la visita guarda el código anotado (campo `codigo_cupon` solo existe ahí).
- **Ventana de detalle** al tocar la tarjeta: solo el taller (`_cita_detalle.html`).
- **Verificación, horario, tarifa de visita**: viven en sus perfiles y en las tareas propias del «Por hacer»
  (cédula en `domicilio/identidad.py`; ubicación exacta del local en el taller).
- **Cabecera y accesos del panel**: el contenido es real de cada uno (agenda/estadísticas vs urgencias/zonas); se dejaron como están.
- Las vistas de acciones siguen separadas por modelo (URLs intactas); `solicitud_estado/cotizar/descuento` del mecánico
  ahora respetan `volver` (para actuar desde el panel).

## Código eliminado
Plantillas borradas: `_cita_item.html`, `domicilio/_solicitud_item.html`, `domicilio/_resena_item.html`,
`resenas_taller.html`, `domicilio/resenas.html`. CSS muerto: `.vd-*` (lista/ítem/chips), `.pt-precios*`, `.dm-solicitud`.
Líneas netas (talleres + domicilio, incluye los cambios sin commit previos de las tarjetas): **plantillas −117,
CSS −10, Python +314** (`negocio.py` ~280 nuevas y el «Por hacer» del mecánico pasó de plantilla a datos). Total +187.

## Verificación
- Suite completa: 1129 pruebas OK. Ningún texto de prueba tuvo que cambiar.
- revisar-ux 1280/375 con `taller@` y `mecanicodomi@prueba.com` vía Chrome sin ventana (el navegador integrado bloquea
  localhost; sesión con `entrar.py`). Sin bloqueantes propios; los dos paneles dan los mismos hallazgos. Previos sin
  tocar: enlace suelto «Ver» de `_fila_cupones` y «N zonas»; «Crear cupón» con borde punteado; contraste del sello
  «✓ Verificada» (2,6:1) en «Mis reseñas»; menú superior < 44 px; pie tapado por «Instala TallerYa».
- Sin commit.
