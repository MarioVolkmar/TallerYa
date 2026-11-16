# Revisión UX: fig. 1 «Cilindro, culata y bujía» (`motor/culata.html`)

Revisora UX · 16-nov-2026 (09:47–09:51). Medí con `medir_lamina.py` en los 6 anchos (rúbrica v3), con el motor nuevo de encuadre por estado. Revisé a ojo con dos capturas (vista general a 1280 y grupo «Bujía» con hoja a 390) y leí los 10 pasos de desarme.

## Veredicto: aprueba
| Medible (6 · 8 · 9 · 10 · 11 · 12) | A ojo (1 · 2 · 3 · 4 · 5 · 7) | **Total** | Bloqueantes |
|---|---|---|---|
| 5 · 4,7 · 5 · 5 · 4,8 · 4,8 = **4,88** | 5 · **4** · **4,5** · 4 · 4 · 4,5 | **4,57** | ninguno |

**Medidas:**
- 4 grupos (Bujía, Tapa, Culata, Cilindro) con marcas de 45 px, sin fallas.
- Las 15 piezas tienen 24 px o más a 360.
- Dibujo completo en los 6 anchos (520 px a 1280). «Desarmar» a la vista al entrar a un grupo; el desarme dura 4 s.
- Hoja inferior al 12 %, sin tapar la pieza. «¿Se repara?» queda a 0,81 pantallas del inicio de la ficha.
- 3D en la bujía y el cilindro. Sin errores.
- **El encuadre por estado funciona:** al entrar a «Bujía», la bujía llena el lienzo del celular.

## La vista desde arriba
**Es lo más flojo de la lámina** (por eso bajo descubribilidad a 4):
- **Las capas se tapan:** desde arriba, la tapa de la culata cubre a la culata y al cilindro, que quedan como dos rectángulos gris oscuro detrás. Sin la píldora, el motero no sabe cuál es cuál. Además, el cilindro, que es lo que da nombre a la lámina, casi no se ve.
- **Las píldoras se amontonan:** «Cilindro», «Culata» y «Tapa» caen en el mismo punto, a menos de 60 px una de otra a 1280, sobre la tapa. Se pueden tocar (el medidor no encuentra roces), pero no dicen a qué capa apuntan.
- **Lo que sí funciona:** la bujía, de lado y con su color, se reconoce al instante.

**Qué haría:**
1. **Mejor:** vista de tres cuartos o de lado, donde se apilen a la vista la tapa arriba, la culata en el medio y el cilindro con sus aletas abajo. Es como lo muestran los manuales, y cada píldora quedaría sobre su capa.
2. **Si se mantiene la vista desde arriba:**
   - correr cada píldora al borde visible de su capa: «Cilindro» en las aletas que asoman, «Culata» en su borde y «Tapa» en el centro;
   - aclarar un poco la culata y el cilindro, para que no queden como sombras;
   - una línea fina de guía de cada píldora a su capa.

## El largo de los pasos
| Paso | Largo | Opinión |
|---|---|---|
| 4 «Tuercas y tornillos de la culata» | **498 caracteres** (unas 80 palabras) | demasiado largo |
| 0 «Bujía» | 301 | largo, pero lo que trae vale la pena |
| 3 y 8 | 218 | bien |
| el resto | 105–242 | bien |

- **El paso 4 dice cuatro cosas a la vez:**
  - es trabajo de taller;
  - aviso de seguridad: no abrir el radiador en caliente;
  - lo que sale antes, de otras láminas;
  - cómo aflojar, más el apriete del manual.

  A 360 ocupa unas 9 líneas bajo el dibujo, y con el desarme automático no se alcanza a leer.

  **Propuesta, sin quitar el aviso ni el cierre:**
  - dejar en el paso «Trabajo de taller», el aviso del radiador, cómo se aflojan y el apriete del manual, en unos 250 caracteres;
  - pasar lo que sale antes a una línea aparte, «Antes salen: escape, admisión, mangueras, árbol de levas y cadena (otras láminas)», o a la ficha de la culata.
- **Paso 0 (bujía):** las especificaciones son lo más útil para el motero que hace esto en casa. Conviene ponerlas en una línea compacta al final: «Al armar: NGK CPR8EA-9 · 0,8–0,9 mm · 13 N·m (o ¼–½ vuelta después de apretar a mano)». Así se leen de un vistazo.
- **Regla general para la skill:** un paso de 250 caracteres como máximo. Lo que no quepa va a «Antes de esto» o a la ficha. Los avisos de seguridad y los pasos de cierre nunca se acortan.

## Qué corregir (nada bloquea)
1. Vista: tres cuartos o lateral; o, si no, las píldoras en el borde visible de cada capa y la culata y el cilindro más claros.
2. Paso 4: separar «lo que sale antes» del paso, conservando el aviso del radiador y el apriete.
3. Paso 0: las especificaciones de la bujía en una línea compacta.
