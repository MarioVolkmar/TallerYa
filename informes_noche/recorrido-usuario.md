# Recorrido de punta a punta como usuario real

Hecho contra el servidor local (puerto 8001, compartido con otras sesiones) con cuentas de prueba nuevas (datos en `informes_noche/relevos/cuentas-recorrido.txt`, **fuera de git: comprobar que esa carpeta no se suba**; no está en `.gitignore`).
Cubierto: visitante, motero nuevo, taller, diagnóstico y despiece (XR 190L y NMAX 155).
Limitación: el panel del navegador estaba oculto (sin pantalla real), así que lo visual se midió con DOM/`scrollWidth` a 375 px y no con capturas; el 3D no se revisó (solo que sus scripts cargan: 304).

## Hallazgos

| Flujo | Problema | Arreglo / pendiente |
|---|---|---|
| Foro · reaccionar | **500** al reaccionar casi a la vez (doble clic o varios emojis): `IntegrityError` por reacción duplicada | **Arreglado** en `foro/reacciones.py` (captura el choque y solo actualiza el tipo). Verificado: 4 peticiones paralelas → 200 |
| Registro | Error de clave decía «muy parecida a **nombre de usuario**» (nadie tiene usuario, es el correo) | **Arreglado**: validador propio `cuentas/validadores.py` + `config/settings.py` («se parece demasiado a tu correo o a tu nombre») |
| Entrar | Error con texto de Django: «nombre de usuario y clave correctos… sensibles a mayúsculas» | **Arreglado** en `EntrarForm` («El correo o la contraseña no coinciden…») |
| Mi cuenta · actividad con talleres | «Última: Cita… 16 nov» cuando se pidió el 15 (fecha en UTC, no hora de Bogotá) | **Arreglado** en `cuentas/views.py` (`localtime`) |
| Avisos / Mi cuenta | «hace 0 minutos» (timesince de Django) | **Arreglado**: se usa la etiqueta `hace` («hace un momento», «hace 5 min») en lista de avisos, Mi cuenta y panel de la campana |
| Chispa | «¿Cada cuánto cambio el aceite?» respondía «¿Cómo registro lo que le hice?» | **Arreglado**: nueva pregunta frecuente `cada-cuanto` en `ayuda/faq.json` |
| Chispa | «hola» → «no encontré una respuesta» | **Arreglado**: los saludos se contestan con el saludo (`ayuda/motor.py`) |
| Mi cuenta | «Taller visitado: 1» y «Calificar taller» aparecen con solo una cita **pendiente** (aún no hubo visita) | **Pendiente (decisión de producto)**: contar/ofrecer reseña solo tras cita atendida o servicio registrado |
| Taller · servicio hecho | El formulario acepta un km muy inferior al odómetro (100 vs 9.500) y deja el aceite «Toca ya» | Pendiente (decisión): válido para servicios viejos, pero quizá avisar «es menor que el kilometraje actual» |
| Panel del taller | «Te falta: … descripción» aunque se escribió una corta | Pendiente: aclarar el mínimo de caracteres o no listarla |
| Agenda | Taller que dice «Lun-Vie 8am-6pm» ofrece horas desde 9:00 (franjas del taller de demo) | Pendiente: revisar que franjas y horario público coincidan |
| Diagnóstico | Con una moto del garaje elegida por catálogo (`?despiece=`) sigue diciendo «Agrega esta moto a tu garaje» | Menor; usar `?moto=` cuando la moto ya es del usuario |
| Consola | 97 avisos «An unknown error occurred when fetching the script» | No se pudo atribuir: todos los .js responden 304/200; parece el service worker en este navegador embebido. Probar en Chrome real |
| Seed | Un celular de prueba (3009990001) ya estaba tomado por otra cuenta local | Solo datos de prueba |

## Lo que funcionó sin problemas
- 109 URLs del sitemap, 37 enlaces de portada y 68 de talleres/foro/rodadas/cupones/noticias/técnico/SOAT/emergencias/Plus: **ninguna 404/500** (visitante).
- Registro motero (errores claros de celular/correo/clave/términos) → guía de 4 pasos → moto → plan → km → «Lo hice yo» → hoja de vida → papeles (SOAT/tecno con aviso «vence pronto/vencido») → avisos coherentes.
- Cita (con y sin franjas) → taller la ve → confirma → registra servicio → el motero recibe aviso y queda **verificado** en la hoja de vida → reseña publicada.
- Foro: preguntar (valida preguntas cortas), responder, reaccionar/votar.
- Diagnóstico: recorrido completo del árbol (69 pasos, XR 190L y NMAX) sin errores; despiece JSON y 38 SVG de láminas de XR 190L y NMAX: todos 200.
- Móvil 375 px: sin desborde horizontal en 17 páginas (visitante y motero).
- Pruebas `ayuda cuentas foro notificaciones` (133): OK. No se tocaron tests ni archivos 3D.
