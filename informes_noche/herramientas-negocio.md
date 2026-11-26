# Herramientas del negocio («Mi día») — taller y mecánico a domicilio

Estado: hecho, **sin commit**. Una sola implementación para los dos (vía `talleres/negocio.py` → `variante_de`).

## Qué hace
Página **/mi-negocio/** («Mi día», en el menú del taller y del mecánico junto a «Panel») con tres secciones plegables:

1. **Agenda**: tira de 7 días + lista por día de las citas (taller) o visitas (mecánico) abiertas, con hora, estado,
   WhatsApp y «Llegó: recibir moto» / «Empezar trabajo» en las confirmadas. Las visitas sin fecha salen en
   «Por acordar fecha». Botón **«+ Anotar cita/visita»**: el negocio anota la que le llegó por teléfono → se guarda
   en `SolicitudCita` / `SolicitudVisita` **ya confirmada**; si el celular es de un motero con cuenta se enlaza a él
   y le llega «X te agendó una cita» (`cita-agendada:` / `visita-agendada:`). Cotizar/reprogramar/cancelar sigue en
   «Mis citas» / «Solicitudes» (no se duplicó).
2. **Motos en el taller** (mecánico: «Trabajos en curso»): tablero Recibida → En reparación → Lista para entregar →
   Entregada (últimos 7 días). «Marcar lista» pide nota opcional y **avisa al dueño** (`trabajo-listo:<pk>`: push y,
   sin push, correo de respaldo; prefijo agregado a `notificaciones/correo.py`). Sin cuenta: botón de WhatsApp con el
   mensaje «tu moto ya está lista». «Entregada» redirige a **registrar el servicio** con el flujo existente
   (`talleres:servicio_cita`, `garaje:servicio_visita`, o el registro suelto). «+ Recibir moto» para clientes sin cita.
3. **Recordatorios a tus clientes**: motos cuyo **último servicio verificado** (`ServicioTaller`) lo hizo este negocio
   y a las que el plan (`garaje.plan.calcular_plan`, sin lo pospuesto) dice «Toca ya / Se acerca». Botón por cliente y
   «Avisar a los N»; el comando diario **`manage.py recordar_clientes`** lo hace solo (cron sugerido 8 a. m.). Clave
   `negocio-recordatorio:<taller|mecanico><pk>:<moto>:<firma>`: no repite hasta que cambie la lista de tareas. El aviso
   lleva a la ficha del taller con `?agendar=1` (abre el formulario de cita) o a la ficha del mecánico.

En el **panel** («Por hacer») de los dos aparecen «N motos listas para entregar» y «N motos en el taller/en curso».

## Interruptor (igual que el foro)
`consola/ajustes.py`: módulo **`herramientas_activo`** (prendido por defecto), prefijo `/mi-negocio/` → 404 apagado
(middleware `config/piloto.OcultarSocial`), variable de plantilla `herramientas_activo` (`config/piloto.py`), el
comando no envía nada y las tareas del panel no salen. Se cambia en Consola › Configuración.

## Archivos
- Nuevos: `talleres/herramientas.py` (lógica), `talleres/vista_herramientas.py` (vistas y formularios),
  `talleres/templates/talleres/negocio/{mi_dia,_item_agenda,_tablero}.html`,
  `talleres/management/commands/recordar_clientes.py`, `talleres/tests_herramientas.py` (14 pruebas),
  `garaje/migrations/0041_trabajo_en_curso.py`.
- Modelo nuevo: **`garaje.TrabajoEnCurso`** (taller XOR mecánico, cita/visita opcionales, usuario dueño, estado,
  `lista_en`, `entregada_en`, `avisado_en`). En `garaje` para evitar ciclos de migraciones (como `ServicioTaller`).
- Tocados: `consola/ajustes.py`, `config/piloto.py`, `talleres/urls.py` (6 rutas `mi-negocio/…`), `talleres/views.py`
  (`?agendar=1` en la ficha; tareas del panel), `domicilio/views.py` (tareas del panel), `notificaciones/correo.py`
  (prefijo urgente), `templates/base.html` (enlace «Mi día» en menú de taller y mecánico),
  `talleres/static/talleres/css/secciones/talleres.css` (bloque `.md-*`), `tw.css` recompilado (`npm run css`).
- **No** se tocaron modelos de citas/visitas/servicios ni el cambio sin commit de «uso de la moto» en garaje.

## Para la sesión del ciclo del motero (cita → cotización → servicio → reseña)
- Pantallas: `/mi-negocio/` (nueva). Lo demás del ciclo sigue en «Mis citas», «Solicitudes», registro de servicio y
  `cita_publica` / `visita_publica` (el aviso «lista» enlaza a esas páginas públicas cuando hay cita/visita).
- Modelos: solo `TrabajoEnCurso` nuevo. Las citas anotadas por el negocio son `SolicitudCita`/`SolicitudVisita`
  normales con estado `confirmada` (no hay campo «origen»; si las métricas necesitan separarlas, agregar uno).
- Puente natural: al entregar → registrar servicio → (flujo existente) el dueño confirma y califica.

## Pruebas y revisión
- `talleres.tests_herramientas`: 14 OK. Suite rápida: 1107 OK. Suite completa: 1158 OK.
- revisar-ux a 1280 y 375: sin hallazgos propios (arreglados: «–» en días libres y citas sin hora → «Libre»/«Sin hora»,
  días de la semana < 44 px en celular, botones apretados, borde fuera de paleta). Lo que queda es previo: contador de
  la campana (system-ui/color), `chip-reprogramada` azul fuera de paleta, enlaces del pie < 44 px, nombre de cuenta en
  la cabecera con contraste 1:1 a 1280.
- Base local migrada (`garaje 0041`) y con datos de prueba en el taller «Biela y Pistón» (3 trabajos, 2 citas).

## Pendiente / ideas
- Cron de `recordar_clientes` en producción (junto a `recordar_citas`).
- Opción por negocio para no enviar recordatorios automáticos (hoy solo el interruptor global).
- La portada del taller (`_inicio_taller`) ya tiene una agenda por días: podría enlazar a «Mi día» (archivo de la
  sesión de portada; no se tocó).
