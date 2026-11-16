# Revisión mecánica v8 (corta): freno delantero NMAX 155, lámina 22

Revisora · 15-nov-2026 · Revisé `v8.html` (idéntico a `index.html`, comprobado con `cmp`) contra `v2.html`, la versión que aprobé con 4,67. Usé el diff y `cambios.md` (de la v3 a la v8). La UX no la califico aquí.

**Veredicto: el visto bueno se mantiene. Nota mecánica: 5/5, sin errores mecánicos.**

## Qué revisé
- **Textos y datos.** Comparé el texto visible de la página y los datos JS de la v2 y la v8.
  - `FICHAS`, `PASOS` (los 14 pasos del desarme), `FN` («Cómo funciona», 7 pasos), `CADENAS` y las filas de la tabla «Cuándo» **no cambiaron ni una palabra**.
  - Solo hay tres cambios de texto, todos correctos:
    - En el corte, «Soporte (fijo a la barra)» pasó a «Soporte (fijo)».
    - En la tabla, el renglón de los empaques ya no remite a «contradicción 9», porque esa lista salió de la página en la v5. Ahora dice «anotado para el equipo».
    - `TXT_ARMADO` ahora menciona «Transparente».
  - No queda ninguna referencia colgando a las contradicciones (grep).
- **Intervalos.** Siguen como en la v2: pastillas a los 1.000 km y luego cada 6.000 km; líquido DOT 4 y empaques de la bomba y del caliper cada 2 años («Seguro», manual pp. 9-7 y 9-25); mangueras revisadas en cada servicio y cambiadas cada 4 años. Los 3 tornillos del disco siguen como dato seguro.
- **v3: ventana del caliper (3).** Muestra los cantos de las pastillas y el borde del disco por el puente, que es correcto para un caliper flotante de un pistón.
- **Números → piezas (v8).**
  - En `PIEZAS` solo cambió `et`, es decir, dónde va el círculo del número. El ancla `anc` de cada guía no cambió. Cada número se mueve con su pieza, en el mismo grupo `g`.
  - Medido en el navegador a 1024 px: las 18 guías empiezan **sobre su propia pieza** (0 px de distancia), en el armado y en el despiece.
  - Visto en el despiece completo:
    - 4 queda bajo el pistón;
    - los dos 5 quedan junto a los dos anillos del kit de empaques (sello y guardapolvo);
    - 9b queda bajo la segunda pastilla;
    - 14 queda bajo la lámina antirruido;
    - 5b queda arriba, fuera del brazo del soporte 13.
  - Ninguno señala una pieza ajena.

## Errores mecánicos
Ninguno.

## Nota
Los 5 números que se movieron no se probaron uno por uno al tacto a 360 px. Eso lo cubre la revisión de UX (`elementFromPoint`, 50/50 según `cambios.md`).
