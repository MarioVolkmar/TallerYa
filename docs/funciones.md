# Funciones de TallerYa (guía de usuario)

> Actualizado el 2026-11-14, a partir del código. Las 10 funciones y el pedido de SOAT están en el código. El pago del SOAT es una simulación.

| # | Función | Para quién | Estado en el código (14-nov-2026) |
| --- | --- | --- | --- |
| 1 | Pico y placa y vencimientos | Motociclista | Listo |
| 2 | Hoja de vida verificada | Motociclista, taller, comprador | Listo |
| 3 | Gastos y consumo | Motociclista | Listo |
| 4 | Diagnóstico guiado | Motociclista | Listo (`/diagnostico/`) |
| 5 | Emergencias ("¿Te varaste?") y grúas | Motociclista | Listo (`/emergencias/`) |
| 6 | Panel del taller | Taller | Listo (`/mi-taller/estadisticas/`) |
| 7 | Agenda con franjas | Taller, motociclista | Listo (`/mi-taller/agenda/`) |
| 8 | Precios de referencia | Motociclista, taller | Listo (`/mi-taller/precios/` y directorio) |
| 9 | Rodadas | Motociclista | Listo (`/foro/rodadas/`) |
| 10 | Insignias y puntos | Motociclista | Listo (`/insignias/`) |

**Extra: intervalos según el manual.** El plan de mantenimiento usa los intervalos del manual de cada moto cuando los hay (ver la sección *Plan de mantenimiento por moto*, al final).

## Dónde está cada cosa

- **Menú:**
  - *Diagnóstico*;
  - el desplegable **Papeles**, con SOAT y Técnico-mecánica (en el celular aparece como grupo);
  - la píldora roja **"¿Te varaste?"**, que lleva a Emergencias.
- **Portada:** la sección *03 Trámites de tu moto* trae tarjetas de SOAT (con el precio de ley más bajo), Técnico-mecánica (con el número de CDA) y ¿Te varaste?. Después viene *04 Comunidad*.
- **Pie de página:** enlaces a Emergencias, Diagnóstico, SOAT y Técnico-mecánica.
- **Mi cuenta:** *Mis citas* (ver la sección 7).

## 1. Pico y placa y vencimientos

**Qué hace:** te dice si tu moto tiene pico y placa hoy y mañana, y te avisa antes de que se venzan el SOAT y la técnico-mecánica.

- **Pico y placa:** se calcula con el **primer número de tu placa**. En el Valle de Aburrá rige de lunes a viernes, de 5:00 a. m. a 8:00 p. m., y no aplica los festivos. Si lo activas, te llega un recordatorio por WhatsApp la tarde anterior.
- **SOAT:** dura 1 año. Escribe la fecha de vencimiento que aparece en tu póliza.
- **Técnico-mecánica:** la primera se hace a los 2 años de la matrícula y después cada año. Escribe la fecha de matrícula o la fecha de vencimiento de la última revisión.
- La rotación cambia cada semestre (febrero y agosto) y TallerYa la actualiza. Las fechas exactas siempre se pueden confirmar en el RUNT con tu placa.

**Dónde ves los avisos:** en la franja de avisos de *Mi garaje* y de la ficha de cada moto, y en tus notificaciones.

- Te avisa **30, 15 y 3 días** antes de que venza cada documento, y también cuando ya venció.
- Si hoy tienes pico y placa, sale primero un aviso aparte.
- Para la técnico-mecánica, agrega la **fecha de matrícula** al editar la moto. Con ella se calcula la primera revisión, a los 2 años.

Para el equipo:

- La lógica está en `garaje/avisos.py`. La usan la franja de avisos, las notificaciones y el comando `python manage.py avisar_vencimientos`, que hay que programar en un cron diario temprano (por ejemplo, a las 5:30 a. m.).
- La regla de 2026-2 termina el 29-01-2027 y lleva `fin_por_verificar`, porque esa fecha viene de la prensa y no del decreto. Cuando salga el decreto hay que confirmarla y cargar la rotación de 2027-1.

Datos y fuentes: [docs/datos/pico_placa_y_vencimientos.md](datos/pico_placa_y_vencimientos.md).

## 2. Hoja de vida verificada

**Dónde:** en la ficha de tu moto, la sección *Hoja de vida* (`/garaje/<moto>/hoja-de-vida/`).

**Qué hace:** guarda el historial de servicios de tu moto (fecha, kilometraje, qué se le hizo, costo y taller). Los servicios que registra un taller de TallerYa salen marcados como **verificados**.

- **Registrar tú mismo:** agregas un servicio hecho en cualquier taller. Queda en tu historial, pero sin la marca de verificado.
- **Que lo verifique el taller:** en tu hoja de vida generas un **código de 6 caracteres** (o su QR) y se lo muestras al taller.
  - El taller lo escribe en su panel y registra el servicio.
  - El código sirve **una sola vez** y vence a los **30 minutos**.
  - Solo hay un código vivo a la vez: si generas otro, el anterior deja de servir.
  - El código no usa letras que se confunden al dictarlo (0/O, 1/I/L).
- **Privacidad:** un taller nunca puede buscar tu moto por la placa. Solo la ve cuando tú le muestras un código vigente.
- **Compartir para vender:** creas un **enlace público** (con QR) con el historial de la moto, sin tu nombre y con la placa oculta (por ejemplo, `A••••D`). Lo puedes **desactivar** cuando quieras.

Para el equipo: la lógica está en `garaje/hoja_vida.py`, las vistas en `garaje/vista_hoja_vida.py`, el QR en `garaje/qr.py` y las pruebas en `garaje/tests_hoja_vida.py`. Los modelos son `RegistroServicio`, `CodigoServicio` y `EnlaceHojaVida` (migración 0017). El QR que escanea el taller abre `/garaje/servicio/<código>/`, que lo lleva a su panel con el código ya puesto.

## 3. Gastos y consumo

**Dónde:** en la ficha de tu moto, la sección *Gastos* (`/garaje/<moto>/gastos/`).

**Qué hace:** anotas lo que gastas en tu moto y ves cuánto te cuesta, sin tener que llevar cuentas.

- **Anotar un gasto:** solo eliges la **categoría**, el **valor** y la **fecha**. Las notas son opcionales.
- **12 categorías**, cada una con su ícono y color: Gasolina, Aceite y lubricantes, Servicio en taller, Repuestos, Llantas, Lavada, Accesorios y equipo, SOAT, Técnico-mecánica, Parqueadero, Multas y Otro.
- **Gasolina:** no tienes que anotar galones. TallerYa los estima con el valor que pagaste y el precio de referencia del galón en Medellín, y los muestra como "≈ 1,8 gal estimados".
- **Kilómetros:** salen de las lecturas de kilometraje que registras en la moto. No hay que escribirlos en cada gasto.
- **Resumen en tarjetas:**
  - gasto del mes;
  - km recorridos en el mes;
  - costo por km;
  - rendimiento estimado en km por galón.

  Si faltan lecturas de kilometraje, la tarjeta te lleva a *Registra el kilometraje*.
- **Gráficas:** el reparto por categoría en barras y el gasto de los últimos 6 meses.
- Los servicios con costo que ya están en tu **hoja de vida** suman solos: no los anotes dos veces.

Los galones y el rendimiento son **estimados**: cada estación cobra distinto del precio de referencia.

Para el equipo:

- Los cálculos están en `garaje/gastos.py`, la vista en `garaje/vista_gastos.py` y las pruebas en `garaje/tests_gastos.py`. El modelo `Gasto` se creó en la migración 0018. La 0019 pasa a las 12 categorías y convierte "tanqueo" en "Gasolina".
- Los campos viejos de galones y km se conservan, pero el formulario ya no los pide.
- **Precio de la gasolina:** está en `garaje/combustible.py` ($16.251 por galón de corriente en Medellín, vigente desde el 1-nov-2026, con fuente en la [CREG](https://creg.gov.co/publicaciones/15565/precios-de-combustibles-liquidos/)). **Hay que actualizarlo a mano cada mes**, porque la CREG suele ajustarlo al inicio de cada mes.

## Extra: pedir el SOAT en TallerYa (con pago simulado)

> **Importante:** todavía no hay una aseguradora ni una agencia aliada. **El pago es una simulación**: el botón "Pagar" lleva a una página de *pago de prueba* que **no cobra nada ni pide datos de tarjeta**. Para emitir una póliza real hace falta el aliado.

**Dónde:** `/soat/` ("Pide tu SOAT"). En el menú está dentro de **Papeles**.

- **Sin cuenta:** eliges el cilindraje (o escribes los cc) y ves el precio de ley al instante. Para hacer el pedido, *Crear cuenta y pedir mi SOAT* o *Ya tengo cuenta* te devuelven al pedido con lo que ya habías elegido.
- **Técnico-mecánica** (`/tecnomecanica/`, también en *Papeles*): muestra los CDA, con los aliados primero, su precio y su WhatsApp. Funciona sin cuenta y sin moto registrada.

1. **Precio de ley:** TallerYa muestra la tarifa del SOAT según el cilindraje (menos de 100 cc, de 100 a 200 cc, más de 200 cc), con la fuente de donde sale el valor.
2. **Pedido:** los datos de la moto se toman de tu garaje. Tú agregas:
   - los datos del tomador: tipo y número de documento, nombre, correo, dirección y celular;
   - el número de chasis o de motor (opcional) y una foto de la tarjeta de propiedad;
   - la autorización de tratamiento de datos (Ley 1581).
3. **Estado del pedido:** en `/soat/` ves una línea de estado:

   | Estado | Qué significa | Aviso |
   | --- | --- | --- |
   | Recibido | TallerYa recibió tu pedido | — |
   | En proceso | El equipo lo está tramitando | — |
   | Lista para pagar | Ya puedes pagar | Notificación "Tu SOAT está listo para pagar" |
   | Pagada | Pago confirmado (hoy, simulado) | — |
   | Emitida | La póliza está lista para descargar en PDF | Notificación "Tu SOAT quedó emitido" |
   | Cancelada | El pedido no siguió | — |

4. **Al quedar emitida:** el vencimiento del SOAT de tu moto se actualiza solo (inicio de vigencia + 1 año), y desde ahí funcionan los avisos de vencimiento de la función 1.

**Privacidad:** la foto de la tarjeta de propiedad solo la ve el equipo de TallerYa, para emitir la póliza. El PDF de la póliza solo lo ven el dueño y el equipo.

Para el equipo:

- **Cola en el admin:** *Pedidos de SOAT* lista fecha, placa, línea, tomador, valor y estado. Tiene acciones para pasar los pedidos a cada estado, enlaces para ver la tarjeta y la póliza, y notas internas.
  - Al pasar a "Lista para pagar" se puede poner el enlace de pago del aliado.
  - Al emitir se sube el PDF, el número de póliza y el inicio de vigencia.
  - Cada cambio de estado pasa por `PedidoSoat.cambiar_estado()`, que guarda las fechas y envía los avisos.
- **Pago:** todo está en `tramites/pagos.py`. Mientras `SOAT_PAGO_SIMULADO` sea `True` (el valor por defecto), "Pagar" lleva a `/soat/pedido/<id>/pago-de-prueba/` y el pedido queda con `pago_simulado = True`. Para conectar al aliado:
  - poner `SOAT_PAGO_SIMULADO = False`;
  - llenar `enlace_pago` en cada pedido o completar `url_pago()`;
  - llamar a `confirmar_pago(pedido, simulado_=False)` desde el retorno o el webhook del aliado.
- **Código:** app `tramites`, migración 0003. Las tarifas se cargan en el admin (`TarifaSoat`, con su fuente). La misma app tiene `/tecnomecanica/`, con los CDA, que es adonde llevan los avisos de técnico-mecánica.
- **Para el plan de negocio:** esta es la base de la comisión por póliza, que sigue siendo un supuesto mientras no haya aliado.

## 4. Diagnóstico guiado

**Dónde:** `/diagnostico/`. No hace falta cuenta. Funciona con cualquier moto que tenga despiece en TallerYa, aunque no esté en tu garaje.

**Cómo se usa:**

1. **Tu moto.** Eliges una de tu garaje o **buscas cualquier modelo** entre las motos que tienen despiece, por marca, línea y año. Esto funciona también sin cuenta. Si no eliges modelo, basta con decir si es de cambios (con cadena) o automática (scooter con correa CVT).
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
   - el **esquema del sistema** probable, con las piezas candidatas numeradas y señaladas y su lista al lado. Si no elegiste moto, se ve el esquema general del sistema;
   - **3 talleres** que ofrecen ese servicio (primero los destacados y verificados) y un enlace al directorio ya filtrado.

Si elegiste una moto del catálogo, el resultado te invita a *agregarla a tu garaje*, o a crear una cuenta si no tienes.

Es una orientación, no un diagnóstico: no reemplaza la revisión de un mecánico. La página lo dice siempre.

Para el equipo: los síntomas, las preguntas y los resultados están en `garaje/diagnostico.py`, que solo contiene datos y no usa modelos. La vista está en `garaje/vista_diagnostico.py` (una moto del catálogo se elige con `?despiece=<id>`; los esquemas salen de `dx.esquemas` y `dx.esquema_generico`) y las pruebas en `garaje/tests_diagnostico.py`. Para sumar un síntoma basta con agregarlo en `SINTOMAS` y sus resultados en `RESULTADOS`.

## 5. Emergencias ("¿Te varaste?")

**Dónde:** `/emergencias/`. No hace falta cuenta. Se llega desde la píldora **"¿Te varaste?"** del menú y de la portada, y desde el diagnóstico guiado cuando el resultado es "No la ruedes".

**Arriba aparecen 5 botones**, según lo que te pasó:

| Botón | Qué muestra |
| --- | --- |
| 🚨 Accidente | Un botón grande para **llamar al 123** (línea única de emergencias), consejos básicos y la línea de la Secretaría de Movilidad, **(604) 445 77 77**, para trámites y reportes, con su fuente oficial |
| 🛻 Necesito grúa | Las grúas de motos y los talleres con grúa |
| 🔧 Pinchazo | Los talleres con **despinche a domicilio** |
| 🔑 No prende o se apagó | Cuatro chequeos rápidos (gasolina, interruptor de apagado, pata lateral, batería) y un enlace al diagnóstico guiado |
| ⛽ Me quedé sin gasolina | Los talleres que **llevan gasolina a domicilio** |

**Lista de talleres:** son los que atienden emergencias. Salen primero los *Abiertos ahora* (según su horario o porque abren 24 horas) y después los que no tienen horario registrado. Cada uno indica qué ofrece (grúa, despinche o gasolina a domicilio) y trae botones para llamar o escribir por WhatsApp. La página recomienda llamar antes de ir.

**Grúas:** el directorio de grúas para motos es aparte del de talleres. De cada grúa se ve:

- los municipios que cubre;
- si está abierta ahora (24 horas, o un horario que puede pasar de la medianoche);
- la tarifa "desde", si la publicó;
- si lleva la moto en planchón o en cama.

Salen primero las abiertas y después las que cubren el municipio de tu barrio. El botón de WhatsApp abre un mensaje ya escrito: *"Necesito grúa para mi moto…"*, con tu moto si entraste con tu cuenta. Si compartiste tu ubicación, se le agrega un enlace de Google Maps.

**Ubicación:** si das permiso, el teléfono la usa para **ordenar por cercanía** talleres y grúas. Tu ubicación **no sale del teléfono ni se guarda**: el cálculo y el enlace del mapa se arman en el navegador. Solo se ordenan por distancia los que guardaron su ubicación. Si no das permiso, puedes elegir tu barrio.

Para el taller: en *Mi taller → Perfil* marca si atiende emergencias, si abre 24 horas, si tiene grúa o despinche a domicilio, y guarda la ubicación del local. **"Lleva gasolina a domicilio"** se marca en *Mi taller → Agenda*.

Para el equipo:

- La lógica está en `talleres/emergencias.py` (`OPCIONES`, `abierto_ahora`, `ordenar_por_barrio`). Cada botón es un filtro `?necesito=grua|pinchazo|no_prende|gasolina|accidente`.
- Las grúas son el modelo `Grua` (migración 0016) y **se dan de alta en el admin**. Tiene una marca de demo para las grúas de ejemplo.
- `Taller.gasolina_domicilio` es un campo nuevo.
- Los números del 123 y de Movilidad salen de la [página de la Secretaría de Movilidad](https://www.medellin.gov.co/es/secretaria-de-movilidad/conectate-con-la-secretaria/) (actualizada el 13-nov-2026). Hay que revisarlos cada año.

## 6. Panel del taller

**Dónde:** `/mi-taller/` (inicio del panel) y `/mi-taller/estadisticas/`.

**Lo que ya existía:** el taller ve sus citas (puede confirmarlas o reprogramarlas), responde reseñas, crea su propio cupón, edita su perfil y registra servicios verificados con el código del motociclista (función 2). Los talleres nuevos se publican cuando el equipo de TallerYa los aprueba.

**Estadísticas del mes**, comparadas con el mes anterior (sube o baja, en porcentaje):

- visitas al perfil;
- clics a WhatsApp;
- clics a llamar;
- cupones canjeados;
- reseñas nuevas;
- calificación del mes (en este caso se muestra la diferencia en puntos).

Además hay una gráfica diaria de visitas y contactos.

**Privacidad:** solo se suma 1 al contador del día. No se guardan datos personales ni se usan cookies de rastreo, y no cuentan los bots ni las visitas del propio taller.

**Plus taller ("próximamente"):** el panel anuncia lo que tendría la versión de pago, que **hoy no se cobra**:

- historial de 12 meses y descarga en CSV;
- comparación con los talleres de su barrio;
- aparecer primero en el directorio;
- recordatorios de mantenimiento a sus clientes.

Para el equipo: la lógica está en `talleres/estadisticas.py` y el modelo es `EventoDiario` (migración 0012). La lista del Plus taller está en `PLUS_TALLER`.

## 7. Agenda con franjas

**Para el taller** (`/mi-taller/agenda/`):

- Define sus turnos por día de la semana (puede tener varios en un mismo día, por ejemplo mañana y tarde).
- Elige la **duración de cada franja**: 30 min, 45 min, 1 hora, 1 h 30 o 2 horas.
- Fija **cuántas motos atiende por franja**, de 1 a 10.

**Para el motociclista:** al pedir una cita en el perfil del taller, ve las **franjas libres de los próximos 30 días** y elige una.

- Una franja se ocupa con las citas pendientes, reprogramadas o confirmadas.
- Si dos personas piden el último cupo al mismo tiempo, solo una lo consigue y la otra recibe el aviso de que la franja ya no está libre.

**Recordatorio:** el día antes de la cita llega una notificación. WhatsApp sigue disponible como opción manual desde el panel del taller.

Para el equipo:

- La lógica está en `talleres/agenda.py` (`franjas_libres`, `reservar`, con control de concurrencia). Los modelos son `HorarioTaller` y los campos de franja del taller (migración 0013).
- El recordatorio lo envía el comando `python manage.py recordar_citas`, que hay que programar en un cron diario (por ejemplo, a las 6 p. m.). No repite avisos si se corre dos veces.

### Mis citas (para el motociclista)

**Dónde:** en *Mi cuenta*, la sección **Mis citas**, y el detalle de cada cita en `/cuenta/citas/<id>/`.

- **Lista:** las próximas citas, ordenadas por fecha. Cada una muestra la fecha estilo calendario, el logo o las iniciales del taller, la hora, la moto, el servicio y el estado. Las anteriores quedan plegadas en *Ver anteriores*. Si no tienes citas, la página te invita a buscar un taller.
- **Detalle:** el taller con su dirección y un mapa, y los botones *Cómo llegar* y *Ver taller*. También la fecha, la hora, la moto, el servicio y tu nota. Si el taller **propuso otro horario**, aparece un aviso con *Responder propuesta*.
- **Acciones:**
  - escribir al taller por WhatsApp, con el mensaje ya escrito;
  - **agregar la cita al calendario** del teléfono (archivo .ics);
  - **cancelar**, con confirmación y un motivo opcional. Al taller le llega el aviso en sus notificaciones.
- **Privacidad:** cada cita solo la ve su dueño.

Para el equipo: las vistas están en `cuentas/citas.py` y las plantillas son `cuentas/_mis_citas.html`, `_cita_fila.html` y `cita_detalle.html`. Leen `SolicitudCita` de `talleres` sin modificar el modelo, así que no hay migraciones.

## 8. Precios de referencia

**Para el taller** (`/mi-taller/precios/`): publica un rango **desde–hasta** por servicio, que puede separar por cilindraje (hasta 150 cc, de 150 a 400 cc, más de 400 cc, o cualquiera). Es orientativo, no una cotización.

**Para el motociclista:**

- En el perfil de cada taller ve sus precios.
- En el **directorio**, al filtrar por un servicio, aparece el **rango de Medellín**: la mediana de lo que publican los talleres, con la nota *"referencia, no oferta"*.
  - Ese rango solo aparece cuando **al menos 3 talleres activos de Medellín** publicaron ese servicio y cilindraje.
- El directorio se puede ordenar por precio. Los talleres sin precio salen al final.

Para el equipo: la lógica está en `talleres/precios.py` (`medianas_medellin`, `MINIMO_TALLERES = 3`) y el modelo es `PrecioServicio` (migración 0014). Los rangos de prensa de [docs/datos/precios_referencia.md](datos/precios_referencia.md) quedan como respaldo para validar. La función usa solo los datos propios de los talleres, como recomendaba ese documento.

## 9. Rodadas

**Dónde:** `/foro/rodadas/`. Para verlas no hace falta cuenta; para crear una o apuntarse, sí.

- **Lista:** primero salen las próximas; las pasadas quedan archivadas.
- **Crear una rodada:** se indica la fecha y hora, el punto de encuentro, el destino o la ruta (por ejemplo, "Santa Elena por Las Palmas, regreso por Guarne"), el nivel y, si se quiere, un cupo máximo. Hay tres niveles: principiante (ritmo suave), intermedio y avanzado (ruta exigente).
- **"Voy":** te apuntas o te bajas con un botón. Con el cupo lleno no entra nadie más, y las rodadas pasadas ya no cambian.
- **Comentarios:** cada rodada tiene su conversación en el foro, en el tema "Rutas y paseos". Se modera y se reporta igual que el resto del foro: si la pregunta queda oculta por reportes, la rodada también.

Para el equipo: las vistas están en `foro/rodadas.py` y el modelo es `Rodada` en `foro/models.py`, enlazado uno a uno con su `Pregunta`.

## 10. Insignias y puntos

**Dónde:** `/insignias/` ("Mis insignias"). Las insignias también se muestran en tu cuenta y junto a tu nombre en el foro.

| Insignia | Cómo se gana | Puntos | Máximo al mes |
| --- | --- | --- | --- |
| 🔧 Servicio verificado | Un taller registra un servicio en tu hoja de vida con tu código de un solo uso, o canjea en su local un cupón tuyo (los cupones comprados con puntos no cuentan) | 25 | 2 |
| 💡 Aporte útil | Una respuesta en el foro con 2 o más votos "me sirvió" de otras personas, o elegida como solución | 20 | 3 |
| 🏍 Viajero | Asistir a una rodada **de otra persona** con 3 o más asistentes | 15 | 4 |
| ⭐ Buena reseña | Una reseña de un taller con 40 caracteres o más (una por taller) | 10 | 2 |

- **Moto al día ya no da puntos:** el dueño la podía marcar a mano, así que la reemplazó *Servicio verificado*. Las que ya se habían ganado se conservan y siguen sumando.
- **Votos "me sirvió":** en el foro cada persona puede votar una vez cada pregunta o respuesta.
- **Canje:** los puntos se cambian por **cupones** marcados para canje con puntos. Hace falta tener completo el perfil de motociclista (celular) para recibir el código.
- **Antitrampa:** nada se gana solo por publicar. Cada insignia necesita una señal de otra persona: un taller, votos, una solución elegida o asistentes. Además, cada logro cuenta una sola vez y cada insignia tiene un tope al mes.
- **Cuándo llegan:** al momento, salvo *Viajero*, que se revisa cada noche después de la rodada.

Para el equipo:

- Las reglas y los topes están en `logros/reglas.py` (`INSIGNIAS`, `evaluar`, `canjear`). Los modelos son `Logro` y `Canje` en `logros/models.py`, y la etiqueta `{% insignias usuario %}` está en `logros/templatetags/logros.py`.
- El cupón canjeable se marca con `puntos_logros` en el admin de cupones.
- Las insignias se otorgan al momento mediante señales (`logros/signals.py`). *Viajero* depende de que la rodada ya haya pasado, así que la otorga el comando `python manage.py evaluar_logros`, programado cada noche a las 12:00 a. m.

## Plan de mantenimiento por moto (intervalos del manual)

**Qué hace:** cada tarea del plan (aceite, filtro, bujía, cadena…) usa el intervalo del manual de esa moto cuando lo tenemos. Si no, usa el intervalo general.

**Cómo se ve:** junto a cada tarea, la ficha y las guías dicen **"Según el manual"** (con la especificación, p. ej. el aceite y la cantidad) o **"Aproximado"**. Al pasar el cursor se ve la fuente (manual y página).

**Para el equipo:**
- Hay un archivo por línea en `garaje/intervalos/<marca>_<linea>.json`. Hoy son 9 motos: NKD 125, Boxer CT 100, Pulsar NS 200, CB 125F, Aerox 155, Crypton FI 115, FZ 25, NMAX 155 y XTZ 125. `_ejemplo.json` es la plantilla; los archivos que empiezan por `_` no se leen.
- Cada tarea lleva `km`, `dias`, `fuente`, `aproximado`, `especificacion` y `notas`. En `km` o `dias`, `null` (o el campo ausente) usa el intervalo general y `0` significa sin límite.
- **Fuente única:** solo `garaje/intervalos.py` lee esos archivos. De ahí salen colores, avisos y textos. Las fichas del despiece ya no escriben intervalos ni viscosidades fijas.

### Estimación del kilometraje (registros sin km exacto)

**Qué hace:** cuando no sabes el kilometraje exacto de un mantenimiento, el plan lo estima de la forma más realista posible y siempre dice que es una estimación.

**Cómo se ve:** en el despiece, "Ver guía" de una pieza con tarea del plan muestra **"Kilometraje estimado"**: los km desde el último cambio ("≈ 4.200 km desde el último cambio"), una barra con el color del plan ("faltan 1.800 km · 70 %") y una línea con el origen: registro exacto, fecha aproximada o "no sabemos: contamos desde que la moto era nueva". En el catálogo (sin moto propia) no aparece.

**Criterio** (código en `garaje/plan.py`: `km_en_fecha` y `_estado_tarea`). Explicación con ejemplos en `informes_noche/estimacion-km.md`.
- **Ritmo de uso** (km por día): de las lecturas de kilometraje; si no hay suficientes, de los km rodados desde que se registró la moto; si no, de todos sus km desde la fecha de matrícula; si no, del año del modelo. Sin ningún dato, 25 km/día.
- **Fecha sin km** (el km se puede dejar vacío al registrar): km de ese día = km de hoy − lo rodado desde esa fecha. Lo rodado se interpola entre las lecturas sin contar las correcciones del odómetro (saltos de más de 400 km/día). Antes de la primera lectura se cuenta hacia atrás con el ritmo.
- **"Hace unos meses"** (al agregar la moto o al ponerla al día): la fecha es hoy menos esos meses ("Hace más de un año" cuenta 12), y el km sale como arriba.
- **Km sin fecha:** la fecha se estima con el ritmo (como mucho, dos años atrás).
- **"No sé"** en una moto que se registró con menos km que el intervalo de la tarea: contamos desde 0 km (lo peor razonable) y el tiempo desde que se registró. Si ya pasó el intervalo, marca **"Pronto" (revísalo pronto)**, no "Toca ya", porque la única evidencia es la edad de la moto. Si llegó con más km que el intervalo, queda "Sin registro".
- **"Sin idea"** (diálogo "Registrar mantenimiento", dentro de "No sé"): suponemos que nunca se cambió. Cuenta desde 0 km y desde la fecha de matrícula (o mediados del año anterior al modelo), con el mismo tope: "Pronto (estimado)". No va a la hoja de vida.
- **Diálogo "Registrar mantenimiento":** las mismas opciones que "Poner al día", con un solo campo por dato. *Hace poco* no pide nada (hoy y el km actual). *A los … km* pide el kilometraje, y la fecha es opcional ("Agregar fecha"). *No sé* ofrece "hace cuánto" o "Sin idea", o una fecha exacta desplegable.
- Los registros estimados llevan "km estimado" en sus notas, y la guía siempre dice de dónde sale la cuenta.
