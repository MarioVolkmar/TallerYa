# Fase 2: chat propio motero ↔ taller / mecánico (solo diseño, no construido)

## Cuándo construirlo (qué medir en el piloto)
No se construye hasta que la fase 1 (ficha + WhatsApp) muestre uso y fricción real. Medir con lo que ya existe:
- **Uso**: fichas creadas por semana (`FichaDiagnostico`), % de diagnósticos con resultado que llegan a «Enviar» y, de esos, los que terminan en WhatsApp (ficha creada).
- **Interés del destinatario**: `FichaDiagnostico.vistas` > 0 (¿el taller abrió el enlace?) y vistas por ficha. Si menos de ~50 % de las fichas se abren, el problema es el canal, no la falta de chat.
- **Fricción de WhatsApp**: queja directa de talleres/mecánicos (no tienen WhatsApp Business, mezclan chats, pierden el enlace); fichas reenviadas al mismo taller por segunda vez en 48 h (señal de que no hubo respuesta).
- **Cierre del ciclo**: fichas seguidas de un servicio registrado (paso 3) del mismo taller en 14 días. Es la métrica que de verdad paga el chat.
- **Umbral sugerido para decidir**: ≥ 100 fichas/mes, ≥ 60 % abiertas, y ≥ 3 talleres/mecánicos pidiendo «responder desde la página» o ≥ 20 % de fichas sin respuesta reportada por el motero.

## Modelo de datos (apps: `garaje` o una nueva `mensajes`)
- `Conversacion`: `ficha` (FK a FichaDiagnostico, opcional), `motero` (FK Motociclista, nullable: anónimo con token), `taller` / `mecanico` (uno de los dos), `estado` (abierta, cerrada, vencida), `creada`, `ultimo_mensaje`, `token_motero` (acceso sin cuenta, no adivinable), `no_leidos_motero`, `no_leidos_prestador`.
- `Mensaje`: `conversacion`, `autor` (motero | prestador), `texto` (≤ 1000), `foto` (opcional, misma validación y recorte que las fichas), `creado`, `leido`.
- Reglas: sin datos personales obligatorios; el celular del motero solo si él lo comparte. Máximo 1 conversación abierta por (motero, prestador, ficha). Retención: borrar a los 90 días de inactividad (misma lógica del reporte mensual: sin PII que sobreviva).
- Moderación: botón «Reportar» (guarda mensaje + motivo para la consola); el prestador puede bloquear a un token.

## Flujo
1. En «Enviar» aparece una segunda opción por destino: «Escribir por TallerYa» (junto a WhatsApp). Crea la `Conversacion` con la ficha como primer mensaje (tarjeta).
2. El prestador la ve en su bandeja (`Mi taller` / `Mi perfil` del mecánico) con contador de no leídos; responde en texto + foto, y puede adjuntar una cotización (reutiliza el flujo de solicitudes de `domicilio`).
3. El motero abre `/chat/<token>/` sin cuenta (o desde su garaje si tiene cuenta); la página consulta cada ~15 s (polling simple; sin WebSockets en el piloto).
4. Cierre: el prestador marca «atendida» (alimenta el paso 3: ofrecer registrar el servicio verificado y la reseña).

## Notificaciones
- Al prestador: Web Push (VAPID ya configurado) + WhatsApp plantilla «tienes una consulta nueva en TallerYa» con el enlace a la bandeja (una sola plantilla aprobada por Meta; las respuestas dentro de la página no pagan conversación).
- Al motero: Web Push si tiene cuenta; si no, un único WhatsApp/SMS con su enlace al abrir la conversación y «te respondieron» (máx. 1 por hora para no spamear).
- Recordatorio al prestador a las 4 h sin respuesta en horario laboral; marcar la conversación «sin respuesta» a las 48 h y devolverle al motero la opción de otros talleres.

## Riesgos
- Costo y mantenimiento de moderación y soporte; los talleres ya viven en WhatsApp, el chat propio solo gana si trae notificaciones fiables.
- Dependencia de plantillas de Meta (aprobación y costo por conversación iniciada por la empresa).
- Fuga de contactos: si el chat oculta el celular, talleres y moteros se lo pasarán fuera; aceptarlo y cobrar por el valor (cotización, reseña verificada), no por esconder el número.

## Alcance mínimo si se aprueba (≈ 1 sesión pesada)
Modelos + migración, bandeja del prestador, página del motero con token, polling, Web Push y una plantilla de WhatsApp; sin adjuntos distintos de fotos, sin grupos, sin búsqueda.
