# Piloto «Tips y fallas frecuentes» por modelo (18-nov-2026)

En la página de cada moto aparece, después de la Agenda, la sección **«Lo que más les pasa a las [modelo]»**. Tiene tarjetas plegables por falla y debajo los tips del modelo. Funciona en celular: una columna, sin scroll horizontal y botones de 44 px. Captura: `informes_noche/fallas-frecuentes/nmax-celular.jpg`.

## Cómo se ve
- **Cada tarjeta** muestra:
  - la gravedad: Molestia (gris), Cuidado (amarillo) o Peligro (rojo);
  - el título y, al abrirla: cómo lo notas, causa usual, qué hacer y, si hay dato, cuánto cuesta;
  - el alcance: «Reportado por dueños de este modelo» o «Pasa en muchas motos de este tipo».
- **Conexión con el plan:** si la falla tiene que ver con una tarea de la agenda, sale «En tu agenda: X (próximo / requiere atención)».
  - Lo que requiere atención resalta la tarjeta con un borde lava y la sube de primera.
  - Lo próximo solo se menciona, para no resaltar todo en una moto sin registros.
- **Botones:**
  - «¿Te está pasando?» abre el diagnóstico con la moto y el síntoma ya puestos (`/diagnostico/?moto=…&s=cvt&que=tiembla`);
  - «Preguntar en el foro»;
  - «Ver en la agenda»;
  - «Ver la pieza», si la moto tiene despiece de ese sistema;
  - «Talleres que lo atienden» (directorio filtrado por servicio);
  - «Mecánico a domicilio» (listado filtrado por servicio).
- **Fuentes:** van plegadas al final, con la fecha de revisión.
- **Modelo sin datos:** solo salen 3 tips generales según el tipo de moto (scooter, calle o enduro), sin tarjetas de fallas.

## Modelos cubiertos: las 33 líneas del catálogo (ampliado el 18-nov)
- **12 líneas** tienen fallas propias del modelo, con fuente atribuible al modelo.
- **21 líneas** tienen solo fallas «del tipo». Las arma `esqueleto_fallas` según cómo es la moto (cadena o CVT, freno de tambor o de disco, refrigeración líquida, enduro) y les pone los valores de su manual: juego de la cadena e intervalos de correa y válvulas.
- Todas tienen 3 a 6 fallas y 3 a 5 tips. Los tips salen de las notas de `garaje/intervalos/`, sin los comentarios internos.

| Línea | Tipo | Fallas del modelo | Fallas del tipo | Tips | Fuentes externas (además del manual) |
|---|---|---|---|---|---|
| Yamaha NMAX 155 | scooter | 5 | 0 | 5 | motoryk, gridoto, gridoto_servicio |
| Bajaj Pulsar NS 200 | calle | 4 | 0 | 4 | motoryk, zigwheels |
| Honda XR 150L | enduro | 3 | 3 | 4 | motoryk |
| Yamaha Aerox 155 | scooter | 3 | 3 | 4 | motoryk |
| Auteco Bajaj Discover 125 | calle | 2 | 2 | 4 | motoryk |
| Auteco Bajaj Pulsar RS 200 | sport | 2 | 4 | 4 | motoryk |
| KTM Duke 200 | calle | 2 | 4 | 4 | cararac |
| KTM RC 200 | sport | 2 | 4 | 4 | motoryk |
| Honda XR 190L | enduro | 1 | 2 | 3 | procycle |
| Suzuki GN 125 | calle | 1 | 2 | 4 | mot |
| Yamaha MT-03 | calle | 1 | 3 | 5 | mcn |
| Yamaha XTZ 125 | enduro | 1 | 4 | 4 | mw |
| AKT CR4 125 | calle | 0 | 3 | 3 | — |
| AKT Dynamic Pro 125 | scooter | 0 | 3 | 3 | — |
| AKT NKD 125 | calle | 0 | 3 | 3 | carroya |
| AKT TT 125 DS | enduro | 0 | 3 | 3 | — |
| Auteco Bajaj Boxer CT 125 | calle | 0 | 3 | 4 | — |
| Bajaj Boxer CT 100 | calle | 0 | 4 | 3 | c3 |
| Hero Eco Deluxe 100 | calle | 0 | 3 | 4 | — |
| Hero Hunk 125R | calle | 0 | 3 | 4 | — |
| Hero Hunk 150 | calle | 0 | 3 | 4 | — |
| Honda CB 125F | calle | 0 | 3 | 3 | c3_honda |
| Honda Dio 110 | scooter | 0 | 4 | 4 | — |
| Honda Wave 110S | semi | 0 | 3 | 4 | — |
| Suzuki Best 125 | semi | 0 | 3 | 4 | — |
| Suzuki DR 150 | enduro | 0 | 4 | 4 | — |
| Suzuki Gixxer 150 | calle | 0 | 3 | 3 | — |
| TVS Apache RTR 160 | calle | 0 | 3 | 3 | — |
| TVS Raider 125 | calle | 0 | 3 | 4 | — |
| Yamaha Crypton FI 115 | semi | 0 | 3 | 4 | — |
| Yamaha FZ 2.0 | calle | 0 | 3 | 4 | — |
| Yamaha FZ 25 | calle | 0 | 3 | 5 | recall |
| Yamaha XTZ 150 | enduro | 0 | 3 | 3 | — |

**Fuentes externas usadas** (la URL de cada una está en su archivo):
- Motoryk, guías de compra de usadas (NMAX, NS 200, Aerox, Discover, RC 200, RS 200, XR 150L);
- GridOto, para el CVT de la NMAX;
- ZigWheels, para la NS 200;
- MotoDealers, inspecciones MOT de la GN 125 en Reino Unido;
- Cararac, para la Duke 200;
- Motorcycle News, para la MT-03 (el radiador lo golpean las piedras);
- Iamabiker, por el llamado a revisión de la FZ 25 de 2018, que va como tip;
- Motor and Wheels, para la XTZ 125;
- ProCycle, para la XR 190L;
- C3 Care Car Center, para la Boxer CT 100 y Honda en general;
- los manuales del propietario.

**Qué se descartó a propósito:**
- casos de un solo dueño: Raider 125, Gixxer 150, Apache 160, Wave 110S, FZ 2.0 y fallas puntuales de FZ 25 y Duke 200;
- páginas que no abrieron, de las que solo había el extracto del buscador;
- reseñas de otra variante, como la CT 125X o la Xtreme 125R;
- quejas del servicio del concesionario;
- sitios de baja calidad (atvutv.neocities).

**Ojo:** Motoryk es una guía de usados que no cita sus propias fuentes. Se usó porque atribuye cada falla al modelo, pero es lo primero que conviene reforzar con reportes de dueños colombianos o de los talleres aliados.

## Cómo apagarlo
- Bandera `FALLAS_FRECUENTES_ACTIVO`, leída del entorno: está en `.env` local con valor 1 y viene apagada por defecto, así que en producción no aparece.
- Con 0 la página queda igual que antes: ni HTML ni CSS.
- Para quitarlo del todo, borrar:
  - `garaje/fallas.py`, `garaje/fallas_frecuentes/`, `garaje/templates/garaje/_fallas_frecuentes.html`, `garaje/static/garaje/css/fallas.css` y `garaje/tests_fallas.py`;
  - la línea del include en `moto.html`;
  - la llave `"fallas"` y el import en `garaje/views.py` (`detalle`);
  - la bandera en `config/settings.py`.

## Cómo agregar un modelo: skill `fallas-modelo` y comando `esqueleto_fallas`
- **Skill:** `.claude/skills/fallas-modelo/SKILL.md`. Meta: 10 min y 40 k tokens o menos por modelo. Pasos: esqueleto, 2 búsquedas (se pueden delegar a `haiku`), subir o agregar las fallas del modelo con su fuente, prueba y fila en esta tabla.
- **Comando:**
  - `manage.py esqueleto_fallas <slug>` muestra el resumen;
  - `--escribir` crea el archivo;
  - `--faltantes` toma todas las líneas sin archivo;
  - `--forzar` rehace uno que ya existe.
  - Nunca sobrescribe sin `--forzar`, y valida el resultado antes de escribir.
- **Validación:** `manage.py test garaje.tests_fallas` (8 pruebas). Revisa el formato de todos los archivos y que **cada línea del catálogo tenga archivo**, así que una línea nueva sin fallas hace fallar la prueba a propósito.
- Las fallas del modelo de esta tanda se aplicaron con un script del scratchpad. No quedó en el repo porque ya está dentro de los JSON.

## Verificación
- Pruebas: `garaje.tests_fallas` (8) en verde, y la suite rápida (711 pruebas) OK tras la ampliación.
- Ampliación: también revisé en el navegador Aerox 155, Raider 125, XR 150L y RC 200 (motos 42 a 45 de la cuenta de prueba).
- Navegador, puerto 8001: lo revisé en NMAX, NKD y NS 200 con una cuenta de prueba local (`prueba-fallas@local.test`, sin contraseña). Esa cuenta tiene copias de las motos 3, 1 y 7: son las motos 39, 40 y 41. No entré con las cuentas reales.
  - Para borrarla: `User.objects.filter(username="prueba-fallas@local.test").delete()`.
- En el navegador del panel tocó quitar el service worker: servía la página «Sin conexión».
