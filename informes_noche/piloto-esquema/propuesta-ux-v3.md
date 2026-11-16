# Propuesta UX v3 del esquema: más amigable para el motero

Revisora UX · 16-nov-2026. Es una propuesta para que el usuario decida. Las ideas marcadas «va» están montadas en un prototipo sobre la fig. 26 (`motor/prototipo-v3/`), sin tocar el motor.

**Para quién:** un motero no técnico, con el celular en la mano y a veces con la moto varada. No sabe cómo se llama la pieza; sabe **qué nota** («la manigueta se siente blanda», «gotea algo cerca de la rueda»).

**Referencias:**
- **Visores de despiece de concesionario** (catálogos con figura y lista): sirven para encontrar una pieza que ya sabes nombrar, no para quien solo sabe lo que nota.
- **Guías paso a paso tipo iFixit:** un paso por pantalla, lo que vas a necesitar al principio, avisos de seguridad que no se esconden.
- **Apps de diagnóstico de carros (lector OBD con app):** dicen primero **qué tan grave es** y si puedes seguir rodando, después el detalle.
- **Hojas inferiores de mapas y apps de transporte:** se abren a media altura sin tapar lo que tocaste, se arrastran para ver más y se cierran deslizando.
- **Buscadores de síntomas de salud:** buscas con tus palabras y el resultado te dice qué puede ser y qué hacer ya.

**Filtro:** cada idea pasa por `criterios-del-usuario.md`. **Va** quiere decir que cumple del 1 al 10, mejora la claridad para el motero en el celular y cuesta poco por lámina. **Opción** quiere decir que duda en algo: la decide el usuario.

**Ya en curso** (los pidió el usuario y los hace piloto-esquema en el motor; aquí no se repiten): píldoras más chicas, enlaces sutiles, Pedir y Talleres compactos, hoja inferior en vez de «Ver ficha» y la certeza dentro del texto.

## Resumen
| # | Idea | Para qué | Costo por lámina | Decisión |
|---|---|---|---|---|
| 1 | **Buscar por lo que notas**: el buscador también busca en las señales de falla y muestra la frase que coincide | Ir de «tengo este síntoma» a «es esta pieza» en 2 toques | 0 (usa las señales que ya tiene cada ficha) | **va** |
| 2 | **Resumen de una línea en la ficha**: «Se cambia · Mejor en el taller · Cada 2 años» bajo el nombre | Entender en 5 s qué hacer | 0 (sale de campos existentes) | **va** |
| 3 | **«¿Varado?» discreto en la cabecera**, que lleva a emergencias (talleres abiertos y grúas) | La persona con la moto quieta encuentra ayuda en 1 toque | 0 | **va** |
| 4 | **Talleres de verdad**: «Talleres» lleva a los talleres del servicio de la lámina (p. ej. frenos), y «¿No sabes qué pieza es?» lleva al diagnóstico del sitio | Conectar el esquema con TallerYa | 1 dato por lámina (el servicio) | **va** |
| 5 | **Microinteracciones mínimas**: la pieza elegida late una vez; un aviso de lectura de pantalla dice qué se abrió | Saber qué tocaste sin buscar | 0 | **va** |
| 6 | **Teclado y foco**: Esc vuelve a la vista general, ← → recorren piezas, el foco se ve | Accesibilidad sin ruido visual | 0 | **va** |
| 7 | **Semáforo «¿puedes seguir rodando?»** (sigue con cuidado / ve pronto al taller / no ruedes) en cada ficha | Lo primero que pregunta alguien varado | 1 palabra por pieza, revisada por la mecánica | opción |
| 8 | **«¿Lo puedes hacer tú?»** con tiempo y herramientas (destornillador, llave 10, 15 min) | Decidir entre hacerlo o llevarla | 1 línea por pieza | opción |
| 9 | **Glosario al tocar** (p. ej. «cáliper» → definición corta, sin salir de la ficha) | Lenguaje para no técnicos | 0 si se usa el glosario del sitio, pero agrega enlaces | opción |
| 10 | **Primer uso guiado** (una pista que señala una marca y se va al primer toque) | Los 5 primeros segundos | 0 | opción |
| 11 | **Deslizar entre piezas dentro de la hoja inferior** | Recorrer piezas con el pulgar | 0 | opción |
| 12 | **Recordar la última pieza vista** al volver a la lámina | Retomar la consulta | 0 | opción |
| 13 | **Vibración corta al tocar** (solo Android) | Confirmación táctil | 0 | opción |
| 14 | **Agrandar sola el área de toque de las piezas muy chicas** (trazo invisible) | Las arandelas y tapas de 6 a 13 px | 0 | opción |

## Las que van, en detalle

### 1. Buscar por lo que notas (prioridad 1)
- **Qué:**
  - El buscador de la lista también busca en las «Señales de que falla» de cada ficha.
  - Si escribes «blanda», «gotea» o «chilla», aparecen las piezas cuya señal coincide, con la frase debajo en gris («La manigueta se siente blanda o llega casi al puño»).
  - El texto de ejemplo del buscador dice «Pieza o lo que notas: gotea, blanda…».
  - Sin resultados, sale «¿No sabes qué pieza es? Prueba el diagnóstico» (idea 4).
- **Por qué:** el motero sabe lo que siente, no el nombre de la pieza. Hoy hay que adivinar el grupo. Es el camino más corto: síntoma → pieza → qué hago (resumen de la idea 2).
- **Cumple los criterios:** no agrega elementos (usa el buscador que ya hay), habla en segunda persona y cuesta 0 por lámina.
- **Impacto esperado:** de 3 a 5 toques adivinando grupos, a 2 (escribir + tocar el resultado).

### 2. Resumen de una línea en la ficha (prioridad 1)
- **Qué:** bajo el nombre de la pieza, una línea chica con lo que más importa, en el tono del sitio: **Se cambia** · Mejor en el taller · Cada 2 años.
  - Sale de «¿Se repara o se cambia?», de quién lo hace y de la primera frase de «Cuándo».
  - Si un dato no está, no se muestra.
- **Por qué:** en 5 segundos sabes qué hacer sin leer la ficha entera. Las apps de diagnóstico de carros ponen eso primero.
- **Cumple los criterios:** es chica y discreta, y conserva «¿Se repara o se cambia?» (que sigue abajo con su explicación).
- **Impacto esperado:** la decisión se ve sin desplazarse, también en la hoja inferior a media altura.

### 3. «¿Varado?» discreto (prioridad 1)
- **Qué:** un enlace chico en la cabecera de la lámina, «¿Varado? Talleres y grúas cerca ›», que va a `/emergencias/`. Es texto, no botón: no compite con el dibujo.
- **Por qué:** quien entra con la moto quieta no quiere aprender, quiere ayuda. Hoy tendría que salir de la lámina y buscar.
- **Impacto esperado:** ayuda en 1 toque desde cualquier lámina.

### 4. Conectar con TallerYa (prioridad 2)
- **Qué:**
  - «Talleres» abre los talleres del servicio de la lámina (`/talleres/servicio/frenos/` en las láminas de freno), en vez de un enlace genérico.
  - En el buscador sin resultados, «Prueba el diagnóstico» va a `/diagnostico/`, que ya existe en el sitio.
  - Se configura con un dato por lámina (el servicio).
- **Siguiente paso** (cuando se integre al garaje): «Ya lo hice: regístralo en tu plan», el mismo flujo que «Ya lo hice: registrar» del despiece actual.
- **Impacto esperado:** de «qué es» a «quién me lo arregla» sin salir del recorrido.

### 5. Microinteracciones mínimas (prioridad 2)
- **Qué:**
  - La pieza elegida late una vez (0,4 s).
  - Al entrar a un grupo, un aviso oculto para lectores de pantalla dice «Bomba: 6 piezas. Toca una para ver su ficha».
  - Con «reducir movimiento» no hay latido.
- **Por qué:** en el celular el dedo tapa lo que toca; el latido confirma cuál quedó elegida sin agregar elementos.

### 6. Teclado y foco (prioridad 2)
- **Qué:**
  - Esc vuelve a la vista general.
  - ← → recorren las piezas (las mismas flechas anterior / siguiente de la ficha).
  - El foco se ve en las marcas, en la lista y en los botones (contorno mostaza de 2 px).
- **Por qué:** cumple WCAG (foco visible, todo operable con teclado) sin cambiar nada de lo que se ve con el dedo.

## Las que quedan como opción (las decide el usuario)
- **7. Semáforo «¿puedes seguir rodando?»:** es lo más útil para alguien varado.
  - **Duda:** exige un dato por pieza que debe revisar la mecánica. En frenos casi todo es «no ruedes», y equivocarse es grave.
  - **Si va:** que lo escriba la sesión de mecánica y que nunca reemplace los avisos de seguridad.
- **8. «¿Lo puedes hacer tú?»:**
  - **Duda:** el costo por lámina (tiempo y herramientas por pieza). «Mejor en el taller» ya cubre la mitad.
- **9. Glosario al tocar:**
  - **Duda:** agrega enlaces dentro del texto, que el usuario quiere sutiles.
  - **Si va:** solo con subrayado punteado gris y una vez por ficha.
- **10. Primer uso guiado:**
  - **Duda:** puede sentirse como ruido. Con las marcas con nombre quizá no haga falta.
  - **Para decidir:** medirlo con 3 personas.
- **11. Deslizar entre piezas en la hoja:**
  - **Duda:** choca con el gesto de cerrar la hoja deslizando. Esperar a que la hoja inferior esté hecha.
- **12. Recordar la última pieza vista:**
  - **Duda:** útil solo si la gente vuelve a la misma lámina; hoy no se sabe.
- **13. Vibración corta:**
  - **Duda:** puede molestar, y en iPhone no funciona.
- **14. Agrandar sola el área de las piezas chicas:**
  - **Duda:** es un cambio del motor (lo debe hacer piloto-esquema) y puede robarle toques a la pieza vecina. Medir con `medir_lamina.py` antes de adoptarlo.

## Seguridad y confianza
- **Seguridad:** ninguna idea acorta avisos ni pasos de cierre (criterio 9). El resumen de la idea 2 no reemplaza «¿Se repara o se cambia?»; lo anticipa.
- **Confianza:** la certeza va dentro del texto, como pidió el usuario, y ya la hace piloto-esquema. Una mejora más, como opción para después: cuando una frase es aproximada, que lo diga con palabras («aprox.»), sin iconos ni bloques.

## Cómo medir si funcionó
- **Lo que mide `medir_lamina.py`:** toques hasta la ficha (criterio 1) y largo de la ficha (criterio 3); el prototipo no debe empeorar los criterios 6 y 8 a 12.
- **Prueba con personas (3 moteros, 10 minutos):**
  - «Tu manigueta está blanda: ¿qué pieza puede ser y qué haces?»
  - Medir los toques y si encuentran «se cambia / taller».
  - Meta: 2 de 3 en menos de 30 s.

## Prototipo de las ideas «va» (montado sobre la fig. 26 adoptada)
Está en `motor/prototipo-v3/` y envuelve el motor sin cambiarlo:
- `fig26.html` carga `../esquema.js` y suma `prototipo.css` y `prototipo.js`, con 3 KB y 9 KB de código propio;
- se configura con `window.P3_CFG = {servicio: "frenos"}`;
- para montarlo sobre otra lámina, se copia la página y se cambian el JSON, el arte y el servicio.

Qué hace, comprobado en el navegador:
- **1. Buscar por lo que notas:**
  - «blanda» → Bomba delantera, con «La manigueta se hunde hasta el puño…».
  - «gotea» → bombas y mangueras.
  - «chilla» → manigueta.
  - «luz» → interruptores.
  - Sin resultado → «¿No sabes qué pieza es? Prueba el diagnóstico ›».
  - Usa un diccionario corto de palabras de calle (blanda, gotea, chilla, dura…), el mismo para todas las láminas.
- **2. Resumen:** «Se repara · Mejor en el taller · Cada 2 años», en la ficha y en la hoja inferior.
- **3. «¿Varado?»:** en la esquina de la cabecera. En el celular dice solo «¿Varado? ›», para no montarse sobre la cinta, y va a `/emergencias/`.
- **4. Enlaces:** «Talleres» → `/talleres/servicio/frenos/`.
- **5. Microinteracciones:** latido de la pieza elegida y aviso para lector de pantalla («Kit de reparación delantero. Se cambia · Mejor en el taller · Cada 2 años»).
- **6. Teclado:** → pasa a la pieza siguiente y Esc vuelve a la vista general. El foco se ve en mostaza.

### Medidas (`medir_lamina.py`, 6 anchos)
| | 6 | 8 | 9 | 10 | 11 | 12 | Medible | A ojo (1,2,3,4,5,7) | **Total** |
|---|---|---|---|---|---|---|---|---|---|
| Fig. 26 adoptada (`bomba-freno.html`) | 4 | 4,7 | 5 | 5 | 4,8 | 4,8 | 4,72 | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,61** |
| Prototipo v3 (`prototipo-v3/fig26.html`) | 4 | 4,7 | 5 | 5 | 4,8 | 4,8 | 4,72 | 5 · **5** · 5 · **4,5** · 4 · 4,5 | **4,69** |

**El prototipo no empeora nada de lo medible.**
- La hoja inferior pasa del 12 al 17 % de la pantalla con el resumen, y sigue sin tapar la pieza elegida.
- A 1280, «Desarmar» sigue a la vista al entrar a un grupo, porque «¿Varado?» no agrega alto.

Sube a ojo en dos criterios:
- **descubribilidad** (2): buscar por síntoma y «¿Varado?»;
- **accesibilidad** (4): teclado, foco y avisos.

El camino «tengo este síntoma → qué pieza es y qué hago» queda en escribir una palabra y 1 toque, y el resumen dice qué hacer sin bajar.

**Las dos páginas, la adoptada y el prototipo, comparten lo que les queda por mejorar:**
- Piezas chicas a 360: 2 (22 px), 4 (21 px), 24 (21 px) y 44 (16 px).
- Para ver la ficha completa en el celular hacen falta 3 toques: grupo, pieza y «Ver ficha».

### Rutas
- Página: `motor/prototipo-v3/fig26.html` (por HTTP).
- Archivo único para el celular: `motor/prototipo-v3/prueba-p3-fig26.html` (913 KB, con three.js para el 3D). Se arma con `armar_un_archivo_p3.py`.
- Capturas (escala 0,5):
  - `p3-general-1280.jpg` y `p3-general-390.jpg`;
  - `p3-ficha-1280.jpg` y `p3-ficha-390.jpg` (en el celular, la hoja inferior con el resumen);
  - extra: `p3-busqueda-390.jpg` («blanda»).
