# Guía de revisión rápida (cualquier lámina del esquema)

**Revisión integrada (paso 9 de la skill, desde la ronda 3):** una sola revisora hace en una pasada las dos listas de abajo, Mecánica y UX, sin repetir en UX lo que ya dijo en Mecánica. Devuelve solo `{"nota":{"mecanica":x,"ux":y},"hallazgos":[…]}`: máximo 15, graves primero, con `campo`/`reemplazar`/`por` exactos cuando es texto (formato en `motor/aplicar_hallazgos.py`). Un hallazgo de dibujo o de grupos nombra **solo ids que existen** (los de «Grupos» del resumen, entre paréntesis): mira esa lista antes de sugerir uno; no inventes otro para una pieza que ya tiene id («1-taza» cuando ya está `1t`). No hay archivo de salida: la creadora lo aplica con `aplicar_hallazgos.py`. Una revisión externa o de auditoría usa la sección «Salida» de abajo.

## Antes de empezar (1 min)
1. `venv/Scripts/python.exe informes_noche/piloto-esquema/motor/autocontrol.py <lamina> --informe` → `motor/revision/<lamina>.md`. Trae los textos de desarme, fichas, «Cómo funciona», cadenas y «Cuándo», además de las certezas, los pendientes, el validador, la última medición y las capturas.
2. **Revisa sobre ese resumen y las capturas que ya hay.** Abre la página solo para lo que pide el ojo (punto 3 de UX) y no vuelvas a medir: la medición ya está en el resumen.
3. Si el resumen dice «Medición: todavía no hay», devuélvelo: la lámina no está lista para revisión.

## Lo que ya mide la máquina (no lo revises a mano)
Validador y `mas_controles`:
- números, nombres, códigos y cantidades contra el catálogo; kits;
- que lo que sujeta salga antes;
- cifras y torques sin fuente; certeza (catálogo = Seguro);
- intervalos de «Cuándo»;
- estilo v2 (sin «(N)», enlaces) y largo de los pasos;
- palabras de seguridad que se pierden al corregir (regresión);
- estructura de grupos, y píldoras que apuntan a piezas que no se ven.

`chequeo_rapido` y `medir_lamina`:
- etiquetas montadas y letra mínima;
- pasos sin cambio visible e indicador;
- toques hasta la ficha, marcas (centro, ±9 px, alto) y áreas tocables;
- solape del desarme;
- protagonismo del dibujo, primer pantallazo, espacio muerto, proximidad y ritmo;
- errores de consola y el 3D.

## Mecánica (≤ 10 min): solo lo que la máquina no puede saber
Responde ✔ / ✘ con una línea por cada ✘ (cita la ficha o el paso):
1. **Principio:** «Cómo funciona» explica bien cómo trabaja el sistema, sin piezas inventadas ni fuerzas al revés.
2. **Orden del desarme:** es el real (lo que de verdad queda libre en cada paso) y tiene herramienta especial o aviso donde hace falta (motor frío, sujetar, alicate de seguros…).
3. **Cada pieza:** qué es, dónde va fija, qué la sujeta y sobre qué corre, dicho igual en la ficha, el paso y «Cómo funciona».
4. **Fallas y síntomas:** son de moto (no de carro), con su causa; «¿se repara o se cambia?» es lo que haría un taller.
5. **Datos:** lo que dice «Seguro» sale de verdad del manual o del catálogo, y lo aproximado está marcado. Los `pendientes` de la creadora: ¿alguno es un error y no una duda?
6. **Cadenas «Si falla»:** cada eslabón sigue de verdad al anterior.

Nota 1-5 y una lista corta de cambios. No reescribas fichas: di qué cambiar.

## UX (≤ 10 min): solo lo que se juzga a ojo
Con las notas medibles del resumen ya puestas:
1. **Claridad (1) y descubribilidad (2):** en la captura se entiende qué tocar, y se ven las pestañas, «Desarmar» y «Números».
2. **Carga cognitiva (3):** ¿las fichas del resumen se leen en 20 s cada una? ¿Hay jerga sin explicar?
3. **A ojo en la página (un recorrido, no más):**
   - el dibujo es fiel a la forma;
   - «Cómo funciona» se entiende en el celular;
   - el 3D de cada ficha con `con3d` sirve;
   - ninguna píldora apunta a algo que no se ve.
4. **Accesibilidad (4) y consistencia (7):** el orden del foco y el tono de TallerYa.
5. **Rendimiento (5):** el peso de `-arte.js` (≤ ~40 KB).

Notas 1, 2, 3, 4, 5 y 7 (las demás ya las puso la medición) y una lista corta de cambios.

## Salida
Una sola nota por revisión en `informes_noche/piloto-esquema/revision-<tipo>-<lamina>.md`, de ≤ 30 líneas: las notas, los ✘ y los cambios. Después: `metricas.py dato <lamina> notas_mecanica|notas_ux '{…}'`.
