# Cómo se hizo el piloto (método para repetirlo en otra lámina)

> Versión final: el piloto se aprobó en la v2 (promedio 4,67) y la v3 trae los retoques. Archivos: `index.html` (= `v3.html`), `cambios.md` y las revisiones `revision-v1.md` y `revision-v2.md`.

## Resumen del ciclo
| Versión | Nota de la revisora | Qué faltaba |
|---|---|---|
| v1 | 3,67, sin visto bueno | Intervalo de los empaques, cantidad de tornillos, formas del resorte, las pastillas y el soporte, y «Cómo funciona» en el celular |
| v2 | 4,67, visto bueno | Textos del corte en el celular, botones de 42 px y la ventana del caliper |
| v3 | final | — |

Tiempo aproximado por lámina, una vez existe la plantilla: fuentes 20–30 min, dibujo 1,5–2 h, fichas 1 h, verificación 30 min.

## Plantilla reutilizable
La página es autocontenida: CSS y JS van adentro y no hay librerías. Para otra lámina se cambian cuatro bloques del script:
1. **Arte** (`arte*()`): una función por pieza, en coordenadas locales.
2. **`PIEZAS`**: id, número de la lámina, arte, ancla y corrimiento de la etiqueta, `vis` (`arm`/`exp`) y `chica`.
3. **`PASOS`**: el orden de desarme, con los corrimientos de cada paso.
4. **`FICHAS`**, **`CADENAS`** y **`FN`** (los pasos de «Cómo funciona»).
Lo demás funciona solo: el encuadre del despiece, el tamaño de los números, los rayos X, la selección, el desplegable de las fichas y los modos de celular.

## 1. Juntar fuentes (unos 20 min)
1. **Lámina de fábrica**: `despiece_local/grillas/<moto>-figNN.png` (imagen con cuadrícula, sí se puede leer). Los PDF de `despiece_local/` están bloqueados en los permisos: la lista de piezas se saca del catálogo de `manual_despiece/<moto>/` con `pdftotext -layout` al scratchpad y `grep "FIG. NN"`. Se anotan el número, el nombre en inglés y la cantidad.
2. **Manual del propietario** (también con `pdftotext`): cuadro de mantenimiento y la sección de la pieza. De ahí salen los intervalos «seguros».
3. **TallerYa**: `garaje/intervalos/<moto>.json`, la migración `0002_catalogo_inicial.py` (plan general), `despiece_fichas.py`, `despiece_glosario.py` y el dibujo genérico que usa esa lámina en `diagramas.py` (el campo `diagrama` del mapa JSON). Se anota todo lo que no cuadre.
4. **Internet**: medidas (fichas técnicas del fabricante y de repuestos), fotos solo como referencia de forma, y fallas típicas (Haynes, Brembo, fichas de fluidos). Cada dato con su enlace. Si un dato sale de un solo repuesto, se marca «aproximado».

## 2. Dibujar (lo más largo)
- **Proyección**: la pieza grande y plana (aquí el disco) se dibuja en su plano y se proyecta con `matrix(0.78,-0.16,0,1)`. Las demás piezas se dibujan en coordenadas propias con un giro y una escala comunes (`LOC`), así encajan sobre la grande.
- **Volumen** sin librerías: `extruir()` repite el contorno corrido hacia atrás (opuesto a la normal). Encima van gradiente, grano (`pGrano`), luz de borde (trazo blanco al 25 %) y sombra (`fSombra`). Los huecos se hacen con máscara para que se vea el canto adentro.
- **Lo que no se ve armado** (rosca de los tornillos, varilla del pasador) lleva la clase `oculto-arm` y aparece al salir la pieza.
- **Despiece**: cada paso mueve unas piezas y los corrimientos se suman (`PASOS[i].m`). Lo que sale en conjunto (el caliper con todo adentro) se mueve en un paso, y cada pieza sale después en el suyo. Las posiciones finales se planean en papel: zona por zona, sin cruces.
- **Encuadre**: la vista armada se ve de cerca (`VB_ARM`) y el despiece completo (`VB_EXP`). Los números se agrandan según el ancho real (`escalarEtiquetas`).

## 3. Escribir las fichas
Plantilla por pieza: qué es · para qué sirve · cómo falla **y por qué** (causa: desgaste, calor, humedad, mal uso, golpe, edad) · síntomas · cuándo · ¿se repara o se cambia? · **qué se compra de verdad** · se conecta con · si falla, qué les pasa a las demás · seguro/aproximado. Los nombres salen del glosario de TallerYa y los intervalos del plan de la moto. Cuando no coinciden, se pone el del manual y se anota la contradicción.

## Lecciones de la revisión v1
- **Leer la columna de cantidades del catálogo** antes de marcar algo «aproximado» (con `pdftotext -layout`, la cantidad va en la línea siguiente).
- **Buscar en el manual el intervalo de cada pieza, no solo el de la tarea.** Ejemplo: los empaques van cada 2 años junto con el líquido (p. 9-7).
- **Dibujar con la proporción de la foto**: medir alto y ancho de la pieza en el plano. Ojo con la escala local (`SX`), que angosta lo que se dibuja.
- Las piezas que explican el mecanismo (el soporte con sus pasadores) deben verse en el despiece, aunque armadas queden tapadas.
- **Celular**: el corte animado se apila en vertical en vez de deslizarse. Los números se comprueban por código: tamaño ≥ 28 px y que no se crucen.

## 4. Verificar
- Navegador del panel con `file:///…/index.html`. Ojo: es una copia estática, así que tras cada cambio hay que volver a navegar (recargar no basta). Las capturas a veces llegan atrasadas: confirmar el estado con `javascript_tool`.
- Probar a 360 px: sin desborde horizontal (en una grilla, los hijos con `min-width:0`), números legibles y la ficha al alcance.
- Sin errores de consola. Probar despiece completo y de vuelta, paso a paso, rayos X y enlaces de las fichas.
- **Si el panel del navegador está oculto**, las transiciones y `requestAnimationFrame` se congelan. Para medir, poner `transition:none`, llamar `aplicar(14)` y fijar el `viewBox` a mano.
- **Medir en vez de mirar** (gasta menos tokens que las capturas): números de ≥ 28 px que no se crucen; textos del corte de ≥ 11 px, sin cruzarse ni salirse; botones de ≥ 44 px; `scrollWidth` igual a `innerWidth`.
- Las reglas de CSS dentro de `@media` deben ganar en especificidad a las de más abajo (por ejemplo `#fn .fn-et`).

## Para llevarlo al sitio (no se hizo: el piloto no toca el código)
- Los datos de `FICHAS` encajan con `despiece_fichas.py` agregando los campos `por_que` (con causa), `compra`, `conecta` y `efectos`. Conviene hacerlo después de corregir allá las 11 contradicciones.
- El dibujo propio de cada lámina reemplazaría al genérico de `diagramas.py` solo en las láminas que tengan piloto.
