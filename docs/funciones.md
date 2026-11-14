# Funciones de TallerYa (guía de usuario)

> **Borrador del 2026-11-14.** Otras sesiones están programando estas 10 funciones. Cada sección dice qué ya está en el código y qué falta. Se completa a medida que cada sesión termine.

| # | Función | Para quién | Estado en el código (14-nov-2026) |
| --- | --- | --- | --- |
| 1 | Pico y placa y vencimientos | Motociclista | Pico y placa listo; avisos de técnico-mecánica en desarrollo |
| 2 | Hoja de vida verificada | Motociclista, comprador | En desarrollo |
| 3 | Gastos | Motociclista | En desarrollo |
| 4 | Diagnóstico guiado | Motociclista | Listo (`/diagnostico/`) |
| 5 | Emergencias | Motociclista | En desarrollo |
| 6 | Panel del taller | Taller | Básico listo (citas, reseñas, cupón propio) |
| 7 | Agenda con franjas | Taller, motociclista | En desarrollo |
| 8 | Precios de referencia | Motociclista | En desarrollo (datos en `docs/datos/precios_referencia.md`) |
| 9 | Rodadas | Motociclista | En desarrollo |
| 10 | Insignias | Motociclista, taller | En desarrollo (hoy solo existe la insignia de taller en el foro) |

## 1. Pico y placa y vencimientos

**Qué hace:** te dice si tu moto tiene pico y placa hoy y mañana, y te avisa antes de que se venzan el SOAT y la técnico-mecánica.

- **Pico y placa:** se calcula con el **primer número de tu placa**. En el Valle de Aburrá rige de lunes a viernes, de 5:00 a. m. a 8:00 p. m., y no aplica los festivos. Si lo activas, te llega un recordatorio por WhatsApp la tarde anterior.
- **SOAT:** dura 1 año. Escribe la fecha de vencimiento que aparece en tu póliza.
- **Técnico-mecánica:** la primera se hace a los 2 años de la matrícula y después cada año. Escribe la fecha de matrícula o la fecha de vencimiento de la última revisión.
- La rotación cambia cada semestre (febrero y agosto) y TallerYa la actualiza. Las fechas exactas siempre se pueden confirmar en el RUNT con tu placa.

Datos y fuentes: [docs/datos/pico_placa_y_vencimientos.md](datos/pico_placa_y_vencimientos.md).

## 2. Hoja de vida verificada

*Pendiente de revisar en el código.* Lo previsto: el historial de mantenimiento de tu moto, con los trabajos que confirma el taller que los hizo, para mostrarlo al venderla.

## 3. Gastos

*Pendiente de revisar en el código.* Lo previsto: registrar lo que gastas en tu moto (mantenimiento, gasolina, SOAT, repuestos) y ver cuánto te cuesta al mes.

## 4. Diagnóstico guiado

**Dónde:** `/diagnostico/`. No hace falta cuenta. Si tienes motos en tu garaje, eliges una y el resultado sale con sus piezas.

**Cómo se usa:**

1. **Tu moto.** Si está en tu garaje, TallerYa ya sabe si es de cambios o automática. Si no, te pregunta si es de cambios (con cadena) o automática (scooter con correa CVT).
2. **Qué notas.** Eliges un síntoma:
   - Ruido extraño
   - Vibra más de lo normal
   - No prende
   - Se apaga
   - Frena mal
   - Sale humo
   - Fuga o goteo
   - Pierde fuerza
   - Luces o eléctrico
   - Cambios o clutch, solo en motos de cambios; en las automáticas aparece "Transmisión CVT"
3. **De 1 a 3 preguntas** para afinar, por ejemplo "¿De dónde viene el ruido?" y "¿Cómo suena?". Puedes volver a cambiar cualquier respuesta.
4. **El resultado:**
   - el sistema afectado y la **causa probable**, con una explicación corta;
   - **qué puedes revisar tú mismo** antes de ir al taller;
   - la **urgencia**, en uno de tres niveles: "Puedes seguir rodando", "Revísalo pronto" (esta semana) o "No la ruedes" (llévala en grúa o pide revisión a domicilio);
   - si la moto tiene despiece, las **piezas a revisar**, con un enlace que abre cada pieza en el despiece de tu moto;
   - **3 talleres** que ofrecen ese servicio (primero los destacados y verificados) y un enlace al directorio ya filtrado.

Es una orientación, no un diagnóstico: no reemplaza la revisión de un mecánico. La página lo dice siempre.

Para el equipo: los síntomas, las preguntas y los resultados están en `garaje/diagnostico.py`, que solo contiene datos y no usa modelos. La vista está en `garaje/vista_diagnostico.py` y las pruebas en `garaje/tests_diagnostico.py`. Para sumar un síntoma basta con agregarlo en `SINTOMAS` y sus resultados en `RESULTADOS`.

## 5. Emergencias

*Pendiente de revisar en el código.* Lo previsto: acceso rápido a ayuda si te varas o tienes un accidente (talleres cercanos, grúa, líneas de emergencia, qué hacer con el SOAT).

## 6. Panel del taller

**Qué hace hoy:** el taller entra a su panel y ve sus citas (puede confirmarlas o reprogramarlas), responde reseñas y crea su propio cupón. Los talleres nuevos se publican cuando el equipo de TallerYa los aprueba.

*Pendiente:* las métricas y lo que incluirá el Plus taller.

## 7. Agenda con franjas

*Pendiente de revisar en el código.* Lo previsto: el taller define franjas horarias y cupos, y el motociclista elige una franja libre al pedir la cita.

## 8. Precios de referencia

*Pendiente de revisar en el código.* Lo previsto: rangos orientativos de lo que cuesta cada servicio en Medellín (cambio de aceite, mantenimiento general…), separados por cilindraje. Son una guía y el precio final lo da el taller.

Datos: [docs/datos/precios_referencia.md](datos/precios_referencia.md). Solo el cambio de aceite y el mantenimiento general tienen datos con confianza suficiente.

## 9. Rodadas

*Pendiente de revisar en el código.* Lo previsto: organizar salidas en grupo o unirse a una (punto de encuentro, fecha y ruta).

## 10. Insignias

*Pendiente de revisar en el código.* Lo previsto: reconocimientos por llevar la moto al día, participar en el foro o en rodadas. Hoy solo existe la insignia de taller en el foro.
