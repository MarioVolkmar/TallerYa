# Revisión mecánica: plan, fichas, guía y diagnóstico (2026-11-15)

Alcance: las 33 líneas, incluidas las 8 nuevas. No toqué el 3D, `diagramas.py` ni el chat de Chispa. Nada tiene commit.
Pruebas: Despiece, GuiaPiezas, GuiaCompleta, SistemasDespiece, DespiecePorAnio, tests_diagnostico y tests_avisos → 73 OK.

## Idea central de los cambios
Las fichas y la guía mecánica traían **cifras fijas para todas las motos**: válvulas "cada 6.000 km", barras "cada 20.000 km", refrigerante "cada 2 años", bujía "cada 8.000 km", etc. Esas cifras contradecían el plan de muchas motos. Ejemplos: las válvulas de la MT-03 van a 42.000 km y las de la Aerox a 12.000; el refrigerante de las KTM va cada 4 años; las barras de la FZ 25 van a 10.000 km y las de la Hunk a 30.000.
Cuando una pieza tiene tarea en el plan, la vista ya cambiaba el texto por la cifra del plan. Las demás piezas de la misma zona seguían mostrando la cifra genérica. Ahora todas dicen **"cuando lo pide el plan de tu moto"**, y donde ayuda, con el rango real entre modelos. Así hay una sola fuente de cifras: `garaje/intervalos/*.json`.

## Qué cambió
**`garaje/despiece_fichas.py`**
- Válvulas, tornillo de calibrar, tapa de válvulas y balancín: sin "6.000 km"; remiten al plan. Además, "muy apretada" ahora se explica: sin holgura la válvula no cierra del todo y se quema; con holgura de más suena y pierde fuerza.
- Correa, rodillos, deslizadores y zapatas del clutch: sin "12.000 km"; se revisan con la correa, según el plan.
- Barras (aceite, resorte, cilindro y botella): sin "20.000 km"; según el plan (10.000 a 30.000 km según el modelo).
- Refrigerante, radiador, su tapa y el drenaje: sin "2 años" fijos (las KTM van cada 4).
- Líquido de frenos: quitado "o 20.000 km", porque la mayoría de manuales lo piden solo por tiempo. En el depósito decía "normalmente DOT 4"; ahora dice "DOT 3 o DOT 4, según la tapa" (Honda y Hero usan DOT 3).
- Tapón de drenaje: "lo que se cambia es su arandela o empaque, no el tapón". Antes decía "cada 2.500 km".
- Filtro de aire:
  - Antes: "los filtros de papel no se lavan ni se soplan". Eso contradecía el consejo para el filtro seco (Boxer CT 100, Eco Deluxe), que sí se sopla suave.
  - Antes: "míralo a contraluz". Eso está mal para el viscoso, que nunca deja pasar luz.
  - Ahora explica los tres tipos: espuma, papel con aceite y papel seco.
- Bomba del freno trasero: decía "manigueta izquierda", que solo vale en las scooter. Ahora dice "pedal" (o manigueta en las scooter).
- Quitadas dos menciones a la NMAX que salían en todas las motos ("en la NMAX viene en la descripción").
- Batería: "inyección" solo si la moto la tiene. Gramática de "baterías de gel".

**`garaje/despiece_glosario.py`**: los mismos arreglos en las ayudas cortas: bomba trasera, barras, batería, y el filtro de papel con aceite, que no se limpia.

**`garaje/despiece_guia_mecanica.py`**
- Cadena: decía "cada 500 km"; ahora "según el plan (500 a 1.000 km) y después de lluvia".
- Bujía, válvulas, tapa de válvulas, correa, filtro y aceite de barras: según el plan.
- Filtro: "míralo contra la luz" corregido para el viscoso.
- Refrigerante: nivel cada semana, igual que en las fichas (antes una decía cada mes y la otra cada semana).
- Bornes de la batería: cada 6 meses, igual que en las fichas (antes una decía 3 meses y la otra 6).

**`garaje/views.py`** (2 líneas)
- `_FILTRO_AIRE_POR_LINEA`: la XTZ 150 queda como "sin confirmar". Su plan pide limpiar el filtro entre cambios, pero el respaldo por marca (Yamaha = viscoso) le habría dicho "no se limpia".
- Cuando la ficha toma la cifra del plan, ya no repite una frase que también dice "plan de tu moto".

**`garaje/diagnostico.py`**
- "Galgas" ahora dice "calibrador de láminas (galgas)", como en las fichas.
- "Sprocket" ahora dice "corona (sprocket)", como en el plan.
- El juego de la cadena remite a la medida de cada moto.
- La correa "se cambia cuando lo pide el plan".
- El juego del clutch ahora es "en la mayoría, 10 a 20 mm".

## Plan de mantenimiento: revisado, sin cambios de cifras
Revisé la tabla de las 33 líneas: claves, km, días y fuentes. Todas las cifras traen fuente y página, así que no cambié ninguna. Los nombres de tarea son únicos porque vienen de la base de datos, así que son iguales en todas las motos.

## Queda para decisión del usuario (dudoso, sin tocar)
1. **Lubricar la cadena: dos criterios**
   - Hunk 125R, Hunk 150, XR 150L, XR 190L y DR 150 usan los 1.000 km del manual.
   - Best 125, GN 125, Eco Deluxe, Raider, Boxer y Discover usan el general de 600 km, "más corto por lluvia".
   - Conviene unificar. Propuesta: el general de 600 km para todas, con la cifra del manual en las notas.
2. **Filtro de aire de la Best 125 y la GN 125**: los 4.000 km son de *limpieza*, pero la tarea se llama "Cambio de filtro de aire". Las notas lo aclaran. Opciones:
   - poner el km de cambio, si aparece en el manual;
   - o renombrar la tarea a "Revisión y cambio de filtro de aire". Esto exige una migración de datos.
3. ~~NMAX contra Aerox~~ → resuelto abajo, en "Verificación con manuales".
4. ~~DR 150, manguera de freno~~ → resuelto abajo.
5. ~~DR 150, filtro~~ → resuelto abajo.
6. ~~Tipo de filtro~~ → resuelto en parte abajo.
7. **Catálogos en español** (AKT, Bajaj, Hero, Suzuki, TVS): las fichas por nombre están en inglés (Yamaha/Honda). Esas motos dependen de la guía mecánica por puesto del dibujo, que es de la sesión de Planos. Falta una revisión pieza a pieza con datos de la base, que no pude leer desde esta sesión.

## Verificación con manuales (segunda pasada, 15-nov-2026)
Fuentes: los manuales en `manual_despiece/`. Leí las tablas con pdftotext; los chulos de Yamaha solo se ven en imagen, así que esas páginas las rendericé. Después de los cambios, `garaje.tests` (105) y ArchivosIntervalosTests pasan OK.

**3. NMAX y Aerox: las cifras son correctas.** La diferencia viene de los manuales, no de un error de lectura.
- NMAX (manual del propietario B6Y4 2022, Argentina, p. 9-2): válvulas en todas las columnas, es decir cada 6.000 km; bujía cada 10.000 km o 12 meses; correa cuando parpadea el indicador V-BELT, cada 18.000 km.
- Aerox (manual BVT colombiano, cap. 10): válvulas solo en la columna de 7.000 km y el ciclo se repite desde los 16.000, es decir cada 12.000 km; bujía también a los 7.000 y luego cada 12.000; correa a los 25.000 km.
- No hay manual colombiano de la NMAX en la carpeta. Si aparece, conviene compararlo.
- No cambié nada.

**4. DR 150, manguera de freno: el propio manual se contradice.** La tabla de la p. 2-1 dice "cambiar cada 10.000 km"; el texto de frenos dice "cambiar cada 4 años". La nota de `suzuki_dr_150.json` ahora cita las dos cosas: lo que llegue primero.

**5. DR 150, filtro: es viscoso.** La p. 2-5 dice que es de papel engrasado y que no se limpia ni se le aplica aire comprimido: si está sucio, se cambia. La "limpieza" de la tabla se entiende como revisarlo y limpiar la caja y su drenaje. Se corrigió la nota y la DR 150 quedó como `viscoso`.

**6. Tipo de filtro** (en `_FILTRO_AIRE_POR_LINEA` de `views.py`):

| Moto | Tipo | Fuente |
|---|---|---|
| Hunk 125R | viscoso | Manual Perú 2025, p. 65: "papel viscoso plegado; nunca lave ni limpie". Nota añadida al JSON |
| XR 190L | viscoso | Manual del propietario LA 2016 |
| FZ 2.0 | viscoso | Manual FZ-S FI V3.0 2022: "papel revestido de aceite; se debe cambiar" |
| DR 150 | viscoso | Ver el punto 5 |
| Best 125 | seco | Manual, p. 21: elemento de papel que se limpia cada 4.000 km. Nota del JSON aclarada |
| Raider 125 | sin confirmar (se deja así) | Manual TVS India 2026: espuma y papel combinados, que se cambian, no se lavan. Nota del JSON corregida; antes decía "se limpia" |

**Pendiente, sin dato en ningún documento de la carpeta** (siguen como "sin confirmar"):
- **Hunk 150**: solo hay catálogo. Por su familia probablemente es viscoso, como la 125R, pero no está confirmado.
- **Discover 125**: el manual solo dice "clean the air filter element periodically".
- **GN 125**: el PDF es escaneado, sin texto.
- **XTZ 150**: el PDF solo trae la garantía.

## Decisiones del usuario aplicadas (15-nov-2026)
**1. Lubricar la cadena: 600 km en todas las líneas.**
- Las 28 líneas con `cadena-lubricar` en su archivo de intervalos quedan con km 600. A las que no la tienen les rige el general, que también es 600 km.
- La nota de cada una cita lo que dice su manual. Por ejemplo: «Manual: cada 1.000 km. Usamos 600 km, más seguido, por la lluvia y el uso diario».
- La fuente de cada una dice que la cifra es una unificación de TallerYa.
- **Para tener en cuenta:** en 12 líneas el manual pide **500 km** (NKD, Boxer CT 125, NS 200, RS 200, CB 125F, Wave, Crypton, FZ 2.0, FZ 25, Apache, XTZ 125 y XTZ 150). Para ellas los 600 km quedan algo por encima de lo que pide el fabricante. Su nota añade «si llueve o la lavas, lubrícala ese mismo día».
- La guía mecánica de la cadena ahora dice «cada 600 km».

**2. Nombre de la tarea: «Revisión y cambio de filtro de aire».**
- La tarea es una sola para todas las motos, así que el nombre nuevo aplica a todas, no solo a la Best y la GN. Es correcto para todas: el filtro siempre se revisa y se cambia según su estado o su plan.
- La migración `garaje/migrations/0034_nombre_tarea_filtro_aire.py` solo cambia el nombre de la tarea con clave `filtro-aire`, y es reversible. Como no cambian ni la clave ni el id, no se pierden el historial, los ajustes ni los registros de «ya lo hice».

**Coherencia revisada:**
- Plan, «Lo urgente» y la guía de pieza toman el nombre de la base de datos y el km del archivo de intervalos, así que se actualizan solos.
- El chat de Chispa (`ayuda/`) no tiene cifras de cadena ni de filtro escritas a mano: nombra la tarea a partir del plan.
- No quedan menciones a «Cambio de filtro de aire» en el código.

**Pruebas:** las de garaje pasan (230 OK) y la suite completa también (526 OK).
