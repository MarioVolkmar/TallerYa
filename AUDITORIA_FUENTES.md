# Auditoría con fuentes externas (filtro 4)

Lo hace el Auditor, según `docs/auditor.md`. Los cambios los aplica "Planos y Esquema Piezas". Este filtro se suma a los requisitos 1 a 10 y a los criterios de Planos, que siguen en `AUDITORIA_DESPIECE.md`.

## Capa 1: chequeo automático de todas las piezas (14-nov-2026)

- **Qué se hizo:** se volcaron las 8.481 piezas de las 24 motos tal como las muestra el visor (`views._laminas_base`): nombre, sistema, guía (`que_hace`, `cada_cuanto`, señales, consejos, dificultad…) y tarea del plan.
- **Scripts:** `capa1_volcado.py` y `capa1_analisis.py`, en el scratchpad del Auditor.

| Chequeo | Resultado |
|---|---|
| Ficha de cadena (kit de arrastre, sprocket) en una scooter | 0 |
| Pieza de seguridad (frenos, ruedas, suspensión) marcada "Lo puedes hacer tú" | 0 |
| "Pastillas" en un freno de tambor | 0 |
| Pieza con tarea y sin "¿Cada cuánto?" | 0 |
| **Texto de la CVT (rodillos, variador) en piezas que no son CVT** | **55, crítico** (lote 1, F4-1) |
| "Carburador" en motos de inyección | 18, casi todos con el genérico "carburador o cuerpo de aceleración", que es aceptable; 5 con un consejo equivocado (lote 1, F4-3) |
| "Cada cuánto" de la ficha que contradice la tarea del plan | 171 marcadas; revisadas a mano, la mayoría es revisión frente a cambio (no se contradicen). Una contradicción real: F4-2 |
| "Inyección" en motos de carburador | 9 falsos positivos: textos de CDI y regulador que nombran "ECU o inyección" en general |

## Lote 1: piezas del plan de mantenimiento y conceptos (14-nov-2026)

| Pieza o ficha | Moto(s) | Qué se revisó | Dice hoy | Debería decir | Fuente(s) | Gravedad | Confianza |
|---|---|---|---|---|---|---|---|
| F4-1. Ficha "CAM" (rampa de rodillos del variador), que también cae en CAMSHAFT, CAMISA, CAMPANA y "CAM, RR. BRAKE" | Best, Crypton, Boxer, Discover, CB 125F y otras (51 piezas) | a. concepto | El árbol de levas, la leva del freno, la campana del freno y las camisas de la telescópica dicen "Es la rampa sobre la que ruedan los rodillos del variador" y "Se revisa al cambiar rodillos" | Que cada una reciba la ficha de su pieza (árbol de levas, leva del freno, campana o tambor, tubo de la telescópica) | Concepto: el catálogo dice CAMSHAFT, CAM RR. BRAKE, Campana y Camisa Telescópico, y la lámina las pone en Motor, Frenos, Ruedas o Suspensión, no en la CVT | crítico | alta |
| F4-1b. Ficha "SLIDER" (guías del variador) | CB 125F "SLIDER, CHAIN" (3) | a | "Guías plásticas de la polea del variador… cada 12.000 km con los rodillos" | Deslizador de la cadena: protege el basculante del roce de la cadena; se revisa con la cadena y se cambia si está gastado o roto | Concepto (lámina del basculante, moto de cadena) | crítico | alta |
| F4-1c. Guía mecánica "correa" (correa del variador) | Apache "CORREA PLÁSTICA RAMAL" y Pulsar RS 200 "Kit Correas", ambas en la lámina eléctrica | a | "Es la correa del variador… cámbiala cada 12.000 a 20.000 km" | Amarras plásticas del cableado: sujetan el ramal al chasis; se cambian si se rompen; no tienen intervalo | Concepto (lámina "Sistema eléctrico"; las motos son de cadena) | crítico | alta |
| F4-2. Amortiguador trasero: ficha "SHOCK ABSORBER" y guía mecánica "amortiguador" frente a la tarea `suspension-tras` | Todas | b. intervalo | La ficha dice "Revísalo cada 10.000 km"; la tarea, 20.000 km. Se contradicen | Una sola cifra. Honda revisa la suspensión en cada servicio programado (CB125E: cada 4.000 km). Propuesta: que la ficha diga "en cada mantenimiento (cada 4.000 a 6.000 km)" y que la tarea baje a 6.000 km, o al menos que coincidan. **Decide el usuario**: es un intervalo del plan | maintenanceschedule.com, plan del CB125E tomado del manual Honda (consulta: 14-nov-2026) | importante | media |
| F4-3. Guía mecánica "cuerpo" (cuerpo del carburador o del acelerador) en motos de inyección | Duke 200, RC 200, NS 200, RS 200, Gixxer (5 piezas) | b. consejos | "Límpialo con limpiador de carburador, sin meter alambres en los chicleres" | En inyección: "Límpialo con limpiador de cuerpo de aceleración (apto para sensores), aplicado con un trapo, sin mojar el sensor de posición del acelerador (TPS)". Un cuerpo de aceleración no tiene chicleres | MotorWeek, "Induction system cleaning"; CRC Throttle Body Cleaner (thsmoto.co.nz) (consulta: 14-nov-2026) | importante | media |
| Tarea `liquido-frenos`: 20.000 km o 730 días | Todas con disco | b | 2 años | Correcto | Manuales Yamaha (MT-07 y MT-09 en manualslib: "cambiar el líquido cada 2 años"); Harley-Davidson Service Info; CB125E "cada 2 años" (consulta: 14-nov-2026) | — | alta |
| Tarea `cadena-lubricar`: 600 km o 15 días | Todas de cadena | b | 600 km | Correcto: está dentro del rango (Honda: cada 1.000 km o antes si se ve seca; Tsubaki: 300 a 600 km) | Manual Honda CB1000 (manualslib); rider.tsubaki.eu (consulta: 14-nov-2026) | — | alta |
| Tarea `bujia`: 8.000 km | Todas | b | 8.000 km | Correcto como cifra general: el CB125E la cambia a los 8.000 km; Suzuki, entre 10.000 y 12.000 km. Depende de la moto: se coteja por modelo en la capa 3 | maintenanceschedule.com (CB125E); manuales Suzuki GW250 y AN400 (manualslib) (consulta: 14-nov-2026) | — | media |
| Tarea `aceite`: 2.500 km o 120 días | Todas | b | 2.500 km | Es más conservador que los fabricantes: Yamaha Indonesia pide 3.000 a 4.000 km en la NMAX y Honda, 4.000 km en el CB125E. No es peligroso, pero no coincide con ningún manual. Se coteja por moto en la capa 3 | gridoto.com (Yamaha Indonesia, NMAX); maintenanceschedule.com (CB125E) (consulta: 14-nov-2026) | menor | media |
| Tarea `valvulas`: 6.000 km | Todas | b | 6.000 km | Depende de la moto: CB125E cada 4.000 km; NMAX, revisión cada 8.000 km. Capa 3 | maintenanceschedule.com (CB125E); manual de la NMAX 155 (manualslib, fragmento) (consulta: 14-nov-2026) | menor | media |

### Cambios exactos para Planos (lote 1)

1. **F4-1 y F4-1b: claves genéricas de la CVT que caen en otras piezas por prefijo** (`garaje/despiece_fichas.py`)
   - Hoy: `ficha_para` hace `clave.startswith(k)` sin límite de palabra. Por eso "CAM" atrapa CAMSHAFT, CAMISA y CAMPANA, y "SLIDER" atrapa "SLIDER, CHAIN".
   - Propuesta:
     - (a) el prefijo solo vale si lo que sigue es el fin del texto, una coma o un espacio: `clave == k or clave.startswith(k + ",") or clave.startswith(k + " ")`;
     - (b) las fichas de la CVT ("CAM", "SLIDER", "WEIGHT", "PRIMARY…", "SECONDARY…", "V-BELT", etc.) solo se dan si la lámina es de la CVT (`pieza == "correa"` o diagrama `cvt`);
     - (c) "CAM, RR. BRAKE" o "CAM, BRAKE" lleva su propia ficha de leva del freno: "Es la leva que, al girar con el pedal o la palanca, abre las bandas contra el tambor"; se engrasa al cambiar las bandas; si está gastada, el freno queda largo;
     - (d) "SLIDER, CHAIN" lleva la ficha del deslizador de la cadena (texto en la tabla).
   - Cómo comprobarlo: 0 piezas fuera de la lámina de la CVT con "rodillos" o "variador" en `que_hace` o `cada_cuanto`. Lo mide `capa1_analisis.py`, grupo `cvt_en_cambios`.
2. **F4-1c: CORREA PLÁSTICA y Kit Correas** (puesto y guía mecánica)
   - Por primera palabra, CORREA PLÁSTICA es una amarra (`h_abrazadera`), no la correa del variador.
   - Propuesta: si la descripción dice "CORREA PLÁSTICA" o "KIT CORREAS" y la lámina es eléctrica, el tipo es abrazadera o amarra, con el nombre "Amarra plástica del cableado" y el texto de la tabla.
3. **F4-2: amortiguador** (la ficha "SHOCK ABSORBER" en `despiece_fichas.py:284` y la guía mecánica "amortiguador" en `despiece_guia_mecanica.py:352`)
   - Unificar el "cada cuánto" con la tarea `suspension-tras`.
   - Hasta que el usuario decida la cifra, que la ficha diga: "Revísalo en cada mantenimiento (fugas y rebote); dura entre 20.000 y 40.000 km según el uso".
4. **F4-3: guía mecánica "cuerpo"** (`despiece_guia_mecanica.py:429`)
   - Que el consejo dependa de si la moto tiene inyección: si el diagrama es `inyeccion`, el consejo del limpiador de cuerpo de aceleración de la tabla; si es `carburador`, el actual.
   - Lo mismo para `que_hace`: en inyección, "Es el cuerpo de aceleración: por ahí pasa el aire que entra al motor y la mariposa regula cuánto, según cuánto aceleres".

### Verificación del lote 1 (14-nov-2026): **verificado**
- Hecho con un volcado nuevo de las 8.481 piezas y los chequeos anteriores.
- Resultados:
  - 0 piezas fuera de la CVT con "rodillos" o "variador".
  - La leva del freno (CB, Dio, XR), el árbol de levas, el deslizador de la cadena, las amarras (Apache, RS 200) y el cuerpo de aceleración de la Duke reciben ya su ficha propia.
  - 0 "chicleres" en motos de inyección.
  - Criterio 3 en 0; criterio 2 en 28 (todos casos 2e, que el usuario ya decidió).
- Decisión del usuario, según lo reportó Planos: la tarea `suspension-tras` queda en 20.000 km, y la ficha y la guía del amortiguador se alinearon a esa cifra.
  - La fuente (Honda, CB125E) revisa la suspensión en cada servicio de 4.000 km. Queda anotado; no se cambia.
- El chequeo nuevo encontró otro caso del mismo tipo, más estrecho: lote 2.

### Abierto (sin verificar todavía)
- **Capa 3:** los intervalos por moto (aceite, válvulas, bujía, filtro de aire, correa CVT y aceite de la transmisión final) contra el manual de cada una de las 24 motos. No se encontró el manual oficial colombiano en línea de la NMAX (Incolmotos), el CB 125F (Fanalca) ni el Boxer (Auteco). Las cifras de Yamaha Indonesia y Malasia sirven como referencia, pero son de otra versión.
- **Desgaste mínimo legal de llantas de moto en Colombia:** las fuentes citan 1,6 mm (NTC 5375), pero para vehículos livianos (M1, N1), no para motos. No queda confirmado.

## Lote 2: guía de la polea trasera de la CVT en piezas "DRIVEN" de motos de cambios (14-nov-2026)

| Pieza o ficha | Moto(s) | Qué se revisó | Dice hoy | Debería decir | Fuente(s) | Gravedad | Confianza |
|---|---|---|---|---|---|---|---|
| F4-4. `_PALABRAS` en `despiece_guia_mecanica.py:769`: `DRIVEN` → "polea_trasera" | Best (WASHER, 1ST DRIVEN; CIRCLIP, 4TH DRIVEN), Gixxer (BUSH, 1ST/2ND DRIVEN GEAR), CB 125F y Eco Deluxe (FLANGE… DRIVEN), GN (GEAR, SLEEVE y SEAL del TACHOMETER DRIVEN) | a. concepto | "Es la polea trasera (conducida): recibe la correa… Se revisa con la correa" | La guía de lo que dice su primera palabra: arandela o pin seguro de la caja, buje del piñón, brida portacorona (sprocket) de la rueda, piñón, camisa o retenedor del tacómetro | Concepto: en el catálogo, DRIVEN es "conducido", no polea; estas motos son de cadena | crítico | alta |
| F4-5. Ficha "CLUTCH CARRIER ASSY" y guía mecánica "clutch" | Crypton FI 115 (CLUTCH CARRIER ASSY; SPRING, CLUTCH WEIGHT) | a/b | "Se revisa cada 12.000 km junto con la correa" | La Crypton tiene clutch centrífugo pero no correa: "Se revisa si la moto patina o tiembla al arrancar, o al abrir el motor" | Concepto: lámina de clutch de una moto de cadena, sin CVT | importante | alta |

### Cambios exactos para Planos (lote 2)
1. **F4-4**
   - `(r"DRIVEN|POLEA TRASERA|POLEA CONDUCIDA", "polea_trasera")` solo debe valer en láminas de la CVT (diagrama `cvt` o pieza `correa`).
   - Y, como en `herraje_para`, la primera palabra manda antes que las palabras de taller: WASHER y CIRCLIP van a la tornillería; BUSH al buje; FLANGE a la brida portacorona; GEAR y SEAL del tacómetro a su guía.
   - Cómo comprobarlo: 0 piezas fuera de la CVT con "correa" o "polea" en `que_hace` o `cada_cuanto`, sin contar las amarras.
2. **F4-5**: `despiece_fichas.py:140` ("CLUTCH CARRIER ASSY") y `despiece_guia_mecanica.py:285` ("clutch")
   - Si la lámina no es de la CVT, el "cada cuánto" debe decir "Se revisa si la moto patina o tiembla al arrancar, o cuando se abre el motor".

### Verificación del lote 2 (14-nov-2026): **verificado, con un efecto nuevo (lote 3)**
- Hecho con un volcado nuevo de las 8.481 piezas.
- Resultados:
  - 0 piezas fuera de la CVT con "correa", "polea", "rodillos" o "variador", sin contar las amarras.
  - "WASHER, 1ST DRIVEN" es ya una arandela de la caja; "BUSH, 1ST DRIVEN", un buje; "FLANGE… RR. DRIVEN", el porta corona.
  - "CLUTCH CARRIER ASSY" de la Crypton: "Se revisa si la moto patina…".
  - Chequeos anteriores: criterio 3 en 0; criterio 2 en 28 (2e).

## Lote 3: velocímetro mecánico y tacómetro tratados como sensor electrónico (14-nov-2026)

| Pieza o ficha | Moto(s) | Qué se revisó | Dice hoy | Debería decir | Fuente(s) | Gravedad | Confianza |
|---|---|---|---|---|---|---|---|
| F4-6. Patrón nuevo `(r"TACHOMETER|SPEEDOMETER", "sensor_cable")` en `despiece_guia_mecanica.py:769`, que va antes de "pinon_velocimetro" | CB 125F, XR 150L, Dio, Eco Deluxe ("GEAR, SPEEDOMETER"), Best ("BOX ASSY, SPEEDOMETER") | a. concepto | "Es el sensor de velocidad con su cable: va frente al disco agujereado y cuenta sus huecos" | Velocímetro mecánico: guía "pinon_velocimetro" ("va en la rueda y mueve la guaya del velocímetro"). El sensor electrónico solo aplica a las descripciones con "SENSOR" (AKT, Duke) | Concepto: el catálogo dice GEAR o BOX ASSY, SPEEDOMETER (caja de engranajes de la guaya), no "SENSOR" | importante | alta |
| F4-6b. "GEAR TACHOMETER DRIVEN" y "SLEEVE, TACHOMETER DRIVEN GEAR" | GN 125 (lámina de la culata) | a | El mismo texto del sensor de velocidad | "Es el piñón del tacómetro: lo mueve el árbol de levas y hace girar la guaya del tacómetro (las revoluciones del motor)". Su retenedor va como retenedor | Concepto: va en la culata, movido por el árbol de levas; mide revoluciones, no velocidad | importante | alta |
| F4-6c. "CLAMPER, SPEEDOMETER CABLE" | XR 150L | a | Sensor de velocidad | Abrazadera de la guaya (por primera palabra: CLAMPER = abrazadera) | Concepto (primera palabra) | menor | alta |

### Cambios exactos para Planos (lote 3)
1. Cambiar `(r"TACHOMETER|SPEEDOMETER", "sensor_cable")` por estos tres:
   - `(r"SENSOR.*(VELOC|SPEED)|SPEED SENSOR|(VELOC|SPEED).*SENSOR", "sensor_cable")`;
   - `(r"TACHOMETER", "pinon_tacometro")`, con una guía nueva y el texto de la tabla;
   - `(r"SPEEDOMETER (GEAR|BOX)|GEAR, SPEEDOMETER|GEAR SET, SPEEDOMETER|BOX ASSY, SPEEDOMETER", "pinon_velocimetro")`.
2. Aplicar antes la primera palabra: CLAMPER o CLAMP va a la abrazadera, y SEAL al retenedor.
3. Cómo comprobarlo: ninguna pieza con GEAR o BOX de SPEEDOMETER, ni ninguna TACHOMETER, con "disco agujereado" en `que_hace`.

### Verificación del lote 3 (14-nov-2026): **verificado**
- Hecho con un volcado nuevo de las 8.481 piezas.
- Resultados:
  - 0 piezas GEAR o BOX SPEEDOMETER, ni TACHOMETER, con "disco agujereado".
  - Los sensores electrónicos de AKT y Duke siguen como sensor.
  - Chequeos anteriores: criterio 3 en 0; criterio 2 en 28 (2e).
- **Enlaces nuevos de REGLAS_GLOBALES y REPRESENTATIVAS** (13 cambios, ninguno quitado):
  - Correctos:
    - el retenedor de la barra pasa a `suspension-del` (Gixxer y GN), porque la tarea es "aceite y retenedores";
    - "Element filtr aire" de la Dynamic pasa a `filtro-aire`;
    - la bomba de freno lleva `liquido-frenos` (CR4 y TT), en línea con la decisión 2e;
    - la carcasa de la caja lleva `aceite-caja` (Dio y Dynamic), porque el catálogo no trae el tapón.
  - **Para que decida el usuario:** la tarea `bateria` quedó en accesorios de la batería y no en la batería.
    - Es el caso de "Abrazadera batería" (Boxer f17, que además está en una lámina clasificada como Admisión), "Correa batería" (NKD f216) y "Soporte de la batería" (GN f15), más "CUSHION" (GN f5) para `suspension-tras`.
    - El aviso "Toca ya" saldría sobre una correa o un soporte, que no es lo que se cambia, y el usuario podría pedir el repuesto equivocado.
    - Propuesta: tratarlas como las otras 9 tareas sin pieza ("Sin pieza en el catálogo") en vez de usar un accesorio como representante.
    - Gravedad: importante. Confianza: alta (concepto).

## Lote 4: tareas sobre accesorios y piezas que no vienen en el catálogo (14-nov-2026)

**Criterio del usuario** (14-nov-2026): "Lo dejo a tu criterio": manda el sentido mecánico, la función y la forma se verifican con fuentes y planos, y los esquemas existen para explicar la mecánica de la moto.

**Decisión del Auditor**, con ese criterio: ninguna tarea va sobre un accesorio (correa, soporte o caucho) haciendo de la pieza.
- Si la pieza existe en la moto pero el catálogo no la lista, se agrega como pieza **virtual** en la lámina cuyo dibujo la contiene, igual que ya se hace con la rueda fónica (`_con_rueda_fonica`).
- La pieza virtual se dibuja, lleva su tarea y se rotula "No viene en el catálogo de esta moto".
- Así el esquema sigue explicando el sistema completo y el aviso "Toca ya" cae en la pieza correcta.

| Pieza o ficha | Moto(s) | Qué se revisó | Dice hoy | Debería decir | Fuente(s) | Gravedad | Confianza |
|---|---|---|---|---|---|---|---|
| F4-7. GN f15 r1 "33610-10311" (descripción que es solo un código) | GN 125 | a | Nombre: el código. La tarea `bateria` está en "HOLDER COMP, BATTERY" (r12) | r1 es la **batería** (Battery Assy YB7-A, 12 V 8 Ah): nombre "Batería", tarea `bateria` en r1, y el soporte r12 sin tarea | megazip.net, diagrama Battery del GN125 (33610-10311-000, YB7-A 12 V 8 Ah); revzilla.com, GN125E Battery (consulta: 14-nov-2026) | importante | alta |
| F4-8. Tarea `bateria` en "Abrazadera Batería" (Boxer f17 r12) y en "Correa Bateria" (NKD f216 r12) | Boxer CT 100, NKD 125 | a / plan | El aviso de la batería sale sobre la correa o abrazadera | El catálogo no trae la batería: va una pieza virtual "Batería" en la lámina eléctrica que la dibuja, con la tarea. La correa y la abrazadera quedan sin tarea | Concepto: la correa sujeta la batería; en la revisión de batería no se cambia la correa | importante | alta |
| F4-9. Tarea `suspension-tras` en "CUSHION" (GN f5 r10) | GN 125 | a / plan | El aviso del amortiguador sale sobre un caucho del basculante | Pieza virtual "Amortiguadores traseros" en la lámina del basculante, que ya dibuja los amortiguadores, con la tarea. El CUSHION queda sin tarea | Concepto: el GN 125 lleva dos amortiguadores traseros; el catálogo no los lista en esa lámina | importante | alta |
| F4-10. Las 9 tareas "sin pieza en el catálogo" (`auditar_tareas_despiece`) | Llantas de Best, GN y Dynamic; bujía de Best y Eco; barras de la Dynamic; bandas de la GN | plan / c | El sistema se muestra sin estado | El mismo tratamiento: pieza virtual en la lámina que dibuja ese puesto (llanta, bujía, barra, bandas), con su tarea y el rótulo | Concepto: todas existen en la moto | menor | alta |

### Cambios exactos para Planos (lote 4)
1. **Una función general** en `views._laminas_base`, en lugar de la rueda fónica sola: `_con_piezas_de_tarea(lamina, partes)`.
   - Para cada tarea que aplica a la moto y no tiene pieza en el despiece, si el diagrama de esta lámina tiene el puesto de esa tarea (bateria, amortiguador, llanta, bujia, barra, bandas), agrega una pieza `virtual=True`:
     - `descripcion` en inglés de catálogo ("BATTERY", "SHOCK ABSORBER, RR", "TIRE, FR", "PLUG, SPARK", "FORK, FR", "SHOE SET, BRAKE"), para que tome su puesto y su ficha;
     - `nombre` en español;
     - `tarea_id` de esa tarea;
     - `ref` = el máximo + 1.
   - La guía lleva el contexto: "No viene en el catálogo de esta moto: se compra por su referencia (tipo y medida en el manual)".
   - La rueda fónica pasa a ser un caso más de esta función.
2. **Quitar la tarea** de "Abrazadera Batería" (Boxer f17 r12), "Correa Bateria" (NKD f216 r12), "HOLDER COMP, BATTERY" (GN f15 r12) y "CUSHION" (GN f5 r10), con `null` en el mapa.
3. **GN f15 r1** ("33610-10311"):
   - nombre "Batería";
   - descripción guardada como "BATTERY ASSY (33610-10311)" o regla en el mapa;
   - tarea `bateria`.
4. **Cómo comprobarlo:**
   - `auditar_tareas_despiece` con 0 tareas sin pieza;
   - ninguna tarea `bateria` ni `suspension-tras` sobre una pieza cuya primera palabra sea abrazadera, correa, soporte, caucho, cushion o holder;
   - en el visor, la pieza virtual se dibuja y lleva el rótulo.

### Verificación del lote 4 (14-nov-2026): **verificado**
- **Tareas en accesorios:** 0 piezas con `bateria` o `suspension-tras` cuya primera palabra sea abrazadera, correa, soporte, caucho, CUSHION (sin ASSY), holder o tirante.
- **Piezas virtuales:** 10 ("No aparece en los planos"), cada una en la lámina que dibuja su puesto y con su tarea.
  - Visto en la NKD f216: la batería va dibujada (x = 0,91), con `_tarea` y con el texto de contexto.
- **GN f15 r1:** "Batería", con la tarea `bateria`.
- **Quedan 2 tareas sin pieza, porque ninguna lámina dibuja ese puesto:**
  - la batería de la Boxer (sus piezas están en f17, Admisión, y no tiene lámina eléctrica con batería);
  - las barras de la Dynamic (no tiene lámina de suspensión delantera).
  - Se aceptan como abiertas: inventar una lámina iría contra la regla de no inventar.
- **Chequeos anteriores:** criterio 3 en 0; criterio 2 en 28 (2e).
- **Boxer "Kit Bujes Amortiguador Tras." con `suspension-tras`:** por sentido mecánico se acepta. Los bujes (silentblocks) de los anclajes se revisan y se cambian con el amortiguador, y el amortiguador también lleva la tarea.
  - Detalle menor de nombre: "Kit bujes amortiguador trasera" → "Kit de bujes del amortiguador trasero".

## Lote 5: revisión de la Yamaha Aerox 155 (BVT2) y efectos de sus frases en otras motos (14-nov-2026)

**Verificado en la Aerox:**
- **Contraste con el PDF:** las 437 filas de la base están en el catálogo. Las únicas que mi script no lee son los 2 rines con sufijo de color (-P7/-P8). Ninguna figura importada tiene filas de menos.
- **Sistemas:** los 11 de una CVT con refrigeración líquida, sin kit de arrastre.
- **Datos de la moto con fuentes:**
  - refrigeración líquida (motorradundreisen.de y elcarrocolombiano.com, consulta 14-nov-2026; el catálogo trae radiador y bomba de agua);
  - freno trasero de tambor (lámina 24 del catálogo del fabricante).
- **Tareas:**
  - todas tienen pieza;
  - `aceite` en el o-ring del tapón de drenaje con colador (f7 r6) y en el del tapón de nivel (f10 r15);
  - `aceite-caja` en la junta del tornillo de drenaje de la transmisión final (f10 r11);
  - `correa-cvt` en correa, rodillos y zapatas;
  - `refrigerante` en el radiador y la tapa.
- **Nombres:** 0 sellos con nombre a secas en el visor. Primera palabra: 0.
- **Dibujos:** variador, correa y clutch (f12) coherentes. La bomba de agua (f5) aparece en el circuito del radiador.

| Pieza o ficha | Moto(s) | Qué se revisó | Dice hoy | Debería decir | Fuente(s) | Gravedad | Confianza |
|---|---|---|---|---|---|---|---|
| F4-11. Nombre "Colador del aceite" para el filtro de papel | Crypton ("ELEMENT ASSY, OIL CLEANER"), GN y Gixxer ("FILTER, ENGINE OIL"), AKT ("Filtro de Aceite"): 8 piezas | a. concepto | "Colador del aceite" (antes decía "Filtro de aceite") | "Filtro de aceite". El colador (malla que se lava) es solo STRAINER, MALLA o CEDAZO. El filtro de papel se cambia con el aceite | Concepto: el catálogo dice ELEMENT o FILTER, no STRAINER | crítico | alta |
| F4-12. Dueño del guardapolvo tomado de la pieza vecina aunque la descripción lo nombra | Varias Yamaha y Honda | a / nombre | "BOOT, PIN BUSH" → "Guardapolvo del pistón"; "BOOT, REAR SHOCK ABSORBER" → "…del basculante"; "SEAL, WHEEL DUST" → "…del disco de freno"; "SEAL, FRONT HUB DUST" → "…del separador delantero"; "COVER, DUST" → "…de la reparacion" | "Guardapolvo del pasador del caliper", "…del amortiguador trasero", "…de la rueda", "…de la manzana delantera", y el de COVER, DUST según su puesto (nunca "reparacion") | Concepto (lo dice la propia descripción) | importante | alta |
| F4-13. Falta la figura 11 "CUBIERTA DE CARTER 1" (tapa de la CVT) | Aerox; también la NMAX, que no tiene su tapa de la CVT | c. componentes | No hay lámina | Importarla: trae ELEMENTO 1 (el filtro de aire de la caja de la correa), el respiradero y sus sellos. Enlazar el elemento a `correa-cvt` | Yamaha incluye el "V-belt case air filter element" en el cuadro de mantenimiento periódico (manuales de la NMAX 155 y de la Aerox GDR155, manualslib, consulta 14-nov-2026) | importante | alta |
| F4-14. Guía del retenedor con "piñón de salida, palanca de cambios" en scooters | Aerox f10 (2), y también en otras CVT | b. texto | "sella donde un eje sale del motor (piñón de salida, palanca de cambios)" | En una CVT: "sella donde un eje sale del motor (cigüeñal del lado del variador o del generador, eje de la rueda)" | Concepto: una scooter no tiene piñón de salida ni palanca de cambios | menor | alta |

### Cambios exactos para Planos (lote 5)
1. **F4-11:** en `_FRASES`, la regla "colador" solo para STRAINER, MALLA o CEDAZO. ELEMENT (OIL CLEANER) y FILTER (ENGINE OIL) vuelven a "Filtro de aceite". Cómo comprobarlo: 0 piezas ELEMENT o FILTER con nombre "Colador".
2. **F4-12:** al buscar el dueño de un guardapolvo o empaque, la descripción manda si nombra la pieza (PIN BUSH, REAR SHOCK ABSORBER, WHEEL, FRONT HUB, BRAKE CAM…). El puesto o la pieza vecina solo se usan si no la nombra.
3. **F4-13:** agregar la figura 11 al mapa de la Aerox, con diagrama `cvt` o carcasa, y la equivalente en la NMAX ("CRANKCASE COVER 1"). Regla: ELEMENTO / ELEMENT de esa lámina → `correa-cvt`.
4. **F4-14:** la guía del retén depende del tipo de transmisión.

### Verificación del lote 5 (14-nov-2026): **verificado**
- Hecho con un volcado nuevo de las 8.974 piezas (25 motos).
- **Nombres:**
  - 0 filtros de papel (ELEMENT, FILTER) llamados "colador"; el colador de la Aerox f7 sí se llama "Colador del aceite".
  - Guardapolvos con su dueño: "…del pasador del caliper" (CB), "…del amortiguador trasero" (FZ 25), "…de la rueda" y "…de la manzana delantera" (Gixxer).
- **Figura 11 importada en la Aerox y la NMAX:** "Filtro de aire de la caja de la correa", enlazado a `correa-cvt`.
- **Retenedor en las CVT:** 0 guías que digan "piñón de salida". El grupo "cadena en scooter" quedó en 0.
- **Chequeos anteriores:** criterio 3 en 0; criterio 2 en 29 (los 28 casos 2e, más la tapa del depósito de la Aerox, que es el mismo caso 2e).

## Capa 3: intervalos por moto (en curso)
- **Dónde están hoy:** no hay intervalos por moto en el código. Son 19 tareas genéricas en `TareaMantenimiento`, iguales para todas las motos.
- **Reparto:**
  - el "Auditor mecánico" saca las cifras de los manuales del propietario (con URL y fecha) y las deja en `side-session-notes/…/capa3-<moto>.md`, empezando por la NMAX;
  - el Auditor las cruza con el plan y las fichas.
- **Si hay que guardarlas por moto:** hace falta un modelo nuevo o un archivo de datos. Lo decide el usuario, y la migración la hace "Modelos 3d".
- **Decisión del usuario** (vía Auxiliares, 14-nov-2026): los intervalos por moto van en **archivos del repo**, uno por línea, no en la base de datos.
  - "Garaje" arma el mecanismo en `plan.py` y avisa el formato.
  - El Auditor y el Auditor mecánico llenan los archivos: cifras del manual, con `fuente` y la marca `aproximado` cuando no sean dato exacto.
  - Si a una moto le falta un dato, se usa el plan general.

### Estado de la capa 3 (14-nov-2026)
- **Archivos llenos y validados en `garaje/intervalos/`:** 9 motos.
  - Con manual oficial: NMAX (B6Y4, misma plataforma), FZ 25, XTZ 125, CB 125F (Twister, en español), Aerox (BVT, colombiana) y Crypton FI (T115FL-5, BF2).
  - Aproximados: NS 200 y Boxer (manuales de Bajaj India BS6) y NKD (manual escaneado, sin cuadro).
  - Las demás motos usan el plan general.
- **Cómo se leyeron los cuadros:** por coordenadas, sin abrir el PDF como imagen.
  - En los manuales Yamaha, el glifo "√" de la fuente Symbol (script `cuadro_casillas.py`); falla en el de la FZ 25, que se leyó a ojo.
  - En los Bajaj, letras por columna (CL, A, R, C).
  - En los Honda, figuras vectoriales: gris = revisar, oscura = cambiar (script `honda_cuadro.py`).
  - Lo dudoso lo confirmó a ojo el Auditor mecánico.
- **Fuente única, verificada con un volcado de 9.446 piezas:**
  - todas las piezas con tarea muestran "…, según el plan de tu moto." con el intervalo y la especificación del archivo de su línea, sin otras cifras;
  - de las filas sin tarea de conceptos del plan, queda 1 con cifras propias: Discover "Batería de gel".
- **Formato:** km o días en null usan el general en esa dimensión; 0 significa sin límite.

### Capa 3: segunda ronda (14-nov-2026), con 14 manuales más entregados por el usuario
- **Archivos en `garaje/intervalos/`:** 23 de 25 líneas, todos validados (`ArchivosIntervalosTests`).
- **Faltan:** la MT-03 (el manual que llegó es de la 660 vieja) y la Wave 110S.
- **Con manual oficial del modelo:**
  - NMAX, FZ 25, XTZ 125, CB 125F, Aerox, Crypton FI, Dio 110, XR 150L, Best 125, TT 125, Dynamic Pro, Eco Deluxe y CR4;
  - Discover y RS 200: manual del modelo; el aceite va aproximado por la regla del aceite especial de Bajaj;
  - Gixxer: versión de carburador 2015–2019.
- **Aproximados:**
  - NS 200 y Boxer: manuales indios BS6;
  - NKD, GN 125 y Gixxer FI ABS (desde 2020): referencia del manual de la 2015;
  - KTM Duke y RC: manual de 2024 frente al catálogo de 2019;
  - Apache: el manual es de la 4V; solo se usan la presión, la cadena y el líquido de frenos.
- **Cómo se leyeron los cuadros nuevos:**
  - Bajaj (Discover, RS 200): letras por columna, con `bajaj_cuadro.py`. Las filas clave de la RS 200 vienen como texto en la columna de observaciones.
  - Honda (Dio, XR): figuras vectoriales, con `honda_cuadro.py`.
  - KTM: símbolos ● y ○, con las columnas sacadas de la posición de los símbolos.
- **Criterio aplicado a la cadena:** cuando el manual la atiende cada 1.000–5.000 km, sin O-ring y con uso diario con lluvia (Boxer, Discover, Best, GN, Eco Deluxe, Gixxer), se deja el intervalo general de lubricación (600 km / 15 días) y la cifra del manual queda en las notas. La XR (1.000 km, Honda oficial) y las Yamaha (500 km) conservan la suya.
- **Versiones por año:** formato `versiones` de Garaje, con los cortes en los años de los despieces (Gixxer: 2015–2019 y 2020 en adelante).
