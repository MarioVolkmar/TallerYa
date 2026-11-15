# Chispa, la mascota de TallerYa

Bujía real (terminal, cerámica con 4 anillos, hombro, tuerca hexagonal, anillo lava, rosca, electrodo de tierra) con **visor de casco**. Los ojos son dos luces ámbar que parpadean y miran. Brazos metálicos delgados que salen de la tuerca, con tornillos en los hombros. Solo SVG y CSS, sin imágenes (~9 KB de HTML).

## Archivos
- Componente: `templates/parciales/chispa.html`
- Animaciones: bloque «Chispa, la mascota» al final de `talleres/static/talleres/css/tallerya.css`
- Portada sin motos: `talleres/templates/talleres/_portada_moto.html` (dentro del enlace `.pm-vacio`, así que tocar a Chispa también lleva a `garaje:bienvenida`)
- Muestra de las poses: `informes_noche/chispa-muestra.html` (archivo estático, ábrelo en el navegador)

## Cómo usarlo
```django
{% include "parciales/chispa.html" with pose="saludando" clase="w-24" etiqueta="Chispa te saluda" %}
```
| Parámetro | Valores | Nota |
|---|---|---|
| `pose` | `quieta` (por defecto), `barriendo`, `saludando`, `escena` | `escena` trae todos los juegos de brazos (`.ch-b-izq`, `.ch-b-der`, `.ch-b-alza`, `.ch-b-escoba`) y la animación de la página decide cuál se ve |
| `estilo` | `a` (por defecto), `b` | `b` = línea técnica azul con ojos ámbar (modo Rayos X). Listo, sin usar todavía |
| `clase` | clases CSS/Tailwind | el tamaño se da con el ancho (`w-24`, etc.) |
| `x`, `y`, `ancho`, `alto` | números | para meterla dentro de otro SVG (unidades del SVG padre). Proporción 150 × 226 |
| `id` | texto | prefijo de los degradados: cámbialo si hay dos Chispas en la misma página |
| `etiqueta` | texto | para lectores de pantalla. Sin ella, Chispa es decorativa (`aria-hidden`) |
| `mira` | `derecha` | por defecto mira a la izquierda de vez en cuando |

Animaciones: respira (quieta/saludando), vaivén y escoba con polvo (barriendo), mano que saluda, parpadeo cada ~5 s, mirada hacia un lado cada ~8 s, chispazo en el electrodo. Con `prefers-reduced-motion` todo queda quieto.

## En la portada
Barre junto al puesto punteado, a la derecha, y mira de vez en cuando hacia el «+». Revisado con la cuenta de prueba sin motos a 1440, 1920, 390 y 360 px: no tapa ni el botón ni el título. En celular la escena vacía se corrió un poco a la izquierda (`.portada-vitrina .portada-escena.portada-vacia { left: -10%; width: 120% }`) para que Chispa quepa. En celular se ve pequeña (unos 25 px de ancho). Si se quiere más grande, habría que darle más altura a la escena.
(Esta Chispa quieta que barre sigue siendo la que se ve si se apagan las escenas.)

## Escenas animadas (experimento, fácil de revertir)
Se activan con `chispa_escena=True` en el `include` de `talleres/inicio.html`. Esa variable le pone la clase `.pm-chispa-escena` al SVG de la portada.

La intro se ve completa en cada carga o recarga y no se repite sola mientras se mira. Después queda un reposo en bucle. No hay capas oscuras: el fondo es siempre el de la página.

**1) Portada sin sesión (intro de unos 10 s; la lámpara prende a los 7,4 s y el saludo termina a los 9,8 s):**
1. La escena arranca oscura, con la lámpara apagada: campana oscurecida (`brightness`), bombillo gris, sin cono, charco, motas ni halos.
2. La moto entra desde la izquierda en penumbra (`filter: brightness(.22)`), sin farola ni haz, y se estaciona.
3. Chispa entra también en penumbra (mismo filtro) desde la derecha, barriendo con polvo (2,6–4,2 s, mientras la moto termina de asentarse). Solo brillan sus ojos, mediante una capa aparte fuera del filtro y se detiene a la derecha de la rueda delantera.
4. Da un último barrido y apoya la escoba contra la pared, entre la rueda y ella, con un movimiento visible (4,5–5,2 s): la escoba se levanta, se endereza, se asienta con un pequeño rebote y Chispa se inclina hacia ella.
5. Carga (anillo y vibración), lanza el rayo doble con ramas, hay destello y chispas, y la lámpara parpadea blanco → ámbar → fijo (6,8–7,8 s). Al prender (7,4 s), Chispa, la escoba, la moto y el tablero recuperan su color juntos en 0,4 s y aparecen el cono y el polvo.
6. Chispa saluda (7,8–9,8 s) con la escoba apoyada. A los 8 s la moto enciende: destello del faro, stop, direccionales, sacudida y bocanada. Sigue con su ralentí y su arranque cada 6 s.
7. En reposo, cada 14 s, Chispa saluda y luego toma la escoba con el mismo movimiento al revés, barre un rato y la vuelve a apoyar.

En escritorio la moto va al 90 % y el tablero y el letrero al 85 %. En celular la moto (con su haz, farola, halos, humo y sombra) va al 78 % y un poco a la izquierda, y el tablero al 67 %, con la base cerca del asiento de la moto y por encima de Chispa, y Chispa se corre 85 unidades: queda entre la rueda delantera y el borde, con la escoba apoyada y el saludo a la vista.

**2) Garaje vacío (intro de unos 5 s), sin oscuridad ni rayo:** ya entraste al taller, así que la lámpara está prendida desde el inicio, con cono y polvo.
1. Chispa entra con unos pasos cortos (0,3–1,5 s).
2. Sus ojos pasan de ámbar a azul (#85B7EB) en 0,3 s y quedan así mientras proyecta, y el visor escanea el piso como en Rayos X (1,3–3,1 s): un haz con una línea clara que barre de ida y vuelta donde iría la moto.
3. Aparece el holograma (3,2 s), a la misma escala que la moto de la portada sin sesión: silueta detallada con relleno translúcido, contorno, rayas finas, brillo, detalles internos tenues, líneas de barrido que suben y un parpadeo ocasional. Alterna scooter tipo NMAX → naked → enduro cada 3 s, y queda un cono suave desde los ojos.
4. El globo «¿Y tu moto?» / «Agrégala en 1 minuto» sale encima de Chispa.
5. Al terminar de imprimirse el holograma (3,8 s), aparece con un pequeño rebote el «+» dentro del cono de la lámpara, centrado en su eje y justo encima de la silueta (en celular baja 62 unidades con el holograma). Tiene estilo holográfico en el color lava de la página: relleno lava translúcido con rayas finas, contorno lava luminoso con brillo, anillo exterior punteado lava que gira en 9 s, cruz #F0997B, una línea de barrido que baja y el mismo parpadeo del holograma. Late suave y, al pasar el cursor o con foco, se rellena más y brilla. Toda la escena, incluida la moto proyectada, es el enlace a `garaje:bienvenida` (aria-label «Agrega tu moto»). En celular el «+» sigue la escala del holograma.

No hay nube, ni puesto punteado, ni raya naranja del piso: solo una sombra elíptica suave bajo el holograma. En celular, Chispa, el haz y el escaneo se corren 110 unidades a la izquierda, el globo (al 85 %) 125, y el holograma va al 78 %, como la moto de la otra portada.

**Mismo tamaño en las dos portadas:** el garaje vacío usa el mismo recuadro de SVG que la portada sin sesión. En escritorio es `left: 46%` con una altura fija de `28rem`, para que la escala no dependa de cuántas líneas ocupe el título ni de cuándo carga la fuente; en celular, `left: -28%; width: 156%; height: 93.6vw` en celular). El holograma va a 1,5×, como la moto real.

Medidas en Edge sin interfaz, con la escena en reposo:

| Ancho | Chispa (px) | Lámpara (px), sin sesión / garaje vacío | Rueda (px), moto / holograma naked |
|---|---|---|---|
| 1440 | 147 / 146 | 27 / 25 | 106 / 114 |
| 1920 | 146 / 146 | 27 / 25 | 107 / 114 |
| 390 | 113 / 113 | 21 / 19 | 82 / 88 |
| 360 | 104 / 104 | 20 / 18 | 75 / 81 |

El piso queda en y=519 en ambas en escritorio.

**Cruces medidos:** solo quedan cruces de cajas sin solape real.
- La caja del `<use>` de la moto llega hasta x=800, aunque la rueda termina en 740.
- El cono cae sobre la moto a propósito.
- La caja del holograma incluye la región del filtro de brillo.
- La lámpara roza la caja de «Cita por WhatsApp», pero las dos ya estaban así antes de este trabajo.
- Sin desborde horizontal en ningún ancho.

**Sin movimiento** (`prefers-reduced-motion`): los estilos base ya son la escena final. Se apagan todas las animaciones.

### Cómo revertir
1. **Apagar sin borrar nada:** quitar `chispa_escena=True` del `include` en `talleres/inicio.html`. Vuelven la Chispa quieta que barre en el garaje vacío y la portada sin sesión de siempre.
2. **Borrar del todo**, además del paso 1:
   - En `talleres/_portada_moto.html`, los bloques `{% if chispa_escena ... %}`: la clase del `<svg>`, el bloque `.pm-ch-garaje` tras la moto, la lámpara `.pm-chv-lampara` antes del enlace, y dentro del enlace la rama `{% if chispa_escena %}…{% else %}` (se deja solo la Chispa quieta).
   - Las clases `pm-v-foco`, `pm-v-piso` y `pm-sombra-moto` son inofensivas.
   - En `tallerya.css`, el bloque «Chispa: escenas animadas de la portada» hasta «fin de escenas de Chispa».
   - La pose `escena` del componente puede quedarse.

## Ideas para después
- **Guía y primer uso:** `saludando` al lado de cada paso de `garaje:bienvenida`, con un globo de texto corto. Una pose nueva, «señalando», ayudaría (un brazo extendido; se arma igual que el brazo que saluda).
- **Páginas vacías** (sin citas, sin cupones, foro sin respuestas, garaje sin gastos): `quieta`, de unos 96 px, encima del mensaje vacío.
- **Errores 404/500:** Chispa con el visor apagado (ojos en línea, sin halo) y el chispazo fallando. Basta con una clase `.chispa-apagada` que oculte `.ch-halo` y aplane `.ch-ojo`.
- **Chatbot:** burbuja flotante abajo a la derecha con Chispa `quieta` recortada desde el visor hacia arriba (cambiar el `viewBox` a `-30 -8 60 110`). «Pensando» = ojos que barren de lado a lado (reusar `ch-mirar` con más velocidad). «Respondiendo» = chispazo continuo.
- **Rayos X / diagnóstico:** estilo `b` junto al modelo 3D en modo Rayos X.
