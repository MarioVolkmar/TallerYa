# Ciclo del motero: de buscar un negocio a la reseña (taller y mecánico a domicilio)

Estado: hecho, **sin commit**. Pruebas: `talleres.tests_ciclo` (9 nuevas) OK; suite rápida **1116 OK**; revisar-ux a
1280 y 375 px sin hallazgos propios.

## El flujo (cómo quedó)
| Paso | Motero | Negocio |
|---|---|---|
| 1. Busca | Ficha del taller / mecánico | — |
| 2. Pide | Cita (form con sus datos) · **Visita: ahora queda en la página de su visita** con «¡Solicitud enviada!», pasos y botón «Avisarle también por WhatsApp» | Aviso «X pidió una cita/visita» |
| 3. Cotiza/confirma | Aviso → página para aceptar; en «Mis citas» el chip dice **«Falta tu respuesta»** y el detalle muestra el precio y «Responder» | «Mis citas» / «Solicitudes»: Cotizar, Confirmar |
| 4. Lleva la moto | Pasos: «En el taller · Recibida / En reparación»; franja **«Tu moto … está en X»** en Mis citas y en la página de la moto | «Mi día»: Llegó: recibir moto → Empezar reparación |
| 5. Lista y entrega | Aviso «Tu … está lista» → **detalle de la cita en Mis citas** (antes, la página pública) con la nota del taller | Marcar lista (avisa) → Entregada → registrar servicio |
| 6. Hoja de vida | Aviso «registró el servicio» → servicio verificado; pasos «En tu hoja de vida ✓» y botón «Ver mi hoja de vida» | Registrar servicio (ahora elige la moto correcta) |
| 7. Reseña | Botón «★ Calificar a X» en los pasos y en el servicio → ficha con la reseña **abierta** (también la del mecánico) | — |

Pieza común: `talleres/ciclo.py` (solo lee: cita/visita + `TrabajoEnCurso` + `ServicioTaller` + reseñas) y
`templates/parciales/ciclo.html` / `en_curso.html` (CSS `.ciclo*`, `.en-curso` en `tallerya.css`, anotado en
`anexo-guia.md`). «Mi día» se reutilizó tal cual; no se duplicó nada.

## Cortes encontrados y arreglo
1. **Visitas a domicilio no salían en «Mis citas»** → ahora van en la misma lista (`cuentas/citas.py`, `_visita_fila.html`).
2. **Pantallas sin salida**: detalle de cita y páginas públicas de cita/visita no decían en qué iba el trabajo ni qué
   seguía → pasos + siguiente botón; «Cita atendida» (antes «Tu solicitud está atendida»); «Ver en Mis citas».
3. **Avisos que llevaban a la ficha del taller** (cita confirmada/cancelada) → al detalle de la cita.
4. **Aviso «lista» a la página pública** → al detalle en Mis citas (`herramientas.url_cliente`).
5. **Reseña que no se pide**: cita o visita marcada «Atendida» sin servicio registrado no invitaba a calificar →
   aviso «¿Cómo te fue en X?» con `?calificar=1` (una vez; sin WhatsApp).
6. **`?calificar=1` no abría la reseña del mecánico** → abre (`domicilio/views.ficha`).
7. **Cliente que vuelve nunca era invitado** (ya tenía una reseña vieja del taller) → cuenta la reseña hecha después
   del pedido (el taller admite una por visita; el mecánico, una editable). También en la página del servicio.
8. **Estados que no se actualizan**: registrar el servicio desde la cita sin pasar por «Entregada» dejaba la moto en el
   tablero de «Mi día» → se cierra sola (`servicio_taller.crear`).
9. **Chips en lenguaje del negocio** («Esperando al motero», «Cotizada») en Mis citas → «Falta tu respuesta».
10. **Visita**: el formulario abría en pestaña nueva directo a WhatsApp (en el panel ni se guardaba) y no traía celular
    ni moto → se queda en TallerYa, prellenado.
11. **Servicio desde la cita elegía otra moto** del motero cuando la cita traía el nombre completo o el apodo → la
    busca por `nombre_completo` (taller y mecánico).
12. Detalles: «p. m..» doble punto (avisos y páginas), «?» en la fecha de visitas sin fecha → «pedida», «—» en la nota.

## Verificación
- Navegador (cuentas `usuario@prueba.com` y `taller@prueba.com`): taller completo de punta a punta (pedir → cotizar →
  aceptar → recibir → reparación → lista → entregar → servicio → reseña). Mecánico: pedir visita y página de la visita;
  cotizar, atendida, servicio y reseña cubiertos por pruebas (`CicloMecanicoTests`).
- Pruebas ajustadas (comportamiento nuevo): `tests_herramientas` (URL del aviso «lista»), `domicilio.tests` y
  `tests_descuentos` (la visita ya no redirige a wa.me).

## Para tener en cuenta
- Servidor de prueba nuevo en `.claude/launch.json`: **`tallerya-ciclo`** (puerto 8033, hosts `ciclo.localhost`,
  `taller.localhost`, `mecanico.localhost`): cada host tiene sus cookies, sirve para probar dos cuentas a la vez sin
  tocar la sesión del panel en 127.0.0.1. Sesión de prueba sin clave: `.claude/skills/revisar-ux/entrar.py <correo>`.
- En el navegador del panel, 127.0.0.1:8001 tiene sesión con la cuenta real del usuario: no usarla para pruebas.
  Se creó y borró ahí una cita de prueba por error (cita 73).
- Datos de prueba que quedaron en la base local: cita 74 (atendida, con servicio y reseña de `usuario@prueba.com` a
  Biela y Pistón) y una visita pendiente a «Mecánico de prueba».
- Ideas no hechas: aviso al motero al «Recibir moto» (hoy solo se ve en los pasos); el aviso «aceptó la cotización»
  al negocio podría llevar a «Mi día»; el enlace de WhatsApp de `cita_publica`/`visita_publica` sigue suelto (previo).
