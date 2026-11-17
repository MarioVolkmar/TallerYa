# Autocontrol manual antes de entregar

Lo automatizable ya lo revisa el validador: preguntas 1, 2, 3, 4, 9 (parte), 10a, 12, 14a, 14b (silbido antes de la mariposa), 15, 16 (parte) y 18 de `M/autocontrol-mecanico.md`, más lado y versión. Aquí va **lo que solo se ve leyendo y mirando**. Responde sí o no; si es «no», corrige antes de entregar.

## A. Mecánico (`M/autocontrol-mecanico.md`, preguntas sin [S])
5. ¿El dibujo corresponde al tipo de pieza? Un sello con labio y no un aro fino; un resorte de lámina y no de alambre; la proporción real de una pastilla.
6. Para cada parte móvil o guía, ¿dices en qué pieza va fija y sobre cuál corre, y lo dices igual en todas las fichas?
7. Para cada pieza, ¿dices qué la sujeta (tuerca, anillo, rodamiento, tornillo, presión), y eso existe en la lámina con su número? Si sí, ¿está en `sujeta`?
8. ¿Las superficies de trabajo están donde son? Rampas, pistas, caras de fricción, el sello del pistón.
9. ¿El orden del desarme es el real, y cada pieza sale en el paso en que de verdad queda libre? El validador solo revisa lo que pusiste en `sujeta`.
10. ¿Hay herramienta especial o aviso de seguridad donde hace falta? Sujetar la polea, el compresor del resorte, la moto en el gato, el motor frío.
11. ¿Explicas el principio sin inventar piezas? En el freno, el sello devuelve el pistón y no hay ningún resorte.
13. ¿Los síntomas son de moto y no de carro? Por ejemplo, «se va hacia un lado» no aplica con un solo disco.
14. ¿«Cómo funciona», las fichas y los pasos dicen lo mismo sobre la misma pieza? Lee juntos todos los textos que nombran cada «(N)».
16. ¿Lo del manual está como «Seguro» y la práctica de taller como «Práctica de taller» o «Aproximado», sin mezclarlos? El validador solo ve que haya marca.
17. ¿Registraste las contradicciones con las fichas o el glosario de TallerYa? Por ejemplo, pastillas a 3.000 km contra 6.000.

**Según el sistema** (sección 5 de `M/autocontrol-mecanico.md`):
- **Motor y válvulas:** holguras en frío y del manual; admisión y escape distintos; marcas en el PMS de compresión.
- **Refrigeración:** refrigerante en tiempo y en km; termostato; la tapa presuriza y no se abre en caliente.
- **Suspensión:** grado y nivel del aceite; retén y guardapolvo son piezas distintas; precarga, compresión y rebote.
- **Eléctrico:** tipo de batería, carga y voltaje del manual; fusible con amperios; regulador y estator distintos.

## B. UX a ojo (`informes_noche/piloto-esquema/criterios-ux.md`: lo que `medir_lamina.py` no mide)
Pon una nota de 1 a 5 a cada uno y pásalas en `--ojo` en este orden: 1, 2, 3, 4, 5, 7.
1. **Claridad del recorrido:** ¿se entiende sin explicación qué hacer: tocar un número, desarmar, ver la ficha?
2. **Descubribilidad:** ¿se ven las pestañas, «Desarmar», «Números» y el zoom sin buscarlos?
3. **Carga cognitiva:** ¿textos cortos, una idea por paso y fichas que no abruman (lo largo, en «Para qué sirve…»)?
4. **Accesibilidad:** orden de foco lógico; `aria-*` que dicen la verdad, con el nombre de la pieza y no «botón»; contraste. El script solo mide los 44 px.
5. **Rendimiento:** peso de `-arte.js` y del JSON. Si el arte pasa de ~40 KB, revisar qué se puede pasar a la biblioteca.
7. **Consistencia con TallerYa:** clases `esq-`, la paleta, Oswald y Archivo, el tono de los textos (tú, frases cortas, sin jerga sin explicar).

Además:
- **10, ficha vacía:** ¿el texto sirve de verdad (plan, km, estado)?
- **12, espaciados:** ¿ritmo parejo entre bloques? El script pone 4 por defecto.
- **Lo propio de la lámina:** ¿el dibujo es fiel a la forma? ¿«Cómo funciona» se entiende en el celular, con el texto pegado al dibujo? ¿El 3D de cada pieza propia se reconoce en las 4 vistas?

## Validador y toques (pasado desde SKILL.md, paso 6-7)
- El validador revisa campos, catálogo, nombres, desarme, cifras y torques sin fuente, intervalos, certeza, estilo y seguridad v2, y la estructura v2 (grupos, `torn`, pasos, `certezaDe`, `con3d`, piezas sin grupo). Los **avisos** se leen todos: «¿nombre viejo?» casi siempre es un error de verdad.
- Errores de toque en el despiece: `--separar` corre antes `separar_numeros.py --escribir`. Si armas el JSON con un script propio, córrelo después de cada regeneración.
- Una pieza que no recibe el toque dentro de su grupo: píntala después (orden de `piezas`) o ponla en `v2.toqueExtra` (pocas: tapan a las vecinas). Dos píldoras de grupo encimadas: `marca` a mano.
- Rastros de la hermana (ronda 5): con `"hermana"` en el JSON, `--rapido` da error si un enlace `[[n|…]]` o un eslabón de «Si falla» copiado de la hermana no tiene el número remapeado (viejo o remapeado dos veces), o si la cinta, un texto o un rótulo del arte nombra la figura de la hermana; y aviso si una «fig./lámina N» está igual que en una hermana de otro catálogo. La marca propia, «sin ABS» y el verbo «junta» ya no son falsos positivos.

## Regresión de la skill y del motor (`M/regresion.py`)
- `regresion.py` (sin argumentos) mira `git status` y, de eso, solo lo que cambió desde la corrida anterior (`regresion/estado.json`); con archivos como argumentos, decide por ellos.
  - **Siempre** (5-10 s): validador en todas las láminas (en paralelo) y extractor (NMAX, Boxer, AKT, Honda y Crypton bilingüe) + esqueleto comparados byte a byte con `regresion/ref/`.
  - **Cambió el motor** (`esquema*.js/css`, `piezas-comunes.js`, `medir_*`, `chequeo_rapido.py`): chequeo en el navegador (360/390/1280) y firmas en las representativas (`REPRESENTATIVAS` en `regresion.py`: CVT, culata Honda y la última lámina creada), más las láminas que también cambiaron. Las firmas ignoran `guiasG`/`marcasG` (ruido).
  - **Cambiaron los datos, el arte o la página de una lámina:** solo esa en el navegador (390/1280).
  - **Catálogo, plantillas, esqueleto, validador o texto de la skill:** nada de navegador.
- `regresion.py --todas`: las láminas en el navegador, 5 a la vez en un solo Chrome, con el solape en la misma pestaña y la confirmación sin carga de lo que bloquee. **Caché:** una lámina cuyo JSON, arte, página y motor no cambiaron desde su último OK se salta. Con el motor cambiado usa 360/390/1280; si no, 390/1280. `--sin-cache` las revisa todas. Córrelo en segundo plano; el resumen queda en `regresion/ultimo.md`.
- `regresion.py --aceptar`: tras un cambio querido del extractor, del esqueleto o del dibujo, guarda las referencias nuevas (extractor, esqueleto y firmas).
- Lo de antes, a mano, sigue sirviendo para un caso puntual: `firma_lamina.py <páginas> --guardar|--comparar <archivo>` y `chequeo_rapido.py <página>`.
