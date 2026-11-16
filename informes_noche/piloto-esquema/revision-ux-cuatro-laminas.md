# Revisión UX: las cuatro láminas del motor v2 (rúbrica v3)

Revisora UX · 16-nov-2026 (06:20–06:55). Revisé `motor/freno.html` (fig. 22), `motor/cvt.html` (fig. 12), `motor/bomba-freno.html` (fig. 26) y `motor/admision.html` (fig. 8, nueva), sobre el motor con:
- área de toque mínima automática;
- píldoras de tornillería que se esconden al salir su pieza;
- desarme automático más corto.

Las medí con `medir_lamina.py` en los 6 anchos. Lo dudoso lo comprobé en un Chrome propio por DevTools: el panel de la app, oculto, congela las animaciones. Además miré capturas de la fig. 8.

## Veredicto: aprueban las cuatro
| Lámina | Medible (6 · 8 · 9 · 10 · 11 · 12) | A ojo (1 · 2 · 3 · 4 · 5 · 7) | **Total** | Piezas ≥ 24 px a 360 | **¿Aprueba?** |
|---|---|---|---|---|---|
| Fig. 22 freno | 4 · 4,7 · 5 · 5 · 4,7 · 4,8 = **4,70** | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,60** | 14 de 16 | **SÍ** |
| Fig. 12 CVT | 4 · 4,7 · 5 · 5 · 4,8 · 4,8 = **4,72** | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,61** | 24 de 29 | **SÍ** |
| Fig. 26 bombas | 4 · 4,7 · 5 · 5 · 4,8 · 4,8 = **4,72** | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,61** | 23 de 28 | **SÍ** |
| Fig. 8 admisión | 4 · 4,7 · 5 · 5 · 4,8 · 4,8 = **4,72** | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,61** | 22 de 25 | **SÍ** |

**En las cuatro:**
- marcas de grupo de 45 a 46 px, sin fallas ni solapes;
- la tornillería recibe el toque;
- dibujo completo y «Desarmar» a la vista al entrar a un grupo, en los 6 anchos;
- hoja inferior al 12 % de la pantalla, sin tapar la pieza, con cerrar y botones de 44 px;
- «¿Se repara?» a entre 0,3 y 0,7 pantallas del inicio de la ficha;
- desarme automático de 4,2 s como máximo (antes, 9,1);
- sin desborde ni errores de consola, y el 3D abre en la fig. 26 y la fig. 8.

**Fig. 8 a ojo:**
- La vista general son 7 píldoras chicas con nombre (Inyector, Cuerpo, Múltiple, Respiro, Unión, Caja, Tapa), con buen reparto. Encaja con lo que pide el usuario.
- En el celular, el grupo «Tapa y filtro» se abre con la hoja abajo: nombre, una línea de «Qué es», «Ver ficha» y ×.

## Diferencias con la medición de piloto-esquema (CVT 3,5 / 4,63 → 4 / 4,72)
Las piezas 10 y 11 de la CVT (resortes y seguros de las zapatas) aparecían como «no se selecciona».
- **Lo comprobé:** desarmadas miden unos 52 px y se seleccionan bien (el círculo automático funciona). Con el grupo armado, asoman un borde de 12 a 16 px que no responde.
- **Qué cambié en el medidor:** ahora marca «no se selecciona» solo si una pieza falla en todos sus estados. Si falla en uno, sale como aviso y no baja la nota.
- **Otra corrección:** la espera del desarme ya no se estima (pasos × 1,3 s); se cronometra tocando «Desarmar». Da 4,2 s, y la subnota del criterio 1 sube de 3 a 4 en el freno y la CVT.

## ¿Piezas enteras antes que racimos? Sí
En la fig. 8, los círculos de los racimos de los tornillos 25 recortan a la 21 (19 px) y a la 27 (14 px). Conviene que **las piezas enteras tengan prioridad**:
1. **Cada pieza necesita un solo blanco bueno**, no uno por parte. Tocar cualquier racimo abre la misma ficha, así que basta con su racimo más grande.
2. **Orden de reparto:**
   - primero, los círculos de piezas enteras chicas, recortados solo entre ellos;
   - después, los racimos, recortados también contra los círculos y el dibujo de las piezas enteras;
   - un racimo nunca achica a otra pieza.
3. **Una pieza con un racimo de 24 px o más no recibe más círculos.**

Con eso la 21 y la 27 recuperan su área, y la fig. 8 debería volver a acercarse al 4,8 que piloto-esquema medía sin racimos. Los racimos siguen sirviendo para piezas de partes sueltas sin ninguna parte tocable, como los rodillos de un variador.

**Verificación:** con `medir_lamina.py`, ver que la fig. 8 no tenga piezas de menos de 24 px a 360 por culpa de un vecino, y que la CVT no pierda las suyas.

## Qué corregir (ninguna bloquea)
1. **Racimos con prioridad para piezas enteras** (lo de arriba). Arregla la 21 y la 27 de la fig. 8.
2. **Piezas que siguen por debajo de 24 px a 360:**
   - **freno:** resorte 11 (21 px) y 4 (20 px);
   - **CVT:** 5 (15 px), 18 (17 px), 19 (21 px), 3 (22 px) y 33 (23 px);
   - **fig. 26:** 12, 4 y 24 (21 px), 42 y 48 (22 px);
   - **fig. 8:** 27 (14 px), 21 (19 px) y 26 (22 px).

   La mayoría está a 1 a 3 px de la meta. Con la regla de los racimos y un radio mínimo de 13 px, en vez de 12, deberían pasar casi todas.
3. **CVT, Clutch armado:** el borde de las piezas 10 y 11 que asoma no responde. Mejor que tampoco se vea (que quede tapado del todo) o que responda y desarme el grupo, como al elegirlas en la lista.
4. **Celular:** ver la ficha completa sigue costando 3 toques (grupo, pieza y «Ver ficha»). El resumen de una línea del prototipo v3 adelanta lo esencial en la hoja.

## Prototipo v3 sobre el motor nuevo
`motor/prototipo-v3/fig26.html` ahora carga el motor nuevo sin cambios en sus archivos. **Sigue ganando: 4,69 contra 4,61** de la fig. 26 adoptada.
- **Medible:** igual (4,72); la hoja inferior pasa del 12 al 17 % de la pantalla con el resumen y sigue sin tapar la pieza.
- **A ojo:** suma en descubribilidad (buscar por síntoma, «¿Varado?») y en accesibilidad (teclado, foco y avisos).
